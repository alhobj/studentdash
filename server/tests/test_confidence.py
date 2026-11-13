"""Separate confidence persistence, reporting and reviewed historical correction."""
from copy import deepcopy
import json
import unittest
import test_metadata_assessment as fixtures
from studentdash import metadata_assessment as metadata
from studentdash.analytics import build_dashboard
from studentdash.assessment_types import filtered
from studentdash.confidence import CONFIG, correct_scored_question
from studentdash.config import Config, ROOT
from studentdash.entry import ClassStore, EntryError, as_workbook, save_scores, save_assessment, read_document
from studentdash.metadata_report import evidence
from studentdash.portability import backup_workspace, restore_workspace
from studentdash.render import generate_dashboards
from studentdash.freshness import fingerprints
from studentdash.teacher import create_app

class ConfidenceTests(unittest.TestCase):
    setUp=fixtures.MetadataTests.setUp
    payload=fixtures.MetadataTests.payload
    preview=fixtures.MetadataTests.preview
    commit=fixtures.MetadataTests.commit

    def imported(self):
        doc=self.store.read(self.key)
        doc['profile']['curriculum']={'nodes':[dict(id='fictional-root',label='Course',parent=None),dict(id='fictional-part',label='Part',parent='fictional-root')]}
        self.store.save(doc,doc['version'])
        payload=self.payload();payload.update(assessment_type='exit_ticket',confidence=deepcopy(CONFIG))
        payload['questions']=[dict(number=str(i),marks=1,tags={'CommandTerm':['Explain']},curriculum_nodes=['fictional-part'],scope='SL') for i in range(1,5)]
        aid=self.commit(self.preview(payload),payload)
        self.sids=[s['id'] for s in self.doc['students']]
        return aid

    def save(self,aid,ratings=None):
        save_scores(self.store,self.key,aid,[[1,1,1,0],[0,0,'A','P']],self.store.read(self.key)['version'],ratings)

    def test_exit_prompt_defaults_and_optional_schema(self):
        sample=json.loads((ROOT/'examples'/'exit-ticket-confidence.json').read_text())
        sample['class_id']=self.key
        parsed=metadata.parse(json.dumps(sample),self.key)
        self.assertEqual(sum(q['marks'] for q in parsed['questions']),4)
        self.assertEqual(parsed['confidence'],CONFIG)
        prompt=metadata.prompt(self.doc,'exit_ticket')
        for phrase in ['default to 1 mark','explicit printed marks','teacher override','ordinary assessments','not a scored question','Never include individual ratings']:
            self.assertIn(phrase,prompt)
        self.assertIn('\"marks\": 1',prompt)
        self.assertIn('\"marks\": 2',metadata.prompt(self.doc,'assessment'))
        aid=self.imported();self.save(aid,{self.sids[0]:2})
        data=as_workbook(self.store.path(self.key));view=build_dashboard(data,self.sids[0])
        self.assertEqual((view.history[0].score,view.history[0].maximum,view.history[0].confidence),(3,4,2))
        self.assertEqual(len(data.questions),4)
        payload=self.payload();payload['confidence']=dict(enabled=True,min=0,max=5)
        with self.assertRaises(EntryError):metadata.parse(json.dumps(payload),self.key)
        payload['confidence']=dict(CONFIG,ratings={self.sids[0]:3})
        with self.assertRaises(EntryError):metadata.parse(json.dumps(payload),self.key)

    def test_confidence_never_changes_performance(self):
        aid=self.imported();self.save(aid)
        before=as_workbook(self.store.path(self.key))
        report=evidence(before,self.sids[0]);view=build_dashboard(before,self.sids[0])
        self.save(aid,{self.sids[0]:1,self.sids[1]:5})
        after=as_workbook(self.store.path(self.key));new=build_dashboard(after,self.sids[0])
        self.assertEqual(evidence(after,self.sids[0]),report)
        self.assertEqual((view.overall_percent,view.total_score,view.total_possible,view.revision),(new.overall_percent,new.total_score,new.total_possible,new.revision))
        self.assertEqual(before.question_results,after.question_results)
        self.assertEqual(before.questions,after.questions)
        self.assertEqual(view.history[0].grade,new.history[0].grade)
        self.assertEqual(filtered(after,'exit_ticket').assessment_confidence[aid][self.sids[0]],1)

    def test_invalid_ratings_are_atomic_missing_is_distinct_and_clear(self):
        aid=self.imported();self.save(aid,{self.sids[0]:1})
        for invalid in [0,6,-1,True,False,1.5,1.0,'1.0','bad',[],{}]:
            before=self.store.read(self.key)
            with self.subTest(invalid=invalid),self.assertRaises(EntryError):self.save(aid,{self.sids[0]:invalid})
            self.assertEqual(before,self.store.read(self.key))
        self.assertNotIn(self.sids[1],self.store.read(self.key)['assessments'][0]['confidence_ratings'])
        self.save(aid,{self.sids[0]:''})
        self.assertEqual(self.store.read(self.key)['assessments'][0]['confidence_ratings'],{})
        with self.assertRaises(EntryError):self.save(aid,{'other-student':4})

    def test_reimport_score_update_restart_backup_and_freshness(self):
        aid=self.imported();self.save(aid,{self.sids[0]:2})
        config=Config(self.store.path(self.key),self.root/'output');before=fingerprints(config)
        self.save(aid,{self.sids[0]:4})
        self.assertNotEqual(before['workbook'],fingerprints(config)['workbook'])
        self.save(aid)  # Excel/pasted score updates do not include confidence fields.
        payload=self.payload();payload.update(assessment_id=aid,assessment_type='exit_ticket')
        payload['questions']=[dict(number=str(i),marks=1,tags={'CommandTerm':['Explain']},curriculum_nodes=['fictional-part'],scope='SL') for i in range(1,5)]
        self.commit(self.preview(payload),payload)
        self.store=ClassStore(self.root/'entered_classes')
        item=self.store.read(self.key)['assessments'][0]
        self.assertEqual(item['confidence_ratings'],{self.sids[0]:4})
        self.assertEqual(item['confidence'],CONFIG)
        save_assessment(self.store,self.key,aid,deepcopy(item),self.store.read(self.key)['version'])
        restored=restore_workspace(backup_workspace(config),self.root/'restored')
        self.assertEqual(read_document(restored.workbook)['assessments'][0]['confidence_ratings'],{self.sids[0]:4})
        self.assertEqual(len(self.store.read(self.key)['assessments']),1)

    def test_teacher_entry_snapshot_and_student_isolation(self):
        aid=self.imported();self.save(aid,{self.sids[0]:2})
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client()
        page=client.get(f'/classes/{self.key}/assessments/{aid}/scores')
        self.assertIn(b'Confidence: 2/5',page.data)
        self.assertIn(b'Not recorded',page.data)
        with client.session_transaction() as s:token=s['csrf_token']
        rows=[[1,1,1,0],[0,0,'A','P']]
        response=client.post(f'/classes/{self.key}/assessments/{aid}/scores',data=dict(
            csrf_token=token,version=self.store.read(self.key)['version'],payload=json.dumps(rows),
            **{'confidence-'+self.sids[0]:'4','confidence-'+self.sids[1]:''}))
        self.assertEqual(response.status_code,303)
        page=client.get(f'/?class_key={self.key}&assessment={aid}&assessment_type=exit_ticket')
        self.assertIn(b'Confidence: 4/5',page.data)
        config=Config(self.store.path(self.key),self.root/'output');generate_dashboards(config,False)
        own=(config.output/f'student{self.sids[0]}.html').read_text()
        other=(config.output/f'student{self.sids[1]}.html').read_text()
        self.assertIn('Confidence: 4/5',own)
        self.assertNotIn('Confidence: 4/5',other)
        self.assertIn('Confidence: Not recorded',other)
        self.assertNotIn('Fictional Beta',own)

    def test_legacy_scored_confidence_is_not_automatically_reinterpreted(self):
        payload=self.payload();payload['name']='Fictional exit check';payload['assessment_type']='exit_ticket'
        payload['questions']=[dict(number=str(i),marks=1,tags={},curriculum_nodes=[],scope='SL',name='Self-reported confidence' if i==5 else '') for i in range(1,6)]
        aid=self.commit(self.preview(payload),payload)
        sids=[s['id'] for s in self.doc['students']]
        save_scores(self.store,self.key,aid,[[1,1,1,0,1],[0,0,0,0,0]],self.store.read(self.key)['version'])
        self.commit(self.preview(payload),payload)
        item=self.store.read(self.key)['assessments'][0]
        self.assertEqual(len(item['questions']),5)
        self.assertFalse(item.get('confidence_ratings'))
        qid=item['questions'][-1]['id']
        correct_scored_question(self.store,self.key,aid,qid,self.store.read(self.key)['version'])
        view=build_dashboard(as_workbook(self.store.path(self.key)),sids[0])
        self.assertEqual((view.history[0].score,view.history[0].maximum,view.history[0].confidence),(3,4,None))
        item=self.store.read(self.key)['assessments'][0]
        save_assessment(self.store,self.key,aid,deepcopy(item),self.store.read(self.key)['version'])
        config=Config(self.store.path(self.key),self.root/'output')
        restored=restore_workspace(backup_workspace(config),self.root/'restored-correction')
        self.assertEqual(read_document(restored.workbook)['assessments'][0]['confidence_corrections'],item['confidence_corrections'])

    def test_reviewed_correction_archives_original_evidence(self):
        aid=self.imported();self.save(aid,{self.sids[0]:2})
        before=self.store.read(self.key);item=before['assessments'][0];qid=item['questions'][-1]['id']
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client()
        path=f'/classes/{self.key}/assessments/{aid}/confidence-correction'
        response=client.get(path+'?question='+qid)
        self.assertIn(b'Maximum marks change from 4',response.data)
        self.assertEqual(before,self.store.read(self.key))
        with client.session_transaction() as s:token=s['csrf_token']
        form=dict(csrf_token=token,version=before['version'],question=qid)
        self.assertEqual(client.post(path,data=form).status_code,400)
        self.assertEqual(before,self.store.read(self.key))
        form['confirm']='archive'
        self.assertEqual(client.post(path,data=form).status_code,303)
        after=self.store.read(self.key)['assessments'][0]
        archived=after['confidence_corrections'][0]
        self.assertEqual(archived['question'],item['questions'][-1])
        self.assertEqual(archived['scores'][self.sids[0]],item['scores'][self.sids[0]][qid])
        self.assertEqual(after['confidence_ratings'],{self.sids[0]:2})
        self.assertEqual(len(after['questions']),3)
        version=self.store.read(self.key)['version']
        with self.assertRaises(EntryError):correct_scored_question(self.store,self.key,aid,after['questions'][0]['id'],before['version'])
        self.assertEqual(self.store.read(self.key)['version'],version)
