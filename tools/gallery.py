#!/usr/bin/env python3
"""Every document image on the site, with the caption it already carries and the
page it sits on. Read out of the built HTML so the gallery can never drift from
the pages — if a caption is corrected, the gallery corrects with it."""
import json, os, re, glob, html

DIST = "site/dist"
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
# any doc image the pages do not put in a figure still belongs in the gallery
allimgs = {("/TheBooyzen" + p[len(DIST):]) for p in glob.glob(os.path.join(DIST, "docs", "*"))}
missing = sorted(allimgs - seen)
for s in missing:
    items.append({"src": s, "alt": "", "cap": "", "page": "", "pagetitle": "", "detail": "/detail-" in s})
json.dump({"items": items}, open("site/src/data/gallery.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(items)} images · {sum(1 for i in items if i['detail'])} details · {len(missing)} without a caption")
