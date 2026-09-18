#!/usr/bin/env python3
"""Chunk 5, task C5-10 -- `SetFactor` picks exactly ONE of four.

The chunk's central machinery, and the one the build order singled out:

    Factor = MaxPeriodOfIndemnityFactor      if MaxPeriod = "Yes"
           | MonthlyLimitOfIndemnityFactor   elif MonthlyLimitOfIndemnity <> "Not Applicable"
           | ExtraExpenseFactor              elif CovType = "Extra Expense Only"
           | TypeOfRiskFactor                otherwise

**Multiplying them instead of selecting would overstate the premium by a large
multiple**, and no single case can show which happened -- a case that elects one
branch looks identical either way. So the set below elects each branch alone AND
elects several at once, which is the only way to tell selection from
multiplication, and priority from selection.

Derived by hand from Oregon's filed rows before the run, on the chunk 5 golden
case (Basic Group I rate 0.203, `CovType` "Business Income With Extra Expense",
`TypeOfRisk` "Mercantile and Non-manufacturing", coinsurance 90%):

    default    TypeOfRiskFactor          0.55  -> final 0.112 -> $112
    MaxPeriod  MaxPeriodOfIndemnity      1.15  -> final 0.233 -> $233
    monthly    MonthlyLimitOfIndemnity   1.08  -> final 0.219 -> $219
    extra exp  ExtraExpenseFactor        1.70  -> final 0.345 -> $345

    **MaxPeriod AND monthly together    -> 1.15, $233**
        multiplying gives 1.15 x 1.08 = 1.242, final 0.252, $252
    **all three together                -> NULL, $0**
        predicted 1.15/$233; multiplying would give 2.11, final 0.428, $428

$233 against $252 is the proof of priority. The three-way case proves
something the task did not ask about: **the winning branch can fail to
resolve, and `SetFactor` does not fall through.** `MaxPeriodOfIndemnityFactor`
is keyed on `CovType` and files no `Extra Expense Only` row, so the first
branch wins, finds nothing, and the premium is zero.

    python scripts/cf/35_chunk5_factor.py

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

BI = chunk5.BI
PREM = chunk5._P % "BasicGroupI"
EE_LIMITS = "40%,80%,100%"

#: id, BI-record overrides, (Factor, final rate, premium), why
CASES = [
    ("default -- TypeOfRiskFactor", {}, ("0.55", "0.112", "112"),
     "the fourth branch, and the only one that reads the three-key "
     "`BusnIncomeFactor` table"),

    ("MaxPeriod = Yes", {"MaxPeriod": "Yes"}, ("1.15", "0.233", "233"),
     "the first branch. **A factor above 1.0** -- the max-period-of-indemnity "
     "option is a surcharge, where the default type-of-risk factor is a "
     "discount at 0.55. Electing it more than doubles the premium"),

    ("MonthlyLimitOfIndemnity = 1/3",
     {"MonthlyLimitOfIndemnity": "1/3"}, ("1.08", "0.219", "219"),
     "the second branch, keyed on the fraction as well as covType and risk"),

    ("CovType = Extra Expense Only",
     {"CovType": "Extra Expense Only",
      "ExtraExpenseLimitOnLossPayment": EE_LIMITS}, ("1.7", "0.345", "345"),
     "the third branch, keyed on the limits-on-loss-payments schedule rather "
     "than on the risk at all. **`Extra Expense Only` appears in 18 rules** "
     "(C5-07), so this literal does more than pick a branch. "
     "And the field is `ExtraExpenseLimitOnLossPayment` -- the TABLE's key "
     "column is called `ExtraExpnLimitOnLossPymts`, which is not the datadef "
     "name. Supplying the column name leaves the factor at 0 and the premium "
     "at zero, silently"),

    ("MaxPeriod AND monthly limit",
     {"MaxPeriod": "Yes", "MonthlyLimitOfIndemnity": "1/3"},
     ("1.15", "0.233", "233"),
     "**priority, not just selection.** MaxPeriod wins and the monthly limit "
     "is discarded. Multiplying the two would give 1.242, a final rate of "
     "0.252 and a premium of $252"),

    ("all three elected at once",
     {"MaxPeriod": "Yes", "MonthlyLimitOfIndemnity": "1/3",
      "CovType": "Extra Expense Only", "ExtraExpenseLimitOnLossPayment": EE_LIMITS},
     (None, "0", "0"),
     "**predicted at $233 and it is $0 -- and the correction is worth more "
     "than the prediction.** The MaxPeriod branch still wins on priority, but "
     "`MaxPeriodOfIndemnityFactor` is itself keyed on `CovType`, and there is "
     "no `Extra Expense Only` row in it. So the winning branch cannot resolve, "
     "the Factor is NULL, and the premium is zero. "
     "    **`SetFactor` is a priority selector with no recovery.** It does not "
     "fall through to the next branch when the branch it chose fails -- it "
     "just produces nothing. Electing a valid combination of options can "
     "therefore price at zero in silence, which is a different failure from "
     "the multiplication the build order warned about, and one nothing in the "
     "corpus documents"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, over, expect, why in CASES:
        sub = chunk5.submission("Basic")
        zeros5._bi(sub).update(over)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:34s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{BI}/Factor", data),
               read(f"{BI}/FinalBasicGroupIRate", data),
               read(PREM, data))
        good = got == expect
        ok &= good
        print(f"{name:34s} Factor={str(got[0]):>6s} final={str(got[1]):>6s} "
              f"premium={str(got[2]):>4s}"
              + ("" if good else f"   <-- expected {expect}"))

    print("\nWhat each case proves")
    for name, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print("`SetFactor` selects exactly one value, in priority order.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
