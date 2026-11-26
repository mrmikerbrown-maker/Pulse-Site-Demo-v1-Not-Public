"""Marks release days where something else could have moved markets, so the page can warn and optionally leave them out.
  - a Fed decision later the same day (from fed-scenario-planner/fomc_surprises.csv, kept up to date by that page's job)
  - another of this page's releases out the same day (e.g. jobs and retail sales together)
Also attaches the hand-written "what else was going on" notes in notes.json (keyed by date)."""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

def fomc_dates():
    p = os.path.join(HERE, "..", "fed-scenario-planner", "fomc_surprises.csv")
    try:
        return {r["date"] for r in csv.DictReader(open(p))}
    except Exception:
        return set()

def mark(rels):
    """rels: {key: {"tab":..., "rows": [{"d":...}, ...]}}. Adds row["x"] (list of reasons) and row["n"] (note)."""
    fomc = fomc_dates()
    try:
        notes = json.load(open(os.path.join(HERE, "notes.json")))
    except Exception:
        notes = {}
    by_day = {}
    for k, R in rels.items():
        for r in R["rows"]:
            by_day.setdefault(r["d"], []).append(R["tab"])
    for k, R in rels.items():
        for r in R["rows"]:
            x = []
            if r["d"] in fomc:
                x.append("Fed decision later the same day")
            others = [t for t in by_day[r["d"]] if t != R["tab"]]
            if others:
                x.append("Also out the same day: " + ", ".join(others))
            if x:
                r["x"] = x
            else:
                r.pop("x", None)
            if r["d"] in notes:
                r["n"] = notes[r["d"]]
    return rels
