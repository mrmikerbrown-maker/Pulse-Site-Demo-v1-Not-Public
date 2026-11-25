import json, sys, requests
sys.path.insert(0, "cross-asset")
from feeds import tradingview as tv
UA = tv.UA
print("== symbol search")
for q in ["VSTOXX","V2TX","CVOL","EUVL","JYVL","GBVL","Nikkei volatility","VHSI","DVOL","OVX","GVZ","VXEEM","currency volatility","FX volatility","EVZ","VFTSE","VDAX","SKEW","VVIX","VIX3M","VIX9D"]:
    try:
        r = requests.get("https://symbol-search.tradingview.com/symbol_search/v3/", params={"text": q, "hl": 0, "lang": "en", "domain": "production"},
                         headers=dict(UA, Origin="https://www.tradingview.com", Referer="https://www.tradingview.com/"), timeout=20)
        js = r.json()
        rows = js.get("symbols", js) if isinstance(js, dict) else js
        print(q, r.status_code, [(s.get("prefix") or s.get("exchange"), s.get("symbol"), s.get("description"), s.get("type")) for s in rows[:8]])
    except Exception as e:
        print(q, "ERR", e)
cands = ["CBOE:VIX","TVC:VIX","CBOE:VVIX","CBOE:VXN","CBOE:RVX","CBOE:VIX9D","CBOE:VIX3M","CBOE:VIX1D","CBOE:OVX","CBOE:GVZ","CBOE:EVZ","CBOE:VXEEM","CBOE:VXD","CBOE:SKEW","TVC:MOVE","ICE:MOVE",
 "EUREX:FVS1!","EUREX:V2TX","TVC:V2TX","TVC:VSTOXX","TVC:JNIV","OSE:JNIV","CBOE:VXTLT","CBOE:VXSLV","TVC:CVIX","NSE:INDIAVIX","TVC:VHSI","HSI:VHSI","CBOE:VX1!","CBOE:VX2!","DERIBIT:DVOL","DERIBIT:BTCDVOL","DERIBIT:ETHDVOL",
 "CME:EUVL","CME:JYVL","CME:BPVL","CME:CVOL","TVC:VDAX","XETR:VDAX","EUREX:VDAX","CBOE:VXFXI","CBOE:VXEWZ","CBOE:VXAPL","CBOE:VXGS"]
print("== scanner")
cols = ["description","close","change","price_52_week_high","price_52_week_low","update_mode"]
r = requests.post("https://scanner.tradingview.com/global/scan", headers=UA, timeout=30, json={"symbols":{"tickers":cands},"columns":cols})
print(r.status_code)
found = {}
for row in r.json().get("data", []):
    print(row["s"], row["d"]); found[row["s"]] = row["d"]
print("missing:", [c for c in cands if c not in found])
print("== history (websocket, 300 daily bars)")
for t in cands:
    try:
        b = tv.history(t, 300)
        print(t, len(b), b[-1] if b else None)
    except Exception as e:
        print(t, "ERR", e)
print("== other sources")
for u in ["https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
          "https://cdn.cboe.com/api/global/us_indices/daily_prices/OVX_History.csv",
          "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS",
          "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EVZCLS",
          "https://www.stoxx.com/document/Indices/Current/HistoricalData/h_v2tx.txt",
          "https://cmegroup-tools.quikstrike.net/",
          "https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&start_timestamp=1700000000000&end_timestamp=1764000000000&resolution=1D"]:
    try:
        r = requests.get(u, headers=UA, timeout=20); print(u, r.status_code, r.text[:200].replace("\n"," | "))
    except Exception as e:
        print(u, "ERR", e)
