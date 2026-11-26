"""Volatility Monitor: writes vol-monitor/data.json for the page.

Each gauge gets about 340 daily closes (oldest first), enough for a full past year (252 trading days) behind
every day of the page's 3-month heat map. The page does all the maths (percentile, range, expected move),
so this script only collects prices.

- Option-based volatility indices (VIX, VXN, VHSI, MOVE, OVX, GVZ): TradingView's free chart data,
  the same feed the Cross-Asset page uses (cross-asset/feeds/tradingview.py). Cboe indices are 15 min delayed.
- VSTOXX: STOXX's own daily history file (one day behind, since STOXX publishes after the close).
- Currencies: TradingView daily FX prices. There is no free implied FX volatility feed, so the page turns
  these prices into REALISED volatility (how much the pair actually moved over the last 21 trading days).
Run by the Cross-Asset job (cross-asset.yml) every 15 minutes, weekdays 07:00-22:00 London.
"""
import datetime as dt, json, os, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cross-asset"))
from feeds import tradingview as tv

BARS = 340
TV = {"VIX": "CBOE:VIX", "VXN": "CBOE:VXN", "VHSI": "HSI:VHSI", "MOVE": "TVC:MOVE", "OVX": "CBOE:OVX", "GVZ": "CBOE:GVZ",
      "EURUSD": "FX:EURUSD", "USDJPY": "FX:USDJPY", "GBPUSD": "FX:GBPUSD"}
V2X_URL = "https://www.stoxx.com/document/Indices/Current/HistoricalData/h_v2tx.txt"


def day(t):
    # Daily bars are stamped with their session start (FX: 22:00 UTC the evening before). +6h gives the trading day.
    return (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=6)).date().isoformat()


def main():
    old = {}
    path = os.path.join(HERE, "data.json")
    try:
        old = json.load(open(path)).get("series", {})
    except Exception:
        pass
    series, problems = {}, []
    for k, sym in TV.items():
        try:
            bars = tv.history(sym, BARS)
            if len(bars) < 260:
                raise ValueError("only %d bars" % len(bars))
            nd = 5 if k in ("EURUSD", "GBPUSD") else 3
            series[k] = {"d": [day(t) for t, _ in bars], "c": [round(c, nd) for _, c in bars]}
        except Exception as e:
            problems.append("%s: %s" % (k, e))
            if k in old:
                series[k] = old[k]          # keep the last good copy rather than dropping the gauge
    try:
        r = requests.get(V2X_URL, headers=tv.UA, timeout=30)
        r.raise_for_status()
        rows = [l.split(";") for l in r.text.strip().splitlines()[1:] if l.count(";") == 2][-BARS:]
        series["V2X"] = {"d": [dt.datetime.strptime(a, "%d.%m.%Y").date().isoformat() for a, _, _ in rows],
                         "c": [round(float(v), 3) for _, _, v in rows]}
    except Exception as e:
        problems.append("V2X: %s" % e)
        if "V2X" in old:
            series["V2X"] = old["V2X"]
    if len(series) < 6:
        sys.exit("Too few gauges came back, not saving: " + "; ".join(problems))
    out = {"asof": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
           "problems": problems, "series": series}
    json.dump(out, open(path, "w"), separators=(",", ":"))
    print("Saved %d gauges" % len(series), "; problems: " + "; ".join(problems) if problems else "")


if __name__ == "__main__":
    main()
