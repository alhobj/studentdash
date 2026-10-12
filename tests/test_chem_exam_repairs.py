import unittest
from tools.repair_chem_exam_bank import clean, parts, suggestions


def example(index, marks=1):
    return dict(id=str(index), source_sha256='fictional', source_row=index,
                source_file='fictional.xlsx', source_sheet='Source', source_id=str(index), issues=[],
                raw={'Reference code':'example.1', 'Question part':"[['a.'], ['b.']]",
                     'Marks for each part':"[['[1]'], ['[2]']]", 'Marks available':marks,
                     'Question':'[[<p>Fictional A [X]</p>], [<p>Fictional B</p>]]',
                     'Markscheme':'[[<p>Answer A</p>], [<p>Answer B</p>]]'})


class RepairTests(unittest.TestCase):
    def test_matching_order_and_marks_propose_parts(self):
        rows = [example(1), example(2, 2)]
        output = suggestions(rows)
        self.assertEqual(output['1']['fields']['Question'], '<p>Fictional A [X]</p>')
        self.assertEqual(output['2']['fields']['Markscheme'], '<p>Answer B</p>')
        self.assertEqual(output['2']['part'], 'b.')
        self.assertIn('[[', rows[0]['raw']['Question'])
        self.assertTrue(output['1']['inferred'])

    def test_conflicting_marks_do_not_match(self):
        output = suggestions([example(1, 9), example(2, 2)])
        self.assertFalse(output['1']['inferred'])
        self.assertIn('Fictional B', output['1']['fields']['Question'])

    def test_mismatched_answer_count_keeps_answers_grouped(self):
        rows = [example(1), example(2, 2)]
        for row in rows:
            row['raw']['Markscheme'] = '[[<p>Unknown grouped answer</p>]]'
        output = suggestions(rows)
        self.assertIn('Unknown grouped answer', output['2']['fields']['Markscheme'])
        self.assertTrue(any('unresolved' in n for n in output['2']['notes']))

    def test_truncated_data_is_not_split(self):
        self.assertIsNone(parts('[[<p>'+'x'*32767))
        self.assertIn('missing content', clean('<p>Fictional <img src="data:image/png;base64,broken'))
        self.assertNotIn('<img', clean('<p>Fictional <img src="data:image/png;base64,broken'))

    def test_safe_cleanup_preserves_scientific_brackets(self):
        text = clean('[[<p>[X] = [Y]</p>, <p>X<sub>2</sub></p>]]')
        self.assertIn('[X] = [Y]', text)
        self.assertNotIn('[[', text)
        self.assertIn('<sub>2</sub>', text)


if __name__ == '__main__':
    unittest.main()
