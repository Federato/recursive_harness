#!/usr/bin/env python3
"""Chunk 7's golden cases -- Special Class Business Income, four core forms.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK7-GOLDEN-CASE.md`.

Built differentially: **chunk 6's Special Class item**, with a Business Income
record hanging off it. The nesting is three deep and new to the project --
Location -> SpecialClass -> SpecialClassBusnIncome -- so `../../` from the
Business Income record is the Special Class item.

    Basic Group I    $39    rate = a straight COPY of the item's 0.07
    Basic Group II   $123   base 0.028 [OR, Entire State, B, "Bldg"] x the
                            item's numeric value 8
    Broad            $23    base 0.023 [CW, "Frame" LITERAL, "All Other"]
    Special          $47    base 0.047 [CW, "Frame", "All Other",
                            "Other than Apartments and Condominiums" LITERAL]

**Broad and Special come out identical to chunk 5's plain Business Income.**
That is not a coincidence and not a defect: both coverages read the same shared
tables, and on a Frame building with extra expense and a non-apartment risk the
pinned literals land on exactly the rows plain Business Income computes its way
to. **The pins only bite when the parent is not Frame or is apartments** --
which is C7-18 and C7-19's job, not this case's.

    python scripts/cf/50_chunk7_golden_case.py [--trace]

Exit 0 when all four forms match and the Special Class item is unmoved.
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

raas6 = import_module("44_chunk6_raas")
chain6 = import_module("45_chunk6_description_chain")
g6 = import_module("41_chunk6_golden_case")

JURIS, ASOF = g6.JURIS, g6.ASOF
SC = g6.SC
BI = SC + ("/CommercialPropertySpecialClassBusnIncomeTable"
           "/CommercialPropertySpecialClassBusnIncome")
_P = BI + "/CommercialPropertySpecialClassBusnIncome%sCoverage/Premium"
P6 = {f: g6._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}

#: The Business Income record. Chunk 5's inputs, on chunk 6's parent.
RECORD = {
    "Limit": "100000",
    "CovType": "Business Income With Extra Expense",
    "TypeOfRisk": "Mercantile and Non-manufacturing",
    "Coinsurance": "90%",
    "LossCostMultiplier": "1.0",
    "IncludedInBlkt": "No",
    # **These two are not optional, and the first run proved it.**
    # `SetFactor` picks by priority, and its second branch tests
    # `MonthlyLimitOfIndemnity != "Not Applicable"` through
    # `FirstValue FromConstant=""`. An ABSENT field therefore reads as `""`,
    # which is not equal to "Not Applicable", so the branch is ELECTED -- and
    # it copies `MonthlyLimitOfIndemnityFactor`, which nothing has computed.
    # `Factor` lands on 0, `TypeOfRiskFactor` sits at a perfectly good 0.55
    # one field away, and both Basic premiums are $0 with no message.
    # **Omitting a field is not the same as saying "Not Applicable".**
    "MaxPeriod": "No",
    "MonthlyLimitOfIndemnity": "Not Applicable",
}

RUNS = {
    "Basic": [("Basic Group I", _P % "BasicGroupI", "39"),
              ("Basic Group II", _P % "BasicGroupII", "123")],
    "Broad": [("Broad", _P % "Broad", "23")],
    "Special": [("Special", _P % "Special", "47")],
}

CHAIN = {"Basic": [
    ("BasicGroupIRate", "0.07", "BGI 1  a straight COPY of ../../BasicGroupIRate"),
    ("VandalismExclFactor", "1", "       the ONLY multiplier in the adjustment"),
    ("BasicGroupICauseOfLossAdjustment", "0.07", "BGI 2  rate x vandalism, and nothing else"),
    ("Factor", "0.55", "       the shared BusnIncomeFactor [CW]"),
    ("FinalBasicGroupIRate", "0.039", "       final -- r3(0.07 x 0.55), a half-up tie"),

    ("BasicGroupIIBaseRate", "0.028", "BGII 1 its OWN lookup [OR, Entire State, B, \"Bldg\"]"),
    ("BasicGroupIIRate", "0.224", "BGII 3 base x LCM x the ITEM's numeric value 8"),
    ("BasicGroupIICauseOfLossAdjustment", "0.224", "BGII 4 no wind/hail exclusion -- a copy"),
    ("FinalBasicGroupIIRate", "0.123", "       final -- r3(0.224 x 0.55)"),
], "Broad": [
    ("BroadBaseRate", "0.023", "Broad 1 [CW, \"Frame\" LITERAL, \"All Other\"]"),
    ("BroadRate", "0.023", "Broad 2 base x LCM"),
    ("FinalBroadRate", "0.023", "        a straight copy -- no Factor, no adjustment"),
], "Special": [
    ("SpecialTheftExclusionFactor", "1", "Spec 1 theft (not elected)"),
    ("SpecialBaseRate", "0.047", "Spec 2 [CW, \"Frame\", \"All Other\", \"Other than Apts\"]"),
    ("SpecialRate", "0.047", "Spec 3 base x LCM"),
    ("SpecialCauseOfLossAdjustment", "0.047", "Spec 4 rate x theft factor"),
    ("FinalSpecialRate", "0.047", "       a straight copy -- no Factor"),
]}


def submission(col="Basic"):
    """Chunk 6's Special Class item, with a Business Income record on it."""
    sub = g6.submission(col)
    item = g6.item(sub)
    rec = dict(RECORD, CauseOfLoss=col)
    item["CommercialPropertySpecialClassBusnIncomeTable"] = {
        "CommercialPropertySpecialClassBusnIncome": [rec],
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
            print(f"    {label:52s} {dd:34s} = {got}"
                  + ("" if good else f"   <-- expected {want}"))

        for form, path, want in wanted:
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {form:16s} PREMIUM = {str(got):>5s}   "
                  f"(expected {want:>5s}) {'OK' if good else 'MISMATCH'}")

        # The parent must not move. Business Income reads its finished rate,
        # so anything it did to the parent would be invisible in its own
        # premium and fatal everywhere else.
        for name, form, want in (("SPECIAL CLASS Group I ", "BasicGroupI", "66"),
                                 ("SPECIAL CLASS Group II", "BasicGroupII", "209")):
            got = read(P6[form], data)
            good = got == want
            ok &= good
            print(f"    {name} = {str(got):>5s}   (expected {want:>5s})"
                  f" {'OK' if good else 'MISMATCH'}  -- must not move")
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)}): "
                  + "; ".join(str(m)[:56] for m in ip.messages[:4]))
        print()

    if ok:
        print("All four forms match, and the Special Class item is unmoved "
              "at 66 / 209.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
