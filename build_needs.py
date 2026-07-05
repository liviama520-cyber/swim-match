#!/usr/bin/env python3
"""Build per-school recruiting-needs data (needs.json) for SwimMatch.

Inputs:
  - Championship participant files (scrape_hytek.py / parse_d3_psych.py
    output): 2026 NCAA D1 M/W, 2026 Ivy League M/W, 2026 NCAA D3 psych.
  - swim-coach/public/recruits-2026.json (incoming class of 2026).

Model: a school's recruiting focus for HS class Y is driven by the
championship-level talent that graduates the spring Y (class Y replaces
them). 2025-26 season: JR graduate 2027, SO 2028, FR 2029; the incoming
2026 recruits graduate 2030. Each swimmer contributes weight 1.0 split
across stroke groups by his/her championship events.

Output needs.json:
  {"schools": {name: {g: {"n": swimmers, "total": {grp: w},
                          "byYear": {"2027": {grp: w}, ...},
                          "leaving": {"2027": count, ...}}}}}
"""
import glob
import json
import re
import sys
from collections import defaultdict

MEET_FILES = sys.argv[1:-1] if len(sys.argv) > 2 else None
OUT = sys.argv[-1] if len(sys.argv) > 2 else "needs.json"
RECRUITS = "/Users/lima/swim-coach/public/recruits-2026.json"
STATS = "stats.json"

GRAD = {"SR": 2026, "5Y": 2026, "GR": 2026,
        "JR": 2027, "SO": 2028, "FR": 2029}

GROUPS = ["FR-SP", "FR-MID", "FR-DIST", "BK", "BR", "FL", "IM"]


def event_group(ev):
    m = re.match(r"(\d+)\s+(Free|Back|Breast|Fly|IM)", ev)
    if not m:
        return None
    d, s = int(m.group(1)), m.group(2)
    if s == "Free":
        d = {400: 500, 800: 1000, 1500: 1650}.get(d, d)
        if d <= 100:
            return "FR-SP"
        if d <= 500:
            return "FR-MID"
        return "FR-DIST"
    return {"Back": "BK", "Breast": "BR", "Fly": "FL", "IM": "IM"}[s]


# meet-results school name -> stats.json school name
def make_alias(stats_schools):
    alias = {s: s for s in stats_schools}
    alias.update({
        "California": "Cal", "UNC": "North Carolina",
        "UCSD": "UC San Diego", "GTWN": "Georgetown",
        "Wash U. MO": "Wash U (MO)",
        "BROW": "Brown", "CORN": "Cornell",
        "Dartmouth-NE": "Dartmouth", "HARV-NE": "Harvard",
        "Penn-MA": "Penn", "Princeton-NJ": "Princeton",
        "Yale-CT": "Yale", "Columbia-NY": "Columbia",
    })
    alias.pop("Penn St", None)   # Penn State is not Penn
    return alias


def main():
    stats = json.load(open(STATS))
    schools33 = [s["name"] for s in stats["schools"]]
    alias = make_alias(schools33)

    files = MEET_FILES or sorted(glob.glob("meets/*.json"))
    # championship swimmers: (school, g, name) -> {"yr", "events": set}
    swimmers = {}
    for f in files:
        for r in json.load(open(f)):
            sch = alias.get(r["school"].strip())
            grp = event_group(r["event"])
            if not sch or not grp:
                continue
            key = (sch, r["g"], r["name"].lower().replace(" ", ""))
            e = swimmers.setdefault(key, {"yr": r["yr"], "events": set()})
            e["events"].add(r["event"])
            # keep the more senior label if meets disagree
            if GRAD.get(r["yr"], 9999) < GRAD.get(e["yr"], 9999):
                e["yr"] = r["yr"]

    # aggregate: school -> g -> byYear/total group weights
    agg = defaultdict(lambda: defaultdict(lambda: {
        "n": 0, "total": defaultdict(float),
        "byYear": defaultdict(lambda: defaultdict(float)),
        "leaving": defaultdict(float)}))
    for (sch, g, _), e in swimmers.items():
        grad = GRAD.get(e["yr"])
        if not grad:
            continue
        groups = [event_group(ev) for ev in e["events"]]
        groups = [x for x in groups if x]
        if not groups:
            continue
        w = 1.0 / len(groups)
        a = agg[sch][g]
        a["n"] += 1
        for grp in groups:
            a["total"][grp] += w
            if 2027 <= grad <= 2029:
                a["byYear"][str(grad)][grp] += w
        if 2027 <= grad <= 2029:
            a["leaving"][str(grad)] += 1

    # class of 2030 <- incoming 2026 recruits' stroke mix
    for r in json.load(open(RECRUITS)):
        if not r.get("top5") or r["college"] not in alias.values():
            continue
        if r["college"] not in [s for s in schools33]:
            continue
        groups = [event_group(e["e"]) for e in r["top5"]]
        groups = [x for x in groups if x]
        if not groups:
            continue
        w = 1.0 / len(groups)
        a = agg[r["college"]][r["g"]]
        for grp in groups:
            a["byYear"]["2030"][grp] += w
        a["leaving"]["2030"] += 1

    rnd = lambda d: {k: round(v, 2) for k, v in sorted(d.items())}
    out = {"generated": "2026-07-05", "season": "2025-26",
           "sources": ["2026 NCAA D1 Championships (M/W)",
                       "2026 Ivy League Championships (M/W)",
                       "2026 NCAA D3 Championships psych sheet (M/W)",
                       "SwimSwam class-of-2026 recruiting database"],
           "groups": GROUPS, "schools": {}}
    for sch in sorted(agg):
        out["schools"][sch] = {}
        for g, a in sorted(agg[sch].items()):
            out["schools"][sch][g] = {
                "n": a["n"], "total": rnd(a["total"]),
                "leaving": rnd(a["leaving"]),
                "byYear": {y: rnd(d) for y, d in sorted(a["byYear"].items())},
            }

    json.dump(out, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    cov = sum(len(v) for v in out["schools"].values())
    missing = [s for s in schools33 if s not in out["schools"]]
    print(f"{OUT}: {len(out['schools'])} schools, {cov} gender rosters, "
          f"{len(swimmers)} championship swimmers")
    if missing:
        print("no championship data:", ", ".join(missing))


if __name__ == "__main__":
    main()
