# Suggested next milestones

The immediate priority is usability with real IB Chemistry assessment data in the
local workflow. Automated tests and development fixtures continue to use fictional
learners. Follow the [architecture direction](docs/ARCHITECTURE.md): preserve current
behavior, add no new subject assumptions to the core, and migrate incrementally only
when needed for the current feature.

## Immediate priority: the first real assessment

- [x] Persistent class roster and assessment/question setup through teacher screens.
- [x] Optional existing classifications and a spreadsheet grid with rectangular Excel paste.
- [x] Save/reopen, authoritative question totals, overview and isolated dashboard exports.
- [ ] Teacher walkthrough with the first actual assessment using [the short guide](docs/FIRST_ASSESSMENT.md).
- [ ] Complete teacher review of selected questions, scored parts and curriculum mappings.
- [ ] Rehearse the score-matrix import and verify totals against the teacher's records.
- [ ] Review generated feedback and individual snapshots for the local pilot.
- [ ] Address blockers found in this workflow before broader product milestones below.

## Completed in this update

- [x] Correct exit-ticket marks and feedback with preserved before/after history.
- [x] Override automatic marks with an explicit teacher reason.
- [x] Create linked, single-learner retakes without overwriting original evidence.
- [x] Control accepted-answer release after submission, after marking, or while closed.
- [x] Add five distinctive designs, bringing the comparison gallery to ten options.

## 1. Choose and integrate the student experience

- [ ] Compare the ten designs with fellow teachers and fictional student scenarios.
- [ ] Choose one design and adapt the live exit-ticket pages to the same visual system.
- [ ] Add a focused student home showing the next action, latest feedback and practice.
- [ ] Verify keyboard, screen-reader, phone and print use; record results per browser.

Done when one consistent design works across the live app and offline snapshots.

## 2. Make follow-up easier to manage

- [ ] Show original and retake marks together in a teacher comparison view.
- [ ] Add class-wide retake selection with a reviewable recipient list.
- [ ] Separate closing submissions from unpublishing and make release timing explicit.
- [ ] Support correction of formal revision-attempt records with an audit history.
- [ ] Add attributed teacher identities before treating audit entries as accountability.

Done when a teacher can review a class's follow-up without opening every ticket.
Retake scores should continue to remain separate from original assessment evidence.

## 3. Protect and recover a course workspace

- [ ] Add a backup command that captures workbook and consistent SQLite state together.
- [ ] Add a restore rehearsal with integrity checks and a clear course identity.
- [ ] Add database versioning and upgrade tests using saved older fictional fixtures.
- [ ] Define archive/export and retention procedures for ticket answers and audit records.

Done when a fresh local installation can restore a fictional course and reproduce
its published feedback, submissions and histories.

## 4. Streamline test preparation and marking

- [ ] Review the test-to-Excel prompt/import workflow with teacher-made sample papers.
- [ ] Preview classifications, marks and duplicate IDs before merging an import.
- [ ] Support per-question topics on mixed-topic exit tickets.
- [ ] Decide whether multiple-select questions need a configurable partial-credit rule.
- [ ] Add a teacher marking queue for all pending written responses.

Done when a teacher can prepare and mark an assessment without hand-editing links
between records or losing sight of work awaiting review.

## 5. Prepare an approved classroom pilot

- [ ] Agree marking, storage, distribution and retention with the school.
- [ ] Rehearse individual snapshot delivery through an approved channel.
- [ ] Confirm calculations with hand-worked examples and representative devices.

Public/hosted implementation, portal sign-in and Microsoft integration are deferred;
do not begin this work until explicitly requested.

The local role switch remains a simulation. A networked student portal is a separate
engineering milestone, not a deployment switch for the current development server.
