"""Booklet companions, contextual mappings and offline reference links."""
import json
from html import unescape
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1] / 'resources'


class BookletResourceTests(unittest.TestCase):
    def test_booklet_maps_and_generated_links(self):
        for profile in ('ib-chemistry', 'ib-math-ai-sl'):
            root = ROOT / profile
            data = json.loads((root / 'booklet.json').read_text(encoding='utf-8'))
            syllabus = json.loads((root / 'syllabus-reference.json').read_text(encoding='utf-8'))
            foundations = json.loads((root / 'foundations.json').read_text(encoding='utf-8'))
            self.assertEqual(set(data['sections']), set(syllabus['sections']))
            self.assertLessEqual(set(data['prior']), {c['id'] for c in foundations['prior']})
            keys = {entry['id'] for entry in data['entries']}
            self.assertEqual(len(keys), len(data['entries']))
            for mapping in ('sections', 'prior'):
                for code, values in data[mapping].items():
                    self.assertLessEqual(set(values), keys, code)
                    self.assertEqual(len(values), len(set(values)))
            html = (root / data['filename']).read_text(encoding='utf-8')
            self.assertIn('version 1.1', html)
            self.assertIn('does not reproduce or replace', html)
            self.assertNotRegex(html, r'<(?:script|iframe)\b')
            for entry in data['entries']:
                self.assertIn('id="' + entry['id'] + '"', html)
                self.assertIn(data['url'] + '#page=' + str(entry['pdf_page']), html)
                self.assertGreater(entry['pdf_page'], data['page_offset'])
            self.assertIn(data['filename'], (root / data['hub']).read_text(encoding='utf-8'))
            # Validate every generated local reference, including links inside task help.
            for file in root.glob('*.html'):
                for href in re.findall(r'href="([^"]+)"', file.read_text(encoding='utf-8')):
                    href = unescape(href)
                    if href.startswith(('https:', 'http:')):
                        continue
                    filename, _, anchor = href.partition('#')
                    target = root / (filename or file.name)
                    self.assertTrue(target.is_file(), (file.name, href))
                    if anchor:
                        self.assertIn('id="' + anchor + '"', target.read_text(encoding='utf-8'), href)

    def test_relevant_help_and_level_boundaries(self):
        chem = ROOT / 'ib-chemistry'
        math = ROOT / 'ib-math-ai-sl'
        self.assertIn('data-booklet.html#gas', (chem / 's1-5.html').read_text(encoding='utf-8'))
        self.assertIn('data-booklet.html#heat', (chem / 'basics-r1.html').read_text(encoding='utf-8'))
        self.assertIn('data-booklet.html#potentials', (chem / 'challenges-r3.html').read_text(encoding='utf-8'))
        self.assertIn('formula-booklet.html#arithmetic', (math / 'topic-1.html').read_text(encoding='utf-8'))
        self.assertIn('formula-booklet.html#integral', (math / 'challenges-5.html').read_text(encoding='utf-8'))
        self.assertIn('formula-booklet.html#measurement', (math / 'prior-learning.html').read_text(encoding='utf-8'))
        data = json.loads((chem / 'booklet.json').read_text(encoding='utf-8'))
        entries = {e['id']: e for e in data['entries']}
        for key in ('gibbs', 'arrhenius', 'equilibrium-energy'):
            self.assertIn('AHL', entries[key]['title'])
        self.assertIn('not multiply', entries['potentials']['note'])
        self.assertIn('kelvin', entries['gas']['note'])
        data = json.loads((math / 'booklet.json').read_text(encoding='utf-8'))
        entries = {e['id']: e for e in data['entries']}
        self.assertEqual(data['sections']['4.11'], [])  # No invented test formula in the booklet.
        self.assertIn('lump sum', entries['finance']['note'])
        self.assertIn('n = −1', entries['integral']['note'])
