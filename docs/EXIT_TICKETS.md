# Local exit tickets

This milestone adds a complete local loop: import one JSON block, preview, publish,
submit as a fictional student, mark automatically where configured, review written
answers, and view separate exit-ticket evidence. It does not use an LLM to mark
responses and does not connect to Microsoft services.

## Launch and try it

From the project directory:

```powershell
# On a fresh checkout only: create the environment, dependencies and fictional class.
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python create_example_workbook.py

# Add the example ticket as a draft; repeating this keeps existing work.
.\.venv\Scripts\python seed_exit_tickets.py --workbook data\classroom.xlsx
.\.venv\Scripts\python teacher.py
```

If the environment and `data/classroom.xlsx` already exist, skip their creation.
Open http://127.0.0.1:5000 and select **Open Exit Tickets**. The seeded ticket is
**Fictional ionic bonding check**. It has six questions covering all supported types
and is initially assigned to the current fictional class. It is not published and
contains no invented student submissions.

To use a different fictional workbook, set `STUDENTDASH_WORKBOOK` before launching.
The seed command's `--workbook` flag selects its target but does not change the
server's environment configuration. Restart an already-running server after code
changes. No separate database installation is required.

### Short manual test

1. Select **Create exit ticket**. Copy all of `examples/exit-ticket.json` into the
   paste box, choose a class or leave **All current fictional students**, and select
   **Import & Preview**. Alternatively open the seeded draft's preview.
2. Inspect the exact student form, marking rules and recipient list. Select
   **Publish**. The ticket now appears as available to assigned students.
3. In Exit Tickets, select fictional learner **2001** under **Act as a fictional
   student**. The local page is `/student/student2001`. Open the available ticket.
4. Answer: `Mg2+`; select `Cl-` and `O2-`; choose True; enter `-2`; enter `cation`;
   write an explanation mentioning attraction between oppositely charged ions and
   the energy required to overcome it. Select **Submit exit ticket**.
5. Confirm that the answers were saved. Five automatic marks should be awarded;
   the two-mark written response should be awaiting review. Refreshing or repeating
   the submit request must not create another submission.
6. Select **Return to teacher simulation**. Open the ticket's **Results & review**,
   then **Review responses** for 2001. Award the written response 1 or 1.5 marks out
   of 2 and add student-visible feedback. Save it.
7. Act as 2001 again. Open the completed ticket. Verify the final total and feedback,
   and the separate exit-ticket percentage on the local dashboard. Formal assessment
   scores must remain unchanged.
8. Return to teacher simulation and unpublish the ticket. An unsubmitted assigned
   student must no longer see it as available. Student 2001 must still be able to
   read their stored submission and result.

The UI uses one simulated identity per browser session. Tabs share that session;
switching roles affects all tabs. Use separate browser profiles for simultaneous
teacher and student sessions. Opening a student's URL alone does not select them.

## Exact JSON format

Paste one JSON object, optionally inside a single `json` Markdown code fence.
Do not include prose before or after it. Duplicate field names and unsupported
fields are rejected rather than silently ignored.

### Ticket fields

| Field | Required | Type and meaning |
|---|---|---|
| `title` | Yes | Non-empty string, at most 200 characters |
| `subject` | Yes | Non-empty string, at most 200 characters |
| `topic` | Yes | Non-empty string, at most 200 characters |
| `subtopic` | Yes | Non-empty string, at most 200 characters |
| `allow_answer_review` | No | Boolean; defaults to `false`. If true, correct answers/accepted wording may be shown to that student after submission |
| `questions` | Yes | Array of 1–30 question objects |

The full JSON block is limited to 64,000 characters. Ticket IDs, creation time,
publication time, status and edit version are assigned by the application.

### Common question fields

| Field | Required | Type and meaning |
|---|---|---|
| `id` | No on initial import | 1–80 letters, digits, underscores or hyphens; unique within the ticket. Missing IDs become `q1`, `q2`, etc. Keep them in later edits |
| `type` | Yes | One of the six types below |
| `question` | Yes | Non-empty string, at most 2,000 characters |
| `marks` | Yes | Finite JSON number greater than 0 and at most 100; fractional marks are allowed |
| `action_verb` | Yes | Non-empty string, at most 80 characters |
| `manual_marking` | No | Defaults according to type. `text` requires true; short answers without accepted wording require manual review. The other four types are automatically marked |

### Type-specific fields and marking

| Type | Additional fields | Marking rule |
|---|---|---|
| `multiple_choice` | `options`: 2–12 unique strings; `answer`: exactly one option | All marks for an exact match, otherwise zero |
| `multiple_select` | `options`: 2–12 unique strings; `answer`: non-empty list of distinct correct options | All marks only for exactly the correct set, independent of order. No partial credit |
| `true_false` | `answer`: JSON `true` or `false`, not a quoted string | All marks for the correct Boolean, otherwise zero |
| `number` | `answer`: finite JSON number; optional `tolerance`: non-negative finite number, default 0 | Decimal numeric comparison using absolute tolerance. No unit parsing or expression evaluation |
| `short_answer` | Optional `accepted_answers`: up to 20 non-empty strings; optional `case_sensitive`: Boolean, default true | With accepted wording: exact match after trimming outer whitespace. Case is ignored only when explicitly configured false. Without accepted wording: teacher review |
| `text` | No answer key | Teacher awards 0 through the question's marks, including partial marks; never automatically scored |

Options and accepted short answers are limited to 300 characters each. Do not combine
non-empty `accepted_answers` with `manual_marking: true`. To use manual short-answer
marking, omit accepted answers. `manual_marking: false` on a text question is rejected.
Fields intended for another question type are rejected.

There is no spelling correction, semantic similarity, inferred synonym matching,
negative marking, unit conversion or AI marking. `cation` does not accept `a cation`
unless both strings are explicitly listed. Number tolerance is absolute: with an
answer of 0.30 and tolerance 0.01, 0.31 is accepted and 0.311 is not.

Student inputs are required for every question. Text responses are limited to 4,000
characters, short answers to 300, and numeric input to 80 characters. Non-finite
numbers, unknown options and duplicate multiple-select options are rejected.

### Minimal example

```json
{
  "title": "S2.2 Ionic bonding",
  "subject": "Chemistry",
  "topic": "S2",
  "subtopic": "S2.2",
  "allow_answer_review": false,
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "Which ion does magnesium usually form?",
      "options": ["Mg+", "Mg2+", "Mg3+", "Mg-"],
      "answer": "Mg2+",
      "marks": 1,
      "action_verb": "State"
    },
    {
      "id": "q2",
      "type": "number",
      "question": "What is the charge of an oxide ion?",
      "answer": -2,
      "tolerance": 0,
      "marks": 1,
      "action_verb": "State"
    },
    {
      "id": "q3",
      "type": "text",
      "question": "Explain why MgO has a high melting point.",
      "marks": 2,
      "action_verb": "Explain",
      "manual_marking": true
    }
  ]
}
```

Topic and subtopic are ticket-wide in this milestone. They are not validated against
an official syllabus. Match the workbook labels exactly if you want formal and
exit-ticket evidence to appear side by side for the same category. A mismatch shows
no matching formal evidence; it does not trigger a guessed classification.

## Reusable ChatGPT prompt

Copy this prompt and replace the bracketed details:

```text
Create a Studentdash exit ticket on [topic] for [class/level] with [number] questions.
Use subject "[subject]", topic "[exact topic label]", and subtopic "[exact subtopic label]".
Return ONE valid JSON object only, with no explanation before or after it.

Root fields: title, subject, topic, subtopic, allow_answer_review:false, questions.
Each question needs: id (q1, q2, ...), type, question, marks, action_verb.
Use a mix of automatic checks and at least one written explanation for teacher review.

Supported types:
- multiple_choice: options array and answer equal to one option.
- multiple_select: options array and answer array containing the exact correct set.
- true_false: answer is the Boolean true or false, not a string.
- number: answer is a number; tolerance is a non-negative absolute tolerance, normally 0.
- short_answer: either accepted_answers containing precise accepted strings and
  case_sensitive:true, or manual_marking:true with no accepted_answers.
- text: manual_marking:true, with no answer field.

Multiple choice/select options must be unique. Use positive numeric marks.
Do not include student data, rubrics, explanations of correct answers, HTML or extra fields.
Keep the whole ticket below 30 questions. Automatic marking is exact and conservative:
do not use short-answer automatic marking for responses with many reasonable phrasings.
Check all answer keys and ensure each question can be answered without missing context.
```

Review the generated content, applicability and answer keys before publishing.
The import parser validates structure; it cannot determine whether chemistry content
or the question's expected answer is pedagogically correct.

## Publication and assignment rules

- Import creates a draft and immediately opens its preview. **Save Draft & Preview**
  edits the whole structured block; individual-question paste operations are unnecessary.
- Assign to all current students, one or more class labels, or individual students.
  Class selections resolve to explicit IDs when saved; future roster changes do not
  silently add recipients. Unassigned students cannot open or submit the ticket.
- Publication requires at least one assigned student. Drafts are never student-visible.
- Published tickets cannot be edited. Unpublish first if nobody has submitted.
- Once any submission exists, definitions, marking policy and assignments are frozen.
  Create a new ticket for changed content. This preserves question IDs, keys and marks
  against which existing answers were evaluated.
- Unpublishing stops new submissions. It does not delete answers, hide the student's
  own completed history or prevent teacher marking. Republish resumes availability
  for the same assigned students who have not already submitted.
- One submission per student per ticket is enforced by a database uniqueness constraint
  and a transaction. Retrying a submitted request returns the existing submission;
  it never replaces stored answers. There are no retakes or reset controls yet.
- Edit/publication versions reject stale forms. A ticket changed while the form was
  open must be reopened before its first submission.

## Results and evidence

The results page lists every assigned student, submitted/not-submitted counts,
question-level full-credit counts, graded-response counts, average awarded marks and
manual-review counts. The overall mean percentage uses **fully marked submissions
only**, with that denominator displayed. Pending written responses are never scored
as zero to produce a provisional total percentage.

Teachers can award partial marks and a comment explicitly labelled student-visible.
An unreviewed answer has no teacher score; a reviewed zero is a real zero. Review
versions prevent one tab from silently overwriting another. Automatically awarded
marks cannot be overridden in this milestone.

The local student dashboard shows available and completed tickets. Its history contains
only the current student's answers, scores and teacher feedback. Automatic marks can
appear immediately, but a final total and progress contribution require all questions
to be marked. Correct-answer review is disabled by default and only included in the
post-submission view when explicitly enabled for the ticket.

Progress aggregates fully marked exit tickets by exact topic/subtopic, using earned
marks divided by available marks. It shows the corresponding graded formal-question
percentage separately. No combined mastery score, final-grade adjustment or automatic
replacement of formal assessment records is performed.

The offline generator remains unchanged as a workflow: its HTML files contain no
submission mechanism. Local ticket submissions/results live in the interactive app,
not the workbook or offline snapshots. The workbook's existing `ExitTickets` sheet
remains historical imported reflection data, distinct from these interactive tickets.

## Storage and replaceable architecture

The existing paired SQLite workspace gains these additive tables:

| Table | Purpose |
|---|---|
| `et_tickets` | ID, metadata, created/published timestamps, state, answer-review policy and edit version |
| `et_questions` | Stable question ID within a ticket, ordering and validated definition, including marking key |
| `et_assignments` | Explicit ticket/student pairs |
| `et_submissions` | Submission ID, ticket/student pair, submitted timestamp; unique per ticket/student |
| `et_answers` | Submitted value, separate automatic and teacher scores, public feedback, review timestamp and review version |

All values use parameterized SQL. Foreign keys are enabled in the ticket adapter.
Publication checks and submission inserts run in the same write transaction, so an
unpublish racing with a submission cannot bypass the stored publication state.
Excel files are read for the current fictional roster and formal evidence only;
submissions never write to them.

`exit_schema.py` contains pure parsing, validation, public-field projection and marking
functions. `exit_tickets.py` provides use cases and student/teacher result views.
`exit_store.py` is the SQLite adapter; its transaction methods call the pure marking
functions. `exit_routes.py` handles Flask forms and the simulated session identity.
Business rules are not embedded in templates.

A later Microsoft milestone would implement an identity adapter and an alternative
repository with equivalent conditional writes, idempotency and assignment checks.
The JSON schema, deterministic marking functions and student-scoped views can remain.
Storage replacement must preserve atomic state checks and submission uniqueness;
merely mapping fields into another list or table would not preserve those guarantees.
No Microsoft adapter, real login or hosting configuration is implemented here.

## Simulation limitations

The server still binds to loopback. The teacher explicitly selects a fictional
student, which stores that StudentID in the signed Flask session. Student routes
compare the URL identity to the session identity. They do not trust an ID supplied
in a form. While in student mode, teacher pages, editor routes and static teacher
previews are blocked until **Return to teacher simulation** is deliberately selected.

This is **not authentication**. Anyone with local access can deliberately return to
teacher mode, or open a fresh teacher session. Tabs share identity, the secret is
generated at server startup, and a restart resets sessions. There are no passwords,
school identities, durable user roles or production authorization. Do not expose
this development app to students over a network.

Student templates receive allowlisted question fields without keys before submission.
Keys are only added to a student's own post-submission view when review is enabled.
Drafts, other students' answers, teacher-only pages and feedback drafts are excluded
from student routes. All mutation forms use CSRF tokens and workbook/free-text values
are escaped. These controls exercise the intended boundary inside the simulation;
they are not a claim that the simulation is a secure student portal.

## Decisions to settle next

Decide whether to allow retakes; when correct answers should be released (immediately,
after marking, or after closure); whether to offer partial multiple-select credit;
how teacher corrections and automatic-score overrides should be audited; whether
assignments can change after submissions; and whether each question needs its own
topic/subtopic. Evidence weighting remains deliberately undecided.

Recommended next milestone: test this local workflow with realistic fictional
classroom scenarios, then add agreed retake/correction and answer-release policies
with an audit history. Microsoft integration remains a separate, later milestone.
