"""Builds data.json for the Earnings Moves page: how big a move the options market prices for each large US
company's earnings, and how much the stock actually moved after past reports.

Universe: S&P 500 members (from ../index-contribution-site/spy-weights.csv, the SPY holdings the index page already
downloads) worth at least MIN_CAP, market caps from the TradingView screener.

Sources (all free, no key, all checked from GitHub Actions on 18 Nov 2026):
- Earnings dates and timing (before the open / after the close): Nasdaq earnings calendar, one call per day.
  TradingView's screener is the backup for upcoming dates if Nasdaq fails.
- Options: Cboe's delayed quotes (15 min delayed), the full chain for one stock per call.
  Implied move = price of the at-the-money straddle (call + put) for the first expiry after the report,
  divided by the share price. Strikes either side of the share price are blended.
- Past report dates and timing: the same Nasdaq calendar, read back about 3 years and kept in calendar-archive.json
  (SEC EDGAR was tried first, but www.sec.gov refuses GitHub's servers).
- Daily closes for actual past moves: Nasdaq historical prices (about 3 years).

There is no free archive of old option prices, so the implied move for past reports only exists from the day this
job started saving them (implied-log.csv, one row per stock per run, kept for good).

If a source fails, the last good numbers are kept, the problem is listed in data.json "problems" and the job still
finishes green."""
import csv
import math, json, os, sys, time, datetime as dt
from zoneinfo import ZoneInfo
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data.json")
LOG = os.path.join(HERE, "implied-log.csv")
SPY = os.path.join(HERE, "..", "index-contribution-site", "spy-weights.csv")
NY, LDN = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
MIN_CAP = 50e9
AHEAD_DAYS = 14        # calendar days of upcoming reports shown
RECENT_DAYS = 10       # calendar days of recent results shown
HIST_N = 12            # past reports kept per stock (3 years)
HIST_REFRESH_DAYS = 6  # re-download a stock's past moves at least this often
HIST_YEARS = 3.1
MAX_ARCHIVE_CALLS = 450  # Nasdaq calendar days read per run: the ~3-year backfill spreads over the first runs so none runs long
WORKERS = 3              # downloads at once
HIST_VERSION = 3         # bump to force every stock's past moves to be recomputed
ARCH = os.path.join(HERE, "calendar-archive.json")
SURP = os.path.join(HERE, "surprises.json")  # EPS and revenue against forecasts, per report, kept between runs
# US market holidays (NYSE), so index options expiries either side of one count as one session apart
HOLIDAYS = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
            "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24", "2028-01-17", "2028-02-21"}
# Index options used for each index's implied move per session: SPX has options expiring every weekday;
# NDX options don't, so QQQ (the Nasdaq 100 ETF), which does, stands in for the Nasdaq 100.
IDX_OPT = {"SPX": ("_SPX", "SPXW"), "NDX": ("QQQ", "QQQ")}
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
NASDAQ_H = {"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/", "Accept": "application/json, text/plain, */*"}
TV_H = {"Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/", "Content-Type": "application/json"}

S = requests.Session()
S.headers["User-Agent"] = BROWSER
problems = []
TV_HABIT = {}


def note(msg):
    print("PROBLEM:", msg)
    problems.append(msg)


def fetch(url, headers=None, data=None, tries=3, timeout=40):
    last = None
    for i in range(tries):
        try:
            r = (S.post(url, data=data, headers=headers, timeout=timeout) if data is not None
                 else S.get(url, headers=headers, timeout=timeout))
            if r.status_code == 404:
                r.raise_for_status()
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError("HTTP %s" % r.status_code)
            r.raise_for_status()
            return r
        except requests.HTTPError as e:
            last = e
            if getattr(e.response, "status_code", None) == 404:
                break
        except Exception as e:
            last = e
        time.sleep(3 * (i + 1))
    raise last


def money(s):
    if s in (None, "", "N/A"):
        return None
    try:
        return float(str(s).replace("$", "").replace(",", ""))
    except ValueError:
        return None


def iso(d):
    return d.isoformat()


def session_today():
    """The US trading date whose close is the latest available (weekends roll back to Friday)."""
    now = dt.datetime.now(NY)
    d = now.date()
    if now.hour < 16:  # before today's close the latest finished session is the previous weekday
        d -= dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


# ---------- universe ----------
def spy_members():
    syms = []
    with open(SPY) as f:
        for row in csv.reader(f):
            if row and row[0] != "asof":
                syms.append(row[0].strip().upper())
    return syms


def tv_scan(extra_filter=None, cols=None, n=400):
    cols = cols or ["name", "description", "market_cap_basic", "close", "earnings_release_next_date", "earnings_release_next_time"]
    flt = [{"left": "market_cap_basic", "operation": "greater", "right": MIN_CAP * 0.8},
           {"left": "type", "operation": "equal", "right": "stock"},
           {"left": "is_primary", "operation": "equal", "right": True}] + (extra_filter or [])
    q = {"columns": cols, "filter": flt, "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}, "range": [0, n]}
    j = fetch("https://scanner.tradingview.com/america/scan", headers=TV_H, data=json.dumps(q)).json()
    return [dict(zip(cols, r["d"])) for r in j.get("data", [])]


def index_levels():
    """Latest close of each index from the Index Contribution snapshot, for turning % into index points."""
    out = {}
    try:
        with open(os.path.join(HERE, "..", "index-contribution-site", "last-session.csv")) as f:
            for r in csv.reader(f):
                if len(r) > 3 and r[0] in ("IDX_SPX", "IDX_NDX", "IDX_DOW"):
                    out[r[0][4:]] = float(r[3].replace(",", ""))
    except Exception as e:
        print("Index levels could not be read:", e)
    return out


def index_weights():
    """{symbol: {"SPX": %, "NDX": %, "DOW": %}} from the Index Contribution page's latest snapshot."""
    out = {}
    try:
        with open(os.path.join(HERE, "..", "index-contribution-site", "last-session.csv")) as f:
            for r in csv.reader(f):
                if len(r) > 7 and r[0] in ("SPX", "NDX", "DOW") and r[4]:
                    try:
                        out.setdefault(r[4].strip().upper(), {})[r[0]] = round(float(r[7]), 2)
                    except ValueError:
                        pass
    except Exception as e:
        note("Index weights could not be read: %s" % e)
    return out


def universe(prev):
    members = set(spy_members())
    try:
        rows = tv_scan()
    except Exception as e:
        note("TradingView screener (market caps) failed: %s" % e)
        return prev.get("universe") or {}, {}
    uni, nxt = {}, {}
    for r in rows:
        sym = (r["name"] or "").replace("/", ".").upper()
        if sym in members and (r["market_cap_basic"] or 0) >= MIN_CAP and sym not in uni:
            uni[sym] = {"name": clean_name(r["description"]), "cap": round(r["market_cap_basic"] / 1e9, 1), "price": r["close"]}
            if r.get("earnings_release_next_date"):
                t = r.get("earnings_release_next_time")
                nxt[sym] = {"date": dt.datetime.fromtimestamp(r["earnings_release_next_date"], NY).date().isoformat(),
                            "time": "bmo" if t == -1 else "amc" if t == 1 else "tbc"}
    # Each company's usual timing (before the open / after the close), used for past reports where Nasdaq's
    # calendar doesn't say. TradingView: -1 = before the open, 1 = after the close.
    try:
        for r in tv_scan(cols=["name", "earnings_release_time", "earnings_release_next_time"]):
            sym = (r["name"] or "").replace("/", ".").upper()
            t = r.get("earnings_release_time") or r.get("earnings_release_next_time")
            if sym in uni and t in (-1, 1):
                TV_HABIT[sym] = "bmo" if t == -1 else "amc"
    except Exception as e:
        print("TradingView timing lookup failed:", e)
    W = index_weights()
    for sym in uni:
        if sym in W:
            uni[sym]["w"] = W[sym]
    print("Universe:", len(uni), "S&P 500 stocks over $%.0fbn" % (MIN_CAP / 1e9), "; usual timing known for", len(TV_HABIT))
    if len(uni) < 50:
        note("Universe looked too small (%d), kept the previous one" % len(uni))
        return prev.get("universe") or uni, nxt
    return uni, nxt


# Short names people actually use. Anything not listed gets the generic tidy-up in clean_name().
SHORT = {
    "Abbott Laboratories": "Abbott", "Advanced Micro Devices": "AMD", "Air Products and Chemicals": "Air Products",
    "Altria Group": "Altria", "Amazon.com": "Amazon", "American Electric Power": "AEP", "Apollo Global Management": "Apollo",
    "Arthur J. Gallagher & Co": "Gallagher", "Automatic Data Processing": "ADP", "Bank of New York Mellon": "BNY",
    "Becton, Dickinson and": "BD", "Bristol-Myers Squibb": "Bristol Myers", "Cadence Design Systems": "Cadence",
    "Capital One Financial": "Capital One", "Charles Schwab": "Schwab", "Chubb Limited": "Chubb", "Cigna Group": "Cigna",
    "Cisco Systems": "Cisco", "Costco Wholesale": "Costco", "CRH public limited company": "CRH", "Dell Technologies": "Dell",
    "Digital Realty Trust": "Digital Realty", "Edwards Lifesciences": "Edwards", "Eli Lilly and": "Eli Lilly",
    "Emerson Electric": "Emerson", "Exxonmobil": "ExxonMobil", "Gilead Sciences": "Gilead", "Goldman Sachs Group": "Goldman Sachs",
    "Hewlett Packard Enterprise": "HPE", "Hilton Worldwide": "Hilton", "Honeywell International": "Honeywell",
    "Howmet Aerospace": "Howmet", "IDEXX Laboratories": "IDEXX", "Illinois Tool Works": "Illinois Tool Works",
    "Interactive Brokers Group": "Interactive Brokers", "Intercontinental Exchange": "ICE",
    "International Business Machines": "IBM", "JPMorgan Chase & Co": "JPMorgan", "Johnson Controls International": "Johnson Controls",
    "Kinder Morgan Inc Class P": "Kinder Morgan", "KKR & Co": "KKR", "Lowe's Companies": "Lowe's", "Marathon Petroleum": "Marathon",
    "Marriott International": "Marriott", "Marsh & McLennan Companies": "Marsh McLennan", "Marvell Technology": "Marvell",
    "Merck & Co": "Merck", "Meta Platforms": "Meta", "Micron Technology": "Micron", "Mondelez International": "Mondelez",
    "Monolithic Power Systems": "Monolithic Power", "Monster Beverage": "Monster", "Motorola Solutions": "Motorola",
    "NIKE": "Nike", "NVIDIA": "Nvidia", "NXP Semiconductors NV": "NXP", "Occidental Petroleum": "Occidental",
    "Palantir Technologies": "Palantir", "PNC Financial Services Group": "PNC", "Philip Morris International": "Philip Morris",
    "QUALCOMM": "Qualcomm", "Regeneron Pharmaceuticals": "Regeneron", "Robinhood Markets": "Robinhood",
    "Royal Caribbean Group": "Royal Caribbean", "SLB Limited": "SLB", "Seagate Technology": "Seagate",
    "Simon Property Group": "Simon Property", "Southern": "Southern Co", "T-Mobile US": "T-Mobile", "TJX Companies": "TJX",
    "Texas Instruments": "Texas Instruments", "Thermo Fisher Scientific": "Thermo Fisher", "Trane Technologies": "Trane",
    "TransDigm Group": "TransDigm", "Travelers Companies": "Travelers", "Truist Financial": "Truist",
    "Uber Technologies": "Uber", "United Parcel Service": "UPS", "UnitedHealth Group": "UnitedHealth", "Valero Energy": "Valero",
    "Verizon Communications": "Verizon", "Vertex Pharmaceuticals": "Vertex", "W.W. Grainger": "Grainger",
    "Walt Disney": "Disney", "Waste Management": "Waste Management", "Wells Fargo & Co": "Wells Fargo",
    "Williams Companies": "Williams", "Xcel Energy": "Xcel", "Constellation Energy": "Constellation",
    "Lumentum": "Lumentum", "CME Group": "CME", "Coca-Cola": "Coca-Cola", "Freeport-McMoRan": "Freeport",
}


def clean_name(s):
    import re
    s = (s or "").strip()
    s = re.sub(r"\b(Class [A-C]|Common Stock|Ordinary Shares)\b", "", s)
    s = re.sub(r"^The\s+", "", s)
    for _ in range(3):
        s = re.sub(r"[ ,]+(Inc\.?|Incorporated|Corporation|Corp\.?|Co\.?|Company|plc|PLC|Plc|Ltd\.?|N\.V\.|Holdings|S\.A\.|AG|SE|L\.P\.)$", "", s.strip(" ,"))
    s = re.sub(r"\s*&$", " & Co", s.strip(" ,"))
    s = re.sub(r"\s+", " ", s).strip(" ,")
    return SHORT.get(s, s)


# ---------- calendar ----------
TIME_MAP = {"time-pre-market": "bmo", "time-after-hours": "amc"}


def nasdaq_calendar(uni, start, end):
    """{sym: [(date, time)]} from Nasdaq, for days start..end."""
    out, fails, d = {}, 0, start
    while d <= end:
        if d.weekday() < 5:
            try:
                j = fetch("https://api.nasdaq.com/api/calendar/earnings?date=" + iso(d), headers=NASDAQ_H).json()
                for r in ((j.get("data") or {}).get("rows") or []):
                    sym = (r.get("symbol") or "").upper().replace("/", ".")
                    if sym in uni:
                        out.setdefault(sym, []).append((iso(d), TIME_MAP.get(r.get("time"), "tbc"), money(r.get("epsForecast"))))
            except Exception as e:
                fails += 1
                print("Nasdaq calendar", d, "failed:", e)
            time.sleep(0.4)
        d += dt.timedelta(days=1)
    if fails:
        note("Nasdaq earnings calendar failed for %d day(s)" % fails)
    return out, fails


# ---------- options ----------
def cboe_chain(sym):
    for s in [sym, sym.replace(".", ""), sym.replace(".", "/")]:
        try:
            return s, fetch("https://cdn.cboe.com/api/global/delayed_quotes/options/%s.json" % s, tries=2).json()["data"]
        except Exception as e:
            last = e
    raise last


def tdays(a, b):
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def mid(o):
    b, a = o.get("bid") or 0, o.get("ask") or 0
    if b > 0 and a > 0 and a >= b:
        return (a + b) / 2, (a - b) / ((a + b) / 2)
    return None, None


def atm_straddle(chain, price):
    """chain = {strike: {"C": option, "P": option}} for one expiry. Call + put at the money, interpolated between
    the strikes either side of the price. Returns (straddle, worst bid/ask spread as a share of mid, [(strike, ...)])."""
    strikes = sorted(k for k, v in chain.items() if "C" in v and "P" in v)
    below = [k for k in strikes if k <= price]
    above = [k for k in strikes if k >= price]
    if not below or not above:
        raise ValueError("price outside strikes")
    pts = []
    for k in sorted({below[-1], above[0]}):
        c, cs = mid(chain[k]["C"])
        p, ps = mid(chain[k]["P"])
        if c is None or p is None:
            continue
        pts.append((k, c + p, max(cs, ps)))
    if not pts:
        raise ValueError("no two-sided quotes at the money")
    if len(pts) == 2 and pts[1][0] != pts[0][0]:
        w = (price - pts[0][0]) / (pts[1][0] - pts[0][0])
        straddle = pts[0][1] * (1 - w) + pts[1][1] * w
    else:
        straddle = pts[0][1]
    return straddle, max(p[2] for p in pts), pts


def sessions_between(a, b):
    """US trading sessions after date a up to and including date b."""
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and iso(d) not in HOLIDAYS:
            n += 1
    return n


def forward(chain, price):
    """The index level the options themselves are priced off (put-call parity at the strike where call and put
    are closest), so options quoted after the index has moved overnight, or on the morning of a gap, still give
    an at-the-money straddle rather than one that is partly in the money."""
    best = None
    for k, v in chain.items():
        if "C" in v and "P" in v and abs(k / price - 1) < 0.05:
            c, _ = mid(v["C"])
            p, _ = mid(v["P"])
            if c is not None and p is not None and (best is None or abs(c - p) < best[0]):
                best = (abs(c - p), k + c - p)
    return best[1] if best else price


def index_days(sess):
    """{date: {"SPX": %, "NDX": %}}: the move index options imply for each coming session on its own.
    Straddles on consecutive daily expiries are turned into one day's move: an at-the-money straddle grows with
    the square root of time, so (move to expiry)^2 minus (move to the expiry before)^2 leaves that one session's
    share. A busy day (CPI, payrolls, the Fed, Nvidia results) shows up as a bigger number than the days around it."""
    out = {}
    for ix, (sym, root) in IDX_OPT.items():
        try:
            d = fetch("https://cdn.cboe.com/api/global/delayed_quotes/options/%s.json" % sym, tries=2, timeout=90).json()["data"]
            price = d.get("current_price") or d.get("close")
            by = {}
            for o in d["options"]:
                code = o["option"]
                if code[:-15] != root:
                    continue
                tail = code[-15:]
                exp = dt.date(2000 + int(tail[:2]), int(tail[2:4]), int(tail[4:6]))
                if exp <= sess or (exp - sess).days > 21:
                    continue
                by.setdefault(exp, {}).setdefault(int(tail[7:]) / 1000.0, {})[tail[6]] = o
            prev_var, prev_exp, n = 0.0, sess, 0
            for exp in sorted(by):
                try:
                    fwd = forward(by[exp], price)
                    st, spread, _ = atm_straddle(by[exp], fwd)
                except ValueError as e:
                    print("  %s %s: %s" % (ix, exp, e))
                    continue
                var = (st / fwd * 100) ** 2
                gap = sessions_between(prev_exp, exp)
                if var > prev_var and gap == 1:
                    out.setdefault(iso(exp), {})[ix] = round(math.sqrt(var - prev_var), 2)
                    n += 1
                prev_var, prev_exp = max(prev_var, var), exp
            print("Index options %s (%s): %d sessions" % (ix, sym, n))
            if not n:
                note("%s options gave no per-day implied moves" % ix)
        except Exception as e:
            note("%s index options failed: %s" % (ix, e))
    return out


def implied_move(sym, report_date, when):
    """ATM straddle for the first expiry on/after the day the report hits the price."""
    root, d = cboe_chain(sym)
    price = d.get("current_price") or d.get("close")
    if not price:
        raise ValueError("no share price")
    rd = dt.date.fromisoformat(report_date)
    first = rd if when == "bmo" else rd + dt.timedelta(days=1)  # after the close (or time unknown): next day's move
    root_std = root.replace("/", "").replace(".", "")
    by = {}
    for o in d["options"]:
        code = o["option"]
        r, tail = code[:-15], code[-15:]
        if r != root_std:
            continue  # skips adjusted contracts left over from splits or deals
        exp = dt.date(2000 + int(tail[:2]), int(tail[2:4]), int(tail[4:6]))
        if exp < first:
            continue
        k = int(tail[7:]) / 1000.0
        by.setdefault(exp, {}).setdefault(k, {})[tail[6]] = o
    if not by:
        raise ValueError("no expiry after %s" % first)
    exp = min(by)
    straddle, spread, pts = atm_straddle(by[exp], price)
    return {
        "move": round(straddle / price * 100, 2),
        "straddle": round(straddle, 2),
        "price": round(price, 2),
        "expiry": iso(exp),
        "days_after": (exp - first).days,  # extra days beyond the report day the expiry also covers
        # trading days the straddle covers from the last close; the page only shows moves covering 5 or fewer,
        # because further out the straddle is mostly ordinary day-to-day movement rather than the results
        "tdays": tdays(session_today(), exp),
        "strikes": [p[0] for p in pts],
        "wide": spread > 0.25,  # bid/ask spread over 25% of the mid: treat with care
        "iv30": d.get("iv30"),
        "asof": (d.get("last_trade_time") or d.get("timestamp") or "")[:19],
    }


# ---------- past report dates (Nasdaq calendar archive) ----------
def update_archive(arch, members, today):
    """Keeps calendar-archive.json: for each weekday back to HIST_YEARS ago, the S&P 500 members that reported
    and when. Each past day is downloaded once (the last RECENT_DAYS are re-read in case Nasdaq corrected them);
    the first runs fill in about 3 years, 450 days at a time; later runs only add new days."""
    days = arch.setdefault("days", {})
    start = today - dt.timedelta(days=int(365 * HIST_YEARS))
    want, d = [], today
    while d >= start:
        if d.weekday() < 5 and (iso(d) not in days or d >= today - dt.timedelta(days=RECENT_DAYS)):
            want.append(d)
        d -= dt.timedelta(days=1)
    want = want[:MAX_ARCHIVE_CALLS]
    fails = 0

    def one(d):
        j = fetch("https://api.nasdaq.com/api/calendar/earnings?date=" + iso(d), headers=NASDAQ_H, tries=2, timeout=20).json()
        rows = ((j.get("data") or {}).get("rows") or [])
        return sorted([(r.get("symbol") or "").upper().replace("/", "."), TIME_MAP.get(r.get("time"), "tbc")]
                      for r in rows if (r.get("symbol") or "").upper().replace("/", ".") in members)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(WORKERS) as ex:
        for n, (d, fut) in enumerate([(d, ex.submit(one, d)) for d in want]):
            try:
                days[iso(d)] = fut.result()
            except Exception as e:
                fails += 1
                print("Nasdaq calendar archive", d, "failed:", e)
            if n % 50 == 49:  # save as we go, so a slow run that gets stopped still keeps what it read
                with open(ARCH, "w") as f:
                    json.dump(arch, f, separators=(",", ":"))
    arch["_read_this_run"] = len(want)
    print("Calendar archive: %d days read this run, %d failed, %d days held" % (len(want), fails, len(days)))
    if fails > 5:
        note("Nasdaq calendar history failed for %d day(s); they'll be retried next run" % fails)
    for k in [k for k in days if k < iso(start)]:
        del days[k]
    return arch


def archive_reports(arch, sym, before):
    out = []
    for d in sorted(arch.get("days", {})):
        if d >= before:
            break
        for s, t in arch["days"][d]:
            if s == sym:
                if out and (dt.date.fromisoformat(d) - dt.date.fromisoformat(out[-1][0])).days < 20:
                    # Nasdaq occasionally lists a company twice a few days apart (seen in Feb 2026, 9 cases in
                    # 3 years); the later listing is the real one in the cases checked (CEG 24 Feb).
                    out[-1] = (d, t)
                    continue
                out.append((d, t))
    return out


# ---------- EPS and revenue against forecasts ----------
def tv_surprises(uni, surp):
    """Latest reported quarter from TradingView: EPS and revenue, actual vs forecast. Saved per report date so
    the history builds up (TradingView only gives the latest quarter). Also returns the next quarter's forecasts."""
    cols = ["name", "earnings_release_date", "earnings_per_share_fq", "earnings_per_share_forecast_fq", "eps_surprise_percent_fq",
            "revenue_fq", "revenue_forecast_fq", "revenue_surprise_percent_fq",
            "earnings_per_share_forecast_next_fq", "revenue_forecast_next_fq"]
    fc = {}
    try:
        rows = tv_scan(cols=cols, n=500)
    except Exception as e:
        note("TradingView EPS/revenue lookup failed: %s" % e)
        return fc
    r2 = lambda x, n=2: None if x is None else round(x, n)
    for r in rows:
        sym = (r["name"] or "").replace("/", ".").upper()
        if sym not in uni:
            continue
        if r.get("earnings_per_share_forecast_next_fq") is not None or r.get("revenue_forecast_next_fq") is not None:
            fc[sym] = {"eps": r2(r.get("earnings_per_share_forecast_next_fq")), "rev": r2(r.get("revenue_forecast_next_fq"), -6)}
        if not r.get("earnings_release_date") or r.get("earnings_per_share_fq") is None:
            continue
        d = dt.datetime.fromtimestamp(r["earnings_release_date"], NY).date().isoformat()
        rec = {"eps": r2(r.get("earnings_per_share_fq")), "eps_fc": r2(r.get("earnings_per_share_forecast_fq")),
               "eps_s": r2(r.get("eps_surprise_percent_fq"), 1), "rev": r2(r.get("revenue_fq"), -6),
               "rev_fc": r2(r.get("revenue_forecast_fq"), -6), "rev_s": r2(r.get("revenue_surprise_percent_fq"), 1), "src": "TradingView"}
        surp.setdefault(sym, {})[d] = {k: v for k, v in rec.items() if v is not None}
    return fc


def nasdaq_eps_history(syms, surp, today):
    """EPS vs forecast for each company's last 4 reports, from Nasdaq (no revenue there). Read once per company,
    then again after each new report. Doesn't overwrite TradingView's record of the same report."""
    def one(s):
        j = fetch("https://api.nasdaq.com/api/company/%s/earnings-surprise" % s.replace(".", "%5E"), headers=NASDAQ_H, tries=2, timeout=20).json()
        rows = ((((j.get("data") or {}).get("earningsSurpriseTable") or {}).get("rows")) or [])
        out = {}
        for r in rows:
            try:
                m, d, y = r["dateReported"].split("/")
                out["%s-%02d-%02d" % (y, int(m), int(d))] = {"eps": money(r.get("eps")), "eps_fc": money(r.get("consensusForecast")),
                                                           "eps_s": money(r.get("percentageSurprise")), "src": "Nasdaq"}
            except Exception:
                pass
        return out
    from concurrent.futures import ThreadPoolExecutor
    fails = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for s, fut in [(s, ex.submit(one, s)) for s in syms]:
            try:
                got = fut.result()
                cur = surp.setdefault(s, {})
                for d, rec in got.items():
                    if not any(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(k)).days) <= 3 and v.get("src") == "TradingView" for k, v in cur.items()):
                        cur[d] = {k: v for k, v in rec.items() if v is not None}
                cur["_nasdaq"] = iso(today)
            except Exception as e:
                fails += 1
                print("  %-6s Nasdaq EPS history failed: %s" % (s, e))
    if fails > len(syms) / 3 and fails > 5:
        note("Nasdaq EPS history failed for %d stock(s)" % fails)


def surprise_for(surp, sym, date):
    """The EPS/revenue record closest to a report date (within 3 days)."""
    best = None
    for k, v in (surp.get(sym) or {}).items():
        if k.startswith("_"):
            continue
        gap = abs((dt.date.fromisoformat(k) - dt.date.fromisoformat(date)).days)
        if gap <= 3 and (best is None or gap < best[0] or (gap == best[0] and v.get("src") == "TradingView")):
            best = (gap, v)
    return best[1] if best else None


# ---------- prices ----------
def nasdaq_closes(sym, since):
    s = sym.replace(".", "%5E") if "." in sym else sym
    url = ("https://api.nasdaq.com/api/quote/%s/historical?assetclass=stocks&fromdate=%s&todate=%s&limit=9999"
           % (s, iso(since), iso(dt.date.today())))
    j = fetch(url, headers=NASDAQ_H).json()
    rows = ((j.get("data") or {}).get("tradesTable") or {}).get("rows") or []
    out = {}
    for r in rows:
        m, d, y = r["date"].split("/")
        c = money(r.get("close"))
        if c:
            out["%s-%s-%s" % (y, m, d)] = c
    if len(out) < 100:
        raise ValueError("only %d closes" % len(out))
    return dict(sorted(out.items()))


def actual_move(closes, days, date, when):
    """% move from the last close before the news to the first close after it."""
    if when == "bmo":
        after = next((d for d in days if d >= date), None)
    else:
        after = next((d for d in days if d > date), None)
    if not after:
        return None
    i = days.index(after)
    if i == 0:
        return None
    before = days[i - 1]
    return {"from": before, "to": after, "move": round((closes[after] / closes[before] - 1) * 100, 2)}


# ---------- main ----------
def load_json(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def read_log():
    if not os.path.exists(LOG):
        return []
    with open(LOG) as f:
        return list(csv.DictReader(f))


LOG_COLS = ["run_utc", "session", "symbol", "report_date", "time", "price", "expiry", "days_after", "straddle", "move_pct", "iv30"]


def main():
    prev = load_json(OUT)
    sess = session_today()
    today_ny = dt.datetime.now(NY).date()
    print("Session date", sess, "New York date", today_ny)

    uni, tv_next = universe(prev)
    syms = set(uni)
    surp = load_json(SURP)
    fc = tv_surprises(uni, surp)
    for s, f in fc.items():
        uni[s]["fc"] = f
    idx_days = index_days(sess) or prev.get("index_days") or {}

    # Calendar: recent past plus the next AHEAD_DAYS.
    cal, fails = nasdaq_calendar(syms, today_ny - dt.timedelta(days=RECENT_DAYS), today_ny + dt.timedelta(days=AHEAD_DAYS))
    habitual = {}
    for s, lst in cal.items():
        for d, t, _ in lst:
            if t != "tbc":
                habitual[s] = t
    upcoming = {}
    for s, lst in cal.items():
        for d, t, eps in lst:
            if d >= iso(today_ny) or (d == iso(sess) and t == "amc"):
                if s not in upcoming:
                    if t == "tbc" and tv_next.get(s, {}).get("date") == d:
                        t = tv_next[s]["time"]
                    upcoming[s] = {"date": d, "time": t, "eps_fc": eps}
    # Backup / gap fill from TradingView for upcoming dates Nasdaq didn't list.
    for s, v in tv_next.items():
        if s not in upcoming and iso(today_ny) <= v["date"] <= iso(today_ny + dt.timedelta(days=AHEAD_DAYS)):
            upcoming[s] = {"date": v["date"], "time": v["time"], "eps_fc": None, "src": "TradingView"}
    # A report from today before the open, or one from the last session after the close, already hit the price
    # only once the next close is in; until then it stays in "upcoming" as "reported, waiting for the close".
    print("Upcoming reports:", len(upcoming))

    # Options: implied move for each upcoming report.
    log_rows, run_utc = [], dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev_up = {u["symbol"]: u for u in prev.get("upcoming", [])}
    opt_fail = 0
    for s, u in sorted(upcoming.items()):
        already_out = (u["date"] < iso(today_ny)) or (u["date"] == iso(today_ny) and u["time"] == "bmo" and dt.datetime.now(NY).hour >= 9)
        if already_out:
            # Keep the implied move captured before the report rather than a post-report one.
            pu = prev_up.get(s)
            if pu and pu.get("date") == u["date"] and pu.get("implied"):
                u["implied"] = pu["implied"]
            continue
        try:
            u["implied"] = implied_move(s, u["date"], u["time"])
            im = u["implied"]
            log_rows.append([run_utc, iso(sess), s, u["date"], u["time"], im["price"], im["expiry"], im["days_after"],
                             im["straddle"], im["move"], im["iv30"]])
            print("  %-6s %s %s implied ±%.2f%% (exp %s)" % (s, u["date"], u["time"], im["move"], im["expiry"]))
        except Exception as e:
            opt_fail += 1
            print("  %-6s options failed: %s" % (s, e))
            pu = prev_up.get(s)
            if pu and pu.get("date") == u["date"] and pu.get("implied"):
                u["implied"] = pu["implied"]
            time.sleep(0.5)
        time.sleep(0.3)
    if opt_fail:
        note("Cboe options failed for %d stock(s); last good implied move kept where there was one" % opt_fail)
    new_log = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(LOG_COLS)
        w.writerows(log_rows)
    log = read_log()

    # Past moves: refresh stocks reporting soon or recently, and any not refreshed for a while.
    hist = prev.get("history", {})
    since = today_ny - dt.timedelta(days=int(365 * HIST_YEARS))
    arch = update_archive(load_json(ARCH), set(spy_members()), today_ny)
    with open(ARCH, "w") as f:
        json.dump(arch, f, separators=(",", ":"))
    recent_set = {s for s, lst in cal.items() for d, t, _ in lst if d < iso(today_ny)}
    hist_fail = 0
    backfilling = arch.get("_read_this_run", 0) > RECENT_DAYS + 2  # older days just added: recompute every stock
    todo = []
    for s in sorted(syms):
        h = hist.get(s) or {}
        stale = (not h.get("refreshed") or h.get("v") != HIST_VERSION or backfilling
                 or (today_ny - dt.date.fromisoformat(h["refreshed"])).days >= HIST_REFRESH_DAYS)
        if stale or s in upcoming or s in recent_set:
            reps = archive_reports(arch, s, iso(today_ny + dt.timedelta(days=1)))
            if reps:
                todo.append((s, reps))

    def one(item):
        s, reps = item
        closes = nasdaq_closes(s, since - dt.timedelta(days=7))
        days = list(closes)
        moves = []
        ts = [t for _, t in reps if t != "tbc"] + [t for _, t, _ in cal.get(s, []) if t != "tbc"]
        habit = max(set(ts), key=ts.count) if ts else TV_HABIT.get(s, "amc")
        for d, when in reps:
            stated = when != "tbc"
            if not stated:  # Nasdaq's older calendar days rarely say: use the company's usual timing
                when = habit
            am = actual_move(closes, days, d, when)
            if am:
                moves.append({"date": d, "time": when, **am, **({} if stated else {"time_assumed": 1})})
        return {"v": HIST_VERSION, "refreshed": iso(today_ny), "moves": moves[-HIST_N:], "last_close": closes[days[-1]], "last_date": days[-1]}

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(WORKERS) as ex:
        for (s, _), fut in [(it, ex.submit(one, it)) for it in todo]:
            try:
                hist[s] = fut.result()
                m = hist[s]["moves"]
                print("  %-6s %d past reports, last %s" % (s, len(m), m[-1]["date"] if m else "-"))
            except Exception as e:
                hist_fail += 1
                print("  %-6s history failed: %s" % (s, e))
    if hist_fail:
        note("Past moves could not be refreshed for %d stock(s); older data kept" % hist_fail)

    # EPS history from Nasdaq: once per company, and again for companies that reported in the last few days.
    need = [s for s in sorted(syms) if not (surp.get(s) or {}).get("_nasdaq") or
            (s in recent_set and (surp.get(s) or {}).get("_nasdaq", "") < iso(today_ny - dt.timedelta(days=1)))]
    print("Nasdaq EPS history to read:", len(need))
    nasdaq_eps_history(need, surp, today_ny)
    with open(SURP, "w") as f:
        json.dump({s: surp[s] for s in sorted(surp)}, f, separators=(",", ":"))
    for s, h in hist.items():
        for m in h.get("moves", []):
            for k in ("eps", "eps_fc", "eps_s", "rev", "rev_fc", "rev_s"):
                m.pop(k, None)
            sp = surprise_for(surp, s, m["date"])
            if sp:
                m.update({k: v for k, v in sp.items() if k != "src"})

    # Attach the implied move captured before each past report (from our own log).
    for s, h in hist.items():
        for m in h.get("moves", []):
            cands = [r for r in log if r["symbol"] == s and r["report_date"] == m["date"] and
                     (r["session"] < m["date"] if m["time"] == "bmo" else r["session"] <= m["date"])]
            if cands:
                c = max(cands, key=lambda r: r["run_utc"])
                m["implied"] = float(c["move_pct"])
                m["implied_expiry"] = c["expiry"]

    # Recent results: reports in the last RECENT_DAYS with an actual move.
    recent = []
    for s in syms:
        for m in (hist.get(s) or {}).get("moves", []):
            if m["date"] >= iso(today_ny - dt.timedelta(days=RECENT_DAYS)):
                recent.append({"symbol": s, **m})
    # A report that already has its actual move moves from upcoming to recent.
    done = {(r["symbol"], r["date"]) for r in recent}
    up_list = []
    for s, u in upcoming.items():
        if (s, u["date"]) in done:
            continue
        past = [m["move"] for m in (hist.get(s) or {}).get("moves", []) if m["date"] < u["date"]][-8:]
        # EPS/revenue: the actual figures once the company has reported, else the forecasts for the quarter.
        sp = surprise_for(surp, s, u["date"])
        if sp:
            u["surp"] = {k: v for k, v in sp.items() if k != "src"}
        else:
            f = dict(uni.get(s, {}).get("fc") or {})
            if f.get("eps") is None and u.get("eps_fc") is not None:
                f["eps"] = u["eps_fc"]
            if f.get("eps") is not None or f.get("rev") is not None:
                u["fc"] = f
        up_list.append({"symbol": s, **u, "avg_abs": round(sum(abs(x) for x in past) / len(past), 2) if past else None,
                        "n_past": len(past)})
    up_list.sort(key=lambda u: (u["date"], {"bmo": 0, "tbc": 1, "amc": 2}.get(u["time"], 1), -uni.get(u["symbol"], {}).get("cap", 0)))
    recent.sort(key=lambda r: (r["date"], r["symbol"]), reverse=True)

    if not up_list and prev.get("upcoming") and fails > 3:
        note("No upcoming reports found; kept the previous list")
        up_list = prev["upcoming"]

    data = {
        "generated": run_utc,
        "session": iso(sess),
        "min_cap_bn": MIN_CAP / 1e9,
        "universe": uni,
        "indices": index_levels(),
        "index_days": idx_days,
        "upcoming": up_list,
        "recent": recent,
        "history": {s: hist[s] for s in sorted(hist) if s in uni},
        "problems": problems,
    }
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("Wrote data.json: %d upcoming, %d recent, %d stocks with history, problems: %s"
          % (len(up_list), len(recent), len(data["history"]), problems or "none"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # keep the job green; the page shows the last good data and its age
        import traceback
        traceback.print_exc()
        print("Build failed, data.json left as it was:", e)
    sys.exit(0)
