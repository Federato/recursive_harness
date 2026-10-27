#!/usr/bin/env python3
"""Chunk 5's golden cases -- Business Income, all four cause-of-loss forms.

Built differentially on the same Oregon building as chunks 1-4: class 0951,
Frame, Protection Class 3, Portland, symbol B / Entire State / BCEG 4, limit
100,000, coinsurance 90%, LCM 1.0. The Business Income record carries a 100,000
limit, `CovType` "Business Income With Extra Expense" and `TypeOfRisk`
"Mercantile and Non-manufacturing".

**Business Income is arithmetically downstream of Building** -- C5-02's whole
point. Basic Group I reads the Structure's already-computed
`BasicGroupIBaseRate` and Basic Group II reads the shared `BasicGroupIIRate`
table **with the literal covType `"Bldg"`**: not a Business Income row, the
BUILDING's row. Only Broad and Special have base rates of their own.

Derived by hand from Oregon's filed rows before the run:

    BASIC GROUP I   Building's base 0.498, adjustment 0.85 [OR]
        rate   = 0.498 x terr 0.499 x protClass 0.96 x 0.85        = 0.203
        COLadj = r3(0.203 - 0) x 1 x 1 x 1                         = 0.203
        Factor = BusnIncomeFactor[CW, With Extra Expense,
                 Mercantile and Non-manufacturing, 90%]            = 0.55
        final  = r3(0.203 x 0.55)                                  = 0.112  -> $112

    BASIC GROUP II  BasicGroupIIRate[OR, Entire State, B, "Bldg"]  = 0.028
        rate   = r3(r3(0.028 x BCEG 0.96) x adjustment 0.9)        = 0.024
        final  = r3(0.024 x Factor 0.55)                           = 0.013  -> $13
        **This was predicted at $14 and the engine said $13 -- BCEG applies.**
        The prediction was written without it because the algorithms page's
        five-way comparison lists only `BGIIBaseRateAdjustmentFactor` as
        Business Income's own multiplier for this form. It also inherits
        Building's BCEG factor. The comparison table is incomplete; corrected
        there.

    BROAD           BroadFormBaseRate[CW, Frame, "All Other"]      = 0.023
        final  = rate = 0.023                                               -> $23
        "All Other" because the CovType is WITH extra expense; the table's
        other Business Income row is "Business Income Without Extra Expense"
        at 0.011. **A two-value covType key, and the wrong one is half price.**

    SPECIAL         SpecialFormIncldgTheftTimeElementBaseRate
                    [CW, Frame, "All Other", "Other than Apartments
                     and Condominiums"]                            = 0.047
        final  = rate x theft 1.0 = 0.047                                   -> $47

**No deductible factor and no limit-of-insurance factor appear anywhere in any
of the four chains** -- the premium is the final rate times `Limit / 100`
directly. That is C5-24 and C5-25, and it is visible in every line above.

**And each form gates on the cause of loss**, so Business Income needs a
submission per form exactly as chunks 3 and 4 did -- the pattern has now held
for three coverages running. The first draft ran one submission and read Broad
and Special pricing at zero as a defect; it is the gate working.

**Building must not move**: $261 and $32, chunk 1 case A and chunk 2.

    python scripts/cf/32_chunk5_golden_case.py [--trace]

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

chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")

JURIS, ASOF = chunk2.JURIS, chunk2.ASOF
STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII

BI = STRUCT + "/CommercialPropertyBusinessIncomeTable/CommercialPropertyBusinessIncome"
_P = BI + "/CommercialPropertyBusinessIncome%sCoverage/Premium"

COVTYPE = "Business Income With Extra Expense"
RISK = "Mercantile and Non-manufacturing"

#: cause of loss -> [(form, premium path, expected)]
RUNS = {
    "Basic": [("Basic Group I", _P % "BasicGroupI", "112"),
              ("Basic Group II", _P % "BasicGroupII", "13")],
    "Broad": [("Broad", _P % "Broad", "23")],
    "Special": [("Special", _P % "Special", "47")],
}

#: cause of loss -> the chain steps that submission proves.
CHAIN = {"Basic": [
    ("BGIBaseRateAdjustmentFactor", "0.85", "BGI   adjustment      [OR]"),
    ("BasicGroupIRate", "0.203", "BGI   rate -- off BUILDING's base rate"),
    ("BasicGroupICauseOfLossAdjustment", "0.203", "BGI   COL adjustment"),
    ("TypeOfRiskFactor", "0.55", "      type-of-risk    [CW, 3 keys]"),
    ("Factor", "0.55", "      Factor -- ONE of four, not a product"),
    ("FinalBasicGroupIRate", "0.112", "BGI   final rate"),

    ("BGIIBaseRateAdjustmentFactor", "0.9", "BGII  adjustment      [OR]"),
    ("BasicGroupIIBaseRate", "0.028", "BGII  base -- the BUILDING row, covType 'Bldg'"),
    ("BasicGroupIIRate", "0.024", "BGII  rate -- BCEG applies too"),
    ("FinalBasicGroupIIRate", "0.013", "BGII  final rate"),
], "Broad": [
    ("BroadBaseRate", "0.023", "Broad base -- covType 'All Other'"),
    ("BroadRate", "0.023", "Broad rate"),
    ("FinalBroadRate", "0.023", "Broad final -- a straight copy, no Factor"),
], "Special": [
    ("SpecialBaseRate", "0.047", "Spec  base -- covType + risk type"),
    ("SpecialTheftExclusionFactor", "1", "Spec  theft (not elected)"),
    ("SpecialCauseOfLossAdjustment", "0.047", "Spec  COL adjustment"),
    ("FinalSpecialRate", "0.047", "Spec  final -- a straight copy, no Factor"),
]}


def submission(col="Basic"):
    """Chunk 2's building, plus a Business Income record that rates.

    `col` is the cause of loss, carried on the BUSINESS INCOME record -- each
    form gates its base rate on it, so the four premiums never appear together.
    """
    sub = chunk2.submission()
    st = zeros2.structure(sub)
    st["CommercialPropertyBusinessIncomeTable"] = {
        "CommercialPropertyBusinessIncome": [{
            "Limit": "100000",
            "CovType": COVTYPE,
            "TypeOfRisk": RISK,
            "Coinsurance": "90%",
            "LossCostMultiplier": "1.0",
            "IncludedInBlkt": "No",
            # The three `SetFactor` branch tests, all set to their
            # NON-selecting values so the default branch runs. Each is a
            # separate case in C5-10.
            "MaxPeriod": "No",
            "MonthlyLimitOfIndemnity": "Not Applicable",
            "CauseOfLoss": col,
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
            got = read(f"{BI}/{dd}", data)
            good = want is None or got == want
            ok &= good
            flag = "" if good else f"   <-- expected {want}"
            print(f"    {label:48s} {dd:34s} = {got}{flag}")

        for form, path, want in wanted:
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {form:16s} PREMIUM = {str(got):>5s}   "
                  f"(expected {want:>5s}) {'OK' if good else 'MISMATCH'}")

        # Building must not move. Business Income READS Building's rate, so the
        # two are coupled by design in one direction -- and must not be in the
        # other.
        for name, path, want in (("BUILDING Group I ", BGI, "261"),
                                 ("BUILDING Group II", BGII, "32")):
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {name} = {str(got):>5s}   (expected {want:>5s})"
                  f" {'OK' if good else 'MISMATCH'}  -- must not move")
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)})")
        print()

    if ok:
        print("All four Business Income forms match, and Building is unmoved")
        print("at 261 / 32. No engine code was written -- the fifth coverage")
        print("in a row on chunk 0's foundation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
