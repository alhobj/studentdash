"""Learner-scoped projection of saved question classifications; no node inference."""
from copy import deepcopy


def curriculum_labels(doc, references):
    nodes = {node['id']: node for node in (doc['profile'].get('curriculum') or {}).get('nodes', [])}
    return [dict(id=key, code=nodes.get(key, {}).get('code', ''),
                 label=nodes.get(key, {}).get('label', key)) for key in references]


def category_labels(doc):
    options = doc['profile'].get('category_options', {})
    return {key: options.get(key, {}).get('label', key) for key in doc['profile']['categories']}


def learner_classifications(doc, data, student_id):
    if student_id not in data.students:
        raise ValueError('Choose an existing student.')
    results = {(r.assessment_id, r.question_id): r for r in data.question_results if r.student_id == student_id}
    rows = []
    for assessment in doc['assessments']:
        for question in assessment['questions']:
            result = results.get((assessment['id'], question['id']))
            if result is None:
                continue
            links = list(question.get('curriculum_nodes', []))
            rows.append(dict(assessmentId=assessment['id'], assessmentTitle=assessment['name'],
                             questionId=question['id'], questionNumber=question['number'],
                             score=result.score if result.status == 'graded' else None,
                             maxScore=question['marks'], status=result.status,
                             scope=question.get('scope', ''), tags=deepcopy(question.get('tags', {})),
                             curriculumNodes=links, curriculumLabels=curriculum_labels(doc, links),
                             curriculumReview=deepcopy(question.get('curriculum_review', {}))))
    curriculum = doc['profile'].get('curriculum') or {}
    return dict(schemaVersion='1.0', learnerId=student_id, categoryLabels=category_labels(doc),
                curriculum=dict(id=curriculum.get('id'), version=curriculum.get('version')), questions=rows)
