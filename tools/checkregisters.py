#!/usr/bin/env python3
"""Twelve checks on the registers this site is mostly made of.

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

  11 evidence-dropped    a person the dossier says is discussed nowhere, whose
                         name the BUILT PAGES plainly carry. This is the Mazza
                         fault: the data is fine, the build eats it, and the
                         person's page ends up asserting that nothing is known
                         about somebody documented a hundred times over.

  12 marriage-orphan     a person whose marriage marriages.json holds and whose
                         page carries no record of it. marriages.json is keyed
                         to a husband and a wife by name and the person page
                         does not read it, so the dossier is the only thing
                         that can carry it across.

  6  kit-behind          the archive-kit pin, against the kit's own head. This
                         archive sat four commits behind and noticed only
                         because a component it needed was missing. An archive
                         silently behind on the shared kit is a convention
                         drifting with nobody watching.
"""
import os, re, sys, json, glob, argparse, datetime, subprocess, html, unicodedata

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



def dslug(s):
    """The same slug dossiers.py builds, so a name can be looked up in it."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("\u00ff", "y").replace("\u0178", "Y")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60]


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
        # NB: not `a` - that is the argparse namespace, and shadowing it here
        # hid a live AttributeError from every later check until 17 Sep 2026.
        in_js = set(x.replace('\\"', '"') for x in names_js)
        in_json = set(p["n"] for p in people)
        for miss in sorted(in_js - in_json)[:5]:
            bad.append(f"people-drift       {miss!r} is in people.js and not in people.json")
        for miss in sorted(in_json - in_js)[:5]:
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

    # 11 - EVIDENCE THAT EXISTS AND NEVER REACHES THE PERSON
    #
    # 17 September 2026. The Mazza archive kept its evidence in two TSVs keyed to
    # a person and the per-person build script read neither, so twelve people
    # whose evidence had been read several times over got a page saying "No
    # record has been read for this person". The data was fine. The build
    # dropped it. Nothing refused.
    #
    # The same fault was live here, by a different route. dossiers.py dropped
    # any name that was a strict prefix of a longer person's name, so the
    # SETTLER - George Augustus Kolbe, named 155 times in the built pages -
    # scored zero mentions and his page said "not yet discussed on any page".
    # Seventeen people, including John Barry, George Mountjoy and Petrus
    # Jacobus Booysen.
    #
    # This gate is written against the SHAPE of the fault, not that one cause:
    # a person whose dossier says the site never mentions them, whose name the
    # built HTML plainly does mention. Any future gatherer that silently eats a
    # person trips it, however it eats them.
    try:
        doss = load("dossiers.json")["people"]
    except Exception:
        doss = None
    if doss:
        body = {}
        for f in glob.glob(os.path.join(a.dist, "**", "index.html"), recursive=True):
            rel = os.path.relpath(os.path.dirname(f), a.dist).replace(os.sep, "/")
            route = "/" if rel == "." else "/" + rel + "/"
            if route.startswith(("/who/", "/places/", "/people/")):
                continue          # these pages are generated FROM the dossier
            t = open(f, encoding="utf-8", errors="ignore").read()
            t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
            t = re.sub(r"<nav[^>]*>.*?</nav>", " ", t, flags=re.S | re.I)
            t = re.sub(r"<footer[^>]*>.*?</footer>", " ", t, flags=re.S | re.I)
            body[route] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
        for d in doss.values():
            # `shared` is not an excuse: two people of one name still have to be
            # mentioned somewhere, and skipping them hid George Mountjoy and
            # Petrus Jacobus Booysen from the first run of this gate.
            if d.get("mentions", 0):
                continue
            pat = re.compile(r"(?<![A-Za-z\u00C0-\u024F])" + re.escape(d["n"])
                             + r"(?![A-Za-z\u00C0-\u024F])")
            where = [r for r, t in body.items() if pat.search(t)]
            if where:
                bad.append(f"evidence-dropped   {d['n']}: the dossier says this person is not "
                           f"discussed anywhere, and the built pages name them on "
                           f"{len(where)} page(s) ({', '.join(sorted(where)[:3])}). The build is "
                           f"throwing evidence away - fix the gatherer, do not silence this")

    # 12 - PERSON-KEYED EVIDENCE THE PERSON PAGE CANNOT SHOW
    #
    # marriages.json keys a marriage to a husband and a wife by name. The person
    # page does not read it, so the only thing that can carry it to the person is
    # the dossier - which means a married person with no mentions is a person
    # whose marriage this archive holds and whose page says nothing is known.
    for r in load("marriages.json")["rows"]:
        for side in ("h", "w"):
            nm = (r.get(side) or "").split("|")[0].strip()
            if not nm or doss is None:
                continue
            sl = dslug(nm)
            d = doss.get(sl)
            if d is not None and not d.get("mentions", 0):
                bad.append(f"marriage-orphan    {nm}: marriages.json holds their marriage "
                           f"({r.get('d','?')}, {r.get('p','?')}) and their page carries no "
                           f"record of it")

    # 13 - A SECTION THAT CANNOT BE LINKED TO, AND IS NOT IN ITS OWN CONTENTS
    #
    # 20 September 2026. /documents/ builds its table of contents by matching
    # <h2 id="...">, so a heading written without an id is silently left out of
    # it AND has no anchor for anything to link to. Thirty-five of them had
    # accumulated - the 1842 will, the 1819 sworn falsehood, the oldest document
    # in the archive - every one a full write-up of a document, none of them
    # reachable and none of them listed. The page rendered perfectly. Nothing
    # refused, because nothing was looking.
    #
    # This is the same shape as check 11: the material was there, the build
    # dropped it on the way to the reader, and the absence was invisible from
    # the inside. An index is only honest if something checks it against what
    # it is supposed to index.
    for fn in sorted(glob.glob(os.path.join(ROOT, "site", "src", "pages", "*.astro"))):
        src = open(fn, encoding="utf-8").read()
        if "matchAll(/<h2 id=" not in src:
            continue  # this page does not build a contents list from its headings
        loose = re.findall(r"<h2(?![^>]*\bid=)[^>]*>([\s\S]*?)</h2>", src)
        for raw in loose:
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", raw))).strip()
            bad.append(f"heading-unlinkable {os.path.basename(fn)}: <h2> with no id, so it is "
                       f"missing from the page's own contents and nothing can link to it "
                       f"- \"{txt[:52]}\"")

    # 14 - A CAUSE THAT EXISTS IN THE ROWS AND NOWHERE ELSE
    #
    # 20 September 2026, found by an end-to-end audit rather than by a gate.
    # corrections.json carries a `causes` dictionary and /corrections/ carries its
    # own short `label` map, and a row's cause has to be in BOTH. One row had been
    # sitting since 14 September with cause "reasoning", which was in neither - so
    # the page rendered it with an undefined severity heading and an empty
    # explanation, and said nothing about it.
    #
    # It is the same shape as check 11 and check 13: the data was right, the build
    # dropped it on the way to the reader, and nothing refused. A vocabulary that
    # lives in two files will drift unless something counts them against each other.
    corr = load("corrections.json")
    declared = set(corr.get("causes") or {})
    used = set(r[3] for r in corr["rows"] if len(r) > 3)
    for c in sorted(used - declared):
        bad.append(f"cause-undeclared   corrections.json uses cause {c!r}, which is not in "
                   f"its own `causes` - the page shows no explanation for those rows")
    page = os.path.join(ROOT, "site", "src", "pages", "corrections.astro")
    if os.path.exists(page):
        src = open(page, encoding="utf-8").read()
        m = re.search(r"const label = \{(.*?)\};", src, re.S)
        if m:
            labelled = set(re.findall(r"(\w+)\s*:", m.group(1)))
            for c in sorted(used - labelled):
                bad.append(f"cause-unlabelled   cause {c!r} is used but has no entry in the "
                           f"`label` map on /corrections/ - its heading renders undefined")

    # 15 - A DATA FILE THAT NOTHING READS
    #
    # 20 September 2026, found by an end-to-end audit. A hand-written name-fold file
    # had sat in src/data for weeks and NOTHING imported it - not a page, not a
    # tool, not a script. Its 38 pairs had been merged into the live fold map, so
    # the search was correct and no reader lost anything. But a live-looking data
    # file that nothing reads is the Mazza trap with the safety catch off: the next
    # person to add a fold pair would add it there, the site would not change, and
    # nothing would say so.
    #
    # NB: this check scans tool source, so DO NOT NAME A DATA FILE IN A COMMENT
    # HERE - the first version of this check named its own example and therefore
    # always found it referenced, and passed while the fault was in front of it.
    #
    # A file may declare itself out of service with a top-level "superseded" key
    # saying what replaced it. Anything else unread is a failure.
    data_dir = os.path.join(ROOT, "site", "src", "data")
    srctext = ""
    for pat in ("site/src/**/*.astro", "site/src/**/*.js", "site/src/**/*.mjs",
                "tools/*.py", "tools/*.mjs", "build.sh", "site/package.json",
                # the shared kit's own checkers read data files too, and leaving
                # them out of this scan reported a live file as unread within an
                # hour of another session adding one.
                "site/node_modules/@daviddef/archive-kit/kit/tools/*.py"):
        for fn in glob.glob(os.path.join(ROOT, pat), recursive=True):
            try:
                srctext += open(fn, encoding="utf-8", errors="ignore").read()
            except OSError:
                pass
    for fn in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        base = os.path.basename(fn)
        if base in srctext:
            continue
        try:
            blob = json.load(open(fn, encoding="utf-8"))
        except Exception:
            blob = {}
        if isinstance(blob, dict) and blob.get("superseded"):
            continue
        bad.append(f"data-unread        site/src/data/{base} is imported by no page, tool or "
                   f"script - either wire it in, delete it, or give it a \"superseded\" key "
                   f"saying what replaced it")

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
