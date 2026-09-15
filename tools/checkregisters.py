#!/usr/bin/env python3
"""Six checks on the registers this site is mostly made of.

The atlas check was written on 15 September to catch one old mistake and caught
eighteen live ones on its first run. These are the same idea pointed at the
other registers, and they exist for the same reason every convention that has
held in this project held: a build refused when it slipped.

  1  doc-with-no-link    a person marked `doc` whose record links nowhere.
                         Documented is a claim. A claim with no visible
                         evidence is the Marico atlas line again, in the
                         register this site is mostly made of.

  2  correction-anchor   a corrections row whose href does not resolve to a
                         real page or anchor. A withdrawal nobody can read is
                         worse than not having published it.

  3  blocked-no-remedy   a searched.json row marked `blocked` whose note never
                         says what would unblock it. A block with no named
                         remedy is indistinguishable from an excuse, and the
                         difference between "searched" and "could not search"
                         is the distinction this archive keeps relearning.

  4  kin-vs-people       a name in kin.js that does not resolve in people.js.
                         On 15 September kin was right and people was wrong -
                         kin had Hermanus Pietersen and his son as two
                         households while people had them merged into one man
                         with a long name, and nothing compared them.

  5  stale-open          a work-list row open more than thirty days. The page
                         marks these; nothing reported them, so a thing blocked
                         in October would still be sitting there in December
                         looking like a thing raised this morning.

  6  kit-behind          the archive-kit pin, against the kit's own head. This
                         archive sat four commits behind and noticed only
                         because a component it needed was missing. An archive
                         silently behind on the shared kit is a convention
                         drifting with nobody watching.
"""
import os, re, sys, json, glob, argparse, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")


def load(name):
    return json.load(open(os.path.join(D, name), encoding="utf-8"))


def anchors(dist):
    """every page path, and every id on it"""
    pages, ids = set(), set()
    for f in glob.glob(os.path.join(dist, "**", "index.html"), recursive=True):
        rel = os.path.relpath(os.path.dirname(f), dist).replace(os.sep, "/")
        p = "/" if rel == "." else "/" + rel + "/"
        pages.add(p)
        for m in re.finditer(r'id="([A-Za-z0-9_-]+)"', open(f, encoding="utf-8", errors="ignore").read()):
            ids.add(p + "#" + m.group(1))
    return pages, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=os.path.join(ROOT, "site", "dist"))
    ap.add_argument("--warn-only", action="store_true")
    a = ap.parse_args()
    bad, warn = [], []

    people = load("people.json")["people"]
    pages, ids = anchors(a.dist)

    # 1 - a documented person with nowhere to look
    for p in people:
        if p.get("s") == "doc" and not (p.get("p") or []):
            bad.append(f"doc-with-no-link   {p['n']}: marked documented and links nowhere")

    # 2 - corrections that point at nothing
    base = "/TheBooyzen"
    for row in load("corrections.json")["rows"]:
        href = (row[4] or "").strip() if len(row) > 4 else ""
        if not href:
            bad.append(f"correction-anchor  {row[0]} {row[1][:44]}: no link at all")
            continue
        if not href.startswith("/"):
            continue
        page = href.split("#")[0]
        if page not in pages:
            bad.append(f"correction-anchor  {row[0]}: {href} - no such page")
        elif "#" in href and href not in ids:
            bad.append(f"correction-anchor  {row[0]}: {href} - page exists, anchor does not")

    # 3 - a block with no named way out
    OUT = re.compile(r"reading room|in person|depot|errand|sign|log ?in|subscription|letter|writ|"
                     r"telephone|order|film|register|archives|kew|roeland|pretoria|bloemfontein|"
                     r"would unblock|what is left|different route|another route|until", re.I)
    for s in load("searched.json")["sets"]:
        for r in s["rows"]:
            if len(r) > 3 and r[3] == "blocked" and not OUT.search(r[2] or ""):
                warn.append(f"blocked-no-remedy  {s['d']} {r[0][:48]}: nothing says what would unblock it")

    # 4 - kin against people
    src = open(os.path.join(D, "kin.js"), encoding="utf-8").read()
    known = {}
    for p in people:
        known.setdefault(p["n"], []).append(f"{p.get('b','')} {p.get('d','')}")
    # a word boundary, because kin.js also has a `warn:` field and `n:` matched it
    for raw in set(re.findall(r'(?<![A-Za-z])[hwn]:\s*"([^"]+)"', src)):
        bare, _, tok = raw.partition("|")
        if bare not in known:
            bad.append(f"kin-vs-people      kin.js names {bare!r} and people.js has no such person")
        elif tok and not any(tok in s for s in known[bare]):
            bad.append(f"kin-vs-people      kin.js says {raw!r} but no {bare} has {tok!r} in a date")

    # 7 - a letter drafted and never registered, or registered and never written
    req = os.path.join(ROOT, "requests")
    if os.path.isdir(req):
        letters = load("letters.json")["rows"]
        blob = " ".join((r.get("to", "") + " " + r.get("what", "")).lower() for r in letters)
        for f in sorted(os.listdir(req)):
            if not f.endswith(".md"):
                continue
            # the file name carries the institution; one distinctive word of it must appear
            words = [w for w in re.split(r"[-_.]", f[:-3]) if len(w) > 4]
            if words and not any(w.lower() in blob for w in words):
                warn.append(f"letter-unregistered {f}: drafted in requests/ and not in the letters register")

    # 8 - a searched set pointing at a page or anchor that does not exist
    for st in load("searched.json")["sets"]:
        href = (st.get("h") or "").strip()
        if not href.startswith("/"):
            continue
        page = href.split("#")[0]
        if page not in pages:
            bad.append(f"searched-anchor    {st.get('d')} {st.get('g','')[:38]}: {href} - no such page")
        elif "#" in href and href not in ids:
            bad.append(f"searched-anchor    {st.get('d')} {st.get('g','')[:38]}: {href} - anchor does not exist")

    # 9 - people.js and people.json, which drifted once and lost four people off the index
    src_js = open(os.path.join(D, "people.js"), encoding="utf-8").read()
    names_js = re.findall(r'\{\s*n:\s*"((?:[^"\\]|\\.)*)"', src_js)
    if len(names_js) != len(people):
        bad.append(f"people-drift       people.js has {len(names_js)} records, people.json has "
                   f"{len(people)} - the generated file is stale, rebuild")
    else:
        a, b = set(x.replace('\\"', '"') for x in names_js), set(p["n"] for p in people)
        for miss in sorted(a - b)[:5]:
            bad.append(f"people-drift       {miss!r} is in people.js and not in people.json")
        for miss in sorted(b - a)[:5]:
            bad.append(f"people-drift       {miss!r} is in people.json and not in people.js")

    # 10 - a person who says in terms that the tree is the only source, marked documented
    # A record can be documented AND carry one detail that is not. The status field
    # holds one value and cannot say so, so the person carries a `tree` field
    # naming WHICH claim is untested - and the person page prints it. Reporting
    # the phrase and stopping there was half a check: it said something was wrong
    # without saying what, five times, every build.
    SAYS_TREE = re.compile(r"not from a document this archive has read", re.I)
    for p in people:
        if p.get("s") == "doc" and SAYS_TREE.search(p.get("r", "")) and not p.get("tree"):
            bad.append(f"doc-cites-tree     {p['n']}: marked `doc` and says a claim is not from a "
                       f"document - name which claim, in a `tree` field")

    # 5 - open too long
    today = datetime.date.today()
    for r in load("worklist.json")["rows"]:
        if r.get("state") in ("running", "next", "blocked") and r.get("since"):
            try:
                age = (today - datetime.date.fromisoformat(r["since"])).days
            except ValueError:
                continue
            if age > 30:
                warn.append(f"stale-open         row {r['n']} {r['state']} for {age} days - "
                            f"still true, or should it be struck? {r['what'][:44]}")

    # 6 - the shared kit
    try:
        pin = json.load(open(os.path.join(ROOT, "site", "package.json"), encoding="utf-8")
                        )["dependencies"]["@daviddef/archive-kit"].split("#")[-1]
        head = subprocess.run(["git", "ls-remote", "https://github.com/daviddef/TheArchiveKit", "HEAD"],
                              capture_output=True, text=True, timeout=25).stdout.split()[0]
        # the pin is often abbreviated, so compare on the shorter of the two
        if head and not head.startswith(pin) and not pin.startswith(head):
            warn.append(f"kit-behind         pinned {pin[:9]}, kit head is {head[:9]} - "
                        f"check what changed before bumping, then bump")
    except Exception:
        pass  # offline is not a failure

    for w in warn:
        print("  warn  registers  " + w)
    for b in bad:
        print("  FAIL  registers  " + b)
    print(f"  {'FAIL' if bad else 'ok  '}  registers  {len(people)} people, {len(pages)} pages, "
          f"{len(bad)} failing, {len(warn)} advisory")
    return 1 if bad and not a.warn_only else 0


if __name__ == "__main__":
    sys.exit(main())
