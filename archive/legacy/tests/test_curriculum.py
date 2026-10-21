"""Generic curriculum behavior with fictional learners, questions and subject nodes."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from studentdash.config import ROOT, Config
from studentdash.curriculum import catalog, evidence_by_node, next_steps, node_index, resource_path
from studentdash.entry import ClassStore, EntryError, as_workbook, save_assessment, save_scores
from studentdash.render import generate_dashboards, render_student
from studentdash.teacher import create_app


def fictional_curriculum():
    return dict(schema=1, id='fictional', version='1', label='Fictional subject', nodes=[
        dict(id='root', label='Whole course', parent=None),
        dict(id='foundation', label='Foundation', parent='root'),
        dict(id='branch', label='Branch', parent='root'),
        dict(id='a', label='Topic A', parent='branch', prerequisites=['foundation']),
        dict(id='b', label='Topic B', parent='branch')], resources=[
            dict(id='warm', node_id='foundation', role='basic', title='Warm up', path='fictional/basic.html#start'),
            dict(id='try', node_id='a', role='practice', title='Try', path='fictional/practice.html'),
            dict(id='check', node_id='a', role='check', title='Check', path='fictional/check.html')])


class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional', 'PRIVATE ALPHA\nPRIVATE BETA',
                                     dict(categories={}, curriculum=fictional_curriculum()))
        self.key = self.doc['id']
        self.sids = [s['id'] for s in self.doc['students']]
        self.payload = dict(name='Fictional assessment', date='2026-01-01', participants=self.sids, questions=[
            dict(number='1', marks=5, text='Explain the fictional process.', tags={}, curriculum='Original raw label', curriculum_nodes=['a', 'b']),
            dict(number='2', marks=8, text='Another fictional question.', tags={}, curriculum='', curriculum_nodes=['b'])])
        self.aid = save_assessment(self.store, self.key, None, self.payload, self.doc['version'])
        save_scores(self.store, self.key, self.aid, [['1', 'P'], ['5', '0']], self.store.read(self.key)['version'])

    def data(self):
        return as_workbook(self.store.path(self.key))

    def test_three_steps_and_learner_scope(self):
        plan = next_steps(self.data(), self.sids[0])
        self.assertEqual(plan['focus']['number'], '1')
        self.assertEqual([s['resource_id'] for s in plan['steps']], ['warm', 'try', 'check'])
        self.assertEqual(next_steps(self.data(), self.sids[1])['focus']['number'], '2')
        html = render_student(self.data(), self.sids[0], False)
        self.assertIn('/practice/fictional/basic.html#start', html)
        self.assertNotIn('PRIVATE BETA', html)
        self.assertNotIn(self.sids[1], html)
        self.assertIsNone(next_steps(self.data(), self.sids[0], 'not-an-assessment')['focus'])

    def test_ancestor_rollup_deduplicates_multi_mapping(self):
        evidence = evidence_by_node(self.data(), self.sids[0])
        self.assertEqual((evidence['root']['score'], evidence['root']['maximum'], evidence['root']['count']), (1, 5, 1))
        self.assertEqual(evidence['branch']['maximum'], 5)
        self.assertEqual(evidence['b']['maximum'], 5)

    def test_no_inference_from_raw_labels_and_no_changes_to_marks(self):
        doc = self.store.read(self.key)
        for q in doc['assessments'][0]['questions']:
            q['curriculum_nodes'] = []
        self.store.save(doc, doc['version'])
        data = self.data()
        plan = next_steps(data, self.sids[0])
        self.assertIsNone(plan['focus'])
        self.assertEqual(plan['unmapped'], 1)
        self.assertEqual(next(iter(data.questions.values())).topic, 'Original raw label')
        self.assertEqual(data.question_results[0].score, 1)

    def test_statuses_and_full_marks_do_not_create_deficits(self):
        for status in ('A', 'E', 'M', 'P', '5'):
            save_scores(self.store, self.key, self.aid, [[status, '8'], ['5', '0']], self.store.read(self.key)['version'])
            self.assertIsNone(next_steps(self.data(), self.sids[0])['focus'])

    def test_editor_preserves_reviewed_ids_and_rejects_unknown_ids(self):
        doc = self.store.read(self.key)
        item = deepcopy(doc['assessments'][0])
        for q in item['questions']:
            del q['curriculum_nodes']
        save_assessment(self.store, self.key, self.aid, item, doc['version'])
        self.assertEqual(next_steps(self.data(), self.sids[0])['focus']['label'], 'Topic A')
        item['questions'][0]['curriculum_nodes'] = ['other-course']
        with self.assertRaises(EntryError):
            save_assessment(self.store, self.key, self.aid, item, self.store.read(self.key)['version'])

    def test_cycles_and_dangling_references(self):
        for relation, value in [('parent', 'a'), ('prerequisites', ['a']), ('prerequisites', ['unknown'])]:
            config = fictional_curriculum()
            config['nodes'][0][relation] = value
            if relation == 'prerequisites' and value == ['a']:
                config['nodes'][3]['prerequisites'] = ['root']
            with self.assertRaises(ValueError):
                node_index(config)

    def test_resource_path_rejects_external_and_traversal(self):
        for path in ('https://example.invalid/a.html', '../secret.html', 'x/../secret.html', '/x/a.html', 'x/%2e%2e/a.html', 'x\\a.html'):
            with self.assertRaises(ValueError):
                resource_path(path)

    def test_review_route_is_versioned_and_keeps_scores(self):
        app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        client = app.test_client()
        path = f'/classes/{self.key}/curriculum'
        self.assertEqual(client.get(path).status_code, 200)
        with client.session_transaction() as session:
            token = session['csrf_token']
        doc = self.store.read(self.key)
        original_scores = deepcopy(doc['assessments'][0]['scores'])
        qid = doc['assessments'][0]['questions'][0]['id']
        form = dict(csrf_token=token, version=doc['version'])
        form['node-' + qid] = ['a']
        self.assertEqual(client.post(path, data=form).status_code, 303)
        self.assertEqual(client.post(path, data=form).status_code, 400)
        saved = self.store.read(self.key)
        self.assertEqual(saved['assessments'][0]['scores'], original_scores)
        self.assertEqual(saved['assessments'][0]['questions'][0]['curriculum_history'][0]['previous'], ['a', 'b'])
        page = client.get(f'/classes/{self.key}/students/{self.sids[0]}/next')
        self.assertIn(b'Check independently', page.data)
        self.assertEqual(client.get(f'/classes/{self.key}/students/unknown/next').status_code, 404)
        with client.session_transaction() as session:
            session['simulated_student'] = 'fictional'
        self.assertEqual(client.get(path).status_code, 403)
        self.assertEqual(client.get(f'/classes/{self.key}/students/{self.sids[1]}/next').status_code, 403)

    def test_catalog_links_and_offline_copy(self):
        for curriculum in catalog().values():
            for r in curriculum['resources']:
                url = urlsplit(r['path'])
                source = ROOT / 'resources' / url.path
                self.assertTrue(source.is_file(), r['path'])
                if url.fragment:
                    self.assertIn(f'id="{url.fragment}"', source.read_text(encoding='utf-8'), r['path'])
        doc = self.store.read(self.key)
        curriculum = next(iter(catalog().values()))
        doc['profile']['curriculum'] = deepcopy(curriculum)
        target = next(r['node_id'] for r in curriculum['resources'] if r['role'] == 'practice')
        for q in doc['assessments'][0]['questions']:
            q['curriculum_nodes'] = [target]
        self.store.save(doc, doc['version'])
        config = Config(self.store.path(self.key), self.root / 'output')
        _, pages = generate_dashboards(config, False)
        html = (config.output / pages[0]).read_text(encoding='utf-8')
        self.assertIn('href="resources/', html)
        for r in curriculum['resources']:
            self.assertTrue((config.output / 'resources' / urlsplit(r['path']).path).is_file())
        client = create_app(Config(self.root / 'unused.xlsx', self.root / 'output')).test_client()
        path = urlsplit(curriculum['resources'][0]['path']).path
        with client.get('/practice/' + path) as response:
            self.assertEqual(response.status_code, 200)
        with client.get('/preview/resources/' + path) as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get('/practice/../studentdash/entry.py').status_code, 404)
