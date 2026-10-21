"""Offline practice navigation and low-stakes skill checks from profile data."""
import json
from html import escape


def build_support(root, title, hub, stylesheet, topics):
    checks = json.loads((root / 'readiness.json').read_text(encoding='utf-8'))
    assert len({c['id'] for c in checks}) == len(checks)

    def write(name, heading, body):
        (root / name).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(heading)} · {escape(title)}</title><link rel="stylesheet" href="{stylesheet}">'
            '</head><body><main>' + body + '<footer><p>Works offline. Responses remain in this page; '
            'nothing is saved or sent to a teacher.</p></footer></main><script src="study-support.js"></script></body></html>\n',
            encoding='utf-8')

    body = (f'<header><a href="{hub}">← {escape(title)} hub</a><h1>Find your next step</h1>'
            '<p>Try any of these eight short skill checks. An answer can help you choose a useful next activity; '
            'this is not a test of your overall ability or a complete syllabus assessment. There is no timer or score. '
            'Use a calculator if needed. Enter numbers only in the stated units.</p>'
            '<p>If a question is unfamiliar, open its worked explanation and follow the prior-learning link. '
            'A correct answer is a starting point for further practice, not proof of mastery.</p>'
            '<p><a href="find-practice.html">Already know what to practise? Find a section and difficulty level.</a></p></header>'
            '<noscript><p>Enable JavaScript for answer checks and recommendations. Worked explanations and practice links are available below.</p></noscript>')
    for c in checks:
        key = c['id']
        payload = escape(json.dumps(c, ensure_ascii=False), quote=True)
        body += (f'<section id="{key}" data-readiness="{payload}"><h2>{escape(c["title"])}</h2>'
                 f'<form novalidate><label for="{key}-answer">{escape(c["prompt"])}</label>'
                 f'<input type="number" step="any" id="{key}-answer" aria-describedby="{key}-feedback">'
                 '<button type="submit">Check and suggest a next step</button>'
                 f'<p id="{key}-feedback" class="feedback" role="status"></p></form>'
                 '<p class="recommendation" aria-live="polite"></p>'
                 f'<details class="ready-working"><summary>Worked explanation</summary><p>{escape(c["working"])}</p></details>'
                 '<details><summary>Choose a practice route</summary><nav>'
                 f'<a href="{c["prior"]}">Revisit the prerequisite</a><a href="{c["basic"]}">Build with small steps</a>'
                 f'<a href="{c["challenge"]}">Try a harder task</a></nav></details>'
                 '<button type="button" class="readiness-reset">Try this check again</button></section>')
    write('readiness.html', 'Find your next step', body)

    body = (f'<header><a href="{hub}">← {escape(title)} hub</a><h1>Find practice</h1>'
            '<p>Search by syllabus code, topic or activity name. Choose a difficulty level to narrow the links. '
            'All sections remain listed when JavaScript is disabled.</p><nav>'
            '<a href="readiness.html">Help me choose a starting point</a><a href="prior-learning.html">Prior-learning lessons</a></nav></header>'
            '<div class="finder-controls" hidden><label for="practice-search">Search sections and activities</label>'
            '<input id="practice-search" type="search" placeholder="Try a topic, an activity, or a syllabus code">'
            '<label for="practice-level">Difficulty level</label><select id="practice-level">'
            '<option value="all">All levels</option><option value="basic">Small steps</option>'
            '<option value="explore">Main practice</option><option value="challenge">Harder tasks</option></select>'
            '<button type="button" id="finder-reset">Clear filters</button>'
            '<p id="finder-status" role="status"></p></div>')
    for t in topics:
        search = escape(' '.join([t['id'], t['title'], t.get('keywords', '')]), quote=True)
        body += (f'<section data-find="{search}"><p class="eyebrow">{escape(t["id"])}'
                 + (' · AHL' if t.get('level') == 'AHL' else '') + f'</p><h2>{escape(t["title"])}</h2><nav>'
                 f'<a data-level="basic" href="{t["basic"]}">Small steps</a>'
                 f'<a data-level="explore" href="{t["explore"]}">Main practice</a>'
                 f'<a data-level="challenge" href="{t["challenge"]}">Harder task</a></nav></section>')
    body += '<p id="finder-empty" hidden>No sections match. Try a shorter phrase or a syllabus code, or clear the filters.</p>'
    write('find-practice.html', 'Find practice', body)
