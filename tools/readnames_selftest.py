#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-test for tools/readnames.py: a planted fault for every rule that holds a name out, and a control that passes.

    python3 tools/readnames_selftest.py        exits 0 when every fault is refused and the control is made

The cases are found in the committed register at run time, so the test needs no fixture and cannot drift from the data."""
import difflib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("readnames", os.path.join(HERE, "readnames.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def run(lines):
    with tempfile.TemporaryDirectory() as d:
        tsv = os.path.join(d, "r.tsv")
        with io.open(tsv, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        R.TSV = tsv
        res, held, held_alias, _n, _a = R.build()
        return res, held


def main():
    reg = R.read_json("register.json")["rows"]
    people = R.read_json("people.json")["people"]
    pf = [R.surname_fold(R.fold(p["n"])) for p in people]
    own = {}
    for r in reg:
        own.setdefault(R.fold(r["n"]), []).append(r)

    def far(f):                                           # not close to any person's name
        g = R.surname_fold(f)
        return not any(difflib.SequenceMatcher(None, g, k).ratio() >= R.NEAR for k in pf) and len(f.split()) >= 2

    late = next(rows[0]["n"] for f, rows in own.items() if len(rows) == 1 and far(f) and not R.DEATH.search(rows[0]["w"].split("with:")[0])
                and not R.DEATH_COLLECTION.search(rows[0]["s"]) and (lambda ys: ys and max(ys) > R.LATEST_YEAR)([int(y) for y in R.YEAR.findall(rows[0]["w"].split("with:")[0])]))
    many = next(rows[0]["n"] for f, rows in own.items() if len(rows) > R.MAX_ROWS and far(f)
                and all(R.row_ok(r, False) for r in rows))
    control = next(rows[0]["n"] for f, rows in own.items() if len(rows) == 1 and far(f)
                   and R.row_ok(rows[0], False) and R.YEAR.search(rows[0]["w"].split("with:")[0] or "") and
                   max(int(y) for y in R.YEAR.findall(rows[0]["w"].split("with:")[0])) <= 1900)
    cases = [
        ("late year, no death event", late, "rule"),
        ("more rows than a page lists", many, "many"),
        ("a name a person already bears", people[0]["n"], "namesake"),
        ("a name in no register row", "Zzyzx Qwertyuiop Plugh", "unknown"),
    ]
    bad = 0
    for label, name, key in cases:
        res, held = run(["NAME\t%s\t/documents/\ttest" % name])
        ok = not res["names"] and held[key] == 1
        print("%-34s %s" % (label, "refused" if ok else "NOT REFUSED"))
        bad += 0 if ok else 1
    res, held = run(["NAME\t%s\t/documents/\ttest" % control])
    ok = len(res["names"]) == 1 and sum(held.values()) == 0
    print("%-34s %s" % ("control (an old single row)", "made" if ok else "NOT MADE"))
    bad += 0 if ok else 1
    print("readnames self-test: %s" % ("ok" if not bad else "FAILED (%d)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
