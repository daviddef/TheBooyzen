#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the feed the kit's prose gate (kit/tools/checkprose.py) reads: who is living, and who is dead.

    python3 tools/build-checkprose-feed.py                # writes private/checkprose-feed.json
    python3 tools/build-checkprose-feed.py --out PATH     # or $CHECKPROSE_FEED
    python3 tools/build-checkprose-feed.py --counts       # counts only, writes nothing

The feed holds living people's NAMES, so it is never committed: it is written under private/ (gitignored),
or wherever $CHECKPROSE_FEED / --out says, and the file is created readable by its owner only. This script
prints COUNTS only, never a name.

    {"living":    [{"id": "<opaque>", "names": ["Given Family", ...]}, ...],
     "deadNames": ["Given Family", ...]}

WHO IS LIVING is not decided here. It is this archive's own decision, tools/livingflags.py (imported, not
copied), which asks the kit's living_rule.py and then adds the one thing this archive reads that the rule does
not: a person recorded as b = "living" (a statement in the field a date would occupy, no year) counts as living.
This script does not change how that statement is read; it asks livingflags.classify() the same question the
generator and the build ask, so the three always agree. Whether such a statement SHOULD count as living is
David's ruling to make and is not made here. The count of people who are living only by that statement is
printed as a number.

  * LIVING: every person livingflags.classify() calls living.
  * HELD OUT (possible minors, people promised privacy by id) are also put in the feed as living: held out means
    absent, so any date or detail beside such a name in a hand-written file is as wrong as for a living one.

WHO IS DEAD is decided by IDENTITY, never by "every name that is not a living name" (a living person and an
ancestor who share a name would then cancel each other out of the corpus; the kit skips and counts a name
both have, it does not guess). The dead are the people.json rows that are neither living nor held out: their
name, the name without its disambiguating tail ("of 1782", "of Rustenburg"), the maiden name given in
brackets, and the spellings the archive records for them (field v).

Everything this reads (people.js through people.json, kin.js, living-policy.json) is in the repository, so the
feed can be built in CI as well as here. It says "not run" (exit 2) only when it cannot read them (no node, no
people.json): "cannot say who is living" is not "nobody is".
"""
import os, sys, re, io, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
DEFAULT_FEED = os.path.join(ROOT, "private", "checkprose-feed.json")
sys.path.insert(0, HERE)


def feed_path(explicit=None):
    return explicit or os.environ.get("CHECKPROSE_FEED") or DEFAULT_FEED


def _clean(n):
    return re.sub(r"\s+", " ", str(n or "").replace("/", " ")).strip()


def spellings(p, with_variants):
    """Every plain 'Given Family' string the archive records for one person row."""
    out = set()
    n = _clean(p.get("n"))
    if n:
        out.add(n)
        out.add(re.sub(r"\s+of\s+\S.*$", "", n).strip())            # "X Booijsen of 1782" -> "X Booijsen"
        m = re.search(r"^(.*?)\s*\(([A-Z][\w'’ -]+)\)\s*$", n)       # "A B Booyzen (Vermaak)" -> "A B Vermaak"
        if m:
            words = m.group(1).split()
            out.add(" ".join(words[:-1] + [m.group(2)]))
            out.add(m.group(1))
    if with_variants:
        for seg in re.split(r"\s*[·;]\s*", str(p.get("v") or "")):
            seg = seg.split(",")[0]
            seg = _clean(re.sub(r"\s*\(.*?\)", " ", seg))
            if seg and len(seg.split()) >= 2:
                out.add(seg)
    return sorted(s for s in out if len(s.split()) >= 2)


def build():
    """Return (feed, stats), or (None, reason) when who is living cannot be decided on this machine."""
    try:
        import livingflags as lf
    except Exception as e:                                           # noqa: BLE001
        return None, "tools/livingflags.py would not load (%s: is the kit installed?)" % type(e).__name__
    try:
        people = json.load(io.open(os.path.join(DATA, "people.json"), encoding="utf-8"))["people"]
        pol = json.load(io.open(os.path.join(DATA, "living-policy.json"), encoding="utf-8"))
        fams = lf.families()
    except Exception as e:                                           # noqa: BLE001
        return None, "the archive's people could not be read (%s)" % type(e).__name__
    if len(people) < 50:
        return None, "people.json has %d people; refusing to decide who is living from that" % len(people)
    living, held = lf.classify(people, fams, pol.get("heldOut", []), pol.get("author", []))
    live, hold = set(living), set(held)
    stats = {"people in people.json": len(people), "living": len(live), "held out": len(hold)}
    stats["living only by the statement 'living' (no birth year)"] = sum(
        1 for i in live if lf.said_living(people[i]) and lf.birth_year(people[i]) is None)
    stats["living by the kit rule from a birth year"] = sum(
        1 for i in live if lf.birth_year(people[i]) is not None)

    feed_living = [{"id": "person-%d" % (i + 1), "names": spellings(people[i], False)}
                   for i in sorted(live | hold)]
    feed_living = [x for x in feed_living if x["names"]]
    dead = set()
    for i, p in enumerate(people):
        if i in live or i in hold:
            continue
        dead.update(spellings(p, True))
    dead = sorted(dead)
    feed = {"living": feed_living, "deadNames": dead}
    stats["living people in the feed"] = len(feed_living)
    stats["living names"] = sum(len(x["names"]) for x in feed_living)
    stats["dead rows"] = len(people) - len(live | hold)
    stats["dead names"] = len(dead)
    sys.path.insert(0, os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools"))
    try:
        import checkprose as cp
        lp, dp = set(), set()
        for x in feed_living:
            lp |= cp.phrases(x["names"])
        for n in dead:
            dp |= cp.phrases([n])
        stats["living phrases"] = len(lp)
        stats["living phrases shared with a dead person (skipped by the gate)"] = len(lp & dp)
    except ImportError:
        pass
    return feed, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the living / dead name feed for checkprose.py (counts only are printed).")
    ap.add_argument("--out")
    ap.add_argument("--counts", action="store_true", help="print counts, write nothing")
    a = ap.parse_args(argv)
    feed, stats = build()
    if feed is None:
        print("build-checkprose-feed: not run: %s" % stats)
        return 2
    if not feed["living"] or not feed["deadNames"]:
        print("build-checkprose-feed: FAIL, %d living, %d dead names; refusing to write a feed that could pass on nothing" % (
            len(feed["living"]), len(feed["deadNames"])))
        return 1
    for k, v in stats.items():
        print("  %-62s %d" % (k, v))
    if a.counts:
        return 0
    out = feed_path(a.out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False)
    print("build-checkprose-feed: wrote %s (names inside; not for commit)" % os.path.relpath(out, ROOT)
          if os.path.abspath(out).startswith(ROOT + os.sep) else "build-checkprose-feed: wrote the feed outside the repo (names inside)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
