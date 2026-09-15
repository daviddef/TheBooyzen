#!/usr/bin/env python3
"""Catch a narrative page that has fallen behind the data.

people.json drifted from people.js once and hid four people off the index.
The timeline drifted and hid eight documents. Both were found by eye, weeks
apart. This fails the build instead.

Each check compares something the data knows against something a page claims.
"""
import json, os, re, sys, glob, unicodedata

def norm(t):
    """Compare on letters alone: case, accents and curly quotes are not drift."""
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t.lower())

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "site", "src", "data")
PAGES = os.path.join(HERE, "site", "src", "pages")
DIST = os.path.join(HERE, "site", "dist")

def load(n):
    return json.load(open(os.path.join(DATA, n), encoding="utf-8"))

def page(n):
    return open(os.path.join(PAGES, n), encoding="utf-8").read()

def built(route):
    p = os.path.join(DIST, route, "index.html")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

fails, warns = [], []

people = load("people.json")["people"]
byname = {p["n"]: p for p in people}

# 1. every year this archive has WRITTEN A FINDING ABOUT should reach the timeline.
#    (Not every person's dates — that would demand an event per person. The test is
#    whether the timeline has fallen behind the research log, which is what happened.)
tl = load("timeline.json")
tlrows = tl["events"] if isinstance(tl, dict) and "events" in tl else (
    tl if isinstance(tl, list) else list(tl.values())[0])
tlyears = {str(e.get("y")) for e in tlrows}
log = load("log.json")["entries"]
logyears = {}
for e in log:
    if e.get("k") not in ("find", "back"):
        continue
    # a withdrawal is a finding about something LEAVING the record; the timeline
    # is not behind when it declines to carry a year the archive has just removed
    if re.match(r"\s*(withdrawn|corrected|retracted)\b", e["t"], re.I):
        continue
    # only years in the TITLE: a year mentioned in passing is not a missing event
    for y in re.findall(r"\b(1[6-9]\d\d|20[0-2]\d)\b", e["t"]):
        logyears.setdefault(y, e["t"])
missing = sorted(y for y in logyears if y not in tlyears)
if missing:
    warns.append(f"timeline is behind the log on {len(missing)} years: "
                 + ", ".join(f"{y} ({logyears[y][:34]}…)" for y in missing[:6]))

# 1b. shared names are ALLOWED — dossiers.py gathers them on one page and says so.
#     But people.js once held "Anna Catharina Johanna Olivier" twice for ONE woman:
#     a stub written from the 1908 notice and a full record written from the 1891
#     one. A machine cannot tell that from two real people of one name, so this
#     warns and a human checks the shared page reads as two lives and not one.
#     A warning that fires on every build is a warning nobody reads, so the
#     collisions that HAVE been checked are listed here with the reason, and only
#     a NEW one is reported. Adding a name below is a claim that somebody looked.
CHECKED_SHARED = {
    # name: how many records, and what separates them
    "George Mountjoy": (2, "the 1823 Cradock saddle maker and his 1889–1963 descendant"),
    "Petrus Jacobus Booysen": (3, "generations 6 (b. 1788), 5 (b. 1812) and the boy of 1839"),
    # Dropped 15 Sep 2026. The collision was this archive's own error, not two
    # people sharing a name: it was running Hermanus Pietersen (the husband,
    # m. 5 Apr 1807) and his son Willem Hermanus (bapt. 12 Mar 1809) under one
    # long name built out of two documents that spell him differently. De
    # Villiers separates them, so there is nothing left to collide.
}
from collections import Counter
counts = Counter(p["n"] for p in people)
dupes = sorted(n for n, c in counts.items() if c > 1)
fresh, moved = [], []
for n in dupes:
    if n not in CHECKED_SHARED:
        fresh.append(n)
    elif counts[n] != CHECKED_SHARED[n][0]:
        moved.append("%s (was %d records, now %d)" % (n, CHECKED_SHARED[n][0], counts[n]))
stale = sorted(n for n in CHECKED_SHARED if counts.get(n, 0) < 2)
if fresh:
    warns.append("%d NEW name(s) shared by more than one record — check each is really two "
                 "people and not one entered twice, then list it in CHECKED_SHARED with the "
                 "reason: %s" % (len(fresh), ", ".join(fresh)))
if moved:
    warns.append("%d checked name(s) changed count since somebody looked — re-check: %s"
                 % (len(moved), ", ".join(moved)))
if stale:
    warns.append("%d name(s) in CHECKED_SHARED no longer collide — drop them so the list "
                 "stays a record of real checks: %s" % (len(stale), ", ".join(stale)))

# 1c. a claim taken off a user tree is not a document, and must not read like one.
#     MyHeritage, Geni, WikiTree and the FamilySearch Family Tree are LEADS here —
#     /sources/ says so in as many words. The risk is not that a tree gets cited; it is
#     that a tree-sourced date sits in a sentence beside documented ones and quietly
#     inherits their authority. So: if a person's text names one of those trees, the same
#     text must also carry an explicit marker saying the claim is not from a document.
TREES = ("WikiTree", "MyHeritage", "Geni", "FamilySearch Family Tree")
NOT_A_DOC = ("NOT FROM A DOCUMENT", "FROM A TREE", "FROM A USER TREE",
             "not adopted", "UNPROVED", "a lead and not")
unmarked = []
for pr in people:
    txt = pr.get("r") or ""
    if any(t in txt for t in TREES) and not any(m in txt for m in NOT_A_DOC):
        unmarked.append(pr["n"])
if unmarked:
    fails.append("%d person(s) cite a user tree without saying the claim is not from a "
                 "document — add an explicit marker: %s"
                 % (len(unmarked), ", ".join(sorted(unmarked))))

# 2. the direct line's spouse column must not contradict kin.js
dl = page("direct-line.astro")
kin = open(os.path.join(DATA, "kin.js"), encoding="utf-8").read()
for m in re.finditer(r'\{ h: "([^"]+)", w: "([^"]+)"', kin):
    h, w = m.group(1).split("|")[0], m.group(2)
    if norm(h) in norm(dl) and norm(w) not in norm(dl) and byname.get(h, {}).get("g"):
        fails.append(f"direct-line: {h} is generation {byname[h]['g']} and kin.js gives a "
                     f"spouse the page does not show — {w}")

# 3. every person with a chart should be reachable from the tree page
tree = page("tree.astro") + json.dumps(load("pedigree.json"), ensure_ascii=False)
gens = [p for p in people if p.get("g")]
absent = [p["n"] for p in gens if norm(p["n"].split("“")[0].strip()[:18]) not in norm(tree)]
if absent:
    warns.append(f"tree page does not mention {len(absent)} people on the direct line: "
                 + ", ".join(absent[:6]))

# 3b. every place a timeline event names must exist in the atlas. Six farms and
#     towns were written into /documents/ and the timeline before places.json heard
#     of any of them, and the atlas is the one page a reader uses to see where this
#     family WAS. The timeline's "pl" field is an explicit list of places, so this
#     compares like with like instead of guessing at prose.
places = load("places.json")
prows = places["places"] if isinstance(places, dict) and "places" in places else places
pnames = {norm(r["n"]) for r in prows if isinstance(r, dict) and r.get("n")}
used = {q for e in tlrows for q in (e.get("pl") or [])}
absent = sorted(q for q in used if norm(q) not in pnames)
if absent:
    fails.append("%d place(s) named on the timeline are not in places.json, so the atlas "
                 "cannot show them: %s" % (len(absent), ", ".join(absent)))

# 3b2. an HTML entity that reaches the reader as literal text.
#      On 14 Sep 2026 the home page printed "&rarr;" at three readers, because the
#      three way-in cards passed their call to action as a DATA STRING — cta: "The
#      name &rarr;" — and a string prop is escaped on output. Arrows written
#      directly in markup were always fine; only the ones travelling through data
#      broke, which is why it survived review and was spotted on the live site.
#      This checks the SYMPTOM in the built pages, so it catches the fault whatever
#      the cause: a double-escaped entity is always a bug.
#      It is absolute. It has no exception for a page that means to quote an
#      entity in prose — the first page that wanted to, /searched/, spells the
#      arrow out in words instead, because a check with an exception is a check
#      that will be excepted.
ents = {}
for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
    t = open(f, encoding="utf-8").read()
    for m in re.findall(r"&amp;[a-zA-Z]{2,8};", t):
        ents.setdefault(m, set()).add(os.path.relpath(f, DIST))
if ents:
    bits = ", ".join("%s on %d page(s) (e.g. %s)" % (e, len(fs), sorted(fs)[0])
                     for e, fs in sorted(ents.items()))
    fails.append("%d HTML entity/entities reach the reader as literal text — write "
                 "them in markup, not through a data string or prop: %s"
                 % (len(ents), bits))

# 3c. every /documents/#anchor referenced anywhere in the built site must exist.
#     tools/links.py checks that a PAGE resolves and stops there — a link to a
#     section that was renamed or never written lands the reader at the top of a
#     four-hundred-section page with no idea what went wrong, and nothing warns.
import glob
docs_html = built("documents")
# any heading level can carry an id and be linked to; collecting only h2 made
# a correct link to an h3 read as dangling, which it did on 14 Sep 2026.
anchors = set(re.findall(r'<h[2-4] id="([a-z0-9-]+)"', docs_html))
if anchors:                      # only meaningful after a build has run
    dangling = {}
    for f in glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True):
        t = open(f, encoding="utf-8").read()
        for a in re.findall(r"/TheBooyzen/documents/#([a-z0-9-]+)", t):
            if a not in anchors:
                dangling.setdefault(a, set()).add(f[len(DIST):-len("index.html")])
    if dangling:
        fails.append("%d dangling /documents/ anchor(s): %s" % (len(dangling), ", ".join(
            "#%s (from %s)" % (a, sorted(v)[0]) for a, v in sorted(dangling.items())[:4])))

# 4. the pedigree chart must not contradict kin.js on a parent.
#    ONLY THE SPINE COUNTS. Since 15 Sep 2026 the pedigree also carries `sib`
#    arrays — the brothers and sisters at each step, so /bloodline/ can draw
#    aunts, uncles and cousins instead of a straight line of ancestors. A
#    SIBLING IS ALLOWED TO STAND THERE WITHOUT A SPOUSE; an ancestor is not,
#    because the chart asserts both parents at every step. Serialising the
#    whole file conflated the two and produced nine warnings about marriages
#    the chart was never claiming to draw.
def spine(node, out):
    if not isinstance(node, dict) or not node.get("n"):
        return out
    out.append(node["n"])
    for alt in node.get("alt", []):
        if alt.get("n"):
            out.append(alt["n"])
    spine(node.get("f"), out)
    spine(node.get("m"), out)
    return out

ped = " · ".join(spine(load("pedigree.json").get("root"), []))
for m in re.finditer(r'\{ h: "([^"]+)", w: "([^"]+)", via: "doc"', kin):
    h, w = m.group(1).split("|")[0], m.group(2)
    if norm(h) in norm(ped) and norm(w) not in norm(ped):
        warns.append(f"pedigree: has {h} but not the documented spouse {w}")

# 5. counts quoted in prose must match the data
for route, needle, actual in (
    ("people", r"(\d+) people, (\d+) families", (len(people), len(load("people.json")["lines"]))),
):
    h = built(route)
    m = re.search(needle, h)
    if m and (int(m.group(1).replace(",", "")), int(m.group(2))) != actual:
        fails.append(f"/{route}/ says {m.group(0)} but the data has {actual}")

print(f"{len(people)} people · {len(tlrows)} timeline events")
for w in warns: print("  WARN  " + w)
for f in fails: print("  FAIL  " + f)
print(f"\n{len(fails)} failures · {len(warns)} warnings")
sys.exit(1 if fails else 0)
