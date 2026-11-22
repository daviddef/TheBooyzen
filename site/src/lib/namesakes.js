/* The people who share a name, as the pages draw them (see namesets.js for which people, and why).
   One entry per MAN: a dossier that holds several men of a shared name (Petrus Jacobus Booysen) gives one entry each, every one
   linking to the page they share. A living person is a name and a town or country and nothing else, as the name pages drew them;
   nobody else has a field here that the name page did not show. */
import d from "../data/dossiers.json";
import { isLivingSlug, livingBySlug } from "./living.js";
import { nameSets, othersOf, rowsOf, firstBearer, isShared, byAge, slugify, SECTION_ID } from "./namesets.js";
import { u } from "./url.js";

export const DOSSIERS = Object.values(d.people);
export const SETS = nameSets(DOSSIERS);
export { SECTION_ID, slugify };

const entry = (q, r) => isLivingSlug(q.slug)
  ? { name: r.n, slug: q.slug, href: u(`/people/${q.slug}/`), life: "", where: livingBySlug(q.slug).w || "", note: "", living: true }
  : {
      name: r.n, slug: q.slug, href: u(`/people/${q.slug}/`),
      life: [r.b, r.d].filter((x) => x && x !== "—").join(" – "),
      /* r.p is a list of [label, href] pairs; the labels are what the name page printed */
      where: (r.p || []).length ? "On: " + r.p.map((x) => (Array.isArray(x) ? x[0] : x)).join(" · ") : "",
      note: r.v && r.v !== r.n ? `Also written ${r.v}` : "",
      living: false,
    };

/* the other people of p's name, oldest first: [] when nobody shares it */
export const othersFor = (p) => othersOf(p, SETS).flatMap((q) => rowsOf(q).map((r) => entry(q, r)));

/* every bearer of a name set, oldest first, for the Every Name list */
export const bearersOf = (set) => set.dossiers.slice().sort(byAge).flatMap((q) => rowsOf(q).map((r) => entry(q, r)));

export const firstOf = (set) => firstBearer(set, isLivingSlug);
export { isShared };
