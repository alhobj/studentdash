"""Challenge coverage, independent numerical benchmarks and offline browser behaviour."""
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'resources'


class ChallengeContentTests(unittest.TestCase):
    def test_coverage_and_independent_calculations(self):
        maths = {r['code']: r for r in json.loads((ROOT/'ib-math-ai-sl/challenges.json').read_text(encoding='utf-8'))}
        chemistry = {r['code']: r for r in json.loads((ROOT/'ib-chemistry/challenges.json').read_text(encoding='utf-8'))}
        self.assertEqual(set(maths), {r['code'] for r in json.loads((ROOT/'ib-math-ai-sl/coverage.json').read_text(encoding='utf-8'))})
        self.assertEqual(set(chemistry), {r['id'] for r in json.loads((ROOT/'ib-chemistry/practice-syllabus.json').read_text(encoding='utf-8'))['topics']})
        balance = 10000
        for _ in range(36): balance = balance * 1.005 - 300
        self.assertAlmostEqual(maths['1.7']['parts'][1]['answer'], balance * 1.005, places=8)
        self.assertIn('166.80', maths['1.7']['parts'][1]['working'])
        self.assertAlmostEqual(maths['4.8']['parts'][0]['answer'], sum(math.comb(8,k)*.25**k*.75**(8-k) for k in range(2,9)))
        self.assertEqual(maths['4.2']['parts'][1]['answer'], 28.75)
        x=maths['5.7']['parts'][0]['answer']
        self.assertAlmostEqual(12*x*x-128*x+240, 0)
        self.assertGreater(x, 0); self.assertLess(x, 6)
        self.assertEqual(chemistry['R1.1']['parts'][1]['answer'], -56.16)
        self.assertEqual(chemistry['R2.1']['parts'][1]['answer'], 8)
        self.assertAlmostEqual(chemistry['R2.3']['parts'][1]['answer']/(1.2-chemistry['R2.3']['parts'][1]['answer']), .25)
        self.assertEqual(chemistry['R3.1']['parts'][1]['answer'], .8)


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class ChallengeBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime=sync_playwright().start()
        self.addCleanup(runtime.stop)
        self.browser=runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER','msedge' if os.name=='nt' else 'chromium'),headless=True)
        self.addCleanup(self.browser.close)
        self.page=self.browser.new_page()
        self.errors=[]
        self.page.on('pageerror', lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def test_all_pages_links_mobile_and_answer_wiring(self):
        count=0
        for profile in ['ib-math-ai-sl','ib-chemistry']:
            root=ROOT/profile
            for file in root.glob('challenges*.html'):
                self.page.goto(file.as_uri())
                for width in [320,1100]:
                    self.page.set_viewport_size({'width':width,'height':900})
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'),file.name)
                self.assertEqual(self.page.evaluate('''() => { const ids=[...document.querySelectorAll('[id]')].map(e=>e.id); return ids.length-new Set(ids).size; }'''),0)
                for href in self.page.locator('a[href]').evaluate_all('(a)=>a.map(e=>e.getAttribute("href"))'):
                    name,_,anchor=href.partition('#')
                    target=root/(name or file.name)
                    self.assertTrue(target.exists(),href)
                    if anchor:self.assertIn(f'id="{anchor}"',target.read_text(encoding='utf-8'))
                for form in self.page.locator('.challenge-part').all():
                    count+=1
                    form.locator('input').fill(form.get_attribute('data-answer'))
                    form.locator('button').click()
                    self.assertIn('Numerical answer accepted',form.locator('.feedback').inner_text())
        self.assertEqual(count,122)

    def test_retry_zero_negative_reset_and_static_solutions(self):
        self.page.goto((ROOT/'ib-chemistry/challenges-r3.html').as_uri())
        section=self.page.locator('[id="challenge-R3.3"]')
        form=section.locator('form').nth(1)
        field=form.locator('input')
        field.press('Enter')
        self.assertIn('Enter a finite number',form.locator('.feedback').inner_text())
        field.fill('0.01');field.press('Enter')
        self.assertIn('Not yet',form.locator('.feedback').inner_text())
        field.fill('0');field.press('Enter')
        self.assertIn('accepted',form.locator('.feedback').inner_text())
        section.locator('textarea').fill('Radicals are regenerated during propagation.')
        section.locator('summary').first.click()
        section.locator('.challenge-reset').click()
        self.assertEqual(field.input_value(),'')
        self.assertEqual(section.locator('textarea').input_value(),'')
        self.assertFalse(section.locator('details').first.evaluate('(e)=>e.open'))
        field=self.page.locator('[id="challenge-R3.4-part-2"]')
        field.fill('-1');field.press('Enter')
        self.assertIn('accepted',self.page.locator('[id="challenge-R3.4-part-2-feedback"]').inner_text())
        context=self.browser.new_context(java_script_enabled=False)
        self.addCleanup(context.close)
        page=context.new_page()
        page.goto((ROOT/'ib-chemistry/challenges-r1.html').as_uri())
        self.assertIn('AHL',page.locator('[id="challenge-R1.4"] .eyebrow').inner_text())
        page.locator('[id="challenge-R1.4"]').get_by_text('Worked solution',exact=True).first.click()
        self.assertTrue(page.get_by_text('ΔS=0.120 kJ mol⁻¹ K⁻¹, so T=40.0/0.120≈333.333 K.').is_visible())
