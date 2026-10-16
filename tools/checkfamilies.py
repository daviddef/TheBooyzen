#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Do the family pages say what the archive's data says, and can a reader find every one of them?

    python3 ../tools/checkfamilies.py --dist dist --data src/data            # from site/
    python3 ../tools/checkfamilies.py --dist dist --data src/data --no-selftest

WHAT IT CHECKS, on the BUILT pages, against the data, with a second implementation.
src/lib/families.js decides who is on a family page. This file decides it again, in Python, from
people.json, namefold.json and families.json, without importing or reading the JavaScript, and
fails when the two disagree. Two readers agreeing proves something only when they can disagree,
so the first thing this does on every run is plant faults in a copy of the built pages and check
that each one is caught (see selftest()).

  1. every family in families.json has a built page (its hand-built address, or /families/<slug>/),
     with a title, a canonical, no `noindex`, and an entry in sitemap.xml
  2. every one of them is in the main menu's "The families" group, and on /families/
  3. the page's people table has exactly as many rows as this file computes for that family, and
     its eyebrow says the same number
  4. no living person's row carries a digit (a year), a record or a note: a name, a "Living" mark and
     a town and country only; and the number of "Living" marks equals the number living.json holds
     among that family's members
  5. every family matches somebody (a family that matches nobody is a typo in families.json)

It reads only this archive's own build. It exits 2 (NOT RUN, not a pass) when it cannot see the
pages it was pointed at.
"""
import argparse, html, json, os, re, shutil, sys, tempfile, unicodedata

YEAR = re.compile(r"\b(1[0-9]\d\d|20\d\d)\b")


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Data:
    def __init__(self, data_dir):
        self.people = load(os.path.join(data_dir, "people.json"))["people"]
        self.fam = load(os.path.join(data_dir, "families.json"))["families"]
        fold = load(os.path.join(data_dir, "namefold.json"))["fold"]
        self.fold = {}
        for k, v in fold.items():
            a, b = norm(k), norm(v)
            if a != b:
                self.fold[a] = b
        self.living = {x["slug"]: x for x in load(os.path.join(data_dir, "living.json"))["living"]}
        self.dossiers = load(os.path.join(data_dir, "dossiers.json"))["people"]

    def canon(self, k):
        x, n = norm(k), 0
        while x in self.fold and self.fold[x] != x and n < 6:
            x, n = self.fold[x], n + 1
        return x

    def surname(self, n):
        s = re.sub(r"\s+of\s+(\d{4}|[A-Z][\w'’\- ]*)$", "", str(n), flags=re.A)
        s = re.sub(r"\s*\(.*?\)", "", s)
        s = re.sub(r"\s+born\s+\S+$", "", s, flags=re.I)
        s = re.sub(r"\s+the\s+(younger|elder)$", "", s, flags=re.I)
        s = re.sub(r"\s+(I|II|III)$", "", s)
        t = s.strip().split()
        return t[-1] if t else ""

    def born_into(self, v):
        rx = re.compile(r"(?:born|geboren|gebore|gebooren)\s+(?:(?:van|von|de|du|der|den|ten)\s+)*([A-Za-zÀ-ÿ'’\-]+)", re.I)
        return [m.group(1) for m in rx.finditer(str(v or ""))]

    def keys(self, f):
        ks = set()
        for t in f["fold"]:
            c = self.canon(t)
            ks.add(c)
            ks.update(k for k in self.fold if self.canon(k) == c)
        return ks

    def slug_of(self, p):
        for d in self.dossiers.values():
            if d["n"] == p["n"] or any(a.get("n") == p["n"] and a.get("b") == p.get("b") for a in d.get("also", [])):
                return d["slug"]
        return ""

    def members(self, f):
        ks = self.keys(f)
        out = []
        for p in self.people:
            carries = self.canon(self.surname(p["n"])) in ks or any(self.canon(b) in ks for b in self.born_into(p.get("v")))
            online = bool(f.get("line")) and p.get("l") == f["line"]
            if carries or online:
                out.append(p)
        return out


def page_path(dist, href):
    return os.path.join(dist, href.strip("/"), "index.html")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def href_of(f):
    return f.get("page") or "/families/%s/" % f["slug"]


def menu_links(index_html):
    nav = re.search(r'<nav[^>]*class="[^"]*topnav[^"]*".*?</nav>', index_html, re.S)
    if not nav:
        return None
    for m in re.finditer(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>", nav.group(0), re.S):
        if html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() == "The families":
            return set(html.unescape(a) for a in re.findall(r'href="([^"]*)"', m.group(2)))
    return set()


def check(dist, data_dir):
    """The list of failures, empty when the pages agree with the data. Raises FileNotFoundError when
    the build it was pointed at cannot be seen."""
    D = Data(data_dir)
    fails = []
    idx_path = os.path.join(dist, "index.html")
    if not os.path.exists(idx_path):
        raise FileNotFoundError("no index.html under %s" % dist)
    menu = menu_links(read(idx_path))
    if menu is None:
        raise FileNotFoundError("no main menu in %s/index.html" % dist)
    fam_index = page_path(dist, "/families/")
    if not os.path.exists(fam_index):
        fails.append("/families/ is not built")
        fam_html = ""
    else:
        fam_html = read(fam_index)
    sm_path = os.path.join(dist, "sitemap.xml")
    sitemap = read(sm_path) if os.path.exists(sm_path) else None
    if sitemap is None:
        raise FileNotFoundError("no sitemap.xml under %s" % dist)
    if "/families/" not in menu:
        fails.append("the main menu's 'The families' group does not link /families/")

    for f in D.fam:
        href = href_of(f)
        name = f["slug"]
        mem = D.members(f)
        if not mem:
            fails.append("%s: the family matches nobody in people.json (a typo in families.json?)" % name)
            continue
        if href not in menu:
            fails.append("%s: %s is not in the main menu's 'The families' group" % (name, href))
        if fam_html and ('href="%s"' % href) not in fam_html:
            fails.append("%s: /families/ does not link %s" % (name, href))
        if ("<loc>https://booyzen.defranceski.com%s</loc>" % href) not in sitemap:
            fails.append("%s: %s is not in sitemap.xml" % (name, href))
        pp = page_path(dist, href)
        if not os.path.exists(pp):
            fails.append("%s: %s is not built" % (name, href))
            continue
        h = read(pp)
        if not re.search(r"<title>[^<]+</title>", h):
            fails.append("%s: no <title>" % name)
        if ('<link rel="canonical" href="https://booyzen.defranceski.com%s">' % href) not in h:
            fails.append("%s: no canonical pointing at itself" % name)
        if re.search(r'<meta name="robots"[^>]*noindex', h):
            fails.append("%s: a family page must be indexable, and this one is noindex" % name)
        if f.get("page"):
            continue  # a hand-built page: no people table of ours to compare
        rows = re.findall(r'<tr class="ft-row"[^>]*>(.*?)</tr>', h, re.S)
        if len(rows) != len(mem):
            fails.append("%s: the page has %d people rows, the data gives %d" % (name, len(rows), len(mem)))
        eb = re.search(r'<div class="lab">\s*(\d+) (?:person|people)', h)
        if not eb or int(eb.group(1)) != len(mem):
            fails.append("%s: the eyebrow does not say %d" % (name, len(mem)))
        want_living = sum(1 for p in mem if D.slug_of(p) in D.living)
        got_living = 0
        for r in rows:
            if 'chip lore">Living<' in r:
                got_living += 1
                text = html.unescape(re.sub(r"<[^>]+>", " ", r))
                if YEAR.search(text) or re.search(r"\d", text):
                    fails.append("%s: a living person's row carries a digit: %r" % (name, re.sub(r"\s+", " ", text)[:60]))
        if got_living != want_living:
            fails.append("%s: %d 'Living' marks on the page, %d living people among its members" % (name, got_living, want_living))
    return fails


def selftest(dist, data_dir):
    """Plant a fault in a copy of the build, one at a time, and require that check() names it."""
    D = Data(data_dir)
    base = [f for f in D.fam if not f.get("page")]
    target = next(f for f in base if any(D.slug_of(p) in D.living for p in D.members(f)))  # a family with a living member
    plain = next(f for f in base if f is not target)
    tmp = tempfile.mkdtemp(prefix="checkfamilies-")
    results = []
    try:
        def fresh():
            d = os.path.join(tmp, "dist")
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(os.path.join(d, "families"))
            shutil.copy(os.path.join(dist, "index.html"), d)
            shutil.copy(os.path.join(dist, "sitemap.xml"), d)
            shutil.copytree(os.path.join(dist, "families"), os.path.join(d, "families"), dirs_exist_ok=True)
            for f in D.fam:
                if f.get("page"):
                    os.makedirs(os.path.join(d, f["page"].strip("/")), exist_ok=True)
                    shutil.copy(page_path(dist, f["page"]), page_path(d, f["page"]))
            return d

        def edit(path, fn):
            s = read(path)
            t = fn(s)
            assert t != s, "the planted fault changed nothing in %s" % path
            with open(path, "w", encoding="utf-8") as f:
                f.write(t)

        def case(label, mutate, expect):
            d = fresh()
            mutate(d)
            got = check(d, data_dir)
            hit = any(expect in x for x in got)
            results.append((label, hit, got[:1]))

        clean = check(fresh(), data_dir)
        results.append(("clean copy passes", clean == [], clean[:1]))
        case("a family page removed", lambda d: shutil.rmtree(os.path.join(d, "families", plain["slug"])), "is not built")
        case("a people row dropped",
             lambda d: edit(page_path(d, href_of(plain)), lambda s: re.sub(r'<tr class="ft-row"[^>]*>.*?</tr>', "", s, count=1, flags=re.S)),
             "people rows")
        case("the sitemap forgets a family",
             lambda d: edit(os.path.join(d, "sitemap.xml"), lambda s: s.replace("/families/%s/</loc>" % plain["slug"], "/families/gone/</loc>")),
             "not in sitemap.xml")
        case("the menu forgets a family",
             lambda d: edit(os.path.join(d, "index.html"), lambda s: s.replace('href="/families/%s/"' % plain["slug"], 'href="/families/gone/"')),
             "not in the main menu")
        case("the index forgets a family",
             lambda d: edit(page_path(d, "/families/"), lambda s: s.replace('href="/families/%s/"' % plain["slug"], 'href="/families/gone/"')),
             "does not link")
        case("a family page goes noindex",
             lambda d: edit(page_path(d, href_of(plain)), lambda s: s.replace("</head>", '<meta name="robots" content="noindex"></head>', 1)),
             "noindex")
        case("a living row gets a year",
             lambda d: edit(page_path(d, href_of(target)), lambda s: s.replace('chip lore">Living</span></div></td><td class>', 'chip lore">Living</span></div></td><td class>1799', 1)),
             "carries a digit")
        case("a living mark is lost",
             lambda d: edit(page_path(d, href_of(target)), lambda s: s.replace('chip lore">Living<', 'chip lore">Gone<', 1)),
             "'Living' marks")
        case("an eyebrow says the wrong number",
             lambda d: edit(page_path(d, href_of(plain)), lambda s: re.sub(r'(<div class="lab">\s*)\d+', r"\g<1>9999", s, count=1)),
             "eyebrow")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dist", default=os.environ.get("ARCHIVE_OUT") or "dist")
    ap.add_argument("--data", default="src/data")
    ap.add_argument("--no-selftest", action="store_true")
    a = ap.parse_args()
    try:
        if not a.no_selftest:
            res = selftest(a.dist, a.data)
            bad = [r for r in res if not r[1]]
            for label, ok, got in res:
                print("  %s  selftest  %s%s" % ("ok  " if ok else "FAIL", label, "" if ok else "  (got %r)" % (got,)))
            if bad:
                print("  FAIL  families  the gate cannot catch %d planted fault(s); it proves nothing" % len(bad))
                return 1
        fails = check(a.dist, a.data)
    except (FileNotFoundError, StopIteration) as e:
        print("  --    families  NOT RUN, and not a pass: %s" % e)
        return 2
    if fails:
        for x in fails:
            print("  FAIL  families  " + x)
        return 1
    D = Data(a.data)
    n = sum(1 for f in D.fam if not f.get("page"))
    print("  ok    families  %d family pages agree with people.json (second implementation), each built, "
          "in the menu, on /families/ and in the sitemap; %d hand-built pages present; %d planted faults caught"
          % (n, len(D.fam) - n, 0 if a.no_selftest else len(res) - 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
