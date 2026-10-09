"""Offline guided evidence, backups, graph mapping and class import isolation."""
import json
from pathlib import Path
from tests.test_learning_resources import LearningBrowserTests

ROOT = Path(__file__).resolve().parents[1]


class StudentToolsTests(LearningBrowserTests):
    def test_guided_unlock_restore_and_assistance(self):
        from playwright.sync_api import expect
        self.open(page='guided-practice.html')
        p = self.page
        q = p.evaluate('PRACTICE_CATALOG.questions.find(q=>q.kind==="guided")')
        host = p.locator('#guided-practice section').first
        expect(host.get_by_label('Substitute the values', exact=True)).to_be_disabled()
        host.get_by_label('Choose the equation', exact=True).select_option(q['steps'][0]['answer'])
        p.reload()
        expect(host.get_by_label('Substitute the values', exact=True)).to_be_disabled()
        host.get_by_role('button', name='Check step 1', exact=True).click()
        host.get_by_label('Substitute the values', exact=True).select_option(q['steps'][1]['answer'])
        host.get_by_role('button', name='Check step 2', exact=True).click()
        host.get_by_label('Calculate the numerical value', exact=True).fill(str(q['answer']))
        host.get_by_role('button', name='Check step 3', exact=True).click()
        host.get_by_label('State the unit', exact=True).fill(q['units'][0])
        host.get_by_role('button', name='Check step 4', exact=True).click()
        self.assertEqual(p.evaluate('(id)=>StudentPractice.status(id)', q['id']), 'Correct independently')
        p.reload()
        expect(host.get_by_text('All four steps correct.', exact=False)).to_be_visible()
        host.get_by_role('button', name='Start a fresh independent attempt').click()
        host.get_by_role('button', name='Hint for step 1', exact=True).click()
        for i, step in enumerate(q['steps']):
            value = step['answer']
            if step.get('options'):
                host.get_by_label(step['label'], exact=True).select_option(value)
            else:
                host.get_by_label(step['label'], exact=True).fill(str(value[0] if isinstance(value, list) else value))
            host.get_by_role('button', name=f'Check step {i+1}', exact=True).click()
        self.assertEqual(p.evaluate('(id)=>StudentPractice.status(id)', q['id']), 'Completed with help or retry')

    def test_combined_backup_and_class_isolation(self):
        from playwright.sync_api import expect
        self.open(page='student-backup.html')
        p = self.page
        qid = p.evaluate('PRACTICE_CATALOG.questions[0].id')
        profile = 'ib-math-ai-sl'
        noteid = p.evaluate('STUDENT_RECORD_PROFILES["ib-math-ai-sl"][0]')
        backup = dict(schema=1, type='studentdash-student-backup', name='Fictional learner',
                      progress=dict(schema=1, attempts=[dict(id='fixture-attempt', question=qid, answer='5', correct=False, assisted=False, at='2026-01-01T00:00:00Z')], drafts={}, positions={}, sessions={}, assignments={}),
                      skills={profile:dict(schema=1, profile=profile, notes={noteid:dict(answer='Fictional note', reviewed=True)})})
        path = Path(self.temp.name) / 'fictional.json'
        path.write_text(json.dumps(backup), encoding='utf-8')
        p.get_by_label('Preview combined backup', exact=True).set_input_files(path)
        expect(p.get_by_role('button', name='Import previewed backup')).to_be_enabled()
        p.get_by_role('button', name='Import previewed backup').click()
        expect(p.get_by_role('status').filter(has_text='Backup merged')).to_be_visible()
        self.assertIn('Fictional note', p.evaluate('localStorage.getItem("studentdash.skills.v1:ib-math-ai-sl")'))
        with p.expect_download() as event:
            p.get_by_role('button', name='Export combined backup').click()
        exported = json.loads(Path(event.value.path()).read_text())
        self.assertEqual(len(exported['progress']['attempts']), 1)
        self.open(page='class-practice.html')
        before = p.evaluate('localStorage.getItem("studentdash.practice.v1")')
        p.get_by_label('Import student files', exact=True).set_input_files(path)
        expect(p.get_by_text('By syllabus section', exact=True)).to_be_visible()
        expect(p.get_by_label('Student alias', exact=True)).to_have_value('Fictional learner')
        self.assertEqual(before, p.evaluate('localStorage.getItem("studentdash.practice.v1")'))
        p.get_by_label('Import student files', exact=True).set_input_files(path)
        expect(p.get_by_role('status').filter(has_text='already loaded')).to_be_visible()

    def test_graph_progress_does_not_invent_statement_mapping(self):
        from playwright.sync_api import expect
        self.open(profile='ib-chemistry', page='syllabus-graph.html')
        p = self.page
        p.evaluate('''()=>{const q=PRACTICE_CATALOG.questions.find(q=>q.topic==='S1.1');StudentPractice.recordChoice(q.id,'fixture',true,false);}''')
        p.locator('#graph-picker').select_option('S1.1')
        expect(p.locator('#graph-inspector').get_by_text('Correct independently: 1', exact=False)).to_be_visible()
        p.locator('#graph-picker').select_option('S1.1.1')
        expect(p.locator('#graph-inspector').get_by_text('No directly mapped questions.', exact=False)).to_be_visible()
    def test_guided_standalone_and_saved_assignment(self):
        from playwright.sync_api import expect
        self.open()
        p = self.page
        qid = p.evaluate('PRACTICE_CATALOG.questions.find(q=>q.kind==="guided").id')
        p.get_by_text('Choose questions or create a teacher assignment', exact=True).click()
        p.locator('.learning-list input[type=checkbox]').evaluate_all('(nodes,id)=>nodes.find(n=>n.value===id).click()', qid)
        with p.expect_download() as pending:
            p.get_by_role('button', name='Export standalone assignment page', exact=True).click()
        path = Path(self.temp.name) / 'guided.html'
        pending.value.save_as(path)
        p.reload()
        expect(p.get_by_label('Saved assignments', exact=True)).to_be_visible()
        p.goto(path.as_uri())
        expect(p.locator('#guided-practice section')).to_have_count(1)
        p.get_by_role('button', name='Start assignment', exact=True).click()
        expect(p.get_by_role('link', name='Open guided solution')).to_have_attribute('href', '#'+qid)
        q = p.evaluate('PRACTICE_CATALOG.questions[0]')
        host = p.locator('#guided-practice section')
        for i, step in enumerate(q['steps']):
            value = step['answer']
            if step.get('options'):
                host.get_by_label(step['label'], exact=True).select_option(value)
            else:
                host.get_by_label(step['label'], exact=True).fill(str(value[0] if isinstance(value, list) else value))
            host.get_by_role('button', name=f'Check step {i+1}', exact=True).click()
        self.assertEqual(p.evaluate('(id)=>StudentPractice.status(id)', qid), 'Correct independently')

    def test_invalid_backup_has_no_partial_writes(self):
        from playwright.sync_api import expect
        self.open(page='student-backup.html')
        p = self.page
        before = p.evaluate('JSON.stringify(Object.entries(localStorage))')
        bad = dict(schema=1, type='studentdash-student-backup', name='Fictional', progress=dict(schema=1, attempts=[], drafts={}, sessions={}, positions={}), skills={'unknown-profile':{}})
        path = Path(self.temp.name) / 'bad-backup.json'
        path.write_text(json.dumps(bad), encoding='utf-8')
        p.get_by_label('Preview combined backup', exact=True).set_input_files(path)
        expect(p.get_by_role('status').filter(has_text='unsupported subject')).to_be_visible()
        expect(p.get_by_role('button', name='Import previewed backup')).to_be_disabled()
        self.assertEqual(before, p.evaluate('JSON.stringify(Object.entries(localStorage))'))
