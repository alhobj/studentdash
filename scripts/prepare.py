"""Build only when source changes; share one npm install across all tree views."""
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / 'tree'
SKIP = {'node_modules', 'dist', 'local-package', 'generated', '.cache'}


def fingerprint():
    digest = hashlib.sha256()
    for path in sorted(TREE.rglob('*')):
        if not path.is_file() or any(p in SKIP for p in path.relative_to(TREE).parts):
            continue
        if path.relative_to(TREE).as_posix() == 'simple/src/data/map.json' or path.name.endswith('.tsbuildinfo'):
            continue
        digest.update(path.relative_to(TREE).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def prepare():
    npm = shutil.which('npm.cmd') or shutil.which('npm')
    if not npm:
        raise SystemExit('Install Node.js 22.12+ or 24 LTS, reopen the terminal and run Start.cmd again.')
    marker = ROOT / '.cache/tree-build'
    expected = fingerprint()
    outputs = ['teacher-viewer/dist/index.html', 'dist/index.html', 'simple/dist/index.html', 'local-package/curriculum.json']
    if marker.is_file() and marker.read_text() == expected and all((TREE / p).is_file() for p in outputs):
        return
    lock = hashlib.sha256((TREE / 'package-lock.json').read_bytes()).hexdigest()
    install = ROOT / '.cache/npm-lock'
    if not install.exists() or install.read_text() != lock or not (TREE / 'node_modules/.package-lock.json').is_file():
        subprocess.run([npm, 'ci'], cwd=TREE, check=True)
        install.parent.mkdir(exist_ok=True)
        install.write_text(lock)
    subprocess.run([npm, 'run', 'build:all'], cwd=TREE, check=True)
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(fingerprint())


if __name__ == '__main__':
    prepare()
