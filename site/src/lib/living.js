/* Who is living, as written by tools/livingflags.py (the kit's living_rule.py over
   people.json). The pages read this and never decide it themselves: a second test
   written in JavaScript here would be the second definition the standard forbids.

   A living person is shown with their name, their relationships and their town and
   country, and nothing more - no dates, no records, no notes, no photograph, no
   structured data - and their pages are noindex. */
import L from "../data/living.json";

export const living = L.living;
const bySlug = new Map(L.living.map((x) => [x.slug, x]));
export const isLivingSlug = (slug) => bySlug.has(slug);
export const livingBySlug = (slug) => bySlug.get(slug);
export const nLiving = L.living.length;
/* a person row from people.json (name -> slug is the dossier slug) */
const slugOf = (n) => String(n ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/ÿ/g, "y").replace(/Ÿ/g, "Y").replace(/[^A-Za-z0-9]+/g, "-")
  .replace(/^-+|-+$/g, "").toLowerCase().slice(0, 60);
export const isLivingName = (n) => bySlug.has(slugOf(n));
export const STANDARD =
  "A living person (80 or younger, with no death recorded) is named with their relationships and their town and country, and nothing more.";
