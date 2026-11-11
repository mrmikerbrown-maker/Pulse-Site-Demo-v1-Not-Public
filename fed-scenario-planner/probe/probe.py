"""One-off check of which data sources work from GitHub Actions (not part of the site)."""
import requests, re
UA = {"User-Agent": "Mozilla/5.0"}
def y(tk, rng="max"):
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}", params={"range": rng, "interval": "1d"}, headers=UA, timeout=30)
        j = r.json()["chart"]
        if j.get("error"): return f"ERR {j['error'].get('code')}"
        res = j["result"][0]; ts = res.get("timestamp") or []
        import datetime as dt
        return f"{len(ts)} bars {dt.datetime.utcfromtimestamp(ts[0]).date() if ts else '-'} to {dt.datetime.utcfromtimestamp(ts[-1]).date() if ts else '-'}"
    except Exception as e:
        return "FAIL " + repr(e)[:100]
for tk in ["ZQZ19.CBT", "ZQF24.CBT", "ZQZ25.CBT", "ZQZ26.CBT", "ZQF27.CBT", "ZQ=F", "SR3=F", "^IRX", "EURUSD=X", "^GSPC", "GC=F", "^TNX", "2YY=F", "ZT=F"]:
    print("Yahoo", tk, y(tk))
for name, url in [("SF Fed page", "https://www.frbsf.org/research-and-insights/data-and-indicators/monetary-policy-surprises/"),
                  ("FRED DGS2", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2015-01-01"),
                  ("FRED DFEDTARU", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARU&cosd=2015-01-01")]:
    try:
        r = requests.get(url, headers=UA, timeout=30)
        links = re.findall(r'href="([^"]+\.(?:xlsx|csv|xls))"', r.text)[:10]
        print(name, r.status_code, len(r.text), links)
    except Exception as e:
        print(name, "FAIL", repr(e)[:100])
