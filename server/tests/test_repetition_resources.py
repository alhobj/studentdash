"""Same-method question sets: coverage, switching and answer isolation."""
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/'resources'


class RepetitionContentTests(unittest.TestCase):
    def test_complete_banks_and_known_answers(self):
        for profile,count in [('ib-math-ai-sl',51),('ib-chemistry',34)]:
            root=ROOT/profile
            lessons=json.loads((root/'foundations.json').read_text(encoding='utf-8'))
            banks=json.loads((root/'repetition.json').read_text(encoding='utf-8'))
            self.assertEqual(set(banks),{c.get('code',c.get('id')) for group in lessons.values() for c in group})
            self.assertEqual(len(banks),count)
            self.assertTrue(all(len(b['questions'])>=6 for b in banks.values()))
        maths=json.loads((ROOT/'ib-math-ai-sl/repetition.json').read_text(encoding='utf-8'))
        chemistry=json.loads((ROOT/'ib-chemistry/repetition.json').read_text(encoding='utf-8'))
        self.assertEqual([q['answer'] for q in maths['4.6']['questions']],[.6,.5,.25,.75,.8,.4])
        self.assertEqual([q['answer'] for q in maths['4.10']['questions']],[2.5,1.5,3.5,2.5,2.5,1.5])
        self.assertEqual([q['answer'] for q in chemistry['S1.4']['questions'][:6]],[.1,.2,.5,3,.3,4])
        self.assertEqual([q['answer'] for q in chemistry['S1.2']['questions'][:6]],[8,12,12,18,20,14])


@unittest.skipUnless(importlib.util.find_spec('playwright'),'Requires optional Playwright')
class RepetitionBrowserTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime=sync_playwright().start();self.addCleanup(runtime.stop)
        self.browser=runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER','msedge' if os.name=='nt' else 'chromium'),headless=True)
        self.addCleanup(self.browser.close)
        self.page=self.browser.new_page()
        self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):self.assertEqual(self.errors,[])

    def test_every_variant_and_mobile_layout(self):
        total=0
        for profile in ['ib-math-ai-sl','ib-chemistry']:
            root=ROOT/profile
            for file in [root/'prior-learning.html',*root.glob('basics-*.html')]:
                self.page.goto(file.as_uri())
                self.page.set_viewport_size({'width':320,'height':900})
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                for host in self.page.locator('[data-similar]').all():
                    bank=json.loads(host.get_attribute('data-similar'))
                    for i,q in enumerate(bank['questions']):
                        self.assertEqual(host.locator('form label').inner_text(),q['prompt'])
                        self.assertEqual(host.locator('.similar-hint p').text_content(),q['hint'])
                        self.assertEqual(host.locator('.similar-working p').text_content(),q['working'])
                        control=host.locator('input')
                        self.assertEqual(control.input_value(),'')
                        answer=q['answer'][0] if isinstance(q['answer'],list) else str(q['answer'])
                        control.fill(answer);control.press('Enter')
                        self.assertIn('That’s right',host.locator('.similar-feedback').inner_text())
                        self.assertEqual(host.locator('.similar-next').inner_text(),'Repeat this set' if i==len(bank['questions'])-1 else 'Another like this')
                        host.locator('.similar-next').click();total+=1
                    self.assertEqual(host.locator('.similar-position').inner_text(),f"Question 1 of {len(json.loads(host.get_attribute('data-similar'))['questions'])}")
                    self.assertTrue(host.locator('.similar-previous').is_disabled())
        self.assertEqual(total,542)

    def test_retry_previous_reset_and_offline_worksheet(self):
        self.page.goto((ROOT/'ib-math-ai-sl/basics-1.html').as_uri())
        lesson=self.page.locator('[id="basic-1.4"]');host=lesson.locator('[data-similar]')
        control=host.locator('input')
        control.press('Enter');self.assertIn('Enter a number',host.locator('.feedback').inner_text())
        control.fill('100');control.press('Enter');self.assertEqual(control.get_attribute('aria-invalid'),'true')
        control.fill('105');control.press('Enter');self.assertIn('That’s right',host.locator('.feedback').inner_text())
        host.locator('.similar-hint summary').click()
        host.locator('.similar-next').click()
        self.assertEqual(control.input_value(),'')
        self.assertIsNone(control.get_attribute('aria-invalid'))
        self.assertFalse(host.locator('.similar-hint').evaluate('(e)=>e.open'))
        host.locator('.similar-previous').click()
        self.assertIn('100 earns 5%',host.locator('form label').inner_text())
        host.locator('.similar-next').click();lesson.locator('.foundation-reset').click()
        self.assertEqual(host.locator('.similar-position').inner_text(),f"Question 1 of {len(json.loads(host.get_attribute('data-similar'))['questions'])}")
        context=self.browser.new_context(java_script_enabled=False);self.addCleanup(context.close)
        page=context.new_page();page.goto((ROOT/'ib-chemistry/basics-s1.html').as_uri())
        worksheet=page.locator('[id="basic-S1.4"] .similar-worksheet')
        worksheet.locator('summary').first.click()
        self.assertEqual(worksheet.locator('h4:visible').count(),8)
        worksheet.locator('details summary').first.click()
        self.assertTrue(worksheet.get_by_text('n = 4 ÷ 40 = 0.1 mol.').is_visible())
