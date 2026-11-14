"""One entry point for the class workspace, Excel workspace and learning trees."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'server'), str(ROOT / 'excel')]


def create_app(data_directory=None):
    from flask import abort, send_from_directory
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from studentdash.config import Config
    from studentdash.teacher import create_app as class_app
    from app.teacher import create_app as excel_app

    private = Path(data_directory or ROOT / 'data').resolve()
    config = Config(Path(os.environ.get('STUDENTDASH_WORKBOOK', private / 'classroom.xlsx')),
                    Path(os.environ.get('STUDENTDASH_OUTPUT', ROOT / 'output')))
    app = class_app(config)
    from studentdash.teacher_tree import register_teacher_tree
    register_teacher_tree(app, config, ROOT / 'tree/local-package/curriculum.json')
    app.config['ARBOR_ROOT'] = ROOT
    app.config['ARBOR_DEMO'] = os.environ.get('ARBOR_DEMO') == '1'

    @app.get('/health')
    def health():
        return {'status': 'ok', 'app': 'ArborSynapse'}

    def asset(folder, filename):
        # Serve built assets only; never source, private exports or the repository.
        directory = ROOT / folder
        if not (directory / 'index.html').is_file():
            abort(503, description='Run Start.cmd to prepare the bundled trees first.')
        return send_from_directory(directory, filename)

    @app.get('/tree/')
    def tree():
        return asset('tree/teacher-viewer/dist', 'index.html')

    @app.get('/tree/<path:filename>')
    def tree_asset(filename):
        return asset('tree/teacher-viewer/dist', filename)

    @app.get('/curriculum/')
    def student_tree():
        return asset('tree/dist', 'index.html')

    @app.get('/curriculum/<path:filename>')
    def student_tree_asset(filename):
        return asset('tree/dist', filename)

    @app.get('/simple/')
    def simple():
        return asset('tree/simple/dist', 'index.html')

    @app.get('/simple/<path:filename>')
    def simple_asset(filename):
        return asset('tree/simple/dist', filename)

    excel = excel_app(private_directory=private / 'private', generated_directory=private / 'generated')
    # Distinct cookie names avoid the two independent workspaces overwriting sessions.
    excel.config.update(SESSION_COOKIE_NAME='arbor_excel', SESSION_COOKIE_PATH='/excel')
    app.config.update(SESSION_COOKIE_NAME='arbor_class')
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/excel': excel})
    if os.environ.get('ARBOR_DEMO') == '1':
        seed_demo(config)
    return app


def seed_demo(config):
    """Initialize once with fictional data; never overwrite a saved sandbox."""
    from studentdash.entry import ClassStore, save_assessment, save_scores
    from studentdash.curriculum import selected_curriculum
    store = ClassStore(config.workbook.parent / 'entered_classes')
    if store.list():
        return
    curriculum = selected_curriculum('chemistry-2025')
    profile = dict(curriculum['profile'], curriculum=curriculum)
    doc = store.create('ArborSynapse · fictional sandbox', 'Demo learner A\nDemo learner B', profile)
    q = dict(number='1', marks=5, text='Fictional example', tags={}, curriculum_nodes=[], scope='')
    aid = save_assessment(store, doc['id'], None, dict(name='Fictional assessment', date='2026-01-01',
                          participants=[s['id'] for s in doc['students']], questions=[q]), doc['version'])
    doc = store.read(doc['id'])
    save_scores(store, doc['id'], aid, [['4'], ['2']], doc['version'])
