#!/usr/bin/env python3
"""Find UK comedy / game / panel / chat shows on TMDB and add them to shows.json.

Needs TMDB_API_KEY (a v4 read access token) in the environment.

Two streams of candidates:
  1. Comedy, quiz, game, panel, talk and stand-up shows (reality TV is excluded).
  2. Celebrity reality competitions: reality shows whose title says "Celebrity"
     or "Celeb", or that belong to a known celebrity franchise (Masked, Strictly,
     Dancing on Ice). Regular reality TV (Big Brother, Love Island, ...) is left out.

Environment switches:
  BACKFILL=1  look at every year instead of the last 180 days (one-off catch-up)
  DRY_RUN=1   print what would be added, change nothing
Anything in blocklist.json is never added.
"""
import datetime, json, os, subprocess, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("TMDB_API_KEY", "").strip()
BACKFILL = os.environ.get("BACKFILL") == "1"
DRY_RUN = os.environ.get("DRY_RUN") == "1"
API = "https://api.themoviedb.org/3"

KEYWORDS = ["game show", "panel show", "quiz show", "talk show", "stand-up comedy"]
NOT_COMEDY = "10764,16,10766,18,10765,80,10762"  # reality, animation, soap, drama, sci-fi, crime, kids
REALITY = "10764"
LOOKBACK_DAYS = 180
MIN_VOTES = 3 if BACKFILL else 0          # old shows must have some audience
COMEDY, TALK = 35, 10767

# Reality shows are only allowed in when they look like celebrity competitions.
CELEB_WORDS = ["celeb"]                              # "Celebrity ...", "I'm a Celeb..."
CELEB_FRANCHISES = ["masked", "strictly", "dancing on ice"]
COMPETITION_TAGS = {"game show", "quiz show", "competition", "challenge", "reality competition",
                    "singing competition", "dance competition", "cooking competition", "race"}

def tmdb(path, **params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)

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

def comedy_genre(kw, gids):
    if "panel show" in kw:
        return "Panel"
    if "game show" in kw or "quiz show" in kw:
        return "Challenge" if COMEDY in gids else "Quiz & Game Shows"
    if "talk show" in kw or TALK in gids:
        return "Chat & Entertainment"
    if "stand-up comedy" in kw:
        return "Stand-up"
    return "Panel"

def celebrity_ok(title, kw):
    t = title.lower()
    if any(f in t for f in CELEB_FRANCHISES):
        return True
    if any(w in t for w in CELEB_WORDS):
        # Companion shows have a subtitle ("The Celebrity Traitors: Uncloaked");
        # the main shows carry a competition tag. Lifestyle shows with neither stay out.
        return ":" in title or bool(kw & COMPETITION_TAGS)
    return "celebrity" in kw and bool(kw & COMPETITION_TAGS)

def candidates(since, kw_ids):
    """Yield (stream, tmdb_show) pairs."""
    base = {"with_origin_country": "GB", "first_air_date.gte": since, "sort_by": "vote_count.desc" if BACKFILL else "first_air_date.desc"}
    if MIN_VOTES:
        base["vote_count.gte"] = MIN_VOTES
    streams = [("comedy", dict(base, with_keywords="|".join(kw_ids), without_genres=NOT_COMEDY)),
               ("celebrity", dict(base, with_genres=REALITY))]
    for name, params in streams:
        for page in range(1, 31 if BACKFILL else 6):
            d = tmdb("/discover/tv", page=page, **params)
            for t in d.get("results", []):
                yield name, t
            if page >= d.get("total_pages", 1):
                break

def main():
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
    since = "1950-01-01" if BACKFILL else (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
    added = []
    seen = set()
    for stream, t in candidates(since, kw_ids):
        if t["id"] in seen:
            continue
        seen.add(t["id"])
        try:
            kw = {k["name"].lower() for k in tmdb(f"/tv/{t['id']}/keywords").get("results", [])}
            if stream == "celebrity":
                if not celebrity_ok(t["name"], kw):
                    if os.environ.get("VERBOSE") and any(w in t["name"].lower() for w in ("celeb", "mask", "strict", "dancing", "hunted", "sas", "splash", "bake", "masterchef", "gogglebox")):
                        print(f"REJECT title/tags | {t['name']} | {t.get('first_air_date','')[:4]} | tags {sorted(kw)}")
                    continue
                genre = "Celebrity"
            else:
                genre = comedy_genre(kw, t.get("genre_ids", []))
            imdb = tmdb(f"/tv/{t['id']}/external_ids").get("imdb_id")
            if not imdb or imdb in known:
                if os.environ.get("VERBOSE") and stream == "celebrity":
                    print(f"REJECT {'no imdb id' if not imdb else 'already known'} | {t['name']} | {t.get('first_air_date','')[:4]}")
                continue
            m = cinemeta_uk(imdb)
            if not m:
                if os.environ.get("VERBOSE"):
                    print(f"REJECT not UK in Cinemeta | {t['name']} | {imdb}")
                continue
            print(f"{'WOULD ADD' if DRY_RUN else 'ADD'} | {genre} | {m['name']} | {m.get('releaseInfo','')} | {imdb} | votes {t.get('vote_count')}")
            added.append({"id": imdb, "genres": [genre]})
            known.add(imdb)
        except Exception as e:
            print("skip (error):", t.get("name"), e)
    if added and not DRY_RUN:
        json.dump(shows + added, open(os.path.join(ROOT, "shows.json"), "w"), indent=1)
    print(f"{len(added)} show(s) {'would be ' if DRY_RUN else ''}added")

if __name__ == "__main__":
    main()
