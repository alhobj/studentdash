# Mathematics: Applications and Interpretation SL practice

Open `math-practice.html`. Keep this folder together: the hub, five topic pages,
CSS and JavaScript work offline, including through `file://` URLs.

This collection covers all 39 numbered SL sub-topics of the
first-assessment-2021 AI SL course, organised under its five topics. There are
44 hands-on explorers, 44 independently checked numerical challenges and
39 guided syllabus tasks with worked discussions. `coverage.html` maps each
sub-topic to activities; `investigations.html` adds open investigation prompts.
Coverage means each sub-topic has practice, not exhaustive exam preparation or
certified mastery. The mathematical exploration still requires the student's
own work. This collection does not claim alignment with the future 2029 course.

For students building confidence, `prior-learning.html` offers 12 lessons (24
short tasks) on arithmetic, fractions, percentages, ratio, algebra, units,
coordinates, geometry and calculator use. `basics-1.html` through `basics-5.html`
provide two short steps for each of the 39 syllabus sections (78 more tasks).
Each lesson has a reminder, optional hints, worked steps, untimed answer checking
and a reset button. Topic starters link onward to an explorer. These short tasks
introduce a section; they do not cover all its skills. Nothing is stored between
visits. Hints and worked steps remain available without JavaScript.

`challenges.html` links to harder tasks for all 39 SL sections, grouped into
`challenges-1.html` through `challenges-5.html`. Each challenge has a shared
scenario, two linked numerical parts, optional hints and worked solutions, and
a written explanation/evaluation prompt with a discussion for self-review.
The 78 numerical checks allow 0.1% tolerance; written arguments are not graded.
Notes and answers stay in the open page and are not saved. These are original
teaching problems, not a claim of official examination difficulty or completeness.

Edit `activities.json`, `extensions.json`, `coverage.json`, `math-practice.js`,
`math-extensions.js` and `math-practice.css`. Foundation lesson content lives in
`foundations.json`; its answer-checking UI is in `foundations.js`. Regenerate the
HTML with `python tools/build_math_practice.py` from the repository root.
Harder task content lives in `challenges.json`, with answer checking in
`challenges.js`. Both subject builders use `tools/practice_challenges.py` to
render the same accessible challenge layout; subject content stays in its profile.
All examples are fictional; financial models are teaching examples, with their
assumptions stated. The simulation uses fresh random trials, while displayed
binomial probabilities are exact. Normal probabilities use an approximation;
inverse-normal values use bisection of that approximation. The pooled two-sample
t-test uses numerical integration of the t density (df=18); chi-square examples
have df=2, giving the exact upper-tail expression exp(−χ²/2). These restricted
examples teach interpretation and do not replace a general statistical calculator.
Quartile conventions are stated where used. All financial models exclude fees
and taxes. Explorer numerical answer checks allow 0.5% tolerance and do not assess
precision. Foundation answers use exact short numbers (with 1e-8 tolerance for
floating-point representation); rounding tasks compare the rounded numerical value.
No student data is stored or submitted.

The scope was checked against the IB Mathematics: applications and interpretation
guide, first assessment 2021 (SL 1.1–1.8, 2.1–2.6, 3.1–3.6, 4.1–4.11, 5.1–5.8).
The source link is included in every page. Syllabus labels and teaching tasks
are original paraphrases; this is independent material, not an IB publication.

Run browser checks with:
`.venv\Scripts\python.exe -m unittest discover -s tests -p test_math_resources.py`
