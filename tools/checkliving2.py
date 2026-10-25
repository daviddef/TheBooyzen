#!/usr/bin/env python3
"""The living-people standard, version 2 (16 October 2026): the gate.

    python3 tools/checkliving2.py --dist dist --data src/data          # the build step
    python3 tools/checkliving2.py --dist dist --data src/data --selftest   # plants faults

WHAT IT ENFORCES, AND WHAT IT DELIBERATELY DOES NOT SHARE WITH THE GENERATOR.
Who is living is computed HERE, from people.json and kin.js, with the kit's own
kit/tools/living_rule.py - and not by importing tools/livingflags.py, whose answer is
what the site was built from. The two are then compared. A gate that read the
generator's answer could only ever agree with it.

  R0  refuses an empty build: no pages, no people, no roster computed.
  R1  the roster computed here equals living.json, the one the pages were built from.
  R2  a living person's data shows a name, a line and a town and country, and nothing
      else: no date, note, page link, citation, generation; their dossier holds no
      excerpt, page or mention; the place is "Town, Country" and not a street or an
      institution.
  R3  no data file puts a date beside a living person's name.
  R4  a living person's pages (/people/<slug>/, /who/<slug>/) exist, are noindex, are not
      in the sitemap or the search index, and carry no Person JSON-LD, table, image, or
      year. A name page whose every bearer is living is noindex too.
  R5  no page of the site puts a date beside a living person's name.
  R6  held out means absent: nobody the rule holds out (a possible minor, or listed by id
      in living-policy.json) is in the data, a page, a link, or an index.
  R7  every person this archive names has a page: each household, marriage and place
      reference resolves, each person has /people/ and /who/ pages, and every link to one
      lands.
  R8  the footer counts the living honestly, and the standard's sentence is on /about/,
      /method/ and in the footer.
  R9  a living person has no row in the register.

--selftest plants one fault for every rule above in an in-memory copy and shows that this
gate fails on it, and that the untouched copy passes. A check that can only pass proves
nothing.

Messages name pages by URL and people by position, never by name.
"""
import argparse
import copy
import html
import json
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(HERE, "site")
KIT = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit")
sys.path.insert(0, os.path.join(KIT, "tools"))
import living_rule as lr  # noqa: E402

STANDARD = ("A living person (80 or younger, with no death recorded) is named with their "
            "relationships and their town and country, and nothing more.")
SAID = {w.lower() for w in json.load(open(os.path.join(KIT, "data", "living-words.json"),
                                          encoding="utf-8"))["saidLiving"]}
YEAR_RE = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")
SHOWN_KEYS = {"n", "b", "d", "l", "s", "r", "p", "w"}
PLACE_BAD = re.compile(r"\b(street|st\.?|road|rd\.?|avenue|ave\.?|lane|drive|dr\.?|hospital|clinic|"
                       r"care|home|nursing|hostel|prison|school|university|college|mission|farm|"
                       r"estate|park|house|po box|box)\b", re.I)


# ---------------------------------------------------------------- the rule, read here

def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ÿ", "y").replace("Ÿ", "Y")
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()[:60]


def by_of(p):
    m = re.search(r"\b(1\d{3}|20\d\d)\b", str(p.get("b") or ""))
    return int(m.group(1)) if m else None


def kind_of(p):
    """The kit's own classification of the `d` field: "record", "flag" (the bare word) or None."""
    d = str(p.get("d") or "").strip()
    return None if d.lower() in SAID else lr.death_kind(died=d)


def dead_of(p):
    """A death RECORD. The bare word `deceased` is a flag, not a record (kit 341af33)."""
    return kind_of(p) == "record"


def flag_of(p):
    return kind_of(p) == "flag"


def stated(p):
    return (str(p.get("b") or "").strip().lower() in SAID
            or str(p.get("d") or "").strip().lower() in SAID)


def roster(w):
    """-> (living indexes, held-out indexes), by the kit's rule alone."""
    people, y = w["people"], w["year"]
    living = []
    for i, p in enumerate(people):
        cites = [str(c) for c in (p.get("c") or [])]
        if dead_of(p):
            continue
        if stated(p) or lr.is_living(by_of(p), False, cites, y, undated_dead=flag_of(p)):
            living.append(i)
    liv = set(living)
    parents = {}
    for f in w["fams"]:
        ps = [res(f.get("h"), people), res(f.get("w"), people)]
        for k in f.get("kids", []):
            ki = res(k["n"], people)
            if ki is not None:
                parents.setdefault(ki, set()).update(x for x in ps if x is not None)
    held = []
    pol = w["policy"]
    for i, p in enumerate(people):
        s = slug(p["n"])
        if s in pol.get("author", []):
            continue
        cites = [str(c) for c in (p.get("c") or [])]
        if lr.is_held_out(s, by_of(p), dead_of(p), cites, any(q in liv for q in parents.get(i, ())),
                          pol.get("heldOut", []), y, undated_dead=flag_of(p)):
            held.append(i)
    return living, held


def res(ref, people):
    if not ref:
        return None
    name, _, tok = ref.partition("|")
    hits = [i for i, p in enumerate(people) if p["n"] == name]
    if tok:
        hits = [i for i in hits if tok in (people[i].get("b") or "") or tok in (people[i].get("d") or "")]
    return hits[0] if hits else None


# ---------------------------------------------------------------- reading a build

def main_text(raw):
    m = re.search(r"<main\b.*?</main>", raw, re.S | re.I)
    return m.group(0) if m else raw


def visible(raw):
    s = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", raw)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def families(data):
    code = ("import('" + os.path.join(data, "kin.js") + "').then(m=>"
            "process.stdout.write(JSON.stringify(m.families)))")
    return json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True,
                                     check=True).stdout)


def load_world(dist, data):
    import datetime
    j = lambda f: json.load(open(os.path.join(data, f), encoding="utf-8"))
    w = {"year": datetime.date.today().year, "dist": dist, "data": data}
    w["people"] = j("people.json")["people"]
    w["fams"] = families(data)
    w["policy"] = j("living-policy.json")
    w["livingjson"] = j("living.json")
    w["dossiers"] = j("dossiers.json")["people"]
    w["marriages"] = j("marriages.json")["rows"]
    w["places"] = j("places.json")["places"]
    w["timeline"] = j("timeline.json")["events"]
    reg = os.path.join(data, "register.json")
    w["register"] = json.load(open(reg, encoding="utf-8"))["rows"] if os.path.exists(reg) else []
    pages = {}
    for root, _dirs, files in os.walk(dist):
        for f in files:
            if f == "index.html":
                route = "/" + os.path.relpath(root, dist).replace(os.sep, "/") + "/"
                route = "/" if route == "/./" else route
                pages[route] = open(os.path.join(root, f), encoding="utf-8").read()
    if os.path.exists(os.path.join(dist, "404.html")):
        pages["/404.html"] = open(os.path.join(dist, "404.html"), encoding="utf-8").read()
    w["pages"] = pages
    rd = lambda f: open(os.path.join(dist, f), encoding="utf-8").read() if os.path.exists(os.path.join(dist, f)) else ""
    w["sitemap"] = rd("sitemap.xml")
    w["served"] = {f: rd(f) for f in ("searchindex.json", "whoindex.json", "sitemap.xml")}
    try:
        w["search"] = json.loads(rd("searchindex.json") or "[]")
    except ValueError:
        w["search"] = None
    try:
        w["whoindex"] = json.loads(rd("whoindex.json") or "[]")
    except ValueError:
        w["whoindex"] = None
    w["tracked"] = tracked_texts(HERE)
    w["datatext"] = {}
    for f in sorted(os.listdir(data)):
        if f.endswith((".json", ".js")) and f not in ("living.json", "living-policy.json", "decisions.json"):
            w["datatext"][f] = open(os.path.join(data, f), encoding="utf-8").read()
    return w


# ---------------------------------------------------------------- the checks

def name_dated(text, name):
    """A date written directly after a living person's name, three ways it is written:
    Name (b. 1799) - Name, born 1799 - Name<TAB>12 Mar 1799 (a table column)."""
    n = re.escape(name) + r"(?:['’]s)?"
    day = r"(?:\d{1,2}\s+[A-Z][a-z]+\s+)?"
    y = YEAR_RE.pattern
    pats = (n + r"\s*[(\[]\s*(?:b\.|born|d\.|died|c\.)?\s*(?:c\.\s*)?" + day + y,
            n + r",?\s*(?:b\.|born|d\.|died)\s*(?:c\.\s*)?" + day + y,
            n + r"\t+" + day + y)
    return any(re.search(p, text, re.I) for p in pats)


TEXT_EXT = (".tsv", ".md", ".json", ".js", ".mjs", ".astro", ".py", ".txt", ".csv", ".sh", ".yml")


def tracked_texts(root):
    """Every file git tracks or would add (untracked and not ignored): a gate that reads
    only committed files cannot see the one that is about to be."""
    out = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard"],
                         capture_output=True, text=True)
    texts = {}
    for rel in out.stdout.splitlines():
        if not rel.endswith(TEXT_EXT) or rel.startswith(("site/public/docs/", "sources/")):
            continue
        fp = os.path.join(root, rel)
        try:
            if os.path.getsize(fp) > 30_000_000:
                continue
            texts[rel] = open(fp, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
    return texts


def check(w):
    """-> list of (rule, message). Empty means the build passes."""
    bad = []
    add = lambda r, m: bad.append((r, m))
    people, pages = w["people"], w["pages"]
    # R0
    if not pages or len(pages) < 50:
        add("R0", f"only {len(pages)} built page(s): the build is empty or unfinished, refusing to pass")
    if not people:
        add("R0", "people.json holds nobody: refusing to pass over an empty archive")
    if not w["sitemap"].strip():
        add("R0", "no sitemap.xml was built")
    if w["search"] is None or not w["search"]:
        add("R0", "searchindex.json is missing, empty or unreadable")
    if not people or not pages:
        return bad
    living, held = roster(w)
    live_slugs = [slug(people[i]["n"]) for i in living]
    # R1
    listed = {x["slug"] for x in w["livingjson"]["living"]}
    if set(live_slugs) != listed:
        add("R1", f"the kit's rule finds {len(live_slugs)} living, living.json (what the pages were built "
                  f"from) lists {len(listed)}; {len(set(live_slugs) ^ listed)} differ. Run tools/livingflags.py "
                  "and rebuild")
    # R2
    for k, i in enumerate(living, 1):
        p, s = people[i], slug(people[i]["n"])
        where = f"living person #{k} of {len(living)} (/people/{s}/)"
        extra = set(p) - SHOWN_KEYS
        if extra:
            add("R2", f"{where}: data carries field(s) {sorted(extra)}")
        if p.get("b") != "living" or p.get("d") not in ("—", "living"):
            add("R2", f"{where}: b/d hold something other than the word living: a public file may not carry a living person's date")
        if p.get("r") or p.get("p"):
            add("R2", f"{where}: carries notes or page links")
        if p.get("c"):
            add("R2", f"{where}: carries citations")
        pl = p.get("w") or ""
        if pl and (not re.fullmatch(r"[^,\d]+, [^,\d]+", pl) or PLACE_BAD.search(pl)):
            add("R2", f"{where}: the place is not a plain 'Town, Country' (a street, an address-like string or an institution is not a town)")
        dz = w["dossiers"].get(s)
        if dz is None:
            add("R2", f"{where}: has no dossier entry, so no page is built")
        else:
            if dz.get("hits") or dz.get("pages") or dz.get("r") or dz.get("p") or dz.get("also") \
                    or not isinstance(dz.get("mentions", 0), int):
                add("R2", f"{where}: the dossier holds excerpts, pages or notes (a count of mentions is all it may hold)")
            if set(dz) - (SHOWN_KEYS | {"slug", "mentions", "pages", "hits", "shared", "also"}):
                add("R2", f"{where}: the dossier carries extra field(s)")
    # R3: no file in the repository, and no served data file, puts a date beside a living name
    names = [people[i]["n"] for i in living]
    for fn, txt in list(w["tracked"].items()) + [("dist/" + f, t) for f, t in w["served"].items()]:
        for k, nm in enumerate(names, 1):
            if name_dated(txt, nm):
                add("R3", f"{fn}: a date is written beside living person #{k}")
    # R4
    sm = w["sitemap"]
    index_hrefs = {r.get("h") for r in (w["search"] or []) if isinstance(r, dict)}
    for k, s in enumerate(live_slugs, 1):
        for route in (f"/people/{s}/", f"/who/{s}/"):
            raw = pages.get(route)
            if raw is None:
                add("R4", f"{route}: living person #{k} has no built page")
                continue
            if not re.search(r'<meta name="robots" content="[^"]*noindex', raw):
                add("R4", f"{route}: a living person's page is not noindex")
            if f"{route}</loc>" in sm or re.search(r"<loc>[^<]*" + re.escape(route) + r"</loc>", sm):
                add("R4", f"{route}: a living person's page is in the sitemap")
            if route in index_hrefs:
                add("R4", f"{route}: a living person's page is in the search index")
            if "application/ld+json" in raw:
                add("R4", f"{route}: carries structured data")
            if "og:image" in raw or 'rel="canonical"' in raw:
                add("R4", f"{route}: carries an image or canonical link in its head")
            m = main_text(raw)
            if re.search(r"<(table|img|svg|picture|canvas|video)\b", m, re.I):
                add("R4", f"{route}: shows a table or an image")
            if YEAR_RE.search(visible(m)):
                add("R4", f"{route}: shows a year")
        # the search index must hold no row about them at all, under any href
    for k, r in enumerate(w["search"] or [], 0):
        if isinstance(r, dict) and r.get("k") == "Person" and (r.get("h") or "").strip("/").split("/")[-1] in live_slugs:
            add("R4", f"search index row {k}: a Person row for a living person")
    # R5
    own_pages = {f"/people/{s}/" for s in live_slugs}
    for route, raw in pages.items():
        if route in own_pages:
            continue
        txt = visible(main_text(raw))
        for k, nm in enumerate(names, 1):
            if nm in txt and name_dated(txt, nm):
                add("R5", f"{route}: a date is written beside living person #{k}")
    # R6
    if held:
        add("R6", f"{len(held)} person(s) the rule holds out (possible minor, or listed by id) are in people.json: "
                  "held out means absent from every file and page")
    for hs in w["policy"].get("heldOut", []):
        for route in (f"/people/{hs}/", f"/who/{hs}/"):
            if route in pages:
                add("R6", f"{route}: a person held out by id has a built page")
        for route, raw in pages.items():
            if f"/people/{hs}/" in raw or f"/who/{hs}/" in raw:
                add("R6", f"{route}: links to a person held out by id")
        for fn, txt in w["datatext"].items():
            if hs in txt:
                add("R6", f"data file {fn}: mentions a person held out by id")
        if any(slug(p["n"]) == hs for p in people):
            add("R6", "people.json holds a person held out by id")
        if any(hs in json.dumps(r) for r in (w["search"] or [])):
            add("R6", "the search index mentions a person held out by id")
    if set(w["livingjson"].get("heldOut", [])) != set(w["policy"].get("heldOut", [])):
        add("R6", "living.json and living-policy.json disagree on who is held out")
    # R7
    unresolved = 0
    for f in w["fams"]:
        for ref in [f.get("h"), f.get("w")] + [k["n"] for k in f.get("kids", [])]:
            if ref and res(ref, people) is None:
                unresolved += 1
    for r in w["marriages"]:
        for ref in (r.get("h"), r.get("w")):
            if ref and res(ref, people) is None:
                unresolved += 1
    allnames = {p["n"] for p in people}
    for ev in w.get("timeline", []):
        for n in ev.get("p") or []:
            if n not in allnames:
                unresolved += 1
    for pl in w["places"]:
        for n in pl.get("p", []) or []:
            if n not in allnames:
                unresolved += 1
    if unresolved:
        add("R7", f"{unresolved} person reference(s) in households, marriages or places name nobody in people.json: a name with no page")
    for p in people:
        s = slug(p["n"])
        for route in (f"/people/{s}/", f"/who/{s}/"):
            if route not in pages:
                add("R7", f"{route}: a person in people.json has no built page")
                break
    link = re.compile(r'href="(/(?:people|who)/[^"#?]+/)"')
    seen = set()
    for route, raw in pages.items():
        for h in link.findall(raw):
            if h not in pages and (route, h) not in seen:
                seen.add((route, h))
                add("R7", f"{route}: links to {h}, which is not a built page")
    # R8
    home = visible(pages.get("/", ""))
    foot = re.search(r"<footer.*?</footer>", pages.get("/", ""), re.S)
    ftxt = visible(foot.group(0)) if foot else ""
    n = len(living)
    want = ("This archive holds none." if n == 0 else
            "One person here is living." if n == 1 else f"{n} people here are living.")
    if want not in " ".join(ftxt.split()):
        add("R8", f"the footer does not say '{want}': it miscounts the living")
    for route in ("/", "/about/", "/method/"):
        if STANDARD not in " ".join(visible(pages.get(route, "")).split()):
            add("R8", f"{route}: the standard's sentence is not on the page")
    # R9
    names_l = {x.lower() for x in names}
    for k, r in enumerate(w["register"]):
        if (r.get("n") or "").lower() in names_l or (r.get("p") or "") in live_slugs:
            add("R9", f"register row {k}: a row names or links a living person")
    return bad


# ---------------------------------------------------------------- the planted faults

def selftest(w):
    ok = True
    base = check(w)
    print(f"  control: the untouched build -> {len(base)} finding(s)" + ("" if not base else "  <-- SHOULD BE 0"))
    if base:
        for r, m in base[:8]:
            print(f"      {r}: {m}")
        ok = False
    living, _held = roster(w)
    if not living:
        print("  no living person to plant against: refusing")
        return False
    i0 = living[0]
    s0 = slug(w["people"][i0]["n"])
    nm0 = w["people"][i0]["n"]
    route0 = f"/people/{s0}/"
    who0 = f"/who/{s0}/"
    Y = w["year"]
    # a value no living person can have, and one that makes somebody living by age without
    # being any real person's: computed, never typed
    PLANT_DEAD_YEAR = 1799

    def fresh():
        v = dict(w)
        v["people"] = copy.deepcopy(w["people"])
        v["fams"] = copy.deepcopy(w["fams"])
        v["policy"] = copy.deepcopy(w["policy"])
        v["livingjson"] = copy.deepcopy(w["livingjson"])
        v["dossiers"] = copy.deepcopy(w["dossiers"])
        v["register"] = copy.deepcopy(w["register"])
        v["search"] = copy.deepcopy(w["search"])
        v["pages"] = dict(w["pages"])
        v["datatext"] = dict(w["datatext"])
        v["tracked"] = dict(w["tracked"])
        v["served"] = dict(w["served"])
        v["marriages"] = copy.deepcopy(w["marriages"])
        v["places"] = copy.deepcopy(w["places"])
        v["timeline"] = copy.deepcopy(w["timeline"])
        return v

    faults = []

    def fault(code, label):
        def deco(fn):
            faults.append((code, label, fn))
            return fn
        return deco

    @fault("R0", "an empty build (no pages)")
    def _(v): v["pages"] = {}

    @fault("R0", "an empty archive (no people)")
    def _(v): v["people"] = []

    @fault("R0", "no sitemap")
    def _(v): v["sitemap"] = ""

    @fault("R1", "someone recorded dead who living.json still lists as living")
    def _(v): v["people"][i0]["d"] = f"12 Mar {PLANT_DEAD_YEAR}"

    @fault("R1", "a planted person born inside the bound whom living.json does not list")
    def _(v): v["people"].append({"n": "Qwxz Plantfault", "b": f"{Y - 30}", "d": "—", "l": "Booyzen", "s": "lore", "r": "", "p": []})

    @fault("R1", "the 80-year bound moved to 100: a person who is not living by the real bound")
    def _(v):
        v["people"].append({"n": "Qwxz Oldfault", "b": f"{Y - 90}", "d": "—", "l": "Booyzen", "s": "lore", "r": "", "p": []})
        v["_bound"] = 100

    @fault("R2", "a living person's entry gains a note")
    def _(v): v["people"][i0]["r"] = "A note about them."

    @fault("R2", "a living person's entry gains a page link")
    def _(v): v["people"][i0]["p"] = [["The Rebels", "/rebels/"]]

    @fault("R2", "a living person's entry gains a citation")
    def _(v): v["people"][i0]["c"] = ["a private tree entry"]

    @fault("R2", "a living person's place is a street")
    def _(v): v["people"][i0]["w"] = "12 High Street, Testtown"

    @fault("R2", "a living person's place is a hospital")
    def _(v): v["people"][i0]["w"] = "Testtown General Hospital, Testland"

    @fault("R2", "a living person's dossier keeps an excerpt")
    def _(v): v["dossiers"][s0]["hits"] = [{"page": "/x/", "title": "x", "text": "an excerpt"}]

    @fault("R2", "a living person's entry carries a date")
    def _(v): v["people"][i0]["b"] = "living"; v["people"][i0]["gen"] = 3

    @fault("R3", "a data file puts a date beside a living name")
    def _(v): v["tracked"]["site/src/data/questions.json"] = v["tracked"].get("site/src/data/questions.json", "") + f" {nm0} (b. {PLANT_DEAD_YEAR}) "

    @fault("R3", "the served search index carries a birth date beside a living name")
    def _(v): v["served"]["searchindex.json"] = v["served"]["searchindex.json"] + f' "q": "{nm0.lower()} (b. {PLANT_DEAD_YEAR})"'

    @fault("R3", "a tab-separated data file puts a birth date in a living person's row")
    def _(v): v["tracked"]["data/direct-line.tsv"] = v["tracked"].get("data/direct-line.tsv", "") + f"\n1\t{nm0}\t12 Oct {PLANT_DEAD_YEAR}\tTesttown\n"

    @fault("R3", "a note puts 'born' and a year beside a living name")
    def _(v): v["tracked"]["notes/x.md"] = f"{nm0}, born {PLANT_DEAD_YEAR}, is living."

    @fault("R4", "a living page lacks noindex")
    def _(v): v["pages"][route0] = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', "", v["pages"][route0])

    @fault("R4", "a living name page lacks noindex")
    def _(v): v["pages"][who0] = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', "", v["pages"][who0])

    @fault("R4", "a living page is in the sitemap")
    def _(v): v["sitemap"] += f"<url><loc>https://example.test{route0}</loc></url>"

    @fault("R4", "a living page is in the search index")
    def _(v): v["search"].append({"k": "Page", "t": "x", "s": route0, "h": route0, "q": "x"})

    @fault("R4", "a living person has a Person row in the search index")
    def _(v): v["search"].append({"k": "Person", "t": "x", "s": "x", "h": who0, "q": "x"})

    @fault("R4", "a living page carries JSON-LD")
    def _(v): v["pages"][route0] = v["pages"][route0].replace("</head>", '<script type="application/ld+json">{"@type":"Person"}</script></head>', 1)

    @fault("R4", "a living page carries a table")
    def _(v): v["pages"][route0] = v["pages"][route0].replace("</main>", "<table><tr><td>x</td></tr></table></main>", 1)

    @fault("R4", "a living page carries an image")
    def _(v): v["pages"][route0] = v["pages"][route0].replace("</main>", '<img src="/x.jpg" alt=""></main>', 1)

    @fault("R4", "a living page shows a year")
    def _(v): v["pages"][route0] = v["pages"][route0].replace("</main>", f"<p>Born {PLANT_DEAD_YEAR}</p></main>", 1)

    @fault("R4", "a living page is missing")
    def _(v): del v["pages"][route0]

    @fault("R5", "a prose page puts a birth year beside a living name")
    def _(v): v["pages"]["/direct-line/"] = v["pages"]["/direct-line/"].replace("</main>", f"<p>{nm0} (b. {PLANT_DEAD_YEAR}) is living.</p></main>", 1)

    @fault("R6", "a possible minor is in the data")
    def _(v): v["people"].append({"n": "Qwxz Minorfault", "b": f"{Y - 5}", "d": "—", "l": "Booyzen", "s": "lore", "r": "", "p": []})

    @fault("R6", "an undated person with a living parent is in the data")
    def _(v):
        v["people"].append({"n": "Qwxz Childfault", "b": "—", "d": "—", "l": "Booyzen", "s": "lore", "r": "", "p": []})
        v["fams"].append({"h": nm0, "w": None, "via": "tree", "kids": [{"n": "Qwxz Childfault", "via": "tree"}]})

    @fault("R6", "a person held out by id has a page")
    def _(v):
        v["policy"]["heldOut"] = ["qwxz-heldfault"]
        v["pages"]["/people/qwxz-heldfault/"] = "<html><main>x</main></html>"

    @fault("R6", "a page links to a person held out by id")
    def _(v):
        v["policy"]["heldOut"] = ["qwxz-heldfault"]
        v["pages"]["/about/"] = v["pages"]["/about/"].replace("</main>", '<a href="/who/qwxz-heldfault/">x</a></main>', 1)

    @fault("R7", "a household names someone with no page")
    def _(v): v["fams"].append({"h": "Qwxz Nopagefault", "w": None, "via": "tree", "kids": []})

    @fault("R7", "a marriage names someone with no page")
    def _(v): v["marriages"].append({"h": "Qwxz Nopagefault", "w": None})

    @fault("R7", "a place names someone with no page")
    def _(v): v["places"][0].setdefault("p", []).append("Qwxz Nopagefault")

    @fault("R7", "a timeline event names someone with no page")
    def _(v): v["timeline"][0].setdefault("p", []).append("Qwxz Nopagefault")

    @fault("R7", "a person has no built page")
    def _(v):
        v["people"].append({"n": "Qwxz Unbuiltfault", "b": "—", "d": "—", "l": "Booyzen", "s": "doc", "r": "x", "p": []})

    @fault("R7", "a link to a person page that does not exist")
    def _(v): v["pages"]["/about/"] = v["pages"]["/about/"].replace("</main>", '<a href="/who/qwxz-nowherefault/">x</a></main>', 1)

    @fault("R8", "the footer says the archive holds none")
    def _(v): v["pages"]["/"] = re.sub(r"\d+ people here are living\.|One person here is living\.", "This archive holds none.", v["pages"]["/"])

    @fault("R8", "the standard's sentence is missing from /method/")
    def _(v): v["pages"]["/method/"] = v["pages"]["/method/"].replace("named with their relationships", "named")

    @fault("R9", "a living person has a register row")
    def _(v): v["register"].append({"n": nm0, "g": "OTHER NAMES", "w": "—", "s": "x", "k": "read", "u": "", "p": s0})

    caught = 0
    for code, label, fn in faults:
        v = fresh()
        saved = lr.LIVING_YEARS
        try:
            fn(v)
            if v.get("_bound"):
                lr.LIVING_YEARS = v["_bound"]
            out = check(v)
        finally:
            lr.LIVING_YEARS = saved
        got = sorted({r for r, _ in out})
        hit = code in got
        caught += hit
        print(f"  {'caught ' if hit else 'MISSED '} {code}  {label}" + ("" if hit else f"   (saw {got or 'nothing'})"))
        ok = ok and hit
    print(f"  {caught} of {len(faults)} planted faults caught, and the control passes" if ok else
          f"  {caught} of {len(faults)} planted faults caught: THE GATE HAS A HOLE")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--data", default="src/data")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    dist = os.path.join(SITE, a.dist) if not os.path.isabs(a.dist) else a.dist
    data = os.path.join(SITE, a.data) if not os.path.isabs(a.data) else a.data
    if not os.path.isdir(dist):
        print(f"  FAIL  living2  no build at {dist}")
        sys.exit(1)
    w = load_world(dist, data)
    if a.selftest:
        sys.exit(0 if selftest(w) else 1)
    bad = check(w)
    living, held = roster(w) if w["people"] else ([], [])
    if bad:
        print(f"  FAIL  living2  {len(bad)} finding(s) against the living-people standard v2")
        for r, m in bad[:40]:
            print(f"        {r}  {m}")
        if len(bad) > 40:
            print(f"        ... and {len(bad) - 40} more")
        sys.exit(1)
    print(f"  ok    living2  {len(w['pages'])} pages · {len(w['people'])} people · {len(living)} living "
          f"(each noindex, out of the sitemap and the search index, no JSON-LD, table, image or year; "
          f"a name, relationships and a town and country only) · {len(held)} held out · "
          f"every named person has a page")


if __name__ == "__main__":
    main()
