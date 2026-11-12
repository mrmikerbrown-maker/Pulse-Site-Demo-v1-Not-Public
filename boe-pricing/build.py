"""Builds data.json for the BoE option on the Central Bank Pricing page: what markets price for each MPC meeting.

Source: the Bank of England's own daily OIS curve (short end: instantaneous forward SONIA, monthly from 1 month
to 5 years), from the Bank's yield curve files. There is no free feed for ICE's MPC Dated SONIA futures, so we
read the expected SONIA path off the curve instead: for each meeting, the average forward SONIA between that
meeting and the next one. The curve is fitted (smoothed), so the split between neighbouring meetings is
approximate; the cumulative path matched ICE MPC futures within a few bp when checked on 10 Nov 2026.
The Bank publishes each day's curve around midday the next working day.

If a download fails the last good data.json is kept, the problem is listed in data.json "problems",
and the job still finishes green."""
import csv, io, json, os, time, zipfile, datetime as dt
import requests, openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data.json")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
YC = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/"
LATEST, ARCHIVE = YC + "latest-yield-curve-data.zip", YC + "oisddata.zip"
IADB = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes"
        "&Datefrom={frm}&Dateto=now&SeriesCodes={code}&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
# MPC announcement days, from bankofengland.co.uk/monetary-policy/upcoming-mpc-dates. Same list as central-banks/config.json.
MPC = ["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30", "2026-09-17", "2026-11-05",
       "2026-12-17", "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-17", "2027-07-29", "2027-09-16",
       "2027-11-04", "2027-12-16"]


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=90)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(4 * (i + 1))
    raise last


def short_end_forwards(zbytes, want=None):
    """{date: (months list, forward SONIA list)} from the 'fwds, short end' sheet of each OIS workbook in a zip."""
    out = {}
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    for name in z.namelist():
        if "OIS" not in name.upper() or (want and want not in name.lower()):
            continue
        wb = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True, data_only=True)
        sheets = [s for s in wb.sheetnames if "fwd" in s.lower() and "short" in s.lower()]
        print(name, "->", sheets or "no short-end forward sheet", wb.sheetnames)
        for sn in sheets:
            months = None
            for r in wb[sn].iter_rows(values_only=True):
                if not r:
                    continue
                if isinstance(r[0], str) and r[0].strip().lower().startswith("months"):
                    months = [round(x) for x in r[1:] if isinstance(x, (int, float))]
                elif months and isinstance(r[0], (dt.datetime, dt.date)):
                    vals = list(r[1:1 + len(months)])
                    pts = [(m, float(v)) for m, v in zip(months, vals) if isinstance(v, (int, float))]
                    if len(pts) >= 12:
                        out[r[0].date() if isinstance(r[0], dt.datetime) else r[0]] = pts
    return out


def iadb(code, days=60):
    frm = (dt.date.today() - dt.timedelta(days=days)).strftime("%d/%b/%Y")
    txt = fetch(IADB.format(frm=frm, code=code)).text
    pts = {}
    for row in csv.reader(txt.splitlines()):
        if len(row) > 1:
            try:
                pts[dt.datetime.strptime(row[0].strip(), "%d %b %Y").date()] = float(row[1])
            except ValueError:
                pass
    if not pts:
        raise RuntimeError("no data for " + code)
    return pts


def path_on(day, pts, sonia0, meetings):
    """Average expected SONIA from day to the first meeting (base), then over each meeting-to-meeting period."""
    nodes = [(0.0, sonia0 if sonia0 is not None else pts[0][1])] + [(m * 30.4375, v) for m, v in pts]

    def f(t):                                    # forward SONIA t days ahead, straight lines between monthly points
        for (t0, v0), (t1, v1) in zip(nodes, nodes[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return nodes[-1][1]

    def avg(a, b):                               # average over days a..b-1 (dates)
        ts = [(a - day).days + k for k in range((b - a).days)]
        return sum(f(t) for t in ts) / len(ts)

    ms = [dt.date.fromisoformat(m) for m in meetings]
    ahead = [m for m in ms if m > day]
    if not ahead:
        return None, []
    base = avg(day, ahead[0] + dt.timedelta(days=1))
    rates = []
    for i, m in enumerate(ahead):
        end = ahead[i + 1] if i + 1 < len(ahead) else m + dt.timedelta(days=49)
        rates.append(round(avg(m + dt.timedelta(days=1), end + dt.timedelta(days=1)), 4))
    return round(base, 4), list(zip([m.isoformat() for m in ahead], rates))


def main():
    old = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            old = json.load(f)
    problems, data = [], {"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

    sonia, bank = {}, {}
    try:
        sonia = iadb("IUDSOIA")
        d = max(sonia)
        data["sonia"] = {"value": sonia[d], "date": d.isoformat()}
    except Exception as e:
        print("SONIA failed:", e)
        problems.append("sonia")
    try:
        bank = iadb("IUDBEDR")
        d = max(bank)
        data["bank_rate"] = {"value": bank[d], "date": d.isoformat()}
    except Exception as e:
        print("Bank Rate failed:", e)
        problems.append("bank_rate")
        if old.get("bank_rate"):
            data["bank_rate"] = old["bank_rate"]

    try:
        curves = short_end_forwards(fetch(LATEST).content)
        if len(curves) < 16:                     # early in the month: add last month from the archive
            try:
                curves = {**short_end_forwards(fetch(ARCHIVE).content, want="present"), **curves}
            except Exception as e:
                print("archive failed:", e)
        if not curves:
            raise RuntimeError("no OIS short-end forward curves found")
        days = sorted(curves)
        asof = days[-1]

        def s0(d):                               # SONIA on (or just before) that day, to pin the front of the curve
            ks = [k for k in sonia if k <= d]
            return sonia[max(ks)] if ks else None

        base, path = path_on(asof, curves[asof], s0(asof), MPC)
        if not path:
            raise RuntimeError("no upcoming MPC meetings in the list")
        meetings = [m for m, _ in path]
        p = {"meetings": meetings, "rates": [r for _, r in path], "effr": base, "base": base,
             "asof": asof.isoformat(), "compare": {},
             "source": "Bank of England daily OIS curve (instantaneous forward SONIA, short end)"}
        for label, n in (("1w ago", 5), ("3w ago", 15)):
            if len(days) > n:
                d = days[-1 - n]
                _, op = path_on(d, curves[d], s0(d), MPC)
                om = dict(op)
                p["compare"][label] = {"asof": d.isoformat(), "rates": [om.get(m) for m in meetings]}
        data["path"] = p
        print("OIS curve", asof, "->", len(meetings), "meetings; compare:", {k: v["asof"] for k, v in p["compare"].items()})
    except Exception as e:
        print("OIS pricing failed:", e)
        problems.append("path")
        if old.get("path"):
            data["path"] = old["path"]

    data["problems"] = problems
    if not data.get("path"):
        print("No pricing yet; nothing saved")
        return
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(json.dumps(data, indent=1)[:2500])


if __name__ == "__main__":
    main()
