from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analytics import build_dashboard
from .config import ROOT
from .excel import read_workbook


def template_environment():
    return Environment(loader=FileSystemLoader(ROOT / 'templates'),
                       autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)


def generate_dashboards(config, include_examples=True):
    data = read_workbook(config.workbook)
    template = template_environment().get_template('student.html')
    # Render every page before touching existing output. No workbook object reaches Jinja.
    pages = {f'student{sid}.html': template.render(student=build_dashboard(data, sid, include_examples))
             for sid in data.students}
    output = Path(config.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.studentdash-', dir=output) as staging:
        for name, html in pages.items():
            (Path(staging) / name).write_text(html, encoding='utf-8')
        for name in pages:
            (Path(staging) / name).replace(output / name)
    # Only remove obsolete generated filenames inside the explicitly configured output.
    for old in output.glob('student*.html'):
        if old.name not in pages and old.is_file():
            old.unlink()
    return data, list(pages)
