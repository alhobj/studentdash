"""Build offline IB Chemistry practice pages from profile-local authored content.

Run: python tools/build_chemistry_practice.py
The JSON files and shared CSS/JS in resources/ib-chemistry are the source files.
"""
import json
import re
from html import escape
from pathlib import Path

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
    assert len({t['id'] for t in topics}) == len(topics)
    for topic in topics:
        assert topic['parent'] in groups and topic['activities']
        assert all(key in activities for key in topic['activities'])
    assigned = {key for t in topics for key in t['activities']}
    assert assigned == set(activities), 'Every activity needs a syllabus home'

    footer = ('<footer><p>Original independent practice with invented numerical scenarios. '
              'Not an official IB assessment. Responses stay in this page and are not saved or sent to a teacher. '
              'Numerical checks accept answers within 1%; show appropriate units and significant figures in written work.</p>'
              f'<p>Organisation follows the {escape(syllabus["version"])} syllabus: '
              f'<a href="{escape(syllabus["source"])}">IB Chemistry topic outline</a> (internet required). '
              'These activities introduce selected concepts; they do not cover every syllabus statement.</p></footer>')

    def scripts(keys):
        data = {key: questions[key] for key in keys if key in questions}
        # Embedded JSON keeps direct file:// use working without fetch or a server.
        serialized = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
        return ('<script src="practice-activities.js"></script>'
                '<script src="moly-triangles.js"></script>'
                '<script src="practice-labs.js"></script>'
                f'<script type="application/json" id="practice-question-data">{serialized}</script>'
                '<script src="practice-questions.js"></script>')

    def activity_markup(key, topic=None):
        html = activities[key]['html']
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
                f'<p>{escape(topic.get("focus", "Predict. Change one variable. Explain what happens."))}</p></header>'
                '<nav id="activity-index" aria-label="Activities in this sub-part">'
                + ''.join(f'<a href="#{key}">{escape(activities[key]["title"])}</a>' for key in keys)
                + '</nav><noscript><p class="error">Enable JavaScript for interactive controls. Worked explanations remain readable.</p></noscript>'
                + ''.join(activity_markup(key, topic) for key in keys))
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
            'answer feedback and worked explanations. R1.4 is additional higher level (AHL).</p></header>'
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
    (ROOT / 'practice.html').write_text(page('Practice hub', body, redirect_js), encoding='utf-8')

    keys = list(activities)
    body = ('<header><a href="practice.html">← Practice hub</a><h1>All chemistry activities</h1>'
            '<p>Use the hub for focused practice by syllabus sub-part.</p></header>'
            '<nav id="activity-index" aria-label="Practice activities">'
            + ''.join(f'<a href="#{key}">{escape(activities[key]["title"])}</a>' for key in keys)
            + '</nav>' + ''.join(activity_markup(key) for key in keys) + footer)
    (ROOT / 'all-practice.html').write_text(page('All activities', body, scripts(keys)), encoding='utf-8')
    print(f'Built hub, {len(topics)} topic pages and all-activities page; {len(activities)} unique activities.')


if __name__ == '__main__':
    build()
