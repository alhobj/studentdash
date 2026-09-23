"""Build explicit student-only presentation records; never serialize a workbook."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from .examples import PracticeQuestion, practice_questions
from .models import WorkbookData, Resource


@dataclass(frozen=True)
class QuestionView:
    number: str
    text: str
    topic: str
    subtopic: str
    verb: str
    score: float | None
    marks: float
    status: str
    assessment: str


@dataclass(frozen=True)
class TicketView:
    date: str
    assessment: str
    prompt: str
    response: str
    feedback: str


@dataclass(frozen=True)
class RevisionTask:
    key: str
    assessment: str
    number: str
    text: str
    topic: str
    score: float
    marks: float
    resources: list[Resource]


@dataclass(frozen=True)
class FeedbackView:
    assessment: str
    comment: str
    tasks: list[str]


@dataclass(frozen=True)
class AttemptView:
    assessment: str
    number: str
    text: str
    date: str
    original: float
    score: float
    maximum: float
    change: float
    note: str


@dataclass(frozen=True)
class AssessmentView:
    id: str
    name: str
    date: str
    score: float | None
    maximum: float
    status: str
    percent: float | None
    grade: int | None


@dataclass(frozen=True)
class CategoryView:
    name: str
    percent: float
    score: float
    maximum: float
    questions: list[PracticeQuestion | QuestionView]


@dataclass(frozen=True)
class StudentDashboard:
    anonymous_id: str
    history: list[AssessmentView]
    overall_percent: float | None
    total_score: float
    total_possible: float
    graded_count: int
    topics: list[CategoryView]
    subtopics: list[CategoryView]
    verbs: list[CategoryView]
    practice: list[PracticeQuestion]
    strengths: list[str]
    work_on: list[str]
    questions: list[QuestionView]
    resources: list[Resource]
    tickets: list[TicketView]
    generated_at: str
    using_examples: bool
    assessment_options: list[tuple[str, str]]
    selected_assessment: str
    revision: list[RevisionTask]
    feedback: list[FeedbackView]
    attempts: list[AttemptView]
    question_authoritative: bool = False


def suggested_grade(percent, boundaries):
    return max((b.grade for b in boundaries if percent >= b.percent), default=None)


def categories(questions, attribute):
    grouped = {}
    for question in questions:
        if not getattr(question, attribute):
            continue
        grouped.setdefault(getattr(question, attribute), []).append(question)
    result = []
    for name, rows in grouped.items():
        score, maximum = sum(q.score for q in rows), sum(q.marks for q in rows)
        result.append(CategoryView(name, 100 * score / maximum, score, maximum, rows))
    return result


def build_dashboard(data: WorkbookData, student_id: str, include_examples=True, assessment_id=None, workspace_state=None):
    if student_id not in data.students:
        raise KeyError(f'Unknown student ID {student_id}')
    history = []
    own_results = [r for r in data.results if r.student_id == student_id
                   and (assessment_id is None or r.assessment_id == assessment_id)]
    own_results.sort(key=lambda r: (data.assessments[r.assessment_id].date, r.assessment_id))
    for result in own_results:
        assessment = data.assessments[result.assessment_id]
        percent = 100 * result.score / result.max_score if result.status == 'graded' else None
        history.append(AssessmentView(assessment.id, assessment.name, assessment.date.isoformat(), result.score,
                       result.max_score, result.status, percent,
                       suggested_grade(percent, data.assessment_boundaries.get(assessment.id, data.boundaries)) if percent is not None else None))
    graded = [r for r in own_results if r.status == 'graded']
    score = sum(r.score for r in graded)
    maximum = sum(r.max_score for r in graded)
    questions = []
    for result in data.question_results:
        if result.student_id != student_id or (assessment_id and result.assessment_id != assessment_id):
            continue
        q = data.questions[result.question_id]
        questions.append(QuestionView(q.number, q.text, q.topic, q.subtopic, q.action_verb,
                                      result.score, q.marks, result.status, data.assessments[q.assessment_id].name))
    practice = practice_questions() if include_examples and not data.has_question_tables else []
    evidence = [q for q in questions if q.status == 'graded'] or practice
    verbs = categories(evidence, 'verb')
    topics = {q.topic for q in questions}
    tickets = [TicketView(t.date, data.assessments[t.assessment_id].name, t.prompt, t.response, t.feedback)
               for t in data.exit_tickets if t.student_id == student_id
               and (assessment_id is None or t.assessment_id == assessment_id)]
    own_assessments = {r.assessment_id for r in data.results if r.student_id == student_id}
    own_assessments.update(aid for aid, sid in data.memberships if sid == student_id)
    candidates = [r for r in data.question_results if r.student_id == student_id and r.status == 'graded'
                  and (not assessment_id or r.assessment_id == assessment_id)
                  and r.score < data.questions[r.question_id].marks]
    candidates.sort(key=lambda r: (-(data.questions[r.question_id].marks - r.score), r.assessment_id, r.question_id))
    revision = []
    for result in candidates[:3]:
        q = data.questions[result.question_id]
        # A changed task or mark starts a fresh checklist item; unrelated regeneration preserves it.
        key = sha256(repr((student_id, q.id, q.text, result.score, q.marks)).encode()).hexdigest()[:24]
        revision.append(RevisionTask(key, data.assessments[q.assessment_id].name, q.number, q.text,
                                     q.topic, result.score, q.marks,
                                     [r for r in data.resources if r.topic == q.topic]))
    state = workspace_state or {'feedback': [], 'attempts': []}
    feedback = [FeedbackView(data.assessments[f['assessment']].name, f['comment'], f['tasks'])
                for f in state['feedback'] if f['student'] == student_id and f['assessment'] in own_assessments
                and (not assessment_id or f['assessment'] == assessment_id) and (f['comment'] or f['tasks'])]
    attempts = []
    for attempt in [*data.revision_attempts, *state['attempts']]:
        if attempt['student'] != student_id or attempt['assessment'] not in own_assessments:
            continue
        q = data.questions.get(attempt['question'])
        if not q or q.assessment_id != attempt['assessment'] or (assessment_id and q.assessment_id != assessment_id):
            continue
        attempts.append(AttemptView(data.assessments[q.assessment_id].name, q.number, q.text, attempt['day'],
                                    attempt['original'], attempt['score'], attempt['maximum'],
                                    attempt['score'] - attempt['original'], attempt['note']))
    attempts.sort(key=lambda a: a.date, reverse=True)
    return StudentDashboard(
        'student' + student_id, history, 100 * score / maximum if maximum else None,
        score, maximum, len(graded), categories(evidence, 'topic'), categories(evidence, 'subtopic'),
        verbs, practice, [c.name for c in verbs if len(c.questions) >= 2 and c.percent >= 75],
        [c.name for c in verbs if len(c.questions) >= 2 and c.percent < 50],
        questions, [r for r in data.resources if r.topic in topics], sorted(tickets, key=lambda t: t.date, reverse=True),
        datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), bool(practice),
        [(aid, data.assessments[aid].name) for aid in sorted(own_assessments)], assessment_id or '',
        revision, feedback, attempts, data.question_authoritative,
    )
