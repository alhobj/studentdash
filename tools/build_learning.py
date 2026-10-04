"""Portable practice journal; profiles supply content, the runtime is subject independent."""
import hashlib
import json
from pathlib import Path
from html import escape

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
    catalog = dict(profile=root.name, label=label, hub=hub, questions=questions)
    (root / 'learning-catalog.js').write_text('window.PRACTICE_CATALOG = ' + json.dumps(catalog, ensure_ascii=False).replace('<', '\\u003c') + ';\n', encoding='utf-8')
    for name in ('learning.js', 'learning.css'):
        (root / name).write_bytes((ASSETS / name).read_bytes())
    (root / 'my-practice.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>My practice · {escape(label)}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="learning.css">'
        '</head><body><main id="learning-workspace"></main><script src="learning-catalog.js"></script><script src="learning.js"></script></body></html>', encoding='utf-8')
    for page in root.glob('*.html'):
        if page.name == 'my-practice.html':
            continue
        text = page.read_text(encoding='utf-8')
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
