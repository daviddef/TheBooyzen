#!/usr/bin/env python3
"""Lift the source register off /sources/ and into data, without rewriting it.

/sources/ was 674 lines of hand-written Astro, the largest sources page in the
estate, and four of its sections are plainly tables of records: what was read,
what is in hand, and what is located and still unread. Those are rows. The rest
of the page is not - it argues about a book, it explains seven kinds of shut
door - and prose that is argued rather than listed stays prose.

THE EXTRACTION IS MECHANICAL ON PURPOSE. Cells are carried across as the HTML
they already were, so nothing is reworded and nothing is summarised; the only
change is that `href={u("/x/")}` becomes `href="/x/"` and the page puts the base
back on at render. That is what makes the result checkable: rebuild, strip the
tags, and the reading text of the page must be identical to what it was.

  python3 tools/extractsources.py            # writes site/src/data/sources.json
"""
import io, os, re, json, sys

SRC = "site/src/pages/sources.astro"
OUT = "site/src/data/sources.json"

# The four sections that are registers. Everything else on the page is prose
# that argues rather than lists, and is left alone.
WANT = [
    ("read",     "Original documents read by this archive"),
    ("inhand",   "Estate and archival references in hand"),
    ("transvaal", "The Transvaal, before anyone thought this family was there"),
    ("estates",  "The Transvaal estates — located, and mostly still unread"),
]


def cells(tr):
    """Every <td> in a row, as the HTML it holds. td does not nest, so this is
    a split rather than a parse."""
    out = []
    for m in re.finditer(r"<td\b([^>]*)>(.*?)</td>", tr, re.S):
        attrs, inner = m.group(1), m.group(2)
        cls = re.search(r'class="([^"]*)"', attrs)
        out.append({"h": tidy(inner), "cls": cls.group(1) if cls else ""})
    return out


def tidy(h):
    """One space everywhere, and an Astro href written as a plain path."""
    h = re.sub(r'href=\{u\("([^"]+)"\)\}', r'href="\1"', h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def heads(tbl):
    out = []
    th = re.search(r"<thead>(.*?)</thead>", tbl, re.S)
    if not th:
        return out
    for m in re.finditer(r"<th\b([^>]*)>(.*?)</th>", th.group(1), re.S):
        cls = re.search(r'class="([^"]*)"', m.group(1))
        w = re.search(r"width:([^;\"]+)", m.group(1))
        out.append({"label": tidy(m.group(2)), "cls": cls.group(1) if cls else "",
                    "w": w.group(1).strip() if w else ""})
    return out


def main():
    s = io.open(SRC, encoding="utf-8").read()

    # the FamilySearch arks are already an array; carry them over as they are
    i = s.index("const fs = [")
    j = s.index("\n];", i)
    fs = []
    for row in re.finditer(r'\["(.*?)", "(.*?)", "(.*?)"\]', s[i:j]):
        fs.append({"fact": row.group(1).replace('\\"', '"'),
                   "collection": row.group(2), "ref": row.group(3)})

    # every <section> on the page, by its heading
    secs = {}
    for m in re.finditer(r"<section class=\"blk\">(.*?)</section>", s, re.S):
        blk = m.group(1)
        h = re.search(r"<h2[^>]*>(.*?)</h2>", blk, re.S)
        if h:
            secs[tidy(h.group(1))] = blk

    out = {"fs": fs, "sections": []}
    for sid, title in WANT:
        blk = secs.get(title)
        if blk is None:
            print("  MISS  no section headed %r" % title); return 1
        dek = re.search(r'<p class="dek">(.*?)</p>', blk, re.S)
        tbl = re.search(r"<table>(.*?)</table>", blk, re.S)
        if not tbl:
            print("  MISS  %s has no table" % sid); return 1
        body = re.search(r"<tbody>(.*?)</tbody>", tbl.group(1), re.S).group(1)
        rows = [cells(t.group(1)) for t in re.finditer(r"<tr>(.*?)</tr>", body, re.S)]
        out["sections"].append({
            "id": sid, "title": title,
            "dek": tidy(dek.group(1)) if dek else "",
            "cols": heads(tbl.group(1)),
            "rows": rows,
        })
        print("  %-10s %2d row(s), %d column(s)" % (sid, len(rows),
              max(len(r) for r in rows) if rows else 0))

    json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %d FamilySearch reference(s) + %d section(s) → %s"
          % (len(fs), len(out["sections"]), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
