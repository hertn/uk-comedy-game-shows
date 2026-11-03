#!/usr/bin/env python3
"""Regenerate manifest + catalog files from shows.json using Cinemeta."""
import json, os, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENRES = ["Panel", "Quiz & Game Shows", "Challenge", "Chat & Entertainment", "Stand-up", "Specials", "Classic", "New"]
CAT_ID = "ukcomedy"
NAME = "UK Comedy & Game Shows"

def meta(i):
    u = f"https://v3-cinemeta.strem.io/meta/series/{i}.json"
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", u], capture_output=True, text=True).stdout
        try:
            return json.loads(r)["meta"]
        except Exception:
            time.sleep(3)
    raise RuntimeError("no metadata for " + i)

def main():
    shows = json.load(open(os.path.join(ROOT, "shows.json")))
    metas = []
    pending = []
    for s in json.load(open(os.path.join(ROOT, "new.json"))):
        m = meta(s["id"])
        e = {"id": s["id"], "type": "series", "name": m["name"], "releaseInfo": m.get("releaseInfo", ""),
             "poster": f"https://images.metahub.space/poster/medium/{s['id']}/img"}
        if m.get("imdbRating"):
            e["imdbRating"] = m["imdbRating"]
        pending.append(e)
    for s in shows:
        m = meta(s["id"])
        e = {"id": s["id"], "type": "series", "name": m["name"],
             "releaseInfo": m.get("releaseInfo", ""),
             "poster": f"https://images.metahub.space/poster/medium/{s['id']}/img"}
        if m.get("imdbRating"):
            e["imdbRating"] = m["imdbRating"]
        metas.append((e, s["genres"]))
    metas.sort(key=lambda x: -float(x[0].get("imdbRating", 0)))
    base = os.path.join(ROOT, "catalog", "series")
    os.makedirs(os.path.join(base, CAT_ID), exist_ok=True)
    def dump(path, items):
        with open(path, "w") as f:
            json.dump({"metas": items}, f)
    dump(os.path.join(base, CAT_ID + ".json"), [m for m, _ in metas])
    for g in GENRES:
        items = pending if g == "New" else [m for m, gs in metas if g in gs]
        dump(os.path.join(base, CAT_ID, f"genre={g}.json"), items)
    manifest = {
        "id": "io.github.ukcomedygameshows", "version": json.load(open(os.path.join(ROOT, "manifest.json")))["version"] if os.path.exists(os.path.join(ROOT, "manifest.json")) else "1.0.0",
        "name": NAME,
        "description": "Every UK comedy panel show, game show, quiz, chat show and stand-up showcase. No scripted shows, no reality.",
        "resources": ["catalog"], "types": ["series"], "idPrefixes": ["tt"],
        "catalogs": [{"type": "series", "id": CAT_ID, "name": NAME,
                      "extra": [{"name": "genre", "options": GENRES, "isRequired": False}],
                      "genres": GENRES, "extraSupported": ["genre"]}],
    }
    json.dump(manifest, open(os.path.join(ROOT, "manifest.json"), "w"), indent=1)
    print(len(metas), "shows")

if __name__ == "__main__":
    main()
