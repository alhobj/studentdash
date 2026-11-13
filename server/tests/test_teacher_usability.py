from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
import unittest

from studentdash import metadata_assessment as metadata
from studentdash.assessment_import import create_draft, draft_by_id, save_review
from studentdash.chatgpt_assessment import save_response, SCHEMA
from studentdash.config import Config
from studentdash.curriculum import selected_curriculum
from studentdash.entry import ClassStore, EntryError, save_scores
from studentdash.import_drafts import delete
from studentdash.question_levels import settings
from studentdash.teacher import create_app
from tools.create_import_example import docx_bytes


class UsabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional Chemistry', 'Fictional Alpha\nFictional Beta')
        self.key = self.doc['id']
        self.app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        self.app.testing = True
        self.client = self.app.test_client()
        self.client.get(f'/classes/{self.key}')

    def csrf(self):
        with self.client.session_transaction() as s:
            return s['csrf_token']

    def payload(self):
        return dict(schema=metadata.SCHEMA, class_id=self.key, assessment_id=None, name='Fictional draft', date='2026-10-22',
            questions=[dict(number='1a', marks=2, tags={'CommandTerm':['Explain']}, curriculum_nodes=[], scope='BOTH')])

    def preview(self):
        return metadata.save_preview(self.store,self.key,json.dumps(self.payload()),self.store.read(self.key)['version'])

    def publish(self):
        did = self.preview()
        aid = metadata.commit(self.store,self.key,did,json.dumps(self.payload()),self.store.read(self.key)['version'])
        return did,aid

    def deletion_url(self,kind,did):
        return f'/classes/{self.key}/drafts/{kind}/{did}/delete'

    def test_shared_bar_on_teacher_pages_and_active_sections(self):
        did, aid = self.publish()
        sid = self.store.read(self.key)['students'][0]['id']
        paths = [('/classes','Classes'),(f'/classes/{self.key}','Classes'),
            (f'/classes/{self.key}?section=assessments','Assessments'),
            (f'/classes/{self.key}/import','Assessments'),
            (f'/classes/{self.key}/assessments/{aid}/scores','Assessments'),
            (f'/classes/{self.key}/assessments/{aid}/edit','Assessments'),
            (f'/classes/{self.key}/curriculum','Curriculum'),
            (f'/?class_key={self.key}&section=home','Studentdash'),
            (f'/?class_key={self.key}&section=students','Students'),
            (f'/transfer?class_key={self.key}','Settings'),
            (f'/feedback/{sid}?class_key={self.key}','Students'),
            (f'/classes/{self.key}/students/{sid}/next','Students'),
            ('/classes','Classes')]
        # Use the app's real registered paths for student-specific routes.
        with self.app.test_request_context():
            from flask import url_for
            paths[-3] = (url_for('feedback_editor',sid=sid,class_key=self.key),'Students')
            paths[-2] = (url_for('entry.student_next',key=self.key,sid=sid),'Students')
            paths[-1] = (url_for('entry.classes'),'Classes')
        for path, active in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code,200,response.data[:200])
                html = response.data.decode()
                self.assertEqual(html.count('aria-label="Teacher navigation"'),1)
                nav = html.split('<nav class="teacher-navigation"',1)[1].split('</nav>',1)[0]
                self.assertEqual(nav.count('aria-current="page"'),1)
                self.assertIn('aria-current="page">'+active+'</a>',nav)
                for title in ('Studentdash','Classes','Assessments','Students','Curriculum','Settings'):
                    self.assertIn('>'+title+'</a>',nav)
                self.assertNotIn('A clearer view',html)
                self.assertNotIn('Review saved results, generate snapshots',html)

    def test_class_context_survives_curriculum_settings_and_global_navigation(self):
        other = self.store.create('Other class','Other learner')
        self.client.get(f'/classes/{self.key}')
        response = self.client.get(f'/classes/{other["id"]}/curriculum')
        self.assertIn(other['id'].encode(),response.data)
        with self.client.session_transaction() as s:
            self.assertEqual(s['entered_class'],other['id'])
        response = self.client.get('/transfer')
        self.assertIn(f'class_key={other["id"]}'.encode(),response.data)
        self.assertIn(f'/classes/{other["id"]}?section=assessments'.encode(),response.data)

    def test_simplified_pages_and_student_actions(self):
        _, aid = self.publish()
        before = self.store.read(self.key)
        assessment_page = self.client.get(f'/classes/{self.key}?section=assessments').data
        self.assertNotIn(b'Preview next steps', assessment_page)
        self.assertNotIn(b'Add students', assessment_page)
        students = self.client.get(f'/?class_key={self.key}&section=students').data
        self.assertIn(b'Preview next steps', students)
        self.assertNotIn(b'Add students', students)
        self.assertIn(b'Add students', self.client.get(f'/classes/{self.key}').data)
        sid = before['students'][0]['id']
        self.assertIn(f'/classes/{self.key}/students/{sid}/next'.encode(), students)
        self.assertNotIn(b'Classroom practice', self.client.get('/transfer').data)
        curriculum = self.client.get(f'/classes/{self.key}/curriculum').data
        self.assertNotIn(b'Browse curriculum', curriculum)
        self.assertNotIn(b'Reviewed curriculum links', curriculum)
        editor = self.client.get(f'/classes/{self.key}/assessments/{aid}/edit').data
        self.assertIn(b'Curriculum parts', editor)
        self.assertNotIn(b'Review curriculum links', editor)
        self.assertEqual(before, self.store.read(self.key))
        response = self.client.post(f'/classes/{self.key}', data=dict(
            csrf_token=self.csrf(), version=before['version'], roster='Fictional Gamma', section='students'))
        self.assertEqual(response.status_code, 303)
        self.assertIn(f'/classes/{self.key}', response.location)
        self.assertIn(b'Fictional Gamma', self.client.get(response.location).data)
        self.assertEqual(before['assessments'], self.store.read(self.key)['assessments'])

    def test_curriculum_groups_preserve_evidence_and_explicit_hierarchy(self):
        from studentdash.entry import as_workbook
        from studentdash.overview import build_overview, curriculum_groups
        from studentdash.curriculum import node_index
        self.publish()
        data = as_workbook(self.store.path(self.key))
        data.curriculum = {'nodes': [dict(id='arbitrary', label='Foundations', parent=None), dict(id='unrelated-code', label='Applications', parent='arbitrary')]}
        nodes = node_index(data.curriculum)
        keys = list(nodes)[:2]
        learners, items = build_overview(data)
        item = items[0]
        data.question_curriculum[item.question_id] = keys + keys
        before = deepcopy((learners, items))
        grouped = curriculum_groups(data, items)
        self.assertEqual(len(grouped), 2)
        self.assertEqual({g['label'] for g in grouped}, {nodes[k]['label'] for k in keys})
        self.assertTrue(all(g['items'] == [item] for g in grouped))
        self.assertEqual(next(g for g in grouped if g['label'] == 'Applications')['path'], 'Foundations')
        self.assertEqual(before, build_overview(data))
        data.question_curriculum[item.question_id] = []
        self.assertEqual(curriculum_groups(data, items)[0]['label'], 'Unclassified')
        html = self.client.get(f'/?class_key={self.key}').data
        self.assertIn(b'<summary>Unclassified', html)

    def test_metadata_delete_confirmation_cancel_then_delete(self):
        did = self.preview()
        before = self.store.read(self.key)
        url = self.deletion_url('metadata',did)
        page = self.client.get(url)
        self.assertEqual(page.status_code,200)
        self.assertIn(b'Fictional draft',page.data)
        self.assertIn(b'>Cancel</a>',page.data)
        self.assertEqual(self.store.read(self.key),before)
        response = self.client.post(url,data=dict(csrf_token=self.csrf(),version=before['version'],confirm='cancel'))
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.store.read(self.key),before)
        response = self.client.post(url,data=dict(csrf_token=self.csrf(),version=before['version'],confirm='delete'),follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Deleted draft: Fictional draft',response.data)
        self.assertNotIn(f'/metadata/{did}'.encode(),response.data)
        self.assertFalse(self.store.read(self.key)['metadata_previews'])
        self.assertEqual(self.client.get(f'/classes/{self.key}/metadata/{did}').status_code,400)

    def test_deletion_requires_csrf_and_current_version(self):
        did = self.preview()
        old = self.store.read(self.key)['version']
        self.preview()
        url = self.deletion_url('metadata',did)
        before = self.store.read(self.key)
        self.assertEqual(self.client.post(url,data=dict(version=old,confirm='delete')).status_code,400)
        self.assertEqual(self.client.post(url,data=dict(csrf_token=self.csrf(),version=old,confirm='delete')).status_code,400)
        self.assertEqual(self.store.read(self.key),before)

    def test_published_assessment_scores_and_other_drafts_are_protected(self):
        did,aid = self.publish()
        doc = self.store.read(self.key)
        save_scores(self.store,self.key,aid,[[1],[0]],doc['version'])
        other = self.preview()
        before = self.store.read(self.key)
        response = self.client.post(self.deletion_url('metadata',did),data=dict(csrf_token=self.csrf(),version=before['version'],confirm='delete'))
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.store.read(self.key),before)
        delete(self.store,self.key,'metadata',other,before['version'])
        self.assertEqual(self.store.read(self.key)['assessments'],before['assessments'])
        self.assertEqual(self.store.read(self.key)['metadata_import_history'],before['metadata_import_history'])

    def test_document_delete_removes_original_and_all_owned_json_sources_only(self):
        did = create_draft(self.store,self.key,'fictional.docx',docx_bytes(['1. Explain a fact. [2]'],False))
        other = create_draft(self.store,self.key,'other.docx',docx_bytes(['1. State a fact. [1]'],False))
        original = self.store.source(self.key,other)
        payload = dict(schema=SCHEMA,class_id=self.key,title='Document draft',date='2026-10-22',document_total=2,
            questions=[dict(number='1',parent=None,scorable=True,text='Explain a fictional fact.',marks=2,tags={},curriculum_nodes=[])])
        for i in range(2):
            save_response(self.store,self.key,json.dumps(payload),self.store.read(self.key)['version'],did)
        doc = self.store.read(self.key)
        target = draft_by_id(doc,did)
        owned = {did,*target['chatgpt_source_ids']}
        self.preview()
        with self.assertRaises(EntryError):
            delete(self.store,self.key,'document',did,doc['version'])
        self.assertTrue(self.store.source(self.key,did))
        doc = self.store.read(self.key)
        delete(self.store,self.key,'document',did,doc['version'])
        self.assertEqual(self.store.source(self.key,other),original)
        for source in owned:
            with self.assertRaises(EntryError):self.store.source(self.key,source)
        self.assertEqual([d['id'] for d in self.store.read(self.key)['import_drafts']],[other])

    def test_published_document_cannot_be_deleted_and_source_is_kept(self):
        did = create_draft(self.store,self.key,'fictional.docx',docx_bytes(['1. State a fictional fact. [1]'],False))
        doc = self.store.read(self.key)
        draft = draft_by_id(doc,did)
        payload = dict(title=draft['title'],date=draft['date'],description=draft['description'],participants=draft['participants'],
            review_ack=True,warning_note='',nodes=[dict(n,reviewed=True) for n in draft['nodes']])
        save_review(self.store,self.key,did,payload,doc['version'],finalize=True)
        before = self.store.read(self.key)
        source = self.store.source(self.key,did)
        response = self.client.post(self.deletion_url('document',did),data=dict(csrf_token=self.csrf(),version=before['version'],confirm='delete'))
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.store.read(self.key),before)
        self.assertEqual(self.store.source(self.key,did),source)

    def test_single_level_from_config_hides_field_and_defaults_without_name_guessing(self):
        doc = self.store.read(self.key)
        doc['profile']['curriculum'] = selected_curriculum('math-ai-sl-2021')
        doc['name'] = 'Completely unrelated class name'
        self.store.save(doc,doc['version'])
        self.assertEqual(settings(self.store.read(self.key))['single'],'SL')
        did = self.preview()
        page = self.client.get(f'/classes/{self.key}/metadata/{did}')
        self.assertEqual(page.status_code,200)
        self.assertNotIn(b'class="metadata-scope"',page.data)
        self.assertIn(b'automatically SL',page.data)
        aid = metadata.commit(self.store,self.key,did,json.dumps(self.payload()),self.store.read(self.key)['version'])
        self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'][0]['scope'],'SL')

    def test_old_curriculum_snapshot_gets_additive_level_defaults(self):
        doc = self.store.read(self.key)
        doc['profile']['curriculum'] = selected_curriculum('math-ai-sl-2021')
        for field in ('course_levels','question_levels','question_level_labels','question_level_help'):
            doc['profile']['curriculum'].pop(field,None)
        self.store.save(doc,doc['version'])
        saved = self.store.read(self.key)
        self.assertEqual(settings(saved)['single'],'SL')
        self.assertEqual(self.store.read(self.key),saved)

    def test_mixed_question_level_options_and_settings_do_not_change_scores(self):
        did,aid = self.publish()
        doc = self.store.read(self.key)
        save_scores(self.store,self.key,aid,[[1],[0]],doc['version'])
        before = deepcopy(self.store.read(self.key)['assessments'])
        other = self.preview()
        page = self.client.get(f'/classes/{self.key}/metadata/{other}')
        self.assertIn(b'<label>Question level',page.data)
        self.assertIn(b'value="BOTH" selected>Both</option>',page.data)
        self.assertIn(b'questions for both levels',page.data)
        response = self.client.post(f'/classes/{self.key}',data=dict(csrf_token=self.csrf(),version=self.store.read(self.key)['version'],action='levels',course_levels='HL'),follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertEqual(settings(self.store.read(self.key))['single'],'HL')
        self.assertEqual(self.store.read(self.key)['assessments'],before)


@unittest.skipUnless(importlib.util.find_spec('playwright') and shutil.which('chromium'),'Optional Chromium check')
class NavigationBrowserTests(unittest.TestCase):
    setUp=UsabilityTests.setUp
    payload=UsabilityTests.payload
    preview=UsabilityTests.preview

    def test_navigation_mobile_context_delete_cancel_and_single_level_import(self):
        from playwright.sync_api import sync_playwright,expect
        from werkzeug.serving import make_server
        server=make_server('127.0.0.1',0,self.app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as runtime:
                browser=runtime.chromium.launch(executable_path=shutil.which('chromium'),headless=True)
                try:
                    page=browser.new_page(viewport=dict(width=375,height=812))
                    base=f'http://127.0.0.1:{server.server_port}'
                    page.goto(base+f'/classes/{self.key}')
                    nav=page.get_by_role('navigation',name='Teacher navigation')
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                    for name in ('Assessments','Students','Curriculum','Settings'):
                        nav.get_by_role('link',name=name,exact=True).click()
                        expect(nav.locator('[aria-current=page]')).to_have_text(name)
                        self.assertIn(self.key,page.url)
                        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                    did=self.preview()
                    page.goto(base+f'/classes/{self.key}')
                    page.get_by_role('link',name='Delete draft',exact=True).click()
                    expect(page.get_by_role('heading',name='Delete draft?',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Cancel',exact=True).click()
                    expect(page.get_by_role('link',name='Continue Fictional draft',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Delete draft',exact=True).click()
                    page.get_by_role('button',name='Delete draft',exact=True).click()
                    expect(page.get_by_role('status')).to_contain_text('Deleted draft')
                    self.assertEqual(page.get_by_role('link',name='Continue Fictional draft',exact=True).count(),0)
                    doc=self.store.read(self.key);doc['course_levels']=['SL'];self.store.save(doc,doc['version'])
                    did=self.preview();page.goto(base+f'/classes/{self.key}/metadata/{did}')
                    self.assertEqual(page.locator('.metadata-scope').count(),0)
                    page.get_by_role('button',name='Import assessment',exact=True).click()
                    expect(page.locator('#score-grid')).to_be_visible()
                    self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'][0]['scope'],'SL')
                    doc=self.store.read(self.key)
                    doc['profile']['curriculum']=selected_curriculum('math-ai-sl-2021')
                    self.store.save(doc,doc['version'])
                    aid=doc['assessments'][0]['id']
                    page.goto(base+f'/classes/{self.key}/assessments/{aid}/edit')
                    page.locator('summary').filter(has_text='Classify').first.click()
                    page.get_by_text('Curriculum parts',exact=True).click()
                    page.locator('.curriculum-nodes > .curriculum-group').first.locator('summary').first.click()
                    checkbox=page.locator('.curriculum-nodes input[value="math-ai-sl-2021:prior-signed"]')
                    node=checkbox.input_value();checkbox.check()
                    page.get_by_role('button',name='Save assessment & enter scores',exact=True).click()
                    expect(page.locator('#score-grid')).to_be_visible()
                    self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'][0]['curriculum_nodes'],[node])
                    page.goto(base+f'/?class_key={self.key}&section=students')
                    page.get_by_role('link',name='Preview next steps').first.click()
                    expect(page.get_by_role('navigation').locator('[aria-current=page]')).to_have_text('Students')
                finally:browser.close()
        finally:server.shutdown();thread.join(5);server.server_close()
