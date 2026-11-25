# Temporary probe: which free sources answer from GitHub Actions for a cross-asset dashboard. Removed after the test.
import requests, json, time
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
def show(name,fn):
    t=time.time()
    try:
        r=fn(); print(f"\n=== {name}: HTTP {r.status_code} {len(r.content)}B {time.time()-t:.1f}s"); print(r.text[:1500])
    except Exception as e: print(f"\n=== {name}: ERROR {e}")
TICK=["SP:SPX","NASDAQ:NDX","DJ:DJI","TVC:UKX","XETR:DAX","EURONEXT:PX1","TVC:SX5E","TVC:NI225","HSI:HSI","ASX:XJO","TSX:TSX","CBOE:VIX",
 "TVC:US02Y","TVC:US10Y","TVC:US30Y","TVC:DE10Y","TVC:DE02Y","TVC:GB10Y","TVC:GB02Y","TVC:JP10Y","TVC:IT10Y","TVC:FR10Y",
 "TVC:DXY","FX:EURUSD","FX:GBPUSD","FX:USDJPY","FX:AUDUSD","FX:USDCAD","FX:USDCHF","FX:NZDUSD","FX:EURGBP","FX_IDC:USDCNH",
 "TVC:UKOIL","TVC:USOIL","NYMEX:NG1!","TVC:GOLD","TVC:SILVER","COMEX:HG1!","BITSTAMP:BTCUSD"]
show("TradingView scanner global",lambda: requests.post("https://scanner.tradingview.com/global/scan",headers=UA,
  json={"symbols":{"tickers":TICK},"columns":["description","close","change","change_abs","Perf.W","Perf.1M","Perf.YTD","High.1M","Low.1M","update_mode","currency"]},timeout=30))
show("TradingView OHLC history? (scanner Perf columns above)",lambda: requests.get("https://scanner.tradingview.com/symbol?symbol=TVC:US10Y&fields=close,change",headers=UA,timeout=30))
show("US Treasury par yields XML",lambda: requests.get("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=202611",headers=UA,timeout=30))
show("ECB FX reference rates",lambda: requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",headers=UA,timeout=30))
show("FRED graph CSV DGS10",lambda: requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10,DCOILBRENTEU&cosd=2026-11-01",headers=UA,timeout=30))
show("Yahoo chart ^GSPC",lambda: requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=5d&interval=1d",headers=UA,timeout=30))
show("Nasdaq index quote SPX",lambda: requests.get("https://api.nasdaq.com/api/quote/SPX/info?assetclass=index",headers={**UA,"Origin":"https://www.nasdaq.com","Referer":"https://www.nasdaq.com/"},timeout=30))
show("Cboe delayed _SPX",lambda: requests.get("https://cdn.cboe.com/api/global/delayed_quotes/quotes/_SPX.json",headers=UA,timeout=30))
show("Bundesbank Bund 10y yield",lambda: requests.get("https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZAR.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?lastNObservations=3&format=csv",headers=UA,timeout=30))
show("BoE gilt 10y IUDMNPY",lambda: requests.get("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Nov/2026&Dateto=now&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y",headers=UA,timeout=30))
