"""Offline question-review workflow and bounded practice sets."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from tests import test_authored_mcq_resources as authored

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mcq_review import apply_reviews, option_feedback


class ReviewValidationTests(unittest.TestCase):
    def test_feedback_identifies_sign_and_scale(self):
        self.assertIn('wrong sign',option_feedback('-2','2','Divide mass by molar mass.'))
        self.assertIn('ten times',option_feedback('20','2','Divide mass by molar mass.'))
        self.assertIn('too low',option_feedback('1','2','Divide mass by molar mass.'))

    def test_apply_valid_review_and_reject_unknown_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q={'id':'fictional:1','prompt':'Old'}
            patch=dict(prompt='Fictional revised prompt',options=['one','two','three','four'],answer='B',working='Two is correct.',feedback=dict.fromkeys('ABCD','Check the fictional rule.'),flag='reviewed',notes='Fictional note')
            raw={'schema':1,'profile':root.name,'changes':{'fictional:1':patch}}
            path=root/'mcq-review.json';path.write_text(json.dumps(raw))
            apply_reviews(root,[q]);self.assertEqual(q['answer'],['B']);self.assertEqual(q['prompt'],patch['prompt'])
            raw['changes']={'unknown':patch};path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError):apply_reviews(root,[q])
            raw['changes']={'fictional:1':{**patch,'options':['one']*4}};path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError):apply_reviews(root,[q])


class ReviewBrowserTests(authored.AuthoredMcqBrowserTests):
    def test_five_sets_and_choice_feedback(self):
        for profile,name in [('ib-chemistry','s1-4.html'),('ib-math-ai-sl','mcq-1-2.html')]:
            self.page.goto((ROOT/'resources'/profile/name).as_uri())
            self.page.get_by_role('button',name='Start five-question set',exact=True).click()
            cards=self.page.locator('[data-authored-mcq]:visible');self.assertEqual(cards.count(),5)
            first=cards.first;key=first.get_attribute('id');correct=first.get_attribute('data-correct')
            wrong=first.locator(f'[data-choice]:not([data-choice="{correct}"])').first
            hint=wrong.get_attribute('data-feedback');wrong.click();self.assertIn(hint,first.locator('.mcq-feedback').inner_text())
            for _ in range(3):self.page.get_by_role('button',name='Five more like these',exact=True).click()
            self.assertEqual(cards.count(),5);self.assertNotEqual(cards.first.get_attribute('id'),key)
            self.assertTrue(self.page.get_by_role('button',name='Five more like these',exact=True).is_disabled())
            self.page.get_by_role('button',name='Show all 20 questions').click();self.assertEqual(cards.count(),20)

    def test_journal_five_more_no_repetition(self):
        self.page.goto((ROOT/'resources/ib-math-ai-sl/my-practice.html').as_uri())
        self.page.get_by_role('button',name='Start five-question set',exact=True).click()
        host=self.page.locator('#learning-session');self.assertIn('5 question(s)',host.inner_text())
        first=host.locator('form label').inner_text()
        self.page.get_by_role('button',name='Five more like these',exact=True).click()
        self.assertNotEqual(host.locator('form label').inner_text(),first)
        self.assertIn('5 question(s)',host.inner_text())

    def test_editor_save_preview_export_import_and_validation(self):
        root=ROOT/'resources/ib-math-ai-sl'
        self.page.goto((root/'question-review.html').as_uri())
        self.page.get_by_label('Search questions',exact=True).fill('MCQ_1_1_001')
        self.page.locator('#mcq-review button').filter(has_text='Evaluate').first.click()
        self.page.get_by_label('Question wording',exact=True).fill('Fictional revised question')
        self.page.get_by_label('Option A',exact=True).fill('<b>literal option</b>')
        self.page.get_by_label('Feedback for choice A',exact=True).fill('Fictional targeted hint')
        self.page.get_by_label('Correct answer',exact=True).select_option('A')
        self.page.get_by_label('Review status',exact=True).last.select_option('too repetitive')
        self.page.get_by_role('button',name='Preview question',exact=True).click()
        self.page.get_by_role('region',name='Question preview').get_by_role('button').first.click()
        self.assertIn('Correct. Fictional targeted hint',self.page.get_by_role('region',name='Question preview').inner_text())
        self.assertEqual(self.page.get_by_role('region',name='Question preview').locator('b').count(),0)
        self.page.get_by_role('button',name='Save draft',exact=True).click()
        with self.page.expect_download() as download:self.page.get_by_role('button',name='Export review file').click()
        raw=json.loads(Path(download.value.path()).read_text())
        patch=next(iter(raw['changes'].values()));self.assertEqual(patch['flag'],'too repetitive')
        self.page.reload();self.page.get_by_label('Search questions',exact=True).fill('Fictional revised question')
        self.assertIn('1 matching questions',self.page.locator('#mcq-review').inner_text())
        upload=self.page.get_by_label('Import review file',exact=True)
        upload.set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps({**raw,'profile':'wrong'}).encode()})
        self.page.wait_for_function("document.querySelector('#mcq-review [role=status]').textContent.includes('Import rejected')")
        upload.set_input_files({'name':'good.json','mimeType':'application/json','buffer':json.dumps(raw).encode()})
        self.page.wait_for_function("document.querySelector('#mcq-review [role=status]').textContent.includes('Draft saved')")
