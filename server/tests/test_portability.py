"""Fictional-course recovery and separation of public/private packages."""
from io import BytesIO
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from studentdash.config import Config
from studentdash.entry import ClassStore, as_workbook, save_assessment, save_scores
from studentdash.portability import PackageError, backup_workspace, practice_package, restore_workspace, student_package
from studentdash.workspace import Workspace
from studentdash.teacher import create_app
from studentdash.exit_store import TicketRepository
from studentdash.exit_schema import parse_ticket


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional course', 'PRIVATE_FIRST\nPRIVATE_OTHER')
        self.key = self.doc['id']
        self.sid = self.doc['students'][0]['id']
        self.config = Config(self.store.path(self.key), self.root / 'output')
        aid = save_assessment(self.store, self.key, None, dict(name='Fictional exam', date='2026-01-01',
            participants=[self.sid], questions=[dict(number='1', marks=2, text='Fictional task.', tags={}, curriculum='')]), self.doc['version'])
        save_scores(self.store, self.key, aid, [['1']], self.store.read(self.key)['version'])
        workspace = Workspace(self.config.workspace)
        workspace.save_draft(self.sid, aid, 'Fictional published feedback', 'Retry one task', 0)
        workspace.publish(self.sid, aid, 1)
        workspace.save_draft(self.sid, aid, 'Private unfinished feedback', 'New draft task', 2)
        doc = self.store.read(self.key)
        self.store.save(doc, doc['version'], ('fictional-source', 'source.txt', 'text/plain', b'Fictional original evidence'))
        repo = TicketRepository(self.config.workspace)
        self.ticket = repo.save(parse_ticket(json.dumps(dict(title='Fictional reflection', subject='Fictional subject',
            topic='Reasoning', subtopic='Comparison', questions=[dict(id='q', type='number', question='How many?',
                answer=2, marks=1, action_verb='State')]))), [self.sid])

    def test_backup_restores_original_results_and_workspace(self):
        before = self.config.workbook.read_bytes()
        blob = backup_workspace(self.config)
        restored = restore_workspace(blob, self.root / 'recovered')
        self.assertEqual(as_workbook(restored.workbook).question_results, as_workbook(self.config.workbook).question_results)
        self.assertEqual(Workspace(restored.workspace).export_state(), Workspace(self.config.workspace).export_state())
        self.assertEqual(TicketRepository(restored.workspace).list(), TicketRepository(self.config.workspace).list())
        with closing(sqlite3.connect(restored.workbook)) as db:
            self.assertEqual(db.execute('SELECT content FROM import_sources').fetchone()[0], b'Fictional original evidence')
        self.assertEqual(self.config.workbook.read_bytes(), before)
        with self.assertRaises(PackageError):
            restore_workspace(blob, self.root / 'recovered')

    def test_corruption_and_traversal_do_not_restore(self):
        original = backup_workspace(self.config)
        for extra in ('source.sdclass', '../outside.txt'):
            output = BytesIO()
            with ZipFile(BytesIO(original)) as source, ZipFile(output, 'w', ZIP_DEFLATED) as dest:
                for name in source.namelist():
                    dest.writestr(name, b'corrupt' if name == extra else source.read(name))
                if extra.startswith('..'):
                    dest.writestr(extra, b'bad')
            with self.assertRaises(PackageError):
                restore_workspace(output.getvalue(), self.root / 'invalid')
            self.assertFalse((self.root / 'invalid').exists())

    def test_public_and_single_student_packages(self):
        with ZipFile(BytesIO(practice_package())) as archive:
            self.assertIn('resources/ib-math-ai-sl/my-practice.html', archive.namelist())
            self.assertFalse(any(n.endswith(('.sqlite3', '.sdclass', '.xlsx')) for n in archive.namelist()))
            self.assertNotIn(b'PRIVATE_FIRST', archive.read('index.html'))
        with ZipFile(BytesIO(student_package(self.config, self.sid))) as archive:
            html = archive.read('index.html')
            self.assertNotIn(b'PRIVATE_OTHER', html)
            self.assertNotIn(self.doc['students'][1]['id'].encode(), html)
            self.assertEqual([n for n in archive.namelist() if n.endswith('.html') and '/' not in n], ['index.html'])
        with self.assertRaises(PackageError):
            student_package(self.config, 'unknown')

    def test_transfer_is_teacher_only_and_csrf_protected(self):
        app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        client = app.test_client()
        with client.session_transaction() as session:
            session['entered_class'] = self.key
        self.assertEqual(client.get('/transfer').status_code, 200)
        self.assertEqual(client.post('/transfer/download/backup').status_code, 400)
        with client.session_transaction() as session:
            token = session['csrf_token']
        with client.post('/transfer/download/backup', data={'csrf_token':token}) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'application/zip')
        original = self.config.workbook.read_bytes()
        response = client.post('/transfer', data={'csrf_token':token,
            'backup': (BytesIO(backup_workspace(self.config)), 'backup.zip')})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Open recovered class', response.data)
        self.assertEqual(self.config.workbook.read_bytes(), original)
        recovered = [doc for doc in self.store.list() if doc['id'] != self.key]
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]['restored_from'], self.key)
        with client.session_transaction() as session:
            session['simulated_student'] = self.sid
        self.assertEqual(client.get('/transfer').status_code, 403)
