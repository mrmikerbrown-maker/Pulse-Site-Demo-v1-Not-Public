# One-off probe: which free sources answer from GitHub Actions. Always exits 0.
import json, urllib.request, urllib.error, datetime as dt
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return 0, str(e).encode()
def show(name, url, data=None, headers=None, summarise=None):
    code, body = get(url, data, headers)
    print(f"\n=== {name}: HTTP {code}, {len(body)} bytes")
    if code == 200 and summarise:
        try: print(summarise(json.loads(body)))
        except Exception as e: print("parse fail", e, body[:300])
    else:
        print(body[:300])
tom = (dt.date.today() + dt.timedelta(days=1)).isoformat()

def cboe(j):
    d = j["data"]; o = d["options"]
    exps = sorted({x["option"][-15:-9] for x in o})
    return f"price {d.get('current_price')} iv30 {d.get('iv30')} contracts {len(o)} expiries {exps[:6]} sample {o[0]}"
show("CBOE delayed options NVDA", "https://cdn.cboe.com/api/global/delayed_quotes/options/NVDA.json", summarise=cboe)
show("CBOE delayed options SPY-sized AAPL", "https://cdn.cboe.com/api/global/delayed_quotes/options/AAPL.json", summarise=lambda j: f"contracts {len(j['data']['options'])}")
nh = {"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
show("Nasdaq earnings calendar " + tom, "https://api.nasdaq.com/api/calendar/earnings?date=" + tom, headers=nh,
     summarise=lambda j: f"rows {len((j['data'] or {}).get('rows') or [])} first {((j['data'] or {}).get('rows') or [None])[:2]}")
show("Nasdaq earnings surprise NVDA", "https://api.nasdaq.com/api/company/NVDA/earnings-surprise", headers=nh, summarise=lambda j: str(j)[:500])
show("Nasdaq option chain NVDA", "https://api.nasdaq.com/api/quote/NVDA/option-chain?assetclass=stocks&limit=20", headers=nh, summarise=lambda j: str(j)[:400])
show("Nasdaq historical NVDA", "https://api.nasdaq.com/api/quote/NVDA/historical?assetclass=stocks&fromdate=2024-01-01&limit=9999", headers=nh,
     summarise=lambda j: f"rows {len(j['data']['tradesTable']['rows'])} first {j['data']['tradesTable']['rows'][0]}")
show("Yahoo chart NVDA 3y daily", "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?range=3y&interval=1d&events=earn",
     summarise=lambda j: f"bars {len(j['chart']['result'][0]['timestamp'])} events {list((j['chart']['result'][0].get('events') or {}).keys())}")
show("Yahoo options v7 NVDA", "https://query2.finance.yahoo.com/v7/finance/options/NVDA", summarise=lambda j: str(j)[:300])
tvq = json.dumps({"columns": ["name", "close", "earnings_release_next_date", "earnings_release_next_time", "earnings_release_date", "market_cap_basic"],
                  "filter": [{"left": "earnings_release_next_date", "operation": "in_range", "right": [int(dt.datetime.now().timestamp()), int(dt.datetime.now().timestamp()) + 14*86400]},
                             {"left": "market_cap_basic", "operation": "greater", "right": 20e9}],
                  "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}, "range": [0, 60]}).encode()
show("TradingView scanner earnings next 14d >$20bn", "https://scanner.tradingview.com/america/scan", data=tvq,
     headers={"Content-Type": "application/json", "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"},
     summarise=lambda j: f"total {j.get('totalCount')} rows {[r['d'] for r in j['data'][:12]]}")
show("SEC EDGAR submissions NVDA", "https://data.sec.gov/submissions/CIK0001045810.json", headers={"User-Agent": "AlphaPulse research bot admin@example.com"},
     summarise=lambda j: f"8-K 2.02 dates {[d for d,f,i in zip(j['filings']['recent']['filingDate'], j['filings']['recent']['form'], j['filings']['recent']['items']) if f=='8-K' and '2.02' in i][:10]}")
show("AlphaVantage earnings calendar demo", "https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey=demo")
