"""Fictional evidence isolation, teacher plans, and student learning workflows."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import unittest

from tests import test_curriculum as fixtures
from tests import test_learning_resources as browser_fixtures
from studentdash.learning import learner_context, intervention_rows, save_learning_plan
from studentdash.entry import EntryError
from studentdash.config import Config, ROOT
from studentdash.teacher import create_app
from studentdash.render import generate_dashboards


class LearningIntegrationTests(unittest.TestCase):
    setUp = fixtures.CurriculumTests.setUp
    data = fixtures.CurriculumTests.data

    def test_history_is_scoped_deduplicated_and_preserves_missing(self):
        data = self.data()
        context = learner_context(data, self.sids[0])
        self.assertEqual(len(context['events']), 2)
        graded = next(e for e in context['events'] if e['status']=='graded')
        self.assertEqual(graded['nodes'].count('root'), 1)
        self.assertIsNone(next(e for e in context['events'] if e['status']=='pending')['score'])
        self.assertNotIn(self.sids[1], json.dumps(context))
        rows = intervention_rows(data, 'b')
        self.assertEqual(rows[0]['suggestion'], 'Check first')
        self.assertEqual(rows[0]['count'], 1)

    def test_plans_are_versioned_and_only_reach_selected_students(self):
        doc = self.store.read(self.key)
        marks = deepcopy(doc['assessments'][0]['scores'])
        payload = dict(kind='exam', nodes=['a'], students=[self.sids[0]], title='Fictional upcoming test',
                       date=(date.today()+timedelta(days=10)).isoformat(), instructions='Practise the fictional model.')
        save_learning_plan(self.store, self.key, doc['version'], payload)
        self.assertEqual(self.store.read(self.key)['assessments'][0]['scores'], marks)
        self.assertEqual(len(learner_context(self.data(), self.sids[0])['exams']), 1)
        self.assertEqual(learner_context(self.data(), self.sids[1])['exams'], [])
        self.assertNotIn(self.sids[0], json.dumps(learner_context(self.data(), self.sids[1])))
        with self.assertRaises(EntryError):
            save_learning_plan(self.store, self.key, doc['version'], payload)
        for field,value in [('nodes',['foreign']),('students',['foreign']),('date','2000-01-01')]:
            with self.assertRaises(EntryError):
                save_learning_plan(self.store,self.key,self.store.read(self.key)['version'],dict(payload,**{field:value}))

    def test_teacher_workflow_and_session_guard(self):
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'))
        client=app.test_client()
        path=f'/classes/{self.key}/learning'
        self.assertEqual(client.get(path).status_code,200)
        with client.session_transaction() as s:
            csrf=s['csrf_token']
        form=dict(csrf_token=csrf, version=self.store.read(self.key)['version'], kind='intervention',nodes=['a'],students=[self.sids[0]],title='Fictional support',date=date.today().isoformat(),group='Group A',role='basic',instructions='Explain your method.')
        self.assertEqual(client.post(path,data=form).status_code,303)
        self.assertEqual(client.post(path,data=form).status_code,400)
        self.assertIn(b'Fictional support',client.get(path).data)
        with client.session_transaction() as s:
            s['simulated_student']=self.sids[0]
        self.assertEqual(client.get(path).status_code,403)

    def test_exit_ticket_history_does_not_release_keys_or_invent_links(self):
        ticket=dict(ticket_id='fixture',title='Fictional ticket',topic='Topic A',subtopic='Branch',date='2026-01-02',pending=1,score=0,maximum=2,answers=[dict(question={'question':'Fictional prompt','id':'q'},answer='My response',feedback='Teacher comment',score=None,correct_answer='SECRET KEY')])
        context=learner_context(self.data(),self.sids[0],completed=[ticket])
        event=next(e for e in context['events'] if e['source']=='Exit ticket')
        self.assertEqual(event['nodes'],[])
        self.assertIsNone(event['score'])
        self.assertNotIn('SECRET KEY',json.dumps(context))


    def test_selected_class_tickets_and_reviewed_links_reach_snapshot(self):
        from studentdash.exit_store import TicketRepository
        from studentdash.exit_schema import parse_ticket
        from studentdash.learning import completed_tickets
        from studentdash.freshness import fingerprints, stale_reasons
        config=Config(self.store.path(self.key),self.root/'output')
        repo=TicketRepository(config.workspace)
        definition=dict(title='Fictional follow-up',subject='Fictional',topic='Legacy wording',subtopic='Legacy part',questions=[dict(id='q',type='number',question='Fictional count?',answer=3,marks=1,action_verb='State')])
        tid=repo.save(parse_ticket(json.dumps(definition)),[self.sids[0]])
        repo.change_status(tid,repo.get(tid)['version'],'published')
        before={'fingerprints':fingerprints(config)}
        repo.submit(tid,self.sids[0],repo.get(tid)['version'],{'q':'3'})
        self.assertIn('Exit-ticket records have changed.',stale_reasons(config,before))
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'))
        client=app.test_client()
        path=f'/classes/{self.key}/learning'
        self.assertEqual(client.get(path).status_code,200)
        with client.session_transaction() as session:
            csrf=session['csrf_token']
        form={'csrf_token':csrf,'version':self.store.read(self.key)['version'],'action':'ticket-links','ticket-interactive:'+tid:['a']}
        self.assertEqual(client.post(path,data=form).status_code,303)
        context=learner_context(self.data(),self.sids[0],completed=completed_tickets(config.workspace,self.sids[0]))
        event=next(e for e in context['events'] if e['source']=='Exit ticket')
        self.assertIn('a',event['nodes'])
        self.assertEqual(event['score'],1)
        self.assertEqual(completed_tickets(config.workspace,self.sids[1]),[])
        response=client.post('/simulation/student/'+self.sids[0],data={'csrf_token':csrf})
        self.assertEqual(response.status_code,303)
        response=client.get('/student/student'+self.sids[0]+'/progress')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Fictional follow-up',response.data)
        self.assertNotIn(self.sids[1].encode(),response.data)
        generate_dashboards(config,False)
        manifest=json.loads((config.output/'generation.json').read_text())
        self.assertEqual(stale_reasons(config,manifest),[])


class LearningCentreBrowserTests(unittest.TestCase):
    setUp=browser_fixtures.LearningBrowserTests.setUp
    tearDown=browser_fixtures.LearningBrowserTests.tearDown
    open=browser_fixtures.LearningBrowserTests.open

    def test_home_reveals_questions_only_after_topic_choice(self):
        from playwright.sync_api import expect
        self.open(page='learning-home.html')
        p=self.page
        expect(p.locator('.choices button')).to_have_count(3)
        expect(p.get_by_role('heading',name='What would you like to do today?')).to_be_visible()
        self.assertEqual(p.locator('.learning-question').count(),0)
        p.get_by_role('button',name='Continue learning',exact=True).click()
        node=p.evaluate("JSON.parse(document.querySelector('#learning-context').textContent).nodes.find(n=>n.code==='1.2').id")
        p.get_by_label('Choose a topic to practise',exact=True).select_option(node)
        p.get_by_role('button',name='Show me five questions',exact=True).click()
        expect(p.locator('#student-centre ol li')).to_have_count(5)

    def test_revision_plan_persists_and_stays_inside_scope(self):
        from playwright.sync_api import expect
        self.open(page='learning-home.html')
        p=self.page
        p.get_by_role('button',name='Prepare for a test',exact=True).click()
        p.get_by_text('Choose the topics in this test',exact=True).click()
        node=p.evaluate("JSON.parse(document.querySelector('#learning-context').textContent).nodes.find(n=>n.code==='1.2').id")
        p.locator('input[type=checkbox]').evaluate_all('(items,id)=>items.find(i=>i.value===id).click()',node)
        p.get_by_label('Test date',exact=True).fill((date.today()+timedelta(days=7)).isoformat())
        p.get_by_label('Minutes per day',exact=True).fill('10')
        p.get_by_role('button',name='Build my revision plan',exact=True).click()
        expect(p.locator('#student-centre ol li')).to_have_count(3)
        p.locator('#student-centre ol input[type=checkbox]').first.check()
        p.reload()
        p.get_by_role('button',name='Prepare for a test',exact=True).click()
        expect(p.locator('#student-centre ol input[type=checkbox]').first).to_be_checked()

    def test_investigation_collect_plot_check_and_backup(self):
        from playwright.sync_api import expect
        self.open('ib-chemistry','investigations.html')
        p=self.page
        slider=p.get_by_role('slider',name='Mass of water / g',exact=True)
        for value in (40,80,120):
            slider.evaluate('(e,v)=>{e.value=v;e.dispatchEvent(new Event("input"));}',value)
            p.get_by_role('button',name='Record measurement',exact=True).click()
        expect(p.locator('svg circle')).to_have_count(3)
        p.get_by_label('My conclusion, evidence and limitation',exact=True).fill('The fictional measurements show a lower temperature rise for greater mass at fixed energy.')
        p.get_by_label('Check answer',exact=True).fill('10 K')
        p.get_by_role('button',name='Check my investigation answer',exact=True).click()
        expect(p.get_by_role('status').filter(has_text='not automatically marked')).to_be_visible()
        p.reload()
        expect(p.locator('svg circle')).to_have_count(3)
        self.open('ib-chemistry','student-backup.html')
        with p.expect_download() as event:
            p.get_by_role('button',name='Export combined backup',exact=True).click()
        backup=json.loads(Path(event.value.path()).read_text())
        self.assertEqual(len(backup['learning']['ib-chemistry']['notebooks']['heating']['rows']),3)

    def test_snapshot_home_and_detailed_results_stay_accessible(self):
        from playwright.sync_api import expect
        fixture=LearningIntegrationTests('test_history_is_scoped_deduplicated_and_preserves_missing')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config=Config(fixture.store.path(fixture.key),Path(self.temp.name)/'snapshot')
        _,pages=generate_dashboards(config,False)
        p=self.page
        p.goto((config.output/pages[0]).as_uri())
        expect(p.locator('.choices button')).to_have_count(3)
        expect(p.locator('#student-details')).to_be_hidden()
        p.get_by_role('button',name='See my progress',exact=True).click()
        expect(p.get_by_role('heading',name='Your learning history',exact=True)).to_be_visible()
        p.get_by_label('Topic',exact=True).select_option('a')
        expect(p.locator('.timeline li')).to_have_count(1)
        p.get_by_text('Detailed results & feedback',exact=True).click()
        p.get_by_role('link',name='Assessments',exact=True).click()
        expect(p.locator('#student-details')).to_be_visible()
        p.get_by_role('button',name='Home',exact=True).click()
        expect(p.get_by_role('heading',name='What would you like to do today?')).to_be_visible()
