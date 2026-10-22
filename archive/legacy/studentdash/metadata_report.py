"""Learner-only reporting that needs marks and classifications, never question text."""
from .classification import performance
from .curriculum import evidence_by_node


def evidence(data, sid):
    own = [r for r in data.question_results if r.student_id == sid]
    question_tags = {}
    for tag in data.question_tags:
        question_tags.setdefault(tag.question_id, set()).add((tag.category, tag.tag))
    groups = {}
    for category in data.learning_settings.get('report_categories', {}):
        values = list(dict.fromkeys(data.learning_settings['report_categories'][category]))
        rows = []
        for tag in values:
            result = performance(data, sid, [(category, tag)])
            count = len(result['question_ids'])
            rows.append(dict(label=tag, score=result['score'], maximum=result['maximum'], percent=result['percent'], count=count,
                ungraded=sum(r.status != 'graded' for r in own if (category, tag) in question_tags.get(r.question_id, ())),
                pattern=pattern(count, result['percent'])))
        groups[category] = dict(rows=rows, unknown=sum(not any(c == category for c, _ in question_tags.get(r.question_id, ())) for r in own))
    syllabus = []
    for row in evidence_by_node(data, sid).values():
        percent = 100 * row['score'] / row['maximum'] if row['maximum'] else None
        syllabus.append(dict(row, percent=percent, pattern=pattern(row['count'], percent)))
    questions = [dict(assessment=data.assessments[r.assessment_id].name, number=data.questions[r.question_id].number,
        score=r.score, maximum=data.questions[r.question_id].marks, status=r.status,
        scope=data.questions[r.question_id].level) for r in own]
    from .curriculum_tree import tree
    nodes = {row['node_id']: row for row in syllabus}
    from .curriculum import node_index
    allowed = node_index(data.curriculum or {})
    unclassified = [r for r in own if not any(n in allowed for n in data.question_curriculum.get(r.question_id, []))]
    graded = [r for r in unclassified if r.status == 'graded']
    unknown = dict(count=len(graded), ungraded=len(unclassified)-len(graded),
                   score=sum(r.score for r in graded), maximum=sum(data.questions[r.question_id].marks for r in graded))
    unknown['percent'] = 100 * unknown['score'] / unknown['maximum'] if unknown['maximum'] else None
    return dict(groups=groups, syllabus=syllabus, questions=questions,
                curriculum_tree=tree(data.curriculum, nodes), unclassified=unknown)


def pattern(count, percent):
    if count < 2 or percent is None:
        return 'Insufficient evidence'
    return 'Strength' if percent >= 75 else ('Low performance' if percent < 50 else 'Developing')
