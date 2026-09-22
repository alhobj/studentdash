import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from create_example_workbook import create_example
from studentdash.analytics import build_dashboard
from studentdash.config import Config
from studentdash.excel import read_workbook
from studentdash.overview import build_overview
from studentdash.render import generate_dashboards
from studentdash.teacher import create_app


class OverviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='studentdash-overview-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'fictional.xlsx'
        self.config = Config(self.path, self.root / 'output')
        create_example(self.path)

    def edit(self, change):
        book = load_workbook(self.path)
        try:
            change(book)
            book.save(self.path)
        finally:
            book.close()

    def test_cohort_filters_and_question_evidence(self):
        data = read_workbook(self.path)
        learners, items = build_overview(data, 'A2', 'Chemistry SL')
        self.assertEqual([s.id for s in learners], ['1001'])
        self.assertEqual(learners[0].percent, 100)
        self.assertEqual(learners[0].statuses, {'graded': 1, 'exempt': 1})
        self.assertEqual(learners[0].unrecorded, 0)
        self.assertEqual(len(items), 2)  # HL-only question is not applicable.
        self.assertEqual((items[0].percent, items[0].graded, items[0].expected), (100, 1, 1))
        self.assertIsNone(items[1].percent)
        _, all_items = build_overview(data, 'A2')
        shared = next(q for q in all_items if q.number == '2')
        self.assertAlmostEqual(shared.percent, 200 / 3)
        self.assertEqual((shared.graded, shared.expected), (1, 2))
        hl = next(q for q in all_items if q.number == '3')
        self.assertEqual(hl.expected, 1)

    def test_unrecorded_is_distinct_from_missing_and_absent(self):
        def change(book):
            book['QuestionResults']['D2'] = None
            book['QuestionResults']['E2'] = 'missing'
            book['QuestionResults'].delete_rows(3)
        self.edit(change)
        learners, items = build_overview(read_workbook(self.path), 'A1')
        learner = next(s for s in learners if s.id == '1001')
        self.assertEqual(learner.statuses, {'missing': 1})
        self.assertEqual(learner.unrecorded, 1)
        q2 = next(q for q in items if q.number == '2')
        self.assertEqual((q2.percent, q2.graded, q2.expected, q2.unrecorded), (0, 1, 2, 1))

    def test_no_grades_does_not_mean_zero(self):
        learners, items = build_overview(read_workbook(self.path), 'A3')
        self.assertTrue(all(s.percent is None for s in learners))
        self.assertIsNone(items[0].percent)
        self.assertEqual(items[0].statuses, {'pending': 1, 'absent': 1})

    def test_teacher_filters_and_escaping(self):
        self.edit(lambda b: setattr(b['Students']['B2'], 'value', '<script>learner</script>'))
        client = create_app(self.config).test_client()
        all_response = client.get('/')
        self.assertIn(b'85.7%', all_response.data)
        self.assertIn(b'50.0%', all_response.data)
        self.assertIn(b'2 graded assessments', all_response.data)
        response = client.get('/?assessment=A2&class_name=Chemistry+SL')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'&lt;script&gt;learner&lt;/script&gt;', response.data)
        self.assertNotIn(b'Example learner B', response.data)
        self.assertIn(b'100.0%', response.data)
        self.assertEqual(client.get('/?assessment=unknown').status_code, 400)
        self.assertEqual(client.get('/?class_name=unknown').status_code, 400)

    def test_revision_prioritizes_lost_marks_without_ungraded_tasks(self):
        data = read_workbook(self.path)
        first = build_dashboard(data, '1001')
        self.assertEqual(len(first.revision), 1)
        task = first.revision[0]
        self.assertEqual((task.number, task.score, task.marks), ('2', 1, 2))
        self.assertEqual(task.resources[0].topic, 'Atomic structure')
        second = build_dashboard(data, '1002')
        self.assertEqual(len(second.revision), 3)
        self.assertTrue(all(t.marks - t.score == 2 for t in second.revision))
        self.assertEqual(build_dashboard(data, '1001', assessment_id='A2').revision, [])
        self.assertEqual(build_dashboard(data, '1002', assessment_id='A3').revision, [])
        filtered = build_dashboard(data, '1001', assessment_id='A1')
        self.assertEqual(filtered.revision[0].key, task.key)
        self.assertNotIn(task.key, [t.key for t in second.revision])

    def test_revision_completion_key_changes_when_score_changes(self):
        before = build_dashboard(read_workbook(self.path), '1001').revision[0].key
        self.edit(lambda b: setattr(b['QuestionResults']['D3'], 'value', 0))
        after = build_dashboard(read_workbook(self.path), '1001').revision[0].key
        self.assertNotEqual(before, after)

    def test_teacher_cohort_never_reaches_student_exports(self):
        generate_dashboards(self.config)
        html = (self.config.output / 'student1001.html').read_text(encoding='utf-8')
        self.assertIn('Your revision plan', html)
        self.assertIn('data-task=', html)
        self.assertNotIn('Example learner A', html)
        self.assertNotIn('Example learner B', html)
        self.assertNotIn('Class overview', html)
        self.assertNotIn('limiting reactant for the supplied reaction', html)


if __name__ == '__main__':
    unittest.main()
