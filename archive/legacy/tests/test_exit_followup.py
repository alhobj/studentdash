import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from create_example_workbook import create_example
from studentdash.config import Config
from studentdash.excel import read_workbook
from studentdash.exit_schema import TicketError, parse_ticket
from studentdash.exit_store import TicketRepository
from studentdash.exit_tickets import TicketService, progress_rows
from studentdash.teacher import create_app
from test_exit_tickets import example, answers


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        create_example(root / 'fictional.xlsx')
        self.config = Config(root / 'fictional.xlsx', root / 'output')
        self.data = read_workbook(self.config.workbook)
        self.repo = TicketRepository(self.config.workspace)
        self.service = TicketService(self.repo)
        self.tid = self.repo.save(parse_ticket(json.dumps(example())), ['1001', '1002'])
        self.repo.change_status(self.tid, 1, 'published')
        self.repo.submit(self.tid, '1001', 2, answers())

    def test_corrections_preserve_original_auto_score_and_audit(self):
        self.repo.review(self.tid, '1001', 'mcq', .5, 'Partial credit', 0, 'Mark scheme correction')
        row = next(a for a in self.repo.submission(self.tid, '1001')['answers'] if a['question_id'] == 'mcq')
        self.assertEqual(row['auto_score'], 1)
        self.assertEqual(row['teacher_score'], .5)
        self.repo.review(self.tid, '1001', 'mcq', 1, 'Restored', 1, 'Rechecked answer')
        events = [e for e in self.repo.audit(self.tid) if e['action'] == 'review']
        self.assertEqual(len(events), 2)
        self.assertEqual(json.loads(events[0]['before_json'])['teacher_score'], .5)
        with self.assertRaises(TicketError):
            self.repo.review(self.tid, '1001', 'mcq', 0, '', 1, 'Stale correction')
        self.assertEqual(len(self.repo.audit(self.tid)), 3)
        self.assertNotIn('Mark scheme correction', str(self.service.history(self.tid, '1001')))

    def test_manual_correction_requires_reason(self):
        self.repo.review(self.tid, '1001', 'written', 1, 'Initial review', 0)
        with self.assertRaises(TicketError):
            self.repo.review(self.tid, '1001', 'written', 2, '', 1)
        self.repo.review(self.tid, '1001', 'written', 2, 'Rechecked', 1, 'Missed a valid point')
        self.assertEqual(self.service.history(self.tid, '1001')['score'], 8)

    def test_release_policies_and_stale_version(self):
        self.assertFalse(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.set_release(self.tid, 2, 'marked', 'After marking')
        self.assertFalse(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.review(self.tid, '1001', 'written', 1, '', 0)
        self.assertTrue(self.service.history(self.tid, '1001')['allow_answer_review'])
        with self.assertRaises(TicketError):
            self.repo.set_release(self.tid, 2, 'immediate', 'Stale')
        self.repo.set_release(self.tid, 3, 'closed', 'Close first')
        self.assertFalse(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.change_status(self.tid, 4, 'unpublished')
        self.assertTrue(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.change_status(self.tid, 5, 'published')
        self.assertFalse(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.set_release(self.tid, 6, 'immediate', 'Discuss answers')
        self.assertTrue(self.service.history(self.tid, '1001')['allow_answer_review'])
        self.repo.set_release(self.tid, 7, 'hidden', 'Hide again')
        self.assertFalse(self.service.history(self.tid, '1001')['allow_answer_review'])
        with self.assertRaises(KeyError):
            self.service.history(self.tid, '1002')

    def test_retake_is_idempotent_isolated_and_excluded_from_aggregates(self):
        original = self.repo.submission(self.tid, '1001')
        child = self.repo.create_retake(self.tid, '1001', 2, 'Practise after feedback')
        self.assertEqual(child, self.repo.create_retake(self.tid, '1001', 2, 'Double click'))
        self.assertEqual(self.repo.get(child)['assignments'], ['1001'])
        self.assertEqual(self.repo.get(child)['release_mode'], 'hidden')
        with self.assertRaises(TicketError):
            self.repo.save(parse_ticket(json.dumps(example())), ['1002'], child, 1)
        self.repo.change_status(child, 1, 'published')
        with self.assertRaises(KeyError):
            self.service.available(child, '1002')
        self.repo.submit(child, '1001', 2, answers())
        self.repo.review(child, '1001', 'written', 2, '', 0)
        self.repo.review(self.tid, '1001', 'written', 1, '', 0)
        self.assertEqual(self.repo.submission(self.tid, '1001')['id'], original['id'])
        _, completed = self.service.student_home('1001')
        self.assertEqual(len(completed), 2)
        self.assertEqual(progress_rows(self.data, '1001', completed)[0]['count'], 1)
        grandchild = self.repo.create_retake(child, '1001', 2, 'Another practice')
        self.assertEqual(self.repo.get(grandchild)['retake_of'], child)

    def test_invalid_followups_do_not_write(self):
        for mode, reason in [('unknown', 'reason'), ('hidden', '')]:
            with self.assertRaises(TicketError):
                self.repo.set_release(self.tid, 2, mode, reason)
        with self.assertRaises(TicketError):
            self.repo.create_retake(self.tid, '1002', 2, 'No original')
        with self.assertRaises(TicketError):
            self.repo.create_retake(self.tid, '1001', 1, 'Stale')
        self.assertEqual(len(self.repo.list()), 1)

    def test_legacy_workspace_upgrade_preserves_submission(self):
        original = self.repo.submission(self.tid, '1001')
        with self.repo.connection(True) as db:
            for table in ('et_audit', 'et_retakes', 'et_release'):
                db.execute('DROP TABLE ' + table)
            db.execute('UPDATE et_tickets SET allow_answer_review=1 WHERE id=?', (self.tid,))
        reopened = TicketRepository(self.config.workspace)
        self.assertEqual(reopened.submission(self.tid, '1001'), original)
        self.assertEqual(reopened.get(self.tid)['release_mode'], 'immediate')
        self.assertEqual(reopened.audit(self.tid), [])

    def test_concurrent_retake_creation_returns_one_draft(self):
        def create(_):
            return TicketRepository(self.config.workspace).create_retake(self.tid, '1001', 2, 'Practice')
        with ThreadPoolExecutor(max_workers=2) as pool:
            children = list(pool.map(create, range(2)))
        self.assertEqual(children[0], children[1])
        self.assertEqual(len(self.repo.list()), 2)
        self.assertEqual(len([a for a in self.repo.audit(self.tid) if a['action'] == 'retake created']), 1)

    def test_controls_routes_csrf_isolation_and_escaping(self):
        app = create_app(self.config)
        app.config['TESTING'] = True
        teacher = app.test_client()
        teacher.get('/')
        with teacher.session_transaction() as session:
            csrf = session['csrf_token']
        path = f'/exit-tickets/{self.tid}/controls'
        self.assertEqual(teacher.get(path).status_code, 200)
        self.assertEqual(teacher.post(path, data={}).status_code, 400)
        response = teacher.post(path, data=dict(csrf_token=csrf, version=2, action='release', mode='hidden', reason='<script>private</script>'))
        self.assertEqual(response.status_code, 303)
        page = teacher.get(path).get_data(as_text=True)
        self.assertIn('&lt;script&gt;private', page)
        self.assertEqual(teacher.get(f'/exit-tickets/{self.tid}/review/1001').status_code, 200)
        response = teacher.post(path, data=dict(csrf_token=csrf, version=3, action='retake', student_id='1001', reason='Practice'))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(teacher.get(response.location).status_code, 200)
        teacher.post('/simulation/student/1001', data=dict(csrf_token=csrf))
        self.assertEqual(teacher.get(path).status_code, 403)
        self.assertEqual(teacher.post(path, data={}).status_code, 403)
        self.assertNotIn('private', teacher.get(f'/student/student1001/history/{self.tid}').get_data(as_text=True))
