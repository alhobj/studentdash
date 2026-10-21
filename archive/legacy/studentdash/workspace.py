"""Local teacher drafts and revision attempts, stored separately from Excel."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
import math
import sqlite3


class WorkspaceError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Workspace:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS feedback (
                    student TEXT, assessment TEXT, comment TEXT NOT NULL, tasks TEXT NOT NULL,
                    published_comment TEXT NOT NULL DEFAULT '', published_tasks TEXT NOT NULL DEFAULT '[]',
                    published_at TEXT, version INTEGER NOT NULL,
                    PRIMARY KEY (student, assessment)
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY, student TEXT NOT NULL, assessment TEXT NOT NULL,
                    question TEXT NOT NULL, day TEXT NOT NULL, score REAL NOT NULL,
                    maximum REAL NOT NULL, original REAL NOT NULL, note TEXT NOT NULL
                );
            ''')
            with db:
                yield db
        finally:
            db.close()

    def feedback(self, sid, aid):
        empty = dict(student=sid, assessment=aid, comment='', tasks=[], published_comment='',
                     published_tasks=[], published_at=None, version=0)
        if not self.path.exists():
            return empty
        with self.connection() as db:
            row = db.execute('SELECT * FROM feedback WHERE student=? AND assessment=?', (sid, aid)).fetchone()
        if not row:
            return empty
        result = dict(row)
        for key in ('tasks', 'published_tasks'):
            result[key] = json.loads(result[key])
        return result

    def save_draft(self, sid, aid, comment, tasks, version):
        comment = comment.strip()
        tasks = [line.strip() for line in tasks.splitlines() if line.strip()]
        if len(comment) > 4000 or len(tasks) > 10 or any(len(t) > 500 for t in tasks):
            raise WorkspaceError('Use at most 4,000 comment characters and 10 tasks of up to 500 characters each.')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT version FROM feedback WHERE student=? AND assessment=?', (sid, aid)).fetchone()
            if (current['version'] if current else 0) != version:
                raise WorkspaceError('This feedback changed in another tab. Reload before saving; your change was not applied.')
            db.execute('''INSERT INTO feedback (student, assessment, comment, tasks, version) VALUES (?, ?, ?, ?, 1)
                          ON CONFLICT(student, assessment) DO UPDATE SET comment=excluded.comment,
                          tasks=excluded.tasks, version=feedback.version+1''', (sid, aid, comment, json.dumps(tasks)))

    def publish(self, sid, aid, version):
        with self.connection() as db:
            result = db.execute('''UPDATE feedback SET published_comment=comment, published_tasks=tasks,
                                   published_at=?, version=version+1
                                   WHERE student=? AND assessment=? AND version=?''', (now(), sid, aid, version))
            if result.rowcount != 1:
                raise WorkspaceError('The draft changed or is missing. Preview the current draft before publishing.')

    def published(self):
        if not self.path.exists():
            return []
        with self.connection() as db:
            rows = db.execute('''SELECT student, assessment, published_comment AS comment,
                                 published_tasks AS tasks, published_at FROM feedback
                                 WHERE published_at IS NOT NULL ORDER BY student, assessment''').fetchall()
        return [dict(row, tasks=json.loads(row['tasks'])) for row in rows]

    def attempts(self):
        if not self.path.exists():
            return []
        with self.connection() as db:
            return [dict(row) for row in db.execute('SELECT * FROM attempts ORDER BY day, id')]

    def add_attempt(self, data, sid, aid, qid, day, score, note):
        original = next((r for r in data.question_results if (r.student_id, r.assessment_id, r.question_id)
                         == (sid, aid, qid) and r.status == 'graded'), None)
        if not original:
            raise WorkspaceError('Select a question with an original graded result for this learner and assessment.')
        try:
            parsed_day = date.fromisoformat(day)
            value = float(score)
        except (ValueError, TypeError):
            raise WorkspaceError('Use a valid date and numeric score.') from None
        if parsed_day < data.assessments[aid].date or parsed_day > date.today():
            raise WorkspaceError('The attempt date must be on or after the assessment and no later than today.')
        maximum = data.questions[qid].marks
        if not math.isfinite(value) or not 0 <= value <= maximum:
            raise WorkspaceError(f'Attempt score must be between 0 and {maximum:g}.')
        if len(note) > 2000:
            raise WorkspaceError('Keep the attempt note within 2,000 characters.')
        with self.connection() as db:
            db.execute('''INSERT INTO attempts (student, assessment, question, day, score, maximum, original, note)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (sid, aid, qid, day, value, maximum, original.score, note.strip()))

    def export_state(self):
        # Drafts deliberately do not enter this payload or its freshness fingerprint.
        return {'feedback': self.published(), 'attempts': self.attempts()}
