/* What is new here, and the archive in numbers: the kit computes it at build time from this archive's own logs (kit/docs/whats-new.md).
   This file is the only Booyzen-specific part: which JSON is which, and the one count no log holds.
   searched.json is {sets, searched}; the kit's rowsOf reads `.searched`. corrections.json is {note, causes, rows} and its rows are
   ARRAYS, [date, what was said, the correction, cause, page] (see pages/corrections.astro), so they are turned into the objects the kit
   reads here, rather than changing the kit for one archive's shape. */
import { buildPulse } from "@daviddef/archive-kit/lib/pulse.js";
import { loadReceipts } from "@daviddef/archive-kit/lib/receipts.js";
import { corrIdMap } from "@daviddef/archive-kit/lib/corrections.js";
import searched from "../data/searched.json";
import corrections from "../data/corrections.json";
import worklist from "../data/worklist.json";
import people from "../data/people.json";
import who from "../data/corrections-who.json";
import dossiers from "../data/dossiers.json";
import living from "../data/living.json";

/* WHO A CORRECTION IS ABOUT (`for`, kit/docs/corrections.md): the archive's own pages for the people, read from corrections-who.json, the file tools/correctionswho.py
   derives (a person only when their whole held name appears, less what corrections-who-deny.json refuses) and check:corrections holds current. The key is the one the tool
   writes: the date, then the first 80 characters of the claim. Only people this archive publishes with a page, once each, and never a living person (living.json). */
const livingSlugs = new Set([...(living.living || []), ...(living.heldOut || [])].map((x) => x && x.slug).filter(Boolean));   /* living and held-out: never named as who a correction is about */
const forOf = (r) => ((who.who || {})[`${r[0]} | ${String(r[1]).slice(0, 80)}`] || [])
  .filter((sl) => dossiers.people[sl] && !livingSlugs.has(sl))
  .map((sl) => [`/people/${sl}/`, dossiers.people[sl].n]);

/* ONE list of correction rows, in FILE order, for both What's new (below) and the corrections page, so the anchor the card links to is the one the page draws. */
export const correctionRows = corrections.rows.map((r) => {
  const f = forOf(r);
  return f.length ? { when: r[0], what: r[1], for: f } : { when: r[0], what: r[1] };
});
export const corrIds = corrIdMap(correctionRows);

export const pulse = buildPulse({
  searched, corrections: correctionRows, worklist,
  counts: { people: people.people.length },
  /* the Atlas's record of which rows it holds (kit/docs/whats-new-receipts.md); null on any failure and never throws, so a build never fails
     because recordatlas.org is unreachable. "booyzen" is this archive's id in the Atlas. */
  receipts: await loadReceipts("booyzen"),
});
