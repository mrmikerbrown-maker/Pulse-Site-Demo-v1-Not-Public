#!/usr/bin/env python3
"""Site health check: is every page up, did every data job work, is every data file fresh?

Runs inside the "Site health: check pages and data" GitHub job. When it finds a problem it opens
ONE GitHub issue for the part of the site affected (label "site-alert", assigned to the repo owner),
which makes GitHub email the owner. While the problem lasts the issue is only edited, which sends
no email. A new kind of problem on the same part of the site adds a comment (one email). When the
problem is gone the issue is closed with a short note (one "all clear" email).

Everything the check reads is the LIVE site (what visitors get), plus the GitHub Actions run history.

Settings come from environment variables (the workflow sets them):
  GITHUB_TOKEN, GITHUB_REPOSITORY    GitHub API access (given by Actions)
  BASE_URL      live site address (default https://<owner>.github.io/<repo>/)
  DRY_RUN=1     print what it would do, change nothing on GitHub
  LOOP_MINUTES  keep checking for this long (0 = check once)
  EVERY_MINUTES gap between checks (default 15)
  BROWSER=0     skip the headless-browser page check
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    LONDON = ZoneInfo("Europe/London")
except Exception:  # pragma: no cover
    LONDON = timezone.utc

REPO = os.environ.get("GITHUB_REPOSITORY", "mrmikerbrown-maker/Pulse-Site-Demo-v1-Not-Public")
OWNER, NAME = REPO.split("/")
BASE = os.environ.get("BASE_URL") or "https://%s.github.io/%s/" % (OWNER.lower(), NAME)
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DRY = os.environ.get("DRY_RUN", "0") == "1"
LABEL = "site-alert"
UA = "pulse-site-health-check"

# ---------------------------------------------------------------------------------------------
# What to check. Edit here when a page or data job is added, moved or re-timed.
#
# Freshness of "generated" (when the job last wrote the file) is measured in WEEKDAY HOURS for
# jobs that only run Mon-Fri (so weekends don't count), otherwise in plain hours. GitHub often
# starts scheduled jobs hours late, so the limits leave room for that.
# "asof" limits count market days (weekdays minus that market's holidays) after the data's date.
# ---------------------------------------------------------------------------------------------
AREAS = [
    {"id": "home", "name": "Home page", "page": ""},
    {"id": "calendar", "name": "This week (economic calendar)", "page": "calendar/",
     "workflows": ["calendar.yml"], "keep_running": "calendar.yml"},
    {"id": "index", "name": "Index Contribution", "page": "index-contribution-site/",
     "workflows": ["index-snapshot.yml", "index-spy.yml"]},
    {"id": "clock", "name": "Market Clock", "page": "clock/"},
    {"id": "earnings", "name": "Earnings Moves", "page": "earnings-moves/",
     "workflows": ["earnings-moves.yml"]},
    {"id": "surprises", "name": "Data Surprises", "page": "surprises/"},
    {"id": "thermometer", "name": "Economy Thermometer", "page": "economy-thermometer/",
     "workflows": ["economy-thermometer.yml"]},
    {"id": "central-banks", "name": "Central banks overview", "page": "central-banks/",
     "workflows": ["central-banks.yml"]},
    {"id": "cb-pricing", "name": "Central bank pricing (ECB / BoE)", "page": "cb-pricing/",
     "extra_pages": ["cb-pricing/#ecb", "cb-pricing/#boe"],
     "workflows": ["ecb-pricing.yml", "boe-pricing.yml"]},
    {"id": "fed", "name": "Fed scenario planner and Fed pricing", "page": "fed-scenario-planner/",
     "extra_pages": ["cb-pricing/#fed"], "workflows": ["fed-scenario-planner.yml"]},
    {"id": "cross-asset", "name": "Cross-Asset Moves", "page": "cross-asset/",
     "workflows": ["cross-asset.yml"], "kick_if_idle": "cross-asset.yml"},
    {"id": "yield-curve", "name": "Yield Curves", "page": "yield-curve/",
     "workflows": ["yield-curve.yml"]},
    {"id": "positioning", "name": "Speculator Positioning", "page": "cftc-positioning/",
     "workflows": ["cftc-positioning.yml"]},
    {"id": "glossary", "name": "Glossary", "page": "glossary/"},
]

# Shared files every page needs: if one breaks, the whole site looks broken.
SITE_FILES = ["nav.js", "glossary.js"]

# Market holidays (data dated on these days isn't expected). Add next year's each December.
HOLIDAYS = {
    "us": {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
           "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
           "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18",
           "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"},
    "target": {"2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-12-25",
               "2027-01-01", "2027-03-26", "2027-03-29"},
    "uk": {"2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04", "2026-05-25", "2026-08-31",
           "2026-12-25", "2026-12-28",
           "2027-01-01", "2027-03-26", "2027-03-29", "2027-05-03", "2027-05-31", "2027-08-30",
           "2027-12-27", "2027-12-28"},
}


def now_utc():
    return datetime.now(timezone.utc)


def london(dt):
    return dt.astimezone(LONDON).strftime("%a %d %b %H:%M")


def parse_ts(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def weekday_hours(since, until):
    """Hours between two times that fall on Monday-Friday (UTC)."""
    total, t = 0.0, since
    while t < until:
        nxt = min(until, (t + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0))
        if t.weekday() < 5:
            total += (nxt - t).total_seconds() / 3600
        t = nxt
    return total


def market_days_after(d, today, cal):
    """Market days after date d, up to and including today."""
    n, x = 0, d + timedelta(days=1)
    while x <= today:
        if x.weekday() < 5 and x.isoformat() not in HOLIDAYS.get(cal, ()):
            n += 1
        x += timedelta(days=1)
    return n


def ago(hours):
    return "%d hours" % round(hours) if hours < 48 else "%.1f days" % (hours / 24)


# ---------------------------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------------------------
def http(url, tries=3, wait=20, timeout=30):
    """GET a URL, retrying. Returns (status, bytes or None, error text)."""
    last = (0, None, "")
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), ""
        except urllib.error.HTTPError as e:
            last = (e.code, None, "HTTP %d" % e.code)
        except Exception as e:  # timeouts, DNS, connection resets
            last = (0, None, str(e)[:120])
        if i < tries - 1:
            time.sleep(wait)
    return last


def live(path):
    return BASE + path + ("&" if "?" in path else "?") + "t=%d" % time.time()


def api(method, path, body=None, ok=(200, 201, 204)):
    url = "https://api.github.com/repos/%s%s" % (REPO, path)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        if e.code in ok:
            return {}
        raise RuntimeError("GitHub API %s %s -> HTTP %d %s" % (method, path, e.code, e.read()[:200]))


# ---------------------------------------------------------------------------------------------
# Checks. Each returns a list of (kind, text). "kind" is stable for the same sort of problem;
# "text" can change (e.g. "40 hours old" -> "41 hours old") without counting as a new problem.
# ---------------------------------------------------------------------------------------------
def get_json(path, problems, label):
    st, body, err = http(live(path))
    if body is None:
        problems.append(("fetch:" + path, "%s (%s) could not be downloaded: %s" % (label, path, err)))
        return None
    try:
        return json.loads(body)
    except Exception:
        problems.append(("broken:" + path, "%s (%s) is not valid JSON, so the page can't read it" % (label, path)))
        return None


def check_generated(d, path, label, max_hours, weekdays_only, problems):
    g = d.get("generated") if isinstance(d, dict) else None
    if not g:
        problems.append(("nostamp:" + path, "%s (%s) has no 'generated' time" % (label, path)))
        return
    t = parse_ts(g)
    hours = weekday_hours(t, now_utc()) if weekdays_only else (now_utc() - t).total_seconds() / 3600
    if hours > max_hours:
        problems.append(("stale:" + path, "%s last refreshed %s London, %s ago%s (limit %d)" % (
            label, london(t), ago(hours), " counting weekdays only" if weekdays_only else "", max_hours)))


def check_asof(day, path, label, max_days, cal, problems):
    if not day:
        return
    d = date.fromisoformat(day[:10])
    n = market_days_after(d, now_utc().date(), cal)
    if n > max_days:
        problems.append(("old:" + path, "%s data is dated %s, %d market days old (limit %d)" % (
            label, d.strftime("%a %d %b"), n, max_days)))


def check_problem_list(d, path, label, problems):
    for p in (d.get("problems") or []) if isinstance(d, dict) else []:
        p = str(p)
        if p == "path":
            p = "the futures prices could not be fetched, so pricing is from an earlier day"
        kind = "source:" + path + ":" + re.sub(r"\d+", "N", p)[:80]
        problems.append((kind, "%s - last run reported: %s" % (label, p)))


def data_checks(area_id, problems):
    if area_id == "calendar":
        d = get_json("calendar/data/calendar.json", problems, "Calendar data")
        if d:
            now = now_utc()
            # The page shows Mon-Fri; from Saturday it switches to next week (fetch.py week_window).
            day = now.date()
            if day.weekday() >= 5:
                day += timedelta(days=7 - day.weekday())
            want = (day - timedelta(days=day.weekday())).isoformat()
            grace = now.weekday() == 5 and now.hour < 6  # a few hours to roll over on Saturday
            if d.get("week_start") != want and not grace:
                problems.append(("week", "Calendar is still showing the week of %s (should be %s)" % (
                    d.get("week_start"), want)))
            # 'checked' only moves when something changed (a new number came out). On weekdays
            # releases land every few hours across the 12 countries, so 8 weekday-hours of nothing
            # means the fetch is failing.
            if d.get("checked"):
                h = weekday_hours(parse_ts(d["checked"]), now)
                if h > 8:
                    problems.append(("stale:calendar", "Calendar data last changed %s London, %s ago "
                                     "(counting weekdays only, limit 8)" % (london(parse_ts(d["checked"])), ago(h))))
    elif area_id == "index":
        st, body, err = http(live("index-contribution-site/spy-weights.csv"))
        if body is None:
            problems.append(("fetch:spy", "SPY weights file could not be downloaded: " + err))
        else:
            first = body.decode("utf-8", "replace").splitlines()[:1]
            asof = first[0].split(",")[1] if first and first[0].startswith("asof,") else None
            if not asof:
                problems.append(("broken:spy", "SPY weights file has no 'asof' date on its first line"))
            else:
                check_asof(asof, "spy", "SPY weights", 3, "us", problems)
        st, body, err = http(live("index-contribution-site/periods.csv"))
        if body is None:
            problems.append(("fetch:periods", "Week/Month/YTD closes file could not be downloaded: " + err))
        else:
            head = next(csv.reader(io.StringIO(body.decode("utf-8", "replace"))), [])
            last = head[-1] if len(head) > 1 else None
            if not last or not re.match(r"\d{4}-\d\d-\d\d$", last):
                problems.append(("broken:periods", "Week/Month/YTD closes file has an unexpected header"))
            else:
                check_asof(last, "periods", "Last saved US session (Index Contribution)", 2, "us", problems)
        # The page reads the Google Sheet live during New York hours.
        sheet = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vSE9500jiKFvBw_k0q2m8CPaZ3VbZNv0uIYCe-"
                 "QSnXpbASoqvwr2RW2hocHl5NVQejXIfVe4CdhX67h/pub?gid=454467433&single=true&output=csv")
        st, body, err = http(sheet)
        if body is None or b"IDX_SPX" not in body:
            problems.append(("sheet", "The published Google Sheet (live index numbers) isn't answering properly: %s"
                             % (err or "no IDX_SPX row")))
    elif area_id == "cross-asset":
        # The page reads data.json straight from the repo (raw.githubusercontent.com), not from
        # the published site, because the job saves every 5 minutes without republishing.
        st, body, err = http("https://raw.githubusercontent.com/%s/main/cross-asset/data.json?t=%d"
                             % (REPO, time.time()))
        d = None
        if body is None:
            problems.append(("fetch:cross-asset", "Cross-asset data could not be downloaded: " + err))
        else:
            try:
                d = json.loads(body)
            except Exception:
                problems.append(("broken:cross-asset", "Cross-asset data is not valid JSON"))
        if d:
            if in_cross_asset_hours(now_utc() - timedelta(minutes=45)) and d.get("asof"):
                age = (now_utc() - parse_ts(d["asof"])).total_seconds() / 60
                if age > 45:
                    problems.append(("stale:cross-asset", "Cross-asset prices last updated %s London, "
                                     "%d minutes ago (limit 45 during 07:00-22:00 London on weekdays)"
                                     % (london(parse_ts(d["asof"])), age)))
            if d.get("missing"):
                problems.append(("missing:cross-asset", "Cross-asset prices missing for: "
                                 + ", ".join(map(str, d["missing"]))[:200]))
    elif area_id == "yield-curve":
        d = get_json("yield-curve/data.json", problems, "Yield curve data")
        if d:
            check_generated(d, "yield-curve", "Yield curve data", 30, True, problems)
            check_problem_list(d, "yield-curve", "Yield curve data", problems)
    elif area_id == "positioning":
        # Weekly CFTC data: positions dated Tuesday, published Friday (a few days later in US
        # holiday weeks). The job runs Fri, Sat, Mon and Tue, so it never sits idle 4+ days.
        d = get_json("cftc-positioning/data.json", problems, "Positioning data")
        if d:
            check_generated(d, "positioning", "Positioning data", 100, False, problems)
            check_asof(d.get("asof"), "positioning", "Positioning data", 11, "us", problems)
    elif area_id == "earnings":
        d = get_json("earnings-moves/data.json", problems, "Earnings data")
        if d:
            check_generated(d, "earnings", "Earnings data", 36, True, problems)
            check_asof(d.get("session"), "earnings", "Earnings data", 2, "us", problems)
            check_problem_list(d, "earnings", "Earnings data", problems)
    elif area_id == "thermometer":
        d = get_json("economy-thermometer/data.json", problems, "Thermometer data")
        if d:
            check_generated(d, "thermometer", "Thermometer data", 42, False, problems)
            if d.get("demo"):
                problems.append(("demo:thermometer", "Thermometer is showing DEMO data, not real data"))
    elif area_id == "central-banks":
        d = get_json("central-banks/data.json", problems, "Central bank data")
        if d:
            check_generated(d, "central-banks", "Central bank data", 36, False, problems)
            if d.get("demo"):
                problems.append(("demo:central-banks", "Central banks page is showing DEMO data, not real data"))
    elif area_id == "cb-pricing":
        d = get_json("ecb-pricing/data.json", problems, "ECB pricing data")
        if d:
            check_generated(d, "ecb", "ECB pricing data", 36, True, problems)
            check_asof((d.get("path") or {}).get("asof"), "ecb", "ECB pricing", 2, "target", problems)
            check_problem_list(d, "ecb", "ECB pricing data", problems)
        d = get_json("boe-pricing/data.json", problems, "BoE pricing data")
        if d:
            check_generated(d, "boe", "BoE pricing data", 30, True, problems)
            # The Bank publishes its curve 1-2 days behind, hence 3.
            check_asof((d.get("path") or {}).get("asof"), "boe", "BoE pricing", 3, "uk", problems)
            check_problem_list(d, "boe", "BoE pricing data", problems)
    elif area_id == "fed":
        d = get_json("fed-scenario-planner/data.json", problems, "Fed pricing data")
        if d:
            check_generated(d, "fed", "Fed pricing data", 36, True, problems)
            check_asof((d.get("path") or {}).get("asof"), "fed", "Fed pricing", 2, "us", problems)
            check_problem_list(d, "fed", "Fed pricing data", problems)
        d = get_json("fed-scenario-planner/fomc.json", problems, "Fed-day history")
        if d:
            check_generated(d, "fomc", "Fed-day history", 36, True, problems)


def page_check(path, problems):
    st, body, err = http(live(path.split("#")[0]))
    if body is None:
        problems.append(("down:" + path, "Page %s is not loading (%s)" % (BASE + path, err)))
        return False
    if len(body) < 300 or b"<" not in body[:200]:
        problems.append(("down:" + path, "Page %s came back nearly empty" % (BASE + path)))
        return False
    return True


# ---------------------------------------------------------------------------------------------
# Headless browser: catches a page that loads but breaks in the browser (a JavaScript error,
# or the page's own "could not load the data" message).
# ---------------------------------------------------------------------------------------------
class Browser:
    def __init__(self):
        self.pw = self.browser = None
        if os.environ.get("BROWSER", "1") == "0":
            return
        try:
            from playwright.sync_api import sync_playwright
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch()
        except Exception as e:
            print("Browser check off (Playwright not available: %s)" % str(e)[:100])
            self.browser = None

    def check(self, path):
        """Returns a list of problem texts for this page (empty when fine)."""
        if not self.browser:
            return []
        out = []
        page = self.browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e).splitlines()[0][:160]))
        try:
            page.goto(BASE + path, wait_until="load", timeout=45000)
            page.wait_for_timeout(6000)  # let the page fetch its data and draw
            text = page.inner_text("body")
            m = re.search(r"[^.\n]*could not load[^.\n]*\.?", text, re.I)
            if m:
                out.append("Page %s shows: \"%s\"" % (BASE + path, m.group(0).strip()[:160]))
        except Exception as e:
            out.append("Page %s did not finish loading in a browser (%s)" % (BASE + path, str(e).splitlines()[0][:120]))
        finally:
            page.close()
        for e in errors:
            out.append("Page %s has a JavaScript error: %s" % (BASE + path, e))
        return out

    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.pw:
                self.pw.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------------------------
# GitHub Actions: did each data job's last run fail? Is the calendar job running?
# ---------------------------------------------------------------------------------------------
def last_finished_run(wf):
    runs = api("GET", "/actions/workflows/%s/runs?branch=main&per_page=15" % wf).get("workflow_runs", [])
    for r in runs:
        if r["status"] == "completed" and r["conclusion"] not in ("cancelled", "skipped"):
            return r
    return None


def is_running(wf):
    for st in ("in_progress", "queued", "pending", "waiting"):
        if api("GET", "/actions/workflows/%s/runs?status=%s&per_page=1" % (wf, st)).get("total_count"):
            return True
    return False


KICKED = {}  # workflow -> time this check last started it


def in_cross_asset_hours(t):
    """Weekdays 07:00-22:00 London: when the cross-asset job refreshes prices."""
    lt = t.astimezone(LONDON)
    return lt.weekday() < 5 and 7 <= lt.hour < 22


def job_checks(area, problems):
    for wf in area.get("workflows", []):
        try:
            r = last_finished_run(wf)
        except Exception as e:
            print("  (could not read runs for %s: %s)" % (wf, e))
            continue
        if r and r["conclusion"] != "success":
            problems.append(("job:" + wf, "The job \"%s\" failed on its last run (%s London). Log: %s" % (
                r["name"], london(parse_ts(r["created_at"])), r["html_url"])))
    wf = area.get("kick_if_idle")
    if wf and in_cross_asset_hours(now_utc()):
        # The cross-asset job also loses hours to GitHub skipping its hourly start. A run started
        # by hand does one update and stops, so starting one on each check keeps the prices at
        # most ~15 minutes old until the next scheduled run takes over. Staleness alerts as above.
        try:
            if not is_running(wf):
                print("  %s is not running: starting one update" % wf)
                if not DRY:
                    api("POST", "/actions/workflows/%s/dispatches" % wf, {"ref": "main"})
        except Exception as e:
            print("  (could not check/start %s: %s)" % (wf, e))
    wf = area.get("keep_running")
    if wf:
        # GitHub skips many of the calendar's hourly starts, leaving it switched off for hours.
        # If it isn't running, start it; only complain if starting it didn't work.
        try:
            if is_running(wf):
                KICKED.pop(wf, None)
            elif wf in KICKED and (now_utc() - KICKED[wf]).total_seconds() > 1200:
                problems.append(("notrunning:" + wf, "The calendar job is not running, and starting it "
                                 "automatically at %s London didn't work" % london(KICKED[wf])))
            elif wf not in KICKED:
                print("  %s is not running: starting it" % wf)
                if not DRY:
                    api("POST", "/actions/workflows/%s/dispatches" % wf, {"ref": "main"})
                KICKED[wf] = now_utc()
        except Exception as e:
            print("  (could not check/start %s: %s)" % (wf, e))


# ---------------------------------------------------------------------------------------------
# Issues = the alerts.
# ---------------------------------------------------------------------------------------------
def marker(aid):
    return "<!-- site-alert:%s -->" % aid


def kinds_in(body):
    m = re.search(r"<!-- kinds:(.*?) -->", body or "", re.S)
    return set(json.loads(m.group(1))) if m else set()


def render(area, probs, first_seen):
    url = BASE + area.get("page", "")
    lines = [marker(area["id"]), "<!-- kinds:%s -->" % json.dumps(sorted({k for k, _ in probs})), "",
             "**%s** has a problem:" % area["name"], ""]
    lines += ["- " + t for _, t in probs]
    lines += ["", "Page: " + url, "First noticed: %s London" % first_seen, "",
              "This issue was opened by the site health check. It closes itself (and emails you) once "
              "the problem is gone. To look into it, open the page above or the job log, or ask Claude "
              "with a link to this issue."]
    return "\n".join(lines)


def open_issues():
    out = {}
    for i in api("GET", "/issues?labels=%s&state=open&per_page=100" % LABEL):
        m = re.search(r"<!-- site-alert:([\w-]+) -->", i.get("body") or "")
        if m:
            out[m.group(1)] = i
    return out


def ensure_label():
    try:
        api("POST", "/labels", {"name": LABEL, "color": "d73a4a",
                                "description": "Opened automatically by the site health check"}, ok=(422,))
    except Exception as e:
        print("  (label: %s)" % e)


def sync_issues(found, skip_close=()):
    """found: {area_id: (area, [(kind, text), ...])}"""
    if DRY and not TOKEN:
        print("  (no GitHub token: not looking at issues)")
        return
    existing = open_issues()
    stamp = london(now_utc())
    for aid, (area, probs) in found.items():
        issue = existing.get(aid)
        if not issue:
            title = "Site alert: %s - %s" % (area["name"], probs[0][1][:90])
            print("  OPEN issue: " + title)
            if not DRY:
                api("POST", "/issues", {"title": title, "body": render(area, probs, stamp),
                                        "labels": [LABEL], "assignees": [OWNER]})
            continue
        old_kinds = kinds_in(issue["body"])
        m = re.search(r"First noticed: (.*?) London", issue["body"] or "")
        body = render(area, probs, m.group(1) if m else stamp)
        new = [t for k, t in probs if k not in old_kinds]
        if new:
            print("  COMMENT on #%d: new problem(s)" % issue["number"])
            if not DRY:
                api("POST", "/issues/%d/comments" % issue["number"],
                    {"body": "New problem on top of the one(s) above:\n\n" + "\n".join("- " + t for t in new)})
        if body != issue["body"]:
            print("  update #%d (no email)" % issue["number"])
            if not DRY:
                api("PATCH", "/issues/%d" % issue["number"], {"body": body})
    for aid, issue in existing.items():
        if aid not in found and aid not in skip_close:
            print("  CLOSE #%d (%s is fine again)" % (issue["number"], aid))
            if not DRY:
                api("POST", "/issues/%d/comments" % issue["number"],
                    {"body": "All clear: the health check at %s London found no problems here any more, "
                             "so this is closed. It reopens as a new issue if it happens again." % stamp})
                api("PATCH", "/issues/%d" % issue["number"], {"state": "closed", "state_reason": "completed"})


# ---------------------------------------------------------------------------------------------
def run_once(browser, seen_before, seen_now):
    print("== Check at %s London (%s)" % (london(now_utc()), BASE))
    found = {}

    # 1. Is the site there at all? If the home page and most pages are down, send ONE alert.
    site_probs = []
    for f in SITE_FILES:
        st, body, err = http(live(f))
        if body is None:
            site_probs.append(("down:" + f, "Shared file %s (menu/glossary on every page) is not loading: %s" % (f, err)))
    down = []
    for a in AREAS:
        p = []
        if not page_check(a["page"], p):
            down.append((a, p))
    if len(down) * 2 >= len(AREAS):
        site_probs.append(("site-down", "%d of %d pages are not loading - the whole site looks down. "
                           "Example: %s" % (len(down), len(AREAS), down[0][1][0][1])))
        found["site"] = ({"id": "site", "name": "Whole website", "page": ""}, site_probs)
        print("  Site down: only the site-wide alert is sent this round")
        sync_issues(found, skip_close=[a["id"] for a in AREAS])
        return
    if site_probs:
        found["site"] = ({"id": "site", "name": "Whole website", "page": ""}, site_probs)
    down_ids = {a["id"]: p for a, p in down}

    # 2. Each part of the site.
    for a in AREAS:
        print("  checking %s ..." % a["id"])
        probs = list(down_ids.get(a["id"], []))
        if not probs:
            for extra in a.get("extra_pages", []):
                page_check(extra, probs)
        data_checks(a["id"], probs)
        if a["id"] == "home" and os.environ.get("TEST_ALERT") == "1":
            probs.append(("test", "TEST ALERT to check the emails reach you. Nothing is wrong; "
                                  "this closes itself on the next check."))
        job_checks(a, probs)
        if not probs:
            # Only open a browser when the page itself is up. A browser complaint must show up on
            # two checks in a row before it counts, so a page caught mid-update doesn't alert.
            for path in [a["page"]] + a.get("extra_pages", []):
                for t in browser.check(path):
                    key = "browser:" + path + ":" + re.sub(r"\d+", "N", t)[:80]
                    seen_now.add(key)
                    if key in seen_before:
                        probs.append((key, t))
                    else:
                        print("  (browser, will confirm on the next check) " + t)
        for k, t in probs:
            print("  [%s] %s" % (a["id"], t))
        if probs:
            found[a["id"]] = (a, probs)

    if not found:
        print("  All fine")
    sync_issues(found)


def main():
    loop_min = float(os.environ.get("LOOP_MINUTES", "0"))
    every = float(os.environ.get("EVERY_MINUTES", "15"))
    end = time.time() + loop_min * 60
    if DRY:
        print("DRY RUN: nothing will be changed on GitHub")
    if not DRY:
        ensure_label()
    browser = Browser()
    seen_browser = set()
    failures = 0
    try:
        while True:
            started = time.time()
            seen_now = set()
            try:
                run_once(browser, seen_browser, seen_now)
                failures = 0
            except Exception as e:
                failures += 1
                print("Check failed: %s" % e)
                if failures >= 3:
                    raise
            seen_browser = seen_now
            if time.time() + every * 60 > end:
                break
            time.sleep(max(0, every * 60 - (time.time() - started)))
    finally:
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
