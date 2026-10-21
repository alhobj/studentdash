# Portable practice and classroom packages

## Student workflow

Open **My practice** from either subject's practice pages. The journal includes
all 712 small-step and repeat questions plus 1,220 authored MCQs (440 chemistry and 780 mathematics). Interactive explorers, longer challenges
and written responses remain available in the hub; their state is not yet saved
by this journal. No progress is uploaded automatically and voting is not included.

- **Resume saved session** returns to the questions and draft answers left in a
  session. Short answers entered on the original foundation pages are also saved.
- **Practise my mistakes** selects up to six questions whose latest attempt was
  incorrect or assisted. **Try another using the same method** offers an unattempted
  question from the same topic and question type.
- **Mixed revision** combines up to two questions needing another attempt, up to
  two unattempted questions from the most recently practised topic, and older or
  unattempted work from other topics. It is a transparent selection rule, not an
  adaptive mastery diagnosis.
- A recorded answer is **correct independently**, **completed with help or retry**,
  or **needs another attempt**. Opening a hint/answer or correcting an error marks
  that attempt as assisted. **Retry independently with a blank answer** starts a
  fresh self-reported attempt; it does not prove that the answer was forgotten.
- The journal accepts decimal points or commas and scientific notation such as
  `1.2e3`. Selected unit-bearing questions accept explicit unit aliases from their
  authored content. Wrong units, sign errors, likely scale errors and near answers
  receive different feedback. This is not a symbolic algebra or written-reasoning
  marker, and it does not assess significant-figure notation.

Practice does not change assessment marks. The assessment-based next-step panel
links to a focused journal session while keeping the two evidence sources separate.

## Saving and moving computers

Browser saving is best-effort: local-file storage behavior differs between browsers,
and a renamed/moved file may have different storage. Export **My progress** before
moving files, changing computers, clearing browser data or leaving a shared computer.
On the other computer, open the same collection and import that JSON file. Import
merges attempt IDs without duplicating them and restores drafts/session positions;
an invalid file leaves existing records unchanged. Unknown question IDs are retained
in progress exports but do not appear in the current collection's totals.

On a shared computer, export first and use **Clear this browser** when finished.
There is no account separation. A browser-saving failure is displayed explicitly;
export still works. Keep progress files private. Prefer one active practice tab at
a time; this is a local file workflow, not a synchronised multi-device account.

Question IDs include the subject, lesson, type and a hash of the prompt/answer.
Authored workbook MCQs retain their original question IDs. For other journal questions,
reordering does not detach evidence; changing a prompt/answer creates a new question
version. Hints and unit-alias edits do not invalidate an existing question ID.

## Teacher assignments and completion reports

In My practice, open **Choose questions or create a teacher assignment**. Filter
the collection, select questions, enter a title and instructions, and export either:

- An assignment JSON that students open in the same subject collection/version.
- A standalone HTML assignment containing the selected questions and runtime.
  Download it and open it locally; no adjacent resources are required.

Students select **Start assignment**, then **Export completion report** and upload
the report through the school's file-sharing workflow. A teacher can open it using
**Review a student completion report** in the matching subject's My practice page.
The review shows answer history and independent/assisted status. It neither imports
the report into the teacher's personal progress nor changes assessment marks.

Reports and progress are self-reported, editable files. They are useful for feedback,
not authenticated submissions or secure examinations. Assignment files contain
worked answers; the system deliberately supports learning rather than secret tests.

## Distribution

The local teacher app's **Packages & workspace backup** page provides:

1. A public classroom ZIP containing practice files and an entry page, without
   class databases or student records.
2. A private learner ZIP containing a freshly rendered snapshot for exactly one
   selected student and public practice resources. Deliver it only to that learner.

Extract the complete ZIP and open `index.html`. Keep its resources folder beside it.
The files-only SharePoint workflow is upload/download, not a hosted web application;
it adds no shared server state, school login or real-time synchronisation.

## Backup and restore

**Download workspace backup** captures the selected source workbook or managed
class and its accompanying `.workspace.sqlite3`. This includes feedback, revision
attempts and any exit tickets stored in that workspace. Managed-class original
imports are contained inside the class database. Each class/workbook requires its
own backup. Application code, unrelated classes and generated snapshots are excluded;
keep the application version too and regenerate snapshots after recovery.

SQLite databases are copied through SQLite's backup API while write reservations
prevent concurrent changes to the pair. Integrity checks and per-file SHA-256 hashes
detect corruption; the hashes are not a signature proving who created a backup.

Use **Validate & restore backup** to restore into a new folder. Managed classes
are additionally registered as separately named recovered copies in My classes.
Original class files and marks are never overwritten. Workbook restores show the
path to use as `STUDENTDASH_WORKBOOK` before restarting the app.

Command-line equivalents:

```powershell
.venv\Scripts\python tools/workspace_backup.py backup path\course.sdclass course-backup.zip
.venv\Scripts\python tools/workspace_backup.py restore course-backup.zip path\new-recovery-folder
```

The backup command refuses to replace an existing archive; restore refuses an
existing destination. Restore validates the archive before publishing the new folder.
Keep backups in a private teacher location, separate from student practice downloads.

## Authored chemistry MCQs

The 100 new questions originally prepared for the Excel revision collection are
published from `tools/resources/structure_mcq_authored.json`. The chemistry page
builder calls the same deterministic option-ordering function as the workbook
builder, retaining question IDs, section mappings, A–D letters and explanations.
The Excel artifact itself is not required to rebuild the pages.

S1.1, S1.2, S1.3, S2.1 and S2.2 each contain 20 questions. Click an answer for immediate
feedback, open an explanation or start a fresh independent retry. Selections are
saved in the same portable practice record and can be included in assignments.
These are independently authored questions, not the original source exam questions.

## Expanded section MCQs

Every chemistry section now has 20 MCQs (440 total), and every Mathematics AI SL
sub-topic has 20 (780 total). The original 100 chemistry questions retain their
IDs and option order. Additional questions are authored in `tools/mcq_chemistry.py`
and `tools/mcq_math.py`, with deterministic option ordering in `tools/practice_mcq.py`.

Rebuild with `tools/build_chemistry_practice.py` and `tools/build_math_practice.py`.
Mathematics banks have individual `mcq-*.html` pages linked from the hub, topic,
small-step and coverage pages. All banks support immediate feedback, worked
explanations, independent retries and the portable practice journal.

## Five-question sets and choice feedback

Each MCQ page offers **Start five-question set**, **Five more like these**, and
**Show all 20 questions**. Direct question links reveal the set containing that
question. My practice also offers a section selector and five-question sessions;
additional sets skip questions already attempted or offered during that visit.

Wrong choices now include option-specific feedback. Numerical feedback identifies
sign, scale or high/low discrepancies and gives the relevant method. Conceptual
feedback contrasts the selected statement with the applicable explanation. This
is guidance about the answer, not a diagnosis of the student's thought process.

## Teacher question review

Open **Teacher: review questions** from either subject hub. Search by question
text or ID, filter by section or review status, edit the prompt, four options,
answer key, worked explanation and feedback for each choice. Preview the buttons
before saving. Flag questions as reviewed, needing correction or too repetitive,
and add editorial notes. Save before switching to another question.

Drafts stay in the current browser. **Export review file** downloads
`mcq-review.json`; **Import review file** validates and merges a file for the same
subject, replacing matching saved drafts. Export before moving computers.

To publish reviewed content, put that file in `resources/ib-chemistry/` or
`resources/ib-math-ai-sl/`, then run the corresponding `tools/build_*_practice.py`
builder. Invalid IDs, duplicate options, missing feedback and invalid answer keys
stop the build. Keep the review file with the project so future builds retain the
edits. Student pages are changed by rebuilding, not by saving an editorial draft.
The static review tool has no teacher authentication; exported notes should contain
only editorial information, not private student data.

## Syllabus graphs

Both practice hubs link to `syllabus-graph.html`. Coloured circles represent
syllabus parts; solid arrows retain the guide's cross-reference direction and
dashed links show explicit parent relationships. Select a node for incoming and
outgoing references, source-page links and related practice. Search, group filters,
zoom, a connections-only view and a plain linked list support navigation.

Chemistry includes 165 statement identifiers (such as S1.1.1), with an optional
section overview. Mathematics AI SL uses its 39 actual sub-topic identifiers;
extra statement numbers are not invented. Guide-only targets remain distinct
from locally available practice. References are not prerequisite requirements.

`tools/practice_graph.py` reads the existing profile hierarchy and cross-reference
files. Chemistry statement metadata lives in `syllabus-statements.json`; regenerate
it with `tools/extract_chemistry_statements.py path/to/chemistry-guide.pdf` using the
2025 guide. It extracts codes and references, not the full copyrighted statements.
Both regular practice-page builders regenerate their graph and hub link.

## Guide skills and the skills index

Both hubs now link to `skills.html`, a searchable directory connecting skills to
syllabus sections and specific questions. Each entry links to
`skills-practice.html` for focused practice, guidance and the complete list of
related questions. Skill labels beside MCQs, guided steps, repeat questions and
numerical challenges link back to the directory. Cross-references to chemistry
Tools, Inquiry and Nature of Science now also lead to local skills practice while
retaining guide-page provenance.

The profile inventories are in `skills.json`; `skill-coverage.json` records actual
question links and the build fails if an inventoried skill has no practice.
Chemistry has 103 entries and 103 new focused questions covering the tools/inquiry
tables, assessment skills, nature of science and ATL categories. Maths AI SL has
103 entries: 64 prior-learning, inquiry, modelling, technology and toolkit entries
with new focused questions, plus 39 syllabus-method entries linked to existing
questions. HL-only mathematics extensions are outside the SL profile. Labels and
practice mappings are authored teaching aids, not official skill codes or claims
that every possible use of a skill is covered.

Focused responses are self-reviewed against guidance. Equipment, technology or a
partner is required when specified; answering a written question does not certify
practical competence. Skill notes and self-review checkboxes save locally and have
their own **Export my skills notes** / **Import skills notes** controls. They do not
become automatically marked answers or modify assessment records.

Normal practice builders rebuild the skill pages from profile data. To deliberately
regenerate the authored inventory and mappings, run these tools in order before
both builders (this replaces edits to generated `skills.json`):

```
python tools/author_skill_practice.py
python tools/map_practice_skills.py
python tools/link_skill_sections.py
```

Source audit: chemistry guide PDF pp. 13–14, 21–22, 28, 34–38; mathematics guide
PDF pp. 20–21, 23, 26, 29–30 and the individual SL section references. Chemistry
measurement/technique items are split for practice; related reasoning items are
sometimes combined in one multi-part question. The maths prior-learning audit
includes simultaneous equations and set notation as well as the numerical and
geometric prerequisites. Section links are suggested practice contexts, not new
claims about official syllabus connections.

### Guided solutions, progress rings and class snapshots

Both subjects now link to `guided-practice.html`, `student-backup.html` and
`class-practice.html`. Guided examples check equation, substitution, numerical
calculation and units separately. A correct check unlocks the next step; drafts
and checked stages survive reloads. Hints and incorrect attempts count as help.
A fresh independent attempt resets the working, while previous evidence remains.
Guided examples also work in exported standalone assignments.

The syllabus graph shows rings for the latest checked question results, with
counts in its inspector. Section questions aggregate once through explicit
parents. Individual statements without question mappings remain unscored; a
section result is not evidence for each statement. Colours describe practice
history, not mastery or assessment marks.

The combined backup contains the shared practice journal (including guided
steps), saved assignments, and both subjects' available written skills notes.
Preview an import before merging. Attempts are deduplicated by ID; conflicts
reject the import. Matching drafts, notes and assignments use the imported
version. Existing legacy progress exports still work. Storage depends on browser
and file origin: export from the browser/location where the work was completed.
Reopen other practice tabs after import or clearing to avoid stale in-memory
records. No automatic SharePoint synchronization is attempted.

Teachers can import multiple combined backups or legacy progress files into the
class overview. Use distinct student aliases and remove an old snapshot before
importing a newer one for that student. Repeated filenames are rejected. The
view reports latest results by section and skill, including unattempted questions
in the denominator, and excludes unknown IDs. Written self-review notes are not
scored. Class snapshots remain in memory only and never modify assessment data
or the teacher's own practice. Keep the source files to reopen a class overview.

## Learning home, histories, investigations and test preparation

The default student snapshot now starts with three actions: **Continue learning**,
**Prepare for a test**, and **See my progress**. Detailed assessment tables and the
question explorer remain under **Detailed results & feedback**. No marks or
questions have been removed. The standalone subject homes are
`resources/ib-chemistry/learning-home.html` and
`resources/ib-math-ai-sl/learning-home.html`; public practice ZIPs open these homes.
Maths uses violet accents while chemistry retains teal, with shared layouts and
unchanged correct/incorrect feedback colours. Full topic libraries remain available
under the home page's exploration menu. Students choose a topic before revealing
five question links or starting a focused practice session.

### Teacher workflow

In a managed class, choose **Teaching groups & upcoming tests**. Filter question
results by a reviewed curriculum node, classification, or evidence start date.
The table counts graded evidence separately from other statuses. Group suggestions
require two graded questions and are editable teaching choices, not permanent
student classifications. Select learners, topic scope, activity type, instructions
and a follow-up date, then save a temporary group. The teacher can review subsequent
formal evidence and the latest linked exit-ticket result without combining scores.

Use the same workspace to save an upcoming test's date and scope. Regenerate the
student snapshots to distribute these plans; only assigned learners receive them.
Plans use the class document's version checks and do not modify scores. Removing
a plan affects newly generated snapshots, not files already distributed.

Exit-ticket routes now use the selected class's workspace and roster. The existing
local simulation still applies; no hosted service or authentication was added.
After submission, review ticket-to-topic links in the teaching workspace. Links
are explicit and preserve the original labels and marks. Both snapshots and the
live assessment page include the learner's submitted ticket results; answer keys
and other students' records never enter the history payload. Snapshot freshness
now includes exit-ticket records.

### Student history and planner

History filters by topic or classification. It keeps formal question records,
reviewed retries, teacher feedback, exit tickets and self-reported practice as
separate events. Multi-mapped questions appear once per topic history. Missing,
pending and exempt work remain unscored. Whole-assessment feedback stays in the
full history; unlinked tickets are not guessed into topics. Graph section circles
link to the corresponding standalone practice history.

A private snapshot can explicitly attach a practice backup through **Save or
restore my learning**. This is a separate imported snapshot, not a live connection,
and never changes formal marks. A public subject home uses its browser journal.
Private learning records are scoped to the learner and course and have their own
export/import. Shared subject plans and investigation notebooks are included in
the combined practice backup; private snapshot records must be exported from that
snapshot. Reopen other tabs after restoring records to avoid stale browser state.

The planner uses a teacher-assigned test or a student-created scope, a date and
5–90 minutes per day. It prioritizes linked lost marks, unattempted areas and older
evidence, then offers warm-up, practice and independent-check steps. Activities
are estimated five-minute starting points, spaced within the available days.
Insufficient time is shown explicitly; completion checkboxes are self-reports.

### Investigations

Each subject has two new investigations with adjustable controls, recorded data,
an accessible readings table, scatter plot, prediction, conclusion and fresh check.
Chemistry covers heating and reaction rate; maths covers regression and revenue
optimization. The regression investigation fits a least-squares line only when
other model settings are held constant. All models disclose assumptions; simulated
measurements are not experimental evidence about real systems.

Notebooks save in the browser and can be exported. Only the final numerical check
enters the practice journal; written conclusions and broader investigation skills
are not automatically marked. The previous maths exploration projects remain at
`exploration-projects.html`, linked from the new investigation page. Investigation
assignments require the full practice folder and assignment JSON; single-file
assignment exports continue to support the other question types.
