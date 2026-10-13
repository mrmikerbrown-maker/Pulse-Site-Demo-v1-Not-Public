"""Builds data.json for the Fed scenario planner.
Fetches ~3y of daily history, then computes: latest vols, stock-bond regime,
betas per 10bp of 2yr move (all days / FOMC days), hit rates and an event bump."""
import io, json, datetime as dt
import numpy as np, pandas as pd, requests

UA = {"User-Agent": "Mozilla/5.0"}
YAHOO = {"eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X", "usdjpy": "JPY=X", "spx": "^GSPC",
         "gold": "GC=F", "vix": "^VIX", "gvz": "^GVZ", "move": "^MOVE"}
FRED = {"y2": "DGS2", "y10": "DGS10"}
# FOMC decision days (second day of each meeting). Check against the Fed's calendar.
FOMC = ["2023-11-01", "2023-12-13", "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18", "2025-01-29", "2025-03-19",
        "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16",
        "2026-10-28", "2026-12-09"]
ASSETS = ["eurusd", "gbpusd", "usdjpy", "spx", "gold", "y10"]


def get_yahoo(tk):
    r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
                     params={"range": "3y", "interval": "1d"}, headers=UA, timeout=30)
    r.raise_for_status()
    j = r.json()["chart"]["result"][0]
    s = pd.Series(j["indicators"]["quote"][0]["close"],
                  index=pd.to_datetime(j["timestamp"], unit="s").normalize(), dtype=float).dropna()
    return s[~s.index.duplicated(keep="last")]


def get_fred(sid):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                     params={"id": sid, "cosd": "2023-09-01"}, headers=UA, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["d", "v"]
    df["v"] = pd.to_numeric(df["v"], errors="coerce")
    df = df.dropna()
    return pd.Series(df["v"].values, index=pd.to_datetime(df["d"]))


def stats(y, x, mask, scale=10):
    """Slope per 10bp of 2yr move, R2, hit rate on |move|>=3bp, sample size."""
    yy, xx = y[mask], x[mask]
    if len(xx) < 15:
        return None
    b = float(np.polyfit(xx, yy, 1)[0])
    r2 = float(np.corrcoef(xx, yy)[0, 1] ** 2)
    big = np.abs(xx) >= 3
    hit = float(np.mean(np.sign(yy[big]) == np.sign(b) * np.sign(xx[big]))) if big.sum() >= 5 else None
    return {"b": round(b * scale, 3), "r2": round(r2, 3), "hit": None if hit is None else round(hit, 3), "n": int(len(xx))}


def compute(px, y2, y10):
    d = pd.DataFrame({k: px[k] for k in ["eurusd", "gbpusd", "usdjpy", "spx", "gold"]})
    d["y2"], d["y10"] = y2, y10
    d = d.dropna()
    r = pd.DataFrame(index=d.index)
    for k in ["eurusd", "gbpusd", "usdjpy", "spx", "gold"]:
        r[k] = np.log(d[k]).diff() * 100            # % move
    r["y2"] = d["y2"].diff() * 100                  # bp
    r["y10"] = d["y10"].diff() * 100                # bp
    r = r.dropna()
    fomc = r.index.isin(pd.to_datetime(FOMC))
    corr = r["spx"].rolling(60).corr(r["y2"])
    prior = corr.shift(1)                           # regime known before the day
    allm = np.ones(len(r), dtype=bool)
    x = r["y2"].values
    betas = {}
    for a in ASSETS:
        y = r[a].values
        betas[a] = {"all": stats(y, x, allm), "fomc": stats(y, x, fomc)}
    y = r["spx"].values
    betas["spx"]["rates"] = stats(y, x, (prior < 0).values)
    betas["spx"]["growth"] = stats(y, x, (prior >= 0).values)
    ratios = [r[c][fomc].std() / r[c][~fomc].std() for c in ["eurusd", "gbpusd", "usdjpy", "spx", "gold", "y2"]]
    bump = float(np.clip(np.nanmean(ratios), 1.1, 2.0)) if fomc.sum() >= 10 else 1.3
    real = {k: float(r[k].tail(20).std() * np.sqrt(252)) for k in ["eurusd", "gbpusd", "usdjpy"]}
    cur = float(corr.iloc[-1])
    return betas, bump, real, cur, str(r.index[-1].date())


def main():
    px = {k: get_yahoo(t) for k, t in YAHOO.items()}
    fr = {k: get_fred(s) for k, s in FRED.items()}
    betas, bump, real, cur, last = compute(px, fr["y2"], fr["y10"])
    today = dt.date.today().isoformat()
    nxt = next((x for x in FOMC if x >= today), None)
    out = {
        "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "history_last_date": last,
        "vols": {"vix": round(float(px["vix"].iloc[-1]), 2), "gvz": round(float(px["gvz"].iloc[-1]), 2),
                 "move": round(float(px["move"].iloc[-1]), 1),
                 "eurusd": round(real["eurusd"], 2), "gbpusd": round(real["gbpusd"], 2),
                 "usdjpy": round(real["usdjpy"], 2)},
        "vol_notes": {"fx": "20-day realised vol, annualised (not implied)"},
        "regime": {"name": "rates" if cur < 0 else "growth", "corr60": round(cur, 3)},
        "bump_fomc": round(bump, 2),
        "betas_per_10bp": betas,
        "next_event": {"date": nxt, "type": "FOMC decision"} if nxt else None,
    }
    with open("data.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
