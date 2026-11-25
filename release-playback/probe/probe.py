"""One-off probe (sketch stage): can GitHub Actions get past release numbers and prices for a playback page?
Writes results to release-playback/probe/out/. Never fails the job."""
import json, os, random, re, string, time, datetime as dt, traceback
import requests

OUT = os.path.join(os.path.dirname(__file__), "out"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
report = {}
KEEP = re.compile(r"^(Inflation Rate (YoY|MoM)|Core Inflation Rate (YoY|MoM)|Non Farm Payrolls|Unemployment Rate|Retail Sales MoM|ISM Services PMI|ISM Manufacturing PMI|Core PCE Price Index MoM|GDP Growth Rate QoQ Adv|Average Hourly Earnings MoM|PPI MoM)$")

def cal():
    ev, d = [], dt.datetime(2015, 1, 1)
    end = dt.datetime.utcnow() + dt.timedelta(days=1)
    while d < end:
        e2 = min(d + dt.timedelta(days=60), end)
        u = ("https://economic-calendar.tradingview.com/events?from=%s&to=%s&countries=US&minImportance=0"
             % (d.strftime("%Y-%m-%dT00:00:00.000Z"), e2.strftime("%Y-%m-%dT00:00:00.000Z")))
        r = requests.get(u, headers=dict(UA, Origin="https://www.tradingview.com", Referer="https://www.tradingview.com/"), timeout=40)
        for e in r.json().get("result", []):
            t = (e.get("title") or "").strip()
            if KEEP.match(t):
                ev.append({"t": e["date"][:16] + "Z", "name": t, "period": e.get("period"), "actual": e.get("actual"),
                           "forecast": e.get("forecast"), "previous": e.get("previous"), "unit": e.get("unit"), "scale": e.get("scale")})
        d = e2
        time.sleep(0.5)
    json.dump(ev, open(os.path.join(OUT, "calendar.json"), "w"), separators=(",", ":"))
    report["calendar"] = {"events": len(ev), "with_forecast": sum(1 for e in ev if e["forecast"] is not None),
                          "first": ev[0]["t"] if ev else None}

def _m(f, p):
    s = json.dumps({"m": f, "p": p}, separators=(",", ":"))
    return "~m~%d~m~%s" % (len(s), s)

def bars(ticker, n, res, wait=60):
    from websocket import create_connection
    ws = create_connection("wss://data.tradingview.com/socket.io/websocket", header=["Origin: https://www.tradingview.com"], timeout=30)
    cs = "cs_" + "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    sym = {"symbol": ticker, "adjustment": "splits"}
    if ticker.endswith("!"): sym["backadjustment"] = "default"
    for m in [_m("set_auth_token", ["unauthorized_user_token"]), _m("chart_create_session", [cs, ""]),
              _m("resolve_symbol", [cs, "sym1", "=" + json.dumps(sym)]), _m("create_series", [cs, "s1", "s1", "sym1", res, n, ""])]:
        ws.send(m)
    buf, t0 = "", time.time()
    try:
        while time.time() - t0 < wait:
            r = ws.recv()
            if re.match(r"~m~\d+~m~~h~", r): ws.send(r); continue
            buf += r
            if "series_completed" in r or "symbol_error" in r or "series_error" in r: break
    finally:
        ws.close()
    out = []
    for v in re.findall(r'"v":\[([^\]]+)\]', buf):
        x = v.split(",")
        out.append([int(float(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4])])
    out.sort()
    return out

ASSETS = {"es": "CME_MINI:ES1!", "y10": "TVC:US10Y", "dxy": "TVC:DXY", "eurusd": "FX:EURUSD", "gold": "TVC:GOLD"}

def prices():
    daily, intr = {}, {}
    for k, t in ASSETS.items():
        try:
            b = bars(t, 3000, "1D")
            daily[k] = [[x[0], x[4]] for x in b]
            report["daily_" + k] = {"bars": len(b), "first": dt.datetime.utcfromtimestamp(b[0][0]).isoformat() if b else None}
        except Exception as e:
            report["daily_" + k] = repr(e)
        for res in ["1", "5", "60"]:
            try:
                b = bars(t, 20000, res, wait=90)
                report["intraday_%s_%s" % (k, res)] = {"bars": len(b), "first": dt.datetime.utcfromtimestamp(b[0][0]).isoformat() if b else None}
                intr["%s_%s" % (k, res)] = [[x[0], x[4]] for x in b]
            except Exception as e:
                report["intraday_%s_%s" % (k, res)] = repr(e)
            time.sleep(1)
    json.dump(daily, open(os.path.join(OUT, "daily.json"), "w"), separators=(",", ":"))
    json.dump(intr, open(os.path.join(OUT, "intraday.json"), "w"), separators=(",", ":"))

for f in (cal, prices):
    try: f()
    except Exception: report[f.__name__ + "_error"] = traceback.format_exc()[-800:]
json.dump(report, open(os.path.join(OUT, "report.json"), "w"), indent=1)
print(json.dumps(report, indent=1))
