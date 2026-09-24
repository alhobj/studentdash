# Studentdash

Studentdash is being developed as a subject-independent, curriculum-independent
system. IB Chemistry is the first implementation and test profile. See the
[architecture direction and migration plan](docs/ARCHITECTURE.md) for current
assumptions and the configuration-driven target. Local assessment usability comes
first; public/hosted development is deferred.

A local Python dashboard prototype developed entirely with fictional learners and
assessment records. Excel is the input; each learner gets a self-contained HTML
snapshot. A local Flask workspace lets teachers review validation notes, generate
snapshots and preview them.

The [local exit-ticket workflow](docs/EXIT_TICKETS.md) adds one-block JSON import,
preview/publish, fictional student sessions, submissions, deterministic marking and
teacher review. Use its reusable ChatGPT prompt and `examples/exit-ticket.json`.

Read the [complete system and classroom-use guide](docs/SYSTEM_GUIDE.md) for the data
model, feedback workflow, revision history, operating instructions and readiness checklist.

For colleagues, use the [one-page teacher overview](docs/TEACHER_OVERVIEW.md).
Open the [ten-design gallery](examples/layouts/index.html) locally to compare
student dashboard layouts with identical fictional content. Rebuild these offline
previews with `python build_layout_previews.py`.

Exit tickets also support [audited corrections, linked retakes and answer-release
controls](docs/FOLLOW_UP.md). See [TODO](TODO.md) for suggested next milestones.

## Enter your first assessment

Prefer **Import assessment** to upload a PDF/DOCX test, review its questions and
classification suggestions, and continue into score entry. **Create manually**
remains available. See [Import a test document](docs/ASSESSMENT_IMPORT.md) for the
workflow and supplied fictional examples.

For your own class, start `.\.venv\Scripts\python.exe teacher.py` and open
**http://127.0.0.1:5000/classes**. Follow [Enter your first assessment](docs/FIRST_ASSESSMENT.md)
for class setup, question classification, spreadsheet score entry and dashboards.
No workbook preparation or import commands are needed for this workflow.

## Run the fictional demo

Python 3.10 or newer is required. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python create_example_workbook.py
.\.venv\Scripts\python seed_exit_tickets.py
.\.venv\Scripts\python generate.py
.\.venv\Scripts\python teacher.py
```

Open http://127.0.0.1:5000 or open `output/student2001.html` directly after generation.
On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python`.
The generator creates `data/classroom.xlsx` and refuses to overwrite an existing
workbook. It never reads another workbook. The application defaults to that file;
it no longer falls back to `master.xlsx` or the former private-workbook filename.
Existing workbooks are left untouched. All tests use generated fictional fixtures.

The default demo contains 24 learners in four SL/HL class groups, six assessments
from April to September 2026, 36 questions, 665 question records and 34 revision attempts.
It includes varied performance, graded zeroes, exemptions, absent/pending/missing work
and genuinely unrecorded questions. `--small` creates the original two-learner fixture
at `data/fictional.xlsx`; use the workbook environment override to select that fixture.

## What is implemented

- Assessment history, weighted overall percentage and suggested grades.
- Validated question results joined by stable IDs, with explicit SL/HL membership.
- Topic, subtopic and command-term breakdowns with inspectable evidence.
- Offline assessment filtering: totals, evidence, resources and exit tickets all
  change together. Without JavaScript, the all-assessments view remains available.
- Strength/work-on hints require at least two graded questions in a command term.
  Strength means at least 75%; work-on means below 50%. These are limited learning
  hints, not diagnoses. Sparse categories display an evidence notice.
- Topic-matched revision resources embedded in the snapshot for offline use.
- Student-specific exit-ticket responses and teacher feedback, imported from Excel.
- Grouped teacher validation notes, a legacy demonstration toggle, generation time
  and a stale-snapshot notice when the workbook content changes.
- Assessment-specific grade boundaries with global defaults.
- A live teacher class overview with assessment/class filters, individual performance,
  recorded question statuses and explicitly unrecorded question counts.
- Question review ordered by graded percentage, showing how many eligible learners
  have graded evidence. SL/HL membership determines applicability; small samples are labelled.
- Student revision plans: up to three graded questions with the most lost marks,
  with matching topic resources and a checklist. Ungraded work never becomes a retry task.
- A print button for the currently selected student assessment view.
- Editable per-learner, per-assessment teacher comments and revision tasks with
  save draft, preview and publish states. Published feedback enters the next generation.
- Revision-attempt recording and history showing original and new marks side by side.
- Freshness reasons for workbook, published feedback, attempts, template/calculation
  changes, and missing or modified snapshot files.
- Interactive local exit tickets supporting MCQ, exact multiple-select, true/false,
  numeric, accepted short answers and manually reviewed text. Teacher assignment,
  publication, submissions and results are stored in the paired SQLite workspace.
- Explicit fictional student sessions, per-student histories and separate exit-ticket
  evidence. Offline HTML files do not submit answers, and formal scores are unchanged.

Revision checks are stored in the browser on the current device when storage is
available. They are not teacher submissions and do not affect scores. The same task
stays checked across assessment filters and regeneration; changing its question text
or score starts a fresh task. Browser storage restrictions fall back to checks that
last while the page is open. Moving to another browser or file location may not carry
the checks across.

## Workbook tables

Headers belong in row 1. IDs contain letters, digits, underscores or hyphens.
Question IDs are globally unique; student IDs cannot collide ignoring case.
The five original sheets remain required, and older fictional fixtures still work.

| Sheet | Columns |
|---|---|
| Students | StudentID, StudentName, Email, Class |
| Assessments | AssessmentID, AssessmentName, Date, Subject, Marks |
| Questions | QuestionID, AssessmentID, QuestionNumber, SLHL, Text, Answer, Marks, Topic, Subtopic, QuestionType, ActionVerb, AutoMark |
| Results | AssessmentID, StudentID, Score, MaxScore, Status |
| Grade boundaries | Grade, Percent |
| Memberships | AssessmentID, StudentID, Level |
| QuestionResults | AssessmentID, QuestionID, StudentID, Score, Status |
| AssessmentBoundaries | AssessmentID, Grade, Percent |
| Resources | ResourceID, Topic, Title, Content |
| ExitTickets | TicketID, StudentID, AssessmentID, Date, Prompt, Response, Feedback |
| RevisionAttempts | AttemptID, StudentID, AssessmentID, QuestionID, Date, Score, Note |

The last seven tables are optional extensions. QuestionResults requires Memberships;
exit-ticket rows also require membership. Each assessment/student membership is
unique and has Level SL or HL. Question SLHL is SL, HL or BOTH. HL members can take
SL and HL questions; SL members cannot take HL-only questions. BOTH applies to either.
Class names and row positions are never used to infer these relationships.

Linked questions require positive Marks, text, topic, subtopic and a command term.
MCQ belongs in QuestionType, not ActionVerb. Topic names match resources exactly.
Resources contain teacher-authored text and practice prompts, not fetched content.
The Excel ExitTickets sheet is imported reflection history. Interactive local exit
tickets use separate SQLite tables and Flask forms; they never write to this sheet.
RevisionAttempts imports fictional retry history against original graded question
results. Attempts recorded in the teacher interface are stored separately in SQLite.

## Scoring and reconciliation

| Status | Score | Counts in question-category percentage |
|---|---|---|
| graded | Required, between zero and question Marks | Yes, including zero |
| missing | Blank | No |
| absent | Blank | No |
| exempt | Blank | No |
| pending | Blank | No |

Category percentages are total earned marks divided by total possible marks for
**graded questions only**. Missing rows are not invented. Non-graded questions
remain visible in question records. These percentages describe available evidence,
not assessment completion or an official grade.

Results remains the source for assessment totals. Only graded Results contribute
to overall performance, calculated as total earned / total possible rather than
an average of rounded percentages. The importer compares question totals against
Results only when all questions applicable to that membership have a graded or
exempt record. Exempt questions contribute neither score nor denominator.
Disagreements and incomplete evidence produce teacher notes; no totals are replaced.
Membership can yield different SL/HL maximums, and exemptions can reduce them further.
Assessments.Marks describes the full question set; Results.MaxScore describes the
recorded student summary.

Each boundary set must contain grades 1 through 7 exactly once, with strictly
increasing inclusive minimum percentages, starting at zero for grade 1. Rows in
AssessmentBoundaries override the global set for that assessment only. Suggested
grades remain separate from official teacher or final grades, which are not modeled.

The legacy Results spelling Stratus is accepted. Blank summary status is interpreted
as graded if a score exists, otherwise pending, with a warning. QuestionResults
requires an explicit status. Formula caches are read, never calculated by openpyxl;
missing caches or Excel errors are validation failures. Recalculate and save in Excel
before importing formulas. Saved-cache freshness cannot be established automatically.

## Local review workflow

1. Edit the fictional workbook and save it.
2. Open the teacher workspace and review grouped data-quality notes.
   Use the class overview and question review to identify follow-up: missing, pending,
   absent and exempt are distinct from a question with no record at all. A low question
   percentage is evidence to inspect, not an automatic diagnosis or learner ranking.
3. Generate snapshots after checking totals and question evidence.
4. Open a learner preview and use its assessment selector to inspect each assessment.
5. Use **Feedback & revisions** next to a learner to save a draft, preview it, and
   publish it locally. Regenerate dashboards to distribute the published content.
6. Record later revision attempts there without changing the original grades.

Teacher drafts, published feedback and interface-recorded attempts are stored in
`<workbook-name>.workspace.sqlite3` beside the workbook. Keep that file with the workbook
when backing up or moving a course. Do not reuse learner/assessment IDs for a different
cohort in the same workbook/workspace pair. Stale draft versions are rejected to avoid
overwriting edits made in another browser tab. This is a single-teacher local workflow.

Generation validates and renders every page before replacing existing output.
It removes obsolete `student*.html` files in the dedicated output folder.
Keep unrelated files outside that filename pattern. `generation.json` stores the
input fingerprints, snapshot file fingerprints, generation time and demonstration
setting. The teacher workspace lists stale reasons and filenames needing refresh.
Draft edits do not mark student exports stale; published changes do. Regeneration
rebuilds every current learner, rather than performing an incremental update.
Generation is local publication of files; it does not send anything to students.

## Architecture

- `studentdash/excel.py`: workbook reading, cache checks and core validation.
- `studentdash/question_data.py`: membership, question results, resources, tickets,
  boundary overrides and summary reconciliation.
- `studentdash/models.py`: typed workbook records.
- `studentdash/analytics.py`: student-only views and evidence calculations.
- `studentdash/overview.py`: teacher-only cohort and question review calculations.
- `studentdash/workspace.py`: SQLite draft/publication state and revision recording.
- `studentdash/freshness.py`: source fingerprints and stale reasons.
- `studentdash/exit_schema.py`, `exit_tickets.py`: structured import, marking and ticket views.
- `studentdash/exit_store.py`, `exit_routes.py`: ticket SQLite adapter and local interactive routes.
- `studentdash/render.py`, `templates/`: escaped HTML and offline filtering.
- `studentdash/teacher.py`: local review, generation and preview routes.
- `create_example_workbook.py`, `studentdash/demo.py`: repeatable fictional datasets.

Only allowlisted student views reach student templates. Names, emails, answer keys,
other learners' reflections and unrelated workbook content are excluded. Resources
are shared teacher content. Pages load no external scripts, styles or services.
The server binds to loopback with debug disabled, protects generation using CSRF,
rejects foreign Host headers and prevents caching of previews. The exit-ticket student
session is a development simulation, not authentication. There is no school login,
Microsoft integration, production student portal or network distribution workflow.

## Configuration and checks

```powershell
$env:STUDENTDASH_WORKBOOK = 'C:\path\to\fictional.xlsx'
$env:STUDENTDASH_OUTPUT = 'C:\path\to\demo-output'
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Relative configuration paths are resolved from the repository, not the working
directory. Excel inputs, generated snapshots and common exports are excluded from
Git. CI runs fictional-data tests on Windows and Linux with Python 3.10 and 3.13.

`generate.py --no-examples` disables the separate legacy practice demonstration.
Normalized workbooks with memberships always use their own question records,
including empty states; they never receive invented practice scores.

Before real classroom use, complete the pilot and operating checks in the system guide.
Online use requires authentication, per-student authorization and a deployment design;
the current local teacher server must not be exposed as a student portal.
