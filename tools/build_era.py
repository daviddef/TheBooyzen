#!/usr/bin/env python3
"""The place table behind the "at the time" notes: which Record Atlas region each place beside a date on a person's page belongs to.

THE DECISION IS data/era-ground.tsv, written by hand: one row per place string exactly as marriages.json prints it (the place of a
marriage record, the only place a person's page prints beside a date), with the Atlas region it belongs to, or '-' for "looked at, and
no region clearly covers it", the reason, and the town whose point (data/era-towns.tsv) lets the kit refuse a place that falls in a
neighbouring region's ring or within 15 km of its own region's edge. This tool turns those rows into site/src/data/era-places.json and
refuses to pass when the rows and the data disagree:

    python3 ../tools/build_era.py                       write src/data/era-places.json
    python3 ../tools/build_era.py --check               build gate: the file is what the rows build, every marriage place has a
                                                        row, and no row is stale
    python3 ../tools/build_era.py --snapshot <Record Atlas>/site/public/context.json [--report drops.json]
                                                        also rebuild src/data/era-snapshot.json (snapshot version 4) from the Atlas's
                                                        versioned contract (the deliberate refresh: nothing in a build ever reads the
                                                        Atlas). The rings and bbox come from the contract itself (1.8.0 and later);
                                                        --rings <regions.json> is only an optional override. --report writes, per
                                                        region, how many eras the builder refused and why (counts only).
    python3 ../tools/build_era.py --living-urls ../private/era-living.json
                                                        write the page paths the notes must never appear on (the living and held-out
                                                        people's pages), for check:era

THE POLICY ON ERAS THE ATLAS HAS NOT ASSESSED. From contract 1.9.0 the Atlas has assessed `cape`, `england`, `western-cape` and most of the
regions this archive touches; an era it marks approximate or contested is used by the kit only for a year well inside it (the boundary
margin, kit/docs/era-notes.md rule l: the kit's defaults, --approx margin --contested scope --margin-years 5, are used as they are). An era
the Atlas has not assessed (contested or approx still null) is refused by the kit by default; this archive builds its snapshot with
--unassessed allow, on purpose and on the record (David approved it for now, 18 October 2026): the snapshot's policy says so, the gate prints
how many notes rest on an unassessed era, and dropping that flag below (then rebuilding) is the whole of going strict. An unassessed era
has null margins, so the kit's margin rule keeps it silent whatever the policy; today every era this archive's places touch is assessed.

A living person's page prints a name, relationships and a town and country, and no marriage record: the notes are never drawn there.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
DATA = os.path.join(SITE, "src", "data")
GROUND = os.path.join(HERE, "..", "data", "era-ground.tsv")
TOWNS = os.path.join(HERE, "..", "data", "era-towns.tsv")
OUT = os.path.join(DATA, "era-places.json")
SNAP = os.path.join(DATA, "era-snapshot.json")


def rows_of(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        yield line.rstrip("\n").split("\t")


def ground():
    rows = {}
    for cols in rows_of(GROUND):
        if cols[0] == "place":
            continue
        place, region, why, town = (cols + ["", "", "", ""])[:4]
        if not place or not region or not why:
            raise SystemExit("era-ground.tsv: a row needs a place, a region (or '-') and a reason: %r" % cols[0][:60])
        if place in rows:
            raise SystemExit("era-ground.tsv: a place appears twice (a row must say one thing)")
        rows[place] = (region, why, town)
    return rows


def towns():
    out = {}
    for cols in rows_of(TOWNS):
        if cols[0] == "town":
            continue
        out[cols[0]] = (float(cols[1]), float(cols[2]))
    return out


def marriages():
    return json.load(open(os.path.join(DATA, "marriages.json"), encoding="utf-8"))["rows"]


def living():
    return json.load(open(os.path.join(DATA, "living.json"), encoding="utf-8"))["living"]


def has_name(s):
    """«—» is what a record prints for no place; it folds to nothing, and the kit refuses a table that holds one."""
    return any(c.isalnum() for c in str(s))


def event_places():
    """Every place string a person's page prints beside a date: the place of a marriage record."""
    out = {}
    for r in marriages():
        if r.get("p") and has_name(r["p"]):
            out[r["p"]] = out.get(r["p"], 0) + 1
    return out


def build():
    rows = ground()
    used = event_places()
    pts = towns()
    table = {}
    for place in sorted(rows):
        region, _, town = rows[place]
        if region == "-":
            table[place] = None
            continue
        table[place] = {"region": region}
        if town:
            if town not in pts:
                raise SystemExit("era-ground.tsv: town %r has no row in era-towns.tsv" % town)
            table[place].update(lat=pts[town][0], lon=pts[town][1])
    return rows, used, table


def living_urls():
    """/people/<slug>/ is the person page the notes are drawn on; /who/<slug>/ is the name page. Neither may carry a note for a living or
    held-out person."""
    urls = []
    for p in living():
        urls.append("/people/%s/" % p["slug"])
        urls.append("/who/%s/" % p["slug"])
    held = json.load(open(os.path.join(DATA, "living-policy.json"), encoding="utf-8")).get("heldOut") or []
    for slug in held:
        urls.append("/people/%s/" % slug)
        urls.append("/who/%s/" % slug)
    return sorted(set(urls))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--snapshot", default=None, help="a local copy of the Record Atlas's context.json (the versioned contract): also rebuild era-snapshot.json")
    ap.add_argument("--rings", default=None, help="OPTIONAL override: the Atlas's regions.json. By default the rings come from the contract (1.8.0 and later)")
    ap.add_argument("--report", default=None, help="write, per region, the eras the builder refused and why (counts only) to this file")
    ap.add_argument("--living-urls", default=None, help="write the living / held-out page paths here (JSON list) and stop")
    a = ap.parse_args()
    if a.living_urls:
        urls = living_urls()
        if not urls:
            raise SystemExit("build_era: no living page found (living.json is written by tools/livingflags.py); a list of none would make the living gate a verdict on nothing")
        os.makedirs(os.path.dirname(os.path.abspath(a.living_urls)), exist_ok=True)
        open(a.living_urls, "w", encoding="utf-8").write(json.dumps(urls, indent=0) + "\n")
        print("era living list: %d page path(s)" % len(urls))
        return 0
    rows, used, table = build()
    missing = sorted(set(used) - set(rows))
    stale = sorted(set(rows) - set(used))
    out = {"_about": "Built by tools/build_era.py from data/era-ground.tsv and data/era-towns.tsv. Place as printed -> {region, lat, lon}, or null where no Atlas "
                     "region covers it. Read by kit erasnap.py.", "places": table}
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if a.check:
        bad = False
        if missing:
            print("  FAIL  era-ground  %d marriage place string(s) have no row in data/era-ground.tsv "
                  "(decide a region, or '-', for each)" % len(missing))
            bad = True
        if stale:
            print("  FAIL  era-ground  %d row(s) in data/era-ground.tsv match no place (stale)" % len(stale))
            bad = True
        try:
            have = open(OUT, encoding="utf-8").read()
        except OSError:
            have = None
        if have != text:
            print("  FAIL  era-ground  site/src/data/era-places.json is not what the rows build (run tools/build_era.py)")
            bad = True
        if not bad:
            mapped = sum(1 for v in table.values() if v)
            print("  ok    era-ground  %d place strings decided (%d mapped to a region, %d to none); the table matches" % (len(table), mapped, len(table) - mapped))
        return 1 if bad else 0
    open(OUT, "w", encoding="utf-8").write(text)
    print("era-places.json: %d place strings (%d mapped)" % (len(table), sum(1 for v in table.values() if v)))
    if missing:
        print("  WARNING %d place string(s) have no row in data/era-ground.tsv" % len(missing))
        return 1
    if a.snapshot:
        cmd = [sys.executable, os.path.join(KIT_TOOLS, "erasnap.py"), "--contract", a.snapshot, "--places", OUT, "--out", SNAP, "--unassessed", "allow"]
        if a.rings:
            cmd += ["--rings", a.rings]
        if a.report:
            cmd += ["--report", a.report]
        r = subprocess.run(cmd)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
