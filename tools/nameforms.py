"""The name forms this archive treats as one person's, shared by the two things that need them.

Until 18 October 2026 this logic lived inside tools/dossiers.py, which wrote whoindex.json for
the browser linker (public/wholink.js). The build-time linker (tools/namesindex.py -> the kit's
autolink.py) needs exactly the same decisions - which spellings of a name are safe to search for,
and which longer names fence a shorter one off - so it is lifted out here, UNCHANGED, and both
import it. dossiers.py's output is byte-identical before and after the move.

No file is read and nothing is written at import."""
import re, unicodedata

def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ÿ", "y").replace("Ÿ", "Y")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60]


# The anchor the kit's autolink.py writes: exactly `<a href="..." data-autolink>name</a>` around text that was already there.
# Tools that read the BUILT text (dossiers.py, searchindex.py) take it out first, so a page reads the same linked or not
# and what they write does not depend on whether the linker has run on the page they were given.
AUTOLINK = re.compile(r'<a href="[^"]*" data-autolink>(.*?)</a>', re.S)


def unlink(html):
    return AUTOLINK.sub(r"\1", html)


def make(people):
    """(ALLNAMES, variants, fence) for a list of people.json rows."""
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
    return ALLNAMES, variants, fence
