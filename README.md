# Chaos Space Marines Turn Checklist

Turn checklist for Chaos Space Marines (Heretic Astartes) in Warhammer 40,000 11th edition. Shows what you can do in each phase, including Dark Pacts, and tracks CP, detachments and stratagems. Built for phones. One file, no build.

**Live:** https://josefkaplan.github.io/chsm-checklist-11/ (once deployed, see below)

## Run it locally

Open `index.html` in a browser, or serve the folder the way GitHub Pages does:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://localhost:8000/. Stop it with Ctrl+C. Before every deploy, run `python3 tests/test_app.py` (see `CLAUDE.md`).

## Deploy to GitHub Pages

This folder is already a git repository on branch `main` with `origin` set to `https://github.com/JosefKaplan/chsm-checklist-11.git`.

1. On GitHub, make sure `chsm-checklist-11` exists as an empty **public** repository (no README, no licence, no .gitignore). A free account can only publish Pages from a public repository.
2. In this folder, run:

   ```bash
   git add .
   git commit -m "Chaos Space Marines Turn Checklist"
   git push -u origin main
   ```

3. In the repository, go to **Settings → Pages**. Under **Build and deployment**, set **Source** to **Deploy from a branch**, pick **main** and **/ (root)**, then click **Save**.
4. Wait a minute or two, then open https://josefkaplan.github.io/chsm-checklist-11/.

**To update:** commit and push. The site redeploys by itself.

## Good to know

- Anyone with the link can open the site. Search engines are asked not to list it.
- Your game is saved in your browser. Each device keeps its own.
- On your phone, use **Add to Home Screen** to open it like an app.
- The page loads two fonts from Google Fonts when it is online, so visitors' browsers contact Google. Offline it falls back to system fonts.
- Tests, the rules re-check tool and notes for changes are in `CLAUDE.md`.

## Sources

- [Wahapedia: Chaos Space Marines, 11th edition](https://wahapedia.ru/wh40k11ed/factions/chaos-space-marines). Army rules, detachments, Detachment Points, enhancements and stratagems (Chaos Space Marines rules v1.2).
- [Wahapedia: Core Rules, 11th edition](https://wahapedia.ru/wh40k11ed/the-rules/core-rules/). Core stratagems, turn steps, battle sizes and army building.
- [Wahapedia: Chaos Space Marines datasheets](https://wahapedia.ru/wh40k11ed/factions/chaos-space-marines/datasheets.html) and the [Wahapedia data export](https://wahapedia.ru/wh40k11ed/the-rules/data-export). Unit abilities, and the cross-check of everything above.
- [Warhammer Community: Chaos Faction Packs](https://www.warhammer-community.com/en-gb/articles/2wzoc1fz/new40k-download-new-chaos-faction-packs-today/). Detachment Point costs (cross-check).

All rules are short summaries, not copies, checked point by point against these pages on 18 November 2026. Rules change with balance updates; if something differs, the full text on Wahapedia is right.

Unofficial, for personal use, not affiliated with Games Workshop. Warhammer 40,000 and its rules belong to Games Workshop. Powered by Wahapedia.
