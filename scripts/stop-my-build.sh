#!/bin/sh
# Stop THIS archive's build, and nothing else on this machine.
#
# WHY THIS FILE EXISTS. Eight archives on this Mac all build with `astro build`,
# so `pkill -f "astro build"` matches every one of them. One such line reaped
# three of the Lerena session's verify runs, and two other archives were mid
# build at the moment it was checked. The Defranceski session found it in its
# own publish command and fixed it; the D'Arcy session ships a scoped stopper;
# this archive's build.sh tells the reader to "scope it to a path" and until now
# gave them nothing to run, which is advice rather than a remedy.
#
# HOW IT IS SCOPED. Every node process carries its own absolute path in its
# command line, so matching on THIS repository's path selects this repository's
# build and cannot select another archive's. The match is built from the script's
# own location, so a copy of this file in another archive scopes itself to that
# one.
#
# THE LIMIT, STATED PLAINLY. The `sh -c npm run ...` wrapper around a build does
# NOT carry the absolute path and is not matched. Killing the node process is
# enough - the wrapper loses its child and exits - but if you are looking for
# why a wrapper is still listed, that is why.
#
#   sh scripts/stop-my-build.sh --dry    list what would be stopped, kill nothing
#   sh scripts/stop-my-build.sh          stop them
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DRY=0
[ "$1" = "--dry" ] && DRY=1

PIDS=$(pgrep -f "$ROOT/site/node_modules" 2>/dev/null || true)
SELF=$$

if [ -z "$PIDS" ]; then
  echo "nothing of this archive's is building."
  echo "  scope: $ROOT/site/node_modules"
  exit 0
fi

echo "matched in $ROOT:"
for p in $PIDS; do
  [ "$p" = "$SELF" ] && continue
  echo "  $p  $(ps -o command= -p "$p" 2>/dev/null | cut -c1-110)"
done

if [ "$DRY" -eq 1 ]; then
  echo "--dry: nothing killed."
  exit 0
fi

for p in $PIDS; do
  [ "$p" = "$SELF" ] && continue
  kill -TERM "$p" 2>/dev/null || true
done
echo "sent TERM to this archive's build only."
