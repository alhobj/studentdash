"""Private single-learner HTML exports, with no workbook/database or external assets."""
from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analytics import dashboard
from .storage import ROOT, ValidationError


def fingerprint(doc):
    return sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def render_student(doc, sid):
    environment = Environment(loader=FileSystemLoader(ROOT / 'app/templates'), autoescape=select_autoescape(['html']))
    return environment.get_template('student.html').render(student=dashboard(doc, sid))


def export_pages(doc):
    return {f'student{sid}.html': render_student(doc, sid)
            for sid, student in doc['students'].items() if student.get('active', True)}


def generate(doc, directory):
    """Replace a dedicated course export directory only after all pages render."""
    directory = Path(directory)
    directory.parent.mkdir(parents=True, exist_ok=True)
    pages = export_pages(doc)
    with TemporaryDirectory(prefix='.studentdash-', dir=directory.parent) as temp:
        stage = Path(temp) / 'export'
        stage.mkdir()
        for name, html in pages.items():
            (stage / name).write_text(html, encoding='utf-8')
        (stage / 'manifest.json').write_text(json.dumps(dict(course=doc['id'], revision=doc['revision'], fingerprint=fingerprint(doc), files=list(pages))), encoding='utf-8')
        # Only operate on this app's managed export directory.
        if directory.exists():
            if not (directory / 'manifest.json').is_file():
                raise ValidationError('Export directory is not managed by Studentdash. Choose an empty/new directory.')
            previous = Path(temp) / 'previous'
            directory.rename(previous)
            try:
                stage.rename(directory)
            except Exception:
                previous.rename(directory)
                raise
        else:
            stage.rename(directory)
    return pages


def zip_pages(doc):
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        for name, html in export_pages(doc).items():
            archive.writestr(name, html)
        archive.writestr('READ-ME.txt', 'Private student dashboards. Give each learner only their own student<ID>.html file. Each HTML works offline without Python or Flask. This ZIP contains all learners and is for the teacher only. No database or source workbook is included.')
    return buffer.getvalue()
