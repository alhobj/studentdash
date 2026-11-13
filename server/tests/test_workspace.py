import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from create_example_workbook import create_example
from studentdash.analytics import build_dashboard
from studentdash.config import Config
from studentdash.demo import create_classroom
from studentdash.excel import read_workbook, WorkbookError
from studentdash.freshness import fingerprints, stale_reasons
from studentdash.render import render_student, generate_dashboards
from studentdash.teacher import create_app
from studentdash.workspace import Workspace, WorkspaceError


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='studentdash-workspace-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'fictional.xlsx'
        create_example(self.path)
        self.config = Config(self.path, self.root / 'output')
        self.workspace = Workspace(self.config.workspace)
        self.data = read_workbook(self.path)

    def client(self):
        client = create_app(self.config).test_client()
        client.get('/')
        with client.session_transaction() as session:
            token = session['csrf_token']
        return client, token

    def test_draft_preview_publish_and_student_isolation(self):
        client, token = self.client()
        form = dict(csrf_token=token, version='0', comment='<script>FEEDBACK_A</script>', tasks='Retry Q2\nExplain charge balance')
        response = client.post('/feedback/1001/A1/draft', data=form)
        self.assertEqual(response.status_code, 303)
        self.assertNotIn('FEEDBACK_A', render_student(self.data, '1001', False, self.workspace.export_state()))
        preview = client.get('/feedback/1001/A1/preview')
        self.assertIn(b'Teacher-only draft preview', preview.data)
        self.assertIn(b'&lt;script&gt;FEEDBACK_A&lt;/script&gt;', preview.data)
        self.assertNotIn(b'Example learner B', preview.data)
        response = client.post('/feedback/1001/A1/publish', data=dict(csrf_token=token, version=1))
        self.assertEqual(response.status_code, 303)
        state = self.workspace.export_state()
        own = render_student(self.data, '1001', False, state)
        other = render_student(self.data, '1002', False, state)
        self.assertIn('FEEDBACK_A', own)
        self.assertNotIn('FEEDBACK_A', other)
        self.assertNotIn('Teacher-only draft preview', own)
        self.assertEqual(build_dashboard(self.data, '1001', False, 'A2', state).feedback, [])

    def test_unpublished_edits_keep_previous_publication(self):
        self.workspace.save_draft('1001', 'A1', 'Published first', 'Task first', 0)
        self.workspace.publish('1001', 'A1', 1)
        self.workspace.save_draft('1001', 'A1', 'Secret second draft', 'Task second', 2)
        html = render_student(self.data, '1001', False, self.workspace.export_state())
        self.assertIn('Published first', html)
        self.assertNotIn('Secret second draft', html)
        with self.assertRaises(WorkspaceError):
            self.workspace.publish('1001', 'A1', 1)
        with self.assertRaises(WorkspaceError):
            self.workspace.save_draft('1001', 'A1', 'Stale edit', '', 2)
        self.assertEqual(self.workspace.feedback('1001', 'A1')['comment'], 'Secret second draft')

    def test_publish_empty_removes_feedback(self):
        self.workspace.save_draft('1001', 'A1', 'Remove this', 'A task', 0)
        self.workspace.publish('1001', 'A1', 1)
        self.workspace.save_draft('1001', 'A1', '', '', 2)
        self.workspace.publish('1001', 'A1', 3)
        self.assertEqual(build_dashboard(self.data, '1001', False, workspace_state=self.workspace.export_state()).feedback, [])

    def test_mutations_require_csrf_and_valid_student_assessment(self):
        client, token = self.client()
        for path in ('draft', 'publish', 'attempts'):
            self.assertEqual(client.post(f'/feedback/1001/A1/{path}', data={}).status_code, 400)
        self.assertEqual(client.post('/feedback/unknown/A1/draft', data=dict(csrf_token=token, version=0)).status_code, 404)
        self.assertEqual(client.post('/feedback/1001/unknown/draft', data=dict(csrf_token=token, version=0)).status_code, 404)
        self.assertEqual(client.post('/feedback/1001/A1/draft', data=dict(csrf_token=token, version='bad')).status_code, 400)
        self.assertEqual(client.get('/feedback/unknown').status_code, 404)
        self.assertEqual(client.get('/feedback/1001?assessment=unknown').status_code, 404)

    def test_draft_limits(self):
        with self.assertRaises(WorkspaceError):
            self.workspace.save_draft('1001', 'A1', 'x' * 4001, '', 0)
        with self.assertRaises(WorkspaceError):
            self.workspace.save_draft('1001', 'A1', '', '\n'.join(['task'] * 11), 0)
        self.assertEqual(self.workspace.feedback('1001', 'A1')['version'], 0)

    def test_attempt_history_preserves_originals_and_grades(self):
        # Use an already completed assessment independent of when the suite is run.
        from dataclasses import replace
        from datetime import date
        self.data.assessments['A1'] = replace(self.data.assessments['A1'], date=date(2020, 1, 1))
        before = build_dashboard(self.data, '1001', False)
        self.workspace.add_attempt(self.data, '1001', 'A1', 'Q2', '2020-01-02', '2', 'Improved explanation')
        self.workspace.add_attempt(self.data, '1001', 'A1', 'Q2', '2020-01-03', '0', 'Retry without prompts')
        state = self.workspace.export_state()
        after = build_dashboard(self.data, '1001', False, workspace_state=state)
        self.assertEqual(after.history, before.history)
        self.assertEqual(after.total_score, before.total_score)
        self.assertEqual([a.change for a in after.attempts], [-1, 1])
        self.assertEqual([a.original for a in after.attempts], [1, 1])
        self.assertEqual(build_dashboard(self.data, '1002', False, workspace_state=state).attempts, [])
        self.assertEqual(build_dashboard(self.data, '1001', False, 'A2', state).attempts, [])
        self.assertEqual(len(Workspace(self.config.workspace).attempts()), 2)

    def test_attempt_validation(self):
        from dataclasses import replace
        from datetime import date
        self.data.assessments['A1'] = replace(self.data.assessments['A1'], date=date(2020, 1, 1))
        for score in ('nan', 'inf', '-1', '3', 'text'):
            with self.subTest(score=score), self.assertRaises(WorkspaceError):
                self.workspace.add_attempt(self.data, '1001', 'A1', 'Q2', '2020-01-02', score, '')
        for qid, day in [('Q5', '2020-01-02'), ('Q2', '2019-01-01'), ('Q2', 'invalid'), ('Q2', '2999-01-01')]:
            with self.subTest(qid=qid, day=day), self.assertRaises(WorkspaceError):
                self.workspace.add_attempt(self.data, '1001', 'A1', qid, day, '1', '')

    def test_freshness_excludes_drafts_and_identifies_published_changes(self):
        manifest = {'fingerprints': fingerprints(self.config)}
        self.workspace.save_draft('1001', 'A1', 'Draft', '', 0)
        self.assertEqual(stale_reasons(self.config, manifest), [])
        self.workspace.publish('1001', 'A1', 1)
        self.assertEqual(stale_reasons(self.config, manifest), ['Published teacher feedback has changed.'])
        self.assertTrue(stale_reasons(self.config, {}))
        sources = fingerprints(self.config)
        sources['templates'] = 'previous-template-version'
        self.assertEqual(stale_reasons(self.config, {'fingerprints': sources}), ['Student templates or rendering code have changed.'])
        sources = fingerprints(self.config)
        sources['attempts'] = 'previous-attempts'
        self.assertEqual(stale_reasons(self.config, {'fingerprints': sources}), ['Revision-attempt history has changed.'])

    def test_generation_rejects_inputs_changed_during_render(self):
        with patch('studentdash.render.fingerprints', side_effect=[{'version': 1}, {'version': 2}]):
            with self.assertRaisesRegex(WorkbookError, 'Inputs changed'):
                generate_dashboards(self.config)
        self.assertFalse(self.config.output.exists())

    def test_missing_or_modified_snapshots_are_named_for_refresh(self):
        import hashlib
        self.config.output.mkdir()
        html = render_student(self.data, '1001', False)
        (self.config.output / 'student1001.html').write_bytes(html.encode('utf-8'))
        manifest = dict(fingerprints=fingerprints(self.config), generated_at='test',
                        pages={'student1001.html': hashlib.sha256(html.encode()).hexdigest()})
        (self.config.output / 'generation.json').write_text(json.dumps(manifest), encoding='utf-8')
        client, _ = self.client()
        response = client.get('/')
        self.assertIn(b'1 snapshots need generation or refresh', response.data)
        (self.config.output / 'student1001.html').write_text('changed', encoding='utf-8')
        self.assertIn(b'2 snapshots need generation or refresh', client.get('/').data)

    def test_classroom_fixture_has_varied_history_and_revisions(self):
        path = self.root / 'classroom.xlsx'
        create_classroom(path)
        data = read_workbook(path)
        self.assertEqual(len(data.students), 24)
        self.assertEqual(len(data.assessments), 6)
        self.assertEqual(len(data.questions), 36)
        self.assertGreater(len(data.revision_attempts), 20)
        self.assertEqual({r.status for r in data.question_results}, {'graded', 'missing', 'pending', 'absent', 'exempt'})
        self.assertFalse(any('differs from Results' in warning for warning in data.warnings))
        self.assertTrue(build_dashboard(data, '2001', False).attempts)
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            create_classroom(path)
        self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
