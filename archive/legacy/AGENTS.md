# Architecture direction

Studentdash is subject-independent and curriculum-independent. IB Chemistry is
the first implementation and test profile, not the application domain model.
Read [the architecture direction](docs/ARCHITECTURE.md) before changing domain,
classification, curriculum or assessment behavior.

- Do not introduce new hard-coded IB, Chemistry, SL/HL, command-term, syllabus-code,
  experimental-skill, representation or other curriculum assumptions into the core.
- Subject-specific categories and allowed tags belong in data/configuration. A new
  subject must be able to define different categories without Python/code changes.
- Model curriculum as a generic hierarchy with explicit parent relationships.
  Course-level distinctions belong in configurable course/profile metadata.
- Preserve existing IB Chemistry functionality and workbook compatibility. Refactor
  only what the current feature needs; do not start a broad architecture rewrite.
- Prioritize usability with real IB Chemistry assessment data. Keep automated tests
  and development fixtures fictional; preserve original assessment evidence.
- Do not build the public/hosted version until explicitly requested.

The target concepts are Course, Student, Curriculum, CurriculumNode, Assessment,
Question, QuestionResult, TagCategory, Tag, QuestionTag, Feedback, Resource and
ExitTicket. These are architectural direction, not a requirement to implement all
entities immediately. Existing limitations are inventoried in the linked document.
