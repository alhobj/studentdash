"""Authored practice-context links for the skill directory; not guide prerequisites."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'resources'
chem={
'S1.1':['knowledge','safety','length','chromatography','separation','distillation','recrystallization','melting','qualitative','diagrams'],
'S1.4':['apply-knowledge','mass','volume','standard','dilution','arithmetic','number-operations','units','symbols','precision','scientific-notation','order'],
'S1.5':['simulation','proportionality','models','theories','patterns'],
'S2.2':['molecular-models'],
'S3.2':['chromatography','distillation','recrystallization','melting'],
'R1.1':['ethical-investigation','temperature','calorimetry','sensors','computer-model','insulation','calibration','limitations','improvements','conclusion','scientific-context','uncertain-conclusions','raw-uncertainty','uncertainty-range','propagation','uncertainty-forms','error-bars','estimate','negligible','errors','quality','creative-design'],
'R1.3':['global-impact'],
'R1.4':[],
'R1.2':['databases'],
'R2.1':['constant-mass','titration','spreadsheet','mean-range','percentage-change','error','outliers','quantitative'],
'R2.2':['evaluate-science','exponentials','time','rates','digital-graphs','variables-type','r-squared','sketch','charts','plot','best-fit','graph-features','interpolation','initiative','research-question','prediction','investigation-types','variable-selection','sampling-design','method','pilot','collection-issues','processing','question-conclusion','hypothesis-evaluation','atl-thinking'],
'R3.1':['ph','logarithms','titration','sources','evidence'],
'R3.2':['current','voltage','cells','environment','titration'],
'S1.3':['colorimetry','interpretation']}
math={
'1.1':['number-sets','standard-form','powers'], '1.2':['arithmetic','primes','tech-patterns'],
'1.4':['proportion','currency'], '1.5':['powers','surds'], '1.6':['rounding','absolute'],
'1.8':['algebra','rearrange','substitute','inequalities','linear','systems'],
'2.1':['coordinates','model-parameters'], '2.2':['sets','representations'],
'2.4':['graphing','tech-representations','technology'], '2.5':['model-choice'],
'2.6':['knowledge','model-question','model-assumptions','model-validation','model-refine','model-context','model-transfer','problem-solving'],
'3.1':['volume-area','solids','plane-shapes','units'], '3.2':['pythagoras','triangle-angles','trigonometry','tech-geometry'],
'3.3':['angles','bearings'], '3.4':['circles'], '3.5':['coordinates','geometry-language'],
'3.6':['transformations'], '4.1':['research','data-displays'], '4.3':['summary','tech-data'],
'4.5':['probability','tech-simulation'], '4.6':['venn','trees'], '4.8':['tech-statistics'],
'5.1':['speed'], '5.5':['tech-calculus']}
for profile,mapping in [('ib-chemistry',chem),('ib-math-ai-sl',math)]:
 root=ROOT/profile;data=json.loads((root/'skills.json').read_text(encoding='utf-8'));refs=json.loads((root/'syllabus-cross-references.json').read_text(encoding='utf-8'))
 allcodes=set(refs['sections']);known={s['id'] for s in data['skills']}
 assert set(mapping)<=allcodes and all(k in known for v in mapping.values() for k in v)
 for skill in data['skills']:
  if skill['id'].startswith('method-'):codes=[skill['id'][7:].replace('-','.')]
  else:codes=[code for code,skills in mapping.items() if skill['id'] in skills]
  skill['sections']=codes
  skill['across_course']=not bool(codes)
 data['section_links']={code:refs['targets'][code] for code in refs['sections']}
 (root/'skills.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
