"""The authored Excel extension appears unchanged, with immediate A-D checking."""
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / 'resources' / 'ib-chemistry'


class AuthoredMcqContentTests(unittest.TestCase):
    def test_all_100_source_questions_and_correct_choices(self):
        source = json.loads((ROOT / 'tools/resources/structure_mcq_authored.json').read_text(encoding='utf-8'))['sections']
        published = json.loads((RESOURCES / 'authored-mcq.json').read_text(encoding='utf-8'))
        published = [q for q in published if q['source_id'].startswith('NEW_')]
        self.assertEqual(len(published), 100)
        self.assertEqual(len({q['id'] for q in published}), 100)
        self.assertEqual(Counter(q['topic'] for q in published), {topic:20 for topic in source})
        self.assertEqual(Counter(q['answer'][0] for q in published), dict.fromkeys('ABCD',25))
        for q in published:
            row = source[q['topic']][int(q['source_id'].rsplit('_',1)[1])-1]
            self.assertEqual(q['prompt'], row[0])
            self.assertEqual(q['working'], row[5])
            self.assertEqual(set(q['options']), set(row[1:5]))
            self.assertEqual(q['options']['ABCD'.index(q['answer'][0])], row[1])
            page, anchor = q['path'].split('#')
            html = (RESOURCES / page).read_text(encoding='utf-8')
            self.assertIn(f'id="{anchor}"', html)
            self.assertEqual(html.count('data-authored-mcq='), 20)


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class AuthoredMcqBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime=sync_playwright().start();self.addCleanup(runtime.stop)
        self.browser=runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER','msedge' if os.name=='nt' else 'chromium'),headless=True)
        self.addCleanup(self.browser.close)
        self.page=self.browser.new_page()
        self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def test_every_choice_immediate_feedback_and_reset(self):
        for page in ('s1-1.html','s1-2.html','s1-3.html','s2-1.html','s2-2.html'):
            self.page.goto((RESOURCES / page).as_uri())
            self.page.set_viewport_size({'width':320,'height':900})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            cards=self.page.locator('[data-authored-mcq]')
            self.assertEqual(cards.count(),20)
            for card in cards.all():
                correct=card.get_attribute('data-correct')
                for letter in 'ABCD':
                    card.locator(f'[data-choice="{letter}"]').click()
                    text=card.locator('.mcq-feedback').inner_text()
                    self.assertTrue(text.startswith('Correct' if letter==correct else 'Not correct'),text)
                    self.assertEqual(card.locator('[aria-pressed=true]').count(),1)
                card.locator('.mcq-retry').click()
                self.assertEqual(card.locator('[aria-pressed=true]').count(),0)
                self.assertFalse(card.locator('.mcq-explanation').evaluate('(d)=>d.open'))

    def test_keyboard_saved_choice_and_journal_buttons(self):
        self.page.goto((RESOURCES/'s1-1.html').as_uri())
        card=self.page.locator('[data-authored-mcq]').first
        correct=card.get_attribute('data-correct');key=card.get_attribute('data-authored-mcq')
        control=card.locator(f'[data-choice="{correct}"]')
        control.focus();control.press('Enter')
        self.assertTrue(card.locator('.mcq-feedback').inner_text().startswith('Correct'))
        self.assertEqual(self.page.evaluate('(id)=>StudentPractice.status(id)',key),'Correct independently')
        self.page.reload()
        self.assertTrue(card.locator('.mcq-feedback').inner_text().startswith('Saved answer: Correct'))
        self.page.goto((RESOURCES/'my-practice.html').as_uri())
        self.page.get_by_text('Choose questions or create a teacher assignment',exact=True).click()
        row=self.page.locator('.learning-list > div').filter(has=self.page.locator(f'input[value="{key}"]'))
        row.get_by_role('button',name='Practise this question',exact=True).click()
        host=self.page.locator('#learning-session')
        self.assertEqual(host.get_by_role('group',name='Answer choices').locator('button').count(),4)
        host.get_by_role('button',name='Retry independently with a blank answer',exact=True).click()
        host.get_by_role('group',name='Answer choices').locator('button').nth('ABCD'.index(correct)).click()
        self.assertIn('Correct.',host.locator('form [role=status]').inner_text())
        self.assertIn('Correct independently',host.inner_text())
