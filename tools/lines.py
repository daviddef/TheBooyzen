#!/usr/bin/env python3
"""The lines page's data, made from the archive's own files and never typed by hand.

    python3 tools/lines.py            write site/src/data/lines.json
    python3 tools/lines.py --check    fail if the committed lines.json is not what this would write
    python3 tools/lines.py --check --living-out private/lines-living.json
                                      also write the living slugs the kit's checklines.py reads (--living)

WHAT IS HELD WHERE. The eleven lines are the ones people.json files its people on (people.json `lines`, the
same eleven the Line filter on The People counts). Each is one LANE of the kit's rivers drawing
(components/BranchRivers.astro, contract kit/docs/lines.md). Every person is on exactly one line, so every person
is on exactly one lane (the gate's E1 holds by construction).

  site/src/data/lines-meta.json   the RESEARCH DECISIONS and the presentation, by line: the status, its note, the
                                  few dated places the archive's own origin statement names (each with the person
                                  who is there), the colour, the lane's label and the page it reads on.
  site/src/data/trees.json        `origins`: the archive's own statement of how each line begins. THIS TOOL REFUSES
                                  a status that disagrees with it (documented <-> documented, unknown <->
                                  origin-unknown, inferred <-> inferred), so a status is never stronger than what
                                  /trees/ already says.
  site/src/data/dossiers.json     the person pages: slug, name, line. A lane's `members` are the people on it who
                                  are NOT living (living.json): the gate refuses a living person as a member.
  site/src/data/register.json     the counts the two pens print.

THE SPAN is the first and last year the documented, not-living people of a line give in their own dates. A year
beside «after», «bef.», «about» or «OTHER» is not a documented year and is left out. A line with no such year has no
span, and the drawing then does not claim «Documented». It is mechanical on purpose: if a span is wrong the grade of
a person is wrong, and that is fixed on the person.

THE PENS. not-yet-placed: the Marico claims (the archive has tested them and could not settle them) and, in its
note, the register rows that have no person page. different-stock: the surnames the register holds none of, because
a shared surname is not a relationship. Neither pen lists a person: nobody here is unplaced.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "site", "src", "data")

YEAR = re.compile(r"(?<!\d)(1[5-9]\d\d|20\d\d)(?!\d)")
HEDGE = re.compile(r"\b(after|bef\.?|before|about|OTHER)\b", re.I)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def years_of(text):
    """The years a date string gives as dates. A hedged string gives none."""
    s = str(text or "")
    return [] if HEDGE.search(s) else [int(y) for y in YEAR.findall(s)]


def build():
    meta = load("lines-meta.json")
    people = load("people.json")
    dossiers = load("dossiers.json")["people"]
    living = {x["slug"] for x in load("living.json")["living"]}
    trees = load("trees.json")
    reg = load("register.json")
    fam = load("families.json")["families"]

    problems = []
    lines = people["lines"]
    if sorted(lines) != sorted(meta["lines"]):
        problems.append("lines-meta.json and people.json disagree about the lines: %s vs %s" % (sorted(meta["lines"]), sorted(lines)))
    kind_to_status = {"documented": "documented", "inferred": "inferred", "unknown": "origin-unknown"}
    by_line = {l: [] for l in lines}
    for slug, p in dossiers.items():
        by_line.setdefault(p["l"], []).append((slug, p))

    lanes = []
    for line in lines:
        m = meta["lines"][line]
        o = trees["origins"][line]
        want = kind_to_status[o["kind"]]
        if m["status"] != want:
            problems.append("%s: lines-meta says %s but trees.json origins says %s (%s)" % (line, m["status"], o["kind"], want))
        rows = by_line[line]
        members = sorted(s for s, _ in rows if s not in living)
        ys = []
        for s, p in rows:
            if s in living or p.get("s") != "doc":
                continue
            ys += years_of(p.get("b")) + years_of(p.get("d"))
        lane = {"key": line.lower(), "colour": m["colour"], "label": m["label"], "href": m["href"], "read": m["read"],
                "status": m["status"], "statusNote": m["statusNote"]}
        if ys:
            lane["span"] = [min(ys), max(ys)]
        nodes = []
        for n in m.get("nodes", []):
            if n["person"] not in dossiers or dossiers[n["person"]]["l"] != line or n["person"] in living:
                problems.append("%s: node person %r is not a not-living person of that line" % (line, n["person"]))
            nodes.append({"place": n["place"], "year": n["year"], "why": n["why"], "person": n["person"]})
        # a node's person is on the lane by the node; the kit lists as members the people that are NOT a node (E1)
        on_node = {n["person"] for n in nodes}
        lane["members"] = [s for s in members if s not in on_node]
        if nodes:
            lane["nodes"] = nodes
        lanes.append(lane)

    # ---- the pens
    claims = trees["notPlaced"]["maricoClaims"]
    nrows = len(reg["rows"])
    noperson = sum(1 for r in reg["rows"] if not r.get("p"))
    fmt = lambda n: format(n, ",")
    pens = [{
        "id": "unplaced", "kind": "not-yet-placed",
        "head": "Claims of the name, not placed on any of these lines",
        "note": ("Nobody in this archive is unplaced: every person is on exactly one line. What is not placed is a cluster "
                 "the archive tested and could not settle, drawn here as one dot, and the register's raw catch. %s Booyzen "
                 "claims for compensation were filed from the district of Marico in 1903-04, indexed by initials; nothing "
                 "yet joins any of them to a person on these lines. And %s of the register's %s rows have no person page: "
                 "they come from surname indexes, a shared surname is not a relationship, and they are counted in the "
                 "register, not listed here." % (claims, fmt(noperson), fmt(nrows))),
        "items": [["Marico, 1903-04", "/atlas/",
                   "%s Booyzen claims for compensation as burghers, filed from the district of Marico and indexed by "
                   "initials. Unresolved: the atlas keeps them apart from the Graaff-Reinet line and says so." % claims]],
    }]
    notharvested = sorted(((n, c["total"]) for n, c in (reg.get("caps") or {}).items() if c["total"] > 0 and c["got"] == 0),
                          key=lambda x: (-x[1], x[0]))
    pens.append({
        "id": "other-stock", "kind": "different-stock",
        "head": "Attached to no line here: surnames too common to be evidence",
        "note": ("The register holds none of the records of these surnames. A name shared by this many index rows is not "
                 "evidence of a relationship, so none is harvested and none is placed on a line."),
        "items": [[n, "/register/", "%s index rows, none harvested" % fmt(t)] for n, t in notharvested],
    })

    out = {
        "title": "The lines this archive follows, and how far each is documented",
        "caption": ("Each lane is a surname the archive files people under, and every person is on exactly one. The mark and "
                    "the small capitals under a lane's title say how far its evidence reaches: documented from the first year "
                    "a document gives, and whether where the line began is documented, inferred or not found. Hover or tab any "
                    "dot to read what stands behind it; select it again to go there."),
        "lanes": lanes,
        "pens": pens,
    }
    return out, problems, sorted(living)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--living-out")
    a = ap.parse_args()
    out, problems, living = build()
    text = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    path = os.path.join(DATA, "lines.json")
    if problems:
        print("lines: REFUSED")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    if a.living_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.living_out)), exist_ok=True)
        with open(a.living_out, "w", encoding="utf-8") as f:
            json.dump(living, f)
    if a.check:
        have = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if have != text:
            print("  FAIL  lines  site/src/data/lines.json is not what tools/lines.py makes from the archive's data: run `python3 tools/lines.py` and commit it")
            sys.exit(1)
        n = sum(len(l["members"]) + len(l.get("nodes", [])) for l in out["lanes"])
        print("  ok    lines  %d lanes, %d people on them, %d pens; lines.json is what the data makes" % (len(out["lanes"]), n, len(out["pens"])))
        return
    open(path, "w", encoding="utf-8").write(text)
    print("lines: %d lanes, %d people on them, %d pens" % (len(out["lanes"]), sum(len(l["members"]) + len(l.get("nodes", [])) for l in out["lanes"]), len(out["pens"])))


if __name__ == "__main__":
    main()
