"""Builds data.json for the ECB Pricing page: what ECB dated €STR futures price for each ECB meeting.

Each ECB dated €STR future settles on average €STR over one ECB reserve maintenance period, and a new period
starts the Wednesday after each monetary policy meeting. So the rate priced for the period after a meeting,
minus the rate for the period before it, is what the market expects that meeting to do (the same idea as the
CME FedWatch tool). Prices are Eurex's daily settlements (product FEMP), from the JSON behind the Statistics
tab of Eurex's product page. Eurex only keeps about 30 trading days, so every run also adds the latest
settlements to history.csv.

If a download fails the last good data.json is kept, the problem is listed in data.json "problems",
and the job still finishes green."""
import csv, json, os, time, datetime as dt
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, HIST = os.path.join(HERE, "data.json"), os.path.join(HERE, "history.csv")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept": "application/json"}
EUREX = "https://www.eurex.com/api/v1/overallstatistics/4853044"   # 4853044 = ECB Dated €STR Futures (FEMP)
# ECB monetary policy meetings (decision days), from ecb.europa.eu/press/calendars/mgcgc. Same list as central-banks/config.json.
ECB = ["2025-12-18", "2026-02-05", "2026-03-19", "2026-04-30", "2026-06-11", "2026-07-23", "2026-09-10",
       "2026-10-29", "2026-12-17", "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-10", "2027-07-22",
       "2027-09-09", "2027-10-28", "2027-12-16"]


def fetch(url, params=None, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(4 * (i + 1))
    raise last


def eurex(busdate):
    """Settlements for one trading day: {period start 'YYYY-MM-DD': rate %}, plus the list of trading days Eurex has."""
    j = fetch(EUREX, {"busdate": busdate.strftime("%Y%m%d"), "filtertype": "overview"}).json()
    days = [dt.datetime.strptime(s[:10], "%d-%m-%Y").date() for s in j.get("header", {}).get("tradingDates", [])]
    rates = {}
    for r in j.get("dataRows") or []:
        if r.get("dSettle"):
            d = r["date"]
            rates[f"{d[:4]}-{d[4:6]}-{d[6:]}"] = round(100 - float(r["dSettle"]), 4)
    return rates, days


def ecb_latest(series):
    """Latest value of an ECB Data Portal series, e.g. EST/B.EU000A2X2A25.WT (€STR)."""
    r = fetch(f"https://data-api.ecb.europa.eu/service/data/{series}", {"lastNObservations": 1, "format": "csvdata"})
    row = list(csv.DictReader(r.text.splitlines()))[-1]
    return float(row["OBS_VALUE"]), row["TIME_PERIOD"]


def meeting_for(period_start):
    """The ECB meeting whose decision takes effect at the start of this maintenance period."""
    before = [m for m in ECB if m < period_start]
    return before[-1] if before else None


def path_from(rates, asof):
    """Current period's rate plus one rate per upcoming meeting (the period that meeting starts)."""
    starts = sorted(rates)
    cur = [s for s in starts if s <= asof.isoformat()]
    if not cur:
        return None
    base_start = cur[-1]
    meetings, out = [], []
    for s in starts:
        if s <= base_start:
            continue
        m = meeting_for(s)
        if m and m >= base_start[:10] and m not in meetings and dt.date.fromisoformat(s) - dt.date.fromisoformat(m) < dt.timedelta(days=14):
            meetings.append(m)
            out.append(rates[s])
    return {"base": rates[base_start], "base_period": base_start, "meetings": meetings, "rates": out,
            "periods": [s for s in starts if s > base_start and meeting_for(s) in meetings]}


def main():
    old = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            old = json.load(f)
    problems, data = [], {"generated": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

    try:
        today = dt.datetime.utcnow().date()
        rates, days = eurex(today)
        days = sorted(set(days), reverse=True)
        asof = None
        for d in days[:4]:                       # latest trading day that has settlements
            r, _ = eurex(d)
            if r:
                rates, asof = r, d
                break
        if not asof:
            raise RuntimeError("no settlements in the last 4 trading days")
        p = path_from(rates, asof)
        if not p or not p["rates"]:
            raise RuntimeError("could not line contracts up with ECB meetings")
        p["asof"] = asof.isoformat()
        p["effr"] = p["base"]      # same field name as Fed Pricing, so the page code matches
        p["compare"] = {}
        later = [d for d in days if d < asof]
        for label, n in (("1w ago", 5), ("3w ago", 15)):
            if len(later) >= n:
                try:
                    r, _ = eurex(later[n - 1])
                    by_start = [r.get(s) for s in p["periods"]]
                    if any(x is not None for x in by_start):
                        p["compare"][label] = {"asof": later[n - 1].isoformat(), "rates": by_start}
                except Exception as e:
                    print("compare", label, "failed:", e)
        p["source"] = "Eurex ECB Dated €STR Futures (FEMP), daily settlement"
        data["path"] = p
        # keep our own history: Eurex only keeps ~30 trading days
        have = set()
        if os.path.exists(HIST):
            with open(HIST) as f:
                have = {(row["date"], row["period_start"]) for row in csv.DictReader(f)}
        new = not os.path.exists(HIST)
        with open(HIST, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["date", "period_start", "rate"])
            for s in sorted(rates):
                if (asof.isoformat(), s) not in have:
                    w.writerow([asof.isoformat(), s, rates[s]])
        print("Eurex settlements for", asof, "->", len(p["rates"]), "meetings")
    except Exception as e:
        print("Eurex pricing failed:", e)
        problems.append("path")
        if old.get("path"):
            data["path"] = old["path"]

    for key, series in (("estr", "EST/B.EU000A2X2A25.WT"), ("dfr", "FM/D.U2.EUR.4F.KR.DFR.LEV")):
        try:
            v, d = ecb_latest(series)
            data[key] = {"value": v, "date": d}
        except Exception as e:
            print(key, "failed:", e)
            problems.append(key)
            if old.get(key):
                data[key] = old[key]

    data["problems"] = problems
    if not data.get("path"):
        print("No pricing yet; nothing saved")
        return
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(json.dumps(data, indent=1)[:2500])


if __name__ == "__main__":
    main()
