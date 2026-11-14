# ArborSynapse file inventory

**317 retained repository files; 211 additional practice files inside the bundle.**

Every retained repository file is listed once below. “Optional” tools/tests support maintenance or compatibility and do not run routinely. The normal checks remain five tests. Practice builder source files are retained so bundled student resources can be updated.

## Removed in this audit

| File | Reason |
| --- | --- |
| `excel/teacher.py` | Unused standalone launcher; the Excel workspace is mounted by arborsynapse.py. |
| `server/teacher.py` | Unused standalone launcher; Start.cmd/Start.sh use the combined entry point. |
| `tree/.gitignore` | Duplicated root ignore rules; generated-tree exclusion was moved to the root file. |
| `tree/scripts/hosting-smoke.cjs` | Check for a removed standalone hosting/header configuration; current combined hosting has its own checks. |
| `tree/tests/fixtures/legacy-student-1001.json` | Obsolete assessment-prototype parser/rules/fixture; no production imports, replaced by current local-viewer contracts. |
| `tree/tests/fixtures/prototype/student-1001.json` | Obsolete assessment-prototype parser/rules/fixture; no production imports, replaced by current local-viewer contracts. |
| `tree/tests/fixtures/prototype/student-1002.json` | Obsolete assessment-prototype parser/rules/fixture; no production imports, replaced by current local-viewer contracts. |
| `tree/tests/model.test.ts` | Mixed obsolete prototype tests; three current graph/prompt checks retained in graph-contract.test.ts. |
| `tree/tests/support/assessment/model.ts` | Obsolete assessment-prototype parser/rules/fixture; no production imports, replaced by current local-viewer contracts. |
| `tree/tests/support/assessment/rules.json` | Obsolete assessment-prototype parser/rules/fixture; no production imports, replaced by current local-viewer contracts. |

## Retained repository files

### Root

| File | Purpose |
| --- | --- |
| `.dockerignore` | Exclude private data, caches and local builds from Docker images. |
| `.gitattributes` | Preserve binary bundles and correct Windows/Linux line endings. |
| `.gitignore` | Keep learner data, dependencies and generated outputs out of Git. |
| `AGENTS.md` | Contributor rules, data protection and minimal-test policy. |
| `FILES.md` | Complete retained-file inventory and reasons for this cleanup. |
| `README.md` | Short startup, migration, export and development guide. |
| `Start.cmd` | Windows setup and launch of the combined application. |
| `Start.sh` | Linux/macOS setup and launch of the combined application. |
| `arborsynapse.py` | Mount both assessment workspaces and built trees on one server; seed fictional Atlas data. |
| `requirements.txt` | Python application and local-server dependencies. |

### .github/workflows

| File | Purpose |
| --- | --- |
| `check.yml` | Five routine smoke tests; full suites only when manually requested. |

### deploy

| File | Purpose |
| --- | --- |
| `Dockerfile` | Build all tree viewers and the full Python testing container. |
| `atlas-update.sh` | Fetch changed revisions and rebuild/restart the managed Atlas sandbox. |
| `compose.yaml` | Atlas service, explicit test-host binding and persistent sandbox volumes. |

### docs

| File | Purpose |
| --- | --- |
| `ATLAS.md` | Required one-time setup for automatic Atlas testing. |
| `CURRICULUM.md` | Guide edition, statement provenance and editorial-content boundary. |
| `MOVE.md` | Move this branch to the planned independent repository without old history. |

### excel/app

| File | Purpose |
| --- | --- |
| `__init__.py` | Python package marker for the Excel-only application. |
| `analytics.py` | Weighted learner evidence and classification coverage for Excel imports. |
| `classification_import.py` | Validate and review classification proposals independently of scores. |
| `excel_import.py` | Read the existing grading workbook format without modifying it. |
| `generator.py` | Render single-learner reports and manage generated snapshots/ZIPs. |
| `restore.py` | Validate backups and restore into a new private destination. |
| `storage.py` | Transactional Excel-workspace database, identities and import history. |
| `teacher.py` | Excel-only import/review/report routes mounted at /excel/. |

### excel/app/templates

| File | Purpose |
| --- | --- |
| `backup.html` | Backup/restore and source history. |
| `base.html` | Shared Excel-workspace layout and navigation. |
| `classifications.html` | Classification JSON import. |
| `coverage.html` | Classification/curriculum coverage. |
| `dashboards.html` | Private dashboard generation. |
| `error.html` | Import/storage errors. |
| `results.html` | Grading-workbook import. |
| `review_classifications.html` | Classification replacement review. |
| `review_results.html` | Structural score-import review. |
| `student.html` | Single-learner Excel report. |
| `students.html` | Teacher learner overview. |

### excel/curricula

| File | Purpose |
| --- | --- |
| `chemistry-2025.json` | Chemistry 2025 hierarchy/resource configuration for this workspace’s import and reporting contracts. |
| `math-ai-sl-2021.json` | Mathematics AI SL 2021 hierarchy/resource configuration for this workspace’s import and reporting contracts. |

### excel/profiles

| File | Purpose |
| --- | --- |
| `ib_chemistry.json` | Captured classification vocabulary and level rules for the Excel-only workspace. |

### excel/tests

| File | Purpose |
| --- | --- |
| `test_browser.py` | Optional regression coverage: browser. |
| `test_local_app.py` | Optional regression coverage: local app. |

### scripts

| File | Purpose |
| --- | --- |
| `check.py` | Three routine Python checks; optional full Python suites. |
| `prepare.py` | Install shared npm dependencies and rebuild only changed tree sources. |
| `run.py` | Prepare assets and launch the combined application with Waitress. |

### server

| File | Purpose |
| --- | --- |
| `create_example_workbook.py` | Fictional workbook generator used by workbook regression fixtures. |
| `export_local_tree.py` | Optional single-learner command-line export and saved-source watcher. |
| `generate.py` | Optional headless generation of private student dashboard snapshots. |
| `seed_exit_tickets.py` | Fictional ticket seeding used by compatibility checks. |

### server/assets

| File | Purpose |
| --- | --- |
| `practice.zip` | 211 compressed offline practice assets; extracted automatically and preserved byte for byte. |

### server/curricula

| File | Purpose |
| --- | --- |
| `chemistry-2025.json` | Chemistry 2025 hierarchy/resource configuration for this workspace’s import and reporting contracts. |
| `math-ai-sl-2021.json` | Mathematics AI SL 2021 hierarchy/resource configuration for this workspace’s import and reporting contracts. |

### server/examples

| File | Purpose |
| --- | --- |
| `exit-ticket-confidence.json` | Confidence-enabled ticket schema example used by regressions. |
| `exit-ticket.json` | Fictional ticket definition used by the ticket seed helper. |

### server/examples/assessment_import

| File | Purpose |
| --- | --- |
| `fictional-test.docx` | Synthetic Word import fixture; contains no real assessment or learners. |
| `fictional-test.pdf` | Synthetic PDF import fixture for document-extraction regressions. |

### server/profiles

| File | Purpose |
| --- | --- |
| `ib_chemistry.json` | Captured classification vocabulary and level rules for the class/workbook workspace. |

### server/studentdash

| File | Purpose |
| --- | --- |
| `__init__.py` | Python package marker for the class/workbook application. |
| `analytics.py` | Learner-scoped assessment totals, grade evidence and diagnostic summaries. |
| `assessment_import.py` | Saved document import drafts, explicit review and atomic assessment conversion. |
| `assessment_types.py` | Assessment/exit-ticket filtering without rewriting results. |
| `chatgpt_assessment.py` | Compatibility parser for earlier ChatGPT assessment JSON. |
| `classification.py` | Configurable classification vocabulary, provenance and question diagnostics. |
| `classification_export.py` | Project saved classifications and statuses for one learner only. |
| `confidence.py` | Separate confidence validation and reporting; never changes marks. |
| `config.py` | Resolve workbook/output paths and prepare bundled practice resources. |
| `course_profile.py` | Resolve effective captured course vocabulary without destructive migrations. |
| `curriculum.py` | Explicit curriculum validation, catalog lookup and teaching/resource links. |
| `curriculum_tree.py` | Render curriculum selections using captured parent relationships. |
| `demo.py` | Deterministic fictional dataset backing workbook/import test fixtures. |
| `document_extract.py` | Extract supported PDF/Word content for compatibility imports. |
| `entry.py` | Versioned saved classes, stable identities, assessment definitions and score entry. |
| `entry_routes.py` | Teacher class, curriculum, assessment and score-entry routes. |
| `examples.py` | Clearly fictional practice suggestions for older workbook reports. |
| `excel.py` | Validated normalized workbook and saved-class readers. |
| `exit_routes.py` | Compatibility exit-ticket routes and guards for retired class interactions. |
| `exit_schema.py` | Validate ticket JSON and typed question/answer definitions. |
| `exit_store.py` | Versioned local exit-ticket definitions, participation and answers. |
| `exit_tickets.py` | Ticket parsing, grading and teacher-review helpers for workbook compatibility. |
| `freshness.py` | Detect changed inputs/assets before reusing student snapshots. |
| `import_drafts.py` | Safe deletion of preview drafts and owned temporary source records. |
| `import_routes.py` | Prompt/JSON import, editable previews and draft-review routes. |
| `import_suggestions.py` | Conservative profile-driven classification/curriculum suggestions. |
| `learning.py` | Compatibility learner context and saved teaching plans. |
| `local_tree.py` | Single-learner package export with stable package identity and separate confidence. |
| `metadata_assessment.py` | Current metadata-only prompt, JSON preview and reviewed assessment import. |
| `metadata_report.py` | Classification and curriculum evidence for text-free saved assessments. |
| `models.py` | Shared student, question, assessment and result data structures. |
| `overview.py` | Teacher overview projections and question/curriculum grouping. |
| `portability.py` | Private per-learner exports and safe backup/restore operations. |
| `portability_routes.py` | Teacher backup, restore and private-export endpoints. |
| `question_data.py` | Read question tables, participation and question-level result statuses. |
| `question_levels.py` | Configured course levels and question-scope controls. |
| `render.py` | Render private student reports and generate snapshot output. |
| `runtime_assets.py` | Restore bundled practice files only when the archive changes. |
| `teacher.py` | Class/workbook Flask application, local guards and teacher feedback routes. |
| `teacher_navigation.py` | Shared navigation with selected-class context. |
| `tree_export.py` | Export saved class results/classifications with the bundled local tree viewer. |
| `workspace.py` | Persistent teacher feedback and versioned local workspace state. |
| `teacher_tree.py` | Read-only teacher class/roster/results API; one learner at a time and only directly assigned graded evidence. |


### server/templates

| File | Purpose |
| --- | --- |
| `assessment_entry.html` | Question/classification editor. |
| `assessment_entry.js` | Question reordering and classification editing. |
| `assessment_review.html` | Compatibility document-import review. |
| `assessment_review.js` | Document-preview review interactions. |
| `assessment_upload.html` | Assessment prompt/JSON import entry. |
| `chatgpt_import.html` | Compatibility assessment JSON entry. |
| `chatgpt_import.js` | Assessment JSON form interactions. |
| `class_entry.html` | Selected class and assessment actions. |
| `classes.html` | Class creation and selection. |
| `confidence_correction.html` | Reviewed corrections preserving recorded score history. |
| `curriculum_review.html` | Review saved question-to-curriculum links. |
| `curriculum_select.html` | Reusable explicit-parent selection control. |
| `curriculum_tree.html` | Reusable expandable curriculum display. |
| `delete_import_draft.html` | Explicit draft-deletion confirmation. |
| `entry_base.html` | Shared teacher editor layout. |
| `entry_error.html` | Class-entry validation errors. |
| `error.html` | Application error display. |
| `exit_base.html` | Workbook ticket layout. |
| `exit_controls.html` | Workbook ticket publication controls. |
| `exit_editor.html` | Workbook ticket definition editor. |
| `exit_form.html` | Workbook ticket response form. |
| `exit_history.html` | Workbook ticket history. |
| `exit_list.html` | Workbook ticket listing. |
| `exit_preview.html` | Workbook ticket preview. |
| `exit_questions.html` | Reusable typed ticket-question fields. |
| `exit_results.html` | Workbook ticket results. |
| `exit_review.html` | Workbook ticket answer review. |
| `exit_unavailable.html` | Unavailable or retired ticket explanation. |
| `exported_classifications.html` | Learner-only per-question classifications in exported reports. |
| `feedback.html` | Teacher feedback editor/preview. |
| `learning_teacher.html` | Workbook-compatible teaching plans. |
| `local_student.html` | Workbook-compatible local learner view. |
| `metadata_review.html` | Compact editable metadata-import preview. |
| `metadata_student.html` | Current saved-class student report. |
| `next_plan.html` | Compatibility next-step planning controls. |
| `next_plan_snapshot.html` | Read-only next-step suggestions in snapshots. |
| `next_steps.html` | Curriculum next-step/resource display. |
| `score_entry.html` | Question scores and separate confidence entry. |
| `score_grid.js` | Spreadsheet score paste and validation. |
| `student.html` | Compatibility standalone workbook report. |
| `student_navigation.js` | Compatibility student report navigation. |
| `student_night.html` | Compatibility report theme styling. |
| `student_roster.html` | Student roster editor. |
| `style.html` | Shared report/teacher styling. |
| `teacher.html` | Teacher results overview. |
| `teacher_navigation.html` | Shared ArborSynapse navigation. |
| `transfer.html` | Private export/backup/restore controls. |
| `tree_export.html` | Saved classifications and optional direct-node export controls. |

### server/tests

| File | Purpose |
| --- | --- |
| `test_assessment_import.py` | Optional regression coverage: assessment import. |
| `test_authored_mcq_resources.py` | Optional regression coverage: authored mcq resources. |
| `test_booklet_learning_resources.py` | Optional regression coverage: booklet learning resources. |
| `test_booklet_resources.py` | Optional regression coverage: booklet resources. |
| `test_challenge_resources.py` | Optional regression coverage: challenge resources. |
| `test_chatgpt_assessment.py` | Optional regression coverage: chatgpt assessment. |
| `test_chem_exam_bank.py` | Optional regression coverage: chem exam bank. |
| `test_chem_exam_repairs.py` | Optional regression coverage: chem exam repairs. |
| `test_chemistry_resources.py` | Optional regression coverage: chemistry resources. |
| `test_classification.py` | Optional regression coverage: classification. |
| `test_confidence.py` | Optional regression coverage: confidence. |
| `test_confidence_paste.py` | Optional regression coverage: confidence paste. |
| `test_curriculum.py` | Optional regression coverage: curriculum. |
| `test_entry.py` | Optional regression coverage: entry. |
| `test_entry_browser.py` | Optional regression coverage: entry browser. |
| `test_exit_followup.py` | Optional regression coverage: exit followup. |
| `test_exit_tickets.py` | Optional regression coverage: exit tickets. |
| `test_expanded_mcq_resources.py` | Optional regression coverage: expanded mcq resources. |
| `test_foundation.py` | Optional regression coverage: foundation. |
| `test_import_browser.py` | Optional regression coverage: import browser. |
| `test_learning_expansion.py` | Optional regression coverage: learning expansion. |
| `test_learning_resources.py` | Optional regression coverage: learning resources. |
| `test_local_tree.py` | Optional regression coverage: local tree. |
| `test_math_classification.py` | Optional regression coverage: math classification. |
| `test_math_resources.py` | Optional regression coverage: math resources. |
| `test_mcq_review_resources.py` | Optional regression coverage: mcq review resources. |
| `test_metadata_assessment.py` | Optional regression coverage: metadata assessment. |
| `test_overview.py` | Optional regression coverage: overview. |
| `test_portability.py` | Optional regression coverage: portability. |
| `test_question_data.py` | Optional regression coverage: question data. |
| `test_repetition_resources.py` | Optional regression coverage: repetition resources. |
| `test_report_ordering.py` | Optional regression coverage: report ordering. |
| `test_skill_resources.py` | Optional regression coverage: skill resources. |
| `test_student_tools.py` | Optional regression coverage: student tools. |
| `test_support_resources.py` | Optional regression coverage: support resources. |
| `test_syllabus_graph.py` | Optional regression coverage: syllabus graph. |
| `test_syllabus_reference_resources.py` | Optional regression coverage: syllabus reference resources. |
| `test_teacher_usability.py` | Optional regression coverage: teacher usability. |
| `test_tree_export.py` | Optional regression coverage: tree export. |
| `test_unified_results.py` | Optional regression coverage: unified results. |
| `test_workspace.py` | Optional regression coverage: workspace. |

### server/tools

| File | Purpose |
| --- | --- |
| `author_skill_practice.py` | Original skills practice; source references and classifications are profile data. |
| `booklet-practice.js` | Interactive formula/data-booklet practice. Builder source; browser copies are bundled separately. |
| `build_chemistry_practice.py` | Build offline IB Chemistry practice pages from profile-local authored content. |
| `build_learning.py` | Portable practice journal; profiles supply content, the runtime is subject independent. |
| `build_math_practice.py` | Generate the standalone, offline Mathematics AI SL practice hub and topic pages. |
| `build_structure_mcq.py` | Build a curated 100-question SL collection from the three classified banks. |
| `create_import_example.py` | Build small fictional PDF/DOCX examples of the supported numbered layout. |
| `extend_structure_mcq.py` | Append 100 authored questions to a separate 200-question revision workbook. |
| `extract_chemistry_statements.py` | Rebuild guide statement identifiers/references from a supplied guide PDF. |
| `import_chem_exam_bank.py` | Import legacy Chemistry exports into an offline teacher reference bank. |
| `import_score_matrix.py` | Normalize an explicit-ID ScoreMatrix into a new, validated assessment workbook. |
| `link_skill_sections.py` | Authored practice-context links for the skill directory; not guide prerequisites. |
| `map_practice_skills.py` | Explicit profile-local skill assignments, reviewed by task kind and section. |
| `mcq_authoring.py` | Small authoring helpers; subject content lives in separate profile modules. |
| `mcq_chemistry.py` | Repeated chemistry skills for sections outside the original workbook extension. |
| `mcq_math.py` | Authored AI SL section questions: four skill families with five related variants. |
| `mcq_review.py` | Validated, portable editorial changes to a profile's MCQ bank. |
| `migrate_exam_databases.py` | Add classification sheets without reserializing any original worksheet. |
| `practice_booklet_tasks.py` | Render authored lookup, unit-selection and calculation practice. |
| `practice_booklets.py` | Build offline booklet companions using profile-local references and mappings. |
| `practice_challenges.py` | Render profile-local challenge data without adding curriculum rules to the app. |
| `practice_graph.py` | Build an offline graph from explicit profile hierarchy and guide cross-references. |
| `practice_mcq.py` | Publish the original authored workbook extension with its deterministic A-D order. |
| `practice_repetition.py` | Render short, authored sets for practising the same method repeatedly. |
| `practice_skill_index.py` | Render the offline skill directory and search index. |
| `practice_skills.py` | Generic profile-driven skills labels, practice and coverage reporting. |
| `practice_student_tools.py` | Build generic offline student tools from each profile's authored content. |
| `practice_support.py` | Offline practice navigation and low-stakes skill checks from profile data. |
| `practice_syllabus.py` | Render syllabus references from resource-profile data, without core curriculum rules. |
| `repair_chem_exam_bank.py` | Prepare reversible, evidence-labelled repairs and an offline source editor. |
| `workspace_backup.py` | Create or restore a complete selected-course backup into a new folder. |

### server/tools/assets

| File | Purpose |
| --- | --- |
| `guided-practice.js` | Shared guided exercise interactions. Builder source; browser copies are bundled separately. |
| `learning.css` | Shared practice-journal styling. Builder source; browser copies are bundled separately. |
| `learning.js` | Shared practice-journal runtime. Builder source; browser copies are bundled separately. |
| `mcq-review.js` | Editorial MCQ review controls. Builder source; browser copies are bundled separately. |
| `skills-index.js` | Searchable skill directory runtime. Builder source; browser copies are bundled separately. |
| `skills-practice.css` | Offline skills-practice styling. Builder source; browser copies are bundled separately. |
| `skills-practice.js` | Offline skills-practice interactions. Builder source; browser copies are bundled separately. |
| `student-records.js` | Local student practice persistence and backups. Builder source; browser copies are bundled separately. |
| `syllabus-graph.css` | Offline curriculum graph styling. Builder source; browser copies are bundled separately. |
| `syllabus-graph.js` | Offline curriculum graph interactions. Builder source; browser copies are bundled separately. |

### server/tools/exam_bank_assets

| File | Purpose |
| --- | --- |
| `bank.css` | Teacher exam-bank browser styling. Builder source; browser copies are bundled separately. |
| `bank.js` | Teacher exam-bank filtering and display. Builder source; browser copies are bundled separately. |
| `repair.css` | Reversible exam-bank editor styling. Builder source; browser copies are bundled separately. |
| `repair.js` | Reversible exam-bank edit controls. Builder source; browser copies are bundled separately. |

### server/tools/resources

| File | Purpose |
| --- | --- |
| `structure_mcq_authored.json` | Authored structure MCQ source used by the offline practice builder and its regressions. |

### tests

| File | Purpose |
| --- | --- |
| `test_combined.py` | Optional regression coverage: combined. |
| `test_teacher_tree.py` | Focused checks for learner isolation, direct evidence and read-only teacher APIs. |


### tree

| File | Purpose |
| --- | --- |
| `index.html` | Full-tree browser entry point. |
| `package-lock.json` | Reproducible dependency versions for all tree views. |
| `package.json` | Shared npm dependencies, workspaces and quick/full build/test commands. |
| `tsconfig.json` | Full-tree TypeScript compilation settings. |
| `vite.config.ts` | Full-tree bundling and development asset refresh. |

### tree/docs

| File | Purpose |
| --- | --- |
| `LOCAL_STUDENT_GUIDE.md` | Short guide copied into every individual student folder. |

### tree/integration

| File | Purpose |
| --- | --- |
| `chemistree_links.py` | Validated curriculum-only deep links for teacher/student reports. |

### tree/local-runtime

| File | Purpose |
| --- | --- |
| `Start.cmd` | Windows launcher for the individual local-result viewer. |
| `Start.ps1` | Built-in Windows loopback server without Python/Node requirements. |
| `serve.py` | Optional read-only Python loopback server for student packages. |
| `test_serve.py` | Optional server allowlist, size-limit and symlink regression checks. |

### tree/local-viewer

| File | Purpose |
| --- | --- |
| `Ring.tsx` | Earned/possible mark slices and accessible ring labels. |
| `index.html` | Private local-result viewer browser entry. |
| `main.tsx` | Student results, evidence details and separately persisted confidence. |
| `model.ts` | Validate snapshots, revisions and independent confidence backups. |
| `style.css` | Local-result viewer layout and visual states. |
| `tsconfig.json` | Independent local-viewer type-checking scope. |

### tree/scripts

| File | Purpose |
| --- | --- |
| `accessibility-smoke.cjs` | Optional manual keyboard/mobile/accessibility browser checks. |
| `browser-smoke.cjs` | Optional manual browser checks for full-tree interactions and local progress. |
| `build-local-viewer.mjs` | Bundle the exportable local viewer, registry and launchers. |
| `check-student-build.ts` | Reject private development data and oversized public release assets. |
| `generate-student-data.ts` | Derive compact public runtime data from reviewed sources. |
| `performance-smoke.cjs` | Optional manual lazy-loading and runtime performance browser checks. |
| `practice-smoke.cjs` | Optional manual guided-practice browser checks. |
| `build-teacher-viewer.mjs` | Build the teacher UI separately from public/student exports. |


### tree/simple

| File | Purpose |
| --- | --- |
| `index.html` | Standalone simple-tree browser entry. |
| `package.json` | Simple-tree workspace build/test commands. |
| `tsconfig.json` | Simple-tree compilation boundary; intentionally separate from the full tree. |
| `vite.config.ts` | Standalone simple-tree bundle and development settings. |

### tree/simple/scripts

| File | Purpose |
| --- | --- |
| `build-map.mjs` | Generate the simple map from reviewed nodes and teaching dependencies. |
| `sync-data.mjs` | Refresh the generated simple-map input before builds. |

### tree/simple/src

| File | Purpose |
| --- | --- |
| `HighlightControls.tsx` | Collapsed chapter, arrow-depth and availability sections in the left panel. |
| `dependencies.ts` | Dependency reachability, redundancy cleanup and unlocked-node rules. |
| `highlighting.ts` | Connection levels and chapter color calculations. |
| `highlights.css` | Highlighted/marked/locked card and edge styling. |
| `layout.ts` | Prerequisite-aware top/bottom placement and routed edges. |
| `main.tsx` | Simple-tree interaction entry point. |
| `style.css` | Compact simple-tree layout and controls. |

### tree/simple/src/data

| File | Purpose |
| --- | --- |
| `prerequisites.json` | Reviewed teaching dependencies retained as source data. |

### tree/simple/tests

| File | Purpose |
| --- | --- |
| `bottom-sort.test.ts` | Optional regression coverage: bottom sort. |
| `dependencies.test.ts` | Optional regression coverage: dependencies. |
| `highlighting.test.ts` | Optional regression coverage: highlighting. |
| `placement.test.ts` | Optional regression coverage: placement. |
| `simple.test.ts` | Optional regression coverage: simple. |

### tree/src

| File | Purpose |
| --- | --- |
| `GuidedPractice.tsx` | Hint, worked-solution and transfer-question interaction. |
| `Help.tsx` | Student help and guidance. |
| `MapView.tsx` | Full map, simple-mode switch, marking and dependency display. |
| `PracticeSection.tsx` | Node-specific original practice and level selection. |
| `ProgressTools.tsx` | Explicit local progress export/import/reset controls. |
| `curriculum.ts` | Public curriculum projection, lookup, graph and prompt helpers. |
| `layout.ts` | Full-tree geometry and route planning. |
| `links.ts` | Public curriculum-only links and URL validation. |
| `main.tsx` | Full-tree search, filters, node details and self-assessment UI. |
| `practice.ts` | Guided-practice schema and node/level selection. |
| `progress.ts` | Validated local self-assessment storage and manual transfer. |
| `style.css` | Full-tree responsive styling. |

### tree/src/data

| File | Purpose |
| --- | --- |
| `map.json` | Reviewed official statements, sources and distinct editorial teaching data. |
| `practice.json` | Original guided practice content and explanations. |

### tree/tests

| File | Purpose |
| --- | --- |
| `curriculum.test.ts` | Optional regression coverage: curriculum. |
| `dependencies.test.ts` | Optional regression coverage: dependencies. |
| `graph-contract.test.ts` | Optional regression coverage: graph contract. |
| `layout.test.ts` | Optional regression coverage: layout. |
| `links.test.ts` | Optional regression coverage: links. |
| `local-results.test.ts` | Optional regression coverage: local results. |
| `practice-content.test.ts` | Optional regression coverage: practice content. |
| `progress.test.ts` | Optional regression coverage: progress. |
| `release-boundary.test.ts` | Optional regression coverage: release boundary. |
| `student-data.test.ts` | Optional regression coverage: student data. |
| `temporary-marks.test.ts` | Optional regression coverage: temporary marks. |
| `unlocked.test.ts` | Optional regression coverage: unlocked. |
| `teacher-results.test.ts` | Focused teacher-response identity, status and mark validation checks. |


### tree/tests/python

| File | Purpose |
| --- | --- |
| `test_chemistree_links.py` | Optional regression coverage: chemistree links. |

### tree/teacher-viewer

| File | Purpose |
| --- | --- |
| `index.html` | Teacher-only browser entry; prevents the student entry from mounting twice. |
| `main.tsx` | Off-by-default data toggle, class/student selection, result rings and native evidence dialog. |
| `model.ts` | Reject mismatched learner/class responses and invalid or duplicate evidence. |
| `style.css` | Fixed-size controls and ring overlays that preserve tree geometry. |
| `tsconfig.json` | Type-check the separate teacher entry and its shared UI. |


### tree/shared

| File | Purpose |
| --- | --- |
| `ControlPanel.tsx` | Shared accessible left panel and native sections that start collapsed. |
| `control-panel.css` | Fixed-width, scrollable panels that keep the map stable while menus open. |
| `TimeControls.tsx` | Collapsed time slider, previous/next assessment dates and All results reset. |
| `timeline.ts` | Cumulative date filtering with explicit undated-record handling; no confidence/history writes. |


## Bundled practice files

These are stored inside `server/assets/practice.zip`, then restored to `server/resources/` on first use. They are learner-facing pages, offline scripts/styles, or source data required to rebuild those pages. The archive was not changed in this audit.

### ib-chemistry (inside practice.zip)

| File | Purpose |
| --- | --- |
| `all-practice.html` | Offline page: All activities · Chemistry practice. |
| `authored-mcq.js` | Authored multiple-choice questions. Browser-ready data for file-based use. |
| `authored-mcq.json` | Authored multiple-choice questions. |
| `basics-r1.html` | Offline page: R1 small steps · Chemistry practice. |
| `basics-r2.html` | Offline page: R2 small steps · Chemistry practice. |
| `basics-r3.html` | Offline page: R3 small steps · Chemistry practice. |
| `basics-s1.html` | Offline page: S1 small steps · Chemistry practice. |
| `basics-s2.html` | Offline page: S2 small steps · Chemistry practice. |
| `basics-s3.html` | Offline page: S3 small steps · Chemistry practice. |
| `booklet-practice.html` | Offline page: Booklet lookup practice. |
| `booklet-practice.js` | Formula/data-booklet exercises. |
| `booklet-practice.json` | Formula/data-booklet exercises. |
| `booklet.json` | Booklet definitions and references. |
| `challenges-r1.html` | Offline page: What drives chemical reactions? · Challenge practice. |
| `challenges-r2.html` | Offline page: How much, how fast and how far? · Challenge practice. |
| `challenges-r3.html` | Offline page: What are the mechanisms of chemical change? · Challenge practice. |
| `challenges-s1.html` | Offline page: Models of the particulate nature of matter · Challenge practice. |
| `challenges-s2.html` | Offline page: Models of bonding and structure · Challenge practice. |
| `challenges-s3.html` | Offline page: Classification of matter · Challenge practice. |
| `challenges.html` | Offline page: Harder tasks · Challenge practice. |
| `challenges.js` | Extended challenge exercises. |
| `challenges.json` | Extended challenge exercises. |
| `class-practice.html` | Offline page: Teacher class overview · Chemistry. |
| `data-booklet.html` | Offline page: Chemistry data booklet. |
| `find-practice.html` | Offline page: Find practice · Chemistry. |
| `foundations.js` | Foundational lesson content. Browser-ready data for file-based use. |
| `foundations.json` | Foundational lesson content. |
| `guided-practice.html` | Offline page: Guided problem solving · Chemistry. |
| `guided-practice.js` | Guided practice exercises. Browser-ready data for file-based use. |
| `guided-practice.json` | Guided practice exercises. |
| `investigations.html` | Offline page: Investigations · Chemistry. |
| `investigations.json` | Investigation content/runtime. |
| `learning-catalog.js` | Browser-ready practice catalog. |
| `learning-home.html` | Offline page: My learning · Chemistry. |
| `learning.css` | Practice-journal interface. |
| `learning.js` | Practice-journal interface. |
| `mcq-review.js` | Editorial MCQ review controls. |
| `moly-triangles.js` | Chemistry practice visual interactions. |
| `my-practice.html` | Offline page: My practice · Chemistry. |
| `practice-activities.js` | Chemistry activities. Browser-ready data for file-based use. |
| `practice-activities.json` | Chemistry activities. |
| `practice-extensions.json` | Additional Chemistry exercises. |
| `practice-labs.js` | Laboratory activities. Browser-ready data for file-based use. |
| `practice-labs.json` | Laboratory activities. |
| `practice-questions.js` | Chemistry questions and feedback. Browser-ready data for file-based use. |
| `practice-questions.json` | Chemistry questions and feedback. |
| `practice-syllabus.json` | Section descriptions and ordering. |
| `practice.css` | Chemistry practice styling. |
| `practice.html` | Offline page: Practice hub · Chemistry practice. |
| `prior-learning.html` | Offline page: Prior learning · Chemistry practice. |
| `question-review.html` | Offline page: Teacher question review · Chemistry. |
| `r1-1.html` | Offline page: R1.1 · Measuring enthalpy changes · Chemistry practice. |
| `r1-2.html` | Offline page: R1.2 · Energy cycles in reactions · Chemistry practice. |
| `r1-3.html` | Offline page: R1.3 · Energy from fuels · Chemistry practice. |
| `r1-4.html` | Offline page: R1.4 · Entropy and spontaneity · Chemistry practice. |
| `r2-1.html` | Offline page: R2.1 · How much? The amount of chemical change · Chemistry practice. |
| `r2-2.html` | Offline page: R2.2 · How fast? The rate of chemical change · Chemistry practice. |
| `r2-3.html` | Offline page: R2.3 · How far? The extent of chemical change · Chemistry practice. |
| `r3-1.html` | Offline page: R3.1 · Proton transfer reactions · Chemistry practice. |
| `r3-2.html` | Offline page: R3.2 · Electron transfer reactions · Chemistry practice. |
| `r3-3.html` | Offline page: R3.3 · Electron sharing reactions · Chemistry practice. |
| `r3-4.html` | Offline page: R3.4 · Electron-pair sharing reactions · Chemistry practice. |
| `readiness.html` | Offline page: Find your next step · Chemistry. |
| `readiness.json` | Foundational readiness checks. |
| `repetition.json` | Repeated-method question sets. |
| `s1-1.html` | Offline page: S1.1 · Introduction to the particulate nature of matter · Chemistry practice. |
| `s1-2.html` | Offline page: S1.2 · The nuclear atom · Chemistry practice. |
| `s1-3.html` | Offline page: S1.3 · Electron configurations · Chemistry practice. |
| `s1-4.html` | Offline page: S1.4 · Counting principles by mass: The mole · Chemistry practice. |
| `s1-5.html` | Offline page: S1.5 · Ideal gases · Chemistry practice. |
| `s2-1.html` | Offline page: S2.1 · The ionic model · Chemistry practice. |
| `s2-2.html` | Offline page: S2.2 · The covalent model · Chemistry practice. |
| `s2-3.html` | Offline page: S2.3 · The metallic model · Chemistry practice. |
| `s2-4.html` | Offline page: S2.4 · From models to materials · Chemistry practice. |
| `s3-1.html` | Offline page: S3.1 · The periodic table: Classification of elements · Chemistry practice. |
| `s3-2.html` | Offline page: S3.2 · Functional groups: Classification of organic compounds · Chemistry practice. |
| `similar-practice.js` | Similar-question navigation. |
| `skill-coverage.json` | Question-to-skill coverage data. |
| `skills-index.js` | Skill-directory search. |
| `skills-practice.css` | Skills-practice interface. |
| `skills-practice.html` | Offline page: Chemistry · Skills practice. |
| `skills-practice.js` | Skills-practice interface. |
| `skills.html` | Offline page: Skills index · Chemistry. |
| `skills.json` | Skill definitions and authored prompts. |
| `student-backup.html` | Offline page: Combined student backup · Chemistry. |
| `student-record-profiles.js` | Subject-specific local-record configuration. |
| `student-records.js` | Local practice records and manual backup/restore. |
| `study-support.js` | Study-support interactions. |
| `syllabus-cross-references.json` | Explicit section/skill cross-references. |
| `syllabus-graph.css` | Browsable explicit curriculum graph. |
| `syllabus-graph.html` | Offline page: Syllabus graph · Chemistry. |
| `syllabus-graph.js` | Browsable explicit curriculum graph. |
| `syllabus-graph.json` | Browsable explicit curriculum graph. |
| `syllabus-reference.json` | Curriculum reference text and provenance. |
| `syllabus-statements.json` | Numbered guide statement identifiers and explicit references. |

### ib-math-ai-sl (inside practice.zip)

| File | Purpose |
| --- | --- |
| `activities.json` | Mathematics practice activities. |
| `authored-mcq.js` | Authored multiple-choice questions. Browser-ready data for file-based use. |
| `authored-mcq.json` | Authored multiple-choice questions. |
| `basics-1.html` | Offline page: Number and algebra: small steps · Mathematics AI SL. |
| `basics-2.html` | Offline page: Functions: small steps · Mathematics AI SL. |
| `basics-3.html` | Offline page: Geometry and trigonometry: small steps · Mathematics AI SL. |
| `basics-4.html` | Offline page: Statistics and probability: small steps · Mathematics AI SL. |
| `basics-5.html` | Offline page: Calculus: small steps · Mathematics AI SL. |
| `booklet-practice.html` | Offline page: Booklet lookup practice. |
| `booklet-practice.js` | Formula/data-booklet exercises. |
| `booklet-practice.json` | Formula/data-booklet exercises. |
| `booklet.json` | Booklet definitions and references. |
| `challenges-1.html` | Offline page: Number and algebra · Challenge practice. |
| `challenges-2.html` | Offline page: Functions · Challenge practice. |
| `challenges-3.html` | Offline page: Geometry and trigonometry · Challenge practice. |
| `challenges-4.html` | Offline page: Statistics and probability · Challenge practice. |
| `challenges-5.html` | Offline page: Calculus · Challenge practice. |
| `challenges.html` | Offline page: Harder tasks · Challenge practice. |
| `challenges.js` | Extended challenge exercises. |
| `challenges.json` | Extended challenge exercises. |
| `class-practice.html` | Offline page: Teacher class overview · Mathematics AI SL. |
| `coverage.html` | Offline page: Syllabus coverage · Mathematics AI SL. |
| `coverage.json` | Mathematics activity coverage. |
| `exploration-projects.html` | Offline page: Investigations and reflection · Mathematics AI SL. |
| `extensions.json` | Additional Mathematics activities. |
| `find-practice.html` | Offline page: Find practice · Mathematics AI SL. |
| `formula-booklet.html` | Offline page: Mathematics AI formula booklet. |
| `foundations.js` | Foundational lesson content. Browser-ready data for file-based use. |
| `foundations.json` | Foundational lesson content. |
| `guided-practice.html` | Offline page: Guided problem solving · Mathematics AI SL. |
| `guided-practice.js` | Guided practice exercises. Browser-ready data for file-based use. |
| `guided-practice.json` | Guided practice exercises. |
| `investigations.html` | Offline page: Investigations · Mathematics AI SL. |
| `investigations.json` | Investigation content/runtime. |
| `learning-catalog.js` | Browser-ready practice catalog. |
| `learning-home.html` | Offline page: My learning · Mathematics AI SL. |
| `learning.css` | Practice-journal interface. |
| `learning.js` | Practice-journal interface. |
| `math-extensions.js` | Mathematics extension interactions. |
| `math-practice.css` | Mathematics practice interactions/styling. |
| `math-practice.html` | Offline page: Mathematics practice hub · Mathematics AI SL. |
| `math-practice.js` | Mathematics practice interactions/styling. |
| `math-theme.css` | Mathematics practice theme. |
| `mcq-1-1.html` | Offline page: SL 1.1 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-2.html` | Offline page: SL 1.2 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-3.html` | Offline page: SL 1.3 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-4.html` | Offline page: SL 1.4 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-5.html` | Offline page: SL 1.5 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-6.html` | Offline page: SL 1.6 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-7.html` | Offline page: SL 1.7 multiple-choice practice · Mathematics AI SL. |
| `mcq-1-8.html` | Offline page: SL 1.8 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-1.html` | Offline page: SL 2.1 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-2.html` | Offline page: SL 2.2 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-3.html` | Offline page: SL 2.3 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-4.html` | Offline page: SL 2.4 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-5.html` | Offline page: SL 2.5 multiple-choice practice · Mathematics AI SL. |
| `mcq-2-6.html` | Offline page: SL 2.6 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-1.html` | Offline page: SL 3.1 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-2.html` | Offline page: SL 3.2 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-3.html` | Offline page: SL 3.3 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-4.html` | Offline page: SL 3.4 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-5.html` | Offline page: SL 3.5 multiple-choice practice · Mathematics AI SL. |
| `mcq-3-6.html` | Offline page: SL 3.6 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-1.html` | Offline page: SL 4.1 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-10.html` | Offline page: SL 4.10 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-11.html` | Offline page: SL 4.11 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-2.html` | Offline page: SL 4.2 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-3.html` | Offline page: SL 4.3 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-4.html` | Offline page: SL 4.4 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-5.html` | Offline page: SL 4.5 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-6.html` | Offline page: SL 4.6 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-7.html` | Offline page: SL 4.7 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-8.html` | Offline page: SL 4.8 multiple-choice practice · Mathematics AI SL. |
| `mcq-4-9.html` | Offline page: SL 4.9 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-1.html` | Offline page: SL 5.1 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-2.html` | Offline page: SL 5.2 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-3.html` | Offline page: SL 5.3 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-4.html` | Offline page: SL 5.4 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-5.html` | Offline page: SL 5.5 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-6.html` | Offline page: SL 5.6 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-7.html` | Offline page: SL 5.7 multiple-choice practice · Mathematics AI SL. |
| `mcq-5-8.html` | Offline page: SL 5.8 multiple-choice practice · Mathematics AI SL. |
| `mcq-review.js` | Editorial MCQ review controls. |
| `my-practice.html` | Offline page: My practice · Mathematics AI SL. |
| `prior-learning.html` | Offline page: Prior learning · Mathematics AI SL. |
| `question-review.html` | Offline page: Teacher question review · Mathematics AI SL. |
| `readiness.html` | Offline page: Find your next step · Mathematics AI SL. |
| `readiness.json` | Foundational readiness checks. |
| `repetition.json` | Repeated-method question sets. |
| `similar-practice.js` | Similar-question navigation. |
| `skill-coverage.json` | Question-to-skill coverage data. |
| `skills-index.js` | Skill-directory search. |
| `skills-practice.css` | Skills-practice interface. |
| `skills-practice.html` | Offline page: Mathematics AI SL · Skills practice. |
| `skills-practice.js` | Skills-practice interface. |
| `skills.html` | Offline page: Skills index · Mathematics AI SL. |
| `skills.json` | Skill definitions and authored prompts. |
| `student-backup.html` | Offline page: Combined student backup · Mathematics AI SL. |
| `student-record-profiles.js` | Subject-specific local-record configuration. |
| `student-records.js` | Local practice records and manual backup/restore. |
| `study-support.js` | Study-support interactions. |
| `syllabus-cross-references.json` | Explicit section/skill cross-references. |
| `syllabus-graph.css` | Browsable explicit curriculum graph. |
| `syllabus-graph.html` | Offline page: Syllabus graph · Mathematics AI SL. |
| `syllabus-graph.js` | Browsable explicit curriculum graph. |
| `syllabus-graph.json` | Browsable explicit curriculum graph. |
| `syllabus-reference.json` | Curriculum reference text and provenance. |
| `topic-1.html` | Offline page: Number and algebra · Mathematics AI SL. |
| `topic-2.html` | Offline page: Functions · Mathematics AI SL. |
| `topic-3.html` | Offline page: Geometry and trigonometry · Mathematics AI SL. |
| `topic-4.html` | Offline page: Statistics and probability · Mathematics AI SL. |
| `topic-5.html` | Offline page: Calculus · Mathematics AI SL. |

### learning (inside practice.zip)

| File | Purpose |
| --- | --- |
| `investigations.js` | Investigation content/runtime. |
| `learning-centre.css` | Shared learning-centre styling. |
| `learning-state.js` | Shared local learning-state persistence. |
| `student-centre.js` | Shared learning-centre interaction controller. |

## Local files outside Git

`data/` and `output/` contain private teacher data/exports; keep them locally. `.venv/`, `node_modules/`, generated maps, built viewers, unpacked practice resources and caches are recreated automatically and are excluded from the repository. They are not extra source documents.
