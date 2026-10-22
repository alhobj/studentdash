"""Excel rectangles include confidence without including it in graded evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading
import unittest
import test_confidence as fixtures
from studentdash.config import Config, ROOT
from studentdash.entry import ClassStore
from studentdash.teacher import create_app

class ConfidencePasteTests(unittest.TestCase):
    setUp=fixtures.ConfidenceTests.setUp
    payload=fixtures.ConfidenceTests.payload
    preview=fixtures.ConfidenceTests.preview
    commit=fixtures.ConfidenceTests.commit
    imported=fixtures.ConfidenceTests.imported
    save=fixtures.ConfidenceTests.save

    @unittest.skipUnless(shutil.which('node'),'Optional Node check')
    def test_javascript_rectangles_and_validation(self):
        code=r'''
const assert=require('node:assert/strict');
const grid=require(process.argv[1]);
assert.deepEqual(grid.paste('1\t0\t\r\n0\t1\t5\r\n',2,3,0,0),[['1','0',''],['0','1','5']]);
assert.deepEqual(grid.paste('\r\n',2,3,0,2),[['']]);
assert.deepEqual(grid.paste('2\n5',2,3,0,2),[['2'],['5']]);
assert.throws(()=>grid.paste('1\t2\n3',2,3,0,0),/rectangular/);
assert.throws(()=>grid.paste('1\t2',2,3,1,2),/beyond/);
for(const value of ['0','6','1.0','2.5','A','P','-1','1e0'])assert.ok(grid.parseConfidence(value).error);
for(const value of ['1','2','3','4','5'])assert.equal(grid.parseConfidence(value).rating,Number(value));
assert.equal(grid.parseConfidence(' ').rating,null);
assert.equal(grid.parse('0',1).score,0);
assert.equal(grid.parse('E',1).status,'exempt');
'''
        result=subprocess.run(['node','-e',code,str(ROOT/'templates'/'score_grid.js')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_server_rejects_both_fields_atomically_and_retains_inputs(self):
        aid=self.imported();self.save(aid,{self.sids[0]:2})
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'));client=app.test_client()
        url=f'/classes/{self.key}/assessments/{aid}/scores'
        client.get(url)
        with client.session_transaction() as s:token=s['csrf_token']
        before=self.store.read(self.key)
        response=client.post(url,data=dict(csrf_token=token,version=before['version'],
            payload=json.dumps([['0.5','1','1','0'],['0','A','E','P']]),**{'confidence-'+self.sids[0]:'6'}))
        self.assertEqual(response.status_code,400)
        self.assertEqual(before,self.store.read(self.key))
        self.assertIn(b'Fictional Alpha, confidence',response.data)
        self.assertIn(b'value="6"',response.data)
        self.assertIn(b'value="0.5"',response.data)
        self.assertIn(b'aria-invalid="true"',response.data)
        # Score-only native submissions preserve saved ratings as before.
        response=client.post(url,data=dict(csrf_token=token,version=before['version'],
            payload=json.dumps([[1,1,1,0],[0,0,'A','P']])))
        self.assertEqual(response.status_code,303)
        self.assertEqual(self.store.read(self.key)['assessments'][0]['confidence_ratings'],{self.sids[0]:2})

    @unittest.skipUnless(importlib.util.find_spec('playwright') and shutil.which('chromium'),'Optional Chromium check')
    def test_excel_paste_navigation_save_restart_and_snapshot(self):
        from playwright.sync_api import sync_playwright,expect
        from werkzeug.serving import make_server
        aid=self.imported();self.save(aid,{self.sids[0]:2,self.sids[1]:4})
        app=create_app(Config(self.root/'unused.xlsx',self.root/'output'))
        server=make_server('127.0.0.1',0,app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as runtime:
                browser=runtime.chromium.launch(executable_path=shutil.which('chromium'),headless=True)
                try:
                    page=browser.new_page(viewport=dict(width=375,height=812))
                    errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/classes/{self.key}/assessments/{aid}/scores')
                    def cell(row,col):return page.locator(f'#score-grid input[data-row="{row}"][data-col="{col}"]')
                    def paste(row,col,text):
                        cell(row,col).evaluate('''(el,text)=>{const data=new DataTransfer();data.setData('text/plain',text);el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));}''',text)
                    def values():return page.locator('#score-grid input').evaluate_all('(inputs)=>inputs.map(i=>i.value)')
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                    paste(0,0,'1\t1\t1\t0\t2\r\n0\tA\tE\tP\t5\r\n')
                    expect(page.locator('.row-total').first).to_have_text('3/4')
                    expect(cell(1,4)).to_have_value('5')
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(page.get_by_role('status').first).to_contain_text('Saved')
                    stored=self.store.read(self.key)['assessments'][0]
                    self.assertEqual(stored['confidence_ratings'],dict(zip(self.sids,[2,5])))
                    self.assertEqual(len(stored['scores'][self.sids[0]]),4)
                    paste(0,0,'0\t1')  # Scores only preserve confidence.
                    expect(cell(0,4)).to_have_value('2')
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(page.get_by_role('status').first).to_contain_text('Saved')
                    self.assertEqual(self.store.read(self.key)['assessments'][0]['confidence_ratings'],dict(zip(self.sids,[2,5])))
                    paste(0,3,'0\t3\nP\t4')  # Partial rectangle crossing into confidence.
                    expect(cell(0,4)).to_have_value('3');expect(cell(1,4)).to_have_value('4')
                    paste(0,4,'1\n5')  # Confidence-only multi-student paste.
                    expect(cell(0,4)).to_have_value('1');expect(cell(1,4)).to_have_value('5')
                    paste(0,0,'1\t1\t1\t0\t\r\n0\t0\t0\t0\t4\r\n')
                    expect(cell(0,4)).to_have_value('')  # Explicit trailing blank clears.
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(page.get_by_role('status').first).to_contain_text('Saved')
                    self.assertNotIn(self.sids[0],self.store.read(self.key)['assessments'][0]['confidence_ratings'])
                    before=values()
                    paste(0,0,'1\t2\n3')
                    expect(page.locator('#grid-message')).to_contain_text('rectangular')
                    self.assertEqual(before,values())
                    paste(1,4,'1\t2')
                    expect(page.locator('#grid-message')).to_contain_text('beyond')
                    self.assertEqual(before,values())
                    paste(0,4,'6')
                    expect(cell(0,4)).to_have_attribute('aria-invalid','true')
                    expect(page.locator('#error-0-confidence')).to_contain_text('Fictional Alpha, confidence')
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(cell(0,4)).to_have_value('6')
                    self.assertNotIn(self.sids[0],self.store.read(self.key)['assessments'][0]['confidence_ratings'])
                    self.assertTrue(page.evaluate("()=>{const e=new Event('beforeunload',{cancelable:true});window.dispatchEvent(e);return e.defaultPrevented;}"))
                    page.get_by_role('button',name='Generate student dashboards',exact=True).click()
                    expect(page.locator('#grid-message')).to_contain_text('Save scores before generating')
                    cell(0,4).fill('2');cell(0,4).press('Tab')
                    expect(cell(1,0)).to_be_focused()
                    cell(1,0).press('Shift+Tab');expect(cell(0,4)).to_be_focused()
                    cell(0,4).press('ArrowLeft');expect(cell(0,3)).to_be_focused()
                    cell(0,3).press('ArrowRight');expect(cell(0,4)).to_be_focused()
                    cell(0,4).press('Enter');expect(cell(1,4)).to_be_focused()
                    cell(1,4).press('Shift+Enter');expect(cell(0,4)).to_be_focused()
                    expect(page.locator('.row-total').first).to_have_text('3/4')
                    page.get_by_role('button',name='Save scores',exact=True).click()
                    expect(page.get_by_role('status').first).to_contain_text('Saved')
                    restarted=ClassStore(self.root/'entered_classes').read(self.key)['assessments'][0]
                    self.assertEqual(restarted['confidence_ratings'],dict(zip(self.sids,[2,4])))
                    page.get_by_role('button',name='Generate student dashboards',exact=True).click()
                    expect(page.get_by_role('heading',name='Class overview',exact=True)).to_be_visible()
                    snapshot=self.root/'output'/('class-'+self.key)/f'student{self.sids[0]}.html'
                    html=snapshot.read_text()
                    self.assertIn('Confidence: 2/5',html)
                    self.assertIn('3 / 4',html)
                    self.assertNotIn('Fictional Beta',html)
                    self.assertEqual(errors,[])
                finally:browser.close()
        finally:server.shutdown();thread.join(5);server.server_close()
