"""Fingerprints of inputs that can affect published student snapshots."""
import hashlib
import json

from .config import ROOT
from .workspace import Workspace


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprints(config, state=None):
    state = state if state is not None else Workspace(config.workspace).export_state()
    sources = [ROOT / 'templates' / name for name in ('student.html', 'style.html')]
    sources += [ROOT / 'studentdash' / name for name in ('analytics.py', 'models.py', 'excel.py', 'question_data.py', 'render.py', 'workspace.py', 'examples.py', 'freshness.py')]
    templates = b''.join(p.name.encode() + b'\0' + p.read_bytes() for p in sources)
    return {'workbook': digest(config.workbook.read_bytes()),
            'feedback': digest(json.dumps(state['feedback'], sort_keys=True).encode()),
            'attempts': digest(json.dumps(state['attempts'], sort_keys=True).encode()),
            'templates': digest(templates)}


def stale_reasons(config, manifest, state=None):
    previous = manifest.get('fingerprints', {}) if manifest else {}
    current = fingerprints(config, state)
    labels = {'workbook': 'The workbook has changed since generation.',
              'feedback': 'Published teacher feedback has changed.',
              'attempts': 'Revision-attempt history has changed.',
              'templates': 'Student templates or rendering code have changed.'}
    if not isinstance(previous, dict) or not previous:
        return ['Snapshot freshness is unknown. Generate snapshots to record all source versions.']
    return [labels[key] for key in current if previous.get(key) != current[key]]
