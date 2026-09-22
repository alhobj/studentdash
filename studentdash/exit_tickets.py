"""Exit-ticket use cases and allowlisted views, independent of Flask."""
from .exit_schema import TicketError, parse_ticket, public_question


def definition(ticket):
    return {key: ticket[key] for key in ('title', 'subject', 'topic', 'subtopic', 'allow_answer_review', 'questions')}


def public_ticket(ticket):
    result = {k: ticket[k] for k in ('id', 'title', 'subject', 'topic', 'subtopic', 'version')}
    result['questions'] = [public_question(q) for q in ticket['questions']]
    return result


def score_view(ticket, submission, reveal=False):
    answers = {a['question_id']: a for a in submission['answers']}
    rows = []
    for q in ticket['questions']:
        a = answers[q['id']]
        awarded = a['teacher_score'] if a['teacher_score'] is not None else a['auto_score']
        row = dict(question=public_question(q), answer=a['value'], score=awarded, feedback=a['feedback'],
                   reviewed=a['teacher_score'] is not None, automatic=a['auto_score'] is not None,
                   version=a['version'])
        if reveal:
            if 'answer' in q:
                row['correct_answer'] = q['answer']
            elif q.get('accepted_answers'):
                row['correct_answer'] = q['accepted_answers']
        rows.append(row)
    pending = sum(row['score'] is None for row in rows)
    score = sum(row['score'] or 0 for row in rows)
    maximum = sum(q['marks'] for q in ticket['questions'])
    return dict(ticket_id=ticket['id'], title=ticket['title'], topic=ticket['topic'], subtopic=ticket['subtopic'],
                date=submission['submitted_at'], answers=rows, score=score, maximum=maximum, pending=pending,
                percent=100 * score / maximum if not pending else None, allow_answer_review=bool(reveal))


class TicketService:
    def __init__(self, repository):
        self.repo = repository

    def save(self, raw, audience, students, ticket_id=None, version=None):
        parsed = parse_ticket(raw)
        assigned = set()
        for target in audience:
            if target == 'all':
                assigned.update(students)
            elif target.startswith('class:'):
                members = {sid for sid, s in students.items() if s.class_name == target[6:]}
                if not members:
                    raise TicketError('The selected class is no longer in the workbook.')
                assigned.update(members)
            elif target.startswith('student:') and target[8:] in students:
                assigned.add(target[8:])
            else:
                raise TicketError('Choose students or classes from the current workbook.')
        return self.repo.save(parsed, assigned, ticket_id, version)

    def available(self, ticket_id, sid):
        ticket = self.repo.get(ticket_id)
        if ticket['status'] != 'published' or sid not in ticket['assignments']:
            raise KeyError('Ticket not available')
        return public_ticket(ticket)

    def history(self, ticket_id, sid):
        ticket = self.repo.get(ticket_id)
        submission = self.repo.submission(ticket_id, sid)
        if not submission:
            raise KeyError('Submission not found')
        return score_view(ticket, submission, bool(ticket['allow_answer_review']))

    def student_home(self, sid):
        available, completed = [], []
        for ticket in self.repo.list():
            if sid not in ticket['assignments']:
                continue
            submission = self.repo.submission(ticket['id'], sid)
            if submission:
                completed.append(score_view(ticket, submission, bool(ticket['allow_answer_review'])))
            elif ticket['status'] == 'published':
                available.append({k: ticket[k] for k in ('id', 'title', 'subject', 'topic', 'subtopic')})
        return available, completed

    def results(self, ticket_id):
        ticket = self.repo.get(ticket_id)
        submissions = self.repo.submissions(ticket_id)
        results = [dict(score_view(ticket, s), student_id=s['student_id']) for s in submissions]
        complete = [r for r in results if not r['pending']]
        items = []
        for q in ticket['questions']:
            rows = [next(a for a in r['answers'] if a['question']['id'] == q['id']) for r in results]
            scored = [a for a in rows if a['score'] is not None]
            items.append(dict(question=public_question(q), graded=len(scored), pending=len(rows) - len(scored),
                              correct=sum(a['score'] == q['marks'] for a in scored),
                              average=sum(a['score'] for a in scored) / len(scored) if scored else None))
        return dict(ticket=ticket, submissions=results, submitted=len(results), not_submitted=len(ticket['assignments']) - len(results),
                    complete=len(complete), average=sum(r['percent'] for r in complete) / len(complete) if complete else None,
                    items=items)


def progress_rows(data, sid, completed):
    groups = {}
    for result in completed:
        if result['pending']:
            continue
        key = result['topic'], result['subtopic']
        group = groups.setdefault(key, dict(topic=key[0], subtopic=key[1], score=0, maximum=0, count=0))
        group['score'] += result['score']
        group['maximum'] += result['maximum']
        group['count'] += 1
    for key, group in groups.items():
        formal = [r for r in data.question_results if r.student_id == sid and r.status == 'graded'
                  and (data.questions[r.question_id].topic, data.questions[r.question_id].subtopic) == key]
        maximum = sum(data.questions[r.question_id].marks for r in formal)
        group['assessment_percent'] = 100 * sum(r.score for r in formal) / maximum if maximum else None
        group['exit_percent'] = 100 * group['score'] / group['maximum']
    return list(groups.values())
