# Element Quest

An isolated local design experiment. Open index.html. No existing Studentdash
pages, student records, assessment logic or distribution packages are modified.
No server, external assets or installation are required. Chemistry content and
district configuration live in profile.js; this is not a new core domain model.

## The experience

The player is a student researcher in a lab coat restoring a research campus.
Each syllabus section is a lab; each statement can later become a research station.
Movement is optional: the same destinations have ordinary keyboard-accessible
buttons. Keep discovery sessions short, with a clear next task and no time pressure.

Districts share one visual language but have different identities:

| District | Setting | Activities to develop |
|---|---|---|
| S1 | Green teaching laboratories | Particle models, isotope sorting, mole conversions |
| S2 | Copper and amber fabrication workshop | Bond construction, shapes, material testing |
| S3 | Violet botanical archive | Periodic patterns, organic families, identification |
| R1 | Orange geothermal energy station | Calorimetry, energy cycles, fuel comparisons |
| R2 | Blue waterworks and reactor hall | Rate controls, quantities, equilibrium |
| R3 | Rose electrochemical observatory | Proton/electron transfers and mechanisms |

Syllabus cross-references are conceptual connections, not a directed prerequisite
graph. Use them for visible footpaths, revisiting questions and joint quests.
Keep a separate, teacher-editable prerequisite graph. The initial checkpoint opens
S1.2 from S1.1. Ten equipment and investigation quests now branch across all six
districts; these proposed routes do not claim full syllabus coverage.

## Progression and economy

Unlock S1.2 after three different independent S1.1 answers plus the phase-model
activity. Wrong answers receive explanations; learners can retry, but assisted or
retried answers do not satisfy that checkpoint until a fresh independent attempt.
The prototype's independent retry is self-reported and reuses the question; a
production checkpoint must use unseen variants and delayed retrieval. A local game
save is editable and is not secure assessment evidence.

Use **research credits** as an explicitly fictional currency. Do not call money
electrons or imply that coins can turn one element into another. Award credits
once per question and once per lab quest. Avoid farming rewards for repeating an
already-solved question. No lives, lost streaks, paywalls or public rank tables.

The supply desk offers a 50–50 tool and a worked hint. A free explanation is always
available so students with the most difficulty never run out of help. Using any
help labels the attempt assisted. Later purchases should favour cosmetics, lab
decorations and optional explorations rather than advantages in assessed work.

## Elements and molecules

Unlock reusable **element cards**, not claims to have synthesized those elements.
The S1.1 quest grants hydrogen and oxygen cards; the S1.2 quest grants carbon.
The molecule bench offers water, carbon dioxide, methane and ammonia. Students
choose atom counts and bond orders in curated diagrams. These are formula/bond
models, not synthesis instructions or three-dimensional molecular geometry.
Nitrogen cards come from the periodic archive investigation.

Expand the bench into bonding puzzles with valence, lone pairs and geometry.
Do not accept arbitrary atom counts as evidence that a stable molecule exists.
Use curated molecule recipes and clear distinctions between molecules, ionic
formula units, metals and network structures. Carbon + oxygen could lead to a
later comparison of CO and CO2, requiring different structures and explanations.

## Implemented slice

- Top-down procedural pixel campus and lab-coat avatar; WASD/arrow movement,
  keyboard interaction, and direct buttons for players who do not want to walk.
- Nia's sand-and-water separation quest, with a one-time repair-part, balance,
  and credit reward. Jun spends the part to restore the water still; the campus
  art changes when the repair is complete.
- A simple interactive distillation model awards a one-time sample. Its text marks
  the activity as a diagram-level model, not instructions for real lab work.
- Two five-question banks, independent/assisted tracking, phase and formula models,
  a three-slot equipment bench, a configurable optional-equipment shop, element
  cards, and four non-exclusive research-skill milestones.
- Local save with migration from the earlier prototype save, visible storage errors,
  and validated JSON export/import. Repeated questions, equipment purchases, and
  waterworks runs cannot repeatedly grant their one-time rewards.
- Chemistry quest/shop/reward settings live in `profile.js`; no existing Studentdash
  question records or scores are imported or modified. Copied syllabus links remain
  reference information, not automatic unlock prerequisites.

## Next stages, before a full game

### Playable expansion: ten campus quests

The new quest journal offers two branches after the first restoration:

| Quest | Unlock | Interaction | Permanent reward |
|---|---|---|---|
| Jun: seed-library labels | Place the earned balance | Tare the display, subtract container mass, read a tared sample | Volumetric flask, 12 credits |
| Mira: isotope display | Open the atomic archive | Adjust proton/neutron/electron counters for three species | Access to Materials quests, 16 credits |
| Sol: materials display | Complete the isotope display | Build the smallest neutral ion ratios for three solids | Repaired magnetic stirrer, 18 credits |
| Nia: reference solution | Complete weighing, collect distilled-water sample, place flask | Convert final volume, calculate amount and mass | Preparation record, 18 credits |
| Sol: stirring comparison | Complete materials quest, place magnetic stirrer | Analyse fictional dissolving data with controlled variables | Investigation record, 12 credits |

| Mira: periodic archive | Complete isotope display | Order period-three elements and isoelectronic ions; count outer electrons | Thermometer, nitrogen card, 16 credits |
| Kaia: energy station | Complete weighing and periodic archive; place thermometer | Arrange procedure; control a calorimeter model; account for heat transfer | Calorimeter, 20 credits |
| Bo: reactor clock | Complete stirring comparison | Adjust concentration in a stated model; control variables; calculate rate | Stopwatch, 18 credits |
| Bo: titration desk | Complete solution and materials; place purchased pipette and burette | Order preparation; explore a strong-acid/strong-base pH model; calculate concentration | 22 credits |
| Jun: gas-piston display | Complete weighing and isotope display | Change volume and temperature at controlled conditions; convert temperature to kelvin | Gas syringe, 18 credits |

These contain thirty steps and no new MCQs. Atom and ion counters update a live
particle/charge display. They are counting/formula models, not a molecular dynamics
simulation. Solution preparation and stirring tasks are calculation/data activities;
they do not claim to assess real laboratory technique. Stirring changes the observed
dissolving time here; it is not presented as increasing equilibrium solubility.

Equipment is never consumed or permanently trapped in a slot. Only three items can
be placed at once; removing an item frees the slot and keeps all completed progress.
The journal explains each prerequisite and offers a route back to the teaching lab.
New gates and rewards are in `adventures.js` and `expansion.js`; the generic
runner is in `adventures-engine.js`. Science models state their simplifying
assumptions in each activity; simulated readings are fictional learning data.
Supported completion grants the same quest reward; a separate local field records
an entirely correct, unhinted run. Replays give practice without further rewards.
Existing saves acquire the new fields automatically. “Start a new expedition” opens
a confirmation panel; exporting a save first allows recovery. Unfinished activity
steps, number controls, card order and support flags survive leaving/reloading.
A research notebook collects explanations from completed quests and editable
2,000-character field notes. Notes are included in validated save exports.
The personal lab has a pixel-art interior reflecting repairs and the three placed
equipment items. The journal can show ready, all or completed investigations.

### Decisions for a later expansion

1. Try the slice with 3–5 students. Check whether they understand the next goal,
   can explain their answers and find the game motivating rather than distracting.
2. Connect the existing question catalog through an adapter; preserve question IDs
   and keep game rewards separate from formal assessment marks.
3. Build one authentic practical per district with meaningful choices and feedback:
   separation design, titration interpretation, calorimetry or equilibrium changes.
4. Add a teacher route editor, starting-point placement and manual unlocks. Students
   already taught later material must not have to grind through S1.1.
5. Add narrative quests spanning connected topics, for example identifying an unknown
   using structure, concentration and reaction evidence.
6. Only after the learning loop works, commission sprite sheets, animation, audio,
   accessibility alternatives and a mobile-friendly map. Do not expand art at the
   expense of reliable questions and clear feedback.

The best long-term reward is building a personal lab that demonstrates what the
student can explain. Unlocks should show progress without pretending to diagnose
mastery from a few repeated MCQs.

## Prototype verification

Run locally by opening `index.html` in a modern browser. Try a fresh save in this
order: speak to Nia; accept and solve the separation question; check the repair
part and balance; talk to Jun and restore the still; run the temperature activity;
place the balance; refresh the page and confirm the repaired still/equipment remain.
Replay Nia's question and the still activity to confirm they grant no second quest
or sample reward. Export a save, reset browser storage manually, and import it to
check the portable-save path. `node smoke-test.cjs` runs a dependency-free mock-DOM
interaction check for the quest/reward loop, repair-part cost, still activity,
equipment placement, S1.1 gate and reload persistence. The expansion check also
completes all ten quests, checks science-model values, verifies locked routes,
supported practice, one-time rewards, unfinished-control/order persistence,
four molecule models, notebook notes, valid imports, corrupt-save rejection and
cancel/confirm reset. Both canvas painters are executed by the mock harness.
`lab-preview.png` is a static rendering of the interior painter, not a browser
screenshot. It has been visually inspected. Full browser/layout verification of
this expanded version is still outstanding; mock-DOM tests do not establish
keyboard focus, responsive layout or real browser storage behavior.

The walking paths are illustrative. Dotted gold links aggregate the supplied
syllabus graph by district; they do not represent every individual edge. Full
map topology, building collision, touch walking, unseen checkpoint variants,
text-answer scaffolding, advanced molecule structures and live teacher controls
remain future work. This remains a local, single-player prototype and does not
sync progress across devices or connect to student results.
