"""Cross-Asset Moves: writes data.json for the page.

  python build.py            (uses the feed named in FEED below, or env CROSS_ASSET_FEED)

1. markets.csv lists every market: group, name, unit (pct = % move, bp = yield move in basis points, pt = points)
   and its ticker for each feed (one column per feed, named after the module in feeds/).
2. The feed gives today's price and changes.
3. Once a day the "typical move" for each market is worked out from a year of daily closes:
   the standard deviation of its daily changes over the last 252 trading days. Saved in typical.json.
4. data.json gets one row per market with its move for Today / 1 week / 1 month / YTD, in the market's own unit.
The page divides each move by the typical move (scaled by the square root of the days in the period).
"""
import csv, datetime as dt, importlib, json, math, os, statistics, sys, time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FEED = os.environ.get("CROSS_ASSET_FEED", "tradingview")
LDN = ZoneInfo("Europe/London")
# Continuous futures (tickers ending "!", e.g. ES1!) jump when the front contract rolls, so the feed's own
# 1 week / 1 month / YTD changes are worked out again from back-adjusted daily closes (see futures_perf).
# Cash-market hours (local time) used for the "Open" / "Closed 16:30" / "Tue close" label under stock indices.
SESSIONS = {"us": ("America/New_York", (9, 30), (16, 0)), "uk": ("Europe/London", (8, 0), (16, 30)),
            "eu": ("Europe/Berlin", (9, 0), (17, 30)), "jp": ("Asia/Tokyo", (9, 0), (15, 30)),
            "hk": ("Asia/Hong_Kong", (9, 30), (16, 0))}
DAYNAME = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def status(sess, now):
    if sess not in SESSIONS:
        return ""
    tz, o, c = SESSIONS[sess]
    loc = now.astimezone(ZoneInfo(tz))
    op = loc.replace(hour=o[0], minute=o[1], second=0, microsecond=0)
    cl = loc.replace(hour=c[0], minute=c[1], second=0, microsecond=0)
    if loc.weekday() < 5 and op <= loc < cl:
        return "Open"
    if loc.weekday() < 5 and loc >= cl:
        return "Closed " + cl.astimezone(LDN).strftime("%H:%M")
    d = loc.date() - dt.timedelta(days=1)          # before today's open, or weekend: last weekday's close
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return DAYNAME[d.weekday()] + " close"


def daily_changes(bars, unit):
    cl = [c for _, c in bars]
    if unit == "pct":
        return [(b / a - 1) * 100 for a, b in zip(cl, cl[1:]) if a]
    if unit == "bp":
        return [(b - a) * 100 for a, b in zip(cl, cl[1:])]
    return [b - a for a, b in zip(cl, cl[1:])]


def refresh_typical(feed, markets, today):
    path = os.path.join(HERE, "typical.json")
    try:
        old = json.load(open(path))
    except Exception:
        old = {"date": "", "sd": {}}
    if old.get("date") == today and len(old.get("sd", {})) >= len(markets):
        return old
    sd, ytd_days = dict(old.get("sd", {})), old.get("ytd_days", 0)
    for m in markets:
        try:
            bars = feed.history(m[FEED], 300)
            ch = daily_changes(bars[:-1], m["unit"])[-252:]  # leave out today's unfinished bar
            if len(ch) >= 120:
                sd[m["id"]] = round(statistics.stdev(ch), 4)
            if m["id"] == "dxy":   # trades every weekday, so its bar count = trading days so far this year
                year = dt.datetime.now(LDN).year
                ytd_days = sum(1 for t, _ in bars if dt.datetime.fromtimestamp(t, LDN).year == year)
        except Exception as e:
            print("history failed for", m["id"], e)
        time.sleep(0.3)
    new = {"date": today, "ytd_days": ytd_days, "sd": sd}
    json.dump(new, open(path, "w"), indent=0)
    return new


def futures_perf(feed, ticker, price):
    """% change over 1 week / 1 month / YTD for a continuous future, from back-adjusted closes.
    The last bar is the current session, so 1 week = vs the close 5 sessions earlier, 1 month = 21 sessions."""
    bars = feed.history(ticker, 300)
    if len(bars) < 30:
        return None
    year = dt.datetime.now(LDN).year
    prev = [c for t, c in bars if dt.datetime.fromtimestamp(t, LDN).year < year]
    pct = lambda ref: (price / ref - 1) * 100 if ref else None
    return pct(bars[-6][1]), pct(bars[-22][1]), pct(prev[-1] if prev else None)


def bp_from_perf(price, perf):
    """Yield move in bp from a % change in the yield (feeds quote yield changes as % of the yield)."""
    if perf is None:
        return None
    return (price - price / (1 + perf / 100)) * 100


def main():
    feed = importlib.import_module("feeds." + FEED)
    markets = list(csv.DictReader(open(os.path.join(HERE, "markets.csv"), encoding="utf-8")))
    now = dt.datetime.now(dt.timezone.utc)
    typ = refresh_typical(feed, markets, now.astimezone(LDN).date().isoformat())
    q = feed.quotes([m[FEED] for m in markets])
    rows, missing = [], []
    for m in markets:
        x = q.get(m[FEED])
        if not x:
            missing.append(m["name"])
            continue
        p, u = x["price"], m["unit"]
        if m[FEED].endswith("!"):
            try:
                fp = futures_perf(feed, m[FEED], p)
                if fp:
                    x["perf_w"], x["perf_m"], x["perf_ytd"] = fp
            except Exception as e:
                print("futures history failed for", m["id"], e)
        if u == "pct":
            mv = [x["chg_pct"], x["perf_w"], x["perf_m"], x["perf_ytd"]]
        elif u == "bp":
            mv = [x["chg_abs"] * 100 if x["chg_abs"] is not None else None] + [bp_from_perf(p, x[k]) for k in ("perf_w", "perf_m", "perf_ytd")]
        else:
            mv = [x["chg_abs"]] + [(p - p / (1 + x[k] / 100)) if x[k] is not None else None for k in ("perf_w", "perf_m", "perf_ytd")]
        rows.append({"id": m["id"], "g": m["group"], "n": m["name"], "s": m["sub"], "u": u, "p": p,
                     "mv": [round(v, 4) if v is not None else None for v in mv],
                     "sd": typ["sd"].get(m["id"]), "st": status(m["session"], now)})
    if len(rows) < len(markets) / 2:
        sys.exit("Too few prices came back (%d of %d); keeping the last data.json" % (len(rows), len(markets)))
    out = {"asof": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "feed": feed.NAME, "typical_date": typ["date"],
           "ytd_days": typ.get("ytd_days") or 228, "missing": missing, "rows": rows}
    json.dump(out, open(os.path.join(HERE, "data.json"), "w"), separators=(",", ":"))
    print("Saved %d markets%s" % (len(rows), (", missing: " + ", ".join(missing)) if missing else ""))


if __name__ == "__main__":
    main()
