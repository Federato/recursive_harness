#!/usr/bin/env python3
"""Chunk 8, tasks C8-15 to C8-21 -- the traced map, checked point by point.

  15  Point 1 -- the gate field, and the LEVEL it is chosen at.
  16  Point 2 -- two names for one idea in sibling files.
  17  Point 4 -- Building's setter is gated, Contents' is unconditional.
  18  Point 5 -- the insurable-interest record sits at different levels.
  19  Point 6 -- **the one that moves money.**
  20  Point 8 -- the limit reference.
  21  Point 10, and something the census adds.

Derived by hand before the run. Baselines: Building **$60**, Contents **$132**,
Building Special **$12**, Contents Special **$93**.

    19  theft excluded, OccupCategory "Offices" -> PP factor **0.4**
          CONTENTS  COLadj r3(0.186 x 0.4)=0.074 -> r3(0.037) -> **$37**
          BUILDING  reads the RAW SpecialRate    ->            **$12**
        **One submission field, and only one of the two coverages moves.**
        Both factors default to 1.0, which is why the golden case could not
        tell them apart.

    python scripts/cf/65_chunk8_map.py

Exit 0 when every point matches its derivation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g8 = import_module("59_chunk8_golden_case")
fork = import_module("64_chunk8_fork")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")

S, PP, OCCUP = chunk2.STRUCT, chunk4.PP, chunk4.OCCUP
B = S + "/CommercialPropertyStructureBuilding%sCoverage/Premium"
C = PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
THEFT_B = "CommercialPropertyTheftExclusion"
THEFT_C = "CommercialPropertyTheftExclusionPrsnlProp"
BLDG_FILES = [f"CommercialPropertyStructureBuilding{f}CoverageRules.Rule.xml"
              for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]


def occ(sub):
    return (zeros2.structure(sub)["CommercialPropertyOccupClassTable"]
            ["CommercialPropertyOccupClass"][0])


def item(sub):
    return occ(sub)["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][0]


def main() -> int:
    ok = True
    book = book_for(g8.JURIS, g8.ASOF)
    d = book.parent.package.content / "Rules"

    # ---- C8-15
    print("=== 15  Point 1 -- the gate field, and the LEVEL\n")
    sub = g8.building("Basic")
    st = zeros2.structure(sub)
    second = dict(st)
    second["CovType"] = "Building"
    second.pop(f"{g8.LL_FORM}Table", None)
    (sub["CommercialPropertyTable"]["CommercialProperty"][0]
     ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
     ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]
     ).append(second)
    data = g8.run(sub)[0]
    node = data
    for part in S.split("/"):
        node = node.first(part)
    prem = []
    parent = node.parent
    for child in parent.children:
        if child.tag != "CommercialPropertyStructure":
            continue
        cov = child.first("CommercialPropertyStructureBuildingBasicGroupICoverage")
        prem.append(cov.first("Premium").text if cov else None)
    good = prem == ["60", "261"]
    ok &= good
    print(f"    two BUILDINGS on one location : {prem}  (expected "
          f"['60', '261']) {'OK' if good else 'MISMATCH'}")
    print("    **They disagree, and they are allowed to.** `CovType` is on the")
    print("    item, so one building can be a Legal Liability risk while its")
    print("    neighbour is class-rated.")

    sub = g8.contents("Basic")
    items = occ(sub)["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"]
    twin = dict(items[0])
    twin["CovForm"] = "Class Rated Building Only, No Personal Property Coverage"
    items.append(twin)
    data = g8.run(sub)[0]
    node = data
    for part in OCCUP.split("/"):
        node = node.first(part)
    tbl = node.first("CommercialPropertyPersonalPropertyTable")
    forms = [c.first("CovForm").text if c.first("CovForm") else None
             for c in tbl.children]
    good = forms == ["Legal Liability Coverage Form"] * 2
    ok &= good
    print(f"    two CONTENTS items under one occupancy, one asking to differ:")
    print(f"      CovForm after the run : {forms}  "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **They cannot disagree.** `SetCovForm` copies the occupancy's")
    print("    value over each item's, so the second item's request is")
    print("    overwritten. **The gate is not just a different field -- it is")
    print("    a different level, and the level decides who may differ.**")

    # ---- C8-16
    print("\n=== 16  Point 2 -- two names for one idea in sibling files")
    b_data = fork.rate()
    c_data = g8.run(g8.contents("Basic"))[0]
    cross = [
        ("Building record, LegalLiabFactor (Contents' name)",
         read(f"{S}/LegalLiabFactor", b_data)),
        ("Contents record, LegalLiabilityFactor (Building's name)",
         read(f"{PP}/LegalLiabilityFactor", c_data)),
    ]
    for label, val in cross:
        good = val is None
        ok &= good
        print(f"    {label:54s} {val}  (expected None) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    Each name exists in exactly one datadef group and neither")
    print("    record carries the other. **A shared-name scan finds nothing")
    print("    here, because nothing is shared but the idea** -- C8-05's")
    print("    blind spot, demonstrated rather than argued.")

    # ---- C8-17
    print("\n=== 17  Point 4 -- gated on one side, unconditional on the other")
    cr_b = str(read(f"{S}/LegalLiabilityFactor", fork.rate(covtype="Building")))
    cr_c = str(read(f"{PP}/LegalLiabFactor",
                    g8.run(chunk4.submission("Basic"))[0]))
    good = cr_b == "0" and cr_c == "0.5"
    ok &= good
    print(f"    on a CLASS-RATED building : LegalLiabilityFactor = {cr_b}")
    print(f"    on CLASS-RATED contents   : LegalLiabFactor      = {cr_c}   "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **Contents carries a live 0.50 on a risk that is not Legal")
    print("    Liability at all.** Only the premium branch decides whether it")
    print("    matters. That is the fifth populated-and-unused factor in three")
    print("    chunks, and the first that is populated with a REAL value")
    print("    rather than a default.")

    # ---- C8-18
    print("\n=== 18  Point 5 -- the record sits at different levels")
    sub = g8.contents("Basic")
    o = occ(sub)
    o.pop(f"{g8.LL_OCC}Table", None)
    item(sub)[f"{g8.LL_OCC}Table"] = {g8.LL_OCC: [{"AddlInsurableInt": g8.NONE}]}
    wrong = g8.run(sub)[0]
    got = (str(read(f"{PP}/LegalLiabAddlInsurableIntFactor", wrong)),
           str(read(C % "BasicGroupI", wrong)))
    good = got == ("0", "0")
    ok &= good
    print(f"    Contents' record on the ITEM     : factor {got[0]}, premium "
          f"{got[1]}  (expected 0 / 0) {'OK' if good else 'MISMATCH'}")
    right = g8.run(g8.contents("Basic"))[0]
    got = (str(read(f"{PP}/LegalLiabAddlInsurableIntFactor", right)),
           str(read(C % "BasicGroupI", right)))
    good = got == ("1", "132")
    ok &= good
    print(f"    Contents' record on the OCCUPANCY: factor {got[0]}, premium "
          f"{got[1]}  (expected 1 / 132) {'OK' if good else 'MISMATCH'}")
    print("    **Point 1's consequence, one level further in.** Building's")
    print("    record hangs off the item and Contents' off the occupancy, so")
    print("    one Contents item cannot carry a different insurable-interest")
    print("    answer from its siblings either.")

    # ---- C8-19
    print("\n=== 19  Point 6 -- THE ONE THAT MOVES MONEY")
    sub = g8.building("Special")
    zeros2.structure(sub)[f"{THEFT_B}Table"] = {THEFT_B: [{}]}
    b_theft = str(read(B % "Special", g8.run(sub)[0]))
    sub = g8.contents("Special")
    occ(sub)["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][0][f"{THEFT_C}Table"] = {
        THEFT_C: [{}]}
    c_data2 = g8.run(sub)[0]
    c_theft = str(read(C % "Special", c_data2))
    c_adj = str(read(f"{PP}/SpecialCauseOfLossAdjustment", c_data2))
    good = (b_theft, c_theft, c_adj) == ("12", "37", "0.074")
    ok &= good
    print(f"    theft excluded, BUILDING Special : {b_theft:>3s}  "
          f"(expected 12, unchanged)")
    print(f"    theft excluded, CONTENTS Special : {c_theft:>3s}  "
          f"(expected 37, from 93)   COLadj {c_adj}   "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **One submission field, and only one of the two coverages")
    print("    moves.** Building's Legal Liability Special reads the RAW")
    print("    `SpecialRate` and never sees the theft credit; Contents' reads")
    print("    `SpecialCauseOfLossAdjustment` and keeps it -- a 0.4 factor for")
    print("    Offices, so the premium falls by 60%. **Both factors default to")
    print("    1.0, which is exactly why the golden case could not tell the")
    print("    two rate sources apart.**")

    # ---- C8-20
    print("\n=== 20  Point 8 -- the limit reference")
    rows = []
    for f in BLDG_FILES + [
            "CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverageRules.Rule.xml"]:
        t = (d / f).read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetPremium"')
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        w = [m.start() for m in re.finditer(r"<rul:When>", seg)]
        ll = seg[w[1]:(w[2] if len(w) > 2 else len(seg))]
        lim = sorted({x for x in re.findall(r'FromDataDef="([^"]*Limit[^"]*)"',
                                            ll)})
        rows.append((f, lim))
        side = "Building" if f in BLDG_FILES else "Contents"
        form = f.split("Coverage")[0].split("Building")[-1].split(
            "PrsnlProp")[-1]
        print(f"    {side:9s} {form:13s} {lim}")
    good = rows[-1][1] == ["Limit"] and all(r[1] == ["../Limit"]
                                            for r in rows[:4])
    ok &= good
    print(f"    Contents' Special reads a LOCAL `Limit`; every Building form "
          f"reads `../Limit`  {'OK' if good else 'MISMATCH'}")
    print("    The map calls this deliberate on both sides. **It is at least")
    print("    consistent**: the one form that reads a local limit is also the")
    print("    one form whose rate source differs (point 6).")

    # ---- C8-21
    print("\n=== 21  Point 10, and something the census adds")
    t = (d / BLDG_FILES[0]).read_text(encoding="utf-8-sig")
    i = t.find('<rul:Rule Name="SetPremium"')
    seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
    outer = seg[:seg.find("<rul:Choose>")]
    good = "BuildersRiskReportingForm" in outer and "<rul:Else>" not in outer
    ok &= good
    print(f"    Building's outer If names the reporting form and has NO Else: "
          f"{good}  {'OK' if good else 'MISMATCH'}")
    blkt = []
    for f in BLDG_FILES:
        t = (d / f).read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetPremium"')
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        w = [m.start() for m in re.finditer(r"<rul:When>", seg)]
        last = seg[w[-1]:]
        test = last[:last.find("</rul:Test>") + 12]
        blkt.append("IncludedInBlkt" in test)
    good = blkt == [False, False, False, True]
    ok &= good
    form_names = ("BasicGroupI", "BasicGroupII", "Broad", "Special")
    print(f"    Building's last branch tests IncludedInBlkt: "
          f"{dict(zip(form_names, blkt))}")
    print(f"    (expected only Special)  {'OK' if good else 'MISMATCH'}")
    print("    **The map does not mention this.** Three of Building's four")
    print("    forms reach blanket by elimination and the fourth tests for it")
    print("    explicitly -- one coverage, two mechanisms, and the map")
    print("    describes only one of them.")

    print()
    if ok:
        print("Every point matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
