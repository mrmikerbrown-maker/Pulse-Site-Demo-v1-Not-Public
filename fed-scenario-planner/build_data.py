"""Builds data.json for Fed Pricing and the Fed Scenario Planner: what 30-day fed funds futures price for
each FOMC meeting (the "path"), plus a single-meeting read used as a fallback. Market reactions to Fed
surprises are built separately by fomc_history.py (fomc.json)."""
import json, time, calendar, datetime as dt
import pandas as pd, requests

UA = {"User-Agent": "Mozilla/5.0"}
# FOMC decision days (second day of each meeting), from federalreserve.gov/monetarypolicy/fomccalendars.htm.
FOMC = ["2023-11-01", "2023-12-13", "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18", "2025-01-29", "2025-03-19",
        "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16",
        "2026-10-28", "2026-12-09",
        # 2027 schedule (tentative), Fed press release 5 Sep 2025
        "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15",
        "2027-10-27", "2027-12-08"]


def fetch(url, params=None, tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def get_yahoo(tk, rng="3y"):
    r = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}", {"range": rng, "interval": "1d"})
    j = r.json()["chart"]["result"][0]
    s = pd.Series(j["indicators"]["quote"][0]["close"],
                  index=pd.to_datetime(j["timestamp"], unit="s").normalize(), dtype=float).dropna()
    return s[~s.index.duplicated(keep="last")]


MCODE = "FGHJKMNQUVXZ"


def zq_price(year, month):
    tk = f"ZQ{MCODE[month - 1]}{str(year)[2:]}.CBT"
    s = get_yahoo(tk, "1mo")
    return float(s.iloc[-1]), str(s.index[-1].date()), tk


def get_effr(with_date=False):
    r = fetch("https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json")
    x = r.json()["refRates"][0]
    return (float(x["percentRate"]), x["effectiveDate"]) if with_date else float(x["percentRate"])


def rate_pricing(today, fomc=FOMC):
    """Cut/hold/hike odds for the next FOMC decision from 30-day fed funds futures (100 - price = avg EFFR)."""
    nxt = [d for d in fomc if d >= today]
    if not nxt:
        return None
    dec = dt.date.fromisoformat(nxt[0])
    after = dt.date.fromisoformat(nxt[1]) if len(nxt) > 1 else None
    r0 = get_effr()
    n, d = calendar.monthrange(dec.year, dec.month)[1], dec.day   # new rate applies from day d+1
    if n - d <= 7:                      # late-month meeting: the next month's contract is the cleaner read
        ny, nm = (dec.year + 1, 1) if dec.month == 12 else (dec.year, dec.month + 1)
        if after and (after.year, after.month) == (ny, nm):
            return None
        p, asof, tk = zq_price(ny, nm)
        r1 = 100 - p
    else:
        p, asof, tk = zq_price(dec.year, dec.month)
        r1 = (n * (100 - p) - d * r0) / (n - d)
    delta = (r1 - r0) * 100
    cut, hike = min(1, max(0, -delta / 25)), min(1, max(0, delta / 25))
    return {"meeting": dec.isoformat(), "cut": round(cut, 3), "hike": round(hike, 3),
            "hold": round(1 - cut - hike, 3), "net_bp": round(delta, 1), "effr": r0,
            "contract": tk, "price": p, "asof": asof,
            "source": "30-day fed funds futures via Yahoo (delayed); 25bp steps assumed"}


MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december"]


def get_fomc_dates():
    """Decision days from the Fed's own calendar page, merged with the list above. Falls back to the list
    if the page can't be read. Each year must give 6-10 meetings to be trusted."""
    import re
    found = set()
    try:
        html = fetch("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", tries=2, timeout=30).text
        parts = re.split(r"(\d{4})\s+FOMC Meetings", html)
        for i in range(1, len(parts) - 1, 2):
            yr, chunk = int(parts[i]), parts[i + 1]
            got = []
            for mo, days in re.findall(r"fomc-meeting__month[^>]*>(?:\s|<[^>]+>)*([A-Za-z]+(?:/[A-Za-z]+)?)"
                                       r"(?:\s|<[^>]+>)*</div>(?:\s|<[^>]+>)*?<div[^>]*fomc-meeting__date[^>]*>"
                                       r"(?:\s|<[^>]+>)*(\d{1,2}(?:\s*[-\u2013]\s*\d{1,2})?)", chunk):
                ms = [next((i + 1 for i, n in enumerate(MONTHS) if n[:3] == x[:3].lower()), None)
                      for x in mo.split("/")]
                if None in ms:
                    continue
                dd = [int(x) for x in re.split(r"[-\u2013]", days)]
                mon = ms[0]
                if len(dd) == 2 and dd[1] < dd[0]:          # runs into the next month, e.g. Apr/May 30-1
                    mon = ms[1] if len(ms) > 1 else ms[0] % 12 + 1
                try:
                    got.append(dt.date(yr, mon, dd[-1]).isoformat())
                except ValueError:
                    pass
            if 6 <= len(got) <= 10:
                found.update(got)
        print("FOMC calendar page:", len(found), "dates, last", max(found) if found else None)
    except Exception as e:
        print("FOMC calendar page FAILED, using built-in dates:", repr(e)[:150])
    allc = sorted(set(FOMC) | found)
    # if the page and the list disagree for a year the page covers, trust the page
    yrs = {d[:4] for d in found}
    return sorted([d for d in allc if d[:4] not in yrs or d in found])


def month_add(y, m, k=1):
    m += k
    return y + (m - 1) // 12, (m - 1) % 12 + 1


def path_on(R, meets, r0):
    """Average effective rate after each meeting, chained month by month from 30-day fed funds futures.
    R: {(year, month): 100 - futures price}. Uses the next month's contract when that month has no meeting
    (cleanest read); otherwise backs the post-meeting rate out of the meeting month's average."""
    mm = {(d.year, d.month) for d in meets}
    out, post = [], r0
    for d in meets:
        ym = (d.year, d.month)
        pm, nm = month_add(d.year, d.month, -1), month_add(d.year, d.month, 1)
        pre = R[pm] if pm not in mm and pm in R else post
        n = calendar.monthrange(d.year, d.month)[1]
        if nm not in mm and nm in R:
            post = R[nm]
        elif ym in R:
            post = (n * R[ym] - d.day * pre) / (n - d.day)
        else:
            break                       # no prices this far out yet
        out.append(round(post, 4))
    return out


def rate_path(today, r0, fomc):
    """Meeting-by-meeting priced path, as far out as there are both futures prices and known meeting dates,
    plus the same path 1 and 3 weeks ago."""
    td = dt.date.fromisoformat(today)
    meets = [dt.date.fromisoformat(d) for d in fomc if d >= today]
    if not meets:
        return None
    S, ym, miss = {}, month_add(td.year, td.month, -1), 0
    for _ in range(60):                 # up to 5 years out; stops after 3 missing months in a row
        y, m = ym
        tk = f"ZQ{MCODE[m - 1]}{str(y)[2:]}.CBT"
        try:
            S[ym] = get_yahoo(tk, "3mo")
            miss = 0
        except Exception:
            miss += 1
            if miss >= 3 and ym > (td.year, td.month):
                break
        ym = month_add(y, m, 1)
    print("Path: contracts", min(S), "to", max(S), f"({len(S)})")
    df = pd.DataFrame(S).sort_index().ffill()
    need = [k for k in S if k >= (td.year, td.month)]
    df = df.dropna(subset=need[:3])         # far months trade thinly; forward-fill covers gaps
    df = df.dropna(how="all")
    if df.empty:
        raise ValueError("no complete row of futures prices")

    def at(day):
        row = df[df.index <= pd.Timestamp(day)].iloc[-1]
        R = {k: 100 - float(v) for k, v in row.items() if pd.notna(v)}
        return {"asof": str(row.name.date()), "rates": path_on(R, meets, r0)}

    cur = at(df.index[-1])
    meets = meets[:len(cur["rates"])]
    end = df.index[-1].date()
    comp = {}
    for lab, k in [("1w ago", 7), ("3w ago", 21)]:
        try:
            c = at(end - dt.timedelta(days=k))
            c["rates"] = c["rates"][:len(meets)]
            comp[lab] = c
        except Exception as e:
            print("Path: no", lab, repr(e)[:120])
    return {"meetings": [d.isoformat() for d in meets], "effr": r0, "asof": cur["asof"], "rates": cur["rates"],
            "compare": comp, "source": "CBOT 30-day fed funds futures via Yahoo (delayed)"}


def main():
    today = dt.date.today().isoformat()
    fomc = get_fomc_dates()
    problems = []
    try:
        pricing = rate_pricing(today, fomc)
        print("Pricing:", pricing)
    except Exception as e:
        pricing = None
        print("Pricing FAILED:", repr(e)[:200])
    try:
        r0, r0_date = get_effr(with_date=True)
        # start the path from the effective rate's own date, so a meeting that has just happened stays in
        # the path until the effective rate reflects it (pages pick the next meeting themselves)
        path = rate_path(min(today, r0_date), r0, fomc)
        path["effr_date"] = r0_date
        print("Path:", path)
    except Exception as e:
        path = None
        problems.append("path")
        print("Path FAILED, keeping the last good one:", repr(e)[:200])
        try:
            with open("data.json") as f:
                path = json.load(f).get("path")
        except Exception:
            pass
    if path is None and pricing is None:
        raise SystemExit("No futures data at all; keeping the last data.json")
    nxt = next((x for x in fomc if x >= today), None)
    out = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "problems": problems,          # pages show a warning when the latest prices could not be fetched
        "pricing": pricing,
        "path": path,
        "next_event": {"date": nxt, "type": "FOMC decision"} if nxt else None,
    }
    with open("data.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
