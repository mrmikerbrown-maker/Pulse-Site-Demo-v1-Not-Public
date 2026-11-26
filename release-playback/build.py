"""Release Playback: nightly data build. Writes data.json for index.html.

Steps (each one keeps going if another fails, and the last good files stay in place):
1. Releases and forecasts: TradingView economic calendar (US). releases.json holds every release since Jan 2015;
   each run fetches the last ~45 days again and adds or updates them.
2. Actual figures: as FIRST ANNOUNCED, from FRED's ALFRED archive (fred_first_print.py, needs the FRED_API_KEY
   secret; cached in first-print.csv). TradingView overwrites past actuals with later revisions, so its number is
   only used when FRED has none (ISM Services, which is not on FRED, or a run without the key).
3. Daily closes: TradingView chart data, ~3000 days, for S&P 500 futures (front month, roll gaps taken out),
   US 10-year yield, US dollar index and gold.
4. Release-day replays: 5-minute prices from 60 min before to 8 hours after each release. The free feed only keeps
   about a month of 5-minute bars, so each release is saved into replays.json once its day is over and kept for good.

For every release:
  g    = "above" / "inline" / "below": first-announced actual vs forecast (in line = within the band per release).
  m[k] = market k's move from the last close BEFORE the release to each of the next 10 closes (day 1 = release day).
         % for S&P futures, dollar index and gold; basis points for the 10-year yield."""
import datetime as dt, json, os, random, re, string, sys, time
import requests
from fred_first_print import first_prints

HERE = os.path.dirname(os.path.abspath(__file__))
def path_(f): return os.path.join(HERE, f)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
NOW = dt.datetime.now(dt.timezone.utc)

MARKETS = {  # key: TradingView ticker, names, unit, "too small to call" size of a day-1 move (about a third of a typical day)
    "es":   {"tv": "CME_MINI:ES1!", "name": "S&P 500 futures", "short": "S&P 500", "u": "%",  "min": 0.4},
    "y10":  {"tv": "TVC:US10Y", "name": "US 10-year yield", "short": "US 10y", "u": "bp", "min": 2.0},
    "dxy":  {"tv": "TVC:DXY", "name": "US dollar index", "short": "Dollar", "u": "%",  "min": 0.15},
    "gold": {"tv": "TVC:GOLD", "name": "Gold", "short": "Gold", "u": "%", "min": 0.4},
}
RELEASES = [  # key, TradingView calendar title, button, title, what it measures, in-line band, unit, decimals
    ("cpi", "Core Inflation Rate MoM", "CPI", "US inflation (core CPI)", "Core CPI, month on month: how fast prices rose last month, leaving out food and energy. Markets trade this figure more than the yearly headline.", 0, "%", 1),
    ("nfp", "Non Farm Payrolls", "Jobs", "Jobs report (nonfarm payrolls)", "How many jobs the US added last month, not counting farm work.", 20, "k", 0),
    ("pce", "Core PCE Price Index MoM", "Core PCE", "Core PCE inflation", "The Fed's preferred inflation measure, month on month, leaving out food and energy.", 0, "%", 1),
    ("rs", "Retail Sales MoM", "Retail sales", "Retail sales", "How much shoppers spent last month compared with the month before.", 0, "%", 1),
    ("ism", "ISM Services PMI", "ISM Services", "ISM Services PMI", "A survey of service-company managers. Above 50 means activity is growing.", 0.5, " pts", 1),
    ("gdp", "GDP Growth Rate QoQ Adv", "GDP", "GDP (first estimate)", "How fast the economy grew last quarter, as a yearly rate. First estimate, revised later.", 0.2, "%", 1),
]
NAMES = {r[1] for r in RELEASES}
problems = []

# ---------- 1. releases and forecasts ----------
def update_calendar():
    ev = json.load(open(path_("releases.json")))
    byk = {(e["name"], e["t"]): e for e in ev}
    a, b = NOW - dt.timedelta(days=45), NOW + dt.timedelta(days=1)
    u = ("https://economic-calendar.tradingview.com/events?from=%s&to=%s&countries=US&minImportance=0"
         % (a.strftime("%Y-%m-%dT00:00:00.000Z"), b.strftime("%Y-%m-%dT00:00:00.000Z")))
    r = requests.get(u, headers={"User-Agent": UA, "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"}, timeout=40)
    js = r.json()
    if js.get("status") != "ok":
        raise RuntimeError("TradingView calendar status %r" % js.get("status"))
    n = 0
    for e in js.get("result", []):
        t = (e.get("title") or "").strip()
        if t in NAMES and e.get("actual") is not None:
            k = (t, e["date"][:16] + "Z")
            old = byk.get(k)
            byk[k] = {"t": k[1], "name": t, "period": e.get("period"), "actual": e.get("actual"),
                      "forecast": e.get("forecast") if e.get("forecast") is not None else (old or {}).get("forecast"),
                      "previous": e.get("previous"), "unit": e.get("unit"), "scale": e.get("scale")}
            n += old is None
    ev = sorted(byk.values(), key=lambda e: e["t"])
    json.dump(ev, open(path_("releases.json"), "w"), separators=(",", ":"))
    print("calendar: %d releases, %d new" % (len(ev), n))
    return ev

# ---------- prices from TradingView's chart service ----------
def _m(f, p):
    s = json.dumps({"m": f, "p": p}, separators=(",", ":"))
    return "~m~%d~m~%s" % (len(s), s)

def bars(ticker, n, res, wait=60):
    from websocket import create_connection
    ws = create_connection("wss://data.tradingview.com/socket.io/websocket", header=["Origin: https://www.tradingview.com"], timeout=30)
    cs = "cs_" + "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    sym = {"symbol": ticker, "adjustment": "splits"}
    if ticker.endswith("!"):
        sym["backadjustment"] = "default"
    for m in [_m("set_auth_token", ["unauthorized_user_token"]), _m("chart_create_session", [cs, ""]),
              _m("resolve_symbol", [cs, "sym1", "=" + json.dumps(sym)]), _m("create_series", [cs, "s1", "s1", "sym1", res, n, ""])]:
        ws.send(m)
    buf, t0 = "", time.time()
    try:
        while time.time() - t0 < wait:
            r = ws.recv()
            if re.match(r"~m~\d+~m~~h~", r):
                ws.send(r); continue
            buf += r
            if "series_completed" in r or "symbol_error" in r or "series_error" in r:
                break
    finally:
        ws.close()
    out = {}
    for v in re.findall(r'"v":\[([^\]]+)\]', buf):
        x = v.split(",")
        out[int(float(x[0]))] = float(x[4])
    return out

def sdate(t):  # trading session a daily bar belongs to (futures and FX bars open the evening before)
    return (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=6)).date().isoformat()

def move(k, a, b):
    return round((b - a) * 100, 1) if MARKETS[k]["u"] == "bp" else round((b / a - 1) * 100, 3)

# ---------- main ----------
try:
    cal = update_calendar()
except Exception as e:
    problems.append("Release calendar could not be updated: %s" % e)
    cal = json.load(open(path_("releases.json")))

D = {}
for k, m in MARKETS.items():
    try:
        b = bars(m["tv"], 3000, "1D")
        if len(b) < 500:
            raise RuntimeError("only %d daily bars" % len(b))
        dm = {sdate(t): c for t, c in sorted(b.items())}
        ds = sorted(dm)
        D[k] = (ds, {d: i for i, d in enumerate(ds)}, [dm[d] for d in ds])
    except Exception as e:
        problems.append("Daily prices failed for %s: %s" % (m["name"], e))
if len(D) < len(MARKETS):
    print("PROBLEMS:", problems)
    sys.exit(1)  # keep yesterday's data.json rather than publish one with a market missing

def path10(k, day):
    ds, ix, cl = D[k]
    i = ix.get(day)
    if i is None or i == 0:
        return None
    return [move(k, cl[i - 1], cl[j]) for j in range(i, min(i + 10, len(cl)))]

# release-day replays: add any finished release inside the 5-minute window that isn't saved yet
reps = json.load(open(path_("replays.json"))) if os.path.exists(path_("replays.json")) else {}
key_of = {r[1]: r[0] for r in RELEASES}
todo = []
for e in cal:
    t0 = int(dt.datetime.strptime(e["t"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc).timestamp())
    rk = key_of[e["name"]] + "|" + e["t"][:10]
    if rk not in reps and NOW.timestamp() - t0 > 9 * 3600 and NOW.timestamp() - t0 < 28 * 86400:
        todo.append((rk, t0))
if todo:
    I5 = {}
    for k, m in MARKETS.items():
        try:
            I5[k] = bars(m["tv"], 8000, "5", wait=90)
        except Exception as e:
            problems.append("5-minute prices failed for %s: %s" % (m["name"], e))
    for rk, t0 in todo:
        rep = {}
        for k in MARKETS:
            b = I5.get(k) or {}
            prev = [t for t in b if t < t0]
            if not b or min(b) > t0 - 3600 or not prev or t0 - max(prev) > 1800:
                rep = None; break
            base = b[t0 - 300] if (t0 - 300) in b else b[max(prev)]
            rep[k] = [None if b.get(t - 300) is None else move(k, base, b[t - 300]) for t in range(t0 - 3600, t0 + 8 * 3600 + 1, 300)]
        if rep:
            reps[rk] = rep
            print("saved replay", rk)
    json.dump(reps, open(path_("replays.json"), "w"), separators=(",", ":"))

FP = first_prints([(key_of[e["name"]], e["t"][:10]) for e in cal if e["name"] in key_of])
from fred_first_print import SERIES as FRED_SERIES
missing = [kd for kd in ((key_of[e["name"]], e["t"][:10]) for e in cal) if kd[0] in FRED_SERIES and kd not in FP]
if missing:
    problems.append("No first-announced figure from FRED for %d release(s), e.g. %s %s%s" % (
        len(missing), missing[-1][0], missing[-1][1], "" if os.environ.get("FRED_API_KEY") else ": the FRED_API_KEY secret is missing"))

rels = {}
for key, name, tab, title, what, band, unit, dec in RELEASES:
    rows = []
    for e in cal:
        if e["name"] != name or e["actual"] is None or e["forecast"] is None:
            continue
        tv, f = e["actual"], e["forecast"]
        fp = FP.get((key, e["t"][:10]))
        a = tv if fp is None else (round(fp, dec) if dec else round(fp))
        diff = round(a - f, 3)
        g = "inline" if abs(diff) <= band + 1e-9 else ("above" if diff > 0 else "below")
        day = e["t"][:10]
        row = {"d": day, "t": e["t"][11:16], "p": (e.get("period") or "").replace(".", ""), "a": a, "f": f, "g": g,
               "m": {k: path10(k, day) for k in MARKETS}}
        if fp is not None and abs(a - tv) > 1e-6:
            row["tv"] = tv  # TradingView's later (revised) figure, shown on hover
        if (key + "|" + day) in reps:
            row["r"] = 1
        rows.append(row)
    rows.sort(key=lambda r: r["d"], reverse=True)
    rels[key] = {"tab": tab, "title": title, "what": what, "band": band, "u": unit, "dec": dec, "rows": rows}

first5 = min([k.split("|")[1] for k in reps] or ["2026-10-27"])
out = {"asof": NOW.strftime("%Y-%m-%dT%H:%MZ"), "generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "markets": {k: {x: v for x, v in m.items() if x != "tv"} for k, m in MARKETS.items()},
       "releases": rels, "replays": reps, "intraday_from": first5, "problems": problems}
json.dump(out, open(path_("data.json"), "w"), separators=(",", ":"))
print({k: len(v["rows"]) for k, v in rels.items()}, "replays:", len(reps), "problems:", problems)
