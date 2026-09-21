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
# WHERE THIS BUILD PUTS ITS PAGES, AND WHY IT IS A VARIABLE.
# Eight archives share this machine and more than one session can build THIS repo
# at once. astro EMPTIES its outDir at the start of a build, so a second session
# building into site/dist while this one's gates read it turns every anchor check
# into a failure. On 21 September that was 205 failures over a site reporting
# "0 pages", and not one of them was real.
#   ARCHIVE_OUT=dist-verify sh build.sh     # build somewhere nobody else is using
# THE DEFAULT MUST STAY dist. .github/workflows uploads `path: site/dist`, so a
# different default here would deploy an empty site.
ARCHIVE_OUT="${ARCHIVE_OUT:-dist}"
export ARCHIVE_OUT
OUT="site/$ARCHIVE_OUT"
#
# ONE THING ARCHIVE_OUT CANNOT ISOLATE, AND IT IS NOT OURS TO FIX. The shared
# kit's sitemap.py pins `dist` - `dist = os.path.join(site, "dist")`, no flag,
# derived from the working directory - so it writes sitemap.xml into site/dist
# whatever ARCHIVE_OUT says, and then check:kit correctly reports that robots.txt
# points at a sitemap that is not in the built site. AN ISOLATED RUN THEREFORE
# TRIPS check:kit. Everything else isolates cleanly, which includes the gate that
# produced the 205 false failures. Making the kit tool take a path is a kit
# change and is raised as one rather than patched here, because eight archives
# share that file.
[ "$ARCHIVE_OUT" = "dist" ] || {
  echo "building into $OUT (ARCHIVE_OUT=$ARCHIVE_OUT)"
  echo "  NOTE: check:kit will fail on the sitemap - the kit's sitemap.py pins site/dist."
  echo "        Every other gate isolates. Use this to read gates, not to deploy."
}

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
# THE TWO BUILD STEPS RUN IN SUBSHELLS, AND THAT IS NOT STYLE. They used to read
#     cd site && npm run build >/dev/null && cd ..
# and `set -e` DOES NOT ABORT ON A FAILING COMMAND INSIDE AN && LIST. Proven here
# on 21 September with a three-line script: `cd site && sh -c "exit 143" && cd ..`
# falls through to the next line, leaves the working directory in site/, and the
# script EXITS 0.
#
# WHICH IS HOW A KILLED BUILD COULD HAVE BEEN REPORTED GREEN. When astro was
# reaped, the first pass failed, `cd ..` never ran, the script carried on, and
# python then failed to find site/tools/dossiers.py - two steps downstream of the
# real event, with the trap faithfully reporting "NOT KILLED, exited 2 during:
# dossiers.py". A run earlier the same afternoon failed in exactly that way and
# was written off as load, because it did not reproduce. It was not load. It was
# this, and it had been reproducing all along in whatever step happened to be
# next.
#
# ( cd site && ... ) restores the directory by construction and propagates the
# failure, so `set -e` fires on the step that actually failed.
SIGNALLED=0
on_signal() {
  SIGNALLED=$1
  exit $((128 + $1))
}
# WHAT THIS TRAP CANNOT CATCH, AND IT HAPPENED ON 21 SEPTEMBER. SIGKILL (9) is
# not deliverable to a handler - the kernel stops the process and no trap runs.
# A build here died at load 664 with the log ending mid-pipeline and NOTHING
# printed: no EXIT line, no step name, nothing. That is the signature of a -9,
# and it is the one ending this script cannot narrate.
# SO: A LOG THAT STOPS MID-PIPELINE WITH NO EXIT LINE IS ITSELF THE DIAGNOSIS.
# The trap prints on every ending it can reach, so silence means the process was
# killed outright - check `uptime` before looking for a fault in the data.
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
# The brackets are LOAD-BEARING, not style - see "THE TWO BUILD STEPS RUN IN
# SUBSHELLS" above. `cd site && ... && cd ..` does not abort under set -e.
STEP="first pass - build:pages, checks deliberately skipped"; ( cd site && npm run build:pages >/dev/null )
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
# The brackets are LOAD-BEARING, not style - see "THE TWO BUILD STEPS RUN IN
# SUBSHELLS" above. `cd site && ... && cd ..` does not abort under set -e.
STEP="second pass - the full build WITH every gate"; ( cd site && npm run build >/dev/null )
STEP="links.py"; python3 tools/links.py
STEP="checkatlas.py"; python3 tools/checkatlas.py --data site/src/data --dist "$OUT"
STEP="checkregisters.py"; python3 tools/checkregisters.py --dist "$OUT"
STEP="drift.py"; python3 tools/drift.py
echo "build complete"
