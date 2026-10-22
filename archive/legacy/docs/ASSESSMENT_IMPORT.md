# Import a test document

Start Studentdash with `.\.venv\Scripts\python.exe teacher.py`, open
**http://127.0.0.1:5000/classes**, and select your class.

1. Choose **Import assessment** and upload a **PDF or DOCX**, up to 20 MB.
   **Create manually** remains available beside it.
2. Check the detected question count, marks and document-total comparison.
   The upload is a saved draft, not an assessment yet. You can reopen it from your class.
3. Use **Download original test** and **Compare extracted source** to check the
   questions. Parent instructions, source text, tables and figure references are kept.
4. Edit labels, text, marks or parent relationships. For a split, place the cursor
   where the second question begins, then choose **Split question**. Assign the
   two labels and marks yourself. **Combine with next** combines adjacent leaf
   questions under the same parent. You can also add, delete and reorder questions.
5. Accept or reject proposed classifications, or open **Selected classifications /
   edit manually**. Multiple tags are supported where the category permits them.
   **Accept all high-confidence suggestions** only selects strong explicit signals;
   it does not accept semantic inference or confirm question text/marks.
6. Check each question/context against the original and tick its review checkbox.
   **Save draft** preserves unfinished work without accepting pending suggestions.
7. Resolve validation errors. If you deliberately changed the test total, explain
   the difference in **Review note**. Confirm the final review and choose
   **Create assessment**. The normal spreadsheet score grid opens immediately.

Try the supplied fictional examples first:

- [PDF test](../examples/assessment_import/fictional-test.pdf)
- [DOCX test](../examples/assessment_import/fictional-test.docx)

Both contain **5 scorable questions, 16 marks**, with shared context for question 3.
The DOCX includes an actual table. These examples are not an official assessment.

## What works now and what still needs your real example

Extraction supports simple numbered questions, letter/roman subparts and explicit
mark annotations. DOCX tables are retained; PDF pages and DOCX paragraph references
help locate the source. Original files remain available after finalization.

Automatic classifications currently use **local profile rules and definition/keyword
matching**, not an LLM. Suggestions show detected versus inferred provenance and
heuristic confidence, not probabilities. Nothing is sent to an external AI service.
Teacher edits and rejections take precedence on later suggestion passes.

Curriculum proposals use only the class's configured tree. Select a curriculum
when creating the class, or connect one through **Curriculum & reviewed question
links**. Without a configured tree, suggestions cannot invent syllabus codes.
Tag suggestions still work and all proposed links require review.

Scans need transcription; OCR is not implemented. PDF columns, equations, automatic
Word numbering, table placement and image associations may need correction.
Figures stay in the original document and are referenced in review; diagrams are
not reconstructed in student dashboards. More accurate recognition of your question
bank's layout and stronger semantic inference wait for the real example document.

The original test and its draft/source metadata stay teacher-only. Final questions
use the existing assessment format, retain their parent context and go through the
existing score entry, overview and student export workflow.
# Prepare an assessment with ChatGPT

On **Import assessment**, choose **Prepare this assessment with ChatGPT**. Copy
the prompt, attach your test paper and mark scheme in ChatGPT, then paste its
complete JSON response into the webpage. The prompt includes the selected class's
allowed tags, curriculum node IDs and import schema, but no student information.
It requests question text, marks, shared context, multiple tags and supported
curriculum links. Studentdash does not call an external API.

**Preview ChatGPT assessment** loads an unconfirmed draft. Review it against both
documents; use **I have reviewed all imported questions and marks**, confirm the
final review and choose **Create assessment**. You do not have to edit or check
each question separately when all populated information is correct. Errors and
uncertainties remain visible; unknown marks or unreadable figures are not invented.
The same prompt/paste panel appears on existing PDF/DOCX import drafts. Pasting
there replaces that draft's question proposal while keeping the original uploaded
document and the existing participating students. A stale tab cannot overwrite a
newer saved draft. Existing created assessments and scores are never changed by
pasting a proposal.

Use root `start-assessment-import.bat` to open this workflow on Windows. It uses
root `data/entered_classes` unless STUDENTDASH_WORKBOOK selects another location.
