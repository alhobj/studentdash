"""Check that generated guide references cover each profile's section pages."""
import json
from pathlib import Path
import unittest
import re


ROOT = Path(__file__).resolve().parents[1] / 'resources'


class SyllabusReferenceTests(unittest.TestCase):
    def test_cross_references_resolve_and_retain_source_direction(self):
        for profile in ('ib-chemistry', 'ib-math-ai-sl'):
            root = ROOT / profile
            data = json.loads((root / 'syllabus-cross-references.json').read_text(encoding='utf-8'))
            guide = json.loads((root / 'syllabus-reference.json').read_text(encoding='utf-8'))
            self.assertEqual(set(data['sections']), set(guide['sections']))
            for code, links in data['sections'].items():
                with self.subTest(profile=profile, code=code):
                    identities = [(link['target'], link.get('qualifier')) for link in links]
                    self.assertEqual(len(identities), len(set(identities)))
                    for link in links:
                        target = data['targets'][link['target']]
                        self.assertTrue(link['source_pages'])
                        self.assertTrue(all(isinstance(p, int) and p >= guide['sections'][code]['pdf_page'] for p in link['source_pages']))
                        if target.get('guide_only'):
                            self.assertTrue(target['href'].startswith(guide['copy_url'] + '#page='))
                        else:
                            filename, _, anchor = target['href'].partition('#')
                            path = root / filename
                            self.assertTrue(path.is_file(), target['href'])
                            if anchor:
                                self.assertIn('id="' + anchor + '"', path.read_text(encoding='utf-8'))
            if profile == 'ib-chemistry':
                links = data['sections']['S2.1']
                self.assertIn({'target': 'S1.3', 'source_pages': [44], 'qualifier': 'AHL'}, links)
                self.assertIn('S2', [link['target'] for link in data['sections']['S1.1']])
                self.assertNotIn('S2', [link['target'] for link in data['sections']['S1.5']])
                self.assertIn('inquiry-3', [link['target'] for link in data['sections']['R1.1']])
            else:
                self.assertIn('2.1', [link['target'] for link in data['sections']['3.5']])
                self.assertEqual(data['sections']['2.1'], [])  # No invented reverse link.
                self.assertIn('AHL 2.9', [link['target'] for link in data['sections']['2.6']])
                self.assertIn('1.7', [link['target'] for link in data['sections']['2.5']])

    def test_section_pages_have_correct_references_before_activities(self):
        checked = 0
        for profile in ('ib-chemistry', 'ib-math-ai-sl'):
            root = ROOT / profile
            reference = json.loads((root / 'syllabus-reference.json').read_text(encoding='utf-8'))
            if profile == 'ib-chemistry':
                topics = json.loads((root / 'practice-syllabus.json').read_text(encoding='utf-8'))['topics']
                pages = {t['id'].lower().replace('.', '-') + '.html': [t['id']] for t in topics}
                groups = {t['parent']: [x['id'] for x in topics if x['parent'] == t['parent']] for t in topics}
                self.assertEqual(reference['sections']['R1.4']['level'], 'AHL only')
            else:
                topics = json.loads((root / 'coverage.json').read_text(encoding='utf-8'))
                groups = {str(i): [t['code'] for t in topics if t['code'].startswith(str(i) + '.')] for i in range(1, 6)}
                pages = {f'topic-{group}.html': codes for group, codes in groups.items()}
                self.assertTrue(all(row['level'] == 'SL' for row in reference['sections'].values()))
            self.assertEqual(set(reference['sections']), {code for codes in groups.values() for code in codes})
            for prefix in ('basics', 'challenges'):
                pages.update({f'{prefix}-{group.lower()}.html': codes for group, codes in groups.items()})
            for filename, codes in pages.items():
                with self.subTest(profile=profile, page=filename):
                    html = (root / filename).read_text(encoding='utf-8')
                    panels = list(re.finditer(r'<aside class="syllabus-reference"[^>]*>(.*?)</aside>', html))
                    self.assertEqual(len(panels), 1)
                    panel = panels[0].group(1)
                    self.assertEqual(re.findall(r'<strong>(.*?)</strong>', panel), [reference['sections'][c]['label'] for c in codes])
                    self.assertLess(panels[0].start(), html.index('<section'))
                    for item, code in zip(re.findall(r'<li>(.*?)</li>', panel), codes):
                        row = reference['sections'][code]
                        self.assertGreater(row['pdf_page'], row['printed_page'])
                        self.assertIn(reference['copy_url'] + '#page=' + str(row['pdf_page']), item)
                    self.assertIn('paraphrases', panel)
                    self.assertFalse(re.search(r'<(?:iframe|script|img)\b', panel))
                    checked += 1
        self.assertEqual(checked, 49)
