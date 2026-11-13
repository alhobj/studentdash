"""Run server, Excel and combined-app tests in independent Python processes."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
for folder, tests in [('server', 'tests'), ('excel', 'tests'), ('.', 'tests'),
                      ('tree', 'tests/python'), ('tree', 'local-runtime')]:
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', tests, '-p', 'test_*.py', '-v'],
                   cwd=ROOT / folder, check=True)
