# Roots & Routes (the tree page)

Ten views of the people this archive records as having died, drawn from its own people, households and marriages: hourglass, fan, whole-tree and close-family
maps, Atlas map, movements, kinship, place lanes, eras, lifespans, surnames, an Orphans tab with a "Not drawn yet" list, and the five animated views (Night sky,
Ink ledger, Household, Generations, Where they lived). It is served at `/roots/`.

| File | What it is | Edit by hand? |
|---|---|---|
| `tree.json` | people, parent links (with the grade of each), years, places, the "Not drawn yet" list | no, generated |
| `place_map.json` | each place string with coordinates, country and Record Atlas id; a string with no coordinates is unresolved | no, generated (see below) |
| `place-additions.json` | place strings decided by hand, each with its reason | yes, with a reason |
| `atlas-data.json` | the Record Atlas slice: outlines, regimes, flags, events, collections | no, generated |
| `roots.html`, `roots.embed.html` | the page, whole and as a fragment for the site layout | no, generated |
| `tree.report.json` | counts, and the places not yet resolved | read it |
| `people.ged`, `slugs.json` | intermediates, not committed (a GEDCOM is never published) | no |

## Rebuild

```bash
python3 tools/build-tree-page.py --accept-unique   # rebuild everything and run the page's own checks
python3 tools/build-tree-page.py --check           # exit 1 if the page is older than the data it was built from
```

Needs the Record Atlas checkout (`RECORD_ATLAS`, default `~/Projects/Family Projects/Record Atlas`), read only. The skill's scripts are vendored in `tools/tree-page/`
(the family-tree-page skill, template 1.6.0), so CI and other sessions do not depend on `~/.claude`.

## Where each thing comes from

- **People**: `site/src/data/people.json`. **Parent, child and spouse links**: the households in `site/src/data/kin.js` (a person's first household as a child is the one their page
  draws; a second is not drawn) and the marriages in `site/src/data/marriages.json` (only where each name is borne by one person). Nothing else links anyone.
- **Sex** is kept only where the archive's own data states or entails it, never from a first name: a husband or a wife in a household or marriage; a note that opens "Daughter of ...", "His wife", "Her elder
  son"; or a married woman's birth name in the variants field ("born Mountjoy", "geboren Dormehl"). Everything else is unknown (`u`), and the viewer (skill 1.7.0) then says parent, child, spouse,
  sibling and "uncle or aunt". `tree.report.json` (`adapter.sex_by_source_drawn`) counts each source.
- **Dates and places** are the archive's born and died fields, read the way `tools/familylines.mjs` reads them (`field()` is ported into `tools/build-tree-page.py` and was checked against
  the JavaScript on every person: no difference). A year the field qualifies (c., bef., aft., bapt.) is drawn as an estimate. A burial place is not a death place.
- **Estimates the converter makes** are flagged on the page: "c. 1760" is a birth taken from a child, parent or spouse; "1760–?" is a death not recorded. They are estimates for drawing, not findings.
- **Evidence grade of a parent link** is the household's `via` for the child: read in a record or the direct line (`doc`, `line`) is 2, inferred (`inf`) is 1, the family tree (`tree`) is 0 and is drawn dashed.
- **Colour** is the archive's own line (the `l` of a person in people.json: the seven with most people drawn, the rest together), not a surname spelling. Which spellings are one name is the
  Record Atlas catalogue's to say; nothing here lists them.

## Who is not here

- **No living person is written into the GEDCOM at all**: whoever `tools/livingflags.py` (the kit's `living_rule.py`) calls living or holds out is dropped before the converter sees them. The
  converter then adds its floor: nobody with no death recorded and a birth year in the last 110 years. The page's own gate fails the build on a living person's name.
- **The "Not drawn yet" list names only people with a recorded death** (their name and the link to their own page, which the archive already publishes). Anyone with no death recorded who is not
  drawn is counted in `tree.report.json` (`not_drawn_not_listed_no_death_recorded`) and never named.

## Places are never guessed

1. `data/era-ground.tsv` and `data/era-towns.tsv`: the town and point already decided for a place string (this archive's own `places.json` point, or a hand-written centre); the country is the
   Atlas's `geo.country_of` on the point.
2. `place-additions.json`: strings decided by hand with a reason. A town the Atlas names once (in South Africa, and no other place of that name anywhere in the Atlas) is the Atlas's own place;
   a farm, street, institution or district **inside** a town the Atlas knows is drawn at that town or district seat, and the reason says so (the pin is the town, not the spot); `Cape Colony` and
   `Cape Province` are drawn at the Atlas's own point for the region, and say so.
3. A place the Atlas names once in the country the string names (`--accept-unique`). None of these arose.
4. Everything else is unresolved, listed in `place_map.json` and `tree.report.json`. A person with no place of their own is drawn at a relative's birth place and the page marks it with `*`
   (place taken from a relative, not recorded); with no relative placed, they are not drawn and are listed under "Not drawn yet".
