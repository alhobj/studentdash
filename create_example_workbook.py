"""Create synthetic inputs for a fresh checkout; never read the private workbook."""
import argparse
from pathlib import Path

from openpyxl import Workbook

from studentdash.config import ROOT
from studentdash.excel import SCHEMA


def create_example(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    book.remove(book.active)
    for name, columns in SCHEMA.items():
        book.create_sheet(name).append(list(columns) + (['Status'] if name == 'Results' else []))
    for sid, name in [('1001', 'Example learner A'), ('1002', 'Example learner B')]:
        book['Students'].append([sid, name, '', 'Chemistry SL'])
    book['Assessments'].append(['A1', 'Example atomic structure assessment', '2026-09-20', 'Chemistry SL', 4])
    book['Questions'].append(['Q1', 'A1', '1', 'SL', 'State the charge of an electron.',
                              '-1', 2, 'Atomic structure', 'Particles', 'Short', 'State', False])
    book['Questions'].append(['Q2', 'A1', '2', 'SL', 'Explain why atoms are neutral.',
                              'Equal numbers of protons and electrons', 2, 'Atomic structure',
                              'Particles', 'Short', 'Explain', False])
    book['Results'].append(['A1', '1001', 3, 4, 'graded'])
    book['Results'].append(['A1', '1002', 2, 4, 'graded'])
    for grade, percent in [(1, 0), (2, 16), (3, 32), (4, 44), (5, 54), (6, 65), (7, 80)]:
        book['Grade boundaries'].append([grade, percent])
    try:
        # Exclusive creation prevents accidentally overwriting a real master workbook.
        with path.open('xb') as destination:
            book.save(destination)
    finally:
        book.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data' / 'master.xlsx')
    args = parser.parse_args()
    try:
        create_example(args.output)
    except FileExistsError:
        parser.exit(1, f'Refusing to overwrite existing workbook: {args.output}\n')
    print(f'Created fictional example workbook: {args.output}')
