#!/usr/bin/env python3
"""Chunk 12, C12-18 to C12-21 -- Utility Services' gate points 2 to 8.

  C12-18  tables and literals (gates 2, 5): the 9 tables, which rows are zero,
          and every Utility / UtilityType / WaitingPeriod literal against the
          domain tables
  C12-19  states and edition (gates 3, 8): FL rule by rule; the family across
          the 5 parent editions
  C12-20  zero cases (gate 4): run on the engine (ISO-confirmed ones in 132)
  C12-21  shared names and exclusions (gates 6, 7): the 5 attachments compared
          formula for formula; a vandalism exclusion (the family reads no
          cause-of-loss adjustment, so it should not move)

    python scripts/cf/134_chunk12_utility_gates.py
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

u = import_module("133_chunk12_utility_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
RULE, FAILS, expect = gates.RULE, gates.FAILS, gates.expect


def rows(p):
    with open(p, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def c12_18(bks):
    print("=== C12-18  tables and literals (gates 2, 5) ===\n")
    cw = bks["OR"].parent.package.content
    tabs = set()
    for f in (cw / "Rules").glob("*UtilityServices*"):
        tabs |= set(re.findall(r'MatrixFromConstant="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    for t in sorted(tabs - {"Pages"}):
        body = rows(cw / "Rate Tables" / f"{t}.RateTable.csv")[1:]
        zero = [r for r in body if r[-1] in ("0", "0.0")]
        filers = [j for j, bk in bks.items()
                  if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists()]
        print(f"  {t:68s} {len(body):2d} rows, {len(zero)} zero-rated; state files: {filers or 'none'}")
    dom_text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                         for p in (cw / "Domain Tables").glob("*.DomainTable.csv"))
    lits = set()
    for f in (cw / "Rules").glob("*UtilityServices*"):
        lits |= set(re.findall(r'FromDataDef="(?:Utility|UtilityType|WaitingPeriod)"[^>]*/>\s*<rul:Constant Type="string">([^<]*)<',
                               f.read_text(encoding="utf-8-sig")))
    missing = sorted(x for x in lits if f'"{x}"' not in dom_text)
    print(f"\n  Utility / UtilityType / WaitingPeriod literals: {len(lits)}; not in any domain table: {missing or 'none'}")
    expect("every Utility-family literal is a domain value", str(missing), "[]")
    print()


def c12_19(bks):
    print("=== C12-19  states and edition basis (gates 3, 8) ===\n")
    filers = sorted(j for j, bk in bks.items() if (bk.state.package.content / "Rules").exists()
                    and any((bk.state.package.content / "Rules").glob("*UtilityServices*")))
    print(f"  states filing Utility Services rule files: {filers}")
    for st in filers:
        bk = bks[st]
        par, sd = bk.parent.package.content, bk.state.package.content
        kinds, changed = collections.Counter(), []
        for p in sorted((sd / "Rules").glob("*UtilityServices*")):
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
                    kinds["parent+more" if "ProjectName" in body else "changed"] += 1
                    if r not in ("ErcProcess", "CalculateTotalPremium"):
                        extra = sorted(set(re.findall(r'FromDataDef="([^"]+)"', body))
                                       - set(re.findall(r'FromDataDef="([^"]+)"', prs.get(r, ""))))
                        gone = sorted(set(re.findall(r'FromDataDef="([^"]+)"', prs.get(r, "")))
                                      - set(re.findall(r'FromDataDef="([^"]+)"', body)))
                        changed.append(f"{p.name[18:-14]}::{r}  +{[e.split('/')[-1] for e in extra]} -{[x.split('/')[-1] for x in gone]}")
        print(f"  {st} over {par.name}: {dict(kinds)}")
        for c in changed:
            print(f"      {c}")
    parents = sorted({bk.parent.package.content for bk in bks.values()}, key=lambda p: p.name)
    base = parents[-1]
    print("\n  Edition basis")
    for pdir in parents:
        n = 0
        for f in (base / "Rules").glob("*UtilityServices*"):
            other = pdir / "Rules" / f.name
            a = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(f.read_text(encoding="utf-8-sig"))}
            b = ({m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(other.read_text(encoding="utf-8-sig"))}
                 if other.exists() else {})
            n += sum(1 for r in set(a) | set(b) if a.get(r) != b.get(r) and r != "InitializeRuleSet")
        tdiff = [t for t in (base / "Rate Tables").glob("UtilitySrvc*.csv")
                 if not (pdir / "Rate Tables" / t.name).exists() or rows(t) != rows(pdir / "Rate Tables" / t.name)]
        sts = sorted(j for j, bk in bks.items() if bk.parent.package.content == pdir)
        print(f"    {pdir.name:20s} ({len(sts):2d} states): {n} rules, {len(tdiff)} tables differ")
    print()


def c12_20():
    print("=== C12-20  zero cases (gate 4) ===\n")
    D, T = u.DD_DETAIL, u.TE_DETAIL
    cases = [
        ("Z1 DD detail CauseOfLoss blank", u.dd_submission(dict(D, CauseOfLoss="")), u.dd_cell, "0"),
        ("Z2 DD UtilityType blank", u.dd_submission(dict(D, UtilityType="")), u.dd_cell, None),
        ("Z3 DD Limit absent (falls back to the building's LimitToUse)",
         u.dd_submission({k: v for k, v in D.items() if k != "Limit"}), u.dd_cell, None),
        ("Z4 TE Other Than Public Utilities (filed rate 0)", u.te_submission(dict(T, UtilityType="Other Than Public Utilities")), u.te_cell, "0"),
        ("Z5 TE WaitingPeriod absent (factor 0.0)", u.te_submission({k: v for k, v in T.items() if k != "WaitingPeriod"}), u.te_cell, "0"),
        ("Z6 TE WaitingPeriod unfiled value", u.te_submission(dict(T, WaitingPeriod="36 hours")), u.te_cell, None),
        ("Z7 DD injected BasicGroupIRate 1.0", u.dd_submission(dict(D, BasicGroupIRate="1.0")), u.dd_cell, "400"),
    ]
    for label, sub, cellf, want in cases:
        data, ip = gates.rate(sub)
        if data is None:
            print(f"  {label:58s} REFUSED {ip[:100]}")
            continue
        c = {f: read(cellf(f) + "/Premium", data) for f in u.FORMS}
        print(f"  {label:58s} {c}")
        if want is not None:
            expect(f"{label[:2]} BGI", c["BasicGroupI"], want)
    print()


def c12_21(bks):
    print("=== C12-21  shared names, exclusions, the 5 attachments (gates 6, 7) ===\n")
    cw = bks["OR"].parent.package.content / "Rules"

    def shape(name):
        s = (cw / f"CommercialProperty{name}Rules.Rule.xml").read_text(encoding="utf-8-sig")
        rs = {m.group(1): m.group(0) for m in RULE.finditer(s)}
        m = rs.get("SetPremium", "")
        return sorted(x.split("/")[-1] for x in re.findall(r'FromDataDef="([^"]+)"', m))

    for form in ("BasicGroupI", "Special", "Earthquake"):
        a = shape(f"UtilityServicesDirectDamageBldgDetail{form}Coverage")
        for other in ("UtilityServicesDirectDamagePrsnlPropDetail", "UtilityServicesDirectDamageSpecialClassDetail"):
            b = shape(f"{other}{form}Coverage")
            print(f"  {form:12s} Bldg vs {other[27:]:22s} same fields read: {a == b}"
                  f"{'' if a == b else f'  bldg-only {sorted(set(a)-set(b))} other-only {sorted(set(b)-set(a))}'}")
        a = shape(f"UtilityServicesTimeElementDetail{form}Coverage")
        b = shape(f"UtilityServicesTimeElementSpclClassBusnIncomeDetail{form}Coverage")
        print(f"  {form:12s} TE BI vs TE SC-BI                    same fields read: {a == b}"
              f"{'' if a == b else f'  bi-only {sorted(set(a)-set(b))} scbi-only {sorted(set(b)-set(a))}'}")

    print("\n  Vandalism exclusion: Utility Services reads no cause-of-loss adjustment")
    for excl in (False, True):
        sub = u.dd_submission()
        sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
        if excl:
            gates.structure(sub)["CommercialPropertyVandalismExclusionTable"] = {
                "CommercialPropertyVandalismExclusion": [{}]}
        d, _ = gates.rate(sub)
        print(f"    exclusion={excl!s:5s}  bldg BGI ${read(u.chunk2.BGI, d)}  US DD BGI ${read(u.dd_cell('BasicGroupI') + '/Premium', d)}")
        if excl:
            expect("vandalism exclusion leaves US DD BGI at $15", read(u.dd_cell("BasicGroupI") + "/Premium", d), "15")
    print()


def main() -> int:
    bks = gates.books()
    c12_18(bks)
    c12_19(bks)
    c12_20()
    c12_21(bks)
    print(f"expectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
