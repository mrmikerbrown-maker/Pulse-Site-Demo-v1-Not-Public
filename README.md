# This week's economic calendar

Live page: https://mrmikerbrown-maker.github.io/calendar/

- `index.html` — the page. Reads `data/calendar.json`. Times shown in London time.
- `scripts/fetch.py` — fetches the week (Mon–Fri; from Saturday it loads the coming week).
  Main source: TradingView's public calendar feed (actual, consensus, previous).
  Backup: the ForexFactory weekly feed (no actuals). No API key, no Claude tokens.
- `.github/workflows/update.yml` — runs the fetch every 15 minutes on weekdays (every 30 minutes overnight for Asia),
  and commits only when something changed.
- `data/history.csv` — every released number with its consensus, kept forever. Data Surprises can read this.

Countries: US, Eurozone, Germany, UK, Japan, China, Canada, Australia, New Zealand, Switzerland, Norway, Sweden.
"Key" releases are the feed's high-importance ones plus every central bank decision.
"Medium" releases are shown only when they have a consensus, with auctions and similar noise filtered out.

To switch source later (e.g. the Newsquawk calendar): add a `fetch_newsquawk()` in `scripts/fetch.py` that returns the
same event fields and put it first in `SOURCES`. The page doesn't need to change.
