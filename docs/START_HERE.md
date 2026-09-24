# Start using Studentdash: your next steps

Your first target is **one real class, one marked assessment, and a checked HTML
dashboard for each student**. Use the class-entry screens below. You do not need
to build a special workbook or finish the dashboard design before entering marks.

This guide covers the local system that exists today. Real data comes from your
own roster, test and marking records; the examples supplied in the project are
fictional.

## 1. Gather the material for one assessment

Choose a short assessment you have already marked. Have these ready:

| Material | What you need |
|---|---|
| Class roster | One student name per row in Excel; email is optional |
| Original test | PDF or DOCX, preferably with selectable text |
| Mark scheme | Your reference for checking each question's maximum marks |
| Question marks | Each student's score for each question or subpart |
| Assessment details | Actual title, date and participating students |
| Classifications, if ready | Reviewed topic/curriculum labels and applicable tags |

Keep the original test, mark scheme and marking spreadsheet unchanged. Studentdash
will hold a working copy of your assessment evidence. If you have only overall
totals, collect question marks before using this workflow: do not invent question
scores to make the total fit.

Use school-approved local storage for real records. Keep real source documents
under a private data location, not in `examples/`, `tests/` or documentation.
The project's `data/` folder is Git-ignored, but Git-ignore is not a backup or an
access control.

**Done when:** you can identify every student's marks and the maximum for every
scorable question.

## 2. Start the application

Open the VS Code terminal and select PowerShell. From the project folder:

```powershell
Set-Location 'C:\Users\Alexander\Documents\Programmering\Studentdash'
```

If `.venv` does not exist yet, run this once:

```powershell
python -m venv .venv
```

Install the project dependencies on first setup, or after they change:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the teacher application:

```powershell
.\.venv\Scripts\python.exe teacher.py
```

Leave that terminal running. Open **http://127.0.0.1:5000/classes** in your browser
on this computer. To stop the application later, press **Ctrl+C** in the terminal.
If `python` is unavailable during setup, try `py -m venv .venv`.

You do not need to run `create_example_workbook.py`, seed exit tickets or run
`generate.py` for this class-entry route. If you reach a workbook error on the
home page, open `/classes` directly.

**Done when:** you see **My classes**.

## 3. Create your real class

1. Enter a clear class name including its cohort/year.
2. Copy student names from Excel, one per row, without the heading. You may copy
   emails as a second column, but they are optional.
3. Paste into **Paste student roster** and click **Create class**.
4. Check the names and student count before continuing. Distinguish students with
   identical names in the roster.

Create this class once and reuse it for later assessments. Do not create a new
class for every test. Start a separate class for a new cohort.

**Done when:** the class page shows the correct roster.

## 4. Add and review the real test

### If you have a PDF or DOCX

1. Click **Import assessment** and upload the test (maximum 20 MB).
2. Open **Download original test** and **Compare extracted source**.
3. Compare every question with the original and mark scheme. Check labels, text,
   subparts, shared instructions and maximum marks. Count marks at the scorable
   subparts; do not also count their parent heading as another scored question.
4. Correct extraction mistakes. Use split/combine controls where needed.
5. Review classification suggestions. Accept only tags you agree with; reject or
   edit the others. Leave uncertain classifications unclassified.
6. Check the assessment title, date and participants before entering scores; use
   **Edit questions & classifications** after creation if needed.
7. Tick the review checkbox for each checked question/context. Resolve validation
   errors and check the total against the mark scheme. If you deliberately changed
   the total, explain it in **Review note**.
8. Confirm the final review and click **Create assessment**.

Import suggestions currently use local rules, not an external AI model. Scanned
tests need transcription because OCR is not implemented. Check equations and
tables carefully. Diagrams remain in the original test and are not reconstructed
in the student HTML pages. Keep the original test available for students when
their revision depends on a figure.

For a rehearsal, create a separate class named `Practice - fictional` with invented
students and use the [fictional test](../examples/assessment_import/fictional-test.pdf).
It should produce **5 scorable questions totalling 16 marks**. Keep that rehearsal
separate from your real class.

### If importing is unsuitable

1. Click **Create manually**.
2. Enter the actual assessment title and date; check **Participating students**.
3. Add one row per scorable question/subpart, with labels such as `1`, `2a`, `2b`.
4. Enter the maximum marks and, preferably, question text for useful revision pages.
5. Open **Classify** to add reviewed mappings/tags if available.
6. Click **Save assessment & enter scores**.

Curriculum codes are not verified against an official syllabus. The bundled IB
Chemistry profile does not yet contain a curriculum tree. You can start using
marks and feedback now and improve classifications later.

**Done when:** the score grid has exactly the students and question columns you expect.

## 5. Enter the actual marks

1. Arrange your Excel marks to match the visible student and question order.
2. Copy only the rectangle of marks, excluding names, headings and total columns.
3. Click its starting cell in Studentdash and paste. For the first paste, use a
   small block and check its placement before entering the rest.
4. Use the following values consistently:

| Enter | Meaning |
|---|---|
| A number, including `0` | Graded work; zero means no marks earned |
| `A` | Absent |
| `E` | Exempt; this question's maximum is excluded for this student |
| `M` | Missing |
| `P` or blank | Pending marking |

5. Fix highlighted invalid values and click **Save scores**.
6. Compare at least three students with your original records: a high score, a
   lower score and an incomplete/absent case if present. Check both earned and
   possible marks. Check the first and last pasted rows to catch alignment errors.
7. Reopen **Enter / edit scores** to confirm the saved entries are there.

Totals are derived from question marks. Unfinished rows remain incomplete; do not
replace blanks with zero merely to obtain a total. New class-entry assessments do
not assume grade boundaries, so a blank suggested grade is expected.

**Done when:** saved marks and completed totals agree with your marking records.

## 6. Review results and add feedback

1. Choose **View overview** and select the assessment.
2. Review question performance and data-quality notes. Check how many graded
   responses support a percentage before deciding what to reteach.
3. Open **Feedback & revisions** for a student and select the assessment.
4. Write a short comment and one actionable revision task per line. Refer to the
   student's actual answers and question labels.
5. Save the draft, open **Preview saved draft and publish**, check it, then publish.
6. Repeat for the students whose feedback you want to include.

Publishing makes feedback available for the next export. It does not send anything
or update HTML files already generated. Later draft changes also need publication.

**Done when:** a preview shows the right student's evidence and intended feedback.

## 7. Generate and check the HTML files

1. Return to the class overview and click **Generate student dashboards**.
2. Click **Open snapshot** beside a student.
3. Check their assessment selector, marks, question details and published feedback.
4. Find the files in `output/class-<class-id>/` using VS Code's Explorer or File
   Explorer. With default settings, each class gets its own folder. The files are
   named `student<student-id>.html`; IDs are assigned by the application.
5. Match filenames to students using the overview's snapshot links. Do not guess
   from roster position. Open the actual file directly in a browser to check its
   offline appearance.

The teacher link at `127.0.0.1` works only on your computer. The generated `.html`
file is the item you can give to a student. It is a snapshot: regenerate after
changes to scores, published feedback or templates.

For entered classes, generate through the selected class's interface. The standalone
`generate.py` command uses its configured source rather than your browser's selected
class. Custom `STUDENTDASH_OUTPUT` settings change the output location.

**Done when:** several representative files show correct evidence and work when
opened directly, including one incomplete case if your class has one.

## 8. Choose the HTML design

Generated student pages now use the **Night** palette, with section navigation,
highlighted teacher feedback and no introductory banner. Regenerate existing
dashboards to apply it. To choose a different appearance:

1. Open `examples/layouts/index.html` in a browser, or run this in a second
   PowerShell terminal from the project folder:

   ```powershell
   Start-Process '.\examples\layouts\index.html'
   ```

2. Compare the ten designs using their fictional content. Pick the one you find
   easiest to read. Check a narrow browser window and print preview as well.
3. Write down the design name and the few changes you want: for example, smaller
   heading, larger question text, or feedback nearer the top.
4. Apply the chosen design to the source templates, then regenerate and review
   student pages. **There is no theme-selection button yet.** The gallery files
   are proposals and opening one does not change the application.

If you want me to implement the choice, use a request like this:

> Apply the [design name] gallery design to the generated student dashboards.
> Make feedback easy to find and question text readable on phones. Preserve
> assessment filtering, question details, revision checklists and printing.
> Use fictional data to develop and verify the design.

If editing the code yourself, these are the relevant files:

| File | What to change there |
|---|---|
| `templates/student.html` | Student page structure and student interactions |
| `templates/student_night.html` | Student Night palette, sidebar, phone and print layout |
| `templates/student_navigation.js` | Section links for the selected assessment |
| `templates/style.html` | Shared CSS; changes can also affect teacher screens |
| `build_layout_previews.py` | Gallery theme definitions and preview builder |
| `templates/teacher.html` | Teacher overview structure |
| `templates/entry_base.html` | Shared shell for class and assessment entry screens |

Edit templates for lasting changes. Direct edits to `output/...html` disappear
on regeneration. Gallery edits alone do not update the application templates.
Keep student styling scoped when it should affect only student pages.

After a design change, check assessment filtering, question expansion, checklist
clicks, phone-width layout, long question text, empty/incomplete records and print
preview. Use fictional records for development and automated tests; review real
output locally before distribution.

**Done when:** the generated pages use your chosen appearance and their controls work.

## 9. Back up and share the first set

### Include interactive Chemistry practice

Open [Chemistry practice studio](../resources/ib-chemistry/practice.html) in a
browser. It is a single offline HTML file with three activities:

| Activity | What students do | Suggested feedback task |
|---|---|---|
| Limiting reactants | Change reactant amounts; compare ratios and leftover amounts | Predict the water yield, then explain why adding excess reactant does not increase it |
| Dilution | Change concentration, initial volume and dilution factor | Calculate a final concentration and explain why solute amount stays constant |
| Equilibrium | Calculate Q and compare it with a chosen K | Predict the net reaction direction and justify it using Q and K |

1. Try the relevant activity yourself and check its worked example.
2. In the student's feedback, name the activity and give a specific task from the
   table. Save and publish the feedback, then regenerate the dashboard.
3. Send `resources/ib-chemistry/practice.html` alongside the student's dashboard.
   The practice file is the same for everyone and contains no student data.
4. Ask students to return their working/explanation through your normal classroom
   process. The activities provide immediate feedback but do not submit or save
   responses, update dashboard marks, or tick dashboard revision tasks.

The practice studio is a separate resource file. It is not automatically embedded
in the dashboard's **Resources** section, and the class-entry screens do not yet
offer an interactive-resource attachment editor. Keep both downloaded HTML files
available to students. Only the optional source-reference links require internet.
Use the studio locally; no hosting or student accounts are needed.

### Preserve and distribute your files

1. Finish saving, then stop the teacher application with **Ctrl+C**.
2. Copy the whole `data/entered_classes/` folder to your approved backup location.
   This preserves class files, paired feedback workspaces and imported source/draft
   material together. If you configured a different workbook location, this folder
   lives beside that workbook instead.
3. Archive the generated class output in a dated folder if you need the exact
   version distributed. Keep your original marking records and test too.
4. Check the recipient-to-file match and share only that student's HTML file through
   your school's approved channel. Test one file through that channel first: some
   systems block HTML attachments or require download before opening in a browser.
5. If HTML is unsuitable, check the page's print preview and save a PDF as a static
   alternative. Print the intended assessment view; PDF loses interactive controls.

Each page omits the roster and structured names/emails, but your free-text feedback
and question content still need review. Do not share the class source, database or
whole output folder with students.

Explain to students: open the file, select the assessment, read the feedback, inspect
the relevant questions and do the revision tasks. Checklist ticks stay in that
browser; they are not submissions and are not visible to you.

**Done when:** your backup exists and a correctly matched file opens through your
intended distribution method.

## 10. Use the same routine next time

Start `teacher.py`, open **My classes**, select the existing class and add the next
assessment. Then repeat: **review questions → save marks → review results → save
and publish feedback → generate → check → back up → share**.

Keep original marks when students retry questions. Record a revision attempt
separately in **Feedback & revisions**; retry evidence does not replace the original
assessment score. Check attempt entries carefully because that editor currently
lacks correction/deletion controls.

Leave interactive exit tickets for a separate fictional rehearsal. They currently
use simulated identities and are not a real student login/submission service. The
next step for classroom use is the local assessment-and-file workflow above.

For more detail, see [first assessment entry](FIRST_ASSESSMENT.md),
[document import](ASSESSMENT_IMPORT.md), and the [system reference](SYSTEM_GUIDE.md).
