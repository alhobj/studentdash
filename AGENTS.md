# ArborSynapse

- `server/`: supported saved-class/metadata workflow. `excel/`: Excel-only workflow.
- `tree/`: full, simple and local-result viewers. Keep all user-facing features.
- Keep curriculum, category and course configuration out of generic scoring code.
- Never commit learner data, workbooks, exports, caches or installed dependencies.
- Preserve stable IDs, result statuses and separate local confidence. Zero is graded;
  missing/absent/exempt/pending is not zero. Do not infer statement evidence from sections.
- Keep teacher defaults loopback-only. Atlas is for fictional testing data.
- Run `python scripts/check.py` and `npm test --prefix tree` after relevant changes.
- Keep guides short. Preserve curriculum provenance and authored teaching links.
