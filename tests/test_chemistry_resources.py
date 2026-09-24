"""Offline resource checks with invented numerical examples only."""
import importlib.util
import os
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec('playwright'), 'Requires optional Playwright')
class ChemistryResourceTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        self.runtime = sync_playwright().start()
        self.addCleanup(self.runtime.stop)
        self.browser = self.runtime.chromium.launch(
            channel=os.environ.get('STUDENTDASH_TEST_BROWSER', 'msedge' if os.name == 'nt' else 'chromium'),
            headless=True)
        self.addCleanup(self.browser.close)
        self.page = self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto((Path(__file__).resolve().parents[1] / 'resources/ib-chemistry/practice.html').as_uri())

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def test_stoichiometry_conserves_atoms_and_handles_zero_and_exact_ratio(self):
        for h, o in [(4, 3), (10, 1), (4, 2), (0, 3), (0, 0)]:
            result = self.page.evaluate('([h,o]) => stoichiometry(h,o)', [h, o])
            self.assertAlmostEqual(result['h'] + result['water'], h)
            self.assertAlmostEqual(result['o'] + result['water'] / 2, o)
            self.assertGreaterEqual(result['h'], 0)
            self.assertGreaterEqual(result['o'], 0)
        self.page.locator('#stoich-answer').fill('3')
        self.page.locator('#stoich-check').click()
        self.assertTrue(self.page.locator('#stoich-feedback').inner_text().startswith('Correct.'))

    def test_dilution_units_and_invalid_inputs(self):
        self.assertIn('0.005 mol', self.page.locator('#dilution-result').inner_text())
        self.assertIn('0.05 mol', self.page.locator('#dilution-result').inner_text())
        self.page.locator('#initial-volume').fill('')
        self.assertIn('Enter a concentration', self.page.locator('#dilution-result').inner_text())
        self.page.locator('#dilution-check').click()
        self.assertIn('Enter a non-negative', self.page.locator('#dilution-feedback').inner_text())
        self.page.locator('#dilution-answer').fill('0.0200')
        self.page.locator('#dilution-check').click()
        self.assertTrue(self.page.locator('#dilution-feedback').inner_text().startswith('Correct.'))

    def test_equilibrium_directions_and_validation(self):
        for hi, direction in [('0', 'forward'), ('1', 'forward'), ('2', 'equal'), ('3', 'reverse')]:
            self.page.locator('#eq-hi').fill(hi)
            self.page.select_option('#eq-prediction', direction)
            self.page.locator('#eq-check').click()
            self.assertTrue(self.page.locator('#eq-feedback').inner_text().startswith('Correct.'))
        self.page.locator('#eq-h').fill('0')
        self.page.locator('#eq-check').click()
        self.assertIn('Correct the numerical inputs', self.page.locator('#eq-feedback').inner_text())
        self.assertTrue(self.page.locator('#eq-marker').is_hidden())

    def test_offline_navigation_mobile_and_print(self):
        for width in (320, 390, 1440):
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        for link in self.page.locator('nav a').all():
            link.click()
            self.assertTrue(self.page.locator(link.get_attribute('href')).is_visible())
        self.page.emulate_media(media='print')
        self.assertTrue(self.page.locator('nav').is_hidden())
        self.assertTrue(self.page.locator('#dilution').is_visible())


if __name__ == '__main__':
    unittest.main()
