/* A FAMILY PAGE, DRAWN FROM WHAT THE ARCHIVE ALREADY HOLDS AND FROM NOTHING ELSE.

   This archive had two family pages, /barry/ and /kolbe/, and both are hand-built
   narratives. Eleven names are filed as lines in people.json and a dozen more are the
   surnames of direct-line ancestors, so most of the families the archive has researched
   had no page at all. This module is what lets one template draw all of them.

   NOTHING HERE IS WRITTEN BY HAND ABOUT A FAMILY. Every figure and every sentence the
   pages print is computed from five files the research owner already keeps:

     people.json     who the archive names, with the dates exactly as it prints them, the
                     line (`l`) it filed each person on, and the grade (`s`)
     kin.js          the households: who married whom, who the children were, and on whose
                     word (`via`)
     pedigree.json   the ancestors of the chart's starting point, which is how a family is
                     known to be on the direct line
     places.json     the places that name their people
     register.json   the register's rows, to say how many rows are filed under a name

   AND IT DECIDES NOTHING THE ARCHIVE HAS NOT. Who is living is living.json's answer
   (tools/livingflags.py, on the kit's living_rule.py); this file asks it and never tests
   a date. A name is "carried" by the same grouping namefold.json already makes, which is
   a search rule and merges no person: where the archive has not connected two people of
   one name, nothing here connects them. Every person row is kept as its own row - the
   three pages that hold more than one person of one name keep each of them separately,
   with their own dates.
*/
import P from "../data/people.json";
import D from "../data/dossiers.json";
import NF from "../data/namefold.json";
import PL from "../data/places.json";
import REG from "../data/register.json";
import PED from "../data/pedigree.json";
import FAM from "../data/families.json";
import { families as HOUSEHOLDS } from "../data/kin.js";
import { resolve } from "./kin.js";
import { livingBySlug } from "./living.js";
import { plain } from "@daviddef/archive-kit/lib/md.js";

export const registry = FAM.families;
export const hrefOf = (f) => f.page || `/families/${f.slug}/`;

const norm = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/* namefold.json maps a variant to a target and sometimes a target to a further one
   (montjoÿ -> montjoy -> mountjoy); follow it to the end. */
const FOLD = {};
/* a diacritic folds away on both sides (montjoÿ and montjoy are one key once accents go), so a
   key that maps to itself must never overwrite the one that maps somewhere */
for (const [k, v] of Object.entries(NF.fold)) { const a = norm(k), b = norm(v); if (a !== b) FOLD[a] = b; }
const canon = (k) => { let x = norm(k), n = 0; while (FOLD[x] && FOLD[x] !== x && n++ < 6) x = FOLD[x]; return x; };

/* The surname a name ends in. The archive writes a place or a year after a name to tell
   two people of one name apart ("Willem Hermanus Booyzen of Indwe", "Catherine Mary
   Sophia Barry of 1871"), a married woman's birth name after "born", a father and a son
   with a numeral, and a nickname in quotes. None of those is part of the surname. */
export function surnameOf(n) {
  const s = String(n ?? "")
    .replace(/\s+of\s+(\d{4}|[A-Z][\w'’\- ]*)$/, "")
    .replace(/\s*\(.*?\)/g, "")
    .replace(/\s+born\s+\S+$/i, "")
    .replace(/\s+the\s+(younger|elder)$/i, "")
    .replace(/\s+(I|II|III)$/, "")
    .trim().split(/\s+/);
  return s[s.length - 1] || "";
}
/* The same, with the particles the archive keeps in front of it ("de Beer", "van der Merwe"),
   for printing the name as written. */
export function surnameFull(n) {
  const s = String(n ?? "")
    .replace(/\s+of\s+(\d{4}|[A-Z][\w'’\- ]*)$/, "")
    .replace(/\s*\(.*?\)/g, "")
    .replace(/\s+born\s+\S+$/i, "")
    .replace(/\s+the\s+(younger|elder)$/i, "")
    .replace(/\s+(I|II|III)$/, "")
    .trim();
  const m = s.match(/((?:(?<![\p{L}])(?:van|von|de|du|der|den|ten|te)\s+)*\S+)$/iu);
  return m ? m[1] : surnameOf(n);
}
/* "born Mountjoy", "geboren Dormehl", "gebooren Oliefier": the family a married woman
   was born into, where the archive records it in the field of variant spellings. */
const BORN = /(?:born|geboren|gebore|gebooren)\s+(?:(?:van|von|de|du|der|den|ten)\s+)*([A-Za-zÀ-ÿ'’\-]+)/gi;
export function bornInto(v) {
  const out = [];
  for (const m of String(v ?? "").matchAll(BORN)) out.push(m[1]);
  return out;
}

/* ---- people: one row per person the archive names, never merged ---- */
const dossiers = Object.values(D.people);
const hostOf = (p) => dossiers.find((x) => x.n === p.n || (x.also || []).some((a) => a.n === p.n && a.b === p.b));
const keyOf = (p) => p.n + "|" + (p.b || "");
export const rows = P.people.map((p) => {
  const host = hostOf(p);
  const slug = host ? host.slug : "";
  const lv = slug ? livingBySlug(slug) : null;
  return { p, slug, living: !!lv, where: lv ? (lv.w || "") : "", shared: host ? !!host.shared : false, key: keyOf(p) };
});
const byKey = new Map();
for (const r of rows) if (!byKey.has(r.key)) byKey.set(r.key, r);
export const rowOf = (ref) => {
  const x = resolve(ref);
  return x && !x.missing ? byKey.get(x.key) || null : null;
};

const YR = /\b(1[5-9]\d\d|20\d\d)\b/g;
const years = (r) => (r.living ? [] : [r.p.b, r.p.d].flatMap((f) => (String(f ?? "").match(YR) || []).map(Number)));
const firstYear = (r) => (years(r)[0] ?? 9999);

/* ---- which family a name belongs to ---- */
function keysOf(f) {
  const ks = new Set();
  for (const t of f.fold) {
    const c = canon(t);
    ks.add(c);
    for (const k of Object.keys(FOLD)) if (canon(k) === c) ks.add(k);
  }
  return ks;
}
const KEYS = new Map(registry.map((f) => [f.slug, keysOf(f)]));
const carries = (r, f) => {
  const ks = KEYS.get(f.slug);
  if (ks.has(canon(surnameOf(r.p.n)))) return true;
  return bornInto(r.p.v).some((b) => ks.has(canon(b)));
};
/* Which registered family a person is of, for the "other family" column of a marriage:
   the family a woman was born into where the archive says so, else the name she carries. */
export function familyOfRow(r) {
  for (const b of bornInto(r.p.v)) {
    const f = registry.find((x) => KEYS.get(x.slug).has(canon(b)));
    if (f) return { f, label: f.name };
  }
  const own = canon(surnameOf(r.p.n));
  const f = registry.find((x) => KEYS.get(x.slug).has(own));
  if (f) return { f, label: f.name };
  return { f: null, label: surnameOf(r.p.n) };
}

/* ---- the direct line: the ancestors on pedigree.json, by name (and birth year where the
   chart gives one), at the generation the Spine numbers them (the starting point is 2) ---- */
const ancestors = [];
(function walk(n, depth) {
  if (!n || !n.n) return;
  const yr = (String(n.b ?? "").match(/\d{4}/) || [])[0];
  const named = rows.filter((r) => r.p.n === n.n);
  /* the chart gives a birth year the person's own row sometimes lacks; with one person of that
     name the name settles it, with several the year must */
  const cands = yr ? named.filter((r) => String(r.p.b ?? "").includes(yr)) : named;
  if (!cands.length && named.length === 1) cands.push(named[0]);
  ancestors.push({ node: n, depth, row: cands[0] || null });
  walk(n.f, depth + 1);
  walk(n.m, depth + 1);
})(PED.root, 0);

/* ---- households, resolved once ---- */
const HH = HOUSEHOLDS.map((f, i) => ({
  i, f,
  h: f.h ? rowOf(f.h) : null, w: f.w ? rowOf(f.w) : null,
  hName: f.h ? String(f.h).split("|")[0] : "", wName: f.w ? String(f.w).split("|")[0] : "",
  kids: f.kids.map((k) => ({ row: rowOf(k.n), name: String(k.n).split("|")[0], via: k.via })),
}));

/* The first sentence or two of the archive's own note, as plain text: a pointer to the
   note and never a replacement for it. */
export function digest(text, max = 300) {
  const t = plain(String(text ?? "")).replace(/\s+/g, " ").trim();
  if (!t) return { text: "", cut: false };
  if (t.length <= max) return { text: t, cut: false };
  const parts = t.split(/(?<=[.!?”’"])\s+(?=[A-Z“‘"])/);
  let out = "";
  for (const s of parts) {
    if (out && (out + " " + s).length > max) break;
    out = out ? out + " " + s : s;
    if (out.length >= 140) break;
  }
  return { text: out, cut: out.length < t.length };
}

const cache = new Map();
export function model(slug) {
  if (cache.has(slug)) return cache.get(slug);
  const f = registry.find((x) => x.slug === slug);
  const ks = KEYS.get(slug);

  /* members: everyone who carries or was born to the name, and everyone the archive filed
     on the family's line (its own judgement, person by person) */
  const members = rows
    .map((r) => ({ r, name: carries(r, f), line: !!f.line && r.p.l === f.line }))
    .filter((m) => m.name || m.line)
    .map((m) => ({ ...m, y: firstYear(m.r) }))
    .sort((a, b) => a.y - b.y || (a.r.p.n < b.r.p.n ? -1 : 1));
  const memberKeys = new Set(members.map((m) => m.r.key));
  const isMember = (r) => !!r && memberKeys.has(r.key);

  const dead = members.filter((m) => !m.r.living);
  const living = members.filter((m) => m.r.living);
  const yrs = dead.flatMap((m) => years(m.r));
  const span = yrs.length ? [Math.min(...yrs), Math.max(...yrs)] : null;
  const grade = { doc: 0, inf: 0, lore: 0, open: 0 };
  for (const m of dead) grade[m.r.p.s] = (grade[m.r.p.s] || 0) + 1;

  /* spellings of the name as the archive prints them on its people */
  const sp = new Map();
  for (const m of members) {
    if (!m.name) continue;
    const t = ks.has(canon(surnameOf(m.r.p.n))) ? surnameFull(m.r.p.n) : null;
    if (t) sp.set(t, (sp.get(t) || 0) + 1);
  }
  const spellings = [...sp.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));

  /* the direct line through the family */
  const direct = ancestors
    .filter((a) => a.row && isMember(a.row) && ks.has(canon(surnameOf(a.row.p.n))))
    .map((a) => ({ ...a, gen: a.depth + 2 }))
    .sort((a, b) => b.gen - a.gen);

  /* places: the places that name a member (living people are never counted) */
  const names = new Set(dead.map((m) => m.r.p.n));
  const places = PL.places
    .map((pl) => ({ pl, n: (pl.p || []).filter((x) => names.has(x)).length }))
    .filter((x) => x.n > 0)
    .sort((a, b) => b.n - a.n || (a.pl.n < b.pl.n ? -1 : 1));

  /* households in which a member is a spouse. A spouse "carries the name" by the same test as a
     member does (the name, or born to it); the other spouse is of another family, which the
     column names - the family the archive says a woman was born into, else the name she bears. */
  const carriesName = (r, name) => (r ? carries(r, f) : name ? ks.has(canon(surnameOf(name))) : false);
  const sideOf = (r, name) => (r ? familyOfRow(r) : name ? { f: null, label: surnameOf(name) } : null);
  const marriages = HH.filter((x) => isMember(x.h) || isMember(x.w)).map((x) => {
    const hc = carriesName(x.h, x.hName), wc = carriesName(x.w, x.wName);
    const sides = [];
    if (!hc && (x.h || x.hName)) sides.push(sideOf(x.h, x.hName));
    if (!wc && (x.w || x.wName)) sides.push(sideOf(x.w, x.wName));
    const single = !(x.h || x.hName) || !(x.w || x.wName);
    return { ...x, single, within: !single && hc && wc, hc, wc, sides: sides.filter(Boolean).filter((sd, i, a) => a.findIndex((z) => z.label === sd.label) === i),
             out: !single && hc !== wc };
  });
  const joins = new Map();
  for (const m of marriages) {
    if (!m.out) continue; // exactly one of two recorded spouses carries the name
    for (const sd of m.sides) {
      const j = joins.get(sd.label) || { label: sd.label, fam: sd.f, n: 0 };
      j.n++; joins.set(sd.label, j);
    }
  }
  const nWithin = marriages.filter((m) => m.within).length;
  const nOut = marriages.filter((m) => m.out).length;
  const nSingle = marriages.filter((m) => m.single).length;
  const nOther = marriages.length - nWithin - nOut - nSingle;
  const via = { line: 0, doc: 0, inf: 0, tree: 0 };
  for (const m of marriages) via[m.f.via] = (via[m.f.via] || 0) + 1;

  /* where the archive discusses them: the page links it keeps on each person. One entry per
     label and page, pointing at the anchor most of them use. */
  const disc = new Map();
  for (const m of dead) for (const [label, href] of m.r.p.p || []) {
    const key = label + "|" + href.split("#")[0];
    const d = disc.get(key) || { label, n: 0, hrefs: new Map() };
    d.n++; d.hrefs.set(href, (d.hrefs.get(href) || 0) + 1); disc.set(key, d);
  }
  const discussed = [...disc.values()]
    .map((d) => ({ label: d.label, n: d.n, href: [...d.hrefs.entries()].sort((a, b) => b[1] - a[1])[0][0] }))
    .sort((a, b) => b.n - a.n || (a.label < b.label ? -1 : 1));

  /* the register: how many rows are filed under the name, and how many of them are people
     the archive reconstructed rather than rows from a surname index */
  const rr = REG.rows.filter((r) => f.register.includes(r.g));
  const register = {
    groups: f.register,
    total: rr.length,
    read: rr.filter((r) => r.k === "read").length,
    index: rr.filter((r) => r.k !== "read").length,
    linked: rr.filter((r) => r.p).length,
  };

  const out = {
    folded: new Set(f.fold.map(canon)).size > 1,
    f, members, dead, living, span, grade, spellings, direct, places, marriages, nWithin, nOut, nSingle, nOther, joins: [...joins.values()].sort((a, b) => b.n - a.n || (a.label < b.label ? -1 : 1)),
    via, discussed, register,
    nName: members.filter((m) => m.name).length,
    nLineOnly: members.filter((m) => !m.name).length,
    nPages: new Set(members.map((m) => m.r.slug)).size,
  };
  cache.set(slug, out);
  return out;
}

export const allModels = () => registry.map((f) => model(f.slug));

/* The lines people.json keeps that have no family page, with how many people each holds. */
export const linesWithoutPage = () => {
  const have = new Set(registry.map((f) => f.line).filter(Boolean));
  return P.lines.filter((l) => !have.has(l)).map((l) => ({ line: l, n: P.people.filter((p) => p.l === l).length }));
};

/* Names several people carry that have no page: counted the same way, so the index can say
   what it left out rather than leave a reader to wonder. */
export const otherNames = (min = 5) => {
  const have = new Set();
  for (const ks of KEYS.values()) for (const k of ks) have.add(k);
  const by = new Map();
  for (const r of rows) {
    const t = surnameOf(r.p.n), c = canon(t);
    if (have.has(c) || !c) continue;
    const e = by.get(c) || { n: 0, raw: new Map() };
    e.n++; e.raw.set(t, (e.raw.get(t) || 0) + 1); by.set(c, e);
  }
  return [...by.values()].filter((e) => e.n >= min)
    .map((e) => ({ n: e.n, label: [...e.raw.entries()].sort((a, b) => b[1] - a[1])[0][0] }))
    .sort((a, b) => b.n - a.n || (a.label < b.label ? -1 : 1));
};

export const GRADE = { doc: "Documented", inf: "Inferred", lore: "Testimony", open: "Open" };
export const VIA = { line: "direct line", doc: "a record read here", inf: "inferred", tree: "a family tree, not a document" };
export const VIA_CLS = { line: "doc", doc: "doc", inf: "inf", tree: "lore" };
