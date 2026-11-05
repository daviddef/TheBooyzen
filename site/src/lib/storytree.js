/* THE FAMILY, IN THE SHAPE THE KIT'S STORY LAYER READS (kit/lib/personstory.js: byId[id] = { id, given, sur, by, bye, dy, dye, bp, href, father,
   mother, kids[], spouse[], saidLiving }).

   Nothing is added to what the archive already holds. The nodes are the people in people.json; father and mother, children and spouses are the
   households in data/kin.js, read through lib/kin.js `resolve` exactly as the chart on a page in chart mode reads them, so the same ids come out
   (slugify of name|birth) and the same person is the same person. A person is the child of the FIRST household that lists them (kin.js treeFor
   takes asChild[0] the same way).

   WHAT IS NOT HERE ON PURPOSE. A birthplace: the birth field is free text ("9 Sep 1840, district Rustenburg", "bapt. 13 Jan 1806") and a place is
   never taken out of it by guesswork, so `bp` is empty and no card carries a place. A sex: nothing in the story reads one.

   THE LIVING RULE. «saidLiving» is this archive's own list (data/living.json, written by tools/livingflags.py from the kit's rule), so a person
   living.json calls living is a name and a relationship in the story. The kit then applies its own test on top (years, a recent child) in famNode.
   A date is the same date the chart draws: canonDate refuses a baptism, a bound, a probate or a bare «bef.», so a card never says someone was born
   in the year they were baptised. */
import { families } from "../data/kin.js";
import pj from "../data/people.json";
import dossiers from "../data/dossiers.json";
import { resolve, slugify } from "./kin.js";
import { isLivingSlug } from "./living.js";

const MON = { jan: "Jan", feb: "Feb", mar: "Mar", apr: "Apr", may: "May", jun: "Jun", jul: "Jul", aug: "Aug", sep: "Sep", oct: "Oct", nov: "Nov", dec: "Dec" };
/* A chart date is a day and month and year, or a year, with "c." where the field says circa, and nothing else. The field also holds where
   and what ("9 Sep 1840, district Rustenburg", "bapt. 13 Jan 1806", "bef. 1828", "1884 (probate)", "a minor, bef. 1904"): the part before the first
   comma, dash or bracket is read, a baptism or a bound or a probate is not a birth or a death and is left to the record table, and a month with no day
   gives its year. The year still reaches the kit's living rule through birthYear and deathRecorded. */
export const canonDate = (s) => {
  const t = String(s ?? "").trim();
  if (!t || t === "—" || /\(probate\)/i.test(t)) return undefined;
  const head = t.split(/[,—(]/)[0].trim();
  const m = /^(c\.\s*)?(?:(\d{1,2})\s+)?(?:([A-Za-z]{3})\s+)?(\d{4})$/.exec(head);
  if (!m) return undefined;
  const [, c, day, mon, y] = m;
  const mm = mon && MON[mon.toLowerCase()];
  if (mon && !mm) return undefined;
  if (day && !mm) return undefined;
  return (c ? "c. " : "") + (day && mm ? `${+day} ${mm} ` : "") + y;
};
export const yearIn = (s) => { const m = String(s ?? "").match(/\b(\d{4})\b/); return m ? Number(m[1]) : undefined; };
export const diedSaid = (s) => !!(s && s !== "—" && !/^living$/i.test(String(s).trim())) || undefined;

export const keyOf = (x) => x.n + "|" + (x.b || "");
/* the page a person is on: the dossier that holds them (a namesake page holds both men) */
const DKEY = new Map();
for (const q of Object.values(dossiers.people)) { DKEY.set(keyOf(q), q); for (const a of q.also || []) DKEY.set(keyOf(a), q); }
export const dossierOf = (x) => DKEY.get(keyOf(x));
export const idOf = (x) => slugify(keyOf(x));

let cache = null;
export function storyTree() {
  if (cache) return cache;
  const byId = {};
  const node = (o) => {
    if (!o) return null;
    const id = idOf(o);
    if (byId[id]) return byId[id];
    const dp = dossierOf(o);
    const bc = canonDate(o.b), dc = canonDate(o.d);
    const yr = (c) => (c ? Number(c.slice(-4)) : undefined);
    return (byId[id] = {
      id, given: o.n, sur: "", by: yr(bc), bye: bc ? bc.startsWith("c.") : false, dy: yr(dc), dye: dc ? dc.startsWith("c.") : false,
      bp: "", href: dp ? `/people/${dp.slug}/` : "", father: null, mother: null, kids: [], spouse: [], hasParents: false,
      ...(dp && isLivingSlug(dp.slug) ? { saidLiving: true } : {}),
      // the grade the archive gives the person (people.json `s`): doc, inf, lore or open
      grade: o.s,
    });
  };
  for (const o of pj.people) node({ ...o });
  for (const f of families) {
    const h = node(resolve(f.h)), w = node(resolve(f.w));
    if (h && w) { if (!h.spouse.includes(w.id)) h.spouse.push(w.id); if (!w.spouse.includes(h.id)) w.spouse.push(h.id); }
    for (const k of f.kids || []) {
      const c = node(resolve(k.n));
      if (!c) continue;
      for (const par of [h, w]) if (par && !par.kids.includes(c.id)) par.kids.push(c.id);
      if (!c.hasParents) { c.hasParents = true; c.father = h ? h.id : null; c.mother = w ? w.id : null; }
    }
  }
  return (cache = byId);
}
