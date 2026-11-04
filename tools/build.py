#!/usr/bin/env python3
"""Regenerate manifest + catalog files from shows.json using Cinemeta.

Shows whose metadata can't be fetched keep their previous catalog entry,
so a Cinemeta hiccup never drops a show from the list.
"""
import json, os, re, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENRES = ["Panel", "Quiz & Game Shows", "Challenge", "Chat & Entertainment", "Stand-up", "Specials", "Classic"]
CAT_ID = "ukcomedy"
NAME = "UK Comedy & Game Shows"
CATALOG = os.path.join(ROOT, "catalog", "series")
BLURBS = {
    "Panel": "Comedians trading jokes about the news and each other.",
    "Quiz & Game Shows": "The Chase, Millionaire, QI, Only Connect and the rest.",
    "Challenge": "Taskmaster, Last One Laughing, Battle in the Box and other comedy games.",
    "Chat & Entertainment": "Chat shows and light entertainment fronted by comedians.",
    "Stand-up": "Stand-up showcases and live comedy.",
    "Specials": "One-off formats like the Big Fat Quiz.",
    "Classic": "The older shows, in one place.",
}

def update_readme(entries):
    """Keep the show counts in README.md in step with the catalog."""
    path = os.path.join(ROOT, "README.md")
    text = open(path).read()
    rows = ["| Genre | Shows | |", "| --- | ---: | --- |"]
    for g in GENRES:
        rows.append(f"| {g} | {sum(1 for _, gs in entries if g in gs)} | {BLURBS[g]} |")
    text = re.sub(r"<!-- total -->.*?<!-- /total -->", f"<!-- total -->{len(entries)}<!-- /total -->", text)
    text = re.sub(r"<!-- genres -->.*?<!-- /genres -->", lambda _: "<!-- genres -->\n" + "\n".join(rows) + "\n<!-- /genres -->", text, flags=re.S)
    open(path, "w").write(text)

def meta(i):
    u = f"https://v3-cinemeta.strem.io/meta/series/{i}.json"
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", u], capture_output=True, text=True).stdout
        try:
            return json.loads(r)["meta"]
        except Exception:
            time.sleep(3)
    return None

def previous():
    try:
        return {m["id"]: m for m in json.load(open(os.path.join(CATALOG, CAT_ID + ".json")))["metas"]}
    except Exception:
        return {}

def main():
    blocked = set(json.load(open(os.path.join(ROOT, "blocklist.json"))))
    shows = [s for s in json.load(open(os.path.join(ROOT, "shows.json"))) if s["id"] not in blocked]
    old = previous()
    entries = []
    for s in shows:
        m = meta(s["id"])
        if m:
            e = {"id": s["id"], "type": "series", "name": m["name"],
                 "releaseInfo": m.get("releaseInfo", ""),
                 "poster": f"https://images.metahub.space/poster/medium/{s['id']}/img"}
            if m.get("imdbRating"):
                e["imdbRating"] = m["imdbRating"]
        elif s["id"] in old:
            print("keeping previous entry for", s["id"])
            e = old[s["id"]]
        else:
            print("skipping (no metadata yet):", s["id"])
            continue
        entries.append((e, s["genres"]))
    # Newest first by start year, then highest rated.
    def order(x):
        y = re.search(r"\d{4}", x[0].get("releaseInfo") or "")
        return (-(int(y.group()) if y else 0), -float(x[0].get("imdbRating") or 0))
    entries.sort(key=order)
    os.makedirs(os.path.join(CATALOG, CAT_ID), exist_ok=True)
    def dump(path, items):
        with open(path, "w") as f:
            json.dump({"metas": items}, f)
    dump(os.path.join(CATALOG, CAT_ID + ".json"), [e for e, _ in entries])
    for g in GENRES:
        dump(os.path.join(CATALOG, CAT_ID, f"genre={g}.json"), [e for e, gs in entries if g in gs])
    mpath = os.path.join(ROOT, "manifest.json")
    version = json.load(open(mpath))["version"] if os.path.exists(mpath) else "1.0.0"
    manifest = {
        "id": "io.github.ukcomedygameshows", "version": version, "name": NAME,
        "description": "Every UK comedy panel show, game show, quiz, chat show and stand-up showcase. No scripted shows, no reality.",
        "resources": ["catalog"], "types": ["series"], "idPrefixes": ["tt"],
        "catalogs": [{"type": "series", "id": CAT_ID, "name": NAME,
                      "extra": [{"name": "genre", "options": GENRES, "isRequired": False}],
                      "genres": GENRES, "extraSupported": ["genre"]}],
    }
    json.dump(manifest, open(mpath, "w"), indent=1)
    update_readme(entries)
    print(len(entries), "shows")

if __name__ == "__main__":
    main()
