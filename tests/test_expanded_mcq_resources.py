"""Section coverage, retained source integrity and offline answer controls."""
from collections import Counter
import json
from pathlib import Path
import unittest
from tests import test_authored_mcq_resources as authored

ROOT = Path(__file__).resolve().parents[1]


class ExpandedMcqContentTests(unittest.TestCase):
    def test_section_banks_and_links(self):
        for profile, count in [('ib-chemistry', 22), ('ib-math-ai-sl', 39)]:
            root = ROOT / 'resources' / profile
            rows = json.loads((root / 'authored-mcq.json').read_text(encoding='utf-8'))
            self.assertEqual(len(rows), count*20)
            self.assertEqual(len({q['id'] for q in rows}), count*20)
            self.assertEqual(len({q['topic'] for q in rows}), count)
            self.assertTrue(all(v == 20 for v in Counter(q['topic'] for q in rows).values()))
            for topic in {q['topic'] for q in rows}:
                bank = [q for q in rows if q['topic'] == topic]
                self.assertEqual(len({q['prompt'] for q in bank}), 20)
                if bank[0]['source_id'].startswith('MCQ_'):
                    self.assertEqual(Counter(q['answer'][0] for q in bank), dict.fromkeys('ABCD', 5))
            for q in rows:
                self.assertEqual(len(set(q['options'])), 4)
                self.assertIn(q['answer'][0], 'ABCD')
                self.assertTrue(q['working'])
                filename, anchor = q['path'].split('#')
                page = (root / filename).read_text(encoding='utf-8')
                self.assertIn(f'id="{anchor}"', page)
                self.assertIn('src="authored-mcq.js"', page)
                self.assertIn('src="learning.js"', page)
                self.assertEqual(page.count('data-authored-mcq='), 20)

    def test_independent_numerical_examples(self):
        examples = {
            'ib-chemistry': [('MCQ_S1_4_001', 2), ('MCQ_S1_5_002', 3), ('MCQ_R1_1_001', 4180), ('MCQ_R1_4_001', -14), ('MCQ_R2_1_004', .2)],
            'ib-math-ai-sl': [('MCQ_1_2_002', 48), ('MCQ_3_5_004', 6), ('MCQ_4_6_003', .1), ('MCQ_5_4_004', 1.5), ('MCQ_5_8_004', 24)]
        }
        for profile, examples in examples.items():
            rows = json.loads((ROOT/'resources'/profile/'authored-mcq.json').read_text(encoding='utf-8'))
            for key, expected in examples:
                q = next(q for q in rows if q['source_id'] == key)
                self.assertAlmostEqual(float(q['options']['ABCD'.index(q['answer'][0])]), expected)


class ExpandedMcqBrowserTests(authored.AuthoredMcqBrowserTests):
    # Inherit keyboard/journal checks and original-source button checks.
    def test_new_banks_all_four_choices(self):
        for profile in ['ib-chemistry', 'ib-math-ai-sl']:
            root = ROOT / 'resources' / profile
            rows = json.loads((root/'authored-mcq.json').read_text(encoding='utf-8'))
            pages = {q['path'].split('#')[0] for q in rows if q['source_id'].startswith('MCQ_')}
            for name in sorted(pages):
                self.page.goto((root/name).as_uri())
                self.page.set_viewport_size({'width':320, 'height':900})
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'), name)
                result = self.page.evaluate('''() => {
                    const cards = [...document.querySelectorAll('[data-authored-mcq]')];
                    for (const card of cards) {
                        for (const button of card.querySelectorAll('[data-choice]')) {
                            button.click();
                            const expected = button.dataset.choice === card.dataset.correct ? 'Correct' : 'Not correct';
                            if (!card.querySelector('.mcq-feedback').textContent.startsWith(expected)) return card.id;
                            if (card.querySelectorAll('[aria-pressed="true"]').length !== 1) return card.id;
                        }
                        card.querySelector('.mcq-retry').click();
                        if (card.querySelectorAll('[aria-pressed="true"]').length) return card.id;
                    }
                    return cards.length;
                }''')
                self.assertEqual(result, 20, name)


