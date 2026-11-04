#!/usr/bin/env python3
"""Regenerate manifest + catalog files from shows.json using Cinemeta.

Shows whose metadata can't be fetched keep their previous catalog entry,
so a Cinemeta hiccup never drops a show from the list.
"""
import json, os, re, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENRES = ["Panel", "Quiz & Game Shows", "Challenge", "Chat & Entertainment", "Stand-up", "Specials", "Classic", "Celebrity"]
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
    "Celebrity": "Celebrity reality competitions, from I'm a Celebrity to The Masked Singer.",
}

def update_readme(entries):
    """Keep the show counts in README.md in step with the catalog."""
    path = os.path.join(ROOT, "README.md")
    text = open(path).read()
    rows = ["| Genre | Shows | |", "| --- | ---: | --- |"]
    for g in [g for g in GENRES if any(g in gs for _, gs in entries)]:
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

LATEST_FILE = os.path.join(ROOT, "latest.json")

def latest_aired(m):
    """Date of the most recent episode that has already aired (YYYY-MM-DD), or None."""
    now = time.strftime("%Y-%m-%d", time.gmtime())
    dates = [v["released"][:10] for v in m.get("videos", []) if v.get("released") and v["released"][:10] <= now]
    return max(dates) if dates else None

def end_cap(release_info):
    """For a show that has ended ("2005-2022"), the last day of its end year. Otherwise None."""
    years = re.findall(r"\d{4}", release_info or "")
    if len(years) >= 2 or (years and not re.search(r"[\u2013-]\s*$", release_info or "") and re.search(r"[\u2013-]", release_info or "")):
        return f"{years[-1]}-12-31"
    return None

def fallback_date(release_info):
    """No episode dates: use the end year, or today for a show that is still running."""
    years = re.findall(r"\d{4}", release_info or "")
    if not years:
        return "0000-00-00"
    if re.search(r"\d{4}\s*[\u2013-]\s*$", release_info or ""):
        return time.strftime("%Y-%m-%d", time.gmtime())
    return f"{years[-1]}-12-31"

def previous():
    try:
        return {m["id"]: m for m in json.load(open(os.path.join(CATALOG, CAT_ID + ".json")))["metas"]}
    except Exception:
        return {}

def main():
    blocked = set(json.load(open(os.path.join(ROOT, "blocklist.json"))))
    shows = [s for s in json.load(open(os.path.join(ROOT, "shows.json"))) if s["id"] not in blocked]
    old = previous()
    try:
        dates = json.load(open(LATEST_FILE))
    except Exception:
        dates = {}
    entries = []
    for s in shows:
        m = meta(s["id"])
        if m:
            e = {"id": s["id"], "type": "series", "name": m["name"],
                 "releaseInfo": m.get("releaseInfo", ""),
                 "poster": f"https://images.metahub.space/poster/medium/{s['id']}/img"}
            if m.get("imdbRating"):
                e["imdbRating"] = m["imdbRating"]
            d = latest_aired(m) or fallback_date(e["releaseInfo"])
            cap = end_cap(e["releaseInfo"])
            dates[s["id"]] = min(d, cap) if cap else d
        elif s["id"] in old:
            print("keeping previous entry for", s["id"])
            e = old[s["id"]]
        else:
            print("skipping (no metadata yet):", s["id"])
            continue
        entries.append((e, s["genres"]))
    # Most recently aired first (latest episode date), then highest rated.
    def order(x):
        return (dates.get(x[0]["id"], "0000-00-00"), float(x[0].get("imdbRating") or 0))
    entries.sort(key=order, reverse=True)
    json.dump({e["id"]: dates[e["id"]] for e, _ in entries if e["id"] in dates}, open(LATEST_FILE, "w"), indent=1, sort_keys=True)
    os.makedirs(os.path.join(CATALOG, CAT_ID), exist_ok=True)
    def dump(path, items):
        with open(path, "w") as f:
            json.dump({"metas": items}, f)
    dump(os.path.join(CATALOG, CAT_ID + ".json"), [e for e, _ in entries])
    live_genres = [g for g in GENRES if any(g in gs for _, gs in entries)]
    for g in GENRES:
        dump(os.path.join(CATALOG, CAT_ID, f"genre={g}.json"), [e for e, gs in entries if g in gs])
    mpath = os.path.join(ROOT, "manifest.json")
    version = json.load(open(mpath))["version"] if os.path.exists(mpath) else "1.0.0"
    manifest = {
        "id": "io.github.ukcomedygameshows", "version": version, "name": NAME,
        "description": "Every UK comedy panel show, game show, quiz, chat show and stand-up showcase. No scripted shows, no reality.",
        "resources": ["catalog"], "types": ["series"], "idPrefixes": ["tt"],
        "catalogs": [{"type": "series", "id": CAT_ID, "name": NAME,
                      "extra": [{"name": "genre", "options": live_genres, "isRequired": False}],
                      "genres": live_genres, "extraSupported": ["genre"]}],
    }
    json.dump(manifest, open(mpath, "w"), indent=1)
    update_readme(entries)
    print(len(entries), "shows")

if __name__ == "__main__":
    main()
