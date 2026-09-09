#!/usr/bin/env python3
"""One flat search index over the whole archive: people, places, pages and every
section heading with the paragraph under it. Run after `npm run build`."""
import json, os, re, glob, html, unicodedata

DIST, DATA = "site/dist", "site/src/data"
def clean(t):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

rows = []
d = json.load(open(os.path.join(DATA, "dossiers.json"), encoding="utf-8"))
for p in d["people"].values():
    rows.append({"k": "Person", "t": p["n"], "s": f'{p["b"]} – {p["d"]} · {p["l"]}',
                 "x": p["r"], "h": f'/who/{p["slug"]}/'})
pl = json.load(open(os.path.join(DATA, "places.json"), encoding="utf-8"))
for p in pl["places"]:
    rows.append({"k": "Place", "t": p["n"], "s": f'{p["k"]} · {p["r"]}',
                 "x": p["w"], "h": f'/places/{p["slug"]}/'})

SKIP = ("/who/", "/places/", "/search/")
for f in sorted(glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)):
    route = f[len(DIST):-len("index.html")] or "/"
    if any(route.startswith(s) for s in SKIP): continue
    raw = open(f, encoding="utf-8").read()
    title = clean((re.search(r"<title>(.*?)</title>", raw, re.S) or [None, ""])[1]).replace(" — The Booyzen Archive", "")
    body = re.sub(r"<(nav|footer)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    dek = clean((re.search(r'<p class="dek"[^>]*>(.*?)</p>', body, re.S) or [None, ""])[1])
    rows.append({"k": "Page", "t": title, "s": route, "x": dek[:300], "h": route})
    # split the body at every <h2> so each heading takes the text that follows it,
    # however long the section is
    chunks = re.split(r"<h2[^>]*>", body, flags=re.I)[1:]
    for ch in chunks:
        parts = re.split(r"</h2>", ch, maxsplit=1, flags=re.I)
        if len(parts) != 2: continue
        head, tail = clean(parts[0]), clean(parts[1])
        if len(head) < 4 or len(head) > 160: continue
        rows.append({"k": "Section", "t": head, "s": title, "x": tail[:340], "h": route})
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", body, re.S | re.I):
        head = clean(m.group(1))
        if 6 <= len(head) <= 140:
            rows.append({"k": "Section", "t": head, "s": title, "x": "", "h": route})

seen, out = set(), []
for r in rows:
    key = (r["k"], r["t"], r["h"])
    if key in seen: continue
    seen.add(key); out.append(r)
json.dump(out, open("site/public/searchindex.json", "w"), ensure_ascii=False)
from collections import Counter
print(f"{len(out)} rows ·", dict(Counter(r["k"] for r in out)))
