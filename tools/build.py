#!/usr/bin/env python3
"""Regenerate manifest + catalog files from shows.json using Cinemeta.

Shows whose metadata can't be fetched keep their previous catalog entry,
so a Cinemeta hiccup never drops a show from the list.
"""
import json, os, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENRES = ["Panel", "Quiz & Game Shows", "Challenge", "Chat & Entertainment", "Stand-up", "Specials", "Classic"]
CAT_ID = "ukcomedy"
NAME = "UK Comedy & Game Shows"
CATALOG = os.path.join(ROOT, "catalog", "series")

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
    entries.sort(key=lambda x: -float(x[0].get("imdbRating") or 0))
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
    print(len(entries), "shows")

if __name__ == "__main__":
    main()
