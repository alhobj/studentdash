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


@dataclass
class WorkbookData:
    students: dict[str, Student] = field(default_factory=dict)
    assessments: dict[str, Assessment] = field(default_factory=dict)
    questions: dict[str, Question] = field(default_factory=dict)
    results: list[Result] = field(default_factory=list)
    boundaries: list[GradeBoundary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
