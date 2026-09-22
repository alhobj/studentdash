"""Private local teacher controls; no network integration or authentication."""
import secrets

from flask import Flask, abort, redirect, render_template, request, send_from_directory, session, url_for

from .config import ROOT, Config
from .excel import WorkbookError, read_workbook
from .render import generate_dashboards


def create_app(config=None):
    config = config or Config.from_env()
    app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=None)
    app.secret_key = secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', MAX_CONTENT_LENGTH=16384)

    @app.before_request
    def local_host_only():
        # Reject foreign Host headers (including DNS-rebinding requests).
        if request.host.split(':', 1)[0] not in {'127.0.0.1', 'localhost'}:
            abort(400)

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
            data = read_workbook(config.workbook)
        except WorkbookError as exc:
            error = str(exc)
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        names = [f'student{sid}.html' for sid in data.students
                 if (config.output / f'student{sid}.html').is_file()] if data else []
        message = session.pop('generation_message', None)
        return render_template('teacher.html', workbook_name=config.workbook.name, data=data,
                               error=error, names=names, message=message), status

    @app.get('/')
    def index():
        return status_page()

    @app.post('/generate')
    def generate():
        token = session.get('csrf_token', '')
        if not token or not secrets.compare_digest(token, request.form.get('csrf_token', '')):
            abort(400, description='Invalid form token. Reload the teacher page and retry.')
        try:
            _, names = generate_dashboards(config)
        except (WorkbookError, OSError) as exc:
            return status_page(f'Generation failed: {exc}', 400)
        session['generation_message'] = f'Generated {len(names)} student dashboards successfully.'
        return redirect(url_for('index'), code=303)

    @app.get('/preview/<filename>')
    def preview(filename):
        try:
            data = read_workbook(config.workbook)
        except WorkbookError:
            abort(404)
        if filename not in {f'student{sid}.html' for sid in data.students}:
            abort(404)
        return send_from_directory(config.output, filename)

    return app
