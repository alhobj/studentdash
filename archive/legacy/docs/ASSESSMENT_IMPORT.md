# Import assessment metadata from ChatGPT

Use root **start-assessment-import.bat** on Windows and open
http://127.0.0.1:5000/classes. Keep your existing data directory when updating.

1. Select a class and choose **Import assessment**.
2. Select **Assessment** or **Exit ticket**, click **Update prompt**, then **Copy prompt**. It contains the selected class ID, JSON schema, allowed
   categories/tags, configured curriculum nodes and scope options. No pupil data is included.
3. Attach the test paper in ChatGPT, paste the prompt, and copy the complete JSON response.
4. Paste the response in Studentdash and choose **Preview assessment**.
5. Check the editable table and total maximum marks. Correct only what is necessary.
6. Click **Import assessment** once. Enter/paste the students' scores separately.

The top teacher bar preserves class context across Classes, Assessments, Students,
Curriculum and Settings. Backups/restores and class-level configuration are under
Settings. Add students through Classes and the selected class overview. Class planning
and separate student-interactive exit tickets are retired; historical data is retained.

For a configured single-level class, per-question level is hidden and defaults to
that class level. Mixed classes show **Question level** with configured labels
(SL, HL, Both for Chemistry) and help text. Unknown saved levels remain compatible.
The JSON field stays `scope`, with `BOTH` retained as the Both value. Settings can
select class levels explicitly; the application does not guess from class names.
Changing these defaults does not rewrite existing results or eligibility rules.

Use **Delete draft** in the class's metadata/document draft lists or either review
page. A named confirmation offers Delete and Cancel. Only unpublished drafts and
their owned temporary data are deleted. Published assessments, scores and other
classifications remain protected; deleted previews disappear from the class list.

Only assessment name/date, class identity, question labels and positive maximum
marks are necessary for import. Tags support multiple configured values. Empty
classifications/curriculum/scope remain unknown for new questions and preserve
existing values when updating. Short question names are optional. No full question
text, answers, source files, document extraction, parent contexts, page references,
confidence ratings or question-by-question review checkboxes are required.

The JSON schema is `studentdash-assessment-metadata-v2`. Question fields are
`number`, `marks`, `tags`, `curriculum_nodes`, `scope`, and optional `name`.
Scope and curriculum values must come from the selected profile; arbitrary-depth
curriculum parents remain explicit. Include individually scored parts only, not
parent subtotals. The preview total is calculated from question maxima.

Unknown tags/nodes, duplicate labels and invalid marks prevent confirmation with
an actionable error. The response and editable values remain available. Metadata
previews are saved privately and can be reopened from the class page after restart.
No source document or raw test content is stored by this workflow.

Student snapshots for classes using metadata imports show assessment history,
all configured tag categories, curriculum rollups and question/status evidence.
They are standalone HTML with inline styling, without test text, practice assets
or external dependencies. Each file contains only its own learner's evidence.

Studentdash generates stable internal IDs. Matching name/date imports recognize
an existing assessment; explicit IDs or the update selector identify an existing
assessment even when its name/date changes. Matching labels preserve question IDs,
scores and historical text. Replacements need explicit confirmation. Removing
questions with recorded evidence, or reducing maxima below saved scores, is blocked
rather than deleting evidence. Repeated confirmation of one preview is idempotent.

Metadata, previews, import/correction history and scores are stored in the existing
private `.sdclass` SQLite files under `data/entered_classes` (or your configured
location). Scores are independent of classifications: entering/pasting updated
Excel results does not clear tags or curriculum links. **Packages & workspace
backup** retains the full course and metadata history; restore never overwrites an
existing destination. Student snapshots do not include other students' results.

Older saved document imports remain readable, with their original documents and
review controls preserved. They are not required for new metadata imports. The
historical document-import instructions are in DOCUMENT_IMPORT_LEGACY.md.

## Unified results

Optional `assessment_type` is `assessment` or `exit_ticket`. Omitted types default
to Assessment for old records and preserve the type of an existing assessment on
update. Both use the same question classifications, scores and stable identity.
Type filters affect displayed evidence only. The default overall calculation is
unchanged; exit tickets receive no special weighting.

Regenerate student snapshots to replace old layouts with history, expandable skills
and curriculum analysis, feedback and suggested revision. All class assessments,
including older manual assessments, use this layout. Revision attempts, resource
activities and completion controls are hidden; their historical data is retained.

## Confidence and exit-ticket marks

Exit-ticket prompts default to one mark per scored question, unless explicit marks
or a teacher override say otherwise. Academic explanations remain scored questions;
self-reported confidence/reflection items are excluded from the question list.
Optional assessment metadata is `"confidence": {"enabled": true, "min": 1, "max": 5}`.
The fixed scale is 1 = very low confidence, 5 = very high confidence. `enabled` can
also be false; disabling configuration never deletes saved ratings. Omitted
configuration preserves an existing assessment's setting.

Enter individual ratings beside scores, save, and regenerate snapshots. Blank
means Not recorded and explicitly clears a saved rating. Old score-only submissions
and repeated metadata imports retain ratings. Ratings are stored separately from
scores, never affect performance or grades, and are not included in prompt JSON.
The assessment editor offers a reviewed correction for a mistakenly scored
confidence question, archiving original evidence without translating marks to a
rating. Neither this correction nor any migration runs automatically.
