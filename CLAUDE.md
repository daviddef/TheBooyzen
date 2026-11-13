# Booyzen Family

## Record Atlas

The shared map lives at `../Record Atlas`. Research done here is only
useful to the next person if it gets there.

Invoke the `record-atlas-feedback` skill whenever you finish a search,
open a register, write to an archive, or find a source the atlas does
not list — as you do it, not in a sweep at the end. Record the
FamilySearch waypoint, not just the film number; the skill explains why.

## Writing a found row (What's new)

Every search row that reads as found (a `yes` or `part` outcome, in `searched.json` or derived by `tools/searched_flat.py` from `site/src/data/searched-map.json`) must say two things. The kit gate `check:row-pages` reads `docs/row-pages.json` and fails the build otherwise.

- **Where it went**, for rows dated from 13 Nov 2026: `ev` `[["/page/", "label"]]`, each a built page of this archive, or `"logOnly": true`.
- **Who it is for**, for rows dated from 15 Nov 2026 (`peopleFrom`): either `"for": [["/people/slug/", "Name"], ...]` or `"nobody": true`, never both.
  - Each `for` path is a built page of this archive that is that person's own page (`/people/slug/` here), with the name that page uses, a page once per row, and only people the finding is really about.
  - `"nobody": true` means the pages were read and no new person came out; the reason can go in `what`.
  - Living people: list only people this archive already publishes. Never add a page or a name for a living person to satisfy the gate.

Old rows are not backfilled, and an existing row is never edited: editing a row changes its Atlas key. Nothing about the people goes to the Record Atlas (its receipts hold only the row key).
