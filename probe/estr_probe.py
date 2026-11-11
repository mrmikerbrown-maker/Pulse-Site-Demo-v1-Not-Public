# One-off test, round 2: read FEMP rows from Eurex public reports; try ICE data API. Never fails.
import re, urllib.request, io, zipfile, json
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60)
        b=r.read(); print(f"OK {r.status} {len(b)}B {r.headers.get('Content-Type')} {u}"); return b
    except Exception as e:
        print(f"FAIL {u} -> {e}"); return b""
h=get("https://www.eurex.com/ex-en/data/automatic-file-downloads").decode("utf-8","ignore")
links=sorted(set(re.findall(r'href="(/resource/blob/[^"]+\.zip)"',h)))
names={}
for l in links: names.setdefault(l.rsplit("/",1)[1][:16],[]).append(l)
print("report types:",{k:len(v) for k,v in names.items()})
for l in links: print("  ",l.rsplit("/",1)[1])
# text around each link (labels)
for m in re.finditer(r'href="(/resource/blob/[^"]+\.zip)"',h):
    s=re.sub(r'<[^>]+>|\s+',' ',h[max(0,m.start()-400):m.start()])[-150:]
    print("  label:",s,"->",m.group(1).rsplit("/",1)[1]); 
for kind in ("cb001","cb002"):
    ls=[l for l in links if kind in l.lower()]
    if not ls: continue
    b=get("https://www.eurex.com"+ls[-1]); z=zipfile.ZipFile(io.BytesIO(b)); t=z.read(z.namelist()[0]).decode("latin-1")
    print(kind,"report header:",t[:1500].replace("\n"," "))
    i=t.find("FEMP"); blk=t[max(0,i-1500):i+6000]
    print(f"--- {kind} around first FEMP ---"); print(blk)
for u in ["https://www.ice.com/marketdata/api/productguide/charting/contract-data?productId=83046794&hubId=30019",
          "https://www.ice.com/marketdata/DelayedMarkets.shtml?getContractsAsJson=&productId=83046794&hubId=30019"]:
    t=get(u).decode("utf-8","ignore"); print(t[:2500])
