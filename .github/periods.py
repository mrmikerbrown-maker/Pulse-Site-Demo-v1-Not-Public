"""Save the closing prices the site needs for its Week, Month and Year-to-date views.

Writes periods.csv: one row per stock (keyed by the sheet's Symbol column) and one per index
(IDX_SPX, IDX_NDX, IDX_DOW), one column per date. The dates kept are the last close of last year,
every month-end close since, and the last 15 closes, which covers every start date the site
can need: the close before the year, the month and the week of the session it shows.
Prices are Yahoo daily closes, adjusted for splits but not dividends (like the indices).
"""
import csv, io, json, sys, time, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vSE9500jiKFvBw_k0q2m8CPaZ3VbZNv0uIYCe-QSnXpbASoqvwr2RW2hocHl5NVQejXIfVe4CdhX67h"
       "/pub?gid=454467433&single=true&output=csv")
INDICES = {"IDX_SPX": "^GSPC", "IDX_NDX": "^NDX", "IDX_DOW": "^DJI"}
NY = ZoneInfo("America/New_York")
now = datetime.now(NY)
# Today's bar only counts once the US session has closed.
last_ok = now.date() if now.hour * 60 + now.minute >= 16 * 60 + 30 else now.date() - timedelta(days=1)
start = date(now.year - 1, 12, 1)
p1 = int(datetime(start.year, start.month, start.day, tzinfo=NY).timestamp())
p2 = int((now + timedelta(days=1)).timestamp())

rows = list(csv.reader(io.StringIO(urllib.request.urlopen(URL, timeout=60).read().decode("utf-8"))))
syms = {}
for r in rows[1:]:
    if r and r[0] in ("SPX", "NDX", "DOW") and len(r) > 4 and r[4]:
        g = (r[1].split(":")[-1] if r[1] else r[4]).strip()
        syms[r[4]] = g.replace(".", "-")
syms.update(INDICES)

BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
errors = []

def get(ysym, ua):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ysym)}"
           f"?period1={p1}&period2={p2}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": ua} if ua else {})
    j = json.load(urllib.request.urlopen(req, timeout=20))
    res = j["chart"]["result"][0]
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName") or "America/New_York")
    out = {}
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        d = datetime.fromtimestamp(t, tz).date()
        if c is not None and d <= last_ok:
            out[d] = c
    return out

# Find a User-Agent Yahoo accepts from here (it has refused both kinds from Actions at times).
UA = False
for ua in (BROWSER, None):
    try:
        get("^GSPC", ua); UA = ua; break
    except Exception as e:
        print(f"Probe with {'browser' if ua else 'default'} User-Agent failed: {e}", flush=True)
if UA is False:
    sys.exit(1)
print(f"Using the {'browser' if UA else 'default'} User-Agent; fetching {len(syms)} symbols", flush=True)

def fetch(item):
    key, ysym = item
    for attempt in range(3):
        try:
            return key, get(ysym, UA)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                errors.append(f"{ysym}: 404"); return key, {}
            err = f"{ysym}: HTTP {e.code}"
        except Exception as e:
            err = f"{ysym}: {e}"
        time.sleep(1.5 * (attempt + 1))
    errors.append(err)
    return key, None

t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    got = dict(ex.map(fetch, syms.items()))
print(f"Fetched in {time.time() - t0:.0f}s; problems: {errors[:30]}", flush=True)

bad = [k for k, v in got.items() if not v]
idx_days = sorted(got.get("IDX_SPX") or {})
if any(not got.get(k) for k in INDICES) or len(bad) > 0.05 * len(syms) or not idx_days:
    print(f"Not saving: {len(bad)} of {len(syms)} symbols failed: {bad[:40]}")
    sys.exit(1)

# Dates to keep: last close of last year, each month-end since, and the last 15 closes.
keep = set(idx_days[-15:])
by_month = {}
for d in idx_days:
    by_month[(d.year, d.month)] = d
keep |= set(by_month.values())
keep = sorted(keep)

with open("periods.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sym"] + [d.isoformat() for d in keep])
    for key in list(INDICES) + sorted(k for k in got if k not in INDICES):
        v = got.get(key) or {}
        if not v:
            continue
        line, first = [], min(v)
        for d in keep:
            # A missing day (halt, late listing) takes the last close before it; before its first close it stays blank.
            if d in v:
                line.append(f"{v[d]:.4f}")
            elif d > first:
                line.append(f"{v[max(x for x in v if x < d)]:.4f}")
            else:
                line.append("")
        w.writerow([key] + line)
print(f"Saved {len(got) - len(bad)} symbols, {len(keep)} dates ({keep[0]} to {keep[-1]}). Missing: {bad}")
