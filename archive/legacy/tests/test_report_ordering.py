"""Evidence-first presentation without changing calculations or curriculum structure."""
from copy import deepcopy
import json
import unittest
import test_metadata_assessment as fixtures
from studentdash import metadata_assessment as metadata
from studentdash.entry import as_workbook, save_scores
from studentdash.metadata_report import evidence
from studentdash.curriculum_tree import tree, selection
from studentdash.overview import build_overview, curriculum_groups
from studentdash.render import render_student, template_environment
from studentdash.assessment_types import filtered

class ReportOrderingTests(unittest.TestCase):
    setUp=fixtures.MetadataTests.setUp

    def prepared(self):
        doc=self.store.read(self.key)
        doc['profile']={'categories':{'Unused structure':['Shape'],'CommandTerm':['Unused','State','Find']},
            'curriculum':{'nodes':[
                dict(id='root',label='Course',parent=None),
                dict(id='empty-region',label='Untested region',parent='root'),
                dict(id='used-region',label='Tested region',parent='root'),
                dict(id='empty-part',label='Untested part',parent='used-region'),
                dict(id='used-part',label='Tested part',parent='used-region')]}}
        self.store.save(doc,doc['version'])
        payload={'schema':metadata.SCHEMA,'class_id':self.key,'assessment_id':None,'assessment_type':'exit_ticket',
            'name':'Fictional evidence check','date':'2026-10-24','questions':[
                dict(number='1',marks=1,tags={'CommandTerm':['Find']},curriculum_nodes=['used-part'],scope=''),
                dict(number='2',marks=1,tags={'CommandTerm':['State']},curriculum_nodes=['empty-part'],scope='')]}
        did=metadata.save_preview(self.store,self.key,json.dumps(payload),self.store.read(self.key)['version'])
        aid=metadata.commit(self.store,self.key,did,json.dumps(payload),self.store.read(self.key)['version'])
        save_scores(self.store,self.key,aid,[[0,'P'],['A','E']],self.store.read(self.key)['version'])
        return as_workbook(self.store.path(self.key)),[s['id'] for s in doc['students']]

    def test_tags_and_categories_put_no_graded_evidence_last(self):
        data,sids=self.prepared();before=deepcopy(data)
        report=evidence(data,sids[0])
        self.assertEqual(list(report['groups']),['CommandTerm','Unused structure'])
        rows=report['groups']['CommandTerm']['rows']
        self.assertEqual([r['label'] for r in rows],['Find','Unused','State'])
        self.assertEqual((rows[0]['score'],rows[0]['count'],rows[0]['percent']),(0,1,0))
        self.assertTrue(report['groups']['CommandTerm']['has_graded'])
        self.assertFalse(report['groups']['Unused structure']['has_graded'])
        self.assertEqual(rows[-1]['ungraded'],1)
        self.assertEqual(data,before)
        # The same student has no evidence after choosing the other type.
        empty=evidence(filtered(data,'assessment'),sids[0])
        self.assertEqual(list(empty['groups']),['Unused structure','CommandTerm'])
        self.assertFalse(any(group['has_graded'] for group in empty['groups'].values()))
        self.assertFalse(any(group['has_graded'] for group in evidence(data,sids[1])['groups'].values()))

    def test_curriculum_siblings_sort_but_selection_tree_keeps_course_order(self):
        data,sids=self.prepared();report=evidence(data,sids[0])
        groups=report['curriculum_tree']
        self.assertEqual([n['id'] for n in groups],['used-region','empty-region'])
        self.assertEqual([n['id'] for n in groups[0]['children']],['used-part','empty-part'])
        self.assertEqual(groups[0]['evidence']['count'],1)
        self.assertEqual([n['id'] for n in tree(data.curriculum)],['empty-region','used-region'])
        self.assertEqual([n['id'] for n in selection(data.curriculum)['groups']],['empty-region','used-region'])
        html=template_environment().get_template('curriculum_tree.html').module.display(groups)
        self.assertIn('class="curriculum-part curriculum-leaf no-graded-evidence"',html)
        self.assertIn('No graded evidence',html)
        self.assertIn('0/1',html)

    def test_render_and_teacher_review_are_muted_without_hiding_items(self):
        data,sids=self.prepared();html=render_student(data,sids[0])
        self.assertIn('class="no-graded-evidence"><td>Unused</td>',html)
        self.assertIn('Unused structure · No graded evidence',html)
        self.assertIn('Untested part',html)
        self.assertIn('No graded evidence',html)
        learners,items=build_overview(data)
        groups=curriculum_groups(data,items)
        self.assertEqual([g['label'] for g in groups],['Tested part','Untested part'])
        self.assertTrue(groups[0]['has_graded'])
        self.assertFalse(groups[1]['has_graded'])

    def test_leaf_curriculum_items_are_not_disclosures(self):
        data,sids=self.prepared()
        nodes=tree(data.curriculum)
        html=template_environment().get_template('curriculum_tree.html').module.display(nodes,False)
        self.assertEqual(html.count('<details'),1)  # Only the region with children expands.
        self.assertEqual(html.count('curriculum-leaf'),3)
        self.assertIn('Untested region',html)
        leaf=template_environment().get_template('curriculum_tree.html').module.display([nodes[0]],False)
        self.assertNotIn('<details',leaf)
        self.assertNotIn('<summary',leaf)

    def test_empty_categories_and_unclassified_have_no_expand_controls(self):
        doc=self.store.read(self.key)
        doc['profile']={'categories':{'Empty category':[]}}
        self.store.save(doc,doc['version'])
        data=as_workbook(self.store.path(self.key))
        html=render_student(data,doc['students'][0]['id'])
        self.assertIn('Empty category · No configured values',html)
        self.assertIn('Unclassified · No question evidence',html)
        self.assertNotIn('<details',html)
        from studentdash.config import Config
        from studentdash.teacher import create_app
        client=create_app(Config(self.root/'unused.xlsx',self.root/'output')).test_client()
        editor=client.get(f'/classes/{self.key}/assessments/new').data.decode()
        self.assertIn('Curriculum parts: none configured.',editor)
        self.assertNotIn('<summary>Curriculum parts</summary>',editor)
