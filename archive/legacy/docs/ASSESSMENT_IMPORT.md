# Import assessment metadata from ChatGPT

Use root **start-assessment-import.bat** on Windows and open
http://127.0.0.1:5000/classes. Keep your existing data directory when updating.

1. Select a class and choose **Import assessment**.
2. Click **Copy prompt**. It contains the selected class ID, JSON schema, allowed
   categories/tags, configured curriculum nodes and scope options. No pupil data is included.
3. Attach the test paper in ChatGPT, paste the prompt, and copy the complete JSON response.
4. Paste the response in Studentdash and choose **Preview assessment**.
5. Check the editable table and total maximum marks. Correct only what is necessary.
6. Click **Import assessment** once. Enter/paste the students' scores separately.

The top teacher bar preserves class context across Classes, Assessments, Students,
Curriculum and Settings. Backups/restores and class-level configuration are under
Settings; class planning and upcoming tests remain accessible in the class area.

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
