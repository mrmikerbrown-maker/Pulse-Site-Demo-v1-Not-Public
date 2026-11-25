"""Sketch builder for the Release Playback page. Reads the probe output (TradingView calendar + prices,
fetched from GitHub Actions) and writes data.json for index.html.

For every past release:
  group   = "above" / "inline" / "below": actual vs forecast. In line = within the band set per release below.
  path    = the market's move from the last close BEFORE the release to each of the next 10 closes
            (day 1 = close on release day). % for S&P futures, dollar index and gold; basis points for the 10y yield.
Intraday replays (5-minute bars, zeroed at the release time) only exist for releases inside the
data feed's 5-minute window (about the last month). Going forward the job would save each one as it happens."""
import json, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "probe", "out")
cal = json.load(open(os.path.join(P, "calendar.json")))
daily = json.load(open(os.path.join(P, "daily.json")))
intra = json.load(open(os.path.join(P, "intraday.json")))

MARKETS = {  # key: name, unit, "too small to call" size of day-1 move
    "es":   {"name": "S&P 500 futures", "short": "S&P 500", "u": "%",  "min": 0.4},
    "y10":  {"name": "US 10-year yield", "short": "US 10y", "u": "bp", "min": 2.0},
    "dxy":  {"name": "US dollar index", "short": "Dollar", "u": "%",  "min": 0.15},
    "gold": {"name": "Gold", "short": "Gold", "u": "%", "min": 0.4},
}
RELEASES = [  # key, calendar name, tab, title, what it measures, in-line band, unit, decimals
    ("cpi", "Core Inflation Rate MoM", "CPI", "US inflation (core CPI)", "Core CPI, month on month: how fast prices rose last month, leaving out food and energy. Markets trade this figure more than the yearly headline.", 0, "%", 1),
    ("nfp", "Non Farm Payrolls", "Jobs", "Jobs report (nonfarm payrolls)", "How many jobs the US added last month, not counting farm work.", 20, "k", 0),
    ("pce", "Core PCE Price Index MoM", "Core PCE", "Core PCE inflation", "The Fed's preferred inflation measure, month on month, leaving out food and energy.", 0, "%", 1),
    ("rs", "Retail Sales MoM", "Retail sales", "Retail sales", "How much shoppers spent last month compared with the month before.", 0, "%", 1),
    ("ism", "ISM Services PMI", "ISM Services", "ISM Services PMI", "A survey of service-company managers. Above 50 means activity is growing.", 0.5, " pts", 1),
    ("gdp", "GDP Growth Rate QoQ Adv", "GDP", "GDP (first estimate)", "How fast the economy grew last quarter, as a yearly rate. First estimate, revised later.", 0.2, "%", 1),
]

def sdate(t):  # trading session a daily bar belongs to (futures/FX bars open the evening before)
    return (dt.datetime.utcfromtimestamp(t) + dt.timedelta(hours=6)).date().isoformat()

D = {}
for k in MARKETS:
    m = {}
    for t, c in daily[k]:
        m[sdate(t)] = c
    ds = sorted(m)
    D[k] = (ds, {d: i for i, d in enumerate(ds)}, [m[d] for d in ds])

def move(k, a, b):
    return round((b - a) * 100, 1) if MARKETS[k]["u"] == "bp" else round((b / a - 1) * 100, 3)

def path(k, day):
    ds, ix, cl = D[k]
    i = ix.get(day)
    if i is None or i == 0:
        return None
    base = cl[i - 1]
    return [move(k, base, cl[j]) for j in range(i, min(i + 10, len(cl)))]

# intraday: 5-minute closes, zeroed at the bar ending at the release
I5 = {k: {int(t): c for t, c in intra.get(k + "_5", [])} for k in MARKETS}
first5 = max(min(v) for v in I5.values() if v)

def replay(t0):
    out, start = {}, t0 - 3600
    for k in MARKETS:
        b = I5[k]
        base = b.get(t0 - 300)
        if base is None:
            prev = [t for t in b if t < t0]
            if not prev or t0 - max(prev) > 1800:
                return None
            base = b[max(prev)]
        s = []
        for t in range(start, t0 + 8 * 3600 + 1, 300):
            c = b.get(t - 300)  # close of the bar that ends at t
            s.append(None if c is None else move(k, base, c))
        out[k] = s
    return out

rels, reps = {}, {}
for key, name, tab, title, what, band, unit, dec in RELEASES:
    rows = []
    for e in cal:
        if e["name"] != name or e["actual"] is None or e["forecast"] is None:
            continue
        a, f = e["actual"], e["forecast"]
        diff = round(a - f, 3)
        g = "inline" if abs(diff) <= band + 1e-9 else ("above" if diff > 0 else "below")
        day = e["t"][:10]
        ps = {k: path(k, day) for k in MARKETS}
        t0 = int(dt.datetime.strptime(e["t"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc).timestamp())
        per = (e.get("period") or "").replace(".", "")
        row = {"d": day, "t": e["t"][11:16], "p": per, "a": a, "f": f, "g": g, "m": ps}
        if t0 >= first5 + 3600:
            r = replay(t0)
            if r:
                reps[key + "|" + day] = r
                row["r"] = 1
        rows.append(row)
    rows.sort(key=lambda r: r["d"], reverse=True)
    rels[key] = {"tab": tab, "title": title, "what": what, "band": band, "u": unit, "dec": dec, "rows": rows}

out = {"asof": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "markets": MARKETS, "releases": rels, "replays": reps,
       "intraday_from": dt.datetime.utcfromtimestamp(first5).strftime("%Y-%m-%d")}
json.dump(out, open(os.path.join(HERE, "data.json"), "w"), separators=(",", ":"))
print({k: len(v["rows"]) for k, v in rels.items()}, "replays:", list(reps), "size", os.path.getsize(os.path.join(HERE, "data.json")))
