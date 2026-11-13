from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from studentdash.models import WorkbookData, Student, Assessment, Question, QuestionResult
from studentdash.local_tree import export_package, read_json

class LocalTreeTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.viewer=self.root/'viewer';(self.viewer/'app/assets').mkdir(parents=True)
        for name in ['app/index.html','app/assets/app.js','Start.cmd','Start.ps1','serve.py','LOCAL_STUDENT_GUIDE.md']:(self.viewer/name).write_text('generic app')
        (self.viewer/'assets-manifest.json').write_text(json.dumps(['assets/app.js']))
        (self.viewer/'curriculum.json').write_text(json.dumps(dict(mapId='chemistree',mapVersion='2.0',nodes=[{'id':'node-a'},{'id':'node-b'}])))
        self.dest=self.root/'student'
        self.data=WorkbookData(students={'001':Student('001','Fictional Alice','alice@example.invalid','C'),'002':Student('002','Fictional Bob','bob@example.invalid','C')},assessments={'A':Assessment('A','Fictional test',date(2026,1,1),'Example',5)},questions={'Q':Question('Q','A','2(b)','','Secret text',5,'','','','')},question_results=[QuestionResult('A','Q','001',4,'graded'),QuestionResult('A','Q','002',1,'graded')])
    def export(self,**kw):return export_package(kw.get('data',self.data),kw.get('student','001'),kw.get('mapping',{'Q':'node-a'}),self.viewer,self.dest)
    def test_single_learner_and_independent_updates(self):
        self.export();first=read_json(self.dest/'results.json');config=read_json(self.dest/'package.json')
        self.assertEqual(len(first['evidence']),1);self.assertEqual(first['evidence'][0]['score'],4)
        text=(self.dest/'results.json').read_text()
        for private in ['Fictional Alice','Fictional Bob','bob@example.invalid','Secret text','confidence']:self.assertNotIn(private,text)
        (self.dest/'confidence-backup.json').write_text('student backup')
        self.assertFalse(self.export()['changed'])
        self.data.question_results[0]=QuestionResult('A','Q','001',3,'graded')
        self.assertEqual(self.export()['revision'],2);self.assertEqual(read_json(self.dest/'package.json'),config)
        self.assertEqual((self.dest/'confidence-backup.json').read_text(),'student backup')
        with self.assertRaisesRegex(ValueError,'another learner'):self.export(student='002')
    def test_exclusions_zero_and_mapping(self):
        for status in ['absent','exempt','pending','missing']:
            self.data.question_results[0]=QuestionResult('A','Q','001',0,status)
            self.export();self.assertEqual(read_json(self.dest/'results.json')['evidence'],[])
        self.data.question_results[0]=QuestionResult('A','Q','001',0,'graded')
        self.export();self.assertEqual(read_json(self.dest/'results.json')['evidence'][0]['score'],0)
        self.export(mapping={});self.assertEqual(read_json(self.dest/'results.json')['evidence'],[])
    def test_invalid_export_preserves_previous_bytes(self):
        self.export();old=(self.dest/'results.json').read_bytes()
        for mapping in [{'Q':'unknown'},{'Q':['node-a','node-b']},{'missing':'node-a'}]:
            with self.assertRaises(ValueError):self.export(mapping=mapping)
            self.assertEqual((self.dest/'results.json').read_bytes(),old)
        self.data.question_results.append(self.data.question_results[0])
        with self.assertRaises(ValueError):self.export()
        self.assertEqual((self.dest/'results.json').read_bytes(),old)
    def test_registry_neutral(self):
        registry=read_json(self.viewer/'curriculum.json');registry['mapId']='another-subject';registry['mapVersion']='9'
        (self.viewer/'curriculum.json').write_text(json.dumps(registry))
        self.export();self.assertEqual(read_json(self.dest/'results.json')['mapId'],'another-subject')
    def test_workbook_cli_creates_and_refreshes_one_package(self):
        import subprocess, sys
        from openpyxl import Workbook
        from studentdash.excel import SCHEMA, OPTIONAL_SCHEMA
        wb=Workbook();wb.remove(wb.active)
        tables={**SCHEMA,'Memberships':OPTIONAL_SCHEMA['Memberships'],'QuestionResults':OPTIONAL_SCHEMA['QuestionResults']}
        for name,headers in tables.items():wb.create_sheet(name).append(list(headers)+(['Status'] if name=='Results' else []))
        for sid,name,score in [('001','Fictional Alice',4),('002','Fictional Bob',1)]:
            wb['Students'].append([sid,name,'','Chemistry'])
            wb['Results'].append(['A01',sid,score,5,'graded'])
            wb['Memberships'].append(['A01',sid,'SL'])
            wb['QuestionResults'].append(['A01','Q01',sid,score,'graded'])
        wb['Assessments'].append(['A01','Fictional test','2026-11-12','Chemistry',5])
        wb['Questions'].append(['Q01','A01','2(b)','SL','Fictional question','',5,'Structure','Matter','Short answer','State',''])
        for i in range(1,8):wb['Grade boundaries'].append([i,(i-1)*10])
        source=self.root/'source.xlsx';wb.save(source)
        mapping=self.root/'mapping.json';mapping.write_text(json.dumps({'Q01':'node-a'}))
        cmd=[sys.executable,str(Path(__file__).resolve().parents[1]/'export_local_tree.py'),'--source',str(source),'--student','001','--mapping',str(mapping),'--viewer',str(self.viewer),'--destination',str(self.dest)]
        subprocess.run(cmd,check=True,capture_output=True)
        first=read_json(self.dest/'results.json');self.assertEqual(len(first['evidence']),1);self.assertEqual(first['evidence'][0]['score'],4)
        wb['QuestionResults']['D2']=3;wb['Results']['C2']=3;wb.save(source)
        subprocess.run(cmd,check=True,capture_output=True)
        second=read_json(self.dest/'results.json');self.assertEqual(second['revision'],2);self.assertEqual(second['packageId'],first['packageId']);self.assertEqual(second['evidence'][0]['score'],3)

if __name__=='__main__':unittest.main()
