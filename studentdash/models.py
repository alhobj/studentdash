from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Student:
    id: str
    name: str
    email: str
    class_name: str


@dataclass(frozen=True)
class Assessment:
    id: str
    name: str
    date: date
    subject: str
    marks: float


@dataclass(frozen=True)
class Question:
    id: str
    assessment_id: str
    number: str
    level: str
    text: str
    marks: float | None
    topic: str
    subtopic: str
    question_type: str
    action_verb: str


@dataclass(frozen=True)
class Result:
    assessment_id: str
    student_id: str
    score: float | None
    max_score: float
    status: str


@dataclass(frozen=True)
class GradeBoundary:
    grade: int
    percent: float


@dataclass(frozen=True)
class QuestionResult:
    assessment_id: str
    question_id: str
    student_id: str
    score: float | None
    status: str


@dataclass(frozen=True)
class Resource:
    id: str
    topic: str
    title: str
    content: str


@dataclass(frozen=True)
class ExitTicket:
    id: str
    student_id: str
    assessment_id: str
    date: str
    prompt: str
    response: str
    feedback: str


@dataclass
class WorkbookData:
    students: dict[str, Student] = field(default_factory=dict)
    assessments: dict[str, Assessment] = field(default_factory=dict)
    questions: dict[str, Question] = field(default_factory=dict)
    results: list[Result] = field(default_factory=list)
    boundaries: list[GradeBoundary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    question_results: list[QuestionResult] = field(default_factory=list)
    memberships: dict[tuple[str, str], str] = field(default_factory=dict)
    assessment_boundaries: dict[str, list[GradeBoundary]] = field(default_factory=dict)
    resources: list[Resource] = field(default_factory=list)
    exit_tickets: list[ExitTicket] = field(default_factory=list)
    has_question_tables: bool = False
    revision_attempts: list[dict] = field(default_factory=list)
