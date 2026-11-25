# Temporary probe: can GitHub Actions get a year of daily bars from TradingView's chart websocket? Removed after the test.
import json, random, string, re, time
from websocket import create_connection
def msg(f,p):
    s=json.dumps({"m":f,"p":p},separators=(",",":"));return "~m~%d~m~%s"%(len(s),s)
def rid(pfx):return pfx+"".join(random.choice(string.ascii_lowercase) for _ in range(12))
def bars(sym,n=300):
    ws=create_connection("wss://data.tradingview.com/socket.io/websocket",header=["Origin: https://www.tradingview.com"],timeout=20)
    cs=rid("cs_")
    for m in [msg("set_auth_token",["unauthorized_user_token"]),msg("chart_create_session",[cs,""]),
              msg("resolve_symbol",[cs,"sds_sym_1",'={"symbol":"%s","adjustment":"splits"}'%sym]),
              msg("create_series",[cs,"sds_1","s1","sds_sym_1","1D",n,""])]:
        ws.send(m)
    out="";t=time.time()
    while time.time()-t<20:
        r=ws.recv()
        if r.startswith("~m~") and "~h~" in r: ws.send(r); continue
        out+=r
        if "series_completed" in r or "symbol_error" in r: break
    ws.close()
    v=re.findall(r'"v":\[([^\]]+)\]',out)
    return len(v),(v[-1] if v else out[:300])
for s in ["SP:SPX","TVC:US10Y","FX:EURUSD","TVC:GOLD","TVC:UKX","ICEEUR:BRN1!","TVC:JP10Y","BITSTAMP:BTCUSD"]:
    try: n,last=bars(s);print(s,n,"bars, last:",last)
    except Exception as e: print(s,"ERROR",e)
