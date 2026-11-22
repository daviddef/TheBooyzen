#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One page per person: does every person's page list exactly the other people of their name, and does every old name address land?

    python3 ../tools/checknamesakes.py --dist "${ARCHIVE_OUT:-dist}"        # from site/; `npm run check:namesakes`
    python3 ../tools/checknamesakes.py --selftest                           # plants one fault per rule

WHAT CHANGED (23 November 2026, trial). A name used to have a page, /who/<name>/, beside the person's page, and the kit's
checknamepages.py was written for that (a name page that says "N people" must list N). Booyzen never wired that gate. The name
pages are gone: a person's page lists the other people who carry the same name (#others-of-this-name), and every old /who/<name>/
address is a static redirect. This gate checks the NEW rule, from the BUILD and from nothing the page generator used:

  sets      The sets are derived here from the h1 of every built person page (/people/<slug>/), not from namesets.js: a page's
            name is its h1, accents and case folded; "George Mountjoy of Kokstad" is a bearer of "George Mountjoy" when a page
            called plainly "George Mountjoy" exists (the rule the name pages used). The others of a page are the rest of its set.
  missing   a page's "Others of this name" list lacks a person of its name.
  extra     it lists a page that does not carry the name, or itself.
  absent    a name is shared and the page has no list, or the page has a list and nobody shares its name
            (a page that holds several men of one name on itself says so and may have no list).
  stub      an address under /who/ that is not a person page's redirect or a name READ from the records is a name page that is
            still drawn; a redirect whose target is not built, whose #fragment is not on the target, that lands on the wrong
            page, or that is in the sitemap.
  index     /who/ links to a /who/<name>/ page that is not a read name, or does not link a person page of the archive.

A living person is never named in a message (their slug can carry a year): their page is reported as "a living person's page"
(any page that says noindex). Exit 0 clean, 1 findings, 2 it could not see what it checks (no build, no person page, no stub).
"""
import argparse
import copy
import html
import os
import re
import sys
import unicodedata

SECTION = "others-of-this-name"


def fold(s):
    s = unicodedata.normalize("NFD", html.unescape(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def text_of(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def read_pages(dist):
    pages = {}
    for root, _dirs, files in os.walk(dist):
        if "index.html" in files:
            rel = os.path.relpath(root, dist).replace(os.sep, "/")
            route = "/" if rel == "." else "/" + rel + "/"
            with open(os.path.join(root, "index.html"), encoding="utf-8", errors="replace") as f:
                pages[route] = f.read()
    sm = os.path.join(dist, "sitemap.xml")
    sitemap = open(sm, encoding="utf-8").read() if os.path.exists(sm) else ""
    return pages, sitemap


def is_stub(raw):
    return 'http-equiv="refresh"' in raw[:700]


def stub_target(raw):
    m = re.search(r'http-equiv="refresh" content="0;url=([^"]+)"', raw[:900])
    return html.unescape(m.group(1)) if m else None


def h1_of(raw):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    return text_of(m.group(1)) if m else ""


def listed(raw):
    """(has the section, the person pages its list links to, in order)"""
    m = re.search(r'id="%s"' % SECTION, raw)
    if not m:
        return False, []
    tail = raw[m.end():]
    ul = re.search(r'<ul class="oth-list[^"]*"[^>]*>(.*?)</ul>', tail, re.S)
    hrefs = re.findall(r'href="(/people/[^"#?]+/)"', ul.group(1)) if ul else []
    return True, hrefs


def check(pages, sitemap):
    """(findings, counts, seen) over an in-memory build: route -> html."""
    findings = []
    persons = {}
    for route, raw in pages.items():
        if route.startswith("/people/") and route != "/people/" and "data-person-page" in raw and not is_stub(raw):
            persons[route] = {"h1": h1_of(raw), "living": bool(re.search(r'<meta name="robots" content="[^"]*noindex', raw[:6000]))}
    stubs = {r: s for r, s in pages.items() if r.startswith("/who/") and r != "/who/" and is_stub(s)}
    named = {r: s for r, s in pages.items() if r.startswith("/who/") and r != "/who/" and not is_stub(s)}
    if not persons or "/who/" not in pages:
        return None, {}, {}
    label = lambda r: "a living person's page" if persons.get(r, {}).get("living") else r

    # ---- the sets, from the built h1s
    folded = {r: fold(p["h1"]) for r, p in persons.items()}
    plain = {}
    for r, f in folded.items():
        plain.setdefault(f, []).append(r)
    group = {}
    for r, f in folded.items():
        m = re.match(r"^(.+?) of .+$", f)
        base = m.group(1) if m and m.group(1) in plain else f
        group.setdefault(base, []).append(r)
    setof = {}
    for base, members in group.items():
        for r in members:
            setof[r] = set(members) - {r}

    shared_sets = {b for b, m in group.items() if len(m) > 1}
    with_section = 0
    for r, others in sorted(setof.items()):
        has, got = listed(pages[r])
        if has:
            with_section += 1
        if others and not has:
            findings.append("absent: %s shares its name with %d other page(s) and has no #%s section" % (label(r), len(others), SECTION))
            continue
        if has and not others and "More than one person of this name" not in pages[r]:
            findings.append("absent: %s has a #%s section and nobody shares its name" % (label(r), SECTION))
        miss = sorted(others - set(got))
        extra = sorted(set(got) - others)
        if miss:
            findings.append("missing: %s does not list %d of its name: %s" % (label(r), len(miss), ", ".join(label(x) for x in miss)))
        if extra:
            findings.append("extra: %s lists %d that do not carry its name: %s" % (label(r), len(extra), ", ".join(label(x) for x in extra)))

    # ---- the old addresses
    for r, raw in sorted(stubs.items()):
        tgt = stub_target(raw)
        if not tgt:
            findings.append("stub: %s is a redirect with no target" % r)
            continue
        path, _, frag = tgt.partition("#")
        if path not in persons:
            findings.append("stub: %s lands on %s, which is not a built person page" % (r, path))
            continue
        key = fold(r[len("/who/"):-1].replace("-", " "))
        must = key in shared_sets          # a name that several pages carry lands on the section that lists the others
        if frag and frag != SECTION:
            findings.append("stub: %s lands on #%s, which is not the section" % (r, frag))
        elif must and not frag:
            findings.append("stub: %s is a name %d people carry and has no #%s fragment" % (r, len(group[key]), SECTION))
        elif frag and 'id="%s"' % SECTION not in pages[path]:
            findings.append("stub: %s lands on #%s, which is not on %s" % (r, SECTION, path))
        elif frag and not must and not setof.get(path):
            findings.append("stub: %s has a #%s fragment and the page has nobody of its name" % (r, SECTION))
        if re.search(r"<loc>[^<]*%s</loc>" % re.escape(r), sitemap):
            findings.append("stub: %s is in the sitemap" % r)
    for r, raw in sorted(named.items()):
        if r not in pages or "data-person-page" in raw:
            findings.append("stub: %s is a page, and a name that a person page carries has no page of its own" % r)
        elif fold(h1_of(raw)) in folded.values():
            findings.append("stub: %s is still a name page for a name a person page carries" % r)

    # ---- the index
    idx = pages["/who/"]
    links = set(re.findall(r'href="(/who/[^"#?]+/)"', idx))
    for h in sorted(links):
        if h not in named:
            findings.append("index: /who/ links to %s, which is not a name read from the records" % h)
    index_people = set(re.findall(r'href="(/people/[^"#?]+/)"', idx))
    gone = sorted(set(persons) - index_people)
    if gone:
        findings.append("index: /who/ does not link %d person page(s): %s" % (len(gone), ", ".join(label(x) for x in gone[:6])))
    counts = {"person pages": len(persons), "with a list": with_section, "shared names": len(shared_sets),
              "old name addresses (redirects)": len(stubs), "name pages left (read from the records)": len(named)}
    return findings, counts, setof


def selftest(pages, sitemap):
    f0, _c, setof = check(pages, sitemap)
    ok = True
    print("  control: the untouched build -> %d finding(s)%s" % (len(f0), "" if not f0 else "  <-- SHOULD BE 0"))
    if f0:
        ok = False
    shared = sorted(r for r, o in setof.items() if o)
    solo = sorted(r for r, o in setof.items() if not o)
    if not shared or not solo:
        print("  no shared name or no unshared person to plant against: refusing")
        return False
    a = shared[0]

    def fresh():
        return dict(pages)

    def planted(name, mutate, want):
        nonlocal ok
        v = fresh()
        mutate(v)
        got, _c, _s = check(v, sitemap)
        hit = any(g.startswith(want) for g in (got or []))
        print("  %-52s %s" % (name, "caught" if hit else "MISSED  <-- the gate cannot see this"))
        ok = ok and hit

    other = sorted(setof[a])[0]
    planted("a person of the name left off a list", lambda v: v.__setitem__(a, re.sub(r'<li[^>]*>(?:(?!</li>).)*?href="%s".*?</li>' % re.escape(other), "", v[a], count=1, flags=re.S)), "missing")
    def add_stranger(v):
        i = v[a].index('<ul class="oth-list')
        j = v[a].index("</ul>", i)
        v[a] = v[a][:j] + '<li><a href="%s">x</a></li>' % solo[0] + v[a][j:]
    planted("a stranger added to a list", add_stranger, "extra")
    planted("a list on a name nobody shares",
            lambda v: v.__setitem__(solo[0], v[solo[0]].replace("</main>", '<section id="%s"><ul class="oth-list"><li><a href="%s">x</a></li></ul></section></main>' % (SECTION, a), 1)), "absent")
    planted("a shared name with no section", lambda v: v.__setitem__(a, v[a].replace('id="%s"' % SECTION, 'id="nothing"')), "absent")
    stub = sorted(r for r in pages if r.startswith("/who/") and r != "/who/" and is_stub(pages[r]))[0]
    planted("a redirect to a page that was never built", lambda v: v.__setitem__(stub, v[stub].replace("/people/", "/nowhere/")), "stub")
    planted("a name page for a name a person carries",
            lambda v: v.__setitem__(stub, pages[solo[0]]), "stub")
    planted("a link on /who/ to a name page", lambda v: v.__setitem__("/who/", v["/who/"].replace("</main>", '<a href="%s">x</a></main>' % stub, 1)), "index")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dist):
        print("checknamesakes: %s is not a directory; nothing was checked" % a.dist)
        return 2
    pages, sitemap = read_pages(a.dist)
    if a.selftest:
        return 0 if selftest(pages, sitemap) else 1
    findings, counts, _setof = check(pages, sitemap)
    if findings is None:
        print("checknamesakes: no person page or no /who/ index in %s; nothing was checked" % a.dist)
        return 2
    if not [r for r in pages if r.startswith("/who/") and r != "/who/" and is_stub(pages[r])]:
        print("checknamesakes: no redirect under /who/ in %s; nothing was checked" % a.dist)
        return 2
    for f in findings:
        print("  FAIL  " + f)
    print("checknamesakes: " + ", ".join("%d %s" % (v, k) for k, v in counts.items()) + "; %d finding%s" % (len(findings), "" if len(findings) == 1 else "s"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
