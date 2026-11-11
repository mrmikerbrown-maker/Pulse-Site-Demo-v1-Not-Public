"""Save the sheet's published CSV as last-session.csv once the US session has closed.

The site shows this copy outside market hours, because Google resets some stocks' previous
close before the next open and the live sheet then shows a mix of old and zeroed moves.
Run with FORCE=1 to save regardless of the time (checks on the data still apply).
"""
import csv, io, os, sys, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vSE9500jiKFvBw_k0q2m8CPaZ3VbZNv0uIYCe-QSnXpbASoqvwr2RW2hocHl5NVQejXIfVe4CdhX67h"
       "/pub?gid=454467433&single=true&output=csv")
force = os.environ.get("FORCE") == "1"
ny = datetime.now(ZoneInfo("America/New_York"))

text = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")
rows = list(csv.reader(io.StringIO(text)))
spx = next(r for r in rows if r[0] == "IDX_SPX")
quote = spx[5]  # e.g. "30 Oct 16:47", New York time
count = {k: sum(r[0] == k for r in rows) for k in ("SPX", "NDX", "DOW")}
zeros = sum(1 for r in rows if r[0] == "SPX" and r[8] in ("0", "0.00", ""))

problems = []
if count["SPX"] < 400 or count["NDX"] < 90 or count["DOW"] != 30:
    problems.append(f"incomplete data {count}")
if zeros > 0.2 * count["SPX"]:
    problems.append(f"{zeros} S&P stocks show no change, prices look reset")
if not force:
    if ny.weekday() >= 5 or ny.hour * 60 + ny.minute < 16 * 60 + 20:
        problems.append(f"US session not over yet ({ny:%a %H:%M} New York)")
    parts = quote.split()
    if len(parts) < 2 or not parts[0].isdigit() or (int(parts[0]), parts[1]) != (ny.day, f"{ny:%b}"):
        problems.append(f"index quote is from {quote!r}, not today (holiday?)")
if problems:
    print("Not saving:", "; ".join(problems))
    sys.exit(0)

with open("last-session.csv", "w", encoding="utf-8", newline="") as f:
    f.write(text)
print(f"Saved the session of {quote} ({count})")
