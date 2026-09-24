"""Browser acceptance checks; install requirements-dev.txt and an Edge/Chromium browser."""
import importlib.util
import os
from pathlib import Path
import tempfile
import threading
import unittest

from werkzeug.serving import make_server

from studentdash.config import Config
from studentdash.entry import ClassStore
from studentdash.teacher import create_app


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Optional browser checks require requirements-dev.txt')
class EntryBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright, Error
        self.temporary = tempfile.TemporaryDirectory(prefix='studentdash-browser-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        self.server = make_server('127.0.0.1', 0, self.app)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.shutdown)
        self.playwright = sync_playwright().start()
        self.addCleanup(self.playwright.stop)
        channel = os.environ.get('STUDENTDASH_TEST_BROWSER', 'msedge' if os.name == 'nt' else 'chromium')
        try:
            self.browser = self.playwright.chromium.launch(channel=channel, headless=True)
        except Error as exc:
            self.skipTest(f'Browser unavailable: {exc.message.splitlines()[0]}')
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.page.on('dialog', lambda dialog: dialog.accept())
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def setup_assessment(self):
        p = self.page
        p.goto(self.base)
        p.get_by_label('Class name', exact=True).fill('Fictional Chemistry class')
        p.get_by_label('Paste student roster').fill('Alice Private\talice@example.invalid\nBob Private\tbob@example.invalid\nCarol Private')
        p.get_by_role('button', name='Create class', exact=True).click()
        p.get_by_role('link', name='Create manually', exact=True).click()
        p.get_by_label('Assessment name', exact=True).fill('First real-workflow rehearsal')
        p.get_by_label('Description (optional)').fill('Fictional records only')
        for i, maximum in enumerate([2, 3, 1, 2]):
            if i:
                p.get_by_role('button', name='Add question', exact=True).click()
            row = p.locator('#questions > tr').nth(i)
            row.get_by_label('Question label', exact=True).fill(['1', '2', '3a', '3b'][i])
            row.get_by_label('Maximum marks', exact=True).fill(str(maximum))
        first = p.locator('#questions > tr').first
        first.locator('summary').filter(has_text='Classify').click()
        first.get_by_label('Curriculum mapping (optional)').fill('S1.2')
        first.get_by_text('Command Term', exact=True).click()
        first.get_by_label('Explain', exact=True).check()
        p.get_by_role('button', name='Save assessment & enter scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')

    def paste(self, value, row=0, col=0):
        self.page.evaluate('(value) => navigator.clipboard.writeText(value)', value)
        self.page.locator(f'input[data-row="{row}"][data-col="{col}"]').click()
        self.page.keyboard.press('Control+V')
        self.page.wait_for_function("document.querySelector('#grid-message').textContent.length > 0")

    def test_full_teacher_workflow_clipboard_keyboard_reopen_and_export(self):
        from playwright.sync_api import expect
        self.setup_assessment()
        p = self.page
        self.paste('2\t3\t1\t2\r\n1\t2\t1\t0\r\n2\tA\t1\t1\r\n')
        expect(p.locator('.row-total').nth(0)).to_have_text('8/8')
        expect(p.locator('.row-total').nth(1)).to_have_text('4/8')
        expect(p.locator('.row-total').nth(2)).to_have_text('Incomplete')
        p.locator('input[data-row="0"][data-col="0"]').focus()
        p.keyboard.press('Enter')
        expect(p.locator('input[data-row="1"][data-col="0"]')).to_be_focused()
        p.keyboard.press('Tab')
        expect(p.locator('input[data-row="1"][data-col="1"]')).to_be_focused()
        p.keyboard.press('ArrowRight')
        expect(p.locator('input[data-row="1"][data-col="2"]')).to_be_focused()
        p.get_by_role('button', name='Save scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        scores_url = p.url
        p.reload()
        expect(p.locator('.row-total').first).to_have_text('8/8')
        p.locator('input[data-row="0"][data-col="0"]').fill('P')
        expect(p.locator('.row-total').first).to_have_text('Incomplete')
        p.get_by_role('button', name='Generate student dashboards', exact=True).click()
        expect(p.locator('#grid-message')).to_have_text('Save scores before generating dashboards.')
        p.get_by_role('button', name='Save scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        p.get_by_role('link', name='View overview', exact=True).click()
        expect(p.get_by_role('heading', name='Class overview', exact=True)).to_be_visible()
        p.goto(scores_url)
        p.get_by_role('button', name='Generate student dashboards', exact=True).click()
        p.wait_for_url(self.base + '/?**')
        expect(p.get_by_text('Generated 3 student dashboards successfully.', exact=True)).to_be_visible()
        alice_row = p.locator('tr').filter(has_text='Alice Private')
        alice_row.get_by_role('link', name='Open snapshot', exact=True).click()
        self.assertNotIn('Bob Private', p.content())
        self.assertNotIn('bob@example.invalid', p.content())
        expect(p.locator('.assessment-view:not([hidden])').get_by_text('Incomplete', exact=False).first).to_be_visible()
        doc = ClassStore(self.root / 'entered_classes').list()[0]
        sid = doc['students'][0]['id']
        p.goto((self.root / 'output' / ('class-' + doc['id']) / ('student' + sid + '.html')).as_uri())
        self.assertNotIn(doc['students'][1]['id'], p.content())
        expect(p.get_by_role('heading', name='Assessment history')).to_be_visible()
        # A fresh browser session can select the saved class without reposting a roster.
        fresh = self.browser.new_page()
        try:
            fresh.goto(self.base + '/classes')
            fresh.get_by_role('link', name='Fictional Chemistry class', exact=True).click()
            fresh.get_by_role('link', name='Enter / edit scores', exact=True).click()
            expect(fresh.locator('input[data-row="0"][data-col="0"]')).to_have_value('')
            expect(fresh.locator('.row-total').nth(1)).to_have_text('4/8')
        finally:
            fresh.close()
        self.assertEqual(self.errors, [])

    def test_paste_validation_statuses_reorder_and_errors(self):
        from playwright.sync_api import expect
        self.setup_assessment()
        p = self.page
        self.paste('99\tE\tM\tP\n0\t1,5\t0\t2\nA\tA\tA\tA')
        expect(p.locator('input[data-row="0"][data-col="0"]')).to_have_attribute('aria-invalid', 'true')
        p.get_by_role('button', name='Save scores', exact=True).click()
        expect(p.locator('#grid-message')).to_have_text('Correct the highlighted cells before saving.')
        p.locator('input[data-row="0"][data-col="0"]').fill('2')
        expect(p.locator('.row-total').nth(1)).to_have_text('3.5/8')
        expect(p.locator('.row-total').nth(2)).to_have_text('Absent')
        p.get_by_role('button', name='Save scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        self.paste('1\t2', 2, 3)
        expect(p.locator('#grid-message')).to_contain_text('beyond the grid')
        expect(p.locator('input[data-row="2"][data-col="3"]')).to_have_value('A')
        self.paste('1\t2\n3')
        expect(p.locator('#grid-message')).to_contain_text('rectangular block')
        expect(p.locator('input[data-row="0"][data-col="0"]')).to_have_value('2')
        p.get_by_role('link', name='Edit questions & classifications', exact=True).click()
        p.locator('#questions > tr').first.get_by_role('button', name='Move question down').click()
        p.get_by_role('button', name='Save assessment & enter scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        expect(p.locator('input[data-row="0"][data-col="0"]')).to_have_value('E')
        expect(p.locator('input[data-row="0"][data-col="1"]')).to_have_value('2')
        if os.environ.get('STUDENTDASH_TEST_SCREENSHOT'):
            p.screenshot(path=os.environ['STUDENTDASH_TEST_SCREENSHOT'], full_page=True)
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
