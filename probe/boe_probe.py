# One-off test: can GitHub Actions download the Bank of England OIS curve? Never fails.
import io, zipfile, datetime as dt
import requests, openpyxl

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def get(u):
    try:
        r = requests.get(u, headers=UA, timeout=60)
        print("HTTP", r.status_code, len(r.content), r.headers.get("Content-Type"), u)
        return r.content if r.ok else b""
    except Exception as e:
        print("FAIL", u, e)
        return b""


for u in ["https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/latest-yield-curve-data.zip",
          "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/oisddata.zip"]:
    b = get(u)
    if not b or b[:2] != b"PK":
        print("  not a zip:", b[:200])
        continue
    z = zipfile.ZipFile(io.BytesIO(b))
    print("files:", z.namelist())
    for n in z.namelist():
        if "OIS" not in n.upper():
            continue
        wb = openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True, data_only=True)
        print("==", n, "sheets:", wb.sheetnames)
        for sn in wb.sheetnames:
            if "short" not in sn.lower():
                continue
            rows = [r for r in wb[sn].iter_rows(values_only=True)]
            print("  sheet", sn, "rows", len(rows))
            for r in rows[:6]:
                print("   ", list(r[:16]))
            last = [r for r in rows if r and isinstance(r[0], (dt.datetime, dt.date))][-2:]
            for r in last:
                print("   LAST", r[0], [round(x, 4) if isinstance(x, float) else x for x in r[1:25]])
        break
