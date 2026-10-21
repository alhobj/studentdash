"""Validated, portable editorial changes to a profile's MCQ bank."""
import json

FIELDS = {'prompt', 'options', 'answer', 'working', 'feedback', 'flag', 'notes'}


def apply_reviews(root, catalog):
    path = root / 'mcq-review.json'
    if not path.exists():
        return
    raw = json.loads(path.read_text(encoding='utf-8'))
    if raw.get('schema') != 1 or raw.get('profile') != root.name or not isinstance(raw.get('changes'), dict):
        raise ValueError('Invalid MCQ review file or profile.')
    index = {q['id']: q for q in catalog}
    for key, patch in raw['changes'].items():
        if key not in index or not isinstance(patch, dict) or set(patch) != FIELDS:
            raise ValueError('Unknown question or invalid editorial fields.')
        if any(not isinstance(patch[k], str) or len(patch[k]) > 10000 for k in ('prompt', 'working', 'flag', 'notes')):
            raise ValueError('Invalid editorial text.')
        if not patch['prompt'].strip() or not patch['working'].strip() or patch['flag'] not in ('unreviewed', 'reviewed', 'needs correction', 'too repetitive'):
            raise ValueError('Missing prompt, explanation or invalid review flag.')
        if not isinstance(patch['options'], list) or len(patch['options']) != 4 or any(not isinstance(x, str) or not x.strip() or len(x)>10000 for x in patch['options']) or len(set(patch['options'])) != 4:
            raise ValueError('Expected four distinct options.')
        if patch['answer'] not in ('A','B','C','D') or not isinstance(patch['feedback'], dict) or set(patch['feedback']) != set('ABCD') or any(not isinstance(x,str) or not x.strip() or len(x)>10000 for x in patch['feedback'].values()):
            raise ValueError('Invalid answer or option feedback.')
        index[key].update({**patch, 'answer':[patch['answer']]})


def option_feedback(option, correct, explanation):
    """Explain the chosen value without claiming to know the student's reasoning."""
    if option == correct:
        return explanation
    method = explanation.split(' The result is ')[0]
    try:
        chosen, target = float(option), float(correct)
        if chosen * target < 0:
            reason = 'This has the wrong sign. Check the direction, sign convention, or subtraction order.'
        elif target and abs(abs(chosen / target) - 10) < .0001:
            reason = 'This is ten times the required magnitude. Check powers of ten and unit conversions.'
        elif target and abs(abs(chosen / target) - .1) < .0001:
            reason = 'This is one tenth of the required magnitude. Check powers of ten and unit conversions.'
        else:
            reason = 'This value is too high.' if chosen > target else 'This value is too low.'
        return f'For {option}: {reason} Next step: {method}'
    except ValueError:
        return f'“{option}” does not fit this question. Compare it with this principle: {method}'
