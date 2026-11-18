#!/usr/bin/env python3
"""Find out what changed on Wahapedia since the app's rules data was last checked.

Downloads Wahapedia's public rules data export (CSV, 11th edition), fingerprints every Chaos Space Marines item the app
models (detachments, detachment rules, enhancements, stratagems, core stratagems, army rules, unit abilities) and compares
the fingerprints with tools/wahapedia-snapshot.json. Only SHA-1 hashes are stored, never rules text.

    python3 tools/check_wahapedia.py            list new, removed and changed items (exit code 1 if there are any)
    python3 tools/check_wahapedia.py --update   after you have fixed index.html, store the current state as the new snapshot

Needs network access to wahapedia.ru, so it is NOT part of tests/test_app.py. Mention Wahapedia when publishing the data.
"""
import csv
import hashlib
import html
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://wahapedia.ru/wh40k11ed/"
SNAPSHOT = Path(__file__).resolve().parent / "wahapedia-snapshot.json"
FACTION = "CSM"
LEGENDS_SOURCE = "000000355"  # "Chaos Space Marines (Warhammer Legends)": not in the app
CORE_STRATAGEM_ID = re.compile(r"^0000108100")  # the 11th-edition core stratagems; older "Core –" rows are stale

csv.field_size_limit(sys.maxsize)


def download(name):
    request = urllib.request.Request(BASE + name + ".csv", headers={"User-Agent": "Mozilla/5.0 (compatible; rules-check)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter="|", quoting=csv.QUOTE_NONE))
    header = [h for h in rows[0] if h]
    return [{h: (r[i] if i < len(r) else "") for i, h in enumerate(header)} for r in rows[1:] if r]


def normalise(text):
    text = re.sub(r"<[^>]+>", " ", text.replace("<br>", " "))
    text = html.unescape(text).replace("’", "'")
    text = re.sub(r"[‐‑–—]", "-", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def fingerprint(*parts):
    return hashlib.sha1("|".join(normalise(p) for p in parts).encode()).hexdigest()[:12]


def current_state():
    items = {}
    detachments = {d["id"]: d for d in download("Detachments") if d["faction_id"] == FACTION and not d["type"]}
    names = {d["id"]: d["name"] for d in detachments.values()}
    for d in detachments.values():
        items[f"detachment: {d['name']}"] = fingerprint(d["dp"], d["force_disposition"])
    for r in download("Detachment_abilities"):
        if r["faction_id"] == FACTION and r["detachment_id"] in names:
            items[f"rule: {names[r['detachment_id']]} / {r['name']}"] = fingerprint(r["description"])
    for e in download("Enhancements"):
        if e["faction_id"] == FACTION and e["detachment_id"] in names:
            items[f"enhancement: {names[e['detachment_id']]} / {e['name']}"] = fingerprint(e["cost"], e["description"])
    for s in download("Stratagems"):
        if s["faction_id"] == FACTION and s["detachment_id"] in names:
            items[f"stratagem: {names[s['detachment_id']]} / {s['name']}"] = fingerprint(s["cp_cost"], s["turn"], s["phase"], s["description"])
        elif CORE_STRATAGEM_ID.match(s["id"]) and s["type"] == "Core Stratagem":
            items[f"core stratagem: {s['name']}"] = fingerprint(s["cp_cost"], s["turn"], s["phase"], s["description"])
    for a in download("Abilities"):
        if a["faction_id"] == FACTION and a["name"] in ("Dark Pacts", "Cult of the Dark Gods"):
            items[f"army rule: {a['name']}"] = fingerprint(a["description"])
    datasheets = {d["id"]: d for d in download("Datasheets") if d["faction_id"] == FACTION and d["source_id"] != LEGENDS_SOURCE}
    for row in download("Datasheets_abilities"):
        if row["datasheet_id"] in datasheets and row["type"] in ("Datasheet", "Wargear", "Primarch"):
            items[f"unit ability: {datasheets[row['datasheet_id']]['name']} / {row['name']}"] = fingerprint(row["description"])
    return {"checked": download("Last_update")[0]["last_update"], "items": items}


def main():
    now = current_state()
    if "--update" in sys.argv:
        SNAPSHOT.write_text(json.dumps({"wahapedia_last_update": now["checked"], "items": now["items"]}, indent=1, sort_keys=True) + "\n")
        print(f"Snapshot stored: {len(now['items'])} items, Wahapedia data last updated {now['checked']}.")
        return 0
    old = json.loads(SNAPSHOT.read_text())
    added = sorted(set(now["items"]) - set(old["items"]))
    removed = sorted(set(old["items"]) - set(now["items"]))
    changed = sorted(k for k in set(now["items"]) & set(old["items"]) if now["items"][k] != old["items"][k])
    print(f"Wahapedia data last updated: snapshot {old['wahapedia_last_update']}, now {now['checked']}.")
    for title, keys in (("NEW", added), ("REMOVED", removed), ("CHANGED", changed)):
        for key in keys:
            print(f"  {title:8} {key}")
    if not (added or removed or changed):
        print("No differences: the app still matches Wahapedia.")
        return 0
    print("\nRead these on Wahapedia, update index.html (and unit abilities only if the unit is in UNITS), then run with --update.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
