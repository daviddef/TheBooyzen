#!/usr/bin/env python3
"""Every document image on the site, with the caption it already carries and the
page it sits on. Read out of the built HTML so the gallery can never drift from
the pages — if a caption is corrected, the gallery corrects with it."""
import json, os, re, glob, html

# ARCHIVE_OUT lets a session build somewhere of its own, because more than one
# session can build this repo at once and astro empties its outDir on the way in.
# Default stays site/dist - the deploy workflow uploads that exact path.
DIST = os.path.join("site", os.environ.get("ARCHIVE_OUT") or "dist")
def clean(t):
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

items, seen = [], set()
for f in sorted(glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)):
    route = f[len(DIST):-len("index.html")] or "/"
    if route.startswith(("/who/", "/places/", "/gallery/")): continue
    raw = open(f, encoding="utf-8").read()
    title = clean((re.search(r"<title>(.*?)</title>", raw, re.S) or [None, ""])[1]).replace(" — The Booyzen Archive", "")
    for m in re.finditer(r"<figure[^>]*>(.*?)</figure>", raw, re.S | re.I):
        blk = m.group(1)
        src = (re.search(r'<img[^>]+src="([^"]+)"', blk) or [None, ""])[1]
        if "/docs/" not in src: continue
        alt = (re.search(r'<img[^>]+alt="([^"]*)"', blk) or [None, ""])[1]
        cap = clean((re.search(r"<figcaption[^>]*>(.*?)</figcaption>", blk, re.S | re.I) or [None, ""])[1])
        key = src
        if key in seen: continue
        seen.add(key)
        items.append({"src": src, "alt": html.unescape(alt), "cap": cap,
                      "page": route, "pagetitle": title,
                      "detail": "/detail-" in src})
# any doc image the pages do not put in a figure still belongs in the gallery.
# THE BASE IS READ, NOT ASSUMED. This line hardcoded "/TheBooyzen" until
# 13 October 2026, and on the day the archive moved to booyzen.defranceski.com
# with base "/" it broke silently and in the worst direction: the built pages
# now say src="/docs/x.jpg", the hardcoded set said "/TheBooyzen/docs/x.jpg",
# nothing matched, and so every one of the 207 captioned images was ALSO added
# a second time as "missing, no caption". 207 images became 414 with 207
# uncaptioned, and because gallery.json is a COMMITTED artifact that CI consumes
# as-is - npm run build does not run this script - that would have deployed a
# gallery half full of 404s. Derived from astro.config.mjs so it follows the
# site instead of remembering where the site used to be.
_cfg = open(os.path.join("site", "astro.config.mjs"), encoding="utf-8").read()
_m = re.search(r"base:\s*['\"]([^'\"]+)['\"]", _cfg)
BASE = (_m.group(1) if _m else "/").rstrip("/")
allimgs = {(BASE + p[len(DIST):]) for p in glob.glob(os.path.join(DIST, "docs", "*"))}
missing = sorted(allimgs - seen)
for s in missing:
    items.append({"src": s, "alt": "", "cap": "", "page": "", "pagetitle": "", "detail": "/detail-" in s})
json.dump({"items": items}, open("site/src/data/gallery.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(items)} images · {sum(1 for i in items if i['detail'])} details · {len(missing)} without a caption")
