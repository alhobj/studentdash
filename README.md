# ArborSynapse

Assessments, classifications, student dashboards and learning trees in one folder.
Chemistry is the included tree; the assessment system also supports other subjects.

## Start locally

Install Python 3.10+ and Node.js 22.12+ (or 24 LTS), then open **Start.cmd**.
On Linux/macOS run `sh Start.sh`. First start installs dependencies and builds the
bundled tree views. Later starts reuse the build until its source changes.
Open **http://127.0.0.1:5000/classes**. Keep the launcher window open.

Tree options live in a left panel. Its sections start closed: open a heading for
chapter highlights, arrows, layout, student data, practice or backups.

Open **Teacher tree** for the teacher view. **Student data: Off / On** enables
class/student selection and read-only result rings; click a ring for tests and
question marks. Data starts off and is not saved in the browser. Broad section
classifications do not become individual-node evidence.

The navigation includes classes, results, the full/simple learning trees and the
Excel-only workspace. Use your existing prompt → metadata JSON → paste scores
workflow. Student exports include saved classifications and optional node rings.
Confidence remains local to each student's browser.

## Keep your existing data

Stop the old app, back it up, then **copy** its `data` directory into this folder.
Keep your original until you have checked the class list and results. Do not copy
Python/npm dependencies or generated builds. Existing `.sdclass` IDs/formats and
local confidence keys are retained. Custom `STUDENTDASH_*` paths still work.

## Export for a student

Open a class → **Export student folder**. The bundled viewer path is filled
in. Saved tags and section classifications follow automatically. Choose one student
and their own empty/local OneDrive folder, then export. They open **Start Studentdash.cmd**.
Re-export to that same folder for updates; confidence stays separate.

## Develop and test

Small changes need only the relevant feature tests. The default quick checks are
`python scripts/check.py` (3 tests) and `npm test --prefix tree` (2 tests).
GitHub pushes/PRs use these checks; documentation-only edits skip CI.
For releases or broad refactors, run `python scripts/check.py --full` and
`npm run test:full --prefix tree`, or choose **Full suite** when manually running
GitHub Actions. `npm run build:all --prefix tree` rebuilds all tree views.
Only source and a compressed practice bundle belong in Git; data, dependencies and
builds are ignored. Practice resources unpack automatically on first use.

For automatic Atlas testing after the new repository exists, follow
[the short Atlas setup](docs/ATLAS.md). Keep the testing sandbox fictional.
For moving this branch into the new repository, see [the move steps](docs/MOVE.md).

[File inventory](FILES.md) lists every retained source file, bundled practice asset and removal from the cleanup.
