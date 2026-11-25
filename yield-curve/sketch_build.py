"""Sketch only: turns the probe downloads into data.json. The real job would fetch the same files nightly."""
import csv, json, os, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, "probe", "out")
def d(s): return dt.datetime.strptime(s, "%m/%d/%Y").date().isoformat()
# US: Treasury par yield curve
UCOL = {"3 Mo": .25, "6 Mo": .5, "1 Yr": 1, "2 Yr": 2, "3 Yr": 3, "5 Yr": 5, "7 Yr": 7, "10 Yr": 10, "20 Yr": 20, "30 Yr": 30}
us = {}
for y in (2024, 2025, 2026):
    rows = list(csv.DictReader(open(f"{P}/ust-{y}.csv", encoding="utf-8-sig")))
    for r in rows:
        pts = {}
        for c, m in UCOL.items():
            v = r.get(c, "")
            if v not in ("", "N/A"): pts[m] = float(v)
        if len(pts) == len(UCOL): us[d(r["Date"])] = pts
# Germany: Bundesbank Svensson zero-coupon
de = {}
for code, m in [("R01XX",1),("R02XX",2),("R03XX",3),("R05XX",5),("R07XX",7),("R10XX",10),("R15XX",15),("R20XX",20),("R30XX",30)]:
    for line in open(f"{P}/bund-{code}.csv", encoding="utf-8-sig"):
        p = line.strip().split(",")
        if len(p) >= 2 and p[0][:2] == "20" and p[1] not in (".", ""):
            de.setdefault(p[0], {})[m] = float(p[1])
de = {k: v for k, v in de.items() if len(v) == 9}
# UK: Bank of England fitted nominal zero-coupon (spot) curve
uk = {}
for f in os.listdir(P):
    if f.startswith("gilt-") and ("2025_to_present" in f or "2016_to_2024" in f or "current_month" in f):
        for k, v in json.load(open(os.path.join(P, f))).items():
            pts = {float(a): b for a, b in v.items() if float(a) in (.5,1,2,3,5,7,10,15,20,30)}
            if all(m in pts for m in (2.0,5.0,10.0,30.0)): uk[k] = pts
def pack(series):
    days = sorted(k for k in series if k >= "2024-01-01")
    mats = sorted(series[days[-1]])
    return {"mats": mats, "dates": days, "y": [[round(series[k][m], 3) if m in series[k] else None for m in mats] for k in days]}
out = {"generated": "2026-11-25T11:10:00Z",
       "us": dict(pack(us), name="US Treasuries", kind="par"),
       "de": dict(pack(de), name="German Bunds", kind="zero"),
       "uk": dict(pack(uk), name="UK Gilts", kind="zero")}
for k in ("us", "de", "uk"): print(k, out[k]["dates"][0], out[k]["dates"][-1], len(out[k]["dates"]), out[k]["mats"], out[k]["y"][-1])
json.dump(out, open(os.path.join(H, "data.json"), "w"), separators=(",", ":"))
print(os.path.getsize(os.path.join(H, "data.json")))
