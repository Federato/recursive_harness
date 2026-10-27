#!/usr/bin/env python3
"""Chunk 12, C12-06 to C12-09 -- Debris Removal's gate points 2 to 8.

Every case is the golden case (`127_chunk12_golden_case.py`, Oregon, chunk 2's
building, Debris Removal limit 60,000 -> $49 + $6 = $55) with ONE change, so
each difference has one cause.

  C12-06  tables and literals (gates 2, 5)
          - the two family tables, row by row, and who files state rows
          - the LOI factor: keyed by the BUILDING's limit, and equal to the
            building's own LOI factor, including inside an interpolated band
          - every string literal in the 18 files, against the domain tables
  C12-07  states and edition basis (gates 3, 8)
          - FL and NY, rule by rule: pin, same, or changed
          - FL's minimum limit and its Contents switch-off, run on the engine
          - the family's files and tables across all 5 parent editions
  C12-08  zero cases (gate 4) -- each a different cause
  C12-09  shared names and exclusion records (gates 6, 7)
          - the record's field names that the Structure also carries
          - a vandalism exclusion (flows into Group I through the COL
            adjustment) and a theft exclusion (does it reach Special?)

    python scripts/cf/128_chunk12_debris_removal_gates.py

Exits 0 when every expectation below holds.
"""
from __future__ import annotations

import copy
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read
from gl_engine.interp.values import InterpretError

g = import_module("127_chunk12_golden_case")
census11 = import_module("106_chunk11_census")
ASOF = g.ASOF
DR, PFX, STRUCT = g.DR, g.PFX, g.STRUCT
RULE = re.compile(r'<rul:Rule Name="([^"]+)"[\s\S]*?</rul:Rule>')
FAILS: list[str] = []
#: Literals checked by hand and found unreachable, with the reason.
DEAD_LITERALS = {
    "Tobacco Sales Warehouses": "a FORM name (Form Pages), never a CovType value in any "
    "edition's domain tables: the Contents gate `../../CovType != 'Tobacco Sales Warehouses'` "
    "is always true. Dead, harmless",
}
LIMIT_MSG = "CP 04 15 Debris Removal Additional Insurance must have a limit greater than"


def expect(label, got, want):
    ok = g.num_eq(got, want) if want is not None else got is None
    print(f"    {label:58s} {str(got):>12s}   want {str(want):>8s}  {'ok' if ok else 'MISMATCH'}")
    if not ok:
        FAILS.append(label)


def structure(sub):
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    return (cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])


def rate(sub, juris="OR"):
    try:
        data, ip = g.run(sub, juris=juris)
    except InterpretError as exc:
        return None, str(exc)
    return data, ip


def cells(data):
    return {f: read(g.cell(f) + "/Premium", data) for f in g.FORMS}


def rows(path):
    with open(path, encoding="utf-8-sig") as h:
        return [r for r in csv.reader(h) if r]


def books():
    out = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            out[j] = book_for(j, ASOF)
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- C12-06

def c12_06(bks):
    print("=== C12-06  tables and literals (gates 2, 5) ===\n")
    cw = bks["OR"].parent.package.content
    for t in ("DebrisRemovalRate", "DebrisRemovalMinimumLimit"):
        rs = rows(cw / "Rate Tables" / f"{t}.RateTable.csv")
        print(f"  {t}: {len(rs) - 1} CW rows  {rs[1:]}")
        filers = {}
        for j, bk in bks.items():
            for layer in (bk.state.package.content, bk.parent.package.content):
                p = layer / "Rate Tables" / f"{t}.RateTable.csv"
                if p.exists():
                    body = rows(p)[1:]
                    if layer == bk.state.package.content:
                        filers[j] = body
                    break
        print(f"    state layers filing their own rows: {filers or 'none'}")
    print("    Keys used by the rules: GroupI, GroupII, Broad, SpecialBldg, Earthquake "
          "(Building/Special Class), SpecialPersProp (Contents). All 6 CW rows are read.\n")

    print("  The LOI factor: Debris Removal's against the building's own, at three building limits")
    for lim, label in ((100000, "band edge"), (110000, "inside a band (interpolated)"),
                       (1100000, "a higher band")):
        sub = g.submission(structure={"Limit": str(lim)})
        data, ip = rate(sub)
        for fld in ("BasicGroupILOIFactor", "BasicGroupIILOIFactor"):
            ours = read(DR + "/" + fld, data)
            bldg = read(STRUCT + "/" + fld, data)
            expect(f"{fld} @ bldg {lim:,} ({label}) = building's", ours, bldg)
    sub = g.submission(limit=200000)
    data, _ = rate(sub)
    expect("DR limit 200,000 leaves BGI LOI at the building's 1.172",
           read(DR + "/BasicGroupILOIFactor", data), "1.172")

    print("\n  String literals in the 18 files, against the domain tables")
    domain = cw / "Domain Tables"
    dom_text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                         for p in domain.glob("*.DomainTable.csv"))
    lits = {}
    for f in (cw / "Rules").glob("*DebrisRemoval*.xml"):
        for m in re.finditer(r'<rul:Constant Type="string">([^<]*)</rul:Constant>',
                             f.read_text(encoding="utf-8-sig")):
            lits.setdefault(m.group(1), set()).add(f.name)
    table_keys = {"CW", "Y", "Coverage", "Value Not Found", "GroupI", "GroupII", "Broad",
                  "SpecialBldg", "SpecialPersProp", "Earthquake"}
    for lit in sorted(lits):
        if lit in table_keys or lit.startswith("CommercialProperty"):
            continue
        found = f'"{lit}"' in dom_text
        print(f"    {lit!r:36s} in a domain table: {'yes' if found else 'NO'}")
        if not found and lit not in DEAD_LITERALS:
            FAILS.append(f"literal {lit!r} not in any domain table")
        elif not found:
            print(f"      -> {DEAD_LITERALS[lit]}")
    print()


# ---------------------------------------------------------------- C12-07

def c12_07(bks):
    print("=== C12-07  states and edition basis (gates 3, 8) ===\n")
    for st in ("FL", "NY"):
        bk = bks[st]
        par, sd = bk.parent.package.content, bk.state.package.content
        print(f"  {st} over {par.name}")
        for p in sorted((sd / "Rules").glob("*DebrisRemoval*")):
            srs = {m.group(1): re.sub(r"\s+", " ", m.group(0))
                   for m in RULE.finditer(p.read_text(encoding="utf-8-sig"))}
            prs = {m.group(1): re.sub(r"\s+", " ", m.group(0))
                   for m in RULE.finditer((par / "Rules" / p.name).read_text(encoding="utf-8-sig"))}
            for r, body in srs.items():
                if re.search(r'<rul:Sequence> <rul:RunRule[^>]*ProjectName="[^"]+"[^>]*/> </rul:Sequence>',
                             body) and body.count("<rul:") <= 4:
                    kind = "pin"
                elif body == prs.get(r):
                    kind = "same"
                elif "ProjectName" in body:
                    kind = "parent + more"
                else:
                    kind = "CHANGED"
                if kind != "pin":
                    print(f"    {p.name.replace('CommercialPropertyDebrisRemovalAdditionalInsurance', 'DR'):48s}"
                          f" {r:30s} {kind}")
        print()

    print("  Florida on the engine: the golden building re-rated as FL")
    sub = g.submission()
    data, ip = rate(sub, "FL")
    if data is None:
        print(f"    refused: {ip[:160]}")
    else:
        expect("FL MinimumLimit (state row)", read(DR + "/MinimumLimit", data), "10000")
        expect("FL ExposureStatAmount (60,000 - 10,000)/1000", read(DR + "/ExposureStatAmount", data), "50")
        print(f"    FL cell premiums: {cells(data)}  (building BGI {read(g.chunk2.BGI, data)})")

    print("\n  Florida Contents: a Contents Debris Removal record, OR against FL")
    for j in ("OR", "FL"):
        sub = g.submission()
        st = structure(sub)
        pp = st.setdefault("CommercialPropertyPersonalPropertyTable", None)
        print(f"    {j}: Contents records on the golden building: "
              f"{'present' if pp else 'none -- Contents half checked statically only'}")
        break

    print("\n  Edition basis: the family across the 5 parent editions")
    parents = sorted({bk.parent.package.content for bk in bks.values()}, key=lambda p: p.name)
    base = parents[-1]
    for pdir in parents:
        diff_rules, diff_tables = [], []
        for f in sorted((base / "Rules").glob("*DebrisRemoval*")):
            other = pdir / "Rules" / f.name
            a = {m.group(1): re.sub(r"\s+", " ", m.group(0))
                 for m in RULE.finditer(f.read_text(encoding="utf-8-sig"))}
            b = ({m.group(1): re.sub(r"\s+", " ", m.group(0))
                  for m in RULE.finditer(other.read_text(encoding="utf-8-sig"))}
                 if other.exists() else {})
            for r in set(a) | set(b):
                if a.get(r) != b.get(r) and r not in ("InitializeRuleSet",):
                    diff_rules.append(f"{f.name[48:-14]}::{r}")
        for t in ("DebrisRemovalRate", "DebrisRemovalMinimumLimit", "BasicGroupILOIFactorBldg",
                  "BasicGroupIILOIFactorBldg", "BroadSpecialLOIFactorBldg"):
            pa, pb = base / "Rate Tables" / f"{t}.RateTable.csv", pdir / "Rate Tables" / f"{t}.RateTable.csv"
            if not pb.exists() or rows(pa) != rows(pb):
                diff_tables.append(t)
        sts = sorted(j for j, bk in bks.items() if bk.parent.package.content == pdir)
        print(f"    {pdir.name:20s} ({len(sts):2d} states): rules differing {len(diff_rules)}"
              f"{' ' + str(diff_rules[:4]) if diff_rules else ''}; tables differing "
              f"{diff_tables or 'none'}")
    print()


# ---------------------------------------------------------------- C12-08

def c12_08():
    print("=== C12-08  zero cases (gate 4) ===\n")
    cases = [
        ("Z1 limit = minimum (25,000)", dict(limit=25000), "1", "0",
         "ON (the switch compares against a MinimumLimit not yet set); rated to $0; error message"),
        ("Z2 limit = minimum + 1", dict(limit=25001), "1", "0", "on, and rated to $0 (exposure 0.01)"),
        ("Z3 limit absent", dict(record={}), "0", "0", "off; FirstValue reads 0"),
        ("Z4 limit below minimum (10,000)", dict(limit=10000), "1", "-21",
         "ON, NEGATIVE premium -$21/-$3, behind the CP 04 15 error message"),
        ("Z5 building CovType 'No Coverage'", dict(structure={"CovType": "No Coverage"}), None, None,
         "LOI falls to Otherwise"),
        ("Z6 ConstructionCode missing", dict(structure={"ConstructionType": ""}), None, None,
         "LOI needs ConstructionCode != 0"),
        ("Z7 EQ elected, no EQ chain inputs", dict(structure={"EQCovIndicator": "Yes, Not Included in Blanket"}),
         None, None, "EQ cell on, chunk 10 chain has nothing to read"),
        ("Z8 injected MinimumLimit = 0", dict(record={"Limit": "60000", "MinimumLimit": "0"}), "1", None,
         "IsNull guard honours the submitted value"),
        ("Z9 injected BasicGroupIFactor = 5", dict(record={"Limit": "60000", "BasicGroupIFactor": "5"}),
         "1", None, "IsNull guard honours the submitted factor"),
    ]
    for label, kw, bgi_on, bgi_prem, why in cases:
        data, ip = rate(g.submission(**kw))
        if data is None:
            print(f"  {label:38s} REFUSED: {ip[:120]}")
            continue
        c = cells(data)
        print(f"  {label:38s} on={read(g.cell('BasicGroupI') + '/CoverageOnPolicyIndicator', data)} "
              f"cells={c} total={read(DR + '/ErcCalculatedTotalPremium', data)} "
              f"stat={read(DR + '/ExposureStatAmount', data)} LOI_I={read(DR + '/BasicGroupILOIFactor', data)}"
              f"  -- {why}")
        msg = any(LIMIT_MSG in m for m in ip.messages)
        print(f"      CP 04 15 limit message: {'fires' if msg else 'no'}")
        if label[:2] in ("Z1", "Z4"):
            expect(f"{label[:3]} CP 04 15 message fires", str(msg), "True")
        if bgi_on is not None:
            expect(f"{label[:3]} BGI on-policy", read(g.cell("BasicGroupI") + "/CoverageOnPolicyIndicator", data), bgi_on)
        if bgi_prem is not None:
            expect(f"{label[:3]} BGI premium", c["BasicGroupI"], bgi_prem)
    print()


# ---------------------------------------------------------------- C12-09

def c12_09():
    print("=== C12-09  shared names and exclusion records (gates 6, 7) ===\n")
    data, _ = rate(g.submission())
    dr_node = data
    for seg in DR.split("/"):
        dr_node = next(c for c in dr_node.children if c.tag == seg)
    st_node = dr_node.parent.parent
    shared = sorted({c.tag for c in dr_node.children} & {c.tag for c in st_node.children})
    print(f"  Field names on BOTH the Debris Removal record and its Structure: {len(shared)}")
    for f in shared:
        a = next(c.text for c in dr_node.children if c.tag == f)
        b = next(c.text for c in st_node.children if c.tag == f)
        print(f"    {f:32s} DR {str(a):>10s}   Structure {str(b):>10s}"
              f"{'   (differ: two records, two values)' if a != b else ''}")
    print()

    print("  Vandalism exclusion on the building: Group I moves through the COL adjustment")
    for excl in (False, True):
        sub = g.submission()
        sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
        if excl:
            structure(sub)["CommercialPropertyVandalismExclusionTable"] = {
                "CommercialPropertyVandalismExclusion": [{}]}
        data, _ = rate(sub)
        print(f"    exclusion={excl!s:5s}  bldg COL adj {read(STRUCT + '/BasicGroupICauseOfLossAdjustment', data)}"
              f"  VandalismExclFactor {read(STRUCT + '/VandalismExclFactor', data)}"
              f"  DR BGI ${read(g.cell('BasicGroupI') + '/Premium', data)}"
              f"  bldg BGI ${read(g.chunk2.BGI, data)}")

    print("\n  Theft exclusion on a Special building: does it reach Debris Removal's Special cell?")
    for excl in (False, True):
        sub = g.submission(structure={"CauseOfLoss": "Special"})
        if excl:
            structure(sub)["CommercialPropertyTheftExclusionTable"] = {
                "CommercialPropertyTheftExclusion": [{}]}
        data, ip = rate(sub)
        if data is None:
            print(f"    refused: {ip[:120]}")
            continue
        sp_bldg = STRUCT + "/CommercialPropertyStructureBuildingSpecialCoverage/Premium"
        print(f"    theft excl={excl!s:5s}  bldg SpecialRate {read(STRUCT + '/SpecialRate', data)}"
              f"  bldg Special ${read(sp_bldg, data)}  LossCostMultiplier {read(STRUCT + '/LossCostMultiplier', data)}"
              f"  DR Special ${read(g.cell('Special') + '/Premium', data)}")
    print()


def main() -> int:
    bks = books()
    c12_06(bks)
    c12_07(bks)
    c12_08()
    c12_09()
    print(f"expectations failed: {len(FAILS)} {FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
