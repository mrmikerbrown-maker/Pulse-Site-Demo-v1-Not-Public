"""One-off check of which data sources work from GitHub Actions (not part of the site)."""
import requests, re, io, datetime as dt
UA = {"User-Agent": "Mozilla/5.0"}
r = requests.get("https://www.frbsf.org/research-and-insights/data-and-indicators/monetary-policy-surprises/", headers=UA, timeout=30)
links = sorted(set(re.findall(r'(?:href|src)="([^"]+)"', r.text)))
print("SF links with xls/upload/csv:")
for l in links:
    if re.search(r"xls|csv|upload|download", l, re.I): print("  ", l)
for m in re.finditer(r"(updated|through|sample|last)[^<]{0,120}", r.text, re.I):
    print(" text:", m.group(0)[:140])
for l in links:
    if re.search(r"\.xlsx?($|\?)", l, re.I):
        try:
            import pandas as pd
            u = l if l.startswith("http") else "https://www.frbsf.org" + l
            b = requests.get(u, headers=UA, timeout=60).content
            x = pd.read_excel(io.BytesIO(b), sheet_name=None)
            for k, df in x.items():
                print("SHEET", k, df.shape); print(df.head(3).to_string()[:800]); print(df.tail(3).to_string()[:800])
        except Exception as e:
            print("xlsx fail", repr(e)[:200])
def y(tk, rng):
    j = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}", params={"range": rng, "interval": "1d"}, headers=UA, timeout=30).json()["chart"]["result"][0]
    ts = j["timestamp"]; return f"{len(ts)} bars {dt.datetime.utcfromtimestamp(ts[0]).date()} to {dt.datetime.utcfromtimestamp(ts[-1]).date()}"
for tk in ["ZQ=F", "^IRX", "ZT=F", "EURUSD=X", "^GSPC"]:
    try: print("Yahoo 10y daily", tk, y(tk, "10y"))
    except Exception as e: print(tk, "FAIL", repr(e)[:100])
