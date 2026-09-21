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

# WHY THIS TRAP EXISTS, AND IT COST TWO ARCHIVES A DAY BETWEEN THEM.
# `set -e` exits with whatever status the failing step returned, and prints
# nothing about it. A gate refusing the build and a build KILLED by the machine
# are then indistinguishable: both are a non-zero exit after several steps have
# printed "ok". On 21 September this machine ran at load 289 with eleven
# concurrent astro builds across the estate, and builds here died repeatedly
# with EXIT=143 - SIGTERM - which reads exactly like a check saying no. The
# Lerena session lost two rounds hunting a data fault that was never there, the
# Defranceski session wrote one of its own off as bad data, and this archive
# invented a three-strikes rule to tell weather from fault.
#
# A signal death is >128: 143 is 128+15, SIGTERM. That one number is the whole
# distinction, and naming the STEP it died in is what turns it into an action.
# Adopted from the D'Arcy session, which added it for the SIGTERM case and then
# had it catch something it was not written for within the hour.
#
# AND IT MISLABELLED SOMETHING WITHIN THE HOUR TOO, WHICH IS WHY THE SECOND
# BRANCH SAYS "NOT KILLED" RATHER THAN "REFUSED". A run died EXIT=2 because a
# step ran from the wrong directory and python could not find the file; the trap
# announced "a gate said no, this is a real finding" and it was neither. The
# test it performs is >128, which separates KILLED from NOT KILLED and nothing
# else. Anything finer has to be read off the output. That run did not reproduce
# - one failure is the weather, three identical ones are a fault.
STEP="starting up"

# THE SIGNAL MUST BE TRAPPED, NOT INFERRED FROM $?. Found by the D'Arcy session
# on 21 September, in the branch of this trap neither of us had tested.
#
# $? inside an EXIT handler is the status of the last CHILD. That is 143 when a
# pkill reaps the `astro` process and `set -e` propagates it up - which is the
# case both archives watched work and took as proof. It is NOT 143 when the
# signal is sent to THE SCRIPT ITSELF, where $? is whatever finished last and is
# usually zero. And a signal to the script itself is exactly what
# `pkill -f build.sh` does, which is the pattern that was actually run here.
#
# Their trap announced EXIT=0 and a clean pass over a killed build. This one was
# worse in its own way: it read $? as 0, took the `exit 0` branch, and printed
# NOTHING AT ALL while the shell still died 143 - a partial log, no explanation
# and a non-zero code, which is precisely the ambiguity the trap was added to
# remove. The instrument went silent in the one case it was built for.
#
# So the signals are caught and a flag is set, and the EXIT handler reads the
# flag BEFORE it reads $?. The two kill paths print different sentences on
# purpose: a reader chasing a reaped child should not be shown the case where
# somebody killed the whole run, and the remedies differ.
SIGNALLED=0
on_signal() {
  SIGNALLED=$1
  exit $((128 + $1))
}
trap 'on_signal 15' TERM
trap 'on_signal 2'  INT
trap 'on_signal 1'  HUP

on_exit() {
  st=$?
  if [ "$SIGNALLED" -ne 0 ]; then
    echo ""
    echo "EXIT=$((128 + SIGNALLED))  KILLED by signal $SIGNALLED sent to THIS SCRIPT during: $STEP"
    echo "          Somebody or something killed the whole build, not a step inside it."
    echo "          A bare \`pkill -f \"astro build\"\` or \`pkill -f build.sh\` on this machine"
    echo "          reaps every archive's build, not only its own. Use the scoped one:"
    echo "              sh scripts/stop-my-build.sh --dry   # list"
    echo "              sh scripts/stop-my-build.sh         # stop only this archive"
    echo "          Nothing is wrong with the data. Re-run it."
    exit $((128 + SIGNALLED))
  fi
  [ "$st" -eq 0 ] && exit 0
  if [ "$st" -gt 128 ]; then
    echo ""
    echo "EXIT=$st  KILLED by signal $((st - 128)) during: $STEP"
    echo "          A STEP was reaped - the build process itself, not this script."
    echo "          THIS IS NOT A GATE REFUSING. Nothing is wrong with the data."
    echo "          $(uptime | sed 's/.*\(load[^,]*.*\)/\1/')"
    echo "          Re-run it. Three identical failures is a fault; one is the weather."
  else
    echo ""
    echo "EXIT=$st  NOT KILLED - a step exited $st during: $STEP"
    echo "          Usually a gate refusing, and it said why above. But NOT KILLED is"
    echo "          not the same as REFUSED: this branch also catches a missing file,"
    echo "          a wrong directory or a typo. Read the output before believing it."
  fi
  exit "$st"
}
trap on_exit EXIT

STEP="people.json from people.js"; node tools/people-json.mjs
STEP="first pass - build:pages, checks deliberately skipped"; cd site && npm run build:pages >/dev/null && cd ..
STEP="dossiers.py"; python3 tools/dossiers.py
STEP="gallery.py"; python3 tools/gallery.py
# SEARCHINDEX IS A COMMITTED ARTEFACT THAT ONLY THIS SCRIPT REGENERATES, AND
# THAT ASYMMETRY BITES EXACTLY ONCE, CONFUSINGLY. `npm run build` - which is all
# GitHub Actions runs - VALIDATES site/public/searchindex.json against the built
# pages and never rebuilds it. So the moment a page is removed or a route
# renamed, the committed index still points at it, and the next build refuses
# with "N of M rows point at pages that were not built". It reads like a
# dangling link in the pages and it is not: it is a stale artefact.
# THE RECOVERY IS ONE COMMAND - `python3 tools/searchindex.py` - or just run
# this script, which does it below, between the two passes and in the right
# order. Warned about by the D'Arcy session, which hit it folding pages away;
# confirmed here by planting a row pointing at a page that was never built and
# watching the kit's check name it.
STEP="searchindex.py"; python3 tools/searchindex.py
STEP="register.py"; python3 tools/register.py
STEP="second pass - the full build WITH every gate"; cd site && npm run build >/dev/null && cd ..
STEP="links.py"; python3 tools/links.py
STEP="checkatlas.py"; python3 tools/checkatlas.py --data site/src/data --dist site/dist
STEP="checkregisters.py"; python3 tools/checkregisters.py --dist site/dist
STEP="drift.py"; python3 tools/drift.py
echo "build complete"
