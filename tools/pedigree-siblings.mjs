/* Put the siblings on the pedigree.
 *
 * pedigree.json is an ancestor chart: every node has a father and a mother and
 * nothing sideways, so /bloodline/ could draw twenty-six people and not one
 * aunt, uncle or cousin. The siblings are not missing from the archive — they
 * are in kin.js, which records each household and the document that puts every
 * child in it. This walks the pedigree, finds the household each ancestor was a
 * child of, and writes the other children back onto the node as `sib`.
 *
 * TWO RULES, AND BOTH OF THEM ARE ABOUT NOT GUESSING.
 *
 * 1. THE ESTATE RULE. Only the dead are named. A sibling is carried only when
 *    something proves it: a death of their own, a birth more than eighty years
 *    ago, a parent who died before 1946, or a household whose latest known
 *    child was born early enough that no child of it can still be living. A
 *    sibling this cannot establish is LEFT OFF and counted in the report.
 *
 * 2. THE SHARED-NAME RULE. This family reuses forenames relentlessly — there
 *    are two George Mountjoys and six men called Petrus Jacobus. Where a name
 *    matches more than one person in people.js, the dates are NOT taken from
 *    either; the sibling is drawn with a name and no dates. A wrong date on a
 *    chart is worse than no date, because a chart looks settled.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { families } from "../site/src/data/kin.js";
import { people } from "../site/src/data/people.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PED = path.join(HERE, "..", "site", "src", "data", "pedigree.json");
const THIS_YEAR = new Date().getFullYear();
const PRESUME_DEAD_AFTER = 80;          // the kit's own rule
const CHILDBEARING = 25;                // years after a known birth a sibling may still arrive

const ped = JSON.parse(readFileSync(PED, "utf8"));
const bare = (s) => s.split("|")[0];
const token = (s) => (s.includes("|") ? s.split("|")[1] : null);
const yearOf = (s) => { const m = String(s || "").match(/\b(1[6-9]\d\d|20\d\d)\b/); return m ? +m[1] : null; };
const hasDeath = (p) => p && p.d && p.d !== "—" && p.d.trim() !== "";

/* names carried by more than one person — dates from these are never trusted */
const counts = new Map();
for (const p of people) counts.set(p.n, (counts.get(p.n) || 0) + 1);
const byName = new Map();
for (const p of people) if (counts.get(p.n) === 1) byName.set(p.n, p);

/* a kin kid entry matches a pedigree node when the name agrees and, if the
   entry is disambiguated with |token, the token appears in the node's dates */
const matches = (kidName, node) =>
  bare(kidName) === node.n &&
  (!token(kidName) || `${node.b || ""} ${node.d || ""}`.includes(token(kidName)));

const report = { placed: 0, carried: 0, cousins: 0, withheld: [], undated: [] };

function deadness(fam) {
  /* the latest moment this household can still have been producing children */
  let latest = null;
  for (const k of fam.kids || []) {
    const p = byName.get(bare(k.n));
    const y = p ? yearOf(p.b) : null;
    if (y && (latest === null || y > latest)) latest = y;
  }
  let parentDeath = null;
  for (const who of [fam.h, fam.w]) {
    const p = who ? byName.get(bare(who)) : null;
    const y = p && hasDeath(p) ? yearOf(p.d) : null;
    if (y && (parentDeath === null || y > parentDeath)) parentDeath = y;
  }
  const cutoff = THIS_YEAR - PRESUME_DEAD_AFTER;          // born on or before this = presumed dead
  if (parentDeath !== null && parentDeath <= cutoff) return "the household's parents were dead by " + parentDeath;
  if (latest !== null && latest + CHILDBEARING <= cutoff) return "no child of this household can have been born after about " + (latest + CHILDBEARING);
  return null;
}

const walk = (node) => {
  if (!node || !node.n) return;
  delete node.sib;
  const fam = families.find((f) => (f.kids || []).some((k) => matches(k.n, node)));
  if (fam) {
    report.placed++;
    const houseRule = deadness(fam);
    const sibs = [];
    for (const k of fam.kids || []) {
      if (matches(k.n, node)) continue;
      const name = bare(k.n);
      const p = byName.get(name);                          // undefined when the name is shared
      const cutoff = THIS_YEAR - PRESUME_DEAD_AFTER;
      const own = p && (hasDeath(p) || (yearOf(p.b) !== null && yearOf(p.b) <= cutoff));
      if (!own && !houseRule) { report.withheld.push(`${name} (sibling of ${node.n})`); continue; }
      const rec = { n: name, via: k.via || "doc" };
      if (p) {
        if (p.b && p.b !== "—") rec.b = String(p.b).split(",")[0].trim();
        if (hasDeath(p)) rec.d = String(p.d).split(",")[0].split("—")[0].trim();
      } else {
        rec.amb = true;                                    // name shared; no dates taken
        report.undated.push(`${name} (sibling of ${node.n})`);
      }
      /* AND THEIR CHILDREN, WHICH IS WHERE THE COUSINS COME FROM. A sibling
         who heads a household in kin.js brings that household's children with
         them, under the same estate rule. One generation only: this is a chart
         of blood relatives, not a descent report. */
      const household = families.find((f) => bare(f.h || "") === name || bare(f.w || "") === name);
      if (household) {
        const kidRule = deadness(household);
        const kids = [];
        for (const c of household.kids || []) {
          const kn = bare(c.n);
          const kp = byName.get(kn);
          const kdead = kp && (hasDeath(kp) || (yearOf(kp.b) !== null && yearOf(kp.b) <= THIS_YEAR - PRESUME_DEAD_AFTER));
          if (!kdead && !kidRule) { report.withheld.push(`${kn} (child of ${name})`); continue; }
          const kr = { n: kn, via: c.via || "doc" };
          if (kp) {
            if (kp.b && kp.b !== "—") kr.b = String(kp.b).split(",")[0].trim();
            if (hasDeath(kp)) kr.d = String(kp.d).split(",")[0].split("—")[0].trim();
          } else { kr.amb = true; report.undated.push(`${kn} (child of ${name})`); }
          kids.push(kr); report.cousins++;
        }
        if (kids.length) rec.kids = kids;
      }
      sibs.push(rec);
      report.carried++;
    }
    if (sibs.length) { node.sib = sibs; node.sibwhy = fam.why ? (fam.src ? fam.src[0] : "kin.js") : "kin.js"; }
  }
  walk(node.f); walk(node.m);
};

walk(ped.root);
ped.note = ped.note.replace(/\s*Siblings are drawn[\s\S]*$/, "") +
  " Siblings are drawn from kin.js, which records each household and the document that places every child in it — only the dead, and where a forename is carried by more than one person in this archive the sibling is drawn without dates rather than with somebody else's.";
writeFileSync(PED, JSON.stringify(ped, null, 1) + "\n", "utf8");

console.log(`pedigree: ${report.placed} of the chart's people placed in a household`);
console.log(`siblings carried: ${report.carried}`);
console.log(`their children carried (the cousins): ${report.cousins}`);
console.log(`withheld as possibly living: ${report.withheld.length}${report.withheld.length ? " — " + report.withheld.join("; ") : ""}`);
console.log(`drawn without dates (shared forename): ${report.undated.length}${report.undated.length ? " — " + report.undated.join("; ") : ""}`);
