#!/usr/bin/env python3
"""THE MINI FLAGS ON THE RIBBON CARDS (27 October 2026): the kit's generator, run over this archive's ribbons, into a file of its own.

    python3 tools/ribbonflags.py                  write site/src/data/ribbon-flags.json and print what each place line drew
    python3 tools/ribbonflags.py --check          fail if the committed ribbon-flags.json is not what this would write
    python3 tools/ribbonflags.py --merged DIR     also write DIR/story.json and DIR/family-lines.json: the two ribbon files with
                                                  each card's `flags` put back, for the kit's gate checkribbonflags.py
    python3 tools/ribbonflags.py --report F       also write the kit's report (every line, what it drew and why not more) to F

WHAT DECIDES A FLAG is the kit's, not this file's: kit/tools/ribbonflags.py (imported, never copied) with this archive's era
snapshot (era-snapshot.json, the same table and rules as the 'at the time' notes), its --alias table (src/data/flag-places.json:
a card's town -> the era table's place in the same Atlas region) and its --countries table (src/data/flag-countries.json: today's
country of a place the kit's table cannot name). Both tables are typed by hand, with their evidence. The rules are
kit/docs/ribbon-flags.md.

WHY A FILE OF ITS OWN, AND NOT `flags` ON THE CARDS. The kit's generator writes `flags` into story.json and family-lines.json, but
at kit 1fa6b54 the kit's own contract gates for those two files (checkfamilystory.py S0, checkfamilyribbon.py F0) refuse a card
field they do not know, and `flags` is one. story.json is also typed by hand, and family-lines.json is rewritten by
tools/familylines.mjs. So the flags live here, keyed by ribbon, card position and the card's name (a living card: `living`, no name), and the pages put them on the
cards at build time (site/src/lib/ribbonflags.js: the story page, the family pages, /barry/ and /kolbe/). A card whose name no
longer matches gets no flags, and the gate then fails it (R7) until this is run again. build.sh runs this after
tools/familylines.mjs; `npm run build` only CHECKS it (check:ribbonflags: this --check, then the kit's checkribbonflags.py over
the --merged copies and the built pages; check:flagfit: the kit's checkflagfit.mjs, no card changes size).

Exit 0 ok, 1 (--check) the file is not what the inputs make, 2 an input cannot be read.
"""
import argparse, copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")

SNAPSHOT = os.path.join(DATA, "era-snapshot.json")
STORY = os.path.join(DATA, "story.json")
FAMILIES = os.path.join(DATA, "family-lines.json")
ALIAS = os.path.join(DATA, "flag-places.json")
COUNTRIES = os.path.join(DATA, "flag-countries.json")
OUT = os.path.join(DATA, "ribbon-flags.json")

NOTE = ("Made by tools/ribbonflags.py (the kit's ribbonflags.py) from story.json, family-lines.json, era-snapshot.json, flag-places.json "
        "and flag-countries.json; do not edit by hand. Each ribbon card's mini flags, by ribbon ('story', or a family's id), card "
        "position and the card's name; site/src/lib/ribbonflags.js puts them on the cards when the pages are built. The contract is "
        "the kit's kit/docs/ribbon-flags.md; the art and its credit are the kit's (kit/data/flags/index.json).")


def read(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def table(path):
    """A hand table, its `_` keys (the notes and the evidence) left out."""
    return {k: v for k, v in read(path).items() if not k.startswith("_")}


def text_of(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def flags_of(cards):
    """A living (or minor) card is keyed by its position and `living` only: this file names no living person."""
    return [dict({"card": i + 1}, **({"living": True} if c.get("living") or c.get("minor") else {"name": c.get("name")}), flags=c["flags"])
            for i, c in enumerate(cards) if c.get("flags")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--merged")
    ap.add_argument("--report")
    ap.add_argument("--quiet", action="store_true", help="print the summary line only")
    a = ap.parse_args(argv)
    sys.path.insert(0, KIT_TOOLS)
    try:
        import ribbonflags as kit  # the kit's generator
    except ImportError as e:
        print(f"ribbonflags: the kit's ribbonflags.py cannot be imported from {KIT_TOOLS}: {e}", file=sys.stderr)
        return 2
    try:
        snap, story, fams = read(SNAPSHOT), read(STORY), read(FAMILIES)
        alias, countries = table(ALIAS), table(COUNTRIES)
    except (OSError, ValueError) as e:
        print(f"ribbonflags: cannot read an input: {e}", file=sys.stderr)
        return 2
    carried = [f"story card {i + 1}" for i, c in enumerate(story["ribbon"]["cards"]) if "flags" in c]
    carried += [f"{f['id']} card {i + 1}" for f in fams["families"] for i, c in enumerate(f.get("cards") or []) if "flags" in c]
    if carried:
        print("ribbonflags: the flags belong in ribbon-flags.json, not on the cards of story.json or family-lines.json: "
              + ", ".join(carried), file=sys.stderr)
        return 1
    story_f, fams_f = copy.deepcopy(story), copy.deepcopy(fams)
    rep = kit.run(kit.context(snap, alias, None, countries=countries), story_f, fams_f)
    if a.quiet:
        print(f"ribbonflags: {len(rep['cards'])} flags on {len({(c['where'], c['card']) for c in rep['cards']})} cards; place lines by what "
              "they draw: " + ", ".join(f"{k} {v}" for k, v in sorted(rep["lines"].items())))
    else:
        kit.print_report(rep)
    if a.report:
        kit.dump(a.report, rep)
    doc = {"_note": NOTE, "story": flags_of(story_f["ribbon"]["cards"]),
           "families": {f["id"]: flags_of(f["cards"]) for f in fams_f["families"] if flags_of(f.get("cards") or [])}}
    want = text_of(doc)
    have = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if a.merged:
        os.makedirs(a.merged, exist_ok=True)
        for name, d in (("story.json", story_f), ("family-lines.json", fams_f)):
            with open(os.path.join(a.merged, name), "w", encoding="utf-8") as fh:
                fh.write(text_of(d))
    if a.check:
        if have != want:
            print("ribbonflags: site/src/data/ribbon-flags.json is not what the ribbons, the era snapshot, flag-places.json, "
                  "flag-countries.json and the kit make: run python3 tools/ribbonflags.py", file=sys.stderr)
            return 1
        print("  ok    ribbonflags  the committed ribbon-flags.json is exactly what the kit makes of the ribbons")
        return 0
    if have != want:
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(want)
        print(f"ribbonflags: wrote {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
