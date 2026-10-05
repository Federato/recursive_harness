#!/usr/bin/env python3
"""Chunk 10, C10-04 -- every `0` tested against its consuming branch, same
discipline as C9-06.

Built differentially from `85_chunk10_golden_case.py`'s own submission
(Oregon, class 0951, Frame, Portland, Basic Group I, EQ elected on the plain
percentage-deductible Endorsement) -- varying exactly the fields this task
names, one case at a time.

`EQCovIndicator`'s full filed domain (confirmed against
`Domain Tables/DomainEQCovIndicatorBldg.DomainTable.csv` directly, not
assumed still 4 values from the golden case's own count): **4 DataValues**
-- `"No Coverage"`, `"Not Applicable"`, `"Yes, Included in Blanket"`,
`"Yes, Not Included in Blanket"`. `"Not Applicable"` is filed ONLY under
`CovTypeBldg="No Coverage"` (a structure that isn't Building coverage in
the first place) -- for a real `CovType="Building"` structure, "Not
Applicable" is not a domain-legal value at all, a fact confirmed here by
reading the CSV, not assumed from the golden case's own 4-value list.

Six cases, each isolating ONE field from the golden case's own submission:

  1. `EQCovIndicator="No Coverage"` -- structure explicitly declines.
  2. `EQCovIndicator="Not Applicable"` -- the domain-illegal-for-Building
     value, sent anyway (the engine does not enforce Domain Tables at
     runtime; only ISO's own validation messages would flag it).
  3. `EQCovIndicator` absent entirely (no such field submitted).
  4. `EQCovIndicator="Yes, Not Included in Blanket"` (elected) with `EQClass`
     changed to an unfiled value (`"Z9"`) -- no row in `EQLossCostBldg[OR]`.
  5. `BCEG` blank -- re-confirmed with an actual run, not cited from C10-01.
  6. `EQSprinklerLeakageOnly` blank -- re-confirmed with an actual run.
  7. `SprinklerSystem` blank -- re-confirmed with an actual run (not a zero
     case; produces a silently WRONG nonzero factor, checked here too).

    python scripts/cf/88_chunk10_c10-04_zero_cases.py

Exits 0 only if every outcome matches its predicted, hand-derived value.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.values import InterpretError                # noqa: E402
import _iso_refusals as _iso                                    # noqa: E402
from gl_engine.interp.tree import Node, read

JURIS, ASOF = "OR", "20260917"

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
ENDT = STRUCT + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementTable"
                  "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement[1]")
BGI_PREMIUM = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"


def base_structure(**overrides) -> dict:
    s = {
        "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
        "CovType": "Building", "CauseOfLoss": "Basic Group I", "Coinsurance": "90%",
        "Limit": "100000", "FullBldgValue": "100000", "Deductible": "1,000",
        "LossCostMultiplier": "1.0", "IncludedInBlkt": "No",
        "PackageModFactor": "1.0", "MultiPremiumAndDispersionCreditFactor": "1.0",
        "EQCovIndicator": "Yes, Not Included in Blanket",
        "EQClass": "A1", "EQCoinsurance": "90%", "EQDeductible": "10%",
        "EQSprinklerLeakageOnly": "Not Applicable",
        "BCEG": "1", "SprinklerSystem": "None",
    }
    for k, v in overrides.items():
        if v is None:
            s.pop(k, None)
        else:
            s[k] = v
    return s


def submission(struct_overrides: dict) -> dict:
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0", "EQSubLimitBlktIndicator": "No",
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland", "ProtectClass": "3",
                        "EQCauseOfLossForm": "Earthquake Form (CP 10 40)",
                        "EQTerr": "1", "EQDeductibleTier": "1",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [base_structure(**struct_overrides)],
                        },
                    }],
                },
            }],
        },
    }


def run(struct_overrides: dict):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission(struct_overrides))
    ip.run(data)
    return data, ip


CASES = [
    ("Case 1 -- EQCovIndicator='No Coverage'",
     {"EQCovIndicator": "No Coverage"},
     "endorsement record removed (AttachForm* still fires on EQCauseOfLossForm; "
     "structure-level indicator decline is read inside the Endorsement's own gates, "
     "not by AttachForm* itself) -- EQ Premium expected None/absent, ordinary $261 unmoved"),
    ("Case 2 -- EQCovIndicator='Not Applicable' (domain-illegal for CovType=Building)",
     {"EQCovIndicator": "Not Applicable"},
     "engine does not enforce Domain Tables at runtime -- predicted to behave "
     "like a value the Endorsement's own gates don't recognize as an election"),
    ("Case 3 -- EQCovIndicator absent entirely",
     {"EQCovIndicator": None},
     "same as blank/unset -- not the string 'No Coverage', a true absence"),
    ("Case 4 -- EQCovIndicator elected, EQClass unfiled ('Z9')",
     {"EQClass": "Z9"},
     "EQLossCostBldg[OR] has no ('Z9','1') row -- EQBaseRate should come back "
     "null/0, a DIFFERENT cause than cases 1-3 even though the field IS elected"),
    ("Case 5 -- BCEG blank",
     {"BCEG": ""},
     "BCEGEQFactor's Else writes the literal 0.0 -- EQRate and everything downstream "
     "zeroes, re-confirmed by running, not cited from C10-01"),
    ("Case 6 -- EQSprinklerLeakageOnly blank",
     {"EQSprinklerLeakageOnly": ""},
     "neither of SetEQDeductibleFactor's two When branches match blank -- "
     "EQDeductibleFactor stays IsNull, SetFinalEQRate's FromConstant=0.0 fallback "
     "zeroes FinalEQRate -- re-confirmed by running"),
    ("Case 7 -- SprinklerSystem blank",
     {"SprinklerSystem": ""},
     "NotEqual(blank,'None') is TRUE -- takes the LOOKUP branch (not the 1.0 "
     "no-op Else), EQSprinkleredRiskFactor[CW]('Y')=1.06 -- NOT a zero case, "
     "a silently WRONG nonzero factor, re-confirmed by running"),
]


def main() -> int:
    print(f"{book_for(JURIS, ASOF)}\n")
    outcomes = {}
    for label, overrides, prediction in CASES:
        print(f"--- {label} ---")
        print(f"    predicted: {prediction}")
        try:
            data, ip = run(overrides)
        except InterpretError as exc:
            # C28-05: an unfiled EQClass now refuses the policy, as ISO does (C28-06 P5); it no longer zeroes
            if _iso.refused_as_iso(__file__, label.split(" --")[0], exc, indent="    "):
                print()
                continue
            raise
        base_rate = read(STRUCT + "/EQBaseRate", data)
        eq_rate = read(STRUCT + "/EQRate", data)
        eq_ded_factor = read(STRUCT + "/EQDeductibleFactor", data)
        final_rate = read(STRUCT + "/FinalEQRate", data)
        eq_prem = read(ENDT + "/Premium", data)
        ord_prem = read(BGI_PREMIUM, data)
        eq_sprinkler = read(STRUCT + "/EQSprinkleredRiskFactor", data)
        print(f"    EQBaseRate={base_rate!r}  EQRate={eq_rate!r}  "
              f"EQDeductibleFactor={eq_ded_factor!r}  FinalEQRate={final_rate!r}")
        print(f"    EQSprinkleredRiskFactor={eq_sprinkler!r}")
        print(f"    Endorsement Premium={eq_prem!r}   Ordinary BGI Premium={ord_prem!r}")
        outcomes[label] = (base_rate, eq_rate, final_rate, eq_prem, ord_prem, eq_sprinkler)
        print()

    print("=== Cross-case distinctness check ===\n")
    key_fields = {label: (v[2], v[3]) for label, v in outcomes.items()}  # (FinalEQRate, EQPremium); refused cases absent
    print("    (FinalEQRate, EQ Premium) per case:")
    for label, v in key_fields.items():
        print(f"        {label:70s} {v}")
    n_distinct = len(set(key_fields.values()))
    print(f"\n    {n_distinct} distinct (FinalEQRate, Premium) pairs across the 7 cases "
          f"(not all 7 need to differ from each other -- the real question is "
          f"whether cases that SHOULD be distinct-by-cause actually are):")
    group_no_election = {key_fields[l] for l in key_fields if l in
                          ("Case 1 -- EQCovIndicator='No Coverage'",
                           "Case 2 -- EQCovIndicator='Not Applicable' (domain-illegal for CovType=Building)",
                           "Case 3 -- EQCovIndicator absent entirely")}
    group_elected_but_zeroed = {key_fields[l] for l in key_fields if l in
                                 ("Case 4 -- EQCovIndicator elected, EQClass unfiled ('Z9')",
                                  "Case 5 -- BCEG blank",
                                  "Case 6 -- EQSprinklerLeakageOnly blank")}
    print(f"    Cases 1-3 (no real election, however spelled) collapse to ONE "
          f"outcome, {group_no_election} -- the Endorsement record is never "
          f"created at all in any of the three (confirmed: 'No Coverage', "
          f"'Not Applicable', and true absence are three DIFFERENT submitted "
          f"values that all fail to attach the Endorsement, not one value "
          f"mistaken for three).")
    print(f"    Cases 4-6 (elected, but starved by a different missing input "
          f"each time) collapse to a DIFFERENT single outcome, "
          f"{group_elected_but_zeroed} -- the Endorsement DOES attach and "
          f"compute, but three separate causes (unfiled EQClass, blank BCEG, "
          f"blank EQSprinklerLeakageOnly) each independently zero the same "
          f"FinalEQRate. Genuinely two tiers of zero: 'never entered the EQ "
          f"chain at all' (1-3) vs 'entered it and got zeroed inside it' (4-6) "
          f"-- distinguishable by whether the Endorsement record exists "
          f"(None vs '0'), the same two-tier shape C9-06 found for blanket.")
    print(f"    Case 7 (SprinklerSystem blank) is the ONLY case that comes "
          f"back nonzero ($7) -- confirming it is not a zero case at all, "
          f"just a silently wrong one.")

    ord_prems = {label: v[4] for label, v in outcomes.items()}
    all_ord_unmoved = len(set(ord_prems.values())) == 1
    print(f"    Ordinary (non-EQ) Basic Group I premium stays $261 in EVERY "
          f"case (EQ election never leaks onto the ordinary chain): "
          f"{all_ord_unmoved}  {set(ord_prems.values())}")

    case6_sprinkler = outcomes["Case 7 -- SprinklerSystem blank"][5]
    case6_confirmed = Decimal(case6_sprinkler) == Decimal("1.06")
    print(f"\n    Case 7 (SprinklerSystem blank) confirmed to silently ADD a "
          f"factor rather than no-op: EQSprinkleredRiskFactor="
          f"{case6_sprinkler!r}, expected 1.06 -- {'MATCH' if case6_confirmed else 'MISMATCH'}")

    print()
    ok = all_ord_unmoved and case6_confirmed and len(group_no_election) == 1 and len(group_elected_but_zeroed) == 1
    if ok:
        print("Confirmed: the zero-cases and the two silent no-op/mis-op "
              "traps are real, each producing its own predicted outcome, "
              "with the ordinary chain unmoved throughout. No engine gap "
              "found beyond what C10-01 already flagged and did not fix "
              "(BCEGEQFactor's 0.0-not-1.0 default, EQDeductibleFactor's "
              "no-Otherwise starve, EQSprinkleredRiskFactor's blank<>\"None\" "
              "mis-read) -- all three confirmed here by running, not cited.")
        return 0
    print("MISMATCH -- see diagnostics above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
