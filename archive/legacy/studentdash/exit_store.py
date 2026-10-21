"""SQLite adapter for local tickets. Definitions freeze after the first submission."""
from contextlib import contextmanager
import json
from uuid import uuid4

from .workspace import Workspace, now
from .exit_schema import TicketError, automatic_score, validate_answers


SCHEMA = '''
CREATE TABLE IF NOT EXISTS et_release (
 ticket_id TEXT PRIMARY KEY REFERENCES et_tickets(id), mode TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS et_retakes (
 ticket_id TEXT PRIMARY KEY REFERENCES et_tickets(id), parent_id TEXT NOT NULL REFERENCES et_tickets(id),
 student_id TEXT NOT NULL, UNIQUE(parent_id,student_id));
CREATE TABLE IF NOT EXISTS et_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT NOT NULL REFERENCES et_tickets(id),
 created_at TEXT NOT NULL, action TEXT NOT NULL, student_id TEXT, question_id TEXT,
 before_json TEXT NOT NULL, after_json TEXT NOT NULL, reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS et_tickets (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL,
 subtopic TEXT NOT NULL, created_at TEXT NOT NULL, published_at TEXT,
 status TEXT NOT NULL CHECK(status IN ('draft','published','unpublished')),
 allow_answer_review INTEGER NOT NULL, version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS et_questions (
 ticket_id TEXT NOT NULL, id TEXT NOT NULL, position INTEGER NOT NULL, definition TEXT NOT NULL,
 PRIMARY KEY(ticket_id,id), FOREIGN KEY(ticket_id) REFERENCES et_tickets(id));
CREATE TABLE IF NOT EXISTS et_assignments (
 ticket_id TEXT NOT NULL, student_id TEXT NOT NULL, PRIMARY KEY(ticket_id,student_id),
 FOREIGN KEY(ticket_id) REFERENCES et_tickets(id));
CREATE TABLE IF NOT EXISTS et_submissions (
 id TEXT PRIMARY KEY, ticket_id TEXT NOT NULL, student_id TEXT NOT NULL, submitted_at TEXT NOT NULL,
 UNIQUE(ticket_id,student_id), FOREIGN KEY(ticket_id,student_id) REFERENCES et_assignments(ticket_id,student_id));
CREATE TABLE IF NOT EXISTS et_answers (
 submission_id TEXT NOT NULL, question_id TEXT NOT NULL, value TEXT NOT NULL,
 auto_score REAL, teacher_score REAL, feedback TEXT NOT NULL DEFAULT '', reviewed_at TEXT,
 version INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(submission_id,question_id),
 FOREIGN KEY(submission_id) REFERENCES et_submissions(id));
'''


class TicketRepository:
    def __init__(self, path):
        self.workspace = Workspace(path)

    @contextmanager
    def connection(self, write=False):
        with self.workspace.connection() as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.executescript(SCHEMA)
            if write:
                db.execute('BEGIN IMMEDIATE')
            yield db

    def _ticket(self, db, ticket_id):
        row = db.execute('SELECT * FROM et_tickets WHERE id=?', (ticket_id,)).fetchone()
        if row is None:
            raise KeyError('Ticket not found')
        ticket = dict(row)
        ticket['allow_answer_review'] = bool(ticket['allow_answer_review'])
        policy = db.execute('SELECT mode FROM et_release WHERE ticket_id=?', (ticket_id,)).fetchone()
        ticket['release_mode'] = policy[0] if policy else ('immediate' if ticket['allow_answer_review'] else 'hidden')
        parent = db.execute('SELECT parent_id FROM et_retakes WHERE ticket_id=?', (ticket_id,)).fetchone()
        ticket['retake_of'] = parent[0] if parent else None
        ticket['questions'] = [json.loads(q['definition']) for q in db.execute(
            'SELECT definition FROM et_questions WHERE ticket_id=? ORDER BY position', (ticket_id,))]
        ticket['assignments'] = [r[0] for r in db.execute(
            'SELECT student_id FROM et_assignments WHERE ticket_id=? ORDER BY student_id', (ticket_id,))]
        ticket['submitted'] = db.execute('SELECT COUNT(*) FROM et_submissions WHERE ticket_id=?', (ticket_id,)).fetchone()[0]
        return ticket

    def get(self, ticket_id):
        with self.connection() as db:
            return self._ticket(db, ticket_id)

    def list(self):
        with self.connection() as db:
            return [self._ticket(db, r[0]) for r in db.execute('SELECT id FROM et_tickets ORDER BY created_at DESC, id').fetchall()]

    def save(self, definition, assignments, ticket_id=None, version=None):
        with self.connection(True) as db:
            if ticket_id:
                current = self._ticket(db, ticket_id)
                if current['version'] != version:
                    raise TicketError('This ticket changed in another tab. Reload before saving.')
                if current['retake_of']:
                    raise TicketError('Retake questions and assignment are fixed. Create a new original ticket for different questions.')
                if current['status'] == 'published' or current['submitted']:
                    raise TicketError('Unpublish before editing. Tickets with submissions are frozen; create a new ticket instead.')
                db.execute('DELETE FROM et_questions WHERE ticket_id=?', (ticket_id,))
                db.execute('DELETE FROM et_assignments WHERE ticket_id=?', (ticket_id,))
                db.execute('''UPDATE et_tickets SET title=?, subject=?, topic=?, subtopic=?, allow_answer_review=?,
                              version=version+1 WHERE id=?''',
                           (*[definition[k] for k in ('title', 'subject', 'topic', 'subtopic', 'allow_answer_review')], ticket_id))
            else:
                ticket_id = uuid4().hex
                db.execute('''INSERT INTO et_tickets VALUES (?, ?, ?, ?, ?, ?, NULL, 'draft', ?, 1)''',
                           (ticket_id, *[definition[k] for k in ('title', 'subject', 'topic', 'subtopic')], now(), definition['allow_answer_review']))
            for position, q in enumerate(definition['questions']):
                db.execute('INSERT INTO et_questions VALUES (?, ?, ?, ?)', (ticket_id, q['id'], position, json.dumps(q)))
            db.executemany('INSERT INTO et_assignments VALUES (?, ?)', [(ticket_id, sid) for sid in sorted(set(assignments))])
        return ticket_id

    def change_status(self, ticket_id, version, status):
        if status not in {'published', 'unpublished'}:
            raise TicketError('Unsupported publication action.')
        with self.connection(True) as db:
            ticket = self._ticket(db, ticket_id)
            if ticket['version'] != version:
                raise TicketError('This ticket changed. Reload its preview before publishing or unpublishing.')
            if status == 'published' and not ticket['assignments']:
                raise TicketError('Assign at least one student before publishing.')
            if status == 'unpublished' and ticket['status'] == 'draft':
                raise TicketError('This ticket is still a draft.')
            db.execute('UPDATE et_tickets SET status=?, published_at=?, version=version+1 WHERE id=?',
                       (status, now() if status == 'published' else ticket['published_at'], ticket_id))
            self._audit(db, ticket_id, 'publication', ticket['status'], status, 'Local teacher publication control')

    def _submission(self, db, ticket_id, sid):
        row = db.execute('SELECT * FROM et_submissions WHERE ticket_id=? AND student_id=?', (ticket_id, sid)).fetchone()
        if not row:
            return None
        result = dict(row)
        result['answers'] = [dict(a, value=json.loads(a['value'])) for a in db.execute(
            'SELECT * FROM et_answers WHERE submission_id=? ORDER BY question_id', (row['id'],))]
        return result

    def submission(self, ticket_id, sid):
        with self.connection() as db:
            return self._submission(db, ticket_id, sid)

    def submissions(self, ticket_id):
        with self.connection() as db:
            students = [r[0] for r in db.execute('SELECT student_id FROM et_submissions WHERE ticket_id=? ORDER BY submitted_at', (ticket_id,))]
            return [self._submission(db, ticket_id, sid) for sid in students]

    def submit(self, ticket_id, sid, version, values):
        # Publication check and unique insert share one write transaction, including unpublish races.
        with self.connection(True) as db:
            ticket = self._ticket(db, ticket_id)
            if sid not in ticket['assignments'] or ticket['status'] != 'published':
                raise TicketError('This ticket is not available for submission.')
            previous = self._submission(db, ticket_id, sid)
            if previous:
                return previous['id']  # An accidental retry cannot overwrite the first submission.
            if ticket['version'] != version:
                raise TicketError('This ticket changed while the form was open. Reopen it before submitting.')
            values = validate_answers(ticket['questions'], values)
            submission_id = uuid4().hex
            db.execute('INSERT INTO et_submissions VALUES (?, ?, ?, ?)', (submission_id, ticket_id, sid, now()))
            for q in ticket['questions']:
                value = values[q['id']]
                db.execute('''INSERT INTO et_answers (submission_id,question_id,value,auto_score)
                              VALUES (?, ?, ?, ?)''', (submission_id, q['id'], json.dumps(value), automatic_score(q, value)))
            return submission_id

    def review(self, ticket_id, sid, qid, score, feedback, version, reason=''):
        with self.connection(True) as db:
            ticket = self._ticket(db, ticket_id)
            question = next((q for q in ticket['questions'] if q['id'] == qid), None)
            if not question:
                raise TicketError('Question not found.')
            try:
                from math import isfinite
                score = float(score)
                valid = isfinite(score) and 0 <= score <= question['marks']
            except (ValueError, TypeError):
                valid = False
            if not valid:
                raise TicketError(f'Enter a score from 0 to {question["marks"]:g}, including partial marks.')
            if len(feedback) > 2000:
                raise TicketError('Keep student-visible feedback within 2,000 characters.')
            submission = self._submission(db, ticket_id, sid)
            if not submission:
                raise KeyError('Submission not found')
            previous = next(a for a in submission['answers'] if a['question_id'] == qid)
            if previous['teacher_score'] is not None or not question['manual_marking']:
                if not reason.strip():
                    raise TicketError('Explain the correction or automatic-mark override.')
            if len(reason) > 1000:
                raise TicketError('Keep the audit reason within 1,000 characters.')
            result = db.execute('''UPDATE et_answers SET teacher_score=?, feedback=?, reviewed_at=?, version=version+1
                                   WHERE submission_id=? AND question_id=? AND version=?''',
                                (score, feedback.strip(), now(), submission['id'], qid, version))
            if result.rowcount != 1:
                raise TicketError('This response was reviewed in another tab. Reload before saving.')
            self._audit(db, ticket_id, 'review', previous,
                        dict(teacher_score=score, feedback=feedback.strip()), reason.strip(), sid, qid)

    def _audit(self, db, tid, action, before, after, reason, sid=None, qid=None):
        db.execute('''INSERT INTO et_audit
            (ticket_id,created_at,action,student_id,question_id,before_json,after_json,reason)
            VALUES (?,?,?,?,?,?,?,?)''',
            (tid, now(), action, sid, qid, json.dumps(before), json.dumps(after), reason))

    def audit(self, tid):
        with self.connection() as db:
            self._ticket(db, tid)
            return [dict(r, before=json.loads(r['before_json']), after=json.loads(r['after_json']))
                    for r in db.execute('SELECT * FROM et_audit WHERE ticket_id=? ORDER BY id DESC', (tid,))]

    def set_release(self, tid, version, mode, reason):
        if mode not in {'hidden', 'immediate', 'marked', 'closed'}:
            raise TicketError('Choose a supported answer-release policy.')
        if not reason.strip() or len(reason) > 1000:
            raise TicketError('Give an audit reason of 1 to 1,000 characters.')
        with self.connection(True) as db:
            ticket = self._ticket(db, tid)
            if ticket['version'] != version:
                raise TicketError('This ticket changed. Reload before changing answer release.')
            db.execute('INSERT OR REPLACE INTO et_release VALUES (?,?)', (tid, mode))
            db.execute('UPDATE et_tickets SET version=version+1 WHERE id=?', (tid,))
            self._audit(db, tid, 'answer release', ticket['release_mode'], mode, reason.strip())

    def create_retake(self, tid, sid, version, reason):
        if not reason.strip() or len(reason) > 1000:
            raise TicketError('Give an audit reason of 1 to 1,000 characters.')
        with self.connection(True) as db:
            ticket = self._ticket(db, tid)
            if ticket['version'] != version:
                raise TicketError('This ticket changed. Reload before assigning a retake.')
            if not self._submission(db, tid, sid):
                raise TicketError('A retake requires an original submission.')
            existing = db.execute('SELECT ticket_id FROM et_retakes WHERE parent_id=? AND student_id=?', (tid, sid)).fetchone()
            if existing:
                return existing[0]
            child = uuid4().hex
            db.execute("INSERT INTO et_tickets VALUES (?,?,?,?,?,?,NULL,'draft',0,1)",
                       (child, ('Retake: ' + ticket['title'])[:200], ticket['subject'], ticket['topic'], ticket['subtopic'], now()))
            db.execute('INSERT INTO et_questions SELECT ?,id,position,definition FROM et_questions WHERE ticket_id=?', (child, tid))
            db.execute('INSERT INTO et_assignments VALUES (?,?)', (child, sid))
            db.execute('INSERT INTO et_retakes VALUES (?,?,?)', (child, tid, sid))
            self._audit(db, tid, 'retake created', None, dict(ticket_id=child), reason.strip(), sid)
            return child
