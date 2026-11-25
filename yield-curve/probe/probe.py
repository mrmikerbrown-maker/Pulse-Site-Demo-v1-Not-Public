"""Temporary probe: can GitHub Actions reach the free yield sources? Saves what it gets into probe/out/."""
import io, json, os, time, zipfile, datetime as dt, traceback
import requests, openpyxl
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"); os.makedirs(OUT, exist_ok=True)
log = {}
def get(url, **kw):
    t = time.time(); r = requests.get(url, headers=UA, timeout=120, **kw)
    print(r.status_code, len(r.content), round(time.time()-t, 1), "s", url[:140]); return r
def step(name, fn):
    try: log[name] = fn() or "ok"
    except Exception as e: log[name] = "FAIL " + repr(e)[:300]; traceback.print_exc()

def ust():
    res = {}
    for y in (2024, 2025, 2026):
        r = get(f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv")
        open(f"{OUT}/ust-{y}.csv", "wb").write(r.content); res[y] = [r.status_code, len(r.content), r.text.splitlines()[:2]]
    return res
step("ust", ust)

def bund():
    res, data = {}, {}
    for m in ["R01XX","R02XX","R03XX","R05XX","R07XX","R10XX","R15XX","R20XX","R30XX"]:
        url = f"https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.{m}.R.A.A._Z._Z.A?format=csv&lang=en&startPeriod=2024-01-01"
        r = get(url); res[m] = [r.status_code, len(r.content)]
        if r.ok: open(f"{OUT}/bund-{m}.csv", "wb").write(r.content)
    # short end: 3m and 6m from listed federal securities? try money-market maturity codes
    for m in ["R0.5XX","R00.5","R0M06"]:
        r = get(f"https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.{m}.R.A.A._Z._Z.A?format=csv&lang=en&lastNObservations=3"); res[m] = r.status_code
    return res
step("bund", bund)

def gilt():
    res = {}
    YC = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/"
    for name in ["latest-yield-curve-data.zip", "glcnominalddata.zip"]:
        r = get(YC + name); res[name] = [r.status_code, len(r.content)]
        if not r.ok: continue
        z = zipfile.ZipFile(io.BytesIO(r.content)); res[name].append(z.namelist())
        for n in z.namelist():
            if "nominal" not in n.lower(): continue
            wb = openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True, data_only=True)
            res[n] = wb.sheetnames
            for sn in wb.sheetnames:
                if "spot" in sn.lower() and "short" not in sn.lower():
                    rows, yrs = {}, None
                    for row in wb[sn].iter_rows(values_only=True):
                        if not row: continue
                        if isinstance(row[0], str) and row[0].strip().lower().startswith("years"):
                            yrs = [x for x in row[1:] if isinstance(x, (int, float))]
                        elif yrs and isinstance(row[0], (dt.datetime, dt.date)):
                            d = row[0].date().isoformat() if isinstance(row[0], dt.datetime) else row[0].isoformat()
                            rows[d] = {str(y): v for y, v in zip(yrs, row[1:]) if isinstance(v, (int, float)) and y in (0.5,1,2,3,5,7,10,15,20,25,30,40)}
                    if rows:
                        ds = sorted(rows); keep = {d: rows[d] for d in ds if d >= "2024-01-01"}
                        json.dump(keep, open(f"{OUT}/gilt-{n.split('/')[-1][:40].replace(' ','_')}-{sn[:10].replace(' ','_')}.json", "w"))
                        res[n + "|" + sn] = [len(rows), ds[0], ds[-1]]
    # IADB par yields as a cross-check
    for code in ["IUDSNPY", "IUDMNPY", "IUDLNPY", "IUDSNZC"]:
        r = get(f"https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Oct/2026&Dateto=now&SeriesCodes={code}&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
        res[code] = [r.status_code, r.text.splitlines()[-3:]]
    return res
step("gilt", gilt)

def ecb():  # backup for Bunds: ECB has no Bund curve, only euro-area AAA; check it anyway
    r = get("https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?format=csvdata&lastNObservations=3")
    return [r.status_code, r.text.splitlines()[-2:]]
step("ecb_aaa", ecb)
json.dump(log, open(f"{OUT}/log.json", "w"), indent=1, default=str)
print(json.dumps(log, indent=1, default=str)[:6000])
