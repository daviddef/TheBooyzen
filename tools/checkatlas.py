#!/usr/bin/env python3
"""Every event on the atlas must be citable from somewhere on the site.

The Marico entry carried "1898 - JGL Booyzen of Kwaggafontein, in the
field-cornet's papers" for weeks. The papers were the education department's.
It survived because NOTHING ON THE SITE POINTED AT IT: no page cited the line,
so no page could contradict it, and it was written from a memory of a record
rather than from the record.

An event nobody can check is an event nobody can correct.

Every other register here is gated - the kit check, the living-person rule, the
work list. The atlas was the one with no gate, and it is the one that was wrong.

A place entry is citable when EITHER
  - it carries a 'w' of real length, which is where this archive puts its
    argument and its sources, or
  - its name or slug appears somewhere in the built pages outside the atlas
    itself, which means a page is talking about it.

An event whose place satisfies neither is reported. Places pinned on an
inference must additionally carry 'why', which is the field that says so out
loud; that one is a failure, not a warning, because an unexplained approximate
pin is a guess wearing a coordinate.
"""
import os, re, sys, json, glob, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="site/src/data")
    ap.add_argument("--dist", default="site/dist")
    a = ap.parse_args()

    path = os.path.join(a.data, "places.json")
    places = json.load(open(path, encoding="utf-8"))["places"]

    # everything the built site says, minus the atlas page itself
    said = []
    for f in glob.glob(os.path.join(a.dist, "**", "*.html"), recursive=True):
        if os.sep + "atlas" + os.sep in f or os.sep + "places" + os.sep in f:
            continue
        said.append(open(f, encoding="utf-8", errors="ignore").read())
    said = "\n".join(said)

    bad, warn = [], []
    ev = 0
    for p in places:
        name, slug = p.get("n", "?"), p.get("slug", "")
        events = p.get("e") or []
        ev += len(events)
        if p.get("approx") and not str(p.get("why", "")).strip():
            bad.append(f"{name}: pinned approximate with no 'why' - an unexplained pin is a guess wearing a coordinate")
        if not events:
            continue
        grounded = len(str(p.get("w", "")).strip()) > 200 or name in said or (slug and f"/{slug}/" in said)
        if not grounded:
            warn.append(f"{name}: {len(events)} event(s) and nothing on the site discusses this place")

    for w in warn:
        print("  WARN  atlas      " + w)
    for b in bad:
        print("  FAIL  atlas      " + b)
    print(f"  {'FAIL' if bad else 'ok  '}  atlas      {len(places)} places, {ev} events, "
          f"{len(bad)} failing, {len(warn)} unwitnessed")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
