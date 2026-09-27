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


raise SystemExit(check(os.path.join(SITE, "src", "data", "decisions.json"), {
    "kitPin": kit_pin,
    "livingPolicy": living_policy,
    "kinRatchet": kin_ratchet,
    "namedLiving": named_living,
}))
