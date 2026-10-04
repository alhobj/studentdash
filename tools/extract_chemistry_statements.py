from pypdf import PdfReader
from pathlib import Path
import re,json
import argparse
parser=argparse.ArgumentParser(description='Extract statement codes and explicit references from the 2025 Chemistry guide; no statement text is copied.')
parser.add_argument('pdf',type=Path)
args=parser.parse_args()
r=PdfReader(args.pdf);nodes=[];current=None;level='SL and HL'
for page in range(38,70):
 lines=r.pages[page].extract_text().splitlines()
 for line_index,line in enumerate(lines):
  if line.startswith('Standard level and higher level:'):level='SL and HL'
  if line.startswith('Additional higher level:'):level='Additional HL'
  m=re.match(r'^(Structure|Reactivity) (\d+\.\d+\.\d+)—',line)
  if m:
   code=m[1][0]+m[2];current=dict(id=code,parent=code.rsplit('.',1)[0],pdf_page=page+1,level=level,links=[]);nodes.append(current);continue
  if re.match(r'^(Structure|Reactivity) \d+\.\d+—',line) and any('Guiding question:' in x for x in lines[line_index+1:line_index+4]):current=None
  if re.match(r'^(Structure|Reactivity) \d+\. ',line):current=None
  if line.startswith('Additional higher level:'):continue
  if current:
   for ref in re.finditer(r'\b(Structure|Reactivity) (\d+(?:\.\d+){0,2})\b',line):
    target=ref[1][0]+ref[2]
    if target!=current['id'] and not any(x['target']==target for x in current['links']):current['links'].append(dict(target=target,pdf_page=page+1))
assert len(nodes)==165
Path('resources/ib-chemistry/syllabus-statements.json').write_text(json.dumps(dict(source='https://anatolia.edu.gr/images/highschool/IBDP/Chemistry%20Guide%202025.pdf',note='Numbered statement identifiers and explicit Structure/Reactivity references, checked against guide pages 33–64. Descriptions are supplied at parent-section level; full statement wording remains in the guide.',nodes=nodes),indent=2)+'\n',encoding='utf-8')
print(f'Extracted {len(nodes)} statement identifiers.')
