# Offline chemistry practice

Open `practice.html` for the syllabus hub. Each numbered sub-part has its own
page (`s1-1.html` through `r3-4.html`). `all-practice.html` is an optional view
of every activity. Keep this directory together when copying the resources;
pages share local CSS and JavaScript and need no server or internet connection.

The 22 sub-parts follow the first-assessment-2025 Structure/Reactivity outline.
R1.4 is labelled AHL. Coverage now includes at least two activities per sub-part, not
every syllabus statement. Some established activities include AHL extensions.
All numerical scenarios and question wording are original practice content.

For students building confidence, `prior-learning.html` contains 12 lessons
with 24 short tasks on symbols, formulas, particles, changes, units, ratios and
basic calculations. `basics-s1.html` through `basics-r3.html` contain two starter
tasks for each of the 22 sub-parts (44 additional tasks). R1.4 remains labelled
AHL. Every lesson includes a reminder, optional hints, worked steps, answer
checks and a reset button. Topic pages and the hub link to these starters;
each starter links back to its topic's main activities.

These introductory tasks are untimed and have no score. Responses are not
stored or transmitted. Hints and explanations also work without JavaScript.
Numeric starter answers use 1e-8 tolerance; short word answers accept the
listed synonyms, ignoring case, surrounding whitespace and final punctuation.
They do not grade free-form explanations or significant-figure notation.

`challenges.html` links to 22 harder multi-part tasks, one for every sub-part,
in `challenges-s1.html` through `challenges-r3.html`. Each has two linked
numerical checkpoints (44 in total), optional hints and worked solutions,
and a written explanation/evaluation prompt with a discussion for self-review.
R1.4 remains labelled AHL. Numerical checks use 0.1% tolerance; written arguments
are not graded. These are original teaching problems rather than official exam
questions. Notes and answers stay in the open page and are not saved.

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
- `foundations.json` and `foundations.js`: prior-learning and section starter content and answer checking.
- `challenges.json` and `challenges.js`: harder multi-part tasks and numerical checking. Both subject builders use `tools/practice_challenges.py` for layout; subject content stays in its profile.

The builder preserves original activity hashes by redirecting hub bookmarks to
their topic page. The mixed bonding activity is focused on ionic, covalent or
metallic examples on the corresponding S2 page; the all-activities view retains
the full comparison.

Browser checks (optional development dependencies and Edge on Windows):

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_chemistry_resources.py
```
