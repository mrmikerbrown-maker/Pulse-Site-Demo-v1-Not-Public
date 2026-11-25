# Temporary probe: can GitHub Actions reach the CFTC's free Commitments of Traders API?
import json, time, requests
B = "https://publicreporting.cftc.gov/resource/"
SETS = {"legacy": "6dca-aqww", "tff": "gpe5-46if", "disagg": "72hh-3qpy"}
out = {"checked_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "status": {}}
for k, d in SETS.items():
    t = time.time()
    r = requests.get(B + d + ".json", params={"$order": "report_date_as_yyyy_mm_dd DESC", "$limit": 1}, timeout=60)
    out["status"][k] = {"code": r.status_code, "secs": round(time.time() - t, 2)}
    if r.ok:
        last = r.json()[0]["report_date_as_yyyy_mm_dd"]
        out["status"][k]["latest"] = last
        rows = requests.get(B + d + ".json", params={"$where": f"report_date_as_yyyy_mm_dd='{last}'", "$limit": 5000}, timeout=60).json()
        json.dump(rows, open(f"cftc-probe/{k}-latest.json", "w"))
        out["status"][k]["rows_latest"] = len(rows)
codes = "099741 097741 096742 092741 090741 232741 112741 095741 098662 133741 042601 044601 043602 043607 020601 020604 134741 045601 13874A 209742 124603 239742 1170E1 067651 06765T 023651 088691 084691 085692 076651 002602 005602 001602 080732 083731 073732 033661".split()
inlist = ",".join(f"'{c}'" for c in codes)
for k in ("legacy", "tff", "disagg"):
    t = time.time()
    r = requests.get(B + SETS[k] + ".json", params={"$where": f"cftc_contract_market_code in({inlist}) AND report_date_as_yyyy_mm_dd > '2019-11-01'", "$limit": 50000, "$order": "report_date_as_yyyy_mm_dd"}, timeout=120)
    out["status"][k]["hist_code"] = r.status_code
    out["status"][k]["hist_secs"] = round(time.time() - t, 2)
    if r.ok:
        rows = r.json(); out["status"][k]["hist_rows"] = len(rows)
        json.dump(rows, open(f"cftc-probe/{k}-hist.json", "w"))
json.dump(out, open("cftc-probe/status.json", "w"), indent=1)
print(json.dumps(out, indent=1))
