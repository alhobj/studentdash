"""Portable progress, independence, assignments and numerical feedback in a real browser."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires Playwright')
class LearningBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime = sync_playwright().start()
        self.addCleanup(runtime.stop)
        self.browser = runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER', 'msedge' if os.name == 'nt' else 'chromium'), headless=True)
        self.addCleanup(self.browser.close)
        self.page = self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open(self, profile='ib-math-ai-sl', page='my-practice.html'):
        self.page.goto((ROOT / 'resources' / profile / page).as_uri())

    def test_saved_session_mistakes_and_independence(self):
        from playwright.sync_api import expect
        self.open()
        p = self.page
        p.get_by_role('button', name='Start mixed revision (up to 6)', exact=True).click()
        host = p.locator('#learning-session')
        host.locator('input').fill('999')
        host.get_by_role('button', name='Check answer', exact=True).click()
        expect(host.get_by_text('Recorded: Needs another attempt', exact=True)).to_be_visible()
        p.reload()
        p.get_by_role('button', name='Resume saved session', exact=True).click()
        expect(host.locator('input')).to_have_value('999')
        prompt = host.locator('label').inner_text()
        answer = p.evaluate('(prompt)=>PRACTICE_CATALOG.questions.find(q=>q.prompt===prompt).answer', prompt)
        host.get_by_role('button', name='Retry independently with a blank answer', exact=True).click()
        host.locator('input').fill(str(answer))
        host.get_by_role('button', name='Check answer', exact=True).click()
        expect(host.get_by_text('Recorded: Correct independently', exact=True)).to_be_visible()
        host.get_by_role('button', name='Next question', exact=True).click()
        host.get_by_text('Hint', exact=True).click()
        prompt = host.locator('label').inner_text()
        answer = p.evaluate('(prompt)=>PRACTICE_CATALOG.questions.find(q=>q.prompt===prompt).answer', prompt)
        host.locator('input').fill(str(answer))
        host.get_by_role('button', name='Check answer', exact=True).click()
        expect(host.get_by_text('Recorded: Completed with help or retry', exact=True)).to_be_visible()
        host.get_by_role('button', name='Finish session and refresh progress', exact=True).click()
        p.get_by_role('button', name='Practise my mistakes', exact=True).click()
        self.assertEqual(host.locator('label').inner_text(), prompt)
        p.set_viewport_size({'width':320, 'height':900})
        self.assertTrue(p.evaluate('document.documentElement.scrollWidth <= innerWidth'))

    def test_regular_pages_record_and_resume_answers(self):
        from playwright.sync_api import expect
        self.open(page='basics-1.html')
        form = self.page.locator('.foundation-step').first
        form.locator('input').fill('500')
        form.get_by_role('button').click()
        self.page.reload()
        expect(form.locator('input')).to_have_value('500')
        self.assertGreater(self.page.evaluate("JSON.parse(localStorage.getItem('studentdash.practice.v1')).attempts.length"), 0)

    def test_progress_merge_validation_and_assignment_export(self):
        from playwright.sync_api import expect
        self.open()
        p = self.page
        p.get_by_role('button', name='Start mixed revision (up to 6)', exact=True).click()
        p.locator('#learning-session input').fill('7')
        p.locator('#learning-session').get_by_role('button', name='Check answer', exact=True).click()
        with p.expect_download() as pending:
            p.get_by_role('button', name='Export my progress', exact=True).click()
        progress = Path(self.temp.name) / 'progress.json'
        pending.value.save_as(progress)
        p.get_by_label('Import my progress', exact=True).set_input_files(progress)
        expect(p.locator('.learning-status')).to_contain_text('Progress merged')
        self.assertEqual(p.evaluate("JSON.parse(localStorage.getItem('studentdash.practice.v1')).attempts.length"), 1)
        bad = Path(self.temp.name) / 'bad.json'
        bad.write_text('{"schema":999,"attempts":[]}', encoding='utf-8')
        p.get_by_label('Import my progress', exact=True).set_input_files(bad)
        expect(p.locator('.learning-status')).to_contain_text('Unsupported')
        p.get_by_text('Choose questions or create a teacher assignment', exact=True).click()
        p.locator('.learning-list input[type=checkbox]').first.check()
        p.get_by_label('Assignment title', exact=True).fill('Fictional practice')
        p.get_by_label('Instructions', exact=True).fill('<script>throw Error("unsafe")</script> Explain your method.')
        with p.expect_download() as pending:
            p.get_by_role('button', name='Export standalone assignment page', exact=True).click()
        standalone = Path(self.temp.name) / 'assignment.html'
        pending.value.save_as(standalone)
        p.goto(standalone.as_uri())
        expect(p.get_by_role('heading', name='Fictional practice', exact=True)).to_be_visible()
        p.get_by_role('button', name='Start assignment', exact=True).click()
        with p.expect_download() as pending:
            p.get_by_role('button', name='Export completion report', exact=True).click()
        report = Path(self.temp.name) / 'report.json'
        pending.value.save_as(report)
        data = json.loads(report.read_text(encoding='utf-8'))
        self.assertTrue(data['selfReported'])
        self.assertEqual(len(data['questions']), 1)
        p.get_by_label('Review a student completion report', exact=True).set_input_files(report)
        expect(p.locator('#report-review')).to_contain_text('not authenticated')

    def test_checker_units_scale_sign_and_all_authored_answers(self):
        self.open('ib-chemistry')
        result = self.page.evaluate('''() => {
          const q=PRACTICE_CATALOG.questions.find(q=>q.units?.includes('mol'));
          return [StudentPractice.check(q, `${q.answer} mol`), StudentPractice.check(q, `${q.answer} g`),
            StudentPractice.check({answer:-20}, '20'), StudentPractice.check({answer:.2},'200'),
            StudentPractice.check({answer:1/3},'.33'),
            PRACTICE_CATALOG.questions.every(q=>StudentPractice.check(q, String(Array.isArray(q.answer)?q.answer[0]:q.answer)).correct)];
        }''')
        self.assertTrue(result[0]['correct'])
        self.assertIn('requested unit', result[1]['message'])
        self.assertIn('sign', result[2]['message'])
        self.assertIn('scale', result[3]['message'])
        self.assertIn('rounding', result[4]['message'])
        self.assertTrue(result[5])

    def test_storage_unavailable_is_explicit_and_export_still_works(self):
        self.page.add_init_script("Object.defineProperty(window, 'localStorage', {get(){throw new Error('blocked')}})")
        self.open()
        self.assertIn('unavailable', self.page.locator('[data-storage-message]').inner_text())
        with self.page.expect_download():
            self.page.get_by_role('button', name='Export my progress', exact=True).click()
