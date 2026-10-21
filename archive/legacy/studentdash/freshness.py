"""Fingerprints of inputs that can affect published student snapshots."""
import hashlib
import json
import sqlite3
from contextlib import closing

from .config import ROOT
from .workspace import Workspace


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprints(config, state=None):
    state = state if state is not None else Workspace(config.workspace).export_state()
    sources = [ROOT / 'templates' / name for name in ('student.html', 'style.html', 'student_night.html', 'student_navigation.js', 'next_plan.html')]
    sources += [ROOT / 'studentdash' / name for name in ('analytics.py', 'models.py', 'excel.py', 'question_data.py', 'render.py', 'workspace.py', 'examples.py', 'freshness.py', 'entry.py', 'classification.py', 'curriculum.py', 'learning.py')]
    sources += [ROOT / 'profiles' / 'ib_chemistry.json']
    sources += sorted((ROOT / 'resources').rglob('*.html'))
    sources += sorted((ROOT / 'resources').rglob('*.js'))
    sources += sorted((ROOT / 'resources').rglob('*.json'))
    sources += sorted((ROOT / 'resources').rglob('*.css'))
    templates = b''.join(p.name.encode() + b'\0' + p.read_bytes() for p in sources)
    tickets = {}
    if config.workspace.is_file():
        with closing(sqlite3.connect(config.workspace.resolve().as_uri()+'?mode=ro', uri=True)) as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table in ('et_tickets', 'et_questions', 'et_assignments', 'et_submissions', 'et_answers', 'et_retakes', 'et_release'):
                if table in tables:
                    rows = db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                    if rows:
                        tickets[table] = rows
    return {'exit_tickets': digest(json.dumps(tickets, sort_keys=True).encode()), 'workbook': digest(config.workbook.read_bytes()),
            'feedback': digest(json.dumps(state['feedback'], sort_keys=True).encode()),
            'attempts': digest(json.dumps(state['attempts'], sort_keys=True).encode()),
            'templates': digest(templates)}


def stale_reasons(config, manifest, state=None):
    previous = manifest.get('fingerprints', {}) if manifest else {}
    current = fingerprints(config, state)
    labels = {'exit_tickets': 'Exit-ticket records have changed.', 'workbook': 'Saved assessment data has changed since generation.' if config.workbook.suffix == '.sdclass' else 'The workbook has changed since generation.',
              'feedback': 'Published teacher feedback has changed.',
              'attempts': 'Revision-attempt history has changed.',
              'templates': 'Student templates or rendering code have changed.'}
    if not isinstance(previous, dict) or not previous:
        return ['Snapshot freshness is unknown. Generate snapshots to record all source versions.']
    return [labels[key] for key in current if previous.get(key) != current[key]]
