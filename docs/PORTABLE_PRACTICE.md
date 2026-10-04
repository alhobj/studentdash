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
