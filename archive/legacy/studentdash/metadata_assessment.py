"""Metadata-only ChatGPT proposals, editable previews and non-destructive imports."""
from copy import deepcopy
from datetime import date, datetime, timezone
import json
import re

from .assessment_import import import_profile
from .entry import EntryError, identifier, prepare_assessment, text
from .import_suggestions import curriculum_nodes

SCHEMA = 'studentdash-assessment-metadata-v2'


def prompt(doc):
    profile = import_profile(doc)
    example = dict(schema=SCHEMA, class_id=doc['id'], assessment_id=None,
        name='Assessment name', date=date.today().isoformat(), questions=[dict(number='1a', marks=2,
        tags={c: [] for c in profile['categories']}, curriculum_nodes=[], scope='', name='')])
    return ('Create assessment METADATA for Studentdash from the attached test paper. '
        'Return one JSON object only, following the exact schema below. '
        'Include only individually scored questions/subparts, preserving their exact labels (including * prefixes). '
        'Do not include parent subtotals as additional questions or count marks twice. '
        'Include positive maximum marks, classifications and supported curriculum references. '
        'Do NOT include full question text, answers, marking instructions, source documents, page references, '
        'student information, confidence values, context entries or review checkboxes. '
        'The optional name is a short label, not question text. '
        'Use exact configured category/tag values; multiple tags are arrays. '
        'Leave uncertain classifications as empty arrays and unknown scope as an empty string; never invent them. '
        'Use only configured curriculum node IDs; never infer parents by splitting syllabus codes. '
        'If maximum marks cannot be determined, use null so the teacher can correct them in the preview. '
        'Use the assessment date below unless I specify another; it is editable in Studentdash. '
        'Keep class_id exactly as given. Leave assessment_id null for a new import: Studentdash manages stable IDs '
        'and recognizes repeated name/date imports. For an explicit update, use an existing ID listed below.\n\n'
        'JSON schema/example (return all scored parts, not just this example):\n' + json.dumps(example, indent=2) +
        '\n\nAllowed categories and tags:\n' + json.dumps(profile['categories'], indent=2) +
        '\n\nConfigured scope values (empty string also allowed):\n' + json.dumps(profile.get('levels', [])) +
        '\n\nConfigured curriculum nodes:\n' + json.dumps([dict(id=k, label=n['label'], parent=n.get('parent'), code=n.get('code'))
            for k, n in curriculum_nodes(profile).items()], indent=2) +
        '\n\nExisting assessment identities (no student results):\n' + json.dumps([
            dict(assessment_id=a['id'], name=a['name'], date=a['date']) for a in doc['assessments']], indent=2))


def parse(raw, key):
    if not isinstance(raw, str) or not raw.strip() or len(raw.encode()) > 1_000_000:
        raise EntryError('Paste a complete JSON response of at most 1 MB.')
    value = raw.strip()
    fence = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', value, re.S | re.I)
    if fence:
        value = fence[1]
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate JSON field')
            result[k] = v
        return result
    def invalid(value):
        raise ValueError('invalid number')
    try:
        payload = json.loads(value, object_pairs_hook=unique, parse_constant=invalid)
    except (ValueError, RecursionError):
        raise EntryError('Invalid JSON. Paste the complete response without extra explanation.') from None
    if not isinstance(payload, dict) or payload.get('schema') != SCHEMA or payload.get('class_id') != key:
        raise EntryError('Copy the prompt for this class. The schema and class_id must match.')
    if set(payload) - {'schema', 'class_id', 'assessment_id', 'name', 'date', 'questions'}:
        raise EntryError('Use metadata fields only: schema, class_id, assessment_id, name, date, questions.')
    if payload.get('assessment_id') is not None and not isinstance(payload['assessment_id'], str):
        raise EntryError('assessment_id must be an existing ID or null.')
    questions = payload.get('questions')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 200:
        raise EntryError('Include 1–200 individually scored questions.')
    for i, q in enumerate(questions, 1):
        if not isinstance(q, dict) or set(q) - {'number', 'marks', 'tags', 'curriculum_nodes', 'scope', 'name'}:
            raise EntryError(f'Question {i}: include only number, marks, tags, curriculum_nodes, scope and optional name.')
        if not isinstance(q.get('number'), str) or not isinstance(q.get('name', ''), str) or not isinstance(q.get('scope', ''), str):
            raise EntryError(f'Question {i}: label, optional name and scope must be text.')
        if not isinstance(q.get('marks'), (int, float, str, type(None))) or isinstance(q.get('marks'), bool):
            raise EntryError(f'Question {i}: marks must be numeric or null.')
        tags = q.setdefault('tags', {})
        if not isinstance(tags, dict) or any(not isinstance(v, list) or any(not isinstance(t, str) for t in v) for v in tags.values()):
            raise EntryError(f'Question {i}: tags must map categories to arrays of text values.')
        nodes = q.setdefault('curriculum_nodes', [])
        if not isinstance(nodes, list) or any(not isinstance(n, str) for n in nodes):
            raise EntryError(f'Question {i}: curriculum_nodes must contain configured node IDs.')
        q.setdefault('scope', '')
        q.setdefault('name', '')
    return payload


def proposal(doc, payload):
    """Build against a copy: no scores, IDs or classifications change during preview."""
    working = deepcopy(doc)
    working['profile'] = import_profile(doc)
    profile = working['profile']
    aid = payload.get('assessment_id')
    if aid:
        matches = [a for a in doc['assessments'] if a['id'] == aid]
        if not matches:
            raise EntryError('Unknown assessment ID. Select an existing assessment or leave the ID null.')
    else:
        matches = [a for a in doc['assessments'] if a['date'] == payload.get('date') and a['name'].casefold() == str(payload.get('name', '')).strip().casefold()]
        if len(matches) > 1:
            raise EntryError('Several saved assessments share this name/date. Select the intended assessment explicitly.')
    old = matches[0] if matches else None
    old_questions = {q['number']: q for q in old['questions']} if old else {}
    questions, changes = [], []
    allowed_nodes = curriculum_nodes(profile)
    for raw in payload['questions']:
        previous = old_questions.get(raw['number'].strip(), {})
        scope = raw.get('scope', '').strip() or previous.get('scope', '')
        if scope and scope not in profile.get('levels', []):
            raise EntryError(f'Question {raw["number"]}: unknown scope {scope}. Use a configured scope or leave it blank.')
        tags = deepcopy(previous.get('tags', {}))
        for category, values in raw.get('tags', {}).items():
            if category not in profile['categories'] or any(t not in profile['categories'][category] for t in values):
                raise EntryError(f'Question {raw["number"]}: unknown category/tag in {category}. Choose a listed value.')
            if not profile.get('category_options', {}).get(category, {}).get('multiple', True) and len(set(values)) > 1:
                raise EntryError(f'Question {raw["number"]}: {category} permits only one tag.')
            if values:
                tags[category] = list(dict.fromkeys(values))
        links = raw.get('curriculum_nodes') or previous.get('curriculum_nodes', [])
        name = text(raw.get('name', ''), 'Short question name', 200)
        questions.append(dict(id=previous.get('id'), number=raw['number'], marks=raw.get('marks'),
            text=previous.get('text', name), tags=tags, curriculum_nodes=links,
            curriculum='; '.join(allowed_nodes[n].get('code') or allowed_nodes[n]['label'] for n in links if n in allowed_nodes), scope=scope))
    item = prepare_assessment(working, old['id'] if old else None, dict(name=payload.get('name'), date=payload.get('date'),
        description=old.get('description', '') if old else '', participants=old['participants'] if old else [s['id'] for s in doc['students']], questions=questions))
    for q, raw in zip(item['questions'], questions):
        q['scope'] = raw['scope']
    for q, raw in zip(item['questions'], payload['questions']):
        previous = old_questions.get(raw['number'].strip(), {})
        q['name'] = raw.get('name', '') or previous.get('name', '')
    item['metadata_only'] = True
    if old:
        old_ids = {q['id'] for q in old['questions']}
        new_ids = {q['id'] for q in item['questions']}
        if old_ids != new_ids:
            changes.append('The question list changes. Matching labels keep their IDs and scores; questions with recorded evidence cannot be removed.')
        for q in item['questions']:
            prev = next((p for p in old['questions'] if p['id'] == q['id']), None)
            if prev and any(prev.get(f, '' if f == 'scope' else None) != q.get(f) for f in ('marks', 'tags', 'curriculum_nodes', 'scope')):
                changes.append(f'Question {q["number"]}: replace maximum marks, classifications, curriculum or scope; existing scores are retained.')
        if (old['name'], old['date']) != (item['name'], item['date']):
            changes.append('Update the existing assessment name/date while retaining its stable ID.')
    return item, changes


def save_preview(store, key, raw, version, assessment_id=None):
    payload = parse(raw, key)
    if assessment_id:
        payload['assessment_id'] = assessment_id
    doc = store.read(key)
    if not payload.get('assessment_id'):
        matches = [a for a in doc['assessments'] if a['date'] == payload.get('date') and a['name'].casefold() == str(payload.get('name', '')).strip().casefold()]
        if len(matches) == 1:
            payload['assessment_id'] = matches[0]['id']
    did = identifier()
    doc.setdefault('metadata_previews', []).append(dict(id=did, payload=payload, status='preview',
        created=datetime.now(timezone.utc).isoformat()))
    store.save(doc, version)
    return did


def get_preview(doc, did):
    preview = next((p for p in doc.get('metadata_previews', []) if p['id'] == did), None)
    if preview is None:
        raise EntryError('This metadata preview is unavailable. Paste the response again.')
    return preview


def commit(store, key, did, raw, version, replace=False):
    doc = store.read(key)
    preview = get_preview(doc, did)
    if preview['status'] == 'imported':
        return preview['assessment_id']
    payload = parse(raw, key)
    if preview['payload'].get('assessment_id') and not payload.get('assessment_id'):
        payload['assessment_id'] = preview['payload']['assessment_id']
    item, changes = proposal(doc, payload)
    if changes and not replace:
        raise EntryError('Review and confirm replacements before updating the existing assessment.')
    existing = next((a for a in doc['assessments'] if a['id'] == item['id']), None)
    if existing:
        doc['assessments'][doc['assessments'].index(existing)] = item
    else:
        doc['assessments'].append(item)
    doc.setdefault('metadata_import_history', []).append(dict(assessment_id=item['id'],
        imported=datetime.now(timezone.utc).isoformat(), before=deepcopy(existing), after=deepcopy(item),
        replacements_confirmed=replace))
    preview.update(status='imported', assessment_id=item['id'], payload=payload)
    store.save(doc, version)
    return item['id']
