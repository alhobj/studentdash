# Individual local tree packages (OneDrive method B)

The teacher's source remains private. This exporter writes only one student's directly
mapped graded question results into their individual OneDrive folder. It does not share
or connect to OneDrive itself. Existing access restrictions must be set on each folder.

Build Chemistree's local viewer first (`node scripts/build-local-viewer.mjs` in Chemistree).
Its `local-package/curriculum.json` lists the exact permitted node IDs and codes.
Create a private, teacher-reviewed JSON mapping such as:

```json
{
  "Q001": "ib-2025-structure-1.1.1",
  "Q002": "ib-2025-structure-2.2.6"
}
```

Each listed question must assess exactly that one objective directly. This is an explicit
teacher decision, not a conversion of broad topic tags. Multi-objective questions require
separately scored subquestions in the source, each mapped once. Unmapped questions are
omitted. Existing historical mappings, scores and workbooks are never modified.

From the Studentdash folder, with its normal Python environment:

```powershell
.\.venv\Scripts\python.exe export_local_tree.py --source "C:\Private\classroom.xlsx" --student "1001" --mapping "C:\Private\tree-links.json" --viewer "C:\Projects\chemistree\local-package" --destination "C:\SchoolOneDrive\Student1001\MyLearning"
```

Replace the paths and ID with your actual local locations. A `.sdclass` source is also
accepted via the existing Studentdash reader. Existing validated question scores are used;
revisions/retakes are not silently combined with original marks. QuestionResults are needed
for workbook exports; assessment totals cannot be assigned to individual tree nodes.

Add `--watch` to keep the teacher process running. It re-exports when the source or mapping
is saved, checking every 10 seconds; close it with Ctrl+C. Formula-based workbook results
still require Excel recalculation and saving. This command uses the existing source reader;
it does not monitor an unsaved Excel editing session. Re-run without watch after building
new viewer assets to update the application even if marks have not changed.

The initial destination must be empty. Updates preserve its package ID and reject a
different student or curriculum. Results are written using atomic file replacement and a
monotonic revision number. If marks and mappings have not changed, results are untouched.
Source/mapping validation errors retain the previous results. A partial OneDrive transfer
may still occur on the remote device; the viewer validates updates before replacing its
in-memory results. Do not run two exporters simultaneously for the same destination.

The package contains generic application assets plus:
- `package.json`: schema/map versions, internal learner ID and stable opaque package ID.
- `results.json`: package ID, revision, export time, and only this student's mapped graded
  question evidence (assessment names, question IDs/numbers, node IDs, earned/possible marks).

Confidence is not exported or stored in the shared folder. It belongs to the student's
browser profile at the stable loopback address and uses a separate package-specific key.
Re-exporting marks, changing a mapping, or updating app assets cannot write that store.
Keep package bindings and teach students to export confidence backups. Recreating a package
with a new ID deliberately does not silently reuse another package's confidence.

Students choose **Always keep on this device**, then open **Start.cmd** and keep its terminal
running. The built-in Windows launcher needs no Python/npm but respects script execution
policy. A permitted Python runtime can alternatively run **serve.py**. If neither runtime
is permitted, this pilot cannot run there yet. Windows and school OneDrive checks remain
on-device acceptance work; do not claim automatic school-wide compatibility.

The exporter core is curriculum-neutral: it consumes a registry and explicit mappings.
Chemistree is the first viewer; this change does not yet add rings to the separate Mathtree.
No class data, private fixtures, student names/emails, teacher comments or answer text are
bundled in the shared generic template. No public hosting, authentication or student result
API is added to Studentdash. This is not a declaration of GDPR compliance or school approval.

## Try it with a fictional learner first

With Chemistree and Studentdash in sibling folders, run `npm run build:local` in Chemistree,
then from Studentdash:

```powershell
.\.venv\Scripts\python.exe tools\create_local_tree_demo.py --viewer "..\chemistree\local-package" --destination "..\chemistree\local-pilot"
```

Open `chemistree\local-pilot\Start.cmd`. The first curriculum node shows Results 4/5
from two fictional questions. Set its confidence to Confident. Repeat the same command
with `--updated`: the node should change to Results 3/5 after the next local check, while
confidence stays Confident. Close and reopen the viewer in the same browser to check recovery.
This is the acceptance scenario for the actual Windows device; it uses no real student data.
