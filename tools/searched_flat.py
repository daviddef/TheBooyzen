#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The flat `searched` list, derived from `sets` so the two cannot drift.

WHY. Record Atlas imports a list of OBJECTS (src / url / what / when / outcome)
from each archive's searched.json. This archive records its work as `sets`,
whose rows are lists (question, answer, note, verdict) for a reader. The
importer read 0 of them; a hand-kept flat list followed and held 28 rows
against about 880 recorded queries. A second list written by hand is the
mechanism that made the first gap, so it is derived here instead.

WHAT IS DERIVED, AND WHAT IS NOT GUESSED.
  * A set contributes rows only when src/data/searched-map.json names the ONE
    source the whole set was run against. Nothing is read out of a row's wording
    to find a provider: a set whose title names no single source is listed there
    as `source-not-named`, and an audit, a reading of this archive's own files
    or an answer received is `not-a-search`. Both contribute nothing.
  * One row per query: src = the mapped source, what = the question, when = the
    set's date (ISO), outcome from the verdict (yes/part -> yield, no ->
    nothing, blocked -> blocked). A `void` row is a query that did not count and
    is left out. No url, film, pages, waypoint or walked is written: the sets do
    not hold them, and the hand-written rows above the derived ones do.
  * tags = the surname families and place names written IN THE QUESTION, plus
    the source. Not taken from the set title.
  * A set whose source and date already have a hand-written flat row is left to
    that row, which is richer (it carries the film and the pages).

THE GATE. `python3 tools/searched_flat.py` exits 1 if a set has no entry in the
map, if a map entry matches no set, or if the derived rows in searched.json
differ from what the map and the sets give now. `--write` regenerates them.
Hand-written rows are never touched: a derived row carries "derived": "sets".
"""
import datetime
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")
SEARCHED = os.path.join(DATA, "searched.json")
MAP = os.path.join(DATA, "searched-map.json")

OUTCOME = {"yes": "yield", "part": "yield", "no": "nothing", "blocked": "blocked"}

# Surname families written in a question. The family a name belongs to, not a
# spelling list: the spellings live in the Record Atlas catalogue.
FAMILIES = {
    "booyzen": r"boo[iyÿ][sz]en|booyzen",
    "mountjoy": r"mou?ntjo[yi]\w*|montjo[yi]\w*",
    "kolbe": r"[kc]olbe\w?",
    "barry": r"\bbarry\b|\bberry\b",
    "daschner": r"daschner",
    "mccabe": r"mc ?cabe",
    "downing": r"downing",
    "slier": r"slier|sleer",
    "werdmuller": r"werdm[uü]ller",
    "pretorius": r"pretorius",
    "olivier": r"olivier",
    "schoeman": r"schoeman",
    "kumm": r"k[uü]mm",
}


def fold(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def head(src):
    """The provider part of a source string: text before the first dash or comma."""
    return fold(re.split(r"\s+[—–-]\s+|\s*·\s*|,", src.strip())[0]).strip()


def iso(d):
    return datetime.datetime.strptime(d.replace("Sept", "Sep"), "%d %b %Y").strftime("%Y-%m-%d")


def place_names():
    p = json.load(open(os.path.join(DATA, "places.json"), encoding="utf-8"))
    return sorted({x["n"] for x in p["places"] if len(x.get("n", "")) >= 5}, key=len, reverse=True)


def tags_for(question, src, places):
    q = fold(question)
    out = [f for f, rx in FAMILIES.items() if re.search(rx, q)]
    for n in places:
        if re.search(r"\b" + re.escape(fold(n)) + r"\b", q):
            out.append(fold(n).replace(" ", "-"))
    t = re.sub(r"[^a-z0-9]+", "", head(src).split(" ")[0])
    if t:
        out.append(t)
    seen = []
    for x in out:
        if x not in seen:
            seen.append(x)
    return seen


def derive(doc, mp):
    problems = []
    entries = {(e["g"], e["d"]): e for e in mp["sets"]}
    keys = [(s["g"], s["d"]) for s in doc["sets"]]
    for k in keys:
        if k not in entries:
            problems.append(f"set has no entry in searched-map.json: {k[1]} · {k[0][:70]}")
    for k in entries:
        if k not in keys:
            problems.append(f"searched-map.json entry matches no set: {k[1]} · {k[0][:70]}")
    for k, e in entries.items():
        if "src" not in e and "skip" not in e:
            problems.append(f"map entry has neither src nor skip: {k[1]} · {k[0][:70]}")

    hand = [r for r in doc["searched"] if r.get("derived") != "sets"]
    covered = {(head(r.get("src", "")), r.get("when")) for r in hand}
    places = place_names()
    rows, left_to_hand = [], 0
    for s in doc["sets"]:
        e = entries.get((s["g"], s["d"]))
        if not e or "src" not in e:
            continue
        when = iso(s["d"])
        if (head(e["src"]), when) in covered:
            left_to_hand += len(s["rows"])
            continue
        for r in s["rows"]:
            v = (r[3] if len(r) > 3 else "").strip().lower()
            if v not in OUTCOME:
                continue
            rows.append({
                "src": e["src"], "what": r[0].strip(), "when": when,
                "outcome": OUTCOME[v], "tags": tags_for(r[0], e["src"], places),
                "note": s["g"], "derived": "sets",
            })
    return hand, rows, problems, left_to_hand


def main():
    write = "--write" in sys.argv
    doc = json.load(open(SEARCHED, encoding="utf-8"))
    mp = json.load(open(MAP, encoding="utf-8"))
    hand, rows, problems, left = derive(doc, mp)
    total = sum(len(s["rows"]) for s in doc["sets"])
    have = [r for r in doc["searched"] if r.get("derived") == "sets"]
    if have != rows:
        problems.append(f"derived rows in searched.json ({len(have)}) differ from what searched-map.json derives ({len(rows)}); "
                        "run: python3 tools/searched_flat.py --write")
    if write and have != rows:
        doc["searched"] = hand + rows
        with open(SEARCHED, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        problems = [p for p in problems if "differ from what" not in p]
        print(f"wrote {len(rows)} derived rows after {len(hand)} hand-written")
    skipped = {}
    for e in mp["sets"]:
        if "skip" in e:
            skipped[e["skip"]] = skipped.get(e["skip"], 0) + 1
    print(f"  {'FAIL ' if problems else 'ok   '} searched-flat  {len(hand)} hand-written + {len(rows)} derived flat rows from {total} set rows "
          f"({left} left to a hand-written row for the same source and day; skipped sets: {skipped})")
    if problems:
        for p in problems:
            print("        ", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
