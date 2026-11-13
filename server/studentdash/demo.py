"""Deterministic fictional class spanning six months; no external inputs."""
from datetime import date, timedelta
from random import Random

from openpyxl import Workbook

from .excel import SCHEMA, OPTIONAL_SCHEMA


def create_classroom(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    book.remove(book.active)
    for name, headers in {**SCHEMA, **OPTIONAL_SCHEMA}.items():
        book.create_sheet(name).append(list(headers) + (['Status'] if name == 'Results' else []))
    rng = Random(20260922)
    topics = [
        ('Atomic structure', ['State the charge of an electron.', 'Explain why isotopes have different masses.',
         'Calculate the neutrons in a specified isotope.', 'Explain why atoms form ions.',
         'Explain the pattern in successive ionization energies.', 'Calculate relative atomic mass from isotope abundances.']),
        ('Stoichiometry', ['State the meaning of one mole.', 'Explain why equations must be balanced.',
         'Calculate the amount in 36 g of water.', 'Explain how concentration changes on dilution.',
         'Explain how to identify a limiting reactant.', 'Calculate the yield from the supplied reaction data.']),
        ('Bonding', ['State the meaning of a covalent bond.', 'Explain the conductivity of molten salts.',
         'Calculate the formal charge in a supplied structure.', 'Explain the boiling-point difference of two molecules.',
         'Explain the shapes using electron-domain repulsion.', 'Calculate a bond enthalpy estimate.']),
        ('Energetics', ['State what an exothermic reaction means.', 'Explain the sign of an enthalpy change.',
         'Calculate heat transferred from temperature data.', 'Explain a calorimetry assumption.',
         'Explain a Hess cycle.', 'Calculate an enthalpy change using a cycle.']),
        ('Kinetics', ['State what reaction rate measures.', 'Explain how temperature affects rate.',
         'Calculate mean rate from a concentration table.', 'Explain the effect of a catalyst.',
         'Explain evidence for a rate-determining step.', 'Calculate the rate constant from supplied data.']),
        ('Equilibrium', ['State the meaning of dynamic equilibrium.', 'Explain the effect of increasing pressure.',
         'Calculate an equilibrium concentration from supplied data.', 'Explain the effect of changing temperature.',
         'Explain what the reaction quotient predicts.', 'Calculate an equilibrium constant.']),
    ]
    marks = [2, 3, 3, 4, 3, 4]
    for i in range(24):
        level = 'HL' if i % 3 == 0 else 'SL'
        group = 'North' if i % 2 == 0 else 'South'
        book['Students'].append([str(2001 + i), f'Fictional learner {i + 1:02}', '', f'Chemistry {level} {group}'])
    for grade, percent in enumerate([0, 16, 32, 44, 54, 65, 80], 1):
        book['Grade boundaries'].append([grade, percent])
    for a, (topic, prompts) in enumerate(topics):
        aid = f'C{a + 1}'
        day = date(2026, a + 4, 10)
        book['Assessments'].append([aid, f'Fictional {topic.lower()} assessment', day, 'Chemistry SL/HL', sum(marks)])
        for q, prompt in enumerate(prompts):
            verb = prompt.split()[0]
            book['Questions'].append([f'{aid}Q{q + 1}', aid, str(q + 1), 'SL' if q < 4 else 'HL',
                prompt, '', marks[q], topic, 'Core concepts' if q < 4 else 'HL extension', 'Short', verb, False])
        for grade, percent in enumerate([0, 18, 33, 45, 56, 68, 83], 1):
            book['AssessmentBoundaries'].append([aid, grade, percent])
        book['Resources'].append([f'CR{a + 1}', topic, f'{topic} revision guide',
            f'Fictional classroom resource: revisit your {topic.lower()} notes, define two key terms, '
            'then retry a calculation and explain each step. Compare your reasoning with the worked example from class.'])
        for i in range(24):
            sid = str(2001 + i)
            level = 'HL' if i % 3 == 0 else 'SL'
            book['Memberships'].append([aid, sid, level])
            applicable = range(6 if level == 'HL' else 4)
            score_total, maximum, statuses = 0, 0, []
            for q in applicable:
                status = 'graded'
                if a == 5 and i == 23:
                    continue  # Explicit membership, but no results recorded yet.
                if a == 5 and i % 11 == 0:
                    status = 'absent'
                elif a == 5 and i % 7 == 0:
                    status = 'pending'
                elif a == 5 and i % 5 == 0 and q == 1:
                    status = 'missing'
                elif a == 4 and i % 8 == 0 and q == 2:
                    status = 'unrecorded'
                elif i % 6 == 1 and q == 3 and a == 2:
                    status = 'exempt'
                trend = (a - 2) * (0.08 if i % 3 == 0 else -0.04 if i % 3 == 1 else 0)
                fraction = min(1, max(0, 0.25 + (i % 7) * 0.09 + trend + rng.uniform(-0.22, 0.22)))
                score = round(marks[q] * fraction) if status == 'graded' else None
                statuses.append(status)
                if status != 'exempt':
                    maximum += marks[q]
                score_total += score or 0
                qid = f'{aid}Q{q + 1}'
                if status != 'unrecorded':
                    book['QuestionResults'].append([aid, qid, sid, score, status])
                if a < 5 and i % 4 == 0 and q == 1 and score is not None and score < marks[q]:
                    book['RevisionAttempts'].append([f'RA{a}-{i}', sid, aid, qid, day + timedelta(days=7),
                        min(marks[q], score + 1), 'Fictional revision: used the topic guide and explained the steps again.'])
                    if i == 0:
                        book['RevisionAttempts'].append([f'RB{a}-{i}', sid, aid, qid, day + timedelta(days=14),
                            min(marks[q], score + 2), 'Fictional second retry after teacher feedback.'])
            if not statuses:
                continue
            summary_status = ('graded' if all(s in {'graded', 'exempt'} for s in statuses) else
                              'absent' if all(s == 'absent' for s in statuses) else
                              'missing' if 'missing' in statuses else 'pending')
            book['Results'].append([aid, sid, score_total if summary_status == 'graded' else None, maximum, summary_status])
            if i % 3 == a % 3:
                book['ExitTickets'].append([f'CT{a}-{i}', sid, aid, day,
                    'What will you practise next?', f'I will revisit {topic.lower()} and explain my reasoning.',
                    'Retry one question without notes, then compare each step with your class example.'])
    try:
        with path.open('xb') as destination:
            book.save(destination)
    finally:
        book.close()
