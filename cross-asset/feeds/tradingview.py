"""TradingView price feed for the cross-asset page.

Every feed module gives build.py the same two functions, so a different feed can be dropped in later:
  quotes(tickers)       -> {ticker: {"price", "chg_abs", "chg_pct", "perf_w", "perf_m", "perf_ytd", "mode"}}
                           chg_* = since the previous daily close; perf_* = % change over 1 week / 1 month / year to date.
  history(ticker, n)    -> [(unix_seconds, close), ...] daily closes, oldest first, about n bars.
                           resolution="15" gives 15-minute bars instead (used for the homepage 48-hour charts).
                           Futures ("ES1!" = front month) come back-adjusted (roll gaps taken out by shifting
                           older prices), unless adjusted=False, which gives the real traded prices.
The ticker for each market comes from that feed's column in markets.csv (column name = module name).
Free, delayed data: quotes from TradingView's screener, history from its chart data service. No login or key.
"""
import json, random, re, string, time
import requests

NAME = "TradingView"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
COLS = ["close", "change_abs", "change", "Perf.W", "Perf.1M", "Perf.YTD", "update_mode"]


def quotes(tickers):
    r = requests.post("https://scanner.tradingview.com/global/scan", headers=UA, timeout=30,
                      json={"symbols": {"tickers": list(tickers)}, "columns": COLS})
    r.raise_for_status()
    out = {}
    for row in r.json().get("data", []):
        d = dict(zip(COLS, row["d"]))
        if d["close"] is None:
            continue
        out[row["s"]] = {"price": d["close"], "chg_abs": d["change_abs"], "chg_pct": d["change"],
                         "perf_w": d["Perf.W"], "perf_m": d["Perf.1M"], "perf_ytd": d["Perf.YTD"], "mode": d["update_mode"]}
    return out


def _m(f, p):
    s = json.dumps({"m": f, "p": p}, separators=(",", ":"))
    return "~m~%d~m~%s" % (len(s), s)


def history(ticker, n=300, adjusted=True, resolution="1D"):
    from websocket import create_connection
    ws = create_connection("wss://data.tradingview.com/socket.io/websocket",
                           header=["Origin: https://www.tradingview.com"], timeout=20)
    cs = "cs_" + "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    for m in [_m("set_auth_token", ["unauthorized_user_token"]), _m("chart_create_session", [cs, ""]),
              _m("resolve_symbol", [cs, "sym1", "=" + json.dumps(dict({"symbol": ticker, "adjustment": "splits"},
                                                                        **({"backadjustment": "default"} if adjusted and ticker.endswith("!") else {})))]),
              _m("create_series", [cs, "s1", "s1", "sym1", resolution, n, ""])]:
        ws.send(m)
    buf, t0 = "", time.time()
    try:
        while time.time() - t0 < 25:
            r = ws.recv()
            if re.match(r"~m~\d+~m~~h~", r):   # heartbeat: echo it back
                ws.send(r)
                continue
            buf += r
            if "series_completed" in r or "symbol_error" in r or "series_error" in r:
                break
    finally:
        ws.close()
    bars = []
    for v in re.findall(r'"v":\[([^\]]+)\]', buf):
        x = v.split(",")
        bars.append((float(x[0]), float(x[4])))
    bars.sort()
    return bars
