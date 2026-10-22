"""Course vocabulary upgrades and explicit curriculum selection with fictional data."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
import unittest
from studentdash.config import Config
from studentdash.curriculum import selected_curriculum
from studentdash.course_profile import effective
from studentdash.entry import ClassStore, EntryError, as_workbook, save_assessment, save_scores
from studentdash import metadata_assessment as metadata
from studentdash.render import generate_dashboards
from studentdash.teacher import create_app

class MathClassificationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=ClassStore(self.root/'entered_classes')
        self.captured=selected_curriculum('math-ai-sl-2021');self.captured.pop('profile',None);self.captured['categories']={}
        self.doc=self.store.create('Fictional mathematics','Fictional Alpha\nFictional Beta',dict(categories={},curriculum=deepcopy(self.captured)))
        self.key=self.doc['id']

    def raw(self):
        with sqlite3.connect(self.store.path(self.key)) as db:
            return json.loads(db.execute('SELECT body FROM class_document').fetchone()[0])

    def payload(self):
        return dict(schema=metadata.SCHEMA,class_id=self.key,assessment_id=None,assessment_type='exit_ticket',
            confidence=dict(enabled=True,min=1,max=5),name='Fictional classified check',date='2026-10-22',questions=[
                dict(number='1a',marks=1,tags={'CommandTerm':['Find','State']},curriculum_nodes=['math-ai-sl-2021:root','math-ai-sl-2021:1.2'],scope='SL'),
                dict(number='1b',marks=1,tags={},curriculum_nodes=['math-ai-sl-2021:2.1'],scope='SL')])

    def publish(self):
        p=self.payload();did=metadata.save_preview(self.store,self.key,json.dumps(p),self.store.read(self.key)['version'])
        aid=metadata.commit(self.store,self.key,did,json.dumps(p),self.store.read(self.key)['version'])
        return aid

    def test_existing_snapshot_read_is_additive_and_does_not_write(self):
        path=self.store.path(self.key);before=path.read_bytes();doc=self.store.read(self.key)
        self.assertEqual(doc['profile']['curriculum'],self.captured)
        self.assertEqual(doc['version'],1)
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(self.raw()['profile']['categories'],{})
        self.assertIn('Write down',doc['profile']['categories']['CommandTerm'])
        self.assertEqual(doc['profile']['command_category'],'CommandTerm')
        self.assertEqual(doc['profile']['category_options']['CommandTerm']['label'],'Action verbs')
        self.assertNotIn('Skill',doc['profile']['categories'])
        self.assertNotIn('ExperimentalSkill',doc['profile']['categories'])
        prompt=metadata.prompt(doc,'exit_ticket')
        for value in doc['profile']['categories']['CommandTerm']:self.assertIn(value,prompt)
        self.assertIn('"parent":',prompt);self.assertIn('Action verbs',prompt)
        self.assertNotIn('Fictional Alpha',prompt)

    def test_new_class_and_custom_configuration(self):
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client();client.get('/classes')
        with client.session_transaction() as s:token=s['csrf_token']
        result=client.post('/classes',data=dict(csrf_token=token,name='Fictional new maths',roster='Fictional Gamma',curriculum_id='math-ai-sl-2021'))
        self.assertEqual(result.status_code,303)
        created=next(d for d in self.store.list() if d['name']=='Fictional new maths')
        self.assertIn('Find',created['profile']['categories']['CommandTerm'])
        raw=dict(categories={'CommandTerm':['Custom verb'],'Custom category':['Custom tag']},
                 curriculum=deepcopy(self.captured),command_category='Custom category',
                 category_options={'CommandTerm':dict(label='Custom heading',multiple=False)})
        upgraded=effective(raw)
        self.assertEqual(raw['categories']['CommandTerm'],['Custom verb'])
        self.assertIn('Custom verb',upgraded['categories']['CommandTerm'])
        self.assertIn('Find',upgraded['categories']['CommandTerm'])
        self.assertEqual(upgraded['command_category'],'Custom category')
        self.assertEqual(upgraded['category_options']['CommandTerm'],dict(label='Custom heading',multiple=False))
        self.assertEqual(upgraded['curriculum'],raw['curriculum'])
        self.assertEqual(effective(upgraded),upgraded)
        other=deepcopy(raw);other['curriculum']['version']='unmatched'
        self.assertEqual(effective(other),other)
        saved=self.store.read(self.key)
        saved['profile']['categories']={'CommandTerm':['Custom verb']}
        self.store.save(saved,saved['version'])
        payload=self.payload();payload['questions'][0]['tags']={'CommandTerm':['Custom verb']}
        did=metadata.save_preview(self.store,self.key,json.dumps(payload),self.store.read(self.key)['version'])
        metadata.commit(self.store,self.key,did,json.dumps(payload),self.store.read(self.key)['version'])
        stored=self.store.read(self.key)['assessments'][0]
        self.assertEqual(stored['questions'][0]['tags'],{'CommandTerm':['Custom verb']})
        self.assertEqual(self.store.read(self.key)['profile']['curriculum'],self.captured)

    def test_import_edit_clear_reorder_scores_and_reporting(self):
        aid=self.publish();doc=self.store.read(self.key);item=deepcopy(doc['assessments'][0]);ids=[q['id'] for q in item['questions']]
        sid=doc['students'][0]['id']
        save_scores(self.store,self.key,aid,[[1,0],[0,1]],doc['version'],{sid:2})
        original=deepcopy(self.store.read(self.key)['assessments'][0])
        item=deepcopy(original);item['questions'].reverse();item['questions'][1]['tags']={}
        save_assessment(self.store,self.key,aid,item,self.store.read(self.key)['version'])
        stored=ClassStore(self.root/'entered_classes').read(self.key)['assessments'][0]
        self.assertEqual([q['id'] for q in stored['questions']],list(reversed(ids)))
        self.assertEqual(stored['questions'][1]['tags'],{})
        self.assertIn('math-ai-sl-2021:root',stored['questions'][1]['curriculum_nodes'])
        self.assertEqual(stored['scores'],original['scores']);self.assertEqual(stored['confidence_ratings'],{sid:2})
        stored['questions'][0]['tags']={'CommandTerm':['Explain']}
        save_assessment(self.store,self.key,aid,stored,self.store.read(self.key)['version'])
        save_scores(self.store,self.key,aid,[[1,0],[0,1]],self.store.read(self.key)['version'])
        config=Config(self.store.path(self.key),self.root/'output');generate_dashboards(config,False)
        html=(config.output/f'student{sid}.html').read_text()
        self.assertIn('<summary>Action verbs</summary>',html);self.assertIn('Explain',html)
        self.assertNotIn('Fictional Beta',html)
        # Legacy empty tags do not overwrite a saved classification in JSON updates.
        p=self.payload();p['questions'][0]['tags']={};p['questions'][1]['tags']={}
        p['questions'].reverse()
        did=metadata.save_preview(self.store,self.key,json.dumps(p),self.store.read(self.key)['version'])
        metadata.commit(self.store,self.key,did,json.dumps(p),self.store.read(self.key)['version'])
        self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'][0]['tags'],{'CommandTerm':['Explain']})
        current=deepcopy(self.store.read(self.key)['assessments'][0])
        original_scores=deepcopy(current['scores'])
        target=next(q for q in current['questions'] if q['number']=='1a')
        target['curriculum_nodes'].remove('math-ai-sl-2021:root')
        save_assessment(self.store,self.key,aid,current,self.store.read(self.key)['version'])
        restarted=ClassStore(self.root/'entered_classes').read(self.key)['assessments'][0]
        self.assertNotIn('math-ai-sl-2021:root',next(q for q in restarted['questions'] if q['number']=='1a')['curriculum_nodes'])
        self.assertEqual(restarted['scores'],original_scores)

    def test_single_value_category_rejects_multiple_without_mutation(self):
        aid=self.publish();doc=self.store.read(self.key)
        doc['profile']['category_options']['CommandTerm']['multiple']=False
        self.store.save(doc,doc['version']);before=self.store.read(self.key)
        with self.assertRaises(EntryError):save_assessment(self.store,self.key,aid,deepcopy(before['assessments'][0]),before['version'])
        self.assertEqual(before,self.store.read(self.key))

    @unittest.skipUnless(importlib.util.find_spec('playwright') and shutil.which('chromium'),'Optional Chromium check')
    def test_browser_grouped_import_editor_and_preserved_references(self):
        from playwright.sync_api import sync_playwright,expect
        from werkzeug.serving import make_server
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));server=make_server('127.0.0.1',0,app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as runtime:
                browser=runtime.chromium.launch(executable_path=shutil.which('chromium'),headless=True)
                try:
                    page=browser.new_page(viewport=dict(width=375,height=812));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    base=f'http://127.0.0.1:{server.server_port}'
                    page.goto(base+f'/classes/{self.key}/import')
                    self.assertIn('Find',page.locator('#chatgpt-prompt').input_value())
                    page.get_by_label('Paste ChatGPT response',exact=True).fill(json.dumps(self.payload()))
                    page.get_by_role('button',name='Preview assessment',exact=True).click()
                    row=page.locator('.metadata-question').first
                    row.get_by_text('Curriculum parts',exact=True).click()
                    expect(row.locator('.metadata-curriculum > .curriculum-group')).to_have_count(6)
                    expect(page.locator('.metadata-question').nth(1).locator('.saved-container')).not_to_be_visible()
                    expect(row.get_by_text('Existing broad reference:',exact=False)).to_be_visible()
                    self.assertIn('Arithmetic sequences',row.locator('.metadata-selected-curriculum').inner_text())
                    page.get_by_role('button',name='Import assessment',exact=True).click()
                    expect(page.locator('#score-grid')).to_be_visible()
                    aid=self.store.read(self.key)['assessments'][0]['id']
                    page.get_by_role('link',name='Edit questions & classifications',exact=True).click()
                    first=page.locator('#questions > tr').first
                    self.assertIn('Find',first.locator('.selected-classifications').inner_text())
                    self.assertIn('Arithmetic sequences',first.locator('.selected-classifications').inner_text())
                    first.locator('summary').filter(has_text='Classify').first.click()
                    first.get_by_text('Action verbs',exact=True).click()
                    first.locator('input[data-category="CommandTerm"][value="Find"]').uncheck()
                    first.locator('input[data-category="CommandTerm"][value="State"]').uncheck()
                    first.locator('input[data-category="CommandTerm"][value="Explain"]').check()
                    first.get_by_text('Curriculum parts',exact=True).click()
                    expect(first.locator('.curriculum-nodes > .curriculum-group')).to_have_count(6)
                    expect(first.locator('.saved-container')).to_be_visible()
                    expect(page.locator('#questions > tr').nth(1).locator('.saved-container')).not_to_be_visible()
                    first.locator('.curriculum-nodes > .curriculum-group').nth(2).locator('summary').first.click()
                    choice=first.locator('input[value="math-ai-sl-2021:2.2"]')
                    choice.focus();page.keyboard.press('Space');expect(choice).to_be_checked()
                    first.locator('.curriculum-nodes > .curriculum-group').nth(2).locator('summary').first.click()
                    self.assertIn('Functions, domains',first.locator('.selected-classifications').inner_text())
                    expect(first.locator('.tag-count')).to_have_text('(4)')  # One tag + three references.
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                    first.get_by_role('button',name='Move question down',exact=True).click()
                    page.get_by_role('button',name='Save assessment & enter scores',exact=True).click()
                    expect(page.locator('#score-grid')).to_be_visible()
                    item=self.store.read(self.key)['assessments'][0]
                    q=next(q for q in item['questions'] if q['number']=='1a')
                    self.assertEqual(q['tags'],{'CommandTerm':['Explain']})
                    self.assertIn('math-ai-sl-2021:root',q['curriculum_nodes'])
                    self.assertIn('math-ai-sl-2021:2.2',q['curriculum_nodes'])
                    self.assertEqual(errors,[])
                finally:browser.close()
        finally:server.shutdown();thread.join(5);server.server_close()
