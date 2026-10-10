"""Offline distribution and integrity-checked, non-overwriting workspace recovery."""
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from .config import ROOT, Config
from .excel import read_workbook
from .render import render_student
from .learning import completed_tickets
from .workspace import Workspace


class PackageError(ValueError):
    pass


def _assets(archive):
    root = (ROOT / 'resources').resolve()
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.resolve().is_relative_to(root) and path.suffix in {'.html', '.css', '.js', '.json'}:
            archive.write(path, 'resources/' + path.relative_to(root).as_posix())


def practice_package():
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        _assets(archive)
        links = ''.join(f'<li><a href="resources/{p.name}/learning-home.html">{p.name}</a></li>'
                        for p in sorted((ROOT / 'resources').iterdir()) if (p / 'my-practice.html').is_file())
        archive.writestr('index.html', '<!doctype html><html lang="en"><meta charset="utf-8"><title>Practice</title><h1>Practice</h1><p>Extract the complete ZIP first, then open this file. Keep the resources folder beside it.</p><ul>' + links + '</ul></html>')
    return output.getvalue()


def student_package(config, sid):
    data = read_workbook(config.workbook)
    if sid not in data.students:
        raise PackageError('Unknown student.')
    html = render_student(data, sid, False, Workspace(config.workspace).export_state(), resource_base='resources/', completed_tickets=completed_tickets(config.workspace, sid))
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('index.html', html)
        _assets(archive)
        archive.writestr('READ-ME.txt', 'Private learner package. Share only with this learner. Extract the complete ZIP, then open index.html. Export practice progress before changing computers. Browser saving for local files depends on the browser; use the progress file to transfer records.')
    return output.getvalue()


def backup_workspace(config):
    """Hold SQLite write reservations across both snapshots; never copy live WAL files."""
    if config.workbook.suffix not in {'.sdclass', '.xlsx', '.xlsm'} or not config.workbook.is_file():
        raise PackageError('Select a saved class or workbook first.')
    files = {'source' + config.workbook.suffix: config.workbook}
    if config.workspace.is_file():
        files['source.workspace.sqlite3'] = config.workspace
    blobs = {}
    with TemporaryDirectory(prefix='studentdash-backup-') as temp, ExitStack() as stack:
        for name, path in files.items():
            if path.suffix in {'.sdclass', '.sqlite3'}:
                guard = stack.enter_context(closing(sqlite3.connect(path, timeout=10)))
                guard.execute('BEGIN IMMEDIATE')
        before = config.workbook.read_bytes() if config.workbook.suffix != '.sdclass' else None
        for name, path in files.items():
            if path.suffix in {'.sdclass', '.sqlite3'}:
                target = Path(temp) / name
                with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(target)) as dest:
                    source.backup(dest)
                    if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise PackageError('Database integrity check failed; backup cancelled.')
                blobs[name] = target.read_bytes()
            else:
                blobs[name] = before
        if before is not None and config.workbook.read_bytes() != before:
            raise PackageError('Workbook changed during backup. Save it and retry.')
    manifest = dict(schema=1, type='studentdash-backup', created=datetime.now(timezone.utc).isoformat(),
                    source='source' + config.workbook.suffix,
                    files={name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()})
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', json.dumps(manifest))
        for name, blob in blobs.items():
            archive.writestr(name, blob)
    return output.getvalue()


def restore_workspace(content, destination):
    """Validate in staging, then rename to a new destination; never overwrite a course."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise PackageError('Restore requires a new destination folder; existing data will not be overwritten.')
    try:
        with ZipFile(BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) > 3 or len({i.filename for i in infos}) != len(infos) or sum(i.file_size for i in infos) > 100 * 1024 * 1024:
                raise PackageError('Invalid or oversized backup (maximum 100 MB uncompressed).')
            manifest = json.loads(archive.read('manifest.json'))
            allowed = {'source.sdclass', 'source.xlsx', 'source.xlsm'}
            if manifest.get('schema') != 1 or manifest.get('type') != 'studentdash-backup' or manifest.get('source') not in allowed:
                raise PackageError('Unsupported backup version or source type.')
            expected = {manifest['source'], 'source.workspace.sqlite3'}
            files = manifest.get('files', {})
            if not isinstance(files, dict) or manifest['source'] not in files or not set(files) <= expected or set(archive.namelist()) != set(files) | {'manifest.json'}:
                raise PackageError('Unexpected backup contents.')
            blobs = {name: archive.read(name) for name in files}
            if any(hashlib.sha256(blob).hexdigest() != files[name] for name, blob in blobs.items()):
                raise PackageError('Backup checksum mismatch; nothing restored.')
    except (BadZipFile, KeyError, ValueError, TypeError) as exc:
        raise PackageError('This is not a valid, intact Studentdash backup.') from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.restore-', dir=destination.parent) as temp:
        staged = Path(temp) / 'course'
        staged.mkdir()
        for name, blob in blobs.items():
            path = staged / name
            path.write_bytes(blob)
            if path.suffix in {'.sdclass', '.sqlite3'}:
                try:
                    with closing(sqlite3.connect(path)) as db:
                        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                            raise PackageError('Database integrity check failed.')
                except sqlite3.Error as exc:
                    raise PackageError('Invalid database in backup.') from exc
        restored = Config(staged / manifest['source'], staged / 'output')
        read_workbook(restored.workbook)
        if restored.workspace.exists():
            Workspace(restored.workspace).export_state()
        staged.rename(destination)
    return Config(destination / manifest['source'], destination / 'output')
