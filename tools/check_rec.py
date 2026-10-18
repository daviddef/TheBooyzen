#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate: every record link in the BUILT site goes where the records table says, and what it points at exists.

    python3 ../tools/check_rec.py --dist "${ARCHIVE_OUT:-dist}"        (from site/)
    python3 ../tools/check_rec.py --selftest

The kit's Rec draws <a class="lk-rec" href=... data-rec="<id>" data-cite>. This reads every such link on every built page and holds:

  1. the id is a row of src/data/records.json (the table tools/build_records.py makes from the pages and data);
  2. the href is that row's url (an address of this archive, or a FamilySearch address the data holds), not some other;
  3. an address of this archive resolves: the page is built, the fragment (#plate-...) is an id on it, a /docs/ file is built;
  4. the table is the one the pages and data give (build_records.py --check), and no row names a living person.

Exit 0 pass, 1 fail, 2 refused (nothing built, no table). Counts only: it never prints a name.
"""
import argparse
import html as htmllib
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
LINK = re.compile(r'<a\b([^>]*\bdata-rec="[^"]*"[^>]*)>', re.S)
ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def ids_of(html):
    return set(re.findall(r'\bid="([^"]+)"', html))


def check(dist, records_path, living_path=None):
    if not os.path.isfile(os.path.join(dist, "index.html")):
        return 2, ["no built site under %s: nothing was examined" % dist], {}
    if not os.path.isfile(records_path):
        return 2, ["the records table %s is missing" % records_path], {}
    table = {r["id"]: r for r in read_json(records_path)["records"]}
    bad, stats = [], {"pages": 0, "links": 0, "internal": 0, "external": 0}
    id_cache = {}

    def page_ids(path):
        if path not in id_cache:
            p = os.path.join(dist, path.strip("/"), "index.html")
            id_cache[path] = ids_of(io.open(p, encoding="utf-8").read()) if os.path.isfile(p) else None
        return id_cache[path]

    for dp, _ds, fs in os.walk(dist):
        if "index.html" not in fs:
            continue
        route = "/" + os.path.relpath(dp, dist).replace(os.sep, "/") + "/"
        route = "/" if route == "/./" else route
        html = io.open(os.path.join(dp, "index.html"), encoding="utf-8").read()
        found = LINK.findall(html)
        if not found:
            continue
        stats["pages"] += 1
        for attrs in found:
            a = {k: htmllib.unescape(v) for k, v in ATTR.findall(attrs)}
            rid, href = a.get("data-rec", ""), a.get("href", "")
            stats["links"] += 1
            row = table.get(rid)
            if row is None:
                bad.append(("unknown id", route))
                continue
            want = row["url"]
            if re.match(r"^https?://", want):
                stats["external"] += 1
                if href != want:
                    bad.append(("href is not the row's address", route))
                continue
            stats["internal"] += 1
            if href != want:
                bad.append(("href is not the row's address", route))
                continue
            path, _, frag = want.partition("#")
            if path.startswith("/docs/"):
                if not os.path.isfile(os.path.join(dist, path.lstrip("/"))):
                    bad.append(("a /docs/ file that is not built", route))
                continue
            ids = page_ids(path)
            if ids is None:
                bad.append(("the page is not built", route))
            elif frag and frag not in ids:
                bad.append(("the fragment is no id on the page", route))
    if living_path and os.path.isfile(living_path):
        names = [x.casefold() for x in read_json(living_path) if not x.startswith("/")]
        blob = json.dumps(list(table.values()), ensure_ascii=False).casefold()
        if any(n and n in blob for n in names):
            bad.append(("a living person's name is in the records table", "src/data/records.json"))
    return (1 if bad else 0), bad, stats


def selftest():
    """A planted fault of each kind, and a control, on a three-page fake site."""
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        dist = os.path.join(d, "dist")
        os.makedirs(os.path.join(dist, "docs"))
        for p, body in (("", '<a class="lk-rec" href="/documents/#plate-a" data-rec="plate-a" data-cite>x</a>'),
                        ("documents", '<figure id="plate-a"></figure>'), ("other", "")):
            os.makedirs(os.path.join(dist, p), exist_ok=True)
            io.open(os.path.join(dist, p, "index.html"), "w", encoding="utf-8").write("<html><body>%s</body></html>" % body)
        io.open(os.path.join(dist, "docs", "a.jpg"), "w").write("x")
        rec = os.path.join(d, "records.json")

        def run(rows, html):
            io.open(rec, "w", encoding="utf-8").write(json.dumps({"records": rows}))
            io.open(os.path.join(dist, "index.html"), "w", encoding="utf-8").write("<html><body>%s</body></html>" % html)
            return check(dist, rec)[0]
        row = {"id": "plate-a", "url": "/documents/#plate-a", "label": "a", "kind": "plate"}
        good = '<a class="lk-rec" href="/documents/#plate-a" data-rec="plate-a" data-cite>x</a>'
        cases = [
            ("control", [row], good, 0),
            ("unknown id", [row], good.replace('data-rec="plate-a"', 'data-rec="zzz"'), 1),
            ("href is not the row's", [row], good.replace("#plate-a", "#plate-b"), 1),
            ("fragment is no id", [dict(row, url="/documents/#plate-x")], good.replace("#plate-a", "#plate-x"), 1),
            ("page is not built", [dict(row, url="/nowhere/#plate-a")], good.replace("/documents/", "/nowhere/"), 1),
            ("file is not built", [dict(row, url="/docs/missing.jpg")], good.replace("/documents/#plate-a", "/docs/missing.jpg"), 1),
            ("external address", [dict(row, url="https://www.familysearch.org/ark:/61903/1:1:AAAA-BBBB")], good.replace("/documents/#plate-a", "https://www.familysearch.org/ark:/61903/1:1:AAAA-BBBB"), 0),
        ]
        for label, rows, html, want in cases:
            got = run(rows, html)
            ok = got == want
            fails += 0 if ok else 1
            print("%-26s %s" % (label, "ok" if ok else "WRONG (exit %d, wanted %d)" % (got, want)))
    print("check_rec self-test: %s" % ("ok" if not fails else "FAILED (%d)" % fails))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    dist = os.environ.get("ARCHIVE_OUT") or a.dist
    if not os.path.isabs(dist):
        dist = os.path.join(SITE, dist)
    code, bad, stats = check(dist, os.path.join(DATA, "records.json"), os.path.join(SITE, ".autolink", "living.json"))
    if code == 2:
        print("check_rec: REFUSED. " + bad[0])
        return 2
    # the table must be the one the pages and data give
    here = os.path.join(HERE, "build_records.py")
    import subprocess
    r = subprocess.run([sys.executable, here, "--check"], capture_output=True, text=True)
    if r.returncode != 0:
        bad.append(("records.json is not what build_records.py gives", "src/data/records.json"))
        code = 1
    if bad:
        kinds = {}
        for k, where in bad:
            kinds.setdefault(k, set()).add(where)
        print("check_rec: FAIL (%d)" % len(bad))
        for k, ws in sorted(kinds.items()):
            print("  - %s on %d page(s)" % (k, len(ws)))
        return 1
    print("check_rec: ok. %d record links on %d pages (%d to this archive, %d to FamilySearch); every id is in the table, every address is its row's, every target is built"
          % (stats["links"], stats["pages"], stats["internal"], stats["external"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
