# Site health check

The job **Site health: check pages and data** (`.github/workflows/site-health.yml`) checks the live site every 15 minutes, all day, every day. It's free: the repo is public, so GitHub doesn't charge for Actions minutes, and it uses no Claude tokens.

## What it checks

| Part of the site | Page loads | Data job's last run | Data freshness |
|---|---|---|---|
| Home, Clock, Surprises, Glossary | yes | none | none |
| This week (calendar) | yes | yes, and the job restarts itself if it stops | still showing this week, and a change within 8 weekday hours |
| Index Contribution | yes | both jobs | SPY weights at most 3 US market days old, last session at most 2, Google Sheet answering |
| Earnings Moves | yes | yes | refreshed within 36 weekday hours, session at most 2 US market days old, no source failures reported |
| Economy Thermometer | yes | yes | refreshed within 42 hours, not demo data |
| Central banks overview | yes | yes | refreshed within 36 hours, not demo data |
| Central bank pricing (ECB, BoE) | yes, including the #ecb and #boe tabs | both jobs | ECB within 36 weekday hours and 2 market days; BoE within 30 weekday hours and 3 UK market days (the Bank publishes late); no source failures |
| Fed planner and Fed pricing | yes, including cb-pricing #fed | yes | within 36 weekday hours and 2 US market days; no source failures |
| Whole site | nav.js and glossary.js | none | none |

"Page loads" means two things. First, the page answers. Second, in a real (headless) browser it has no JavaScript error and doesn't show its own "could not load" message. A browser problem has to show up on two checks in a row before it alerts, so a page caught halfway through an update doesn't send an email.

All data is read from the **live** site, so a GitHub Pages build that fails to publish also shows up as stale data.

## How the alert reaches you

Each problem opens a GitHub **issue** labelled `site-alert`, with one issue for each part of the site. The issue is assigned to the repo owner, so GitHub emails you.

- **Problem starts:** 1 email.
- **Problem continues:** no more emails. The issue text is quietly kept up to date.
- **A different problem on the same page:** 1 email, as a comment on the open issue.
- **Problem fixed:** the issue closes itself with an "All clear" comment, which sends 1 email.
- **Whole site down:** 1 email in total, not one per page.

## Changing a limit

The limits and the list of pages are at the top of `check.py`, in `AREAS`, and in `data_checks()`. The market holiday lists in `HOLIDAYS` need next year's dates added each December.
