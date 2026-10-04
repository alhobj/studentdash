"""Generate the standalone, offline Mathematics AI SL practice hub and topic pages."""
import json
from html import escape
from pathlib import Path
from practice_challenges import build_challenges
from build_learning import build_learning
from practice_mcq import build_mcq, render_mcq
from practice_support import build_support
from practice_repetition import load_repetition, render_repetition
from practice_syllabus import render_syllabus
from practice_booklets import build_booklet, booklet_link, render_booklet_help

ROOT = Path(__file__).resolve().parents[1] / 'resources' / 'ib-math-ai-sl'
TOPICS = {1: 'Number and algebra', 2: 'Functions', 3: 'Geometry and trigonometry',
          4: 'Statistics and probability', 5: 'Calculus'}
SOURCE = 'https://www.ibo.org/globalassets/new-structure/university-admission/pdfs/subject-guides/mathematics-applications-interpretation-guide.pdf'


def build():
    authored_mcq = build_mcq(ROOT, 'math')
    (ROOT / 'authored-mcq.js').write_text((ROOT.parent / 'ib-chemistry' / 'authored-mcq.js').read_text(encoding='utf-8'), encoding='utf-8')
    build_booklet(ROOT)
    data = json.loads((ROOT / 'activities.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'extensions.json').read_text(encoding='utf-8'))
    assert not data.keys() & extra.keys(), 'Duplicate activity keys'
    data.update(extra)
    coverage = json.loads((ROOT / 'coverage.json').read_text(encoding='utf-8'))
    foundations = json.loads((ROOT / 'foundations.json').read_text(encoding='utf-8'))
    repetition = load_repetition(ROOT, foundations)
    expected = {f'{topic}.{n}' for topic, count in enumerate([8, 6, 6, 11, 8], 1) for n in range(1, count + 1)}
    assert {c['code'] for c in coverage} == expected and len(coverage) == 39
    assert {c['code'] for c in foundations['sections']} == expected
    assert len(foundations['sections']) == len(expected)
    assert all(c['activity'] in data for c in foundations['sections'])
    assert all(key in data for c in coverage for key in c['activities'])
    assert all(c['topic'] in TOPICS for c in data.values())
    build_support(ROOT, 'Mathematics AI SL', 'math-practice.html', 'math-practice.css', [
        {'id':c['code'], 'title':c['title'], 'keywords':' '.join(data[k]['title'] for k in c['activities']),
         'basic':f'basics-{c["code"].split(".")[0]}.html#basic-{c["code"]}',
         'explore':f'topic-{c["code"].split(".")[0]}.html#{c["activities"][0]}',
         'challenge':f'challenges-{c["code"].split(".")[0]}.html#challenge-{c["code"]}'} for c in coverage])
    build_challenges(ROOT, [{'id':str(n), 'title':t} for n,t in TOPICS.items()],
                     [{'id':c['code'], 'parent':c['code'].split('.')[0], 'title':c['title'],
                       'filename':f'topic-{c["code"].split(".")[0]}.html'} for c in coverage],
                     'math-practice.html', 'math-practice.css')
    footer = ('<footer><p>Independent AI SL practice for the first-assessment-2021 course. '
              'Original fictional examples; not official IB assessment material. All 39 SL sub-topics have linked practice. '
              'This is a learning collection, not an exhaustive exam bank or a substitute for the mathematical exploration. '
              'No responses are saved or sent anywhere. All activities work offline.</p>'
              f'<p>Topic organisation: <a href="{SOURCE}">IB Mathematics: applications and interpretation guide</a> '
              '(internet required). Explorer checks allow 0.5% tolerance; small-step tasks check the stated numerical result. '
              'Checks do not assess significant-figure notation.</p></footer>')

    def write(name, title, body, activities=None):
        scripts = ''
        if activities:
            serialized = json.dumps(activities, ensure_ascii=False).replace('<', '\\u003c')
            scripts = f'<script type="application/json" id="math-data">{serialized}</script><script src="math-extensions.js"></script><script src="math-practice.js"></script>'
        if 'data-authored-mcq' in body:
            scripts += '<script src="authored-mcq.js"></script>'
        if 'data-foundation' in body:
            scripts += '<script src="foundations.js"></script><script src="similar-practice.js"></script>'
        text = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{escape(title)} · Mathematics AI SL</title><link rel="stylesheet" href="math-practice.css">'
                '</head><body><main>' + body + footer + '</main>' + scripts + '</body></html>\n')
        (ROOT / name).write_text(text, encoding='utf-8')

    def foundation_lesson(c, key):
        label = f'SL {c["code"]} · Start here' if 'code' in c else 'Prior learning'
        html = (f'<section id="{key}" data-foundation><p class="eyebrow">{label}</p><h2>{escape(c["title"])}</h2>'
                f'<p class="reminder">{escape(c["reminder"])}</p>')
        if 'code' in c:
            html += f'<p><a href="mcq-{c["code"].replace(".", "-")}.html">20 multiple-choice questions with instant feedback</a></p>'
        html += render_booklet_help(ROOT, [c['code']] if 'code' in c else [], c.get('id'))
        for i, step in enumerate(c['steps'], 1):
            field = f'{key}-step-{i}'
            html += (f'<form class="foundation-step" data-answer="{step["answer"]}"><h3>Step {i}</h3>'
                     f'<label for="{field}">{escape(step["prompt"])}</label>'
                     f'<input id="{field}" class="answer" type="number" step="any" aria-describedby="{field}-feedback">'
                     '<button type="submit">Check this step</button>'
                     f'<p id="{field}-feedback" class="feedback" role="status"></p>'
                     f'<details class="hint"><summary>Give me a hint</summary><p>{escape(step["hint"])}</p></details>'
                     f'<details><summary>Show the worked step</summary><p>{escape(step["working"])}</p></details></form>')
        html += render_repetition(repetition[c.get('code', c.get('id'))], key)
        html += '<button type="button" class="foundation-reset">Try these steps again</button>'
        if 'activity' in c:
            html += f'<p><a href="topic-{data[c["activity"]]["topic"]}.html#{c["activity"]}">Next: explore this idea →</a></p>'
        return html + '</section>'

    intro = ('<p>Work at your own pace. Read the reminder, try each step, and use a hint whenever you need one. '
             'You can use a calculator. Enter numbers only; units are stated in each question. '
             'There is no timer or assessment score. My practice saves these short answers in this browser; export progress to move it between computers.</p>'
             '<noscript><p>Enable JavaScript to check answers. Hints and worked steps can still be opened without it.</p></noscript>')
    body = '<header><a href="math-practice.html">← Mathematics hub</a><h1>Prior learning: small steps</h1>' + intro + '</header>'
    body += '<nav aria-label="Prior-learning lessons">' + ''.join(f'<a href="#{c["id"]}">{escape(c["title"])}</a>' for c in foundations['prior']) + '</nav>'
    body += ''.join(foundation_lesson(c, c['id']) for c in foundations['prior'])
    body += '<h2>Choose your next topic</h2><nav>' + ''.join(f'<a href="basics-{n}.html">{escape(t)}: start here</a>' for n, t in TOPICS.items()) + '</nav>'
    write('prior-learning.html', 'Prior learning', body)
    for n, title in TOPICS.items():
        lessons = [c for c in foundations['sections'] if c['code'].startswith(f'{n}.')]
        body = (f'<header><a href="math-practice.html">← Mathematics hub</a><p class="eyebrow">Topic {n} · Start here</p>'
                f'<h1>{escape(title)}: small steps</h1>' + intro + '</header>'
                + render_syllabus(ROOT, [c['code'] for c in lessons])
                + '<nav><a href="prior-learning.html">Practise prior learning</a>'
                f'<a href="topic-{n}.html">Open topic {n} explorers</a></nav><nav aria-label="Basic lessons">'
                + ''.join(f'<a href="#basic-{c["code"]}">SL {c["code"]}: {escape(c["title"])}</a>' for c in lessons) + '</nav>'
                + ''.join(foundation_lesson(c, f'basic-{c["code"]}') for c in lessons))
        write(f'basics-{n}.html', f'{title}: small steps', body)

    hub = ('<header><p class="eyebrow">Mathematics · Applications and interpretation SL</p>'
           '<h1>Mathematics practice hub</h1><p>Predict. Adjust. Model. Interpret.</p>'
           f'<p class="muted">Five topics · 39 syllabus sub-topics · {len(data)} hands-on explorers · {len(data)} numerical challenges</p>'
           '<p>Move sliders, edit data, simulate experiments and test models. Open a topic below. '
           'The challenges use fixed scenarios, so you can check your reasoning independently of the explorer settings.</p>'
           '<nav><a href="readiness.html">Not sure where to start?</a><a href="find-practice.html">Find practice by topic and level</a>'
           '<a href="coverage.html">Browse all 39 syllabus sub-topics</a><a href="challenges.html">Harder tasks: all 39 sections</a><a href="investigations.html">Investigations and reflection</a></nav></header>'
           '<section><p class="eyebrow">Start here</p><h2>Build confidence with small steps</h2>'
           '<p>12 prior-learning lessons and a two-step starter for each syllabus section. Read a reminder, try a short question, '
           'then open a hint or worked step when you need it. Every lesson also includes at least six more questions using the same method.</p><nav><a href="prior-learning.html">Prior learning: 24 short tasks + extra practice</a>'
           + ''.join(f'<a href="basics-{n}.html">Topic {n}: small steps</a>' for n in TOPICS) + '</nav></section><div class="cards">')
    for number, title in TOPICS.items():
        activities = {k: v for k, v in data.items() if v['topic'] == number}
        hub += (f'<a class="card" href="topic-{number}.html"><span class="eyebrow">Topic {number}</span>'
                f'<h2>{escape(title)}</h2><p>{len(activities)} explorers</p><p class="muted">'
                + ' · '.join(escape(v['title']) for v in activities.values()) + '</p></a>')
        body = (f'<header><a href="math-practice.html">← Mathematics hub</a><p class="eyebrow">AI SL · Topic {number}</p>'
                f'<h1>{escape(title)}</h1><a href="coverage.html#topic-{number}">Topic {number} syllabus checklist and guided tasks</a>'
                f'<p>Build up to these explorers: <a href="basics-{number}.html">start with short, guided tasks</a> '
                'or <a href="prior-learning.html">revisit prior learning</a>.</p>'
                f'<p>Ready for more? <a href="challenges-{number}.html">Try multi-part harder tasks</a>.</p></header>'
                + render_syllabus(ROOT, [c['code'] for c in coverage if c['code'].startswith(f'{number}.')])
                + '<nav aria-label="Multiple-choice practice">' + ''.join(f'<a href="mcq-{c["code"].replace(".", "-")}.html">SL {c["code"]}: 20 MCQs</a>' for c in coverage if c['code'].startswith(f'{number}.')) + '</nav>'
                + '<nav aria-label="Activities">'
                + ''.join(f'<a href="#{key}">{escape(c["title"])}</a>' for key, c in activities.items()) + '</nav>'
                '<noscript><p>Enable JavaScript for the explorers and answer checks. Worked explanations remain readable.</p></noscript>')
        for key, c in activities.items():
            codes = [v['code'] for v in coverage if key in v['activities']]
            links = ' · '.join(f'<a href="coverage.html#sl-{code}">SL {code}</a>' for code in codes)
            body += (f'<section id="{key}" data-math="{key}"><p class="eyebrow">Hands-on explorer · {links}</p><h2>{escape(c["title"])}</h2>'
                     + '<p>Start with: ' + ' · '.join(f'<a href="basics-{code.split(".")[0]}.html#basic-{code}">SL {code} small steps</a>' for code in codes) + '</p>'
                     f'<p>{escape(c["intro"])}</p><div class="controls"></div><div class="graph"></div>'
                     '<p class="result" aria-live="polite"></p>' + render_booklet_help(ROOT, codes)
                     + '<div class="challenge"><h3>Try a fixed scenario</h3>'
                     f'<p>{escape(c["challenge"])}</p><label for="{key}-answer">{escape(c["unit"])}</label>'
                     f'<input id="{key}-answer" class="answer" type="number" step="any">'
                     '<button type="button" class="check">Check answer</button><p class="feedback" role="status"></p>'
                     f'<details><summary>Worked explanation</summary><p>{escape(c["working"])}</p></details></div></section>')
        body += '<nav aria-label="Topic navigation">'
        if number > 1:
            body += f'<a href="topic-{number-1}.html">← Topic {number-1}</a>'
        body += '<a href="math-practice.html">All topics</a>'
        if number < 5:
            body += f'<a href="topic-{number+1}.html">Topic {number+1} →</a>'
        body += '</nav>'
        write(f'topic-{number}.html', title, body, activities)
    hub += '</div><section><h2>780 multiple-choice questions</h2><p>20 questions for every SL sub-topic, with immediate A–D feedback and explanations.</p><nav>' + ''.join(f'<a href="mcq-{c["code"].replace(".", "-")}.html">{c["code"]}: {escape(c["title"])}</a>' for c in coverage) + '</nav></section>'
    hub = hub.replace('</header>', '<nav>' + booklet_link(ROOT) + '</nav></header>', 1)
    write('math-practice.html', 'Mathematics practice hub', hub)
    body = ('<header><a href="math-practice.html">← Mathematics hub</a><h1>AI SL syllabus coverage</h1>'
            '<p>First assessment 2021 · 39 of 39 SL sub-topics. Each entry links to live activities and adds a guided task '
            'with a worked discussion. Use these tasks to practise explanations, diagrams, assumptions and calculator interpretation as well as numerical answers.</p>'
            '<p>These are original teaching summaries, not reproduced syllabus statements. Coverage means practice is provided for each sub-topic; '
            'it does not certify mastery. Work on paper or in your own notes; checkboxes last only while this page remains open.</p></header><nav>'
            + ''.join(f'<a href="#topic-{n}">Topic {n}</a>' for n in TOPICS) + '</nav>')
    for n, title in TOPICS.items():
        body += f'<h2 id="topic-{n}">{n}. {escape(title)}</h2>'
        for c in coverage:
            if not c['code'].startswith(f'{n}.'):
                continue
            code = c['code']
            body += (f'<section id="sl-{code}"><h3>SL {code} · {escape(c["title"])}</h3>'
                     f'<p><a href="mcq-{code.replace(".", "-")}.html">20 multiple-choice questions with instant feedback</a></p>'
                     f'<p><a href="basics-{n}.html#basic-{code}">Start here: two short steps with hints</a></p>'
                     f'<p><a href="challenges-{n}.html#challenge-{code}">Go further: multi-part harder task</a></p>'
                     '<nav aria-label="Linked practice">' + ''.join(f'<a href="topic-{data[k]["topic"]}.html#{k}">{escape(data[k]["title"])}</a>' for k in c['activities'])
                     + f'</nav><p>{escape(c["task"])}</p>' + render_booklet_help(ROOT, [code])
                     + f'<details><summary>Check your reasoning</summary><p>{escape(c["solution"])}</p></details>'
                     f'<label class="checklist"><input type="checkbox"> I can explain SL {code} and have tried its practice.</label></section>')
    write('coverage.html', 'Syllabus coverage', body)
    write('investigations.html', 'Investigations and reflection',
          '<header><a href="math-practice.html">← Mathematics hub</a><h1>Investigate, explain and reflect</h1>'
          '<p>Use the explorers as a mathematical toolkit. These prompts support exploration skills; they are not a completed internal assessment or an assessment rubric.</p></header>'
          '<section><h2>Which savings plan meets your goal?</h2><p>Choose a fictional savings goal and realistic constraints. Use the '
          '<a href="topic-1.html#annuity">annuity</a> and <a href="topic-1.html#finance">inflation</a> explorers to compare monthly deposits, nominal balances and purchasing power. '
          'Formulate a question, predict the result, make a parameter table and test sensitivity to rates. Explain timing assumptions, fees excluded from the model and the limitations of long-term predictions.</p></section>'
          '<section><h2>Where should a new service point go?</h2><p>Use <a href="topic-3.html#voronoi-regions">Voronoi cells</a> to compare locations for a third site. '
          'Choose an objective: equal areas, shortest typical journey or reducing the longest journey. State why these may lead to different locations. '
          'Compare candidate vertices and boundaries, record distances, and discuss the effect of roads or unequal population density.</p></section>'
          '<section><h2>Does the model predict new data?</h2><p>Fit a <a href="topic-2.html#model-family">model</a> to a fictional table, keep one point for validation, '
          'plot residuals and compare predictions with a simpler model. Justify the domain and units. Reflect on whether extra complexity improves useful predictions.</p></section>'
          '<section><h2>From simulation to statistical evidence</h2><p>Predict the mean of a <a href="topic-4.html#binomial">binomial experiment</a>, simulate several batches and record results. '
          'Discuss random variation and which assumptions a real experiment could violate. Design an independent-samples comparison, choose the alternative and significance level before collecting data, '
          'and use the <a href="topic-4.html#t-test">test explorer</a> to discuss effect size versus statistical significance.</p></section>'
          '<section><h2>Communicate your work</h2><p>Define variables and units; label diagrams and graphs; explain technology outputs; '
          'support conclusions with mathematics; check reasonableness and precision; acknowledge data sources; reflect on assumptions and improvements. '
          'Use your own question, reasoning and observations when developing an assessed exploration.</p></section>')
    for c in coverage:
        code = c['code']
        body = (f'<header><a href="math-practice.html">← Mathematics hub</a>'
                f'<h1>SL {code} · {escape(c["title"])}</h1>'
                f'<nav><a href="basics-{code.split(".")[0]}.html#basic-{code}">Guided small steps</a>'
                f'<a href="coverage.html#sl-{code}">Related explorers and tasks</a></nav></header>'
                + render_syllabus(ROOT, [code]) + render_booklet_help(ROOT, [code])
                + render_mcq(authored_mcq, code))
        write(f'mcq-{code.replace(".", "-")}.html', f'SL {code} multiple-choice practice', body)
    build_learning(ROOT, 'Mathematics AI SL', 'math-practice.html', 'math-practice.css')
    print(f'Built mathematics hub and five topic pages with {len(data)} explorers.')


if __name__ == '__main__':
    build()
