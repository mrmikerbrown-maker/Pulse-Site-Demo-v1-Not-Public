# One-off test: can GitHub Actions download ECB Dated €STR futures settlements? Never fails.
import re, urllib.request, io, zipfile, gzip
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40)
        b=r.read(); print(f"OK {r.status} {len(b)}B {r.headers.get('Content-Type')} {u}"); return b
    except Exception as e:
        print(f"FAIL {u} -> {e}"); return b""
pages=["https://www.eurex.com/ex-en/data/trading-files/product-and-price-report",
 "https://www.eurex.com/ex-en/data/free-reference-data-api",
 "https://www.eurex.com/ex-en/data/automatic-file-downloads",
 "https://www.eurex.com/ex-en/data/statistics",
 "https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/ECB-Dated-Euro-STR-Futures-4853042"]
cands=set()
for p in pages:
    h=get(p).decode("utf-8","ignore")
    for m in re.findall(r'(?:href|src|data-[a-z-]+)="([^"]+)"',h):
        ml=m.lower()
        if any(k in ml for k in ("csv","zip","xls","json","api","price","settle","quote","report","download","4853")) and not ml.endswith((".css",".png",".svg",".jpg")):
            print("   link:",m[:200])
            if any(k in ml for k in (".csv",".zip",".gz","json")): cands.add(m if m.startswith("http") else "https://www.eurex.com"+m)
    for m in re.findall(r'https?://[a-z0-9.-]*(?:api|data)[a-z0-9.-]*\.[a-z]+[^"\' <]*',h)[:20]: print("   apiurl:",m[:200])
for c in sorted(cands)[:15]:
    b=get(c)
    if not b: continue
    try:
        if b[:2]==b"PK":
            z=zipfile.ZipFile(io.BytesIO(b)); print("   zip:",z.namelist()[:5]); b=z.read(z.namelist()[0])
        elif b[:2]==b"\x1f\x8b": b=gzip.decompress(b)
    except Exception as e: print("   unpack fail",e)
    t=b.decode("utf-8","ignore")
    print("   head:",t[:300].replace("\n"," | "))
    hits=[l for l in t.splitlines() if "FEMP" in l or "EMP" in l.split(";")[:3]]
    print("   FEMP lines:",len(hits)); [print("     ",l[:250]) for l in hits[:15]]
# Eurex public quotes JSON used by product pages (guesses)
for u in ["https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/4853044!quotesSingleViewFuture",
          "https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/ECB-Dated-Euro-STR-Futures-4853042!quotesSingleViewFuture?productGroupId=184&productId=4853044"]:
    t=get(u).decode("utf-8","ignore"); print("   rows with 'Settle':",len(re.findall("ettle",t))); 
    for m in re.findall(r'<tr[^>]*>(.*?)</tr>',t,re.S)[:12]: print("     ",re.sub(r'<[^>]+>|\s+',' ',m)[:200])
# ICE
for u in ["https://www.ice.com/products/83046794/ECB-Dated-ESTR-Futures/data",
          "https://www.ice.com/marketdata/api/productguide/charting/contract-data?productId=83046794&hubId=0"]:
    t=get(u).decode("utf-8","ignore"); print("   ",t[:300].replace("\n"," "))
    for m in re.findall(r'hubId[=:"\s]+(\d+)',t)[:5]: print("   hubId",m)
