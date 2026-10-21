"""Explicit curriculum trees, teaching prerequisites and stable resource links."""
from copy import deepcopy
import json
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from .config import ROOT


def node_index(curriculum):
    nodes = curriculum.get('nodes', [])
    if not isinstance(nodes, list):
        raise ValueError('Curriculum nodes must be a list.')
    index = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get('id'), str) or not node['id'] or node['id'] in index or not isinstance(node.get('label'), str) or not node['label'].strip():
            raise ValueError('The course curriculum has missing or duplicate node references.')
        index[node['id']] = node
    for relation in ('parent', 'prerequisites'):
        visiting, done = set(), set()
        def visit(key):
            if key in visiting:
                raise ValueError('The course curriculum has an invalid parent or prerequisite cycle.')
            if key in done:
                return
            visiting.add(key)
            node = index[key]
            refs = ([node['parent']] if node.get('parent') else []) if relation == 'parent' else node.get('prerequisites', [])
            if not isinstance(refs, list) or any(not isinstance(r, str) or r not in index for r in refs):
                raise ValueError('The course curriculum has an invalid parent or prerequisite reference.')
            for ref in refs:
                visit(ref)
            visiting.remove(key)
            done.add(key)
        for key in index:
            visit(key)
    return index


def resource_path(value):
    if not isinstance(value, str) or any(c in value for c in ('\\', '%', '\x00')):
        raise ValueError('Resource paths must name local practice files.')
    url = urlsplit(value)
    path = PurePosixPath(url.path)
    if url.scheme or url.netloc or url.query or path.is_absolute() or '..' in path.parts or len(path.parts) < 2 or path.suffix != '.html':
        raise ValueError('Resource paths must name local practice HTML files without traversal.')
    return url.path


def validate_curriculum(curriculum):
    if not isinstance(curriculum, dict) or curriculum.get('schema') != 1:
        raise ValueError('Unsupported curriculum format.')
    for name in ('id', 'version', 'label'):
        if not isinstance(curriculum.get(name), str) or not curriculum[name].strip():
            raise ValueError('Curriculum identity, version and label are required.')
    index = node_index(curriculum)
    if curriculum.get('practice_journal'):
        resource_path(curriculum['practice_journal'])
    seen = set()
    resources = curriculum.get('resources', [])
    if not isinstance(resources, list):
        raise ValueError('Curriculum resources must be a list.')
    for resource in resources:
        if not isinstance(resource, dict) or not isinstance(resource.get('id'), str) or not resource['id'] or resource['id'] in seen:
            raise ValueError('Resource IDs must be unique.')
        seen.add(resource['id'])
        if resource.get('node_id') not in index or resource.get('role') not in {'basic', 'practice', 'check'} or not resource.get('title'):
            raise ValueError('Each resource needs a valid node, learning role and title.')
        resource_path(resource.get('path'))
    return curriculum


def catalog():
    result = {}
    for path in sorted((ROOT / 'curricula').glob('*.json')):
        item = validate_curriculum(json.loads(path.read_text(encoding='utf-8')))
        if item['id'] in result:
            raise ValueError('Duplicate curriculum identity in catalog.')
        result[item['id']] = item
    return result


def selected_curriculum(key):
    available = catalog()
    if key not in available:
        raise ValueError('Choose a curriculum from the catalog.')
    return deepcopy(available[key])


def ancestors(index, key):
    result = []
    while key:
        result.append(key)
        key = index[key].get('parent')
    return result


def evidence_by_node(data, sid, assessment_id=None):
    """Each graded question contributes once to each ancestor, including multi-mapped questions."""
    index = node_index(data.curriculum or {})
    grouped, seen = {}, set()
    for result in data.question_results:
        if result.student_id != sid or result.status != 'graded' or (assessment_id and result.assessment_id != assessment_id):
            continue
        key = (result.assessment_id, result.question_id)
        if key in seen:
            continue
        seen.add(key)
        q = data.questions[result.question_id]
        if result.score is None or not q.marks:
            continue
        parents = {parent for node in data.question_curriculum.get(q.id, []) if node in index for parent in ancestors(index, node)}
        for node in parents:
            row = grouped.setdefault(node, dict(node_id=node, label=index[node]['label'], score=0, maximum=0, count=0))
            row['score'] += result.score
            row['maximum'] += q.marks
            row['count'] += 1
    return grouped


def next_steps(data, sid, assessment_id=None):
    curriculum = data.curriculum
    plan = dict(focus=None, steps=[], reason='', unmapped=0, coverage=[], journal=curriculum.get('practice_journal') if curriculum else None)
    if not curriculum:
        plan['reason'] = 'Your teacher can connect this class to a curriculum to enable linked next steps. Your existing feedback and revision plan are still available.'
        return plan
    index = node_index(curriculum)
    own = [r for r in data.question_results if r.student_id == sid and r.status == 'graded'
           and (not assessment_id or r.assessment_id == assessment_id)]
    plan['unmapped'] = len({r.question_id for r in own if not data.question_curriculum.get(r.question_id)})
    grouped = evidence_by_node(data, sid, assessment_id)
    plan['coverage'] = [grouped[key] for key in index if key in grouped]
    candidates = [r for r in own if r.score is not None and data.questions[r.question_id].marks
                  and r.score < data.questions[r.question_id].marks and data.question_curriculum.get(r.question_id)]
    candidates.sort(key=lambda r: (-(data.questions[r.question_id].marks - r.score),
                                  -data.assessments[r.assessment_id].date.toordinal(), r.question_id))
    if not candidates:
        plan['reason'] = ('Some graded questions still need reviewed curriculum links. Ask your teacher to review them.' if plan['unmapped'] else
                          'No graded, linked question with lost marks in this view. This does not establish mastery of the whole curriculum.')
        return plan
    result = candidates[0]
    q = data.questions[result.question_id]
    linked = [key for key in data.question_curriculum[q.id] if key in index]
    if not linked:
        plan['reason'] = 'The curriculum links need teacher review.'
        return plan
    target = sorted(linked, key=lambda key: (-len(ancestors(index, key)), key))[0]
    resources = curriculum.get('resources', [])
    def resource(node, role):
        return next((r for r in resources if r['node_id'] == node and r['role'] == role), None)
    prerequisites = index[target].get('prerequisites', [])
    prerequisite = next((key for key in prerequisites if resource(key, 'basic')), target)
    plan['focus'] = dict(label=index[target]['label'], code=index[target].get('code', ''), assessment=data.assessments[q.assessment_id].name,
                         number=q.number, text=q.text, score=result.score, marks=q.marks)
    plan['reason'] = 'Start with one graded question with marks to recover; this is a practice suggestion, not a diagnosis of a whole topic.'
    for label, node, role, instruction in [
        ('Warm up', prerequisite, 'basic', 'Revisit this foundation before the main task. The prerequisite is a teaching suggestion, not evidence that you are weak at it.'),
        ('Practise', target, 'practice', 'Try one activity. Use its hints if needed and explain your method.'),
        ('Check independently', target, 'check', 'Try the check without hints first, then compare your reasoning with the worked answer.')]:
        item = resource(node, role)
        plan['steps'].append(dict(label=label, title=index[node]['label'], instruction=instruction,
                                  resource_id=item['id'] if item else None, path=item['path'] if item else None,
                                  fallback='Use the original question and ask your teacher for a suitable task.' if item is None else ''))
    return plan
