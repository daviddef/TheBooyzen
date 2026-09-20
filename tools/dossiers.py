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

# The generated "Every mention, page by page" section on a person page - see
# page_text. EXCERPT_P identifies it; MENTION_BLK is the whole <section> that
# carries it, headings and all.
EXCERPT_P = re.compile(r'<p style="font-size:14\.5px;line-height:1\.66;margin:0">….*?…</p>', re.S)
MENTION_BLK = re.compile(r'<section class="blk">.*?</section>', re.S)

# THE ARCHIVE'S RECORDS ABOUT ITS OWN WORK, WHICH ARE NOT EVIDENCE ABOUT A PERSON.
# A dossier and a name-fold want opposite things out of this one file. For a reader,
# somebody discussed on /changes/ genuinely is discussed there and the excerpt is
# honest. For namefold's corpus - which reads dossiers.json, and is the ONLY path
# from page prose to the fold - that is the archive writing ABOUT a name, which is
# precisely the standing its NARRATIVE deny-list exists to refuse. The deny-list
# excludes worklist.json, searched.json and corrections.json by filename, and then
# the pages built from them were scraped and the same prose walked back in.
#
# MEASURED BEFORE CUTTING: 330 of 5,864 excerpts, 5.6%, across 128 of 347 people.
# NOBODY IS ORPHANED - not one page becomes "not yet discussed on any page", which
# is the failure this tool has already caused once. Largest single loss is
# james-mountjoy, 9 of 23.
#
# /corrections/ goes with the rest, and it is the one worth arguing over. That a
# person's record was withdrawn IS something a reader should meet - but as a link
# the page carries deliberately, not as a quotation lifted out of the register by a
# scraper that cannot tell a correction from a mention. Harvesting a withdrawn
# reading as though it were a finding is what check:retired exists to catch.
#
# /disputed/ and /name/ are deliberately NOT here. They read as registers but they
# are substantive: "The Name" is the surname's own history, and "Disputed" is about
# contested facts concerning people rather than about this archive's working.
NARRATIVE = ("/changes/", "/corrections/", "/open-questions/", "/method/",
             "/letters/", "/searched/", "/worklist/", "/research-log/", "/errands/")
def page_text(p):
    t = open(p, encoding="utf-8").read()
    title = (re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1]
    title = html.unescape(re.sub(r"\s+", " ", title)).replace(" — The Booyzen Archive", "").strip()
    t = TAG.sub(" ", t)
    # CHROME IS NOT PROSE. <nav> and <footer> were stripped; the skip link, the
    # site header and the <head> were not, and all three sit outside those two
    # elements - so 344 of 5,864 excerpts, 5.9%, opened with "A.M. Kolbe of Piet
    # Retief - The Booyzen Archive Skip to the content ... Menu Start Home
    # About The trees". That is the site's own furniture, printed to a reader
    # on a person's page as though it were a quotation about their ancestor.
    # The <head> goes too, because the <title> is read out of the ORIGINAL text
    # above and its words were otherwise surviving into the body.
    t = re.sub(r"<head[^>]*>.*?</head>", " ", t, flags=re.S | re.I)
    t = re.sub(r'<a class="skiplink"[^>]*>.*?</a>', " ", t, flags=re.S | re.I)
    t = re.sub(r"<header[^>]*>.*?</header>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<nav[^>]*>.*?</nav>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<footer[^>]*>.*?</footer>", " ", t, flags=re.S | re.I)
    # THE GENERATOR MUST NOT READ ITS OWN OUTPUT — 21 SEPTEMBER 2026.
    # This tool scrapes the BUILT site, and the built site prints what this tool
    # wrote last cycle. [slug].astro renders "Every mention, page by page": one
    # <p> per stored excerpt, on every person page. Measured on the committed
    # output, 7,307 of 9,008 excerpts — 81.1% — were harvested from person
    # pages, so four fifths of the corpus was the previous cycle re-rendered.
    # The visible symptom was the counts: people.astro prints "<N> mentions"
    # and each person page heads itself "<family> · <N> mentions across <N>
    # pages", and 1,732 excerpts — 19% — quoted one of those numbers back.
    #
    # THE PROOF IT NEVER SETTLED: generate, rebuild, generate again and ALL 347
    # dossiers changed, 24,981 mentions down to 24,636. Two consecutive runs
    # were byte-identical and proved NOTHING, because both read the same dist.
    # The test that catches this is generate → rebuild → generate → diff.
    #
    # The excerpt paragraph is stripped and NOT the whole person page, because a
    # person page carries real prose — the dek, the eyebrow, the `r` field out
    # of people.js — in which other people are legitimately named. That prose
    # SHOULD be harvestable; only the regenerated section should not. The
    # signature below is exact: 8,972 matches across dist, every one of them on
    # a person page, no other template using it.
    #
    # The two count strips stay. They are largely redundant once the excerpts
    # go, but the /people/ listing is not a person page and still prints counts.
    # STRIPPED BY CLASS, NOT BY PHRASE: corrections.json says "2,428 mentions"
    # in ordinary prose and a text-level strip would eat the "2,".
    # THE WHOLE SECTION GOES, NOT ONLY ITS PARAGRAPHS. Stripping the excerpt
    # <p>s alone was not enough: each group is headed <h2> with the TITLE of a
    # page that mentions this person, and most of those pages are person pages,
    # so the headings are a list of OTHER PEOPLE'S NAMES that this tool wrote
    # last cycle. One page carried 26 of them. Removing the paragraphs and
    # leaving the headings dropped the churn but never cleared it - the run
    # oscillated, 24,636 mentions to 14,115 to 13,444 to 13,455.
    t = MENTION_BLK.sub(lambda m: " " if EXCERPT_P.search(m.group(0)) else m.group(0), t)
    t = EXCERPT_P.sub(" ", t)   # belt and braces, if one is printed outside a blk
    t = re.sub(r'<span class="cap"[^>]*>\s*[\d,]+\s+mentions?\s*</span>', " ", t, flags=re.I)
    t = re.sub(r"(?:·|&middot;|&#183;)?\s*[\d,]+\s+mentions?\s+across\s+[\d,]+\s+pages",
               " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return title, re.sub(r"\s+", " ", t).strip()

pages = {}
for f in glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True):
    route = f[len(DIST):-len("index.html")] or "/"
    if route.startswith("/who/") or route.startswith("/places/") or route in NARRATIVE:
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
    person's name; and a variant that is a strict PREFIX of another person's
    name is KEPT, but fenced, so it cannot claim the longer person's mentions.

    17 SEPTEMBER 2026 — THIS USED TO DROP THE SHORTER NAME OUTRIGHT, and that
    was the bug. 'George Augustus Kolbe' is a prefix of 'George Augustus Kolbe
    of Wakkerstroom', so the Settler — the most documented person on the site,
    named 155 times in the built pages — was given a variant list of nothing,
    scored zero mentions, and his own page said "not yet discussed on any page".
    Seventeen people were affected, including John Barry, George Mountjoy,
    Petrus Jacobus Booysen and Johanna Catharina Mountjoy. The data was fine;
    this function threw it away; nothing refused the build.

    The fence is a negative lookahead per longer name: 'George Augustus Kolbe'
    now matches everywhere EXCEPT where it is followed by ' of Wakkerstroom',
    ' of Bethulie' or ' of Burgersdorp'. The longer name still collects its own.
    See tools/checkregisters.py, which now refuses the build if this ever
    silently drops a person again."""
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
        keep.append(x)
    # TOTAL ORDER, NOT JUST BY LENGTH. `keep` becomes a set, and CPython randomises
    # string hashing per process, so set iteration order differs between runs. Sorting
    # on length alone is stable but leaves ties in that arbitrary order - and because
    # this list drives the ORDER OF MATCHING below, the excerpts in every dossier came
    # out shuffled. Two runs over identical source produced ~30,000-line diffs for a
    # few hundred real changes, which made `git diff --stat` useless for telling a real
    # regeneration from a no-op. Breaking ties on the string itself fixes it.
    return sorted(set(keep), key=lambda x: (-len(x), x))

def fence(v):
    """The suffixes that must NOT follow variant `v`, because they would make it
    a different, longer-named person."""
    return sorted({o[len(v):] for o in ALLNAMES
                   if o != v and o.startswith(v + " ")},
                  key=lambda x: (-len(x), x))   # total order - see variants()

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
            ahead = "".join("(?!" + re.escape(sfx) + ")" for sfx in fence(v))
            pat = (r"(?<![A-Za-z\u00C0-\u024F])" + re.escape(v)
                   + ahead + r"(?![A-Za-z\u00C0-\u024F])")
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
 "people": dict(sorted(dossiers.items()))}   # by slug, so the file is diffable
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
index.sort(key=lambda r: (-len(r[0]), r[0], r[1]))   # total order - see variants()
json.dump(index, open("site/public/whoindex.json", "w"), ensure_ascii=False)
print(f"{len(dossiers)} dossiers · {sum(v['mentions'] for v in dossiers.values())} mentions · {len(index)} auto-link names")
for b in sorted(dossiers.values(), key=lambda v: -v["mentions"])[:8]:
    print(f"  {b['mentions']:4d}  {b['n']}")
