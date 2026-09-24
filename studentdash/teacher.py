"""Private local teacher controls; no network integration or authentication."""
import secrets
import json
import hashlib
from datetime import date
import sqlite3

from flask import Flask, abort, redirect, render_template, request, send_from_directory, session, url_for

from .config import ROOT, Config
from .excel import WorkbookError, read_workbook
from .render import generate_dashboards, render_student
from .overview import build_overview
from .workspace import Workspace, WorkspaceError
from .freshness import stale_reasons
from .exit_routes import register_exit_routes, STUDENT_ENDPOINTS
from .entry_routes import register_entry_routes


def create_app(config=None):
    config = config or Config.from_env()
    app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=None)
    app.secret_key = secrets.token_hex(32)
    active_config = register_entry_routes(app, config)

    def workspace():
        return Workspace(active_config().workspace)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', MAX_CONTENT_LENGTH=2097152)

    @app.before_request
    def local_host_only():
        if request.endpoint == 'assessment_import.upload':
            request.max_content_length = 21 * 1024 * 1024
        # Reject foreign Host headers (including DNS-rebinding requests).
        if request.host.split(':', 1)[0] not in {'127.0.0.1', 'localhost'}:
            abort(400)
        if session.get('simulated_student'):
            if request.endpoint not in STUDENT_ENDPOINTS | {'exit_tickets.simulate_teacher'}:
                abort(403, description='Return to teacher simulation before opening teacher-only pages.')
        elif request.endpoint in STUDENT_ENDPOINTS:
            abort(403, description='Choose a fictional student from the teacher Exit Tickets area first.')
        if request.method == 'POST':
            token = session.get('csrf_token', '')
            if not token or not secrets.compare_digest(token, request.form.get('csrf_token', '')):
                abort(400, description='Invalid form token. Reload the teacher page and retry.')

    @app.errorhandler(413)
    def upload_too_large(error):
        return render_template('entry_error.html', error='The upload is too large. Use a PDF/DOCX of at most 20 MB or a shorter review form.'), 413

    @app.errorhandler(WorkspaceError)
    @app.errorhandler(WorkbookError)
    def invalid_workspace(error):
        return render_template('error.html', error=str(error)), 400

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        return render_template('error.html', error='The local teacher workspace could not be read or saved. Check file access and retry.'), 503

    @app.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    def status_page(error=None, status=200):
        data = None
        try:
            data = read_workbook(active_config().workbook)
        except WorkbookError as exc:
            error = str(exc)
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        names = [f'student{sid}.html' for sid in data.students
                 if (active_config().output / f'student{sid}.html').is_file()] if data else []
        message = session.pop('generation_message', None)
        generation = None
        stale = False
        reasons = []
        try:
            generation = json.loads((active_config().output / 'generation.json').read_text(encoding='utf-8'))
            if not isinstance(generation, dict):
                generation = None
            elif data:
                reasons = stale_reasons(active_config(), generation)
                stale = bool(reasons)
        except (OSError, ValueError):
            pass
        groups = {}
        for warning in data.warnings if data else []:
            group = ('Summary reconciliation' if warning.startswith('Reconciliation') else
                     'Question metadata' if warning.startswith(('Questions', 'Assessment ')) else
                     'Workbook and assessment totals')
            groups.setdefault(group, []).append(warning)
        assessment_id = request.args.get('assessment', '')
        class_name = request.args.get('class_name', '')
        classes = sorted({s.class_name for s in data.students.values() if s.class_name}) if data else []
        if data and ((assessment_id and assessment_id not in data.assessments)
                     or (class_name and class_name not in classes)):
            abort(400, description='Unknown assessment or class filter.')
        learners, items = build_overview(data, assessment_id, class_name) if data else ([], [])
        recorded_pages = generation.get('pages', {}) if generation else {}
        if not isinstance(recorded_pages, dict):
            recorded_pages = {}
        snapshots_to_refresh = []
        for sid in data.students if data else []:
            name = f'student{sid}.html'
            needs_refresh = stale or not generation or name not in names
            if not needs_refresh:
                expected = recorded_pages.get(name)
                try:
                    needs_refresh = not expected or hashlib.sha256((active_config().output / name).read_bytes()).hexdigest() != expected
                except OSError:
                    needs_refresh = True
            if needs_refresh:
                snapshots_to_refresh.append(name)
        return render_template('teacher.html', managed=active_config().workbook.suffix == '.sdclass', workbook_name=active_config().workbook.name, data=data,
                               error=error, names=names, message=message, warning_groups=groups,
                               generation=generation, stale=stale, learners=learners, items=items,
                               stale_reasons=reasons, snapshots_to_refresh=snapshots_to_refresh,
                               classes=classes, selected_class=class_name, selected_assessment=assessment_id), status

    @app.get('/')
    def index():
        if not request.values.get('class_key', session.get('entered_class')) and not config.workbook.exists():
            return redirect(url_for('entry.classes'))
        return status_page()

    @app.post('/generate')
    def generate():
        try:
            _, names = generate_dashboards(active_config(), include_examples=request.form.get('include_examples') == 'on')
        except (WorkbookError, OSError) as exc:
            return status_page(f'Generation failed: {exc}', 400)
        session['generation_message'] = f'Generated {len(names)} student dashboards successfully.'
        return redirect(url_for('index'), code=303)

    def learner_data(sid, aid=None):
        data = read_workbook(active_config().workbook)
        if sid not in data.students:
            abort(404)
        aids = {a for a, s in data.memberships if s == sid}
        aids.update(r.assessment_id for r in data.results if r.student_id == sid)
        if aid is not None and aid not in aids:
            abort(404)
        return data, sorted(aids, key=lambda a: (data.assessments[a].date, a))

    def form_version():
        try:
            return int(request.form['version'])
        except (ValueError, KeyError):
            raise WorkspaceError('Missing draft version. Reload the editor and retry.') from None

    @app.get('/feedback/<sid>')
    def feedback_editor(sid):
        data, aids = learner_data(sid)
        aid = request.args.get('assessment') or (aids[-1] if aids else None)
        if aid is not None and aid not in aids:
            abort(404)
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        record = workspace().feedback(sid, aid) if aid else None
        questions = [(data.questions[r.question_id], r.score) for r in data.question_results
                     if (r.student_id, r.assessment_id, r.status) == (sid, aid, 'graded')]
        from .analytics import build_dashboard
        view = build_dashboard(data, sid, False, aid, workspace().export_state())
        return render_template('feedback.html', learner=data.students[sid], data=data, aids=aids, aid=aid,
                               record=record, questions=questions, attempts=view.attempts,
                               today=date.today().isoformat(), message=session.pop('generation_message', None))

    @app.post('/feedback/<sid>/<aid>/draft')
    def save_draft(sid, aid):
        learner_data(sid, aid)
        workspace().save_draft(sid, aid, request.form.get('comment', ''), request.form.get('tasks', ''), form_version())
        session['generation_message'] = 'Draft saved. Preview it before publishing. Existing student snapshots are unchanged.'
        return redirect(url_for('feedback_editor', sid=sid, assessment=aid), code=303)

    @app.get('/feedback/<sid>/<aid>/preview')
    def feedback_preview(sid, aid):
        data, _ = learner_data(sid, aid)
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        record = workspace().feedback(sid, aid)
        state = workspace().export_state()
        state['feedback'] = [r for r in state['feedback'] if (r['student'], r['assessment']) != (sid, aid)]
        state['feedback'].append(dict(student=sid, assessment=aid, comment=record['comment'], tasks=record['tasks']))
        return render_student(data, sid, False, state, draft_preview=True, draft_record=record,
                              draft_assessment=data.assessments[aid].name,
                              publish_url=url_for('publish_feedback', sid=sid, aid=aid),
                              editor_url=url_for('feedback_editor', sid=sid, assessment=aid),
                              csrf_token=session['csrf_token'])

    @app.post('/feedback/<sid>/<aid>/publish')
    def publish_feedback(sid, aid):
        learner_data(sid, aid)
        workspace().publish(sid, aid, form_version())
        session['generation_message'] = 'Feedback published locally. Generate student dashboards to include it in the snapshots.'
        return redirect(url_for('feedback_editor', sid=sid, assessment=aid), code=303)

    @app.post('/feedback/<sid>/<aid>/attempts')
    def record_attempt(sid, aid):
        data, _ = learner_data(sid, aid)
        workspace().add_attempt(data, sid, aid, request.form.get('question', ''), request.form.get('day', ''),
                              request.form.get('score', ''), request.form.get('note', ''))
        session['generation_message'] = 'Revision attempt recorded. Original marks are unchanged. Regenerate snapshots to show the attempt.'
        return redirect(url_for('feedback_editor', sid=sid, assessment=aid), code=303)

    @app.get('/preview/<filename>')
    def preview(filename):
        try:
            data = read_workbook(active_config().workbook)
        except WorkbookError:
            abort(404)
        if filename not in {f'student{sid}.html' for sid in data.students}:
            abort(404)
        return send_from_directory(active_config().output, filename)

    register_exit_routes(app, config)
    return app
