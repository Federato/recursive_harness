#!/usr/bin/env python3
"""Chunk 12, C12-36 to C12-39 -- Dependent Properties' gate points 2 to 8 (offline).

  C12-36  tables and literals; the 4 inert files read in full (what makes
          them inert)
  C12-37  states (FL) and the family across the 5 parent editions
  C12-38  zero cases on the engine (the ISO-confirmed ones are in 132 dependent)
  C12-39  shared names and exclusions: the Business Income and SC Business
          Income attachments compared rule for rule; a theft exclusion on the
          Special form (the Special rate reads SpecialTheftExclusionFactor)

    python scripts/cf/142_chunk12_dependent_gates.py
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

dp = import_module("141_chunk12_dependent_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
RULE, FAILS, expect = gates.RULE, gates.FAILS, gates.expect
KEY = "DependentProp"


def rows(p):
    with open(p, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def rules_of(p):
    return {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(p.read_text(encoding="utf-8-sig"))}


def main() -> int:
    bks = gates.books()
    cw = bks["OR"].parent.package.content
    R = cw / "Rules"

    print("=== C12-36  tables, literals, the inert files ===\n")
    tabs = set()
    for f in R.glob(f"*{KEY}*"):
        tabs |= set(re.findall(r'MatrixFromConstant="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    for t in sorted(tabs - {"Pages"}):
        body = rows(cw / "Rate Tables" / f"{t}.RateTable.csv")[1:]
        filers = [j for j, bk in bks.items() if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists()]
        print(f"  {t:44s} {len(body):3d} CW rows; state files: {filers or 'none'}")
    inert = [f for f in sorted(R.glob(f"*{KEY}*"))
             if set(re.findall(r'<rul:Rule Name="([^"]+)"', f.read_text(encoding="utf-8-sig")))
             <= {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess"}]
    print(f"\n  inert files (system rules only): {len(inert)}")
    for f in inert:
        rs = rules_of(f)
        print(f"    {f.name[18:-14]}: rules {sorted(rs)}; "
              f"CalculateTotalPremium sums {len(re.findall('RunRule', rs.get('CalculateTotalPremium', '')))} children,"
              f" writes nothing but totals")
    expect("the census's 4 inert files", str(len(inert)), "4")
    dom_text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace") for p in (cw / "Domain Tables").glob("*.DomainTable.csv"))
    missing = [v for v in (dp.ONLY, dp.NOT_ONLY) if f'"{v}"' not in dom_text]
    print(f"  nature-of-dependency values not in a domain table: {missing or 'none'}")
    expect("both nature-of-dependency values are domain values", str(missing), "[]")

    print("\n=== C12-37  states and edition ===\n")
    for st, bk in sorted(bks.items()):
        sd, par = bk.state.package.content, bk.parent.package.content
        if not (sd / "Rules").exists() or not any((sd / "Rules").glob(f"*{KEY}*")):
            continue
        kinds, changed = collections.Counter(), set()
        for p in sorted((sd / "Rules").glob(f"*{KEY}*")):
            srs = rules_of(p)
            prs = rules_of(par / "Rules" / p.name) if (par / "Rules" / p.name).exists() else {}
            for r, body in srs.items():
                if body.count("<rul:") <= 4 and "ProjectName" in body:
                    kinds["pin"] += 1
                elif body == prs.get(r):
                    kinds["same"] += 1
                else:
                    kinds["changed"] += 1
                    if r not in ("ErcProcess", "CalculateTotalPremium"):
                        a = {x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', body)}
                        b = {x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', prs.get(r, ""))}
                        changed.add(f"{r} +{sorted(a - b)} -{sorted(b - a)}")
        print(f"  {st} over {par.name}: {dict(kinds)}")
        for c in sorted(changed)[:10]:
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

    print("\n=== C12-38  zero cases (engine) ===\n")
    D = dp.DETAIL
    for label, sub in (("Z1 nature of dependency unfiled", dp.submission(details=[dict(D, NatureOfDependency="Sometimes")])),
                       ("Z2 no dependent property at all", dp.submission(details=[])),
                       ("Z3 injected record BasicGroupIRate 1", dp.submission(record={"BasicGroupIRate": "1"}))):
        data, ip = gates.rate(sub)
        if data is None:
            print(f"  {label:40s} REFUSED {ip[:90]}")
            continue
        print(f"  {label:40s} BGI {read(dp.BFP + '/' + dp.BF + 'BasicGroupICoverage/Premium', data)}"
              f"  BGII {read(dp.BFP + '/' + dp.BF + 'BasicGroupIICoverage/Premium', data)}"
              f"  rate {read(dp.BFP + '/BasicGroupIRate', data)}")

    print("\n=== C12-39  shared names, exclusions, the two attachments ===\n")
    pairs = collections.Counter()
    for f in sorted(R.glob("*DependentProp*SpclClassBusnIncome*")):
        twin = R / f.name.replace("SpclClassBusnIncome", "")
        if not twin.exists():
            continue
        a, b = rules_of(f), rules_of(twin)
        norm = lambda x: re.sub(r"SpclClassBusnIncome|DataDefGroup=\"[^\"]+\"|FileName=\"[^\"]+\"|FromDataDef=\"[^\"]*\"|AtDataDef=\"[^\"]*\"|AtOutputDataDef=\"[^\"]*\"|AtInputDataDef=\"[^\"]*\"", "", x)
        diff = sorted(r for r in set(a) & set(b) if norm(a[r]) != norm(b[r]))
        pairs["same" if not diff else "differ"] += 1
        if diff:
            print(f"  {twin.name[18:-14]} vs SC-BI twin: {len(diff)} rules differ beyond names/paths: {diff[:4]}")
    print(f"  BI vs SC-BI file pairs: {dict(pairs)}")
    for excl in (False, True):
        sub = dp.submission(col="Special")
        if excl:
            gates.structure(sub)["CommercialPropertyTheftExclusionTable"] = {"CommercialPropertyTheftExclusion": [{}]}
        data, _ = gates.rate(sub)
        print(f"  theft exclusion={excl!s:5s} BI SpecialTheftExclusionFactor {read(dp.c5.BI + '/SpecialTheftExclusionFactor', data)}"
              f"  DP Special ${read(dp.BFP + '/' + dp.BF + 'SpecialCoverage/Premium', data)}")
    print(f"\nexpectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
