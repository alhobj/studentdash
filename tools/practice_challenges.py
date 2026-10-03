"""Render profile-local challenge data without adding curriculum rules to the app."""
import json
import math
from html import escape


def build_challenges(root, groups, topics, hub, stylesheet):
    rows = json.loads((root / 'challenges.json').read_text(encoding='utf-8'))
    by_code = {row['code']: row for row in rows}
    assert len(by_code) == len(rows)
    assert set(by_code) == {topic['id'] for topic in topics}
    assert all(len(row['parts']) >= 2 and row['reason'] and row['discussion'] for row in rows)
    assert all(isinstance(p['answer'], (int, float)) and math.isfinite(p['answer'])
               and p['hint'] and p['working'] for row in rows for p in row['parts'])

    def write(name, title, body):
        footer = ('<footer><p>Original fictional teaching problems. Numerical checks allow 0.1% tolerance '
                  '(an absolute tolerance of 10⁻⁸ for zero). Keep full calculator precision until the final answer. '
                  'A numerical check does not assess your method, units or written argument. '
                  'Answers stay in this page and are not saved or transmitted. Works offline.</p></footer>')
        (root / name).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)} · Challenge practice</title><link rel="stylesheet" href="{stylesheet}">'
            '</head><body><main>' + body + footer + '</main><script src="challenges.js"></script></body></html>\n',
            encoding='utf-8')

    intro = ('<p>Combine ideas, choose a method and justify your conclusions. Try the two linked parts '
             'before opening hints or worked solutions. Then write your reasoning and compare it with the discussion. '
             'Written responses are for self-review; they are not automatically marked.</p>'
             '<noscript><p>Enable JavaScript for numerical checks. Problems, hints and worked solutions remain readable.</p></noscript>')
    index = f'<header><a href="{hub}">← Practice hub</a><h1>Harder tasks: connect and explain</h1>{intro}</header>'
    for group in groups:
        selected = [t for t in topics if t['parent'] == group['id']]
        index += (f'<section><h2>{escape(group["title"])}</h2><p>{len(selected)} multi-part challenges</p>'
                  f'<a href="challenges-{group["id"].lower()}.html">Open {group["id"]} harder tasks →</a></section>')
        body = (f'<header><a href="challenges.html">← All harder tasks</a><h1>{escape(group["title"])}</h1>{intro}</header>'
                '<nav aria-label="Challenge sections">' + ''.join(
                    f'<a href="#challenge-{t["id"]}">{t["id"]}' + (' · AHL' if t.get('level') == 'AHL' else '') + '</a>'
                    for t in selected) + '</nav>')
        for topic in selected:
            c = by_code[topic['id']]
            key = 'challenge-' + topic['id']
            level = ' · AHL' if topic.get('level') == 'AHL' else ''
            body += (f'<section id="{key}" data-challenge><p class="eyebrow">{topic["id"]}{level} · Harder task</p>'
                     f'<h2>{escape(c["title"])}</h2><p>{escape(c["scenario"])}</p>')
            for number, part in enumerate(c['parts'], 1):
                field = f'{key}-part-{number}'
                body += (f'<form class="challenge-part" data-answer="{part["answer"]}" novalidate>'
                         f'<h3>Part {number}</h3><label for="{field}">{escape(part["prompt"])}</label>'
                         f'<input type="number" step="any" id="{field}" aria-describedby="{field}-feedback">'
                         '<button type="submit">Check numerical answer</button>'
                         f'<p id="{field}-feedback" class="feedback" role="status"></p>'
                         f'<details><summary>Hint</summary><p>{escape(part["hint"])}</p></details>'
                         f'<details><summary>Worked solution</summary><p>{escape(part["working"])}</p></details></form>')
            body += (f'<h3>Explain and evaluate</h3><label for="{key}-reason">{escape(c["reason"])}</label>'
                     f'<textarea id="{key}-reason" rows="5" placeholder="Write your reasoning here, or work on paper. This is not saved."></textarea>'
                     f'<details><summary>Compare your reasoning</summary><p>{escape(c["discussion"])}</p></details>'
                     '<button type="button" class="challenge-reset">Reset this task</button>'
                     f'<p><a href="{topic["filename"]}">Revisit {topic["id"]} practice</a></p></section>')
        body += f'<nav><a href="{hub}">Practice hub</a><a href="challenges.html">All harder tasks</a></nav>'
        write(f'challenges-{group["id"].lower()}.html', group['title'], body)
    write('challenges.html', 'Harder tasks', index)
