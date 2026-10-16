# Pattern Quest — mathematics game experiment

Open **index.html** in a modern browser. No server, installation, account, external
assets or network connection is required for the game. Keep this folder together.
The optional links to existing mathematics practice need the rest of the repository.

This is the mathematics counterpart to `experiments/chemistry-game`: a procedural
pixel town, optional walking, characters to help, investigations, permanent idea
cards, a personal studio and portable browser saves. It is a first playable chapter,
not a complete copy of the chemistry game's much larger content collection.

## Start exploring

1. Meet **Nia** at the Number market and restore the price board, or start with
   **Mira** at the harbour or **Sol** in the gardens. All three routes are open.
2. Complete an investigation's three steps to earn credits, an idea card and,
   on selected quests, a studio tool. Every step has a free hint and worked answer.
3. Follow **Continue quest** or open the journal. **All quests** explains locked
   routes and links directly to the investigations that open them.
4. Place up to three collected items in the studio. Buy optional decorations at
   the supply desk. Equipment and currency never prevent access to hints or answers.
5. Experiment at the graph workbench and write a field note after a completed quest.
6. **Export save** before changing computers. **Import save** restores progress,
   unfinished answers, support flags, equipment and notes after confirmation.

Click the map, then use WASD/arrows to walk and E near a district to meet its guide.
The destination buttons offer the same access on phones and without walking.
Escape or the labelled close button exits dialogs. Number fields support Enter to
check an answer. Graphs have numerical descriptions alongside their canvas images.

## Current scope

Content follows the five topics of the repository's **Math AI SL first-assessment-
2021** practice profile. These are original fictional tasks, not imported student
records or examination questions. They sample selected ideas and do not cover all
39 sections, certify mastery or claim alignment with a newer curriculum.

| District / guide | Investigations | Ideas sampled |
|---|---|---|
| Number market / Nia | Night market; scale archive | Percentages, arithmetic sequences, compound growth, standard form, powers, percentage error |
| Function foundry / Jun | Town clock; gateway arch | Linear models, intersections, quadratic vertex and intercepts |
| Surveyor's harbour / Mira | Harbour route; shelter | Distance, midpoint, right-triangle trigonometry, triangle area, cylinder volume, perpendicular bisector |
| Data gardens / Sol | Garden records; probability fair | Mean/median, explicitly defined quartiles, regression prediction, independent events, binomial probability, normal symmetry |
| Change observatory / Kaia | Tracker; riverside park | Average and instantaneous rates, stationary points, optimization, integration, trapezoidal approximation |

Ten investigations contain thirty numerical steps. Four task models display live
graphs or diagrams (linear, quadratic, tangent and enclosure). The graph workbench
provides an additional freely adjustable linear model. Angles in the content are
in degrees; numerical tolerances and units are authored per field. Canvas graphs
have fixed, labelled viewing windows and are illustrative rather than a calculator.

Progression is an authored game route, not an official prerequisite hierarchy.
Each reward is paid once. Hints, worked answers or an incorrect attempt label the
current run as supported. Supported runs earn the same completion rewards. A fresh
replay can record an unhinted, correct run but repeats the same questions; it is not
evidence of independent mastery. No lives, time pressure, leaderboard or paid hints.

## Files and separation

- `profile.js`: subject content, five districts, authored prerequisites, rewards,
  equipment and answers. This is an experiment-specific profile, not a new core schema.
- `engine.js`: profile-driven progression, answer checking, one-time rewards and
  bounded/validated save import. It does not read assessment data.
- `game.js`: DOM interface, map, graph/diagram presentation and browser controls.
- `style.css`: responsive visual styling inspired by Element Quest.
- `smoke-test.html` / `smoke-test.js`: dependency-free state and real-browser checks.

The save key is `studentdash-pattern-quest-v1`, separate from Element Quest and the
practice journals. Exports identify their profile and schema version. Chemistry
saves are rejected. Validation happens before replacing the current session; it
checks IDs, prerequisites, rewards, equipment, notes and unfinished steps. Storage
errors remain visible and an in-memory session can still be exported. Saves remain
editable local game data, not secure assessment evidence. Browser storage may be
unavailable or behave differently for local files; use export for reliable backup.

No existing Chemistry files, course profiles, curricula, assessment records or
teacher interfaces are changed. No hosting, synchronization or score integration
is included. Static delivery and ordinary script tags support direct `file://` use.

## Verification

From the repository root, serve files locally if you want to run the browser suite:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/experiments/math-game/smoke-test.html` in a temporary
browser profile. The UI suite temporarily exercises the actual game save key and
backs up/restores its previous value; use a temporary profile to avoid affecting a
live play session if the test window is interrupted. No Node installation is needed.

The suite checks all 30 steps against separately worked answers, route locks,
draft recovery, support tracking, reward replay, slot limits, duplicate purchases,
notes, import/export, invalid-save preservation and storage failures. Its real-DOM
flow completes all ten quests, renders the model canvases, places studio tools,
changes a workbench slider, writes a note and reloads the game. Chromium headless
checks passed during development; desktop and narrow-screen screenshots were also
reviewed. This is not a full screen-reader or physical touch-device audit.

## Next expansion

Test this chapter with learners before expanding: ask whether they find the next
quest, understand the models and can explain the result. Then add richer interactive
tasks (data manipulation, probability simulation and geometric construction), unseen
question variants and more section coverage through authored content. A later map
could have collision and touch walking. Keep game progress separate from formal marks.
