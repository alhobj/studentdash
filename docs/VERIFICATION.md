# Verification of the feedback and classroom update

Recorded 22 September 2026. This is a development-session record, not a production
readiness certification.

## Completed

- All Python sources and tests compiled successfully.
- 44 regression tests passed inside the managed sandbox using ordinary fixture
  directories under the permitted workspace instead of system temporary directories.
  The application logic was not mocked for these workflow checks; the generation
  race-condition test deliberately substitutes changing fingerprints.
- Checks covered Excel validation, scoring, membership, teacher filters, feedback
  draft/preview/publication, unpublished-edit isolation, escaping, per-student
  feedback isolation, stale-version rejection, CSRF, retry validation, original-score
  preservation, source freshness and modified/missing output detection.
- The expanded classroom fixture loaded 24 learners, six assessments, 36 questions,
  665 question records and 34 imported revision attempts. No complete question totals
  disagreed with their assessment summaries. Fourteen expected incomplete-evidence
  warnings demonstrate unfinished marking and non-graded work.
- Teacher overview, feedback editor and draft-preview routes returned successful
  responses for the classroom fixture.
- Twenty-four student inspection previews and two teacher interface inspection pages
  were rendered under `output/classroom-preview/`. Teacher HTML copies are static
  inspection artifacts; their forms require the running local app and a live session.
- `git diff --check` completed without whitespace errors.

## Still required

The standard suite now contains 50 tests. Its normal runner could not complete in
this managed environment: Python temporary directories were created but their
contents could not be accessed. The six tests exercising successful batch generation,
replacement, stale-output removal and related Flask generation/export paths were
excluded from the workspace-based run. Therefore this update is **not claimed to
have passed the full 50-test suite**.

Automatic approval review rejected the request to run the suite outside the sandbox
because the approval service reported a usage limit. No unsandboxed test or browser
run was performed after that rejection. Earlier browser checks and the earlier
39-test pass predate this update and do not establish verification of these new forms.

On the normal development/school computer, run:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python generate.py --no-examples
.\.venv\Scripts\python teacher.py
```

Check that all 50 tests pass, generation succeeds and the teacher page reports that
all current snapshots match their recorded inputs. Then exercise draft save, preview,
publication, regeneration, student isolation, attempt recording, offline filtering,
checklist persistence and print preview in the intended browsers.

The inspection previews are not evidence that the complete batch writer succeeded.
Do not distribute real student data until these release checks and the classroom
pilot requirements in `SYSTEM_GUIDE.md` are complete.
