# ArborSynapse

- `server/`: supported saved-class/metadata workflow. `excel/`: Excel-only workflow.
- `tree/`: full, simple and local-result viewers. Keep all user-facing features.
- Keep curriculum, category and course configuration out of generic scoring code.
- Never commit learner data, workbooks, exports, caches or installed dependencies.
- Preserve stable IDs, result statuses and separate local confidence. Zero is graded;
  missing/absent/exempt/pending is not zero. Do not infer statement evidence from sections.
- Keep teacher defaults loopback-only. Atlas is for fictional testing data.
- For small changes, run only the relevant feature tests; use the default smoke checks
  (`python scripts/check.py`, `npm test --prefix tree`) for a quick integration check.
- Run full suites only before releases, after broad refactors, or when an unresolved
  failure warrants them: `python scripts/check.py --full`, `npm run test:full --prefix tree`.
- Do not routinely repeat full suites for small edits or documentation updates.
- Keep guides short. Preserve curriculum provenance and authored teaching links.
