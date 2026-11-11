import requests, time, datetime as dt, collections
UA={"User-Agent":"Mozilla/5.0"}
for tk in ["EURUSD=X","JPY=X","GC=F","^GSPC"]:
    j=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",params={"period1":int(dt.datetime(1994,1,1).timestamp()),"period2":int(time.time()),"interval":"1d"},headers=UA,timeout=60).json()["chart"]["result"][0]
    ts=j["timestamp"];c=j["indicators"]["quote"][0]["close"]
    hist=collections.Counter((dt.datetime.utcfromtimestamp(t).year//4*4,dt.datetime.utcfromtimestamp(t).strftime("%H:%M")) for t in ts)
    print(tk, sorted(hist.items()))
    for day in ["2008-12-16","2015-09-17","2022-06-15","2026-07-29"]:
        d0=dt.datetime.fromisoformat(day)
        print("  ",day,[(dt.datetime.utcfromtimestamp(t).strftime("%m-%d %H:%M"),round(x,5) if x else None) for t,x in zip(ts,c) if abs((dt.datetime.utcfromtimestamp(t)-d0).days)<=2])
