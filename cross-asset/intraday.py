"""Homepage mini charts: writes intraday.json with the last 48 hours of trading for the S&P 500 and Gold tiles.

  python intraday.py

15-minute closes from the same free TradingView chart feed as build.py (real traded prices, no roll adjustment,
so the chart ends at the price shown on the tile). 48 hours of trading = 192 bars of 15 minutes; weekends and the
daily one-hour break have no bars, so on a Monday the chart reaches back into Friday.
Run by the cross-asset job every 5 minutes on weekdays, straight after build.py.
"""
import datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from feeds import tradingview as feed

MARKETS = {"spx": "CME_MINI:ES1!", "gold": "TVC:GOLD"}   # tile id -> ticker (same as markets.csv)
BARS = 48 * 4                                           # 48 hours of 15-minute bars
OUT = os.path.join(HERE, "intraday.json")


def main():
    try:
        old = json.load(open(OUT)).get("series", {})
    except Exception:
        old = {}
    series = {}
    for k, tk in MARKETS.items():
        try:
            bars = feed.history(tk, n=BARS + 20, adjusted=False, resolution="15")[-BARS:]
        except Exception as e:
            print("intraday", k, "failed:", e)
            bars = []
        # Keep the last good chart if the feed has a bad moment, rather than blanking the tile.
        series[k] = [[int(t), round(c, 2)] for t, c in bars] if len(bars) > 20 else old.get(k, [])
    json.dump({"asof": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "bars": "15min",
               "series": series}, open(OUT, "w"), separators=(",", ":"))
    print("intraday:", {k: len(v) for k, v in series.items()})


if __name__ == "__main__":
    main()
