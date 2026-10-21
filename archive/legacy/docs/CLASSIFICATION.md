# Question classifications and the first real assessment

This page documents the current IB Chemistry implementation. Its fixed vocabulary,
SL/HL rules and syllabus syntax are existing limitations, not the generic core
contract. See [Architecture direction](ARCHITECTURE.md) for the inventory and gradual
migration toward configurable profiles, categories and curriculum trees.

For the new teacher-facing workflow, use [Enter your first assessment](FIRST_ASSESSMENT.md).
The question editor exposes the existing tag categories; all are optional. The
vocabulary now lives in `profiles/ib_chemistry.json` and is copied into new classes.
The workbook instructions below remain valid for existing imports. Teacher-entered
curriculum mappings accept reviewed code/label text without official-code validation.

The exam bank contains **legacy syllabus** questions. Its original labels remain
unchanged. `QuestionSyllabus` keeps LegacyCode separate from CurrentCode, with
Status `unreviewed`, `current`, `partial` or `out_of_scope`. Review against your
current syllabus before assigning CurrentCode and Source `teacher`. Code syntax
validation is not verification that a code exists in the official syllabus.
Only `current` mappings participate in current-syllabus diagnostic queries.

Run `python tools/migrate_exam_databases.py` to create the three classified copies
and `classification_report.md` under `output/exam_databases`. Originals are never
saved through openpyxl. Their ZIP members are copied unchanged, with additions to
three XML registries to register the new sheets. Existing sheets, formatting,
formulas, cached values, images and other package members are preserved. Reruns
retain teacher tags and teacher syllabus reviews in the destination copies.

Each original URL number becomes QuestionID in QuestionIndex; source identifiers
are not rewritten. Source metadata and HTML remain in the original sheet. These
are reference banks, not ready-to-import assessment workbooks. In Papers 2 and 3,
the exported question and part arrays do not establish a safe URL-to-part join.
Resolve the actual assessed prompt and marks before copying a question into a test.

QuestionTags has `QuestionID, Category, Tag, Source, Confidence`. Multiple rows
support multiple tags. Source is existing/rule/inferred/teacher; Confidence is
blank or 0–1, and rule confidence is heuristic. Identical tags are deduplicated.
A teacher-reviewed category replaces lower-priority tags in that category;
include **all** desired tags for the category when reviewing it. Existing metadata
also takes precedence over automatic proposals. Deleting a rule row alone does
not suppress regeneration; negative review decisions are not yet supported.
ClassificationVocabulary lists allowed values. CognitiveDemand and Context are
left unknown by automation; review flags are in ClassificationReview. Review is
currently in Excel, with the model ready for a later teacher review interface.

`studentdash.classification.performance(data, student_id, filters, syllabus=...)`
supports AND combinations of (Category, Tag), e.g. Skill/Chemical reasoning and
Representation/Graph. Marks count once per matching question, only for that
student's graded results. These new queries do not add dashboard panels yet.

## Minimum workbook for your next test

Row 1 must contain these exact headers. Keep the required headers even where a
cell is allowed to be blank. Start a new workbook for real learners; do not mix
them with the fictional demo rows.

| Sheet | Required headers | What to fill |
|---|---|---|
| Students | StudentID, StudentName, Email, Class | ID and name required; Email/Class may be blank |
| Assessments | AssessmentID, AssessmentName, Date, Subject, Marks | All; date YYYY-MM-DD, positive total marks |
| Questions | QuestionID, AssessmentID, QuestionNumber, SLHL, Text, Answer, Marks, Topic, Subtopic, QuestionType, ActionVerb, AutoMark | For scored questions fill ID, assessment, number, SL/HL/BOTH, exact prompt, positive marks, topic, subtopic and command term. Answer, QuestionType and AutoMark may be blank |
| Results | AssessmentID, StudentID, Score, MaxScore, Status | Required sheet; may initially contain headers only when importing a complete matrix |
| Grade boundaries | Grade, Percent | Seven rows: grades 1–7, grade 1 starts at 0; increasing thresholds up to 100 |
| Memberships | AssessmentID, StudentID, Level | One row per participating learner/test; Level SL or HL |
| ScoreMatrix | AssessmentID, StudentID, then one column per QuestionID | One row per learner/test; numeric marks, including 0; blank=pending; missing/absent/exempt are supported |

Question IDs must be globally unique; use one per separately scored part. IDs use
letters, digits, underscores and hyphens. HL membership includes SL questions;
leave non-applicable matrix cells blank. Matrix headers require explicit IDs;
names and visual positions are never used as joins. Existing matrices can be
retained by copying their scores under these ID headers.

Optional sheets:

- QuestionTags: QuestionID, Category, Tag, Source, Confidence. Use Source `teacher`
  for reviewed classifications; unknown dimensions can be omitted.
- QuestionSyllabus: QuestionID, LegacyCode, CurrentCode, Status, Source. Needed
  for reviewed current-syllabus aggregation; LegacyCode may be blank for new tests.
- QuestionResults: AssessmentID, QuestionID, StudentID, Score, Status. Generated
  by the matrix importer; you need not enter it manually.
- ClassificationVocabulary is explanatory; it does not override the code's
  controlled vocabulary. AssessmentBoundaries, Resources, ExitTickets and
  RevisionAttempts remain optional existing extensions.

## Five steps

1. Fill Students, Assessments, Grade boundaries and Memberships.
2. Add selected Questions with the exact scored part and its marks. Check old
   questions for current relevance; adapt or exclude out-of-scope content.
3. Add reviewed QuestionTags and, where verified, QuestionSyllabus mappings.
4. Enter ScoreMatrix marks and run:
   `python tools/import_score_matrix.py first-test.xlsx first-test-ready.xlsx`.
   This creates and validates a new copy. Complete graded/exempt rows generate
   assessment totals; incomplete rows keep existing Results unchanged, so enter
   the appropriate Results status/total if you need an incomplete assessment shown.
5. In PowerShell set `$env:STUDENTDASH_WORKBOOK = 'first-test-ready.xlsx'`, then
   run `python generate.py --no-examples`. Review the generated learner pages
   and reconciliation warnings before sharing through your established workflow.

The matrix importer uses openpyxl on the assessment copy; Excel formula caches
are not retained by that library. Use literal values for imported assessment
fields. The exam-bank migration uses archive copying and preserves those caches.
