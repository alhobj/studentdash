"""Learner-scoped learning histories and teacher-authored follow-up plans.

Evidence sources stay separate. Curriculum relationships come from explicit links.
"""
from collections import defaultdict
from datetime import datetime, timezone, date
from hashlib import sha256
from pathlib import PurePosixPath

from .curriculum import node_index, ancestors, next_steps
from .entry import EntryError, identifier, text


def learner_context(data, sid, state=None, completed=()):
    if sid not in data.students:
        raise KeyError(sid)
    state = state or {'feedback': [], 'attempts': []}
    curriculum = data.curriculum or {}
    index = node_index(curriculum)
    settings = getattr(data, 'learning_settings', {})
    def ticket_nodes(key):
        return sorted({parent for node in settings.get('ticket_links', {}).get(key, []) if node in index for parent in ancestors(index, node)})
    nodes = [dict(id=n['id'], parent=n.get('parent'), code=n.get('code', ''), label=n['label']) for n in index.values()]
    tags = defaultdict(list)
    for tag in data.question_tags:
        tags[tag.question_id].append(tag.category + ': ' + tag.tag)
    events = []
    own = [r for r in data.question_results if r.student_id == sid]
    own_assessments = {r.assessment_id for r in data.results if r.student_id == sid} | {aid for aid, student in data.memberships if student == sid}
    own_assessments |= {r.assessment_id for r in own}
    def linked(qid):
        return sorted({parent for node in data.question_curriculum.get(qid, []) if node in index for parent in ancestors(index, node)})
    for r in own:
        q, a = data.questions[r.question_id], data.assessments[r.assessment_id]
        events.append(dict(id='question:'+q.id, source='Assessment', date=a.date.isoformat(), title=a.name+' · '+q.number,
                           text=q.text, nodes=linked(q.id), skills=tags[q.id], status=r.status,
                           score=r.score if r.status == 'graded' else None, maximum=q.marks, assessment=a.id))
    for f in state.get('feedback', []):
        if f['student'] != sid or f['assessment'] not in own_assessments:
            continue
        # Whole-assessment feedback is not attributed to every topic covered by the test.
        events.append(dict(id='feedback:'+f['assessment'], source='Teacher feedback', date=f.get('published_at', ''),
                           title=data.assessments[f['assessment']].name, text=f['comment'], tasks=f['tasks'],
                           nodes=[], skills=[], status='Published', assessment=f['assessment']))
    for t in data.exit_tickets:
        if t.student_id == sid:
            events.append(dict(id='ticket:'+t.id, source='Exit ticket reflection', date=t.date,
                               title=data.assessments[t.assessment_id].name, text=t.prompt, response=t.response,
                               feedback=t.feedback, nodes=ticket_nodes('reflection:'+t.id), skills=[], status='Recorded', assessment=t.assessment_id))
    for a in [*data.revision_attempts, *state.get('attempts', [])]:
        q = data.questions.get(a['question'])
        if a['student'] != sid or not q or a['assessment'] not in own_assessments or q.assessment_id != a['assessment']:
            continue
        events.append(dict(id='retry:'+str(a.get('id', len(events))), source='Reviewed retry', date=a['day'],
                           title=data.assessments[a['assessment']].name+' · '+q.number, text=q.text,
                           feedback=a['note'], nodes=linked(q.id), skills=tags[q.id], status='Reviewed',
                           score=a['score'], maximum=a['maximum'], assessment=a['assessment']))
    for t in completed:
        # Only teacher-reviewed ticket links become topic evidence. Never infer
        # links from legacy labels or release answer keys into these histories.
        events.append(dict(id='interactive-ticket:'+t['ticket_id'], source='Exit ticket retake' if t.get('retake_of') else 'Exit ticket',
                           date=t['date'], title=t['title'], text=t['topic']+' / '+t['subtopic'], nodes=ticket_nodes('interactive:'+t['ticket_id']), skills=[],
                           status='Awaiting teacher review' if t['pending'] else 'Marked',
                           score=None if t['pending'] else t['score'], maximum=t['maximum'],
                           responses=[dict(prompt=a['question']['question'], answer=a['answer'], feedback=a['feedback'], score=a['score']) for a in t['answers']]))
    journal = curriculum.get('practice_journal')
    profile = str(PurePosixPath(journal).parent) if journal else None
    return dict(schema=1, learner='student'+sid, scope=sha256((settings.get('class_id', curriculum.get('id', 'legacy'))+':'+sid).encode()).hexdigest()[:24],
                label=curriculum.get('label', 'My learning'), generated=datetime.now(timezone.utc).isoformat(),
                nodes=nodes, events=sorted(events, key=lambda e:(e['date'], e['id']), reverse=True),
                resources=curriculum.get('resources', []), profile=profile, journal=journal,
                next=next_steps(data, sid),
                interventions=[{k:v for k,v in item.items() if k!='students'} for item in settings.get('interventions', []) if sid in item['students']],
                exams=[{k:v for k,v in item.items() if k!='students'} for item in settings.get('exams', []) if sid in item['students']])


def intervention_rows(data, node=None, skill=None, since=None, workspace=None):
    """Teacher-only evidence table; thresholds are suggestions, never fixed groups."""
    rows = []
    for sid, student in data.students.items():
        context = learner_context(data, sid, completed=completed_tickets(workspace, sid) if workspace else ())
        ticket_events = [e for e in context['events'] if e['source'] in {'Exit ticket', 'Exit ticket retake'} and (not node or node in e['nodes']) and (not since or e['date']>=since) and (not skill or skill in e['skills'])]
        events = [e for e in context['events'] if e['source']=='Assessment' and
                  (not node or node in e['nodes']) and (not skill or skill in e['skills']) and
                  (not since or e['date'] >= since)]
        graded = [e for e in events if e['status']=='graded' and e['score'] is not None and e['maximum']]
        maximum = sum(e['maximum'] for e in graded)
        percent = 100*sum(e['score'] for e in graded)/maximum if maximum else None
        suggestion = 'Check first' if len(graded)<2 else 'Foundation' if percent<50 else 'Independent practice' if percent<80 else 'Extension'
        latest_ticket = ticket_events[0] if ticket_events else None
        rows.append(dict(ticket=latest_ticket, id=sid, name=student.name, count=len(graded), percent=percent, suggestion=suggestion,
                         pending=len(events)-len(graded), latest=max((e['date'] for e in graded), default='No graded evidence')))
    return rows


def save_learning_plan(store, key, version, raw):
    doc = store.read(key)
    curriculum = doc['profile'].get('curriculum') or {}
    nodes = node_index(curriculum)
    kind = raw.get('kind')
    if kind not in {'intervention', 'exam'}:
        raise EntryError('Choose an intervention or an upcoming test.')
    selected = list(dict.fromkeys(raw.get('nodes', [])))
    students = list(dict.fromkeys(raw.get('students', [])))
    if not selected or any(n not in nodes for n in selected):
        raise EntryError('Select at least one topic from the class curriculum.')
    if not students or any(s not in {s['id'] for s in doc['students']} for s in students):
        raise EntryError('Select students from this class.')
    try:
        day = date.fromisoformat(raw.get('date', ''))
    except (ValueError, TypeError):
        raise EntryError('Enter a valid test or follow-up date.') from None
    if day < date.today():
        raise EntryError('Choose today or a future date for a new plan.')
    item = dict(id=identifier(), title=text(raw.get('title', ''), 'Title', 160, True), date=day.isoformat(),
                nodes=selected, students=students, instructions=text(raw.get('instructions', ''), 'Instructions', 4000),
                created=datetime.now(timezone.utc).isoformat())
    if kind=='intervention':
        role=raw.get('role')
        if role not in {'basic', 'practice', 'check'}:
            raise EntryError('Choose a learning activity type.')
        item.update(role=role, group=text(raw.get('group', ''), 'Temporary group', 100, True))
    keyname = 'interventions' if kind=='intervention' else 'exams'
    items=doc.setdefault('learning', {}).setdefault(keyname, [])
    if len(items)>=200:
        raise EntryError('This class already has 200 plans of this type. Remove an older plan first.')
    items.append(item)
    return store.save(doc, version)


def completed_tickets(workspace, sid):
    from .exit_store import TicketRepository
    from .exit_tickets import TicketService
    if not workspace.is_file():
        return []
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(workspace.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='et_submissions'").fetchone():
            return []
        if not db.execute('SELECT 1 FROM et_submissions WHERE student_id=? LIMIT 1', (sid,)).fetchone():
            return []
    return TicketService(TicketRepository(workspace)).student_home(sid)[1]
