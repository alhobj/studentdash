# Local Chemistry exam reference bank

The three legacy Chemistry XLSX exports can be imported without changing student
practice pages. Open `output/chemistry-exam-bank/index.html` directly in a browser.
It supports wording/reference/topic search, paper and level filters, source-warning
filtering, and expandable source markschemes and examiner reports. No server or
internet connection is required.

```powershell
.venv/Scripts/python.exe tools/import_chem_exam_bank.py "C:/path/Chem paper 1 all.xlsx" "C:/path/Chem paper 2 all.xlsx" "C:/path/Chem paper 3 all.xlsx"
```

Use `--output output/another-bank` for another import. Existing destinations are
refused so imports cannot silently overwrite prior work. The importer accepts only
destinations inside the repository's ignored `output` directory. The source adapter
is separate from the subject-independent application core.

The bank contains raw source fields in `bank.json`, a source manifest and issue
counts in `report.json`, readable question pages, and byte-identical workbook
copies in `sources`. Each record retains its workbook hash, sheet, row and original
source ID. Formula strings are preserved, not evaluated. Original workbooks are
never saved or changed. IDs identify source records, not necessarily distinct
exam questions: overlapping parent questions and subparts are retained.

The original syllabus labels are legacy metadata. All current-curriculum mappings
remain unreviewed. The original imported pages retain grouped prompt, marks and
answer arrays. Cells at Excel's 32,767-character limit are flagged as
possibly truncated. Missing/external/incomplete diagrams are visibly marked, and
source markup is restricted to formatting, MathML and embedded PNG images. No
external images, scripts or links from the workbook are executed. The source
workbook remains the reference for formatting unsupported by the preview.

Nothing is added to `resources`, student navigation, assessments or student ZIPs.
This is a local teacher reference artifact, not an authenticated hosted service.
Keep the output folder private; do not copy it into the student SharePoint folder.
It is ignored by Git, so copying the entire bank folder is needed to move it to
another teacher computer. The importer, viewer assets and fictional tests are
version-controlled; exam content is not.

## Repair source HTML

Run `.venv/Scripts/python.exe -m tools.repair_chem_exam_bank` after importing, then
open `output/chemistry-exam-bank/repair.html` (also linked from the local bank).
This leaves `bank.json`, original question content and workbooks unchanged.
Re-running regenerates suggestions without touching browser corrections.

The repair adapter normalizes list punctuation and closes display markup. It
proposes a subpart only when records share a source/reference, the row/part counts
match, ordered marks agree, and the complete field has matching group counts and
identical content across the source rows. Question and markscheme are checked
separately. These are inferences, not verified official joins. Unresolved fields
stay grouped; lost text and diagram pixels are not invented. Source warnings
remain visible. Related-row links allow comparison in source order.

Select a question, edit context/question/markscheme/report HTML, and inspect the
sandboxed preview. Original source is available alongside the draft. Add notes
and a replacement source reference, select a review status and Save correction.
The editor retains drafts in browser storage with a visible warning if saving
fails. Export all corrections regularly: the JSON file is the portable saved
record, and can be imported on another computer with the same bank. Imports
validate source-bank identity and ask before replacing overlapping saved records.
Individual corrected HTML can also be downloaded. Corrections do not silently
overwrite original pages or publish to students.

Online source leads checked during repair work:
- Official legacy Chemistry question bank: https://questionbank.ibo.org/
- Official specimen papers: https://ibo.org/programmes/diploma-programme/assessment-and-exams/sample-exam-papers/
- November 2016 paper/markscheme listings (third-party, not verified as replacements): https://www.papersdaddy.com/ib/past-papers/sciences/chemistry/2016-november

No third-party exam text was substituted automatically. A better PDF or source
can be used to repair a record and its reference recorded in the repair notes.
