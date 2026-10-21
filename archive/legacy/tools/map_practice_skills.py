"""Explicit profile-local skill assignments, reviewed by task kind and section."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'resources'
math_methods={'1.1':'standard-form','1.2':'arithmetic','1.3':'powers','1.4':'proportion','1.5':'powers','1.6':'rounding','1.7':'problem-solving','1.8':'algebra','2.1':'coordinates','2.2':'representations','2.3':'representations','2.4':'graphing','2.5':'model-choice','2.6':'model-validation','3.1':'volume-area','3.2':'trigonometry','3.3':'bearings','3.4':'circles','3.5':'coordinates','3.6':'problem-solving','4.1':'research','4.2':'data-displays','4.3':'summary','4.4':'model-parameters','4.5':'probability','4.6':'probability','4.7':'probability','4.8':'probability','4.9':'probability','4.10':'summary','4.11':'reasoning','5.1':'speed','5.2':'graphing','5.3':'algebra','5.4':'coordinates','5.5':'tech-calculus','5.6':'graphing','5.7':'problem-solving','5.8':'arithmetic'}
for profile in ['ib-chemistry','ib-math-ai-sl']:
 root=ROOT/profile;data=json.loads((root/'skills.json').read_text(encoding='utf-8'))
 raw=(root/'learning-catalog.js').read_text(encoding='utf-8');catalog=json.loads(raw.removeprefix('window.PRACTICE_CATALOG = ').strip().removesuffix(';'))
 bindings={};skills={s['id'] for s in data['skills']}
 if profile=='ib-math-ai-sl':
  data['skills']=[s for s in data['skills'] if not s['id'].startswith('method-')]
  coverage=json.loads((root/'coverage.json').read_text(encoding='utf-8'));ref=json.loads((root/'syllabus-reference.json').read_text(encoding='utf-8'))
  for section in coverage:
   data['skills'].append(dict(id='method-'+section['code'].replace('.','-'),label=section['title'],group='Syllabus methods',source_pages=[ref['sections'][section['code']]['pdf_page']]))
 for q in catalog['questions']:
  key=q.get('source_id') or hashlib.sha256(q['prompt'].encode()).hexdigest()[:20]
  tags=[]
  if profile=='ib-math-ai-sl':
   tags=['knowledge']
   if q['topic'] in math_methods:tags.append('method-'+q['topic'].replace('.','-'))
   elif isinstance(q.get('answer'),(int,float)):tags.append('arithmetic')
  else:
   numeric=isinstance(q.get('answer'),(int,float))
   if q.get('options'):
    try:
     for option in q['options']:float(option)
     numeric=True
    except ValueError:pass
   tags=['arithmetic'] if numeric else ['knowledge']
   if q['topic']=='S1.5' and numeric:tags.append('proportionality')
   if q['topic']=='R2.2' and numeric:tags.append('rates')
   if q['topic']=='R3.1' and numeric and ('pH' in q['prompt'] or 'H⁺' in q['prompt']):tags.append('logarithms')
   if q['topic'] in ('S1.1','S1.2','S1.3','S2.1','S2.2','S2.3') and not numeric:tags.append('models')
  if tags:bindings[key]=tags
 if profile=='ib-chemistry':
  corrected={'voltage':35,'models':13,'evidence':13,'research-integrity':14,'planning':22}
  for skill in data['skills']:
   if skill['id'] in corrected:skill['source_pages']=[corrected[skill['id']]]
 data['bindings']=bindings
 data['numeric_skills']=['arithmetic']
 data['cross_reference_groups']={'tool-1':'Tool 1','tool-2':'Tool 2','tool-3':'Tool 3','inquiry-1':'Inquiry 1','inquiry-2':'Inquiry 2','inquiry-3':'Inquiry 3','nature-of-science':'Scientific thinking'} if profile=='ib-chemistry' else {}
 (root/'skills.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(profile,len(data['skills']),'skills;',len(data['questions']),'new questions;',len(bindings),'existing question assignments')
