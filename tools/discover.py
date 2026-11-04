#!/usr/bin/env python3
"""Find new UK comedy/game/panel shows via TMDB and add them to shows.json.

Needs TMDB_API_KEY (a v4 read access token) in the environment.
Anything listed in blocklist.json is never added.
"""
import datetime, json, os, subprocess, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("TMDB_API_KEY", "").strip()
API = "https://api.themoviedb.org/3"
KEYWORDS = ["game show", "panel show", "quiz show", "talk show", "stand-up comedy"]
EXCLUDE_GENRES = "10764,16,10766,18,10765,80,10762"  # reality, animation, soap, drama, sci-fi, crime, kids
LOOKBACK_DAYS = 180
COMEDY, TALK = 35, 10767

def tmdb(path, **params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def read(name):
    return json.load(open(os.path.join(ROOT, name)))

def cinemeta_uk(imdb):
    for _ in range(3):
        r = subprocess.run(["curl", "-sL", "--max-time", "30", f"https://v3-cinemeta.strem.io/meta/series/{imdb}.json"], capture_output=True, text=True).stdout
        try:
            m = json.loads(r)["meta"]
            c = m.get("country") or ""
            return m if "United Kingdom" in c and "Ireland" not in c.split(",")[0] else None
        except Exception:
            time.sleep(2)
    return None

def pick_genre(kw, gids):
    if "panel show" in kw:
        return "Panel"
    if "game show" in kw or "quiz show" in kw:
        return "Challenge" if COMEDY in gids else "Quiz & Game Shows"
    if "talk show" in kw or TALK in gids:
        return "Chat & Entertainment"
    if "stand-up comedy" in kw:
        return "Stand-up"
    return "Panel"

def preview_reality():
    """Print recent UK reality shows with the signals a 'celebrity only' rule could use. Changes nothing."""
    for k in ["celebrity", "celebrities", "famous", "celebrity reality show", "reality competition"]:
        res = [r for r in tmdb("/search/keyword", query=k).get("results", []) if r["name"].lower() == k]
        print(f"keyword '{k}':", res[0]["id"] if res else "not found")
    rows = []
    for page in range(1, 8):
        d = tmdb("/discover/tv", with_origin_country="GB", with_genres="10764", **{"first_air_date.gte": "2022-01-01"}, sort_by="popularity.desc", page=page)
        for t in d.get("results", []):
            kw = sorted(k["name"] for k in tmdb(f"/tv/{t['id']}/keywords").get("results", []))
            title = t["name"].lower()
            rows.append((("CELEB-TITLE" if "celeb" in title else "-"), t["name"], t.get("first_air_date", "")[:4], ", ".join(kw)))
        if page >= d.get("total_pages", 1):
            break
    for r in rows:
        print(" | ".join(r))
    print(len(rows), "reality shows")

def main():
    if "--preview-reality" in sys.argv:
        if not TOKEN:
            sys.exit("TMDB_API_KEY is not set")
        return preview_reality()
    if not TOKEN:
        sys.exit("TMDB_API_KEY is not set")
    shows = read("shows.json")
    known = {s["id"] for s in shows} | set(read("blocklist.json"))
    kw_ids = []
    for k in KEYWORDS:
        hit = [r for r in tmdb("/search/keyword", query=k).get("results", []) if r["name"].lower() == k]
        if hit:
            kw_ids.append(str(hit[0]["id"]))
    if not kw_ids:
        sys.exit("no keywords resolved; check the token")
    since = (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
    added = 0
    for page in range(1, 6):
        d = tmdb("/discover/tv", with_origin_country="GB", with_keywords="|".join(kw_ids), without_genres=EXCLUDE_GENRES, **{"first_air_date.gte": since}, sort_by="first_air_date.desc", page=page)
        for t in d.get("results", []):
            try:
                imdb = tmdb(f"/tv/{t['id']}/external_ids").get("imdb_id")
                if not imdb or imdb in known:
                    continue
                m = cinemeta_uk(imdb)
                if not m:
                    print("skip (not in Cinemeta as UK yet):", t["name"], imdb)
                    continue
                kw = {k["name"].lower() for k in tmdb(f"/tv/{t['id']}/keywords").get("results", [])}
                genre = pick_genre(kw, t.get("genre_ids", []))
                print(f"ADD: {m['name']} {imdb} -> {genre}")
                shows.append({"id": imdb, "genres": [genre]})
                known.add(imdb)
                added += 1
            except Exception as e:
                print("skip (error):", t.get("name"), e)
        if page >= d.get("total_pages", 1):
            break
    if added:
        json.dump(shows, open(os.path.join(ROOT, "shows.json"), "w"), indent=1)
    print(f"{added} show(s) added")

if __name__ == "__main__":
    main()
