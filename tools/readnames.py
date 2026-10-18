#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The second source of names: people the archive READ in a record and holds in no family file.

    python3 tools/readnames.py            writes site/src/data/readnames.json
    python3 tools/readnames.py --check    exits 1 if the committed readnames.json is not what the inputs give (no build needed)

WHY THIS EXISTS (18 October 2026, the linking standard's L2). The narrative pages name people whom the archive read in a
FamilySearch index row (a baptism, a marriage, a burial) and who are in no family file: no /people/ page, no /who/ page, so
the build-time linker (tools/namesindex.py -> kit autolink.py) had nothing to link a name to. A /who/<slug>/ NAME page is
made for each name David's ruling allows: ONLY a name the narrative pages need, and ONLY a person the living rule shows dead.

THE MODEL. data/read-names.tsv is the REVIEWED list: one line per name the prose uses, with the pages that use it and the
reason it was accepted (the prose context agrees with the row: the year, the place, the relationship). This tool does not
choose names; it REFUSES any name on that list that fails a rule, and drops it (counted, never named):

  * the name must be the name of at least one row of src/data/register.json (the row's own name field), or, for a role
    NAMED, a parent or spouse the "with:" field of a row names. Nothing is invented and nothing is guessed.
  * THE LIVING RULE (the estate's, kit living_rule.py: a citation from a public record source, FamilySearch, means not
    living) AND David's hold-out of 18 October 2026: a row whose latest event year is after 1945 and which records no death,
    burial or probate event is held out, and so is the name. A name only a "with:" field gives needs the indexed act itself
    dated 1945 or earlier (a relative named in a recent act may be living). Any row that fails holds the whole name out,
    because the page lists every row of the name.
  * a name a living person bears (as a name or a recorded spelling), or one that is the same name as anyone in people.json once the
    spelling variants are folded (Booy-/Booij-/Booys-, Stefanus/Stephanus, Nicolas/Nicolaas), or that begins with the same three
    forenames as a person's: that person has a page and the name is, or may be, theirs; a second, read-name page would send the narrative's man to a list of strangers' index rows.
  * not more than FOUR rows: a name that many index rows share is a name of many men, and the prose means one of them.
  * the slug must be new: no /who/ page exists for it already.

ALIASES. A line `ALIAS<TAB>name<TAB>person slug` gives a person who already has a page one more spelling, only where the
DATA states it: every register row of that name carries that same person page (the register's `p` field, made by
tools/register.py from people.js). Nothing else is added as an alias.

Reads only committed files, so CI builds the same readnames.json. Prints counts, never a name.
"""
import argparse
import difflib
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "site", "src", "data")
PAGES_DIR = os.path.join(ROOT, "site", "src", "pages")
TSV = os.environ.get("READNAMES_TSV") or os.path.join(ROOT, "data", "read-names.tsv")
OUT = os.environ.get("READNAMES_OUT") or os.path.join(DATA, "readnames.json")
LATEST_YEAR = 1945          # David, 18 October 2026: a later year with no death event is held out
MAX_ROWS = 4
NEAR = 0.88                 # how alike two folded names must be to be taken for the same person's
YEAR = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")
DEATH = re.compile(r"\b(death|burial|buried|probate|funeral|died)\b", re.I)
DEATH_COLLECTION = re.compile(r"Probate|Cemetery|Deceased Estate|Death", re.I)


def fold(s):
    s = unicodedata.normalize("NFKD", " ".join(str(s or "").split()))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ÿ", "y").replace("'", "").replace("’", "").replace("‘", "").replace("-", " ").replace("*", "")
    return " ".join(s.casefold().split())


def surname_fold(f):
    """Booij-/Booys-/Booyz- and the like are one family's spellings here; the near-name test reads them as one."""
    return re.sub(r"\bboo(?:ij|y|i)?[sz]?e?n\b", "booyzen", f)


def slugify(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ÿ", "y").replace("Ÿ", "Y")
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()[:60]


def read_json(name):
    with io.open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def page_titles():
    out = {}
    for fn in os.listdir(PAGES_DIR):
        if fn.endswith(".astro"):
            m = re.search(r'<Base\s+title="([^"]+)"', io.open(os.path.join(PAGES_DIR, fn), encoding="utf-8").read())
            if m:
                out["/" + fn[:-6] + "/"] = m.group(1)
    return out


def read_tsv():
    names, aliases = [], []
    if not os.path.isfile(TSV):
        return names, aliases
    with io.open(TSV, encoding="utf-8") as fh:
        for ln in fh.read().split("\n"):
            if not ln.strip() or ln.startswith("#"):
                continue
            c = ln.split("\t") + [""] * 4
            if c[0] == "NAME":
                names.append({"name": c[1].strip(), "pages": [p for p in c[2].split(",") if p.strip()], "basis": c[3].strip()})
            elif c[0] == "ALIAS":
                aliases.append({"name": c[1].strip(), "person": c[2].strip(), "basis": c[3].strip()})
    return names, aliases


def row_event(r):
    return r["w"].split("with:")[0].strip(" ·|—-")


def row_ok(r, named):
    """David's rule for one row (see the module note)."""
    ev = r["w"].split("with:")[0]
    ys = [int(y) for y in YEAR.findall(ev)]
    if named:                                   # a relative named in the act: the act must be old
        return bool(ys) and max(ys) <= LATEST_YEAR
    if DEATH.search(ev) or DEATH_COLLECTION.search(r.get("s", "")):
        return True
    if not ys:
        return True                             # no date in the row: the public source alone decides, as the rule says
    return max(ys) <= LATEST_YEAR


def build():
    reg = read_json("register.json")["rows"]
    people = read_json("people.json")["people"]
    living = read_json("living.json")["living"]
    dossiers = read_json("dossiers.json")["people"]
    titles = page_titles()
    names, aliases = read_tsv()

    # the folded names of everyone in people.json, with spellings the data records
    pfold, living_f = {}, set()
    live_slugs = {x["slug"] for x in living}
    for p in people:
        forms = {p["n"], re.sub(r"\s*\(.*?\)\s*", " ", p["n"]), re.sub(r"\s*[“\"][^”\"]+[”\"]\s*", " ", p["n"]),
                 re.sub(r"[“”\"]", "", p["n"])}
        for seg in re.split(r"\s*[·;]\s*", str(p.get("v") or "")):
            forms.add(re.sub(r"\(.*?\)", "", seg.split(",")[0]))
        for f in forms:
            if len(f.split()) >= 2:
                pfold.setdefault(fold(f), set()).add(slugify(p["n"]))
                if slugify(p["n"]) in live_slugs:
                    living_f.add(fold(f))
    for x in living:
        living_f.add(fold(x["n"]))
    pfold_n = {surname_fold(k): v for k, v in pfold.items()}
    who_slugs = set(dossiers)
    for d in dossiers.values():
        who_slugs.add(slugify(d["n"]))
        for a in d.get("also", []):
            who_slugs.add(slugify(a["n"]))

    own, withr = {}, {}
    for r in reg:
        own.setdefault(fold(r["n"]), []).append(r)
        if "with:" in r["w"]:
            for nm in r["w"].split("with:", 1)[1].split("·"):
                if nm.strip():
                    withr.setdefault(fold(nm), []).append(r)

    held = {"unknown": 0, "living": 0, "namesake": 0, "rule": 0, "many": 0, "slug": 0}
    out_names, seen = [], set()
    for e in names:
        f = fold(e["name"])
        rows, named = own.get(f), False
        if not rows:
            rows, named = withr.get(f), True
        if not rows:
            held["unknown"] += 1
            continue
        if f in living_f or any(difflib.SequenceMatcher(None, surname_fold(f), l).ratio() >= NEAR for l in living_f):
            held["living"] += 1
            continue
        fs = surname_fold(f)
        if fs in pfold_n or any(difflib.SequenceMatcher(None, fs, k).ratio() >= NEAR for k in pfold_n) \
                or any(len(fs.split()) >= 4 and k.split()[:3] == fs.split()[:3] for k in pfold_n):
            held["namesake"] += 1
            continue
        if not all(row_ok(r, named) for r in rows):
            held["rule"] += 1
            continue
        if len(rows) > MAX_ROWS:
            held["many"] += 1
            continue
        sl = slugify(rows[0]["n"] if not named else e["name"])
        if sl in who_slugs or sl in seen:
            held["slug"] += 1
            continue
        seen.add(sl)
        nm = re.sub(r"\s+", " ", (rows[0]["n"] if not named else e["name"]).replace("*", "")).strip()
        out_names.append({
            "slug": sl, "name": nm, "role": "named" if named else "indexed", "basis": e["basis"],
            "rows": [{"what": row_event(r) or "—", "source": r["s"], "url": r["u"]} for r in rows],
            "pages": [[p, titles.get(p, p)] for p in e["pages"]],
        })
    out_names.sort(key=lambda x: x["slug"])

    # aliases the data states: every register row of the name carries the same person page
    by_slug = {}
    for p in people:
        by_slug.setdefault(slugify(p["n"]), []).append(p)
    out_alias, held_alias = [], 0
    for a in aliases:
        rows = own.get(fold(a["name"]), [])
        ps = {r["p"] for r in rows}
        who = by_slug.get(a["person"], [])
        if (not rows or ps != {a["person"]} or len(who) != 1 or a["person"] in live_slugs
                or fold(a["name"]) in living_f or fold(a["name"]) == fold(who[0]["n"])):
            held_alias += 1
            continue
        out_alias.append({"person": a["person"], "name": re.sub(r"\s+", " ", rows[0]["n"]).strip(), "basis": a["basis"]})
    out_alias.sort(key=lambda x: (x["person"], x["name"]))
    return {
        "note": ("People the archive READ in a FamilySearch index row and holds in no family file, one /who/ name page each, and "
                 "the spellings the register itself states for people who have a page. Made by tools/readnames.py from "
                 "data/read-names.tsv (the reviewed list) and src/data/register.json; the rules are in that file. A page names "
                 "a NAME and its index rows; it never says that two rows are one person."),
        "names": out_names, "aliases": out_alias,
    }, held, held_alias, len(names), len(aliases)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write src/data/readnames.json (counts only).")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    res, held, held_alias, n_in, a_in = build()
    text = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    msg = ("readnames: %d name(s) listed, %d page(s) made, held out %d (no row %d, living %d, same as a person %d, "
           "the rule %d, over %d rows %d, slug taken %d); %d alias(es) listed, %d made, %d refused"
           % (n_in, len(res["names"]), sum(held.values()), held["unknown"], held["living"], held["namesake"], held["rule"],
              MAX_ROWS, held["many"], held["slug"], a_in, len(res["aliases"]), held_alias))
    if a.check:
        have = io.open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if have != text:
            print("readnames: FAIL. src/data/readnames.json is not what data/read-names.tsv and register.json give; run tools/readnames.py")
            print(msg)
            return 1
        living_bad = [n for n in res["names"] if False]
        print("readnames: ok. " + msg)
        return 0
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
