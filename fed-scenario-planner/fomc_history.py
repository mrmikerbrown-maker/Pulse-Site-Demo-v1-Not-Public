"""Fed-day reaction history for the Fed Scenario Planner.

For every scheduled FOMC decision since 2004 it records:
  target_bp  - the surprise in the rate decision itself, in bp (positive = more hawkish than priced)
               2004-2023: San Francisco Fed / Bauer-Swanson dataset (30-minute window around the statement, FF1)
               2024 on : fomc_recent.csv, from 30-day fed funds futures daily settlements (Kuttner method)
  msg_bp     - the "message" part: the day's 2-year yield move not explained by the decision surprise
  the day's move in each market (close to close)
Then fits, per market:  move = a + b_target * target_bp + b_msg * msg_bp  and keeps the leftover spread.
Writes fomc.json."""
import io, json, time, datetime as dt
import numpy as np, pandas as pd, requests

UA = {"User-Agent": "Mozilla/5.0"}
START = "1994-02-01"   # the Fed has announced decisions on the day since Feb 1994
YAHOO = {"eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X", "usdjpy": "JPY=X", "spx": "^GSPC", "gold": "GC=F"}


def fetch(url, params=None, tries=3, timeout=60):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def yahoo(tk):
    p1 = int(pd.Timestamp(START).timestamp())
    j = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
              {"period1": p1, "period2": int(time.time()), "interval": "1d"}).json()["chart"]["result"][0]
    s = pd.Series(j["indicators"]["quote"][0]["close"], index=pd.to_datetime(j["timestamp"], unit="s").normalize(), dtype=float).dropna()
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


def surprises():
    page = fetch("https://www.frbsf.org/research-and-insights/data-and-indicators/monetary-policy-surprises/").text
    import re
    links = re.findall(r'(?:href|src)="([^"]+)"', page)
    url = next(l for l in links if re.search(r"\.xlsx?($|\?)", l, re.I)).replace("&amp;", "&")
    url = url if url.startswith("http") else "https://www.frbsf.org" + url
    x = pd.read_excel(io.BytesIO(fetch(url).content), sheet_name=None)
    parts = []
    for k, df in x.items():
        print("SF sheet", repr(k), df.shape, list(df.columns)[:8])
        if not {"Date", "FF1"} <= set(df.columns):
            continue
        dd = pd.to_datetime(df["Date"], errors="coerce")
        print("   dates", dd.min(), "to", dd.max(), "FF1 non-null", int(df["FF1"].notna().sum()),
              "Unscheduled values", df["Unscheduled"].value_counts(dropna=False).to_dict() if "Unscheduled" in df else "-")
        if "fomc" not in k.lower():
            continue
        df = df.assign(date=dd.dt.normalize())
        if "Unscheduled" in df:
            df = df[df["Unscheduled"].fillna(0) == 0]
        df = df[df["FF1"].notna() & df["date"].notna()]
        parts.append(pd.DataFrame({"date": df["date"], "target_bp": df["FF1"].astype(float) * 100, "source": "SF Fed (" + k + ")"}))
    sf = pd.concat(parts).drop_duplicates("date", keep="last").sort_values("date")
    print("SF Fed scheduled meetings:", len(sf), sf["date"].min().date(), "to", sf["date"].max().date())
    rec = pd.read_csv("fomc_recent.csv", parse_dates=["date"])
    rec = rec[rec["date"] > sf["date"].max()]
    out = pd.concat([sf, rec]).sort_values("date")
    return out[out["date"] >= START].reset_index(drop=True)


def main():
    ev = surprises()
    print("Meetings:", len(ev), ev["date"].min().date(), "to", ev["date"].max().date())
    px = {k: yahoo(t) for k, t in YAHOO.items()}
    y2, y10 = treasury()
    d = pd.DataFrame(px)
    d["y2"], d["y10"] = y2, y10
    d = d.sort_index()
    for c in d.columns:
        print("data", c, d[c].first_valid_index().date(), "to", d[c].last_valid_index().date(), int(d[c].notna().sum()), "days")
    chg = pd.DataFrame(index=d.index)
    for k in YAHOO:
        chg[k] = np.log(d[k]).diff() * 100           # % move, close to close
    chg["y2"] = d["y2"].diff() * 100                 # bp
    chg["y10"] = d["y10"].diff() * 100
    rows = []
    for _, e in ev.iterrows():
        if e["date"] not in chg.index:
            continue
        m = chg.loc[e["date"]]
        rows.append({"date": e["date"].date().isoformat(), "target_bp": round(float(e["target_bp"]), 2),
                     **{k: (None if pd.isna(m[k]) else round(float(m[k]), 3)) for k in chg.columns}})
    t = pd.DataFrame(rows).dropna(subset=["y2"])
    # message = 2-year move not explained by the decision surprise
    X1 = np.c_[np.ones(len(t)), t["target_bp"]]
    c2 = np.linalg.lstsq(X1, t["y2"], rcond=None)[0]
    t["msg_bp"] = t["y2"] - X1 @ c2
    msg_sd = float(t["msg_bp"].std())
    print(f"2y on target: {c2[1]:.3f} bp per bp; message sd {msg_sd:.2f} bp; n={len(t)}")
    fit = {}
    X = np.c_[np.ones(len(t)), t["target_bp"], t["msg_bp"]]
    for k in ["y2", "y10", "eurusd", "gbpusd", "usdjpy", "spx", "gold"]:
        ok = t[k].notna().values
        y = t[k].values[ok].astype(float)
        Xk = X[ok]
        b, *_ = np.linalg.lstsq(Xk, y, rcond=None)
        res = y - Xk @ b
        dof = len(y) - 3
        s2 = res @ res / dof
        cov = s2 * np.linalg.inv(Xk.T @ Xk)
        r2 = 1 - (res @ res) / ((y - y.mean()) @ (y - y.mean()))
        fit[k] = {"b_target": round(float(b[1]), 4), "se_target": round(float(np.sqrt(cov[1, 1])), 4),
                  "b_msg": round(float(b[2]), 4), "se_msg": round(float(np.sqrt(cov[2, 2])), 4),
                  "resid_sd": round(float(np.sqrt(s2)), 4), "r2": round(float(r2), 3),
                  "n": int(ok.sum()), "from": t["date"].values[ok][0]}
        print(k, fit[k])
    big = t.reindex(t["target_bp"].abs().sort_values(ascending=False).index).head(12)
    print("Biggest decision surprises:\n", big[["date", "target_bp", "msg_bp", "y2", "eurusd", "spx"]].to_string())
    t["msg_bp"] = t["msg_bp"].round(2)
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "n": int(len(t)),
           "from": t["date"].iloc[0], "to": t["date"].iloc[-1], "msg_sd": round(msg_sd, 2), "fit": fit,
           "events": t.astype(object).where(t.notna(), None).to_dict("records"),
           "sources": "Decision surprises: SF Fed monetary policy surprises (Bauer-Swanson), then 30-day fed funds futures. "
                      "Market moves: Yahoo Finance and US Treasury, close to close on the decision day."}
    with open("fomc.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
