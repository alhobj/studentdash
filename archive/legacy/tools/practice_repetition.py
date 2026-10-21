"""Render short, authored sets for practising the same method repeatedly."""
import json
import math
from html import escape
from practice_skills import tag_question,render_skills


def load_repetition(root, foundations):
    banks = json.loads((root / 'repetition.json').read_text(encoding='utf-8'))
    expected = {c.get('code', c.get('id')) for group in foundations.values() for c in group}
    assert set(banks) == expected, 'Every foundation lesson needs a repetition set'
    for bank in banks.values():
        assert len(bank['questions']) >= 4 and bank['focus']
        assert len({q['prompt'] for q in bank['questions']}) == len(bank['questions'])
        for q in bank['questions']:
            tag_question(root,q)
            q['skill_html']=render_skills(root,q['skills'])
            assert q['prompt'] and q['hint'] and q['working']
            answer = q['answer']
            assert (isinstance(answer, list) and answer and all(isinstance(a, str) and a for a in answer)
                    or isinstance(answer, (int, float)) and math.isfinite(answer))
    return banks


def render_repetition(bank, key):
    first = bank['questions'][0]
    count = len(bank['questions'])
    field = key + '-similar-answer'
    payload = escape(json.dumps(bank, ensure_ascii=False), quote=True)
    kind = 'text' if isinstance(first['answer'], list) else 'number'
    return (f'<div class="similar-practice" data-similar="{payload}"><h3>Practise more like this</h3>'
            f'<p>{escape(bank["focus"])}</p><p>{count} closely matched questions. Keep using the same method. '
            'There is no timer or score; you can repeat the set.</p>'
            f'<p class="similar-position" aria-live="polite">Question 1 of {count}</p>'
            f'<form class="similar-form" novalidate><label for="{field}">{escape(first["prompt"])}</label>'
            f'<input id="{field}" type="{kind}" step="any" aria-describedby="{field}-feedback">'
            '<button type="submit" class="similar-check" hidden>Check answer</button>'
            f'<p class="similar-feedback feedback" id="{field}-feedback" role="status"></p></form>'
            f'<details class="similar-hint"><summary>Give me a hint</summary><p>{escape(first["hint"])}</p></details>'
            f'<details class="similar-working"><summary>Show the worked answer</summary><p>{escape(first["working"])}</p></details>'
            '<div class="similar-controls" hidden><button type="button" class="similar-previous" disabled>Previous question</button>'
            '<button type="button" class="similar-next">Another like this</button></div>'
            f'<details class="similar-worksheet"><summary>Read or print all {count} questions and solutions</summary>'
            + ''.join(f'<h4>Question {i}</h4>{q.get("skill_html", "")}<p>{escape(q["prompt"])}</p><details><summary>Worked answer</summary>'
                      f'<p>{escape(q["working"])}</p></details>' for i,q in enumerate(bank['questions'],1))
            + '</details><noscript><p>Enable JavaScript to switch questions and check answers, or use the full question list above.</p></noscript></div>')
