# Mathematics: Applications and Interpretation SL practice

Open `math-practice.html`. Keep this folder together: the hub, five topic pages,
CSS and JavaScript work offline, including through `file://` URLs.

`readiness.html` offers eight low-stakes checks with feedback for specific common
mistakes and links to prerequisites, small steps or harder tasks. Viewing an
explanation before answering leads to a recommendation for independent basic
practice. These checks do not measure mastery of the whole syllabus.
`find-practice.html` searches all 39 sections by code, topic and activity name,
with filters for small steps, main practice and harder tasks. Prior learning is
linked separately. Without JavaScript, all practice routes and worked explanations
remain available. No responses, history or scores are saved.
Content is in `readiness.json`; `study-support.js` handles feedback and search.
Both profile builders call `tools/practice_support.py` to generate these pages.

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

Every one of the 51 prior-learning and section starter lessons also has six
closely matched follow-up questions: 306 additional tasks. “Another like this”
changes the example while keeping the method fixed; previous-question and repeat-set
controls allow unhurried repetition. Each question has its own hint, worked answer
and numeric check. Switching clears the answer and feedback. Lesson reset returns
to the first question. The complete six-question set is readable without JavaScript.
Edit `repetition.json`; `tools/practice_repetition.py` renders it and
`similar-practice.js` handles switching. These are finite authored sets, not unlimited
random generation. They use the same numerical tolerance as foundation tasks.

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

Syllabus references appear above activities on topic, basic and challenge pages. `syllabus-reference.json` stores brief paraphrases, level labels and verified guide page links; `tools/practice_syllabus.py` renders them. PDF page numbers are one-based, while printed page numbers follow the guide. Section links use school-hosted copies of the IB guides; the IB download is also linked. These summaries do not replace the full official syllabus.

`syllabus-cross-references.json` records the guide's explicit numbered section and skills links, their source PDF pages, and their destinations. Links are directional: a reference from A to B does not imply B refers to A. Repeated references are combined; explicit AHL qualifiers remain visible. Local sections link to practice, while skills and out-of-course sections link to the guide. Cross-references are expanded on single-section pages and can be opened per section on grouped pages.

The booklet companion is generated from `booklet.json` by `tools/practice_booklets.py`. It links to the verified version 1.1 booklet, gives selected formulas and original study reminders, and supplies contextual help for mapped syllabus and prior-learning sections. Booklet PDF links require internet; all local notes and practice links work offline. Table values are not bulk-reproduced, and question-specific values continue to take precedence.

`booklet-practice.html` adds three-question lookup sets from `booklet-practice.json`: choose a reference, select units and calculate. Guidance fades from a worked setup to a cue to an independent attempt; full support remains optional. Authored distractor and numerical feedback address specific method, unit and sign mistakes without claiming to diagnose every error. The shared source is `tools/booklet-practice.js`, copied by the builder. No progress is stored or transmitted.
