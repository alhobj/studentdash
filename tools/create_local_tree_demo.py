"""Create one fictional local tree package for launcher and confidence-update checks."""
import argparse
from datetime import date
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studentdash.local_tree import export_package, read_json
from studentdash.models import WorkbookData, Student, Assessment, Question, QuestionResult


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--viewer',required=True,type=Path)
    parser.add_argument('--destination',required=True,type=Path,help='An empty demo folder, never an actual student destination')
    parser.add_argument('--updated',action='store_true',help='Change the first node from 4/5 to 3/5 while retaining the same package')
    args=parser.parse_args()
    node=read_json(args.viewer/'curriculum.json')['nodes'][0]
    data=WorkbookData(students={'demo-learner':Student('demo-learner','Fictional learner','','')},assessments={'DEMO-A':Assessment('DEMO-A','Fictional structure test',date(2026,11,12),'Example',3),'DEMO-B':Assessment('DEMO-B','Fictional exit ticket',date(2026,11,13),'Example',2)},questions={'DEMO-Q1':Question('DEMO-Q1','DEMO-A','2(b)','','',3,'','','',''),'DEMO-Q2':Question('DEMO-Q2','DEMO-B','1','','',2,'','','','')},question_results=[QuestionResult('DEMO-A','DEMO-Q1','demo-learner',1 if args.updated else 2,'graded'),QuestionResult('DEMO-B','DEMO-Q2','demo-learner',2,'graded')])
    result=export_package(data,'demo-learner',{'DEMO-Q1':node['id'],'DEMO-Q2':node['id']},args.viewer,args.destination)
    print(f"Fictional package: {args.destination}\n{node['code']}: {'3/5' if args.updated else '4/5'} at revision {result['revision']}. Open Start.cmd.")


if __name__=='__main__':main()
