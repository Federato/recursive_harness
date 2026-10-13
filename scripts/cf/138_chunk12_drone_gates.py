#!/usr/bin/env python3
"""Chunk 12, C12-24 to C12-27 -- Unmanned Aircraft's gate points 2 to 9 (offline).

  C12-24  tables and literals (gates 2, 5): every table the family reads,
          rows at countrywide, how many states file their own; the drone
          literals against the domain tables
  C12-25  all 46 states, both layers (gates 3, 8): per state, what its own
          layer does to the family (pins, changes, tables), grouped into
          patterns; the family across the 5 parent editions
  C12-26  zero cases (gate 4)
  C12-27  shared names and exclusions (gates 6, 7), and the golden case's
          messages against the same Contents case without a drone (gate 9)

    python scripts/cf/138_chunk12_drone_gates.py
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from gl_engine.interp.tree import read

d = import_module("137_chunk12_drone_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
g, c4 = d.g, d.c4
RULE, FAILS, expect = gates.RULE, gates.FAILS, gates.expect
KEY = "UnmannedAircraft"


def rows(p):
    with open(p, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def c12_24(bks):
    print("=== C12-24  tables and literals (gates 2, 5) ===\n")
    cw = bks["OR"].parent.package.content
    tabs = set()
    for f in (cw / "Rules").glob(f"*{KEY}*"):
        tabs |= set(re.findall(r'MatrixFromConstant="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    for t in sorted(tabs - {"Pages"}):
        p = cw / "Rate Tables" / f"{t}.RateTable.csv"
        n = len(rows(p)) - 1 if p.exists() else None
        filers = sum(1 for bk in bks.values()
                     if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists())
        print(f"  {t:52s} CW {str(n):>5s} rows; {filers:2d} states file their own")
    dom = cw / "Domain Tables"
    dom_text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace") for p in dom.glob("*.DomainTable.csv"))
    missing = [v for k, v in d.DETAIL.items() if not v.isdigit() and f'"{v}"' not in dom_text]
    print(f"\n  golden-case drone values not in any domain table: {missing or 'none'}")
    expect("every golden drone value is a domain value", str(missing), "[]")
    print()


def c12_25(bks):
    print("=== C12-25  all 46 states, both layers (gates 3, 8) ===\n")
    patterns = collections.defaultdict(list)
    for st, bk in sorted(bks.items()):
        par, sd = bk.parent.package.content, bk.state.package.content
        kinds = collections.Counter()
        changed = []
        if (sd / "Rules").exists():
            for p in sorted((sd / "Rules").glob(f"*{KEY}*")):
                pp = par / "Rules" / p.name
                srs = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(p.read_text(encoding="utf-8-sig"))}
                prs = ({m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(pp.read_text(encoding="utf-8-sig"))}
                       if pp.exists() else {})
                for r, body in srs.items():
                    if body.count("<rul:") <= 4 and "ProjectName" in body:
                        kinds["pin"] += 1
                    elif body == prs.get(r):
                        kinds["same"] += 1
                    else:
                        kinds["changed"] += 1
                        changed.append(f"{p.name[70:-14] or 'UA'}::{r}")
        tabs = sorted(t.name.replace(".RateTable.csv", "") for t in (sd / "Rate Tables").glob("*.RateTable.csv")
                      if any(k in t.name for k in ("UnmannedAircraft", "DroneModification")))
        key = (tuple(sorted(set(changed))), tuple(tabs))
        patterns[key].append(f"{st}({kinds['pin']})")
    for (ch, tabs), sts in sorted(patterns.items(), key=lambda x: -len(x[1])):
        print(f"  {len(sts):2d} states: {', '.join(sts)}")
        print(f"      rules changed: {list(ch) or 'none (pins only)'}")
        print(f"      own tables:    {list(tabs) or 'none'}")
    parents = sorted({bk.parent.package.content for bk in bks.values()}, key=lambda p: p.name)
    base = parents[-1]
    print("\n  Edition basis")
    for pdir in parents:
        n = []
        for f in (base / "Rules").glob(f"*{KEY}*"):
            other = pdir / "Rules" / f.name
            a = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(f.read_text(encoding="utf-8-sig"))}
            b = ({m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(other.read_text(encoding="utf-8-sig"))}
                 if other.exists() else {})
            n += [r for r in set(a) | set(b) if a.get(r) != b.get(r) and r != "InitializeRuleSet"]
        sts = sorted(j for j, bk in bks.items() if bk.parent.package.content == pdir)
        print(f"    {pdir.name:20s} ({len(sts):2d} states): {len(n)} rules differ"
              f"{'  ' + str(sorted(set(n))[:5]) if n else ''}")
    print()


def c12_26():
    print("=== C12-26  zero cases (gate 4) ===\n")
    D = d.DETAIL
    cases = [
        ("Z1 Contents on the Basic form", d.submission(col="Basic"), "0"),
        ("Z2 TypeOfOperations blank", d.submission(dict(D, TypeOfOperations="")), None),
        ("Z3 High risk (Search & Rescue)", d.submission(dict(D, TypeOfOperations="Search & Rescue")), "290"),
        ("Z4 LimitOfInsurance absent (the null is skipped)", d.submission({k: v for k, v in D.items() if k != "LimitOfInsurance"}), None),
        ("Z5 deductible 1,000", d.submission(dict(D, Deductible="1,000")), None),
        ("Z6 newly-acquired extension Yes (1.05)", d.submission(dict(D, CoverageExtensionForNewlyAcquiredPropertyIncludingTemporarySubstitutePropertyAppliesToScheduledCoverageonly="Yes")), None),
        ("Z7 blanket drone, 10,000", d.submission(dict(D, BlanketCoverageUnmannedAircraftAppliesToUnmannedAircraftNotIndividuallyDescribed="Yes", BlanketLimitOfInsurance="10000")), None),
        ("Z8 two scheduled drones", d.submission(details=[dict(D), dict(D, LimitOfInsurance="5000")]), None),
        ("Z9 injected UnmannedAircraftBaseRate 10", d.submission(dict(D, UnmannedAircraftBaseRate="10")), None),
    ]
    for label, sub, want in cases:
        data, ip = gates.rate(sub)
        if data is None:
            print(f"  {label:48s} REFUSED {ip[:100]}")
            continue
        prems = [n.text for n in _all(data, d.DET + "DroneCov", "Premium")]
        print(f"  {label:48s} drone premiums {prems}  base {read(d.DETP + '/UnmannedAircraftBaseRate', data)}"
              f"  ded {read(d.DETP + '/DeductibleFactor', data)}  TSL {read(d.UAP + '/TotalScheduleLimit', data)}"
              f"  skipped {len(ip.null_skips)}")
        if want is not None:
            expect(f"{label[:2]} drone premium", prems[0] if prems else None, want)
    print()


def _all(data, tag, leaf):
    out, stack = [], [data]
    while stack:
        n = stack.pop(0)
        for c in n.children:
            if c.tag == tag:
                out += [x for x in c.children if x.tag == leaf]
            stack.append(c)
    return out


def c12_27():
    print("=== C12-27  shared names, exclusions, messages (gates 6, 7, 9) ===\n")
    data, ip = gates.rate(d.submission())
    base_d, base_ip = gates.rate(c4.submission("Special"))
    extra = sorted(set(ip.messages) - set(base_ip.messages))
    print(f"  golden messages {len(set(ip.messages))}; the same Contents case WITHOUT a drone fires "
          f"{len(set(base_ip.messages))}; messages the drone adds: {extra or 'none'}")
    expect("the drone adds no message of its own", str(extra), "[]")

    print("\n  Exclusions on the Contents record reach the drone through its own factors")
    occ = lambda s: (s["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
                     ["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]
                     ["CommercialPropertyStructure"][0])
    for label, fn in (("none", lambda s: None),
                      ("theft exclusion", lambda s: occ(s).__setitem__(
                          "CommercialPropertyTheftExclusionTable", {"CommercialPropertyTheftExclusion": [{}]})),
                      ("windstorm or hail exclusion (Contents)", lambda s: _pp(s).__setitem__(
                          "CommercialPropertyWindstormOrHailExclusionPrsnlPropTable",
                          {"CommercialPropertyWindstormOrHailExclusionPrsnlProp": [{}]}))):
        sub = d.submission()
        fn(sub)
        dd, _ = gates.rate(sub)
        print(f"    {label:40s} theft {read(c4.PP + '/SpecialTheftExclusionFactor', dd)}"
              f"  wind {read(d.DETP + '/WindstormOrHailExclFactor', dd)}"
              f"  drone ${read(d.DRONE, dd)}  Contents Special ${read(c4.PP + '/CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage/Premium', dd)}")
    print()


def _pp(sub):
    occ = (sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
           ["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
           ["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0])
    return occ["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0]


def main() -> int:
    bks = gates.books()
    c12_24(bks)
    c12_25(bks)
    c12_26()
    c12_27()
    print(f"expectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
