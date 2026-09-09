#!/usr/bin/env python3
"""Check every internal link resolves to a built page, every local img exists,
and every built page is reachable from another page."""
import os, re, sys, collections

DIST = "site/dist"
BASE = "/TheBooyzen"

pages, assets = set(), set()
for r, _, fs in os.walk(DIST):
    for f in fs:
        rel = os.path.relpath(os.path.join(r, f), DIST)
        if f == "index.html":
            d = os.path.dirname(rel)
            pages.add("/" + (d + "/" if d else ""))
        else:
            assets.add("/" + rel.replace(os.sep, "/"))

HREF = re.compile(r'(?:href|src)="([^"]+)"')
bad_links, bad_assets = [], []
linked_from = collections.defaultdict(set)

for r, _, fs in os.walk(DIST):
    for f in fs:
        if f != "index.html": continue
        rel = os.path.relpath(os.path.join(r, f), DIST)
        d = os.path.dirname(rel)
        here = "/" + (d + "/" if d else "")
        html = open(os.path.join(r, f), encoding="utf-8").read()
        ids = set(re.findall(r'id="([^"]+)"', html))
        for h in HREF.findall(html):
            if h.startswith(("http://", "https://", "mailto:", "data:", "//")): continue
            if "' +" in h or "${" in h or "+ base" in h: continue   # JS template, not a link
            if h.startswith("#"):
                if h[1:] and h[1:] not in ids: bad_links.append((here, h, "no such id"))
                continue
            if not h.startswith(BASE):
                bad_links.append((here, h, "not base-prefixed")); continue
            t = h[len(BASE):].split("?")[0]
            t, _, frag = t.partition("#")
            if t in pages:
                linked_from[t].add(here)
            elif t in assets:
                pass
            elif t + "/" in pages:
                linked_from[t + "/"].add(here)
                bad_links.append((here, h, "missing trailing slash"))
            else:
                (bad_assets if "." in os.path.basename(t) else bad_links).append((here, h, "missing"))

orphans = sorted(p for p in pages if p != "/" and not (linked_from[p] - {p}))

print(f"{len(pages)} pages · {len(assets)} assets")
for label, rows in (("BROKEN LINKS", bad_links), ("MISSING FILES", bad_assets)):
    print(f"\n{label}: {len(rows)}")
    for a, b, why in rows[:40]: print(f"  {a}  ->  {b}   ({why})")
print(f"\nORPHAN PAGES (nothing links to them): {len(orphans)}")
for o in orphans: print("  " + o)
sys.exit(1 if bad_links or bad_assets or orphans else 0)
