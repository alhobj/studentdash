"""Portable practice journal; profiles supply content, the runtime is subject independent."""
import hashlib
import json
from pathlib import Path
from html import escape
from practice_student_tools import guided_questions, build_student_tools
from practice_skills import tag_question, build_skills, load_skills

ASSETS = Path(__file__).parent / 'assets'


def build_learning(root, label, hub, css):
    lessons = json.loads((root / 'foundations.json').read_text(encoding='utf-8'))
    banks = json.loads((root / 'repetition.json').read_text(encoding='utf-8'))
    questions = []
    # Discover links from rendered sections, rather than interpreting curriculum codes.
    pages = list(root.glob('basics-*.html')) + [root / 'prior-learning.html']
    for group in lessons.values():
        for lesson in group:
            key = lesson.get('code', lesson.get('id'))
            anchor = 'basic-' + key if 'code' in lesson else key
            page = next(p for p in pages if f'id="{anchor}"' in p.read_text(encoding='utf-8'))
            for kind, items in [('step', lesson['steps']), ('repeat', banks[key]['questions'])]:
                for q in items:
                    identity = json.dumps([q['prompt'], q['answer']], ensure_ascii=False, sort_keys=True)
                    qid = root.name + ':' + key + ':' + kind + ':' + hashlib.sha256(identity.encode()).hexdigest()[:16]
                    questions.append(dict(q, id=qid, topic=key, title=lesson['title'], kind=kind,
                                          path=page.name + '#' + anchor))
    authored = root / 'authored-mcq.json'
    if authored.is_file():
        questions.extend(json.loads(authored.read_text(encoding='utf-8')))
    for q in questions: tag_question(root,q)
    questions.extend(guided_questions(root))
    skills = load_skills(str(root))
    build_skills(root,label,hub,css,questions)
    catalog = dict(profile=root.name, label=label, hub=hub, questions=questions, numeric_skills=skills["numeric_skills"] if skills else [], skill_labels={s["id"]:s["label"] for s in skills["skills"]} if skills else {})
    (root / 'learning-catalog.js').write_text('window.PRACTICE_CATALOG = ' + json.dumps(catalog, ensure_ascii=False).replace('<', '\\u003c') + ';\n', encoding='utf-8')
    for name in ('learning.js', 'learning.css', 'mcq-review.js'):
        (root / name).write_bytes((ASSETS / name).read_bytes())
    (root / 'my-practice.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>My practice · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="learning.css">'
        '</head><body><main id="learning-workspace"></main><script src="learning-catalog.js"></script><script src="learning.js"></script><script src="guided-practice.js"></script></body></html>', encoding='utf-8')
    (root / 'question-review.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Teacher question review · {escape(label)}</title><link rel="stylesheet" href="{css}">'
        '<style>#mcq-review label{display:block;margin:1rem 0}#mcq-review textarea{display:block;width:100%;box-sizing:border-box}#mcq-review button{margin:.3rem}</style>'
        '</head><body><main><header>'
        f'<a href="{hub}">← Practice hub</a><h1>Teacher question review</h1>'
        '<p>Review MCQ wording, choices and feedback; flag corrections or repetition. This is an offline editorial tool, without an account or shared server.</p>'
        '<p>Save drafts, then export mcq-review.json. To publish, place it in this subject’s resource folder and run its page builder. '
        'Edits here do not change student pages automatically. Teacher notes are included in exported files; do not include private student information.</p>'
        '</header><div id="mcq-review"></div></main><script src="learning-catalog.js"></script><script src="mcq-review.js"></script></body></html>', encoding='utf-8')
    build_student_tools(root,label,hub,css)
    for page in root.glob('*.html'):
        if page.name in ('my-practice.html', 'question-review.html', 'skills-practice.html', 'skills.html', 'student-backup.html', 'class-practice.html', 'guided-practice.html', 'learning-home.html', 'investigations.html'):
            continue
        text = page.read_text(encoding='utf-8')
        if 'skills-practice.css' not in text:
            text = text.replace('</head>', '<link rel="stylesheet" href="skills-practice.css"></head>')
        if page.name == hub:
            text = text.replace('</header>', '<p><a href="learning-home.html">Start here: my learning</a> · <a href="investigations.html">Investigations</a> · <a href="guided-practice.html">Guided problem solving</a> · <a href="student-backup.html">Combined student backup</a> · <a href="class-practice.html">Teacher class overview</a> · <a href="question-review.html">Teacher: review questions</a></p></header>', 1)
        if 'class="booklet-entry"' in text:
            # Reference booklets stay script-free, including when opened for printing.
            text = text.replace('</header>', '<p><a href="my-practice.html">My practice</a></p></header>', 1)
            page.write_text(text, encoding='utf-8')
            continue
        if 'src="learning.js"' not in text:
            text = text.replace('<body>', '<body><script src="learning-catalog.js"></script><script src="learning.js"></script>')
            text = text.replace('</head>', '<link rel="stylesheet" href="learning.css"></head>')
        text = text.replace('No responses are saved or sent anywhere.', 'Small-step and repeat-practice progress can be saved in this browser. Export it from My practice to keep a portable copy. Nothing is sent automatically.')
        page.write_text(text, encoding='utf-8')
