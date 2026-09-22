# IB student dashboard — foundation

A local Python prototype that reads a private Excel workbook and renders a separate,
self-contained HTML page for every student. No database, external scripts, Microsoft
integration, authentication, or exit-ticket submission is included.

## Working from another computer

Python 3.10 or newer is required. Clone your repository, open its folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python create_example_workbook.py
.\.venv\Scripts\python generate.py
.\.venv\Scripts\python teacher.py
```

On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python`.
Open http://127.0.0.1:5000. The example generator creates two fictional students in
`data/master.xlsx`; it never reads the private workbook and refuses to overwrite an
existing file. The private-workbook test is skipped when that workbook is absent;
the remaining tests use synthetic fixtures.

Git excludes Excel workbooks, the data directory, generated output, environment
files, and common data exports. Do not force-add those files. The repository carries
the application and synthetic example generator, not the private student records.
The original-workbook audit below describes the school-computer file; it does not
describe the smaller synthetic workbook. This repository may be public; keep all
student records and generated dashboards outside Git regardless of visibility.

## Workbook inspection (22 September 2026)

The supplied file is **Studentdashtest.xlsx** in the project root, not
`data/master.xlsx`. The application prefers `data/master.xlsx` when present and
otherwise explicitly reports use of the supplied file. The original is never edited.
Inspection covered all populated cells, formulas and cached values, Excel tables,
sheet visibility, hidden rows/columns, merged cells, validations and defined names.
All eight sheets are visible; there are no hidden rows/columns, merged cells,
defined names or data validations. Formatted empty cells extend some sheet dimensions.

| Sheet | Current structure and role |
|---|---|
| Overview | Four student-name rows. Columns A–I: Name, a date (26 September 2026), three types of assessment/term/final placeholders. B2:B5 reference suggested grades L3:L6 on the dated sheet. Names are manually maintained, not linked by StudentID. |
| Students | `tblStudents`, A1:D5. StudentID, StudentName, Email, Class. Four students, IDs 1–4; three Chemistry HL and one Chemistry SL. |
| Assessments | `tblAssessments`, A1:E5. AssessmentID, AssessmentName, Date, Subject, Marks. Four assessments: September SL/HL (12/14 marks) and October SL/HL (20/20 marks). |
| Questions | `Tabell4`, A1:L8. QuestionID, AssessmentID, QuestionNumber, SLHL, Text, Answer, Marks, Topic, Subtopic, QuestionType, ActionVerb, AutoMark. Seven question rows, all assigned AssessmentID 1; six SL, one HL. Only the first three have text, answers and marks (2 each). All topics, subtopics and AutoMark values are blank. ActionVerb is State, State, MCQ for those three questions. |
| Results | `tblResults`, A1:E5. AssessmentID, StudentID, Score, MaxScore, **Stratus** (spelling as supplied). Four assessment-total rows, all AssessmentID 1. Score formulas reference dated-sheet I3:I6; MaxScore references I2. Saved formula values are available; individual scores are omitted from this documentation. Status cells are blank. There is no QuestionID. |
| 26.09.2026 | Question matrix: B:H are tasks 1–7; row 2 has two marks per task. A3:A6 references Overview names. I sums scores; J is absence; K calculates percent; L suggests grades; M is a blank teacher grade override. N:O holds grade counts. Row 7 averages each question; row 8 repeats task labels. This sheet has no StudentID or AssessmentID. |
| Assessment blueprint | Unlinked template with 35 task columns B:AJ, labels from *1a to 12c, worth 57 marks total. AK totals, AL absence, AM percent, AN suggested grade, AO override, AP:AQ counts. Four name formulas reference Overview but score cells are blank. Row 7 averages generate cached #DIV/0! errors. It is not a recorded assessment. |
| Grade boundaries | Grade, Percent. Global descending minimum percentages: 7→80, 6→65, 5→54, 4→44, 3→32, 2→16, 1→0. A ninth row contains FRAV (absence), without a percentage. |

### Relationships and problems

Students.StudentID → Results.StudentID; Assessments.AssessmentID →
Results.AssessmentID and Questions.AssessmentID. Results has no relationship to
individual questions. Overview → dated-sheet names; dated-sheet totals → Results;
dated-sheet grade formulas → Grade boundaries; dated-sheet grades → Overview.
The blueprint also reads Overview and Grade boundaries, but nothing identifies it
as an assessment in Assessments.

* StudentID 2 has a different name in Students and Overview. Names or row positions
  are therefore unsafe join keys. We do **not** infer student question results from
  matrix row order, names, or formula destinations.
* Assessment 1 is an SL assessment worth 12, but every Results row uses maximum 14.
  All question rows belong to assessment 1, including its HL-only question. Results
  also assigns three HL students to this SL assessment. An explicit policy is needed
  for shared SL/HL questions and assessment membership.
* The SL student's task 7 contains `x`. SUM ignores it, yet the percent denominator
  remains 14. It is unclear whether this means absent, exempt, or not applicable.
* Only six marks are populated in Questions for an assessment declared worth 12.
  Missing metadata prevents reliable topic analytics. MCQ is a question type,
  not an IB command term.
* Suggested-grade formulas use `>=` for most thresholds but `>` for grade 1 at zero;
  zero marks can produce grade 0. Absence is checked after numeric comparisons,
  so an absence marker may not take precedence. Row-7 grade formulas use strict
  comparisons and reference empty boundary rows down to 17. Count formulas mix
  strict and non-strict thresholds. These are not copied into Python.
* No weighting, assessment-specific boundary sets, final-grade policy, resource
  links, exit tickets, or submissions are defined. Blank teacher grade overrides
  exist in the matrices but have no normalized representation.
* openpyxl **does not calculate formulas**. Existing saved caches are available for
  Results. They can be stale; recalculate and save in Excel before generating.
  Missing formula caches and Excel error cells in required input tables are fatal
  validation errors. Blueprint errors are documented but not imported.

## Proposed workbook changes (not applied)

1. Keep Students and Assessments as reference tables; preserve stable IDs. Add
   explicit SL/HL membership or separate assessment variants with explicit questions.
   Resolve the 12-versus-14 maximum discrepancy before treating grades as authoritative.
2. Add **QuestionResults**: AssessmentID, QuestionID, StudentID, Score, Status.
   Use a unique (AssessmentID, QuestionID, StudentID) key, and validate that the
   question belongs to the assessment. Suggested statuses: graded, missing,
   absent, exempt, pending. Zero is a graded score; blank is not zero. Non-graded
   rows should have blank scores. Agree on denominator rules before implementation.
3. Retain Results as assessment summaries or derive it from QuestionResults;
   rename Stratus to Status. Do not replace its current totals with guessed marks.
   Add an explicit final/override grade and reason if needed.
4. Complete Questions.Marks, Topic, Subtopic, ActionVerb and question text. Use
   controlled syllabus codes and IB command terms; keep MCQ in QuestionType.
   Decide whether QuestionID is globally unique (this prototype requires it).
5. Add StudentID and AssessmentID to any retained score matrices and retire
   name/position joins. Confirm the student-name discrepancy and meaning of `x`.
6. Keep Grade/Percent as inclusive minimum thresholds. Later introduce named
   boundary sets and an Assessment→BoundarySet relationship if needed. Represent
   absence as status, not a grade. Keep official final grades distinct from suggestions.
7. Add resources and exit-ticket tables only after their format and storage workflow
   are agreed. No workbook changes or extra tables are required to run milestone 1.

## Architecture and prototype decisions

* `studentdash/config.py`: paths and environment configuration.
* `studentdash/excel.py`: read-only openpyxl loading, schema/value validation,
  formula cache handling and teacher-only data-quality warnings.
* `studentdash/models.py`: reusable typed records and a workbook container.
* `studentdash/analytics.py`: student-scoped view models, weighted percentages,
  inclusive suggested grades and question-category calculations.
* `studentdash/examples.py`: clearly labelled fictional question results,
  independent of real assessment totals.
* `studentdash/render.py` and `templates/`: Jinja2 generation with automatic escaping
  and inline styles. Only a student's allowlisted view model reaches their template.
* `studentdash/teacher.py`: Flask status, POST generation and local preview routes.
* `generate.py`, `teacher.py`: small entry points. `tests/`: validation, calculation,
  privacy and Flask integration checks using standard-library unittest.

Only the five reference/input sheets are required. Legacy matrices remain private
and are not exported. The reader supports the current Stratus spelling and future
Status spelling. This milestone does not yet import the proposed QuestionResults
table: that should follow agreement on the model.

Real assessment history uses Results.Score/MaxScore as saved, with a visible
provisional-data notice. Overall percent is total earned / total possible across
recorded scored results, not an average of rounded percentages. Suggested grades
use inclusive minimum boundaries, so zero gives grade 1. Absent, missing, exempt,
and pending results do not count; blank status with a numeric score is treated as
graded with a teacher warning. There is no term/final grade calculation.

Question drill-down uses a separate fictional practice example by default because
real question-to-student mappings are ambiguous. Its marks never affect actual
totals, history or grades. Example strength/work-on hints require at least two
questions in a category and use ≥75% / <50%; they are illustrative, not diagnoses.
Unrecorded assessments and future dates are not guessed to mean missing work.
Exit-ticket and resource areas use honest empty states.

Files are named `student<ID>.html` (the supplied IDs produce `student1.html` through
`student4.html`; ID 1001 would produce `student1001.html`). IDs must contain only
letters, digits, underscores or hyphens, and case-insensitive filename collisions
are rejected. Names, emails, answers, complete rosters, workbook warnings, other
students' results and hidden/unrelated workbook content are never passed to student
templates. Only the current anonymous ID and that student's results are rendered.
Standalone files contain no network dependencies, roster index or fetch calls.

## Run locally (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python generate.py
.\.venv\Scripts\python teacher.py
```

With dependencies already installed, `python generate.py` and `python teacher.py`
work directly. Open `http://127.0.0.1:5000` for the teacher interface. Open generated
`output/student1.html` directly for a standalone preview. All four supplied students
are generated. To omit fictional practice, run `python generate.py --no-examples`.

Optional path overrides (resolved independently of the current working directory):

```powershell
$env:STUDENTDASH_WORKBOOK = 'C:\path\to\master.xlsx'
$env:STUDENTDASH_OUTPUT = 'C:\path\to\private-output'
python generate.py
python -m unittest discover -s tests -v
```

Teacher generation includes the labelled examples. The server binds only to
loopback, has debug disabled and uses a CSRF token for its generation button.
It is a local prototype without authentication: do not expose it to the network.
The teacher preview list is private and intentionally includes every generated
student page. Static filenames are not access control; distribute only the correct
file to each student. The output directory and workbook must stay private.
Old generated pages for students removed from the workbook are not listed or served
by the teacher interface; generation removes obsolete `student*.html` files only
from its dedicated output directory. Do not store unrelated files with that pattern
there. Validation completes before any output is replaced.

## Milestone 2 recommendation

Agree and implement QuestionResults, status/denominator rules and SL/HL assignment;
resolve the workbook discrepancies; then replace fictional drill-down with validated
real question-level topic/subtopic and command-term analytics. Add regression cases
for absent/exempt work and assessment-specific boundaries. After that, design the
structured exit-ticket import/preview/publish workflow locally before designing
Microsoft 365 storage and authentication separately.
