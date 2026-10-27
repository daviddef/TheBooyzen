/* WHO IS ON OUR DIRECT LINE, for a chart that draws people by name (27 October 2026).

   The one answer is src/data/direct-line.json, which the kit's directline.py makes from the story's ribbon. The person
   chart (components/PersonTree.astro) draws relatives as kin.js names them ("Name" or "Name|token"), so this turns the
   file into the same keys the archive's people carry (name and birth field, as kin.js and families.js key them) and
   says, for a relative, what the tint names: the person page's slug, or "gen:N" for a generation of the ribbon that has
   no person page of its own (the son Petrus Jacobus Booysen, who shares his father's page).

   Matching is on name AND birth, never on name: two of the line are father and son of one name. A living person is
   never tinted here (the living get their name and relationships and nothing more). */
import DL from "../data/direct-line.json";
import STORY from "../data/story.json";
import PJ from "../data/people.json";
import D from "../data/dossiers.json";

const keyOf = (p) => p.n + "|" + (p.b || "");
const year = (s) => (String(s ?? "").match(/\d{4}/) || [])[0];
const KEY = new Map();
for (const e of [...(DL.people || []), ...(DL.partners || [])]) {
  const d = D.people[e.slug];
  if (d && !KEY.has(keyOf(d))) KEY.set(keyOf(d), e.slug);
}
for (const e of DL.unlinked || []) {
  const c = (STORY.ribbon.cards || [])[e.generation - 1];
  if (!c || c.living) continue;
  const y = year(c.years);
  const rows = PJ.people.filter((p) => p.n === c.name && (!y || String(p.b || "").includes(y)));
  if (rows.length === 1 && !KEY.has(keyOf(rows[0]))) KEY.set(keyOf(rows[0]), `gen:${e.generation}`);
}
/* a resolved kin.js person -> the data-ours value, or undefined */
export const oursKey = (p) => (p && !p.missing ? KEY.get(keyOf(p)) : undefined);
