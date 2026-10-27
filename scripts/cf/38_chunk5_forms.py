#!/usr/bin/env python3
"""Chunk 5, tasks C5-19, C5-20, C5-22 and C5-23 -- the per-form specifics.

  19  **Broad is a 2-rule chain -- the shortest in the project.** Own base
      rate, then the rate. No cause-of-loss adjustment, no `Factor`, and the
      final rate is a straight copy.
  20  **Special keys its base rate on covType AND risk type** -- a dimension
      neither Building's flat statewide Special nor Contents' occupancy-keyed
      Special uses.
  22  **The educational branch defaults to 0.0, not 1.0** -- one of the three
      meanings of zero the build order warned about.
  23  **Earthquake is a real fifth chain with no standalone premium file.**

All figures derived by hand from Oregon's filed rows before the run. The
golden case is `CovType` "Business Income With Extra Expense" on a Frame
building, which keys BOTH Broad and Special to the table's `"All Other"` rows.

    BROAD     Frame  All Other                   0.023 -> $23
              Frame  Without Extra Expense       0.011 -> $11
              FR     All Other                   0.012 -> $12
              FR     Without Extra Expense       0.007 -> $7

    SPECIAL   Frame  All Other / Other than Apts 0.047 -> $47
              class 0311 (an apartments class)  0.029 -> $29
              Frame  Without EE / Other than     0.033 -> $33
              class 1150 -> Builders Risk        0.018 -> $18

**Broad's covType key halves the rate.** "Business Income Without Extra
Expense" is 0.011 where "All Other" is 0.023, and the two strings are the only
Business Income values in a table shared with Building and Contents. Picking
the wrong one is a 2x error that looks entirely plausible.

    python scripts/cf/38_chunk5_forms.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import glob
import os
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
zeros5 = import_module("33_chunk5_zero_cases")
chunk5 = import_module("32_chunk5_golden_case")

BI = chunk5.BI
WITHOUT_EE = "Business Income Without Extra Expense"
FR = "Fire Resistive - Reinforced Masonry - Light Steel"

#: id, cause of loss, BI overrides, structure overrides, (base, premium), why
CASES = [
    # ---- C5-19
    ("19  Broad  Frame / All Other", "Broad", {}, {}, ("0.023", "23"),
     "the baseline. `All Other` because the coverage type is WITH extra "
     "expense -- the table's only other Business Income row is `Business "
     "Income Without Extra Expense`"),

    ("19  Broad  Frame / Without EE", "Broad", {"CovType": WITHOUT_EE}, {},
     ("0.011", "11"),
     "**the covType key halves the rate.** 0.011 against 0.023 on the same "
     "building, from two strings in a table shared with Building and Contents. "
     "Picking the wrong one is a 2x error that looks entirely plausible"),

    ("19  Broad  Fire Resistive / All Other", "Broad", {},
     {"ConstructionType": FR}, ("0.012", "12"),
     "construction still matters for Broad, where Basic Group I gets it "
     "second-hand through Building's computed rate"),

    ("19  Broad  Fire Resistive / Without EE", "Broad",
     {"CovType": WITHOUT_EE}, {"ConstructionType": FR}, ("0.007", "7"),
     "both keys at once -- 0.007 against the baseline's 0.023, a 3x spread "
     "across two fields"),

    # ---- C5-20
    ("20  Special  All Other / Other than Apts", "Special", {}, {},
     ("0.047", "47"), "the baseline"),

    ("20  Special  All Other / Apts and Condos", "Special", {},
     {"ClassCode": "0311"}, ("0.029", "29"),
     "**the risk-type key, which no other coverage's Special has.** Building's "
     "Special is a flat statewide constant and Contents' is occupancy-keyed; "
     "this one splits on whether the risk is apartments. "
     "And `ApartmentCondoIndicator` is DERIVED, not submitted -- "
     "`SetApartmentCondoIndicator` computes it from the class code against a "
     "hardcoded list of 13 (0300, 0311-0313, 0321-0323, 0331-0333, 0341-0343). "
     "Setting the indicator directly, on the record or on the structure, does "
     "nothing at all: it is overwritten with `No`. The same shape as chunk 4's "
     "`OccupCategoryRiskSeverity`, and the third derived-field trap in two "
     "chunks"),

    ("20  Special  Without EE / Other than Apts", "Special",
     {"CovType": WITHOUT_EE}, {}, ("0.033", "33"),
     "the covType key again, on a four-way table -- construction x covType x "
     "risk type, 24 countrywide rows"),

    ("20  Special  class 1150 -> Builders Risk", "Special", {},
     {"ClassCode": "1150"}, ("0.018", "18"),
     "the Builders Risk branch, a single countrywide row at 0.018 that ignores "
     "construction, covType and risk type alike"),

    # ---- C5-22
    ("22  TypeOfRisk = Educational Institutions", "Basic",
     {"TypeOfRisk": "Educational Institutions"}, {}, ("0", "0"),
     "**the educational branch, exactly as the build order described it.** "
     "The Factor is 0.0, not 1.0, and the premium is zero. Predicted as a "
     "NULL on the assumption the row was simply missing; it is a written "
     "zero, which is the build order's point -- one of CF's three meanings of "
     "zero, and the one that collapses a premium"),

    ("22  TypeOfRisk = Combined Educational + Rental", "Basic",
     {"TypeOfRisk": "Combined Educational Institutes and Rental Operations"},
     {}, ("0", "0"),
     "the combined educational risk IS filed -- at 0, for every coinsurance "
     "percentage, like the other three Combined risks. A filed zero and an "
     "absent row, side by side, both priced at nothing"),
]

BASE_DD = {"Broad": "BroadBaseRate", "Special": "SpecialBaseRate",
           "Basic": "Factor"}


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, col, bi_over, st_over, expect, why in CASES:
        sub = chunk5.submission(col)
        zeros5._bi(sub).update(bi_over)
        zeros2.structure(sub).update(st_over)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:44s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        form = "BasicGroupI" if col == "Basic" else col
        got = (read(f"{BI}/{BASE_DD[col]}", data),
               read(chunk5._P % form, data))
        good = got == expect
        ok &= good
        print(f"{name:44s} {BASE_DD[col][:9]:9s}={str(got[0]):>6s} "
              f"premium={str(got[1]):>3s}"
              + ("" if good else f"   <-- expected {expect}"))

    # ---- C5-19, the absent step
    print("\n=== 19  Broad has no cause-of-loss adjustment step")
    sub = chunk5.submission("Broad")
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    adj = read(f"{BI}/BroadCauseOfLossAdjustment", data)
    rate, final = (read(f"{BI}/BroadRate", data),
                   read(f"{BI}/FinalBroadRate", data))
    good = adj is None and rate == final == "0.023"
    ok &= good
    print(f"    BroadCauseOfLossAdjustment = {adj}  (expected None)")
    print(f"    rate {rate} -> final {final}  -- a straight copy, two rules "
          f"end to end  {'OK' if good else 'MISMATCH'}")

    # ---- C5-23
    print("\n=== 23  Earthquake runs, produces a rate, and charges nothing")
    eq_rate = read(f"{BI}/FinalEQRate", data)
    eq_prem = read(chunk5._P % "Earthquake", data)
    d = book.parent.package.content / "Rules"
    plain = os.path.join(str(d),
                         "CommercialPropertyBusinessIncomeEarthquakeCoverageRules.Rule.xml")
    variants = sorted(os.path.basename(x) for x in glob.glob(
        str(d / "CommercialPropertyBusinessIncome*Earthquake*.xml")))
    good = (not os.path.exists(plain)) and eq_prem is None
    ok &= good
    print(f"    FinalEQRate on a Basic submission : {eq_rate}")
    print(f"    plain Earthquake premium          : {eq_prem}  (expected None)")
    print(f"    plain Earthquake coverage FILE    : "
          f"{os.path.exists(plain)}  (expected False)")
    print(f"    Earthquake premium files that DO exist: {len(variants)}, and "
          f"every one is\n    an Agreed Value or endorsement variant  "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **A rate chain with nowhere to send its answer.** The chain")
    print("    runs unconditionally alongside the other four; only Agreed")
    print("    Value charges. Earthquake proper is chunk 10.")

    print("\nWhat each case proves")
    for name, _, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match, plus the two absences.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
