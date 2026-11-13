"""Transport-independent exit-ticket validation and deterministic marking."""
from decimal import Decimal, InvalidOperation
import json
import math
import re

from .workspace import WorkspaceError


class TicketError(WorkspaceError):
    pass


TYPES = {'multiple_choice', 'multiple_select', 'true_false', 'number', 'short_answer', 'text'}


def text(value, label, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise TicketError(f'{label}: enter non-empty text, at most {limit} characters.')
    return value.strip()


def numeric(value, label, positive=False):
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise TicketError(f'{label}: use a finite JSON number.')
    if positive and not 0 < value <= 100:
        raise TicketError(f'{label}: marks must be greater than zero and at most 100.')
    return value


def boolean(value, label):
    if not isinstance(value, bool):
        raise TicketError(f'{label}: use true or false, without quotes.')
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TicketError(f'Duplicate JSON field: {key}.')
        result[key] = value
    return result


def parse_ticket(raw):
    if not isinstance(raw, str) or len(raw) > 64000:
        raise TicketError('Paste one JSON block of at most 64,000 characters.')
    raw = raw.strip()
    if raw.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n([\s\S]*)\n```', raw)
        if not match:
            raise TicketError('Paste just one JSON block, without commentary around it.')
        raw = match.group(1)
    try:
        source = json.loads(raw, object_pairs_hook=unique_object)
    except (ValueError, RecursionError) as exc:
        if isinstance(exc, TicketError):
            raise
        raise TicketError('The pasted block is not valid JSON. Check quotes, commas and brackets.') from None
    if not isinstance(source, dict):
        raise TicketError('The JSON must be one object containing title and questions.')
    extra = set(source) - {'title', 'subject', 'topic', 'subtopic', 'questions', 'allow_answer_review'}
    if extra:
        raise TicketError('Unsupported ticket fields: ' + ', '.join(sorted(extra)))
    ticket = {key: text(source.get(key), key, 200) for key in ('title', 'subject', 'topic', 'subtopic')}
    ticket['allow_answer_review'] = boolean(source.get('allow_answer_review', False), 'allow_answer_review')
    questions = source.get('questions')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 30:
        raise TicketError('questions must contain between 1 and 30 questions.')
    ticket['questions'] = []
    seen = set()
    for index, row in enumerate(questions, 1):
        label = f'Question {index}'
        if not isinstance(row, dict):
            raise TicketError(f'{label}: use an object.')
        kind = row.get('type')
        if not isinstance(kind, str) or kind not in TYPES:
            raise TicketError(f'{label}: unsupported type. Use {", ".join(sorted(TYPES))}.')
        allowed = {'id', 'type', 'question', 'marks', 'action_verb', 'manual_marking'}
        allowed |= {'multiple_choice': {'options', 'answer'}, 'multiple_select': {'options', 'answer'},
                    'true_false': {'answer'}, 'number': {'answer', 'tolerance'},
                    'short_answer': {'accepted_answers', 'case_sensitive'}, 'text': set()}[kind]
        if set(row) - allowed:
            raise TicketError(f'{label}: unsupported fields for {kind}: {", ".join(sorted(set(row) - allowed))}.')
        qid = row.get('id', f'q{index}')
        if not isinstance(qid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', qid):
            raise TicketError(f'{label}: id must use 1–80 letters, digits, underscores or hyphens.')
        if qid in seen:
            raise TicketError(f'{label}: duplicate question ID {qid}.')
        seen.add(qid)
        q = dict(id=qid, type=kind, question=text(row.get('question'), label),
                 marks=numeric(row.get('marks'), label, True), action_verb=text(row.get('action_verb'), label + ' action_verb', 80))
        default_manual = kind == 'text' or (kind == 'short_answer' and not row.get('accepted_answers'))
        manual = boolean(row.get('manual_marking', default_manual), label + ' manual_marking')
        if kind == 'text' and not manual:
            raise TicketError(f'{label}: text questions always require manual marking.')
        if kind not in {'text', 'short_answer'} and manual:
            raise TicketError(f'{label}: this question type uses deterministic automatic marking.')
        q['manual_marking'] = manual
        if kind in {'multiple_choice', 'multiple_select'}:
            options = row.get('options')
            if not isinstance(options, list) or not 2 <= len(options) <= 12:
                raise TicketError(f'{label}: supply 2–12 different options.')
            q['options'] = [text(v, label + ' option', 300) for v in options]
            if len(set(q['options'])) != len(q['options']):
                raise TicketError(f'{label}: options must be unique.')
            answer = row.get('answer')
            if kind == 'multiple_choice':
                if not isinstance(answer, str) or answer not in q['options']:
                    raise TicketError(f'{label}: answer must exactly match one option.')
            elif (not isinstance(answer, list) or not answer or any(not isinstance(a, str) or a not in q['options'] for a in answer)
                  or len(set(answer)) != len(answer)):
                raise TicketError(f'{label}: answer must be a non-empty list of distinct correct options.')
            q['answer'] = answer
        elif kind == 'true_false':
            q['answer'] = boolean(row.get('answer'), label + ' answer')
        elif kind == 'number':
            q['answer'] = numeric(row.get('answer'), label + ' answer')
            q['tolerance'] = numeric(row.get('tolerance', 0), label + ' tolerance')
            if q['tolerance'] < 0:
                raise TicketError(f'{label}: tolerance cannot be negative.')
        elif kind == 'short_answer':
            accepted = row.get('accepted_answers', [])
            if not isinstance(accepted, list) or len(accepted) > 20:
                raise TicketError(f'{label}: accepted_answers must be a list of at most 20 strings.')
            q['accepted_answers'] = [text(v, label + ' accepted answer', 300) for v in accepted]
            q['case_sensitive'] = boolean(row.get('case_sensitive', True), label + ' case_sensitive')
            if not manual and not accepted:
                raise TicketError(f'{label}: automatic short answers require accepted_answers.')
            if manual and accepted:
                raise TicketError(f'{label}: choose either accepted_answers or manual marking, not both.')
        ticket['questions'].append(q)
    return ticket


def public_question(q):
    """Never serialize the definition into a student page."""
    return {k: q[k] for k in ('id', 'type', 'question', 'marks', 'action_verb', 'options', 'manual_marking', 'case_sensitive', 'tolerance') if k in q}


def validate_answers(questions, values):
    if set(values) != {q['id'] for q in questions}:
        raise TicketError('Answer every question, and do not include unknown questions.')
    result = {}
    for index, q in enumerate(questions, 1):
        value = values[q['id']]
        kind = q['type']
        label = f'Question {index}'
        if kind == 'multiple_select':
            if (not isinstance(value, list) or not value or any(not isinstance(v, str) or v not in q['options'] for v in value)
                    or len(set(value)) != len(value)):
                raise TicketError(f'{label}: select one or more listed options without duplicates.')
        elif kind == 'true_false':
            if not isinstance(value, bool):
                raise TicketError(f'{label}: choose True or False.')
        elif kind == 'number':
            if not isinstance(value, str) or not value.strip() or len(value) > 80:
                raise TicketError(f'{label}: enter a number.')
            try:
                number = Decimal(value.strip())
                if not number.is_finite() or number.copy_abs() > Decimal('1e100'):
                    raise InvalidOperation
            except InvalidOperation:
                raise TicketError(f'{label}: enter a finite number without units.') from None
            value = value.strip()
        else:
            value = text(value, label, 4000 if kind == 'text' else 300)
            if kind == 'multiple_choice' and value not in q['options']:
                raise TicketError(f'{label}: choose a listed option.')
        result[q['id']] = value
    return result


def automatic_score(q, answer):
    if q['manual_marking']:
        return None
    kind = q['type']
    if kind == 'multiple_select':
        correct = set(answer) == set(q['answer'])
    elif kind == 'number':
        correct = abs(Decimal(answer) - Decimal(str(q['answer']))) <= Decimal(str(q['tolerance']))
    elif kind == 'short_answer':
        normalize = (lambda x: x.strip()) if q['case_sensitive'] else (lambda x: x.strip().casefold())
        correct = normalize(answer) in {normalize(v) for v in q['accepted_answers']}
    else:
        correct = answer == q['answer']
    return q['marks'] if correct else 0
