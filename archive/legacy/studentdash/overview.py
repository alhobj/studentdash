"""Teacher-only cohort views. Never pass these records to student templates."""
from collections import Counter
from dataclasses import dataclass

from .analytics import build_dashboard
from .question_data import eligible


@dataclass(frozen=True)
class LearnerOverview:
    id: str
    name: str
    class_name: str
    percent: float | None
    graded: int
    statuses: dict[str, int]
    unrecorded: int
    practice: list[str]
    result_label: str = ''
    confidence: tuple = ()


@dataclass(frozen=True)
class ItemOverview:
    assessment: str
    number: str
    text: str
    topic: str
    percent: float | None
    graded: int
    expected: int
    statuses: dict[str, int]
    unrecorded: int
    question_id: str = ''


def build_overview(data, assessment_id=None, class_name=None):
    assessment_id = assessment_id or None
    student_ids = {sid for sid, s in data.students.items() if not class_name or s.class_name == class_name}
    if assessment_id:
        members = {sid for aid, sid in data.memberships if aid == assessment_id}
        members.update(r.student_id for r in data.results if r.assessment_id == assessment_id)
        student_ids &= members
    learners = []
    for sid in sorted(student_ids):
        student = data.students[sid]
        view = build_dashboard(data, sid, False, assessment_id)
        rows = [r for r in data.question_results if r.student_id == sid
                and (not assessment_id or r.assessment_id == assessment_id)]
        expected = {q.id for (aid, member), level in data.memberships.items() if member == sid
                    and (not assessment_id or aid == assessment_id)
                    for q in data.questions.values() if q.assessment_id == aid and (data.question_authoritative or eligible(q, level))}
        result_label = ''
        if data.question_authoritative and len(view.history) == 1:
            result = view.history[0]
            result_label = (f'{result.score:g}/{result.maximum:g}' if result.status == 'graded' else
                            'Incomplete' if result.status == 'pending' else result.status.capitalize())
        learners.append(LearnerOverview(sid, student.name, student.class_name, view.overall_percent,
                                       view.graded_count, dict(Counter(r.status for r in rows)),
                                       len(expected - {r.question_id for r in rows}), view.work_on, result_label, tuple((a.name, data.assessment_confidence.get(a.id, {}).get(sid)) for a in data.assessments.values() if (not assessment_id or a.id == assessment_id) and (a.id, sid) in data.memberships)))
    items = []
    for question in data.questions.values():
        if assessment_id and question.assessment_id != assessment_id:
            continue
        expected = {sid for (aid, sid), level in data.memberships.items() if aid == question.assessment_id
                    and sid in student_ids and (data.question_authoritative or eligible(question, level))}
        if not expected:
            continue
        rows = [r for r in data.question_results if r.question_id == question.id and r.student_id in expected]
        graded = [r for r in rows if r.status == 'graded']
        percent = 100 * sum(r.score for r in graded) / (len(graded) * question.marks) if graded else None
        items.append(ItemOverview(data.assessments[question.assessment_id].name, question.number,
                                 question.text, question.topic, percent, len(graded), len(expected),
                                 dict(Counter(r.status for r in rows)), len(expected) - len(rows), question.id))
    items.sort(key=lambda q: (q.percent is None, q.percent if q.percent is not None else 0, q.assessment, q.number))
    return learners, items


def curriculum_groups(data, items):
    """Group evidence by explicit nodes; each question occurs once per node.

    No group totals are summed: shared links never inflate cohort totals.
    Ancestor labels follow captured parent references, never code syntax.
    """
    from .curriculum import node_index
    nodes = node_index(data.curriculum or {})
    groups = {}
    for item in items:
        links = list(dict.fromkeys(k for k in data.question_curriculum.get(item.question_id, []) if k in nodes))
        for key in links or [None]:
            if key not in groups:
                path, seen, current = [], set(), key
                while current in nodes and current not in seen:
                    seen.add(current)
                    path.insert(0, nodes[current]['label'])
                    current = nodes[current].get('parent')
                groups[key] = dict(label=nodes[key]['label'] if key else 'Unclassified',
                                   path=' / '.join(path[:-1]), items=[])
            groups[key]['items'].append(item)
    return sorted(groups.values(), key=lambda g: (g['label'] == 'Unclassified', g['path'], g['label']))
