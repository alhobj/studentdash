from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analytics import build_dashboard
from .config import ROOT
from .excel import read_workbook, WorkbookError
from .workspace import Workspace
from .freshness import fingerprints


def template_environment():
    return Environment(loader=FileSystemLoader(ROOT / 'templates'),
                       autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)


def render_student(data, sid, include_examples=True, state=None, **context):
    student = build_dashboard(data, sid, include_examples, workspace_state=state)
    views = [student] + [build_dashboard(data, sid, include_examples, aid, state)
                         for aid, _ in student.assessment_options]
    return template_environment().get_template('student.html').render(student=student, views=views, **context)


def generate_dashboards(config, include_examples=True):
    state = Workspace(config.workspace).export_state()
    source_versions = fingerprints(config, state)
    data = read_workbook(config.workbook)
    # Render every page before touching existing output. No workbook object reaches Jinja.
    pages = {}
    for sid in data.students:
        pages[f'student{sid}.html'] = render_student(data, sid, include_examples, state)
    if fingerprints(config) != source_versions:
        raise WorkbookError('Inputs changed while rendering. Retry generation to make a consistent snapshot.')
    output = Path(config.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.studentdash-', dir=output) as staging:
        for name, html in pages.items():
            (Path(staging) / name).write_bytes(html.encode('utf-8'))
        for name in pages:
            (Path(staging) / name).replace(output / name)
    # Only remove obsolete generated filenames inside the explicitly configured output.
    for old in output.glob('student*.html'):
        if old.name not in pages and old.is_file():
            old.unlink()
    manifest = {'generated_at': build_dashboard(data, next(iter(data.students)), False).generated_at,
                'workbook_sha256': source_versions['workbook'],
                'include_examples': include_examples, 'fingerprints': source_versions,
                'pages': {name: hashlib.sha256(html.encode('utf-8')).hexdigest() for name, html in pages.items()}}
    (output / 'generation.json').write_text(json.dumps(manifest), encoding='utf-8')
    return data, list(pages)
