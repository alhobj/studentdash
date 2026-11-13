"""Run a minimal smoke check by default; --full runs all Python suites."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--full', action='store_true', help='Run every Python suite before a release or broad refactor')
args = parser.parse_args()
if args.full:
    checks = [(folder, ['discover', '-s', tests, '-p', 'test_*.py', '-v'])
              for folder, tests in [('server', 'tests'), ('excel', 'tests'), ('.', 'tests'),
                                    ('tree', 'tests/python'), ('tree', 'local-runtime')]]
else:
    checks = [('.', ['discover', '-s', 'tests', '-p', 'test_combined.py',
                     '-k', 'both_workspaces_and_navigation', '-k', 'class_results_export', '-v']),
              ('server', ['discover', '-s', 'tests', '-p', 'test_tree_export.py',
                          '-k', 'saved_metadata_scores_export_and_update_keep_package_identity', '-v'])]
for folder, arguments in checks:
    subprocess.run([sys.executable, '-m', 'unittest', *arguments], cwd=ROOT / folder, check=True)
