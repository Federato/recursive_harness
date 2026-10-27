#!/usr/bin/env python3
"""Chunk 6's golden cases -- Special Class, all four cause-of-loss forms.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK6-GOLDEN-CASE.md`.

Built differentially: the **same Oregon location as chunks 1-5**, with a Special
Class item on it. And Special Class hangs off the **LOCATION**, not the
Structure -- Contents live under Structure/OccupClass and Business Income under
the Structure, but a Special Class item is a SIBLING of the building record. It
is the first coverage in the project that is not inside a building.

    Basic Group I    $66     base 0.07   [CW, Option34a, "1 to 4"]
    Basic Group II   $209    base 0.028  [OR, Entire State, B, Bldg] x numeric 8
    Broad            $14     base 0.015  [CW, "Frame" LITERAL, Bldg]
    Special          $44     base 0.047  [OR, "Y"] -- CW files no row

The item is a broadcasting tower, chosen because its Group II numeric value is
**8** -- the largest single multiplier found anywhere in six chunks, and the
reason Group II is three times Group I on the same limit.

    python scripts/cf/41_chunk6_golden_case.py [--trace]

Exit 0 when all four forms match and Building is unmoved at 261 / 32.
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

chunk2 = import_module("09_chunk2_golden_case")

JURIS, ASOF = chunk2.JURIS, chunk2.ASOF
BGI, BGII = chunk2.BGI, chunk2.BGII

LOC = ("CommercialPropertyTable/CommercialProperty/"
       "CommercialPropertyLocationTable/CommercialPropertyLocation")
SC = LOC + "/CommercialPropertySpecialClassTable/CommercialPropertySpecialClass"

_P = SC + "/CommercialPropertySpecialClass%sCoverage/Premium"

#: The description is the rating driver. Its converted option keys Group I's
#: base rate; the RAW string keys Group II's numeric value -- two different
#: tables, two different key columns, one submitted field.
DESC = "Towers - Broadcasting Antennas (Cell, Radio and TV)"

RUNS = {
    "Basic": [("Basic Group I", _P % "BasicGroupI", "66"),
              ("Basic Group II", _P % "BasicGroupII", "209")],
    "Broad": [("Broad", _P % "Broad", "14")],
    "Special": [("Special", _P % "Special", "44")],
}

CHAIN = {"Basic": [
    ("ProtectionClassToUse", "1 to 4", "prep    protection class -- COPIED from the LOCATION"),
    ("SpecialClassDescConvertedOption", "Option34a", "prep    lookup 1 of 2 -- the description converted"),
    ("TotAmtInsuranceToUse", "100000", "prep    the ITEM's own limit, not the location total"),
    ("CoinsuranceFactor", "0.95", "BGI 1   coinsurance -- computed FIRST, unlike Building"),
    ("BasicGroupIBaseRate", "0.07", "BGI 2   base rate -- NO construction key"),
    ("BasicGroupIRate", "0.07", "BGI 3   rate"),
    ("BasicGroupICauseOfLossAdjustment", "0.07", "BGI 4   COL adjustment -- no sprinkler term"),
    ("AdjustedBasicGroupIRate", "0.067", "BGI 5   adjusted -- r3(0.0665), a half-up TIE"),
    ("DeductibleFactorBasicGroupI", "0.98", "BGI 6   deductible  [OR, 1,000, 50k-175k]"),
    ("FinalBasicGroupIRate", "0.066", "BGI 7   final rate -- three factors, not four"),

    ("BasicGroupIISymbolNum", "8", "BGII    numeric -- keyed on the RAW description"),
    ("BasicGroupIINumericValue", "8", "BGII 1  numeric value"),
    ("BasicGroupIIBaseRate", "0.028", "BGII 2  base rate        [OR, Bldg]"),
    ("LowestBasicGroupIIBaseRate", "0.028", "BGII 3  lowest (unused here)"),
    ("BasicGroupIIRate", "0.224", "BGII 4  rate -- base x LCM x EIGHT"),
    ("BasicGroupIICauseOfLossAdjustment", "0.224", "BGII 5  COL adjustment"),
    ("BasicGroupIICoinsuranceFactor", "0.95", "BGII 6  coinsurance -- copied, not flat"),
    ("AdjustedBasicGroupIIRate", "0.213", "BGII 7  adjusted rate"),
    ("DeductibleFactorBasicGroupII", "0.98", "BGII 9  deductible"),
    ("FinalBasicGroupIIRate", "0.209", "BGII 10 final rate"),
], "Broad": [
    ("BroadBaseRate", "0.015", "Broad 1 base rate -- LITERAL \"Frame\", not the item's"),
    ("BroadRate", "0.015", "Broad 2 rate"),
    ("AdjustedBroadRate", "0.014", "Broad 3 adjusted -- no COL adjustment step at all"),
    ("DeductibleFactorBroad", "0.97", "Broad 4 deductible [Other Cause Of Loss]"),
    ("FinalBroadRate", "0.014", "Broad 5 final rate"),
], "Special": [
    ("SpecialTheftExclusionIndicator", "0", "Spec 1  theft exclusion -- not elected"),
    ("SpecialTheftExclusionFactor", "1", "Spec 2  theft factor"),
    ("SpecialBaseRate", "0.047", "Spec 3  base rate  [OR] -- CW files NO row"),
    ("SpecialRate", "0.047", "Spec 4  rate"),
    ("SpecialCauseOfLossAdjustment", "0.047", "Spec 5  COL adjustment -- no roof factor"),
    ("AdjustedSpecialRate", "0.045", "Spec 6  adjusted -- r3(0.04465), a second TIE"),
    ("DeductibleFactorSpecial", "0.97", "Spec 8  deductible"),
    ("FinalSpecialRate", "0.044", "Spec 9  final rate"),
]}


def location(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])


def item(sub):
    return (location(sub)["CommercialPropertySpecialClassTable"]
            ["CommercialPropertySpecialClass"][0])


def submission(col="Basic"):
    """Chunk 2's building, plus a Special Class item on the same LOCATION.

    `col` is the cause of loss. Broad and Special gate their base rate on an
    exact match, so they need their own submissions -- but Basic Group I and II
    do NOT gate on it at all (C6-26), which is why the Basic pair is read off
    every run rather than only the Basic one.
    """
    sub = chunk2.submission()
    # **`PolicyType` is DERIVED, not submitted on the item.** Broad's and
    # Special's base rates both gate on it, and `SetPolicyType` copies it from
    # `../../../../PolicyType` -- the POLICY -- with no `IsNull` guard, so a
    # value set on the Special Class record is overwritten with blank and both
    # forms price at zero in silence. The fifth derived-field trap in four
    # chunks, and the first that lives four levels above the coverage.
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    location(sub)["CommercialPropertySpecialClassTable"] = {
        "CommercialPropertySpecialClass": [{
            "ClassDescription": DESC,
            "Limit": "100000",
            "CovType": "Bldg",
            "CauseOfLoss": col,
            "PolicyType": "Commercial Property Policy",
            "IncludedInBlkt": "No",
            # Not folded into a building: `SetTotAmtInsuranceToUse` therefore
            # copies the item's own `TotAmtInsurance`, which `SetTotAmtInsurance`
            # has already copied from `Limit`. The band is the ITEM's, not the
            # location's.
            "IncludedInBuilding": "No",
            "LossCostMultiplier": "1.0",
            "Coinsurance": "90%",
            "Deductible": "1,000",
            "ConstructionType": "Frame",
            # Group II's symbol has NO setter in this ruleset -- Building
            # derives its own from construction and storeys, Special Class
            # reads this and never writes it (C6-18).
            "BasicGroupIISymbol": "B",
            "BasicGroupIIRatingTerr": "Entire State",
        }],
    }
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
            got = read(f"{SC}/{dd}", data)
            good = want is None or got == want
            ok &= good
            flag = "" if good else f"   <-- expected {want}"
            print(f"    {label:56s} {dd:34s} = {got}{flag}")

        for form, path, want in wanted:
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {form:16s} PREMIUM = {str(got):>5s}   "
                  f"(expected {want:>5s}) {'OK' if good else 'MISMATCH'}")

        # Special Class is a SIBLING of the Structure, not a child. Its 100,000
        # limit should not reach Building's `TotAmtInsurance` and should not
        # move Building's deductible factor off chunk 1 case A's 0.98.
        for name, path, want in (("BUILDING Group I ", BGI, "261"),
                                 ("BUILDING Group II", BGII, "32")):
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {name} = {str(got):>5s}   (expected {want:>5s})"
                  f" {'OK' if good else 'MISMATCH'}  -- must not move")
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)}): "
                  + "; ".join(str(m)[:60] for m in ip.messages[:4]))
        print()

    if ok:
        print("All four Special Class forms match, and Building is unmoved "
              "at 261 / 32.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
