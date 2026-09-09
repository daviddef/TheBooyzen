#!/usr/bin/env python3
"""Build a dossier for every named person: every mention of them anywhere on the
site, with the page it appears on and the sentence around it.

Unlike the Defranceski generator this one reads the BUILT HTML, because this
archive's evidence lives in prose rather than in JSON. Run after `npm run build`.

Identity is by NAME, not by resolved individual. Two people of one name share a
dossier and the page says so — this archive has two Petrus Jacobus Booysens, two
George Mountjoys and two Gertrudes, and silently merging them would be worse
than not generating anything."""
import json, os, re, glob, unicodedata, html, collections

DIST = "site/dist"
DATA = "site/src/data"

def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ÿ", "y").replace("Ÿ", "Y")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60]

people = json.load(open(os.path.join(DATA, "people.json"), encoding="utf-8"))["people"]

# ---- 1. page text, cleaned
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
def page_text(p):
    t = open(p, encoding="utf-8").read()
    title = (re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1]
    title = html.unescape(re.sub(r"\s+", " ", title)).replace(" — The Booyzen Archive", "").strip()
    t = TAG.sub(" ", t)
    t = re.sub(r"<nav[^>]*>.*?</nav>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<footer[^>]*>.*?</footer>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return title, re.sub(r"\s+", " ", t).strip()

pages = {}
for f in glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True):
    route = f[len(DIST):-len("index.html")] or "/"
    if route.startswith("/who/") or route.startswith("/places/"):
        continue
    title, text = page_text(f)
    pages[route] = {"title": title or route, "text": text}

# ---- 2. what to look for
ALLNAMES = set()
for _p in people:
    _n = _p["n"]
    ALLNAMES.add(_n)
    ALLNAMES.add(re.sub(r"\s*[“\"][^”\"]+[”\"]\s*", " ", _n).replace("  ", " ").strip())
    ALLNAMES.add(re.sub(r"\s*\(.*?\)\s*", " ", _n).strip())
ALLNAMES = {x for x in ALLNAMES if x}

def variants(p):
    """Forms of this person's name safe to search for.

    Two rules keep people apart. A variant is dropped if it is exactly another
    person's name, and a variant is dropped if it is a strict prefix of another
    person's name — otherwise 'Willem Hermanus Booyzen' the grandson collects
    every mention of 'Willem Hermanus Booyzen' the grandfather, and 'John Barry'
    swallows 'John Barry Booyzen'."""
    n = p["n"]
    v = {n}
    v.add(re.sub(r"[“”\"']", "", re.sub(r"\s*\(.*?\)\s*", " ", n)).strip())
    v.add(re.sub(r"\s*[“\"][^”\"]+[”\"]\s*", " ", n).replace("  ", " ").strip())
    for x in (p.get("v") or "").split("·"):
        x = re.sub(r"\(.*?\)", "", x)
        x = re.split(r"\s[—–-]\s", x)[0].strip(" ,;")   # cut trailing prose after a dash
        if len(x) < 5: continue
        if re.search(r"\b(spelling|across|five|the|and|also|written|source|index|tree|register)\b", x, re.I):
            continue
        if not re.match(r"^[A-ZÀ-Ž][\w'’ÿÀ-ž.-]*(\s+[A-Za-zÀ-ž'’ÿ.-]+){0,4}$", x): continue
        v.add(x)
    others = ALLNAMES - {n}
    keep = []
    for x in v:
        if len(x) < 6 or x.startswith("—"): continue
        # a bare surname would link every Booysen on the site to one man
        if len(x.split()) < 2: continue
        if x in others: continue
        if any(o != x and o.startswith(x + " ") for o in others): continue
        keep.append(x)
    return sorted(set(keep), key=len, reverse=True)

SENT = re.compile(r"(?<=[.!?])\s+")
def excerpt(text, i, j):
    a = max(0, i - 340); b = min(len(text), j + 400)
    seg = text[a:b]
    parts = SENT.split(seg)
    if len(parts) > 2: seg = " ".join(parts[1:-1]) or seg
    return seg.strip()

dossiers, index = {}, []
for p in people:
    name = p["n"]
    sl = slug(name)
    if sl in dossiers:            # two people, one name — merge, flag, and keep both records
        dossiers[sl]["shared"] = True
        dossiers[sl].setdefault("also", []).append(p)
        continue
    hits, seen, hitpages = [], set(), []
    for route, pg in sorted(pages.items()):
        found = []
        for v in variants(p):
            pat = r"(?<![A-Za-z\u00C0-\u024F])" + re.escape(v) + r"(?![A-Za-z\u00C0-\u024F])"
            for m in re.finditer(pat, pg["text"]):
                key = (m.start() // 220)
                if key in seen: continue
                seen.add(key)
                found.append(excerpt(pg["text"], m.start(), m.end()))
                break                      # one hit per variant per page section
        if found:
            hitpages.append({"h": route, "t": pg["title"]})
            for f in found[:4]:
                hits.append({"page": route, "title": pg["title"], "text": f})
        seen = set()
    dossiers[sl] = {**p, "slug": sl, "mentions": len(hits), "pages": hitpages,
                    "hits": hits[:26], "shared": False, "also": []}
    if hits:
        # every safe variant links to the dossier, not only the canonical name
        for v in variants(p):
            index.append([v, sl, len(hits)])

out = {
 "note": ("A dossier is every mention of a person anywhere in this archive, gathered automatically after "
          "the site is built and linked back to the page it appears on. Identity here is by NAME, not by "
          "resolved individual — where two people share a name they share this page, and the archive says "
          "so rather than guessing. Nothing on a dossier page is new evidence; it is the same evidence, "
          "brought together."),
 "people": dossiers}
json.dump(out, open(os.path.join(DATA, "dossiers.json"), "w"), ensure_ascii=False, indent=1)
# a variant claimed by two people is ambiguous — drop it rather than link it wrong
owner = {}
for nm, sl, k in index:
    owner.setdefault(nm.lower(), set()).add(sl)
index = [r for r in index if len(owner[r[0].lower()]) == 1]
seenv = set(); uniq = []
for r in index:
    if r[0].lower() in seenv: continue
    seenv.add(r[0].lower()); uniq.append(r)
index = uniq
index.sort(key=lambda r: -len(r[0]))
json.dump(index, open("site/public/whoindex.json", "w"), ensure_ascii=False)
print(f"{len(dossiers)} dossiers · {sum(v['mentions'] for v in dossiers.values())} mentions · {len(index)} auto-link names")
for b in sorted(dossiers.values(), key=lambda v: -v["mentions"])[:8]:
    print(f"  {b['mentions']:4d}  {b['n']}")
