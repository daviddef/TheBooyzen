#!/usr/bin/env python3
"""Build public/atlas-data.json — the places, in the shape the kit's Atlas wants.

The archive's own places.json is the authority; this only reshapes it. The
category is read off the region rather than the kind of settlement, because on
this family the geography IS the story: a Karoo band, a jump of four hundred
miles to the Rand, and a handful of London parishes that are the other end of
the Montjoy line.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "site", "src", "data", "places.json")
OUT  = os.path.join(HERE, "..", "site", "public", "atlas-data.json")

def cat(r):
    reg = (r.get("r") or "") + " " + (r.get("k") or "")
    if re.search(r"London|Middlesex|Mayfair|Strand", reg): return "london"
    if re.search(r"Queensland|Australia", reg):            return "away"
    if re.search(r"Transvaal|Rand|Johannesburg|Pretoria", reg): return "rand"
    if re.search(r"Karoo|Cape|Wodehouse|Barkly|Indwe|Free State", reg): return "cape"
    return "other"

def main():
    d = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in d["places"]:
        if r.get("lat") is None:
            continue
        people = r.get("p") or []
        out.append({
            "name": r["n"], "lat": r["lat"], "lon": r["lon"],
            "cat": cat(r),
            "n": len(people),
            # the kind and the region together are what a reader wants under the name
            "when": r.get("k") or "",
            "what": r.get("w") or "",
            "events": r.get("e") or [],
            "people": [{"n": x} for x in people],
            "href": f"/places/{r['slug']}/" if r.get("slug") else None,
        })
    stats = {"places": len(out),
             "withPeople": sum(1 for p in out if p["n"]),
             "people": sum(p["n"] for p in out)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"places": out, "stats": stats}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"atlas: {len(out)} places, {stats['withPeople']} carrying people, "
          f"{stats['people']} people placed -> {os.path.relpath(OUT, HERE)}")

if __name__ == "__main__":
    sys.exit(main())
