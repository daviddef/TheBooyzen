/* What is new here, and the archive in numbers: the kit computes it at build time from this archive's own logs (kit/docs/whats-new.md).
   This file is the only Booyzen-specific part: which JSON is which, and the one count no log holds.
   searched.json is {sets, searched}; the kit's rowsOf reads `.searched`. corrections.json is {note, causes, rows} and its rows are
   ARRAYS, [date, what was said, the correction, cause, page] (see pages/corrections.astro), so they are turned into the objects the kit
   reads here, rather than changing the kit for one archive's shape. */
import { buildPulse } from "@daviddef/archive-kit/lib/pulse.js";
import { loadReceipts } from "@daviddef/archive-kit/lib/receipts.js";
import searched from "../data/searched.json";
import corrections from "../data/corrections.json";
import worklist from "../data/worklist.json";
import people from "../data/people.json";

const correctionRows = corrections.rows.map((r) => ({ when: r[0], what: r[1] }));

export const pulse = buildPulse({
  searched, corrections: correctionRows, worklist,
  counts: { people: people.people.length },
  /* the Atlas's record of which rows it holds (kit/docs/whats-new-receipts.md); null on any failure and never throws, so a build never fails
     because recordatlas.org is unreachable. "booyzen" is this archive's id in the Atlas. */
  receipts: await loadReceipts("booyzen"),
});
