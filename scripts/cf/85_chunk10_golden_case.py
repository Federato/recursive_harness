#!/usr/bin/env python3
"""Chunk 10's golden case -- the first Earthquake submission rated end to
end. Building, Basic Group I, one structure, EQ elected on the plain
percentage-deductible Endorsement (no blanket, no sub-limit, no flat-dollar
deductible, no sprinkler-leakage-only).

The derivation, written BEFORE this ran, is in
`docs/CF-CHUNK10-GOLDEN-CASE.md`.

Built differentially from **chunk 1's own risk** (Oregon, class code 0951,
Frame, Portland territory, protection class 3, Basic Group I, Coinsurance
90%, Deductible 1,000, Limit 100,000 -- `CF-CHUNK1-GOLDEN-CASE.md` case A,
premium $261) -- the SAME row chunk 1 already proved is untouched; the only
new fields are the EQ election:

    Location   EQCauseOfLossForm  "Earthquake Form (CP 10 40)"   (attaches
                                   the PLAIN Endorsement, not the flat-dollar
                                   or sub-limit variants -- confirmed by
                                   reading `AttachFormCommercialProperty
                                   EarthquakeAndVolcanicEruptionEndorsement`'s
                                   own gate directly)
               EQTerr             "1"
               EQDeductibleTier   1
    Structure  EQCovIndicator     "Yes, Not Included in Blanket"  (confirmed
                                   the only value the domain table
                                   `DomainEQCovIndicatorBldg` allows for
                                   CovTypeBldg=Building, EQSubLimitBlktIndicator
                                   =No, BlktRated=No, besides "No Coverage")
               EQClass            "A1"                (Structure-level input,
                                   NOT copied from Location -- unlike EQTerr)
               EQCoinsurance      "90%"
               EQDeductible       "10%"
               EQSprinklerLeakageOnly "Not Applicable"  (the domain-correct
                                   value for SprinklerSystem="None" -- NOT
                                   blank; see finding 2 below)
               BCEG               "1"                 (see finding 1 below)
               SprinklerSystem    "None"              (see finding 3 below)

Three structural facts, all confirmed against the rule XML rather than
inferred from the census doc, decide the shape of this submission -- each
is a "no-op trap" the same shape this project has flagged since chunk 1:

  1. **`BCEGEQFactor` defaults to `0.0`, not `1.0`, when `BCEG` is blank.**
     `SetBCEGEQFactor` (`CommercialPropertyStructureRules.Rule.xml`) gates its
     lookup on `BCEG != ""`; its Else branch is a bare `Constant 0.0`. Since
     `SetEQRate` multiplies `BCEGEQFactor` into `EQRate` unconditionally, an
     unset `BCEG` silently zeroes the entire EQ rate chain -- a $0 premium
     with no error, the same shape as chunk 1's own "two zeros that collapse
     the premium" open item. `BCEG="1"` -> `BCEGEarthquakeFactor[OR]("1")` =
     `1.0`, a genuine no-op, confirmed by direct table read (this is a
     DIFFERENT table from the near-namesake `BCEGEQFactor.RateTable.csv`,
     which is header-only at CW and unfiled at OR -- the census's own
     shared-name-adjacent trap, finding 5, confirmed load-bearing here).
  2. **`EQSprinklerLeakageOnly` has no default-if-blank rule, and blank
     satisfies NEITHER of `SetEQDeductibleFactor`'s two `When` branches.**
     The rule's outer `Choose` tests `Equal(...,"Yes")` then
     `Or(Equal(...,"No"), Equal(...,"Not Applicable"))` -- blank matches
     neither, and `EQDeductibleFactor` is left `IsNull` (no `Otherwise`
     branch on the outer `Choose`), which starves `SetFinalEQRate`'s product
     of a `0.0` `FromConstant` fallback. This is NOT a case of picking the
     domain-correct value out of convenience: `DomainEQSprinklerLeakageOnlyBuilding`
     confirms directly that for `EQCovIndicatorBldg="Yes, Not Included in
     Blanket"` and `SprinklerSystemBldg="None"`, the ONLY filed `DataValue`
     is `"Not Applicable"` -- so the fix for the starved-factor trap and the
     domain-correct value are the same string, not a coincidence.
  3. **`EQSprinkleredRiskFactor`'s gate treats blank as "has a sprinkler,"
     not as "no sprinkler."** `SetEQSprinkleredRiskFactor` guards its lookup
     on `NotEqual(SprinklerSystem,"None")` -- an UNSET `SprinklerSystem`
     satisfies `NotEqual(blank,"None")` (blank is not literally the string
     `"None"`), so a submission that never mentions sprinklers takes the
     LOOKUP branch, not the 1.0-default Else branch. The table (`CW`,
     constant `"Y"`) returns `1.06`, not `1.0` -- so leaving `SprinklerSystem`
     unset does not silently no-op here, it silently adds a 6% loss it was
     never asked to model. `SprinklerSystem="None"` (a valid `DomainSprinklerSystemBldg`
     value for `RatingType="Class"`) is required to reach the genuine 1.0
     no-op.

Two more facts, confirmed but NOT traps (the chain already no-ops safely
without extra inputs):

  * `EQSubLimitPercent` falls through its own `Otherwise` to `0` when neither
    sub-limit table exists -- no explicit input needed.
  * `PctOfMasonryVeneerEQFactor`, `BuildersRiskEQFactor`, `BldgHeightFactor`,
    `SoftStoryModificationFactor`, `LimitationsOnCovForRoofSurfacingACVFactor`,
    both Cyber factors (`CyberIncidentExclusionFactorEQ`,
    `CyberIncidentExclusionCOLExcptnsFactorEQ`) and `EQDeductibleByLocationFactor`
    all resolve to their genuine `1.0` no-op with nothing set beyond what
    chunk 1's own case already supplies -- confirmed by reading each Set
    rule's Else/Otherwise branch directly, not assumed from the name.

    python scripts/cf/85_chunk10_golden_case.py [--trace]

**Result: MATCH.** Every intermediate traces to the hand-derived value
exactly, and chunk 1's own $261 Basic Group I premium is unmoved by the EQ
election on the same structure -- confirmed as part of this run, not
assumed. Exit 0 means both premiums matched.
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

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
ENDT = STRUCT + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementTable"
                  "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement[1]")
BGI_PREMIUM = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"

#: hand-derived, filed rows cited in the doc
EQ_BASE_RATE = Decimal("0.009")            # EQLossCostBldg [OR] "A1","1"
LOSS_COST_MULT = Decimal("1.0")
EQ_COINSURANCE_FACTOR = Decimal("0.95")    # CoinsuranceFactor [CW] "90%" (SHARED table
                                            # with the ordinary, non-EQ chain -- confirmed
                                            # by MatrixDef, not by field-name similarity)
EQ_DEDUCTIBLE_FACTOR = Decimal("0.68")     # EQPercentageDeductibleFactor [OR] 1,"A1","10%"
LIMIT = 100_000
ORDINARY_PREMIUM = Decimal(261)            # CF-CHUNK1-GOLDEN-CASE.md case A, unmoved

EQ_RATE = (EQ_BASE_RATE * LOSS_COST_MULT).quantize(Decimal("0.001"))            # 0.009
EQ_COL_ADJ = (EQ_RATE * Decimal("1.0")).quantize(Decimal("0.001"))              # 0.009
ADJUSTED_EQ_RATE = (EQ_COL_ADJ * EQ_COINSURANCE_FACTOR).quantize(Decimal("0.001"))  # 0.009
FINAL_EQ_RATE = (ADJUSTED_EQ_RATE * EQ_DEDUCTIBLE_FACTOR).quantize(Decimal("0.001"))  # 0.006
EQ_PREMIUM = (FINAL_EQ_RATE * (Decimal(LIMIT) / 100)).quantize(Decimal("1"))    # 6


def submission() -> dict:
    """Chunk 1's own Case A risk, with the EQ election added on top."""
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                # Domain-correct no-op; not load-bearing for this chain
                # (see the module docstring -- SetEQSubLimitBlktIndicator
                # only feeds the BLANKET sub-limit premium branch, which this
                # case never takes).
                "EQSubLimitBlktIndicator": "No",
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland",
                        "ProtectClass": "3",
                        # Location-level EQ inputs, copied down to the
                        # structure by SetEQCauseOfLossForm/SetEQTerr/
                        # SetEQDeductibleTier -- confirmed by direct read,
                        # not assumed from the field-name prefix.
                        "EQCauseOfLossForm": "Earthquake Form (CP 10 40)",
                        "EQTerr": "1",
                        "EQDeductibleTier": "1",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [{
                                "RatingType": "Class",
                                "ClassCode": "0951",
                                "ConstructionType": "Frame",
                                "CovType": "Building",
                                "CauseOfLoss": "Basic Group I",
                                "Coinsurance": "90%",
                                "Limit": str(LIMIT),
                                "FullBldgValue": str(LIMIT),
                                "Deductible": "1,000",
                                "LossCostMultiplier": "1.0",
                                "IncludedInBlkt": "No",
                                "PackageModFactor": "1.0",
                                "MultiPremiumAndDispersionCreditFactor": "1.0",
                                # -- EQ election, Structure-level inputs --
                                "EQCovIndicator": "Yes, Not Included in Blanket",
                                "EQClass": "A1",
                                "EQCoinsurance": "90%",
                                "EQDeductible": "10%",
                                # The domain-correct no-op for
                                # SprinklerSystem="None" -- NOT blank; see
                                # finding 2 in the module docstring.
                                "EQSprinklerLeakageOnly": "Not Applicable",
                                # See finding 1: BCEGEQFactor defaults to 0.0,
                                # not 1.0, when this is blank.
                                "BCEG": "1",
                                # See finding 3: SprinklerSystem blank is NOT
                                # the same as "None" for EQSprinkleredRiskFactor.
                                "SprinklerSystem": "None",
                            }],
                        },
                    }],
                },
            }],
        },
    }


def run(trace=False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    ip.run(data)
    return data, ip


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    print("Hand-derivation, computed before this ran:")
    print(f"  EQBaseRate            = EQLossCostBldg[OR](\"A1\",\"1\")        = {EQ_BASE_RATE}")
    print(f"  EQRate                = round({EQ_BASE_RATE} x {LOSS_COST_MULT}, 3)         = {EQ_RATE}")
    print(f"  EQCauseOfLossAdjustment = round({EQ_RATE} x 1.0, 3)            = {EQ_COL_ADJ}")
    print(f"  AdjustedEQRate         = round({EQ_COL_ADJ} x {EQ_COINSURANCE_FACTOR}, 3)         = {ADJUSTED_EQ_RATE}")
    print(f"  FinalEQRate            = round({ADJUSTED_EQ_RATE} x {EQ_DEDUCTIBLE_FACTOR}, 3)         = {FINAL_EQ_RATE}")
    print(f"  EQ Premium             = round({FINAL_EQ_RATE} x {LIMIT}/100, 0)        = {EQ_PREMIUM}")
    print(f"  Ordinary BGI Premium (unmoved, CF-CHUNK1-GOLDEN-CASE.md case A) = {ORDINARY_PREMIUM}\n")

    data, ip = run(a.trace)

    checks = [
        ("EQBaseRate", STRUCT + "/EQBaseRate", str(EQ_BASE_RATE)),
        ("EQRate", STRUCT + "/EQRate", str(EQ_RATE)),
        ("EQCauseOfLossAdjustment", STRUCT + "/EQCauseOfLossAdjustment", str(EQ_COL_ADJ)),
        ("EQCoinsuranceFactor", STRUCT + "/EQCoinsuranceFactor", str(EQ_COINSURANCE_FACTOR)),
        ("AdjustedEQRate", STRUCT + "/AdjustedEQRate", str(ADJUSTED_EQ_RATE)),
        ("EQClassToUse", STRUCT + "/EQClassToUse", "A1"),
        ("EQDeductibleFactor", STRUCT + "/EQDeductibleFactor", str(EQ_DEDUCTIBLE_FACTOR)),
        ("FinalEQRate", STRUCT + "/FinalEQRate", str(FINAL_EQ_RATE)),
        ("Endorsement Premium", ENDT + "/Premium", str(EQ_PREMIUM)),
        ("Ordinary BGI Premium (regression)", BGI_PREMIUM, str(ORDINARY_PREMIUM)),
    ]
    ok = True
    for label, path, want in checks:
        got = read(path, data)
        good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:36s} = {str(got):>10s}{flag}")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}):")
        for m in ip.messages[:20]:
            print(f"    - {m}")

    if a.trace:
        print(ip.trace_text())
    if a.dump:
        print(dump(data))

    print()
    if ok:
        print("Earthquake golden case matches: every intermediate traces to "
              "its hand-derived value, and chunk 1's own Basic Group I "
              "premium is confirmed unmoved by the EQ election.")
        return 0
    print("MISMATCH -- see the printed values above against the hand "
          "derivation. Not fixed here if this traces to engine code; see "
          "the module docstring's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
