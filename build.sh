#!/bin/sh
# Full build: pages, then the indexes that are derived from the built pages,
# then a rebuild so the pages carry the fresh indexes.
set -e
cd "$(dirname "$0")"
cd site && npm run build >/dev/null && cd ..
python3 tools/dossiers.py
python3 tools/searchindex.py
cd site && npm run build >/dev/null
echo "build complete"
