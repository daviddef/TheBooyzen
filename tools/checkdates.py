#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A person record that is vaguer than a date this archive already holds.

THE FAULT, THREE TIMES IN A MONTH, ALWAYS IN THE SAME FILE.

  Sept  JOHAN CASIMIR KOLBE was named in both his parents' death notices,
        transcribed here since 10 September, and had no person record at all.
        That row wrote the lesson itself: A SEARCH OF THE INDEX IS NOT A
        SEARCH OF THE HOLDINGS.
  Oct   MARGARET DOWNING carried d = "2_ Nov 1867 — the day illegible on the
        stone". Her death notice answers question 7 with "25th November
        1867", and the 25th was ALREADY WRITTEN in five other files here.
  Oct   ANNA JOHANNA MARIA PRETORIUS carried "1944" against a published form
        reading "Twenty-sixth day of February, 1944"; WILLIEM JOHANNES KOLBE
        carried "1941 — aged about 94" against a civil death registration
        giving 23 April 1941, at 93.

Every one of them was a fact the archive HAD, missing from the one file the
pages and the charts actually read. Nothing could see it, because the two
records live in different files and nothing compared them.

WHAT IT COMPARES. Every event in timeline.json that carries an exact day,
month and year AND names people in `p`, against those people's own `b` and
`d`. It speaks when the event's YEAR appears in the person's field and that
field is vaguer than the event — an underscore, "c.", "bef.", "aft.",
"about", a question mark, or simply no day and month. Same year only: this
gate does not guess which event belongs to which field, it only notices that
one of them is sharper.

WHY EXEMPTIONS ARE DECLARED AND NOT INFERRED. The first sweep flagged nine
and two were real. The other seven were the archive being careful — a bound
derived from somebody else's document, a baptism eleven months after a birth,
a burial that is not a death, and a death year left open because two sons
wrote contradictory notices in 1915. A gate at that signal-to-noise gets
switched off, so each one is named in src/data/dates-exempt.json with its
reason, and the reason is the point: it is the archive stating why the vaguer
value is the honest one.

IT ALSO REPORTS AN EXEMPTION IT NO LONGER NEEDS, which is the direction
checkcovers.py taught. A declaration that has stopped applying means somebody
sharpened the record and left the excuse behind.

  python3 tools/checkdates.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")

EXACT = re.compile(r"\b(\d{1,2}) ([A-Z][a-z]{2})[a-z]*\.? (\d{4})\b")
VAGUE = re.compile(r"_|c\.|bef\.|aft\.|about|\?")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    events = load("timeline.json")["events"]
    people = {p["n"]: p for p in load("people.json")["people"]}
    dec = load("dates-exempt.json")["exempt"]
    declared = {(e["n"], e["f"]): e["why"] for e in dec}

    pairs = 0
    found = {}
    for ev in events:
        m = EXACT.search(ev.get("d") or "")
        if not m:
            continue
        for name in ev.get("p") or []:
            person = people.get(name)
            if not person:
                continue
            pairs += 1
            for field in ("b", "d"):
                val = person.get(field) or ""
                if m.group(3) in val and (VAGUE.search(val) or not EXACT.search(val)):
                    found.setdefault((name, field), (val, ev.get("d"), ev.get("t", "")))

    undeclared = {k: v for k, v in found.items() if k not in declared}
    stale = [k for k in declared if k not in found]

    if undeclared or stale:
        print("  FAIL  dates      %d undeclared, %d stale declaration(s)"
              % (len(undeclared), len(stale)))
        for (name, field), (val, evd, evt) in sorted(undeclared.items()):
            print("          %s (%s) = %r" % (name, field, val))
            print("            but the timeline has %s — %s" % (evd, evt[:66]))
            print("            Put the sharper date in the person record, or declare why not")
            print("            in src/data/dates-exempt.json.")
        for name, field in sorted(stale):
            print("          %s (%s) is declared exempt and no longer needs to be —" % (name, field))
            print("            the record was sharpened; delete the line.")
        return 1

    print("  ok    dates      %d person-event pair(s) compared, %d declared exempt with a "
          "reason · no record vaguer than a date this archive holds" % (pairs, len(declared)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
