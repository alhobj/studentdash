"""Learner-scoped evidence, explicit hierarchy rollups, and weighted marks."""
from .classification_import import node_index
from .storage import ValidationError


def eligible(doc, student, question):
    level = student.get('level') or doc.get('default_level', '')
    scope = question.get('classification', {}).get('level', '')
    rules = doc['profile'].get('level_eligibility', {})
    return not level or not scope or level not in rules or scope in rules[level]


def summary(evidence, boundaries):
    graded = [(q, r) for q, r in evidence if r['status'] == 'graded']
    score = sum(r['score'] for q, r in graded)
    maximum = sum(q['marks'] for q, r in graded)
    states = {r['status'] for _, r in evidence}
    complete = bool(evidence) and states <= {'graded', 'exempt'} and bool(graded)
    status = 'graded' if complete else (next(iter(states)) if len(states) == 1 else 'incomplete')
    percent = 100 * score / maximum if complete and maximum else None
    grade = max((b['grade'] for b in boundaries if percent is not None and percent >= b['percent']), default=None)
    return dict(score=score, maximum=maximum, percent=percent, grade=grade,
                assessment_maximum=sum(q['marks'] for q, r in evidence if r['status'] != 'exempt'),
                status=status if evidence else 'no applicable questions', graded=len(graded),
                pending=sum(r['status'] == 'pending' for _, r in evidence),
                missing=sum(r['status'] == 'missing' for _, r in evidence),
                absent=sum(r['status'] == 'absent' for _, r in evidence),
                exempt=sum(r['status'] == 'exempt' for _, r in evidence))


def classification_status(assessment, profile):
    questions = [q for q in assessment['questions'].values() if q.get('active', True)]
    classified = sum(bool(q.get('classification', {}).get('nodes') or
                          any(q.get('classification', {}).get('tags', {}).values()) or
                          q.get('classification', {}).get('topic')) for q in questions)
    full = sum(bool(q.get('classification', {}).get('nodes')) and
               all(q.get('classification', {}).get('tags', {}).get(c) for c in profile['categories']) for q in questions)
    label = 'Missing classifications' if not classified else ('Complete' if full == len(questions) else 'Partial classifications')
    return dict(label=label, classified=classified, total=len(questions))


def dashboard(doc, sid):
    if sid not in doc['students']:
        raise ValidationError('Unknown StudentID.')
    student = doc['students'][sid]
    index = node_index(doc['curriculum'])
    buckets = {}
    unknown = {c: 0 for c in doc['profile']['categories']}
    unknown.update(Syllabus=0, Topic=0, Subtopic=0)
    history, question_rows = [], []
    for aid, a in sorted(doc['assessments'].items()):
        if not a.get('active', True) or sid not in a['results']:
            continue
        evidence = []
        for qid, q in a['questions'].items():
            if not q.get('active', True) or not eligible(doc, student, q):
                continue
            r = a['results'][sid].get(qid, dict(status='pending', score=None))
            c = q.get('classification', {})
            evidence.append((q, r))
            question_rows.append(dict(assessment=aid, question=qid, marks=q['marks'], result=r,
                                      classification=c))
            scopes = set()
            for category, values in c.get('tags', {}).items():
                scopes.update((category, value) for value in values)
            for category in doc['profile']['categories']:
                if not c.get('tags', {}).get(category):
                    unknown[category] += 1
            unknown['Syllabus'] += not bool(c.get('nodes'))
            unknown['Topic'] += not bool(c.get('topic'))
            unknown['Subtopic'] += not bool(c.get('subtopic'))
            if c.get('topic'):
                scopes.add(('Topic', c['topic']))
                if c.get('subtopic'):
                    scopes.add(('Subtopic', (c['topic'], c['subtopic'])))
            visited = set()
            for nid in c.get('nodes', []):
                while nid and nid not in visited:
                    visited.add(nid)
                    node = index[nid]
                    scopes.add(('Syllabus', nid))
                    nid = node.get('parent')
            # A question contributes once per tag/node even with multiple descendant mappings.
            for category, tag in scopes:
                label = ((index[tag].get('code') + ' · ' if index[tag].get('code') else '') + index[tag]['label']) if category == 'Syllabus' else (' / '.join(tag) if category == 'Subtopic' else tag)
                bucket = buckets.setdefault((category, tag), dict(category=category, tag=label, score=0., maximum=0., questions=0, ungraded=0))
                if r['status'] == 'graded':
                    bucket['score'] += r['score']
                    bucket['maximum'] += q['marks']
                    bucket['questions'] += 1
                else:
                    bucket['ungraded'] += 1
        history.append(dict(id=aid, name=a['name'], date=a['date'], **summary(evidence, doc['boundaries']),
                            classification=classification_status(a, doc['profile'])))
    groups = {}
    for bucket in buckets.values():
        percent = 100 * bucket['score'] / bucket['maximum'] if bucket['maximum'] else None
        pattern = 'Insufficient evidence' if bucket['questions'] < 2 else (
            'Low performance' if percent < 50 else ('Strength' if percent >= 75 else 'Developing'))
        bucket.update(percent=percent, pattern=pattern)
        groups.setdefault(bucket['category'], []).append(bucket)
    for category in groups:
        groups[category].sort(key=lambda b: b['tag'])
    for category in doc['profile']['categories']:
        groups.setdefault(category, [])
    for category in ('Syllabus', 'Topic', 'Subtopic'):
        groups.setdefault(category, [])
    return dict(id=sid, name=student['name'], course=doc['id'], assessments=history,
                groups=groups, unknown=unknown, questions=question_rows,
                updated=doc.get('updated', ''))
