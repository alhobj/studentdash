"""Teacher-only class setup, assessment editing and score entry."""
from datetime import date, datetime, timezone
import json
import secrets

from flask import abort, Blueprint, redirect, render_template, request, session, url_for

from .config import Config
from .curriculum import catalog, selected_curriculum, node_index, next_steps
from .entry import as_workbook
from .entry import ClassStore, EntryError, assessment, save_assessment, save_scores, score_rows, summary_label
from .import_routes import register_import_routes


def register_entry_routes(app, base_config):
    bp = Blueprint('entry', __name__)
    store = ClassStore(base_config.workbook.parent / 'entered_classes')
    register_import_routes(app, store)

    def active_config():
        key = request.values.get('class_key', session.get('entered_class'))
        if not key:
            return base_config
        return Config(store.path(key), base_config.output / ('class-' + key))

    @app.url_defaults
    def keep_class_context(endpoint, values):
        if endpoint in {'index', 'generate', 'feedback_editor', 'feedback_preview', 'save_draft',
                        'publish_feedback', 'record_attempt', 'preview', 'portability.transfer', 'portability.download'}:
            values.setdefault('class_key', request.values.get('class_key', session.get('entered_class', '')))

    def version():
        try:
            return int(request.form['version'])
        except (ValueError, KeyError):
            raise EntryError('Reload this page before saving; its version is missing.') from None

    def payload():
        try:
            return json.loads(request.form.get('payload', ''))
        except ValueError:
            raise EntryError('The form could not be read. Keep this page open and retry.') from None

    @bp.before_request
    def token():
        session.setdefault('csrf_token', secrets.token_urlsafe(32))

    @bp.errorhandler(EntryError)
    def invalid(error):
        return render_template('entry_error.html', error=str(error)), 400

    @bp.route('/classes', methods=['GET', 'POST'])
    def classes():
        error = None
        if request.method == 'POST':
            try:
                chosen = request.form.get('curriculum_id', '')
                curriculum = selected_curriculum(chosen) if chosen else None
                profile = dict(curriculum.get('profile', {'categories': curriculum.get('categories', {})}), curriculum=curriculum) if curriculum else None
                doc = store.create(request.form.get('name', ''), request.form.get('roster', ''), profile)
                session['entered_class'] = doc['id']
                return redirect(url_for('entry.class_page', key=doc['id']), code=303)
            except ValueError as exc:
                error = str(exc)
        return render_template('classes.html', classes=store.list(), curricula=catalog().values(), error=error), 400 if error else 200

    @bp.post('/classes/legacy')
    def legacy():
        session.pop('entered_class', None)
        return redirect(url_for('index'), code=303)

    @bp.route('/classes/<key>', methods=['GET', 'POST'])
    def class_page(key):
        doc = store.read(key)
        session['entered_class'] = key
        error = None
        if request.method == 'POST':
            try:
                store.add_students(key, request.form.get('roster', ''), version())
                return redirect(url_for('entry.class_page', key=key), code=303)
            except EntryError as exc:
                error = str(exc)
        return render_template('class_entry.html', doc=doc, error=error), 400 if error else 200

    @bp.route('/classes/<key>/curriculum', methods=['GET', 'POST'])
    def curriculum_review(key):
        doc = store.read(key)
        curriculum = doc['profile'].get('curriculum')
        if request.method == 'POST':
            if not curriculum:
                try:
                    doc['profile']['curriculum'] = selected_curriculum(request.form.get('curriculum_id', ''))
                except ValueError as exc:
                    raise EntryError(str(exc)) from exc
            else:
                allowed = node_index(curriculum)
                for item in doc['assessments']:
                    for q in item['questions']:
                        links = request.form.getlist('node-' + q['id'])
                        if any(k not in allowed for k in links):
                            raise EntryError('Choose links from the captured class curriculum.')
                        if links != q.get('curriculum_nodes', []):
                            q.setdefault('curriculum_history', []).append(dict(
                                previous=list(q.get('curriculum_nodes', [])), selected=links,
                                source='teacher', date=datetime.now(timezone.utc).isoformat()))
                        q['curriculum_nodes'] = list(dict.fromkeys(links))
                        q['curriculum_review'] = dict(status='reviewed', source='teacher')
            store.save(doc, version())
            return redirect(url_for('entry.curriculum_review', key=key), code=303)
        return render_template('curriculum_review.html', doc=doc, curriculum=curriculum,
                               nodes=node_index(curriculum or {}), curricula=catalog().values())

    @bp.get('/classes/<key>/students/<sid>/next')
    def student_next(key, sid):
        data = as_workbook(store.path(key))
        if sid not in data.students:
            abort(404)
        # Teacher preview is private; shared snapshots contain only this learner's plan.
        return render_template('next_steps.html', plan=next_steps(data, sid), resource_base='/practice/')

    @bp.route('/classes/<key>/assessments/new', methods=['GET', 'POST'])
    @bp.route('/classes/<key>/assessments/<aid>/edit', methods=['GET', 'POST'])
    def edit(key, aid=None):
        doc = store.read(key)
        session['entered_class'] = key
        item = assessment(doc, aid) if aid else dict(name='', date=date.today().isoformat(), description='',
            participants=[s['id'] for s in doc['students']], questions=[dict(number='1', marks='', text='', tags={}, curriculum='')])
        error = None
        form_version = doc['version']
        if request.method == 'POST':
            try:
                form_version = version()
                submitted = payload()
                if isinstance(submitted, dict):
                    item = submitted
                saved = save_assessment(store, key, aid, submitted, form_version)
                return redirect(url_for('entry.scores', key=key, aid=saved, saved='1'), code=303)
            except EntryError as exc:
                error = str(exc)
        return render_template('assessment_entry.html', doc=doc, item=item, aid=aid,
                               form_version=form_version, error=error), 400 if error else 200

    @bp.route('/classes/<key>/assessments/<aid>/scores', methods=['GET', 'POST'])
    def scores(key, aid):
        doc = store.read(key)
        session['entered_class'] = key
        item = assessment(doc, aid)
        students = score_rows(doc, item)
        rows = []
        for student in students:
            row = []
            for q in item['questions']:
                value = item['scores'].get(student['id'], {}).get(q['id'], {'status': 'pending'})
                row.append(f"{value['score']:g}" if value['status'] == 'graded' else
                           ('' if value['status'] == 'pending' else value['status'][0].upper()))
            rows.append(row)
        error, cells = None, {}
        form_version = doc['version']
        if request.method == 'POST':
            try:
                form_version = version()
                submitted = payload()
                if isinstance(submitted, list) and len(submitted) == len(students) and all(isinstance(r, list) and len(r) == len(item['questions']) for r in submitted):
                    rows = submitted
                save_scores(store, key, aid, submitted, form_version)
                return redirect(url_for('entry.scores', key=key, aid=aid, saved='1'), code=303)
            except EntryError as exc:
                error, cells = str(exc), exc.cells
        totals = [summary_label(item, s['id']) for s in students]
        return render_template('score_entry.html', doc=doc, item=item, students=students, rows=rows,
                               totals=totals, form_version=form_version, error=error, cells=cells), 400 if error else 200

    app.register_blueprint(bp)
    app.register_error_handler(EntryError, lambda e: (render_template('entry_error.html', error=str(e)), 400))
    return active_config
