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
                    for q in data.questions.values() if q.assessment_id == aid and eligible(q, level)}
        learners.append(LearnerOverview(sid, student.name, student.class_name, view.overall_percent,
                                       view.graded_count, dict(Counter(r.status for r in rows)),
                                       len(expected - {r.question_id for r in rows}), view.work_on))
    items = []
    for question in data.questions.values():
        if assessment_id and question.assessment_id != assessment_id:
            continue
        expected = {sid for (aid, sid), level in data.memberships.items() if aid == question.assessment_id
                    and sid in student_ids and eligible(question, level)}
        if not expected:
            continue
        rows = [r for r in data.question_results if r.question_id == question.id and r.student_id in expected]
        graded = [r for r in rows if r.status == 'graded']
        percent = 100 * sum(r.score for r in graded) / (len(graded) * question.marks) if graded else None
        items.append(ItemOverview(data.assessments[question.assessment_id].name, question.number,
                                 question.text, question.topic, percent, len(graded), len(expected),
                                 dict(Counter(r.status for r in rows)), len(expected) - len(rows)))
    items.sort(key=lambda q: (q.percent is None, q.percent if q.percent is not None else 0, q.assessment, q.number))
    return learners, items
