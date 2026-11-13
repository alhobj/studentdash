"""Offline navigation and formative feedback for both resource collections."""
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'resources'


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class SupportResourceTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime=sync_playwright().start()
        self.addCleanup(runtime.stop)
        self.browser=runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER','msedge' if os.name=='nt' else 'chromium'),headless=True)
        self.addCleanup(self.browser.close)
        self.page=self.browser.new_page()
        self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors,[])

    def test_specific_feedback_and_explanation_aware_routes(self):
        for profile in ['ib-math-ai-sl','ib-chemistry']:
            root=ROOT/profile
            self.page.goto((root/'readiness.html').as_uri())
            checks=json.loads((root/'readiness.json').read_text(encoding='utf-8'))
            self.assertEqual(len(checks),8)
            for check in checks:
                section=self.page.locator('#'+check['id'])
                control=section.locator('input')
                control.press('Enter')
                self.assertIn('Enter a number',section.locator('.feedback').inner_text())
                for mistake in check['mistakes']:
                    control.fill(str(mistake['value']));control.press('Enter')
                    self.assertEqual(section.locator('.feedback').inner_text(),mistake['feedback'])
                    self.assertEqual(section.locator('.recommendation a').get_attribute('href'),check['prior'])
                control.fill(str(check['answer']));control.press('Enter')
                self.assertEqual(section.locator('.recommendation a').get_attribute('href'),check['challenge'])
                section.locator('.ready-working summary').click()
                control.press('Enter')
                self.assertEqual(section.locator('.recommendation a').get_attribute('href'),check['basic'])
                section.locator('.readiness-reset').click()
                self.assertEqual(control.input_value(),'')
                self.assertEqual(section.locator('.recommendation').inner_text(),'')
                control.fill(str(check['answer']));control.press('Enter')
                self.assertEqual(section.locator('.recommendation a').get_attribute('href'),check['challenge'])

    def test_search_level_filter_empty_state_and_links(self):
        for profile,code,total in [('ib-math-ai-sl','3.4',39),('ib-chemistry','S.1.4',22)]:
            root=ROOT/profile
            self.page.goto((root/'find-practice.html').as_uri())
            self.assertEqual(self.page.locator('[data-find]:visible').count(),total)
            self.page.locator('#practice-search').fill(code)
            self.assertEqual(self.page.locator('[data-find]:visible').count(),1)
            self.page.locator('#practice-level').select_option('challenge')
            self.assertEqual(self.page.locator('[data-find]:visible a:visible').count(),1)
            self.page.locator('#practice-search').fill('not-a-real-topic')
            self.assertTrue(self.page.locator('#finder-empty').is_visible())
            self.page.locator('#finder-reset').click()
            self.assertEqual(self.page.locator('[data-find]:visible').count(),total)
            for name in ['find-practice.html','readiness.html']:
                self.page.goto((root/name).as_uri())
                for width in [320,1100]:
                    self.page.set_viewport_size({'width':width,'height':900})
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                self.assertEqual(self.page.evaluate('''() => {const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length-new Set(ids).size;}'''),0)
                for href in self.page.locator('a[href]').evaluate_all('(a)=>a.map(e=>e.getAttribute("href"))'):
                    file,_,anchor=href.partition('#')
                    target=root/(file or name)
                    self.assertTrue(target.exists(),href)
                    if anchor:self.assertIn(f'id="{anchor}"',target.read_text(encoding='utf-8'))

    def test_support_without_javascript(self):
        context=self.browser.new_context(java_script_enabled=False)
        self.addCleanup(context.close)
        page=context.new_page()
        page.goto((ROOT/'ib-chemistry/find-practice.html').as_uri())
        self.assertEqual(page.locator('[data-find]:visible').count(),22)
        self.assertFalse(page.locator('.finder-controls').is_visible())
        page.goto((ROOT/'ib-math-ai-sl/readiness.html').as_uri())
        page.locator('#percent .ready-working summary').click()
        self.assertTrue(page.get_by_text('Increase = 0.15 × 40 = 6; new price = 40 + 6 = 46.').is_visible())
