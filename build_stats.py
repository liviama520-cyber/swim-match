#!/usr/bin/env python3
"""Build aggregate recruiting stats from swim-coach/public/recruits-2026.json.

Publishes ONLY aggregate statistics (per school x gender: roster point
distributions; per event: time ranges). No swimmer names or individual
records are included in the output.

Output: stats.json
"""
import json
import statistics
from collections import defaultdict

SRC = "/Users/lima/swim-coach/public/recruits-2026.json"
OUT = "stats.json"


def parse_t(s):
    s = str(s)
    if ":" in s:
        m, sec = s.split(":")
        return int(m) * 60 + float(sec)
    return float(s)


def implied_base(t, p):
    # SwimCloud points: p = 1000 * (B/T)^3  =>  B = T * (p/1000)^(1/3)
    return t * (p / 1000.0) ** (1.0 / 3.0)


def cluster_bases(values, gap=0.03):
    """Sort implied bases and split into clusters at relative gaps > 3%."""
    values = sorted(values)
    clusters = [[values[0]]]
    for v in values[1:]:
        if v - clusters[-1][-1] > gap * clusters[-1][-1]:
            clusters.append([])
        clusters[-1].append(v)
    return [statistics.median(c) for c in clusters]


def main():
    data = json.load(open(SRC))
    recruits = [r for r in data if r.get("top5")]

    # ---- 1. recover base times per (gender, event), split SCY vs LCM ----
    raw = defaultdict(list)
    for r in recruits:
        for e in r["top5"]:
            t, p = parse_t(e["t"]), e["p"]
            if t and p:
                raw[(r["g"], e["e"])].append(implied_base(t, p))

    LCM_ONLY = {"400 Free", "800 Free", "1500 Free"}
    SCY_ONLY = {"500 Free", "1000 Free", "1650 Free"}
    bases = {}  # (g, event) -> {"scy": B or None, "lcm": B or None}
    for (g, ev), vals in raw.items():
        cl = cluster_bases(vals)
        entry = {"scy": None, "lcm": None}
        if ev in LCM_ONLY:
            entry["lcm"] = cl[0]
        elif ev in SCY_ONLY:
            entry["scy"] = cl[0]
        else:
            entry["scy"] = cl[0]
            if len(cl) > 1:
                entry["lcm"] = cl[-1]
        bases[(g, ev)] = entry

    # fill missing LCM bases using the median lcm/scy ratio of events that have both
    ratios = [b["lcm"] / b["scy"] for b in bases.values() if b["scy"] and b["lcm"]]
    med_ratio = statistics.median(ratios)
    for b in bases.values():
        if b["scy"] and not b["lcm"]:
            b["lcm"] = b["scy"] * med_ratio

    # ---- 2. per-recruit best points; per school+gender roster distribution ----
    schools = {}
    meta = {}
    for r in recruits:
        key = (r["college"], r["g"])
        best = max(e["p"] for e in r["top5"] if e["p"])
        schools.setdefault(key, []).append(best)
        meta[r["college"]] = {"div": r["div"], "conf": r["conf"]}

    # drop outliers far below a roster's median — these are almost always
    # wrong SwimCloud name matches, and one bad point wrecks the school's range
    OUTLIER_GAP = 150
    dropped = []
    for key, pts in schools.items():
        if len(pts) >= 3:
            med = statistics.median(pts)
            kept = [p for p in pts if p >= med - OUTLIER_GAP]
            if len(kept) < len(pts):
                dropped.append((key, [p for p in pts if p < med - OUTLIER_GAP]))
            schools[key] = kept
    for key, out in dropped:
        print(f"  outlier dropped {key}: {out}")

    # ---- 3. per school+gender+event: SCY-equivalent time ranges ----
    # convert every swim to SCY-equivalent via points identity:
    #   t_scy = B_scy * (1000/p)^(1/3)
    ev_times = defaultdict(list)
    for r in recruits:
        for e in r["top5"]:
            p = e["p"]
            b = bases.get((r["g"], e["e"]))
            if not p or not b:
                continue
            ev = e["e"]
            # map LCM-only events onto their SCY counterparts for display
            ev = {"400 Free": "500 Free", "800 Free": "1000 Free",
                  "1500 Free": "1650 Free"}.get(ev, ev)
            bb = bases.get((r["g"], ev))
            if not bb or not bb["scy"]:
                continue
            t_scy = bb["scy"] * (1000.0 / p) ** (1.0 / 3.0)
            ev_times[(r["college"], r["g"], ev)].append(round(t_scy, 2))

    out = {
        "generated": "2026-07-04",
        "classYear": 2026,
        "pointBases": {
            f"{g}|{ev}": {"scy": round(b["scy"], 3) if b["scy"] else None,
                          "lcm": round(b["lcm"], 3) if b["lcm"] else None}
            for (g, ev), b in bases.items()
        },
        "lcmScyRatio": round(med_ratio, 4),
        "schools": [],
    }

    for college in sorted(meta):
        entry = {"name": college, **meta[college], "rosters": {}}
        for g in ("M", "W"):
            pts = schools.get((college, g))
            if not pts:
                continue
            pts = sorted(pts)
            events = {}
            for (c, gg, ev), ts in ev_times.items():
                if c == college and gg == g:
                    events[ev] = {"n": len(ts), "min": min(ts),
                                  "med": round(statistics.median(ts), 2),
                                  "max": max(ts)}
            entry["rosters"][g] = {
                "n": len(pts),
                "pMin": pts[0], "pMax": pts[-1],
                "pMed": round(statistics.median(pts), 1),
                "points": pts,
                "events": events,
            }
        if entry["rosters"]:
            out["schools"].append(entry)

    json.dump(out, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    n_sch = len(out["schools"])
    n_ros = sum(len(s["rosters"]) for s in out["schools"])
    print(f"stats.json: {n_sch} schools, {n_ros} gender rosters, "
          f"{len(out['pointBases'])} point bases, lcm/scy ratio {med_ratio:.4f}")


if __name__ == "__main__":
    main()
