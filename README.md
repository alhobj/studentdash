# Studentdash — local assessment results and persistent classifications

Import your existing Excel grading workbook, review classifications produced
separately with ChatGPT, and generate a private standalone HTML file per student.
The application uses local SQLite and makes no external API calls. Normal use
works offline after the initial Python dependencies have been installed.

## 1. Start on Windows

Install Python **3.10 or newer**, clone/download the repository, and double-click
`start.bat`. It creates `.venv` and installs `requirements.txt` if needed. Open
**http://127.0.0.1:5000**. The server stays on loopback with debug disabled.
Stop it with Ctrl+C before moving/restoring its private database.

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python teacher.py
```

## 2. Import the grading workbook

Choose **Import results**, give your course a permanent ClassID such as
`Chemistry_HL_2026`, and upload the original `.xlsx`. Use that same ClassID on
subsequent imports even if the workbook filename changes. Preview the students,
assessments, scores, warnings and identity mappings, then confirm.

The adapter supports the supplied `Chemistry 23-25 HL.xlsx` structure:

- `Overview`: names in A2 onward, with `Name` in A1. No scores are read from this
  administrative overview. Optional `StudentID` and `Level` columns are supported.
- `Assessment blueprint`: a template, **never an assessment**.
- Copy that template and name each assessment sheet `DD.MM.YYYY` (ISO
  `YYYY-MM-DD` also works). Row 1 contains question labels, row 2 maximum marks,
  and rows 3 onward contain students and marks. Question columns run from B up to
  the `Marks` total column. Labels such as `*1a` are kept exactly, with no inferred
  syllabus or level meaning.
- The adapter ignores `Marks`, absence, percentages, suggested/official grades
  and statistics columns as question data. It skips the `Sum` and `Task` footer
  rows and reports unknown non-date sheets as ignored.
- `Grade boundaries`: numeric grades and minimum percentages. The `FRAV` row is
  an absence label, not a grade. Suggested grades are recomputed from complete
  question evidence, using inclusive thresholds; official teacher grades are not
  silently substituted.

**The supplied example currently contains 33 roster entries, seven grade boundaries
and no dated assessment sheets.** Its blueprint has no scores. Importing it must
not invent assessments, results or classifications. No structural change to the
original workbook is required: continue copying the blueprint as usual.

Blank marks stay **pending**; numeric zero stays a **graded zero**. `A`, `X` or
`FRAV` means absent, `E` exempt, `M` missing and `P` pending; full English status
names also work. An `x` in the `x for absence` column marks all that row's questions
absent and warns if it overrides recorded marks. Ungraded statuses do not contribute
to category performance. Incomplete assessments have no suggested overall grade.

Original Excel files are **never modified**. Direct name links such as
`=Overview!A2` are resolved read-only. Other score formulas require saved cached
values: recalculate/save in Excel before importing. Excel errors and missing score
formula caches block import; cache freshness cannot be established automatically.
Administrative totals/grades need not be recalculated by Python. Complete cached
totals that disagree with question marks produce a warning for teacher review.

Student mappings use an explicit source StudentID if present, otherwise the exact
normalized name, never the row position. Without source IDs, renamed students must
be mapped to their existing internal ID in the preview. Unmatched students require
confirmation as new. Duplicate/ambiguous names are rejected; use distinguishing
names in this case. No IDs or classifications are guessed from names or filenames.

## 3. Obtain and import classifications

After importing results, open **Import classifications**. Download either the
blank template or a template populated with your existing question identities and
classifications. Download the short ChatGPT prompt too. Give ChatGPT the **question
paper**, template and vocabulary; do not send student names, results or the grading
workbook. ChatGPT is used separately; Studentdash has no API integration.

The `.xlsx` contains `Classifications`, `Vocabulary`, `SyllabusNodes` and
`Instructions` sheets. UTF-8 comma-delimited CSV is supported for the
Classifications table with the same headers:

```text
ClassID,AssessmentID,QuestionID,Level,SyllabusCode,Topic,Subtopic,CommandTerm,Skill,CognitiveDemand,Context,Representation,QuantitativeSkill,ExperimentalSkill
```

Use ISO assessment dates, preserve question labels exactly, and separate multiple
tags with semicolons. Categories/allowed tags come from the class's captured
`profiles/*.json` profile. The included Chemistry profile permits SL, HL or BOTH;
other subjects can configure entirely different categories and level rules without
core Python changes. Level is optional. Eligibility filtering applies only when
both student level and question scope are explicitly known from profile metadata.
No level is inferred from `*` labels or filenames.

SyllabusCode accepts explicit configured node IDs or external codes. Existing
hierarchy nodes come from the selected `curricula/*.json`. For finer syllabus
statements, add rows to `SyllabusNodes` with `NodeID`, `ParentID`, `Label`, `Code`.
Parents must exist; cycles, duplicates and redefinition of existing nodes are
rejected. **No hierarchy is inferred by splitting codes.** CSV can reference
existing nodes but cannot add nodes. Topic/Subtopic are optional teacher-supplied
labels, kept separate from the controlled tag vocabulary.

Upload and preview the file. Unknown classes, assessments, questions and tags,
duplicates and conflicts are reported. Blank fields preserve existing values;
unknown new fields remain unknown. Use `[clear]` to explicitly clear a field.
Existing teacher-confirmed classifications require explicit replacement consent.
To correct them, download the populated template, edit it, upload, review and
confirm. Before/after changes are recorded in the private import history.

## 4. Generate student HTML dashboards

**Student overview** shows results, classification coverage and per-student previews.
**Generate dashboards** regenerates every active student's file under:

```text
data/generated/<ClassID>/student1001.html
data/generated/<ClassID>/student1002.html
```

Each file includes only its learner's assessment history, question evidence and
classification analyses. Styling is inline. There are no external scripts, fonts,
APIs, workbook files or databases; each HTML works offline without Flask/Python.
Marks and percentages use graded question evidence only. Multi-tag questions count
once per tag and once per explicit syllabus ancestor. Category percentages overlap
and must not be added. Strength/low-performance labels require at least two graded
questions; insufficient evidence, missing results and no classification are distinct.

Saved files are marked stale after imports. The ZIP download always renders current
data. **The all-student ZIP is for the teacher**: distribute each HTML individually
to the correct student. It contains no source workbook or teacher database.

## 5. Back up or move to another computer

All classes, stable student mappings, assessment metadata, result snapshots,
classifications, retired classifications, teacher corrections and import history
are stored in **`data/private/studentdash.sqlite3`**. Scores remain authoritative in
your original Excel workbook; the database contains its last confirmed import.

Use **Backup & history → Create and download database backup**. This uses SQLite's
consistent backup API and verifies integrity. A copy also stays under
`data/private/backups/`; retain a secure copy on another device. Backups contain
private data for **all classes**, not just the currently selected class.

On the new computer clone Studentdash, install its dependencies, and keep the server
stopped. Restore to a **new** location:

```bat
.venv\Scripts\python.exe -m app.restore "D:\Backups\studentdash.sqlite3" data\restored\studentdash.sqlite3
set "STUDENTDASH_PRIVATE=C:\path\to\studentdash\data\restored"
start.bat
```

Restore validates the database version/integrity and never overwrites existing
data. Keep the backup and previous directory until you verify the restored classes.
The session key is regenerated on another machine; it is not needed to recover
classifications. Use `STUDENTDASH_GENERATED` to choose another generated-file root.
Keep private and generated directories separate. Both default directories, Excel,
SQLite, ZIP, CSV and mapping files under `data/` are excluded from Git. GitHub does
not back up your private classifications.

## 6. Add the next test

Copy the blueprint, name it with the new test date, enter scores, and upload the
updated workbook using the same ClassID. Studentdash recognizes existing students,
assessments and question labels. All previous classifications remain stored and
the new assessment is flagged as needing classification. Upload only the new
classification file and regenerate dashboards. Previous files are not needed.

If an existing question's label or maximum changes, review and confirm the structure
change. Affected classifications are **retired into history**, never silently
reattached. Reclassify the changed questions explicitly. Removed sheets are retained
privately with their classifications, but excluded from current dashboards after
confirmation. Preview revisions prevent stale tabs from overwriting newer imports.

## Development and archive

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests generate only fictional workbooks and temporary databases. They cover
reimports, the three-assessment workflow, classification corrections, IDs, statuses,
formula caches, hierarchical/multi-tag analytics, privacy, persistence, backup,
restore, standalone exports and the teacher HTTP workflow.

An optional real-browser test additionally exercises uploads, confirmations, ZIP
download and an offline-rendered student document. Install `requirements-dev.txt`
and set `STUDENTDASH_BROWSER_EXECUTABLE` to your Chromium/Chrome executable (or use
system `chromium`). The browser check is skipped if these optional tools are absent;
all core workflow tests still run.

The previous application is preserved intact under **`archive/legacy/`**, including
its original source, tests, documentation, workbook support, quizzes, games,
question banks, exit tickets and student submission simulations. It is not imported
by the active app. Shared profile/curriculum data remain available at the root;
the archive retains its own snapshot for compatibility. See [archive notes](archive/README.md)
for running the old workflow separately. Public hosting and student submissions
are outside the active application.
