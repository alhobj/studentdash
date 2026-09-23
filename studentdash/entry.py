"""Persistent teacher-entered classes, adapted to the existing reporting model.

Each class is an independent, versioned document in a transactional local file.
Original workbooks are never modified. Summary results are derived on every read.
"""
from copy import deepcopy
from contextlib import closing
from datetime import date
import json
import math
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from .classification import DEFAULT_PROFILE, QuestionTag
from .models import Assessment, Question, QuestionResult, Result, Student, WorkbookData


class EntryError(ValueError):
    def __init__(self, message, cells=None):
        super().__init__(message)
        self.cells = cells or {}


def identifier():
    return uuid4().hex


def text(value, label, limit=1000, required=False):
    if not isinstance(value, str):
        raise EntryError(f'{label}: enter text.')
    value = value.strip()
    if len(value) > limit or (required and not value):
        raise EntryError(f'{label}: {"a value is required; " if required else ""}maximum {limit} characters.')
    return value


def roster_rows(raw):
    rows = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) > 2:
            raise EntryError('Paste one name per line, with an optional email in the second column. Omit headings.')
        rows.append(dict(id=identifier(), name=text(parts[0], 'Student name', 200, True),
                         email=text(parts[1] if len(parts) == 2 else '', 'Email', 200)))
    if not rows:
        raise EntryError('Enter at least one student.')
    return rows


def read_document(path):
    path = Path(path)
    if not path.is_file():
        raise EntryError('This class is no longer available. Select a class again.')
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT version, body FROM class_document WHERE id=1').fetchone()
    doc = json.loads(row[1])
    if doc.get('schema') != 1:
        raise EntryError('This class needs a newer version of Studentdash.')
    doc['version'] = row[0]
    return doc


class ClassStore:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()

    def path(self, key):
        if not re.fullmatch(r'[a-f0-9]{32}', key or ''):
            raise EntryError('Select a valid class.')
        return self.directory / (key + '.sdclass')

    def list(self):
        return sorted([read_document(p) for p in self.directory.glob('*.sdclass')],
                      key=lambda d: d['name'].casefold())

    def read(self, key):
        return read_document(self.path(key))

    def create(self, name, roster, profile=None):
        doc = dict(schema=1, id=identifier(), name=text(name, 'Class name', 200, True),
                   students=roster_rows(roster), assessments=[], profile=deepcopy(profile or DEFAULT_PROFILE))
        self.directory.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path(doc['id']))) as db, db:
            db.execute('CREATE TABLE class_document (id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER, body TEXT)')
            db.execute('INSERT INTO class_document VALUES (1, 1, ?)', (json.dumps(doc),))
        return self.read(doc['id'])

    def save(self, doc, version):
        with closing(sqlite3.connect(self.path(doc['id']), timeout=10)) as db, db:
            changed = db.execute('UPDATE class_document SET body=?, version=version+1 WHERE id=1 AND version=?',
                                 (json.dumps({k: v for k, v in doc.items() if k != 'version'}), version))
            if changed.rowcount != 1:
                raise EntryError('Another tab saved this class. Your changes were not saved. Copy your edits, then reload before retrying.')
        return self.read(doc['id'])

    def add_students(self, key, raw, version):
        doc = self.read(key)
        additions = roster_rows(raw)
        seen = {(s['name'].casefold(), s['email'].casefold()) for s in doc['students']}
        for student in additions:
            identity = student['name'].casefold(), student['email'].casefold()
            if identity in seen:
                raise EntryError(f"{student['name']} already appears in this roster. Use a distinguishing name or email for different students.")
            seen.add(identity)
        doc['students'].extend(additions)
        return self.save(doc, version)


def assessment(doc, aid):
    for item in doc['assessments']:
        if item['id'] == aid:
            return item
    raise EntryError('This assessment is no longer available.')


def save_assessment(store, key, aid, payload, version):
    doc = store.read(key)
    old = assessment(doc, aid) if aid else None
    if not isinstance(payload, dict):
        raise EntryError('The assessment could not be read. Reload and retry.')
    name = text(payload.get('name', ''), 'Assessment name', 200, True)
    try:
        day = date.fromisoformat(payload.get('date', '')).isoformat()
    except (ValueError, TypeError):
        raise EntryError('Choose a valid assessment date.') from None
    participants = payload.get('participants', [])
    known = {s['id'] for s in doc['students']}
    if not isinstance(participants, list) or not participants or any(not isinstance(s, str) or s not in known for s in participants):
        raise EntryError('Select at least one student from this class.')
    questions = payload.get('questions', [])
    if not isinstance(questions, list) or not 1 <= len(questions) <= 200:
        raise EntryError('Add between 1 and 200 questions.')
    old_questions = {q['id']: q for q in old['questions']} if old else {}
    cleaned, used, numbers = [], set(), set()
    for index, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            raise EntryError(f'Question {index} could not be read.')
        qid = q.get('id') or identifier()
        if not isinstance(qid, str) or (q.get('id') and qid not in old_questions) or qid in used:
            raise EntryError('Question list changed unexpectedly. Reload and retry.')
        used.add(qid)
        number = text(q.get('number', ''), f'Question {index} label', 40, True)
        if number.casefold() in numbers:
            raise EntryError(f'Question {number}: use a unique label.')
        numbers.add(number.casefold())
        try:
            maximum = float(q.get('marks', ''))
        except (TypeError, ValueError):
            maximum = 0
        if isinstance(q.get('marks'), bool) or not math.isfinite(maximum) or maximum <= 0:
            raise EntryError(f'Question {number}: maximum marks must be a positive number.')
        tags = q.get('tags', {})
        if not isinstance(tags, dict):
            raise EntryError(f'Question {number}: invalid classifications.')
        for category, values in tags.items():
            if not isinstance(values, list):
                raise EntryError(f'Question {number}: invalid classifications.')
            for value in values:
                try:
                    QuestionTag(qid, category, value, 'teacher', vocabulary=doc['profile']['categories'])
                except (ValueError, TypeError):
                    raise EntryError(f'Question {number}: choose classifications from the listed values.') from None
        cleaned.append(dict(id=qid, number=number, marks=maximum,
                            text=text(q.get('text', ''), f'Question {number} text', 10000),
                            curriculum=text(q.get('curriculum', ''), f'Question {number} curriculum mapping', 300),
                            tags={c: list(dict.fromkeys(v)) for c, v in tags.items() if v}))
    if not math.isfinite(sum(q['marks'] for q in cleaned)):
        raise EntryError('The assessment maximum is too large. Check the question marks.')
    scores = deepcopy(old['scores']) if old else {}
    # Do not silently delete evidence or detach it by removing a participant/question.
    for sid, row in scores.items():
        for qid, value in row.items():
            if value['status'] != 'pending' and (sid not in participants or qid not in used):
                raise EntryError('A student or question with recorded marks/statuses cannot be removed. Clear those entries to pending first if removal is intended.')
    scores = {sid: {qid: v for qid, v in row.items() if qid in used}
              for sid, row in scores.items() if sid in participants}
    for q in cleaned:
        for row in scores.values():
            v = row.get(q['id'], {})
            if v.get('score') is not None and v['score'] > q['marks']:
                raise EntryError(f"Question {q['number']}: the new maximum is below a saved score. Correct that score first.")
    item = dict(id=aid or identifier(), name=name, date=day,
                description=text(payload.get('description', ''), 'Description', 5000),
                participants=list(dict.fromkeys(participants)), questions=cleaned, scores=scores)
    if old:
        doc['assessments'][doc['assessments'].index(old)] = item
    else:
        doc['assessments'].append(item)
    store.save(doc, version)
    return item['id']


def parse_score(raw, maximum):
    if not isinstance(raw, (str, int, float)) or isinstance(raw, bool):
        raise ValueError('Enter a mark or A, E, M, P.')
    value = str(raw).strip().lower()
    aliases = {'': 'pending', 'a': 'absent', 'e': 'exempt', 'm': 'missing', 'p': 'pending'}
    status = aliases.get(value, value)
    if status in {'absent', 'exempt', 'missing', 'pending'}:
        return dict(status=status, score=None)
    try:
        mark = float(value.replace(',', '.'))
    except ValueError:
        raise ValueError('Enter a mark or A, E, M, P.') from None
    if not math.isfinite(mark) or not 0 <= mark <= maximum:
        raise ValueError(f'Enter a mark from 0 to {maximum:g}.')
    return dict(status='graded', score=mark)


def score_rows(doc, item):
    students = {s['id']: s for s in doc['students']}
    return [students[sid] for sid in item['participants']]


def save_scores(store, key, aid, rows, version):
    doc = store.read(key)
    item = assessment(doc, aid)
    students = score_rows(doc, item)
    if not isinstance(rows, list) or len(rows) != len(students) or any(not isinstance(r, list) or len(r) != len(item['questions']) for r in rows):
        raise EntryError('The score grid dimensions changed. Copy your entries and reload before retrying.')
    errors, scores = {}, {}
    for r, (student, values) in enumerate(zip(students, rows)):
        scores[student['id']] = {}
        for c, (q, value) in enumerate(zip(item['questions'], values)):
            try:
                scores[student['id']][q['id']] = parse_score(value, q['marks'])
            except ValueError as exc:
                errors[f'{r}:{c}'] = f"{student['name']}, question {q['number']}: {exc}"
    if errors:
        raise EntryError('Scores were not saved. Correct the highlighted cells.', errors)
    item['scores'] = scores
    store.save(doc, version)


def summary(item, sid):
    values = [(q, item['scores'].get(sid, {}).get(q['id'], dict(status='pending', score=None)))
              for q in item['questions']]
    states = {v['status'] for _, v in values}
    maximum = sum(q['marks'] for q, v in values if v['status'] != 'exempt')
    earned = sum(v['score'] for _, v in values if v['status'] == 'graded')
    if states <= {'graded', 'exempt'} and maximum:
        return earned, maximum, 'graded'
    if states == {'exempt'}:
        return None, 0, 'exempt'
    if states <= {'absent', 'exempt'}:
        return None, maximum, 'absent'
    if states <= {'missing', 'exempt'}:
        return None, maximum, 'missing'
    return None, maximum, 'pending'


def summary_label(item, sid):
    score, maximum, status = summary(item, sid)
    return f'{score:g}/{maximum:g}' if status == 'graded' else ('Incomplete' if status == 'pending' else status.capitalize())


def as_workbook(path):
    doc = read_document(path)
    data = WorkbookData(has_question_tables=True)
    data.question_authoritative = True
    for s in doc['students']:
        data.students[s['id']] = Student(s['id'], s['name'], s['email'], doc['name'])
    for a in doc['assessments']:
        aid = a['id']
        data.assessments[aid] = Assessment(aid, a['name'], date.fromisoformat(a['date']), '', sum(q['marks'] for q in a['questions']))
        for q in a['questions']:
            verb = ', '.join(q['tags'].get(doc['profile'].get('command_category'), []))
            data.questions[q['id']] = Question(q['id'], aid, q['number'], '', q['text'], q['marks'],
                                              q['curriculum'], '', '', verb)
            for category, tags in q['tags'].items():
                data.question_tags.extend(QuestionTag(q['id'], category, tag, 'teacher', vocabulary=doc['profile']['categories']) for tag in tags)
            if q['curriculum']:
                data.question_syllabus[q['id']] = dict(CurrentCode=q['curriculum'], LegacyCode='', Status='current', Source='teacher')
        for sid in a['participants']:
            data.memberships[aid, sid] = ''  # All selected students receive the entered question set.
            score, maximum, status = summary(a, sid)
            data.results.append(Result(aid, sid, score, maximum, status))
            for q in a['questions']:
                value = a['scores'].get(sid, {}).get(q['id'], dict(status='pending', score=None))
                data.question_results.append(QuestionResult(aid, q['id'], sid, value['score'], value['status']))
    return data
