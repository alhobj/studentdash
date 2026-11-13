"""Restore byte-identical bundled practice assets only when their archive changes."""
import hashlib
from pathlib import Path
import tempfile
import os
import zipfile


def ensure_resources(root):
    root = Path(root)
    archive = root / 'assets/practice.zip'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    destination = root / 'resources'
    marker = destination / '.bundle-sha256'
    if marker.is_file() and marker.read_text() == digest:
        return
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            path = Path(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename:
                raise ValueError('Invalid bundled resource path.')
            target = destination / path
            if target.is_symlink() or not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Linked resource destination refused.')
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                temp = Path(handle.name)
                handle.write(bundle.read(item))
            try:
                os.replace(temp, target)
            finally:
                temp.unlink(missing_ok=True)
    marker.write_text(digest)
