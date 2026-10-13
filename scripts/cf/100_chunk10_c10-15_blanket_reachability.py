#!/usr/bin/env python3
"""Chunk 10, C10-15 -- the genuinely different angle C10-11 didn't test.

C10-11 (`95_chunk10_c10-11_all_groups_chain.py`) already ran ONE real
submission per premium group and matched every one's CORE (`EQCovIndicator=
"Yes, Not Included in Blanket"`) chain to a hand derivation -- Building $6
(golden case), Contents $5, Business Income $5, Special Class $6, SC
Business Income $5. For that branch, C10-15 is fully SUBSUMED by C10-11;
re-running the identical case here would add nothing.

What neither the golden case nor C10-11 ever touched -- named explicitly as
out of scope by both (`CF-CHUNK10-GOLDEN-CASE.md` section 6; C10-11's own
module docstring) -- is EQ's THIRD `SetPremium` branch: `EQCovIndicator=
"Yes, Included in Blanket"`, reading `BlktEQAvgRate`/`EQLimitToUse` instead
of the plain `FinalEQRate`. That is a genuinely different reachability
question, not a re-run of the same one, so this script builds and runs it.

Read directly off the XML before writing this submission (not assumed):

  * `SetEQBlanketRatesAndFactors` (`CommercialPropertyStructureRules.Rule.xml`)
    copies `BlktEQAvgRate` from the Detail record's own `EQAvgRate`, matched
    by `UnitNumber = EQCauseOfLossCovBlktIDNum` -- **a SEPARATE blanket-ID
    field from the ordinary chain's own `BlktIDNum`**, not the same field
    reused. A structure could in principle be EQ-blanket-rated under one
    group and ordinarily blanket-rated under a different one; this project's
    census never named this second blanket-ID field.
  * `SetEQAvgRate` (`CommercialPropertyBlanketRatingDetailRules.Rule.xml`,
    `TypeOfBlanketRating="Average"`) = `round((TotalFullValTimesEQCauseOfLoss
    Adjmt / TotalFullValueAmount) x CoinsuranceFactor x BldrsRiskFactor, 3)`
    -- the SAME shape as chunk 9's own ordinary blanket AvgRate, just fed by
    an EQ-prefixed numerator.
  * `SetEQStructureCalc` (same file) = `round(FullBldgValue x
    EQCauseOfLossAdjustment x EQDeductibleByLocationFactor x
    MarginClausesFactor x EQDeductibleFactor, 0)`, summed across every
    structure whose `EQCauseOfLossCovBlktIDNum` matches the Detail's
    `UnitNumber` -- reads the SAME `EQCauseOfLossAdjustment`/
    `EQDeductibleFactor` the golden case's own plain chain already produces,
    confirming EQ's blanket branch shares the base-rate-to-deductible-factor
    chain with the plain branch and only diverges at the averaging step.
  * `SetTotalFullValueAmount` (same file) sums `FullBldgValue` across BOTH an
    ordinary-blanket match (`IncludedInBlkt="Yes" AND BlktIDNum=UnitNumber`)
    and an EQ-blanket match (`EQCovIndicator="Yes, Included in Blanket" AND
    EQCauseOfLossCovBlktIDNum=UnitNumber`) -- an EQ-only-blanket structure
    (never ordinarily blanket-rated) still counts toward the total, confirmed
    by direct read, not assumed.
  * `SetEQLimitToUse`, the `EQCauseOfLossCovBlktIDNum>0` branch, reads
    `BlktEQTotalFullValueAmount`/`BlktEQLimit` -- both copied from the SAME
    matched Detail record by `SetEQBlanketValues`, mirroring
    `BlktTotalFullValueAmount`/`BlktLimit`'s own ordinary-chain shape one
    field-prefix over.

**Two findings, found only by running, neither named by the census or the
golden case's own "what this case cannot show" list:**

1. A SINGLE-structure version of this case computes the identical $6 by
   hand, but the engine raises *"Blanket Rating requires 2 or more risks to
   be valid"* and *"EQ Cause of Loss coverage cannot be Yes, Included in
   Blanket"* -- ISO's own validation layer refuses a one-structure EQ
   blanket exactly the way OI-99 describes for the ordinary chain, even
   though the arithmetic still silently computes a nonzero number. Two
   structures (below) is the minimum ISO itself will accept as a real
   blanket, not an arbitrary choice.
2. Both that message and a second one (*"Blanket ID number entered contains
   no EQ blanket coverage"*) turned out to gate on the SAME Detail-level
   field, `EQCauseOfLossIncludedInBlkt`, which is NOT one of the fields any
   prior chunk-10 task named -- confirmed only by reading the two
   `DoMessage` rules' own bodies after they fired on the first run of this
   script (which omitted the field). Setting it to `"Yes"` on the Detail
   record silences both.

Two structures, one Detail record (`TypeOfBlanketRating="Average"`,
`Type="Building Only"`), UNEQUAL values so the average genuinely disperses
(unlike a single structure, which degenerates to the plain chain's own
number and does not exercise the averaging step at all).

    python scripts/cf/100_chunk10_c10-15_blanket_reachability.py [--trace]

Exit 0 on match. No engine code touched regardless of outcome.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
import _state_inputs as _si                                     # noqa: E402
from gl_engine.interp.tree import Node, read

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty"
LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
STRUCT_TBL = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure"
S1, S2 = STRUCT_TBL + "[1]", STRUCT_TBL + "[2]"
ENDT1 = S1 + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementTable"
              "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement[1]")
ENDT2 = S2 + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementTable"
              "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement[1]")
DETAIL = (CP + "/CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]"
          "/CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]")

BLKT_ID = 1
VALUE_A, VALUE_B = 100_000, 200_000
TOTAL_LIMIT = VALUE_A + VALUE_B

#: re-used verbatim from the golden case -- the exact same base-rate-to-
#: deductible-factor chain, confirmed by C10-11 to be shared by every group,
#: now confirmed shared by the BLANKET branch too.
EQ_BASE_RATE = Decimal("0.009")
EQ_CAUSE_OF_LOSS_ADJ = Decimal("0.009")
EQ_DEDUCTIBLE_FACTOR = Decimal("0.68")


def _structure(value: int) -> dict:
    return {
        "RatingType": "Class", "ClassCode": "0951",
        "ConstructionType": "Frame", "CovType": "Building",
        "CauseOfLoss": "Basic", "Coinsurance": "90%",
        "Limit": str(value), "FullBldgValue": str(value),
        "Deductible": "1,000", "LossCostMultiplier": "1.0",
        "IncludedInBlkt": "No",
        "PackageModFactor": "1.0",
        "MultiPremiumAndDispersionCreditFactor": "1.0",
        # -- EQ election, elected INTO the blanket this time --
        "EQCovIndicator": "Yes, Included in Blanket",
        "EQCauseOfLossCovBlktIDNum": str(BLKT_ID),
        "EQClass": "A1",
        "EQDeductible": "10%",
        "EQSprinklerLeakageOnly": "Not Applicable",
        "BCEG": "1",
        "SprinklerSystem": "None",
    }


def submission() -> dict:
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {"CommercialProperty": [{
            "IRPMFactor": "1.0",
            "PolicyType": "Commercial Property Policy",
            "BlktRated": "Yes",
            "MUBlktRated": "No",
            "CommercialPropertyBlanketRatingTable": {"CommercialPropertyBlanketRating": [{
                "CommercialPropertyBlanketRatingDetailTable": {
                    "CommercialPropertyBlanketRatingDetail": [{
                        "UnitNumber": str(BLKT_ID),
                        "TypeOfBlanketRating": "Average",
                        "Type": "Building Only",
                        "Coinsurance": "90%",
                        "TotalLimit": str(TOTAL_LIMIT),
                        # Required to silence both DoMessageBlanketIDNumber
                        # EnteredContainsNoEQBlanketCoverage and DoMessageEQ
                        # CauseofLossCoverageCannotBeYesIncludedinBlanket --
                        # both gate on this Detail-level field, copied down
                        # to the structure by SetEQBlanketValues as
                        # BlktEQCauseOfLossIncludedInEQBlkt. Found only by
                        # reading the message rules after they fired.
                        "EQCauseOfLossIncludedInBlkt": "Yes",
                    }],
                },
            }]},
            "CommercialPropertyLocationTable": {"CommercialPropertyLocation": [{
                "ProtectClass": "3",
                "EQCauseOfLossForm": "Earthquake Form (CP 10 40)",
                "EQTerr": "1",
                "EQDeductibleTier": "1",
                "CommercialPropertyStructureTable": {"CommercialPropertyStructure": [
                    _structure(VALUE_A), _structure(VALUE_B)]},
            }]},
        }]},
    }


def _structure_calc(value: int) -> Decimal:
    return (Decimal(value) * EQ_CAUSE_OF_LOSS_ADJ * Decimal("1.0")
            * Decimal("1.0") * EQ_DEDUCTIBLE_FACTOR).quantize(Decimal("1"))


def predict() -> dict:
    calc_a, calc_b = _structure_calc(VALUE_A), _structure_calc(VALUE_B)
    total_full_val_times = calc_a + calc_b
    total_full_value_amount = Decimal(TOTAL_LIMIT)
    eq_avg_rate = (total_full_val_times / total_full_value_amount
                   * Decimal("1.0") * Decimal("1.0")).quantize(Decimal("0.001"))
    limit_a = (Decimal(VALUE_A) / total_full_value_amount
               * Decimal(TOTAL_LIMIT)).quantize(Decimal("1"))
    limit_b = (Decimal(VALUE_B) / total_full_value_amount
               * Decimal(TOTAL_LIMIT)).quantize(Decimal("1"))
    prem_a = (eq_avg_rate * (limit_a / 100)).quantize(Decimal("1"))
    prem_b = (eq_avg_rate * (limit_b / 100)).quantize(Decimal("1"))
    return {
        "EQStructureCalc_A": calc_a, "EQStructureCalc_B": calc_b,
        "TotalFullValTimesEQCauseOfLossAdjmt": total_full_val_times,
        "TotalFullValueAmount": total_full_value_amount,
        "EQAvgRate": eq_avg_rate,
        "EQLimitToUse_A": limit_a, "EQLimitToUse_B": limit_b,
        "Premium_A": prem_a, "Premium_B": prem_b,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")

    p = predict()
    print("Hand-derivation, EQ BLANKET branch, computed before running:")
    for k, v in p.items():
        print(f"  {k:38s} = {v}")
    print()

    ip = Interpreter(book, rounding=ROUNDING, trace=a.trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", _si.localize(submission(), JURIS, ASOF))
    ip.run(data)

    checks = [
        ("EQBaseRate (Structure A)", S1 + "/EQBaseRate", str(EQ_BASE_RATE)),
        ("EQCauseOfLossAdjustment (A)", S1 + "/EQCauseOfLossAdjustment", str(EQ_CAUSE_OF_LOSS_ADJ)),
        ("EQDeductibleFactor (A)", S1 + "/EQDeductibleFactor", str(EQ_DEDUCTIBLE_FACTOR)),
        ("Detail.TotalFullValTimesEQCauseOfLossAdjmt",
         DETAIL + "/TotalFullValTimesEQCauseOfLossAdjmt", str(p["TotalFullValTimesEQCauseOfLossAdjmt"])),
        ("Detail.EQAvgRate", DETAIL + "/EQAvgRate", str(p["EQAvgRate"])),
        ("Structure A.BlktEQAvgRate", S1 + "/BlktEQAvgRate", str(p["EQAvgRate"])),
        ("Structure B.BlktEQAvgRate", S2 + "/BlktEQAvgRate", str(p["EQAvgRate"])),
        ("Structure A.EQLimitToUse", S1 + "/EQLimitToUse", str(p["EQLimitToUse_A"])),
        ("Structure B.EQLimitToUse", S2 + "/EQLimitToUse", str(p["EQLimitToUse_B"])),
        ("EQ Endorsement Premium A (BLANKET branch)", ENDT1 + "/Premium", str(p["Premium_A"])),
        ("EQ Endorsement Premium B (BLANKET branch)", ENDT2 + "/Premium", str(p["Premium_B"])),
    ]
    ok = True
    for label, path, want in checks:
        got = read(path, data)
        try:
            good = got is not None and Decimal(got) == Decimal(want)
        except Exception:
            good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:48s} = {str(got):>10s}{flag}")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}): "
              + "; ".join(str(m)[:60] for m in ip.messages[:6]))

    print()
    if ok:
        print("MATCH -- EQ's own BLANKET branch (EQCovIndicator=\"Yes, "
              "Included in Blanket\") reaches a nonzero, genuinely dispersed "
              "premium on a real 2-structure submission ($6/$12, not equal), "
              "confirmed by running, not just reading the XML. Structure A's "
              "own EQBaseRate/EQCauseOfLossAdjustment/EQDeductibleFactor are "
              "the IDENTICAL values the plain (non-blanket) golden case "
              "produced, confirming the two branches share the base-rate "
              "chain and diverge only at the averaging step. This closes "
              "the one angle C10-11 did not test. No engine gap -- both "
              "surfaced messages traced to a missing submission field, not "
              "an engine defect.")
        return 0
    print("MISMATCH above -- not patched here if it traces to engine code, "
          "per this project's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
