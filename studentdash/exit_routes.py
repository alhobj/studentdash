"""Local development simulation and exit-ticket HTTP adapter."""
import json
import secrets

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from .analytics import build_dashboard
from .excel import read_workbook
from .exit_schema import TicketError
from .exit_store import TicketRepository
from .exit_tickets import TicketService, definition, public_ticket, progress_rows
from .render import render_student
from .workspace import Workspace


STUDENT_ENDPOINTS = {'exit_tickets.student_home', 'exit_tickets.student_ticket', 'exit_tickets.student_submit',
                     'exit_tickets.student_history', 'exit_tickets.student_progress'}


def register_exit_routes(app, config):
    bp = Blueprint('exit_tickets', __name__)
    repo = TicketRepository(config.workspace)
    service = TicketService(repo)

    def roster():
        return read_workbook(config.workbook)

    def version():
        try:
            return int(request.form['version'])
        except (ValueError, KeyError):
            raise TicketError('Reload this page before continuing; its version is missing.') from None

    def student(student_key):
        sid = session.get('simulated_student')
        if not sid or student_key != 'student' + sid:
            abort(403, description='This URL does not match the current fictional student session.')
        data = roster()
        if sid not in data.students:
            abort(404)
        return sid, data

    @bp.before_request
    def token():
        session.setdefault('csrf_token', secrets.token_urlsafe(32))

    @bp.errorhandler(KeyError)
    def missing(_):
        context = {'student_key': 'student' + session['simulated_student']} if session.get('simulated_student') else {}
        return render_template('exit_unavailable.html', **context), 404

    @bp.get('/exit-tickets')
    def list_tickets():
        return render_template('exit_list.html', tickets=repo.list(), students=roster().students,
                               message=session.pop('generation_message', None))

    def editor_page(raw='', ticket=None, error=None, audience=None, status=200):
        data = roster()
        return render_template('exit_editor.html', raw=raw, ticket=ticket, error=error,
                               students=data.students, classes=sorted({s.class_name for s in data.students.values()}),
                               audience=audience if audience is not None else ['all']), status

    @bp.get('/exit-tickets/new')
    def new_ticket():
        return editor_page()

    @bp.post('/exit-tickets/import')
    def import_ticket():
        raw = request.form.get('source', '')
        audience = request.form.getlist('audience')
        try:
            ticket_id = service.save(raw, audience, roster().students)
        except TicketError as exc:
            return editor_page(raw, error=str(exc), audience=audience, status=400)
        return redirect(url_for('exit_tickets.preview_ticket', ticket_id=ticket_id), code=303)

    @bp.route('/exit-tickets/<ticket_id>/edit', methods=['GET', 'POST'])
    def edit_ticket(ticket_id):
        ticket = repo.get(ticket_id)
        if request.method == 'POST':
            raw = request.form.get('source', '')
            audience = request.form.getlist('audience')
            try:
                service.save(raw, audience, roster().students, ticket_id, version())
            except TicketError as exc:
                return editor_page(raw, ticket, str(exc), audience, 400)
            return redirect(url_for('exit_tickets.preview_ticket', ticket_id=ticket_id), code=303)
        return editor_page(json.dumps(definition(ticket), indent=2, ensure_ascii=False), ticket,
                           audience=['student:' + sid for sid in ticket['assignments']])

    @bp.get('/exit-tickets/<ticket_id>/preview')
    def preview_ticket(ticket_id):
        ticket = repo.get(ticket_id)
        return render_template('exit_preview.html', ticket=ticket, student_ticket=public_ticket(ticket), values={},
                               students=roster().students)

    @bp.post('/exit-tickets/<ticket_id>/publish')
    def publish_ticket(ticket_id):
        ticket = repo.get(ticket_id)
        if not set(ticket['assignments']) <= set(roster().students):
            raise TicketError('An assigned student was removed from the workbook. Review the assignment before publishing.')
        repo.change_status(ticket_id, version(), 'published')
        session['generation_message'] = 'Exit ticket published. Assigned fictional students can now submit.'
        return redirect(url_for('exit_tickets.list_tickets'), code=303)

    @bp.post('/exit-tickets/<ticket_id>/unpublish')
    def unpublish_ticket(ticket_id):
        repo.change_status(ticket_id, version(), 'unpublished')
        session['generation_message'] = 'Exit ticket unpublished. Stored submissions and results are preserved.'
        return redirect(url_for('exit_tickets.list_tickets'), code=303)

    @bp.get('/exit-tickets/<ticket_id>/results')
    def ticket_results(ticket_id):
        return render_template('exit_results.html', result=service.results(ticket_id), students=roster().students)

    @bp.route('/exit-tickets/<ticket_id>/controls', methods=['GET', 'POST'])
    def ticket_controls(ticket_id):
        if request.method == 'POST':
            if request.form.get('action') == 'retake':
                sid = request.form.get('student_id', '')
                if sid not in roster().students:
                    raise TicketError('Select a student in the current workbook.')
                child = repo.create_retake(ticket_id, sid, version(), request.form.get('reason', ''))
                return redirect(url_for('exit_tickets.preview_ticket', ticket_id=child), code=303)
            if request.form.get('action') != 'release':
                raise TicketError('Unsupported control action.')
            repo.set_release(ticket_id, version(), request.form.get('mode'), request.form.get('reason', ''))
            return redirect(url_for('exit_tickets.ticket_controls', ticket_id=ticket_id), code=303)
        return render_template('exit_controls.html', ticket=repo.get(ticket_id), audit=repo.audit(ticket_id),
                               submissions=repo.submissions(ticket_id))

    @bp.route('/exit-tickets/<ticket_id>/review/<sid>', methods=['GET', 'POST'])
    def review_response(ticket_id, sid):
        if request.method == 'POST':
            repo.review(ticket_id, sid, request.form.get('question_id'), request.form.get('score'),
                        request.form.get('feedback', ''), version(), request.form.get('reason', ''))
            return redirect(url_for('exit_tickets.review_response', ticket_id=ticket_id, sid=sid), code=303)
        result = service.results(ticket_id)
        response = next((r for r in result['submissions'] if r['student_id'] == sid), None)
        if response is None:
            abort(404)
        return render_template('exit_review.html', ticket=result['ticket'], response=response, sid=sid)

    @bp.post('/simulation/student/<sid>')
    def simulate_student(sid):
        if sid not in roster().students:
            abort(404)
        session.clear()
        session.update(simulated_student=sid, csrf_token=secrets.token_urlsafe(32))
        return redirect(url_for('exit_tickets.student_home', student_key='student' + sid), code=303)

    @bp.post('/simulation/teacher')
    def simulate_teacher():
        session.clear()
        session['csrf_token'] = secrets.token_urlsafe(32)
        return redirect(url_for('exit_tickets.list_tickets'), code=303)

    @bp.get('/student/<student_key>')
    def student_home(student_key):
        sid, data = student(student_key)
        available, completed = service.student_home(sid)
        formal = build_dashboard(data, sid, False, workspace_state=Workspace(config.workspace).export_state())
        return render_template('local_student.html', student_key=student_key, available=available, completed=completed,
                               formal=formal, progress=progress_rows(data, sid, completed))

    @bp.get('/student/<student_key>/progress')
    def student_progress(student_key):
        sid, data = student(student_key)
        return render_student(data, sid, False, Workspace(config.workspace).export_state(),
                              local_dashboard_url=url_for('exit_tickets.student_home', student_key=student_key))

    @bp.get('/student/<student_key>/tickets/<ticket_id>')
    def student_ticket(student_key, ticket_id):
        sid, _ = student(student_key)
        if repo.submission(ticket_id, sid):
            return redirect(url_for('exit_tickets.student_history', student_key=student_key, ticket_id=ticket_id))
        return render_template('exit_form.html', student_key=student_key, ticket=service.available(ticket_id, sid), values={})

    @bp.post('/student/<student_key>/tickets/<ticket_id>')
    def student_submit(student_key, ticket_id):
        sid, _ = student(student_key)
        ticket = service.available(ticket_id, sid)
        values = {}
        for q in ticket['questions']:
            field = 'answer_' + q['id']
            if q['type'] == 'multiple_select':
                values[q['id']] = request.form.getlist(field)
            else:
                value = request.form.get(field)
                values[q['id']] = {'true': True, 'false': False}.get(value) if q['type'] == 'true_false' else value
        try:
            repo.submit(ticket_id, sid, version(), values)
        except TicketError as exc:
            return render_template('exit_form.html', student_key=student_key, ticket=ticket, values=values, error=str(exc)), 400
        return redirect(url_for('exit_tickets.student_history', student_key=student_key, ticket_id=ticket_id), code=303)

    @bp.get('/student/<student_key>/history/<ticket_id>')
    def student_history(student_key, ticket_id):
        sid, _ = student(student_key)
        return render_template('exit_history.html', student_key=student_key, result=service.history(ticket_id, sid))

    app.register_blueprint(bp)
