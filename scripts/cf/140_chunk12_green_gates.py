#!/usr/bin/env python3
"""Chunk 12, C12-30 to C12-33 -- Green Upgrades' gate points 2 to 8 (offline).

  C12-30  tables and literals: the 4 tables; the IncreasedCostOfLossPct and
          PeriodOfRestoration literals against the domain tables
  C12-31  states and edition: FL rule by rule; the family across the 5 parents
  C12-32  zero cases, on the engine (the ISO-confirmed ones are in 132 green)
  C12-33  shared names and exclusions: the 5 attachments formula for formula;
          a vandalism exclusion (the family reads the ADJUSTED rate, so it flows)

    python scripts/cf/140_chunk12_green_gates.py
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

gu = import_module("139_chunk12_green_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
RULE, FAILS, expect = gates.RULE, gates.FAILS, gates.expect
KEY = "GreenUpgrades"


def rows(p):
    with open(p, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def rules_of(p):
    return {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(p.read_text(encoding="utf-8-sig"))}


def main() -> int:
    bks = gates.books()
    cw = bks["OR"].parent.package.content

    print("=== C12-30  tables and literals ===\n")
    for t in ("IncreasedCostOfLossPercentConverted", "PeriodOfRestorationFactor",
              "RateModificationFactor", "RelatedExpensesFactor"):
        body = rows(cw / "Rate Tables" / f"{t}.RateTable.csv")[1:]
        filers = [j for j, bk in bks.items() if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists()]
        print(f"  {t:38s} {len(body):2d} CW rows; state files: {filers or 'none'}")
    dom_text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace") for p in (cw / "Domain Tables").glob("*.DomainTable.csv"))
    vals = [r[1] for r in rows(cw / "Rate Tables" / "IncreasedCostOfLossPercentConverted.RateTable.csv")[1:]]
    missing = [v for v in vals if f'"{v}"' not in dom_text]
    print(f"  IncreasedCostOfLossPct table keys not in a domain table: {missing or 'none'}")
    expect("every increased-cost % row is a domain value", str(missing), "[]")

    print("\n=== C12-31  states and edition ===\n")
    for st, bk in sorted(bks.items()):
        sd, par = bk.state.package.content, bk.parent.package.content
        if not (sd / "Rules").exists():
            continue
        kinds, changed = collections.Counter(), []
        for p in sorted((sd / "Rules").glob(f"*{KEY}*")):
            srs, prs = rules_of(p), (rules_of(par / "Rules" / p.name) if (par / "Rules" / p.name).exists() else {})
            for r, body in srs.items():
                if body.count("<rul:") <= 4 and "ProjectName" in body:
                    kinds["pin"] += 1
                elif body == prs.get(r):
                    kinds["same"] += 1
                else:
                    kinds["changed"] += 1
                    if r not in ("ErcProcess", "CalculateTotalPremium"):
                        gone = sorted({x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', prs.get(r, ""))}
                                      - {x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', body)})
                        added = sorted({x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', body)}
                                       - {x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', prs.get(r, ""))})
                        changed.append(f"{p.name[70:-14] or 'Bldg'}::{r} +{added} -{gone}")
        if kinds:
            print(f"  {st} over {par.name}: {dict(kinds)}")
            for c in sorted(set(changed))[:12]:
                print(f"      {c}")
    parents = sorted({bk.parent.package.content for bk in bks.values()}, key=lambda p: p.name)
    base = parents[-1]
    print("\n  Edition basis")
    for pdir in parents:
        n = 0
        for f in (base / "Rules").glob(f"*{KEY}*"):
            o = pdir / "Rules" / f.name
            a, b = rules_of(f), (rules_of(o) if o.exists() else {})
            n += sum(1 for r in set(a) | set(b) if a.get(r) != b.get(r) and r != "InitializeRuleSet")
        sts = sorted(j for j, bk in bks.items() if bk.parent.package.content == pdir)
        print(f"    {pdir.name:20s} ({len(sts):2d} states): {n} rules differ")

    print("\n=== C12-32  zero cases (engine) ===\n")
    R = gu.RECORD
    for label, sub in (("Z1 increased-cost % unfiled ('25%')", gu.submission(dict(R, IncreasedCostOfLossPct="25%"))),
                       ("Z2 limit above the building's (ratio 1.5)", gu.submission(dict(R, Limit="150000"))),
                       ("Z3 injected RateModificationFactor 2", gu.submission(dict(R, RateModificationFactor="2")))):
        data, ip = gates.rate(sub)
        if data is None:
            print(f"  {label:44s} REFUSED {ip[:90]}")
            continue
        print(f"  {label:44s} cells { {f: read(gu.cell(f) + '/Premium', data) for f in ('BasicGroupI', 'BasicGroupII')} }"
              f" ratio {read(gu.GU + '/Ratio', data)} factor {read(gu.GU + '/RateModificationFactor', data)}")

    print("\n=== C12-33  shared names, exclusions, the 5 attachments ===\n")
    R_ = cw / "Rules"

    def reads(name):
        m = rules_of(R_ / f"CommercialProperty{name}Rules.Rule.xml").get("SetGreenUpgradesPremium", "")
        return sorted(x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', m))
    base_ = "IncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndt"
    for form in ("BasicGroupICov", "SpecialCov"):
        b = reads(f"{base_}Bldg{form}")
        for other in ("PersProp", "SpecialClass", "BusInc", "SpclClassBusnIncome"):
            o = reads(f"{base_}{other}{form}")
            print(f"  {form:15s} Bldg vs {other:20s} same fields: {b == o}"
                  f"{'' if b == o else f'  bldg-only {sorted(set(b)-set(o))}  other-only {sorted(set(o)-set(b))}'}")
    for excl in (False, True):
        sub = gu.submission()
        sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
        if excl:
            gates.structure(sub)["CommercialPropertyVandalismExclusionTable"] = {"CommercialPropertyVandalismExclusion": [{}]}
        data, _ = gates.rate(sub)
        print(f"  vandalism exclusion={excl!s:5s} bldg adjusted {read(gu.STRUCT + '/AdjustedBasicGroupIRate', data)}"
              f"  GU BGI ${read(gu.cell('BasicGroupI') + '/Premium', data)}")
    print(f"\nexpectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
