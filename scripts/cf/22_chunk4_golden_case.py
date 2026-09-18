#!/usr/bin/env python3
"""Chunk 4's golden cases -- Contents (Personal Property), all four forms.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK4-GOLDEN-CASE.md`.

Built differentially: the **same Oregon building as chunks 1, 2 and 3**, with
contents on it. That is chunk 1's case B, which already carried a Personal
Property record that never rated -- it existed only to put contents into the
location total the deductible keys on. Now it rates.

    Basic Group I    $223      base 0.548  [OR, 0951, Frame, Not Applicable, PersProp]
    Basic Group II   $24       base 0.031  [OR, Entire State, B, PersProp]
    Broad            $16       base 0.021  [CW, Frame, PersProp]
    Special          $137      base 0.153  [OR, Offices, Not Applicable] x terr 1.214

**Three predictions were wrong on the first run, and each is a finding.**

1. **PP's rate step rounds ONCE, where Building's rounds at every `Product`.**
   Building's Group I goes 0.498 -> r3 0.478 -> r3 0.239. PP's does
   `r3(0.548 x 0.96 x 0.499)` in one go = 0.263, where per-step rounding gives
   0.262. One dollar on this case; more wherever the chain is longer.
2. **The adjusted-rate multiplication order is coinsurance THEN limit**, not
   the `LOI x COLadj x coins` the algorithms page records. `r3(0.263 x 0.95)`
   = 0.250, `x 0.898` = 0.2245 -> **0.225**, another half-up tie. Taking the
   documented order gives 0.224 and a $222 premium.
3. **Each form gates on the cause of loss**, exactly as chunk 3's Broad and
   Special do -- so Contents needs a separate submission per form too. The
   first draft ran one submission with `CauseOfLoss = Basic` and read Broad and
   Special pricing at zero as a defect. It is the gate working.

And one uncertainty the case was written to settle, now settled:
**`SpecialTotAmtInsurance` is the LOCATION total (200,000)**, the same key
Building's Special deductible uses -- so the factor is 0.98 and Special is
$137, as first derived. A mid-run reading of 0.97 came from the *Basic*
submission, where the Special sum has not accrued; reading a Special-only
datadef out of a run that is not rating Special is a trap worth naming.

Two more fields turned out to be DERIVED rather than submitted, and both gate
Special shut when absent:

* **`OccupCategoryRiskSeverity`** is looked up from `OccupCategory` + the
  OCCUPANCY CLASS's own `ClassCode`. The rule has no `IsNull` guard, so a value
  supplied in the payload is overwritten -- with BLANK if the occupancy carries
  no class code. The mirror of chunk 3's derived-field hole: here the
  submission loses, and loses silently.
* **`CauseOfLoss` is the PP RECORD's own field**, not the structure's.
  `SetCauseOfLossToUse` reads it locally when the item is not blanketed, so
  setting the cause of loss on the building leaves every PP form gated shut.

**And Building must not move** -- $263 and $32, unchanged from chunk 1 case B
and chunk 2. The two coverages share the deductible key, the coinsurance factor
and the protection class, so Contents rating for the first time is exactly the
change that could disturb Building. Holding is half of what this case proves.

Two things worth knowing before reading the numbers:

* **The PersProp LOI factors are all below 1.0 where Building's are above it**
  -- 0.898 against 1.172, 0.843 against 1.266, 0.790 against 1.237. A Contents
  premium is not a scaled Building premium at any limit.
* **Broad's $16 equals Building's Broad $16 by coincidence**, out of two
  different chains: base 0.021 x LOI 0.790 against base 0.015 x LOI 1.237.

    python scripts/cf/22_chunk4_golden_case.py [--trace]

Exit 0 when all four forms match and Building is unmoved.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

golden = import_module("01_golden_case")
chunk2 = import_module("09_chunk2_golden_case")

JURIS, ASOF = chunk2.JURIS, chunk2.ASOF
STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII

OCCUP = STRUCT + "/CommercialPropertyOccupClassTable/CommercialPropertyOccupClass"
PP = OCCUP + "/CommercialPropertyPersonalPropertyTable/CommercialPropertyPersonalProperty"

#: form -> (premium path, expected). Grouped by the SUBMISSION that produces
#: it: `Basic` yields both Group I and Group II, `Broad` and `Special` one each.
_P = PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
RUNS = {
    "Basic": [("Basic Group I", _P % "BasicGroupI", "223"),
              ("Basic Group II", _P % "BasicGroupII", "24")],
    "Broad": [("Broad", _P % "Broad", "16")],
    "Special": [("Special", _P % "Special", "137")],
}

#: cause of loss -> the chain steps that submission proves.
CHAIN = {"Basic": [
    ("Group", "Not Applicable", "prep    occupancy group -- NOT A/B/C for 0951"),
    ("BasicGroupIBaseRate", "0.548", "BGI 1   base rate         [OR, PersProp]"),
    ("FireSafeVaultFactor", "1", "BGI 2   fire-safe vault -- PP-only concept"),
    ("ProtectionClassFactor", "0.96", "BGI 3   protection class  [CW]"),
    ("BasicGroupIRate", "0.263", "BGI 4   rate -- ONE round, not per-Product"),
    ("BasicGroupICauseOfLossAdjustment", "0.263", "BGI 5   COL adjustment"),
    ("BasicGroupILOIFactor", "0.898", "BGI 6   LOI -- PersProp table, BELOW 1.0"),
    ("CoinsuranceFactor", "0.95", "BGI 6   coinsurance -- shared"),
    ("AdjustedBasicGroupIRate", "0.225", "BGI 8   adjusted -- coins THEN LOI, a half-up tie"),
    ("DeductibleFactorBasicGroupI", "0.99", "BGI 7   deductible -- COPIED from 4 levels up"),
    ("FinalBasicGroupIRate", "0.223", "BGI 9   final rate"),

    ("BasicGroupIISymbol", "B", "BGII    symbol -- COPIED from the structure"),
    ("BasicGroupIIRatingTerr", "Entire State", "BGII    territory -- COPIED from the location"),
    ("BasicGroupIIBaseRate", "0.031", "BGII 2  base rate         [OR, PersProp]"),
    ("BasicGroupIIRate", "0.03", "BGII 4  rate"),
    ("BasicGroupIILOIFactor", "0.843", "BGII 7  LOI -- PersProp table"),
    ("AdjustedBasicGroupIIRate", "0.024", "BGII 8  adjusted rate  (a half-up TIE)"),
    ("FinalBasicGroupIIRate", "0.024", "BGII 11 final rate"),
], "Broad": [
    ("BroadLOIFactor", "0.79", "Broad 1 LOI -- computed FIRST here"),
    ("BroadBaseRate", "0.021", "Broad 2 base rate         [CW, PersProp]"),
    ("BroadRate", "0.021", "Broad 3 rate"),
    ("AdjustedBroadRate", "0.016", "Broad 4 adjusted rate"),
    ("FinalBroadRate", "0.016", "Broad 5 final rate"),
], "Special": [
    ("OccupCategory", "Offices", "Spec    category -- COPIED from the occupancy"),
    ("SpecialBaseRate", "0.153", "Spec 4  base rate  [OR, Offices, Not Applicable]"),
    ("PrsnlPropTerrMultiplier", "1.214", "Spec 5  territory -- BUILDING'S SPECIAL HAS NONE"),
    ("SpecialRate", "0.186", "Spec 6  rate"),
    ("SpecialTheftExclusionFactor", "1", "Spec 3  theft (not elected)"),
    ("SpecialCauseOfLossAdjustment", "0.186", "Spec 7  COL adjustment"),
    ("WatchmanCreditFactor", "1", "Spec 8  watchman -- COPIED from the submission"),
    ("BurglaryAlarmCreditFactor", "1", "Spec 9  burglary alarm -- same"),
    ("SpecialLOIFactor", "0.79", "Spec 10 LOI -- shared with Broad"),
    ("AdjustedSpecialRate", "0.14", "Spec 11 adjusted rate"),
    ("DeductibleFactorSpecial", "0.98", "Spec 2  deductible -- LOCAL, and keyed on the LOCATION total"),
    ("FinalSpecialRate", "0.137", "Spec 12 final rate"),
]}


def submission(col="Basic"):
    """Chunk 2's building, plus a Personal Property record that RATES.

    `col` is the cause of loss. Each PP form gates its base rate on it, exactly
    as Building's Broad and Special do -- so Contents needs a submission per
    form too, and the four premiums above never appear together.

    Chunk 1 case B already put a PP record here to drive `TotAmtInsurance`; it
    carried a limit and a CovType and nothing the rate chains read. The extra
    fields below are what turns it from a number in a sum into a rated risk.
    """
    sub = chunk2.submission()
    st = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
          ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
          ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    st["CommercialPropertyOccupClassTable"] = {
        "CommercialPropertyOccupClass": [{
            # Special's base rate is keyed on these two, and they are `Copy`d
            # down to every PP record under the class. Building's Special has
            # neither dimension.
            "OccupCategory": "Offices",
            # `OccupCategoryRiskSeverity` is DERIVED, not submitted: it is
            # looked up from OccupCategory + the OCCUPANCY CLASS's own
            # ClassCode. The rule has no `IsNull` guard, so a value supplied
            # here is overwritten -- and without a ClassCode on the occupancy
            # it is overwritten with BLANK, which gates Special's base rate
            # shut and prices it at zero. The first draft supplied the
            # severity and no class code and got exactly that.
            "ClassCode": "0951",
            "CommercialPropertyPersonalPropertyTable": {
                "CommercialPropertyPersonalProperty": [{
                    "Limit": "100000",
                    "CovType": "Personal Property",
                    "IncludedInBlkt": "No",
                    "RatingType": "Class",
                    "BldgClassCode": "0951",
                    "LossCostMultiplier": "1.0",
                    "Coinsurance": "90%",
                    "Deductible": "1,000",
                }],
            },
        }],
    }
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    # PP's Special territory is its own field, read six levels up -- and it is
    # a different scheme from Group I's (Portland) and Group II's (Entire
    # State). Three territory fields on one location, none interchangeable.
    loc["SpecialRatingTerr"] = "Multnomah (including entire city of Portland)"
    # The cause of loss is the PP RECORD's own field, not the structure's.
    # `SetCauseOfLossToUse` reads `CauseOfLoss` locally when the item is not
    # blanketed -- so setting it on the building, as the first draft did,
    # leaves every PP form gated shut and pricing at zero.
    (st["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
       ["CommercialPropertyPersonalPropertyTable"]
       ["CommercialPropertyPersonalProperty"][0])["CauseOfLoss"] = col
    from importlib import import_module as _imp
    _imp("10_chunk2_zero_cases").structure(sub)["CauseOfLoss"] = col
    return sub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")
    ok = True
    for col, wanted in RUNS.items():
        print(f"=== CauseOfLoss = {col!r}")
        ip = Interpreter(book, rounding=ROUNDING, trace=a.trace,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{JURIS}", submission(col))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"    RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue

        for dd, want, label in CHAIN[col]:
            got = read(f"{PP}/{dd}", data)
            good = want is None or got == want
            ok &= good
            flag = "" if good else f"   <-- expected {want}"
            print(f"    {label:52s} {dd:34s} = {got}{flag}")

        for form, path, want in wanted:
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {form:16s} PREMIUM = {str(got):>5s}   "
                  f"(expected {want:>5s}) {'OK' if good else 'MISMATCH'}")

        # Building must not move. It shares the deductible key, the coinsurance
        # factor and the protection class with Contents, so Contents rating for
        # the first time is exactly the change that could disturb it.
        for name, path, want in (("BUILDING Group I ", BGI, "263"),
                                 ("BUILDING Group II", BGII, "32")):
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {name} = {str(got):>5s}   (expected {want:>5s})"
                  f" {'OK' if good else 'MISMATCH'}  -- must not move")
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)}): "
                  + "; ".join(str(m)[:60] for m in ip.messages[:3]))
        print()

    if ok:
        print("All four Personal Property forms match, and Building is "
              "unmoved at 263 / 32.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
