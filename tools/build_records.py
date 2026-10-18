#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The records table: every record a narrative passage can link to, made from the archive's own data.

    python3 tools/build_records.py            writes site/src/data/records.json
    python3 tools/build_records.py --check    exits 1 if the committed file is not what the data gives (no build needed)

WHY (18 October 2026, L3 of the linking standard). A sentence that quotes a record ("the 1915 death notice", "KAB MOOC
6/9/35: 7698", "film 007844936") was plain text, and the scan sat a page away. site/src/components/Rec.astro (a wrapper
round the kit's Rec) turns the words the author already wrote into the link to the record, from this table. Nothing is
reworded and nothing is guessed: a row exists only where this archive holds the address.

ROWS (id, url, label, kind). Every address is the archive's own page or anchor, or a FamilySearch address stated in the data:
  plate-<stem>   /documents/#plate-<stem>   the figure of a plate (the published scan with its reading); ids are on the figures
  scan-<stem>    /docs/<file>               the same scan, full size: what a caption's own citation links to
  src-<id>       /sources/#<id>             an entry of src/data/sources.json (a document read here, a located reference...)
  ark-<id>       FamilySearch record page   a FamilySearch id the pages write out (1:1:XXXX-XXXX, 3:1:...) AND the data holds:
                                            harvest/rows.tsv (the index rows), sources.json `fs`, or a searched.json address
  film-<n>       the image ark of searched.json   a film number for which searched.json holds exactly one image address

NOT HERE, ON PURPOSE. No row is made for a person who is, or may be, living: the table holds documents, and no plate of
this archive names a living person (checked on the captions by tools/check_rec.py). FamilySearch, NAA and the like are
link-only: the table carries their address as a link and never a `plate`/`show` field, so Rec never draws a scan from it.
David has not ruled on MyHeritage terms, so no row carries `show` either: no scan is placed beside a passage.

Reads only committed files, so CI builds the same file. Prints counts.
"""
import argparse
import html
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
PAGES = os.path.join(SITE, "src", "pages")
OUT = os.environ.get("RECORDS_OUT") or os.path.join(DATA, "records.json")
PLATE_PAGES = ["documents", "barry", "kolbe", "name"]          # pages that carry figures of /docs/ plates
TEXT_PAGES = ["documents", "open-questions", "kolbe", "barry", "rebels", "women", "name", "marriages", "disputed",
              "direct-line", "dna", "johannesburg"]
FS = re.compile(r"\b([13]:1:[A-Z0-9]{3,5}(?:-[A-Z0-9]{3,5}){1,3})\b")
FS_BASE = "https://www.familysearch.org/ark:/61903/"


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


INLINE = r"(?:strong|em|b|i|span|small|sup|sub|mark|u|a|Rec)"


def plain(t):
    """The text of a caption as a reader gets it: inline tags (a link, an emphasis, a Rec) add no space, other tags one."""
    t = re.sub(r"</?%s\b[^>]*>" % INLINE, "", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def stem_id(stem):
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def short(t, n=90):
    t = plain(t)
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.-") + "…"


def figures():
    """[(page, stem, file, label)] in page order; the first figure of a stem on a page owns the id (as the pages are written)."""
    out = []
    for page in PLATE_PAGES:
        s = io.open(os.path.join(PAGES, page + ".astro"), encoding="utf-8").read()
        seen = set()
        for m in re.finditer(r'<figure\b([^>]*)>(.*?)</figure>', s, re.S):
            im = re.search(r'/docs/([^"\']+?\.(?:jpg|jpeg|png|webp))', m.group(2))
            if not im:
                continue
            f = im.group(1)
            sid = stem_id(os.path.splitext(f)[0])
            if sid in seen:
                continue
            seen.add(sid)
            idm = re.search(r'\bid="([^"]+)"', m.group(1))
            if not idm or idm.group(1) != "plate-" + sid:
                raise SystemExit("build_records: the figure of %s on /%s/ has no id=\"plate-%s\"" % (f, page, sid))
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", m.group(2), re.S)
            alt = re.search(r'alt="([^"]*)"', m.group(2))
            out.append((page, sid, f, short(cap.group(1)) if cap else short(alt.group(1)) if alt else sid))
    return out


def build():
    rows = []
    fig = figures()
    first_page = {}
    for page, sid, f, label in fig:
        first_page.setdefault(sid, page)
    done = set()
    for page, sid, f, label in fig:
        if sid in done:
            continue
        done.add(sid)
        home = first_page[sid]                                   # the first page in PLATE_PAGES order carries it (/documents/)
        rows.append({"id": "plate-" + sid, "url": "/%s/#plate-%s" % (home, sid), "label": label, "kind": "plate"})
    done = set()
    for page, sid, f, label in fig:
        if sid in done:
            continue
        done.add(sid)
        rows.append({"id": "scan-" + sid, "url": "/docs/" + f, "label": label, "kind": "scan"})
    src = read_json(os.path.join(DATA, "sources.json"))
    for e in src["entries"]:
        rows.append({"id": "src-" + e["id"], "url": "/sources/#" + e["id"], "label": e["title"], "kind": "source"})

    # FamilySearch ids the pages write out, when the data holds them
    held = set(f["ref"] for f in src.get("fs", []))
    searched = read_json(os.path.join(DATA, "searched.json"))["searched"]
    film = {}
    for x in searched:
        for m in FS.finditer(x.get("url", "")):
            held.add(m.group(1))
        if x.get("film") and "/ark:/" in x.get("url", ""):
            film.setdefault(x["film"], set()).add(x["url"])
    ids = set()
    with io.open(os.path.join(ROOT, "harvest", "rows.tsv"), encoding="utf-8") as fh:
        for ln in fh:
            c = ln.split("\t")
            if c and c[0].strip():
                ids.add(c[0].strip())
    texts = [io.open(os.path.join(PAGES, p + ".astro"), encoding="utf-8").read() for p in TEXT_PAGES]
    texts.append(io.open(os.path.join(DATA, "questions.json"), encoding="utf-8").read())
    used = set()
    for t in texts:
        used.update(FS.findall(t))
    for a in sorted(used):
        if (a.startswith("1:1:") and a[4:] in ids) or a in held:
            rows.append({"id": "ark-" + a, "url": FS_BASE + a, "label": "FamilySearch " + a, "kind": "ark"})
    for n in sorted(film):
        if len(film[n]) == 1:
            rows.append({"id": "film-" + n, "url": sorted(film[n])[0], "label": "FamilySearch, film " + n, "kind": "film"})
    return {"records": rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write src/data/records.json (counts only).")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    res = build()
    text = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    kinds = {}
    for r in res["records"]:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    msg = "build_records: %d rows (%s)" % (len(res["records"]), ", ".join("%s %d" % kv for kv in sorted(kinds.items())))
    if a.check:
        have = io.open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if have != text:
            print("build_records: FAIL. src/data/records.json is not what the pages and data give; run tools/build_records.py")
            print(msg)
            return 1
        print(msg + " · ok")
        return 0
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
