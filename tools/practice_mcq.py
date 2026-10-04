"""Publish the original authored workbook extension with its deterministic A-D order."""
from collections import Counter
from html import escape
import json
import random
from mcq_math import math_questions
from mcq_chemistry import chemistry_questions

from extend_structure_mcq import authored_questions


def build_mcq(root, subject='chemistry'):
    questions = authored_questions() if subject == 'chemistry' else []
    extra = chemistry_questions() if subject == 'chemistry' else math_questions()
    for code, rows in extra.items():
        rng = random.Random(f'{subject}:{code}:mcq-v1')
        positions = list(range(4)) * 5
        rng.shuffle(positions)
        for index, (row, position) in enumerate(zip(rows, positions), 1):
            options = list(row['wrong'])
            rng.shuffle(options)
            options.insert(position, row['correct'])
            questions.append(dict(id=f'MCQ_{code.replace(".", "_")}_{index:03}', section=code,
                                  prompt=row['prompt'], options=options, correct=row['correct'],
                                  answer='ABCD'[position], explanation=row['explanation']))
    counts = Counter(q['section'] for q in questions)
    if any(count != 20 for count in counts.values()):
        raise ValueError('Each section must contain 20 questions.')
    catalog = []
    for q in questions:
        if q['options']['ABCD'.index(q['answer'])] != q['correct']:
            raise ValueError('Authored answer and letter disagree.')
        catalog.append(dict(id=root.name + ':mcq:' + q['id'], source_id=q['id'], topic=q['section'],
                            title='Multiple-choice practice', kind='mcq', prompt=q['prompt'], options=q['options'],
                            answer=[q['answer']], hint='Identify the relevant relationship or definition, work out your answer, then compare the four options.',
                            working=q['explanation'],
                            path=('mcq-' if subject == 'math' else '') + q['section'].lower().replace('.', '-') + '.html#' + q['id']))
    (root / 'authored-mcq.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return catalog


def render_mcq(questions, code):
    rows = [q for q in questions if q['topic'] == code]
    if not rows:
        return ''
    html = ('<section id="authored-mcq"><h2>20 multiple-choice questions</h2>'
            '<p>Click A, B, C or D for immediate feedback. You can change your answer or open the explanation. '
            'These independently authored questions include related examples for repeated practice.</p>'
            '<noscript><p>Enable JavaScript for answer buttons, or open the worked explanations below.</p></noscript>')
    for number, q in enumerate(rows, 1):
        correct = q['answer'][0]
        html += (f'<article class="authored-mcq-card" id="{escape(q["source_id"])}" data-authored-mcq="{escape(q["id"])}" data-correct="{correct}">'
                 f'<h3>Question {number}</h3><p class="mcq-prompt">{escape(q["prompt"])}</p>'
                 f'<div class="mcq-options" role="group" aria-label="Answers for question {number}">')
        for letter, option in zip('ABCD', q['options']):
            html += (f'<button type="button" data-choice="{letter}" aria-pressed="false" aria-describedby="{q["source_id"]}-feedback">'
                     f'<strong>{letter}.</strong> {escape(option)}</button>')
        html += (f'</div><p class="mcq-feedback feedback" role="status" id="{q["source_id"]}-feedback"></p>'
                 f'<details class="mcq-explanation"><summary>Show the correct answer and explanation</summary>'
                 f'<p>Correct answer: {correct}. {escape(q["options"]["ABCD".index(correct)])}</p>'
                 f'<p class="mcq-working">{escape(q["working"])}</p></details>'
                 '<button type="button" class="mcq-retry">Retry independently</button></article>')
    return html + '</section>'
