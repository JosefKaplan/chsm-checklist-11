# Chaos Space Marines Turn Checklist

A personal, single-page web app for playing **Chaos Space Marines (Heretic Astartes) in Warhammer 40,000 11th edition**. At the table it tells you, for the current turn (yours or your opponent's) and phase, what you are able to do: phase steps, Dark Pacts, army and detachment rules, enhancements, unit abilities, and every stratagem you can use right now, with a CP tracker.

Personal use only. Rules belong to Games Workshop; data comes from Wahapedia.

It is the same idea as the Necron checklist (`../necron-11th-test-checklist`): same one-file app, same three tabs, same data model. What is specific to this faction is listed under "What is different from the Necron app" below.

## Files

| Path                            | What it is                                                                                                                                                                                  |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `index.html`                    | The whole app: HTML, CSS and JS in one file. No build step, no dependencies.                                                                                                                |
| `tests/test_app.py`             | Playwright smoke test with assertions (game flow, CP, Dark Pacts timing, Detachment Points, enhancement limit, battle-size values, augmentations, overview, saves, layout, data integrity). |
| `tools/check_wahapedia.py`      | Compares Wahapedia's current data with `tools/wahapedia-snapshot.json` and lists what changed. Needs network, so it is not part of the tests.                                               |
| `tools/wahapedia-snapshot.json` | SHA-1 fingerprints (no rules text) of every Chaos Space Marines item as checked on 18 November 2026.                                                                                        |
| `README.md`                     | Short deploy guide and the sources list. Keep it short and direct, and keep its Sources in sync with the one below.                                                                         |
| `.nojekyll`                     | Empty. Tells GitHub Pages to serve files as they are, without Jekyll.                                                                                                                       |
| `.gitignore`                    | Ignores `.DS_Store`, `__pycache__/` and `.idea/`.                                                                                                                                           |
| `CLAUDE.md`                     | This file.                                                                                                                                                                                  |

Open `index.html` in a browser to use it. The game is saved in that browser's `localStorage` only (key `csm-turn-checklist-v1`), so each device and each address has its own save.

**Deployment:** not deployed yet. `origin` is `https://github.com/JosefKaplan/chsm-checklist-11.git`, so the site will be `https://josefkaplan.github.io/chsm-checklist-11/`. Pages serves branch `main`, folder `/ (root)`, with no workflow and no build; `README.md` has the steps. The site is public to anyone with the link; `<meta name="robots" content="noindex, nofollow">` in `index.html` keeps it out of search engines, so leave that tag in.
- It lives under a subpath, so the page must not reference files by relative or root-absolute paths (everything is inline, and the test checks it).
- `localStorage` is shared by every site on `josefkaplan.github.io` (per origin, not per path). The key `csm-turn-checklist-v1` differs from the Necron app's `necron-turn-checklist-v1`; keep keys unique per app.
- Google Fonts is the only outside request the page makes (blocked in tests).

## Hard rules for changes

1. **Keep it one self-contained static file.** GitHub Pages serves it as is, and a claude.ai artifact copy would block `fetch` and remote images (only inline code and Google Fonts load). No frameworks, no CDN scripts, no build tooling, no paths that assume the site lives at the domain root.
2. **Never paste rules text verbatim** from Wahapedia, Games Workshop or anywhere else. Every `when` / `target` / `effect` / `text` is a short summary in our own words. Keep numbers exact (CP, inches, dice, rolls). This is also why the snapshot in `tools/` stores hashes, not text.
3. **Keep IDs stable.** Stratagem, enhancement, unit, ability, augmentation and detachment `id`s are stored in saved games (`state.dets`, `state.enh`, `state.units`, `state.aug`, `state.used`, `state.battle`…). Renaming one silently breaks saves. Add new IDs instead. IDs must be unique across stratagems, reminders, enhancements and unit abilities (the test checks it).
4. **Saved-state changes need a migration.** State is `v: 1`. Add new fields with defaults in `freshGame()` and backfill them in `migrate()`. `tests/test_app.py` checks that a save without the newest fields migrates.
5. **Be honest about uncertainty.** If a rule's exact timing or effect is not confirmed, set `verify: true`; the UI shows a "Check wording" tag. Remove the flag only after checking the full text.
6. Storage access stays wrapped in try/catch (`store.get/set`); the app must work without storage.
7. Run `python3 tests/test_app.py` after every change.

## How the code is organised (`<script>` in `index.html`)

Sections appear in this order. Find things by name, not line number.

- **Data**
  - `PHASES` (command, movement, shooting, charge, fight, end) and `WIN` (timing windows: `start`, `during`, `react`, `end`). `PACT` is the slot list for "when a unit is selected to shoot or fight" (Dark Pacts).
  - `CORE`: the 10 core stratagems. `Explosives` and `Smokescreen` carry `needs` (a keyword note) but are **not** hidden: 35 Chaos Space Marines datasheets have GRENADES and 6 have SMOKE.
  - `ARMY_RULES`: Dark Pacts (shooting, fight) and Dark Pacts for Fire Overwatch. Each has `pact: true`, so they disappear while a selected detachment removes Dark Pacts.
  - `STEPS`: core turn steps, written from core rules 07–12 and 20.
  - `SIZES`: battle sizes with DP budget, enhancement limit and the `{dec}` / `{wps}` / `{cult}` values. `AUGMENTATIONS`: the Creations of Bile D6 table.
  - `DETACHMENTS`: 17 detachments built with `D(id, name, rule, ruleReminders, enh, strats)`. `DET_META`: Detachment Points, Unique tag, Force Dispositions, Wahapedia `anchor`, and the flags `noDarkPacts` / `needsDarkPacts`, merged into `DETACHMENTS`.
  - `UNITS`: datasheets with timed abilities, built with `U(id, name, abilities, short)`, sorted by name.
- **State**: `freshGame()`, `migrate()`, `store`, `undoStack` (in memory).
- **Helpers**: `slotMatches` / `matches` (is an item active in this turn and phase?), `selDets`, `selUnits`, `dpUsed`, `currentSize`, `dyn` (fills `{dec}`, `{wps}`, `{cult}`), `darkPactsLost`, `isLoneIncursionDetachment`, `armyProblems` (rule breaks: Unique, DP, enhancement limit), `armyNotes` (explained interactions), `blockReason` (can this detachment still be added), `stratPool`, `stratStatus` (once per phase / turn / round / battle), `timedReminders`, `fmt` (escapes text, styles CAPS keywords and `[ABILITIES]`).
- **Mutations**: always go through `mutate(fn)`, which snapshots for undo, saves and re-renders. `nextPhase`, `useStrat`, `toggleReminder`, `addLog`.
- **Rendering**: `render()` rebuilds `#tracker`, `#main`, `#tabbar` and `#sheet-root` from state.
  - Views: `renderGame`, `renderStrats` (which calls `renderOverview` or `renderStratCards`), `renderArmy`.
  - Pieces: `stratCard`, `renderSheet`, `renderTracker`.
- **Events**: one delegated `click` handler switches on `data-act`, plus delegated `change`, `submit` and `keydown` (Escape closes the sheet).

## Data model

Every timed item has `slots` and a window `w`.

- A **slot** is the string `"turn:phase"`.
  - turn is `mine`, `opp` or `any`.
  - phase is `command`, `movement`, `shooting`, `charge`, `fight`, `end` or `any`.
  - `any:any` means any phase of either turn. It is never shown in the End-of-turn step.
- **Reading 11th-edition WHEN lines:**
  - "Your opponent's Shooting phase or the Fight phase" becomes `["opp:shooting", "any:fight"]`.
  - "Your Shooting phase or the Fight phase" becomes `["mine:shooting", "any:fight"]`; "your Shooting phase or your Fight phase" is `["mine:shooting", "mine:fight"]`.
  - "Fight phase." or "Command phase." without "your" means either player's phase, so `any:fight` / `any:command`.
  - Fire Overwatch happens at the end of the opponent's Movement phase (`opp:movement`, window `end`).
- Window `w`: `start` (start of phase), `during`, `react` (just after something happens), `end`. Lists are sorted by window, then detachment before core, then CP.
- **Stratagem** `S(id, name, cp, type, slots, w, when, target, effect, extra)`.
  - `type` is one of: Battle Tactic, Strategic Ploy, Epic Deed, Wargear, Detachment (the stratagems Wahapedia lists without a type: Nightmare Hunt and the three 1 DP detachments), Core.
  - `extra` can set `restr`, `limit` (`battle` / `turn` / `round`), `verify`, `needs` (keyword note).
- **Reminder** `R(id, name, slots, w, text, extra)`, used for army rules, detachment rule reminders, steps and unit abilities. `extra` can set `limit`, `pact` (hidden when Dark Pacts are lost) and `needsUnit` (only shown while that unit is ticked on the Army tab; used for "Huron in sight").
- **Enhancement** `E(id, name, who, text, extra)`. Give it `slots` and `w` only if it does something at a specific time; otherwise it is passive and shows under "Always on".
- **Detachment**: `rule` `{name, text}`, `ruleReminders` (timed parts of the rule), `enh`, `strats`, plus the `DET_META` fields.
- **Unit** `U(id, name, abilities, short)`: one tick on the Army tab enables all its abilities. An ability with `slots: null` is passive. Ability ids must start with the unit id. `short` is the heading used in the checklist when the name is long (a heading is not doubled when the ability has the same name).
- Text can contain `{dec}`, `{wps}`, `{cult}`; `dyn()` replaces them with the current battle size's values.

### Common tasks

- **Fix or verify a rule:** edit its summary and slots in `CORE` / `DETACHMENTS` / `UNITS`, and drop `verify: true` once confirmed.
- **Add a unit ability:** add an `R("<unit id>-…", …)` to that unit's `abilities`, or add a `U(...)`. It appears under Army > Units.
- **Add a detachment:** add a `D(...)` entry and its `DET_META` line (DP, Unique tag, Force Dispositions, Wahapedia anchor, flags). Use a new short id with prefixed child ids (for example `xx-name`). It shows up everywhere automatically.
- **Another faction (Chaos Daemons, Death Guard…):** the model is faction-agnostic, but `ARMY_RULES`, `UNITS`, the `WAHA` link and texts are faction-specific. Prefer a copy of the app per faction over a faction switcher, unless asked.
- **Colours:** design tokens are in the `:root` block at the top of `<style>`, redefined for dark mode in two places (media query and `[data-theme="dark"]`). Keep all three blocks in sync. Gold (`--mine`) marks your turn, crimson (`--opp`) the opponent's turn and errors, blue (`--cp`) is CP. `--s1` to `--s4` colour the chosen detachments, in `DETACHMENTS` order (see `srcClass`).

## What is different from the Necron app

- **Dark Pacts** (the army rule) happen each time a unit is selected to shoot or fight, so they are reminders in your Shooting phase, in the Fight phase of either turn, and in the opponent's Movement phase for Fire Overwatch (Wahapedia FAQ: a unit targeted by Fire Overwatch is selected to shoot). Many detachment and unit effects hang off Dark Pacts and use the `PACT` slots.
- **Renegade Warband** removes Dark Pacts from your HERETIC ASTARTES models and forbids Cults of the Dark Gods. The app hides the Dark Pact reminders and says which selected detachments depend on Dark Pacts (`needsDarkPacts`).
- **Chaos Cult's Desperate Pact** is a Movement (Normal or Advance move) and Charge reminder.
- **Battle-size values:** Deceptors' Infiltrators picks (2 / 3 / 4), Warpstrike Champions' Warp Portals (1 / 2 / 3) and the Cults of the Dark Gods allowance (250 / 500 / 750 pts) follow the battle size.
- **Creations of Bile** keeps its augmentations in `state.aug` (up to two, picked on the Army tab; the D6 numbers are shown for rolling).
- **Huron's Marauders** needs a pick in your Command phase; the "Huron in sight" reminder only appears when Huron Blackheart is ticked.
- **Explosives and Smokescreen** are shown (see `CORE` above).
- The turn steps were rewritten from the core rules (Start of turn step, Gain Core CP, Battle-shock step, Move Units step with Reinforcements, Shoot step, Charge step, Pile in / Fight / Consolidate, End of Turn step).

## 11th-edition rules the app enforces

- Both players gain 1CP in each Command phase. The app adds yours when you tap **Next** into a Command phase (setting: Army > Game).
- Each stratagem once per phase. A unit can be targeted by only one stratagem per phase, shown as a reminder only (units aren't tracked). Battle-shocked units can't be targeted.
- **Detachment Points** (core rules 25.03 and 25.04):
  - Budget: Incursion 2 DP, Strike Force 3 DP. Onslaught is in the faction rules but not in the core rules table, so its DP stays user-set.
  - No detachment twice. No two detachments sharing a Unique tag: NIGHTMARE is on Nightmare Hunt and Murdertalon Raiders.
  - In an Incursion battle a 3 DP detachment is allowed as the **only** detachment (budget 2, so it would otherwise be over).
  - All chosen detachments' rules, enhancements and stratagems apply together.
- **Enhancement limit:** Incursion 2, Strike Force 4 (a warning, not a block; Onslaught has none published). One enhancement per unit and one of each is up to you.
- Reminders support limits `battle`, `turn` and `round` (e.g. Lord of Chaos is once per battle round).

## Verification status

On 18 November 2026 (Wahapedia rules data export last updated 12 November 2026; Chaos Space Marines App rules v1.2):
- Everything was written from Wahapedia's live pages and then **checked by script** against Wahapedia's HTML page and its CSV export:
  - Names, CP costs, Detachment Points, Force Dispositions and Unique tags of all 17 detachments, 93 stratagems and 62 enhancements match.
  - The turn and phase columns match the app's `slots` for every stratagem except one (below).
  - Every number, distance, dice roll, `[ABILITY]` and keyword in each summary was compared with the source text. The remaining differences are wording only (shortened "That HERETIC ASTARTES unit" to "That unit", "7 or more" for "7+", plural vs singular).
  - The HTML page and the CSV export agree word for word on all 93 stratagems and 62 enhancements.
- The 10 core stratagems, the core turn steps, battle sizes and the muster rules were checked against the core rules page.
- The 41 unit entries were compared with the datasheet abilities in the CSV export.

**Flagged `verify: true`:** *Armour of Corruption* (Warpstrike Champions). Its text says "Fight phase" (either player's), but Wahapedia's turn column and icon say the opponent's turn only. The app lists it in both Fight phases.

**Details worth knowing:**
- Heroic Intervention's "Into the Fray" mode costs +1CP. The Use button takes the base 1CP, so add the extra yourself.
- Wahapedia's text already has the errata applied (for example Millennia of Experience says 8", Bringers of Despair costs 1CP).
- Force Dispositions follow Wahapedia (v1.2). The Warhammer Community article of 10 June 2026 lists a different one for six detachments (for example Murdertalon Raiders: Purge the Foe there, Reconnaissance on Wahapedia); the DP costs agree everywhere.
- Legends datasheets (31 of them, source "Chaos Space Marines (Warhammer Legends)") are not included. Khorne Berzerkers and Noise Marines (Cults of the Dark Gods) are; Plague Marines' and Rubric Marines' abilities are not (the first has no effect under Cults of the Dark Gods per the FAQ, the second is passive).
- Some datasheet abilities are listed once per unit even if several datasheets share them (Chaos Icon, Lord of Chaos).

**How to re-verify after a rules update:**
1. `python3 tools/check_wahapedia.py` lists new, removed and changed items since the snapshot (it downloads Wahapedia's public CSV export, pipe-separated, and compares hashes). Unit abilities only matter if that unit is in `UNITS`.
2. Read each changed item on Wahapedia, update `index.html`, and run `python3 tests/test_app.py`.
3. `python3 tools/check_wahapedia.py --update` stores the new snapshot.
4. Where the export isn't enough: the faction page `https://wahapedia.ru/wh40k11ed/factions/chaos-space-marines` has the NIGHTMARE Unique tag (a tooltip before the detachment heading), the FAQ and errata; each stratagem is a `.str11Wrap` block. Core stratagems in the CSV are the rows whose id starts `0000108100` and type is `Core Stratagem` (older "Core –" rows are stale 10th-edition entries).

## Known gaps / next steps

- Not modelled:
  - Enhancement points, unit limits per battle size and Upgrades.
  - Boarding Actions detachments (Champions of Chaos, Infernal Reavers, Underdeck Uprising) and Crusade rules.
  - Per-unit tracking of the one-stratagem-per-unit rule, which unit has which Mark of Chaos, and which enemy unit is your focus of hatred / Vendetta target (use "Your own reminders").
  - Most passive unit abilities and all Legends datasheets.
- Onslaught: the DP budget and enhancement limit are not published in the core rules, so they stay user-set.
- Data snapshot: Wahapedia Chaos Space Marines 11th edition (rules v1.2), verified 18 November 2026. Rules and balance updates change often, so re-verify after a balance dataslate or Munitorum Field Manual update.

## Testing

```bash
pip install playwright && python3 -m playwright install chromium   # once
python3 tests/test_app.py                                          # tests ./index.html
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" python3 tests/test_app.py   # use installed Chrome
python3 tests/test_app.py http://localhost:8000/                   # a local server (python3 -m http.server 8000 --bind 127.0.0.1)
```

The test runs a fresh browser profile at phone size (390×844, then 360×740), blocks Google Fonts, and stops at the first failing check. Add a check to it for every new feature. It only talks to a local file or a server on `localhost` / `127.0.0.1` (it refuses any other URL), so it never touches the network.

To check how GitHub Pages will serve it, copy `index.html` and `.nojekyll` into a temporary folder under a subpath (`site/chsm-checklist-11/`), serve `site/` on 127.0.0.1 and run the test against `http://127.0.0.1:<port>/chsm-checklist-11/`.

## Sources

- Wahapedia, Chaos Space Marines (11th edition): https://wahapedia.ru/wh40k11ed/factions/chaos-space-marines (army rules, detachments, Detachment Points, enhancements, stratagems, FAQ and errata)
- Wahapedia, Core Rules (11th edition): https://wahapedia.ru/wh40k11ed/the-rules/core-rules/ (core stratagems, turn steps, battle sizes, muster rules)
- Wahapedia, Chaos Space Marines datasheets: https://wahapedia.ru/wh40k11ed/factions/chaos-space-marines/datasheets.html (unit abilities, Legends status)
- Wahapedia data export (CSV, no API, attribution recommended): https://wahapedia.ru/wh40k11ed/the-rules/data-export (files `Stratagems.csv`, `Enhancements.csv`, `Detachments.csv`, `Detachment_abilities.csv`, `Datasheets.csv`, `Datasheets_abilities.csv`, `Abilities.csv`, `Source.csv`, `Last_update.csv` at `https://wahapedia.ru/wh40k11ed/<name>.csv`)
- Warhammer Community, Chaos Faction Packs (cross-check of DP costs; older than Wahapedia's v1.2): https://www.warhammer-community.com/en-gb/articles/2wzoc1fz/new40k-download-new-chaos-faction-packs-today/
