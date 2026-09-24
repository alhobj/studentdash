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

    def test_ten_new_activities_and_numerical_challenges(self):
        self.assertEqual(self.page.locator('section[data-new-activity]').count(), 10)
        answers = {'mole-mass': '0.100', 'mole-entities': '3.011e23',
                   'gas-pressure': '99.77', 'gas-change': '2.00', 'gas-molar-mass': '29.93'}
        for key, answer in answers.items():
            self.page.locator('#' + key + '-check').click()
            self.assertIn('Enter a non-negative', self.page.locator('#' + key + '-feedback').inner_text())
            self.page.locator('#' + key + '-answer').fill('1')
            self.page.locator('#' + key + '-check').click()
            self.assertTrue(self.page.locator('#' + key + '-feedback').inner_text().startswith('Try again.'))
            self.page.locator('#' + key + '-answer').fill(answer)
            self.page.locator('#' + key + '-check').click()
            self.assertTrue(self.page.locator('#' + key + '-feedback').inner_text().startswith('Correct.'))

    def test_gas_units_proportionality_and_invalid_controls(self):
        self.assertAlmostEqual(self.page.evaluate('idealPressure(1, 0, 22.71)'), 100, delta=0.01)
        self.assertAlmostEqual(self.page.evaluate('idealPressure(0.1, 26.85, 2)'), 124.71)
        self.assertAlmostEqual(self.page.evaluate('changedVolume(2,100,200,300,450)'), 1.5)
        self.assertAlmostEqual(self.page.evaluate('gasMolarMass(0.88,100,0.5,300)'), 43.89792)
        for control, value, result in [('gas-pressure-temperature', '-273.15', 'gas-pressure'),
                                        ('gas-pressure-volume', '0', 'gas-pressure'),
                                        ('mole-mass-molar', '', 'mole-mass'),
                                        ('mole-entities-atoms', '2.5', 'mole-entities'),
                                        ('gas-change-t1', '0', 'gas-change'),
                                        ('gas-molar-mass-pressure', '-1', 'gas-molar-mass')]:
            self.page.locator('#' + control).fill(value)
            self.assertIn('Enter a valid', self.page.locator('#' + result + '-result').inner_text())
            self.page.locator('#' + result + '-reset').click()
            self.assertNotIn('Enter a valid', self.page.locator('#' + result + '-result').inner_text())
        self.assertAlmostEqual(self.page.evaluate('particleCounts(0.5,3).atoms'), 9.03321114e23)

    def test_empirical_ratios_must_be_whole_and_simplest(self):
        for index, ratio, formula in [('0', '1:3', 'CH₃'), ('1', '2:3', 'Fe₂O₃'),
                                      ('2', '1:2:1', 'CH₂O')]:
            self.page.select_option('#empirical-sample', index)
            self.page.locator('#empirical-answer').fill(ratio)
            self.page.locator('#empirical-check').click()
            self.assertIn(formula, self.page.locator('#empirical-feedback').inner_text())
            self.page.locator('#empirical-reveal').click()
            self.assertIn(formula, self.page.locator('#empirical-working').inner_text())
        self.page.locator('#empirical-answer').fill('2:4:2')
        self.page.locator('#empirical-check').click()
        self.assertIn('simplest', self.page.locator('#empirical-feedback').inner_text())
        self.page.locator('#empirical-answer').fill('1:1.5:1')
        self.page.locator('#empirical-check').click()
        self.assertIn('positive whole numbers', self.page.locator('#empirical-feedback').inner_text())

    def test_triangle_and_alloy_models(self):
        position = self.page.evaluate('trianglePosition(1,3)')
        self.assertEqual(position, {'mean': 2, 'difference': 2, 'x': 230, 'y': 170})
        self.assertEqual(position, self.page.evaluate('trianglePosition(3,1)'))
        for a, b in [(0, 0), (4, 4), (0, 4), (4, 0)]:
            pos = self.page.evaluate('([a,b])=>trianglePosition(a,b)', [a, b])
            self.assertTrue(50 <= pos['x'] <= 410)
            self.assertTrue(50 <= pos['y'] <= 290)
        for key, answer in [('triangle', 'metallic'), ('alloy', 'obstruct')]:
            self.page.select_option('#' + key + '-answer', answer)
            self.page.locator('#' + key + '-check').click()
            self.assertTrue(self.page.locator('#' + key + '-feedback').inner_text().startswith('Correct.'))
        self.page.locator('#alloy-shear').click()
        self.assertIn('upper row slides', self.page.locator('#alloy-result').inner_text())
        for kind in ['substitutional', 'interstitial']:
            self.page.select_option('#alloy-kind', kind)
            self.page.locator('#alloy-shear').click()
            self.assertIn('moves less', self.page.locator('#alloy-result').inner_text())
        self.assertEqual(self.page.locator('#alloy-svg circle').count(), 20)

    def test_polymer_side_groups_linkages_and_water_count(self):
        for monomer, group in [('ethene', 'CH₂–CH₂'), ('propene', 'CH(CH₃)'), ('chloroethene', 'CHCl')]:
            self.page.select_option('#addition-monomer', monomer)
            self.page.select_option('#addition-answer', monomer)
            self.page.locator('#addition-check').click()
            self.assertTrue(self.page.locator('#addition-feedback').inner_text().startswith('Correct.'))
            self.page.locator('#addition-reveal').click()
            self.assertIn(group, self.page.locator('#addition-chain').inner_text())
            self.assertNotIn('=', self.page.locator('#addition-chain').inner_text())
        for kind in ['ester', 'amide']:
            self.page.select_option('#condensation-kind', kind)
            self.page.select_option('#condensation-answer', kind)
            self.page.locator('#condensation-check').click()
            self.assertTrue(self.page.locator('#condensation-feedback').inner_text().startswith('Correct.'))
            self.page.locator('#condensation-reveal').click()
            self.assertIn('H₂O', self.page.locator('#condensation-link').inner_text())
        self.assertEqual(self.page.evaluate('condensationLinks(2)'), 1)
        self.assertEqual(self.page.evaluate('condensationLinks(10)'), 9)


if __name__ == '__main__':
    unittest.main()
