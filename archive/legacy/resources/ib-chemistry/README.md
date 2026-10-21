# Offline chemistry practice

Open `practice.html` for the syllabus hub. Each numbered sub-part has its own
page (`s1-1.html` through `r3-4.html`). `all-practice.html` is an optional view
of every activity. Keep this directory together when copying the resources;
pages share local CSS and JavaScript and need no server or internet connection.

`readiness.html` provides eight low-stakes checks with feedback for specific common
mistakes and recommendations linking to prerequisites, starters or harder tasks.
Students who view the explanation are directed to try related basic practice
independently. This is guidance, not a complete syllabus assessment.
`find-practice.html` searches all 22 sub-parts by code, topic and activity name,
with difficulty filters and AHL labels. Prior learning is linked separately.
Without JavaScript, all routes and worked explanations remain readable. Nothing
is saved or transmitted. Edit `readiness.json` for content and `study-support.js`
for behaviour; `tools/practice_support.py` generates both subjects' support pages.

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

Each of the 34 prior-learning and section starter lessons has six closely
matched follow-up questions (204 additional tasks). “Another like this” changes
the example while retaining the same method, with previous-question and repeat-set
controls. Hints, worked answers and accepted responses change with the question.
Switching clears the answer and feedback; lesson reset returns to question one.
All six questions and solutions can also be read without JavaScript.
Edit `repetition.json`; `tools/practice_repetition.py` renders the sets and
`similar-practice.js` handles them. These are finite authored sets, not unlimited
random generation. Numerical and short-word checks follow the starter conventions.

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

Syllabus references appear above activities on topic, basic and challenge pages. `syllabus-reference.json` stores brief paraphrases, level labels and verified guide page links; `tools/practice_syllabus.py` renders them. PDF page numbers are one-based, while printed page numbers follow the guide. Section links use school-hosted copies of the IB guides; the IB download is also linked. These summaries do not replace the full official syllabus.

`syllabus-cross-references.json` records the guide's explicit numbered section and skills links, their source PDF pages, and their destinations. Links are directional: a reference from A to B does not imply B refers to A. Repeated references are combined; explicit AHL qualifiers remain visible. Local sections link to practice, while skills and out-of-course sections link to the guide. Cross-references are expanded on single-section pages and can be opened per section on grouped pages.

The booklet companion is generated from `booklet.json` by `tools/practice_booklets.py`. It links to the verified version 1.1 booklet, gives selected formulas and original study reminders, and supplies contextual help for mapped syllabus and prior-learning sections. Booklet PDF links require internet; all local notes and practice links work offline. Table values are not bulk-reproduced, and question-specific values continue to take precedence.

`booklet-practice.html` adds three-question lookup sets from `booklet-practice.json`: choose a reference, select units and calculate. Guidance fades from a worked setup to a cue to an independent attempt; full support remains optional. Authored distractor and numerical feedback address specific method, unit and sign mistakes without claiming to diagnose every error. The shared source is `tools/booklet-practice.js`, copied by the builder. No progress is stored or transmitted.
