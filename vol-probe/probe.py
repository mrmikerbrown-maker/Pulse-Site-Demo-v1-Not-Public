import json, re, math, datetime as dt, requests
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/", "Accept": "application/json, text/plain, */*"}
M = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
def num(x):
    try: return float(str(x).replace(",", "").replace("$", ""))
    except: return None
today = dt.date.today()
for sym in ["FXE", "FXY", "FXB", "UUP", "FXA", "FXC", "FXF"]:
    url = ("https://api.nasdaq.com/api/quote/%s/option-chain?assetclass=etf&limit=3000&fromdate=%s&todate=%s&money=all&type=all"
           % (sym, today + dt.timedelta(days=10), today + dt.timedelta(days=75)))
    try:
        r = requests.get(url, headers=H, timeout=30); j = r.json()
    except Exception as e:
        print(sym, "ERR", e); continue
    d = j.get("data") or {}
    rows = ((d.get("table") or {}).get("rows")) or []
    m = re.search(r"\$([\d,.]+)", d.get("lastTrade") or ""); S = num(m.group(1)) if m else None
    print("==", sym, r.status_code, "price", S, "rows", len(rows), "keys", list(rows[1].keys()) if len(rows) > 1 else None)
    year = None; best = {}
    for x in rows:
        g = x.get("expirygroup") or ""
        if g:
            ym = re.search(r"(\d{4})", g); year = int(ym.group(1)) if ym else year; continue
        if not x.get("expiryDate") or not year: continue
        mon, day = x["expiryDate"].split(); exp = dt.date(year, M[mon[:3].lower()], int(day))
        k = num(x.get("strike"))
        if k is None or S is None: continue
        cb, ca, pb, pa = (num(x.get(f)) for f in ("c_Bid", "c_Ask", "p_Bid", "p_Ask"))
        if abs(k - S) < abs(best.get(exp, (1e9,))[0] - S):
            best[exp] = (k, cb, ca, pb, pa, x.get("c_Volume"), x.get("c_Openinterest"), x.get("p_Volume"), x.get("p_Openinterest"))
    for exp, (k, cb, ca, pb, pa, cv, coi, pv, poi) in sorted(best.items()):
        T = (exp - today).days / 365
        iv = None
        if None not in (cb, ca, pb, pa) and ca > 0 and pa > 0:
            strad = (cb + ca) / 2 + (pb + pa) / 2
            iv = strad / (0.7979 * S * math.sqrt(T)) * 100
        print(" ", exp, "K", k, "call", cb, ca, "put", pb, pa, "vol/OI", cv, coi, pv, poi, "IV~", round(iv, 2) if iv else None)
