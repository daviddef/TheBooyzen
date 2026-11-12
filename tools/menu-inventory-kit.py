#!/usr/bin/env python3
"""Runs the kit's menu_inventory.py (the estate's one copy) with THIS archive's docs/ as its declarations folder.
The kit tool reads docs/menu-text-changes.json from beside itself (kit/docs, inside node_modules here), which an archive cannot
commit; this runs the same source with __file__ pointing into this repo, so docs/menu-text-changes.json and docs/menu-scope.json
(the pages in scope) here are the ones read. Run from the repo root:
    python3 tools/menu-inventory-kit.py snapshot DIST OUT.json | sitediff BEFORE_DIST AFTER_DIST | compare BEFORE.json DIST | report BEFORE.json DIST OUT.md"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools", "menu_inventory.py")
os.chdir(os.path.join(HERE, ".."))
g = {"__file__": os.path.join(HERE, "menu_inventory.py"), "__name__": "__main__"}
src = open(KIT, encoding="utf-8").read()
# LOCAL PATCH (not an edit of the kit): the kit's all_blocks() skips /person/, /people/ and /who/, so compare reports their blocks
# as lost even when main is compared with itself. Same workaround as TheMazza's tools. The kit is fixed separately; when it is,
# the assert below fails and this patch is to be deleted.
SKIP = 'if url.startswith(("/person/", "/people/", "/who/")):'
assert SKIP in src, "kit menu_inventory.py no longer has the /person/ /people/ /who/ skip line: remove this patch from tools/menu-inventory-kit.py"
src = src.replace(SKIP, "if False:  # patched locally by tools/menu-inventory-kit.py")
exec(compile(src, KIT, "exec"), g)
