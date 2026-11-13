"""Teacher-reviewed adapter from saved classes to a local curriculum viewer."""
from pathlib import Path
import json
import hashlib
import secrets
import os
import tempfile

from flask import Blueprint, render_template, request, session
from .entry import as_workbook
from .local_tree import export_package, read_json
from .render import render_student
from .config import Config
from .workspace import Workspace
from .classification_export import learner_classifications, curriculum_labels, category_labels


def question_signature(question):
    fields = {k: question.get(k) for k in ('curriculum_nodes', 'curriculum_review', 'scope', 'text')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def choices(doc, registry):
    """Only exact stable IDs are reused; broad links never become leaf evidence."""
    ids = {node['id'] for node in registry['nodes']}
    saved = doc.get('local_tree', {}).get('mapping', {})
    rows = []
    for assessment in doc['assessments']:
        for question in assessment['questions']:
            links = question.get('curriculum_nodes', [])
            candidates = list(dict.fromkeys(links))
            direct = (candidates[0] if len(candidates) == 1 and candidates[0] in ids
                      and question.get('curriculum_review', {}).get('status') == 'reviewed' else '')
            selected = saved.get(question['id'], direct)
            if question['id'] in saved and doc['local_tree'].get('signatures', {}).get(question['id']) != question_signature(question):
                selected = ''
            if selected not in ids:
                selected = ''
            rows.append(dict(question=question, assessment=assessment, selected=selected,
                             links=links, curriculum=curriculum_labels(doc, links)))
    return rows


def atomic_text(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Linked destination files are not supported.')
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(content)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def register_tree_export(app, store, base_config):
    bp = Blueprint('tree_export', __name__)

    @bp.route('/classes/<key>/chemistree', methods=['GET', 'POST'])
    def page(key):
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        doc = store.read(key)
        session['entered_class'] = key
        settings = doc.get('local_tree', {})
        viewer = request.form.get('viewer', settings.get('viewer', ''))
        destination = request.form.get('destination', '')
        student_id = request.form.get('student_id', '')
        message, error, registry, rows = '', None, None, []
        try:
            if viewer:
                registry = read_json(Path(viewer).expanduser() / 'curriculum.json')
                if registry.get('mapId') != 'chemistree' or registry.get('mapVersion') != '2.0':
                    raise ValueError('Choose a Chemistree 2.0 local-package folder.')
                rows = choices(doc, registry)
            if request.method == 'POST' and request.form.get('action') in {'save', 'export'}:
                if not registry:
                    raise ValueError('Load a built local-package folder first.')
                mapping = {r['question']['id']: request.form.get('node-' + r['question']['id'], '') for r in rows}
                ids = {n['id'] for n in registry['nodes']}
                if any(n and n not in ids for n in mapping.values()):
                    raise ValueError('Choose listed nodes only.')
                # Capture exclusions too, so a later visit never silently restores a suggestion.
                settings = dict(viewer=str(Path(viewer).expanduser().resolve()), mapping=mapping,
                                destinations=dict(settings.get('destinations', {})),
                                signatures={r['question']['id']: question_signature(r['question']) for r in rows})
                if request.form['action'] == 'export':
                    if student_id not in {s['id'] for s in doc['students']}:
                        raise ValueError('Choose one student.')
                    if not destination.strip() or not Path(destination).expanduser().is_absolute():
                        raise ValueError('Enter the full path to this student’s private local or OneDrive folder.')
                    target = Path(destination).expanduser().resolve()
                    private = store.directory.resolve()
                    if target == private or target in private.parents or private in target.parents:
                        raise ValueError('Choose a student folder outside the private class-data directory.')
                    # Render before filesystem export; it receives this learner only.
                    data = as_workbook(store.path(key))
                    config = Config(store.path(key), base_config.output / ('class-' + key))
                    state = Workspace(config.workspace).export_state()
                    classifications = learner_classifications(doc, data, student_id)
                    html = render_student(data, student_id, False, state, classification_export=classifications)
                    html = html.replace('<main>', '<main><p><a href="http://127.0.0.1:8765/">Open Chemistree</a> · Keep the Start window open while using the tree.</p>', 1)
                    # Save configuration with the same version check as score entry before exporting.
                    settings['destinations'][student_id] = str(target)
                    doc['local_tree'] = settings
                    store.save(doc, int(request.form.get('version', '0')))
                    result = export_package(data, student_id, {q: n for q, n in mapping.items() if n}, viewer, target)
                    classifications['packageId'] = read_json(target / 'package.json')['packageId']
                    atomic_text(target / 'classifications.json', json.dumps(classifications, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
                    atomic_text(target / 'studentdash.html', html)
                    atomic_text(target / 'Start Studentdash.cmd', '@echo off\r\nstart "" "%~dp0studentdash.html"\r\ncall "%~dp0Start.cmd"\r\n')
                    message = f'Exported one student: {len(classifications["questions"])} question parts with their saved classifications; {result["questions"]} graded parts also assigned to individual node rings. Open Start Studentdash.cmd in the student folder.'
                else:
                    doc['local_tree'] = settings
                    store.save(doc, int(request.form.get('version', '0')))
                    message = 'Node assignments saved. Scores and existing classifications are unchanged.'
                doc = store.read(key)
                settings = doc['local_tree']
                rows = choices(doc, registry)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            error = str(exc)
            doc = store.read(key)
        return render_template('tree_export.html', doc=doc, viewer=viewer, registry=registry,
                               rows=rows, settings=settings, destination=destination, category_labels=category_labels(doc),
                               student_id=student_id, message=message, error=error), 400 if error else 200

    app.register_blueprint(bp)
