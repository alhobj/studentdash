"""Real-assessment workflow with fictional students and isolated storage."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from studentdash.analytics import build_dashboard
from studentdash.config import Config
from studentdash.entry import ClassStore, EntryError, assessment, as_workbook, save_assessment, save_scores, summary
from studentdash.freshness import stale_reasons
from studentdash.render import generate_dashboards
from studentdash.teacher import create_app


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='studentdash-entry-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = Config(self.root / 'unused.xlsx', self.root / 'output')
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional class', 'ALICE_PRIVATE\talice@example.invalid\nBOB_PRIVATE\tbob@example.invalid')
        self.key = self.doc['id']
        self.sids = [s['id'] for s in self.doc['students']]
        self.payload = dict(name='First assessment', date='2026-09-23', description='Teacher description',
                            participants=self.sids, questions=[
            dict(number='1', marks='2', text='Question one', curriculum='', tags={}),
            dict(number='3b', marks='3', text='', curriculum='S1.2', tags={'CommandTerm': ['Explain'], 'Skill': ['Chemical reasoning']})])
        self.aid = save_assessment(self.store, self.key, None, self.payload, self.doc['version'])

    def save(self, rows):
        save_scores(self.store, self.key, self.aid, rows, self.store.read(self.key)['version'])

    def item(self):
        return assessment(self.store.read(self.key), self.aid)

    def data(self):
        return as_workbook(self.store.path(self.key))

    def test_class_persistent_roster_and_stable_ids(self):
        reopened = ClassStore(self.root / 'entered_classes')
        self.assertEqual([s['id'] for s in reopened.read(self.key)['students']], self.sids)
        doc = reopened.add_students(self.key, 'CAROL_PRIVATE', reopened.read(self.key)['version'])
        self.assertEqual([s['id'] for s in doc['students'][:2]], self.sids)
        self.assertEqual(len(set(s['id'] for s in doc['students'])), 3)
        aid = save_assessment(reopened, self.key, None, self.payload, doc['version'])
        self.assertNotEqual(aid, self.aid)
        self.assertEqual(assessment(reopened.read(self.key), aid)['participants'], self.sids)

    def test_assessment_questions_classification_and_optional_text(self):
        item = self.item()
        self.assertEqual(item['description'], 'Teacher description')
        self.assertEqual([q['marks'] for q in item['questions']], [2, 3])
        self.assertEqual(len(set(q['id'] for q in item['questions'])), 2)
        self.assertEqual(item['questions'][1]['text'], '')
        self.assertEqual(len(self.data().question_tags), 2)
        changed = deepcopy(item)
        changed['questions'].reverse()
        save_assessment(self.store, self.key, self.aid, changed, self.store.read(self.key)['version'])
        self.assertEqual(self.item()['questions'][0]['id'], item['questions'][1]['id'])

    def test_maximum_validation_and_recorded_question_protection(self):
        for maximum in [0, -1, 'NaN', 'Infinity', 'bad', True]:
            payload = deepcopy(self.payload)
            payload['questions'][0]['marks'] = maximum
            with self.subTest(maximum=maximum), self.assertRaises(EntryError):
                save_assessment(self.store, self.key, None, payload, self.store.read(self.key)['version'])
        self.save([['2', '3'], ['0', '0']])
        changed = deepcopy(self.item())
        changed['questions'][0]['marks'] = 1
        with self.assertRaisesRegex(EntryError, 'below a saved score'):
            save_assessment(self.store, self.key, self.aid, changed, self.store.read(self.key)['version'])
        changed['questions'] = changed['questions'][1:]
        with self.assertRaisesRegex(EntryError, 'cannot be removed'):
            save_assessment(self.store, self.key, self.aid, changed, self.store.read(self.key)['version'])

    def test_zero_decimal_scores_and_correction(self):
        self.save([['0', '1,5'], ['2', '3']])
        self.assertEqual(summary(self.item(), self.sids[0]), (1.5, 5, 'graded'))
        self.save([['1', '2.5'], ['2', '3']])
        self.assertEqual(summary(self.item(), self.sids[0]), (3.5, 5, 'graded'))
        self.assertEqual(build_dashboard(self.data(), self.sids[0], False).overall_percent, 70)

    def test_all_statuses_and_no_stale_totals(self):
        for value, expected in [('A', 'absent'), ('absent', 'absent'), ('M', 'missing'),
                                ('missing', 'missing'), ('E', 'exempt'), ('exempt', 'exempt'),
                                ('P', 'pending'), ('pending', 'pending'), ('', 'pending')]:
            with self.subTest(value=value):
                self.save([['2', '3'], ['2', '3']])
                self.save([[value, value], ['2', '3']])
                data = self.data()
                own = next(r for r in data.results if r.student_id == self.sids[0])
                self.assertEqual(own.status, expected)
                self.assertIsNone(own.score)
                view = build_dashboard(data, self.sids[0], False)
                self.assertIsNone(view.overall_percent)
                self.assertIsNone(view.history[0].grade)
                self.assertTrue(all(r.status == expected for r in data.question_results if r.student_id == self.sids[0]))

    def test_exempt_denominator_and_mixed_incomplete(self):
        self.save([['2', 'E'], ['1', 'P']])
        self.assertEqual(summary(self.item(), self.sids[0]), (2, 2, 'graded'))
        self.assertEqual(summary(self.item(), self.sids[1]), (None, 5, 'pending'))
        view = build_dashboard(self.data(), self.sids[1], False)
        self.assertIsNone(view.history[0].score)
        self.assertEqual(view.questions[0].score, 1)

    def test_question_changes_recompute_totals_and_new_questions_are_pending(self):
        self.save([['2', '3'], ['1', '2']])
        changed = deepcopy(self.item())
        changed['questions'][0]['marks'] = 4
        save_assessment(self.store, self.key, self.aid, changed, self.store.read(self.key)['version'])
        self.assertEqual(summary(self.item(), self.sids[0]), (5, 7, 'graded'))
        changed = deepcopy(self.item())
        changed['questions'].append(dict(number='4', marks=2, text='', tags={}, curriculum=''))
        save_assessment(self.store, self.key, self.aid, changed, self.store.read(self.key)['version'])
        self.assertEqual(summary(self.item(), self.sids[0]), (None, 9, 'pending'))
        from studentdash.overview import build_overview
        learners, _ = build_overview(self.data(), self.aid)
        self.assertTrue(all(s.result_label == 'Incomplete' for s in learners))

    def test_invalid_cell_does_not_partially_save(self):
        self.save([['1', '2'], ['0', '0']])
        before = self.store.read(self.key)
        for invalid in ['3', '-1', 'NaN', 'Infinity', 'word', True, None]:
            with self.subTest(value=invalid), self.assertRaises(EntryError) as caught:
                self.save([[invalid, '3'], ['2', '3']])
            self.assertIn('0:0', caught.exception.cells)
            self.assertEqual(before, self.store.read(self.key))
        with self.assertRaises(EntryError):
            self.save([['1']])

    def test_save_reopen_and_concurrent_edit_protection(self):
        stale = self.store.read(self.key)['version']
        self.save([['2', '1'], ['1', '2']])
        with self.assertRaisesRegex(EntryError, 'Another tab'):
            save_scores(self.store, self.key, self.aid, [['0', '0'], ['0', '0']], stale)
        reopened = ClassStore(self.root / 'entered_classes')
        self.assertEqual(summary(assessment(reopened.read(self.key), self.aid), self.sids[0]), (3, 5, 'graded'))

    def test_configured_categories_without_code_changes(self):
        other = self.store.create('Fictional literature', 'Reader', profile=dict(name='Literature', categories={'Lens': ['Narrator', 'Audience']}))
        payload = deepcopy(self.payload)
        payload['participants'] = [other['students'][0]['id']]
        for q in payload['questions']:
            q['tags'] = {'Lens': ['Narrator']}
        save_assessment(self.store, other['id'], None, payload, other['version'])
        data = as_workbook(self.store.path(other['id']))
        self.assertEqual({t.category for t in data.question_tags}, {'Lens'})

    def test_generate_reopen_isolation_and_staleness(self):
        self.save([['0', '1'], ['1.234', '2.345']])
        config = Config(self.store.path(self.key), self.root / 'exports')
        _, names = generate_dashboards(config, False)
        self.assertEqual(len(names), 2)
        own = (config.output / f'student{self.sids[0]}.html').read_text(encoding='utf-8')
        for private in ['ALICE_PRIVATE', 'BOB_PRIVATE', 'alice@example.invalid', 'bob@example.invalid', self.sids[1], '1.234', '2.345']:
            self.assertNotIn(private, own)
        manifest = json.loads((config.output / 'generation.json').read_text())
        self.assertEqual(stale_reasons(config, manifest), [])
        self.save([['0', 'P'], ['1.234', '2.345']])
        self.assertTrue(stale_reasons(config, manifest))
        generate_dashboards(config, False)
        self.assertIn('Incomplete', (config.output / names[0]).read_text(encoding='utf-8'))

    def client(self):
        app = create_app(self.config)
        app.testing = True
        client = app.test_client()
        client.get('/classes')
        return client

    def post(self, client, path, **data):
        with client.session_transaction() as session:
            token = session['csrf_token']
        return client.post(path, data=dict(csrf_token=token, **data))

    def test_teacher_http_workflow_and_reopen(self):
        client = self.client()
        self.assertEqual(client.get('/').status_code, 302)
        response = self.post(client, '/classes', name='Second class', roster='Another learner')
        self.assertEqual(response.status_code, 303)
        response = client.get(f'/classes/{self.key}')
        self.assertIn(b'First assessment', response.data)
        for path in [f'/classes/{self.key}/assessments/new', f'/classes/{self.key}/assessments/{self.aid}/edit',
                     f'/classes/{self.key}/assessments/{self.aid}/scores']:
            self.assertEqual(client.get(path).status_code, 200)
        path = f'/classes/{self.key}/assessments/{self.aid}/scores'
        response = self.post(client, path, version=self.store.read(self.key)['version'], payload=json.dumps([['2', '3'], ['1', '2']]))
        self.assertEqual(response.status_code, 303)
        self.assertIn(b'5/5', client.get(response.location).data)
        response = client.get(f'/?class_key={self.key}&assessment={self.aid}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'100.0%', response.data)
        response = self.post(client, '/generate?class_key=' + self.key)
        self.assertEqual(response.status_code, 303)
        preview = client.get(f'/preview/student{self.sids[0]}.html?class_key={self.key}')
        self.assertEqual(preview.status_code, 200)
        self.assertNotIn(b'BOB_PRIVATE', preview.data)
        preview.close()
        fresh_client = self.client()
        self.assertEqual(fresh_client.get(path).status_code, 200)
        self.assertIn(b'5/5', fresh_client.get(path).data)

    def test_http_cell_errors_and_teacher_only(self):
        client = self.client()
        path = f'/classes/{self.key}/assessments/{self.aid}/scores'
        response = self.post(client, path, version=self.store.read(self.key)['version'], payload=json.dumps([['99', '3'], ['1', '2']]))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'value="99"', response.data)
        self.assertIn(b'ALICE_PRIVATE, question 1', response.data)
        self.assertEqual(client.post(path).status_code, 400)
        with client.session_transaction() as session:
            session['simulated_student'] = self.sids[0]
        self.assertEqual(client.get('/classes').status_code, 403)
        self.assertEqual(client.get(path).status_code, 403)

    def test_class_context_does_not_follow_other_tab(self):
        client = self.client()
        self.save([['1', '2'], ['1', '2']])
        other = self.store.create('Other class', 'UNRELATED_PERSON')
        client.get(f'/classes/{other["id"]}')
        response = client.get(f'/?class_key={self.key}')
        self.assertIn(b'ALICE_PRIVATE', response.data)
        self.assertNotIn(b'UNRELATED_PERSON', response.data)
        self.assertIn(f'class_key={self.key}'.encode(), response.data)


if __name__ == '__main__':
    unittest.main()
