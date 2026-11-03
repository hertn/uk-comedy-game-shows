<h1 align="center">UK Comedy &amp; Game Shows</h1>

<p align="center">Every UK comedy panel show, game show, quiz, chat show and stand-up showcase, in one Stremio list.<br>88 shows. No scripted comedy, no reality TV.</p>

<p align="center"><a href="https://ko-fi.com/hertn"><img src="https://img.shields.io/badge/support-%E2%9D%A4%20Ko--fi-ff5e5b?style=flat&amp;labelColor=15181e&amp;logo=kofi&amp;logoColor=white" alt="Support on Ko-fi"></a></p>

## Install

**[Install in Stremio](stremio://hertn.github.io/uk-comedy-game-shows/manifest.json)**

Or open Addons in Stremio, choose Add addon, and paste:

```
https://hertn.github.io/uk-comedy-game-shows/manifest.json
```

The list appears on your Discover page as **UK Comedy & Game Shows**. Use the genre menu to narrow it down.

## What's in it

| Genre | Shows | |
| --- | ---: | --- |
| Panel | 21 | Comedians trading jokes about the news and each other. |
| Quiz & Game Shows | 26 | The Chase, Millionaire, QI, Only Connect and the rest. |
| Challenge | 13 | Taskmaster, Last One Laughing, Battle in the Box and other comedy games. |
| Chat & Entertainment | 20 | Chat shows and light entertainment fronted by comedians. |
| Stand-up | 7 | Stand-up showcases and live comedy. |
| Specials | 1 | One-off formats like the Big Fat Quiz. |
| Classic | 11 | The older shows, in one place. |

A show can appear under more than one genre.

## How it stays current

New episodes of every listed show appear in Stremio on their own. Every Monday, a GitHub Action looks for new UK panel, quiz, game and chat shows, adds them to the right genre and publishes the update. Nothing needs doing by hand. Changes go live within about ten minutes.

Only UK shows are added, and reality, drama, animation and kids' shows are filtered out.

## Remove a show

If something slips in that doesn't belong:

1. Open [`blocklist.json`](blocklist.json) on GitHub and click the pencil icon.
2. Add the show's IMDb ID (the `tt...` number from its IMDb page) inside the brackets, like `["tt1234567"]`. Separate several with commas.
3. Click Commit changes. The next weekly run removes it, or run it now from the Actions tab with Run workflow.

## If the weekly job fails

GitHub emails the repo owner. The usual cause is the TMDB token: create a new one at themoviedb.org (Settings > API) and save it under Settings > Secrets and variables > Actions as `TMDB_API_KEY`. The list keeps working in the meantime, and it just stops adding new shows.

## Support

This is free, with no ads or subscriptions. If you enjoy it, you can [buy me a coffee on Ko-fi](https://ko-fi.com/hertn).
