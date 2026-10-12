#!/usr/bin/env python3
"""The values here that are a DECISION and not a measurement.

The machinery is the kit's (kit/tools/decisions.py); the probes are this
archive's, because only this archive knows where its own decisions live. The
shape is the D'Arcy session's, from their own error 48: a kit pin moved inside a
commit about something else and three builds printed the correct new value under
«ok» before anybody read it. A decision changing is exactly the case where a
deliberate act should be required, and editing decisions.json in the same commit
IS that act.

Four here. Each is a judgement somebody made, not a number the data produces —
the other 30-odd numbers this build prints move every run for good reasons, and
watching those would be noise with a different shape.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(SITE, "node_modules", "@daviddef", "archive-kit",
                                "kit", "tools"))
from decisions import check                                  # noqa: E402
import checkliving                                           # noqa: E402


def _scripts():
    return json.load(open(os.path.join(SITE, "package.json"), encoding="utf-8"))["scripts"]


def _flag(script, flag):
    """The value given to `flag` in a build script, read from the script itself."""
    m = re.search(re.escape(flag) + r'[= ]"?([^\s"]+)"?', _scripts()[script])
    return m.group(1) if m else None


def kit_pin():
    dep = json.load(open(os.path.join(SITE, "package.json"),
                         encoding="utf-8"))["dependencies"]["@daviddef/archive-kit"]
    return dep.split("#")[-1][:7]


def living_policy():
    return _flag("check:living", "--policy")


def kin_ratchet():
    return int(_flag("check:kin", "--max"))


def named_living():
    """Whoever the living gate itself would find — not a hand-kept list.

    Deliberately routed through the REAL harvest rather than a second reading of
    the data, so this cannot agree with the declaration while disagreeing with
    the gate that enforces the rule. It is how Tersia Booyzen was missed: she is
    recorded b = "living" and no flag anywhere, so a flag-reading probe would
    have declared «nobody living» in perfect agreement with a gate that also
    could not see her.
    """
    import datetime
    living, _presumed, _skipped, _rows = checkliving.from_data(
        os.path.join(SITE, "src", "data"), datetime.date.today())
    return sorted(living)


def goat_counter():
    """Which GoatCounter site this archive reports its reads to.

    A DECISION, and one this repository does not contain. The code lives in the
    SHARED kit (kit/data/archives.json, one row per archive) and is selected by
    matching that row's `base` against the base this site is built at. So an npm
    update of the kit can move it with nothing in this repository changing —
    which is the exact shape of the fault check-decisions.py exists for.

    Resolved the way Base.astro resolves it, not by a second reading: the layout
    does `ring.archives.find(a => a.base === BASE_URL)` and passes `.counter` to
    VisitCount. If the kit renames the field, drops the row, or changes the base
    key, this returns None and the gate refuses rather than agreeing with a
    template that has quietly stopped counting. Seven archives share that file
    and the codes differ by one word, so the failure to fear is not «no counter»
    — it is this archive silently reporting into another family's statistics.
    """
    ring = json.load(open(os.path.join(
        SITE, "node_modules", "@daviddef", "archive-kit", "kit", "data",
        "archives.json"), encoding="utf-8"))
    cfg = open(os.path.join(SITE, "astro.config.mjs"), encoding="utf-8").read()
    m = re.search(r"base:\s*['\"]([^'\"]+)['\"]", cfg)
    base = (m.group(1) if m else "/").rstrip("/")
    # RESOLVED BY ORIGIN, as Base.astro now does it. Matching on base alone is
    # ambiguous the moment two archives share an empty base, and by 12 October
    # 2026 seven of them did, so taking the first match returned the Defranceschi
    # row for every one of them. This check would have reported the old bug as the
    # current truth while the layout, and the built page, said otherwise.
    ms = re.search(r"site:\s*['\"]([^'\"]+)['\"]", cfg)
    def origin(u):
        mo = re.match(r"^(https?://[^/]+)", u or "")
        return mo.group(1) if mo else ""
    site_origin = origin(ms.group(1)) if ms else ""
    on_base = [a for a in ring.get("archives", []) if a.get("base") == base]
    row = next((a for a in on_base if site_origin and origin(a.get("url")) == site_origin),
               on_base[0] if on_base else None)
    return row.get("counter") if row else None


raise SystemExit(check(os.path.join(SITE, "src", "data", "decisions.json"), {
    "kitPin": kit_pin,
    "livingPolicy": living_policy,
    "kinRatchet": kin_ratchet,
    "namedLiving": named_living,
    "goatCounter": goat_counter,
}))
