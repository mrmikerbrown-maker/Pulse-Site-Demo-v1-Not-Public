"""Add the session just saved in last-session.csv to periods.csv, the closes the site uses for Week, Month and YTD.

periods.csv has one row per stock (the sheet's Symbol) and one per index (IDX_SPX, IDX_NDX, IDX_DOW),
and one column per close. It was seeded once with closes for 31 Dec 2025, 30 Sep, 23 Oct and 30 Oct 2026
(TradingView). Each evening this rolls every stock forward by its % change on the day from the sheet,
and records the index closes as they are. Nothing is fetched from outside, so nothing can be blocked.

The file keeps last year's final close, the last close of each month since, and the last 15 closes:
every date a Week, Month or Year-to-date view can start from.
"""
import csv
from datetime import date, datetime
from zoneinfo import ZoneInfo

MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
num = lambda s: float(str(s).replace(",", "")) if str(s).strip() not in ("", "-") else None

rows = list(csv.reader(open("last-session.csv", encoding="utf-8")))
idx = {r[0]: r for r in rows if r and r[0].startswith("IDX_")}
d, m = idx["IDX_SPX"][5].split()[:2]
ny = datetime.now(ZoneInfo("America/New_York")).date()
year = ny.year - (1 if MON[m] > ny.month else 0)
day = date(year, MON[m], int(d)).isoformat()

table = list(csv.reader(open("periods.csv", encoding="utf-8")))
dates, data = table[0][1:], {r[0]: r[1:] for r in table[1:] if r}
if day <= dates[-1]:
    print(f"periods.csv already has {dates[-1]}; nothing to add for {day}")
    raise SystemExit(0)

new = {}
for k, r in idx.items():
    new[k] = num(r[3])
for r in rows:
    if r and r[0] in ("SPX", "NDX", "DOW") and len(r) > 8 and r[4] and r[4] not in new:
        chg = num(r[8])
        prev = data.get(r[4], [""])[-1]
        new[r[4]] = float(prev) * (1 + (chg or 0) / 100) if prev else 100.0  # a new member counts from here
if any(new.get(k) is None for k in ("IDX_SPX", "IDX_NDX", "IDX_DOW")):
    raise SystemExit("Index closes missing from last-session.csv")

dates.append(day)
for k in set(data) | set(new):
    row = data.get(k, [""] * (len(dates) - 1))
    v = new.get(k)
    row.append(f"{v:.4f}" if v is not None else row[-1])
    data[k] = row

# Keep the last 15 closes, plus the last close of every month from December last year.
last_of_month = {}
for i, s in enumerate(dates):
    last_of_month[s[:7]] = i
first_month = f"{int(day[:4]) - 1}-12"
keep = sorted(set(range(max(0, len(dates) - 15), len(dates))) | {i for mth, i in last_of_month.items() if mth >= first_month})

order = ["IDX_SPX", "IDX_NDX", "IDX_DOW"] + sorted(k for k in data if not k.startswith("IDX_"))
with open("periods.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sym"] + [dates[i] for i in keep])
    for k in order:
        w.writerow([k] + [data[k][i] for i in keep])
print(f"Added {day}: {len(new)} rows; keeping {len(keep)} dates from {dates[keep[0]]}")
