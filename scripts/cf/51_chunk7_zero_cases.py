#!/usr/bin/env python3
"""Chunk 7, task C7-03 -- every zero tested against its consuming branch.

Six cases, each derived by hand before the run. Baseline: Basic Group I **$39**,
Basic Group II **$123**, Broad **$23**, Special **$47**, with the Special Class
item at **$66 / $209**.

  1  **The parent cannot rate.** Remove the item's `ClassDescription` and its
     Basic Group I rate is 0 -- so Business Income's Group I is 0 too, while
     Group II, Broad and Special carry on untouched.
  2  **The parent's deductible, removed.** The item's OWN premiums go to zero
     and **Business Income does not move at all** -- because it copies the
     parent's rate, which is computed BEFORE the deductible factor.
  3  **No `MonthlyLimitOfIndemnity`.** An absent field elects a priced branch
     whose factor nothing computed. Both Basic forms zero; Broad and Special
     untouched, because neither reads `Factor`.
  4  **No `TypeOfRisk`.** The factor lookup misses and the same two forms fall.
  5  **The parent's Group II symbol, removed.** Business Income's Group II
     falls and its Group I does not -- two forms borrowing two different
     things from the same parent.
  6  **No `Limit`.** Predicted to raise, as every coverage before it has.

    python scripts/cf/51_chunk7_zero_cases.py

Exit 0 when every case matches its derivation.
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

g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")

BI, SC = g7.BI, g7.SC
RAISES = object()

P7 = {f: g7._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
P6 = {f: g6._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}


def record(sub):
    return (g6.item(sub)["CommercialPropertySpecialClassBusnIncomeTable"]
            ["CommercialPropertySpecialClassBusnIncome"][0])


#: id, mutation, {form: BI premium}, (item Group I, item Group II), why
CASES = [
    ("0  baseline", lambda s: None,
     {"Basic": ("39", "123"), "Broad": ("23",), "Special": ("47",)},
     ("66", "209"), "the reference"),

    ("1  the parent has no ClassDescription",
     lambda s: g6.item(s).pop("ClassDescription", None),
     {"Basic": ("0", "0"), "Broad": ("23",), "Special": ("47",)},
     ("0", "0"),
     "**predicted to take ONE child form and it takes TWO.** Group I was "
     "obvious -- the item's Group I rate is 0 and the child copies it. Group "
     "II was predicted to survive at $123 because it does its own lookup, and "
     "it does -- the base rate is still a healthy 0.028. What kills it is the "
     "OTHER borrowed value: `BasicGroupIINumericValue`, which the parent looks "
     "up on the RAW class description. **The description feeds both the "
     "answer Group I borrows and the multiplier Group II borrows**, so one "
     "missing field on the parent reaches two child forms by two different "
     "routes. Broad and Special, which borrow nothing, are untouched"),

    ("2  the parent has no Deductible",
     lambda s: g6.item(s).pop("Deductible", None),
     {"Basic": ("39", "123"), "Broad": ("23",), "Special": ("47",)},
     ("0", "0"),
     "**the parent prices at ZERO and the child does not move.** The "
     "deductible factor is applied at the parent's FINAL-rate step, and "
     "Business Income copies `BasicGroupIRate` -- two steps earlier. So a "
     "Special Class item worth nothing still carries a $39 Business Income "
     "premium, and nothing anywhere says so"),

    ("3  no MonthlyLimitOfIndemnity",
     lambda s: record(s).pop("MonthlyLimitOfIndemnity", None),
     {"Basic": ("0", "0"), "Broad": ("23",), "Special": ("47",)},
     ("66", "209"),
     "**omitting a field is not saying \"Not Applicable\".** The absent field "
     "reads as `\"\"`, which is not equal to \"Not Applicable\", so "
     "`SetFactor` elects the monthly-limit branch and copies a factor nothing "
     "computed. Broad and Special never read `Factor` and are untouched"),

    ("4  no TypeOfRisk", lambda s: record(s).pop("TypeOfRisk", None),
     {"Basic": ("0", "0"), "Broad": ("23",), "Special": ("47",)},
     ("66", "209"),
     "the same two forms, a different route -- the factor lookup misses on a "
     "blank key instead of electing the wrong branch. **Two unrelated causes, "
     "one indistinguishable $0**"),

    ("5  the parent has no BasicGroupIISymbol",
     lambda s: g6.item(s).pop("BasicGroupIISymbol", None),
     {"Basic": ("39", "0"), "Broad": ("23",), "Special": ("47",)},
     ("66", "0"),
     "**the mirror of case 1.** Group II borrows an INPUT from the parent and "
     "falls; Group I borrows an ANSWER and holds at $39. Two forms, two kinds "
     "of borrowing, and only one of them notices"),

    ("6  no Limit on the BI record",
     lambda s: record(s).pop("Limit", None), RAISES, ("66", "209"),
     "predicted to raise, as every coverage before it has -- the null-premium "
     "guard, contract 12.3"),
]

PATHS = {"Basic": [("Basic Group I", P7["BasicGroupI"]),
                   ("Basic Group II", P7["BasicGroupII"])],
         "Broad": [("Broad", P7["Broad"])],
         "Special": [("Special", P7["Special"])]}


def main() -> int:
    book = book_for(g7.JURIS, g7.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, item, why in CASES:
        print(f"=== {name}")
        raised, got = None, {}
        for col in PATHS:
            sub = g7.submission(col)
            mutate(sub)
            ip = Interpreter(book, rounding=ROUNDING, trace=False,
                             null_arithmetic=NULL_ARITHMETIC)
            data = Node.from_dict(f"MasterCF{g7.JURIS}", sub)
            try:
                ip.run(data)
            except Exception as exc:
                raised = f"{type(exc).__name__}: {exc}"
                break
            got[col] = tuple(str(read(p, data)) for _, p in PATHS[col])
            if col == "Basic":
                got["_item"] = (str(read(P6["BasicGroupI"], data)),
                                str(read(P6["BasicGroupII"], data)))

        if expect is RAISES:
            good = raised is not None
            ok &= good
            print(f"    RAISED: {str(raised)[:110]}   (expected a refusal) "
                  f"{'OK' if good else 'MISMATCH -- it rated'}")
        elif raised is not None:
            ok = False
            print(f"    RAISED unexpectedly: {raised}")
        else:
            for col in PATHS:
                good = got[col] == expect[col]
                ok &= good
                labels = [l for l, _ in PATHS[col]]
                pairs = ", ".join(f"{l} {v}" for l, v in zip(labels, got[col]))
                print(f"    {pairs:46s} (expected {expect[col]}) "
                      f"{'OK' if good else 'MISMATCH'}")
            good = got["_item"] == item
            ok &= good
            print(f"    SPECIAL CLASS ITEM {got['_item'][0]} / "
                  f"{got['_item'][1]:<4s}{'':>12s} (expected {item}) "
                  f"{'OK' if good else 'MISMATCH'}")
        print()

    print("What each case proves")
    for name, _, _, _, why in CASES[1:]:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match their derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
