import json, sys, requests
sys.path.insert(0, "cross-asset")
from feeds import tradingview as tv
UA = tv.UA
for u in ["https://cdn.cboe.com/api/global/delayed_quotes/options/FXE.json","https://cdn.cboe.com/api/global/delayed_quotes/options/FXY.json",
          "https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json",
          "https://www.cmegroup.com/services/cvol/EUVL","https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-group-volatility-indexes.html"]:
    try:
        r = requests.get(u, headers=UA, timeout=20); print(u, r.status_code, len(r.content), r.text[:300].replace("\n"," "))
    except Exception as e: print(u, "ERR", e)
try:
    r = requests.get("https://cdn.cboe.com/api/global/delayed_quotes/options/FXE.json", headers=UA, timeout=20).json()["data"]
    print("FXE iv30", r.get("iv30"), "price", r.get("current_price"))
    r = requests.get("https://cdn.cboe.com/api/global/delayed_quotes/options/FXY.json", headers=UA, timeout=20).json()["data"]
    print("FXY iv30", r.get("iv30"), "price", r.get("current_price"))
except Exception as e: print("ivERR", e)
out = {}
for k, t in [("VIX","CBOE:VIX"),("VXN","CBOE:VXN"),("MOVE","TVC:MOVE"),("OVX","CBOE:OVX"),("GVZ","CBOE:GVZ"),("DVOL","DERIBIT:DVOL"),("VHSI","HSI:VHSI"),("VXEEM","CBOE:VXEEM"),
             ("EURUSD","FX:EURUSD"),("USDJPY","FX:USDJPY"),("GBPUSD","FX:GBPUSD")]:
    b = tv.history(t, 320)
    out[k] = {"t": [int(x[0]) for x in b], "c": [round(x[1], 5 if k in ("EURUSD","GBPUSD") else 3) for x in b]}
r = requests.get("https://www.stoxx.com/document/Indices/Current/HistoricalData/h_v2tx.txt", headers=UA, timeout=20)
rows = [l.split(";") for l in r.text.strip().splitlines()[1:]]
rows = rows[-320:]
import datetime
out["V2X"] = {"t": [int(datetime.datetime.strptime(a, "%d.%m.%Y").replace(tzinfo=datetime.timezone.utc).timestamp()) for a, _, _ in rows], "c": [round(float(v), 3) for _, _, v in rows]}
print("V2X last", rows[-3:])
open("vol-probe/data.json","w").write(json.dumps(out, separators=(",", ":")))
