"""Build explicit student-only presentation records; never serialize a workbook."""
from dataclasses import dataclass

from .examples import PracticeQuestion, practice_questions
from .models import WorkbookData


@dataclass(frozen=True)
class AssessmentView:
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
    questions: list[PracticeQuestion]


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


def suggested_grade(percent, boundaries):
    return max(b.grade for b in boundaries if percent >= b.percent)


def categories(questions, attribute):
    grouped = {}
    for question in questions:
        grouped.setdefault(getattr(question, attribute), []).append(question)
    result = []
    for name, rows in grouped.items():
        score, maximum = sum(q.score for q in rows), sum(q.marks for q in rows)
        result.append(CategoryView(name, 100 * score / maximum, score, maximum, rows))
    return result


def build_dashboard(data: WorkbookData, student_id: str, include_examples=True):
    if student_id not in data.students:
        raise KeyError(f'Unknown student ID {student_id}')
    history = []
    own_results = [r for r in data.results if r.student_id == student_id]
    own_results.sort(key=lambda r: (data.assessments[r.assessment_id].date, r.assessment_id))
    for result in own_results:
        assessment = data.assessments[result.assessment_id]
        percent = 100 * result.score / result.max_score if result.status == 'graded' else None
        history.append(AssessmentView(assessment.name, assessment.date.isoformat(), result.score,
                       result.max_score, result.status, percent,
                       suggested_grade(percent, data.boundaries) if percent is not None else None))
    graded = [r for r in own_results if r.status == 'graded']
    score = sum(r.score for r in graded)
    maximum = sum(r.max_score for r in graded)
    practice = practice_questions() if include_examples else []
    verbs = categories(practice, 'verb')
    return StudentDashboard(
        'student' + student_id, history, 100 * score / maximum if maximum else None,
        score, maximum, len(graded), categories(practice, 'topic'), categories(practice, 'subtopic'),
        verbs, practice, [c.name for c in verbs if len(c.questions) >= 2 and c.percent >= 75],
        [c.name for c in verbs if len(c.questions) >= 2 and c.percent < 50],
    )
