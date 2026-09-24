"""Saved import drafts, teacher review and atomic conversion to normal assessments."""
from copy import deepcopy
from datetime import date
import hashlib
import math
from pathlib import PurePath
import re

from .classification import DEFAULT_PROFILE, QuestionTag
from .document_extract import IMPORTERS, MAX_BYTES, ExtractionError, ExtractedDocument, structure
from .entry import EntryError, identifier, prepare_assessment, text
from .import_suggestions import curriculum_nodes, suggest_draft


def draft_by_id(doc, did):
    draft = next((d for d in doc.get('import_drafts', []) if d['id'] == did), None)
    if draft is None:
        raise EntryError('This import draft is unavailable.')
    return draft


def import_profile(doc):
    profile = deepcopy(doc['profile'])
    # Earlier saved copies of this exact vocabulary predate suggestion definitions.
    # Add only missing configuration, without changing existing categories or curriculum.
    if profile.get('name') == DEFAULT_PROFILE['name'] and profile['categories'] == DEFAULT_PROFILE['categories']:
        for key in ('suggestion_rules', 'tag_definitions', 'category_options'):
            profile.setdefault(key, deepcopy(DEFAULT_PROFILE.get(key, {})))
    return profile


def create_draft(store, key, filename, content, provider=None):
    filename = filename.replace('\\', '/').split('/')[-1][:240]
    extension = PurePath(filename).suffix.lower()
    if extension not in IMPORTERS:
        raise EntryError('Upload a PDF or DOCX test document.')
    if not content or len(content) > MAX_BYTES:
        raise EntryError('Choose a non-empty document no larger than 20 MB.')
    doc = store.read(key)
    try:
        extracted = IMPORTERS[extension]().extract(content)
    except ExtractionError as exc:
        # Keep the original even when extraction fails; do not create a fake question.
        extracted = ExtractedDocument(method='failed', warnings=[str(exc)])
    parsed = structure(extracted)
    draft = dict(id=identifier(), status='draft', title=parsed['title'][:200] or PurePath(filename).stem[:200],
                 date=date.today().isoformat(), description='', participants=[s['id'] for s in doc['students']],
                 source=dict(filename=filename, sha256=hashlib.sha256(content).hexdigest(), method=parsed['method']),
                 extraction=deepcopy(parsed), nodes=parsed['nodes'], profile=import_profile(doc),
                 review_ack=False, warning_note='')
    suggest_draft(draft, provider)
    doc.setdefault('import_drafts', []).append(draft)
    mime = 'application/pdf' if extension == '.pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    store.save(doc, doc['version'], source=(draft['id'], filename, mime, content))
    return draft['id']


def parent_context(node, index):
    parents, parent, seen = [], node.get('parent'), set()
    while parent in index and parent not in seen:
        seen.add(parent)
        parents.append(index[parent])
        parent = index[parent].get('parent')
    return list(reversed(parents))


def validation(draft):
    errors, warnings = [], list(draft['extraction'].get('warnings', []))
    nodes = draft['nodes']
    index = {n['id']: n for n in nodes}
    if not nodes:
        errors.append('Add at least one scorable question.')
    if len(index) != len(nodes):
        errors.append('Question references must be unique.')
    numbers, seen_text = set(), set()
    for node in nodes:
        number = node['number'].strip().casefold()
        if not number or number in numbers:
            errors.append('Every question/context needs a unique, non-empty label.')
        numbers.add(number)
        if node.get('parent') and node['parent'] not in index:
            errors.append(f"Question {node['number']}: select an existing parent or no parent.")
        parent, visited = node.get('parent'), {node['id']}
        while parent in index:
            if parent in visited:
                errors.append(f"Question {node['number']}: parent relationships contain a cycle.")
                break
            visited.add(parent)
            parent = index[parent].get('parent')
        children = [n for n in nodes if n.get('parent') == node['id']]
        if node['scorable']:
            if children:
                errors.append(f"Question {node['number']}: a shared-context parent cannot also be scored. Put any separate marks on a child question.")
            if not node['text'].strip():
                errors.append(f"Question {node['number']}: enter its question text.")
            if node['marks'] is None or node['marks'] <= 0:
                errors.append(f"Question {node['number']}: enter positive maximum marks.")
            full_text = '\n'.join(n['text'] for n in parent_context(node, index) + [node])
            normalized = re.sub(r'\W+', ' ', full_text).strip().casefold()
            if normalized and normalized in seen_text:
                errors.append(f"Question {node['number']}: duplicate question text and context. Remove the duplicate or correct its context.")
            seen_text.add(normalized)
        elif not children:
            warnings.append(f"Context {node['number']} has no children and will not appear in score entry.")
        elif node['marks'] is not None:
            leaves = [n for n in nodes if n['scorable'] and node in parent_context(n, index)]
            if all(n['marks'] is not None for n in leaves) and not math.isclose(sum(n['marks'] for n in leaves), node['marks']):
                warnings.append(f"Question {node['number']}: parent subtotal {node['marks']:g} differs from its scorable parts.")
    scorable = [n for n in nodes if n['scorable']]
    if not scorable:
        errors.append('Add at least one scorable question.')
    maximum = sum(n['marks'] or 0 for n in scorable)
    if not math.isfinite(maximum):
        errors.append('The total maximum marks is too large.')
    document_total = draft['extraction'].get('document_total')
    mismatch = document_total is not None and not math.isclose(document_total, maximum)
    if mismatch:
        warnings.append(f'Document total: {document_total:g}; extracted/reviewed total: {maximum:g}. Check the difference.')
    warnings.extend(f"Question {n['number']}: {w}" for n in nodes for w in n.get('warnings', []))
    return dict(errors=list(dict.fromkeys(errors)), warnings=list(dict.fromkeys(warnings)), total=maximum,
                document_total=document_total, mismatch=mismatch, count=len(scorable),
                number_confident=sum(n['confidence']['number'] >= .9 for n in scorable),
                marks_confident=sum(n['confidence']['marks'] >= .9 for n in scorable),
                curriculum_confident=sum(any(s['kind'] == 'curriculum' and s['confidence'] >= .9 for s in n.get('suggestions', [])) for n in scorable))


def update_review(draft, payload, doc):
    if not isinstance(payload, dict) or not isinstance(payload.get('nodes'), list) or len(payload['nodes']) > 250:
        raise EntryError('The draft could not be read, or contains more than 250 questions/context entries.')
    draft['title'] = text(payload.get('title', ''), 'Assessment name', 200, True)
    try:
        draft['date'] = date.fromisoformat(payload.get('date', '')).isoformat()
    except (TypeError, ValueError):
        raise EntryError('Choose a valid assessment date.') from None
    draft['description'] = text(payload.get('description', ''), 'Description', 5000)
    participants = payload.get('participants', [])
    if not isinstance(participants, list) or not participants or any(s not in {p['id'] for p in doc['students']} for s in participants):
        raise EntryError('Select at least one student in this class.')
    draft['participants'] = list(dict.fromkeys(participants))
    prior = {n['id']: n for n in draft['nodes']}
    profile = draft['profile']
    curriculum = curriculum_nodes(profile)
    nodes, seen = [], set()
    for raw in payload['nodes']:
        if not isinstance(raw, dict):
            raise EntryError('A question could not be read.')
        key = raw.get('id') or identifier()
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{32}', key) or key in seen:
            raise EntryError('Questions must have distinct references. Reload and retry.')
        seen.add(key)
        old = prior.get(key)
        node = deepcopy(old) if old else dict(id=key, source_text='', source_pages=[], source_locations=[], tables=[], figures=[],
            confidence=dict(number=0, text=0, marks=0), warnings=['Teacher-added or split question: compare with the source.'])
        origins = raw.get('origins', [])
        if not isinstance(origins, list) or any(not isinstance(i, str) or i not in prior for i in origins):
            raise EntryError('A combined/split source reference is invalid.')
        if origins:
            for field in ('source_pages', 'source_locations', 'figures'):
                node[field] = list(dict.fromkeys(node[field] + [v for i in origins for v in prior[i].get(field, [])]))
            node['source_text'] = '\n\n'.join(dict.fromkeys([node['source_text']] + [prior[i]['source_text'] for i in origins])).strip()
            node['tables'] = [*node.get('tables', []), *(t for i in origins if i != key for t in prior[i].get('tables', []))]
        node['number'] = text(raw.get('number', ''), 'Question label', 40)
        node['text'] = text(raw.get('text', ''), 'Question text', 20000)
        node['parent'] = raw.get('parent') or None
        if node['parent'] is not None and not isinstance(node['parent'], str):
            raise EntryError('Choose a parent question from the list.')
        node['scorable'] = raw.get('scorable') is True
        maximum = raw.get('marks')
        if maximum in ('', None):
            node['marks'] = None
        else:
            try:
                node['marks'] = float(maximum)
            except (TypeError, ValueError):
                raise EntryError(f"Question {node['number']}: enter numeric marks or leave blank for review.") from None
            if isinstance(maximum, bool) or not math.isfinite(node['marks']) or node['marks'] < 0:
                raise EntryError(f"Question {node['number']}: invalid maximum marks.")
        tags = raw.get('tags', {})
        if not isinstance(tags, dict):
            raise EntryError('Choose tags from the listed classifications.')
        for category, values in tags.items():
            if category not in profile['categories'] or not isinstance(values, list):
                raise EntryError('Choose tags from the listed classifications.')
            if not profile.get('category_options', {}).get(category, {}).get('multiple', True) and len(values) > 1:
                raise EntryError(f'{category} allows only one tag per question.')
            for value in values:
                try:
                    QuestionTag(key, category, value, 'teacher', vocabulary=profile['categories'])
                except (TypeError, ValueError):
                    raise EntryError(f'{category}: unknown classification.') from None
        node['tags'] = {c: list(dict.fromkeys(v)) for c, v in tags.items() if v}
        selected_nodes = raw.get('curriculum_nodes', [])
        if not isinstance(selected_nodes, list) or any(not isinstance(k, str) or k not in curriculum for k in selected_nodes):
            raise EntryError('Select curriculum mappings from the configured course nodes.')
        node['curriculum_nodes'] = list(dict.fromkeys(selected_nodes))
        # Saving an unfinished draft is not an implicit rejection of pending proposals.
        # Only explicit decisions and edits protect a category against later automation.
        decisions = raw.get('decisions', (old or {}).get('decisions', {}))
        if not isinstance(decisions, dict) or any(v not in {'accepted', 'rejected', 'pending'} for v in decisions.values()):
            raise EntryError('A classification review decision is invalid.')
        reviewed_categories = set((old or {}).get('reviewed_categories', []))
        for category in profile['categories']:
            if set(node['tags'].get(category, [])) != set((old or {}).get('tags', {}).get(category, [])):
                reviewed_categories.add(category)
        if set(node['curriculum_nodes']) != set((old or {}).get('curriculum_nodes', [])):
            reviewed_categories.add('__curriculum__')
        node['decisions'] = deepcopy((old or {}).get('decisions', {}))
        for suggestion in (old or {}).get('suggestions', []):
            selected = node['curriculum_nodes'] if suggestion['kind'] == 'curriculum' else node['tags'].get(suggestion['category'], [])
            category = suggestion['category'] if suggestion['kind'] == 'tag' else '__curriculum__'
            decision = decisions.get(suggestion['key'], 'pending')
            if decision != 'pending' or category in reviewed_categories:
                node['decisions'][suggestion['key']] = 'accepted' if suggestion['value'] in selected else 'rejected'
                reviewed_categories.add(category)
        node['reviewed_categories'] = list(reviewed_categories)
        node['reviewed'] = raw.get('reviewed') is True
        nodes.append(node)
    draft['nodes'] = nodes
    draft['review_ack'] = payload.get('review_ack') is True
    draft['warning_note'] = text(payload.get('warning_note', ''), 'Review note', 2000)
    suggest_draft(draft)


def save_review(store, key, did, payload, version, finalize=False):
    doc = store.read(key)
    draft = draft_by_id(doc, did)
    if draft['status'] != 'draft':
        raise EntryError('This draft has already created an assessment. Open that assessment to make changes.')
    update_review(draft, payload, doc)
    report = validation(draft)
    if finalize:
        if report['errors']:
            raise EntryError(' '.join(report['errors']))
        if not draft['review_ack'] or any(not n['reviewed'] for n in draft['nodes']):
            raise EntryError('Check each question/context against the original, then confirm the final review.')
        if report['mismatch'] and not draft['warning_note'].strip():
            raise EntryError('Explain the document-total difference in the review note before creating the assessment.')
        index = {n['id']: n for n in draft['nodes']}
        curriculum = curriculum_nodes(draft['profile'])
        leaves = [n for n in draft['nodes'] if n['scorable']]
        questions = []
        for node in leaves:
            context = parent_context(node, index)
            parts = [n['text'] for n in context + [node] if n['text'].strip()]
            questions.append(dict(number=node['number'], marks=node['marks'], text='\n\n'.join(parts), tags=node['tags'],
                curriculum='; '.join(curriculum[k].get('code') or curriculum[k]['label'] for k in node['curriculum_nodes'])))
        item = prepare_assessment(doc, None, dict(name=draft['title'], date=draft['date'], description=draft['description'],
                                                 participants=draft['participants'], questions=questions))
        for question, node in zip(item['questions'], leaves):
            question['import_context'] = dict(draft=did, node=node['id'], parent=node['parent'], source_pages=node['source_pages'],
                source_text=node['source_text'], figures=node['figures'], tables=node['tables'], curriculum_nodes=node['curriculum_nodes'],
                classifications=[dict(category=c, tag=t, source='teacher', confidence=None) for c, tags in node['tags'].items() for t in tags],
                suggestions=deepcopy(node.get('suggestions', [])))
        item['import_source'] = dict(draft=did, filename=draft['source']['filename'], sha256=draft['source']['sha256'],
                                    hierarchy=deepcopy(draft['nodes']), instructions=draft['extraction']['instructions'])
        draft['status'], draft['assessment_id'] = 'confirmed', item['id']
    store.save(doc, version)
    return draft.get('assessment_id') if finalize else None
