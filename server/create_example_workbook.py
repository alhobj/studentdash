"""Create synthetic inputs for a fresh checkout; never read the private workbook."""
import argparse
from pathlib import Path

from openpyxl import Workbook

from studentdash.config import ROOT
from studentdash.excel import SCHEMA, OPTIONAL_SCHEMA


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
    for name, columns in OPTIONAL_SCHEMA.items():
        book.create_sheet(name).append(list(columns))
    book['Students']['D3'] = 'Chemistry HL'
    book['Assessments'].append(['A2', 'Example stoichiometry assessment', '2026-09-21', 'Chemistry SL/HL', 10])
    book['Assessments'].append(['A3', 'Example follow-up assessment', '2026-09-22', 'Chemistry SL/HL', 2])
    for row in [
        ['Q3', 'A2', '1', 'SL', 'Explain the meaning of amount of substance.', '', 3, 'Stoichiometry', 'Amount of substance', 'Short', 'Explain', False],
        ['Q4', 'A2', '2', 'SL', 'Calculate the amount in 36 g of water.', '', 3, 'Stoichiometry', 'Amount of substance', 'Short', 'Calculate', False],
        ['Q5', 'A2', '3', 'HL', 'Calculate the limiting reactant for the supplied reaction.', '', 4, 'Stoichiometry', 'Limiting reactants', 'Short', 'Calculate', False],
        ['Q6', 'A3', '1', 'BOTH', 'Explain how an ion differs from an atom.', '', 2, 'Atomic structure', 'Particles', 'Short', 'Explain', False],
    ]:
        book['Questions'].append(row)
    for aid in ('A1', 'A2', 'A3'):
        for sid, level in [('1001', 'SL'), ('1002', 'HL')]:
            book['Memberships'].append([aid, sid, level])
    for row in [
        ['A1', 'Q1', '1001', 2, 'graded'], ['A1', 'Q2', '1001', 1, 'graded'],
        ['A1', 'Q1', '1002', 2, 'graded'], ['A1', 'Q2', '1002', 0, 'graded'],
        ['A2', 'Q3', '1001', 3, 'graded'], ['A2', 'Q4', '1001', None, 'exempt'],
        ['A2', 'Q3', '1002', 1, 'graded'], ['A2', 'Q4', '1002', 2, 'graded'], ['A2', 'Q5', '1002', 2, 'graded'],
        ['A3', 'Q6', '1001', None, 'pending'], ['A3', 'Q6', '1002', None, 'absent'],
    ]:
        book['QuestionResults'].append(row)
    for row in [['A2', '1001', 3, 3, 'graded'], ['A2', '1002', 5, 10, 'graded'],
                ['A3', '1001', None, 2, 'pending'], ['A3', '1002', None, 2, 'absent']]:
        book['Results'].append(row)
    for grade, percent in [(1, 0), (2, 20), (3, 35), (4, 45), (5, 60), (6, 75), (7, 90)]:
        book['AssessmentBoundaries'].append(['A2', grade, percent])
    book['Resources'].append(['R1', 'Atomic structure', 'Particles revision card',
        'Fictional lesson resource: list the charge and relative mass of protons, neutrons and electrons. Then explain why a neutral atom has no overall charge.'])
    book['Resources'].append(['R2', 'Stoichiometry', 'Amount of substance practice',
        'Fictional lesson resource: practise n = m / M. Write the units at each step and explain what one mole represents.'])
    book['ExitTickets'].append(['T1', '1001', 'A1', '2026-09-20', 'What would you revisit?',
        'I want to practise explaining charge balance.', 'Use the particles revision card and write a two-sentence explanation.'])
    book['ExitTickets'].append(['T2', '1002', 'A2', '2026-09-21', 'What is your next step?',
        'I need to identify the limiting reactant more reliably.', 'Calculate the amount of each reactant before comparing the ratio.'])
    try:
        # Exclusive creation prevents accidentally overwriting a real master workbook.
        with path.open('xb') as destination:
            book.save(destination)
    finally:
        book.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--small', action='store_true', help='Create the original two-learner fixture instead of the full classroom.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    destination = args.output or ROOT / 'data' / ('fictional.xlsx' if args.small else 'classroom.xlsx')
    try:
        if args.small:
            create_example(destination)
        else:
            from studentdash.demo import create_classroom
            create_classroom(destination)
    except FileExistsError:
        parser.exit(1, f'Refusing to overwrite existing workbook: {destination}\n')
    print(f'Created fictional example workbook: {destination}')
