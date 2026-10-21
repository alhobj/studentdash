# Enter your first assessment

Start Studentdash from the project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe teacher.py
```

Open **http://127.0.0.1:5000/classes** on the same computer.

1. **Create a class.** Give it a name. Paste one student name per row from Excel;
   optionally include email addresses in the second column. Leave out column
   headings. Your roster is saved and can be reused for every assessment.
2. Choose **Import assessment** to [upload and review your test](ASSESSMENT_IMPORT.md),
   or **Create manually** to follow the question-entry steps below.
   For manual creation, enter its name and date, and an optional description.
   All current students are selected; expand **Participating students** to change that.
3. Enter question labels and maximum marks. Use **Add question**, the arrow buttons
   and **Remove** to arrange questions. Text is optional.
4. Open **Classify** beside a question. Enter a reviewed curriculum code or topic
   label, and select any applicable tags. Every category can remain unclassified.
   Curriculum text is stored as entered; Studentdash does not verify official codes.
5. Choose **Save assessment & enter scores**. Students appear as rows and questions
   as columns, with maximum marks in the headings.
6. Enter scores, or copy a rectangle of cells from Excel, click the starting cell
   in the grid and paste. Do not include names or headings. Match the visible row
   and column order before pasting. Use Tab across cells, Enter down, Shift+Enter
   up, or arrow keys. Decimal points and decimal commas are accepted.
7. Use **A** for absent, **E** for exempt, **M** for missing, and **P** or blank for
   pending. Full status words also work. **0 is a graded score.** Invalid values
   are highlighted beside the affected cell; fix them before saving.
8. Choose **Save scores**. A completed row shows its earned/possible marks. Exempt
   questions are removed from the possible marks. Other unfinished rows show
   **Incomplete**, **Absent** or **Missing**. No previous total survives a change
   to incomplete question evidence. Suggested grades are left blank for these new
   assessments; no grade boundaries are assumed.
9. Choose **View overview** to review the class and questions. Return through
   **Back to class & score entry** to make corrections.
10. Choose **Generate student dashboards** after saving. In the overview, choose
    **Open snapshot** beside a student. Review that student's marks and feedback.
    The snapshot omits the class roster, names/emails and other students' records.
    Review your own free-text content before sharing the individual page.

To continue another day, start Studentdash, open **My classes**, select your class
and choose **Enter / edit scores** beside the assessment. You do not need to paste
the roster again. **Add students** updates the class roster; select additions in
the assessment editor if they should also join an existing assessment.

Use **Edit questions & classifications** to revise questions. Reordering retains
their marks. A maximum cannot be reduced below an existing score. A student or
question with recorded marks/statuses cannot be removed unless you deliberately
clear those entries to pending first. Concurrent edits from an older tab are
rejected rather than overwriting newer work.

These classes are separate from the existing workbook/demo. The **Existing workbook
/ demonstration** option opens that workflow. Studentdash remains local; give
students only their individual generated page, not access to the teacher application.
