# Mathtree

This is the Mathematics AI SL syllabus graph in Studentdash. Open `syllabus-graph.html`
through the local resource server or existing practice hub.

The Chemistree-style update includes:
- Five independently toggled topic colours, separate from grey prerequisite-distance fills.
- See x levels before / See y levels after sliders, initially 0 / 1. These follow the existing
  curriculum's authored prerequisites, never guide reference arrows. The right endpoint covers
  the full chain. Cyclic guide cross-references remain references.
- Topological placement, compact branch ordering, obstacle-aware routes and botton sort / top sort.
- Double-click or press M to toggle a dark-grey mark. The inspector also has a mark button.
  Marks, topic highlights and sliders are session-only; reload resets them.
- Optional circular prior-learning skills from the existing mathematics curriculum, rectangular
  syllabus cards, more map space and pointer-drag panning. Existing search, fit, zoom, guide links,
  keyboard selection and accessible list remain.
- Existing practice rings remain practice outcomes, not documented assessment mastery.

39 original sub-topic nodes and their stable IDs/guide links remain. Twelve existing prior-learning
nodes and their authored prerequisites are added as a separate optional display layer. No Chemistry
Tools/Inquiry categories, invented mathematics codes, HL course content or Studentdash private
assessment results are introduced. The current profile supplies SL only, so no misleading HL selector
is added.

`graph-options.json` opts this profile into the new generated assets. `tools/practice_graph.py`
reads authored links from the curriculum and copies the corresponding assets on rebuild. Other
profiles retain their current renderer. `mathtree-layout.js` is the transpiled, standalone Chemistree
layout/router (card dimensions 264 x 172); no React or npm runtime dependency is added.

Validation: `node --test tests/mathtree.test.cjs` from repository root; JavaScript syntax and
Python compilation checks. Tests cover both sorts, obstacle routing, stable IDs, topic buttons,
sliders, optional skills and marks through a minimal DOM harness. This is not full browser/visual QA;
local-preview browser access was blocked in the preceding Chemistree session. No site deployed.
