"""Fictional source rows only; no original exam text in fixtures."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.import_chem_exam_bank import ROOT, SafeMarkup, build


class ExamBankTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'output').mkdir(exist_ok=True)

    def test_safe_markup(self):
        parser = SafeMarkup()
        html = parser.finish('<p onclick="bad()">X<sub>2</sub><script>bad()</script>'
                             '<img src="https://example.invalid/pixel"><math><msup><mi>x</mi><mn>2</mn></msup></math>')
        self.assertNotIn('<script', html)
        self.assertNotIn('onclick', html)
        self.assertNotIn('https:', html)
        self.assertIn('<sub>2</sub>', html)
        self.assertIn('<msup>', html)
        self.assertIn('Missing, external or incomplete diagram', parser.issues)
        self.assertTrue(html.endswith('</p>'))

    def test_import_preserves_rows_and_provenance(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as folder:
            source = Path(folder)/'fictional.xlsx'
            source.write_bytes(b'fictional source stand-in')
            row = {'URL number': '17', 'Question': '<p>A fictional prompt</p>',
                   'Markscheme': 'A', 'Paper': 2, 'Level': 'Example',
                   'Syllabus section': 'Old topic', 'Question part': "[['a'], ['b']]",
                   'Specification': 'x'*32767, 'Year': '=MID(E2,1,2)',
                   '_sheet': 'Source', '_row': 2}
            destination = Path(folder)/'bank'
            with patch('tools.import_chem_exam_bank.inspect', return_value=[row]):
                report = build([source], destination)
            bank = json.loads((destination/'bank.json').read_text(encoding='utf-8'))
            record = bank['questions'][0]
            self.assertEqual(record['raw'], row)
            self.assertEqual(record['current_curriculum_status'], 'unreviewed')
            self.assertEqual(report['records'], 1)
            self.assertEqual(report['records_with_issues'], 1)
            self.assertEqual(record['source_sha256'], sha256(source.read_bytes()).hexdigest())
            self.assertEqual((destination/report['sources'][0]['archive']).read_bytes(), source.read_bytes())
            self.assertTrue((destination/'questions'/f"{record['id']}.html").exists())
            with self.assertRaises(ValueError):
                build([source], destination)

    def test_public_destination_rejected(self):
        with self.assertRaisesRegex(ValueError, 'local output'):
            build([], ROOT/'resources'/'exam-bank')

    def test_duplicate_workbook_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as folder:
            source = Path(folder)/'fictional.xlsx'
            source.write_bytes(b'fictional')
            with patch('tools.import_chem_exam_bank.inspect', return_value=[]):
                with self.assertRaisesRegex(ValueError, 'same workbook'):
                    build([source, source], Path(folder)/'bank')


if __name__ == '__main__':
    unittest.main()
