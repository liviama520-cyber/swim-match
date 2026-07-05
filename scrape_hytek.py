#!/usr/bin/env python3
"""Scrape Hy-Tek realtime results (swimmeetresults.tech style) for individual
swimming events; output one JSON of participant rows:
  {"meet", "g", "event", "name", "yr", "school"}

Usage: python3 scrape_hytek.py <base_url> <gender M|W> <out.json>
Prefers prelims pages (full field); falls back to finals for timed-final
events (e.g. 1650 Free). Skips relays and diving.
"""
import json
import re
import sys
import time
import html
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
STROKE_EVENTS = re.compile(
    r"#(\d+)\s+(?:Men|Women)\s+(\d+)\s+(Free|Back|Breast|Fly|IM)\s*(Prelims|Finals)?\s*$")

YR = r"(?:FR|SO|JR|SR|5Y|GR)"
ROW = re.compile(
    r"^\s*(?:\d+|--)\s+"          # rank or --
    r"(.+?,.+?)\s+"               # "Last, First"
    r"(" + YR + r")\s+"           # class year
    r"([A-Za-z].*?)\s{2,}"        # school (2+ trailing spaces before seed)
    r"\S")


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(t):
    return html.unescape(re.sub(r"<[^>]+>", "", t))


def main():
    base, gender, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    base = base.rstrip("/") + "/"
    idx = get(base + "evtindex.htm")

    # collect event pages: {evt_no: {"P": page, "F": page, "label": ...}}
    events = {}
    for m in re.finditer(r'href="(\d+[PF]\d+\.htm)"[^>]*>([^<]*)', idx):
        page, label = m.group(1), strip_html(m.group(2)).strip()
        em = STROKE_EVENTS.search("#" + label.lstrip("#"))
        if not em:
            continue
        no = em.group(1)
        ev = f"{em.group(2)} {em.group(3)}"
        kind = "P" if "P" in re.search(r"\d+([PF])\d+", page).group(1) else "F"
        events.setdefault(no, {"event": ev, "pages": {}})
        events[no]["pages"][kind] = page

    rows, seen = [], set()
    for no, info in sorted(events.items(), key=lambda kv: int(kv[0])):
        page = info["pages"].get("P") or info["pages"].get("F")
        if not page:
            continue
        try:
            txt = strip_html(get(base + page))
        except Exception as e:
            print(f"  !! {info['event']}: {e}", file=sys.stderr)
            continue
        n = 0
        for line in txt.splitlines():
            rm = ROW.match(line)
            if not rm:
                continue
            name, yr, school = (rm.group(1).strip(), rm.group(2),
                                rm.group(3).strip())
            key = (name, school, info["event"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({"g": gender, "event": info["event"], "name": name,
                         "yr": yr, "school": school})
            n += 1
        print(f"  {info['event']:<12s} {page}  {n} swimmers")
        time.sleep(0.4)

    json.dump(rows, open(out_path, "w"), ensure_ascii=False, indent=0)
    print(f"{out_path}: {len(rows)} rows, "
          f"{len(set((r['name'], r['school']) for r in rows))} swimmers")


if __name__ == "__main__":
    main()
