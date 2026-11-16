#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roots & Routes: the tree page for this archive, built from this archive's own committed data.

    python3 tools/build-tree-page.py            # rebuild data/tree-page/ (tree.json, atlas-data.json, roots.html, roots.embed.html)
    python3 tools/build-tree-page.py --check    # exit 1 if the page is older than the data it was built from

WHERE THE PEOPLE COME FROM. This archive keeps no GEDCOM. Its people are site/src/data/people.json (written from people.js), its parent and child links are the
households in site/src/data/kin.js (each with the `via` that says on whose word), and its marriages are site/src/data/marriages.json. All three are turned into a
small GEDCOM (data/tree-page/people.ged, not committed) and handed to the family-tree-page skill's converter, vendored in tools/tree-page/ so CI and other sessions
do not depend on ~/.claude.

WHO IS LEFT OUT. Anyone tools/livingflags.py (the kit's living_rule.py) calls living or holds out is not written into the GEDCOM at all, so they cannot reach tree.json.
The converter then adds its own floor: nobody with no death recorded and a birth year in the last 110 years is drawn. Both counts are in tree.report.json.

DATES AND PLACES come from the archive's own born and died fields, read the way tools/familylines.mjs reads them (its `field()` is ported here and checked against it:
the part before the first comma is the date, the part after is the place, and a baptism's or a burial's place is named as such; a burial place is NOT a death place).
A year the field qualifies ("c. 1788", "bef. 1828", "bapt. 1741") is drawn as an estimate, "c. 1788", never as exact.

PLACES are resolved through data/tree-page/place_map.json, never guessed: the town and point data/era-ground.tsv + data/era-towns.tsv already decided for a string, then the
strings decided by hand in place-additions.json (each with its reason), then a place the Record Atlas names uniquely in the country the string names. Anything else is
listed in tree.report.json (unresolved_places). A person with no place of their own is drawn at a relative's birth place and carries the page's "*" (bpe); a person with no
relative placed is not drawn and is listed under "Not drawn yet".

COLOUR is the archive's own line (the `l` of a person in people.json), not a surname spelling: which spellings are one name is the Record Atlas catalogue's to say
(surname-variants skill), and this archive keeps no list of them here.
"""
import argparse, collections, datetime, hashlib, io, json, math, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")
OUT = os.path.join(ROOT, "data", "tree-page")
TP = os.path.join(ROOT, "tools", "tree-page")
EXT = os.path.join(TP, "painted-lines.ext.html")
HOST = "booyzen.defranceski.com"
ATLAS_CANDIDATES = [os.environ.get("RECORD_ATLAS", ""), os.path.expanduser("~/Projects/Family Projects/Record Atlas"),
                    os.path.join(os.path.dirname(ROOT), "Record Atlas")]
INPUTS = [("site/src/data", n) for n in ("people.json", "kin.js", "marriages.json", "living.json", "living-policy.json")] + [("data", "era-ground.tsv"), ("data", "era-towns.tsv")]

sys.path.insert(0, os.path.join(ROOT, "tools"))
import livingflags as lf  # the archive's own living decision: the kit's living_rule.py over people.json

def jl(path): return json.load(io.open(path, encoding="utf-8"))
def run(args):
    print("$", " ".join(os.path.relpath(a, ROOT) if os.path.isabs(a) and a.startswith(ROOT) else a for a in args)); r = subprocess.run(args)
    if r.returncode: sys.exit(r.returncode)
def inputs_hash():
    h = hashlib.sha1()
    for d, n in INPUTS: h.update(io.open(os.path.join(ROOT, d, n), "rb").read())
    for n in ("tree-views.template.html", "painted-lines.ext.html", "gedcom_to_tree.py"): h.update(io.open(os.path.join(TP, n), "rb").read())
    h.update(io.open(os.path.abspath(__file__), "rb").read())
    h.update(io.open(os.path.join(ROOT, "tools", "livingflags.py"), "rb").read())
    for n in ("place-additions.json",):
        if os.path.exists(os.path.join(OUT, n)): h.update(io.open(os.path.join(OUT, n), "rb").read())
    return h.hexdigest()[:16]
def atlas_path():
    for c in ATLAS_CANDIDATES:
        if c and os.path.exists(os.path.join(c, "data", "places.json")): return c
    sys.exit("Record Atlas checkout not found (set RECORD_ATLAS)")

# ---------------------------------------------------------------- the archive's own born/died field (ported from tools/familylines.mjs field())
FULLDATE = re.compile(r"^(\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4})(?=$|,| — )")   # "23 Mar 1850": a day, an English month abbreviation, a year, at the START of the field (no c. / bapt. / buried / bef. before it)
YEAR = re.compile(r"(1[5-9]\d\d|20\d\d)")
QUAL = re.compile(r"(c\.|ca\.|bef\.|aft\.|after|before|about|abt\.?|bapt\.|buried)\s+(?:\d{1,2}\s+)?(?:[A-Z][a-z]{2,8}\.?\s+)?$", re.I)
QMAP = {"ca.": "c.", "about": "c.", "abt.": "c.", "abt": "c.", "before": "bef.", "after": "aft.", "buried": ""}
def field(s):
    pre = re.split(r"\s+—\s+", str(s if s is not None else ""))[0].strip()
    if not pre or re.fullmatch(r"[—–-]+", pre): return {"year": "", "place": "", "event": ""}
    parts = [x.strip() for x in re.split(r",(?![^(]*\))", pre) if x.strip()]
    year = ""; event = "baptism" if re.match(r"bapt", parts[0], re.I) else "burial" if re.match(r"buried", parts[0], re.I) else ""
    m = YEAR.search(parts[0])
    if m:
        q = QUAL.search(parts[0][:m.start()])
        w = q.group(1).lower() if q else ""
        year = QMAP.get(w, w); year = (year + " " if year else "") + m.group(1)
    places = []
    for part in parts[1:]:
        if re.match(r"(baptised|bapt\.)", part, re.I):
            event = "baptism"; at = re.search(r"\bat\s+(.+)$", part)
            if at: places.append(at.group(1))
            continue
        if re.match(r"buried", part, re.I): event = "burial"; continue
        if re.match(r"(or|aged|estate|death notice|will)\b", part, re.I) or re.search(r"\d", part): continue
        places.append(re.sub(r"\s*\((?!\?\))[^)]{4,}\)", "", part).strip())
    return {"year": year, "place": ", ".join(x for x in places if x), "event": event}

def gdate(year):
    if not year: return ""
    q, _, y = year.rpartition(" ")
    return {"c.": "ABT ", "bef.": "BEF ", "aft.": "AFT ", "bapt.": "ABT "}.get(q, "") + y

# ---------------------------------------------------------------- names, as the archive's own families.js splits them
PARTICLE = r"(?:van|von|de|du|der|den|ten|te)"
def split_name(n):
    s = re.sub(r"\s+of\s+(\d{4}|[A-Z][\w'’\- ]*)$", "", str(n))
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r"\s+born\s+\S+$", "", s, flags=re.I)
    s = re.sub(r"\s+the\s+(younger|elder)$", "", s, flags=re.I)
    s = re.sub(r"\s+(I|II|III)$", "", s).strip()
    m = re.search(r"((?:(?<![^\W\d_])%s\s+)*\S+)$" % PARTICLE, s, re.I)
    if not m: return s, ""
    return s[:m.start()].strip(), m.group(1)

def fold(s): return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()).strip()
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

# ---------------------------------------------------------------- the people, the households, the marriages -> a small GEDCOM
VIA_GRADE = {"doc": 2, "line": 2, "inf": 1, "tree": 0}   # the page's grades: 2 read from a register, 1 household tree, 0 index entry only (drawn dashed)

# SEX is kept only where the archive's own data states or entails it, never from a first name. A husband or a wife in a household or marriage (below); then the archive's own wording:
# a note that opens "Daughter of ...", "His daughter", "Her second son" or "Wife of ..." says what the person is, and a married woman's birth name in the variants field
# ("born Mountjoy", "geboren Dormehl"; the archive's own bornInto() reads it as the family a married woman was born into). Everything else is unknown ('u').
_ORD = r"(?:(?:eldest|elder|younger|second|third|fourth|fifth|sixth|seventh|eighth|youngest|only|first)\s+)?"
WORD_F = re.compile(r"^\W*(?:(?:his|her)\s+)?%s(?:daughter|sister|wife|widow)\b" % _ORD, re.I)
WORD_M = re.compile(r"^\W*(?:(?:his|her)\s+)?%s(?:son|brother|husband|widower)\b" % _ORD, re.I)
BORN = re.compile(r"(?:^|[,(·]\s*)(?:born|geboren|gebore|gebooren)\s+[A-Za-zÀ-ÿ'’]", re.I)
def stated_sex(p):
    r = re.sub(r"[*_]", "", str(p.get("r") or "")).strip()
    f, m = bool(WORD_F.match(r)), bool(WORD_M.match(r))
    if f and not m: return "F", "wording"
    if m and not f: return "M", "wording"
    if BORN.search(str(p.get("v") or "")): return "F", "born"
    return None, None

def load():
    people = jl(os.path.join(DATA, "people.json"))["people"]
    pol = jl(os.path.join(DATA, "living-policy.json"))
    fams = lf.families()
    living, held = lf.classify(people, fams, pol.get("heldOut", []), pol.get("author", []))
    return people, fams, set(living), set(held)

def resolve_strict(ref, people):
    """A marriage's reference to one person, or None. A bare name is accepted only if exactly one person bears it."""
    name, _, token = (ref or "").partition("|")
    hits = [i for i, p in enumerate(people) if p["n"] == name and (not token or token in (p.get("b") or "") or token in (p.get("d") or ""))]
    return hits[0] if len(hits) == 1 else None

def dossier_pages(people):
    """The page each person is on: the dossier that holds them (a namesake page holds both men), as site/src/lib/families.js hostOf finds it."""
    doss = list(jl(os.path.join(DATA, "dossiers.json"))["people"].values())
    out = {}
    for i, p in enumerate(people):
        h = next((x for x in doss if x["n"] == p["n"] or any(a["n"] == p["n"] and a.get("b") == p.get("b") for a in x.get("also") or [])), None)
        out[i] = h["slug"] if h else None
    return out

def build_model():
    people, fams, living, held = load()
    omitted = living | held
    pid = lambda i: "P%d" % (i + 1)
    # sex only where a household or a marriage says it: a husband is male, a wife female. Nothing is read from a first name.
    sex = {}
    hh = []                                                        # (h, w, [(kid, via)], via)
    for f in fams:
        h, w = lf.resolve(f.get("h"), people), lf.resolve(f.get("w"), people)
        if h is not None: sex[h] = "M"
        if w is not None: sex[w] = "F"
        hh.append((h, w, [(lf.resolve(k["n"], people), k.get("via")) for k in f.get("kids", [])], f.get("via")))
    marr = []
    sexsrc = {i: "household" for i in sex}
    for r in jl(os.path.join(DATA, "marriages.json"))["rows"]:
        h, w = resolve_strict(r.get("h"), people), resolve_strict(r.get("w"), people)
        if h is not None and w is not None and h != w:
            for x, v in ((h, "M"), (w, "F")):
                if x not in sex: sex[x] = v; sexsrc[x] = "marriage"
            marr.append((h, w))
    for i, p in enumerate(people):
        v, how = stated_sex(p)
        if not v: continue
        if i in sex and sex[i] != v: sexsrc[i] = "conflict-household-kept"; continue   # a household role wins; the disagreement is reported
        if i not in sex: sex[i] = v; sexsrc[i] = how
    return people, living, held, omitted, hh, marr, sex, pid, sexsrc

def write_ged(path):
    people, living, held, omitted, hh, marr, sex, pid, sexsrc = build_model()
    fam_of = {}; famrec = {}; childgrade = {}; second_parentage = 0
    def fam(h, w):
        k = (h, w)
        if k not in famrec: famrec[k] = {"id": "@F%d@" % (len(famrec) + 1), "kids": []}
        return famrec[k]
    for h, w, kids, via in hh:
        h = h if h is not None and h not in omitted else None
        w = w if w is not None and w not in omitted else None
        if h is None and w is None: continue
        fr = fam(h, w)
        for ki, kvia in kids:
            if ki is None or ki in omitted: continue
            if ki in fam_of:
                if fam_of[ki] != fr["id"]: second_parentage += 1   # a person already has a first household as a child (the one their page draws): the second is not drawn
                continue
            fam_of[ki] = fr["id"]; fr["kids"].append(ki); childgrade[ki] = VIA_GRADE.get(kvia, 0)
    for h, w in marr:
        if h in omitted or w in omitted: continue
        fam(h, w)
    spouse_fams = collections.defaultdict(list)
    for (h, w), fr in famrec.items():
        for x in (h, w):
            if x is not None and fr["id"] not in spouse_fams[x]: spouse_fams[x].append(fr["id"])
    fields = {}
    out = ["0 HEAD", "1 CHAR UTF-8"]
    drawn_candidates = []
    for i, p in enumerate(people):
        if i in omitted: continue
        given, sur = split_name(p["n"])
        bf, df = field(p.get("b")), field(p.get("d"))
        fields[i] = (bf, df)
        out += ["0 @%s@ INDI" % pid(i), "1 NAME %s /%s/" % (given, sur), "1 SEX %s" % sex.get(i, "U")]
        if bf["year"] or bf["place"]:
            out.append("1 CHR" if bf["event"] == "baptism" else "1 BIRT")
            if bf["year"]: out.append("2 DATE %s" % gdate(bf["year"]))
            if bf["place"]: out.append("2 PLAC %s" % bf["place"])
        kind = lf.death_kind(p)                                      # "record" (a date, a place, a register line), "flag" (the bare word deceased) or None
        if kind:
            out.append("1 BURI" if df["event"] == "burial" else "1 DEAT")
            if df["year"]: out.append("2 DATE %s" % gdate(df["year"]))
            if df["place"] and df["event"] != "burial": out.append("2 PLAC %s" % df["place"])   # a burial place is not a death place
        if i in fam_of: out.append("1 FAMC %s" % fam_of[i])
        for fx in spouse_fams.get(i, []): out.append("1 FAMS %s" % fx)
    for (h, w), fr in famrec.items():
        out.append("0 %s FAM" % fr["id"])
        if h is not None: out.append("1 HUSB @%s@" % pid(h))
        if w is not None: out.append("1 WIFE @%s@" % pid(w))
        for k in fr["kids"]: out.append("1 CHIL @%s@" % pid(k))
    out.append("0 TRLR")
    io.open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return {"people": people, "fields": fields, "childgrade": childgrade, "sex": sex, "omitted": omitted, "living": living, "held": held,
            "second_parentage": second_parentage, "pid": pid, "sexsrc": sexsrc}

# ---------------------------------------------------------------- places the archive has already placed
TOWN_ROW = re.compile(r"^(.*?)\s*$")
def seed_place_map(atlas):
    """Place strings this archive has already put on the ground, then those decided by hand with a reason. data/era-ground.tsv decided, for each place string AS PRINTED, the
    town it belongs to, and data/era-towns.tsv that town's point (this archive's own places.json, or a hand-written centre). A string with no town there stays unresolved.
    The country is the Atlas's own `geo.country_of` on the point, never a guess from the string; a Record Atlas place is linked only where it has the same name within 15 km."""
    sys.path.insert(0, os.path.join(atlas, "scripts")); import geo
    cj = jl(os.path.join(atlas, "data", "countries.json"))["countries"]
    pj = jl(os.path.join(atlas, "data", "places.json"))["places"]
    byname = collections.defaultdict(list)
    for x in pj:
        for nm in [x["name"]] + [n["n"].split(",")[0] for n in x.get("names", [])]: byname[fold(nm)].append(x)
    points = {}
    for line in io.open(os.path.join(ROOT, "data", "era-towns.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        c = line.rstrip("\n").split("\t")
        if len(c) >= 3 and c[0] != "town": points[c[0]] = (float(c[1]), float(c[2]))
    pm_path = os.path.join(OUT, "place_map.json")
    pm = jl(pm_path) if os.path.exists(pm_path) else {}
    seeded = 0
    for line in io.open(os.path.join(ROOT, "data", "era-ground.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        c = line.rstrip("\n").split("\t")
        if len(c) < 4 or c[0] == "place": continue
        raw, town = c[0], c[3].strip()
        if not town or town not in points or (pm.get(raw) or {}).get("lat") is not None: continue
        lat, lon = points[town]
        iso = geo.country_of(lat, lon)
        if not iso: continue
        hit = next((x for x in byname.get(fold(town), []) if x.get("country") == iso and km(lat, lon, x["lat"], x["lon"]) <= 15), None)
        pm[raw] = {"name": town, "lat": lat, "lon": lon, "country": cj.get(iso, {}).get("name", iso), "iso": iso, "atlas_id": hit["id"] if hit else None,
                   "how": "data/era-ground.tsv town and data/era-towns.tsv point; country by the Atlas's geo.country_of"}
        seeded += 1
    ap_ = os.path.join(OUT, "place-additions.json")
    if os.path.exists(ap_):
        for k, v in jl(ap_)["places"].items():
            if (pm.get(k) or {}).get("lat") is None: pm[k] = v; seeded += 1
    io.open(pm_path, "w", encoding="utf-8").write(json.dumps(pm, indent=1, ensure_ascii=False))
    print("place_map: %d place strings seeded (era-ground.tsv and place-additions.json)" % seeded)
    return seeded

def build(a):
    os.makedirs(OUT, exist_ok=True)
    ged = os.path.join(OUT, "people.ged"); M = write_ged(ged)
    people, fields, pid, omitted = M["people"], M["fields"], M["pid"], M["omitted"]
    pages = dossier_pages(people)
    slugs = {pid(i): pages[i] for i in fields if pages[i]}
    io.open(os.path.join(OUT, "slugs.json"), "w", encoding="utf-8").write(json.dumps(slugs, ensure_ascii=False))
    atlas = atlas_path(); seed_place_map(atlas)
    tree, pm = os.path.join(OUT, "tree.json"), os.path.join(OUT, "place_map.json")
    cmd = [sys.executable, os.path.join(TP, "gedcom_to_tree.py"), ged, "--out", tree, "--place-map", pm, "--atlas", atlas, "--living", "omit",
           "--lines", "8", "--slugs", os.path.join(OUT, "slugs.json"), "--title", "Roots & Routes",
           "--subtitle", "Explore the family tree ten ways: by generation, place, era and relationship. Click anyone and every view follows."]
    if a.accept_unique: cmd.append("--accept-unique")
    run(cmd)
    t = jl(tree)
    # lines: the archive's own line (`l`), the seven with most people drawn, the rest together
    byid = {pid(i): i for i in fields}
    cnt = collections.Counter(people[byid[p["id"]]]["l"] for p in t["people"])
    top = [l for l, _ in cnt.most_common(7)]
    t["lines"] = [{"sur": l, "host": HOST} for l in top] + [{"sur": "Other", "host": HOST}]
    t["meta"].update({"rowLabel": "Family line", "lineLabel": "Family line"})
    pm_ = jl(pm); okp = lambda k: bool(k and pm_.get(k) and pm_[k].get("lat") is not None and pm_[k].get("name"))
    # CORRECTIONS (cx): how many of this archive's corrections name a person, for the Atlas Tree Canvas's pencil mark. A count only, never what a correction says. It is read from
    # corrections-who.json, the file tools/correctionswho.py derives (a person attached only when their whole held name appears, minus what corrections-who-deny.json refuses) and
    # that `check:corrections` holds current, so the number is the one a reader sees on /corrections/ and on the person's page. A correction naming two people counts for each.
    # Only the people the converter drew are here, so never a living or held-out person; a person with none gets no field.
    cx_by_slug = collections.Counter(sl for sls in jl(os.path.join(DATA, "corrections-who.json"))["who"].values() for sl in sls)
    est_b = est_d = relpl = 0
    for p in t["people"]:
        i = byid[p["id"]]; bf, df = fields[i]
        p["line"] = top.index(people[i]["l"]) if people[i]["l"] in top else 7
        p["page"] = "/people/%s/" % pages[i] if pages[i] else None
        if p["page"] is None: p.pop("page")
        # a year the archive's own field qualifies (c., bef., aft., bapt.) is an estimate, drawn as "c. 1788"
        # FULL DATES (bd, dd), for DEAD people only: this loop only sees the people the converter drew (--living omit, and its 110-year floor), so a living person never gets one.
        # The value is the date as the person page prints it, "23 Mar 1850" (day not padded, English month abbreviation), cut from the front of people.json's own `b` / `d`; the
        # place and the rest of the field are not part of it. A year alone, a year-month, an approximate date ("c. 1850"), a baptism ("bapt. 4 Jul 1810") or a burial gets no field:
        # `by` / `dy` and the `bye` / `dye` flags already carry those.
        cx = cx_by_slug.get((p.get("page") or "").strip("/").split("/")[-1], 0)
        if cx: p["cx"] = cx
        mb = FULLDATE.match(str(people[i].get("b") or "")); md = FULLDATE.match(str(people[i].get("d") or ""))
        if mb: p["bd"] = mb.group(1)
        if md: p["dd"] = md.group(1)
        if re.match(r"(c\.|bef\.|aft\.|bapt\.)", bf["year"]) and not p["bye"]: p["bye"] = True; est_b += 1
        if re.match(r"(c\.|bef\.|aft\.|bapt\.)", df["year"]) and not p["dye"]: p["dye"] = True; est_d += 1
        # the place of a person with no resolvable birth place of their own was taken from a relative: the page marks it with *
        own = bf["place"] if okp(bf["place"]) else None
        if not own: p["bpe"] = True; relpl += 1
        g = M["childgrade"].get(i)
        if g is not None:
            if p.get("father"): p["fg"] = g
            if p.get("mother"): p["mg"] = g
    conflicts = drop_conflicts(t, tree, people, byid)
    keep_death_place(t, people, fields, byid)
    rep_path = os.path.splitext(tree)[0] + ".report.json"; rep = jl(rep_path)
    drawn = {p["id"] for p in t["people"]}
    t["undrawn"] = undrawn_list(people, fields, pid, pages, M, drawn, pm_, okp, rep, cx_by_slug)
    json.dump(t, io.open(tree, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    rep["adapter"] = {"people_in_archive": len(people), "living_withheld": len(M["living"]), "held_out": len(M["held"]),
                      "birth_year_qualified_by_the_archive": est_b, "death_year_qualified_by_the_archive": est_d,
                      "drawn_at_a_relatives_birth_place": relpl, "second_parentage_not_drawn": M["second_parentage"],
                      "sex_unknown_drawn": sum(1 for p in t["people"] if p["sex"] == "u"),
                      "sex_by_source_drawn": dict(collections.Counter(M["sexsrc"].get(byid[p["id"]], "none") for p in t["people"] if p["sex"] != "u")),
                      "sex_conflicts": sum(1 for v in M["sexsrc"].values() if v == "conflict-household-kept"),
                      "place_strings_total": len(pm_), "place_strings_resolved": sum(1 for k in pm_ if okp(k)),
                      "from_era_ground": sum(1 for v in pm_.values() if (v.get("how") or "").startswith("data/era-ground")),
                      "from_place_additions": sum(1 for k in jl(os.path.join(OUT, "place-additions.json"))["places"] if okp(k)) if os.path.exists(os.path.join(OUT, "place-additions.json")) else 0,
                      "conflicts_not_drawn": len(conflicts)}
    lr = living_rows(t)
    t["people"] += lr; t["meta"]["livingNames"] = "name-and-family-only"
    json.dump(t, io.open(tree, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    rep["living_rows"] = len(lr)
    if conflicts: rep["conflicts"] = conflicts
    io.open(rep_path, "w", encoding="utf-8").write(json.dumps(rep, indent=1, ensure_ascii=False))

def drop_conflicts(t, tree, people, byid):
    """A person whose recorded death comes before their birth, or more than 110 years after it, is not one life. They are not drawn, they are named in tree.report.json (conflicts) for
    the research to settle, and every relation to them is removed so the page stays symmetric."""
    bad = {p["id"] for p in t["people"] if p.get("dy") is not None and not 0 <= p["dy"] - p["by"] <= 110}
    if not bad: return []
    conf = [{"id": p["id"], "name": people[byid[p["id"]]]["n"], "born": p["by"], "died": p["dy"]} for p in t["people"] if p["id"] in bad]
    t["people"] = [p for p in t["people"] if p["id"] not in bad]
    for p in t["people"]:
        for k in ("father", "mother"):
            if p.get(k) in bad: p[k] = None
        p["spouse"] = [x for x in p["spouse"] if x not in bad]; p["kids"] = [x for x in p["kids"] if x not in bad]
    if t.get("focus") in bad: t["focus"] = t["people"][0]["id"]
    print("conflicts: %d people whose death is before their birth, or over 110 years after it, are not drawn" % len(bad))
    return conf

def keep_death_place(t, people, fields, byid):
    """The converter takes a later residence as the place of death. A death place the record states and the place map resolves is the place of death."""
    pm = jl(os.path.join(OUT, "place_map.json")); n = 0
    for p in t["people"]:
        df = fields[byid[p["id"]]][1]; r = pm.get(df["place"] or "") if df["event"] != "burial" else None
        if r and r.get("lat") is not None and r.get("name") and r["name"] != p["dp"]: p["dp"] = r["name"]; n += 1
    print("death places: %d put back to the recorded place of death" % n)

def ged_links(path):
    """father, mother, spouses and children of every person in the GEDCOM this build wrote (the same households and marriages the drawn people come from)."""
    famc, fams, fam = {}, collections.defaultdict(list), {}
    cur = None
    for ln in io.open(path, encoding="utf-8"):
        m = re.match(r"0 @(\w+)@ (INDI|FAM)", ln)
        if m: cur = (m.group(1), m.group(2)); fam.setdefault(cur[0], {"h": None, "w": None, "k": []}) if cur[1] == "FAM" else None; continue
        m = re.match(r"1 (FAMC|FAMS|HUSB|WIFE|CHIL) @(\w+)@", ln)
        if not m or not cur: continue
        tag, ref = m.groups()
        if cur[1] == "INDI":
            if tag == "FAMC": famc[cur[0]] = ref
            elif tag == "FAMS": fams[cur[0]].append(ref)
        else:
            if tag == "HUSB": fam[cur[0]]["h"] = ref
            elif tag == "WIFE": fam[cur[0]]["w"] = ref
            elif tag == "CHIL": fam[cur[0]]["k"].append(ref)
    out = {}
    for pid_ in set(famc) | set(fams):
        fa = fam.get(famc.get(pid_), {})
        sp, kids = [], []
        for fx in fams.get(pid_, []):
            r = fam[fx]
            other = r["w"] if r["h"] == pid_ else r["h"]
            if other and other not in sp: sp.append(other)
            kids += [k for k in r["k"] if k not in kids]
        out[pid_] = {"father": fa.get("h"), "mother": fa.get("w"), "spouse": sp, "kids": kids}
    return out

def undrawn_list(people, fields, pid, pages, M, drawn, pm, okp, rep, cx_by_slug=None):
    """EVERY published person the converter did not draw, each with why and with the details the Record Atlas Tree Canvas needs to draw them as an unplaced card: given, sur, sex,
    by / dy, bd / dd, cx, and father / mother / spouse / kids (tree ids, only of people who are themselves in this file, drawn or listed here). `why` is "year" or "place" for a person
    with a recorded death the maps could not place, and "death" for a person with no death recorded (older than the living line, so not living by the estate rule: the 80-year rule
    puts anyone born in the last 80 years with no death into the living list, which is never listed here). A living or held-out person is never listed: they are not in `fields`."""
    out = []; ent = {}
    sexm = {"M": "m", "F": "f"}
    links = ged_links(os.path.join(OUT, "people.ged"))
    for i, (bf, df) in fields.items():
        if pid(i) in drawn: continue
        recorded = bool(lf.death_kind(people[i]))
        yr = re.search(r"\d{4}", bf["year"] or df["year"] or "")
        why = ("year" if not bf["year"] else "place") if recorded else "death"
        e = {"id": pid(i), "name": people[i]["n"], "href": "/people/%s/" % pages[i] if pages[i] else None, "b": int(yr.group(0)) if yr else None,
             "place": bf["place"] or df["place"] or None, "why": why}
        g, sur = split_name(people[i]["n"]); e["given"] = g; e["sur"] = sur; e["sex"] = sexm.get(M["sex"].get(i), "u")
        by = re.search(r"\d{4}", bf["year"] or ""); dy = re.search(r"\d{4}", df["year"] or "")
        if by: e["by"] = int(by.group(0))
        if dy: e["dy"] = int(dy.group(0))
        mb = FULLDATE.match(str(people[i].get("b") or "")); md = FULLDATE.match(str(people[i].get("d") or ""))
        if mb: e["bd"] = mb.group(1)
        if md: e["dd"] = md.group(1)
        if pages[i]:
            e["slug"] = pages[i]; e["page"] = "/people/%s/" % pages[i]
            if cx_by_slug and cx_by_slug.get(pages[i]): e["cx"] = cx_by_slug[pages[i]]
        out.append(e); ent[pid(i)] = e
    here = set(drawn) | set(ent)
    for e in out:
        l = links.get(e["id"], {})
        for k in ("father", "mother"):
            if l.get(k) in here: e[k] = l[k]
        for k in ("spouse", "kids"):
            v = [x for x in l.get(k, []) if x in here]
            if v: e[k] = v
    rep["not_drawn_listed"] = {"with_a_recorded_death": sum(1 for e in out if e["why"] != "death"), "no_death_recorded": sum(1 for e in out if e["why"] == "death")}
    return out

def living_rows(t):
    """The people this archive lists as living, as name-and-family-only rows for the Record Atlas Tree Canvas (David, 17 Nov 2026: what the archive publishes, the Canvas draws; he
    decided this knowing /roots/ is indexed and these pages are noindex). Each row is {id, sex, given, sur, father, mother, spouse, kids, living: true} and NOTHING else: no date, no place,
    no route, no page, no corrections count. The links are the people around them, only those who are themselves in this file. Held-out people (no page, no name anywhere) are never here.
    The page's own views skip these rows (the template's loadTree), and check_tree_page.py allows a living row only with exactly these keys and meta.livingNames set."""
    people, living, held, omitted, hh, marr, sex, pid, sexsrc = build_model()
    here = {p["id"] for p in t["people"]} | {u["id"] for u in t["undrawn"]} | {pid(i) for i in living}
    rows = []
    for i in sorted(living):
        if i in held: continue
        g, sur = split_name(people[i]["n"])
        father = mother = None; spouse = []; kids = []
        for h, w, ks, _via in hh:
            if i in [k for k, _ in ks]:
                father = father or (pid(h) if h is not None and h not in held else None); mother = mother or (pid(w) if w is not None and w not in held else None)
            if i == h and w is not None and w not in held: spouse.append(pid(w))
            if i == w and h is not None and h not in held: spouse.append(pid(h))
            if i in (h, w): kids += [pid(k) for k, _ in ks if k is not None and k not in held]
        for h, w in marr:
            if i == h and w not in held and pid(w) not in spouse: spouse.append(pid(w))
            if i == w and h not in held and pid(h) not in spouse: spouse.append(pid(h))
        row = {"id": pid(i), "sex": {"M": "m", "F": "f"}.get(sex.get(i), "u"), "given": g, "sur": sur, "living": True}
        if father in here: row["father"] = father
        if mother in here: row["mother"] = mother
        sp = [x for x in dict.fromkeys(spouse) if x in here]; ks_ = [x for x in dict.fromkeys(kids) if x in here]
        if sp: row["spouse"] = sp
        if ks_: row["kids"] = ks_
        rows.append(row)
    return rows

def write_roots_links(tree):
    """site/public/roots-links.json: the people Roots & Routes DRAWS, by tree id (P<position in people.json + 1>). A person's page offers 'Where they lived' only for those,
    and only a page that is a story (a living person is never drawn here, and their page is never a story)."""
    ids = sorted((p["id"] for p in jl(tree)["people"] if not p.get("living")), key=lambda x: int(x[1:]))
    out = {"note": "The people Roots & Routes draws, by tree id (P plus the person's position in people.json, from 1). Made by tools/build-tree-page.py; do not edit by hand.", "people": ids}
    io.open(os.path.join(ROOT, "site", "public", "roots-links.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("roots-links: %d people" % len(ids))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true"); ap.add_argument("--accept-unique", action="store_true")
    a = ap.parse_args()
    if a.check:
        try: have = jl(os.path.join(OUT, "tree.json"))["meta"]["inputs"]
        except Exception: print("tree page: not built yet. python3 tools/build-tree-page.py"); sys.exit(1)
        if have != inputs_hash(): print("tree page is STALE: the people, households, marriages, living list, place map or builder changed since it was built.\n  python3 tools/build-tree-page.py"); sys.exit(1)
        print("tree page is current"); return
    build(a)
    tree = os.path.join(OUT, "tree.json"); pm = os.path.join(OUT, "place_map.json"); ad = os.path.join(OUT, "atlas-data.json"); page = os.path.join(OUT, "roots.html")
    run([sys.executable, os.path.join(TP, "build_atlas_data.py"), "--atlas", atlas_path(), "--tree", tree, "--place-map", pm, "--out", ad])
    t = jl(tree); t["meta"]["inputs"] = inputs_hash()
    io.open(tree, "w", encoding="utf-8").write(json.dumps(t, ensure_ascii=False, separators=(",", ":")))
    tpl = os.path.join(TP, "tree-views.template.html")
    run([sys.executable, os.path.join(TP, "build_page.py"), "--template", tpl, "--tree", tree, "--atlas-data", ad, "--out", page, "--ext", EXT])
    embed = os.path.join(OUT, "roots.embed.html")
    run([sys.executable, os.path.join(TP, "build_page.py"), "--template", tpl, "--tree", tree, "--atlas-data", ad, "--out", embed, "--embed", "--ext", EXT])
    run([sys.executable, os.path.join(TP, "check_tree_page.py"), "--tree", tree, "--atlas-data", ad, "--page", page])
    run([sys.executable, os.path.join(TP, "check_tree_page.py"), "--tree", tree, "--atlas-data", ad, "--page", embed])
    write_roots_links(tree)

if __name__ == "__main__": main()
