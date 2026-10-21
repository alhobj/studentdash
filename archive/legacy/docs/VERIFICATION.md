# Verification

## Assessment import - 24 September 2026

- Full suite: **124 tests passed, no skips**, including five headless Edge browser
  tests (three for import/review and two for the existing score-entry workflow).
- Import coverage includes PDF/DOCX extraction, parent/letter/roman hierarchy,
  missing/conflicting marks, duplicates, total mismatch, tables, figure references,
  classification confidence, multiple tags, teacher overrides/rejections, configured
  curriculum matching, failed extraction, original-file preservation and finalization.
- Browser checks cover upload, saved draft reopen, high-confidence acceptance,
  explicit rejection, manual multi-tag edits, split/combine, add/delete, total-warning
  resolution, final review confirmation and normal spreadsheet score entry.
- Student exports exclude the original document and draft metadata; original sources
  remain restricted to the teacher workflow and their owning class.
- A review-screen screenshot was inspected. This is a desktop workflow check, not
  a full accessibility or mobile audit. All examples and fixtures are fictional.
- The initial suggestion provider uses local configured rules and definition/keyword
  matching, not an external language model. Curriculum matching needs configured
  nodes; the bundled profile deliberately does not invent an official curriculum.
- Actual question-bank layout tuning, OCR and stronger semantic inference await
  the real example document. See [the import guide](ASSESSMENT_IMPORT.md).

## Enter one real assessment — 23 September 2026

- Full suite: **103 tests passed, no skips**, including two headless Edge acceptance
  tests using actual rectangular clipboard paste and keyboard navigation.
- New coverage includes persistent classes/stable IDs, assessment and question
  creation/reordering, configured tags, optional classifications, maximum marks,
  all result statuses, zero/decimal marks, correction, incomplete totals, changing
  question maxima, concurrent edits, save/reopen, dashboard generation and isolation.
- Browser checks follow class creation through score entry, save, overview, generation,
  individual preview and opening the standalone HTML file. They also check invalid
  scores, malformed/overflowing paste, preserved marks after question reordering,
  and reopening the class in a fresh browser session. No JavaScript errors occurred.
- The score-grid screenshot was inspected with fictional data. This is a desktop
  workflow check, not a complete screen-reader or mobile accessibility audit.
- Temporary-directory errors were reproduced inside the managed execution sandbox,
  even with TEMP/TMP pointed into the repository. The same tests passed outside that
  sandbox with normal permissions. No application permission workaround was needed.
- Existing workbook and demo data were not modified. Browser verification uses
  temporary fictional classes, not real learner records.

Run `.\.venv\Scripts\python.exe -B -m unittest discover -s tests` in a normal terminal.
Browser checks require `requirements-dev.txt` and Edge on Windows (or installed
Playwright Chromium elsewhere). Without those optional tools, browser checks skip;
the reported run above included them. `STUDENTDASH_TEST_BROWSER` can select an
installed Chromium browser channel.

## Previous milestone: exit tickets and design previews

Recorded 23 September 2026. All checks use fictional records.

## Completed

- The full standard suite passed: **82 tests, no failures or skips**, using
  `python -m unittest discover -s tests -v` with the project environment.
  Running outside the managed sandbox resolved the temporary-directory permission
  blocker. The previous 44-of-50 limitation is superseded.
- Coverage includes workbook validation, analytics, batch generation, feedback,
  freshness, learner isolation and revisions, plus exit-ticket import, publication,
  assignment, six question types, automatic/manual marking, concurrent submissions,
  stale edits, CSRF and answer-key visibility. Follow-up checks cover correction
  history, automatic overrides, release policies, legacy workspace upgrade, learner
  isolation, aggregate exclusion and concurrent duplicate retake creation.
- An isolated fictional classroom HTTP walkthrough exercised import, preview,
  publication, student submission, teacher partial credit and a final 6/7 result.
- Generation succeeded for all 24 classroom snapshots in `output/classroom-preview`.
  Fourteen expected incomplete-evidence notes remained; assessment summaries were retained.
- All ten layout previews were rendered from one newly created fictional learner
  view. Removing CSS leaves byte-identical documents, including content and scripts.
- Headless Edge screenshots were inspected for all ten desktop designs across the
  two design updates, the corrected Focus narrow layout and the student exit-ticket
  form. The five new designs also passed 500-pixel browser checks for horizontal
  overflow, assessment filtering, checklist synchronization and print-button visibility.
  This is a smoke check, not a complete browser, printed-output or accessibility audit.
- The teacher overview is 379 words, intended to fit one ordinary printed page.
- Git whitespace checks passed.

## Before a classroom pilot

Check the chosen design on intended devices, including keyboard navigation, screen
readers, offline filtering, checklist persistence and print preview. Markdown page
length depends on the viewer's font, margins and print settings.

Interactive exit tickets remain a local fictional simulation without real
authentication. Follow the classroom-use steps in `SYSTEM_GUIDE.md` before
introducing actual student records. The implemented follow-up rules are documented in `FOLLOW_UP.md`; remaining
product and pilot work is listed in `TODO.md`.
# Classroom rollout verification — 2026-10-12

- Ran the complete 242-test suite, including local Edge browser tests. Its only
  failure was an old browser expectation that detailed results were immediately
  visible; the current student home intentionally puts them behind navigation.
  Updated the test to open Detailed results & feedback, then Assessments. The
  affected full clipboard/keyboard/save/reopen/snapshot test passed on rerun.
- Added and passed a full PDF upload → question review → score entry → private ZIP
  download → extracted offline snapshot test. Checked selected-class display,
  student-specific download filename, exclusion of another learner's records,
  and exclusion of teacher databases/original documents from the package.
- All four portability tests passed after the download changes, including backup
  restore integrity, private/public separation and teacher-only access. All nine
  exam-bank import/repair tests passed, including clean-checkout output setup.
- These runs cover 243 distinct tests. The complete suite was not repeated after
  the targeted fixes; affected tests were rerun successfully.
- Prepared a practice-only ZIP and verified its ZIP integrity and exclusion of
  class databases and the private exam bank. Updated classroom/import guidance.
- Actual school SharePoint permissions, managed student-device behavior, and the
  user's forthcoming test layout remain untested. Try one downloaded/extracted
  package on an intended student device before class-wide distribution.

# Classification verification — 2026-09-23

- `python -m unittest discover -s tests`: 87 tests passed, including tag validation,
  precedence, duplicate handling, hierarchy, migration preservation, ambiguous
  multi-part abstention, combined analytics, student isolation and matrix import.
- All three source banks inspected before migration: 904 / 1,354 / 1,210 records.
- All original ZIP members except the three extended sheet registries verified
  byte-for-byte against the copies; workbook namespace declarations preserved.
- Legacy codes retained; no automatic current-syllabus mappings. Paper 2/3 part
  boundaries require review. Cognitive demand/context remain unknown automatically.
- Artifacts: `output/exam_databases`; workflow: [CLASSIFICATION.md](CLASSIFICATION.md).
