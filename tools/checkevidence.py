#!/usr/bin/env python3
"""Refuse the build when evidence keyed to a person does not reach that person.

WHY THIS EXISTS. The Mazza archive kept evidence in two files keyed to a person
and the script that built per-person data read neither, so twelve people whose
records had been read several times over had pages saying "No record has been
read for this person... it is unverified". The data was fine. The build dropped
it, and nothing refused.

THIS ARCHIVE FAILS DIFFERENTLY, because it routes rather than embeds. Evidence
is keyed to a person by SLUG - 778 register rows carry one - and the person page
does not list those rows: it links to the register with the person's NAME as a
query. So there are two ways for the evidence to stop reaching the person, and
neither would show up as a missing file:

  · the page is not built at all, or carries no link to its records;
  · the link is built from a name that does not match the rows keyed to that
    slug, so the reader arrives at 7,620 rows and none of them theirs.

The second is the one worth a gate. A file that nothing reads is easy to find.
A pointer that resolves to nothing looks exactly like a pointer that works.

  python3 tools/checkevidence.py [--dist site/dist] [--data site/src/data]

Exits 1 when a documented person's page cannot reach their own evidence.
"""
import argparse, io, json, os, re, sys, html, unicodedata

# Every file here attaches evidence to a person, and HOW it names them. The
# distinction matters and getting it wrong is how a gate cries wolf: a first
# draft of this read `p` out of all four and reported 123 failures, including
# «Cape Colony» - because marriages.json's `p` is the PLACE a marriage happened
# and not a person at all, and because places.json and timeline.json key their
# people by NAME while the register keys by SLUG.
#
#   slug   the value is a person's slug and must resolve to a dossier
#   name   the value is a person's name; names that match nobody are people the
#          archive mentions without holding a page for, which is not a fault
KEYED = [("register.json", "rows", "p", "slug"),
         ("timeline.json", "events", "p", "name"),
         ("places.json", "places", "p", "name")]
# marriages.json is deliberately absent FROM THIS LIST: its `p` is where the
# wedding was, not who was married. It is checked separately, below, because it
# keys to people by `h` and `w` and needs its own rule.


def dslug(s):
    """The same slug the person pages are built under."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("\u00ff", "y").replace("\u0178", "Y")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60]


def flat(body):
    """The rendered page as reading text: no tags, no entities, one space."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


def marriages_reach_their_people(data, dist, people):
    """marriages.json is keyed to a husband and a wife BY NAME AND BIRTH.

    Until 17 September the person page never opened this file. The chart drew
    the spouse - because kin.js holds the household - so the page looked
    complete, and the record of the marriage itself, the date, the town, whether
    a document or a family tree puts them there, reached nobody. Thirty-four
    people, every one of them with a spouse drawn and not one with the evidence
    shown. A missing file is easy to find; a page that shows half of what it
    holds is not, so this is the half that gets a gate.

    A reference is "Name" or "Name|token", and the token has to appear in that
    person's birth or death. That is not decoration: this archive holds a
    Petrus Jacobus Booysen born 1788 and his son born 1812, both on one page,
    and they have four marriages between them. Matching on the name alone would
    hand the son's two to the father - the merge-on-a-name error this estate
    exists to refuse.
    """
    rows = load(data, "marriages.json", "rows")
    bad, checked = [], 0
    for r in rows:
        for side in ("h", "w"):
            ref = (r.get(side) or "").strip()
            if not ref:
                continue
            name, _, tok = ref.partition("|")
            name, tok = name.strip(), tok.strip()
            hits = [p for p in people if p.get("n") == name]
            if tok:
                hits = [p for p in hits
                        if tok in (p.get("b") or "") or tok in (p.get("d") or "")]
            if len(hits) != 1:
                bad.append("%s in marriages.json resolves to %d people - the page "
                           "cannot be told which" % (ref, len(hits)))
                continue
            other = (r.get("w" if side == "h" else "h") or "").split("|")[0].strip()
            page = os.path.join(dist, "people", dslug(name), "index.html")
            if not os.path.exists(page):
                bad.append("%s is married in marriages.json and has no person page" % name)
                continue
            m = re.search(r"<main.*?</main>", io.open(page, encoding="utf-8",
                                                     errors="ignore").read(), re.S)
            txt = flat(m.group(0) if m else "")
            checked += 1
            # EVERY occurrence, not the first. A first draft took the first and
            # reported four failures that were not failures: the dossier prose
            # on Anna Catharina Sleer's page opens "Married James Montjoy 9 Mar
            # 1817", which is the same marriage written the long way round, and
            # the record block sits further down. A gate that reads the first
            # sentence and stops is reading the summary, not the evidence.
            found = [mm.start() for mm in
                     re.finditer(re.escape("Married " + other), txt)]
            if not found:
                bad.append("%s married %s (%s, %s) and their page does not say so"
                           % (name, other, r.get("d", "?"), r.get("p", "?")))
            elif r.get("d") and not any(r["d"] in txt[i:i + 240] for i in found):
                bad.append("%s's page names the marriage to %s but not its date %s"
                           % (name, other, r["d"]))
    return bad, checked


def load(data, name, listkey):
    p = os.path.join(data, name)
    if not os.path.exists(p):
        return []
    d = json.load(io.open(p, encoding="utf-8"))
    if isinstance(d, list):
        return d
    if listkey and isinstance(d.get(listkey), list):
        return d[listkey]
    for k in ("rows", "events", "places", "items"):
        if isinstance(d.get(k), list):
            return d[k]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default="site/dist")
    ap.add_argument("--data", default="site/src/data")
    a = ap.parse_args()

    if not os.path.isdir(a.dist):
        print("  checkevidence: no %s - build first" % a.dist); return 1

    dj = json.load(io.open(os.path.join(a.data, "dossiers.json"), encoding="utf-8"))["people"]
    reg = load(a.data, "register.json", "rows")

    # who is documented, and by what
    by_name = {}
    for slug, d in dj.items():
        by_name.setdefault(d.get("n", "").strip(), slug)
        for alt in (d.get("also") or []):
            if isinstance(alt, dict) and alt.get("n"):
                by_name.setdefault(alt["n"].strip(), slug)

    documented, unheld = {}, set()
    for fname, listkey, key, kind in KEYED:
        for r in load(a.data, fname, listkey):
            if not isinstance(r, dict):
                continue
            v = r.get(key)
            for who in (v if isinstance(v, list) else [v]):
                if not isinstance(who, str) or not who.strip():
                    continue
                if kind == "slug":
                    documented.setdefault(who, set()).add(fname)
                else:
                    slug = by_name.get(who.strip())
                    if slug:
                        documented.setdefault(slug, set()).add(fname)
                    else:
                        unheld.add(who.strip())

    rows_for = {}
    for r in reg:
        if r.get("p"):
            rows_for.setdefault(r["p"], []).append(r)

    def hay(r):
        return " ".join(str(r.get(k, "")) for k in ("n", "w", "s", "g")).lower()

    bad = []
    for slug, files in sorted(documented.items()):
        page = os.path.join(a.dist, "people", slug, "index.html")
        if not os.path.exists(page):
            page = os.path.join(a.dist, "who", slug, "index.html")
        if not os.path.exists(page):
            bad.append("%s is named in %s and has no page"
                       % (slug, ", ".join(sorted(files))))
            continue
        h = io.open(page, encoding="utf-8", errors="ignore").read()
        # INSIDE <main> ONLY. Every page in this archive carries a link to
        # /corrections/ in its navigation, so a first draft that looked for the
        # word anywhere in the file passed a page with its evidence stripped
        # out - the menu was answering for the content.
        m = re.search(r"<main.*?</main>", h, re.S)
        body = m.group(0) if m else h

        # the page has to offer SOMETHING: its records, a graded claim, or a
        # correction that is about this person rather than a link to the index
        q = re.search(r'/register/\?q=([^"&#]+)', body)
        carries = bool(q) or 'class="ev ' in body or "was withdrawn" in body.lower()
        if not carries:
            bad.append("%s is named in %s and its page carries neither a record "
                       "nor a correction" % (slug, ", ".join(sorted(files))))
            continue

        # and where it offers records, the offer has to resolve to THEIRS
        mine = rows_for.get(slug) or []
        if q and mine:
            from urllib.parse import unquote
            terms = [t for t in unquote(q.group(1).replace("+", " ")).lower().split() if t]
            if terms and not any(all(t in hay(r) for t in terms) for r in mine):
                bad.append("%s has %d record(s) in the register and its page's link "
                           "finds none of them" % (slug, len(mine)))

    people = load(a.data, "people.json", "people")
    mbad, mchecked = marriages_reach_their_people(a.data, a.dist, people)
    bad += mbad

    print("  %d people are named in an evidence file; %d carry records in the register"
          % (len(documented), len(rows_for)))
    print("  %d marriage side(s) resolve to a person, and their page carries the record"
          % mchecked)
    if unheld:
        print("  %d name(s) in those files match no person this archive holds \u2014 mentioned, "
              "not documented, which is not a fault" % len(unheld))
    if bad:
        for b in bad[:20]:
            print("  FAIL  %s" % b)
        if len(bad) > 20:
            print("        … and %d more" % (len(bad) - 20))
        print("\n  FAIL  %d person(s) cannot reach evidence that is keyed to them" % len(bad))
        return 1
    print("  ok    every one of them reaches their own evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
