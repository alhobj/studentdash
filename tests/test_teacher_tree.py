"""Teacher-only endpoints project one learner, retaining zero and excluding absence."""
import json
from pathlib import Path
import tempfile
import unittest
from arborsynapse import create_app, ROOT
from studentdash.entry import ClassStore, save_assessment, save_scores
from studentdash.tree_export import question_signature


class TeacherTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)/'data'
        self.client = create_app(self.data).test_client()
        self.store = ClassStore(self.data/'entered_classes')
        self.doc = self.store.create('Fictional class', 'Alpha example\nBeta example')
        self.key = self.doc['id']
        self.sid, self.other = [s['id'] for s in self.doc['students']]
        self.node = json.loads((ROOT/'tree/local-package/curriculum.json').read_text())['nodes'][0]['id']
        aid = save_assessment(self.store, self.key, None, dict(name='Fictional test', date='2026-01-01',
            participants=[self.sid,self.other],questions=[dict(number='1',marks=2,text='',tags={},curriculum=''),
                dict(number='2b',marks=3,text='',tags={},curriculum='')]), self.doc['version'])
        save_scores(self.store, self.key, aid, [['1','3'],['0','A']], self.store.read(self.key)['version'])
        doc = self.store.read(self.key)
        questions = doc['assessments'][0]['questions']
        doc['local_tree'] = dict(mapping={q['id']:self.node for q in questions},
                                signatures={q['id']:question_signature(q) for q in questions})
        self.store.save(doc,doc['version'])
        self.url = f'/api/teacher-tree/classes/{self.key}'

    def test_roster_and_evidence_are_read_only_and_learner_scoped(self):
        before = self.store.read(self.key)
        self.assertEqual(self.client.get('/api/teacher-tree/classes').status_code,200)
        roster = self.client.get(self.url+'/students')
        self.assertEqual([s['name'] for s in roster.json['students']], ['Alpha example','Beta example'])
        self.assertTrue(all(set(s)=={'id','name'} for s in roster.json['students']))
        response = self.client.get(self.url+f'/students/{self.sid}/results')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual([a['date'] for a in response.json['assessments']], ['2026-01-01'])
        self.assertEqual({r['assessmentDate'] for r in response.json['evidence']}, {'2026-01-01'})
        evidence = response.json['evidence']
        self.assertEqual((sum(r['score'] for r in evidence),sum(r['maxScore'] for r in evidence)),(4,5))
        self.assertEqual({r['questionNumber'] for r in evidence},{'1','2b'})
        self.assertNotIn(self.other,response.text)
        self.assertNotIn('Beta example',response.text)
        other = self.client.get(self.url+f'/students/{self.other}/results').json['evidence']
        self.assertEqual(len(other),1)
        self.assertEqual((other[0]['score'],other[0]['maxScore']),(0,2))
        self.assertEqual(self.store.read(self.key),before)
        foreign = self.store.create('Other class','Foreign example')['students'][0]['id']
        self.assertEqual(self.client.get(self.url+f'/students/{foreign}/results').status_code,404)
        self.assertEqual(self.client.get(self.url+'/students',headers={'Host':'foreign.invalid'}).status_code,400)
        with self.client.session_transaction() as session:
            session['simulated_student']=self.sid
        self.assertEqual(self.client.get(self.url+'/students').status_code,403)

    def test_changed_or_broad_assignments_do_not_populate_statement_rings(self):
        doc = self.store.read(self.key)
        for q in doc['assessments'][0]['questions']:
            q['curriculum_nodes']=['broad-section']
        self.store.save(doc,doc['version'])
        result = self.client.get(self.url+f'/students/{self.sid}/results').json
        self.assertEqual(result['evidence'],[])
        self.assertEqual(result['unassignedGradedParts'],2)
