#!/bin/sh
# Full build. The indexes are derived from the built pages, so the order is:
# build → derive → build again so the pages carry the fresh indexes.
#
# The FIRST pass runs `build:pages`, which is the build without the archive
# checks. That is deliberate. dossiers.py writes the /who/ pages, and it cannot
# run until there are built pages to count mentions in — so on any commit that
# adds a person, the first pass necessarily has links pointing at a /who/ page
# that does not exist yet. Running the checks there fails every single time and
# tells you nothing. They run on the SECOND pass, over the finished site, where
# a broken link is a real broken link.
set -e
cd "$(dirname "$0")"
node tools/people-json.mjs
cd site && npm run build:pages >/dev/null && cd ..
python3 tools/dossiers.py
python3 tools/gallery.py
python3 tools/searchindex.py
python3 tools/register.py
cd site && npm run build >/dev/null && cd ..
python3 tools/links.py
python3 tools/checkatlas.py --data site/src/data --dist site/dist
python3 tools/drift.py
echo "build complete"
