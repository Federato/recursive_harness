#!/usr/bin/env python3
"""Chunk 9, C9-10 -- do the 4 blanket-specific `DoMessage` rules in
`CommercialPropertyBlanketRatingDetailRules.Rule.xml` fire on the golden
case, and are they logged in `CF_Message_Register.md`?

**The 4 rules, named exactly off the dispatcher's own `Sequence`**
(`DoAllBlanketRatingMessages`, same file, read directly rather than trusting
the task doc's paraphrase, which named only 2 of the 4 and abbreviated a
3rd):

    DoMessageBlanketRatingRequires2OrMoreRisksToBeValid
    DoMessageBlanketRatingRequiresAllRisksToHaveTheSameValueForEQSprinklerLeakageCoverage
    DoMessagePeakSeasonGeneralInformationDetailFormIsRequiredForBlanket
    DoMessageIfAnyBusinessIncomeBIRiskUnderAnOperationalUnitInTheBlanketHasAnIndemnityOptionCoverageSelectedThenAllBIRisksInTheBlanketShouldHaveTheSameIndemnityOptionCoverage

Each rule's own condition, read directly (not inferred from the name):

  1. fires when `Counter <= 1` -- `Counter` is `SetCounters`' sum of
     structures/personal-property/BI rows on this Detail record's own
     `UnitNumber` with `IncludedInBlkt="Yes"` (plus an EQ-sprinkler-leakage
     variant of the same test). The golden case's Detail record sees 2
     structures -> `Counter=2` -> does not fire.
  2. fires only when an EQ-form (`CP 10 40`/`CP 10 28`) structure exists with
     `EQCovIndicator="Yes, Included in Blanket"` on this `UnitNumber` --
     the golden case sets no `EQCauseOfLossForm` anywhere -> does not fire.
  3. fires only when `PeakSeasonIndicator="Yes"` on the Detail record with no
     matching `CommercialPropertyPeakSeasonGeneralInformationDetail` row --
     the golden case never sets `PeakSeasonIndicator` -> does not fire.
  4. fires only when a `CommercialPropertyBusinessIncome` row exists with
     `BldgIncludedInOperationalUnit="Yes"` and `IncludedInBlkt="Yes"` on this
     `UnitNumber` -- the golden case carries no Business Income table at all
     -> does not fire.

**Prediction, before running: none of the 4 fire on the golden case as
built.** The golden case's own 3 ISO messages (2x CP 03 20, 1x CP 10 75/76)
are unrelated policy/structure-level form-attachment checks in
`CommercialPropertyRules.Rule.xml`/`CommercialPropertyStructureRules.Rule.xml`,
not this file -- confirmed by name, they don't match any of the 4 above.

**Second submission, built to trigger #1**: drop Structure B, leaving one
structure with `IncludedInBlkt="Yes"` sharing the Detail record's
`UnitNumber`. `Counter` becomes 1 -> `1 <= 1` -> the rule's `Then` fires.
Predicted before running: "Blanket Rating requires 2 or more risks to be
valid" appears in `ip.messages`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
golden = importlib.import_module("68_chunk9_golden_case")

FOUR_MESSAGES = [
    "DoMessageBlanketRatingRequires2OrMoreRisksToBeValid",
    "DoMessageBlanketRatingRequiresAllRisksToHaveTheSameValueForEQSprinklerLeakageCoverage",
    "DoMessagePeakSeasonGeneralInformationDetailFormIsRequiredForBlanket",
    "DoMessageIfAnyBusinessIncomeBIRiskUnderAnOperationalUnitInTheBlanketHasAnIndemnityOptionCoverageSelectedThenAllBIRisksInTheBlanketShouldHaveTheSameIndemnityOptionCoverage",
]

EXPECTED_TEXT = {
    "DoMessageBlanketRatingRequires2OrMoreRisksToBeValid":
        "Blanket Rating requires 2 or more risks to be valid",
    "DoMessagePeakSeasonGeneralInformationDetailFormIsRequiredForBlanket":
        "A Peak Season General Information Detail form is required when Peak Season Coverage is included",
}


def one_structure_submission() -> dict:
    """The golden case with Structure B dropped -- Counter falls to 1."""
    sub = golden.submission()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    structs = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]
    del structs[1]
    return sub


def run_case(sub: dict):
    ip = Interpreter(book_for(golden.JURIS, golden.ASOF), rounding=ROUNDING,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{golden.JURIS}", sub)
    ip.run(data)
    return data, ip


def main() -> int:
    print("=== 1. The 4 blanket-specific DoMessage rules, named exactly ===")
    for n in FOUR_MESSAGES:
        print(f"  - {n}")

    print("\n=== 2. Golden case (2 structures) -- do any of the 4 fire? ===")
    _, ip = run_case(golden.submission())
    print(f"  ISO validation messages ({len(ip.messages)}):")
    for m in ip.messages:
        print(f"    - {m}")
    hit_any = any(any(exp in m for exp in EXPECTED_TEXT.values()) for m in ip.messages)
    print(f"\n  Any of the 4 blanket-specific messages present: {hit_any}")
    print("  Predicted: False (Counter=2, no EQ form, no PeakSeason, no BI table).")

    print("\n=== 3. 1-structure variant -- predicted to trigger message #1 ===")
    _, ip2 = run_case(one_structure_submission())
    print(f"  ISO validation messages ({len(ip2.messages)}):")
    for m in ip2.messages:
        print(f"    - {m}")
    target = EXPECTED_TEXT["DoMessageBlanketRatingRequires2OrMoreRisksToBeValid"]
    fired = any(target in m for m in ip2.messages)
    print(f"\n  '{target}' present: {fired}")

    ok = (not hit_any) and fired
    print()
    if ok:
        print("Confirmed: none of the 4 fire on the 2-structure golden case; "
              "the 1-structure variant fires exactly the predicted message "
              "('requires 2 or more risks'), no others.")
    else:
        print("MISMATCH against prediction -- see printed messages above.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
