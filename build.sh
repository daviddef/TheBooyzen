#!/bin/sh
# Full build. The indexes are derived from the built pages, so the order is:
# build → derive → build again so the pages carry the fresh indexes.
set -e
cd "$(dirname "$0")"
cd site && npm run build >/dev/null && cd ..
python3 tools/dossiers.py
python3 tools/gallery.py
python3 tools/searchindex.py
cd site && npm run build >/dev/null
echo "build complete"
