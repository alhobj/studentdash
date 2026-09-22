# Student dashboard design options

Open `index.html` in a browser to compare Studio, Editorial, Campus, Night and
Focus. Each folder contains a standalone `student1001.html` with identical
fictional content and working assessment filtering, question details, revision
checklists and printing. No server or internet connection is required.

These previews are design proposals; they do not change the application's default
theme. Campus uses a side rail on wide screens, Editorial uses a narrow reading
column, and Focus uses a wider two-column layout. All stack on small screens.

Rebuild from the project root with:

```powershell
.\.venv\Scripts\python build_layout_previews.py
```

The builder creates a fresh fictional fixture and renders the learner once before
applying five styles. It does not read the configured course workbook or workspace.
Generated dates change on rebuild. Browser checklist state may be shared between
these previews because they represent the same learner and tasks.
