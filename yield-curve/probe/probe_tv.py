"""Temporary probe: can a GitHub job read government bond yields from TradingView's public screener?"""
import json, os, requests
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"); os.makedirs(OUT, exist_ok=True)
T = {"US": ["01M","03M","06M","01Y","02Y","03Y","05Y","07Y","10Y","20Y","30Y"],
     "DE": ["03M","06M","01Y","02Y","03Y","05Y","07Y","10Y","15Y","20Y","30Y"],
     "GB": ["01M","03M","06M","01Y","02Y","03Y","05Y","07Y","10Y","15Y","20Y","30Y"]}
tick = ["TVC:%s%s" % (c, m) for c, ms in T.items() for m in ms]
cols = ["description", "close", "change_abs", "Perf.W", "Perf.1M", "Perf.3M", "Perf.Y", "update_mode", "type"]
res = {}
for mkt in ["global", "bond", "cfd", "america"]:
    try:
        r = requests.post(f"https://scanner.tradingview.com/{mkt}/scan", headers=UA, timeout=60,
                          json={"symbols": {"tickers": tick, "query": {"types": []}}, "columns": cols})
        j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
        rows = {d["s"]: dict(zip(cols, d["d"])) for d in j.get("data", [])} if isinstance(j.get("data"), list) else j
        res[mkt] = {"status": r.status_code, "n": len(rows) if isinstance(rows, dict) else 0, "rows": rows}
        print(mkt, r.status_code, res[mkt]["n"])
    except Exception as e:
        res[mkt] = repr(e); print(mkt, e)
json.dump(res, open(f"{OUT}/tv.json", "w"), indent=1)
