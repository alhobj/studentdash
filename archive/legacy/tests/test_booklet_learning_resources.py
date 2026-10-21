"""Check authored answers, staged support and diagnostic feedback in both profiles."""
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BookletLearningContentTests(unittest.TestCase):
    def test_independent_answers_and_shared_runtime(self):
        expected = {
            'ib-math-ai-sl': {'sequence': [19, 21, 29], 'growth': [1210, 2205, 720],
                             'gradient': [-2, -2, -2], 'arc': [2*math.pi, 4*math.pi, 4*math.pi],
                             'expected': [3, 8, 3], 'differentiate': [12, 12, 16]},
            'ib-chemistry': {'concentration': [.4, .4, .5], 'gas-volume': [24.93, 49.86, 16.62],
                            'reaction-heat': [-2.09, -3.344, -3.762], 'bond-energy': [-200, -300, -250],
                            'atomic-data': [18, 44, 16]}}
        for profile, answers in expected.items():
            root = ROOT / 'resources' / profile
            packs = json.loads((root / 'booklet-practice.json').read_text(encoding='utf-8'))
            self.assertEqual({p['id'] for p in packs}, set(answers))
            self.assertEqual((root / 'booklet-practice.js').read_text(encoding='utf-8'), (ROOT / 'tools/booklet-practice.js').read_text(encoding='utf-8'))
            for pack in packs:
                self.assertEqual(len({q['prompt'] for q in pack['questions']}), 3)
                for q, answer in zip(pack['questions'], answers[pack['id']]):
                    self.assertAlmostEqual(q['answer'], answer)
                    self.assertTrue(q['mistakes'])


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class BookletLearningBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime = sync_playwright().start()
        self.addCleanup(runtime.stop)
        self.browser = runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER', 'msedge' if os.name == 'nt' else 'chromium'), headless=True)
        self.addCleanup(self.browser.close)
        self.page = self.browser.new_page()
        self.errors = []
        self.network = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('request', lambda r: self.network.append(r.url) if r.url.startswith('http') else None)

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.network, [])

    def test_all_questions_feedback_stages_and_reset(self):
        checked = 0
        for profile in ('ib-math-ai-sl', 'ib-chemistry'):
            root = ROOT / 'resources' / profile
            packs = json.loads((root / 'booklet-practice.json').read_text(encoding='utf-8'))
            self.page.goto((root / 'booklet-practice.html').as_uri())
            for pack in packs:
                host = self.page.locator('#' + pack['id'])
                ref = host.locator('.lookup-reference')
                unit = host.locator('.lookup-unit')
                number = host.locator('.lookup-answer')
                feedback = host.locator('.lookup-feedback')
                submit = host.locator('button[type=submit]')
                for i, q in enumerate(pack['questions']):
                    checked += 1
                    self.assertIn(f'Question {i+1} of 3', host.locator('.lookup-position').inner_text())
                    self.assertEqual(number.input_value(), '')
                    self.assertEqual(ref.input_value(), '')
                    guidance = host.locator('.lookup-guidance').inner_text()
                    self.assertEqual(guidance, q['hint'] if i == 0 else q['cue'] if i == 1 else 'Try choosing and setting up the calculation yourself. Open More support whenever you need it.')
                    host.locator('.lookup-support summary').click()
                    self.assertEqual(host.locator('.lookup-support p').inner_text(), q['hint'])
                    submit.click()
                    self.assertIn('Choose a booklet entry', feedback.inner_text())
                    for choice in pack['choices']:
                        if choice['id'] != pack['reference']:
                            ref.select_option(choice['id']); submit.click()
                            self.assertEqual(feedback.inner_text(), choice['feedback'])
                    ref.select_option(pack['reference']); submit.click()
                    self.assertIn('Choose the requested unit', feedback.inner_text())
                    for option in pack['units']:
                        if option['label'] != pack['unit']:
                            unit.select_option(label=option['label']); submit.click()
                            self.assertEqual(feedback.inner_text(), option['feedback'])
                    unit.select_option(label=pack['unit']); submit.click()
                    self.assertIn('finite number', feedback.inner_text())
                    for mistake in q['mistakes']:
                        number.fill(str(mistake['value'])); submit.click()
                        self.assertEqual(feedback.inner_text(), mistake['feedback'])
                    number.fill(str(q['answer'])); number.press('Enter')
                    self.assertIn('numerical answer match', feedback.inner_text())
                    self.assertIsNone(number.get_attribute('aria-invalid'))
                    host.locator('.lookup-working summary').click()
                    self.assertEqual(host.locator('.lookup-working p').inner_text(), q['working'])
                    host.locator('.lookup-next').click()
                    self.assertIsNone(host.locator('.lookup-working').get_attribute('open'))
                self.assertIn('Guided setup', host.locator('.lookup-position').inner_text())
                host.locator('.lookup-next').click()
                host.locator('.lookup-previous').click()
                self.assertIn('Question 1', host.locator('.lookup-position').inner_text())
                host.locator('.lookup-next').click()
                host.locator('.lookup-reset').click()
                self.assertTrue(host.locator('.lookup-previous').is_disabled())
                self.assertEqual(feedback.inner_text(), '')
        self.assertEqual(checked, 33)

    def test_mobile_and_no_javascript_worksheet(self):
        for profile, count in [('ib-chemistry', 15), ('ib-math-ai-sl', 18)]:
            url = (ROOT / 'resources' / profile / 'booklet-practice.html').as_uri()
            self.page.goto(url)
            for width in (320, 1100):
                self.page.set_viewport_size({'width': width, 'height': 900})
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            static = self.browser.new_page(java_script_enabled=False)
            try:
                static.goto(url)
                self.assertEqual(static.locator('.lookup-worksheet h3').count(), count)
                self.assertFalse(static.locator('button[type=submit]').first.is_visible())
                static.locator('.lookup-worksheet summary').first.click()
                static.locator('.lookup-worksheet details summary').first.click()
                self.assertTrue(static.locator('.lookup-worksheet details p').first.is_visible())
            finally:
                static.close()
