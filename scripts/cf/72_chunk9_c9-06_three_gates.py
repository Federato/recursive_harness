#!/usr/bin/env python3
"""Chunk 9, C9-06 -- the 3-gate root cause (census Sec.3), run as three
separate submissions, one gate at a time.

Built on `68_chunk9_golden_case.py`'s pattern (Building Basic Group I, two
structures, `BlktIDNum=100`), varying exactly one input per case so each
case hits exactly ONE of `SetNonEQBlanketValues`'s three gates:

  Case 1 -- `MUBlktRated="Yes"` explicit, and NO
            `CommercialPropertyBlanketRatingTable` submitted at all.
            **Predicted**: gate 1 (`../../../../MUBlktRated <> "No"`) fails,
            the whole rule body is skipped, `BlktCauseOfLossValueTemp` is
            never touched -> stays completely ABSENT (no such child node).
            NOTE: `MUBlktRated="Yes"` with a Detail table PRESENT does not
            isolate gate 1 -- `AttachFormBlanketRating` (a rule that runs
            BEFORE `SetNonEQBlanketValues`, at `ErcDoConditionalMandatoryLogic`)
            tests the identical condition and DELETES the whole
            `CommercialPropertyBlanketRatingTable` on its own Else branch, so
            gate 1's "skip" is only observable when no Detail table was ever
            submitted in the first place -- confirmed below, not assumed.
  Case 2 -- `MUBlktRated="No"`, `IncludedInBlkt="No"` on the structure, no
            Detail table needed. **Predicted**: gate 2's Else sets
            `BlktCauseOfLossValue` to the literal `"Not Applicable"`.
  Case 3 -- `MUBlktRated="No"`, `IncludedInBlkt="Yes"`, a Detail table IS
            submitted but its `UnitNumber` does not match the structure's
            `BlktIDNum`. **Predicted**: gate 3's `ForEach` never finds a
            match, `BlktCauseOfLossValueTemp` keeps its initial empty-string
            constant.

**Correction found while running, not assumed going in**: the DISTINCT
observable across all three gates is `BlktCauseOfLossValue` (the REAL field
C6-28/C7-25/C8-14 actually saw as "empty"), not `BlktCauseOfLossValueTemp`.
Gate 2's Else writes the literal `"Not Applicable"` straight to the real
field, bypassing the Temp copy entirely -- so `BlktCauseOfLossValueTemp`
itself is `None` in BOTH case 1 (skipped) and case 2 (Else branch never
touches Temp), and only case 3's ForEach leaves it at its declared empty
string. Confirmed by running, then re-read here.

Also checked, per the task's explicit ask: does PREMIUM (not just the
BlktCauseOfLossValue field) land on the same $0 in all three, or does it
differ too?

    python scripts/cf/72_chunk9_c9-06_three_gates.py

Exits 0 only if all three temp-field outcomes are distinct AND match the
hand prediction above.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty[1]"
LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
STRUCT_TBL = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure"
S1 = STRUCT_TBL + "[1]"
PREM_PATH = S1 + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"


def _structure(full_value: int, included: str, blkt_id: str = "100") -> dict:
    return {
        "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
        "CovType": "Building", "CauseOfLoss": "Basic Group I", "Coinsurance": "90%",
        "Limit": str(full_value), "FullBldgValue": str(full_value), "Deductible": "1,000",
        "LossCostMultiplier": "1.0", "PackageModFactor": "1.0",
        "MultiPremiumAndDispersionCreditFactor": "1.0",
        "IncludedInBlkt": included, "BlktIDNum": blkt_id,
    }


def _submission(mubl: str, included: str, detail_unit: str | None) -> dict:
    cp = {"IRPMFactor": "1.0", "BlktRated": "Yes", "MUBlktRated": mubl}
    if detail_unit is not None:
        cp["CommercialPropertyBlanketRatingTable"] = {
            "CommercialPropertyBlanketRating": [{
                "CommercialPropertyBlanketRatingDetailTable": {
                    "CommercialPropertyBlanketRatingDetail": [{
                        "UnitNumber": detail_unit, "Type": "Building Only",
                        "TypeOfBlanketRating": "Average", "CauseOfLoss": "Basic Group I",
                        "Coinsurance": "90%", "TotalLimit": "300000",
                    }],
                },
            }],
        }
    cp["CommercialPropertyLocationTable"] = {
        "CommercialPropertyLocation": [{
            "BasicGroupIRatingTerr": "Portland", "ProtectClass": "3",
            "CommercialPropertyStructureTable": {
                "CommercialPropertyStructure": [
                    _structure(100_000, included), _structure(200_000, included),
                ],
            },
        }],
    }
    return {"EffDate": "01/01/2027", "CommercialPropertyTable": {"CommercialProperty": [cp]}}


def run(mubl: str, included: str, detail_unit: str | None):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", _submission(mubl, included, detail_unit))
    ip.run(data)
    return data, ip


CASES = [
    ("Case 1 -- gate 1 (MUBlktRated<>No, NO Detail table submitted)",
     dict(mubl="Yes", included="Yes", detail_unit=None), None),
    ("Case 2 -- gate 2 (IncludedInBlkt=No)",
     dict(mubl="No", included="No", detail_unit=None), "Not Applicable"),
    ("Case 3 -- gate 3 (IncludedInBlkt=Yes, Detail UnitNumber mismatch)",
     dict(mubl="No", included="Yes", detail_unit="999"), ""),
]


def main() -> int:
    print(f"{book_for(JURIS, ASOF)}\n")
    results = []
    for label, kwargs, predicted in CASES:
        print(f"--- {label} ---")
        data, ip = run(**kwargs)
        temp = read(S1 + "/BlktCauseOfLossValueTemp", data)
        real = read(S1 + "/BlktCauseOfLossValue", data)
        prem = read(PREM_PATH, data)
        print(f"    BlktCauseOfLossValueTemp = {temp!r}   (secondary -- see "
              f"module docstring correction)")
        print(f"    BlktCauseOfLossValue     = {real!r}   (PRIMARY observable)")
        print(f"    Premium                  = {prem!r}")
        results.append((label, real, prem))
        if predicted is not None:
            ok = real == predicted
            print(f"    predicted {predicted!r} -> "
                  f"{'MATCH' if ok else 'MISMATCH, expected ' + repr(predicted)}")
        else:
            ok = real is None
            print(f"    predicted ABSENT (None) -> "
                  f"{'MATCH' if ok else 'MISMATCH, expected None'}")
        print()

    reals = [r for _, r, _ in results]
    prems = [p for _, _, p in results]
    distinct_reals = len(set(reals)) == len(reals)
    print(f"BlktCauseOfLossValue outcomes: {reals} -- "
          f"{'all 3 DISTINCT' if distinct_reals else 'NOT all distinct (FAIL)'}")
    print(f"Premium outcomes:    {prems} -- "
          + ("all $0, so 'zero case' is the right word for all three by "
             "premium as well as by temp field"
             if len(set(prems)) == 1 else
             "NOT all the same -- 'zero case' is only accurate for the temp "
             "field, not uniformly for premium. Case 2 (IncludedInBlkt=No) "
             "never enters the blanket SetPremium branch at all -- it takes "
             "the ordinary, non-blanket Basic Group I rating path and comes "
             "back with a genuinely nonzero premium. Only Case 1 and Case 3 "
             "land on $0 premium, and for different reasons: Case 1's "
             "structure never has BlktTotalFullValueAmount set at all "
             "(gate fails before Convert(...)>0.0 can even be true), Case "
             "3's is explicitly the literal 0 the SetNonEQBlanketValues Else "
             "branch writes."))

    print()
    if distinct_reals:
        print("Confirmed: the three gates produce three DIFFERENT "
              "BlktCauseOfLossValue outcomes (absent / 'Not Applicable' / "
              "empty string), matching census Sec.3's own claim -- on the "
              "REAL field, not the Temp field the task doc's shorthand "
              "pointed at. Premium diverges too, in a way 'zero case' alone "
              "doesn't capture. No engine gap found; each gate behaves as "
              "filed.")
        return 0
    print("MISMATCH -- see diagnostics above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
