/* WHO SHARES A NAME (one page per person; 23 November 2026, trial).
 *
 * Until now a NAME had a page of its own, /who/<name>/ ("everyone in this archive called ...", about 80 words for a name one
 * person bears, a short list for a name several bear), beside the PERSON's page at /people/<slug>/. David's rule: one page per
 * person, and each person's page links to the other people who carry the same name. The name pages are gone; their addresses
 * redirect (astro.config.mjs reads whoRedirects below) and this file is the one place that says which people share a name.
 *
 * THE SET IS THE ONE THE NAME PAGES USED. It is the old /who/[slug].astro getStaticPaths, moved here unchanged in what it
 * counts, so the people listed under "Others of the same name" are exactly the people /who/ listed:
 *   - a dossier is keyed on its person slug AND on the slug of its name, so every address this archive ever published resolves;
 *   - a dossier stands for everyone of the name: the other men of a shared name are in `also`, with no slug of their own, and
 *     they all live on the one person page (Petrus Jacobus Booysen is three men on one page);
 *   - a dossier named with a qualifier ("George Mountjoy of Kokstad") joins the set of the name before " of " when this
 *     archive has a page for that name and the person slug says the same (<name slug>-of-...).
 * Names READ from FamilySearch index rows and held in no family file (readnames.json) have no person page, so they keep a name
 * page: they are not in these sets.
 *
 * PURE: no imports, so astro.config.mjs can use it (it reads the JSON files itself) and so can the pages.
 */
export const slugify = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase();

/* every row of a dossier: the person, and the other men of a shared name, who share the person's page */
export const rowsOf = (p) => [p, ...(p.also || []).map((a) => ({ ...a, slug: p.slug }))];

/* @param dossiers  Object.values(dossiers.json people)
   @returns Map key -> { key, name, rows, dossiers } in the order the old name pages were made. */
export function nameSets(dossiers) {
  const by = new Map();
  for (const p of dossiers) {
    for (const k of new Set([p.slug, slugify(p.n)])) {
      if (!k) continue;
      if (!by.has(k)) by.set(k, { key: k, name: p.n, rows: [], dossiers: [] });
      const set = by.get(k);
      if (!set.dossiers.includes(p)) { set.dossiers.push(p); set.rows.push(...rowsOf(p)); }
    }
  }
  for (const p of dossiers) {
    const m = /^(.+?) of (.+)$/.exec(String(p.n ?? ""));
    if (!m) continue;
    const base = slugify(m[1]);
    const set = by.get(base);
    if (!set || !String(p.slug).startsWith(`${base}-of-`) || set.dossiers.includes(p)) continue;
    set.dossiers.push(p); set.rows.push(...rowsOf(p));
  }
  return by;
}

const yearOf = (p) => { const m = /\b(1[0-9]{3}|20[0-9]{2})\b/.exec(String(p.b ?? "")); return m ? Number(m[1]) : null; };

/* THE FIRST BEARER of a set: the one a shared name's old address lands on. A bearer who is not living comes first (the page a
   search engine may show), then the earliest born (the first four-digit year in `b`), and a bearer with no year after those
   with one, then slug order. */
export function firstBearer(set, isLiving = () => false) {
  const rank = (p) => [isLiving(p.slug) ? 1 : 0, yearOf(p) ?? 99999, p.slug];
  return [...set.dossiers].sort((a, b) => {
    const x = rank(a), y = rank(b);
    return x[0] - y[0] || x[1] - y[1] || (x[2] < y[2] ? -1 : x[2] > y[2] ? 1 : 0);
  })[0];
}

/* oldest first (the first four-digit year of `b`), those with no year after, then slug order */
export const byAge = (a, b) => (yearOf(a) ?? 99999) - (yearOf(b) ?? 99999) || (a.slug < b.slug ? -1 : a.slug > b.slug ? 1 : 0);

/* a set is SHARED when more than one person bears the name (the old name page said "N people of this name") */
export const isShared = (set) => set.rows.length > 1;

export const SECTION_ID = "others-of-this-name";

/* the old address of every name page -> where it goes now
   a name one person bears -> that person's page; a shared name -> its first bearer's page at the "Others of this name" section */
export function whoRedirects(dossiers, isLiving = () => false, base = "") {
  const out = {};
  for (const [key, set] of nameSets(dossiers)) {
    const to = firstBearer(set, isLiving);
    out[`/who/${key}`] = `${base}/people/${to.slug}/` + (isShared(set) ? `#${SECTION_ID}` : "");
  }
  return out;
}

/* the people of the sets p belongs to, other than p's own page: one row per man, each carrying the page he is on
   (a dossier's other men are on its page: they are not "others" of it). Oldest first, then slug order. */
export function othersOf(p, sets) {
  const seen = new Set([p]);
  const out = [];
  for (const set of sets.values()) {
    if (!set.dossiers.includes(p)) continue;
    for (const q of set.dossiers) {
      if (seen.has(q)) continue;
      seen.add(q);
      out.push(q);
    }
  }
  return out.sort(byAge);
}
