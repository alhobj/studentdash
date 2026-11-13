"""Additive assessment types and non-mutating reporting filters."""
from copy import deepcopy
TYPES = {'assessment': 'Assessment', 'exit_ticket': 'Exit ticket'}

def filtered(data, kind=''):
    if not kind:
        return data
    if kind not in TYPES:
        raise ValueError('Choose a configured assessment type.')
    result = deepcopy(data)
    result.assessments = {k: a for k, a in data.assessments.items() if a.assessment_type == kind}
    result.questions = {k: q for k, q in data.questions.items() if q.assessment_id in result.assessments}
    result.results = [r for r in data.results if r.assessment_id in result.assessments]
    result.question_results = [r for r in data.question_results if r.assessment_id in result.assessments]
    result.memberships = {k: v for k, v in data.memberships.items() if k[0] in result.assessments}
    result.exit_tickets = [t for t in data.exit_tickets if t.assessment_id in result.assessments]
    result.question_tags = [t for t in data.question_tags if t.question_id in result.questions]
    result.assessment_confidence = {k: v for k, v in data.assessment_confidence.items() if k in result.assessments}
    result.question_curriculum = {k: v for k, v in data.question_curriculum.items() if k in result.questions}
    return result
