# Local assessment architecture

The class-based metadata import is implemented in
`archive/legacy/studentdash/metadata_assessment.py` and exposed by that workspace's
Import assessment page. Its canonical Windows launcher remains
`start-assessment-import.bat`, with the original private `.sdclass` data locations.
It accepts metadata-only v2 JSON, persists editable previews, and commits an
assessment in one version-checked transaction. No source files or question text
are required. Stable IDs are retained by explicit assessment ID or name/date and
exact question labels; replacements are confirmed and unsafe score deletion is
blocked. Existing document imports remain readable without migration. The
Excel-results-only workspace below is preserved separately.

Classes containing metadata-only assessments use a focused standalone snapshot
template: history, all configured classification categories, explicit curriculum
rollups and question/status evidence. It does not depend on question text or
practice assets. Existing classes without metadata imports keep their original
dashboard layout. Scope is retained as metadata; explicit class participation
continues to define score-grid applicability rather than guessing student levels.

The active workflow is intentionally small: `app/teacher.py` provides four teacher
areas; `excel_import.py` is the read-only adapter for the supplied grading format;
`classification_import.py` validates explicit classification proposals; `storage.py`
owns persistent versioned SQLite documents and audit transactions; `analytics.py`
builds learner-scoped weighted evidence; `generator.py` renders single-file exports.

Source Excel remains authoritative for scores. A course document in
`data/private/studentdash.sqlite3` captures the last confirmed import, stable
source-to-internal student mappings, assessments keyed by ISO date and question
labels scoped to that course/assessment. Question classifications are a separate
field, never replaced by a result-only import. Teacher corrections have before/after
audit history. Removed/changed questions retain retired classification history.
Structural changes require confirmation and retired classifications are not reused.

SQLite transactions compare the previewed revision with the current document,
so stale tabs cannot overwrite intervening imports. Failed validation rolls back
the whole import, including ID allocation. Preview payloads expire in the private
directory and are bound to the teacher's signed session. No private payload is
stored in the cookie. Database backup uses SQLite snapshots and restore requires a
new destination. Filesystem export is staged before replacing a managed directory.

Core algorithms iterate the captured profile's categories, vocabulary and level
rules. Subject-specific Chemistry vocabulary is data in `profiles/ib_chemistry.json`.
The curriculum uses arbitrary-depth nodes with explicit parent references; imported
statement nodes must identify their parents, and cycles/redefinitions are rejected.
Each graded question contributes once per category/tag and once per ancestor, even
if it maps to several descendants. Grading scales come from the workbook.

Student templates receive only one learner's projected results. Exports contain
escaped HTML with inline CSS and no dependencies, teacher database, roster or other
learners' results. Teacher ZIPs contain all separate files and are clearly labelled.

The original application is preserved under `archive/legacy` with its own source,
assets and tests. It remains a separate compatibility workflow; it is not loaded
by the active app. Its architecture history is in
`archive/legacy/docs/ARCHITECTURE.md`. Active changes must not silently rewrite
historical workbook or classification semantics. The focused local application
does not add public hosting, accounts, external APIs or student submissions.
