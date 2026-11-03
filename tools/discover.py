#!/usr/bin/env python3
"""Find new UK comedy/game/panel shows via TMDB and stage them in new.json.

Needs TMDB_API_KEY (a v4 read access token) in the environment.
Candidates are added to new.json only. A human moves approved ones into
shows.json, and rejected ones into blocklist.json.
"""
import datetime, json, os, subprocess, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("TMDB_API_KEY", "").strip()
API = "https://api.themoviedb.org/3"
KEYWORDS = ["game show", "panel show", "quiz show", "talk show", "stand-up comedy", "comedy panel", "celebrity game show", "comedy game show", "late night talk show"]
EXCLUDE_GENRES = "10764,16,10766,18,10765,80,10762"  # reality, animation, soap, drama, sci-fi, crime, kids
LOOKBACK_DAYS = 180

def tmdb(path, **params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def load(name):
    return json.load(open(os.path.join(ROOT, name)))

def cinemeta_uk(imdb):
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", f"https://v3-cinemeta.strem.io/meta/series/{imdb}.json"], capture_output=True, text=True).stdout
        try:
            m = json.loads(r)["meta"]
            c = (m.get("country") or "")
            return m if "United Kingdom" in c and "Ireland" not in c.split(",")[0] else None
        except Exception:
            time.sleep(2)
    return None

def main():
    if not TOKEN:
        sys.exit("TMDB_API_KEY is not set")
    known = {s["id"] for s in load("shows.json")} | {s["id"] for s in load("new.json")} | set(load("blocklist.json"))
    kw_ids = []
    for k in KEYWORDS:
        res = tmdb("/search/keyword", query=k).get("results", [])
        hit = [r for r in res if r["name"].lower() == k.lower()]
        print(f"keyword '{k}':", hit[0]["id"] if hit else "not found")
        if hit:
            kw_ids.append(str(hit[0]["id"]))
    if not kw_ids:
        sys.exit("no keywords resolved; check the token")
    since = (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
    added = []
    for page in range(1, 6):
        d = tmdb("/discover/tv", with_origin_country="GB", with_keywords="|".join(kw_ids), without_genres=EXCLUDE_GENRES, **{"first_air_date.gte": since}, sort_by="first_air_date.desc", page=page)
        for t in d.get("results", []):
            imdb = tmdb(f"/tv/{t['id']}/external_ids").get("imdb_id")
            if not imdb or imdb in known:
                continue
            m = cinemeta_uk(imdb)
            if not m:
                print("skip (not in Cinemeta as UK yet):", t["name"], imdb)
                continue
            print("NEW:", m["name"], imdb)
            added.append({"id": imdb, "name": m["name"]})
            known.add(imdb)
        if page >= d.get("total_pages", 1):
            break
    if added:
        new = load("new.json") + added
        json.dump(new, open(os.path.join(ROOT, "new.json"), "w"), indent=1)
    print(f"{len(added)} new candidate(s)")

if __name__ == "__main__":
    main()
