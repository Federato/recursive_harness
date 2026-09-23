#!/usr/bin/env python3
"""Chunk 9, C9-02/C9-03 -- the traced chain, and the Average-vs-Highest election.

C9-02: trace `ErcDoBlanketRating` end to end for Building Basic Group I,
naming every rule in the chain (not just the four the task doc lists), and
confirm the chain's arithmetic scales to a THIRD structure.

C9-03: find the real "highest rate" rule, confirm `TypeOfBlanketRating`
actually switches which chain feeds `BasicGroupIAvgRate`, and hand-derive a
case where Average and Highest predictably diverge.

Every rule body below was read directly from
`CommercialPropertyBlanketRatingDetailRules.Rule.xml` (via `book_for`), not
assumed from the task doc's four names -- two of those four names turned out
to be inexact (see the C9-02 report at the bottom of this docstring).

---------------------------------------------------------------------------
C9-02 -- the real chain, named

`ErcDoBlanketRating` (Countrywide, `DataDefGroup=CommercialPropertyBlanketRatingDetail`)
is a plain `Sequence` of 7 `RunRule`s, not a single formula:

    1. SetCounters
    2. SetPolicyType                          <- NOT in the task doc's four
    3. ErcSetRiskLevelAverageAndHighestRates  <- fans out to 21 RunRules
    4. SetCoinsuranceFactor
    5. SetBldrsRiskFactor
    6. SetTenPctOfTotalFullValueAmount
    7. SetFinalCalculations                   <- fans out to 11 RunRules

Step 3 (`ErcSetRiskLevelAverageAndHighestRates`) is itself a dispatcher, not
a rate; for Building Basic Group I it resolves to:

    SetBuildingPPSpecialClassAverageRates -> SetBasicGroupIStructureCalc
    SetBuildingPPSpecialClassHighestRates -> SetMaxBasicGroupIStructureCalc
    ... (12 sibling *StructureCalc/*Calc pairs for II/Broad/Special/EQ/
         Radioactive/PrsnlProp/SpecialClass, all gated the same way, all
         irrelevant to a Building-only submission because their own `Type`
         gate never matches)
    SetTotalFullValTimesBasicGroupICauseOfLossAdjmt   (feeds the AVERAGE's
                                                        numerator directly)
    SetMaxBasicGroupICauseOfLossAdjmtRate             (feeds the HIGHEST's
                                                        rate directly)

Step 7 (`SetFinalCalculations`) resolves the per-coverage-form averages,
`SetBasicGroupIAvgRate` among them -- the rule that actually writes the
field the task doc names, reading whichever of the two step-3 outputs its
own `TypeOfBlanketRating` branch selects.

**Two of the task doc's four names are inexact, confirmed against the XML,
not assumed:**
  - `SetBasicGroupIStructureCalc` is real, but it is not called directly by
    `ErcDoBlanketRating` -- it is three RunRule hops down
    (`ErcDoBlanketRating` -> `ErcSetRiskLevelAverageAndHighestRates` ->
    `SetBuildingPPSpecialClassAverageRates` -> `SetBasicGroupIStructureCalc`).
  - `SetMaxBasicGroupIStructureCalc` is real (task doc's guess was right on
    the name), reached the same three hops down through
    `SetBuildingPPSpecialClassHighestRates` instead -- but it does NOT feed
    `SetBasicGroupIAvgRate` directly. It feeds `SetMaxBasicGroupICauseOfLossAdjmtRate`
    (a THIRD rule, absent from the task doc), which is what
    `SetBasicGroupIAvgRate`'s Highest branch actually reads. See C9-03.

Each rule's read/write/gate, named directly from its own `<rul:If>`/`<rul:Test>`:

  SetCounters
    reads:  every structure/PP/BI/SpecialClass/SC-BI item's IncludedInBlkt,
            BlktIDNum (+ EQ analog fields), across ALL locations
    writes: Counter (once, guarded by IsNull -- never overwritten on rerun)
    gate:   none at the rule level; the COUNT itself gates nothing here

  SetBasicGroupIStructureCalc (the AVERAGE path)
    reads:  TypeOfBlanketRating, Type (must be one of Building Only/
            Personal Property Only/Builders Risk/Building & PP Combined),
            then per matching structure: FullBldgValue, BasicGroupICauseOf-
            LossAdjustment, DeductibleByLocationFactor, DeductibleFactor-
            BasicGroupI, MultiResidentialPropSpecialCreditFactor, Margin-
            ClausesFactor, BlktBasicGroupILOIFactor
    writes: BasicGroupIStructureCalc = SUM over matching structures of
            round(FullBldgValue x rate-factors, 0) -- each ADDEND rounded
            to whole dollars before summing (`Product DecimalPlaces="0"`
            inside the `ForEach`, confirmed straight off the XML)
    gate:   TypeOfBlanketRating="Average" AND Type in the 4-value list above.
            Any other TypeOfBlanketRating -> Else -> literal 0.0.

  SetMaxBasicGroupIStructureCalc (the HIGHEST path's structure-level piece)
    reads:  TypeOfBlanketRating, Type (same 4-value gate as the Average rule)
            per matching structure: BasicGroupICauseOfLossAdjustment,
            DeductibleByLocationFactor, DeductibleFactorBasicGroupI, Multi-
            ResidentialPropSpecialCreditFactor, MarginClausesFactor,
            BlktBasicGroupILOIFactor -- NOTE: no FullBldgValue in this
            Product at all
    writes: MaxBasicGroupIStructureCalc = MAX over matching structures of
            round(rate-factors ONLY, 3) -- a RATE, not a dollar amount,
            despite sharing "StructureCalc" in its name with the Average
            rule that DOES multiply by value. Confirmed by reading the
            `<rul:Product DecimalPlaces="3">` list directly: FullBldgValue
            is absent.
    gate:   TypeOfBlanketRating="Highest" AND same Type list. Else -> 0.0.

  SetMaxBasicGroupICauseOfLossAdjmtRate (NOT in the task doc; the real
                                          bridge to SetBasicGroupIAvgRate)
    reads:  TypeOfBlanketRating, Type, and picks the winner among THREE
            candidates by nested >= comparisons: MaxBasicGroupIStructure-
            Calc (Building/PP/BuildersRisk/Combined), MaxPrsnlPropBasic-
            GroupICauseOfLossAdjmt (Contents), MaxSpclClassBasicGroupI-
            CauseOfLossAdjmt (Special Class) -- OR, for the two Business
            Income Type values, between MaxBasicGroupIBusnIncomeCalc and
            MaxBasicGroupISpclClassBusnIncomeCalc instead
    writes: MaxBasicGroupICauseOfLossAdjmtRate = whichever candidate wins,
            copied verbatim (guarded by IsNull, first-write-wins)
    gate:   TypeOfBlanketRating="Highest"; Otherwise -> literal 0.0.
            On a Building-only submission the PP/SpecialClass candidates
            are always 0 (no such items), so this always resolves to
            MaxBasicGroupIStructureCalc by construction, not by accident.

  SetBasicGroupIAvgRate (the rule the task doc names correctly)
    reads:  Type (routes Business Income types to a BldrsRiskFactor-free
            Else branch -- irrelevant here, Building takes the Then
            branch), then a `Choose` on TypeOfBlanketRating:
              "Average" -> TotalFullValTimesBasicGroupICauseOfLossAdjmt
                           (= BasicGroupIStructureCalc, same field under
                           its "TotalFullVal..." alias two rules later)
                           / TotalFullValueAmount x CoinsuranceFactor x
                           BldrsRiskFactor, gated further on
                           TotalFullValueAmount > 0
              "Highest" -> MaxBasicGroupICauseOfLossAdjmtRate x
                           CoinsuranceFactor x BldrsRiskFactor
              Otherwise -> 0.0
    writes: BasicGroupIAvgRate, DecimalPlaces=3, guarded by IsNull
            (first-write-wins, same pattern as every rule above)
    gate:   as above -- this IS the switch task C9-03 was asked to confirm.

No writes happen inside any `ForEach AtInputDataDef` loop's OWN body in this
part of the chain (`SetMaxBasicGroupIStructureCalc`'s ForEach only computes a
`Max` argument; the write happens once, outside the loop, at the Detail
level) -- so the C9-01 interpreter bug does not recur here. It stays
confined to `SetNonEQBlanketValues`/`SetNonEQBlanketRatesAndFactors`
(`CommercialPropertyStructureRules.Rule.xml`), already fixed.

---------------------------------------------------------------------------
C9-03 -- does the election actually switch?

Yes, confirmed live, not merely readable in the XML: `SetBasicGroupIAvgRate`
takes a different rule chain entirely depending on `TypeOfBlanketRating`,
and this script runs BOTH values against the same 3-structure submission
and shows two different `BasicGroupIAvgRate`s and two different sets of
per-structure premiums, matching the hand derivation to the cent.

The three structures were chosen so the elections predictably diverge:
LOI factor falls as value rises (`BasicGroupILOIFactorBldg`'s own filed
shape), so the SMALLEST structure (A, $100,000) carries the HIGHEST
per-dollar rate. Averaging blends it down; "Highest" locks the whole
blanket group to structure A's rate alone -- and does so RATE-first
(`SetMaxBasicGroupIStructureCalc` never multiplies by value), not by
picking whichever structure has the largest StructureCalc dollar amount.
That distinction is the finding: "Highest" means highest RATE, not highest
dollar StructureCalc, despite the shared "StructureCalc" name.

    python scripts/cf/69_chunk9_c9-02_chain_trace.py

Exits 0 only if every hand-derived number (3-structure Average confirmation
for C9-02, plus both Average and Highest predictions for C9-03) matches the
engine exactly.
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
from gl_engine.interp.tree import Node, dump, read

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty"
LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
STRUCT_TBL = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure"
S1, S2, S3 = STRUCT_TBL + "[1]", STRUCT_TBL + "[2]", STRUCT_TBL + "[3]"
DETAIL = (CP + "/CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]"
          "/CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]")
PREM_PATH = "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"

BLKT_ID = 100
BLKT_LIMIT = 600_000
VALUE_A, VALUE_B, VALUE_C = 100_000, 200_000, 300_000

#: filed rows, same OR/CW rows C9-01 already proved, plus a third band
COL_ADJ = Decimal("0.239")
DED_A, DED_B, DED_C = Decimal("0.98"), Decimal("0.99"), Decimal("0.99")
LOI_A, LOI_B, LOI_C = Decimal("1.172"), Decimal("1.039"), Decimal("0.969")

STRUCTS = [
    ("A", VALUE_A, DED_A, LOI_A),
    ("B", VALUE_B, DED_B, LOI_B),
    ("C", VALUE_C, DED_C, LOI_C),
]


def q(x: Decimal, places: int) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places))


def hand_derive(rating_type: str) -> tuple[Decimal, dict[str, Decimal]]:
    """Returns (BasicGroupIAvgRate, {label: Premium}) predicted by hand."""
    if rating_type == "Average":
        calcs = {lbl: q(Decimal(v) * COL_ADJ * ded * loi, 0)
                 for lbl, v, ded, loi in STRUCTS}
        total = sum(calcs.values())
        avg_rate = q(total / Decimal(BLKT_LIMIT), 3)
    else:  # Highest
        rates = {lbl: q(COL_ADJ * ded * loi, 3) for lbl, _, ded, loi in STRUCTS}
        avg_rate = max(rates.values())  # CoinsuranceFactor=BldrsRiskFactor=1.0
    premiums = {lbl: q(Decimal(BLKT_LIMIT) / 100 * (Decimal(v) / BLKT_LIMIT) * avg_rate, 0)
                for lbl, v, _, _ in STRUCTS}
    return avg_rate, premiums


def _structure(full_value: int, deductible_factor_hint: str) -> dict:
    """Same differential pattern as `68_chunk9_golden_case.py`: chunk 1's own
    risk (OR, class 0951, Frame, Portland, protection class 3, Basic Group I,
    90% coinsurance, $1,000 deductible), duplicated per structure."""
    return {
        "RatingType": "Class",
        "ClassCode": "0951",
        "ConstructionType": "Frame",
        "CovType": "Building",
        "CauseOfLoss": "Basic Group I",
        "Coinsurance": "90%",
        "Limit": str(full_value),
        "FullBldgValue": str(full_value),
        "Deductible": "1,000",
        "LossCostMultiplier": "1.0",
        "IncludedInBlkt": "Yes",
        "BlktIDNum": str(BLKT_ID),
        "PackageModFactor": "1.0",
        "MultiPremiumAndDispersionCreditFactor": "1.0",
    }


def submission(type_of_blanket_rating: str) -> dict:
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                "BlktRated": "Yes",
                "MUBlktRated": "No",
                "CommercialPropertyBlanketRatingTable": {
                    "CommercialPropertyBlanketRating": [{
                        "CommercialPropertyBlanketRatingDetailTable": {
                            "CommercialPropertyBlanketRatingDetail": [{
                                "UnitNumber": str(BLKT_ID),
                                "Type": "Building Only",
                                "TypeOfBlanketRating": type_of_blanket_rating,
                                "CauseOfLoss": "Basic Group I",
                                "Coinsurance": "90%",
                                "TotalLimit": str(BLKT_LIMIT),
                            }],
                        },
                    }],
                },
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland",
                        "ProtectClass": "3",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [
                                _structure(VALUE_A, "0.98"),
                                _structure(VALUE_B, "0.99"),
                                _structure(VALUE_C, "0.99"),
                            ],
                        },
                    }],
                },
            }],
        },
    }


def run(type_of_blanket_rating: str, trace=False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission(type_of_blanket_rating))
    ip.run(data)
    return data, ip


def check_case(label: str, rating_type: str, trace=False, dump_=False) -> bool:
    print(f"\n--- {label}: TypeOfBlanketRating={rating_type!r} ---")
    avg_rate, premiums = hand_derive(rating_type)
    print(f"  Hand-derived BasicGroupIAvgRate = {avg_rate}")
    for lbl, p in premiums.items():
        print(f"  Hand-derived Premium {lbl} = {p}")

    data, ip = run(rating_type, trace)

    ok = True
    got_rate = read(DETAIL + "/BasicGroupIAvgRate", data)
    good = got_rate == str(avg_rate)
    ok &= good
    print(f"  Engine  BasicGroupIAvgRate      = {got_rate:>10s}"
          f"{'' if good else f'   <-- expected {avg_rate}'}")

    for (lbl, _v, _d, _l), s_path in zip(STRUCTS, (S1, S2, S3)):
        got = read(s_path + PREM_PATH, data)
        want = str(premiums[lbl])
        good = got == want
        ok &= good
        print(f"  Engine  Premium {lbl}                = {str(got):>10s}"
              f"{'' if good else f'   <-- expected {want}'}")

    if ip.messages:
        print(f"  ISO validation messages ({len(ip.messages)}): {ip.messages[:10]}")
    if dump_:
        print(dump(data))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    print("C9-02 -- 3-structure Average confirmation (scales the C9-01 case "
          "from 2 structures to 3, new BlktLimit={:,})".format(BLKT_LIMIT))
    ok1 = check_case("C9-02", "Average", a.trace, a.dump)

    print("\nC9-03 -- Average vs Highest, same 3 structures, election flipped")
    ok2 = check_case("C9-03 (Average, restated)", "Average", a.trace, a.dump)
    ok3 = check_case("C9-03 (Highest)", "Highest", a.trace, a.dump)

    print()
    if ok1 and ok2 and ok3:
        avg_rate_a, _ = hand_derive("Average")
        avg_rate_h, _ = hand_derive("Highest")
        print("All hand-derivations match the engine.")
        print(f"  Average BasicGroupIAvgRate = {avg_rate_a}  vs  "
              f"Highest BasicGroupIAvgRate = {avg_rate_h}  -- CONFIRMED "
              f"DIFFERENT. The election is live: SetBasicGroupIAvgRate's "
              f"Choose reads MaxBasicGroupICauseOfLossAdjmtRate on the "
              f"Highest branch and TotalFullValTimesBasicGroupICauseOfLoss"
              f"Adjmt/TotalFullValueAmount on the Average branch, and this "
              f"run proves both branches actually fire and actually differ.")
        return 0
    print("MISMATCH against the hand derivation -- see the module docstring "
          "and printed diagnostics above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
