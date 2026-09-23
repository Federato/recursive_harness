#!/usr/bin/env python3
"""Chunk 9, C9-15/C9-16/C9-17 -- run the untested reachability mechanisms.

C9-01/02/03 proved ONE of the 20 premium files end to end: Building Basic
Group I, Average election, ISO-confirmed. The census (`67_chunk9_census.py`
§7) only read the other 19 files' `SetPremium` XML; nothing in them had run.
This script runs three more, one per reachability SHAPE:

  C9-15/16  Building Basic Group II and Broad -- the census's other two
            "by elimination" forms (reach the blanket branch through the
            final `When` on `CovType <> "Leasehold Interest"`, the same as
            Basic Group I, not through an explicit top-level `IncludedInBlkt`
            `When`). Read directly (not assumed from the census): both are
            structurally IDENTICAL to Basic Group I's 3-`When` `Choose` --
            When 1 tests the ordinary (non-blanket) path's own eligibility
            (`IncludedInBlkt="No"` explicitly, so a blanket-elected item can
            never land there), When 2 is Legal Liability, When 3
            (`CovType<>"Leasehold Interest"`) is where every blanket-elected,
            non-Leasehold item actually lands, and INSIDE When 3 there is a
            nested `If IncludedInBlkt="Yes"` that is the real blanket gate.
            "By elimination" describes the top-level `Choose`; the blanket
            election itself is still an explicit test, just one level deeper.

            Broad's nested `If` carries an EXTRA test Basic I/II do not:
            `BlktCauseOfLossValue = "Broad"` (Basic I/II test only
            `IncludedInBlkt = "Yes"`). `BlktCauseOfLossValue` is the field
            C6-28/C7-25/C8-14/C9-06 already traced -- copied from the
            Detail record's `CauseOfLoss` by `SetNonEQBlanketValues`. So
            Broad silently zeroes if the Detail record's `CauseOfLoss`
            does not say "Broad", even with `IncludedInBlkt="Yes"` and a
            populated `BlktTotalFullValueAmount` -- a fourth zero-case this
            chunk's census never named.

  C9-16     Do the three forms' blanket `Product`s (read directly in the
            Detail engine's `Set<Form>AvgRate` and `Set<Form>StructureCalc`)
            compute the SAME arithmetic given the same inputs? All three
            `StructureCalc` rules multiply the identical shape (value x
            cause-of-loss-adjustment x deductible-by-location x deductible
            x multi-residential x margin-clauses x LOI), differing only in
            OPERAND NAMES (`BasicGroupICauseOfLossAdjustment` vs `...II...`
            vs `BroadRate` + an added `LimitationsOnCovForRoofSurfacingACV
            Factor` Broad alone carries), inside a single `Product
            DecimalPlaces="0"` -- one rounding at the very end, not
            per-operand. Unlike C8-23's Legal Liability finding (nested
            `Round`s per step, so operand ORDER changed the result), there
            is only one rounding site here, so multiplication order cannot
            move the answer -- confirmed by predicting the naive formula by
            hand and matching the engine exactly for all three forms below.

  C9-17     SC Business Income's Broad/Special `SetPremium` (census: the
            only 2-`When` shape) is read directly: `When 1` is
            `IncludedInBlkt = "No"` (the ordinary path), `When 2` is
            `IncludedInBlkt = "Yes"` (blanket), `Otherwise` a bare
            `Premium := 0.0` that is unreachable given `IncludedInBlkt`'s
            2-value domain (C9-07). Building needs 3 `When`s because it has
            to carve out Legal Liability (its own rate chain) and Leasehold
            Interest (an exclusion) from the ordinary/blanket switch; SC
            Business Income has neither concept, so nothing but the
            ordinary/blanket switch is ever needed. **Not a weaker or
            different reachability mechanism -- the same switch as
            Building's `When 3`, just without the two carve-outs that force
            Building's `Choose` to be 3-deep.** SC BI's blanket branch also
            omits `MultiPremiumAndDispersionCreditFactor` entirely (Building
            includes it) -- a real formula difference, not a shape one.

            The Detail engine confirms the same story one level down:
            `SetBroadAvgRate` and `SetTotalFullValTimesBroadRate` are
            SHARED between Building's Broad forms and SC Business Income's
            Broad form -- routed by the Detail record's OWN `Type` field
            (`"Building Only"` etc. vs `"Business Income With/Without Extra
            Expense"`), not by separate per-group fields. One `BlktIDNum`
            group is either a Building blanket or a Business-Income
            blanket, never both, because `Type` selects exactly one `Sum`
            path in `SetTotalFullValTimesBroadRate`. SC BI's own
            `Set*BusnIncomeCalc` rules (`SetBroadSpclClassBusnIncomeCalc`)
            multiply only `FullBusnIncomeValue x BroadRate` -- no deductible,
            no LOI -- confirming C9-09's finding that Business Income/SC
            Business Income never had an LOI step at all.

Every prediction below was computed by reading the filed rate rows directly
(`book_for(...).table(...)`, not the interpreter) and hand-multiplying in
Decimal, BEFORE the interpreter ran -- same discipline as
`68_chunk9_golden_case.py`.

    python scripts/cf/80_chunk9_c9-15-16-17_reachability.py [--trace]

Exit 0 when all three cases match their hand derivation exactly.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty"
LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
STRUCT_TBL = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure"
S1, S2 = STRUCT_TBL + "[1]", STRUCT_TBL + "[2]"
DETAIL = (CP + "/CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]"
          "/CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]")

SC = LOC + "/CommercialPropertySpecialClassTable/CommercialPropertySpecialClass[1]"
BI_TBL = SC + "/CommercialPropertySpecialClassBusnIncomeTable/CommercialPropertySpecialClassBusnIncome"
BI1, BI2 = BI_TBL + "[1]", BI_TBL + "[2]"

BLKT_ID = 100
BLKT_LIMIT = 300_000
VALUE_A, VALUE_B = 100_000, 200_000


def _base_policy(detail_extra: dict) -> dict:
    detail = {
        "UnitNumber": str(BLKT_ID),
        "TypeOfBlanketRating": "Average",
        "Coinsurance": "90%",          # keeps Detail.CoinsuranceFactor at its 1.0 default
        "TotalLimit": str(BLKT_LIMIT),
    }
    detail.update(detail_extra)
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {"CommercialProperty": [{
            "IRPMFactor": "1.0",
            "PolicyType": "Commercial Property Policy",
            "BlktRated": "Yes",
            "MUBlktRated": "No",
            "CommercialPropertyBlanketRatingTable": {"CommercialPropertyBlanketRating": [{
                "CommercialPropertyBlanketRatingDetailTable": {
                    "CommercialPropertyBlanketRatingDetail": [detail],
                },
            }]},
            "CommercialPropertyLocationTable": {"CommercialPropertyLocation": [{
                "ProtectClass": "3",
            }]},
        }]},
    }


# ---------------------------------------------------------------- C9-15a --
# Building, Basic Group II, two structures. Same rate chain chunk 2 proved
# (CF-CHUNK2-GOLDEN-CASE.md): CauseOfLoss="Basic" (the filed domain value --
# "Basic Group I" is off-domain, chunk 2's own §3 correction), Frame/1-3
# stories -> symbol B, BCEG 4 -> 0.96, BasicGroupIIRatingTerr "Entire State".

BGII_COL_ADJ = Decimal("0.027")              # chunk 2 step 5, CW/OR row, unaffected by value
BGII_DED_A = Decimal("0.98")                 # DeductibleFactor[OR,"1,000",50000-175000,"Basic Group II"]
BGII_DED_B = Decimal("0.98")                 # DeductibleFactor[OR,"1,000",175000-500000,"Basic Group II"]
BGII_LOI_A = Decimal("1.266")                # BasicGroupIILOIFactorBldg[CW] band [100000,125000) FromFactor
BGII_LOI_B = Decimal("1.059")                # BasicGroupIILOIFactorBldg[CW] band [200000,225000) FromFactor

BGII_CALC_A = (VALUE_A * BGII_COL_ADJ * BGII_DED_A * BGII_LOI_A).quantize(Decimal("1"))
BGII_CALC_B = (VALUE_B * BGII_COL_ADJ * BGII_DED_B * BGII_LOI_B).quantize(Decimal("1"))
BGII_AVG = ((BGII_CALC_A + BGII_CALC_B) / BLKT_LIMIT).quantize(Decimal("0.001"))
BGII_PREM_A = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_A) / BLKT_LIMIT) * BGII_AVG
               ).quantize(Decimal("1"))
BGII_PREM_B = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_B) / BLKT_LIMIT) * BGII_AVG
               ).quantize(Decimal("1"))


def bgii_structure(value: int) -> dict:
    return {
        "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
        "CovType": "Building", "CauseOfLoss": "Basic", "Coinsurance": "90%",
        "Limit": str(value), "FullBldgValue": str(value), "Deductible": "1,000",
        "LossCostMultiplier": "1.0", "NumStories": "1-3", "BCEG": "4",
        "IncludedInBlkt": "Yes", "BlktIDNum": str(BLKT_ID),
        "PackageModFactor": "1.0", "MultiPremiumAndDispersionCreditFactor": "1.0",
    }


def bgii_submission() -> dict:
    sub = _base_policy({"Type": "Building Only", "CauseOfLoss": "Basic"})
    loc = sub["CommercialPropertyTable"]["CommercialProperty"][0][
        "CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc["BasicGroupIIRatingTerr"] = "Entire State"
    loc["CommercialPropertyStructureTable"] = {
        "CommercialPropertyStructure": [bgii_structure(VALUE_A), bgii_structure(VALUE_B)],
    }
    return sub


# ---------------------------------------------------------------- C9-15b --
# Building, Broad, two structures. Same rate chain chunk 3 proved
# (CF-CHUNK3-BROAD-STRUCTURE.md): class 0951 -> "Bldg" tier, BroadRate 0.015,
# no cause-of-loss-adjustment step (0 of 47 jurisdictions file one). Broad's
# own SetPremium ALSO tests `BlktCauseOfLossValue = "Broad"` -- Detail.
# CauseOfLoss must say "Broad" too, not just the structures.

BROAD_RATE = Decimal("0.015")
BROAD_DED_A = Decimal("0.97")   # DeductibleFactor[OR,"1,000",50000-175000,"Other Cause Of Loss"]
BROAD_DED_B = Decimal("0.98")   # DeductibleFactor[OR,"1,000",175000-500000,"Other Cause Of Loss"]
BROAD_LOI_A = Decimal("1.237")  # BroadSpecialLOIFactorBldg[CW] band [100000,125000) FromFactor
BROAD_LOI_B = Decimal("1.053")  # BroadSpecialLOIFactorBldg[CW] band [200000,225000) FromFactor

BROAD_CALC_A = (VALUE_A * BROAD_RATE * BROAD_DED_A * BROAD_LOI_A).quantize(Decimal("1"))
BROAD_CALC_B = (VALUE_B * BROAD_RATE * BROAD_DED_B * BROAD_LOI_B).quantize(Decimal("1"))
BROAD_AVG = ((BROAD_CALC_A + BROAD_CALC_B) / BLKT_LIMIT).quantize(Decimal("0.001"))
BROAD_PREM_A = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_A) / BLKT_LIMIT) * BROAD_AVG
                ).quantize(Decimal("1"))
BROAD_PREM_B = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_B) / BLKT_LIMIT) * BROAD_AVG
                ).quantize(Decimal("1"))


def broad_structure(value: int) -> dict:
    return {
        "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
        "CovType": "Building", "CauseOfLoss": "Broad", "Coinsurance": "90%",
        "Limit": str(value), "FullBldgValue": str(value), "Deductible": "1,000",
        "LossCostMultiplier": "1.0",
        "IncludedInBlkt": "Yes", "BlktIDNum": str(BLKT_ID),
        "PackageModFactor": "1.0", "MultiPremiumAndDispersionCreditFactor": "1.0",
    }


def broad_submission() -> dict:
    sub = _base_policy({"Type": "Building Only", "CauseOfLoss": "Broad"})
    loc = sub["CommercialPropertyTable"]["CommercialProperty"][0][
        "CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc["CommercialPropertyStructureTable"] = {
        "CommercialPropertyStructure": [broad_structure(VALUE_A), broad_structure(VALUE_B)],
    }
    return sub


# ---------------------------------------------------------------- C9-17 ---
# SC Business Income, Broad, two records under ONE Special Class item.
# Chunk 7's own chain (CF-CHUNK7-GOLDEN-CASE.md): BroadBaseRate 0.023
# [CW, "Frame" LITERAL, "All Other"], FinalBroadRate = 0.023 (no Factor,
# no adjustment). The blanket StructureCalc for BI types
# (`SetBroadSpclClassBusnIncomeCalc`) multiplies ONLY
# `FullBusnIncomeValue x BroadRate` -- no deductible, no LOI, confirming
# C9-09's "no LOI step at all" finding. Detail.Type must say "Business
# Income With Extra Expense" (not "Building Only") to route
# `SetTotalFullValTimesBroadRate`/`SetBroadAvgRate` down the BI-Sum path.

SCBI_RATE = Decimal("0.023")
SCBI_CALC_A = (VALUE_A * SCBI_RATE).quantize(Decimal("1"))
SCBI_CALC_B = (VALUE_B * SCBI_RATE).quantize(Decimal("1"))
SCBI_AVG = ((SCBI_CALC_A + SCBI_CALC_B) / BLKT_LIMIT).quantize(Decimal("0.001"))
#: SC BI's blanket Product omits MultiPremiumAndDispersionCreditFactor
#: entirely (read directly off SetPremium XML) -- IRPMFactor x PackageModFactor
#: x BlktBroadAvgRate x (value/total) x (limit/100), one factor fewer than
#: Building's.
SCBI_PREM_A = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_A) / BLKT_LIMIT) * SCBI_AVG
               ).quantize(Decimal("1"))
SCBI_PREM_B = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_B) / BLKT_LIMIT) * SCBI_AVG
               ).quantize(Decimal("1"))


def scbi_record(value: int) -> dict:
    return {
        "Limit": str(value), "CovType": "Business Income With Extra Expense",
        "TypeOfRisk": "Mercantile and Non-manufacturing", "Coinsurance": "90%",
        "LossCostMultiplier": "1.0", "MaxPeriod": "No",
        "MonthlyLimitOfIndemnity": "Not Applicable", "CauseOfLoss": "Broad",
        "FullBusnIncomeValue": str(value),
        "IncludedInBlkt": "Yes", "BlktIDNum": str(BLKT_ID),
        "PackageModFactor": "1.0",
    }


def scbi_submission() -> dict:
    sub = _base_policy({"Type": "Business Income With Extra Expense",
                         "CauseOfLoss": "Broad"})
    loc = sub["CommercialPropertyTable"]["CommercialProperty"][0][
        "CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc["CommercialPropertySpecialClassTable"] = {"CommercialPropertySpecialClass": [{
        "ClassDescription": "Towers - Broadcasting Antennas (Cell, Radio and TV)",
        "Limit": "100000", "CovType": "Bldg", "CauseOfLoss": "Broad",
        "PolicyType": "Commercial Property Policy",
        "IncludedInBlkt": "No", "IncludedInBuilding": "No",
        "LossCostMultiplier": "1.0", "Coinsurance": "90%", "Deductible": "1,000",
        "ConstructionType": "Frame", "BasicGroupIISymbol": "B",
        "BasicGroupIIRatingTerr": "Entire State",
        "CommercialPropertySpecialClassBusnIncomeTable": {
            "CommercialPropertySpecialClassBusnIncome": [
                scbi_record(VALUE_A), scbi_record(VALUE_B)],
        },
    }]}
    return sub


CASES = [
    ("C9-15a Building Basic Group II", bgii_submission,
     [("Detail.BasicGroupIIAvgRate", DETAIL + "/BasicGroupIIAvgRate", str(BGII_AVG)),
      ("Structure A Premium",
       S1 + "/CommercialPropertyStructureBuildingBasicGroupIICoverage/Premium",
       str(BGII_PREM_A)),
      ("Structure B Premium",
       S2 + "/CommercialPropertyStructureBuildingBasicGroupIICoverage/Premium",
       str(BGII_PREM_B))]),
    ("C9-15b Building Broad", broad_submission,
     [("Detail.BroadAvgRate", DETAIL + "/BroadAvgRate", str(BROAD_AVG)),
      ("Structure A Premium",
       S1 + "/CommercialPropertyStructureBuildingBroadCoverage/Premium",
       str(BROAD_PREM_A)),
      ("Structure B Premium",
       S2 + "/CommercialPropertyStructureBuildingBroadCoverage/Premium",
       str(BROAD_PREM_B))]),
    ("C9-17 SC Business Income Broad", scbi_submission,
     [("Detail.BroadAvgRate", DETAIL + "/BroadAvgRate", str(SCBI_AVG)),
      ("Record A Premium",
       BI1 + "/CommercialPropertySpecialClassBusnIncomeBroadCoverage/Premium",
       str(SCBI_PREM_A)),
      ("Record B Premium",
       BI2 + "/CommercialPropertySpecialClassBusnIncomeBroadCoverage/Premium",
       str(SCBI_PREM_B))]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")
    print("Hand-derivation, computed from filed rate rows before this ran:")
    print(f"  BGII  CalcA={BGII_CALC_A} CalcB={BGII_CALC_B} AvgRate={BGII_AVG} "
          f"PremA={BGII_PREM_A} PremB={BGII_PREM_B}")
    print(f"  Broad CalcA={BROAD_CALC_A} CalcB={BROAD_CALC_B} AvgRate={BROAD_AVG} "
          f"PremA={BROAD_PREM_A} PremB={BROAD_PREM_B}")
    print(f"  SC BI CalcA={SCBI_CALC_A} CalcB={SCBI_CALC_B} AvgRate={SCBI_AVG} "
          f"PremA={SCBI_PREM_A} PremB={SCBI_PREM_B}\n")

    ok = True
    for label, build, checks in CASES:
        print(f"=== {label}")
        ip = Interpreter(book, rounding=ROUNDING, trace=a.trace,
                          null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{JURIS}", build())
        try:
            ip.run(data)
        except Exception as exc:
            print(f"    RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        for clabel, path, want in checks:
            got = read(path, data)
            try:
                good = got is not None and Decimal(got) == Decimal(want)
            except Exception:
                good = got == want
            ok &= good
            flag = "" if good else f"   <-- expected {want}"
            print(f"    {clabel:20s} = {str(got):>10s}{flag}")
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)}): "
                  + "; ".join(str(m)[:56] for m in ip.messages[:4]))
        print()

    if a.trace:
        pass

    if ok:
        print("All three forms activate blanket, and the arithmetic matches "
              "the hand derivation exactly for every one -- no operand-order "
              "divergence found (C9-16), and SC Business Income's 2-When "
              "shape reaches the same formula (C9-17).")
        return 0
    print("MISMATCH above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
