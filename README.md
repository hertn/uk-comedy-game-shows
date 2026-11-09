<p align="center">
  <img src="icon.svg" width="88" height="88" alt="UK Comedy & Game Shows icon">
</p>

<h1 align="center">UK Comedy &amp; Game Shows</h1>

<p align="center">Every UK comedy panel show, game show, quiz, chat show and stand-up showcase, in one Stremio list.<br><!-- total -->159<!-- /total --> shows. No scripted comedy, no reality TV.</p>

<p align="center">
  <a href="https://web.stremio.com/#/addons?addon=https%3A%2F%2Fhertn.github.io%2Fuk-comedy-game-shows%2Fmanifest.json"><img src="https://img.shields.io/badge/install-in%20Stremio-7b5cf0?style=flat&amp;labelColor=15181e" alt="Install in Stremio"></a>
  <a href="https://ko-fi.com/hertn"><img src="https://img.shields.io/badge/support-%E2%9D%A4%20Ko--fi-ff5e5b?style=flat&amp;labelColor=15181e&amp;logo=kofi&amp;logoColor=white" alt="Support on Ko-fi"></a>
</p>

## Install

**[Install in Stremio](stremio://hertn.github.io/uk-comedy-game-shows/manifest.json)**

Or open Addons in Stremio, choose Add addon, and paste:

```
https://hertn.github.io/uk-comedy-game-shows/manifest.json
```

The list appears on your Discover page as **UK Comedy & Game Shows**. Use the genre menu to narrow it down.

## What's in it

<!-- genres -->
| Genre | Shows | |
| --- | ---: | --- |
| Panel | 30 | Comedians trading jokes about the news and each other. |
| Quiz & Game Shows | 41 | The Chase, Millionaire, QI, Only Connect and the rest. |
| Challenge | 23 | Taskmaster, Last One Laughing, Battle in the Box and other comedy games. |
| Chat & Entertainment | 31 | Chat shows and light entertainment fronted by comedians. |
| Stand-up | 15 | Stand-up showcases and live comedy. |
| Specials | 1 | One-off formats like the Big Fat Quiz. |
| Classic | 11 | The older shows, in one place. |
| Celebrity | 18 | Celebrity reality competitions, from I'm a Celebrity to The Masked Singer. |
<!-- /genres -->

A show can appear under more than one genre.

## How it stays current

New episodes of every listed show appear in Stremio on their own. Every Monday, a GitHub Action looks for new UK panel, quiz, game and chat shows, adds them to the right genre and publishes the update. Nothing needs doing by hand. Changes go live within about ten minutes.

Only UK shows are added. Reality TV is left out, except celebrity competitions (see Rules below). Drama, animation and kids' shows are filtered out.

## Support

This is free, with no ads or subscriptions. If you enjoy it, you can [buy me a coffee on Ko-fi](https://ko-fi.com/hertn).

## Maintenance

Reference for whoever looks after this, which will probably be you in a few months with everything forgotten. Nothing here needs doing in normal use.

### How it works

It's a Stremio addon made of plain files on GitHub Pages, with no server. Stremio reads `manifest.json`, then the catalog files under `catalog/series/`. Every file in this repo is either data or a small Python script, and there's nothing to install or host.

| File | What it is |
| --- | --- |
| `shows.json` | The list: each show's IMDb ID and its genres. This is the source of truth. |
| `blocklist.json` | IMDb IDs that must never appear. Wins over everything else. |
| `tools/discover.py` | Finds new UK shows on TMDB and appends them to `shows.json`. |
| `tools/build.py` | Reads `shows.json`, fetches names, years and ratings from Cinemeta, and writes `manifest.json` and `catalog/`. |
| `.github/workflows/update.yml` | Runs both scripts every Monday at 07:00 UTC, commits, and publishes. |
| `latest.json` | Cached date of each show's latest aired episode, used for the sort order. Rewritten by the build. |
| `last-run.txt` | Written by every run so GitHub never pauses the schedule for inactivity. |
| `.github/FUNDING.yml` | The Ko-fi Sponsor button. |

The list is shown with the most recently aired shows first, using the date of each show's latest aired episode from Cinemeta (capped at the end year for shows that have finished). Ties are broken by IMDb rating. The dates are cached in `latest.json`. Change the sort in `tools/build.py` (the `order` function) if you want something else.

Never edit anything under `catalog/` or `manifest.json` by hand, because the next run overwrites it. The same goes for the show count at the top of this README and the genre table, which the build rewrites between the `<!-- total -->` and `<!-- genres -->` markers. Keep those markers if you edit the README.

### Remove a show

1. Open `blocklist.json` on GitHub and click the pencil icon.
2. Add the show's IMDb ID (the `tt...` number in its IMDb URL) inside the brackets, like `["tt1234567"]`. Separate several with commas.
3. Commit changes. The next weekly run removes it, or go to the Actions tab, choose Find new shows, and click Run workflow to do it now.

### Add a show by hand

Add `{"id": "tt1234567", "genres": ["Panel"]}` to `shows.json`, then run the workflow from the Actions tab. Genres are `Panel`, `Quiz & Game Shows`, `Challenge`, `Chat & Entertainment`, `Stand-up`, `Specials`, `Classic` and `Celebrity`, and a show can have several. The show must exist in Cinemeta as a series, or it can't appear in Stremio. Check by opening `https://v3-cinemeta.strem.io/meta/series/<id>.json`. Use the UK entry, because US, Australian and other versions have their own IDs and Cinemeta lists them separately.

### Rules for what belongs

- UK shows only. No US, Irish or other versions.
- Comedy panel, game, quiz, chat and stand-up shows, plus Taskmaster-style comedy games. Quiz shows don't need comedians.
- No scripted comedy.
- No reality TV, with one exception: celebrity competitions that have a prize or a winner (I'm a Celebrity, Celebrity Big Brother, The Masked Singer, Strictly, and so on). They go in the Celebrity genre. Regular Big Brother, Love Island, The Traitors, Bake Off and MasterChef stay out.
- One-off specials such as the Big Fat Quiz are allowed.

### How new shows are found

Each Monday `discover.py` makes two searches on TMDB, both limited to UK series from the last 180 days.

1. **Comedy and game shows.** Series tagged game show, panel show, quiz show, talk show or stand-up comedy, excluding the genres reality, animation, soap, drama, sci-fi, crime and kids. A game or quiz show that is also tagged Comedy goes to Challenge, other game and quiz shows to Quiz & Game Shows, panel shows to Panel, talk shows to Chat & Entertainment, and anything else to Panel.
2. **Celebrity competitions.** Reality series are only let in if the title contains "Celeb" or a celebrity franchise name (Masked, Strictly, Dancing on Ice), or if TMDB tags them "celebrity" and also a competition. A title with "Celeb" needs a competition tag or a subtitle, so companion shows such as "The Celebrity Traitors: Uncloaked" get in and lifestyle shows such as "Celebrity Escape to the Country" don't. These go to the Celebrity genre. To add another franchise, add its name to `CELEB_FRANCHISES` in `tools/discover.py`.

Every candidate must also exist in Cinemeta with a UK country tag. There's no data source that tells a celebrity reality show from a regular one, so the rule goes by name. A future celebrity show with an unrelated title and no "celebrity" tag would be missed. Occasionally something that doesn't belong gets through, so use the blocklist.

### Catch up on older shows

The weekly job only looks back 180 days. To scan every year (done once, on 2026-11-04), go to the Actions tab, choose Backfill (one-off), and click Run workflow. Leave "Dry run" as `true` to print what would be added without changing anything, or set it to `false` to add the shows and publish. Shows with fewer than 3 votes on TMDB are skipped.

### If the weekly job fails

GitHub emails the repo owner. Check the Actions tab for the failed run and open its log.

- **"TMDB_API_KEY is not set" or an HTTP 401 error.** The token is missing or no longer valid. Create a new one at themoviedb.org (Settings, then API, and copy the API Read Access Token, the long one starting with `eyJ`). Save it at Settings, then Secrets and variables, then Actions, and edit `TMDB_API_KEY`. From a terminal with the GitHub CLI you can instead copy the token and run `pbpaste | gh secret set TMDB_API_KEY -R hertn/uk-comedy-game-shows`.
- **Cinemeta errors.** These are usually temporary. `build.py` keeps the previous entry for any show it can't fetch, so the list is not affected. Re-run the workflow later.
- **The schedule stopped.** GitHub pauses scheduled jobs after 60 days without repo activity. The weekly `last-run.txt` commit prevents this, but if it ever happens, open the Actions tab and re-enable the workflow.

While the job is failing, the list keeps working. It just stops picking up new shows.

### Changing genres or the name

Stremio caches the genre list and name from `manifest.json`. After changing the `GENRES` list, `NAME` or `CAT_ID` in `tools/build.py`, raise the `version` in `manifest.json` (for example 1.2.0 to 1.3.0) and remove and re-add the addon in Stremio. Changing which shows are in the list needs neither, because Stremio refreshes the catalogs on its own within about ten minutes.

### Run it on your own computer

You need Python 3 and curl. `python3 tools/build.py` rebuilds the catalog. `TMDB_API_KEY=<token> python3 tools/discover.py` runs the discovery step and edits `shows.json`.

### Things the automation can't do

- Each week it only looks at shows that started in the last 180 days, and only finds those TMDB has tagged with the keywords above. Older shows are covered by the one-off backfill, and anything TMDB tagged differently has to be added by hand. Splash! and Celebrity Gogglebox, for example, are not tagged as competitions and so are missing.
- Cinemeta is the only source of what Stremio shows, so a show it doesn't list can't be added. Some shows only have a single entry covering all their editions. The Big Fat Quiz, for example, is just one entry, and as of November 2026 there is no UK Blockbusters or UK The Floor entry.
- If TMDB changes how it tags shows, or ends its free API, `discover.py` will need rewriting. The existing list keeps working either way.
