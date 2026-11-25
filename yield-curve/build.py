"""Builds data.json for the Yield Curves page.

Today's curves (and their change on the day, over 1 week and over 1 month) come from TradingView's public
screener: benchmark government bond yields for the US, Germany and the UK. The request carries no login, cookie
or key. The screener gives no history, so the spreads-over-time chart uses the official curves instead:
  US  - US Treasury daily par yield curve (same day)
  DE  - Bundesbank yield curve for Federal securities, Svensson method (same day, ~12:30 London)
  UK  - Bank of England fitted nominal gilt curve, spot (published the next working day)
Each run also adds the day's TradingView closes to tv-history.csv, so a TradingView history builds up.

If a download fails, the last good part of data.json is kept, the problem is listed in "problems",
and the job still finishes green."""
import csv, io, json, os, time, zipfile, datetime as dt
import requests, openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, TVH = os.path.join(HERE, "data.json"), os.path.join(HERE, "tv-history.csv")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
START = "2024-01-01"            # spreads history starts here
HM = [2, 5, 10, 30]             # maturities kept in the history (enough for 2s10s, 5s30s, 2s30s)
# TradingView maturities per country, in years. Under 1 year TradingView quotes bill prices, not yields, so the curve starts at 1y.
TV = {"us": [1, 2, 3, 5, 7, 10, 20, 30], "de": [1, 2, 3, 5, 7, 10, 15, 20, 30], "uk": [1, 2, 3, 5, 7, 10, 15, 20, 30]}
TVC = {"us": "US", "de": "DE", "uk": "GB"}
NAMES = {"us": "US Treasuries", "de": "German Bunds", "uk": "UK Gilts"}


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(5 * (i + 1))
    raise last


def tradingview():
    """{country: {mats, now, d1, w1, m1}} from the TradingView screener. Levels a week / month ago are backed out
    from the screener's Perf.W / Perf.1M (percentage change of the yield)."""
    tick = {f"TVC:{TVC[c]}{m:02d}Y": (c, m) for c, ms in TV.items() for m in ms}
    cols = ["close", "change_abs", "Perf.W", "Perf.1M", "type"]
    h = dict(UA, Origin="https://www.tradingview.com", Referer="https://www.tradingview.com/")
    r = None
    for i in range(3):
        try:
            r = requests.post("https://scanner.tradingview.com/global/scan", headers=h, timeout=60,
                              json={"symbols": {"tickers": list(tick), "query": {"types": []}}, "columns": cols})
            r.raise_for_status(); break
        except Exception as e:
            r = e; time.sleep(5 * (i + 1))
    if isinstance(r, Exception):
        raise r
    rows = {d["s"]: dict(zip(cols, d["d"])) for d in r.json().get("data", [])}
    out = {}
    for c, ms in TV.items():
        now, d1, w1, m1 = [], [], [], []
        for m in ms:
            q = rows.get(f"TVC:{TVC[c]}{m:02d}Y")
            if not q or q.get("close") is None:
                raise RuntimeError(f"TradingView gave no yield for {TVC[c]}{m:02d}Y")
            y = q["close"]
            now.append(round(y, 4))
            d1.append(round(y - q["change_abs"], 4) if q.get("change_abs") is not None else None)
            w1.append(round(y / (1 + q["Perf.W"] / 100), 4) if q.get("Perf.W") is not None else None)
            m1.append(round(y / (1 + q["Perf.1M"] / 100), 4) if q.get("Perf.1M") is not None else None)
        out[c] = {"mats": ms, "now": now, "d1": d1, "w1": w1, "m1": m1}
    print("TradingView OK:", {c: v["now"] for c, v in out.items()})
    return out


def us_history():
    UCOL = {"2 Yr": 2, "5 Yr": 5, "10 Yr": 10, "30 Yr": 30}
    hist = {}
    for y in range(int(START[:4]), dt.date.today().year + 1):
        url = (f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"
               f"?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")
        for row in csv.DictReader(io.StringIO(fetch(url).content.decode("utf-8-sig"))):
            try:
                d = dt.datetime.strptime(row["Date"], "%m/%d/%Y").date().isoformat()
                hist[d] = {m: float(row[c]) for c, m in UCOL.items()}
            except (KeyError, ValueError):
                pass
    return hist


def de_history():
    hist = {}
    for m in HM:
        url = (f"https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R{m:02d}XX.R.A.A._Z._Z.A"
               f"?format=csv&lang=en&startPeriod={START}")
        for line in fetch(url).content.decode("utf-8-sig").splitlines():
            p = line.split(",")
            if len(p) >= 2 and p[0][:2] == "20" and p[1] not in (".", ""):
                hist.setdefault(p[0], {})[m] = float(p[1])
    return {d: v for d, v in hist.items() if len(v) == len(HM)}


def gilt_spot(zbytes):
    """{date: {maturity: yield}} from the '4. spot curve' sheet of every nominal workbook in a BoE zip."""
    out = {}
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    for name in z.namelist():
        low = name.lower()
        if "nominal" not in low or not any(s in low for s in ("current month", "present", "2016 to 2024")):
            continue
        wb = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True, data_only=True)
        for sn in wb.sheetnames:
            if "spot" not in sn.lower() or "short" in sn.lower():
                continue
            yrs = None
            for r in wb[sn].iter_rows(values_only=True):
                if not r:
                    continue
                if isinstance(r[0], str) and r[0].strip().lower().startswith("years"):
                    yrs = list(r[1:])
                elif yrs and isinstance(r[0], (dt.datetime, dt.date)):
                    d = (r[0].date() if isinstance(r[0], dt.datetime) else r[0]).isoformat()
                    pts = {int(y): v for y, v in zip(yrs, r[1:]) if isinstance(y, (int, float)) and y in HM and isinstance(v, (int, float))}
                    if len(pts) == len(HM) and d >= START:
                        out[d] = pts
    return out


def uk_history(old):
    YC = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/"
    hist = dict(old)
    cur = gilt_spot(fetch(YC + "latest-yield-curve-data.zip").content)
    # The current-month file only covers this month: fetch the big archive (~40 MB) when our saved history
    # doesn't reach back to the start of it (first run, or after a gap).
    first = min(cur) if cur else dt.date.today().isoformat()
    have = [d for d in hist if d < first]
    if not have or (dt.date.fromisoformat(first) - dt.date.fromisoformat(max(have))).days > 5:
        print("Fetching the Bank of England archive")
        hist.update(gilt_spot(fetch(YC + "glcnominalddata.zip").content))
    hist.update(cur)
    return hist


def pack(hist, src):
    days = sorted(d for d in hist if d >= START)
    return {"mats": HM, "dates": days, "y": [[round(hist[d][m], 3) for m in HM] for d in days], "src": src}


def unpack(h):
    return {d: dict(zip(h["mats"], y)) for d, y in zip(h["dates"], h["y"])} if h else {}


def main():
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    now = dt.datetime.now(dt.timezone.utc)
    out = {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "problems": []}
    try:
        tv = tradingview()
        out["curve_asof"] = out["generated"]
    except Exception as e:
        print("TradingView failed:", e); out["problems"].append("curve")
        tv = {c: old.get(c, {}).get("curve") for c in NAMES}
        out["curve_asof"] = old.get("curve_asof")
    jobs = {"us": (us_history, "US Treasury par yield curve"), "de": (de_history, "Bundesbank Svensson curve"),
            "uk": (None, "Bank of England fitted gilt curve")}
    for c, (fn, src) in jobs.items():
        prev = old.get(c, {}).get("hist")
        try:
            h = uk_history(unpack(prev)) if c == "uk" else fn()
            if len(h) < 50:
                raise RuntimeError("too little history")
            hist = pack(h, src)
            print(c, "history", hist["dates"][0], "to", hist["dates"][-1], len(hist["dates"]))
        except Exception as e:
            print(c, "history failed:", e); out["problems"].append("hist-" + c); hist = prev
        out[c] = {"name": NAMES[c], "curve": tv.get(c), "hist": hist}
    if not all(out[c]["curve"] for c in NAMES):
        raise SystemExit("No curve data at all; keeping the old file")
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    # Keep our own TradingView history: one row per weekday and maturity, the latest run of the day wins.
    if "curve" not in out["problems"]:
        day = now.date().isoformat()
        rows = [r for r in csv.reader(open(TVH))][1:] if os.path.exists(TVH) else []
        rows = [r for r in rows if r[0] != day]
        for c in NAMES:
            for m, y in zip(tv[c]["mats"], tv[c]["now"]):
                rows.append([day, c, str(m), str(y)])
        with open(TVH, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "country", "years", "yield"]); w.writerows(rows)
    print("Problems:", out["problems"] or "none")


if __name__ == "__main__":
    main()
