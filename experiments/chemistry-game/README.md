# Element Quest prototype

Open `index.html` directly in a modern browser. No installation or server is needed.
Everything in this folder is independent of the existing Studentdash pages and scores.

## First expedition

1. Talk to Nia and accept the sample-separation quest. Answer it to earn a repair part and balance.
2. Talk to Jun, restore the still, and complete its water-preparation activity.
3. Arrange equipment and place the balance. Open the quest journal to help label the seed library.
4. In the teaching lab, complete the water-state model and three independent S1.1 questions to open the atomic archive.
5. Use **Ready to start** in the journal to find your next investigation. **All quests** explains locked routes and equipment requirements.
6. Visit the molecule bench as element cards unlock. Enter your laboratory to see equipment you have collected and placed.
7. After an investigation, write a field note in the research notebook. Export your save before switching browsers or computers.

Walk with WASD or arrow keys; press E near a character or building. The destination
and character buttons provide the same access without walking. Hints are free in
investigations. Supported completion earns the same quest reward; unhinted runs are
recorded separately. Replays do not award credits twice.

Ten investigations contain thirty steps across six districts. They include particle
counters, ion ratios, ordering cards, numerical experiments, a calorimeter, titration
and gas-piston models. Four curated molecular puzzles cover atom counts and bonds.
This is an exploratory learning game, not a complete course or a secure assessment.

Progress and unfinished investigations save in this browser. Export/import moves a
save manually. Imported saves are validated before replacing progress. Reset asks
for confirmation. There is no account, online synchronization or teacher-results link.

## Development check

Run `node experiments/chemistry-game/smoke-test.cjs` from the repository root.
The dependency-free mock-DOM harness exercises the progression and save flows.
It is not a real-browser layout/accessibility test. See `CONCEPT.md` for scope,
design decisions and remaining work.
