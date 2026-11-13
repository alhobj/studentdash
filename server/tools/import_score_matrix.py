"""Normalize an explicit-ID ScoreMatrix into a new, validated assessment workbook.

ScoreMatrix headers: AssessmentID, StudentID, then globally unique QuestionIDs.
Numbers mean graded (including zero); blank means pending; other cells must be
pending/missing/absent/exempt. This command also writes assessment totals only
for complete graded/exempt rows. It never modifies the input workbook.
"""
import argparse
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpyxl import load_workbook
from studentdash.excel import read_workbook, WorkbookError, STATUSES, _number
from studentdash.question_data import eligible


def import_matrix(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Choose a new output path; input and existing output are never overwritten.')
    data = read_workbook(source)
    book = load_workbook(source)
    try:
        if 'ScoreMatrix' not in book:
            raise WorkbookError('Add ScoreMatrix with AssessmentID, StudentID and QuestionID headers.')
        rows = iter(book['ScoreMatrix'].values)
        headers = next(rows)
        if headers[:2] != ('AssessmentID', 'StudentID') or len(headers) != len(set(headers)):
            raise WorkbookError('ScoreMatrix needs unique headers: AssessmentID, StudentID, QuestionIDs.')
        qids = [str(v) for v in headers[2:]]
        if set(qids) - set(data.questions):
            raise WorkbookError('ScoreMatrix contains unknown QuestionIDs.')
        normalized, summaries, seen = [], [], set()
        for n, row in enumerate(rows, 2):
            if not any(v is not None for v in row):
                continue
            aid, sid = str(row[0]), str(row[1])
            key = aid, sid
            level = data.memberships.get(key)
            if not level or key in seen:
                raise WorkbookError(f'ScoreMatrix row {n}: missing membership or duplicate assessment/student.')
            seen.add(key)
            expected = {q.id for q in data.questions.values() if q.assessment_id == aid and eligible(q, level)}
            if not expected <= set(qids):
                raise WorkbookError(f'ScoreMatrix row {n}: an applicable question column is missing.')
            score = maximum = 0
            complete = True
            for qid, value in zip(qids, row[2:]):
                if qid not in expected:
                    if value is not None:
                        raise WorkbookError(f'ScoreMatrix row {n}: score outside assessment/level.')
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    status, mark = 'graded', _number(value, f'ScoreMatrix row {n}')
                    if data.questions[qid].marks is None or mark > data.questions[qid].marks:
                        raise WorkbookError(f'ScoreMatrix row {n}: score exceeds or lacks question marks.')
                    score += mark
                    maximum += data.questions[qid].marks
                else:
                    status, mark = ('pending' if value is None else str(value).strip().lower()), None
                    if status not in STATUSES - {'graded'}:
                        raise WorkbookError(f'ScoreMatrix row {n}: invalid score/status.')
                    if status != 'exempt':
                        complete = False
                normalized.append([aid, qid, sid, mark, status])
            if complete and maximum:
                summaries.append([aid, sid, score, maximum, 'graded'])
        # Replace only pairs explicitly present in the matrix; retain all others.
        old_questions = [[r.assessment_id, r.question_id, r.student_id, r.score, r.status] for r in data.question_results if (r.assessment_id, r.student_id) not in seen]
        new_summaries = {(r[0], r[1]) for r in summaries}
        old_summaries = [[r.assessment_id, r.student_id, r.score, r.max_score, r.status] for r in data.results if (r.assessment_id, r.student_id) not in new_summaries]
        for name, header, values in [
            ('QuestionResults', ['AssessmentID', 'QuestionID', 'StudentID', 'Score', 'Status'], old_questions+normalized),
            ('Results', ['AssessmentID', 'StudentID', 'Score', 'MaxScore', 'Status'], old_summaries+summaries),
        ]:
            if name in book:
                del book[name]
            ws = book.create_sheet(name)
            ws.append(header)
            for row in values:
                ws.append(row)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=destination.parent, suffix='.xlsx', delete=False) as handle:
            temporary = Path(handle.name)
        try:
            book.save(temporary)
            read_workbook(temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    finally:
        book.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    import_matrix(args.source, args.destination)
