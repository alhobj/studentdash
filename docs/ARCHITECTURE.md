# Local assessment architecture

Teacher navigation is centralized in `teacher_navigation.py` and one shared HTML
partial reused by the teacher base and standalone teacher pages. It links to
existing routes/anchors and carries explicit class context. Student exports are
excluded. Question-level display/defaults come from explicit class/profile or
matching curriculum metadata in `question_levels.py`, never class-name parsing;
they do not introduce new scoring/eligibility filters. Import draft deletion uses
named confirmation, CSRF and optimistic class versions. Draft removal and deletion
of owned temporary SQLite source rows share one transaction; published records and
sources referenced by other imports are protected.

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

### Unified class-based results

The supported `.sdclass` workspace stores optional `assessment_type` on each
assessment. The default is `assessment`; `exit_ticket` uses identical scoring,
classification and import services. Filters operate on copied report data and do
not rewrite records or alter default weighting. All class-based snapshots share
the results-focused metadata template, including feedback draft previews. Rendering
fingerprints include the report templates and helpers. Explicit curriculum parents
produce expandable region trees and deduplicated ancestor evidence. Settings and
storage remain compatible. Retired planning, interactive ticket, revision-attempt
and practice routes/data remain archival implementation; interactive routes are
unavailable when a class workspace is selected. No destructive migration runs.

### Separate confidence ratings

Assessment definitions optionally carry `confidence` with boolean `enabled` and
fixed integer `min=1`, `max=5`. The separate `confidence_ratings` map stores integer
ratings by participating student ID. Scores remain unchanged; `save_scores` accepts
an optional partial ratings map, preserving omitted entries and clearing explicit
blank/null values atomically under the existing document-version check. Report
history and teacher overview views read ratings without passing them to any
performance calculation. The document hash covers snapshot freshness and backups.
`confidence_corrections` archives a question and its recorded scores only after an
explicit review; normal imports never reinterpret a question by its name.

### Effective course vocabulary and selection controls

`course_profile.effective` adds missing configured vocabulary for an exact captured
curriculum ID/version. It unions tag values and fills absent category options and
command-category metadata without replacing custom values or the saved curriculum.
`read_document` returns this effective profile without modifying SQLite or its
version; normal validated saves can persist it. Generic code contains no subject
vocabulary. The mathematics catalog profile owns the IB command-term labels and
Action verbs display label. Prompt, editor, validation and analytics share this
profile. Vocabulary/catalog changes participate in snapshot freshness fingerprints.

Editor and import preview reuse a selection-tree macro based on explicit parents.
Saved container roots have a separate preserved-reference control rather than an
ordinary new-selection checkbox. Selection summaries/counts do not alter stored
links. The legacy free-text label never creates hierarchy or links.
