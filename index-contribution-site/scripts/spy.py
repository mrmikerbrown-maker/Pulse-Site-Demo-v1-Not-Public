"""Download State Street's daily SPY holdings and save spy-weights.csv (symbol, weight %) for the website.

SPY's weights are struck at the previous close, which is exactly what the site needs to turn
each stock's % move into S&P 500 points. Standard library only: an .xlsx file is a zip of XML.
"""
import csv, io, re, sys, urllib.request, zipfile, xml.etree.ElementTree as ET
from datetime import datetime

URL = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (index-contribution-site)"})
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
shared = []
if "xl/sharedStrings.xml" in z.namelist():
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
        shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
rows = []
for r in ET.fromstring(z.read(sheet)).iter("{%s}row" % NS["m"]):
    out = {}
    for c in r.findall("m:c", NS):
        col = re.match(r"[A-Z]+", c.get("r")).group()
        v = c.find("m:v", NS)
        is_ = c.find("m:is", NS)
        if c.get("t") == "s" and v is not None: val = shared[int(v.text)]
        elif is_ is not None: val = "".join(t.text or "" for t in is_.iter("{%s}t" % NS["m"]))
        else: val = v.text if v is not None else ""
        out[col] = val.strip()
    rows.append(out)

asof = ""
for r in rows[:10]:
    for v in r.values():
        m = re.search(r"As of (\d{1,2}-\w{3}-\d{4})", v)
        if m: asof = datetime.strptime(m.group(1), "%d-%b-%Y").strftime("%Y-%m-%d")
hi = next(i for i, r in enumerate(rows) if "Ticker" in r.values() and "Weight" in r.values())
cols = {v: k for k, v in rows[hi].items()}
out = []
for r in rows[hi + 1:]:
    t, w = r.get(cols["Ticker"], ""), r.get(cols["Weight"], "")
    try: w = float(w)
    except ValueError: continue
    if not re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", t) or w <= 0: continue
    out.append((t, w))

total = sum(w for _, w in out)
if not asof or len(out) < 480 or not 95 < total < 101:
    sys.exit(f"SPY file looks wrong: as of {asof!r}, {len(out)} stocks, weights sum {total:.2f}")
# Keep the previous day's file too: after the close the site shows that session, which needs the weights
# from the close before it, not the ones State Street posts that evening.
import os, shutil
if os.path.exists("spy-weights.csv"):
    old = open("spy-weights.csv").readline().strip().split(",")[-1]
    if old != asof: shutil.copy("spy-weights.csv", "spy-weights-prev.csv")
with open("spy-weights.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["asof", asof])
    for t, wt in out: w.writerow([t, f"{wt:.6f}"])
print(f"Saved {len(out)} SPY weights as of {asof}, sum {total:.3f}%")
