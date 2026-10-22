# Active application

For the supported class-based ChatGPT metadata assessment workflow, work in
`archive/legacy/studentdash/metadata_assessment.py` and its import routes/templates.
The canonical Windows launcher is `start-assessment-import.bat`. New imports use
metadata-only v2 JSON and one compact preview confirmation, not document extraction
or per-question checks. Keep legacy saved documents readable without migration.

The active local assessment workflow is in `app/`, launched by root `teacher.py`.
Read `docs/ARCHITECTURE.md` before domain or classification changes. The previous
application, its tests and original guidance are preserved in `archive/legacy/`.

- Keep the core subject- and curriculum-independent. Categories, vocabulary,
  levels and eligibility belong in profile data; curriculum nodes have explicit
  parents. Do not infer hierarchy from syllabus-code syntax.
- Preserve source workbooks. Do not put real student data, mappings, generated
  dashboards, private databases or backups into Git. Automated fixtures are fictional.
- Keep student identity stable across reimports and row reordering. Structural
  changes and classification replacements require explicit teacher review.
- Keep scores separate from classifications. Zero marks are graded; absent,
  exempt, missing and pending evidence never becomes zero.
- Keep the active teacher server loopback-only. No public/hosted features, games,
  exit tickets or student submission work without an explicit request.
- Run `python -m unittest discover -s tests -v` for active changes. Archived
  regression suites must be run from `archive/legacy` with that checkout on PYTHONPATH.
