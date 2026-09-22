"""Fictional practice only: never used to fill gaps in real assessment totals."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PracticeQuestion:
    number: str
    text: str
    topic: str
    subtopic: str
    verb: str
    score: float
    marks: float


def practice_questions():
    return [
        PracticeQuestion('E1', 'Explain why an atom has no overall charge.', 'Atomic structure', 'Particles', 'Explain', 1, 3),
        PracticeQuestion('E2', 'Explain the meaning of isotopes.', 'Atomic structure', 'Isotopes', 'Explain', 1, 3),
        PracticeQuestion('E3', 'Calculate the amount of substance in 18 g of water.', 'Stoichiometry', 'Amount of substance', 'Calculate', 3, 3),
        PracticeQuestion('E4', 'Calculate the mass of 0.5 mol of carbon dioxide.', 'Stoichiometry', 'Amount of substance', 'Calculate', 2, 3),
    ]
