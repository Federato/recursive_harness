#!/usr/bin/env python3
"""Chunk 10, C10-13 -- confirm the 12 "dead" EQ tables (census Sec.7,
re-confirmed by `86_chunk10_c10-02_tables.py`'s Bucket D) are genuinely
unreachable, not just missed by a single-hop `MatrixDef="<table>Def"`
regex. Per this project's standing lesson ("check all tables before calling
a factor blank" / "a shared name is a question"), a table can be read
through a `RunRule` INDIRECTION (a `Set*` rule that never contains a
`Lookup` itself, but calls a `Lookup*` rule by name that does) or through a
MatrixDef ALIAS (a Lookup whose `MatrixDef` attribute does not literally
match `"<table>Def"` even though its `MatrixFromConstant` names the table).
`04_shared_names.py`'s own `scan()`/`effective()` functions already built
the transitive-RunRule-following machinery this project uses elsewhere
(added 2026-09-18 specifically because a direct-only scan was blind to
`SetSpecialBaseRate`/`SetSpecialTheftExclusionFactor`); this script reuses
that exact technique, corpus-wide, for the 12 tables instead of trusting
the single-hop regex `86_chunk10_c10-02_tables.py` used.

Two independent checks, both corpus-wide (every `.Rule.xml` file, not just
the 97-file Earthquake population or the 5 parent files):

  1. **MatrixFromConstant alias check** -- does ANY `Lookup` anywhere name
     the table as its `MatrixFromConstant`, regardless of what its
     `MatrixDef` attribute says? This catches a Lookup that reads the
     table's rows under a DIFFERENT declared MatrixDef name (an alias),
     which a `MatrixDef="<table>Def"` regex cannot see.
  2. **Transitive RunRule check** -- build the direct rule graph (every
     rule's own `Lookup` MatrixFromConstants and every `RunRule` it calls),
     then follow `RunRule` edges transitively from EVERY rule in the
     corpus (not scoped to one datadef group, unlike `04_shared_names.py`'s
     own per-chunk scan) to see whether any reachable rule's effective
     matrix set includes the table -- catching the case where a `Set*`
     rule in one of the 97/5-parent files calls a `Lookup*` rule by name
     that itself lives in, or delegates further into, a file the original
     single-hop scan never opened.

    python scripts/cf/97_chunk10_c10-13_dead_tables_transitive.py

Always exits 0 -- an adjudication. If either check finds a table alive
after all, that is reported as a correction to C10-02/the opening census,
not silently absorbed.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"

DEAD_12 = [
    "ASLOBEarthquake", "BCEGEQFactor", "EQRateBldg", "EQRatePrsnlProp",
    "EQRoofTankHazardFactor", "EQSprinklerLeakageOnlyLessThan80PctFactor",
    "EQSubLimitDeductibleFactor", "EarthquakeExposureBaseStatCode",
    "EarthquakeRateGradeStatCode", "SprinklerLeakageEQExtensionBldgRate",
    "SprinklerLeakageEQExtensionPrsnlPropRate", "SprinklerLeakageEQExtensionZoneFactor",
]


def lname(tag):
    return tag.rsplit("}", 1)[-1]


def main() -> int:
    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"
    files = sorted(rules_dir.glob("*.Rule.xml"))
    bodies = {p.name: p.read_text(encoding="utf-8-sig", errors="replace") for p in files}

    print(f"=== 1  MatrixFromConstant alias check, all 12, corpus-wide "
          f"({len(files)} rule files)\n")
    alias_found = {}
    for t in DEAD_12:
        hits = []
        for fn, body in bodies.items():
            for m in re.finditer(
                    r'<rul:Lookup[^>]*MatrixFromConstant="' + re.escape(t) + r'"[^>]*/?>',
                    body):
                # capture the MatrixDef this Lookup actually declares
                seg = m.group(0)
                md = re.search(r'MatrixDef="(\w+)"', seg)
                hits.append((fn, md.group(1) if md else None))
        alias_found[t] = hits
        if hits:
            print(f"    {t:44s} FOUND as MatrixFromConstant in {hits}")
        else:
            print(f"    {t:44s} zero MatrixFromConstant reference anywhere in the corpus")

    print("\n=== 2  Transitive RunRule check, all 12, corpus-wide "
          "(04_shared_names.py's own effective() technique, unscoped)\n")

    # direct[rule_name][group] = (files, matrices, calls)
    import xml.etree.ElementTree as ET
    direct: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(lambda: [set(), set(), set()]))
    for f in files:
        try:
            root = ET.fromstring(bodies[f.name])
        except ET.ParseError:
            continue
        for el in root:
            if lname(el.tag) != "Rule":
                continue
            name = el.get("Name")
            group = el.get("DataDefGroup", "?")
            mats = {d.get("MatrixFromConstant") for d in el.iter()
                    if lname(d.tag) == "Lookup" and d.get("MatrixFromConstant")}
            calls = {(d.get("FileName"), d.get("Rule")) for d in el.iter()
                     if lname(d.tag) == "RunRule" and d.get("Rule")}
            slot = direct[name][group]
            slot[0].add(f.name)
            slot[1] |= mats
            slot[2] |= calls

    # Memoized DFS over the WHOLE corpus's rule graph, computed once. A
    # per-(name,group) cache (rather than 04_shared_names.py's own
    # per-top-level-call `seen` set) is what makes this tractable
    # corpus-wide instead of per-chunk-scoped -- tens of thousands of
    # (rule, group) pairs, each visited once.
    memo: dict[tuple[str, str], frozenset] = {}
    IN_PROGRESS: frozenset = frozenset()

    def effective(name, group):
        key = (name, group)
        if key in memo:
            return memo[key]
        slot = direct.get(name, {}).get(group)
        if slot is None:
            others = direct.get(name, {})
            if len(others) != 1:
                return frozenset()
            (group, slot), = others.items()
            key = (name, group)
            if key in memo:
                return memo[key]
        memo[key] = IN_PROGRESS  # cycle guard
        mats = set(slot[1])
        for _fn, callee in slot[2]:
            if callee is None:
                continue
            for g2 in direct.get(callee, {}):
                sub = effective(callee, g2)
                if sub is not IN_PROGRESS:
                    mats |= sub
        result = frozenset(mats)
        memo[key] = result
        return result

    # Reachable-from-everywhere effective matrix set, unscoped by group --
    # the whole corpus's rule graph, transitively closed.
    all_effective_matrices: set[str] = set()
    for name, groups in direct.items():
        for group in groups:
            all_effective_matrices |= effective(name, group)

    transitive_found = {t: (t in all_effective_matrices) for t in DEAD_12}
    for t, found in transitive_found.items():
        print(f"    {t:44s} reachable via ANY transitive RunRule chain corpus-wide: {found}")

    print("\n=== 3  Verdict\n")
    still_dead = []
    resurrected = []
    for t in DEAD_12:
        alive = bool(alias_found[t]) or transitive_found[t]
        (resurrected if alive else still_dead).append(t)

    print(f"    Still genuinely DEAD (zero MatrixFromConstant reference AND "
          f"zero transitive RunRule path to one, corpus-wide): "
          f"{len(still_dead)} of 12")
    for t in still_dead:
        print(f"        {t}")
    if resurrected:
        print(f"\n    RESURRECTED -- reachable after all, a correction to "
              f"C10-02/the census: {len(resurrected)} of 12")
        for t in resurrected:
            print(f"        {t}: alias={alias_found[t]}  "
                  f"transitive={transitive_found[t]}")
    else:
        print("\n    None resurrected. All 12 are confirmed dead by BOTH the "
              "alias check and the transitive-RunRule check, not just the "
              "single-hop MatrixDef=\"<table>Def\" regex "
              "`86_chunk10_c10-02_tables.py` used. The 12 tables are filed "
              "(all have declared TableDef files -- confirmed separately) "
              "but genuinely unread by any rule, direct or indirect, "
              "anywhere in the countrywide corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
