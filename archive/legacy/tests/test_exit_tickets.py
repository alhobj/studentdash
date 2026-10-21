import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from create_example_workbook import create_example
from studentdash.analytics import build_dashboard
from studentdash.config import Config
from studentdash.excel import read_workbook
from studentdash.exit_schema import parse_ticket, TicketError, automatic_score, validate_answers
from studentdash.exit_store import TicketRepository
from studentdash.exit_tickets import TicketService, progress_rows
from studentdash.teacher import create_app


def example():
    return dict(title='Fictional ionic bonding', subject='Chemistry', topic='Atomic structure', subtopic='Particles', questions=[
        dict(id='mcq', type='multiple_choice', question='Which ion does magnesium form?', options=['Mg+', 'Mg2+', 'Mg3+'], answer='Mg2+', marks=1, action_verb='State'),
        dict(id='multi', type='multiple_select', question='Select the specified examples.', options=['Ionic', 'Covalent', 'Metallic'], answer=['Ionic', 'Metallic'], marks=2, action_verb='Identify'),
        dict(id='tf', type='true_false', question='An electron has a negative charge.', answer=True, marks=1, action_verb='State'),
        dict(id='num', type='number', question='What is the charge of an oxide ion?', answer=-2, marks=1, action_verb='State'),
        dict(id='short', type='short_answer', question='Name a positively charged ion.', accepted_answers=['cation'], marks=1, action_verb='State'),
        dict(id='written', type='text', question='Explain the melting point of MgO.', marks=2, action_verb='Explain', manual_marking=True),
    ])


def answers():
    return dict(mcq='Mg2+', multi=['Metallic', 'Ionic'], tf=True, num='-2.0', short='cation', written='Strong electrostatic attraction in a giant ionic lattice.')


class ExitSchemaTests(unittest.TestCase):
    def test_valid_import_and_generated_ids(self):
        source = example()
        del source['questions'][0]['id']
        ticket = parse_ticket('```json\n' + json.dumps(source) + '\n```')
        self.assertEqual(ticket['questions'][0]['id'], 'q1')
        self.assertFalse(ticket['allow_answer_review'])
        self.assertEqual(parse_ticket(json.dumps(ticket)), ticket)

    def test_invalid_json_and_shape(self):
        for raw in ('{broken', '[]', '{}', '{"title":"a","title":"b"}', '{"questions":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(TicketError):
                parse_ticket(raw)

    def test_missing_fields_unknown_types_and_duplicates(self):
        for mutate in [lambda t: t.pop('subject'), lambda t: t['questions'][0].update(type='essay'),
                       lambda t: t['questions'][1].update(id='mcq'), lambda t: t.update(teacher_private_note='secret'),
                       lambda t: t.update(allow_answer_review='false'), lambda t: t.update(questions=[])]:
            source = example()
            mutate(source)
            with self.assertRaises(TicketError):
                parse_ticket(json.dumps(source))

    def test_invalid_keys_options_marks_and_manual_rules(self):
        changes = [(0, {'answer': 'missing'}), (0, {'options': ['A','A']}), (0, {'marks': True}),
                   (0, {'marks': 0}), (0, {'marks': float('nan')}), (0, {'marks': 10**500}),
                   (1, {'answer': ['Ionic','Ionic']}), (2, {'answer': 'true'}), (3, {'tolerance': -1}),
                   (5, {'manual_marking': False}), (4, {'manual_marking': True})]
        for index, change in changes:
            source = example()
            source['questions'][index].update(change)
            with self.subTest(change=change), self.assertRaises(TicketError):
                parse_ticket(json.dumps(source))

    def test_automatic_marking_and_exact_multiple_select(self):
        questions = parse_ticket(json.dumps(example()))['questions']
        values = validate_answers(questions, answers())
        self.assertEqual([automatic_score(q, values[q['id']]) for q in questions], [1, 2, 1, 1, 1, None])
        self.assertEqual(automatic_score(questions[0], 'Mg+'), 0)
        self.assertEqual(automatic_score(questions[1], ['Ionic']), 0)
        self.assertEqual(automatic_score(questions[1], ['Ionic', 'Metallic', 'Covalent']), 0)
        self.assertEqual(automatic_score(questions[2], False), 0)

    def test_numeric_tolerance_and_no_nonfinite_values(self):
        questions = parse_ticket(json.dumps(example()))['questions']
        q = dict(questions[3], answer=0.3, tolerance=0.01)
        self.assertEqual(automatic_score(q, '0.31'), 1)
        self.assertEqual(automatic_score(q, '0.311'), 0)
        for value in ('NaN', 'Infinity', '1e999999999', 'two', ''):
            values = answers()
            values['num'] = value
            with self.subTest(value=value), self.assertRaises(TicketError):
                validate_answers(questions, values)

    def test_short_answer_matching_is_conservative(self):
        q = parse_ticket(json.dumps(example()))['questions'][4]
        self.assertEqual(automatic_score(q, ' cation '), 1)
        self.assertEqual(automatic_score(q, 'Cation'), 0)
        self.assertEqual(automatic_score(q, 'a cation'), 0)
        self.assertEqual(automatic_score(dict(q, case_sensitive=False), 'CATION'), 1)
        source = example()
        source['questions'][4].pop('accepted_answers')
        q = parse_ticket(json.dumps(source))['questions'][4]
        self.assertTrue(q['manual_marking'])
        self.assertIsNone(automatic_score(q, 'anything'))

    def test_all_answers_required_and_unknown_options_rejected(self):
        questions = parse_ticket(json.dumps(example()))['questions']
        for change in [dict(written=' '), dict(mcq='Unknown'), dict(multi=[]), dict(multi=['Ionic','Ionic']), dict(tf='true')]:
            with self.subTest(change=change), self.assertRaises(TicketError):
                validate_answers(questions, dict(answers(), **change))
        values = answers()
        values.pop('num')
        with self.assertRaises(TicketError):
            validate_answers(questions, values)


class ExitWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='studentdash-exit-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'fictional.xlsx'
        create_example(self.path)
        self.config = Config(self.path, self.root / 'output')
        self.data = read_workbook(self.path)
        self.repo = TicketRepository(self.config.workspace)
        self.service = TicketService(self.repo)
        self.app = create_app(self.config)
        self.app.config['TESTING'] = True
        self.teacher = self.app.test_client()
        self.teacher.get('/')

    def csrf(self, client):
        with client.session_transaction() as session:
            return session['csrf_token']

    def make(self, audience=None, reveal=False, publish=True):
        source = example()
        source['allow_answer_review'] = reveal
        tid = self.service.save(json.dumps(source), audience if audience is not None else ['all'], self.data.students)
        if publish:
            self.repo.change_status(tid, 1, 'published')
        return tid

    def simulated(self, sid):
        client = self.app.test_client()
        client.get('/')
        response = client.post('/simulation/student/' + sid, data={'csrf_token': self.csrf(client)})
        self.assertEqual(response.status_code, 303)
        return client

    def post_answers(self, client, sid, tid, values=None):
        values = values or answers()
        form = {'csrf_token': self.csrf(client), 'version': str(self.repo.get(tid)['version'])}
        form.update({'answer_' + key: ('true' if value else 'false') if isinstance(value, bool) else value for key, value in values.items()})
        return client.post(f'/student/student{sid}/tickets/{tid}', data=form, follow_redirects=True)

    def test_import_preview_edit_and_publish_routes(self):
        response = self.teacher.post('/exit-tickets/import', data=dict(csrf_token=self.csrf(self.teacher), source=json.dumps(example()), audience='class:Chemistry SL'))
        self.assertEqual(response.status_code, 303)
        tid = self.repo.list()[0]['id']
        preview = self.teacher.get(response.headers['Location'])
        self.assertEqual(preview.status_code, 200)
        self.assertIn(b'Student form preview', preview.data)
        self.assertEqual(self.repo.get(tid)['assignments'], ['1001'])
        source = example()
        source['title'] = 'Edited ticket'
        response = self.teacher.post(f'/exit-tickets/{tid}/edit', data=dict(csrf_token=self.csrf(self.teacher), source=json.dumps(source), audience='all', version=1))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.repo.get(tid)['questions'][0]['id'], 'mcq')
        self.assertEqual(self.teacher.post(f'/exit-tickets/{tid}/publish', data=dict(csrf_token=self.csrf(self.teacher), version=2)).status_code, 303)
        self.assertEqual(self.repo.get(tid)['status'], 'published')

    def test_invalid_import_keeps_text_and_has_no_side_effects(self):
        response = self.teacher.post('/exit-tickets/import', data=dict(csrf_token=self.csrf(self.teacher), source='{bad', audience='all'))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'{bad', response.data)
        self.assertEqual(self.repo.list(), [])

    def test_assignment_and_publication_states(self):
        tid = self.make(['student:1001'], publish=False)
        with self.assertRaises(KeyError): self.service.available(tid, '1001')
        self.repo.change_status(tid, 1, 'published')
        self.assertEqual(self.service.available(tid, '1001')['title'], example()['title'])
        with self.assertRaises(KeyError): self.service.available(tid, '1002')
        self.repo.change_status(tid, 2, 'unpublished')
        with self.assertRaises(TicketError): self.repo.submit(tid, '1001', 3, answers())
        self.repo.change_status(tid, 3, 'published')
        self.assertEqual(self.repo.get(tid)['status'], 'published')

    def test_no_assignment_cannot_publish_and_bad_audience_rejected(self):
        tid = self.make([], publish=False)
        with self.assertRaises(TicketError): self.repo.change_status(tid, 1, 'published')
        with self.assertRaises(TicketError): self.service.save(json.dumps(example()), ['student:unknown'], self.data.students)

    def test_full_submission_review_and_separate_progress(self):
        tid = self.make()
        student = self.simulated('1001')
        before = build_dashboard(self.data, '1001', False)
        response = self.post_answers(student, '1001', tid)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submission saved', response.data)
        self.assertIn(b'awaiting teacher review', response.data)
        result = self.service.results(tid)
        self.assertEqual((result['submitted'], result['not_submitted'], result['average']), (1, 1, None))
        self.assertEqual(result['items'][-1]['pending'], 1)
        self.assertEqual(self.teacher.get(f'/exit-tickets/{tid}/results').status_code, 200)
        self.assertEqual(self.teacher.get(f'/exit-tickets/{tid}/review/1001').status_code, 200)
        response = self.teacher.post(f'/exit-tickets/{tid}/review/1001', data=dict(csrf_token=self.csrf(self.teacher), question_id='written', score='1.5', feedback='Good reasoning; explain the energy needed.', version=0))
        self.assertEqual(response.status_code, 303)
        history = self.service.history(tid, '1001')
        self.assertEqual((history['score'], history['maximum'], history['pending']), (7.5, 8, 0))
        self.assertAlmostEqual(self.service.results(tid)['average'], 93.75)
        home = student.get('/student/student1001')
        self.assertIn(b'93.8%', home.data)
        result_page = student.get(f'/student/student1001/history/{tid}')
        self.assertIn(b'Good reasoning', result_page.data)
        groups = progress_rows(self.data, '1001', self.service.student_home('1001')[1])
        self.assertEqual(groups[0]['assessment_percent'], 75)
        self.assertEqual(groups[0]['exit_percent'], 93.75)
        self.assertEqual(build_dashboard(self.data, '1001', False).history, before.history)
        self.assertEqual(read_workbook(self.path).results, self.data.results)

    def test_duplicate_and_concurrent_submissions_preserve_first_answers(self):
        tid = self.make()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.repo.submit(tid, '1001', 2, answers()), range(2)))
        self.assertEqual(results[0], results[1])
        self.repo.submit(tid, '1001', 2, dict(answers(), written='Replacement should not be stored'))
        self.assertEqual(len(self.repo.submissions(tid)), 1)
        self.assertNotIn('Replacement', json.dumps(self.repo.submission(tid, '1001')))

    def test_freeze_and_unpublish_preserve_history(self):
        tid = self.make()
        self.repo.submit(tid, '1001', 2, answers())
        self.repo.change_status(tid, 2, 'unpublished')
        with self.assertRaises(TicketError): self.service.save(json.dumps(example()), ['all'], self.data.students, tid, 3)
        with self.assertRaises(TicketError): self.repo.submit(tid, '1002', 3, answers())
        self.assertEqual(self.service.history(tid, '1001')['pending'], 1)
        self.assertEqual(self.service.student_home('1002'), ([], []))
        self.repo.review(tid, '1001', 'written', 2, 'Reviewed after closure', 0)
        self.assertEqual(self.service.history(tid, '1001')['score'], 8)

    def test_version_checks_on_edit_publish_submit_and_review(self):
        tid = self.make(publish=False)
        with self.assertRaises(TicketError): self.service.save(json.dumps(example()), ['all'], self.data.students, tid, 0)
        with self.assertRaises(TicketError): self.repo.change_status(tid, 0, 'published')
        self.repo.change_status(tid, 1, 'published')
        with self.assertRaises(TicketError): self.repo.submit(tid, '1001', 1, answers())
        self.repo.submit(tid, '1001', 2, answers())
        self.repo.review(tid, '1001', 'written', 0, '', 0)
        with self.assertRaises(TicketError): self.repo.review(tid, '1001', 'written', 1, '', 0)

    def test_manual_mark_range_and_pending_versus_zero(self):
        tid = self.make()
        self.repo.submit(tid, '1001', 2, answers())
        for score in (-1, 3, 'NaN', 'bad'):
            with self.subTest(score=score), self.assertRaises(TicketError): self.repo.review(tid, '1001', 'written', score, '', 0)
        self.repo.review(tid, '1001', 'written', 0, 'Try explaining the lattice.', 0)
        result = self.service.history(tid, '1001')
        self.assertEqual(result['pending'], 0)
        self.assertEqual(result['score'], 6)
        with self.assertRaises(TicketError): self.repo.review(tid, '1001', 'mcq', 1, '', 0)

    def test_session_cannot_change_identity_via_url_or_read_teacher_data(self):
        tid = self.make()
        self.repo.submit(tid, '1002', 2, dict(answers(), written='OTHER_STUDENT_SECRET'))
        student = self.simulated('1001')
        for url in ['/student/student1002', f'/student/student1002/history/{tid}', f'/student/student1002/tickets/{tid}',
                    '/', '/exit-tickets', f'/exit-tickets/{tid}/results', '/feedback/1002', '/preview/student1002.html']:
            response = student.get(url)
            self.assertEqual(response.status_code, 403, url)
            self.assertNotIn(b'OTHER_STUDENT_SECRET', response.data)
        self.assertEqual(student.get(f'/student/student1001/history/{tid}').status_code, 404)
        self.assertEqual(student.post('/simulation/student/1002', data=dict(csrf_token=self.csrf(student))).status_code, 403)
        self.assertEqual(student.post('/simulation/teacher', data=dict(csrf_token=self.csrf(student))).status_code, 303)
        self.assertEqual(student.get('/exit-tickets').status_code, 200)

    def test_draft_unassigned_and_unpublished_student_routes(self):
        tid = self.make(['student:1002'], publish=False)
        student = self.simulated('1001')
        self.assertEqual(student.get(f'/student/student1001/tickets/{tid}').status_code, 404)
        self.repo.change_status(tid, 1, 'published')
        self.assertEqual(student.get(f'/student/student1001/tickets/{tid}').status_code, 404)
        student2 = self.simulated('1002')
        self.repo.change_status(tid, 2, 'unpublished')
        self.assertEqual(self.post_answers(student2, '1002', tid).status_code, 404)

    def test_answer_keys_hidden_before_submission_and_review_opt_in(self):
        for reveal in (False, True):
            tid = self.make(reveal=reveal)
            student = self.simulated('1001')
            page = student.get(f'/student/student1001/tickets/{tid}')
            self.assertEqual(page.status_code, 200)
            self.assertNotIn(b'cation', page.data)
            self.assertNotIn(b'accepted_answers', page.data)
            self.assertNotIn(b'Teacher marking rules', page.data)
            response = self.post_answers(student, '1001', tid, dict(answers(), short='unknown'))
            self.assertEqual(b'Accepted answer:' in response.data, reveal)
            self.assertEqual(b'cation' in response.data, reveal)

    def test_form_validation_keeps_answers_and_no_partial_submission(self):
        tid = self.make()
        student = self.simulated('1001')
        response = self.post_answers(student, '1001', tid, dict(answers(), num='NaN', written='Keep this work'))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Keep this work', response.data)
        self.assertEqual(self.repo.submissions(tid), [])

    def test_mutations_require_csrf_and_escape_free_text(self):
        self.assertEqual(self.teacher.post('/exit-tickets/import', data=dict(source=json.dumps(example()))).status_code, 400)
        tid = self.make()
        student = self.simulated('1001')
        self.assertEqual(student.post(f'/student/student1001/tickets/{tid}', data={}).status_code, 400)
        response = self.post_answers(student, '1001', tid, dict(answers(), written='<script>answer</script>'))
        self.assertIn(b'&lt;script&gt;answer&lt;/script&gt;', response.data)
        self.repo.review(tid, '1001', 'written', 1, '<script>feedback</script>', 0)
        response = student.get(f'/student/student1001/history/{tid}')
        self.assertIn(b'&lt;script&gt;feedback&lt;/script&gt;', response.data)
        self.assertNotIn(b'<script>feedback', response.data)

    def test_teacher_drafts_and_other_student_feedback_never_enter_live_progress(self):
        from studentdash.workspace import Workspace
        workspace = Workspace(self.config.workspace)
        workspace.save_draft('1001', 'A1', 'TEACHER_DRAFT_SECRET', '', 0)
        workspace.save_draft('1002', 'A1', 'OTHER_LEARNER_FEEDBACK', '', 0)
        workspace.publish('1002', 'A1', 1)
        student = self.simulated('1001')
        for route in ['/student/student1001', '/student/student1001/progress']:
            response = student.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'TEACHER_DRAFT_SECRET', response.data)
            self.assertNotIn(b'OTHER_LEARNER_FEEDBACK', response.data)

    def test_seed_draft_is_repeatable_and_keeps_existing_work(self):
        from seed_exit_tickets import seed
        tid, created = seed(self.config)
        self.assertTrue(created)
        self.assertEqual(self.repo.get(tid)['status'], 'draft')
        again, created = seed(self.config)
        self.assertEqual(tid, again)
        self.assertFalse(created)
        self.assertEqual(self.repo.submissions(tid), [])


if __name__ == '__main__':
    unittest.main()
