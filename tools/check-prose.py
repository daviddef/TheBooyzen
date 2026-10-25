#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The prose gate for living people: run the kit's checkprose.py over what this archive's authors type.

    python3 ../tools/check-prose.py                  # from site/ (what `npm run check:prose` and the build run)
    python3 ../tools/check-prose.py --require-tree   # a run that could not say who is living is a FAILURE, even in CI

checkprose.py (kit/tools) fails when a hand-written page, a hand-edited data file or a note puts a year, a date or
a life-event word beside a living person's name, or when a JSON record naming a living person carries a field
beyond the standard (name, relationships, full town and country). tools/checkliving2.py guards the BUILT pages and
the generated data; this guards what somebody typed.

THE FEED. Who is living is this archive's question, answered by tools/build-checkprose-feed.py over
tools/livingflags.py (the archive's own decision, on the kit's living_rule.py). The feed holds names, so it lives in
private/ (gitignored) or at $CHECKPROSE_FEED, and is rebuilt on every run so it is never stale.

EXIT CODES. 0 passed. 1 failed. 2 NOT RUN: the archive's people could not be read, so nobody can say who is
living, and "cannot say" is not "nobody is". Everything the feed reads is in the repository, so this happens only
when node or the kit is missing. Locally that stops the build. In CI (the environment variable CI is set: GitHub
Actions sets it) the build goes on and the log says, in capitals, that this gate did not run; --require-tree turns
that into a failure there too.

WHICH FILES (see HAND_EDITED and GENERATED below). The kit reads, by default, site/src/pages, site/src/content,
notes/, docs/ and the top-level markdown; this adds the hand-EDITED data files, the components and layouts (a
sentence can be typed there), the letters in requests/, and the two hand-kept tables in data/ and harvest/. A data
file in site/src/data that is in neither list FAILS the gate, so that a new file has to be classified by someone
who knows whether a person edits it or a script writes it.
"""
import os, sys, json, argparse, subprocess, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
CHECKPROSE = os.path.join(KIT_TOOLS, "checkprose.py")
ALLOW = os.path.join(ROOT, "checkprose-allow.json")
DATA = "site/src/data"

# Data files a person edits (or a person's session appends to). Each is read by the gate.
HAND_EDITED = {
    "book.json",               # the book: part titles, intros and chapter blurbs, written by hand
    "corrections.json",        # the corrections page, written by hand
    "corrections-who-deny.json",  # the deny list tools/correctionswho.py reads; typed
    "custody.json",            # what the archive physically holds
    "dates-exempt.json",       # reasoned exemptions for tools/checkdates.py
    "dna.json",                # the DNA page
    "errands.json",            # the errands page
    "families.json",           # which family names have a page (a person edits the list; the pages are drawn from the archive's data)
    "kin.js",                  # households and children (hand-written module)
    "letters.json",            # enquiries sent and answers
    "lines-meta.json",         # the lines page: each line's status, its note and its few dated places, typed (tools/lines.py holds the status to trees.json)
    "line.json",               # the direct line
    "living-policy.json",      # the author and the held-out slugs
    "log.json",                # the research log
    "marriages.json",          # the marriages page
    "namefold-extra.json",     # hand additions to the name fold
    "namesakes.json",          # the namesakes page
    "pedigree.json",           # the pedigree chart, hand-curated and extended by tools/pedigree-siblings.mjs
    "people.js",               # every named person: the source of truth for people.json
    "places.json",             # the places page
    "provenance.json",         # which pages declare their sources
    "rec-links.json",          # the citation words of the open questions and the record each links to
    "questions.json",          # open questions
    "retired.json",            # withdrawn readings
    "searched.json",           # the searches run
    "sources.json",            # the source register (lifted off sources.astro once, edited by hand since)
    "timeline.json",           # the dated events
    "trees.json",              # the trees page
    "worklist.json",           # the worklist
}

# Data files a script writes. Their generator's own gate (checkliving2.py, checkevidence.py ...) is the guard;
# scanning them here would only meet the homonyms of a family that reuses its names, and a fix would be undone
# by the next run of the generator.
GENERATED = {
    "corrections-who.json",    # tools/correctionswho.py
    "decisions.json",          # recomputed by tools/check-decisions.py (also excluded by the kit's defaults)
    "dossiers.json",           # tools/dossiers.py
    "era-places.json",         # tools/build_era.py, from data/era-ground.tsv and data/era-towns.tsv: place strings and a region id, no names
    "era-snapshot.json",       # tools/build_era.py --snapshot, from the Record Atlas's context.json: region eras and regime labels, no names
    "gallery.json",            # tools/gallery.py, read out of the built HTML
    "lines.json",              # tools/lines.py, from lines-meta.json, dossiers.json, living.json, trees.json and register.json
    "living.json",             # tools/livingflags.py (holds living names on purpose: it IS the feed's source)
    "namefold.json",           # kit namefold.py
    "people.json",             # tools/people-json.mjs, from people.js
    "readnames.json",          # tools/readnames.py, from data/read-names.tsv and register.json
    "records.json",            # tools/build_records.py, from the pages and the data
    "register.json",           # tools/register.py
    "sources-state.json",      # tools/checkexternal.py, link status
}

# Prose typed outside src/pages and notes/*.md: components and layouts, the letters the archive writes to record
# offices, and the hand-kept tables.
EXTRA_INCLUDE = ["site/src/components/**/*.astro", "site/src/layouts/**/*.astro", "requests/**/*.md",
                 "data/*.tsv", "harvest/*.tsv"]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tracked_data_files():
    r = subprocess.run(["git", "-C", ROOT, "ls-files", "-z", DATA], capture_output=True, text=True)
    return sorted(os.path.basename(f) for f in r.stdout.split("\0") if f)


def classify():
    """Return (include list, problems)."""
    names = tracked_data_files()
    problems = []
    for n in names:
        if n not in HAND_EDITED and n not in GENERATED:
            problems.append("%s/%s is in neither HAND_EDITED nor GENERATED in tools/check-prose.py: say whether "
                            "a person edits it or a script writes it" % (DATA, n))
    for n in sorted((HAND_EDITED | GENERATED) - set(names)):
        problems.append("tools/check-prose.py lists %s/%s, which is not a tracked file" % (DATA, n))
    for n in sorted(HAND_EDITED & GENERATED):
        problems.append("%s is listed as both hand-edited and generated" % n)
    return ["%s/%s" % (DATA, n) for n in sorted(HAND_EDITED)], problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--require-tree", action="store_true",
                    help="a run that could not say who is living fails even in CI")
    ap.add_argument("--feed", help="where to write the feed (default: $CHECKPROSE_FEED or private/checkprose-feed.json)")
    a = ap.parse_args(argv)

    if not os.path.exists(CHECKPROSE):
        print("checkprose: FAIL, the kit has no checkprose.py at %s (pin the kit at 26a4cba or later)" % CHECKPROSE)
        return 1
    include, problems = classify()
    if problems:
        print("checkprose: FAIL (%d)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1

    fb = load_module(os.path.join(HERE, "build-checkprose-feed.py"), "build_checkprose_feed")
    feed, stats = fb.build()
    if feed is None:
        in_ci = bool(os.environ.get("CI")) and not a.require_tree
        print("checkprose: NOT RUN (%s). The prose gate could not say who is living, so it checked nothing; "
              "this is NOT a pass." % stats)
        if in_ci:
            print("checkprose: NOT RUN in CI, and labelled so; it runs wherever the archive's people can be read")
            return 0
        return 2
    if not feed["living"] or not feed["deadNames"]:
        print("checkprose: FAIL, the feed has %d living and %d dead names; refusing to pass on nothing" % (
            len(feed["living"]), len(feed["deadNames"])))
        return 1

    out = fb.feed_path(a.feed)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False)
    print("checkprose: feed has %d living people (%d names) and %d dead names" % (
        len(feed["living"]), sum(len(x["names"]) for x in feed["living"]), len(feed["deadNames"])), flush=True)
    cmd = [sys.executable, CHECKPROSE, "--root", ROOT, "--feed", out]
    for inc in include + EXTRA_INCLUDE:
        cmd += ["--include", inc]
    if os.path.exists(ALLOW):
        cmd += ["--allow", ALLOW]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
