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
    return questions


def build_student_tools(root, label, hub, css):
    profiles = {}
    for path in root.parent.glob('*/skills.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        profiles[path.parent.name] = [q['id'] for q in data['questions']]
    (root / 'student-record-profiles.js').write_text('window.STUDENT_RECORD_PROFILES = ' + json.dumps(profiles) + ';\n', encoding='utf-8')
    for asset in ('student-records.js', 'guided-practice.js'):
        (root / asset).write_bytes((ASSETS / asset).read_bytes())
    guided_anchors = ''.join(f'<section id="{escape(q["id"], quote=True)}"></section>' for q in guided_questions(root))
    for name, title, content, scripts in [
        ('student-backup.html', 'Combined student backup', '<div id="student-records" data-mode="backup"></div>', ['student-record-profiles.js', 'student-records.js']),
        ('class-practice.html', 'Teacher class overview', '<div id="student-records" data-mode="class"></div>', ['student-record-profiles.js', 'student-records.js']),
        ('guided-practice.html', 'Guided problem solving', '<p>Work through equation, substitution, calculation and units. Later steps unlock after a correct check. Hints and retries count as help. Changing a step clears later answers; previous checked attempts remain in your history.</p><div id="guided-practice">' + guided_anchors + '</div>', ['guided-practice.js'])
    ]:
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{title} · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="learning.css">'
                '<style>label{display:block;margin:.7rem 0}input,select,button{font:inherit;max-width:100%}button{margin:.3rem}fieldset{margin:1rem 0}fieldset:disabled{opacity:.55}table{border-collapse:collapse;display:block;overflow:auto}th,td{padding:.5rem;border:1px solid #aaa}main{max-width:1100px;margin:auto;padding:1rem}</style></head><body><main>'
                f'<header><a href="{hub}">Practice hub</a> · <a href="my-practice.html">My practice</a><h1>{title} · {escape(label)}</h1></header>{content}</main>'
                '<script src="learning-catalog.js"></script><script src="learning.js"></script>'
                + ''.join(f'<script src="{s}"></script>' for s in scripts) + '</body></html>')
        (root / name).write_text(page, encoding='utf-8')
