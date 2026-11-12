/* One sentence for each Research page: what it asks, and a number the archive can state from its own data. Counted at build time, so
   it cannot go stale. 12 November 2026 (the research-menu trial, wave 2). */
import questions from "../data/questions.json";
import errands from "../data/errands.json";
import worklist from "../data/worklist.json";
import searched from "../data/searched.json";
import corrections from "../data/corrections.json";
import { RESEARCH } from "./research-menu.js";

const rows = (x) => (Array.isArray(x) ? x : x.rows || []);
const nf = (n) => n.toLocaleString("en-GB");
const wl = rows(worklist);
const n = (s) => wl.filter((r) => r.state === s).length;
const sets = searched.sets || [];
const COUNT = {
  "/open-questions/": `${nf(rows(questions).length)} questions`,
  "/errands/": `${nf((errands.places || []).length)} places to ask`,
  "/worklist/": `${nf(n("next"))} next, ${nf(n("blocked"))} blocked, ${nf(n("done"))} done`,
  "/searched/": `${nf(sets.reduce((n, s) => n + (s.rows || []).length, 0))} searches in ${nf(sets.length)} sets`,
  "/corrections/": `${nf(rows(corrections).length)} claims taken back`,
};
const ASKS = Object.fromEntries(RESEARCH.flatMap((g) => g.items).filter((x) => x.asks).map((x) => [x.href, x.asks]));

export const blurbOf = (x) => {
  const asks = x.blurb || ASKS[x.href] || "";
  const n = COUNT[x.href];
  return [asks, n ? `<em>${n}.</em>` : ""].filter(Boolean).join(" ");
};
