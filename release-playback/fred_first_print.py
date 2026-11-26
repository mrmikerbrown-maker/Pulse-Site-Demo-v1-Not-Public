"""First-announced numbers from FRED's ALFRED archive (needs FRED_API_KEY, a free key, kept as a GitHub secret).

TradingView's calendar overwrites past 'actual' values with later revisions (Sept 2026 payrolls: 29k announced,
60k shown later). ALFRED keeps every vintage of each series, so asking for the data "as it was known on release day"
gives the number that was actually announced. Results are cached in first-print.csv so each release is fetched once.
  nfp: change in PAYEMS (thousands)          rs:  % change in RSAFS
  cpi: % change in CPILFESL (core CPI)       pce: % change in PCEPILFE (core PCE)
  gdp: A191RL1Q225SBEA (annualised real GDP growth, advance estimate)"""
import csv, json, os, time, requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "first-print.csv")
API = "https://api.stlouisfed.org/fred/series/observations"
SERIES = {"nfp": ("PAYEMS", "diff"), "rs": ("RSAFS", "pct"), "cpi": ("CPILFESL", "pct"), "pce": ("PCEPILFE", "pct"),
          "gdp": ("A191RL1Q225SBEA", "level")}

def load():
    if not os.path.exists(CACHE):
        return {}
    return {(r["k"], r["d"]): r for r in csv.DictReader(open(CACHE))}

def save(c):
    rows = sorted(c.values(), key=lambda r: (r["k"], r["d"]))
    with open(CACHE, "w", newline="") as f:
        w = csv.DictWriter(f, ["k", "d", "ref", "first"]); w.writeheader(); w.writerows(rows)

def fetch(k, day, key):
    sid, how = SERIES[k]
    y, m = int(day[:4]), int(day[5:7])
    start = "%04d-%02d-01" % (y - 1, m)
    r = requests.get(API, params={"series_id": sid, "api_key": key, "file_type": "json", "observation_start": start,
                                  "realtime_start": day, "realtime_end": day}, timeout=30)
    r.raise_for_status()
    ob = [(o["date"], o["value"]) for o in r.json()["observations"] if o["value"] not in (".", "")]
    if len(ob) < 2:
        return None
    (d0, v0), (d1, v1) = ob[-2], ob[-1]
    v0, v1 = float(v0), float(v1)
    val = v1 if how == "level" else round(v1 - v0) if how == "diff" else round((v1 / v0 - 1) * 100, 1)
    return {"k": k, "d": day, "ref": d1, "first": val}

def first_prints(wanted):
    """wanted: list of (release key, release date YYYY-MM-DD). Returns {(k, d): value or None}."""
    key = os.environ.get("FRED_API_KEY", "")
    c = load()
    if key:
        for k, d in wanted:
            if k in SERIES and (k, d) not in c:
                try:
                    got = fetch(k, d, key)
                except Exception as e:
                    print("FRED failed", k, d, e); got = None
                if got:
                    c[(k, d)] = got
                time.sleep(0.55)  # FRED allows 120 calls a minute
        save(c)
    return {kd: float(r["first"]) for kd, r in c.items()}
