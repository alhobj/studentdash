"""Version-checked deletion of unpublished drafts and owned temporary sources only."""
from .entry import EntryError


def locate(doc, kind, did):
    collection = {'metadata': 'metadata_previews', 'document': 'import_drafts'}.get(kind)
    if not collection:
        raise EntryError('Choose an existing import draft.')
    draft = next((d for d in doc.get(collection, []) if d['id'] == did), None)
    if draft is None:
        raise EntryError('This draft no longer exists. The list has been refreshed; no assessment was deleted.')
    if draft.get('status') != ('preview' if kind == 'metadata' else 'draft') or draft.get('assessment_id') or any(a.get('import_source', {}).get('draft') == did for a in doc['assessments']):
        raise EntryError('This draft has already created an assessment and cannot be deleted as an import draft. Published assessments and results are protected.')
    title = draft.get('payload', {}).get('name') if kind == 'metadata' else draft.get('title')
    return collection, draft, title or 'Untitled assessment draft'


def sources(draft):
    return {draft['id'], draft.get('chatgpt_source_id', ''), *draft.get('chatgpt_source_ids', [])} - {''}


def delete(store, key, kind, did, version):
    doc = store.read(key)
    collection, draft, title = locate(doc, kind, did)
    doc[collection].remove(draft)
    protected = set()
    for other in doc.get('import_drafts', []):
        protected.update(sources(other))
    protected.update(a.get('import_source', {}).get('draft', '') for a in doc['assessments'])
    store.save(doc, version, delete_sources=sources(draft) - protected if kind == 'document' else ())
    return title
