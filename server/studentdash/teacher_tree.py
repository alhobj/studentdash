"""Read-only, learner-scoped evidence for the teacher tree; no browser confidence."""
from pathlib import Path
from flask import Blueprint, abort, session
from .entry import ClassStore, as_workbook
from .local_tree import read_json, evidence
from .tree_export import choices


def register_teacher_tree(app, config, registry_path):
    bp = Blueprint('teacher_tree', __name__, url_prefix='/api/teacher-tree')
    store = ClassStore(config.workbook.parent / 'entered_classes')

    def document(key):
        try:
            return store.read(key)
        except (ValueError, OSError):
            abort(404)

    @bp.get('/classes')
    def classes():
        docs = store.list()
        return dict(classes=[dict(id=d['id'], name=d['name']) for d in docs],
                    selectedClassId=session.get('entered_class', ''))

    @bp.get('/classes/<key>/students')
    def students(key):
        doc = document(key)
        return dict(classId=key, students=[dict(id=s['id'], name=s['name']) for s in doc['students']])

    @bp.get('/classes/<key>/students/<sid>/results')
    def results(key, sid):
        doc = document(key)
        if sid not in {s['id'] for s in doc['students']}:
            abort(404)
        if not Path(registry_path).is_file():
            abort(503, description='Build the bundled viewer first.')
        registry = read_json(registry_path)
        mapping = {r['question']['id']:r['selected'] for r in choices(doc, registry) if r['selected']}
        data = as_workbook(store.path(key))
        rows = evidence(data, sid, mapping, registry)
        graded = sum(r.student_id == sid and r.status == 'graded' for r in data.question_results)
        return dict(classId=key, studentId=sid, evidence=rows, unassignedGradedParts=graded-len(rows))

    app.register_blueprint(bp)
