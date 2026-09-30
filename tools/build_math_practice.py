"""Generate the standalone, offline Mathematics AI SL practice hub and topic pages."""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'resources' / 'ib-math-ai-sl'
TOPICS = {1: 'Number and algebra', 2: 'Functions', 3: 'Geometry and trigonometry',
          4: 'Statistics and probability', 5: 'Calculus'}
SOURCE = 'https://www.ibo.org/globalassets/new-structure/university-admission/pdfs/subject-guides/mathematics-applications-interpretation-guide.pdf'


def build():
    data = json.loads((ROOT / 'activities.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'extensions.json').read_text(encoding='utf-8'))
    assert not data.keys() & extra.keys(), 'Duplicate activity keys'
    data.update(extra)
    coverage = json.loads((ROOT / 'coverage.json').read_text(encoding='utf-8'))
    expected = {f'{topic}.{n}' for topic, count in enumerate([8, 6, 6, 11, 8], 1) for n in range(1, count + 1)}
    assert {c['code'] for c in coverage} == expected and len(coverage) == 39
    assert all(key in data for c in coverage for key in c['activities'])
    assert all(c['topic'] in TOPICS for c in data.values())
    footer = ('<footer><p>Independent AI SL practice for the first-assessment-2021 course. '
              'Original fictional examples; not official IB assessment material. All 39 SL sub-topics have linked practice. '
              'This is a learning collection, not an exhaustive exam bank or a substitute for the mathematical exploration. '
              'No responses are saved or sent anywhere. All activities work offline.</p>'
              f'<p>Topic organisation: <a href="{SOURCE}">IB Mathematics: applications and interpretation guide</a> '
              '(internet required). Numerical checks allow 0.5% tolerance; this does not assess significant figures.</p></footer>')

    def write(name, title, body, activities=None):
        scripts = ''
        if activities:
            serialized = json.dumps(activities, ensure_ascii=False).replace('<', '\\u003c')
            scripts = f'<script type="application/json" id="math-data">{serialized}</script><script src="math-extensions.js"></script><script src="math-practice.js"></script>'
        text = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{escape(title)} · Mathematics AI SL</title><link rel="stylesheet" href="math-practice.css">'
                '</head><body><main>' + body + footer + '</main>' + scripts + '</body></html>\n')
        (ROOT / name).write_text(text, encoding='utf-8')

    hub = ('<header><p class="eyebrow">Mathematics · Applications and interpretation SL</p>'
           '<h1>Mathematics practice hub</h1><p>Predict. Adjust. Model. Interpret.</p>'
           f'<p class="muted">Five topics · 39 syllabus sub-topics · {len(data)} hands-on explorers · {len(data)} numerical challenges</p>'
           '<p>Move sliders, edit data, simulate experiments and test models. Open a topic below. '
           'The challenges use fixed scenarios, so you can check your reasoning independently of the explorer settings.</p>'
           '<nav><a href="coverage.html">Browse all 39 syllabus sub-topics</a><a href="investigations.html">Investigations and reflection</a></nav></header><div class="cards">')
    for number, title in TOPICS.items():
        activities = {k: v for k, v in data.items() if v['topic'] == number}
        hub += (f'<a class="card" href="topic-{number}.html"><span class="eyebrow">Topic {number}</span>'
                f'<h2>{escape(title)}</h2><p>{len(activities)} explorers</p><p class="muted">'
                + ' · '.join(escape(v['title']) for v in activities.values()) + '</p></a>')
        body = (f'<header><a href="math-practice.html">← Mathematics hub</a><p class="eyebrow">AI SL · Topic {number}</p>'
                f'<h1>{escape(title)}</h1><a href="coverage.html#topic-{number}">Topic {number} syllabus checklist and guided tasks</a></header><nav aria-label="Activities">'
                + ''.join(f'<a href="#{key}">{escape(c["title"])}</a>' for key, c in activities.items()) + '</nav>'
                '<noscript><p>Enable JavaScript for the explorers and answer checks. Worked explanations remain readable.</p></noscript>')
        for key, c in activities.items():
            codes = [v['code'] for v in coverage if key in v['activities']]
            links = ' · '.join(f'<a href="coverage.html#sl-{code}">SL {code}</a>' for code in codes)
            body += (f'<section id="{key}" data-math="{key}"><p class="eyebrow">Hands-on explorer · {links}</p><h2>{escape(c["title"])}</h2>'
                     f'<p>{escape(c["intro"])}</p><div class="controls"></div><div class="graph"></div>'
                     '<p class="result" aria-live="polite"></p><div class="challenge"><h3>Try a fixed scenario</h3>'
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
    write('math-practice.html', 'Mathematics practice hub', hub + '</div>')
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
                     '<nav aria-label="Linked practice">' + ''.join(f'<a href="topic-{data[k]["topic"]}.html#{k}">{escape(data[k]["title"])}</a>' for k in c['activities'])
                     + f'</nav><p>{escape(c["task"])}</p><details><summary>Check your reasoning</summary><p>{escape(c["solution"])}</p></details>'
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
    print(f'Built mathematics hub and five topic pages with {len(data)} explorers.')


if __name__ == '__main__':
    build()
