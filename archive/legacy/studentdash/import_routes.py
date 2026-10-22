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
from .chatgpt_assessment import prompt as chatgpt_prompt, save_response
from . import metadata_assessment as metadata
from . import import_drafts
from .question_levels import settings as level_settings


def register_import_routes(app, store):
    bp = Blueprint('assessment_import', __name__)

    @bp.errorhandler(EntryError)
    def invalid(error):
        return render_template('entry_error.html', error=str(error)), 400

    @bp.route('/classes/<key>/drafts/<kind>/<did>/delete', methods=['GET', 'POST'])
    def delete_draft(key, kind, did):
        doc = store.read(key)
        session['entered_class'] = key
        _, draft, title = import_drafts.locate(doc, kind, did)
        if request.method == 'POST':
            if request.form.get('confirm') != 'delete':
                raise EntryError('Deletion was not confirmed. The draft has been kept.')
            try:
                version = int(request.form['version'])
            except (ValueError, KeyError):
                raise EntryError('Reload the confirmation page before deleting.') from None
            title = import_drafts.delete(store, key, kind, did, version)
            session['draft_message'] = f'Deleted draft: {title}. Existing assessments and results were kept.'
            return redirect(url_for('entry.class_page', key=key, section='assessments', _anchor='drafts'), code=303)
        return render_template('delete_import_draft.html', doc=doc, draft_title=title)

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
                if request.form.get('method') == 'chatgpt':
                    try:
                        version = int(request.form['version'])
                    except (ValueError, KeyError):
                        raise EntryError('Reload the page before importing the ChatGPT response.') from None
                    did = save_response(store, key, request.form.get('chatgpt_response', ''), version)
                    return redirect(url_for('assessment_import.review', key=key, did=did), code=303)
                if request.form.get('method') == 'metadata':
                    try:
                        version = int(request.form['version'])
                    except (ValueError, KeyError):
                        raise EntryError('Reload before previewing the response.') from None
                    did = metadata.save_preview(store, key, request.form.get('chatgpt_response', ''), version,
                        assessment_id=request.form.get('assessment_id') or None)
                    return redirect(url_for('assessment_import.metadata_review', key=key, did=did), code=303)
                source = request.files.get('document')
                if source is None or not source.filename:
                    raise EntryError('Choose a PDF or DOCX test document.')
                did = create_draft(store, key, source.filename, source.read(MAX_BYTES + 1))
                return redirect(url_for('assessment_import.review', key=key, did=did), code=303)
            except EntryError as exc:
                error = str(exc)
        return render_template('assessment_upload.html', doc=doc, error=error, chatgpt_prompt=metadata.prompt(doc, request.args.get('assessment_type', 'assessment') if request.args.get('assessment_type', 'assessment') in {'assessment', 'exit_ticket'} else 'assessment')), 400 if error else 200

    @bp.route('/classes/<key>/metadata/<did>', methods=['GET', 'POST'])
    def metadata_review(key, did):
        doc = store.read(key)
        session['entered_class'] = key
        saved = metadata.get_preview(doc, did)
        if saved['status'] == 'imported':
            return redirect(url_for('entry.scores', key=key, aid=saved['assessment_id']), code=303)
        payload = deepcopy(saved['payload'])
        error, changes = None, []
        if request.method == 'POST':
            raw = request.form.get('payload', '')
            try:
                payload = metadata.parse(raw, key)
                version = int(request.form['version'])
                aid = metadata.commit(store, key, did, raw, version, replace=request.form.get('replace') == 'yes')
                return redirect(url_for('entry.scores', key=key, aid=aid, saved='1'), code=303)
            except (ValueError, KeyError) as exc:
                error = str(exc) if isinstance(exc, EntryError) else 'Invalid preview. Reload and try again.'
        item = None
        try:
            item, changes = metadata.proposal(doc, payload)
        except EntryError as exc:
            error = error or str(exc)
        return render_template('metadata_review.html', doc=doc, payload=payload, error=error, changes=changes,
            item=item, vocabulary=doc['profile']['categories'], curriculum=curriculum_nodes(metadata.import_profile(doc)),
            scopes=level_settings(doc)['options'], question_levels=level_settings(doc), preview_id=did), 400 if error else 200

    @bp.route('/classes/<key>/imports/<did>/chatgpt', methods=['POST'])
    def paste_chatgpt(key, did):
        doc = store.read(key)
        draft = deepcopy(draft_by_id(doc, did))
        try:
            try:
                version = int(request.form['version'])
            except (ValueError, KeyError):
                raise EntryError('Reload the page before importing the ChatGPT response.') from None
            save_response(store, key, request.form.get('chatgpt_response', ''), version, did)
            return redirect(url_for('assessment_import.review', key=key, did=did), code=303)
        except EntryError as exc:
            return render_template('assessment_review.html', doc=doc, draft=draft, report=validation(draft),
                curriculum=curriculum_nodes(draft['profile']), form_version=doc['version'], error=str(exc),
                submitted=None, chatgpt_prompt=chatgpt_prompt(doc, draft)), 400

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
                               error=error, submitted=submitted, chatgpt_prompt=chatgpt_prompt(doc, draft)), 400 if error else 200

    @bp.get('/classes/<key>/imports/<did>/source')
    def source(key, did):
        doc = store.read(key)
        draft_by_id(doc, did)  # Require ownership by this class, including finalized drafts.
        filename, mime, content = store.source(key, did)
        return send_file(BytesIO(content), download_name=filename, mimetype=mime, as_attachment=True)

    app.register_blueprint(bp)
