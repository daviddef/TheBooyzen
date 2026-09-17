#!/usr/bin/env python3
"""Work out which people a correction is about, so their page can carry it.

THE GAP THIS CLOSES. corrections.json keys a correction to a PAGE - documents,
open questions, the name - and never to a person. So a correction that is
entirely about one named man could be read on /corrections/ and nowhere else,
least of all on his own page, which is where somebody looking him up will be.
The 17 September audit called this the standing gap, as against the fault, and
this is the half of it that can be derived.

HOW, AND WHAT IT REFUSES TO DO. A person is attached only when their WHOLE held
name appears - forename and surname together, as this archive writes it. Never a
surname alone, never a forename alone. That is not caution for its own sake: this
estate once turned Domenica Prostamo into Domenica Anile by matching a forename,
and it is the error it exists to refuse.

Where two held names overlap in the text the LONGER ONE WINS, so «George
Augustus Kolbe of Wakkerstroom» is not also filed as «George Augustus Kolbe»,
who is a different man kept deliberately apart. The same text may still name
several people in several places, and it should: one correction here quotes De
Villiers on Hermanus Pietersen, names Willem Hermanus Pieterzen in its heading
and Willem Slier of Hamburg eight hundred characters later, and all three are
right.

EVERY ATTRIBUTION IS PRINTED, because a person shown a correction that is not
about them is a small harm that is easy to see and easy to fix, and one refused
in corrections-who-deny.json stays refused.

  python3 tools/correctionswho.py [--dry]
"""
import io, os, re, sys, json, argparse

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "site", "src", "data")


def key(row):
    """Stable across edits to the rest of the file: the date and the claim."""
    return "%s | %s" % (row[0], str(row[1])[:80])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="refuse when the written file is not what this would "
                         "derive today - a derived file with nobody checking it "
                         "is a number waiting to go stale")
    a = ap.parse_args()

    doss = json.load(io.open(os.path.join(D, "dossiers.json"), encoding="utf-8"))["people"]
    names = {}
    for slug, p in doss.items():
        names.setdefault(p["n"].strip(), slug)
        for alt in (p.get("also") or []):
            if isinstance(alt, dict) and alt.get("n"):
                names.setdefault(alt["n"].strip(), slug)
    # longest first, so the longer name claims the span before a shorter one can
    held = sorted([n for n in names if len(n.split()) >= 2], key=len, reverse=True)

    denyp = os.path.join(D, "corrections-who-deny.json")
    deny = set()
    if os.path.exists(denyp):
        for k, slugs in json.load(io.open(denyp, encoding="utf-8")).get("never", {}).items():
            for s in slugs:
                deny.add((k, s))

    rows = json.load(io.open(os.path.join(D, "corrections.json"), encoding="utf-8"))["rows"]
    out, total = {}, 0
    for r in rows:
        txt = " ".join(str(x) for x in r[:4])
        spans = []
        for n in held:
            for m in re.finditer(r"\b" + re.escape(n) + r"\b", txt, re.I):
                s, e = m.span()
                if any(s >= x and e <= y for x, y, _ in spans):
                    continue
                spans.append((s, e, names[n]))
        k = key(r)
        who = sorted({sl for _, _, sl in spans if (k, sl) not in deny})
        if who:
            out[k] = who
            total += len(who)
            if not a.check:
                print("  %s" % str(r[1])[:72])
                for sl in who:
                    print("      → %s" % sl)

    if a.check:
        p = os.path.join(D, "corrections-who.json")
        if not os.path.exists(p):
            print("  FAIL  corrections-who.json has never been built"); return 1
        have = json.load(io.open(p, encoding="utf-8")).get("who", {})
        gone = sorted(set(have) - set(out))
        new = sorted(set(out) - set(have))
        moved = sorted(k for k in set(have) & set(out) if have[k] != out[k])
        if gone or new or moved:
            for k in gone[:5]:
                print("  FAIL  filed against a correction that no longer reads that way: %s" % k[:70])
            for k in new[:5]:
                print("  FAIL  names somebody and is not filed against them: %s" % k[:70])
            for k in moved[:5]:
                print("  FAIL  the people named have changed: %s" % k[:70])
            print("  FAIL  corrections   %d stale, %d missing, %d changed - "
                  "run tools/correctionswho.py" % (len(gone), len(new), len(moved)))
            return 1
        print("  ok    corrections %d of %d name somebody held here, %d attribution(s), "
              "all current" % (len(out), len(rows), total))
        return 0

    print("  %d of %d correction(s) name somebody this archive holds; %d attribution(s)"
          % (len(out), len(rows), total))
    if a.dry:
        print("  --dry: nothing written"); return 0
    p = os.path.join(D, "corrections-who.json")
    json.dump({"note": "Derived by tools/correctionswho.py. A correction is "
                       "attached to a person only when their WHOLE held name "
                       "appears - forename and surname together. Run the tool "
                       "again rather than editing this, and refuse one in "
                       "corrections-who-deny.json.",
               "who": out},
              io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  → %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
