#!/usr/bin/env python3
"""
Central bank tracker: daily data job.

Reads each G10 central bank's policy rate from free public sources, works out its last decision
and its next meeting (from the dates typed into config.json), and writes data.json.
The page (index.html) only draws what is in data.json.

Sources
  Fed (target range) and ECB (deposit facility rate): FRED (St. Louis Fed) daily CSV downloads
  Everyone else: Bank for International Settlements, central bank policy rates (daily). BIS can be a week
  or two behind, so where a bank publishes its own free feed we read that too and use whichever is newer.
  Meeting dates and announcement times: config.json, copied from each bank's published calendar

Standard library only. Run with --demo to test on made-up data (no internet needed).
"""
import csv
import datetime as dt
import io
import json
import math
import os
import random
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "data.json")
UA = "Mozilla/5.0 (compatible; central-bank-tracker/1.0)"
DEMO = "--demo" in sys.argv
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date()
START = CFG.get("history_start", "2019-01-01")
UTC = dt.timezone.utc


def http_get(url):
    last = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "*/*"}), timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("could not fetch %s (%s)" % (url, last))


# ----------------------------------------------------------------------------- made-up data for --demo

def demo_series(seed, level):
    rnd = random.Random(seed)
    d, v, out = dt.date.fromisoformat(START), level, []
    while d <= TODAY - dt.timedelta(days=2):
        if rnd.random() < 0.006:
            v = max(0.0, round(v + rnd.choice([-0.5, -0.25, 0.25, 0.5]), 2))
        out.append((d, v))
        d += dt.timedelta(days=1)
    return out


# ----------------------------------------------------------------------------- source readers

def fred_daily(series_id):
    if DEMO:
        return demo_series(series_id, 2.0)
    text = http_get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=%s" % (series_id, START))
    out = []
    for r in list(csv.reader(io.StringIO(text)))[1:]:
        try:
            v = float(r[1])
            if math.isfinite(v):
                out.append((dt.date.fromisoformat(r[0]), v))
        except (ValueError, IndexError):
            continue
    if not out:
        raise RuntimeError("FRED %s returned no data" % series_id)
    return sorted(out)


def bis_daily(areas):
    if DEMO:
        return {a: demo_series(a, 1.5) for a in areas}
    url = ("https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/D.%s?startPeriod=%s&format=csv"
           % ("+".join(areas), START))
    out = {}
    for r in csv.DictReader(io.StringIO(http_get(url))):
        try:
            v = float(r["OBS_VALUE"])
            if math.isfinite(v):
                out.setdefault(r["REF_AREA"], []).append((dt.date.fromisoformat(r["TIME_PERIOD"][:10]), v))
        except (KeyError, ValueError):
            continue
    if not out:
        raise RuntimeError("BIS returned no data")
    return {k: sorted(v) for k, v in out.items()}


# ----------------------------------------------------------------------------- banks' own feeds (faster than BIS)

def _rows(text):
    delim = ";" if text.count(";") > text.count(",") else ","
    return list(csv.reader(io.StringIO(text), delimiter=delim))


def _num(x):
    try:
        v = float(str(x).strip().replace('"', ""))
        return v if math.isfinite(v) else None
    except ValueError:
        return None


def _date(x, fmts=("%Y-%m-%d", "%d-%b-%Y", "%d %b %Y", "%d/%m/%Y")):
    x = str(x).strip().replace('"', "")
    for f in fmts:
        try:
            return dt.datetime.strptime(x, f).date()
        except ValueError:
            pass
    return None


def fill_daily(points):
    """Feeds that only list business days or change dates -> one value per calendar day up to today."""
    points = sorted(p for p in points if p[0] >= dt.date.fromisoformat(START))
    if not points:
        raise RuntimeError("no data")
    out, i, d, v = [], 0, points[0][0], points[0][1]
    last_day = points[-1][0]
    while d <= last_day:
        while i < len(points) and points[i][0] <= d:
            v = points[i][1]
            i += 1
        out.append((d, v))
        d += dt.timedelta(days=1)
    return out


def own_boc():
    t = http_get("https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=%s" % START)
    obs = json.loads(t)["observations"]
    return [(dt.date.fromisoformat(o["d"]), float(o["V39079"]["v"])) for o in obs if o.get("V39079", {}).get("v")]


def own_rba():
    pts = []
    for r in _rows(http_get("https://www.rba.gov.au/statistics/tables/csv/f1-data.csv")):
        if len(r) > 1:
            d, v = _date(r[0]), _num(r[1])
            if d and v is not None:
                pts.append((d, v))
    return pts


def own_norges():
    t = http_get("https://data.norges-bank.no/api/data/IR/B.KPRA.SD.?format=csv&startPeriod=%s&locale=en" % START)
    rows = _rows(t)
    h = rows[0]
    di, vi = h.index("TIME_PERIOD"), h.index("OBS_VALUE")
    return [(_date(r[di]), _num(r[vi])) for r in rows[1:] if len(r) > vi and _date(r[di]) and _num(r[vi]) is not None]


def own_riksbank():
    obs = json.loads(http_get("https://api.riksbank.se/swea/v1/Observations/SECBREPOEFF/%s" % START))
    return [(dt.date.fromisoformat(o["date"]), float(o["value"])) for o in obs if o.get("value") is not None]


def own_boe():
    url = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes"
           "&Datefrom=01/Jan/2019&Dateto=now&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
    pts = []
    for r in _rows(http_get(url)):
        if len(r) > 1:
            d, v = _date(r[0]), _num(r[1])
            if d and v is not None:
                pts.append((d, v))
    return pts


def own_snb():
    pts = []
    for r in _rows(http_get("https://data.snb.ch/api/cube/snbgwdzid/data/csv/en")):
        if len(r) >= 3 and r[1].strip().strip('"') == "LZ":
            d, v = _date(r[0]), _num(r[2])
            if d and v is not None:
                pts.append((d, v))
    return pts


OWN = {"CAD": own_boc, "AUD": own_rba, "NOK": own_norges, "SEK": own_riksbank, "GBP": own_boe, "CHF": own_snb}


# ----------------------------------------------------------------------------- working out the readings

def to_utc(day, hhmm, tz):
    h, m = (int(x) for x in hhmm.split(":"))
    d = dt.date.fromisoformat(day)
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ZoneInfo(tz)).astimezone(UTC)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def changes(series):
    """[(date, old, new)] for every day the rate moved."""
    out = []
    for (d0, v0), (d1, v1) in zip(series, series[1:]):
        if round(v1 - v0, 4) != 0:
            out.append((d1, v0, v1))
    return out


def steps(series):
    """The rate at the start, at every change and at the end: enough to draw a step chart."""
    pts = [(series[0][0], series[0][1])] + [(d, new) for d, _, new in changes(series)] + [series[-1]]
    return [[d.isoformat(), round(v, 4)] for d, v in pts]


def bank_block(b, series, lower=None):
    meetings = [(to_utc(d, b["time"], b["tz"]), d) for d in b["meetings"]]
    meetings.sort()
    asof = series[-1][0]
    moves = changes(series)
    lag = b.get("effective_lag_days", 1)
    past = [m for m in meetings if m[0] <= NOW]
    future = [m for m in meetings if m[0] > NOW]

    last = None
    if past:
        mt, mday = past[-1]
        md = dt.date.fromisoformat(mday)
        hit = [c for c in moves if md - dt.timedelta(days=1) <= c[0] <= md + dt.timedelta(days=lag + 3)]
        if hit:
            c = hit[-1]
            bp = int(round((c[2] - c[1]) * 100))
            last = {"date": mday, "bp": bp, "kind": "hike" if bp > 0 else "cut"}
        elif asof >= md + dt.timedelta(days=lag):
            last = {"date": mday, "bp": 0, "kind": "hold"}
        else:
            last = {"date": mday, "bp": None, "kind": "pending"}
    # a move away from any scheduled meeting (an emergency cut, say) beats the meeting
    if moves:
        c = moves[-1]
        if last is None or c[0] > dt.date.fromisoformat(last["date"]) + dt.timedelta(days=lag + 3):
            bp = int(round((c[2] - c[1]) * 100))
            last = {"date": c[0].isoformat(), "bp": bp, "kind": "hike" if bp > 0 else "cut"}
            first = dt.date.fromisoformat(meetings[0][1]) if meetings else None
            if first and c[0] > first:
                last["unscheduled"] = True  # moved between scheduled meetings, e.g. an emergency cut
    # if the data hasn't caught up with a pending decision, show the latest decision it does show
    prev = None
    if last and last["kind"] == "pending" and len(past) > 1:
        pd_ = dt.date.fromisoformat(past[-2][1])
        hit = [c for c in moves if pd_ - dt.timedelta(days=1) <= c[0] <= pd_ + dt.timedelta(days=lag + 3)]
        bp = int(round((hit[-1][2] - hit[-1][1]) * 100)) if hit else 0
        prev = {"date": past[-2][1], "bp": bp, "kind": "hike" if bp > 0 else "cut" if bp < 0 else "hold"}

    out = {
        "code": b["code"], "short": b["short"], "name": b["name"], "rate_name": b.get("rate_name", ""),
        "rate": round(series[-1][1], 4), "asof": asof.isoformat(),
        "last": last, "prev": prev,
        "next": {"utc": iso(future[0][0]), "approx": b.get("approx", False)} if future else None,
        "upcoming": [iso(t) for t, _ in future[:6]],
        "steps": steps(series),
        "last_meeting_on_file": meetings[-1][1] if meetings else None,
    }
    if lower is not None:
        out["lower"] = round(lower[-1][1], 4)
    return out


def main():
    log, banks = [], []
    try:
        old = {b["code"]: b for b in json.load(open(OUT, encoding="utf-8")).get("banks", [])}
    except (OSError, ValueError):
        old = {}
    bis = {}
    areas = [b["bis"] for b in CFG["banks"] if "bis" in b]
    try:
        bis = bis_daily(areas)
        log.append("OK   BIS policy rates (%s)" % ", ".join(sorted(bis)))
    except Exception as e:  # noqa: keep going, older figures are reused below
        log.append("FAIL BIS policy rates: %s" % e)
    for b in CFG["banks"]:
        try:
            lower = None
            if "fred" in b:
                series = fred_daily(b["fred"])
                if "fred_lower" in b:
                    lower = fred_daily(b["fred_lower"])
                src = "FRED " + b["fred"]
            else:
                if b["bis"] in bis:
                    series, src = bis[b["bis"]], "BIS " + b["bis"]
                elif b["code"] in OWN and not DEMO:
                    series, src = [(dt.date.fromisoformat(START), 0.0)], "none"
                else:
                    raise RuntimeError("no BIS data for %s" % b["bis"])
            if b["code"] in OWN and not DEMO:
                try:
                    own = fill_daily(OWN[b["code"]]())
                    log.append("OK   %-4s own feed: %s%% as of %s" % (b["code"], own[-1][1], own[-1][0]))
                    if own[-1][0] > series[-1][0]:
                        # bank's own feed is newer: use it from where it starts, BIS before that
                        series = [p for p in series if p[0] < own[0][0]] + own
                        src = "own feed"
                except Exception as e:  # noqa: BIS figures still stand
                    log.append("WARN %-4s own feed failed, using BIS: %s" % (b["code"], e))
            if src == "none":
                raise RuntimeError("no BIS data and own feed failed")
            block = bank_block(b, series, lower)
            block["source"] = src
            banks.append(block)
            log.append("OK   %-4s %-9s %s%% as of %s (%s), last: %s" % (
                b["code"], b["short"], block["rate"], block["asof"], src, block["last"]))
        except Exception as e:  # noqa
            log.append("FAIL %s: %s" % (b["code"], e))
            if b["code"] in old:
                ob = dict(old[b["code"]], stale=True)
                banks.append(ob)
                log.append("     %s: kept yesterday's figures" % b["code"])
        if banks and banks[-1]["code"] == b["code"]:
            lf = banks[-1].get("last_meeting_on_file")
            if lf and dt.date.fromisoformat(lf) < TODAY + dt.timedelta(days=60):
                log.append("NOTE %s: meeting dates in config.json run out on %s, add the next year's" % (b["code"], lf))

    data = {"generated": iso(NOW), "demo": DEMO, "history_start": START, "banks": banks, "log": log}
    if not banks:
        print("\n".join(log))
        sys.exit("Nothing fetched; data.json left as it was")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("\n".join(log))
    if any(l.startswith("FAIL") for l in log):
        print("::warning::Some sources failed, see the log above")


if __name__ == "__main__":
    main()
