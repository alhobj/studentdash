"""Existing metadata import -> saved scores -> private combined package."""
import json
from pathlib import Path
import tempfile
import unittest

from studentdash import metadata_assessment as metadata
from studentdash.config import Config
from studentdash.entry import ClassStore, save_scores
from studentdash.teacher import create_app
from studentdash.tree_export import choices


class TreeExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional class', 'ALPHA_PRIVATE\nBETA_PRIVATE')
        self.key = self.doc['id']
        self.sid, self.other = [s['id'] for s in self.doc['students']]
        payload = dict(schema=metadata.SCHEMA, class_id=self.key, assessment_id=None,
                       name='Fictional assessment', date='2026-10-22', questions=[
                           dict(number='1', marks=2, tags={}, curriculum_nodes=[], scope=''),
                           dict(number='2a', marks=3, tags={}, curriculum_nodes=[], scope='')])
        did = metadata.save_preview(self.store, self.key, json.dumps(payload), self.doc['version'])
        metadata.commit(self.store, self.key, did, json.dumps(payload), self.store.read(self.key)['version'])
        self.a = self.store.read(self.key)['assessments'][0]
        save_scores(self.store, self.key, self.a['id'], [['1', '3'], ['0', 'A']], self.store.read(self.key)['version'])
        self.viewer = self.root / 'viewer'
        self.viewer.mkdir()
        self.registry = dict(mapId='chemistree', mapVersion='2.0', nodes=[dict(id='node-one', code='Exact 1', title='Fictional node')])
        (self.viewer / 'curriculum.json').write_text(json.dumps(self.registry))
        (self.viewer / 'assets-manifest.json').write_text('[]')
        (self.viewer / 'app').mkdir()
        for name in ['app/index.html', 'Start.cmd', 'Start.ps1', 'serve.py', 'LOCAL_STUDENT_GUIDE.md']:
            (self.viewer / name).write_text('fictional viewer asset')
        self.client = create_app(Config(self.root / 'unused.xlsx', self.root / 'output')).test_client()
        self.url = f'/classes/{self.key}/chemistree'
        self.client.get(f'/classes/{self.key}')
        with self.client.session_transaction() as session:
            self.csrf = session['csrf_token']
        self.destination = self.root / 'alpha'

    def post(self, action='export', **updates):
        form = dict(action=action, csrf_token=self.csrf, version=str(self.store.read(self.key)['version']),
                    viewer=str(self.viewer), destination=str(self.destination), student_id=self.sid)
        form.update({'node-' + q['id']: 'node-one' for q in self.a['questions']})
        form.update(updates)
        return self.client.post(self.url, data=form)

    def test_saved_metadata_scores_export_and_update_keep_package_identity(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.post()
        self.assertEqual(response.status_code, 200, response.text)
        results = json.loads((self.destination / 'results.json').read_text())
        self.assertEqual((sum(r['score'] for r in results['evidence']), sum(r['maxScore'] for r in results['evidence'])), (4, 5))
        html = (self.destination / 'studentdash.html').read_text()
        self.assertIn(self.sid, html)
        self.assertIn('4 / 5', html)
        self.assertNotIn(self.other, html)
        self.assertNotIn('BETA_PRIVATE', html)
        self.assertIn('http://127.0.0.1:8765/', html)
        self.assertFalse(list(self.destination.rglob('*.sdclass')))
        self.assertTrue((self.destination / 'Start Studentdash.cmd').is_file())
        # Exporter must not touch student-owned files, including confidence backups.
        backup = self.destination / 'confidence-backup.json'
        backup.write_text('student owned')
        self.post()
        same = json.loads((self.destination / 'results.json').read_text())
        self.assertEqual(same, results)
        save_scores(self.store, self.key, self.a['id'], [['2', '3'], ['0', 'A']], self.store.read(self.key)['version'])
        self.assertEqual(self.post().status_code, 200)
        updated = json.loads((self.destination / 'results.json').read_text())
        self.assertEqual(updated['packageId'], results['packageId'])
        self.assertEqual(updated['revision'], results['revision'] + 1)
        self.assertEqual(sum(r['score'] for r in updated['evidence']), 5)
        self.assertEqual(backup.read_text(), 'student owned')

    def test_non_graded_excluded_zero_retained_and_other_learner_refused(self):
        destination = self.root / 'beta'
        self.assertEqual(self.post(student_id=self.other, destination=str(destination)).status_code, 200)
        evidence = json.loads((destination / 'results.json').read_text())['evidence']
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]['score'], 0)
        response = self.post(destination=str(destination))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads((destination / 'results.json').read_text())['evidence'], evidence)

    def test_csrf_stale_versions_and_private_folder_protected(self):
        self.assertEqual(self.post(csrf_token='bad').status_code, 400)
        self.assertEqual(self.post(version='0').status_code, 400)
        self.assertFalse(self.destination.exists())
        self.assertEqual(self.post(destination=str(self.store.directory / 'export')).status_code, 400)
        self.assertEqual(self.post(destination='').status_code, 400)
        self.assertEqual(self.post(viewer=str(self.root / 'missing')).status_code, 400)

    def test_changed_objective_requires_review_again(self):
        self.assertEqual(self.post(action='save').status_code, 200)
        doc = self.store.read(self.key)
        self.assertEqual(choices(doc, self.registry)[0]['selected'], 'node-one')
        doc['assessments'][0]['questions'][0]['text'] = 'Changed objective'
        self.store.save(doc, doc['version'])
        changed = self.store.read(self.key)
        self.assertEqual(choices(changed, self.registry)[0]['selected'], '')
        self.assertEqual(choices(changed, self.registry)[1]['selected'], 'node-one')

    def test_saved_exclusions_and_ambiguous_links_do_not_become_evidence(self):
        q = self.a['questions'][0]
        doc = self.store.read(self.key)
        item = doc['assessments'][0]['questions'][0]
        item.update(curriculum_nodes=['node-one', 'broad-section'], curriculum_review={'status': 'reviewed'})
        self.assertEqual(choices(doc, self.registry)[0]['selected'], '')
        item['curriculum_nodes'] = ['node-one']
        self.assertEqual(choices(doc, self.registry)[0]['selected'], 'node-one')
        response = self.post(action='save', **{'node-' + q['id']: ''})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.store.read(self.key)['local_tree']['mapping'][q['id']], '')
        self.assertFalse(self.destination.exists())
