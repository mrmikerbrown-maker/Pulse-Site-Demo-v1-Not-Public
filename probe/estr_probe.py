# One-off test, round 6: Eurex daily statistics API (settlement per contract). Never fails.
import urllib.request, json
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept":"application/json",
    "Referer":"https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/ECB-Dated-Euro-STR-Futures-4853042"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); b=r.read()
        print("OK",r.status,len(b),r.headers.get("Content-Type"),u); return b
    except Exception as e: print("FAIL",u,e); return b""
for d in ("20261110","20261020","20250915"):
    b=get(f"https://www.eurex.com/api/v1/overallstatistics/4853044?busdate={d}&filtertype=overview")
    print(b[:4000].decode("utf-8","ignore"))
# also the 3M €STR future (FST3) and Euribor for comparison: product ids unknown, skip
