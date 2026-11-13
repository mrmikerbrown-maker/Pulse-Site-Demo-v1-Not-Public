# Alpha Pulse site (Pulse-Site-Demo-v1-Not-Public)

Everything on the Alpha Pulse site lives in this one repo and is served by GitHub Pages at
https://mrmikerbrown-maker.github.io/Pulse-Site-Demo-v1-Not-Public/

The site is public to anyone with the link, despite the repo name.

## What is where

| Folder | Page |
|---|---|
| `/` (index.html) | Home page with live cards for each tool |
| `calendar/` | This week (economic calendar) |
| `index-contribution-site/` | Index Contribution (S&P 500, Nasdaq 100, Dow); `preview/` is a test copy |
| `surprises/` | Data Surprises |
| `economy-thermometer/` | Economy Thermometer |
| `clock/` | Market Clock |
| `central-banks/` | Central banks |
| `fed-scenario-planner/` | Fed Scenario Planner |
| `glossary/` | Glossary page |

Shared by every page:
- `nav.js`: the top bar and menu. To add a tool to the menu, add one line to `TOOLS`.
- `glossary.js`: the hover definitions. To add a term, edit `GG`.

Every page links with relative paths, so the repo can be renamed again without breaking links.

## Data jobs (Actions tab)

All the jobs are free GitHub Actions and need no passwords or keys. Each one can be run by hand from the Actions tab with **Run workflow**.

| Job | When (UK time) | Updates |
|---|---|---|
| Calendar: update this week | every 15 min on weekdays, every 30 min overnight for Asia, plus Sat/Sun | `calendar/data/` |
| Central banks: update rates | about 06:30 and 20:30 in winter (an hour later in summer) | `central-banks/data.json` |
| Economy Thermometer: update data | about 06:17 in winter (07:17 in summer) | `economy-thermometer/data.json` |
| Index Contribution: save SPY weights | 13:15 on weekdays in winter (14:15 in summer) | `index-contribution-site/spy-weights*.csv` |
| Fed Scenario Planner: update data | weekdays 22:30 (often runs a few hours late) | `fed-scenario-planner/data.json` |
| Index Contribution: save last session | 16:40 New York time on weekdays | `index-contribution-site/last-session.csv`, `periods.csv` |

Every job saves through `.github/save.sh`, which retries if another job saved at the same moment and then asks GitHub Pages to rebuild.

The tools used to live in their own repos (calendar, central-banks, economy-thermometer, index-contribution-site, and the private fed-scenario-planner). They were moved here on 11 Nov 2026 with their history kept.

## Brand (Alpha Pulse)

Colours, fonts and logos live in `brand/`:

- `brand/brand.css` holds every shared colour and the font. Each page loads it last, so a colour changed there changes everywhere.
- `brand/logo/` holds the logo files. They are PLACEHOLDERS traced from the brand guide. When the official files arrive, upload them with the same names (`bar-paper.svg`, `bar-near-black.svg`, `icon-32.png`, `icon-192.png`, `icon-512.png`, `icon.svg`) and every page picks them up.
- `brand/fonts/` holds "AP Display": Creato Display (SIL Open Font License, `OFL.txt`) with tabular figures added so numbers line up. The licence asks for a new name on a changed copy, hence "AP Display".
