#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two files the kit's build-time name linker reads (kit/tools/autolink.py, checklinks.py).

    python3 ../tools/namesindex.py --dist "${ARCHIVE_OUT:-dist}" --out .autolink      # from site/

    .autolink/names-index.json   {"people": [{"name","aliases","url"}], "ambiguous": [{"name","url"}]}
    .autolink/living.json        every living or held-out person's names, spellings and addresses

WHY THIS FILE EXISTS (18 October 2026). The names on the narrative pages were linked to their people only in the
browser, by public/wholink.js reading whoindex.json (written by tools/dossiers.py): three links per name per page,
nothing without JavaScript, and only 7% of the person links existed in the HTML a crawler or a printer sees. The kit
now links the FIRST mention in each section when the site is built. This script is the archive's half of that: which
names, and which of them are safe. It reuses the rules whoindex.json was made with (tools/nameforms.py, lifted out of
dossiers.py unchanged), and fixes four defects those rules had:

  * the old index held the living. A living person's name was linked to a page that shows the name and nothing else.
    Here a living or held-out person is never in the index; their names, spellings and both addresses go to living.json.
  * the old index sent a name to /who/<slug>/, a page about a NAME. A name now goes to the PERSON, /people/<slug>/.
  * a name two people bear was linked as though it were one. Petrus Jacobus Booysen is three men; the old index
    held him under the first one's page. Such a name is now `ambiguous`, sent to /people/<slug>/, which draws each
    of them under his own heading with his own dates, and the linker uses it for nobody else.
  * a spelling two DIFFERENT names share ("Willem Hermanus Booyzen", the stripped form of two men with a nickname
    each) was simply left out. It is now `ambiguous` and sent to /search/?q=..., but ONLY when the served search
    index really returns every one of those people for it; if search would not show them, the name is left out.

WHO IS LIVING is not decided here. It is tools/livingflags.classify over the kit's living_rule.py, exactly as
tools/build-checkprose-feed.py asks it, and it is held against the committed src/data/living.json: if the two
disagree this stops. EVERYTHING THIS READS IS COMMITTED (people.json, dossiers.json, living.json, living-policy.json,
kin.js, the served searchindex.json), so CI builds the same two files, and the index is made after astro build
because it checks each address against the BUILT pages (a page that is missing or says noindex is not linked to).

EXIT 0 written. 2 REFUSED: who is living cannot be decided, or disagrees with living.json, or a living name ended
up in the index. A refusal stops the build; nothing is linked from an index that could not be verified.
Prints counts only, never a name.
"""
import argparse
from html import unescape as html_unescape
import importlib.util
import io
import json
import os
import re
import stat
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
sys.path.insert(0, HERE)
sys.path.insert(0, KIT_TOOLS)
from nameforms import slug, make  # noqa: E402
import searchkit  # noqa: E402


class Refused(Exception):
    pass


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def key(s):
    """One name as the matcher folds it: NFC, one space, straight apostrophes; case-insensitive."""
    s = (s or "").replace("’", "'").replace("‘", "'")
    return " ".join(s.split()).casefold()


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def living_rows(people):
    """(living, held) as sets of indexes into people: the archive's own decision, asked the way the prose gate asks it."""
    try:
        import livingflags as lf
        pol = read_json(os.path.join(DATA, "living-policy.json"))
        fams = lf.families()
    except Exception as e:  # noqa: BLE001
        raise Refused("who is living cannot be decided here (%s): no index was written" % type(e).__name__)
    if len(people) < 50:
        raise Refused("people.json has %d people: refusing to decide who is living from that" % len(people))
    living, held = lf.classify(people, fams, pol.get("heldOut", []), pol.get("author", []))
    return set(living), set(held), pol


def build(dist, out_dir):
    people = read_json(os.path.join(DATA, "people.json"))["people"]
    committed = read_json(os.path.join(DATA, "living.json"))
    live, held, pol = living_rows(people)

    # ---- who is living: the decision, held against the roster the pages were built from
    slugs_of = lambda idxs: {slug(people[i]["n"]) for i in idxs}
    live_slugs, held_slugs = slugs_of(live), slugs_of(held) | set(pol.get("heldOut", []))
    if live_slugs != {x["slug"] for x in committed["living"]}:
        raise Refused("the living roster this build computes differs from src/data/living.json: run tools/livingflags.py")
    off = live_slugs | held_slugs                       # every address that must never be linked to

    feed = _load("buildfeed", "build-checkprose-feed.py")
    ALLNAMES, variants, fence = make(people)
    solo = lambda p: make([p])[1](p)                    # one person's spellings, with nobody else's names to drop them

    groups = {}                                         # dossier slug -> [people.json rows]
    for i, p in enumerate(people):
        groups.setdefault(slug(p["n"]), []).append((i, p))

    # ---- living.json: names, spellings and addresses of everyone living or held out
    names = set()
    for i in sorted(live | held):
        p = people[i]
        names.update(feed.spellings(p, False))
        names.update(solo(p))
        names.add(p["n"])
    lk = {key(n) for n in names}                        # every living or held-out spelling, folded
    living_out = sorted(names) + sorted("/people/%s/" % s for s in off) + sorted("/who/%s/" % s for s in off)

    # ---- every spelling and who owns it (the living own spellings too: a spelling they share is nobody's)
    def structural(n):
        """Forms that are the canonical name with something taken away or its quotes removed: the same words."""
        out = {n, re.sub(r"\s*[“\"][^”\"]+[”\"]\s*", " ", n).replace("  ", " ").strip(),
               re.sub(r"\s*\(.*?\)\s*", " ", n).strip(), re.sub(r"[“”\"]", "", n).strip()}
        out.add(re.sub(r"\s*\(.*?\)\s*", " ", re.sub(r"[“”\"]", "", n)).strip())
        out.add(re.sub(r"\s*\(.*?\)\s*", " ", re.sub(r"\s*[“\"][^”\"]+[”\"]\s*", " ", n)).replace("  ", " ").strip())
        return {" ".join(x.split()) for x in out}

    def plain(n):
        return searchkit.fold(re.sub(r"\(.*?\)|[“”\"]", " ", n)).replace(".", " ").split()

    def safe_alias(p, form):
        """A spelling the archive records for this person that is still a FULL name: the same words as the canonical
        name with a nickname or brackets taken away, or at least three words that begin with the person's first name
        and end in the person's surname exactly. The recorded spellings in the v field also hold 'Daniel Jacobus',
        'Jan Hendrik', 'Commandant Kolbe': a given name pair, or a title and a surname, that any number of other men
        would bear. Those are the person's, in the archive's notes, and they are not names a stranger can be linked by."""
        if key(form) in {key(x) for x in structural(p["n"])}:
            return True
        a, c = plain(form), plain(p["n"])
        return len(a) >= 3 and bool(c) and a[0] == c[0] and a[-1] == c[-1]

    def recorded(p):
        """EVERY spelling the archive records for this person, linkable or not, for deciding who bears a name. The
        rule that keeps a spelling out of the index (safe_alias) must not also keep it out of the count of bearers: if
        'John Henry Kolbe' is written down for one man and is another man's name, it is two men's, even though the
        archive would never link by the first. Found by the namesake check, which read every v spelling."""
        out = set(structural(p["n"])) | set(solo(p))
        for seg in re.split(r"\s*[·;]\s*", str(p.get("v") or "")):
            seg = seg.split(",")[0]
            out.add(re.sub(r"\s*\(.*?\)", " ", seg))
            out.add(seg)
        return {" ".join(x.split()) for x in out if len(x.split()) >= 2}

    def spellings_of(p):
        n = p["n"]
        out = {n}
        out.update(x for x in solo(p) if safe_alias(p, x))   # the rules dossiers.py has always used, then the full-name test
        out.update(structural(n))
        return {x for x in out if len(x.split()) >= 2}

    owners = {}                                         # key -> {slug}: every recorded spelling counts here
    forms = {}                                          # slug -> {key: spelling as written}: the ones that may be linked
    for s, rows in groups.items():
        f = forms.setdefault(s, {})
        for _i, p in rows:
            for form in sorted(spellings_of(p)):
                f.setdefault(key(form), form)
            for form in recorded(p):
                owners.setdefault(key(form), set()).add(s)
        for k in f:
            owners.setdefault(k, set()).add(s)

    dead_slugs = [s for s in groups if s not in off]

    # ---- which addresses exist, indexably, in the build
    def page_ok(url):
        p = os.path.join(dist, url.strip("/"), "index.html")
        if not os.path.isfile(p):
            return False
        with io.open(p, encoding="utf-8") as fh:
            head = fh.read(6000)
        return not re.search(r'<meta name="robots" content="[^"]*noindex', head)

    # ---- the served search index, to prove a search address shows the people it stands for
    sidx = os.path.join(SITE, "public", "searchindex.json")
    person_hay = {}
    if os.path.isfile(sidx):
        for r in read_json(sidx):
            if r.get("k") == "Person":
                person_hay.setdefault(r.get("t"), r.get("q") or "")
    search_ok = os.path.isfile(os.path.join(dist, "search", "index.html")) and bool(person_hay)

    stats = dict(people=0, aliases=0, ambiguous_people_page=0, ambiguous_search=0,
                 left_out_living=0, left_out_search_unproven=0, left_out_not_a_full_name=0, left_out_no_page=0, left_out_short=0, ambiguous_continuation=0, fenced_name_sent_to_search=0)
    people_out, amb_out = [], []
    for s in sorted(dead_slugs):
        rows = groups[s]
        url = "/people/%s/" % s
        if not page_ok(url):
            stats["left_out_no_page"] += 1
            continue
        if len(rows) == 1:
            canon = rows[0][1]["n"]
            mine = sorted((form for k, form in forms[s].items() if owners[k] == {s} and k not in lk),
                          key=lambda x: (-len(x), x))   # only the spellings nobody else also bears, none a living one
            names_ = [m for m in mine if key(m) == key(canon)]
            if not names_:
                if not mine:
                    continue
                names_ = [mine[0]]
            name = names_[0]
            als = [m for m in mine if key(m) != key(name)]
            people_out.append({"name": name, "aliases": als, "url": url})
            stats["people"] += 1
            stats["aliases"] += len(als)
        else:                                           # several people of one name, drawn on one page under their own headings
            canon = rows[0][1]["n"]
            if len({r[1]["n"] for r in rows}) != 1 or key(canon) in lk:
                continue                                # two different names in one slug: nothing is claimed
            if owners[key(canon)] == {s}:               # these men are the only bearers, and their page draws each
                amb_out.append({"name": canon, "url": url})
                stats["ambiguous_people_page"] += 1
            # else somebody else also bears it: the loop below decides, and only search can show them all

    # ---- a spelling two different people's names share
    for k, own in sorted(owners.items()):
        if len(own) < 2:
            continue
        if own & off:
            stats["left_out_living"] += 1
            continue
        spelling = next((forms[s][k] for s in sorted(own) if k in forms[s]), None)
        if spelling is None:                            # recorded for these people, but a spelling nobody would link by
            stats["left_out_not_a_full_name"] += 1
            continue
        if not search_ok:
            stats["left_out_search_unproven"] += 1
            continue
        q = searchkit.fold(spelling)
        shown = all(q in person_hay.get(groups[s][0][1]["n"], "") for s in own)
        if not shown:
            stats["left_out_search_unproven"] += 1
            continue
        from urllib.parse import quote
        amb_out.append({"name": spelling, "url": "/search/?q=" + quote(spelling, safe="")})
        stats["ambiguous_search"] += 1

    # ---- A NAME THAT IS THE FIRST WORDS OF ANOTHER PERSON'S NAME, followed in the prose by a word that makes it someone else.
    # 'George Augustus Kolbe' is the Settler, and 'George Augustus Kolbe of Bethulie' is another man. The linker matches
    # longest-first, so the known longer name is handled; but the prose also writes 'George Augustus Kolbe of Sterkfontein',
    # a continuation the data does not list, and the shorter name would be linked to the Settler there. Found by the
    # namesake check on 18 October 2026 (12 such links in the first build). So the BUILT pages are read: wherever such a
    # name is followed by 'of <Place or year>', 'the younger / elder / infant ...' or Jr / Sr / II / III, and the longer
    # name is not one the index lists, that whole phrase is added as an ambiguous name and sent to the search for the
    # name, which shows every man who bears it. The linker, matching longest-first, then takes the phrase and the
    # shorter name is never linked in that place. If search cannot be shown to list them all, the shorter name is
    # left out of the index altogether.
    listed = {key(e["name"]) for e in people_out} | {key(a) for e in people_out for a in e["aliases"]} \
        | {key(e["name"]) for e in amb_out}
    every = {k: o for k, o in owners.items()}

    def longer_bearers(k):
        """Everyone whose recorded spelling is this name followed by more words."""
        return {x for kk, o in every.items() if kk.startswith(k + " ") for x in o}

    fenced = {}                                        # key -> the person entry it belongs to (a dict in people_out)
    for e in people_out:
        for nm in [e["name"]] + e["aliases"]:
            if longer_bearers(key(nm)):
                fenced[key(nm)] = (e, nm)
    TAIL = (r"(?:of\s+(?:[A-Z0-9][\w'’-]*)(?:\s+(?:[A-Z][\w'’-]*|\d{4})){0,2}"
            r"|the\s+(?:younger|elder|infant|second|third|first|junior|senior)\b"
            r"|(?:Jr\.?|Sr\.?|II|III)\b)")
    MARK = "\x01"                                       # where an inline tag stood
    INLINE = re.compile(r"</?(?:a|b|i|em|strong|span|sup|sub|small|mark|u|font)\b[^>]*>", re.I)
    phrases = {}                                       # key of the shorter name -> {phrase as written, in one text}
    split = set()                                      # keys of shorter names whose continuation sits in the NEXT element
    if fenced:
        pat = {}
        for k, (e, nm) in fenced.items():
            words = r"\s+".join(re.escape(w) for w in nm.split())
            pat[k] = (re.compile(r"(?<![\w])((?i:%s))\s+%s" % (words, TAIL)),
                      re.compile(r"(?<![\w])(?i:%s)[\s%s]*%s[\s%s]*%s" % (words, MARK, MARK, MARK, TAIL)))
        for dp, _ds, fs in os.walk(dist):
            if "index.html" not in fs:
                continue
            route = "/" + os.path.relpath(dp, dist).replace(os.sep, "/") + "/"
            if re.match(r"^/(people|who|register)/", route):
                continue                               # the linker is not run there (Base.astro: data-no-autolink)
            with io.open(os.path.join(dp, "index.html"), encoding="utf-8") as fh:
                raw = fh.read()
            m_ = re.search(r"<main\b.*</main>", raw, re.S)
            if not m_:
                continue
            body = re.sub(r"<(script|style)\b.*?</\1>", " ", m_.group(0), flags=re.S | re.I)
            body = re.sub(r"<[^>]+>", " ", INLINE.sub(MARK, body))
            body = " ".join(html_unescape(body).replace("\u00a0", " ").split())
            for k, (same, across) in pat.items():
                if across.search(body):
                    split.add(k)
                for m in same.finditer(body):
                    phrase = m.group(0)
                    kp = key(phrase)
                    if kp in listed or any(kp.startswith(l + " ") and len(l) > len(k) for l in listed):
                        continue                       # a longer name the index lists, in one text: the linker takes it first
                    phrases.setdefault(k, set()).add(phrase)
    from urllib.parse import quote
    for k, (e, nm) in sorted(fenced.items()):
        if k not in phrases and k not in split:
            continue
        bearers = {x for x in owners.get(k, set())} | longer_bearers(k)
        shown = search_ok and all(searchkit.fold(nm) in person_hay.get(groups[x][0][1]["n"], "") for x in bearers)
        if k in split or not shown:                    # the linker cannot take a phrase split across elements, and
            # cannot send the rest anywhere honest: the shorter name goes to the search for it, or is not linked at all
            if key(e["name"]) == k:
                people_out = [x for x in people_out if x is not e]
            else:
                e["aliases"] = [a for a in e["aliases"] if key(a) != k]
            if shown:
                amb_out.append({"name": nm, "url": "/search/?q=" + quote(nm, safe="")})
                stats["ambiguous_search"] += 1
                stats["fenced_name_sent_to_search"] += 1
            else:
                stats["left_out_search_unproven"] += 1
            continue
        for ph in sorted(phrases[k]):
            amb_out.append({"name": ph, "url": "/search/?q=" + quote(nm, safe="")})
            stats["ambiguous_continuation"] += 1

    # ---- the one hard rule, checked a second way before anything is written
    bad = set()
    for e in people_out:
        if key(e["name"]) in lk or any(key(a) in lk for a in e["aliases"]) or e["url"].split("/")[2] in off:
            bad.add(e["url"])
    for e in amb_out:
        if key(e["name"]) in lk:
            bad.add(e["url"] + e["name"])
    if bad:
        raise Refused("LIVING: %d index entr%s a living or held-out person also holds; nothing was written"
                      % (len(bad), "y is one" if len(bad) == 1 else "ies are ones"))

    people_out.sort(key=lambda e: e["url"])
    amb_out.sort(key=lambda e: (e["name"].casefold(), e["url"]))
    os.makedirs(out_dir, exist_ok=True)
    with io.open(os.path.join(out_dir, "names-index.json"), "w", encoding="utf-8") as fh:
        json.dump({"people": people_out, "ambiguous": amb_out}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    lp = os.path.join(out_dir, "living.json")
    fd = os.open(lp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(living_out, fh, ensure_ascii=False)
    stats["living people"] = len(live)
    stats["held out"] = len(held_slugs)
    stats["living names and addresses"] = len(living_out)
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the names index and the living list for autolink.py (counts only).")
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--out", default=".autolink")
    a = ap.parse_args(argv)
    dist = os.environ.get("ARCHIVE_OUT") or a.dist
    if not os.path.isabs(dist):
        dist = os.path.join(SITE, dist) if not os.path.isdir(dist) else os.path.abspath(dist)
    out = a.out if os.path.isabs(a.out) else os.path.join(SITE, a.out)
    if not os.path.isfile(os.path.join(dist, "index.html")):
        print("namesindex: REFUSED. no built site under %s: nothing was examined" % dist)
        return 2
    try:
        st = build(dist, out)
    except Refused as e:
        print("namesindex: REFUSED. %s" % e)
        return 2
    print("namesindex: " + " · ".join("%s %d" % (k, v) for k, v in st.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
