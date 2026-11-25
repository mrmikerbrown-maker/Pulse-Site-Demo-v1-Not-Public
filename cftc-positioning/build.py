"""CFTC positioning: builds data.json from the CFTC's free Commitments of Traders API (publicreporting.cftc.gov).
Three trader groups are saved for each market, and the page picks between them:
  nc = Legacy report, non-commercial traders (what news wires call "CFTC speculators"; standard for FX, indices, rates).
  lf = Traders in Financial Futures report, leveraged funds (hedge funds) - financial futures only.
  mm = Disaggregated report, managed money (hedge funds and CTAs) - commodities only; the standard speculator measure there.
The page's default ("Speculators") is nc for financial futures and mm for commodities; "Hedge funds only" is lf / mm.
Futures only. Positions are as of Tuesday; the CFTC publishes them Friday 15:30 New York (20:30 London).
Usage: python build.py            (fetch from the API)
       python build.py <folder>   (read legacy-hist.json, tff-hist.json, disagg-hist.json saved in <folder>)"""
import json, sys, time, datetime as dt
# code, short name, long name, group, what a long position means
MARKETS = [
 ("099741","EUR","Euro","FX","Long = betting EUR/USD rises"),
 ("097741","JPY","Japanese yen","FX","Long = betting the yen rises (USD/JPY falls)"),
 ("096742","GBP","British pound","FX","Long = betting GBP/USD rises"),
 ("092741","CHF","Swiss franc","FX","Long = betting the franc rises (USD/CHF falls)"),
 ("090741","CAD","Canadian dollar","FX","Long = betting the Canadian dollar rises (USD/CAD falls)"),
 ("232741","AUD","Australian dollar","FX","Long = betting AUD/USD rises"),
 ("112741","NZD","New Zealand dollar","FX","Long = betting NZD/USD rises"),
 ("095741","MXN","Mexican peso","FX","Long = betting the peso rises (USD/MXN falls)"),
 ("098662","DXY","US dollar index","FX","Long = betting the dollar rises against six major currencies"),
 ("042601","UST 2Y","US 2-year note","Rates","Long = betting 2-year yields fall"),
 ("044601","UST 5Y","US 5-year note","Rates","Long = betting 5-year yields fall"),
 ("043602","UST 10Y","US 10-year note","Rates","Long = betting 10-year yields fall"),
 ("043607","Ultra 10Y","Ultra 10-year note","Rates","Long = betting 10-year yields fall"),
 ("020601","UST Bond","US Treasury bond","Rates","Long = betting long-term yields fall"),
 ("020604","Ultra Bond","Ultra Treasury bond","Rates","Long = betting 30-year yields fall"),
 ("134741","SOFR 3M","3-month SOFR","Rates","Long = betting on lower short-term rates (more Fed easing)"),
 ("045601","Fed funds","30-day fed funds","Rates","Long = betting on lower short-term rates (more Fed easing)"),
 ("13874A","S&P 500","E-mini S&P 500","Equities","Long = betting the S&P 500 rises"),
 ("209742","Nasdaq 100","E-mini Nasdaq 100","Equities","Long = betting the Nasdaq 100 rises"),
 ("124603","Dow","E-mini Dow ($5)","Equities","Long = betting the Dow rises"),
 ("239742","Russell 2000","E-mini Russell 2000","Equities","Long = betting the Russell 2000 rises"),
 ("1170E1","VIX","VIX futures","Equities","Long = betting volatility rises"),
 ("133741","Bitcoin","CME bitcoin","Equities","Long = betting bitcoin rises"),
 ("067651","WTI crude","WTI crude oil","Commodities","Long = betting oil rises"),
 ("06765T","Brent","Brent crude (NYMEX)","Commodities","Long = betting Brent rises"),
 ("023651","Nat gas","US natural gas","Commodities","Long = betting gas rises"),
 ("088691","Gold","Gold","Commodities","Long = betting gold rises"),
 ("084691","Silver","Silver","Commodities","Long = betting silver rises"),
 ("085692","Copper","Copper","Commodities","Long = betting copper rises"),
 ("076651","Platinum","Platinum","Commodities","Long = betting platinum rises"),
 ("002602","Corn","Corn","Commodities","Long = betting corn rises"),
 ("001602","Wheat","Wheat (Chicago)","Commodities","Long = betting wheat rises"),
 ("005602","Soybeans","Soybeans","Commodities","Long = betting soybeans rise"),
 ("080732","Sugar","Sugar No. 11","Commodities","Long = betting sugar rises"),
 ("083731","Coffee","Coffee","Commodities","Long = betting coffee rises"),
 ("073732","Cocoa","Cocoa","Commodities","Long = betting cocoa rises"),
 ("033661","Cotton","Cotton","Commodities","Long = betting cotton rises"),
]
API = "https://publicreporting.cftc.gov/resource/"
SETS = {"legacy": "6dca-aqww", "tff": "gpe5-46if", "disagg": "72hh-3qpy"}
WEEKS = 157   # 3 years of history (+1 for the week-on-week change)
since = (dt.date.today() - dt.timedelta(weeks=WEEKS + 2)).isoformat()

def fetch(name):
    if len(sys.argv) > 1:
        return json.load(open(f"{sys.argv[1]}/{name}-hist.json"))
    inlist = ",".join(f"'{m[0]}'" for m in MARKETS)
    for i in range(4):
        try:
            r = __import__("requests").get(API + SETS[name] + ".json", params={
                "$where": f"cftc_contract_market_code in({inlist}) AND report_date_as_yyyy_mm_dd > '{since}'",
                "$limit": 50000, "$order": "report_date_as_yyyy_mm_dd"}, timeout=120)
            r.raise_for_status(); return r.json()
        except Exception as e:
            print(name, "try", i + 1, e); time.sleep(20 * (i + 1))
    raise SystemExit(f"Could not fetch {name}")

def series(rows, lk, sk):
    out = {}
    for r in rows:
        d = r["report_date_as_yyyy_mm_dd"][:10]
        if d <= since: continue
        out.setdefault(r["cftc_contract_market_code"], {})[d] = (int(float(r[lk])), int(float(r[sk])), int(float(r["open_interest_all"])))
    return out

leg, tff, dis = fetch("legacy"), fetch("tff"), fetch("disagg")
spec = series(leg, "noncomm_positions_long_all", "noncomm_positions_short_all")
lev = series(tff, "lev_money_positions_long", "lev_money_positions_short")
mm = series(dis, "m_money_positions_long_all", "m_money_positions_short_all")
dates = sorted({d for s in spec.values() for d in s})[-WEEKS:]
if len(dates) < 100: raise SystemExit("Too little data came back; keeping the last good file")
out = {"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "asof": dates[-1], "dates": dates, "markets": []}
for code, short, name, grp, means in MARKETS:
    m = {"code": code, "s": short, "n": name, "g": grp, "means": means}
    for view, src in (("nc", spec), ("lf" if grp != "Commodities" else "mm", mm if grp == "Commodities" else lev)):
        s = src.get(code, {})
        # long, short, open interest per week; null where the week is missing
        m[view] = [list(s[d]) if d in s else None for d in dates]
    out["markets"].append(m)
json.dump(out, open("data.json", "w"), separators=(",", ":"))
print("Saved", len(out["markets"]), "markets,", len(dates), "weeks, latest", dates[-1])
