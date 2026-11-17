#!/usr/bin/env python3
"""The places the corrections page may link, and the flag table it draws beside them.

    python3 tools/build_correction_places.py     # writes site/src/data/correction-places.json and correction-place-flags.json

Rows are the places in site/src/data/places.json that have a page, /places/<slug>/ ; nothing else is linked. The flags are the kit's
placeflags.py over THIS archive's era snapshot (site/src/data/era-snapshot.json: 4 regions, 8 places). It is given NO --alias and NO
--countries file: flag-places.json and flag-countries.json are keyed by a ribbon card's wording and carry evidence for that card, not for a
place page, so using them here would be a guess. A place the snapshot does not assess in a year gets no era flag; a place the kit's table
cannot place today gets no flag at all. Nothing is filled in. `npm run build` runs this before `astro build`."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")
places = json.load(open(os.path.join(DATA, "places.json"), encoding="utf-8"))["places"]
rows = [{"name": p["n"], "href": "/places/%s/" % p["slug"]} for p in places if p.get("slug")]
rows_path = os.path.join(DATA, "correction-places.json")
open(rows_path, "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1) + "\n")
tool = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools", "placeflags.py")
r = subprocess.run([sys.executable, tool, "--snapshot", os.path.join(DATA, "era-snapshot.json"), "--places", rows_path,
                    "--out", os.path.join(DATA, "correction-place-flags.json")])
sys.exit(r.returncode)
