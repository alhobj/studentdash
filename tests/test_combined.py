"""Combined routing, isolated teacher data, and fictional Atlas mode."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arborsynapse import create_app, ROOT


class CombinedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'

    def test_both_workspaces_and_navigation_share_one_address(self):
        app = create_app(self.data)
        client = app.test_client()
        page = client.get('/classes')
        self.assertEqual(page.status_code, 200)
        for href in ['/tree/', '/simple/', '/excel/']:
            self.assertIn(href, page.text)
        excel = client.get('/excel/', follow_redirects=True)
        self.assertEqual(excel.status_code, 200)
        self.assertIn('Excel workspace', excel.text)
        self.assertTrue((self.data / 'private/studentdash.sqlite3').is_file())
        self.assertEqual(client.get('/health').json['app'], 'ArborSynapse')
        self.assertEqual(client.get('/classes', headers={'Host':'foreign.invalid'}).status_code, 400)
        self.assertEqual(client.get('/excel/', headers={'Host':'foreign.invalid'}).status_code, 400)

    def test_only_built_tree_files_are_served(self):
        client = create_app(self.data).test_client()
        for prefix, folder in [('/tree/', ROOT/'tree/dist'), ('/simple/', ROOT/'tree/simple/dist')]:
            expected = 200 if (folder/'index.html').is_file() else 503
            with client.get(prefix) as response:
                self.assertEqual(response.status_code, expected)
                html = response.get_data(as_text=True)
            if expected == 200:
                import re
                source = re.search(r'src="\./([^\"]+\.js)"', html).group(1)
                with client.get(prefix + source) as response:
                    self.assertEqual(response.status_code, 200)
                self.assertEqual(client.get(prefix + '../src/data/map.json').status_code, 404)
                self.assertEqual(client.get(prefix + '../../arborsynapse.py').status_code, 404)
        self.assertEqual(client.get('/data/private/studentdash.sqlite3').status_code, 404)

    def test_atlas_demo_is_explicit_and_seed_is_idempotent(self):
        with patch.dict(os.environ, {'ARBOR_DEMO':'1', 'ARBOR_TEST_HOSTS':'atlas'}):
            client = create_app(self.data).test_client()
            self.assertEqual(client.get('/classes', headers={'Host':'atlas:5080'}).status_code, 200)
            self.assertEqual(client.get('/classes', headers={'Host':'foreign.invalid'}).status_code, 400)
            from studentdash.entry import ClassStore
            store = ClassStore(self.data/'entered_classes')
            first = store.list()
            self.assertEqual(len(first), 1)
            self.assertEqual([s['name'] for s in first[0]['students']], ['Demo learner A', 'Demo learner B'])
            create_app(self.data)
            self.assertEqual(store.list(), first)
        # Supplying a host allowlist alone must not expose the real teacher workspace.
        with patch.dict(os.environ, {'ARBOR_TEST_HOSTS':'atlas', 'ARBOR_DEMO':'0'}):
            self.assertEqual(create_app(self.data).test_client().get('/classes', headers={'Host':'atlas:5080'}).status_code, 400)

    def test_bundled_viewer_is_selected_without_manual_path(self):
        if not (ROOT/'tree/local-package/curriculum.json').is_file():
            self.skipTest('Run the combined tree build first')
        client = create_app(self.data).test_client()
        from studentdash.entry import ClassStore
        doc = ClassStore(self.data/'entered_classes').create('Fictional class', 'Fictional learner')
        page = client.get(f'/classes/{doc["id"]}/chemistree')
        self.assertEqual(page.status_code, 200)
        self.assertIn(str(ROOT/'tree/local-package'), page.text)
        self.assertIn('bundled viewer', page.text)

    def test_class_results_export_with_bundled_viewer_and_classifications(self):
        import json
        if not (ROOT/'tree/local-package/curriculum.json').is_file():
            self.skipTest('Run the combined tree build first')
        app = create_app(self.data)
        client = app.test_client()
        from studentdash.entry import ClassStore, save_assessment, save_scores
        store = ClassStore(self.data/'entered_classes')
        doc = store.create('Fictional class', 'Fictional learner')
        sid = doc['students'][0]['id']
        aid = save_assessment(store, doc['id'], None,
            dict(name='Fictional assessment', date='2026-01-01', participants=[sid],
                 questions=[dict(number='1', marks=5, text='', curriculum='', tags={'CommandTerm':['State']})]), doc['version'])
        doc = store.read(doc['id'])
        save_scores(store, doc['id'], aid, [['4']], doc['version'])
        doc = store.read(doc['id'])
        url = f'/classes/{doc["id"]}/chemistree'
        client.get(url)
        with client.session_transaction() as session:
            token = session['csrf_token']
        node = json.loads((ROOT/'tree/local-package/curriculum.json').read_text())['nodes'][0]['id']
        qid = doc['assessments'][0]['questions'][0]['id']
        target = Path(self.temp.name)/'learner'
        response = client.post(url, data=dict(action='export', csrf_token=token, version=doc['version'],
            student_id=sid, destination=str(target), **{'node-'+qid:node}))
        self.assertEqual(response.status_code, 200, response.text)
        results = json.loads((target/'results.json').read_text())
        self.assertEqual((results['evidence'][0]['score'], results['evidence'][0]['maxScore']), (4,5))
        classifications = json.loads((target/'classifications.json').read_text())
        self.assertEqual(classifications['questions'][0]['tags']['CommandTerm'], ['State'])
        self.assertIn('Question classifications', (target/'studentdash.html').read_text())
