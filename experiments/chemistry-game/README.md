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

Twenty-three investigations contain sixty-nine steps across six districts. They include particle
counters, ion ratios, ordering cards, numerical experiments, a calorimeter, titration
and gas-piston models. New routes explore electron arrangements (S1.3), covalent
bonding (S2.2), bond enthalpies (R1.2), limiting reactants and yields (R2.1), and
dynamic equilibrium (R2.3). The remaining routes cover metals (S2.3), materials (S2.4), organic families
(S3.2), fuels (R1.3), Gibbs energy (R1.4, labelled AHL), redox (R3.2), radicals
(R3.3), and electron-pair reactions (R3.4). All 22 sections now have an introductory
investigation. Each route samples its section; it does not cover every syllabus
statement. Use **Explore syllabus sections** to find ready, locked and completed
routes. See `COVERAGE.md` for the section-to-quest map. Four curated molecular puzzles cover atom counts and bonds.
This is an exploratory learning game, not a complete course or a secure assessment.

Progress and unfinished investigations save in this browser. Export/import moves a
save manually. Imported saves are validated before replacing progress. Reset asks
for confirmation. There is no account, online synchronization or teacher-results link.

## Development check

Run `node experiments/chemistry-game/smoke-test.cjs` from the repository root.
The dependency-free mock-DOM harness exercises the progression and save flows.
It is not a real-browser layout/accessibility test. See `CONCEPT.md` for scope,
design decisions and remaining work.


## Location screens and edge travel

Each district now occupies its own screen, with a distinct palette and scenery.
Click the map and use WASD or arrow keys. Cross an edge labelled with a destination
to enter that screen from the opposite side. Unlabelled edges stop the character.
You can keep holding a movement key through a transition. A short arrival fade
pauses movement briefly; reduced-motion settings disable that fade. Press E near the local
guide or central entrance to open that district's activities.

Travel buttons offer the same locations without walking; the existing destination
buttons travel and open the local activity menu. Visiting a screen does not bypass
quest prerequisites. Hold the on-screen arrow buttons to walk on touch devices, or activate them with
a keyboard for a small step. Pointer release/cancellation stops movement. The
Talk / enter button works like E. The current travel destination is highlighted
and available exits are listed in text. Paths lead only to connected edges.

Position is session-only; refreshing returns to the first
screen while keeping saved learning progress. Buildings, trees, shelving, machinery and water block walking. Northern paths
pass beside buildings. Small ground decorations and signs remain walkable; there
are no timed obstacles. A nearby-interaction prompt identifies a guide or doorway. Travel routes are authored geography,
not a claim about curriculum prerequisites.

`world-profile.js` contains local routes, palettes and guide positions.
`screen-world.js` is the same standalone controller in both game folders so each
folder remains portable. Run `node experiments/chemistry-game/world-test.cjs`
from the repository root to test both maps and keyboard/travel-button integration.
The tests use a mock DOM; they do not establish actual browser layout or focus
behaviour. `locations-preview.png` is a static painter contact sheet, not a browser
screenshot. Full browser verification remains outstanding.


### Route map and character feedback

**Open route map** displays the authored geography, highlights your current
location and marks places visited during this session. Select a location for
step-by-step walking directions or use its direct-travel button. This map shows
travel connections rather than learning prerequisites; quest gates remain intact.
Visited markers reset on reload and are not scores or mastery indicators.

The character faces the direction of travel and alternates steps while moving.
Walking into a wall stops the stepping pose. Reduced-motion mode keeps a static
walking pose and removes arrival fades. Routes and animation are covered by the
mock-DOM world tests, including route-map selection and direct travel. Actual
browser and touch-device verification is still outstanding.


### Village artwork

The original procedural art in `village-art.js` uses warm cottage roofs, plaster
and timber facades, stone foundations, flowerpots, shaded foliage, textured paths,
pond details, and outlined characters. Each district retains its own palette and
props. No game sprites or external image assets are used. The renderer copies in
both portable folders are identical. Art changes leave collision footprints,
travel links, saved progress and question content unchanged. Updated previews are
static renders of the canvas drawing commands, not browser screenshots.
