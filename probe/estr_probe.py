# One-off test, round 4. Never fails.
import re, urllib.request, io, zipfile, collections
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u,hdr=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={**UA,**(hdr or {})}),timeout=60); b=r.read()
        print("OK",r.status,len(b),r.headers.get("Content-Type"),u); return b
    except Exception as e: print("FAIL",u,e); return b""
# 1) the JS that fills the price table on the product page
js=get("https://www.eurex.com/resource/themes/eurex-facelift/js/prices-statistics-3466696-67.js").decode("utf-8","ignore")
for m in sorted(set(re.findall(r'["\'](/?[\w\-/\.!]*(?:api|quotes|prices|data|json|\!)[\w\-/\.!?=&]*)["\']',js)))[:60]: print("  js str:",m)
for m in re.finditer(r'(ajax|fetch|url)\s*[:(]',js):
    print("  js ctx:",js[max(0,m.start()-150):m.start()+250].replace("\n"," "))
# 2) product page HTML around prices / data attributes
h=get("https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/ECB-Dated-Euro-STR-Futures-4853042").decode("utf-8","ignore")
for m in re.finditer(r'(future-prices|prices-statistics|data-url|data-src|data-ajax|data-endpoint)',h):
    print("  html ctx:",re.sub(r'\s+',' ',h[max(0,m.start()-300):m.start()+400]))
# 3) cb001 tags + FEMP block
ph=get("https://www.eurex.com/ex-en/data/trading-files/product-and-price-report").decode("utf-8","ignore")
ls=sorted(set(re.findall(r'(?:https://www\.eurex\.com)?(/resource/blob/[^"\x27\s]+cb001publi\d+\.zip)',ph)),key=lambda l:l[-12:])
b=get("https://www.eurex.com"+ls[-1]); z=zipfile.ZipFile(io.BytesIO(b)); t=z.read(z.namelist()[0]).decode("latin-1")
print("cb001 distinct tags:",sorted(collections.Counter(re.findall(r'<eur:(\w+)>',t)).items(),key=lambda x:-x[1])[:120])
i=t.find("<eur:prodId>FEMP"); print("cb001 FEMP block:",re.sub(r'\s+',' ',t[max(0,i-600):i+5000]))
