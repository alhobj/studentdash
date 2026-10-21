"""Loopback-only teacher website: import, review, persistent storage and private export."""
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, send_file, session, url_for

from . import classification_import as classifications
from .analytics import classification_status, dashboard
from .excel_import import import_results, read_grading_workbook, structural_changes
from .generator import fingerprint, generate, render_student, zip_pages
from .storage import ROOT, Store, ValidationError, course_id, curriculum_catalog, profile_catalog


def create_app(private_directory=None, generated_directory=None):
    private = Path(private_directory or os.environ.get('STUDENTDASH_PRIVATE', ROOT / 'data/private')).resolve()
    output = Path(generated_directory or os.environ.get('STUDENTDASH_GENERATED', ROOT / 'data/generated')).resolve()
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    previews = private / 'previews'
    previews.mkdir(exist_ok=True)
    key_path = private / '.session-key'
    if not key_path.exists():
        try:
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'w') as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app = Flask(__name__, template_folder=str(ROOT / 'app/templates'), static_folder=None)
    app.secret_key = key_path.read_text().strip()
    app.config.update(MAX_CONTENT_LENGTH=20 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')
    store = Store(private / 'studentdash.sqlite3')
    app.extensions['store'] = store

    @app.before_request
    def protect():
        if request.host.split(':')[0] not in {'127.0.0.1', 'localhost'}:
            abort(400)
        session.setdefault('csrf', secrets.token_urlsafe(32))
        if request.method == 'POST':
            if not secrets.compare_digest(session['csrf'], request.form.get('csrf', '')):
                abort(400, description='Invalid form token. Reload this page and retry.')

    @app.after_request
    def private_response(response):
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                                 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer',
                                 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"})
        return response

    def current():
        key = session.get('course')
        return store.read(key) if key and store.revision(key) else None

    def required():
        doc = current()
        if not doc:
            raise ValidationError('Import a grading workbook or select an existing class first.')
        return doc

    def page(template, **context):
        return render_template(template, courses=store.list(), current=current(), **context)

    @app.errorhandler(ValidationError)
    def invalid(error):
        return page('error.html', error=str(error)), 400

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        return page('error.html', error='The private database could not be read or saved. Check disk space and file access; keep backups.'), 503

    @app.errorhandler(413)
    def upload_too_large(error):
        return page('error.html', error='Upload exceeds the 20 MB limit.'), 413

    def upload():
        file = request.files.get('file')
        if not file or not file.filename:
            raise ValidationError('Select a file.')
        return file.read(), file.filename

    def save_preview(payload):
        for existing in previews.glob('*.json'):
            if time.time() - existing.stat().st_mtime > 3600:
                existing.unlink(missing_ok=True)
        token = uuid4().hex
        payload['created'] = time.time()
        (previews / (token + '.json')).write_text(json.dumps(payload), encoding='utf-8')
        session['previews'] = (session.get('previews', []) + [token])[-10:]
        return token

    def load_preview(token):
        if not re.fullmatch('[a-f0-9]{32}', token or '') or token not in session.get('previews', []):
            raise ValidationError('This preview is unavailable. Upload the file again.')
        path = previews / (token + '.json')
        if not path.is_file():
            raise ValidationError('This preview expired. Upload the file again.')
        payload = json.loads(path.read_text(encoding='utf-8'))
        if time.time() - payload['created'] > 3600:
            raise ValidationError('This preview expired. Upload the file again.')
        return payload

    @app.get('/')
    def home():
        return redirect(url_for('students' if current() else 'results'))

    @app.post('/select')
    def select():
        key = request.form['course_id']
        store.read(key)
        session['course'] = key
        return redirect(url_for('students'))

    @app.route('/results', methods=['GET', 'POST'])
    def results():
        if request.method == 'POST':
            content, filename = upload()
            if not filename.lower().endswith('.xlsx'):
                raise ValidationError('Choose an Excel .xlsx grading workbook.')
            key = course_id(request.form.get('course_id', '').strip())
            revision = store.revision(key)
            doc = store.read(key) if revision else None
            profiles, curricula = profile_catalog(), curriculum_catalog()
            if doc:
                profile, curriculum = doc['profile'], doc['curriculum']
            else:
                profile = profiles.get(request.form.get('profile', 'ib_chemistry'))
                curriculum = curricula.get(request.form.get('curriculum', 'chemistry-2025'))
                if profile is None or curriculum is None:
                    raise ValidationError('Select an available profile and curriculum.')
            incoming = read_grading_workbook(content)
            level = request.form.get('default_level', '')
            if level and level not in profile.get('levels', []):
                raise ValidationError('Default level is not in the selected profile.')
            if doc:
                level = doc.get('default_level', '')
            token = save_preview(dict(kind='results', key=key, revision=revision, incoming=incoming,
                                      profile=profile, curriculum=curriculum, default_level=level))
            return redirect(url_for('review', token=token))
        return page('results.html', profiles=profile_catalog(), curricula=curriculum_catalog())

    @app.route('/review/<token>', methods=['GET', 'POST'])
    def review(token):
        payload = load_preview(token)
        key = payload['key']
        if store.revision(key) != payload['revision']:
            raise ValidationError('This class changed after preview. Upload and preview again; no changes were saved.')
        doc = store.read(key) if payload['revision'] else None
        if payload['kind'] == 'results':
            changes = structural_changes(doc, payload['incoming'])
            if request.method == 'POST':
                mappings = {s['key']: request.form.get('map:' + s['key']) for s in payload['incoming']['students'] if request.form.get('map:' + s['key'])}
                # New students need explicit review on a reimport, to catch accidental renames.
                previous = {s['source_key'] for s in doc['students'].values()} if doc else set()
                unmatched = [s for s in payload['incoming']['students'] if s['key'] not in previous and s['key'] not in mappings]
                if doc and unmatched and request.form.get('new_students') != 'yes':
                    raise ValidationError('Map renamed students to existing IDs, or confirm that unmatched students are genuinely new.')
                imported = import_results(store, key, payload['incoming'], payload['revision'], payload['profile'], payload['curriculum'],
                                          confirm=request.form.get('confirm_changes') == 'yes', mappings=mappings,
                                          default_level=payload['default_level'])
                session['course'] = key
                (previews / (token + '.json')).unlink(missing_ok=True)
                return redirect(url_for('students'))
            previous = {s['source_key']: sid for sid, s in doc['students'].items()} if doc else {}
            return page('review_results.html', payload=payload, token=token, changes=changes, previous=previous, target=doc)
        proposal = classifications.preview(doc, payload['parsed'])
        if request.method == 'POST':
            classifications.import_classifications(store, key, payload['parsed'], payload['revision'],
                                                   replace=request.form.get('replace') == 'yes')
            session['course'] = key
            (previews / (token + '.json')).unlink(missing_ok=True)
            return redirect(url_for('classification_page'))
        return page('review_classifications.html', payload=payload, token=token, proposal=proposal)

    @app.route('/classifications', methods=['GET', 'POST'])
    def classification_page():
        doc = required()
        if request.method == 'POST':
            content, filename = upload()
            parsed = classifications.parse_file(content, filename)
            classifications.preview(doc, parsed)
            token = save_preview(dict(kind='classifications', key=doc['id'], revision=doc['revision'], parsed=parsed))
            return redirect(url_for('review', token=token))
        return page('classifications.html', prompt=classifications.prompt(doc), assessments=assessment_rows(doc))

    @app.get('/classification-template.xlsx')
    def classification_template():
        doc = required()
        return send_file(BytesIO(classifications.template(doc, scaffold=request.args.get('questions') == 'yes')),
                         as_attachment=True, download_name='classifications.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    @app.get('/classification-prompt.txt')
    def classification_prompt():
        return send_file(BytesIO(classifications.prompt(required()).encode()), as_attachment=True, download_name='classification-prompt.txt', mimetype='text/plain')

    def assessment_rows(doc):
        return [dict(id=aid, **classification_status(a, doc['profile'])) for aid, a in sorted(doc['assessments'].items()) if a.get('active', True)]

    @app.get('/students')
    def students():
        doc = required()
        rows = []
        for sid, student in doc['students'].items():
            if student.get('active', True):
                rows.append(dashboard(doc, sid))
        return page('students.html', students=rows, assessments=assessment_rows(doc))

    @app.get('/student/<sid>')
    def student_preview(sid):
        return render_student(required(), sid)

    @app.route('/dashboards', methods=['GET', 'POST'])
    def dashboards():
        doc = required()
        directory = output / doc['id']
        if request.method == 'POST':
            generate(doc, directory)
            return redirect(url_for('dashboards'))
        manifest = json.loads((directory / 'manifest.json').read_text()) if (directory / 'manifest.json').is_file() else None
        return page('dashboards.html', manifest=manifest, stale=not manifest or manifest.get('fingerprint') != fingerprint(doc))

    @app.get('/generated/<sid>')
    def generated(sid):
        doc = required()
        if sid not in doc['students'] or not doc['students'][sid].get('active', True):
            abort(404)
        path = output / doc['id'] / ('student' + sid + '.html')
        if not path.is_file():
            raise ValidationError('Generate dashboards first.')
        return send_file(path, mimetype='text/html')

    @app.get('/dashboards.zip')
    def dashboards_zip():
        doc = required()
        return send_file(BytesIO(zip_pages(doc)), as_attachment=True, download_name=doc['id'] + '-dashboards.zip', mimetype='application/zip')

    @app.route('/backup', methods=['GET', 'POST'])
    def backup():
        if request.method == 'POST':
            destination = private / 'backups' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid4().hex[:8] + '.sqlite3')
            store.backup(destination)
            return send_file(destination, as_attachment=True, download_name='studentdash-' + destination.name, mimetype='application/octet-stream')
        return page('backup.html', history=store.history(required()['id']) if current() else [])

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
