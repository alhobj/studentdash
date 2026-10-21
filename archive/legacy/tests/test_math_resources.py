"""Offline browser checks for original Mathematics AI SL teaching examples."""
import importlib.util
import json
import os
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class MathResourceTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        runtime = sync_playwright().start()
        self.addCleanup(runtime.stop)
        browser = runtime.chromium.launch(channel=os.environ.get('STUDENTDASH_TEST_BROWSER', 'msedge' if os.name == 'nt' else 'chromium'), headless=True)
        self.addCleanup(browser.close)
        self.page = browser.new_page()
        self.root = Path(__file__).resolve().parents[1] / 'resources/ib-math-ai-sl'
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def topic(self, n):
        self.page.goto((self.root / f'topic-{n}.html').as_uri())

    def slider(self, selector, value):
        self.page.locator(selector).evaluate('(e,v)=>{e.value=v;e.dispatchEvent(new Event("input"));}', value)

    def result(self, key):
        return self.page.locator('#'+key+' .result').inner_text()

    def test_offline_hub_topics_mobile_and_unique_ids(self):
        self.page.goto((self.root / 'math-practice.html').as_uri())
        self.assertEqual(self.page.locator('.card').count(), 5)
        total = 0
        for n in range(1, 6):
            self.topic(n)
            total += self.page.locator('[data-math]').count()
            for width in [320, 1100]:
                self.page.set_viewport_size({'width': width, 'height': 900})
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            self.assertEqual(self.page.evaluate('''() => {
                const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
                return ids.length-new Set(ids).size;
            }'''), 0)
            for link in self.page.locator('nav[aria-label=Activities] a').all():
                self.assertTrue(self.page.locator(link.get_attribute('href')).is_visible())
        self.assertEqual(total, 44)

    def test_coverage_links_and_all_control_extremes(self):
        coverage = json.loads((self.root / 'coverage.json').read_text(encoding='utf-8'))
        self.assertEqual(len(coverage), 39)
        for filename in ['math-practice.html', 'coverage.html', 'investigations.html', 'prior-learning.html'] + [f'{prefix}-{n}.html' for prefix in ['topic', 'basics'] for n in range(1, 6)]:
            self.page.goto((self.root / filename).as_uri())
            for href in self.page.locator('a[href]').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))'):
                if href.startswith('https:'):
                    continue
                file, _, anchor = href.partition('#')
                target = self.root / (file or filename)
                self.assertTrue(target.exists(), href)
                if anchor:
                    self.assertIn(f'id="{anchor}"', target.read_text(encoding='utf-8'), href)
        for n in range(1, 6):
            self.topic(n)
            for section in self.page.locator('[data-math]').all():
                for control in section.locator('input[type=range]').all():
                    for attr in ['min', 'max']:
                        control.evaluate('(e,a)=>{e.value=e[a];e.dispatchEvent(new Event("input"));}', attr)
                        self.assertNotRegex(section.locator('.result').inner_text(), r'NaN|Infinity|undefined')
                for select in section.locator('select').all():
                    for value in select.locator('option').evaluate_all('(options)=>options.map(o=>o.value)'):
                        select.select_option(value)
                        self.assertNotRegex(section.locator('.result').inner_text(), r'NaN|Infinity|undefined')
                section.locator('button[id$="-reset"]').click()

    def test_foundation_feedback_hints_keyboard_and_reset(self):
        self.page.goto((self.root / 'prior-learning.html').as_uri())
        first = self.page.locator('#signed-step-1')
        first.press('Enter')
        self.assertIn('Enter a number first', self.page.locator('#signed-step-1-feedback').inner_text())
        first.fill('4')
        first.press('Enter')
        self.assertEqual(first.get_attribute('aria-invalid'), 'true')
        self.assertIn('Not quite yet', self.page.locator('#signed-step-1-feedback').inner_text())
        self.page.locator('#signed .hint summary').first.click()
        self.assertTrue(self.page.locator('#signed .hint').first.evaluate('(e)=>e.open'))
        first.fill('5')
        self.assertEqual(self.page.locator('#signed-step-1-feedback').inner_text(), '')
        first.press('Enter')
        self.assertIn('That’s right', self.page.locator('#signed-step-1-feedback').inner_text())
        self.page.locator('#signed .foundation-reset').click()
        self.assertEqual(first.input_value(), '')
        self.assertIsNone(first.get_attribute('aria-invalid'))
        self.assertFalse(self.page.locator('#signed .hint').first.evaluate('(e)=>e.open'))
        for name, field, answer in [('prior-learning.html','fractions-step-2','.75'),
                                   ('basics-1.html','basic-1.7-step-2','82'),
                                   ('basics-3.html','basic-3.2-step-2','30'),
                                   ('basics-4.html','basic-4.10-step-2','2.5'),
                                   ('basics-5.html','basic-5.4-step-2','-.5')]:
            self.page.goto((self.root / name).as_uri())
            control = self.page.locator(f'[id="{field}"]')
            control.fill(answer)
            control.press('Enter')
            self.assertIn('That’s right', self.page.locator(f'[id="{field}-feedback"]').inner_text())

    def test_foundations_coverage_mobile_and_no_javascript(self):
        data = json.loads((self.root / 'foundations.json').read_text(encoding='utf-8'))
        coverage = json.loads((self.root / 'coverage.json').read_text(encoding='utf-8'))
        self.assertEqual({c['code'] for c in data['sections']}, {c['code'] for c in coverage})
        total = 0
        for name in ['prior-learning.html'] + [f'basics-{n}.html' for n in range(1,6)]:
            self.page.goto((self.root / name).as_uri())
            total += self.page.locator('.foundation-step').count()
            self.page.set_viewport_size({'width':320,'height':900})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            self.assertEqual(self.page.evaluate('''() => {
                const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
                return ids.length-new Set(ids).size;
            }'''), 0)
        self.assertEqual(total, 102)
        context = self.page.context.browser.new_context(java_script_enabled=False)
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto((self.root / 'prior-learning.html').as_uri())
        page.locator('#signed .hint summary').first.click()
        self.assertTrue(page.get_by_text('Start at −3 and move 8 places right.').is_visible())

    def test_extended_models_and_statistical_decisions(self):
        self.topic(3)
        self.assertIn('total=100', self.result('voronoi-regions'))
        self.assertIn('Triple vertex (5, 4.25)', self.result('voronoi-regions'))
        self.page.locator('#voronoi-regions-sites').select_option('two')
        self.assertIn('A=50; B=50', self.result('voronoi-regions'))
        self.topic(4)
        self.slider('#chi-square-shift', 10)
        self.assertIn('χ²=20', self.result('chi-square'))
        self.assertIn('Reject H₀', self.result('chi-square'))
        self.page.locator('#chi-square-test').select_option('fit')
        self.assertIn('χ²=10', self.result('chi-square'))
        self.slider('#t-test-difference', 0)
        self.assertIn('p≈1', self.result('t-test'))
        self.page.locator('#t-test-tail').select_option('greater')
        self.assertIn('p≈0.5', self.result('t-test'))
        self.slider('#t-test-sa', 5); self.slider('#t-test-sb', 5)
        self.slider('#t-test-difference', 5)
        # t=sqrt(5), df=18; benchmark from the regularized incomplete beta integral.
        import re
        p = float(re.search(r'p≈(\d+(?:\.\d+)?(?:e[+-]?\d+)?)', self.result('t-test')).group(1))
        self.assertAlmostEqual(p, 0.0191248, places=6)
        self.slider('#inverse-normal-mean', 50); self.slider('#inverse-normal-sd', 10)
        self.slider('#inverse-normal-percent', 90)
        self.assertIn('62.8155', self.result('inverse-normal'))
        self.assertIn('outliers: 20', self.result('box-transform'))
        self.slider('#binomial-n', 3); self.slider('#binomial-k', 2)
        self.assertIn('P(X ≥ 2) = 0.5', self.result('binomial'))

    def test_growth_loan_and_function_models(self):
        self.topic(1)
        self.assertIn('Total deposited: 325', self.result('sequences'))
        self.slider('#interest-years', 2)
        self.assertIn('Compound balance: 1102.5', self.result('interest'))
        self.page.locator('#loan-step').click()
        self.assertIn('Balance: 4825.00', self.result('loan'))
        self.slider('#loan-payment', 10)
        self.assertIn('debt will not fall', self.result('loan'))
        self.assertIn('Month 0', self.result('loan'))
        self.topic(2)
        self.slider('#line-m', 2); self.slider('#line-b', 3)
        self.assertIn('Exact fit reached', self.result('line'))
        self.slider('#quadratic-h', 3); self.slider('#quadratic-k', 4)
        self.assertIn('Vertex (3, 4)', self.result('quadratic'))

    def test_geometry_statistics_and_probability(self):
        self.topic(3)
        self.slider('#triangle-angle', 45)
        self.assertIn('Total height = 21.5 m', self.result('triangle'))
        self.assertIn('Tie: on the boundary', self.result('voronoi'))
        self.topic(4)
        self.assertIn('mean = 7; median = 4', self.result('statistics'))
        self.page.locator('#statistics-data').fill('1,,2')
        self.assertEqual(self.page.locator('#statistics-data').get_attribute('aria-invalid'), 'true')
        self.page.locator('#statistics-reset').click()
        self.assertIsNone(self.page.locator('#statistics-data').get_attribute('aria-invalid'))
        self.assertIn('Pearson r = 1', self.result('regression'))
        self.slider('#binomial-n', 3); self.slider('#binomial-k', 2)
        self.assertIn('P(X = 2) = 0.375', self.result('binomial'))
        self.slider('#binomial-p', 1)
        self.page.locator('#binomial-simulate').click()
        self.assertIn('observed mean = 3', self.result('binomial'))
        self.slider('#normal-cutoff', 50)
        self.assertIn('0.500000', self.result('normal'))

    def test_calculus_and_answer_feedback(self):
        self.topic(5)
        self.slider('#trapezoids-n', 1)
        self.assertIn('Estimate = 36', self.result('trapezoids'))
        self.slider('#tangent-h', .01)
        self.assertIn('Secant slope = 2.01', self.result('tangent'))
        self.slider('#optimization-width', 10)
        self.assertIn('Maximum reached: 200', self.result('optimization'))
        for topic, key, answer in [(1,'sequences','325'),(2,'line','19'),(3,'triangle','21.5'),(4,'binomial','0.375'),(5,'trapezoids','36')]:
            self.topic(topic)
            section=self.page.locator('#'+key)
            section.locator('.check').click()
            self.assertIn('finite numerical answer', section.locator('.feedback').inner_text())
            section.locator('.answer').fill('-100')
            section.locator('.check').click()
            self.assertIn('Not yet', section.locator('.feedback').inner_text())
            section.locator('.answer').fill(answer)
            section.locator('.check').click()
            self.assertTrue(section.locator('.feedback').inner_text().startswith('Correct.'))


if __name__ == '__main__':
    unittest.main()
