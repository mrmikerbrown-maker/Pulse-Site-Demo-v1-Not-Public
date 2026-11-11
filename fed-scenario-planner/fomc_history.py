"""Fed-day reaction history for the Fed Scenario Planner. Writes fomc.json.

For every scheduled FOMC decision since Feb 1994 (when the Fed started announcing decisions on the day):
  target_bp  how far the decision surprised fed funds futures, in bp (positive = more hawkish than priced).
             Kept in fomc_surprises.csv:
               1994-2009  SF Fed / Bauer-Swanson data, front eurodollar future (ED1), 30 minutes around the statement
               2010-2023  same data set, fed funds future (FF1)
               2024 on    30-day fed funds futures, daily settlements (Kuttner method). This script adds each
                          new meeting by itself once its futures prices are in.
  msg_bp     the "message": the day's 2-year yield move that the decision surprise doesn't explain.
  each market's move around the decision: S&P 500 and Treasury yields close to close on the day; FX (ECB
  reference rates, fixed before the decision) and gold (COMEX settlement, also before it) from that day's
  fix to the next day's.

Then, per market: move = a + b_target * target_bp + b_msg * msg_bp, fitted over normal times
(mid-2007 to 2009 left out: the crisis swamped everything). The leftover spread gives the likely range.
If anything fails, the last good fomc.json is kept."""
import io, json, time, calendar, datetime as dt
import numpy as np, pandas as pd, requests
from build_data import fetch, get_fomc_dates, MCODE

START = "1994-02-01"
YAHOO = {"spx": "^GSPC", "gold": "GC=F"}   # Yahoo daily FX closes are snapshotted at uneven times, so FX comes from the ECB
MARKETS = ["y2", "y10", "eurusd", "gbpusd", "usdjpy", "spx", "gold"]
CRISIS = ("2007-07-01", "2009-12-31")
CSV = "fomc_surprises.csv"


def yahoo(tk, start=START):
    j = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
              {"period1": int(pd.Timestamp(start).timestamp()), "period2": int(time.time()), "interval": "1d"}).json()
    j = j["chart"]["result"][0]
    # Yahoo stamps daily bars at the session start in the exchange's time zone, e.g. 23:00 UTC the day
    # before for FX in summer; shifting 4 hours puts every market on its own trading date
    idx = (pd.to_datetime(j["timestamp"], unit="s") + pd.Timedelta(hours=4)).normalize()
    s = pd.Series(j["indicators"]["quote"][0]["close"], index=idx, dtype=float).dropna()
    return s[~s.index.duplicated(keep="last")]


def treasury():
    fr = []
    for yr in range(int(START[:4]), dt.date.today().year + 1):
        r = fetch(f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{yr}/all",
                  {"type": "daily_treasury_yield_curve", "field_tdr_date_value": yr, "page": "", "_format": "csv"})
        fr.append(pd.read_csv(io.StringIO(r.text))[["Date", "2 Yr", "10 Yr"]])
    df = pd.concat(fr)
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    df = df.dropna().sort_values("Date").drop_duplicates("Date").set_index("Date")
    return df["2 Yr"].astype(float), df["10 Yr"].astype(float)


def ecb_fx():
    """ECB reference rates (fixed about 14:15 Frankfurt each business day) as EURUSD, GBPUSD and USDJPY."""
    import zipfile
    z = zipfile.ZipFile(io.BytesIO(fetch("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip").content))
    df = pd.read_csv(z.open(z.namelist()[0]), na_values=["N/A"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return pd.DataFrame({"eurusd": df["USD"], "gbpusd": df["USD"] / df["GBP"], "usdjpy": df["JPY"] / df["USD"]})


def move(s, day, after, bp=False):
    """Change in a series around a Fed decision (about 19:00 London).
    after=False: close on the day vs the day before (closes after the decision: S&P 500, Treasury yields).
    after=True:  first price after the day vs the price on the day (prices fixed before the decision:
                 ECB FX rates at 14:15 Frankfurt, COMEX gold settlement at 13:30 New York)."""
    s = s.dropna()
    if after:
        a, b = s[s.index <= day], s[s.index > day]
        if a.empty or b.empty or a.index[-1] < day - pd.Timedelta(days=4) or b.index[0] > day + pd.Timedelta(days=4):
            return None
        x0, x1 = a.iloc[-1], b.iloc[0]
    else:
        if day not in s.index:
            return None
        a = s[s.index < day]
        if a.empty or a.index[-1] < day - pd.Timedelta(days=5):
            return None
        x0, x1 = a.iloc[-1], s.loc[day]
    return float((x1 - x0) * 100) if bp else float(np.log(x1 / x0) * 100)


def new_surprise(day, fomc):
    """Decision surprise for a meeting that just happened, from 30-day fed funds futures settlements.
    Meeting-month contract scaled up for the days left in the month; for a late-month meeting the next
    month's contract (if no meeting in that month)."""
    n = calendar.monthrange(day.year, day.month)[1]
    y, m, scale = day.year, day.month, n / (n - day.day)
    if n - day.day <= 7:
        y, m = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
        if any(d[:7] == f"{y}-{m:02d}" for d in fomc):
            return None
        scale = 1.0
    s = yahoo(f"ZQ{MCODE[m - 1]}{str(y)[2:]}.CBT", (day - dt.timedelta(days=20)).isoformat())
    ts = pd.Timestamp(day)
    if ts not in s.index or not (s.index < ts).any():
        return None
    dp = float(s.loc[ts]) - float(s[s.index < ts].iloc[-1])
    return round(-dp * 100 * scale, 2)


def add_new_meetings():
    ev = pd.read_csv(CSV)
    now = dt.datetime.now(dt.timezone.utc)
    # a decision counts once that day's futures have settled (about 20:00 UTC)
    done = now.date() - dt.timedelta(days=0 if now.hour >= 21 else 1)
    fomc = get_fomc_dates()
    todo = [d for d in fomc if ev["date"].max() < d <= done.isoformat()]
    added = []
    for d in todo:
        try:
            s = new_surprise(dt.date.fromisoformat(d), fomc)
        except Exception as e:
            print("New meeting", d, "FAILED:", repr(e)[:150])
            s = None
        if s is None:
            print("New meeting", d, "not added yet")
            break                                   # keep order; try again tomorrow
        added.append({"date": d, "target_bp": s, "source": "Fed funds futures daily settle"})
        print("New meeting", d, "surprise", s, "bp")
    if added:
        ev = pd.concat([ev, pd.DataFrame(added)])
        ev.to_csv(CSV, index=False)
    return ev


def fit(t):
    """Least squares fit per market; returns slopes, leftover spread, sample size and start year."""
    norm = t[(t["date"] < CRISIS[0]) | (t["date"] > CRISIS[1])]
    X1 = np.c_[np.ones(len(norm)), norm["target_bp"]]
    c = np.linalg.lstsq(X1, norm["y2"], rcond=None)[0]
    t = t.assign(msg_bp=t["y2"] - (c[0] + c[1] * t["target_bp"]))
    norm = t.loc[norm.index]
    msd = float(norm["msg_bp"].std())
    out = {"y2": {"bt": round(float(c[1]), 4), "bm": 1.0, "sd": round(msd, 3), "n": int(len(norm)),
                  "from": norm["date"].iloc[0][:4]}}
    X = np.c_[np.ones(len(norm)), norm["target_bp"], norm["msg_bp"]]
    for k in MARKETS[1:]:
        ok = norm[k].notna().values
        y, Xk = norm[k].values[ok].astype(float), X[ok]
        b = np.linalg.lstsq(Xk, y, rcond=None)[0]
        res = y - Xk @ b
        s2 = res @ res / (len(y) - 3)
        se = np.sqrt(np.diag(s2 * np.linalg.inv(Xk.T @ Xk)))
        out[k] = {"bt": round(float(b[1]), 4), "bm": round(float(b[2]), 4), "sd": round(float(np.sqrt(s2)), 3),
                  "t_bt": round(float(b[1] / se[1]), 1), "t_bm": round(float(b[2] / se[2]), 1),
                  "n": int(ok.sum()), "from": norm["date"].values[ok][0][:4]}
    return t, out, round(msd, 2)


def main():
    ev = add_new_meetings()
    px = {k: yahoo(tk) for k, tk in YAHOO.items()}
    fx = ecb_fx()
    y2, y10 = treasury()
    ev = ev[ev["date"] >= START].copy()
    rows = []
    for _, e in ev.iterrows():
        day = pd.Timestamp(e["date"])
        r = {"date": e["date"], "target_bp": float(e["target_bp"]),
             "y2": move(y2, day, False, True), "y10": move(y10, day, False, True),
             "eurusd": move(fx["eurusd"], day, True), "gbpusd": move(fx["gbpusd"], day, True),
             "usdjpy": move(fx["usdjpy"], day, True), "spx": move(px["spx"], day, False), "gold": move(px["gold"], day, True)}
        if r["y2"] is None:
            print("No 2-year yield for", e["date"], "- skipped (data for the latest meeting may not be in yet)")
            continue
        rows.append(r)
    t = pd.DataFrame(rows)
    t, f, msd = fit(t)
    for k, v in f.items():
        print(k, v)
    if len(t) < 200 or not all(np.isfinite(v["bt"]) for v in f.values()):
        raise SystemExit("Too little data; keeping the last good fomc.json")
    events = []
    for r in t.to_dict("records"):
        events.append({k: (None if v is None or (isinstance(v, float) and np.isnan(v)) else
                           (round(v, 2) if isinstance(v, float) else v)) for k, v in r.items()})
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
           "n": int(f["y2"]["n"]), "from": f["y2"]["from"], "last_meeting": t["date"].iloc[-1],
           "crisis_left_out": list(CRISIS), "msg_sd": msd, "fit": f, "events": events,
           "sources": "Decision surprises: SF Fed monetary policy surprises (Bauer-Swanson) to 2023, then 30-day "
                      "fed funds futures. Market moves: S&P 500 (Yahoo Finance) and Treasury yields (US Treasury) close to close "
                      "on the day; FX (ECB reference rates) and gold (COMEX settlement, Yahoo) from the fix before the "
                      "decision to the next one after it."}
    with open("fomc.json", "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print("Saved fomc.json:", len(events), "meetings, last", out["last_meeting"])


if __name__ == "__main__":
    main()
