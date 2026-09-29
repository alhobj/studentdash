# Offline chemistry practice

Open `practice.html` for the syllabus hub. Each numbered sub-part has its own
page (`s1-1.html` through `r3-4.html`). `all-practice.html` is an optional view
of every activity. Keep this directory together when copying the resources;
pages share local CSS and JavaScript and need no server or internet connection.

The 22 sub-parts follow the first-assessment-2025 Structure/Reactivity outline.
R1.4 is labelled AHL. Coverage now includes at least two activities per sub-part, not
every syllabus statement. Some established activities include AHL extensions.
All numerical scenarios and question wording are original practice content.

Edit the source files, then regenerate the HTML from the repository root:

```powershell
python tools/build_chemistry_practice.py
```

- `practice-syllabus.json`: explicit group parents, topic titles and activity assignments.
- `practice-activities.json`: original activity markup.
- `practice-questions.json`: new scenario prompts, answers and worked explanations.
- `practice-extensions.json`: additional gap-filling practices, including labelled AHL extensions.
- `practice-labs.json` and `practice-labs.js`: hands-on experiments, builders, challenges and bounded numerical models. These appear first on their topic pages.
- `practice-activities.js`: existing activity calculations and controls; only present controls initialise.
- `practice-questions.js`: scenario selection, answer checks, explanations and session-only progress.
- `moly-triangles.js`: linked mole triangles and locks.
- `practice.css`: shared page styling.

The builder preserves original activity hashes by redirecting hub bookmarks to
their topic page. The mixed bonding activity is focused on ionic, covalent or
metallic examples on the corresponding S2 page; the all-activities view retains
the full comparison.

Browser checks (optional development dependencies and Edge on Windows):

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_chemistry_resources.py
```
