# One-off test, round 5: Eurex statistics API used by the product page. Never fails.
import re, urllib.request, json, datetime
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept":"application/json"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); b=r.read()
        print("OK",r.status,len(b),r.headers.get("Content-Type"),u); return b
    except Exception as e: print("FAIL",u,e); return b""
h=get("https://www.eurex.com/ex-en/markets/int/mon/3m-euro-str-futures/estr/ECB-Dated-Euro-STR-Futures-4853042").decode("utf-8","ignore")
for m in re.finditer(r'<script type="application/json"(?! data-i18n)[^>]*>(.*?)</script>',h,re.S):
    print("CONFIG:",re.sub(r'\s+',' ',m.group(1))[:1500])
js=get("https://www.eurex.com/resource/themes/eurex-facelift/js/prices-statistics-3466696-67.js").decode("utf-8","ignore")
for k in ("hostUrl","/prices/list","overallstatistics"):
    for m in list(re.finditer(re.escape(k),js))[:4]: print("JS",k,":",js[max(0,m.start()-300):m.start()+300].replace("\n"," "))
