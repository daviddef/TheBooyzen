#!/usr/bin/env python3
"""requests/*.md and letters.json must agree about what has been sent.

THE FAULT THIS COMES FROM. On 11 October 2026 requests/nlsa-msb751-kolbe-collection.md
still read "DRAFTED, NOT SENT — 15 September". The letter had been sent on 15 September
and ANSWERED IN FULL on the 18th; the four pages were already transcribed on the
documents page, credited to the Senior Librarian who sent them, by name. Anybody
working down the requests folder deciding what to post would have written to her a
second time asking for what she had already supplied. Nothing in the build could see
it, because the two records live in different files and nothing compared them.

WHY THE LINK IS DECLARED AND NOT INFERRED. The first attempt matched files to rows on
keywords and flagged six disagreements. Read one at a time, five were the matcher
hitting unrelated rows — "Edinburgh" appears inside the NLSA row's own notes, "Kew"
matched two rows that were both correctly drafted. One was real. A gate with that
signal-to-noise gets switched off, so each file NAMES its row:

    **Row:** `soas-cwm-journals`     one row, and its sent-ness must agree
    **Row:** none — <reason>         exempt, and the reason is on the page

Exempt is a real answer here, not a dodge: one Kew file carries both Kew rows, the five
Anne Brest files and six Anne Brest rows are not one-to-one, and the WikiTree and G2G
drafts are forum posts letters.json does not track. A gate that demanded one row per
file would be demanding a shape this folder does not have.

WHAT IT COMPARES. Only sent-ness, which is the thing that causes the harm — not dates,
not wording. A file is sent unless its Status says NOT SENT or NOT POSTED; a row is sent
unless its state contains "draft". Those two booleans must match.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = os.path.join(ROOT, "requests")
LETTERS = os.path.join(ROOT, "site", "src", "data", "letters.json")


def file_sent(status):
    s = status.upper()
    if "NOT SENT" in s or "NOT POSTED" in s:
        return False
    return "SENT" in s or "ANSWERED" in s


def row_sent(state):
    return "draft" not in str(state).lower()


def main():
    rows = {r["id"]: r for r in json.load(open(LETTERS, encoding="utf-8"))["rows"]}
    bad, exempt, checked, nostatus, norow = [], 0, 0, [], []
    for name in sorted(os.listdir(REQ)):
        if not name.endswith(".md") or name == "OUTBOX.md":
            continue
        t = open(os.path.join(REQ, name), encoding="utf-8").read()
        mrow = re.search(r"^\*\*Row:\*\*\s*(.+)$", t, re.M)
        if not mrow:
            norow.append(name)
            continue
        val = mrow.group(1).strip()
        if val.lower().startswith("none"):
            exempt += 1
            continue
        rid = val.strip("`").split("`")[0].strip()
        mstat = re.search(r"\*\*Status:\s*([^*]+)\*\*", t)
        if not mstat:
            nostatus.append(name)
            continue
        if rid not in rows:
            bad.append((name, "names row %r, which is not in letters.json" % rid))
            continue
        checked += 1
        fs, rs = file_sent(mstat.group(1)), row_sent(rows[rid].get("state"))
        if fs != rs:
            bad.append((name, "file says %s, letters.json row %s says %s" % (
                "SENT" if fs else "NOT SENT", rid,
                "sent (%s)" % rows[rid].get("state") if rs else "drafted")))

    for n in norow:
        bad.append((n, "has no **Row:** line — name its letters.json row, or `none — why`"))
    for n in nostatus:
        bad.append((n, "has no **Status:** line, so nothing can tell whether it was sent"))

    if bad:
        print("  FAIL  letters    %d file(s) disagree with letters.json" % len(bad))
        for n, why in bad:
            print("          %-46s %s" % (n, why))
        print("          A letter whose file says NOT SENT when it has been answered gets")
        print("          sent twice, to somebody who already did the work.")
        return 1
    print("  ok    letters    %d file(s) checked against letters.json, %d exempt by "
          "declaration · %d row(s) in all" % (checked, exempt, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
