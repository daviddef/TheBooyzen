# Reach after the estate clean-up (23 Nov 2026): every address that left a menu is still linked from a hub

Made with `menu_inventory.py` (`snapshot` of the build on origin/main 5f5b66f, `compare` against this branch) and by reading the built hub pages.

| address | left the menu | reached from | the hub is in the menu | the hub's built page links it |
|---|---|---|---|---|
| `/tree/` (Our line, drawn) | yes | `/drawn/` | yes (People / Drawn) | yes |
| `/trees/` (The trees) | yes | `/drawn/` | yes | yes |
| `/bloodline/` (Blood relatives, drawn) | yes | `/drawn/` | yes | yes |
| `/timeline/` (The Timeline) | yes | `/drawn/` | yes | yes |
| `/dna/` (The DNA) | yes | `/research/deep-dives/` (also `/sources/`, `/research/`, `/research/sources-and-method/`) | yes (Research / Deep dives) | yes |
| `/disputed/` (Disputed) | yes | `/research/deep-dives/` (also `/sources/`, `/research/`, `/research/sources-and-method/`) | yes | yes |
| `/roots/` (Roots & Routes) | removed on purpose (David, 23 Nov) | not linked from anywhere; the address redirects to `/tree/` | | |

`/direct-line/` (The Spine) stays in Our line and is also named on `/drawn/`. `/roots/view.html` (the bare viewer a person's page frames) is kept.

## compare, the result

- Every in-scope page answers and every text block of every in-scope page stands on the new site, except the `/people/` and `/who/` rows: the tool leaves `/people/` and
  `/who/` out of its search for a block's new home, so it lists all their blocks as lost (a quirk of the tool). Read directly, `/who/` is identical (322 of 322 blocks) and `/people/`
  differs in 143 of 382 rows by the number in "N mentions" and nothing else (the removed `/roots/` page named everyone, so each count is one lower).
- `/roots/` is out of `docs/menu-scope.json`; it answers with a redirect stub to `/tree/` (`dist/roots/index.html`, `noindex`, not in the sitemap). `/drawn/` and `/research/deep-dives/` are in scope.
- Menu links before / after (header menu, from the built home page): Start 3 / 3, Our line 3 / 3, People 10 / 6, Places & families 8 / 8, The name 2 / 2, Research 15 / 14. Total 41 / 36.
