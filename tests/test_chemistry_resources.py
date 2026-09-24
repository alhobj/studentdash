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

    def test_bonding_conduction_in_different_states(self):
        for material, state, kind, conducts in [
            ('salt', 'solid', 'ionic', 'no'), ('salt', 'liquid', 'ionic', 'yes'),
            ('copper', 'solid', 'metallic', 'yes'), ('copper', 'liquid', 'metallic', 'yes'),
            ('water', 'liquid', 'covalent', 'no'), ('diamond', 'solid', 'covalent', 'no'),
            ('graphite', 'solid', 'covalent', 'yes')]:
            self.page.select_option('#bond-material', material)
            self.page.select_option('#bond-state', state)
            self.page.select_option('#bond-type', kind)
            self.page.select_option('#bond-conduction', conducts)
            self.page.locator('#bond-check').click()
            self.assertTrue(self.page.locator('#bond-feedback').inner_text().startswith('Correct.'))
        self.assertIsNotNone(self.page.locator('#bond-state option[value="liquid"]').get_attribute('disabled'))

    def test_nuclear_counts_ions_and_isotope_mean(self):
        for index, expected in [(0, [6, 6, 6]), (1, [6, 8, 6]), (2, [11, 12, 10]),
                                (3, [17, 18, 18]), (4, [12, 12, 10])]:
            self.page.select_option('#atom-species', str(index))
            for key, value in zip(['protons', 'neutrons', 'electrons'], expected):
                self.page.locator('#atom-' + key).fill(str(value))
            self.page.locator('#atom-check').click()
            self.assertTrue(self.page.locator('#atom-feedback').inner_text().startswith('Correct.'))
        self.page.locator('#atom-neutrons').fill('1.5')
        self.page.locator('#atom-check').click()
        self.assertIn('whole numbers', self.page.locator('#atom-feedback').inner_text())
        for percent, expected in [(0, 12), (25, 12.25), (100, 13)]:
            self.assertEqual(self.page.evaluate('isotopeMean', percent), expected)

    def test_electron_configurations_exceptions_and_orbital_pairing(self):
        for index, config in [(0, '1s2 2s2 2p3'), (1, '[He] 2s2 2p4'), (2, '[Ne]'),
                              (3, '[Ar]'), (4, '[Ar] 4s2'), (5, '[Ar] 4s1 3d5'),
                              (6, '[Ar] 3d10 4s1'), (7, '[Ar] 3d6 4s2'),
                              (8, '[Ar] 3d6'), (9, '[Ar] 3d5')]:
            self.page.select_option('#electron-species', str(index))
            self.page.locator('#electron-answer').fill(config)
            self.page.locator('#electron-check').click()
            self.assertTrue(self.page.locator('#electron-feedback').inner_text().startswith('Correct.'))
            self.page.locator('#electron-reveal').click()
            self.assertTrue(self.page.locator('#electron-orbitals').is_visible())
        self.page.select_option('#electron-species', '8')
        self.page.locator('#electron-answer').fill('[Ar] 3d5 4s1')
        self.page.locator('#electron-check').click()
        self.assertIn('Not yet', self.page.locator('#electron-feedback').inner_text())
        for bad in ['', '[Ne] 2p6', '2p7', '1s2 garbage', '3d0', '1p2']:
            self.assertIsNone(self.page.evaluate('parseConfiguration', bad))
        self.assertEqual(self.page.evaluate("parseConfiguration('[He] 2s² 2p^3')"),
                         {'1s': 2, '2s': 2, '2p': 3})
        self.assertEqual(self.page.evaluate('orbitalSpins(3,3)'), ['↑', '↑', '↑'])
        self.assertEqual(self.page.evaluate('orbitalSpins(4,3)'), ['↑↓', '↑', '↑'])

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
