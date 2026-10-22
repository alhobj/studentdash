"""Teacher-pasted assessment proposals; no API calls and no automatic approval."""
from copy import deepcopy
from datetime import date
import hashlib
import json
import math
import re

from .assessment_import import draft_by_id, import_profile, update_review, validation
from .entry import EntryError, identifier
from .import_suggestions import curriculum_nodes

SCHEMA = 'studentdash-assessment-v1'


def prompt(doc, draft=None):
    profile = draft['profile'] if draft else import_profile(doc)
    example = dict(schema=SCHEMA, class_id=doc['id'], title='Assessment title',
                   date=draft['date'] if draft else date.today().isoformat(), description='',
                   document_total=None, questions=[dict(number='1a', parent=None, scorable=True,
                   text='Exact question text, including necessary context and data', marks=2,
                   tags={category: [] for category in profile['categories']}, curriculum_nodes=[], notes='')])
    context = [dict(number=n['number'], text=n['text'], marks=n['marks'], scorable=n['scorable'])
               for n in draft['nodes']] if draft else []
    return ('Prepare this assessment for import into Studentdash. I am attaching the test paper and mark scheme. '
            'Use both documents to identify every question/subpart, its exact label, readable question text, '
            'maximum marks and classifications. Use the mark scheme to check marks and intended skills, '
            'but do not include answers or marking instructions in question text. Do not include student data. '
            'Return ONE JSON object only, in the format below, not a table or explanatory prose. '
            'Keep schema and class_id exactly as shown. Use the supplied assessment date unless I specify another; '
            'I can correct it in the preview. Include all questions, not just the example. '
            'Represent shared context as a separate non-scorable question with scorable=false and marks=null; '
            'its child questions reference its label in parent. Never count a parent subtotal as a scored question. '
            'Keep labels unique, including * prefixes. Include necessary tables as readable text; do not invent '
            'unreadable figures, equations, marks or question text. Put uncertainties/figure references in notes, '
            'leave unknown marks null and unknown classifications empty. '
            'tags must map configured category names to arrays of exact allowed values, with multiple values '
            'where justified. Use only the vocabulary below. curriculum_nodes must contain exact configured node '
            'IDs below; leave empty when no supported match exists. Do not invent or translate syllabus codes. '
            'document_total is the paper total if explicitly stated, otherwise null. '
            'Any existing extracted questions below are provisional: check and correct them against both attachments.\n\n'
            'JSON format (example values are placeholders):\n' + json.dumps(example, indent=2) +
            '\n\nAllowed classification vocabulary:\n' + json.dumps(profile['categories'], indent=2) +
            '\n\nConfigured curriculum nodes:\n' + json.dumps([dict(id=k, label=n['label'], parent=n.get('parent'), code=n.get('code'))
                for k, n in curriculum_nodes(profile).items()], indent=2) +
            '\n\nExisting extracted questions (not student results):\n' + json.dumps(context, indent=2))


def parse_response(raw, key):
    if not isinstance(raw, str) or not raw.strip() or len(raw.encode('utf-8')) > 1_000_000:
        raise EntryError('Paste a non-empty ChatGPT JSON response of at most 1 MB.')
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

    def invalid_constant(value):
        raise ValueError('non-finite number')

    try:
        payload = json.loads(value, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, RecursionError):
        raise EntryError('The pasted response is not valid JSON. Copy the complete JSON object, with no extra explanation.') from None
    if not isinstance(payload, dict) or payload.get('schema') != SCHEMA or payload.get('class_id') != key:
        raise EntryError('Use the prompt for this class. The response needs the matching schema and class_id.')
    if set(payload) - {'schema', 'class_id', 'title', 'date', 'description', 'document_total', 'questions'}:
        raise EntryError('The response contains unsupported fields. Ask ChatGPT to follow the provided JSON format exactly.')
    questions = payload.get('questions')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 250:
        raise EntryError('The response needs 1–250 questions/context entries.')
    seen = set()
    for n, q in enumerate(questions, 1):
        if not isinstance(q, dict) or set(q) - {'number', 'parent', 'scorable', 'text', 'marks', 'tags', 'curriculum_nodes', 'notes'}:
            raise EntryError(f'Question {n}: use only the fields shown in the prompt.')
        label = q.get('number')
        if not isinstance(label, str) or not label.strip() or label.strip().casefold() in seen:
            raise EntryError(f'Question {n}: question labels must be unique, non-empty strings.')
        seen.add(label.strip().casefold())
        if not isinstance(q.get('text'), str) or not isinstance(q.get('scorable'), bool):
            raise EntryError(f'Question {label}: text and a true/false scorable value are required.')
        if q.get('parent') is not None and not isinstance(q['parent'], str):
            raise EntryError(f'Question {label}: parent must be a question label or null.')
        tags = q.get('tags', {})
        nodes = q.get('curriculum_nodes', [])
        if not isinstance(tags, dict) or any(not isinstance(v, list) or any(not isinstance(t, str) for t in v) for v in tags.values()):
            raise EntryError(f'Question {label}: tags must contain arrays of allowed text values.')
        if not isinstance(nodes, list) or any(not isinstance(k, str) for k in nodes):
            raise EntryError(f'Question {label}: curriculum_nodes must be an array of configured IDs.')
        if not isinstance(q.get('notes', ''), str) or len(q.get('notes', '')) > 2000:
            raise EntryError(f'Question {label}: notes must be text of at most 2000 characters.')
    total = payload.get('document_total')
    if total is not None and (isinstance(total, bool) or not isinstance(total, (int, float)) or not math.isfinite(total) or total <= 0):
        raise EntryError('document_total must be a positive finite number or null.')
    return payload


def save_response(store, key, raw, version, did=None):
    payload = parse_response(raw, key)
    doc = store.read(key)
    original = draft_by_id(doc, did) if did else None
    if original and original['status'] != 'draft':
        raise EntryError('This assessment has already been created. Start a new import or edit the existing assessment.')
    draft = deepcopy(original) if original else dict(id=identifier(), status='draft', nodes=[],
        profile=import_profile(doc), source=dict(filename='chatgpt-assessment.json', method='teacher-pasted-json'),
        extraction=dict(warnings=[], blocks=[], instructions=[]))
    by_number = {n['number']: n['id'] for n in draft['nodes']}
    labels = {q['number'].strip(): by_number.get(q['number'].strip()) or identifier() for q in payload['questions']}
    nodes = []
    for q in payload['questions']:
        parent = q.get('parent')
        if parent is not None and parent.strip() not in labels:
            raise EntryError(f'Question {q["number"]}: unknown parent label {parent}.')
        nodes.append(dict(id=labels[q['number'].strip()], number=q['number'].strip(), parent=labels[parent.strip()] if parent else None,
                          text=q['text'], marks=q.get('marks'), scorable=q['scorable'],
                          tags=q.get('tags', {}), curriculum_nodes=q.get('curriculum_nodes', []), reviewed=False))
    review = dict(title=payload.get('title'), date=payload.get('date'), description=payload.get('description', ''),
                  participants=original['participants'] if original else [s['id'] for s in doc['students']],
                  nodes=nodes, review_ack=False, warning_note='')
    update_review(draft, review, doc)
    for node, q in zip(draft['nodes'], payload['questions']):
        node['warnings'] = [q['notes']] if q.get('notes') else []
    draft['extraction']['document_total'] = payload.get('document_total')
    draft['extraction']['warnings'] = list(dict.fromkeys(draft['extraction'].get('warnings', []) +
        ['ChatGPT-generated proposal: compare question text, figures, marks and classifications with the test and mark scheme before creating the assessment.']))
    # Structural errors are actionable on paste; missing marks can be corrected in the normal review.
    report = validation(draft)
    structural = [error for error in report['errors'] if not error.endswith(': enter positive maximum marks.')]
    if structural:
        raise EntryError(' '.join(structural))
    draft['chatgpt'] = True
    content = raw.encode('utf-8')
    source_id = identifier() if original else draft['id']
    draft['chatgpt_source_id'] = source_id
    if not original:
        draft['source']['sha256'] = hashlib.sha256(content).hexdigest()
        doc.setdefault('import_drafts', []).append(draft)
    else:
        doc['import_drafts'][doc['import_drafts'].index(original)] = draft
    store.save(doc, version, source=(source_id, 'chatgpt-assessment.json', 'application/json', content))
    return draft['id']
