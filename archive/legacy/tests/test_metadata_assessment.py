from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest

from studentdash import metadata_assessment as metadata
from studentdash.config import Config
from studentdash.entry import ClassStore, EntryError, save_scores, as_workbook, read_document
from studentdash.render import generate_dashboards
from studentdash.portability import backup_workspace, restore_workspace
from studentdash.teacher import create_app


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional class', 'Fictional Alpha\nFictional Beta')
        self.key = self.doc['id']

    def payload(self):
        return dict(schema=metadata.SCHEMA, class_id=self.key, assessment_id=None, name='Fictional assessment', date='2026-10-22',
            questions=[dict(number='*1a', marks=2, tags={'CommandTerm': ['Explain', 'Deduce'], 'Skill': ['Chemical reasoning']}, curriculum_nodes=[], scope='HL'),
                       dict(number='1b', marks=3, tags={}, curriculum_nodes=[], scope='')])

    def preview(self, payload=None):
        payload = payload or self.payload()
        return metadata.save_preview(self.store, self.key, json.dumps(payload), self.store.read(self.key)['version'])

    def commit(self, did, payload=None, replace=False):
        return metadata.commit(self.store, self.key, did, json.dumps(payload or self.payload()), self.store.read(self.key)['version'], replace)

    def test_prompt_is_metadata_only_and_class_specific(self):
        result = metadata.prompt(self.doc)
        self.assertIn(metadata.SCHEMA, result)
        self.assertIn(self.key, result)
        self.assertIn('Explain', result)
        self.assertIn('Do NOT include full question text', result)
        self.assertNotIn('Fictional Alpha', result)
        self.assertNotIn('Fictional Beta', result)

    def test_import_without_text_source_or_checkboxes_persists(self):
        did = self.preview()
        self.assertFalse(self.store.read(self.key)['assessments'])
        aid = self.commit(did)
        doc = ClassStore(self.root / 'entered_classes').read(self.key)
        item = doc['assessments'][0]
        self.assertEqual(item['id'], aid)
        self.assertEqual(item['questions'][0]['number'], '*1a')
        self.assertEqual(item['questions'][0]['text'], '')
        self.assertEqual(item['questions'][0]['scope'], 'HL')
        self.assertEqual(item['questions'][0]['tags']['CommandTerm'], ['Explain', 'Deduce'])
        self.assertEqual(item['scores'], {})
        from studentdash.overview import build_overview
        learners, questions = build_overview(as_workbook(self.store.path(self.key)))
        self.assertEqual(len(questions), 2)
        self.assertTrue(all(q.expected == 2 for q in questions))
        self.assertNotIn('import_source', item)
        with __import__('sqlite3').connect(self.store.path(self.key)) as db:
            self.assertFalse(db.execute("SELECT name FROM sqlite_master WHERE name='import_sources'").fetchall())

    def test_repeated_import_and_double_submit_keep_ids_and_scores(self):
        did = self.preview()
        aid = self.commit(did)
        doc = self.store.read(self.key)
        save_scores(self.store, self.key, aid, [[2, 1], [0, 'A']], doc['version'])
        before = self.store.read(self.key)['assessments'][0]
        self.assertEqual(self.commit(did), aid)
        other = self.preview()
        self.assertEqual(self.commit(other), aid)
        after = self.store.read(self.key)
        self.assertEqual(len(after['assessments']), 1)
        self.assertEqual(after['assessments'][0]['questions'], before['questions'])
        self.assertEqual(after['assessments'][0]['scores'], before['scores'])

    def test_missing_classifications_preserve_existing_on_updates(self):
        self.commit(self.preview())
        payload = self.payload()
        payload['questions'][0]['tags'] = {}
        payload['questions'][0]['scope'] = ''
        self.commit(self.preview(payload), payload)
        q = self.store.read(self.key)['assessments'][0]['questions'][0]
        self.assertEqual(q['tags']['Skill'], ['Chemical reasoning'])
        self.assertEqual(q['scope'], 'HL')

    def test_replacements_need_confirmation_and_keep_evidence(self):
        aid = self.commit(self.preview())
        doc = self.store.read(self.key)
        save_scores(self.store, self.key, aid, [[2, 1], [0, 'M']], doc['version'])
        old = self.store.read(self.key)['assessments'][0]
        payload = self.payload()
        payload['questions'][0]['marks'] = 4
        payload['questions'][0]['tags']['CommandTerm'] = ['Evaluate']
        did = self.preview(payload)
        with self.assertRaises(EntryError):
            self.commit(did, payload)
        self.commit(did, payload, replace=True)
        item = self.store.read(self.key)['assessments'][0]
        self.assertEqual(item['id'], aid)
        self.assertEqual(item['questions'][0]['id'], old['questions'][0]['id'])
        self.assertEqual(item['scores'], old['scores'])
        self.assertTrue(self.store.read(self.key)['metadata_import_history'][-1]['before'])

    def test_bad_metadata_preview_is_editable_and_invalid_import_is_atomic(self):
        for field, bad in [('marks', None), ('marks', -1), ('tags', {'Skill': ['Unknown']}),
                           ('curriculum_nodes', ['invented']), ('scope', 'unknown')]:
            payload = self.payload()
            payload['questions'][0][field] = bad
            did = self.preview(payload)
            before = self.store.read(self.key)
            with self.subTest(field=field), self.assertRaises(EntryError):
                self.commit(did, payload)
            self.assertEqual(self.store.read(self.key), before)
        payload = self.payload()
        payload['questions'][1]['number'] = '*1a'
        with self.assertRaises(EntryError):
            self.commit(self.preview(payload), payload)

    def test_stale_preview_and_unsafe_score_changes_are_rejected(self):
        aid = self.commit(self.preview())
        doc = self.store.read(self.key)
        save_scores(self.store, self.key, aid, [[2, 1], [0, 'E']], doc['version'])
        payload = self.payload()
        payload['questions'][0]['marks'] = 1
        with self.assertRaises(EntryError):
            self.commit(self.preview(payload), payload, replace=True)
        payload = self.payload()
        payload['questions'].pop(0)
        with self.assertRaises(EntryError):
            self.commit(self.preview(payload), payload, replace=True)
        did = self.preview()
        stale = self.store.read(self.key)['version']
        self.preview()
        with self.assertRaises(EntryError):
            metadata.commit(self.store, self.key, did, json.dumps(self.payload()), stale)

    def test_source_text_is_rejected_and_existing_text_is_not_destroyed(self):
        payload = self.payload()
        payload['questions'][0]['text'] = 'unnecessary source content'
        with self.assertRaises(EntryError):
            self.preview(payload)
        self.commit(self.preview())
        doc = self.store.read(self.key)
        doc['assessments'][0]['questions'][0]['text'] = 'Existing historical text'
        self.store.save(doc, doc['version'])
        self.commit(self.preview())
        self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'][0]['text'], 'Existing historical text')

    def test_text_free_scores_dashboards_backups_and_privacy(self):
        aid = self.commit(self.preview())
        doc = self.store.read(self.key)
        save_scores(self.store, self.key, aid, [[2, 1], [0, 'A']], doc['version'])
        doc = self.store.read(self.key)
        config = Config(self.store.path(self.key), self.root / 'output')
        data, pages = generate_dashboards(config, include_examples=False)
        first, second = (s['id'] for s in doc['students'])
        first_html = (config.output / f'student{first}.html').read_text()
        self.assertNotIn('Fictional Beta', first_html)
        self.assertNotIn(f'student{second}.html', first_html)
        self.assertIn('Skills and action verbs', first_html)
        self.assertIn('Chemical reasoning', first_html)
        self.assertNotIn('Exit tickets', first_html)
        self.assertNotIn('src=', first_html)
        self.assertNotIn('href=', first_html)
        self.assertTrue(data.question_tags)
        # Consistent legacy class/workspace backup includes the new metadata/history unchanged.
        backup = backup_workspace(config)
        restored = restore_workspace(backup, self.root / 'restored')
        self.assertEqual(read_document(restored.workbook)['assessments'], doc['assessments'])
        self.assertEqual(read_document(restored.workbook)['metadata_import_history'], doc['metadata_import_history'])
        save_scores(self.store, self.key, aid, [[1, 2], ['M', 0]], doc['version'])
        self.assertEqual(self.store.read(self.key)['assessments'][0]['questions'], doc['assessments'][0]['questions'])

    def test_multi_tag_and_explicit_ancestor_evidence_is_counted_once(self):
        doc = self.store.read(self.key)
        doc['profile']['curriculum'] = dict(nodes=[dict(id='root',label='Root',parent=None),
            dict(id='leaf',label='Leaf',parent='root')])
        self.store.save(doc, doc['version'])
        payload = self.payload()
        payload['questions'][0]['curriculum_nodes'] = ['root','leaf']
        aid = self.commit(self.preview(payload), payload)
        doc = self.store.read(self.key)
        save_scores(self.store,self.key,aid,[[2,'M'],[0,'A']],doc['version'])
        from studentdash.metadata_report import evidence
        data = as_workbook(self.store.path(self.key))
        own = evidence(data, doc['students'][0]['id'])
        self.assertEqual([(r['score'],r['maximum'],r['count']) for r in own['groups']['CommandTerm']['rows'] if r['count']],[(2,2,1),(2,2,1)])
        self.assertTrue(all(r['pattern']=='Insufficient evidence' for r in own['groups']['CommandTerm']['rows']))
        self.assertEqual([(r['score'],r['maximum'],r['count']) for r in own['syllabus']],[(2,2,1),(2,2,1)])

    def test_profile_and_arbitrary_curriculum_are_configuration(self):
        doc = self.store.read(self.key)
        doc['profile'] = dict(name='Fictional music', categories={'Technique': ['Listening']}, levels=['Foundation'],
            curriculum=dict(nodes=[dict(id='root', label='Music', parent=None),dict(id='leaf', label='Sound',parent='root')]))
        self.store.save(doc, doc['version'])
        payload = self.payload()
        payload['questions'][0].update(tags={'Technique':['Listening']},scope='Foundation',curriculum_nodes=['leaf'])
        self.commit(self.preview(payload), payload)
        q = self.store.read(self.key)['assessments'][0]['questions'][0]
        self.assertEqual(q['curriculum_nodes'], ['leaf'])
        self.assertEqual(q['tags'], {'Technique':['Listening']})


@unittest.skipUnless(importlib.util.find_spec('playwright') and shutil.which('chromium'), 'Optional Chromium check')
class MetadataBrowserTests(unittest.TestCase):
    setUp = MetadataTests.setUp
    payload = MetadataTests.payload

    def test_paste_edit_import_once_enter_scores_generate_and_reimport(self):
        from playwright.sync_api import sync_playwright, expect
        from werkzeug.serving import make_server
        app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        server = make_server('127.0.0.1', 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as runtime:
                browser = runtime.chromium.launch(executable_path=shutil.which('chromium'), headless=True)
                try:
                    context = browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
                    page = context.new_page()
                    base = f'http://127.0.0.1:{server.server_port}'
                    page.goto(base + f'/classes/{self.key}/import')
                    self.assertEqual(page.locator('input[type=file]').count(), 0)
                    page.get_by_label('Assessment type',exact=True).select_option('exit_ticket')
                    page.get_by_role('button',name='Update prompt',exact=True).click()
                    page.get_by_role('button',name='Copy prompt',exact=True).click()
                    self.assertIn(metadata.SCHEMA,page.evaluate('navigator.clipboard.readText()'))
                    self.assertIn('\"assessment_type\": \"exit_ticket\"',page.evaluate('navigator.clipboard.readText()'))
                    payload=self.payload();payload['assessment_type']='exit_ticket';payload['confidence']=dict(enabled=True,min=1,max=5)
                    page.get_by_label('Paste ChatGPT response',exact=True).fill(json.dumps(payload))
                    page.get_by_role('button',name='Preview assessment',exact=True).click()
                    expect(page.get_by_role('heading',name='Preview assessment',exact=True)).to_be_visible()
                    expect(page.locator('#metadata-total')).to_have_text('5')
                    expect(page.locator('#metadata-type')).to_have_value('exit_ticket')
                    self.assertEqual(page.locator('.question-reviewed').count(),0)
                    page.locator('.metadata-marks').nth(1).fill('4')
                    expect(page.locator('#metadata-total')).to_have_text('6')
                    page.get_by_role('button',name='Import assessment',exact=True).click()
                    expect(page.locator('#score-grid')).to_be_visible()
                    self.assertEqual(len(self.store.read(self.key)['assessments']),1)
                    self.assertEqual(self.store.read(self.key)['assessments'][0]['assessment_type'],'exit_ticket')
                    cells = page.locator('#score-grid input')
                    for i, score in enumerate(['2','3','0','A']): cells.nth(i).fill(score)
                    page.get_by_label('Fictional Alpha, confidence',exact=True).select_option('2')
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(page.get_by_text('Saved. You can close this page and continue later.',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Generate student dashboards',exact=True).click()
                    doc=self.store.read(self.key)
                    first=doc['students'][0]['id']
                    snapshot = self.root/'output'/('class-'+self.key)/f'student{first}.html'
                    self.assertTrue(snapshot.is_file())
                    offline = browser.new_context(offline=True)
                    offline_page = offline.new_page()
                    offline_page.set_content(snapshot.read_text())
                    expect(offline_page.get_by_role('heading',name='Skills and action verbs',exact=True)).to_be_visible()
                    self.assertNotIn('Fictional Beta', offline_page.locator('body').inner_text())
                    offline_page.set_viewport_size(dict(width=375,height=812))
                    self.assertTrue(offline_page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                    expect(offline_page.locator('.report-view:not([hidden]) table').first.locator('tbody tr')).to_have_count(1)
                    offline_page.get_by_label('Assessment type',exact=True).select_option('assessment')
                    expect(offline_page.get_by_text('No assessments in this view.',exact=True)).to_be_visible()
                    offline_page.get_by_label('Assessment type',exact=True).select_option('exit_ticket')
                    expect(offline_page.locator('.report-view:not([hidden]) table').first.locator('tbody tr')).to_have_count(1)
                    expect(offline_page.locator('.report-view:not([hidden])').get_by_text('Confidence: 2/5',exact=True)).to_be_visible()
                    self.assertNotIn('Question-level evidence',offline_page.locator('body').inner_text())
                    offline.close()
                finally:
                    browser.close()
        finally:
            server.shutdown(); thread.join(5); server.server_close()
