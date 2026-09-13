#!/usr/bin/env python3
"""Catch a narrative page that has fallen behind the data.

people.json drifted from people.js once and hid four people off the index.
The timeline drifted and hid eight documents. Both were found by eye, weeks
apart. This fails the build instead.

Each check compares something the data knows against something a page claims.
"""
import json, os, re, sys, unicodedata

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
from collections import Counter
dupes = sorted(n for n, c in Counter(p["n"] for p in people).items() if c > 1)
if dupes:
    warns.append("%d name(s) shared by more than one record — check each is really two "
                 "people and not one entered twice: %s" % (len(dupes), ", ".join(dupes)))

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

# 4. the pedigree chart must not contradict kin.js on a parent
ped = json.dumps(load("pedigree.json"), ensure_ascii=False)
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
