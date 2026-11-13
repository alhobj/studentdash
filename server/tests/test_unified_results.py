"""Fictional end-to-end coverage for unified assessment/exit-ticket results."""
from copy import deepcopy
import importlib.util
import json
import shutil
import threading
import unittest

import test_metadata_assessment as fixtures
from studentdash import metadata_assessment as metadata
from studentdash.assessment_types import filtered
from studentdash.config import Config
from studentdash.curriculum import selected_curriculum
from studentdash.curriculum_tree import tree
from studentdash.entry import ClassStore, EntryError, as_workbook, save_scores
from studentdash.metadata_report import evidence
from studentdash.analytics import build_dashboard
from studentdash.render import generate_dashboards, render_student
from studentdash.teacher import create_app
from studentdash.workspace import Workspace


class UnifiedResultsTests(unittest.TestCase):
    setUp = fixtures.MetadataTests.setUp
    payload = fixtures.MetadataTests.payload
    preview = fixtures.MetadataTests.preview
    commit = fixtures.MetadataTests.commit

    def import_kind(self, kind, name):
        payload = self.payload()
        payload.update(assessment_type=kind, name=name)
        return self.commit(self.preview(payload), payload)

    def test_types_persist_repeat_and_legacy_json_preserves_type(self):
        aid = self.import_kind('exit_ticket', 'Fictional short check')
        doc = self.store.read(self.key)
        save_scores(self.store, self.key, aid, [[1, 2], ['A', 'M']], doc['version'])
        before = self.store.read(self.key)['assessments'][0]
        payload = self.payload();payload['name'] = 'Fictional short check'
        self.commit(self.preview(payload), payload)
        after = self.store.read(self.key)['assessments'][0]
        # A legacy JSON update must retain the type in the editable HTML too.
        app=create_app(Config(self.root/'unused.xlsx', self.root/'output'))
        client=app.test_client();client.get(f'/classes/{self.key}')
        legacy_preview=self.preview(payload)
        html=client.get(f'/classes/{self.key}/metadata/{legacy_preview}').data.decode()
        self.assertIn('value="exit_ticket" selected', html)
        self.assertEqual(after['assessment_type'], 'exit_ticket')
        self.assertEqual(before['scores'], after['scores'])
        self.assertEqual(before['id'], after['id'])
        self.assertEqual(len(self.store.read(self.key)['assessments']), 1)
        self.store = ClassStore(self.root / 'entered_classes')
        self.assertEqual(self.store.read(self.key)['assessments'][0]['assessment_type'], 'exit_ticket')
        self.commit(self.preview())
        self.assertEqual(self.store.read(self.key)['assessments'][1]['assessment_type'], 'assessment')

    def test_prompt_selection_schema_validation_and_type_replacement(self):
        prompt = metadata.prompt(self.doc, 'exit_ticket')
        self.assertIn('"assessment_type": "exit_ticket"', prompt)
        for category, values in self.doc['profile']['categories'].items():
            self.assertIn(category, prompt)
            for value in values:
                self.assertIn(value, prompt)
        self.assertNotIn('Fictional Alpha', prompt)
        aid = self.import_kind('exit_ticket', 'Fictional check')
        payload = self.payload();payload.update(name='Fictional check', assessment_type='assessment')
        did = self.preview(payload)
        with self.assertRaises(EntryError):
            self.commit(did, payload)
        self.commit(did, payload, True)
        self.assertEqual(self.store.read(self.key)['assessments'][0]['id'], aid)
        for invalid in ['quiz', [], None]:
            payload['assessment_type'] = invalid
            with self.assertRaises(EntryError):
                metadata.parse(json.dumps(payload), self.key)

    def test_filters_do_not_mutate_data_or_overall_calculations(self):
        first = self.import_kind('assessment', 'Fictional full test')
        second = self.import_kind('exit_ticket', 'Fictional short check')
        save_scores(self.store, self.key, first, [[2, 3], [0, 'A']], self.store.read(self.key)['version'])
        save_scores(self.store, self.key, second, [[0, 0], ['P', 'E']], self.store.read(self.key)['version'])
        data = as_workbook(self.store.path(self.key));before=deepcopy(data)
        sid = self.doc['students'][0]['id']
        self.assertEqual(build_dashboard(data, sid).overall_percent, 50)
        self.assertEqual(build_dashboard(filtered(data, 'assessment'), sid).overall_percent, 100)
        self.assertEqual(build_dashboard(filtered(data, 'exit_ticket'), sid).overall_percent, 0)
        self.assertEqual(data, before)
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client()
        page=client.get(f'/classes/{self.key}?section=assessments&assessment_type=exit_ticket')
        self.assertIn(b'<h3>Fictional short check</h3>',page.data)
        self.assertNotIn(b'<h3>Fictional full test</h3>',page.data)
        page=client.get(f'/?class_key={self.key}&assessment_type=exit_ticket')
        self.assertEqual(page.status_code,200)
        self.assertIn(b'0.0%',page.data)
        self.assertEqual(client.get(f'/?class_key={self.key}&assessment_type=unknown').status_code,400)

    def test_curriculum_explicit_tree_and_ungraded_evidence(self):
        doc=self.store.read(self.key)
        doc['profile']['curriculum']=dict(nodes=[
            dict(id='container',label='Course',parent=None),
            dict(id='not-a-code',label='Region',parent='container'),
            dict(id='x',label='Part one',parent='not-a-code'),
            dict(id='y',label='Part two',parent='not-a-code'),
            dict(id='z',label='No evidence',parent='container')])
        self.store.save(doc,doc['version'])
        payload=self.payload();payload['questions'][0]['curriculum_nodes']=['x','y']
        aid=self.commit(self.preview(payload),payload)
        save_scores(self.store,self.key,aid,[[0,'P'],['A','E']],self.store.read(self.key)['version'])
        data=as_workbook(self.store.path(self.key));sid=doc['students'][0]['id']
        report=evidence(data,sid)
        region=report['curriculum_tree'][0]
        self.assertEqual(region['label'],'Region')
        self.assertEqual((region['evidence']['score'],region['evidence']['maximum'],region['evidence']['count']),(0,2,1))
        self.assertEqual(len(region['children']),2)
        self.assertIsNone(report['curriculum_tree'][1]['evidence'])
        self.assertEqual(report['unclassified']['ungraded'],1)
        self.assertEqual(report['groups']['CommandTerm']['unknown'],1)
        math=tree(selected_curriculum('math-ai-sl-2021'))
        self.assertEqual(len(math),6)  # Five regions and Prior learning; no root row.

    def test_snapshot_feedback_revision_privacy_and_old_manual_assessments(self):
        aid=self.commit(self.preview())
        doc=self.store.read(self.key);first,second=[s['id'] for s in doc['students']]
        save_scores(self.store,self.key,aid,[[0,1],[2,3]],doc['version'])
        config=Config(self.store.path(self.key),self.root/'output')
        workspace=Workspace(config.workspace)
        workspace.save_draft(first,aid,'Fictional private comment','Explain your reasoning',0)
        record=workspace.feedback(first,aid);workspace.publish(first,aid,record['version'])
        data,pages=generate_dashboards(config,False)
        html=(config.output/f'student{first}.html').read_text()
        other=(config.output/f'student{second}.html').read_text()
        self.assertIn('Fictional private comment',html)
        self.assertNotIn('Fictional private comment',other)
        self.assertNotIn('Fictional Beta',html)
        for removed in ['<progress','Classification performance','Question-level evidence','Prepare for a test',
                        'Record a revision attempt','Revision history','data-task=','Open warm up activity','Practise this focus']:
            self.assertNotIn(removed,html)
        self.assertIn('Skills and action verbs',html)
        self.assertIn('Suggested next steps',html)
        self.assertIn('Revisit your method',html)
        self.assertFalse((config.output/'resources').exists())
        # Older manual assessments use the same results-focused snapshot without migration.
        doc=self.store.read(self.key);doc['assessments'][0].pop('metadata_only');doc['assessments'][0].pop('assessment_type')
        self.store.save(doc,doc['version'])
        old=as_workbook(self.store.path(self.key))
        self.assertIn('Skills and action verbs',render_student(old,first,state=workspace.export_state()))
        self.assertEqual(old.assessments[aid].assessment_type,'assessment')

    def test_feedback_draft_preview_publication_and_restart(self):
        aid=self.commit(self.preview())
        sid=self.doc['students'][0]['id']
        config=Config(self.root/'unused.xlsx',self.root/'output')
        app=create_app(config);client=app.test_client()
        client.get(f'/classes/{self.key}')
        with client.session_transaction() as session:
            token=session['csrf_token']
        response=client.post(f'/feedback/{sid}/{aid}/draft',data=dict(
            csrf_token=token,version=0,comment='Fictional draft only',tasks='Revisit reasoning'))
        self.assertEqual(response.status_code,303)
        preview=client.get(f'/feedback/{sid}/{aid}/preview')
        self.assertIn(b'Teacher-only draft preview',preview.data)
        self.assertIn(b'Fictional draft only',preview.data)
        self.assertIn(b'Publish this saved draft',preview.data)
        actual=Config(self.store.path(self.key),self.root/'output'/('class-'+self.key))
        state=Workspace(actual.workspace).export_state()
        self.assertNotIn('Fictional draft only',render_student(as_workbook(actual.workbook),sid,state=state))
        record=Workspace(actual.workspace).feedback(sid,aid)
        self.assertEqual(client.post(f'/feedback/{sid}/{aid}/publish',data=dict(csrf_token=token,version=record['version'])).status_code,303)
        restarted=create_app(config).test_client()
        restarted.get(f'/classes/{self.key}')
        self.assertIn(b'Fictional draft only',restarted.get(f'/feedback/{sid}').data)
        self.assertIn('Fictional draft only',render_student(as_workbook(actual.workbook),sid,state=Workspace(actual.workspace).export_state()))

    def test_obsolete_controls_absent_and_settings_class_roster_available(self):
        self.commit(self.preview())
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client()
        page=client.get(f'/classes/{self.key}')
        self.assertIn(b'Add students',page.data)
        for removed in [b'Class planning',b'Teaching groups',b'Exit tickets']:
            self.assertNotIn(removed,page.data)
        self.assertNotIn(b'Add students',client.get(f'/?class_key={self.key}&section=students').data)
        self.assertEqual(client.get(f'/classes/{self.key}/learning').status_code,404)
        self.assertEqual(client.get('/exit-tickets').status_code,404)
        sid=self.doc['students'][0]['id']
        page=client.get(f'/feedback/{sid}?class_key={self.key}')
        self.assertIn(b'Teacher feedback draft',page.data)
        self.assertNotIn(b'Record a revision attempt',page.data)
        self.assertNotIn(b'Revision history',page.data)
