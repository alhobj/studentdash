from copy import deepcopy
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest

from studentdash.assessment_import import create_draft, draft_by_id, save_review, validation
from studentdash.chatgpt_assessment import SCHEMA, parse_response, prompt, save_response
from studentdash.config import Config
from studentdash.entry import ClassStore, EntryError, as_workbook
from studentdash.teacher import create_app
from tools.create_import_example import docx_bytes


class ChatGPTAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ClassStore(self.root / 'entered_classes')
        self.doc = self.store.create('Fictional course', 'Fictional Learner\tprivate@example.invalid')
        self.key = self.doc['id']

    def response(self):
        return dict(schema=SCHEMA, class_id=self.key, title='Fictional test', date='2026-10-22',
            document_total=3, questions=[dict(number='1a', parent=None, text='Explain a fictional relationship.', marks=2,
            scorable=True, tags={'CommandTerm': ['Explain'], 'Skill': ['Chemical reasoning', 'Data interpretation']}, curriculum_nodes=[]),
            dict(number='1b', parent=None, text='State a fictional fact.', marks=1, scorable=True,
            tags={'CommandTerm': ['State']}, curriculum_nodes=[])])

    def paste(self, payload=None, did=None, version=None):
        return save_response(self.store, self.key, json.dumps(payload or self.response()),
                             version or self.store.read(self.key)['version'], did)

    def test_prompt_has_exact_format_vocabulary_and_no_roster(self):
        result = prompt(self.doc)
        self.assertIn(SCHEMA, result)
        self.assertIn('mark scheme', result)
        self.assertIn('Chemical reasoning', result)
        self.assertNotIn('Fictional Learner', result)
        self.assertNotIn('private@example.invalid', result)

    def test_full_assessment_can_be_created_without_per_question_edits(self):
        did = self.paste()
        doc = self.store.read(self.key)
        draft = draft_by_id(doc, did)
        self.assertEqual(validation(draft)['errors'], [])
        self.assertFalse(draft['review_ack'])
        self.assertFalse(any(n['reviewed'] for n in draft['nodes']))
        self.assertEqual(doc['assessments'], [])
        self.assertEqual(draft['nodes'][0]['tags']['Skill'], ['Chemical reasoning', 'Data interpretation'])
        review = dict(title=draft['title'], date=draft['date'], description=draft['description'],
            participants=draft['participants'], review_ack=True, warning_note='',
            nodes=[dict(n, reviewed=True) for n in draft['nodes']])
        aid = save_review(self.store, self.key, did, review, doc['version'], finalize=True)
        assessment = self.store.read(self.key)['assessments'][0]
        self.assertEqual(assessment['id'], aid)
        self.assertEqual([q['marks'] for q in assessment['questions']], [2, 1])
        self.assertEqual(assessment['questions'][0]['tags']['CommandTerm'], ['Explain'])
        self.assertEqual(assessment['scores'], {})
        self.assertTrue(as_workbook(self.store.path(self.key)).question_tags)

    def test_existing_document_original_is_preserved_and_question_ids_match(self):
        content = docx_bytes(['1a. Explain a relationship. [2]', '1b. State a fact. [1]'], False)
        did = create_draft(self.store, self.key, 'fictional.docx', content)
        prior = self.store.read(self.key)
        old_ids = {n['number']: n['id'] for n in draft_by_id(prior, did)['nodes']}
        self.paste(did=did)
        updated = self.store.read(self.key)
        draft = draft_by_id(updated, did)
        self.assertEqual(self.store.source(self.key, did)[2], content)
        for node in draft['nodes']:
            if node['number'] in old_ids:
                self.assertEqual(node['id'], old_ids[node['number']])
        self.assertEqual(len(updated['import_drafts']), 1)
        self.assertTrue(draft['chatgpt'])

    def test_fenced_json_supported(self):
        raw = '```json\n' + json.dumps(self.response()) + '\n```'
        self.assertEqual(parse_response(raw, self.key)['title'], 'Fictional test')

    def test_invalid_responses_leave_storage_unchanged(self):
        invalid = []
        for mutation in [lambda p: p.update(class_id='other'),
                         lambda p: p['questions'][0].update(tags={'Skill': ['Invented']}),
                         lambda p: p['questions'][0].update(parent='unknown'),
                         lambda p: p['questions'][0].update(marks=-1),
                         lambda p: p['questions'][0].update(curriculum_nodes=['invented']),
                         lambda p: p['questions'][1].update(number='1a'),
                         lambda p: p['questions'][0].update(tags={'Skill': [{}]}),
                         lambda p: p['questions'][0].update(parent='1b') or p['questions'][1].update(parent='1a')]:
            p = self.response()
            mutation(p)
            invalid.append(json.dumps(p))
        invalid.extend(['not json', '{"schema":NaN}', '{"schema":"one","schema":"two"}'])
        before = self.store.read(self.key)
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(EntryError):
                save_response(self.store, self.key, raw, before['version'])
            self.assertEqual(self.store.read(self.key), before)

    def test_unresolved_marks_need_review_not_invented(self):
        payload = self.response()
        payload['questions'][0]['marks'] = None
        payload['questions'][0]['notes'] = 'Figure needs comparison with original.'
        did = self.paste(payload)
        draft = draft_by_id(self.store.read(self.key), did)
        self.assertIsNone(draft['nodes'][0]['marks'])
        self.assertTrue(validation(draft)['errors'])
        self.assertIn('Figure needs comparison', draft['nodes'][0]['warnings'][0])

    def test_stale_version_cannot_overwrite_draft(self):
        did = self.paste()
        before = self.store.read(self.key)
        with self.assertRaises(EntryError):
            self.paste(did=did, version=before['version'] - 1)
        self.assertEqual(self.store.read(self.key), before)

    def test_routes_offer_prompt_and_paste_before_and_after_document_upload(self):
        app = create_app(Config(self.root / 'unused.xlsx', self.root / 'output'))
        client = app.test_client()
        url = f'/classes/{self.key}/import'
        response = client.get(url)
        self.assertIn(b'Copy prompt', response.data)
        self.assertIn(b'Paste ChatGPT response', response.data)
        with client.session_transaction() as session:
            csrf = session['csrf_token']
        response = client.post(url, data=dict(csrf_token=csrf, method='chatgpt', version=self.doc['version'], chatgpt_response=json.dumps(self.response())))
        self.assertEqual(response.status_code, 303)
        review = client.get(response.location)
        self.assertIn(b'I have reviewed all imported questions and marks', review.data)
        self.assertIn(b'Chemical reasoning', review.data)
        bad = client.post(response.location + '/chatgpt', data=dict(csrf_token=csrf,
            version=self.store.read(self.key)['version'], chatgpt_response='bad'))
        self.assertEqual(bad.status_code, 400)
        self.assertIn(b'>bad</textarea>', bad.data)


@unittest.skipUnless(importlib.util.find_spec('playwright') and shutil.which('chromium'), 'Optional system Chromium browser check')
class ChatGPTBrowserTests(unittest.TestCase):
    setUp = ChatGPTAssessmentTests.setUp
    response = ChatGPTAssessmentTests.response
    def test_copy_paste_preview_bulk_review_and_create(self):
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
                    did = create_draft(self.store, self.key, 'fictional.docx', docx_bytes(['1a. Explain a relationship. [2]', '1b. State a fact. [1]'], False))
                    page.goto(f'http://127.0.0.1:{server.server_port}/classes/{self.key}/imports/{did}')
                    page.get_by_role('button', name='Copy prompt', exact=True).click()
                    expect(page.locator('#chatgpt-copy-status')).to_contain_text('Prompt copied')
                    self.assertIn(SCHEMA, page.evaluate('navigator.clipboard.readText()'))
                    page.get_by_label('Paste ChatGPT response', exact=True).fill(json.dumps(self.response()))
                    page.get_by_role('button', name='Preview ChatGPT assessment', exact=True).click()
                    expect(page.get_by_role('heading', name='Review assessment import', exact=True)).to_be_visible()
                    expect(page.locator('.import-tags').first.get_by_label('Chemical reasoning', exact=True)).to_be_checked()
                    page.get_by_role('button', name='I have reviewed all imported questions and marks', exact=True).click()
                    page.locator('#review-ack').check()
                    page.get_by_role('button', name='Create assessment', exact=True).click()
                    expect(page.locator('.score-grid')).to_be_visible()
                    self.assertEqual(len(self.store.read(self.key)['assessments']), 1)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            thread.join(5)
            server.server_close()
