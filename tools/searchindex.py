#!/usr/bin/env python3
"""One flat search index over the whole archive: people, places, pages and every
section heading with the paragraph under it. Run after `npm run build`."""
import json, os, re, glob, html, unicodedata
import sys

# --- the shared row contract -------------------------------------------------
# All seven archives now emit {k,t,s,h,q}: kind, title, subtitle, href, and a
# lowercased accent-folded haystack. The box that reads it is one component in
# @daviddef/archive-kit, so the schema has to be the same everywhere.
# One fold, shared with the search box and the other six archives.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools"))
import searchkit  # noqa: E402

_fold = searchkit.fold

def to_contract(rows):
    out = []
    for r in rows:
        k = r.get("k", "Page")
        t = r.get("t", "")
        s = r.get("s", r.get("d", ""))
        h = r.get("h", r.get("u", ""))
        q = r.get("q", r.get("x", ""))
        out.append(searchkit.row(k, t, s, h, q))
    return out

# THE BUILD TO READ. ARCHIVE_OUT beats the default, the way it does for every kit
# tool (kit/tools/outdir.py): an isolated build lives in site/$ARCHIVE_OUT, and this
# step used to read site/dist regardless, so a session building somewhere of its
# own derived its search index from whoever last built the shared directory. Found
# 9 October 2026 folding the letters page away: the index was unchanged by a build
# that had removed a page. The default is still dist, which CI uploads.
DIST, DATA = os.path.join("site", os.environ.get("ARCHIVE_OUT") or "dist"), "site/src/data"
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
    # A redirect page is an address that moved, not a page: it has no body to find,
    # and "Redirecting to: ..." was being offered as a search result for /log/ and
    # /changed/. It stays built so the old address keeps working.
    if 'http-equiv="refresh"' in raw[:600]: continue
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
json.dump(to_contract(out), open("site/public/searchindex.json", "w"), ensure_ascii=False)
from collections import Counter
print(f"{len(out)} rows ·", dict(Counter(r["k"] for r in out)))
