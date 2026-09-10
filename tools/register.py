#!/usr/bin/env python3
"""Build the register: every named individual this archive has found, one row
per source that names them.

Two kinds of row, and the page says which is which:
  index         a surname harvest — a shared surname is not a relationship
  reconstructed a person this archive has joined into a household from the words
                of a record, or met while reading a document line by line

Reads harvest/rows.tsv + harvest/titles.json + harvest/meta.json (pulled from the
FamilySearch search API, which refuses curl and has to run in a page) and the
archive's own people list. Writes site/src/data/register.json."""
import os, json, re, unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARVEST = os.path.join(HERE, "harvest")
DATA = os.path.join(HERE, "site", "src", "data")

def slugify(n):
    n = unicodedata.normalize("NFD", n)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = re.sub(r"[‘’“”\"']", "", n)
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", n.lower()))

people = json.load(open(os.path.join(DATA, "people.json"), encoding="utf-8"))["people"]
known = {}
for p in people:
    known[p["n"].lower()] = slugify(p["n"])
    for v in re.split(r"[·,]", p.get("v") or ""):
        v = re.sub(r"\(.*?\)", "", v).strip()
        if len(v.split()) > 1:
            known.setdefault(v.lower(), slugify(p["n"]))

SURNAMES = ["BOOYZEN", "BOOIJZEN", "BOOYSEN", "BOOIJSEN", "BOOYSE", "MOUNTJOY", "MONTJOY",
            "MOUNTJAY", "MONTJAY", "DASCHNER", "DASCHNER", "KUMM", "SLIER", "SLEER", "SCHLEHER",
            "PIETERZEN", "PIETERSEN", "KOLBE", "BARRY", "DOWNING", "NEPGEN", "LERENA"]

def group_for(name):
    up = name.upper()
    for s in SURNAMES:
        if re.search(r"\b" + s + r"\b", up):
            return s
    parts = [x for x in re.split(r"[^A-Za-zÀ-ɏ]+", name) if x]
    return parts[-1].upper() if parts else "—"

titles = json.load(open(os.path.join(HARVEST, "titles.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(HARVEST, "meta.json"), encoding="utf-8"))

rows, seen = [], set()
for line in open(os.path.join(HARVEST, "rows.tsv"), encoding="utf-8"):
    line = line.rstrip("\n")
    if not line.strip():
        continue
    p = line.split("\t")
    if len(p) < 3:
        continue
    ark, name, ti = p[0], p[1].strip(), p[2]
    ev = p[3] if len(p) > 3 else ""
    rel = p[4] if len(p) > 4 else ""
    if not name:
        continue
    coll = titles[int(ti)] if ti.isdigit() and int(ti) < len(titles) else ""
    key = (ark, name.lower())
    if key in seen:
        continue
    seen.add(key)
    says = ev
    if rel:
        says = (says + " · " if says else "") + "with: " + rel
    rows.append({"n": name, "g": group_for(name), "w": says or "—", "s": coll,
                 "k": "index", "u": "https://www.familysearch.org/ark:/61903/1:1:" + ark,
                 "p": known.get(name.lower(), "")})

for p in people:
    bd = " · ".join(x for x in [p.get("b", ""), p.get("d", "")] if x and x != "—")
    rows.append({"n": p["n"], "g": group_for(p["n"]), "w": bd or "—",
                 "s": "reconstructed by this archive", "k": "read", "u": "",
                 "p": slugify(p["n"])})

rows.sort(key=lambda r: (r["g"], r["n"].lower(), r["s"]))
groups = {}
for r in rows:
    groups[r["g"]] = groups.get(r["g"], 0) + 1

out = {"caps": meta,
       "groups": sorted(groups.items(), key=lambda kv: (-kv[1], kv[0])),
       "rows": rows}
json.dump(out, open(os.path.join(DATA, "register.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(f"{len(rows)} rows · {len(groups)} surname groups · "
      f"{sum(1 for r in rows if r['u'])} with a link · "
      f"{len(set(r['n'] for r in rows))} distinct names")
