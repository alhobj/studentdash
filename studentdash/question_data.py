"""Optional normalized workbook tables. No name, class or matrix-position joins."""
from datetime import date, datetime
from math import isclose

from .excel import STATUSES, WorkbookError, _id, _number, _required, _text
from .models import ExitTicket, GradeBoundary, QuestionResult, Resource


def eligible(question, level):
    return question.level.upper() in {'BOTH', level} or (level == 'HL' and question.level.upper() == 'SL')


def read_extensions(data, tables):
    data.has_question_tables = 'Memberships' in tables or 'QuestionResults' in tables
    def reference(row, location):
        aid = _id(row['AssessmentID'], location + ' AssessmentID')
        sid = _id(row['StudentID'], location + ' StudentID')
        if aid not in data.assessments or sid not in data.students:
            raise WorkbookError(f'{location}: unknown assessment or student.')
        return aid, sid

    for n, row in tables.get('Memberships', []):
        loc = f'Memberships row {n}'
        key = reference(row, loc)
        level = _required(row['Level'], loc + ' Level').upper()
        if level not in {'SL', 'HL'}:
            raise WorkbookError(f'{loc}: Level must be SL or HL.')
        if key in data.memberships:
            raise WorkbookError(f'{loc}: duplicate assessment/student membership.')
        data.memberships[key] = level

    if 'QuestionResults' in tables and 'Memberships' not in tables:
        raise WorkbookError('QuestionResults requires an explicit Memberships sheet.')
    if 'Memberships' in tables:
        for result in data.results:
            if (result.assessment_id, result.student_id) not in data.memberships:
                raise WorkbookError('Results: assessment/student result has no explicit membership.')
        for question in data.questions.values():
            if question.level.upper() not in {'SL', 'HL', 'BOTH'}:
                raise WorkbookError(f'Question {question.id}: SLHL must be SL, HL or BOTH.')

    seen = set()
    for n, row in tables.get('QuestionResults', []):
        loc = f'QuestionResults row {n}'
        aid, sid = reference(row, loc)
        qid = _id(row['QuestionID'], loc + ' QuestionID')
        question = data.questions.get(qid)
        if question is None or question.assessment_id != aid:
            raise WorkbookError(f'{loc}: question does not belong to assessment {aid}.')
        level = data.memberships.get((aid, sid))
        if level is None or not eligible(question, level):
            raise WorkbookError(f'{loc}: question is outside the student membership/level.')
        if question.marks is None or not all((question.text, question.topic, question.subtopic, question.action_verb)):
            raise WorkbookError(f'{loc}: question requires marks, text, topic, subtopic and command term.')
        if question.action_verb.upper() == 'MCQ':
            raise WorkbookError(f'{loc}: MCQ is a question type, not a command term.')
        key = aid, qid, sid
        if key in seen:
            raise WorkbookError(f'{loc}: duplicate assessment/question/student result.')
        seen.add(key)
        score = _number(row['Score'], loc + ' Score', optional=True)
        status = _required(row['Status'], loc + ' Status').lower()
        if status not in STATUSES:
            raise WorkbookError(f'{loc}: unknown Status {status!r}.')
        if (status == 'graded') != (score is not None):
            raise WorkbookError(f'{loc}: graded results require a Score; non-graded results require a blank Score.')
        if score is not None and score > question.marks:
            raise WorkbookError(f'{loc}: Score exceeds question Marks.')
        data.question_results.append(QuestionResult(aid, qid, sid, score, status))

    for n, row in tables.get('AssessmentBoundaries', []):
        loc = f'AssessmentBoundaries row {n}'
        aid = _id(row['AssessmentID'], loc)
        if aid not in data.assessments:
            raise WorkbookError(f'{loc}: unknown assessment.')
        grade = _number(row['Grade'], loc + ' Grade')
        percent = _number(row['Percent'], loc + ' Percent')
        if not grade.is_integer() or not 1 <= grade <= 7 or percent > 100:
            raise WorkbookError(f'{loc}: Grade must be 1–7 and Percent 0–100.')
        data.assessment_boundaries.setdefault(aid, []).append(GradeBoundary(int(grade), percent))
    for aid, boundaries in data.assessment_boundaries.items():
        boundaries.sort(key=lambda b: b.grade)
        if ([b.grade for b in boundaries] != list(range(1, 8)) or boundaries[0].percent != 0
                or any(a.percent >= b.percent for a, b in zip(boundaries, boundaries[1:]))):
            raise WorkbookError(f'AssessmentBoundaries {aid}: require grades 1–7, starting at 0%, with strictly increasing thresholds.')

    resource_ids = set()
    for n, row in tables.get('Resources', []):
        loc = f'Resources row {n}'
        rid = _id(row['ResourceID'], loc)
        if rid in resource_ids:
            raise WorkbookError(f'{loc}: duplicate resource ID.')
        resource_ids.add(rid)
        data.resources.append(Resource(rid, _required(row['Topic'], loc + ' Topic'),
                                       _required(row['Title'], loc + ' Title'),
                                       _required(row['Content'], loc + ' Content')))

    ticket_ids = set()
    for n, row in tables.get('ExitTickets', []):
        loc = f'ExitTickets row {n}'
        aid, sid = reference(row, loc)
        if (aid, sid) not in data.memberships:
            raise WorkbookError(f'{loc}: exit ticket requires explicit assessment membership.')
        tid = _id(row['TicketID'], loc)
        if tid in ticket_ids:
            raise WorkbookError(f'{loc}: duplicate ticket ID.')
        ticket_ids.add(tid)
        day = row['Date']
        if isinstance(day, datetime):
            day = day.date()
        if not isinstance(day, date):
            try:
                day = date.fromisoformat(str(day))
            except ValueError:
                raise WorkbookError(f'{loc}: Date must be an Excel date or YYYY-MM-DD.') from None
        data.exit_tickets.append(ExitTicket(tid, sid, aid, day.isoformat(),
            _required(row['Prompt'], loc + ' Prompt'), _text(row['Response']), _text(row['Feedback'])))

    attempt_ids = set()
    for n, row in tables.get('RevisionAttempts', []):
        loc = f'RevisionAttempts row {n}'
        aid, sid = reference(row, loc)
        attempt_id = _id(row['AttemptID'], loc)
        if attempt_id in attempt_ids:
            raise WorkbookError(f'{loc}: duplicate attempt ID.')
        attempt_ids.add(attempt_id)
        qid = _id(row['QuestionID'], loc)
        original = next((r for r in data.question_results if (r.student_id, r.assessment_id, r.question_id)
                         == (sid, aid, qid) and r.status == 'graded'), None)
        if not original:
            raise WorkbookError(f'{loc}: revision requires an original graded question result.')
        day = row['Date']
        if isinstance(day, datetime):
            day = day.date()
        if not isinstance(day, date):
            try:
                day = date.fromisoformat(str(day))
            except ValueError:
                raise WorkbookError(f'{loc}: invalid date.') from None
        if day < data.assessments[aid].date:
            raise WorkbookError(f'{loc}: attempt precedes assessment.')
        score = _number(row['Score'], loc + ' Score')
        maximum = data.questions[qid].marks
        if score > maximum:
            raise WorkbookError(f'{loc}: attempt score exceeds question Marks.')
        data.revision_attempts.append(dict(id=attempt_id, student=sid, assessment=aid, question=qid,
                                          day=day.isoformat(), score=score, maximum=maximum,
                                          original=original.score, note=_text(row['Note'])))

    # Totals remain authoritative inputs; complete question evidence is compared, never substituted.
    summaries = {(r.assessment_id, r.student_id): r for r in data.results}
    if 'QuestionResults' in tables:
        for (aid, sid), level in data.memberships.items():
            expected = {q.id for q in data.questions.values() if q.assessment_id == aid and eligible(q, level)}
            rows = [r for r in data.question_results if (r.assessment_id, r.student_id) == (aid, sid)]
            if not expected or {r.question_id for r in rows} != expected or any(r.status not in {'graded', 'exempt'} for r in rows):
                data.warnings.append(f'Reconciliation {aid}/{sid}: incomplete question evidence; totals were not reconciled.')
                continue
            graded = [r for r in rows if r.status == 'graded']
            score = sum(r.score for r in graded)
            maximum = sum(data.questions[r.question_id].marks for r in graded)
            summary = summaries.get((aid, sid))
            if summary is None:
                data.warnings.append(f'Reconciliation {aid}/{sid}: no assessment summary; question results do not create one automatically.')
            elif summary.status == 'graded' and (not isclose(summary.score, score) or not isclose(summary.max_score, maximum)):
                data.warnings.append(f'Reconciliation {aid}/{sid}: question total {score:g}/{maximum:g} differs from Results {summary.score:g}/{summary.max_score:g}; Results retained.')
            elif summary.status != 'graded' and graded:
                data.warnings.append(f'Reconciliation {aid}/{sid}: graded questions conflict with summary status {summary.status}; Results retained.')
