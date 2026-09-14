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

ARK = re.compile(r"ark:/61903/([0-9]:[0-9]:[A-Z0-9\-]+)")


def fold(x):
    import unicodedata
    x = unicodedata.normalize("NFD", str(x or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", x)).strip()


def records_by_place(places):
    """Indexed entries, reached through the people a place names.

    This archive holds 7,274 of them and not one names a place — each carries a
    person and the collection it was indexed from. So the join runs through the
    people: a place lists who stood in it, and a record naming one of them is a
    record read about that place. It reaches 21 of the 51 places, which is a
    fact about how many people each place names rather than a failure of the
    join, and the rest of the register is on its own page as it always was.
    """
    reg = json.load(open(os.path.join(HERE, "..", "site", "src", "data",
                                      "register.json"), encoding="utf-8"))["rows"]
    idx = {}
    for pl in places:
        for who in (pl.get("p") or []):
            idx.setdefault(fold(who), []).append(pl["n"])
    out = {}
    for r in reg:
        if not isinstance(r, dict) or not r.get("u"):
            continue
        m = ARK.search(r["u"])
        if not m:
            continue
        for pn in idx.get(fold(r.get("n")), []):
            out.setdefault(pn, {})[m.group(1)] = {
                "t": f"{r.get('n')} — {(r.get('s') or 'indexed record')}",
                "ark": m.group(1),
            }
    return out


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    recs = records_by_place(d["places"])
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
            "records": list(recs.get(r["n"], {}).values())[:25],
            "nrecords": len(recs.get(r["n"], {})),
            "moreRecords": max(0, len(recs.get(r["n"], {})) - 25) or None,
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
