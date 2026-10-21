"""Teacher upload and review routes. Source documents never enter student exports."""
from copy import deepcopy
from io import BytesIO
import json
import secrets

from flask import Blueprint, redirect, render_template, request, send_file, session, url_for

from .assessment_import import create_draft, draft_by_id, save_review, update_review, validation
from .document_extract import MAX_BYTES
from .entry import EntryError
from .import_suggestions import curriculum_nodes


def register_import_routes(app, store):
    bp = Blueprint('assessment_import', __name__)

    @bp.before_request
    def token():
        session.setdefault('csrf_token', secrets.token_urlsafe(32))

    @bp.route('/classes/<key>/import', methods=['GET', 'POST'])
    def upload(key):
        doc = store.read(key)
        session['entered_class'] = key
        error = None
        if request.method == 'POST':
            try:
                source = request.files.get('document')
                if source is None or not source.filename:
                    raise EntryError('Choose a PDF or DOCX test document.')
                did = create_draft(store, key, source.filename, source.read(MAX_BYTES + 1))
                return redirect(url_for('assessment_import.review', key=key, did=did), code=303)
            except EntryError as exc:
                error = str(exc)
        return render_template('assessment_upload.html', doc=doc, error=error), 400 if error else 200

    @bp.route('/classes/<key>/imports/<did>', methods=['GET', 'POST'])
    def review(key, did):
        doc = store.read(key)
        draft = deepcopy(draft_by_id(doc, did))
        session['entered_class'] = key
        if draft['status'] == 'confirmed':
            return redirect(url_for('entry.scores', key=key, aid=draft['assessment_id']), code=303)
        error, submitted = None, None
        form_version = doc['version']
        if request.method == 'POST':
            try:
                try:
                    form_version = int(request.form['version'])
                    submitted = json.loads(request.form['payload'])
                except (ValueError, KeyError):
                    raise EntryError('The review could not be read. Reload before retrying.') from None
                update_review(draft, submitted, doc)
                aid = save_review(store, key, did, submitted, form_version, finalize=request.form.get('action') == 'finalize')
                if aid:
                    return redirect(url_for('entry.scores', key=key, aid=aid, saved='1'), code=303)
                return redirect(url_for('assessment_import.review', key=key, did=did, saved='1'), code=303)
            except EntryError as exc:
                error = str(exc)
        return render_template('assessment_review.html', doc=doc, draft=draft, report=validation(draft),
                               curriculum=curriculum_nodes(draft['profile']), form_version=form_version,
                               error=error, submitted=submitted), 400 if error else 200

    @bp.get('/classes/<key>/imports/<did>/source')
    def source(key, did):
        doc = store.read(key)
        draft_by_id(doc, did)  # Require ownership by this class, including finalized drafts.
        filename, mime, content = store.source(key, did)
        return send_file(BytesIO(content), download_name=filename, mimetype=mime, as_attachment=True)

    app.register_blueprint(bp)
