# First classroom use

Use one marked test and one class first. Keep the teacher application on your own
computer. Share downloads, not the teacher application or its data folders.

## Prepare and start

Have the test as a text-based PDF or DOCX, its markscheme, your roster, and scores
for each question/subpart. Scanned PDFs need transcription; OCR is not available.
The score grid accepts pasted Excel cells, not an uploaded arbitrary score workbook.
Overall totals alone cannot produce question-level feedback.

From the Studentdash folder, run:

```powershell
.\.venv\Scripts\python.exe teacher.py
```

Open **http://127.0.0.1:5000/classes**. Create or select your class. When creating
it, select the appropriate curriculum. Paste names and optional emails without
headings. Keep student order consistent with your marking spreadsheet.

## Upload, review and enter scores

1. Choose **Import assessment** and upload the PDF or DOCX (maximum 20 MB).
2. Compare the extracted questions with the original. Check subparts, context,
   maximum marks, equations and diagrams. Figures remain in the original test;
   don't assume they will appear in student snapshots.
3. Review classifications and curriculum links. Suggestions are not verified IB
   classifications. Correct the assessment title/date and participating students.
4. Mark each question/context reviewed, confirm the final review, then choose
   **Create assessment**. Save a draft if you need to finish reviewing later.
5. Paste a rectangle of question scores into the score grid. Exclude headings and
   names; verify the displayed row and column order first. Save scores.
6. Check several totals against your spreadsheet, including a zero and an absent
   student. **0** is graded; **A** absent, **E** exempt, **M** missing, **P** or blank
   pending. Incomplete rows do not receive invented totals. New managed
   assessments do not assume grade boundaries.
7. Review the overview and publish any feedback you want students to see.
   Saved feedback drafts are private. Generate dashboards if using **Open snapshot**.
   Private packages render fresh saved data when downloaded.

## Download and share

Open **Packages & workspace backup** from the class page. Check the selected class
shown at the top. Use one class at a time when distributing packages.

| Download | Where it belongs |
|---|---|
| Classroom practice package | Shared class folder; contains practice resources, no student scores |
| Private student package | A folder or message accessible only to that student and the teacher |
| Teacher workspace backup | Private teacher storage; contains class records and original imports |

Select each student explicitly before downloading their private package. Its
filename contains the student's internal ID. Record the name-to-file match while
downloading. Do not place all private student packages in a class-wide folder.
Do not share `data`, the entire `output` folder, exam-bank repair files, or backups.

Before distributing the class set, download one package yourself, extract the
whole ZIP, and open **index.html** in Edge or Chrome. Check the assessment, marks,
feedback and practice links. Keep the `resources` folder beside `index.html`.
Try this on a student device too: school-managed download/browser settings have
not been tested by the local software checks.

SharePoint is used for file delivery here. Students must **download → extract →
open index.html**; the SharePoint file preview is not the application. Do not send
students the `127.0.0.1` address—it refers to their own computer, not yours.

## Tell students

“Download your ZIP, extract all files, and open index.html. Start with your next
step or practice task. Your practice does not change your test marks. Export My
progress before changing computers or moving files. If I assign practice, export
the completion report and upload it where I specify.”

Progress and completion reports are local/self-reported; there is no automatic
teacher sync or shared login. Local interactive exit-ticket sessions in the teacher
app are a demonstration workflow, not a SharePoint submission service. For tomorrow,
use standalone practice assignments and uploaded completion reports, or your usual
school tool for collecting exit tickets.

## Finish the session

Download a **workspace backup for each class** you changed and keep the application
version with it. Practice progress needs its own student export. Exam-bank repairs
need their own corrections export. Git stores application code, not these records.
After correcting marks or publishing feedback, create a new student package and
tell the student to replace their old copy, exporting practice progress first.

Further detail: [test import](ASSESSMENT_IMPORT.md), [score entry](FIRST_ASSESSMENT.md),
[distribution and backups](PORTABLE_PRACTICE.md), [exam repair bank](EXAM_BANK.md).
