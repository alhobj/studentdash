"""Build offline IB Chemistry practice pages from profile-local authored content.

Run: python tools/build_chemistry_practice.py
The JSON files and shared CSS/JS in resources/ib-chemistry are the source files.
"""
import json
import re
from html import escape
from pathlib import Path
from practice_challenges import build_challenges
from build_learning import build_learning
from practice_mcq import build_mcq, render_mcq
from practice_support import build_support
from practice_repetition import load_repetition, render_repetition
from practice_syllabus import render_syllabus
from practice_booklets import build_booklet, booklet_link, render_booklet_help

ROOT = Path(__file__).resolve().parents[1] / 'resources' / 'ib-chemistry'


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def filename(topic):
    return topic['id'].lower().replace('.', '-') + '.html'


def page(title, body, scripts=''):
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)} · Chemistry practice</title>'
            '<link rel="stylesheet" href="practice.css"></head><body><main>'
            + body + '</main>' + scripts + '</body></html>\n')


def question_section(key, activity):
    return (f'<section id="{key}" class="question-practice" data-practice="{key}">'
            f'<p class="eyebrow">Predict · check · explain</p><h2>{escape(activity["title"])}</h2>'
            f'<p>{escape(activity["intro"])}</p>'
            '<p>Choose a scenario, enter a prediction and check it. Try again or reveal the explanation, then move to another scenario.</p>'
            '<div class="question-host"></div>'
            '<noscript><p>Enable JavaScript to use the interactive answer checks.</p></noscript>'
            '<details><summary>Scenarios and worked explanations</summary>'
            + ''.join(f'<h3>{escape(q["name"])}</h3><p>{escape(q["prompt"])}</p>'
                      f'<p><strong>Answer: {escape(str(q["answer"]))}</strong>. {escape(q["explanation"])}</p>'
                      for q in activity['questions']) + '</details></section>')


def build():
    authored_mcq = build_mcq(ROOT)
    build_booklet(ROOT)
    syllabus = read_json('practice-syllabus.json')
    activities = read_json('practice-activities.json')
    labs = read_json('practice-labs.json')
    for key, lab in labs.items():
        activities[key] = {
            'title': 'Hands-on: ' + lab['title'],
            'html': (f'<section id="{key}" data-lab="{key}"><p class="eyebrow">Hands-on experiment</p>'
                     f'<h2>{escape(lab["title"])}</h2><p>{escape(lab["intro"])}</p>'
                     f'<p class="lab-challenge"><strong>Your challenge:</strong> {escape(lab["challenge"])}</p>'
                     '<div class="lab-host"></div><noscript><p>Enable JavaScript to operate this experiment.</p></noscript>'
                     f'<details><summary>Model, method and limits</summary><p>{escape(lab["method"])}</p></details></section>')
        }
    questions = read_json('practice-questions.json')
    extensions = read_json('practice-extensions.json')
    assert not questions.keys() & extensions.keys(), 'Question activity IDs must be unique'
    questions.update(extensions)
    for key, activity in questions.items():
        activities[key] = {'title': activity['title'], 'html': question_section(key, activity)}
    topics = syllabus['topics']
    groups = {group['id']: group for group in syllabus['groups']}
    foundations = read_json('foundations.json')
    repetition = load_repetition(ROOT, foundations)
    starters = {c['code']: c for c in foundations['sections']}
    assert len(starters) == len(foundations['sections'])
    assert set(starters) == {t['id'] for t in topics}, 'Each sub-part needs a starter'
    build_support(ROOT, 'Chemistry', 'practice.html', 'practice.css', [
        dict(t, keywords=' '.join(activities[k]['title'] for k in t['activities']),
             basic=f'basics-{t["parent"].lower()}.html#basic-{t["id"]}', explore=filename(t),
             challenge=f'challenges-{t["parent"].lower()}.html#challenge-{t["id"]}') for t in topics])
    build_challenges(ROOT, list(groups.values()), [dict(t, filename=filename(t)) for t in topics],
                     'practice.html', 'practice.css')
    assert len({t['id'] for t in topics}) == len(topics)
    for topic in topics:
        assert topic['parent'] in groups and topic['activities']
        assert all(key in activities for key in topic['activities'])
    assigned = {key for t in topics for key in t['activities']}
    assert assigned == set(activities), 'Every activity needs a syllabus home'

    footer = ('<footer><p>Original independent practice with invented numerical scenarios. '
              'Not an official IB assessment. Small-step and repeat answers can be saved in this browser through My practice. Other activity settings stay in the open page; nothing is sent automatically. '
              'Main activity numerical checks accept answers within 1%; small-step tasks check the stated numerical result. '
              'Show appropriate units and significant figures in written work.</p>'
              f'<p>Organisation follows the {escape(syllabus["version"])} syllabus: '
              f'<a href="{escape(syllabus["source"])}">IB Chemistry topic outline</a> (internet required). '
              'These activities introduce selected concepts; they do not cover every syllabus statement.</p></footer>')

    def lesson(c, key, topic=None):
        label = 'Prior learning' if topic is None else topic['id'] + (' · AHL' if topic.get('level') == 'AHL' else '') + ' · Start here'
        html = (f'<section id="{key}" data-foundation><p class="eyebrow">{label}</p>'
                f'<h2>{escape(c["title"])}</h2><p class="foundation-reminder">{escape(c["reminder"])}</p>')
        html += render_booklet_help(ROOT, [topic['id']] if topic else [], c.get('id'))
        for i, step in enumerate(c['steps'], 1):
            field = f'{key}-step-{i}'
            text_answer = isinstance(step['answer'], list)
            accepted = escape(json.dumps(step['answer'], ensure_ascii=False), quote=True)
            html += (f'<form class="foundation-step" data-answer="{accepted}" novalidate><h3>Step {i}</h3>'
                     f'<label for="{field}">{escape(step["prompt"])}</label>'
                     f'<input id="{field}" type="{"text" if text_answer else "number"}" '
                     + ('' if text_answer else 'step="any" ') + f'aria-describedby="{field}-feedback" autocomplete="off">'
                     '<button type="submit">Check this step</button>'
                     f'<p id="{field}-feedback" class="feedback" role="status"></p>'
                     f'<details class="foundation-hint"><summary>Give me a hint</summary><p>{escape(step["hint"])}</p></details>'
                     f'<details><summary>Show the worked step</summary><p>{escape(step["working"])}</p></details></form>')
        html += render_repetition(repetition[c.get('code', c.get('id'))], key)
        html += '<button type="button" class="foundation-reset">Try these steps again</button>'
        if topic:
            html += f'<p><a href="{filename(topic)}">Next: explore {topic["id"]} →</a></p>'
        return html + '</section>'

    intro = ('<p>Take one small step at a time. Read the reminder, try the question and open a hint whenever you need one. '
             'Use a calculator if helpful. For calculations, enter a number only; units are given in the question. '
             'For word answers, use the short term requested. There is no timer or assessment score. My practice saves these short answers in this browser; export progress to move it between computers.</p>'
             '<noscript><p>Enable JavaScript for answer checks. Hints and worked steps remain available without it.</p></noscript>')
    foundation_script = '<script src="foundations.js"></script><script src="similar-practice.js"></script>'
    body = '<header><a href="practice.html">← Chemistry hub</a><h1>Prior learning: small steps</h1>' + intro + '</header>'
    body += '<nav aria-label="Prior-learning lessons">' + ''.join(f'<a href="#{c["id"]}">{escape(c["title"])}</a>' for c in foundations['prior']) + '</nav>'
    body += ''.join(lesson(c, c['id']) for c in foundations['prior'])
    body += '<h2>Choose your next group</h2><nav>' + ''.join(f'<a href="basics-{g.lower()}.html">{g}: small steps</a>' for g in groups) + '</nav>' + footer
    (ROOT / 'prior-learning.html').write_text(page('Prior learning', body, foundation_script), encoding='utf-8')
    for group in groups.values():
        group_topics = [t for t in topics if t['parent'] == group['id']]
        body = (f'<header><a href="practice.html#{group["id"]}">← Chemistry hub</a><p class="eyebrow">{group["id"]} · Start here</p>'
                f'<h1>{escape(group["title"])}: small steps</h1>' + intro + '</header>'
                + render_syllabus(ROOT, [t['id'] for t in group_topics])
                + '<p><a href="prior-learning.html">Revisit prior learning</a></p><nav aria-label="Basic lessons">'
                + ''.join(f'<a href="#basic-{t["id"]}">{t["id"]}' + (' · AHL' if t.get('level') == 'AHL' else '') + f': {escape(starters[t["id"]]["title"])}</a>' for t in group_topics) + '</nav>'
                + ''.join(lesson(starters[t['id']], 'basic-'+t['id'], t) for t in group_topics) + footer)
        (ROOT / f'basics-{group["id"].lower()}.html').write_text(page(group['id']+' small steps', body, foundation_script), encoding='utf-8')

    def scripts(keys):
        data = {key: questions[key] for key in keys if key in questions}
        # Embedded JSON keeps direct file:// use working without fetch or a server.
        serialized = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
        return ('<script src="practice-activities.js"></script>'
                '<script src="moly-triangles.js"></script>'
                '<script src="practice-labs.js"></script>'
                f'<script type="application/json" id="practice-question-data">{serialized}</script>'
                '<script src="practice-questions.js"></script><script src="authored-mcq.js"></script>')

    def activity_markup(key, topic=None):
        html = activities[key]['html']
        related = [topic['id']] if topic else [t['id'] for t in topics if key in t['activities']]
        html = html.replace('</section>', render_booklet_help(ROOT, related) + '</section>', 1)
        if topic:
            html = re.sub(r'<p class="eyebrow">.*?</p>',
                          f'<p class="eyebrow">{topic["id"]} / Practice</p>', html, count=1)
        if topic and key == 'bonding':
            allowed = topic['materials']
            select = re.search(r'(<select id="bond-material">)(.*?)(</select>)', html, re.S)
            options = ''.join(match[0] for match in re.findall(
                r'(<option value="([^"]+)"[^>]*>.*?</option>)', select[2], re.S)
                              if match[1] in allowed)
            html = html[:select.start(2)] + options + html[select.end(2):]
        return html

    for index, topic in enumerate(topics):
        code, title, keys = topic['id'], topic['title'], topic['activities']
        level = ' · Additional higher level' if topic.get('level') == 'AHL' else ''
        body = (f'<header><a href="practice.html#{topic["parent"]}">← Practice hub</a>'
                f'<p class="eyebrow">{code}{level}</p><h1>{escape(title)}</h1>'
                f'<p>{escape(topic.get("focus", "Predict. Change one variable. Explain what happens."))}</p>'
                f'<p>Build up to these activities: <a href="basics-{topic["parent"].lower()}.html#basic-{code}">start with two short steps</a> '
                'or <a href="prior-learning.html">revisit prior learning</a>.</p>'
                f'<p>Ready for more? <a href="challenges-{topic["parent"].lower()}.html#challenge-{code}">Try the multi-part harder task</a>.</p></header>'
                + render_syllabus(ROOT, [code])
                + '<nav id="activity-index" aria-label="Activities in this sub-part">'
                + ''.join(f'<a href="#{key}">{escape(activities[key]["title"])}</a>' for key in keys)
                + '</nav><noscript><p class="error">Enable JavaScript for interactive controls. Worked explanations remain readable.</p></noscript>'
                + ''.join(activity_markup(key, topic) for key in keys))
        if any(q['topic'] == code for q in authored_mcq):
            body = body.replace('</header>', '<p><a href="#authored-mcq">20 A–D questions with instant feedback</a></p></header>', 1)
            body += render_mcq(authored_mcq, code)
        body += '<nav aria-label="Syllabus navigation">'
        if index:
            previous = topics[index-1]
            body += f'<a href="{filename(previous)}">← {previous["id"]}</a>'
        body += '<a href="practice.html">All syllabus sub-parts</a>'
        if index+1 < len(topics):
            following = topics[index+1]
            body += f'<a href="{filename(following)}">{following["id"]} →</a>'
        body += '</nav>' + footer
        (ROOT / filename(topic)).write_text(page(code+' · '+title, body, scripts(keys)), encoding='utf-8')

    body = ('<header><p class="eyebrow">IB Chemistry · Independent practice</p>'
            '<h1>Chemistry practice hub</h1>'
            f'<p class="muted">{len(topics)} syllabus sub-parts · {len(activities)} interactive activities</p>'
            '<p>Choose a syllabus sub-part to open its practices. Each page has interactive questions or models, '
            'answer feedback and worked explanations. R1.4 is additional higher level (AHL).</p>'
            '<nav><a href="readiness.html">Not sure where to start?</a><a href="find-practice.html">Find practice by topic and level</a>'
            '<a href="challenges.html">Harder tasks for all 22 syllabus sub-parts →</a></nav></header>'
            '<section><p class="eyebrow">Start here</p><h2>Build confidence with small steps</h2>'
            '<p>12 prior-learning lessons and two starter tasks for every syllabus sub-part. Each includes a reminder, '
            'optional hints, worked steps and answer checks. Every lesson also includes at least six more questions using the same method.</p><nav><a href="prior-learning.html">Prior learning: 24 short tasks + extra practice</a>'
            + ''.join(f'<a href="basics-{g.lower()}.html">{g}: small steps</a>' for g in groups) + '</nav></section>'
            '<nav aria-label="Syllabus groups">'
            + ''.join(f'<a href="#{g["id"]}">{g["id"]} · {g["parent"]} {g["id"][1:]}</a>' for g in groups.values())
            + '</nav>')
    for group in groups.values():
        body += f'<section id="{group["id"]}"><p class="eyebrow">{group["parent"]} {group["id"][1:]}</p><h2>{escape(group["title"])}</h2><div class="topic-cards">'
        for topic in topics:
            if topic['parent'] != group['id']:
                continue
            count = len(topic['activities'])
            body += (f'<a class="topic-card" href="{filename(topic)}"><span class="eyebrow">{topic["id"]}'
                     + (' · AHL' if topic.get('level') else '') + '</span>'
                     f'<h3>{escape(topic["title"])}</h3><p>{count} activit{"y" if count == 1 else "ies"}</p>'
                     '<span class="muted">' + ' · '.join(escape(activities[key]['title']) for key in topic['activities'])
                     + '</span></a>')
        body += '</div></section>'
    body += '<p><a href="all-practice.html">Open all activities on one page</a></p>' + footer
    # Preserve existing bookmarks such as practice.html#holy-moly.
    redirects = {}
    for topic in topics:
        for key in topic['activities']:
            redirects.setdefault(key, filename(topic))
    redirect_js = ('<script>const activityPages='+json.dumps(redirects)+';'
                   'const activity=location.hash.slice(1);'
                   'if(Object.hasOwn(activityPages,activity)) location.replace(activityPages[activity]+location.hash);</script>')
    mcq_topics = list(dict.fromkeys(q['topic'] for q in authored_mcq))
    mcq_links = f'<p>{len(authored_mcq)} authored A–D questions with instant feedback:</p><nav>' + ''.join(
        f'<a href="{code.lower().replace(".", "-")}.html#authored-mcq">{code}: 20 questions</a>' for code in mcq_topics) + '</nav>'
    body = body.replace('</header>', mcq_links + '</header>', 1)
    body = body.replace('</header>', '<nav>' + booklet_link(ROOT) + '</nav></header>', 1)
    (ROOT / 'practice.html').write_text(page('Practice hub', body, redirect_js), encoding='utf-8')

    keys = list(activities)
    body = ('<header><a href="practice.html">← Practice hub</a><h1>All chemistry activities</h1>'
            '<p>Use the hub for focused practice by syllabus sub-part, including small-step starters, or '
            '<a href="prior-learning.html">begin with prior learning</a>.</p></header>'
            '<nav id="activity-index" aria-label="Practice activities">'
            + ''.join(f'<a href="#{key}">{escape(activities[key]["title"])}</a>' for key in keys)
            + '</nav>' + ''.join(activity_markup(key) for key in keys) + footer)
    (ROOT / 'all-practice.html').write_text(page('All activities', body, scripts(keys)), encoding='utf-8')
    build_learning(ROOT, 'Chemistry', 'practice.html', 'practice.css')
    print(f'Built hub, {len(topics)} topic pages and all-activities page; {len(activities)} unique activities.')


if __name__ == '__main__':
    build()
