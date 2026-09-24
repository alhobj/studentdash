"""End-to-end document import checks in a real browser, with fictional records."""
import importlib.util
import os
import unittest

import test_entry_browser
from studentdash.entry import ClassStore
from tools.create_import_example import docx_bytes, pdf_bytes


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Optional browser checks require requirements-dev.txt')
class ImportBrowserTests(unittest.TestCase):
    setUp = test_entry_browser.EntryBrowserTests.setUp

    def upload(self, extension):
        p = self.page
        p.goto(self.base + '/classes')
        p.get_by_label('Class name', exact=True).fill('Fictional import class')
        p.get_by_label('Paste student roster').fill('Alice Private\nBob Private')
        p.get_by_role('button', name='Create class', exact=True).click()
        p.get_by_role('link', name='Import assessment', exact=True).click()
        content = pdf_bytes() if extension == 'pdf' else docx_bytes()
        p.get_by_label('Test document').set_input_files(dict(name='fictional.' + extension, mimeType='application/pdf' if extension == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', buffer=content))
        p.get_by_role('button', name='Upload test & review', exact=True).click()
        p.wait_for_url('**/imports/*')

    def review_all(self):
        for checkbox in self.page.locator('.question-reviewed').all():
            checkbox.check()
        self.page.locator('#review-ack').check()

    def test_pdf_upload_review_finalize_and_score_grid(self):
        from playwright.sync_api import expect
        self.upload('pdf')
        p = self.page
        expect(p.get_by_role('heading', name='Review assessment import')).to_be_visible()
        expect(p.get_by_text('5 scorable questions', exact=False)).to_be_visible()
        expect(p.locator('.import-question')).to_have_count(6)
        expect(p.locator('.import-question').first.locator('.import-marks')).to_have_value('2')
        p.get_by_role('button', name='Accept all high-confidence suggestions').click()
        self.assertFalse(any(c.is_checked() for c in p.locator('.question-reviewed').all()))
        p.get_by_role('button', name='Create assessment', exact=True).click()
        expect(p.locator('#review-state')).to_contain_text('Check each question')
        p.get_by_role('button', name='Save draft', exact=True).click()
        p.wait_for_url('**?saved=1')
        review_url = p.url
        p.get_by_role('link', name='My classes', exact=True).click()
        p.get_by_role('link', name='Fictional import class', exact=True).click()
        p.get_by_role('link', name='Review Fictional assessment import example', exact=True).click()
        expect(p.locator('.import-question')).to_have_count(6)
        p.goto(review_url)
        self.review_all()
        p.get_by_role('button', name='Create assessment', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        expect(p.locator('#score-grid tbody tr')).to_have_count(2)
        expect(p.locator('#score-grid input[data-row="0"]')).to_have_count(5)
        p.locator('input[data-row="0"][data-col="0"]').fill('2')
        p.get_by_role('button', name='Save scores', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        expect(p.locator('input[data-row="0"][data-col="0"]')).to_have_value('2')
        doc = ClassStore(self.root / 'entered_classes').list()[0]
        self.assertEqual(doc['import_drafts'][0]['status'], 'confirmed')
        first = doc['assessments'][0]['questions'][0]
        self.assertIn('Calculate', first['tags']['CommandTerm'])
        self.assertNotIn('Skill', first['tags'])  # No bulk acceptance of semantic inference.
        self.assertEqual(self.errors, [])

    def test_docx_edit_split_combine_and_total_warning(self):
        from playwright.sync_api import expect
        self.upload('docx')
        p = self.page
        first = p.locator('.import-question').first
        text = first.locator('.import-text')
        original = text.input_value()
        text.fill(original + '\nExplain the next step.')
        text.evaluate('(element, at) => element.setSelectionRange(at, at)', len(original) + 1)
        first.get_by_role('button', name='Split question', exact=True).click()
        expect(p.locator('.import-question')).to_have_count(7)
        first = p.locator('.import-question').first
        first.locator('.import-number').fill('1a')
        first.locator('.import-marks').fill('1')
        second = p.locator('.import-question').nth(1)
        second.locator('.import-number').fill('1b')
        second.locator('.import-marks').fill('1')
        first.get_by_role('button', name='Combine with next', exact=True).click()
        expect(p.locator('.import-question')).to_have_count(6)
        expect(p.locator('.import-question').first.locator('.import-marks')).to_have_value('2')
        p.get_by_role('button', name='Add missing question', exact=True).click()
        p.locator('.import-question').last.get_by_role('button', name='Delete', exact=True).click()
        expect(p.locator('.import-question')).to_have_count(6)
        p.get_by_role('button', name='Add missing question', exact=True).click()
        last = p.locator('.import-question').last
        last.locator('.import-number').fill('5')
        last.locator('.import-text').fill('State another measurement.')
        last.locator('.import-marks').fill('1')
        p.get_by_role('button', name='Save draft', exact=True).click()
        p.wait_for_url('**?saved=1')
        expect(p.get_by_text('Document total: 16; extracted/reviewed total: 17.', exact=False)).to_be_visible()
        self.review_all()
        p.get_by_role('button', name='Create assessment', exact=True).click()
        expect(p.locator('[role="alert"]').first).to_contain_text('document-total difference')
        p.locator('#review-note').fill('Teacher added question 5, worth one additional mark.')
        if os.environ.get('STUDENTDASH_IMPORT_SCREENSHOT'):
            p.screenshot(path=os.environ['STUDENTDASH_IMPORT_SCREENSHOT'], full_page=False)
        p.get_by_role('button', name='Create assessment', exact=True).click()
        p.wait_for_url('**/scores?saved=1')
        expect(p.locator('#score-grid input[data-row="0"]')).to_have_count(6)
        self.assertEqual(self.errors, [])

    def test_reject_and_manual_multiple_tags_persist(self):
        from playwright.sync_api import expect
        self.upload('docx')
        p = self.page
        first = p.locator('.import-question').first
        proposal = first.locator('.import-suggestions p').filter(has_text='CommandTerm: Calculate')
        proposal.get_by_role('button', name='Reject', exact=True).click()
        p.get_by_role('button', name='Accept all high-confidence suggestions').click()
        first = p.locator('.import-question').first
        first.locator('.selected-classifications > summary').click()
        first.get_by_text('Skill (0 selected)', exact=True).click()
        first.get_by_label('Data interpretation', exact=True).check()
        first.get_by_label('Quantitative problem solving', exact=True).check()
        p.get_by_role('button', name='Save draft', exact=True).click()
        p.wait_for_url('**?saved=1')
        doc = ClassStore(self.root / 'entered_classes').list()[0]
        node = doc['import_drafts'][0]['nodes'][0]
        self.assertNotIn('Calculate', node['tags'].get('CommandTerm', []))
        self.assertEqual(set(node['tags']['Skill']), {'Data interpretation', 'Quantitative problem solving'})
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
