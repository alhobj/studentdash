from html import escape

def section_links(data,skill,examples):
    codes=set(skill.get('sections',[]))|{q['topic'] for q in examples if q.get('topic') in data['section_links']}
    if skill.get('across_course'):codes=set(data['section_links'])
    links=''.join(f'<a href="{escape(data["section_links"][c]["href"],quote=True)}">{escape(data["section_links"][c]["label"])}</a> ' for c in data['section_links'] if c in codes)
    return f'<details class="skill-sections"><summary>Related syllabus sections ({len(codes)})</summary><nav>{links}</nav></details>'

def build_skill_index(root,label,hub,css,data,coverage):
    content=(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Skills index · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="skills-practice.css"></head><body><main>'
      f'<header><a href="{hub}">← Practice hub</a><h1>{escape(label)} skills index</h1><p>Choose a skill, open related syllabus sections, or practise it with focused questions.</p>'
      '<p>Skill names are paraphrased teaching labels. Section and question mappings show where to practise; they are not official prerequisite links.</p>'
      '<nav><a href="skills-practice.html">All focused skill questions</a><a href="syllabus-graph.html">Syllabus graph</a></nav></header>'
      '<div class="skill-controls"><label>Find a skill <input id="index-search" type="search" placeholder="Name, group or section code"></label><label>Skill group <select id="index-group"><option value="">All groups</option>'
      +''.join(f'<option>{escape(g)}</option>' for g in dict.fromkeys(s['group'] for s in data['skills']))+'</select></label></div><p id="index-status" role="status"></p><div class="skill-index-grid">')
    for skill in data['skills']:
        key=skill['id'];rows=coverage[key]
        content+=(f'<section class="skill-index-card" id="{escape(key)}" data-skill-group="{escape(skill["group"])}"><p class="eyebrow">{escape(skill["group"])}</p><h2>{escape(skill["label"])}</h2>'
          +section_links(data,skill,rows)+f'<p>{len(rows)} linked question(s)</p><ul>'
          +''.join(f'<li><a href="{escape(q["path"],quote=True)}">{escape(q["prompt"])}</a></li>' for q in sorted(rows,key=lambda q:not q['id'].startswith('skill-'))[:3])
          +f'</ul><p><a href="skills-practice.html#{escape(key)}">All questions and guidance for this skill →</a></p></section>')
    content+='</div><noscript><p>All skills and links are shown; JavaScript enables filtering.</p></noscript><script src="skills-index.js"></script></main></body></html>'
    (root/'skills.html').write_text(content,encoding='utf-8')
