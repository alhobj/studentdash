# Subject-independent architecture direction

Accepted direction, 2026-09-23. Studentdash is being developed as a
subject-independent and curriculum-independent system. IB Chemistry is its first
real-world implementation and test profile. The immediate priority is a usable
local workflow with real IB Chemistry assessment data. Existing functionality must
continue to work. This document proposes incremental changes; it does not describe
an already implemented profile system or authorize a large rewrite.

## Core and profile boundary

The generic core should model Course, Student, Curriculum, CurriculumNode,
Assessment, Question, QuestionResult, TagCategory, Tag, QuestionTag, Feedback,
Resource and ExitTicket. Keep identity, membership, marks, result status, feedback,
review provenance and learner-scoped access independent of subject vocabulary.

A course selects a profile and curriculum version. Course/profile metadata defines
any levels and their question eligibility relationships explicitly; the engine must
not infer eligibility from names such as SL or HL. Grading scales and display labels
also belong in configuration rather than universal curriculum rules.

TagCategory and Tag definitions are data, with stable IDs and display labels.
QuestionTag links questions to allowed tags and preserves source/review information.
IB Chemistry may configure Command term, Skill, Cognitive demand, Context,
Representation, Experimental skill and Quantitative skill. Another subject can
define entirely different categories and tags without Python/code changes. Generic
validation checks references against the selected profile; generic views iterate
configured categories. No category, including Command term, is universally required.

CurriculumNode belongs to a curriculum and has an explicit parent reference, label
and optional external code. Support arbitrary tree depth; codes are metadata, not
instructions for deriving parentage. Validate parent references and reject cycles.
Question-to-node mappings preserve review status and provenance. Legacy-to-current
mapping requires review rather than automatic equivalence. Aggregate each question
once even when it maps to several tags or descendant nodes in the selected scope.

## Current assumptions and migration points

Milestone update: the teacher-entry workflow now stores persistent classes and
assessments separately from imported workbooks. It adapts them to the existing
reporting model, derives totals from question evidence, and does not require levels
or classifications. The existing vocabulary has moved to
`profiles/ib_chemistry.json`; new classes capture a copy, and their generic tag editor
and validation use that copy. The default remains the existing IB Chemistry profile.
This is not a profile-selection UI or a generic curriculum importer. Curriculum
mapping is still teacher-entered text, not an implemented CurriculumNode tree.

This inventory describes the current implementation, not approved patterns for new
generic features. Links identify the main places to revisit when a feature touches
the corresponding behavior.

| Area | Current assumption and evidence | Incremental destination |
|---|---|---|
| Tag definitions and validation | [classification.py](../studentdash/classification.py) loads the default `VOCABULARY` from the IB Chemistry JSON profile. Workbook imports still use that default; teacher-entered classes supply their captured vocabulary. | Retain compatibility while extending explicit profile selection only when needed. |
| Automatic classification | `command_terms`, `RULES` and `classify` in the same module recognize a fixed vocabulary and chemistry text patterns. [question_data.py](../studentdash/question_data.py) automatically creates `CommandTerm` tags from `ActionVerb`. | Keep subject rules in profile configuration or an isolated profile adapter. Generic marking and analytics must not depend on chemistry inference. |
| Curriculum | `syllabus_hierarchy` splits restricted code syntax; `performance` uses those derived ancestors. `question_data.py` requires S/R current codes and stores one mapping per question in `QuestionSyllabus`. | Explicit Curriculum/CurriculumNode trees and reviewed question-node links; preserve legacy/current codes as source metadata. |
| Levels and eligibility | `question_data.py` validates SL/HL memberships and SL/HL/BOTH questions; `applicable` makes HL include SL. The score-matrix and overview workflows reuse this behavior. | Configured course levels and explicit eligibility, preserving today's matrix through a compatibility adapter. |
| Workbook/domain shape | [models.py](../studentdash/models.py) and [excel.py](../studentdash/excel.py) expose level, topic, subtopic and action verb; linked question results require these classifications. Course and Curriculum are not first-class records. | Introduce course/profile identity when needed; translate existing columns at the import boundary while retaining existing workbook support. |
| Grades | `excel.py` and `question_data.py` require grades 1 through 7 for global and assessment boundary sets. | Configurable grading scales retaining existing thresholds and override semantics. |
| Analytics and presentation | [analytics.py](../studentdash/analytics.py) and [student.html](../templates/student.html) expose fixed topic/subtopic/command-term groups and command-term learning hints. Resources match topic text. | Configured category views and hint policies; curriculum/resource references use stable IDs as those features migrate. |
| Exit tickets | [exit_schema.py](../studentdash/exit_schema.py) requires subject/topic/subtopic and question action verbs; [exit_tickets.py](../studentdash/exit_tickets.py) matches formal evidence by topic/subtopic labels. These are structural constraints even though labels accept free text. | Optional configured classifications and node links; keep exit-ticket evidence separate from formal assessment results. |
| Source-bank tools | [migrate_exam_databases.py](../tools/migrate_exam_databases.py) knows exam export columns, chemistry classification and SL/HL reports. [build_structure_mcq.py](../tools/build_structure_mcq.py) curates a specific Chemistry collection. | Treat these as IB Chemistry source adapters/content tooling; do not make their source formats core contracts. |
| Fixtures and wording | Demo/example generators, seeds, tests and the exit-ticket editor contain Chemistry examples; [package description](../studentdash/__init__.py) and an Excel warning explicitly say IB. | Retain IB Chemistry fixtures as regression coverage, label examples as profile examples, and use generic wording when touching core interfaces. |

`ClassificationVocabulary` in exported workbooks is currently explanatory: editing
it does not configure the runtime validator. `studentdash/config.py` currently
selects file locations, not subject profiles. Configured tag categories now work in
the new editor, but the remaining subject assumptions below have not all migrated.

## Gradual migration, triggered by practical features

1. **Now: document and preserve.** Keep the real-assessment import, question review,
   score-matrix, feedback and snapshot workflow as the priority. Record newly found
   assumptions here. No runtime refactor is required for this direction alone.
2. **When extending classification:** extract the existing vocabulary into an IB
   Chemistry profile, then make validation/import and affected views consume generic
   categories. Explicitly select/version profiles and preserve legacy defaults.
   Demonstrate a second fictional subject with different categories using only
   configuration; require unchanged IB tag validation and results.
3. **When extending curriculum coverage:** introduce explicit trees and reviewed
   question-node links behind the existing import boundary. Preserve original codes
   and review decisions. Verify arbitrary-depth trees, non-IB codes, invalid parents,
   cycles and no double-counting, alongside existing IB diagnostic results.
4. **When extending course management or eligibility:** introduce Course and its
   profile metadata, replacing fixed level rules with configured relationships.
   Preserve SL/HL/BOTH eligibility and denominators; demonstrate a course without
   those levels. Move grading-scale assumptions when grading work requires it.
5. **As related interfaces change:** replace fixed category panels and text joins
   with configured views and stable references. Version stored/imported structures
   and provide reversible migrations before changing persisted records.

Each increment should be independently useful for the local assessment workflow.
Keep existing workbooks, IDs, marks, missing/exempt semantics, teacher reviews,
feedback and retry history intact. Compare affected IB outputs before and after;
retain fictional regression fixtures. Do not silently reclassify historical data
when a profile changes. Keep assessment summaries, question evidence and exit-ticket
evidence separate under the existing rules.

Public hosting, accounts, online deployment and service integrations are deferred.
Their discussion in the system guide is future context, not the next implementation
phase. No public/hosted work begins under this architecture direction.
