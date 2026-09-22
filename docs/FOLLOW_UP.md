# Exit-ticket corrections, retakes and answer release

Start the app with `.\.venv\Scripts\python teacher.py`, then open
`http://127.0.0.1:5000/exit-tickets`. Use fictional learners throughout.

## Correct a mark

Open **Results & review**, then **Review responses** for a learner. Every answer
has a marks and feedback form. An automatically marked answer also shows its
original automatic mark. Enter the intended mark, any student-visible feedback,
and a reason for a correction or automatic-mark override.

The first manual review can be saved without a reason. Later changes and automatic
overrides require one. The original student answer and automatic mark stay intact;
the teacher mark becomes the displayed score. Saving is protected against stale tabs.
Corrections immediately affect the live ticket result and original-ticket aggregate,
but never formal assessment marks. There is no bulk override or delete/reset control.

Open **Answer release, retakes & audit history** from the results or publication page
to inspect previous values, replacement values, timestamps and reasons. Audit reasons
are teacher-only; the separate feedback field is student-visible. Publication and
answer-release changes are also recorded. Existing activity predating this feature
is not reconstructed. Entries are attributed only to the local teacher simulation,
not to a verified person, and are not tamper-proof against someone editing SQLite.

## Assign practice without replacing evidence

In follow-up controls, select a learner who has submitted and give a reason. Select
**Create or open retake draft**, inspect the copied questions, then publish it.

The retake is a separate ticket assigned only to that learner, linked to the previous
ticket. Its questions and assignment are fixed, even before publication. It starts
with accepted answers hidden. Repeating the create action returns the same retake;
it does not create duplicates. Each ticket/learner pair can have one direct retake.
A submitted retake can itself receive a further retake.

Students see the practice ticket in their available list and later in completed
history, with a link to the previous attempt. Original submissions remain unchanged.
Retakes are excluded from topic aggregates so repeated familiar questions do not
inflate the original evidence. Retake ticket results still show their own marks.
Previously seen accepted answers may influence practice scores.

## Choose when accepted answers appear

The follow-up controls offer four policies. Every policy requires a saved submission
before any accepted answers are included in a student's result.

| Policy | When accepted answers appear |
|---|---|
| Keep hidden | Never |
| After submission | Immediately after that learner submits |
| After fully marked | When all answers in that learner's submission have marks |
| While unpublished (closed) | While the teacher has unpublished the ticket |

These settings control answer keys only. Own answers, marks and student-visible
feedback remain visible. There is no timed release scheduler. Under the closed
policy, republishing hides accepted answers in newly requested pages, but cannot
recall answers already viewed or copied. Policy changes require a reason, increment
the ticket version and reject stale forms. Already-open submission forms must be
reopened after a policy change.

Existing tickets keep the meaning of `allow_answer_review`: true means immediate,
false means hidden. A policy selected in follow-up controls overrides that import
flag, including on later edits. New retakes always start hidden.

## Quick rehearsal

1. Submit the six-question example as fictional learner 2001.
2. Mark the written answer, then correct it with a reason; inspect both audit entries.
3. Override one automatic mark and verify its original mark is still displayed.
4. Select **After fully marked**, then check the student's own result for accepted answers.
5. Select **While unpublished**, verify answers are hidden, then unpublish and recheck.
6. Create a retake for 2001, publish it and submit it as that learner.
7. Check both histories and confirm the retake does not add another topic contribution.
8. Switch to learner 2002 and confirm that 2001's retake and teacher audit are inaccessible.

## Storage and scope

The adapter adds `et_release`, `et_retakes` and `et_audit` tables to the existing
workspace. It does not rebuild or delete existing tables. Writes and their audit
entries share a transaction. Retake creation is serialized and unique per parent
ticket/learner. Preserve the workbook and workspace together in backups.

These features cover interactive exit tickets. Formal revision-attempt corrections
and formal feedback publication audit are separate future work. See [TODO](../TODO.md).
