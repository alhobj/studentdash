"""Versioned SQLite course documents; scores and reviewed classifications stay separate."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 1


class ValidationError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def course_id(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', value or ''):
        raise ValidationError('ClassID must contain 1–100 letters, digits, underscores or hyphens.')
    return value


def profile_catalog():
    return {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (ROOT / 'profiles').glob('*.json')}


def curriculum_catalog():
    return {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (ROOT / 'curricula').glob('*.json')}


class Store:
    def __init__(self, path=None):
        self.path = Path(path or ROOT / 'data/private/studentdash.sqlite3').resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (schema_version INTEGER NOT NULL);
                INSERT INTO metadata SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM metadata);
                CREATE TABLE IF NOT EXISTS courses
                  (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS history
                  (id INTEGER PRIMARY KEY, course_id TEXT NOT NULL, kind TEXT NOT NULL,
                   created TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sequence (id INTEGER PRIMARY KEY, next_student INTEGER);
                INSERT OR IGNORE INTO sequence VALUES (1, 1001);
            ''')
            if db.execute('SELECT schema_version FROM metadata').fetchone()[0] != SCHEMA:
                raise ValidationError('Unsupported database version. Keep a backup and use a compatible Studentdash version.')

    def connect(self):
        return closing_connection(self.path)

    def list(self):
        with self.connect() as db:
            return [dict(json.loads(body), revision=revision) for revision, body in
                    db.execute('SELECT revision, body FROM courses ORDER BY id')]

    def read(self, key):
        with self.connect() as db:
            row = db.execute('SELECT revision, body FROM courses WHERE id=?', (key,)).fetchone()
        if row is None:
            raise ValidationError('Unknown class. Import its grading workbook first.')
        return dict(json.loads(row[1]), revision=row[0])

    def revision(self, key):
        with self.connect() as db:
            row = db.execute('SELECT revision FROM courses WHERE id=?', (key,)).fetchone()
        return row[0] if row else 0

    def commit(self, key, revision, update, kind, detail):
        """Compare-and-swap the previewed document and its audit trail in one transaction."""
        course_id(key)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT revision, body FROM courses WHERE id=?', (key,)).fetchone()
            if (row[0] if row else 0) != revision:
                raise ValidationError('The class changed after preview. Upload and preview again; nothing was saved.')
            doc = json.loads(row[1]) if row else None
            doc = update(doc, db)
            doc['updated'] = now()
            db.execute('INSERT INTO courses VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision, body=excluded.body',
                       (key, revision + 1, json.dumps(doc, ensure_ascii=False)))
            db.execute('INSERT INTO history(course_id, kind, created, body) VALUES (?, ?, ?, ?)',
                       (key, kind, now(), json.dumps(detail, ensure_ascii=False)))
        return self.read(key)

    def history(self, key):
        with self.connect() as db:
            return [dict(id=i, kind=k, created=t, detail=json.loads(b)) for i, k, t, b in
                    db.execute('SELECT id, kind, created, body FROM history WHERE course_id=? ORDER BY id DESC', (key,))]

    def backup(self, destination):
        destination = Path(destination)
        if destination.exists():
            raise ValidationError('Choose a new backup filename; existing files are never overwritten.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(self.path)) as source, closing(sqlite3.connect(destination)) as target:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValidationError('Backup integrity check failed.')
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return destination

    @classmethod
    def restore(cls, source, destination):
        """Restore into a NEW database only; do not replace a running teacher database."""
        source, destination = Path(source), Path(destination)
        if destination.exists():
            raise ValidationError('Restore requires a new destination. Existing data is never replaced.')
        with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValidationError('Backup integrity check failed.')
            try:
                if db.execute('SELECT schema_version FROM metadata').fetchone()[0] != SCHEMA:
                    raise ValidationError('Unsupported backup version.')
                for key, revision, body in db.execute('SELECT id, revision, body FROM courses'):
                    course_id(key)
                    document = json.loads(body)
                    if document.get('id') != key or not isinstance(document.get('students'), dict) or not isinstance(document.get('assessments'), dict):
                        raise ValidationError('Invalid course document in backup.')
                    if any(not re.fullmatch(r'[1-9][0-9]*', sid) for sid in document['students']):
                        raise ValidationError('Invalid internal StudentID in backup.')
                db.execute('SELECT next_student FROM sequence').fetchone()
                db.execute('SELECT body FROM history LIMIT 1').fetchone()
            except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
                raise ValidationError('Not a valid Studentdash backup.') from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with closing(sqlite3.connect(destination)) as target:
                    db.backup(target)
            except Exception:
                destination.unlink(missing_ok=True)
                raise
        return cls(destination)


class closing_connection:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.execute('PRAGMA foreign_keys=ON')
        return self.db

    def __exit__(self, kind, value, traceback):
        try:
            if kind is None:
                self.db.commit()
            else:
                self.db.rollback()
        finally:
            self.db.close()
