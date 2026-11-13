"""Self-reported confidence is independent of graded assessment evidence."""
from copy import deepcopy
from datetime import datetime, timezone
from .entry import EntryError, assessment

CONFIG = dict(enabled=True, min=1, max=5)

def configuration(value):
    if not isinstance(value, dict) or set(value) != set(CONFIG) or type(value.get('enabled')) is not bool or type(value.get('min')) is not int or type(value.get('max')) is not int or value['min'] != 1 or value['max'] != 5:
        raise EntryError('confidence requires boolean enabled and fixed integer min=1, max=5. Omit it when not requested.')
    return deepcopy(value)

def ratings(item, values):
    if not isinstance(values, dict) or any(s not in item['participants'] for s in values):
        raise EntryError('Confidence must refer only to participating students.')
    result = deepcopy(item.get('confidence_ratings', {}))
    for sid, value in values.items():
        if isinstance(value, str):
            value = value.strip()
        if value is None or value == '':
            result.pop(sid, None)
        elif type(value) is int and 1 <= value <= 5:
            result[sid] = value
        elif isinstance(value, str) and value in {'1','2','3','4','5'}:
            result[sid] = int(value)
        else:
            raise EntryError('Confidence: enter a whole number from 1 to 5, or leave blank for Not recorded.')
    return result

def correct_scored_question(store, key, aid, qid, version):
    doc = store.read(key)
    item = assessment(doc, aid)
    question = next((q for q in item['questions'] if q['id'] == qid), None)
    if not question or len(item['questions']) < 2:
        raise EntryError('Choose an existing question; at least one scored question must remain.')
    item.setdefault('confidence_corrections', []).append(dict(
        question=deepcopy(question), scores={s: deepcopy(row[qid]) for s,row in item['scores'].items() if qid in row},
        previous_maximum=sum(q['marks'] for q in item['questions']),
        corrected_at=datetime.now(timezone.utc).isoformat()))
    item['questions'] = [q for q in item['questions'] if q['id'] != qid]
    for row in item['scores'].values():
        row.pop(qid, None)
    item['confidence'] = deepcopy(CONFIG)
    store.save(doc, version)
