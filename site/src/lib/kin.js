/* Turn the households in data/kin.js into the three tiers a person page draws:
   parents, self + spouses, children — plus siblings. Nothing here invents a
   relationship; it only rearranges the ones written down. */
import { families } from "../data/kin.js";
import pj from "../data/people.json";

const people = pj.people;

export const slugify = (n) =>
  n.normalize("NFD").replace(/[̀-ͯ]/g, "")
   .replace(/[‘’“”"']/g, "")
   .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

/* A reference is "Name" or "Name|token"; the token must appear in that person's
   birth or death string. Ambiguity is an error worth seeing, not swallowing. */
export function resolve(ref) {
  if (!ref) return null;
  const [name, token] = ref.split("|");
  let hits = people.filter(p => p.n === name);
  if (token) hits = hits.filter(p => (p.b || "").includes(token) || (p.d || "").includes(token));
  if (hits.length === 0) return { n: name, missing: true, slug: slugify(name) };
  return { ...hits[0], slug: slugify(hits[0].n), key: hits[0].n + "|" + (hits[0].b || "") };
}

const keyOf = (p) => p.n + "|" + (p.b || "");
const same = (a, b) => a && b && keyOf(a) === keyOf(b);

export function dates(p) {
  const short = (s) => (s && s !== "—" ? s.split(",")[0].trim() : "");
  const b = short(p.b), d = short(p.d);
  if (b && d) return b + " – " + d;
  if (b) return "b. " + b;
  if (d) return "d. " + d;
  return "";
}

/* Every household this person appears in, in each of the three roles. */
export function householdsFor(person) {
  const out = { asChild: [], asParent: [] };
  for (const f of families) {
    const h = resolve(f.h), w = resolve(f.w);
    if (same(h, person) || same(w, person)) out.asParent.push({ f, h, w });
    for (const k of f.kids) {
      if (same(resolve(k.n), person)) { out.asChild.push({ f, h, w, via: k.via }); break; }
    }
  }
  return out;
}

export function treeFor(person) {
  const { asChild, asParent } = householdsFor(person);
  const origin = asChild[0] || null;
  const siblings = origin
    ? origin.f.kids.map(k => ({ ...resolve(k.n), via: k.via }))
        .filter(x => !same(x, person))
    : [];
  const unions = asParent.map(({ f, h, w }) => {
    const spouse = same(h, person) ? w : h;
    return { f, spouse, kids: f.kids.map(k => ({ ...resolve(k.n), via: k.via })) };
  });
  return {
    parents: origin ? [origin.h, origin.w].filter(Boolean) : [],
    parentVia: origin ? origin.f.via : null,
    origin,
    siblings,
    unions,
  };
}

/* How much of what is drawn rests on a record, and how much on the tree. */
export function provenance(t) {
  const vias = [];
  if (t.origin) { for (const p of t.parents) vias.push(t.origin.f.via); vias.push(t.origin.via); }
  for (const s of t.siblings) vias.push(s.via);
  for (const un of t.unions) {
    if (un.spouse) vias.push(un.f.via);
    for (const k of un.kids) vias.push(k.via);
  }
  const n = vias.length;
  const doc = vias.filter(v => v === "doc" || v === "line").length;
  const tree = vias.filter(v => v === "tree").length;
  const inf = vias.filter(v => v === "inf").length;
  return { n, doc, tree, inf };
}
