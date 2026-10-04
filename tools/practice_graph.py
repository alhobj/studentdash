"""Build an offline graph from explicit profile hierarchy and guide cross-references."""
import json
from pathlib import Path
from html import escape
from practice_skills import load_skills

ASSETS=Path(__file__).parent/'assets'


def build_graph(root, curriculum_file, label, hub):
    source=json.loads((root/'syllabus-reference.json').read_text(encoding='utf-8'))
    refs=json.loads((root/'syllabus-cross-references.json').read_text(encoding='utf-8'))
    curriculum=json.loads(curriculum_file.read_text(encoding='utf-8'))
    byid={n['id']:n for n in curriculum['nodes']}
    bycode={n['code']:n for n in curriculum['nodes'] if 'code' in n}
    nodes={};edges=[]
    for code,row in source['sections'].items():
        parent=byid[bycode[code]['parent']]
        group=parent['id'].split(':',1)[1]
        nodes.setdefault(group,dict(id=group,code=parent.get('code',group),title=parent['label'],kind='group',parent=None,group=group,href=hub,guide=source['copy_url']))
        nodes[code]=dict(id=code,code=code,title=row['summary'],kind='section',parent=group,group=group,level=row['level'],href=refs['targets'][code]['href'],guide=source['copy_url']+'#page='+str(row['pdf_page']))
        edges.append(dict(source=group,target=code,kind='hierarchy'))
    for key,target in refs['targets'].items():
        if key not in nodes:
            nodes[key]=dict(id=key,code=target['label'].split(' · ')[0],title=target['label'],kind='reference',parent=None,group='other',href=target['href'],guide=target['href'])
    for code,links in refs['sections'].items():
        for link in links:edges.append(dict(source=code,target=link['target'],kind='reference',pages=link['source_pages'],qualifier=link.get('qualifier','')))
    statements=root/'syllabus-statements.json'
    if statements.exists():
        detail=json.loads(statements.read_text(encoding='utf-8'))
        for row in detail['nodes']:
            parent=nodes[row['parent']]
            nodes[row['id']]=dict(id=row['id'],code=row['id'],title='Statement in '+parent['title'],kind='statement',parent=row['parent'],group=parent['group'],level=row['level'],href=parent['href'],guide=detail['source']+'#page='+str(row['pdf_page']))
            edges.append(dict(source=row['parent'],target=row['id'],kind='hierarchy'))
        for row in detail['nodes']:
            for link in row['links']:
                key=link['target']
                if key not in nodes:
                    raise ValueError('Unmapped guide reference: '+key)
                edges.append(dict(source=row['id'],target=key,kind='reference',pages=[link['pdf_page']],qualifier=''))
    skills=load_skills(str(root))
    if skills:
        for key in skills.get("cross_reference_groups", {}):
            if key in nodes: nodes[key]["href"]="skills-practice.html#group-"+key
    data=dict(label=label,nodes=list(nodes.values()),edges=edges,guide=source['copy_url'],note=refs['note'])
    (root/'syllabus-graph.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in ('syllabus-graph.js','syllabus-graph.css'):(root/name).write_bytes((ASSETS/name).read_bytes())
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    html=('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
          f'<title>Syllabus graph · {escape(label)}</title><link rel="stylesheet" href="syllabus-graph.css"></head><body><main>'
          f'<header><a href="{hub}">← Practice hub</a><p class="eyebrow">EXPLORE THE CONNECTIONS</p><h1>{escape(label)} syllabus graph</h1>'
          '<p>Select a circle to trace its connections and find practice. Solid arrows show explicit guide references; dashed lines show where a part belongs. '
          'A reference is not a prerequisite. Colours identify topic groups.</p></header>'
          '<div class="toolbar"><label>Find a code or topic <input id="graph-search" type="search" placeholder="Type a code or keyword"></label>'
          '<label>Choose a part <select id="graph-picker"></select></label><label>Topic group <select id="graph-group"><option value="">All groups</option></select></label>'
          '<label><input id="graph-detail" type="checkbox" checked> Show individual statements</label>'
          '<label><input id="graph-neighbours" type="checkbox"> Selected connections only</label>'
          '<button id="graph-clear">Clear selection</button><button id="graph-out" aria-label="Zoom out">−</button><button id="graph-in" aria-label="Zoom in">+</button><button id="graph-fit">Fit graph</button></div>'
          '<p id="graph-status" role="status"></p><div class="graph-layout"><div id="graph-viewport" tabindex="0" aria-label="Scrollable syllabus graph">'
          '<svg id="syllabus-graph" xmlns="http://www.w3.org/2000/svg" role="group" aria-label="Interactive syllabus graph"></svg></div>'
          '<aside id="graph-inspector" aria-live="polite"><h2>Choose a syllabus part</h2><p>Click a circle or use the searchable list. Scroll the graph to explore; use + and − to change its size.</p></aside></div>'
          '<details><summary>Accessible list of all syllabus parts</summary><ul>'
          +''.join(f'<li><a href="{escape(n["guide"],quote=True)}">{escape(n["code"])}</a> — {escape(n["title"])}</li>' for n in nodes.values())
          +'</ul></details><footer><p>Works offline; linked guide pages require internet. Statement descriptions use their parent section’s summary; read the guide for exact wording. '
          'The mathematics graph uses the guide’s SL sub-topic numbering.</p>'
          f'<p><a href="{escape(source["copy_url"],quote=True)}">Source: {escape(source["title"])} · {escape(source["edition"])}</a></p></footer>'
          f'<script type="application/json" id="graph-data">{payload}</script><script src="syllabus-graph.js"></script></main></body></html>')
    (root/'syllabus-graph.html').write_text(html,encoding='utf-8')
    page=root/hub;text=page.read_text(encoding='utf-8')
    if 'href="syllabus-graph.html"' not in text:text=text.replace('</header>','<p><a href="syllabus-graph.html">Explore the syllabus graph →</a></p></header>',1)
    page.write_text(text,encoding='utf-8')
