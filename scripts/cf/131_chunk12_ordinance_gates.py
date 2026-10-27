#!/usr/bin/env python3
"""Chunk 12, C12-12 to C12-15 -- Ordinance or Law's gate points 2 to 8.

Every case is the golden case (`130_chunk12_ordinance_golden_case.py`, OR,
chunk 2's building, "Coverages A and B & C Separate", B 20,000 / C 30,000 ->
$198) with ONE change.

  C12-12  tables and literals (gates 2, 5): the 11 factor tables and who files
          state rows; every CovType literal against DomainOrdinanceOrLawCovType
  C12-13  states and edition (gates 3, 8): AK CA FL NY VA WV rule by rule, the
          45 state-only files, and the family across the 5 parent editions
  C12-14  zero cases (gate 4): all 5 CovType combinations, blank CovType, the
          post-loss option, absent limits, EQ elected without inputs, injection
  C12-15  shared names and exclusions (gates 6, 7), and the Business Income
          attachment (Increased Period of Restoration) on chunk 5's risk

    python scripts/cf/131_chunk12_ordinance_gates.py
"""
from __future__ import annotations

import collections
import copy
import csv
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from gl_engine.interp.tree import read
from gl_engine.interp.values import InterpretError

o = import_module("130_chunk12_ordinance_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
chunk5 = import_module("32_chunk5_golden_case")
g = o.g
OL, STRUCT = o.OL, o.STRUCT
RULE = gates.RULE
FAILS = gates.FAILS
expect = gates.expect
COVS, FORMS = o.COVS, o.FORMS


def rate(sub, juris="OR"):
    try:
        return g.run(sub, juris=juris)
    except InterpretError as exc:
        return None, str(exc)


def on_cells(data):
    """{cov/form: premium} for every cell switched on."""
    out = {}
    for c in COVS:
        for f in FORMS:
            if read(o.cell(c, f) + "/CoverageOnPolicyIndicator", data) == "1":
                out[f"{c}/{f}"] = read(o.cell(c, f) + "/Premium", data)
    return out


def rows(p):
    with open(p, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def c12_12(bks):
    print("=== C12-12  tables and literals (gates 2, 5) ===\n")
    cw = bks["OR"].parent.package.content
    tabs = set()
    for f in (cw / "Rules").glob("*OrdinanceOrLaw*"):
        tabs |= set(re.findall(r'MatrixFromConstant="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    for t in sorted(tabs - {"Pages"}):
        body = rows(cw / "Rate Tables" / f"{t}.RateTable.csv")[1:]
        filers = {j: rows(bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv")[1:]
                  for j, bk in bks.items()
                  if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists()}
        print(f"  {t:54s} CW {body}   state rows: {filers or 'none'}")
    dom = {r[2] for r in rows(cw / "Domain Tables" / "DomainOrdinanceOrLawCovType.DomainTable.csv")[1:]}
    lits = set()
    for f in (cw / "Rules").glob("*OrdinanceOrLaw*"):
        for m in re.finditer(r'FromDataDef="(?:\.\./)*CovType"[^>]*/>\s*<rul:Constant Type="string">([^<]*)<',
                             f.read_text(encoding="utf-8-sig")):
            lits.add(m.group(1).replace("&amp;", "&"))
    print(f"\n  CovType literals compared in the rules: {sorted(lits)}")
    ol_lits = {x for x in lits if x.startswith("Coverage")}
    expect("OL CovType literals all in DomainOrdinanceOrLawCovType", str(ol_lits <= dom), "True")
    print(f"  domain values never tested by name: {sorted(dom - ol_lits) or 'none'}\n")


def c12_13(bks):
    print("=== C12-13  states and edition basis (gates 3, 8) ===\n")
    for st in ("AK", "CA", "FL", "NY", "VA", "WV"):
        bk = bks[st]
        par, sd = bk.parent.package.content, bk.state.package.content
        kinds = collections.Counter()
        changed = []
        only = []
        for p in sorted((sd / "Rules").glob("*OrdinanceOrLaw*")):
            pp = par / "Rules" / p.name
            if not pp.exists():
                only.append(p.name)
                continue
            srs = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(p.read_text(encoding="utf-8-sig"))}
            prs = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(pp.read_text(encoding="utf-8-sig"))}
            for r, body in srs.items():
                if body.count("<rul:") <= 4 and "ProjectName" in body:
                    kinds["pin"] += 1
                elif body == prs.get(r):
                    kinds["same"] += 1
                else:
                    k = "parent+more" if "ProjectName" in body else "changed"
                    kinds[k] += 1
                    if r not in ("ErcProcess", "CalculateTotalPremium"):
                        changed.append(f"{p.name[18:-14]}::{r}")
        print(f"  {st} over {par.name}: {dict(kinds)}; state-only files {len(only)}")
        for c in changed[:8]:
            print(f"      {c}")
        if len(changed) > 8:
            print(f"      ... {len(changed) - 8} more")
    parents = sorted({bk.parent.package.content for bk in bks.values()}, key=lambda p: p.name)
    base = parents[-1]
    print("\n  Edition basis: the family across the parent editions")
    for pdir in parents:
        n = 0
        for f in (base / "Rules").glob("*OrdinanceOrLaw*"):
            other = pdir / "Rules" / f.name
            a = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(f.read_text(encoding="utf-8-sig"))}
            b = ({m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in RULE.finditer(other.read_text(encoding="utf-8-sig"))}
                 if other.exists() else {})
            n += sum(1 for r in set(a) | set(b) if a.get(r) != b.get(r) and r != "InitializeRuleSet")
        sts = sorted(j for j, bk in bks.items() if bk.parent.package.content == pdir)
        print(f"    {pdir.name:20s} ({len(sts):2d} states): {n} rules differ from 20260601")
    print()


def c12_14():
    print("=== C12-14  zero cases (gate 4) ===\n")
    base = dict(o.RECORD)
    combined = dict(base, CovType="Coverages A and B & C Combined",
                    CovBDemolitionLimit="0", CovCIncreasedConstructionLimit="0",
                    CombinedBAndCDemolitionAndIncrdConstrctnLimit="50000")
    cases = [
        ("K1 Coverage A Only", dict(base, CovType="Coverage A Only"), {"CovA/BasicGroupI": "39", "CovA/BasicGroupII": "5"}),
        ("K2 Coverage C Only", dict(base, CovType="Coverage C Only"),
         {"CovC/BasicGroupI": "82", "CovC/BasicGroupII": "10"}),
        ("K3 Coverages A and B", dict(base, CovType="Coverages A and B"),
         {"CovA/BasicGroupI": "39", "CovA/BasicGroupII": "5", "CovB/BasicGroupI": "55", "CovB/BasicGroupII": "7"}),
        ("K4 A and B & C Combined, 50,000", combined,
         {"CovA/BasicGroupI": "39", "CovA/BasicGroupII": "5", "CovBAndC/BasicGroupI": "137",
          "CovBAndC/BasicGroupII": "17"}),
        ("K5 CovType blank", dict(base, CovType=""), None),
        ("K6 post-loss option Yes (1.02)", dict(base, PostLossOrdinanceOrLawOption="Yes"), None),
        ("K7 B and C limits absent", {k: v for k, v in base.items() if "Limit" not in k}, None),
        ("K8 injected Cov A Factor 2.0", dict(base, CommercialPropertyOrdinanceOrLawCovACoverage={"Factor": "2.0"}), None),
    ]
    for label, rec, want in cases:
        data, ip = rate(o.submission(record=rec))
        if data is None:
            print(f"  {label:34s} REFUSED {ip[:100]}")
            continue
        got = on_cells(data)
        print(f"  {label:34s} on={ {k: v for k, v in got.items()} } total={read(OL + '/ErcCalculatedTotalPremium', data)}"
              f" PostLoss={read(OL + '/PostLossFactor', data)}"
              f" CovAFactor={read(OL + '/CommercialPropertyOrdinanceOrLawCovACoverage/Factor', data)}")
        if want is not None:
            for k, v in want.items():
                expect(f"{label[:2]} {k}", got.get(k), v)
            expect(f"{label[:2]} no other cells on", str(sorted(set(got) - set(want))), "[]")
    # K2: Coverage A Only / C Only switch the Cov A factor to 1.0 when C Only
    data, _ = rate(o.submission(record=dict(base, CovType="Coverage C Only")))
    expect("K2 Coverage C Only sets Cov A Factor to 1.0", read(OL + "/CommercialPropertyOrdinanceOrLawCovACoverage/Factor", data), "1.0")
    print()


def c12_15():
    print("=== C12-15  shared names, exclusions, the Business Income attachment (gates 6, 7) ===\n")
    data, _ = rate(o.submission())
    node = data
    for seg in OL.split("/"):
        node = next(c for c in node.children if c.tag == seg)
    st = node.parent.parent
    shared = sorted({c.tag for c in node.children} & {c.tag for c in st.children})
    print(f"  field names on both the OL record and its Structure: {shared}")

    print("\n  Vandalism exclusion: A moves through the final rate, B and C through the COL adjustment")
    for excl in (False, True):
        sub = o.submission()
        sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
        if excl:
            gates.structure(sub)["CommercialPropertyVandalismExclusionTable"] = {
                "CommercialPropertyVandalismExclusion": [{}]}
        d, _ = rate(sub)
        print(f"    exclusion={excl!s:5s} bldg final {read(STRUCT + '/FinalBasicGroupIRate', d)}"
              f" COL {read(STRUCT + '/BasicGroupICauseOfLossAdjustment', d)}  cells {on_cells(d)}")

    print("\n  Increased Period of Restoration on chunk 5's Business Income risk")
    sub = chunk5.submission()
    bi = gates.structure(sub)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
    ipr = "CommercialPropertyOrdinanceOrLawIncreasedPeriodOfRestoration"
    bi[ipr + "Table"] = {ipr: [{"PostLossOrdinanceOrLawOption": "No"}]}
    d, ip = rate(sub)
    if d is None:
        print(f"    REFUSED {ip[:140]}")
        return
    BI = chunk5.BI
    IP = f"{BI}/{ipr}Table/{ipr}"
    fac = read(IP + "/Factor", d)
    fin = read(BI + "/FinalBasicGroupIRate", d)
    lim = read(BI + "/LimitToUse", d)
    prem = read(f"{IP}/{ipr}BasicGroupICoverage/Premium", d)
    print(f"    IPR Factor {fac}, PostLoss {read(IP + '/PostLossFactor', d)}, BI final BGI rate {fin},"
          f" BI LimitToUse {lim}, IPR BGI premium {prem}, BI BGI premium {read(BI + '/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium', d)}")
    if fac and fin and lim:
        want = (Decimal(fac) * 1 - 1) * Decimal(fin)
        want = want.quantize(Decimal("0.001"), ROUND_HALF_UP) * Decimal(lim) / 100
        want = want.quantize(Decimal("1"), ROUND_HALF_UP)
        expect("IPR BGI = round3((Factor-1) x BI final rate) x BI limit/100", prem, str(want))
    expect("IPR Factor (CW row)", fac, "1.2")
    print()


def main() -> int:
    bks = gates.books()
    c12_12(bks)
    c12_13(bks)
    c12_14()
    c12_15()
    print(f"expectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
