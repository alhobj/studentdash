"""Generic profile-driven skills labels, practice and coverage reporting."""
import hashlib,json
from html import escape
from pathlib import Path
from functools import lru_cache
from practice_skill_index import build_skill_index,section_links
ASSETS=Path(__file__).parent/'assets'

@lru_cache(maxsize=None)
def load_skills(root):
 path=Path(root)/'skills.json'
 if not path.exists():return None
 data=json.loads(path.read_text(encoding='utf-8'));known={s['id'] for s in data['skills']}
 if len(known)!=len(data['skills']):raise ValueError('Duplicate skills')
 for ids in list(data['bindings'].values())+[q['skills'] for q in data['questions']]:
  if not ids or any(k not in known for k in ids):raise ValueError('Unknown or empty skill assignment')
 return data

def tag_question(root,q):
 data=load_skills(str(root))
 if not data:return q
 key=q.get('source_id') or hashlib.sha256(q['prompt'].encode()).hexdigest()[:20]
 q['skills']=data['bindings'].get(key,[])
 return q

def render_skills(root,ids):
 data=load_skills(str(root));byid={s['id']:s for s in data['skills']} if data else {}
 if not ids:return ''
 return '<p class="question-skills">Skills: '+ ' · '.join(f'<a href="skills.html#{escape(key)}">{escape(byid[key]["label"])}</a>' for key in ids)+'</p>'

def numeric_skills(root):
 data=load_skills(str(root));return render_skills(root,data['numeric_skills']) if data else ''

def build_skills(root,label,hub,css,questions):
 data=load_skills(str(root))
 if not data:return
 byid={s['id']:s for s in data['skills']};coverage={s:[] for s in byid}
 for q in questions:
  for key in q.get('skills',[]):coverage[key].append(dict(id=q['id'],path=q['path'],prompt=q['prompt'],topic=q['topic']))
 for q in data['questions']:
  if not q['prompt'] or not q['working']:raise ValueError('Incomplete skill practice')
  for key in q['skills']:coverage[key].append(dict(id=q['id'],path='skills-practice.html#'+q['id'],prompt=q['prompt']))
 missing=[key for key,rows in coverage.items() if not rows]
 if missing:raise ValueError('Skills without questions: '+', '.join(missing))
 (root/'skill-coverage.json').write_text(json.dumps(dict(skills=len(byid),uncovered=missing,coverage=coverage),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 build_skill_index(root,label,hub,css,data,coverage)
 title=f'{label} · Skills practice'
 html=(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="skills-practice.css"></head><body><main>'
       f'<header><a href="{hub}">← Practice hub</a> · <a href="skills.html">Skills index</a><h1>{escape(title)}</h1><p>{escape(data["scope"])}</p>'
       '<p>Skill labels and mappings are authored teaching aids, not official skill codes or a mastery certificate. Practical, technology and collaboration tasks require the stated equipment, software or partner. Written responses are self-reviewed, not automatically marked.</p>'
       f'<p>{len(byid)} skill entries · {len(data["questions"])} focused questions · every entry has linked practice.</p></header>'
       '<div class="skill-controls"><label>Find a skill <input id="skill-search" type="search"></label><label>Skill group <select id="skill-group"><option value="">All groups</option>'
       +''.join(f'<option>{escape(g)}</option>' for g in dict.fromkeys(s['group'] for s in byid.values()))+'</select></label>'
       '<button type="button" id="skill-export">Export my skills notes</button><label>Import skills notes <input id="skill-import" type="file" accept=".json,application/json"></label></div>'
       '<p id="skill-status" role="status">Your written drafts save in this browser. Export to keep a portable copy.</p>'
       '<details><summary>Coverage checklist: skills and linked questions</summary><ul>'
       +''.join(f'<li><a href="#{escape(s["id"])}">{escape(s["group"])} · {escape(s["label"])}</a> — {len(coverage[s["id"]])} linked question(s)</li>' for s in byid.values())+'</ul></details>')
 for alias,prefix in data.get('cross_reference_groups',{}).items():
  html+=f'<nav id="group-{alias}" aria-label="{escape(prefix)} practice">'+''.join(f'<a href="#{escape(s["id"])}">{escape(s["label"])}</a> ' for s in byid.values() if s['group'].startswith(prefix))+'</nav>'
 for skill in byid.values():
  key=skill['id'];html+=(f'<section id="{escape(key)}" class="skill-section" data-skill-group="{escape(skill["group"])}"><p class="eyebrow">{escape(skill["group"])}</p><h2>{escape(skill["label"])}</h2>'
    +'<p>Guide source: '+ ' · '.join(f'<a href="{escape(data["source"])}#page={p}">PDF page {p}</a>' for p in skill['source_pages'])+'</p>')
  html+=section_links(data,skill,coverage[key])
  for q in data['questions']:
   if key not in q['skills']:continue
   html+=(f'<article id="{q["id"]}" data-skill-question="{q["id"]}">'+render_skills(root,q['skills'])+f'<h3>Try this skill</h3><p>{escape(q["prompt"])}</p>'
     f'<label for="answer-{q["id"]}">Your response or work notes</label><textarea id="answer-{q["id"]}" maxlength="12000" rows="4"></textarea>'
     f'<details><summary>Compare with guidance</summary><p>{escape(q["working"])}</p></details>'
     '<label class="skill-review"><input type="checkbox"> I compared my work with the guidance (self-review, not a marked result)</label></article>')
  existing=[q for q in coverage[key] if not q['id'].startswith('skill-')]
  if existing:html+='<details><summary>More questions using this skill ('+str(len(existing))+')</summary><ul>'+''.join(f'<li><a href="{escape(q["path"],quote=True)}">{escape(q["prompt"])}</a></li>' for q in existing)+'</ul></details>'
  html+='</section>'
 html+=f'<script type="application/json" id="skill-profile">{json.dumps(dict(profile=root.name,ids=[q["id"] for q in data["questions"]])).replace("<", "\\u003c")}</script><script src="skills-practice.js"></script></main></body></html>'
 (root/'skills-practice.html').write_text(html,encoding='utf-8')
 for name in ['skills-practice.js','skills-practice.css','skills-index.js']:(root/name).write_bytes((ASSETS/name).read_bytes())
 page=root/hub;text=page.read_text(encoding='utf-8')
 if 'href="skills.html"' not in text:text=text.replace('</header>','<p><a href="skills.html">Skills index: sections and questions →</a></p></header>',1)
 page.write_text(text,encoding='utf-8')
