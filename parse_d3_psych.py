#!/usr/bin/env python3
"""Parse the NCAA D3 championships psych sheet PDF (Hy-Tek two-column layout)
into participant rows {"g","event","name","yr","school"}.

Usage: python3 parse_d3_psych.py <psych.pdf> <out.json>
"""
import json
import re
import sys
from pypdf import PdfReader

SPLIT = 128  # column split position in layout-mode text

ANY_EVENT = re.compile(r"Event\s+\d+\s")
EVENT = re.compile(r"Event\s+\d+\s*\.*\s*\(?(Men|Women)\s+(\d+)\s+Yard\s+"
                   r"(Freestyle|Backstroke|Breaststroke|Butterfly|IM)\)?\s*$")
ROW = re.compile(r"^\s*\d+\s+(.+?,.+?)\s{2,}(FR|SO|JR|SR|5Y|GR)\s{2,}"
                 r"(.+?)(?:\s{2,}[\d:.NTX]+.*)?$")
STROKE = {"Freestyle": "Free", "Backstroke": "Back",
          "Breaststroke": "Breast", "Butterfly": "Fly", "IM": "IM"}


def main():
    pdf, out_path = sys.argv[1], sys.argv[2]
    r = PdfReader(pdf)
    # flow: per page, left column top-to-bottom, then right column
    stream = []
    for page in r.pages:
        txt = page.extract_text(extraction_mode="layout")
        left, right = [], []
        for line in txt.splitlines():
            left.append(line[:SPLIT].rstrip())
            right.append(line[SPLIT:].rstrip())
        stream.extend(left)
        stream.extend(right)

    rows, seen = [], set()
    cur = None  # (gender, event)
    for line in stream:
        if ANY_EVENT.search(line):
            em = EVENT.search(line)
            if em:
                g = "M" if em.group(1) == "Men" else "W"
                cur = (g, f"{em.group(2)} {STROKE[em.group(3)]}")
            else:
                cur = None  # diving / relay: ignore following rows
            continue
        if cur is None:
            continue
        rm = ROW.match(line)
        if not rm:
            continue
        name, yr, school = (rm.group(1).strip(), rm.group(2),
                            rm.group(3).strip())
        key = (name, school, cur[1], cur[0])
        if key in seen:
            continue
        seen.add(key)
        rows.append({"g": cur[0], "event": cur[1], "name": name,
                     "yr": yr, "school": school})

    json.dump(rows, open(out_path, "w"), ensure_ascii=False, indent=0)
    from collections import Counter
    ev = Counter((r["g"], r["event"]) for r in rows)
    for k, v in sorted(ev.items()):
        print(k, v)
    print(f"{out_path}: {len(rows)} rows, "
          f"{len(set((r['name'], r['school']) for r in rows))} swimmers")


if __name__ == "__main__":
    main()
