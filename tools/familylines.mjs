#!/usr/bin/env node
/* THE FAMILY RIBBONS' DATA, made from the archive's own files and never typed by hand.

    node tools/familylines.mjs            write site/src/data/family-lines.json
    node tools/familylines.mjs --check    fail if the committed file is not what this would write
    node tools/familylines.mjs --report   also print, family by family, what was drawn and why
    node tools/familylines.mjs --check --living-out private/familyribbon-living.json
                                          also write the living names the kit's gate reads (--living)

The contract is the kit's (kit/docs/family-ribbon.md): one entry for each family page, with that family's own line
of generations as cards and, under them, HOW OUR LINE CONNECTS. The pages are the twelve families.json names
(/families/<slug>/, and the two hand-built pages /barry/ and /kolbe/); the page draws the entry with the kit's
FamilyRibbon. Our direct line is src/data/direct-line.json, which the kit's directline.py makes from the story.

WHO IS OF A FAMILY is the family page's own answer: this tool imports site/src/lib/families.js and kin.js (the
same modules the page is drawn from), so a ribbon cannot hold anyone the page itself does not list, and every
relationship is a household in kin.js with the `via` it is known by. Nothing is guessed:

  THE CARDS are one chain of parent and child who both carry the family's name, earliest first, ending at the
  person where our line meets the family (one of ours where one of ours is of the family, else the longest such
  chain), or, for a family our line does not meet, at the person of the name nearest our line through the households
  and the chart, else the longest chain the family has. A card's years are
  the years its person's own dates print; its "from" is the place in the birth field, graded by the person's own
  mark (an open question is drawn dashed); its "at" is the place of death where it differs; its spouse is the other
  parent of the next card. A person on the story's ribbon keeps the ribbon's own card, so the two cannot disagree.
  No living person is a card: the chain stops at the last who is not living.

  THE CONNECTIONS are every household that joins a person of direct-line.json (people and partners) to a person
  who carries or was born to the family's name and has a page of their own: a marriage, a parent, or, for one of
  ours who is not of the family, a brother or sister of the name. The grade is the household's `via` (line and doc:
  documented; inf: inferred; tree: the family's tree); for a child on the line, where a chapter's tree in the story
  draws the same parent and child, the weaker of that and the story's own grade. A marriage between two of ours is
  drawn once, on the page of the family the partner came from. A person who shares a page with a namesake (the two
  Petrus Jacobus Booysens, father and son) is not a party: the page would say the other man.

  A FAMILY OUR LINE DOES NOT MEET (no block of the kit's relations reaches it) gets the kit's "not connected" block,
  and its reason is computed: the shortest run of households and chart boxes from a person of the name to one of
  ours, said in words (descent first, so a family of our ancestors is said to be one), or that there is none.

The gate is the kit's checkfamilyribbon.py (npm run check:familyribbon), which reads this file and the built pages.
*/
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as nodeModule from "node:module";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const SITE = path.join(ROOT, "site");
const DATA = path.join(SITE, "src", "data");
const OUT = path.join(DATA, "family-lines.json");

/* The site's modules import JSON without import attributes (Vite allows it, Node does not): serve a .json file as a
   module whose default export is its content, the same object Vite gives the page. */
const jsonAsModule = (url) => ({ format: "module", shortCircuit: true, source: "export default " + fs.readFileSync(new URL(url), "utf8") + ";" });
if (nodeModule.registerHooks) {
  nodeModule.registerHooks({ load(url, context, next) { return url.startsWith("file:") && url.endsWith(".json") ? jsonAsModule(url) : next(url, context); } });
} else {
  nodeModule.register("data:text/javascript," + encodeURIComponent(
    'import fs from "node:fs"; export async function load(url, context, next) { if (url.startsWith("file:") && url.endsWith(".json")) ' +
    'return { format: "module", shortCircuit: true, source: "export default " + fs.readFileSync(new URL(url), "utf8") + ";" }; return next(url, context); }'));
}
const FAM = await import(pathToFileURL(path.join(SITE, "src", "lib", "families.js")).href);
const KIN = await import(pathToFileURL(path.join(SITE, "src", "lib", "kin.js")).href);
const HH = (await import(pathToFileURL(path.join(DATA, "kin.js")).href)).families;
const read = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));
const STORY = read("story.json");
const DL = read("direct-line.json");
const LINES = read("lines.json");
const DOSS = read("dossiers.json").people;

const STORY_PAGE = "/story/";
const VIA_GRADE = { line: "doc", doc: "doc", inf: "inf", tree: "lore" };
const RANK = { doc: 0, inf: 1, lore: 2 };
const weaker = (...gs) => gs.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "doc");
const MARK_GRADE = { doc: "doc", inf: "inf", lore: "lore", open: "inf" };

/* ---- people ---------------------------------------------------------------------------------------------------- */
const byKey = new Map(FAM.rows.map((r) => [r.key, r]));
const rowOfResolved = (x) => (x && !x.missing ? byKey.get(x.key) || null : null);
/* A row has a page of its own when it is the person its page is about (not a namesake the page also holds). */
const ownPage = (r) => {
  if (!r || !r.slug) return false;
  const d = DOSS[r.slug];
  return !!d && d.n === r.p.n && (d.b || "") === (r.p.b || "");
};
const sexOf = new Map();
for (const f of HH) {
  const h = rowOfResolved(KIN.resolve(f.h)), w = rowOfResolved(KIN.resolve(f.w));
  if (h) sexOf.set(h.key, "m");
  if (w) sexOf.set(w.key, "f");
}
const childWord = (r) => ({ m: "son of", f: "daughter of" })[sexOf.get(r.key)] || "child of";
const sibWord = (r) => ({ m: "brother of", f: "sister of" })[sexOf.get(r.key)] || "sibling of";

const YEAR = /(1[5-9]\d\d|20\d\d)/;
/* A date field as the archive prints it: "c. 21 Sep 1788, Graaff-Reinet", "7 Dec 1802, Soho — baptised 2 Feb 1803,
   Westminster", "bapt. 9 Jan 1792, Westminster", "1857 — from Pama, not from a font", "— — 1796 was the OTHER man's
   year". What follows an em dash is the archive's comment and is never read for a year or a place. The year keeps the
   qualifier printed in front of it (c., bef., aft., bapt.); the place is the part after the date, or the place of the
   baptism or burial the field names instead (`event`), with a part that holds a number (a grave, an erf) left out. */
const QUAL = /(c\.|ca\.|bef\.|aft\.|after|before|about|abt\.?|bapt\.|buried)\s+(?:\d{1,2}\s+)?(?:[A-Z][a-z]{2,8}\.?\s+)?$/i;
function field(s) {
  const pre = String(s ?? "").split(/\s+—\s+/)[0].trim();
  if (!pre || /^[—–-]+$/.test(pre)) return { year: "", place: "", event: "" };
  const parts = pre.split(/,(?![^(]*\))/).map((x) => x.trim()).filter(Boolean);
  let year = "", event = /^bapt/i.test(parts[0]) ? "baptism" : /^buried/i.test(parts[0]) ? "burial" : "";
  const m = parts[0].match(YEAR);
  if (m) {
    const q = parts[0].slice(0, m.index).match(QUAL);
    const w = q ? q[1].toLowerCase() : "";
    year = ({ "ca.": "c.", about: "c.", "abt.": "c.", abt: "c.", before: "bef.", after: "aft.", buried: "" }[w] ?? w);
    year = (year ? year + " " : "") + m[1];
  }
  const places = [];
  for (const part of parts.slice(1)) {
    if (/^(baptised|bapt\.)/i.test(part)) { event = "baptism"; const at = part.match(/\bat\s+(.+)$/); if (at) places.push(at[1]); continue; }
    if (/^buried/i.test(part)) { event = "burial"; continue; }
    if (/^(or|aged|estate|death notice|will)\b/i.test(part) || /\d/.test(part)) continue;
    places.push(part.replace(/\s*\((?!\?\))[^)]{4,}\)/g, "").trim());
  }
  return { year, place: places.filter(Boolean).join(", "), event };
}
function yearsOf(r) {
  if (r.living) return "";
  const bf = field(r.p.b), df = field(r.p.d);
  const b = bf.year, d = df.year;
  const dead = !d && String(r.p.d ?? "").trim() && !/^[—–-]+$/.test(String(r.p.d).trim());
  if (b && d) return `${b}–${d}`;
  if (b) return dead ? `${b}–†` : `b. ${b}`;
  if (d) return `d. ${d}`;
  return "";
}
const birthPlace = (r) => (r.living ? "" : field(r.p.b).place);
const deathPlace = (r) => { const f = field(r.p.d); return r.living || f.event === "burial" ? "" : f.place; };
const ofPlace = (r) => (r && birthPlace(r) ? `of ${birthPlace(r)}` : "");

/* the first sentence of a household's own note, for a marriage block's foot */
function firstSentence(t, max = 220) {
  const s = String(t ?? "").replace(/\*\*|__|`/g, "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/\s+/g, " ").trim();
  if (!s) return "";
  const m = s.match(/^(.+?[.!?])(\s+[A-Z“"‘]|$)/);
  const one = m ? m[1] : s;
  return one.length <= max ? one : one.slice(0, max - 1).replace(/\s+\S*$/, "") + " …";
}

/* ---- our direct line: every story card and every partner, as a row of the archive ------------------------------ */
const DM = new Map();
for (const p of DL.people || []) DM.set(p.slug, { ...p, role: "line" });
for (const p of DL.partners || []) if (!DM.has(p.slug)) DM.set(p.slug, { ...p, role: "partner" });
const ours = new Map(); // row key -> { slug|null, generation, role, chapter, card }
const firstYear = (s) => (String(s ?? "").match(YEAR) || [])[1] || "";
(STORY.ribbon.cards || []).forEach((c, i) => {
  const gen = i + 1;
  let cands = c.person ? FAM.rows.filter((r) => r.slug === c.person && ownPage(r)) : FAM.rows.filter((r) => r.p.n === c.name);
  if (cands.length > 1 && firstYear(c.years)) cands = cands.filter((r) => String(r.p.b || "").includes(firstYear(c.years)));
  if (cands.length !== 1) throw new Error(`story card ${gen} (${c.name}) is ${cands.length} rows of people.json, not one`);
  ours.set(cands[0].key, { slug: c.person && DM.has(c.person) ? c.person : null, generation: gen, role: c.person ? "line" : "unlinked", chapter: c.chapter, card: c });
  if (c.spouseDirect && c.spousePerson) {
    const s = FAM.rows.filter((r) => r.slug === c.spousePerson && ownPage(r));
    if (s.length !== 1) throw new Error(`story card ${gen}: spouse ${c.spousePerson} is ${s.length} rows, not one`);
    if (!ours.has(s[0].key)) ours.set(s[0].key, { slug: c.spousePerson, generation: gen, role: "partner", chapter: c.chapter, card: null });
  }
});
const oursOf = (r) => (r ? ours.get(r.key) || null : null);
const dmName = (slug) => (DM.get(slug) || {}).name || slug;

/* A child's place in a household is graded by its `via`. `line` is the archive's own direct line, argued on
   /direct-line/, which the family pages count as documented; where the story draws the same parent and child in a
   chapter's tree, the story's grade for the child (its thread) is the more particular statement, and the weaker of
   the two is used: George Downing Mountjoy's parentage rests on the family's tree and his names, and the story says so. */
function storyChildGrade(parentSlug, childSlug) {
  for (const ch of STORY.chapters || []) {
    const rows = (ch.tree && ch.tree.rows) || [];
    const couple = rows.find((r) => r.kind === "couple");
    const kids = rows.find((r) => r.kind === "children");
    if (!couple || !kids || !couple.nodes.some((n) => n.person === parentSlug)) continue;
    const k = kids.nodes.find((n) => n.person === childSlug);
    if (k && k.grade) return k.grade;
  }
  return null;
}
function childGrade(via, parentRow, childRow) {
  const g = VIA_GRADE[via] || "lore";
  const sg = parentRow.slug && childRow.slug && ownPage(childRow) ? storyChildGrade(parentRow.slug, childRow.slug) : null;
  return sg ? weaker(g, sg) : g;
}

/* ---- a family ---------------------------------------------------------------------------------------------------- */
function familyFacts(f) {
  const M = FAM.model(f.slug);
  const member = new Set(M.members.map((m) => m.r.key));
  const named = new Set(M.members.filter((m) => m.name).map((m) => m.r.key));
  return { M, member, named };
}

/* every household that joins one of ours to a person of this family */
function connectionsOf(fx) {
  const out = [];
  const seen = new Set();
  const push = (x, xo, r, relation, grade, note, theirOrigin) => {
    const k = `${xo.slug}|${r.slug}|${relation}`;
    if (seen.has(k)) return;
    seen.add(k);
    out.push({
      ourSlug: xo.slug, ourGeneration: DM.get(xo.slug).generation, theirSlug: r.slug, theirName: r.p.n,
      ...(theirOrigin ? { theirOrigin } : {}), relation, grade, storyHref: `${STORY_PAGE}#${DM.get(xo.slug).storyChapter}`,
      ...(note ? { note } : {}), _their: r, _our: x,
    });
  };
  const party = (r, x) => r && fx.named.has(r.key) && ownPage(r) && r.slug !== x.slug && !r.living;
  for (const x of FAM.rows) {
    const xo = oursOf(x);
    if (!xo || !xo.slug || !DM.has(xo.slug)) continue;
    const t = KIN.treeFor(x.p);
    if (t.origin) {
      for (const p of t.parents) {
        const r = rowOfResolved(p);
        /* no note: the household's own note is about the parents' marriage, not about this child's place in it */
        if (party(r, x)) push(x, xo, r, childWord(x), childGrade(t.origin.via, r, x), "");
      }
    }
    for (const un of t.unions) {
      const r = rowOfResolved(un.spouse);
      if (!party(r, x)) continue;
      const ro = oursOf(r);
      if (xo.role === "partner" && ro && ro.role !== "partner") continue; // drawn on the partner's family's page
      const card = xo.card && xo.card.spousePerson === r.slug ? xo.card : null;
      push(x, xo, r, "married", VIA_GRADE[un.f.via] || "lore", firstSentence(un.f.why), card ? card.spouseOrigin : ofPlace(r));
    }
    if (!fx.named.has(x.key) && t.origin) {
      for (const s of t.siblings) {
        const r = rowOfResolved(s);
        if (!party(r, x) || oursOf(r)) continue;
        push(x, xo, r, sibWord(x), weaker(VIA_GRADE[s.via] || "lore", VIA_GRADE[t.origin.via] || "lore"), "");
      }
    }
  }
  return out.sort((a, b) => a.ourGeneration - b.ourGeneration || (a.theirName < b.theirName ? -1 : 1));
}

/* ---- the households and the chart as one graph, for the nearest way a family reaches our line -------------------- */
const PED = read("pedigree.json");
const EDGES = new Map(); // row key -> [{ to: row, kind: "spouse" | "child" | "parent" }]
const addEdge = (a, b, kind) => {
  if (!a || !b || a.key === b.key) return;
  const l = EDGES.get(a.key) || [];
  if (!l.some((e) => e.to.key === b.key && e.kind === kind)) l.push({ to: b, kind });
  EDGES.set(a.key, l);
};
for (const f of HH) {
  const h = rowOfResolved(KIN.resolve(f.h)), w = rowOfResolved(KIN.resolve(f.w));
  if (h && w) { addEdge(h, w, "spouse"); addEdge(w, h, "spouse"); }
  for (const k of f.kids) {
    const kr = rowOfResolved(KIN.resolve(k.n));
    for (const par of [h, w]) if (par && kr) { addEdge(par, kr, "child"); addEdge(kr, par, "parent"); }
  }
}
/* the chart: every box is a person a document names; a box's father and mother are its parents */
const pedRow = (n) => {
  if (!n || !n.n) return null;
  const named = FAM.rows.filter((r) => r.p.n === n.n);
  const yr = firstYear(n.b);
  const c = yr ? named.filter((r) => String(r.p.b ?? "").includes(yr)) : named;
  return c.length === 1 ? c[0] : named.length === 1 ? named[0] : null;
};
(function walk(n) {
  if (!n || !n.n) return;
  const me = pedRow(n);
  for (const par of [n.f, n.m]) {
    const pr = pedRow(par);
    if (me && pr) { addEdge(pr, me, "child"); addEdge(me, pr, "parent"); }
    walk(par);
  }
})(PED.root);

/* the shortest run of households from a person of the family to a person of ours; nobody living on the way. With
   `descent`, only from parent to child: the family is then one of our line's ancestors, which is said first. */
function nearest(fx, descent = false) {
  const starts = FAM.rows.filter((r) => fx.named.has(r.key) && !r.living);
  const prev = new Map(starts.map((r) => [r.key, null]));
  let frontier = starts;
  for (let depth = 0; depth < 6 && frontier.length; depth++) {
    const next = [];
    for (const r of frontier) {
      const o = oursOf(r);
      if (o && depth > 0) {
        const pathRows = [];
        for (let k = r.key, e = { row: r, kind: null }; e; ) {
          pathRows.unshift(e);
          const pv = prev.get(k);
          if (!pv) break;
          e = { row: pv.row, kind: pv.kind };
          k = pv.row.key;
        }
        return pathRows;
      }
      for (const e of EDGES.get(r.key) || []) {
        if (prev.has(e.to.key) || e.to.living || (descent && e.kind !== "child")) continue;
        prev.set(e.to.key, { row: r, kind: e.kind });
        next.push(e.to);
      }
    }
    frontier = next;
  }
  return null;
}
function describe(pathRows) {
  const nm = (r) => r.p.n;
  let out = "";
  for (let i = 0; i < pathRows.length - 1; i++) {
    const a = pathRows[i].row, b = pathRows[i + 1].row, kind = pathRows[i + 1].via;
    const word = kind === "spouse" ? "married" : kind === "child"
      ? ({ m: "father of", f: "mother of" })[sexOf.get(a.key)] || "parent of"
      : ({ m: "son of", f: "daughter of" })[sexOf.get(a.key)] || "child of";
    if (i === 0) out = kind === "spouse" ? `${nm(a)} married ${nm(b)}` : `${nm(a)} was the ${word} ${nm(b)}`;
    else out += kind === "spouse" ? `, who married ${nm(b)}` : `, the ${word} ${nm(b)}`;
  }
  const o = oursOf(pathRows[pathRows.length - 1].row);
  return `${out} (our line, generation ${o.generation})`;
}
/* nearest() gives each step with the kind of the edge INTO it; re-key it as the edge out of the step before */
function walkOf(fx) {
  const raw = nearest(fx, true) || nearest(fx, false);
  if (!raw) return null;
  return raw.map((e, i) => ({ row: e.row, via: i === 0 ? null : raw[i - 1].kind }));
}

/* ---- the cards ------------------------------------------------------------------------------------------------- */
/* the parent who carries the name, the father first */
function namedParent(r, fx) {
  const t = KIN.treeFor(r.p);
  if (!t.origin) return null;
  const cands = t.parents.map(rowOfResolved).filter((p) => p && fx.named.has(p.key) && !p.living);
  cands.sort((a, b) => (sexOf.get(a.key) === "m" ? -1 : 0) - (sexOf.get(b.key) === "m" ? -1 : 0));
  return cands[0] ? { row: cands[0], household: t.origin } : null;
}
/* the chain from the earliest of the name down to the anchor; each link knows the household it shares with the next */
function chainUp(anchor, fx) {
  const chain = [{ row: anchor, next: null }];
  const seen = new Set([anchor.key]);
  let cur = anchor;
  for (;;) {
    const up = namedParent(cur, fx);
    if (!up || seen.has(up.row.key)) break;
    seen.add(up.row.key);
    chain.unshift({ row: up.row, next: { row: cur, household: up.household } });
    cur = up.row;
  }
  return chain;
}
const birthYearN = (r) => Number(firstYear(field(r.p.b).year)) || 9999;

function pickChain(fx, conns, walk) {
  let anchors = [], how = "none";
  if (conns.length) {
    anchors = [...new Set(conns.map((c) => c._their))].filter((r) => fx.named.has(r.key));
    for (const c of conns) if (fx.named.has(c._our.key)) anchors.push(c._our);
    how = "where our line meets it";
  }
  if (!anchors.length && walk) { anchors = [walk[0].row]; how = "the person nearest our line"; }
  if (!anchors.length) {
    anchors = fx.M.direct.map((a) => a.row).filter((r) => r && fx.named.has(r.key) && !r.living);
    if (anchors.length) how = "the archive's chart";
  }
  if (!anchors.length) {
    anchors = fx.M.members.filter((m) => m.name && !m.r.living).map((m) => m.r);
    how = "the longest chain of the name";
  }
  const scored = anchors.map((a) => ({ a, ch: chainUp(a, fx), oursA: oursOf(a) ? 1 : 0,
    storySpouse: (STORY.ribbon.cards || []).some((c) => c.spousePerson && c.spousePerson === a.slug) ? 1 : 0 }));
  /* a chain that ends at one of ours first (the Barrys: to Kathleen, not to her niece), then the longest */
  scored.sort((x, y) => y.oursA - x.oursA || y.ch.length - x.ch.length || y.storySpouse - x.storySpouse
    || birthYearN(x.ch[0].row) - birthYearN(y.ch[0].row) || (x.a.p.n < y.a.p.n ? -1 : 1));
  return scored.length ? { chain: scored[0].ch, how } : { chain: [], how: "none" };
}

const ofOrigin = (o) => (o ? `of ${o}` : "place not known");
function spouseFields(card, sp) {
  if (!sp) return;
  if (!sp.name) { card.spouse = "spouse not named in the records"; return; }
  const so = sp.row ? oursOf(sp.row) : null;
  card.spouse = String(sp.name).split("|")[0];
  if (sp.row && sp.row.living) card.spouseOrigin = "";
  else if (so && so.card) card.spouseOrigin = ofOrigin(so.card.origin);
  else card.spouseOrigin = sp.row ? ofPlace(sp.row) || "place not known" : "place not known";
  if (sp.row && ownPage(sp.row) && !sp.row.living) card.spousePerson = sp.row.slug;
}
function cardOf(link, conns) {
  const r = link.row;
  const o = oursOf(r);
  if (o && o.card) {
    /* a person on the story's ribbon keeps the ribbon's card */
    const c = o.card;
    const card = { name: c.name, years: c.years, origin: c.origin, originGrade: c.originGrade, spouse: c.spouse, spouseOrigin: c.spouseOrigin,
      atPlace: c.atPlace, atYear: c.atYear, living: !!c.living };
    if (c.person) card.person = c.person;
    else card.title = `On our direct line, generation ${o.generation}. ${c.title || ""}`.trim();
    if (c.spousePerson) card.spousePerson = c.spousePerson;
    return card;
  }
  const bf = field(r.p.b);
  const bp = birthPlace(r), dp = deathPlace(r);
  const grade = MARK_GRADE[r.p.s] || "lore";
  const card = {
    name: r.p.n, years: yearsOf(r), origin: bp || "place not known",
    originGrade: bp && bf.event === "baptism" ? weaker(grade, "inf") : grade,
    spouse: "", spouseOrigin: "", atPlace: "", atYear: "", living: !!r.living,
  };
  if (dp && dp !== bp && !r.living) { card.atPlace = dp; card.atYear = field(r.p.d).year; }
  /* the spouse: the other parent of the next card; on the last card, the spouse our line meets, else the first */
  if (link.next) {
    const f = link.next.household.f;
    const h = rowOfResolved(KIN.resolve(f.h)), w = rowOfResolved(KIN.resolve(f.w));
    spouseFields(card, h && h.key === r.key ? { row: w, name: f.w } : { row: h, name: f.h });
  } else {
    const t = KIN.treeFor(r.p);
    const meet = conns.find((c) => c._their.key === r.key && c.relation === "married");
    const un = meet ? t.unions.find((u) => rowOfResolved(u.spouse) && rowOfResolved(u.spouse).key === meet._our.key) : t.unions[0];
    if (un) spouseFields(card, un.spouse ? { row: rowOfResolved(un.spouse), name: un.spouse.n } : { row: null, name: "" });
  }
  if (ownPage(r)) card.person = r.slug;
  else if (r.slug) card.title = `Shares a person page with ${DOSS[r.slug] ? DOSS[r.slug].n : "a namesake"}, so the card has no link of its own`;
  return card;
}

function laneOf(f) {
  return f.line ? (LINES.lanes || []).find((l) => l.label === f.line || l.key === String(f.line).toLowerCase()) || null : null;
}

/* the reason a family our line does not meet is not met, from the households and the chart */
function whyNot(f, fx, walk) {
  const lead = `No one on the story's ribbon, or married to one of them, is the child, parent, spouse or sibling of a ${f.name}.`;
  if (walk) return `${lead} The nearest the archive's households and chart bring the family to the line: ${describe(walk)}.`;
  return `${lead} The archive's households and its chart join the family to the line nowhere.`;
}

function build() {
  const families = [];
  const report = [];
  for (const f of FAM.registry) {
    const fx = familyFacts(f);
    const conns = connectionsOf(fx);
    const walk = conns.length ? null : walkOf(fx);
    const { chain, how } = pickChain(fx, conns, walk);
    const cards = chain.map((l) => cardOf(l, conns));
    const lane = laneOf(f);
    const topHasParents = chain.length ? !!KIN.treeFor(chain[0].row.p).origin : false;
    /* a family that is not one of the lines has no lane span; its span is the lines page's rule applied to its cards:
       the years of documented, not-living cards, leaving out a year beside c., bef., aft. or bapt. */
    const ys = cards.filter((c) => !c.living && c.originGrade === "doc")
      .flatMap((c) => [...c.years.matchAll(/(c\.|bef\.|aft\.|bapt\.|b\.|d\.)?\s*(1[5-9]\d\d|20\d\d)/g)].filter((m) => !m[1] || m[1] === "b." || m[1] === "d.").map((m) => Number(m[2])));
    const entry = {
      id: f.slug, title: f.name, page: FAM.hrefOf(f),
      status: lane && lane.status ? lane.status : "origin-unknown",
      statusNote: lane && lane.statusNote ? lane.statusNote : `not one of the archive's lines${topHasParents ? "" : "; the earliest card's parents are not in its households"}`,
      ...(lane && lane.span ? { span: lane.span } : ys.length ? { span: [Math.min(...ys), Math.max(...ys)] } : {}),
      cards,
    };
    if (conns.length) entry.connections = conns.map(({ _their, _our, ...c }) => c);
    else entry.notConnected = { why: whyNot(f, fx, walk) };
    families.push(entry);
    report.push({ id: f.slug, page: entry.page, cards: cards.length, chainFrom: how,
      connections: conns.map((c) => `${c.ourGeneration} ${dmName(c.ourSlug)} ${c.relation} ${c.theirName} (${c.grade})`),
      notConnected: entry.notConnected ? entry.notConnected.why : null });
  }
  return {
    out: {
      _note: "Made by tools/familylines.mjs from families.json, people.json, kin.js and pedigree.json (through site/src/lib/families.js and kin.js), story.json, direct-line.json, lines.json and dossiers.json; do not edit by hand. The contract is the kit's kit/docs/family-ribbon.md.",
      families,
    }, report,
  };
}

const argv = process.argv.slice(2);
const args = new Set(argv);
/* --living-out FILE: the names of the living (living.json, which holds them on purpose), as the kit's gate reads a
   private list ({"names": [...]}), for checkfamilyribbon.py --living. Written outside the repository (private/). */
const lo = argv.indexOf("--living-out");
if (lo > -1 && argv[lo + 1]) {
  const LV = read("living.json");
  const names = [...(LV.living || []), ...(LV.heldOut || [])].map((x) => x.n || x.name).filter(Boolean);
  fs.mkdirSync(path.dirname(path.resolve(argv[lo + 1])), { recursive: true });
  fs.writeFileSync(path.resolve(argv[lo + 1]), JSON.stringify({ names }, null, 1) + "\n");
}
const { out, report } = build();
const text = JSON.stringify(out, null, 1) + "\n";
if (args.has("--report")) for (const r of report) console.log(JSON.stringify(r, null, 1));
if (args.has("--check")) {
  const have = fs.existsSync(OUT) ? fs.readFileSync(OUT, "utf8") : "";
  if (have !== text) {
    console.error("familylines: site/src/data/family-lines.json is not what the archive's data makes; run node tools/familylines.mjs");
    process.exit(1);
  }
  console.log(`  ok    familylines  ${out.families.length} family pages, ${out.families.reduce((n, f) => n + f.cards.length, 0)} cards, ${out.families.reduce((n, f) => n + (f.connections || []).length, 0)} connections; the committed file is what the data makes`);
} else {
  fs.writeFileSync(OUT, text);
  console.log(`familylines: wrote ${path.relative(ROOT, OUT)} (${out.families.length} family pages)`);
}
