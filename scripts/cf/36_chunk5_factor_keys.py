#!/usr/bin/env python3
"""Chunk 5, tasks C5-11 to C5-14 -- the `Factor` lookup, and who uses it.

  11  `TypeOfRiskFactor` reads `BusnIncomeFactor` on THREE keys -- `CovType`
      x `TypeOfRisk` x `CoinsuranceToUse`. A case on each dimension, so a wrong
      key is distinguishable from a wrong value.
  12  **The combined type-of-risk blend, and what it actually reads.**
  13  `CoinsuranceToUse` is not the structure's coinsurance copied down.
  14  **Broad and Special never apply `Factor` at all.**

All figures derived by hand from Oregon's filed rows before the run, against
the chunk 5 golden case: Basic Group I rate 0.203, Factor 0.55, premium $112.

**C5-12 is the one that needed finding first.** The algorithms page says the
blend is "a percentage-weighted blend of two `TypeRiskCombination1Factor` /
`TypeRiskCombination2Factor` lookups". There are no such tables -- C5-03
established that. Reading the rule: the blend is

    r3( r3(ManufacturingPct/100 x TypeRiskCombination1Factor)
        + (OtherPct/100 x TypeRiskCombination2Factor) )

and **both `TypeRiskCombination*Factor` values are read from the SUBMISSION**,
through `FirstValue FromConstant="0.0"`. Nothing is looked up. So a combined
risk needs four submitted fields -- two percentages and two component factors --
and absent means zero on all four, which is why C5-03's combined-risk case
priced at zero.

That puts it in the same family as chunk 4's watchman credit: a submitter-
supplied factor that ISO intends. It is now the second such case, and the
boundary between "intended" and "a hole" is getting a shape.

    40% manufacturing at 0.71, 60% mercantile at 0.55
        r3(r3(0.284) + 0.330) = 0.614 -> final 0.125 -> $125

    python scripts/cf/36_chunk5_factor_keys.py

Exit 0 when every case matches.
"""
from __future__ import annotations

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
zeros5 = import_module("33_chunk5_zero_cases")
chunk5 = import_module("32_chunk5_golden_case")

BI, BGI = chunk5.BI, chunk2.BGI
COMBINED = "Combined Manufacturing and Mercantile Operations"

#: id, cause of loss, BI-record overrides, (CoinsuranceToUse, Factor, premium,
#: Building Group I), why
CASES = [
    ("baseline", "Basic", {}, ("90%", "0.55", "112", "261"),
     "the reference"),

    # ---- C5-11, one key dimension at a time
    ("11  TypeOfRisk = Manufacturing", "Basic",
     {"TypeOfRisk": "Manufacturing"}, ("90%", "0.71", "144", "261"),
     "the risk-classification key. Manufacturing is 0.71 against Mercantile's "
     "0.55 -- a 29% load on the same building"),

    ("11  CovType = Without Extra Expense", "Basic",
     {"CovType": "Business Income Without Extra Expense"},
     ("90%", "0.5", "102", "261"),
     "the coverage-type key. Dropping extra expense takes the factor from "
     "0.55 to 0.50"),

    # ---- C5-11 third key AND C5-13 in one case
    ("11/13  BI Coinsurance = 80%", "Basic", {"Coinsurance": "80%"},
     ("80%", "0.59", "120", "261"),
     "**the coinsurance key, and where it comes from.** The factor moves "
     "0.55 -> 0.59 and **Building stays at $261** -- the structure is still at "
     "90%. So `CoinsuranceToUse` follows the BUSINESS INCOME record, not the "
     "building it is attached to, and the two coverages can carry different "
     "coinsurance on one submission.\\n"
     "    Note the direction: a LOWER coinsurance percentage is a HIGHER "
     "factor here, because `BusnIncomeFactor` is a discount table -- the "
     "opposite of Building's coinsurance factor, which runs 1.0 at 80% and "
     "0.95 at 90%"),

    # ---- C5-12
    ("12  combined risk, blended", "Basic",
     {"TypeOfRisk": COMBINED,
      "CombinedTypeOfRiskManufacturingPct": "40",
      "CombinedTypeOfRiskMercantilePct": "60",
      "TypeRiskCombination1Factor": "0.71",
      "TypeRiskCombination2Factor": "0.55"},
     ("90%", "0.614", "125", "261"),
     "**the blend, with all four fields supplied.** 0.4 x 0.71 + 0.6 x 0.55 = "
     "0.614. Without them the filed row is 0 and the premium is zero (C5-03) "
     "-- so a combined risk is not a rateable selection on its own, it is a "
     "selection PLUS four submitted numbers"),
]

#: C5-14: elect a Factor branch under Broad and Special and prove the premium
#: does not respond. `Factor` is still computed -- it is simply never read.
IGNORES_FACTOR = [("Broad", "23"), ("Special", "47")]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, col, over, expect, why in CASES:
        sub = chunk5.submission(col)
        zeros5._bi(sub).update(over)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:38s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{BI}/CoinsuranceToUse", data),
               read(f"{BI}/Factor", data),
               read(chunk5._P % "BasicGroupI", data),
               read(BGI, data))
        good = got == expect
        ok &= good
        print(f"{name:38s} coins={str(got[0]):>4s} Factor={str(got[1]):>6s} "
              f"BI={str(got[2]):>4s} Building={str(got[3]):>4s}"
              + ("" if good else f"   <-- expected {expect}"))

    print("\n=== 14  Broad and Special never apply Factor")
    for col, want in IGNORES_FACTOR:
        sub = chunk5.submission(col)
        # MaxPeriod elects the 1.15 branch -- more than double the default
        # 0.55. If either form applied `Factor`, the premium could not hold.
        zeros5._bi(sub)["MaxPeriod"] = "Yes"
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        ip.run(data)
        fac = read(f"{BI}/Factor", data)
        prem = read(chunk5._P % col, data)
        good = prem == want and fac == "1.15"
        ok &= good
        print(f"    {col:8s} Factor={fac} (computed) premium={prem}  "
              f"(expected {want}, unchanged) {'OK' if good else 'MISMATCH'}")
    print("    The Factor is computed for every form and READ by only two.")
    print("    Electing max-period moves Basic Group I from $112 to $233 and")
    print("    leaves Broad and Special exactly where they were.")

    print("\nWhat each case proves")
    for name, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES) + len(IGNORES_FACTOR)} cases match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
