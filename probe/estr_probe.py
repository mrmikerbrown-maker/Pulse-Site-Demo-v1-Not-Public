# One-off test, round 3: which Eurex public report has FEMP settlement prices? Compact output. Never fails.
import re, urllib.request, io, zipfile
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); return r.read()
    except Exception as e: print("FAIL",u,e); return b""
pages=["https://www.eurex.com/ex-en/data/trading-files/product-and-price-report",
       "https://www.eurex.com/ex-en/data/automatic-file-downloads",
       "https://www.eurex.com/ex-en/data/statistics/snapshot-summary-report"]
links={}
for p in pages:
    h=get(p).decode("utf-8","ignore")
    print("PAGE",p,len(h))
    txt=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S)
    txt=re.sub(r'<[^>]+>',' ',txt); txt=re.sub(r'\s+',' ',txt)
    i=txt.find("Product and Price"); print("  text:",txt[i:i+1500] if i>=0 else txt[2000:3500])
    for m in re.findall(r'(?:https://www\.eurex\.com)?(/resource/blob/[^"\x27\s]+\.(?:zip|csv|xlsx?|txt|gz))',h):
        links[m.rsplit("/",1)[1].lower()]=m
by={}
for n,l in links.items():
    k=re.sub(r'\d{8}','',n); by.setdefault(k,[]).append((n,l))
for k,v in sorted(by.items()):
    v.sort(); print("TYPE",k,"count",len(v),"latest",v[-1][0])
for k,v in sorted(by.items()):
    n,l=sorted(v)[-1]
    if not n.endswith(".zip") and not n.endswith(".csv"): continue
    b=get("https://www.eurex.com"+l)
    try:
        if b[:2]==b"PK":
            z=zipfile.ZipFile(io.BytesIO(b)); b=z.read(z.namelist()[0])
    except Exception as e: print(" unzip fail",e); continue
    t=b.decode("latin-1")
    nm=re.search(r'<eur:rptNam>(.*?)<',t); tags=sorted(set(re.findall(r'<eur:(\w*(?:[Ss]e?t?l|[Pp]rc|[Pp]ric)\w*)>',t)))
    print(f"FILE {n} {len(t)}ch name={nm.group(1) if nm else '?'} FEMP={t.count('FEMP')} pricetags={tags[:30]}")
    i=t.find("<eur:prodId>FEMP")
    if i>=0 and tags: print("  FEMP sample:",re.sub(r'\s+',' ',t[i:i+3000]))
    elif not t.lstrip().startswith("<"): 
        print("  head:",t[:400].replace("\n"," | ")); print("  FEMP lines:",[x[:200] for x in t.splitlines() if "FEMP" in x][:10])
