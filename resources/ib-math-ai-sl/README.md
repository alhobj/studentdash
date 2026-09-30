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

Edit `activities.json`, `extensions.json`, `coverage.json`, `math-practice.js`,
`math-extensions.js` and `math-practice.css`. Regenerate the
HTML with `python tools/build_math_practice.py` from the repository root.
All examples are fictional; financial models are teaching examples, with their
assumptions stated. The simulation uses fresh random trials, while displayed
binomial probabilities are exact. Normal probabilities use an approximation;
inverse-normal values use bisection of that approximation. The pooled two-sample
t-test uses numerical integration of the t density (df=18); chi-square examples
have df=2, giving the exact upper-tail expression exp(−χ²/2). These restricted
examples teach interpretation and do not replace a general statistical calculator.
Quartile conventions are stated where used. All financial models exclude fees
and taxes. Numerical answer checks allow 0.5% tolerance and do not assess precision.
No student data is stored or submitted.

The scope was checked against the IB Mathematics: applications and interpretation
guide, first assessment 2021 (SL 1.1–1.8, 2.1–2.6, 3.1–3.6, 4.1–4.11, 5.1–5.8).
The source link is included in every page. Syllabus labels and teaching tasks
are original paraphrases; this is independent material, not an IB publication.

Run browser checks with:
`.venv\Scripts\python.exe -m unittest discover -s tests -p test_math_resources.py`
