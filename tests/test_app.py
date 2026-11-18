#!/usr/bin/env python3
"""Smoke test for the Chaos Space Marines Turn Checklist (index.html).

Setup once:   pip install playwright && python3 -m playwright install chromium
Run:          python3 tests/test_app.py            (tests ../index.html)
              python3 tests/test_app.py path/to/index.html
              python3 tests/test_app.py http://localhost:8000/    (a local server, to test it the way GitHub Pages serves it)
Use a local Chrome instead of Playwright's Chromium:  CHROME_PATH=/path/to/chrome python3 tests/test_app.py

Exits non-zero on the first failed check and prints which one. Nothing leaves the machine: Google Fonts are blocked,
and only a server on localhost or 127.0.0.1 is accepted.
"""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
TARGET = sys.argv[1] if len(sys.argv) > 1 else str(HERE.parent / "index.html")
if TARGET.startswith(("http://", "https://")):
    if not re.match(r"http://(localhost|127\.0\.0\.1)(:\d+)?/", TARGET):
        sys.exit(f"Refusing {TARGET}: tests only talk to a server on localhost or 127.0.0.1.")
    URL = TARGET
else:
    URL = Path(TARGET).resolve().as_uri()
KEY = "csm-turn-checklist-v1"

passed = 0


def check(name, cond, detail=""):
    global passed
    if not cond:
        print(f"FAIL  {name}  {detail}")
        sys.exit(1)
    passed += 1
    print(f"ok    {name}")


def state(pg):
    return pg.evaluate("({round: state.round, turn: state.turn, phase: state.phase, cp: state.cp})")


def names(pg, sel=".strat h3"):
    return pg.eval_on_selector_all(sel, "els => els.map(e => e.textContent.trim())")


def sources(pg):
    """Headings of the checklist items in the Game tab (textContent, so CSS uppercase doesn't matter)."""
    return names(pg, ".check .src")


def go_to(pg, turn, phase, view="game"):
    pg.evaluate(f"state.turn = '{turn}'; state.phase = '{phase}'; state.view = '{view}'; render()")


def has(pg, text, sel=".check .src"):
    return any(text.lower() in t.lower() for t in names(pg, sel))


CELL = """([phase, col]) => {
  const sec = [...document.querySelectorAll('.ov-phase')].find(x => x.getAttribute('aria-label') === phase);
  const c = sec.querySelectorAll('.ov-cell')[col === 'mine' ? 0 : 1];
  return [...c.querySelectorAll('.ov-item .nm')].map(x => x.textContent);
}"""

DATA_CHECK = r"""() => {
  const T = ['mine', 'opp', 'any'], P = ['command', 'movement', 'shooting', 'charge', 'fight', 'end', 'any'];
  const unitAbilities = UNITS.flatMap(u => u.abilities);
  const all = [...CORE, ...DETACHMENTS.flatMap(d => [...d.strats, ...d.ruleReminders, ...d.enh]), ...STEPS, ...unitAbilities, ...ARMY_RULES];
  const seen = new Set(), problems = [];
  all.forEach(it => {
    if (seen.has(it.id)) problems.push('duplicate id ' + it.id);
    seen.add(it.id);
    (it.slots || []).forEach(s => { const [t, p] = s.split(':'); if (!T.includes(t) || !P.includes(p)) problems.push(it.id + ' bad slot ' + s); });
    if (it.slots && !WIN[it.w]) problems.push(it.id + ' bad window ' + it.w);
  });
  [...CORE, ...DETACHMENTS.flatMap(d => d.strats)].forEach(s => {
    if (!(s.cp >= 1 && s.cp <= 3)) problems.push(s.id + ' bad CP ' + s.cp);
    if (!s.when || !s.target || !s.effect) problems.push(s.id + ' missing when/target/effect');
    if (!s.slots || !s.slots.length) problems.push(s.id + ' has no slots');
  });
  DETACHMENTS.forEach(d => {
    if (!(d.dp >= 1 && d.dp <= 3)) problems.push(d.id + ' missing DP');
    if (!d.fd || !d.fd.length) problems.push(d.id + ' missing Force Disposition');
    if (!d.anchor) problems.push(d.id + ' missing Wahapedia anchor');
    if (d.strats.length !== (d.dp === 1 ? 3 : 6)) problems.push(d.id + ' stratagem count ' + d.strats.length);
    if (d.enh.length !== (d.dp === 1 ? 2 : 4)) problems.push(d.id + ' enhancement count ' + d.enh.length);
    d.ruleReminders.forEach(r => { if (r.needsUnit && !UNITS.some(u => u.id === r.needsUnit)) problems.push(r.id + ' needs unknown unit ' + r.needsUnit); });
  });
  UNITS.forEach(u => u.abilities.forEach(a => { if (!a.id.startsWith(u.id + '-')) problems.push(a.id + ' should start with ' + u.id); }));
  SIZES.forEach(z => { ['dec', 'wps', 'cult'].forEach(k => { if (!(z[k] > 0)) problems.push(z.id + ' missing ' + k); }); });
  return { count: all.length, problems, dets: DETACHMENTS.length, strats: DETACHMENTS.reduce((n, d) => n + d.strats.length, 0), enh: DETACHMENTS.reduce((n, d) => n + d.enh.length, 0) };
}"""


def main():
    errors = []
    with sync_playwright() as p:
        launch = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
        browser = p.chromium.launch(**launch)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        ctx.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and "ERR_FAILED" not in m.text and errors.append(m.text))
        pg.goto(URL)
        pg.wait_for_timeout(150)

        # --- data integrity -------------------------------------------------
        d = pg.evaluate(DATA_CHECK)
        check("data: ids unique, slots, windows, CP, counts valid", not d["problems"], d["problems"])
        check("data: 17 detachments, 93 detachment stratagems, 62 enhancements",
              (d["dets"], d["strats"], d["enh"]) == (17, 93, 62), (d["dets"], d["strats"], d["enh"]))
        check("page asks search engines not to index it (public GitHub Pages site)",
              "noindex" in (pg.get_attribute("meta[name=robots]", "content") or ""))
        icons = pg.evaluate("""() => Promise.all(['icon', 'apple-touch-icon'].map(rel => {
          const href = document.querySelector(`link[rel="${rel}"]`)?.href || '';
          return new Promise(done => {
            const img = new Image();
            img.onload = () => done({ rel, inline: href.startsWith('data:image/'), width: img.naturalWidth });
            img.onerror = () => done({ rel, inline: href.startsWith('data:image/'), width: 0 });
            img.src = href;
          });
        }))""")
        check("tab and home-screen icons are inline images that load",
              all(i["inline"] and i["width"] > 0 for i in icons), icons)
        outside = pg.evaluate("""() => [...document.querySelectorAll('[src], [href]')]
          .map(e => e.getAttribute('src') || e.getAttribute('href')).filter(u => !/^(data:|https:|#)/.test(u))""")
        check("no relative or root-absolute file references (works under /repo-name/ on GitHub Pages)", not outside, outside)

        # --- game flow, CP and limits ---------------------------------------
        check("starts in round 1, your Command phase, 1CP",
              state(pg) == {"round": 1, "turn": "mine", "phase": "command", "cp": 1}, state(pg))
        pg.click("[data-act=use][data-id=core-bravery]")
        check("using Insane Bravery costs 1CP", state(pg)["cp"] == 0)
        check("used stratagem is blocked for the phase",
              pg.inner_text(".strat:has(h3:text('Insane Bravery')) .use") == "Used this phase")
        for _ in range(6):
            pg.click("[data-act=next]")
        check("Next after End of turn goes to opponent's Command phase and adds 1CP",
              state(pg) == {"round": 1, "turn": "opp", "phase": "command", "cp": 1}, state(pg))
        pg.click("[data-act=next]"); pg.click("[data-act=next]")
        opp_shoot = names(pg)
        check("opponent's Shooting phase lists Veterans of the Long War's reaction and Smokescreen",
              "Contemptuous Disregard" in opp_shoot and "Smokescreen" in opp_shoot, opp_shoot)
        pg.click("[data-act=use][data-id=vet-disregard]")
        check("using a stratagem in the opponent's turn costs CP", state(pg)["cp"] == 0)
        pg.click("[data-act=undo]")
        check("undo refunds the CP", state(pg)["cp"] == 1)
        for _ in range(4):
            pg.click("[data-act=next]")
        check("round 2 starts in your Command phase with +1CP",
              state(pg) == {"round": 2, "turn": "mine", "phase": "command", "cp": 2}, state(pg))
        check("once-per-battle stratagem stays blocked next round",
              pg.inner_text(".strat:has(h3:text('Insane Bravery')) .use") == "Used this battle")

        # --- Dark Pacts: when they are offered -----------------------------------
        go_to(pg, "mine", "shooting")
        check("Dark Pacts are offered in your Shooting phase", has(pg, "Dark Pacts"), sources(pg))
        check("Explosives is offered in your Shooting phase (35 datasheets have GRENADES)", "Explosives" in names(pg))
        go_to(pg, "opp", "fight")
        check("Dark Pacts are offered in the Fight phase of either turn", has(pg, "Dark Pacts"), sources(pg))
        go_to(pg, "opp", "movement")
        check("Dark Pacts (Fire Overwatch) are offered in the opponent's Movement phase", has(pg, "Fire Overwatch"), sources(pg))
        go_to(pg, "opp", "shooting")
        check("Dark Pacts are not offered in the opponent's Shooting phase", not has(pg, "Dark Pacts"), sources(pg))

        # --- Renegade Warband removes Dark Pacts ------------------------------------
        pg.evaluate("state.dets = ['warband']; state.units = []; save()")
        go_to(pg, "mine", "shooting")
        check("Renegade Warband removes the Dark Pact reminders", not has(pg, "Dark Pacts"), sources(pg))
        go_to(pg, "mine", "command", "army")
        check("Renegade Warband blocks Cults of the Dark Gods",
              "can't use Cults of the Dark Gods" in pg.inner_text(".rules-note"))
        pg.evaluate("state.dets = ['warband', 'zealots']; save(); render()")
        check("a detachment that depends on Dark Pacts is called out next to Renegade Warband",
              "Pactbound Zealots" in pg.inner_text("#h-det ~ .rules-note"))

        # --- detachments and Detachment Points ------------------------------
        pg.evaluate("state.dets = []; state.enh = []; state.settings.size = 'strike'; state.settings.dp = 3; save(); render()")
        pg.check("#det-nightmare")
        check("Nightmare Hunt added: 2/3 DP", pg.evaluate("[state.dets, dpUsed()]") == [["nightmare"], 2])
        check("Murdertalon Raiders can't join Nightmare Hunt (both Unique: NIGHTMARE)",
              pg.is_disabled("#det-murdertalon") and "NIGHTMARE" in pg.inner_text("label[for=det-murdertalon] .why"))
        pg.uncheck("#det-nightmare"); pg.check("#det-veterans"); pg.check("#det-murdertalon")
        check("Veterans of the Long War + Murdertalon Raiders = 3/3 DP",
              pg.evaluate("[state.dets, dpUsed()]") == [["veterans", "murdertalon"], 3])
        check("a 1 DP detachment is now blocked with a reason",
              pg.is_disabled("#det-cabal") and "DP" in pg.inner_text("label[for=det-cabal] .why"))
        check("a Unique clash is blocked before the budget is checked",
              pg.is_disabled("#det-nightmare") and "NIGHTMARE" in pg.inner_text("label[for=det-nightmare] .why"))

        pg.click("[data-act=size][data-size=incursion]")
        check("Incursion sets 2 DP and warns when over budget",
              pg.evaluate("state.settings.dp") == 2 and pg.query_selector("#h-det ~ .overline") is not None)
        pg.uncheck("#det-murdertalon"); pg.uncheck("#det-veterans")
        check("in Incursion a 3 DP detachment is allowed as the only detachment",
              not pg.is_disabled("#det-zealots") and not pg.is_disabled("#det-huron"))
        pg.check("#det-zealots")
        check("a lone 3 DP detachment in Incursion is not over budget",
              pg.evaluate("armyProblems().filter(p => p.kind === 'dp').length") == 0 and pg.query_selector("#h-det ~ .overline") is None)
        check("nothing else can join a 3 DP detachment in Incursion",
              pg.is_disabled("#det-cabal") and "on its own" not in pg.inner_text("label[for=det-cabal] .why"))
        pg.uncheck("#det-zealots"); pg.check("#det-veterans")
        check("a 3 DP detachment can't join another one in Incursion",
              pg.is_disabled("#det-zealots") and "on its own" in pg.inner_text("label[for=det-zealots] .why"))
        pg.click("[data-act=size][data-size=strike]")
        check("Strike Force sets 3 DP", pg.evaluate("state.settings.dp") == 3)

        # --- enhancement limit per battle size -------------------------------------
        pg.evaluate("state.dets = ['veterans']; state.enh = []; state.settings.size = 'incursion'; state.settings.dp = 2; save(); render()")
        for enh in ("vet-eager", "vet-eye", "vet-legend"):
            pg.check(f"#enh-{enh}")
        check("a third enhancement in Incursion is flagged (limit 2)",
              "allows 2" in pg.inner_text("#h-enh ~ .overline"), pg.inner_text("#h-enh ~ .overline") if pg.query_selector("#h-enh ~ .overline") else "no warning")
        pg.click("[data-act=size][data-size=strike]")
        check("the same three enhancements are fine in Strike Force (limit 4)",
              pg.query_selector("#h-enh ~ .overline") is None and "3/4 picked" in pg.inner_text("#h-enh"))

        # --- battle-size values in rules text ------------------------------------------
        pg.evaluate("state.dets = ['warpstrike', 'deceptors']; state.enh = []; state.units = []; state.settings.size = 'strike'; state.settings.dp = 3; save()")
        go_to(pg, "opp", "end")
        check("Warp Portals shows 2 units at Strike Force", any("up to 2" in t for t in names(pg, ".check .txt")), names(pg, ".check .txt"))
        pg.evaluate("state.settings.size = 'incursion'; render()")
        check("Warp Portals shows 1 unit at Incursion", any("up to 1" in t for t in names(pg, ".check .txt")))
        pg.evaluate("state.settings.size = 'strike'; state.view = 'army'; render()")
        check("Deceptors shows 3 units of each at Strike Force", "up to 3" in pg.inner_text("label[for=det-deceptors] .sm"))
        check("the Cults of the Dark Gods allowance is 500 pts at Strike Force", "500 pts" in pg.inner_text(".rules-note"))
        pg.click("[data-act=size][data-size=incursion]")
        check("the Cults of the Dark Gods allowance is 250 pts at Incursion", "250 pts" in pg.inner_text(".rules-note"))
        pg.click("[data-act=size][data-size=strike]")

        # --- Creations of Bile augmentations --------------------------------------------
        pg.evaluate("state.dets = ['bile']; state.aug = []; state.view = 'army'; save(); render()")
        pg.check("#aug-2"); pg.check("#aug-5")
        pg.evaluate("document.getElementById('aug-1').click()")  # a real click would fail: the page un-ticks the box again
        check("only two augmentations can be picked at the start of the battle",
              pg.evaluate("state.aug") == ["aug-2", "aug-5"], pg.evaluate("state.aug"))
        go_to(pg, "mine", "movement")
        always = pg.inner_text(".always")
        check("picked augmentations are listed under Always on",
              "Hyperadrenal Infusion" in always and "Macrotensile Sinews" in always and "Cholinergic" not in always, always)
        pg.evaluate("state.view = 'army'; render()")
        pg.uncheck("#det-bile")
        check("removing Creations of Bile clears its augmentations", pg.evaluate("state.aug") == [])

        # --- reminders that depend on a ticked unit ------------------------------------
        pg.evaluate("state.dets = ['huron']; state.units = []; save()")
        go_to(pg, "mine", "command")
        check("Huron's pick-an-ability reminder shows in your Command phase", has(pg, "Tyrannical Motivation"), sources(pg))
        go_to(pg, "mine", "shooting")
        check("the 'Huron in sight' reminder stays hidden until Huron Blackheart is ticked",
              not has(pg, "Huron in sight"), sources(pg))
        pg.evaluate("state.units = ['u-huron']; render()")
        check("the 'Huron in sight' reminder appears once Huron Blackheart is ticked", has(pg, "Huron in sight"), sources(pg))

        # --- unit abilities ------------------------------------------------------------------
        pg.evaluate("state.units = ['u-warpsmith', 'u-lord-of-chaos']; state.dets = ['veterans']; save()")
        go_to(pg, "mine", "command")
        check("Warpsmith's Master of Mechanisms shows in your Command phase", has(pg, "Master of Mechanisms"), sources(pg))
        go_to(pg, "opp", "shooting")
        check("Lord of Chaos is offered in any phase, without a doubled heading",
              any(t.startswith("Unit · Lord of Chaos") and t.count("Lord of Chaos") == 1 for t in sources(pg)), sources(pg))

        # --- stratagems tab: overview and full cards ------------------------------------
        pg.evaluate("state.dets = ['veterans', 'warpstrike']; state.units = []; state.turn = 'mine'; state.phase = 'command'; save()")
        pg.click("[data-act=view][data-view=strats]")
        pg.click("[data-act=smode][data-mode=overview]")
        check("overview puts Millennia of Experience in the opponent's Movement phase",
              "Millennia of Experience" in pg.evaluate(CELL, ["Movement", "opp"]))
        check("overview puts Counteroffensive only in the opponent's Fight phase",
              "Counteroffensive" in pg.evaluate(CELL, ["Fight", "opp"]) and "Counteroffensive" not in pg.evaluate(CELL, ["Fight", "mine"]))
        check("Explosives and Smokescreen are in the overview (Chaos Space Marines have GRENADES and SMOKE units)",
              "Explosives" in pg.evaluate(CELL, ["Shooting", "mine"]) and "Smokescreen" in pg.evaluate(CELL, ["Shooting", "opp"]))
        pg.click(".ov-item[data-id=wps-armour]")
        check("tapping an entry opens its card", pg.inner_text(".sheet .strat h3") == "Armour of Corruption")
        check("the card of an unconfirmed timing carries the Check wording tag", "Check wording" in pg.inner_text(".sheet"))
        check("the card links to the detachment's section on Wahapedia",
              pg.get_attribute(".sheet .strat footer a", "href").endswith("#Warpstrike-Champions"))
        pg.keyboard.press("Escape")
        check("Escape closes the card", pg.query_selector(".sheet") is None)
        pg.click("[data-act=smode][data-mode=cards]")
        check("full cards list all 10 core stratagems",
              any(h.startswith("Core stratagems 10") for h in names(pg, "main h2")), names(pg, "main h2"))

        # --- layout ----------------------------------------------------------------
        pg.set_viewport_size({"width": 360, "height": 740})
        pg.evaluate("state.dets = ['veterans', 'huron']; state.units = UNITS.map(u => u.id); state.enh = ['vet-eager']; save()")
        for view in ("game", "strats", "army"):
            for phase in ("command", "shooting", "fight"):
                pg.evaluate(f"state.view = '{view}'; state.phase = '{phase}'; render()")
                wide = pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                check(f"no sideways scrolling at 360px ({view}, {phase})", not wide)

        # --- saved games ------------------------------------------------------------
        pg.evaluate("state.dets = ['talons', 'cabal']; state.aug = []; state.view = 'game'; save()")
        pg.reload(); pg.wait_for_timeout(100)
        check("game survives a reload", pg.evaluate("state.dets") == ["talons", "cabal"])
        pg.evaluate(f"""() => {{ const s = JSON.parse(JSON.stringify(state)); delete s.aug;
            s.settings = {{ first: 'mine', autoCP: true }}; localStorage.setItem('{KEY}', JSON.stringify(s)); }}""")
        pg.reload(); pg.wait_for_timeout(100)
        check("a save from before the augmentation and battle-size fields is migrated",
              pg.evaluate("[state.aug, state.settings.size, state.settings.dp]") == [[], "strike", 3])

        # --- consistency fixes ----------------------------------------------------------
        pg.evaluate("state.dets = ['nightmare', 'murdertalon']; state.enh = []; save()")
        pg.reload(); pg.wait_for_timeout(100)
        warn = pg.inner_text(".ctx") if pg.query_selector(".ctx .overline") else ""
        check("an illegal combination from an old save is flagged in the Game tab", "NIGHTMARE" in warn, warn)

        browser.close()

    check("no JavaScript errors", not errors, errors)
    print(f"\n{passed} checks passed")


if __name__ == "__main__":
    main()
