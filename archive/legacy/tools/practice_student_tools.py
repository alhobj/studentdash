"""Build generic offline student tools from each profile's authored content."""
import json
from pathlib import Path
from html import escape

ASSETS = Path(__file__).parent / 'assets'


def guided_questions(root):
    path = root / 'guided-practice.json'
    if not path.exists():
        return []
    questions = json.loads(path.read_text(encoding='utf-8'))
    for q in questions:
        q.update(kind='guided', path='guided-practice.html#' + q['id'])
    lab_path = root / 'investigations.json'
    if lab_path.exists():
        for lab in json.loads(lab_path.read_text(encoding='utf-8')):
            questions.append(dict(lab['check'], id=root.name+':investigation:'+lab['id'], topic=lab['topic'],
                                  title=lab['title'], kind='investigation', path='investigations.html#'+lab['id'],
                                  skills=lab['check']['skills'], working=lab['check']['hint']))
    return questions


def build_student_tools(root, label, hub, css):
    # Match a configured journal path, never interpret subject names or syllabus codes.
    curricula = Path(__file__).resolve().parents[1] / 'curricula'
    curriculum = next((c for path in curricula.glob('*.json') if (c := json.loads(path.read_text(encoding='utf-8'))).get('practice_journal', '').split('/')[0] == root.name), {})
    context = dict(schema=1, scope=root.name, label=label, profile=root.name,
                   nodes=curriculum.get('nodes', []), resources=curriculum.get('resources', []),
                   journal=curriculum.get('practice_journal'), events=[], interventions=[], exams=[])
    payload = json.dumps(context, ensure_ascii=False).replace('<', '\\u003c')
    home = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>My learning · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="../learning/learning-centre.css">'
            '</head><body><main><section id="student-centre" class="learning-centre" data-resource-base="../"></section></main>'
            f'<script type="application/json" id="learning-context">{payload}</script>'
            '<script>window.PRACTICE_EMBEDDED=true;</script><script src="learning-catalog.js"></script><script src="learning.js"></script>'
            '<script src="../learning/learning-state.js"></script><script src="../learning/student-centre.js"></script></body></html>')
    (root / 'learning-home.html').write_text(home, encoding='utf-8')
    lab_path = root / 'investigations.json'
    if lab_path.exists():
        labs = json.loads(lab_path.read_text(encoding='utf-8'))
        lab_payload = json.dumps(labs, ensure_ascii=False).replace('<', '\\u003c')
        extra = '<p><a href="exploration-projects.html">Longer exploration and reflection projects</a></p>' if (root / 'exploration-projects.html').exists() else ''
        anchors = ''.join(f'<span id="{escape(l["id"], quote=True)}"></span>' for l in labs)
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>Investigations · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="../learning/learning-centre.css"></head>'
                '<body><main class="learning-centre"><p><a href="learning-home.html">My learning home</a></p>'
                '<p>Predict, measure, graph, explain, then try a new question. These are simplified simulations; written conclusions need teacher review.</p>'
                + anchors + '<div id="investigations"></div>' + extra + '</main>'
                f'<script id="investigation-data" type="application/json">{lab_payload}</script>'
                '<script>window.PRACTICE_EMBEDDED=true;</script><script src="learning-catalog.js"></script><script src="learning.js"></script>'
                '<script src="../learning/learning-state.js"></script><script src="../learning/investigations.js"></script></body></html>')
        (root / 'investigations.html').write_text(page, encoding='utf-8')
    profiles = {}
    for path in root.parent.glob('*/skills.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        profiles[path.parent.name] = [q['id'] for q in data['questions']]
    (root / 'student-record-profiles.js').write_text('window.STUDENT_RECORD_PROFILES = ' + json.dumps(profiles) + ';\n', encoding='utf-8')
    for asset in ('student-records.js', 'guided-practice.js'):
        (root / asset).write_bytes((ASSETS / asset).read_bytes())
    guided_anchors = ''.join(f'<section id="{escape(q["id"], quote=True)}"></section>' for q in guided_questions(root) if q['kind']=='guided')
    for name, title, content, scripts in [
        ('student-backup.html', 'Combined student backup', '<div id="student-records" data-mode="backup"></div>', ['../learning/learning-state.js', 'student-record-profiles.js', 'student-records.js']),
        ('class-practice.html', 'Teacher class overview', '<div id="student-records" data-mode="class"></div>', ['../learning/learning-state.js', 'student-record-profiles.js', 'student-records.js']),
        ('guided-practice.html', 'Guided problem solving', '<p>Work through equation, substitution, calculation and units. Later steps unlock after a correct check. Hints and retries count as help. Changing a step clears later answers; previous checked attempts remain in your history.</p><div id="guided-practice">' + guided_anchors + '</div>', ['guided-practice.js'])
    ]:
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{title} · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="learning.css">'
                '<style>label{display:block;margin:.7rem 0}input,select,button{font:inherit;max-width:100%}button{margin:.3rem}fieldset{margin:1rem 0}fieldset:disabled{opacity:.55}table{border-collapse:collapse;display:block;overflow:auto}th,td{padding:.5rem;border:1px solid #aaa}main{max-width:1100px;margin:auto;padding:1rem}</style></head><body><main>'
                f'<header><a href="{hub}">Practice hub</a> · <a href="my-practice.html">My practice</a><h1>{title} · {escape(label)}</h1></header>{content}</main>'
                '<script src="learning-catalog.js"></script><script src="learning.js"></script>'
                + ''.join(f'<script src="{s}"></script>' for s in scripts) + '</body></html>')
        (root / name).write_text(page, encoding='utf-8')
