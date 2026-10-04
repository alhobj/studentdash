"""Teacher-only download and non-overwriting restore controls."""
from io import BytesIO
import secrets
import shutil
from uuid import uuid4

from flask import Blueprint, render_template, request, send_file, session

from .excel import read_workbook
from .entry import ClassStore, read_document
from .portability import PackageError, backup_workspace, practice_package, restore_workspace, student_package


def register_portability_routes(app, active_config, base_config):
    bp = Blueprint('portability', __name__)

    @bp.route('/transfer', methods=['GET', 'POST'])
    def transfer():
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        restored, error, restored_key = None, None, None
        if request.method == 'POST':
            upload = request.files.get('backup')
            try:
                if not upload:
                    raise PackageError('Choose a Studentdash backup ZIP.')
                restored = restore_workspace(upload.read(), base_config.workbook.parent / 'restored' / uuid4().hex)
                if restored.workbook.suffix == '.sdclass':
                    # Register a separate recovered copy; existing class IDs and files are untouched.
                    store = ClassStore(base_config.workbook.parent / 'entered_classes')
                    store.directory.mkdir(parents=True, exist_ok=True)
                    restored_key = uuid4().hex
                    target = store.path(restored_key)
                    doc = read_document(restored.workbook)
                    doc['restored_from'] = doc['id']
                    doc['id'] = restored_key
                    doc['name'] += ' (recovered copy)'
                    shutil.copyfile(restored.workbook, target)
                    store.save(doc, doc['version'])
                    if restored.workspace.exists():
                        shutil.copyfile(restored.workspace, target.with_suffix('.workspace.sqlite3'))
            except (ValueError, OSError) as exc:
                error = str(exc)
        config = active_config()
        students = read_workbook(config.workbook).students.values() if config.workbook.exists() else []
        return render_template('transfer.html', students=students, restored=restored, restored_key=restored_key, error=error,
                               source_exists=config.workbook.exists()), 400 if error else 200

    @bp.post('/transfer/download/<kind>')
    def download(kind):
        try:
            if kind == 'practice':
                content, filename = practice_package(), 'classroom-practice.zip'
            elif kind == 'student':
                content, filename = student_package(active_config(), request.form.get('student', '')), 'private-student-package.zip'
            elif kind == 'backup':
                content, filename = backup_workspace(active_config()), 'teacher-workspace-backup.zip'
            else:
                raise PackageError('Choose a valid package type.')
        except (PackageError, OSError) as exc:
            return render_template('entry_error.html', error=str(exc)), 400
        return send_file(BytesIO(content), as_attachment=True, download_name=filename, mimetype='application/zip')

    app.register_blueprint(bp)
