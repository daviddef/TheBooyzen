#!/usr/bin/env python3
"""Who is living in this archive, decided by the estate's one rule, and written down
for the site to read.   Run before every `astro build`.

The living-people standard, version 2 (16 October 2026), applied to this archive:

  LIVING   80 or younger (this year minus the birth year) with no death recorded, and
           no citation from a public record source. Decided by the kit's
           kit/tools/living_rule.py, never by a test of this archive's own.
  HELD OUT possible minors, and the people promised privacy by id. Not published at
           all: no page, no name as anyone's relative. They must not be in the data.

THE ONE THING THIS ARCHIVE ADDS, AND WHY. people.js is a hand-written, PUBLIC file, and
a living person's birth year must not be committed to it. So a living person is recorded
the way the archive has always recorded one - `b:"living"` in the field a date would
occupy, a word the kit declares in kit/data/living-words.json - and "recorded as living"
is read as living even though no year is there to subtract. A person entered WITH a
year who the rule makes living is therefore a mistake to be refused (the year is a
public date of a living person), not quietly scrubbed. A person entered with a year
that makes them a possible minor is refused for the same reason: held out means absent.

This file is the generator's reading. tools/checkliving2.py makes its own, from the same
kit function and without importing this file, and fails the build if the two disagree or
if anything built shows more than a living person may show.

Writes site/src/data/living.json: slug, name and place of each living person. Nothing
else about them leaves this script. Messages refer to people by position, never name.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(HERE, "site")
DATA = os.path.join(SITE, "src", "data")
KIT = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit")
sys.path.insert(0, os.path.join(KIT, "tools"))
import living_rule as lr  # noqa: E402

WORDS = json.load(open(os.path.join(KIT, "data", "living-words.json"), encoding="utf-8"))
SAID_LIVING = {w.lower() for w in WORDS["saidLiving"]}
YEAR = re.compile(r"\b(1[0-9]\d\d|20\d\d)\b")

# The only keys a living person's entry may carry (no generation number: `g` is the dead's).
LIVING_KEYS = {"n", "b", "d", "l", "s", "r", "p", "w"}


def slug(s):
    """The same slug tools/dossiers.py gives a person page."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ÿ", "y").replace("Ÿ", "Y")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60]


def birth_year(p):
    m = YEAR.search(str(p.get("b") or ""))
    return int(m.group(1)) if m else None


def said_living(p):
    return (str(p.get("b") or "").strip().lower() in SAID_LIVING
            or str(p.get("d") or "").strip().lower() in SAID_LIVING)


def recorded_dead(p):
    d = str(p.get("d") or "").strip()
    return d not in ("", "—", "-") and d.lower() not in SAID_LIVING


def citations(p):
    c = p.get("c") or []
    return [str(x) for x in c]


def families():
    """kin.js read by node: the households, names exactly as written."""
    code = ("import('" + os.path.join(DATA, "kin.js") + "').then(m=>"
            "process.stdout.write(JSON.stringify(m.families)))")
    out = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def resolve(ref, people):
    """A kin reference ("Name" or "Name|token") to an index into people, or None."""
    if not ref:
        return None
    name, _, token = ref.partition("|")
    hits = [i for i, p in enumerate(people) if p["n"] == name]
    if token:
        hits = [i for i in hits if token in (people[i].get("b") or "") or token in (people[i].get("d") or "")]
    return hits[0] if hits else None


def classify(people, fams, held_slugs=(), author_slugs=(), today_year=None):
    """-> (living, held_out) as lists of indexes into `people`."""
    y = today_year or lr.this_year()
    living = []
    for i, p in enumerate(people):
        cites = citations(p)
        if lr.public_source(cites) or recorded_dead(p):
            continue
        by = birth_year(p)
        if said_living(p) or lr.is_living(by, False, cites, y):
            living.append(i)
    liv = set(living)
    parents_of = {}
    for f in fams:
        ps = [resolve(f.get("h"), people), resolve(f.get("w"), people)]
        for k in f.get("kids", []):
            ki = resolve(k["n"], people)
            if ki is not None:
                parents_of.setdefault(ki, set()).update(x for x in ps if x is not None)
    held = []
    for i, p in enumerate(people):
        s = slug(p["n"])
        if s in set(author_slugs):
            continue                      # the author: an adult, named on purpose (decisions.json)
        parent_living = any(q in liv for q in parents_of.get(i, ()))
        if lr.is_held_out(s, birth_year(p), recorded_dead(p), citations(p), parent_living,
                          held_slugs, y):
            held.append(i)
    return living, held


def scrub_problems(p):
    """Why a living person's entry shows more than name, line and place. Empty if clean."""
    out = []
    extra = set(p) - LIVING_KEYS
    if extra:
        out.append("carries field(s) " + ", ".join(sorted(extra)))
    if p.get("b") != "living" or p.get("d") not in ("—", "living"):
        out.append("holds a date or a note in b/d")
    if (p.get("r") or "") != "" or (p.get("p") or []):
        out.append("holds notes or page links (r / p)")
    if p.get("c"):
        out.append("holds citations (c)")
    w = p.get("w") or ""
    if re.search(r"\d", w):
        out.append("place holds a digit")
    return out


def main():
    people = json.load(open(os.path.join(DATA, "people.json"), encoding="utf-8"))["people"]
    pol = json.load(open(os.path.join(DATA, "living-policy.json"), encoding="utf-8"))
    held_slugs = pol.get("heldOut", [])
    author = pol.get("author", [])
    fams = families()
    living, held = classify(people, fams, held_slugs, author)
    bad = []
    for i in held:
        bad.append(f"people.js entry #{i + 1}: a held-out person (possible minor, or held by id) "
                   "is in the data. Held out means absent: remove the entry and every mention.")
    for i in living:
        for why in scrub_problems(people[i]):
            bad.append(f"people.js entry #{i + 1}: a living person's entry {why}. A living person "
                       'is recorded as b:"living", d:"—", r:"", p:[] and optionally w:"Town, Country".')
    if not people:
        bad.append("people.json is empty: refusing to write a roster from nothing.")
    if bad:
        print("livingflags: REFUSED")
        for b in bad:
            print("  - " + b)
        sys.exit(1)
    out = {
        "note": ("Who is living in this archive, as decided by the kit's living_rule.py (80 or "
                 "younger, no death recorded) over people.json, plus anyone the archive records as "
                 "living in the field a date would occupy. Written by tools/livingflags.py and read "
                 "by the layout and the person pages; tools/checkliving2.py recomputes it "
                 "independently and refuses the build if the two differ. A living person is shown "
                 "with their name, their relationships and their town and country, and nothing more."),
        "living": [{"slug": slug(people[i]["n"]), "n": people[i]["n"], "w": people[i].get("w", "")}
                   for i in living],
        "heldOut": sorted(held_slugs),
    }
    json.dump(out, open(os.path.join(DATA, "living.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(DATA, "living.json"), "a").write("\n")
    print(f"livingflags: {len(living)} living, {len(held)} held out, of {len(people)} people")


if __name__ == "__main__":
    main()
