#!/usr/bin/env python3
"""Chunk 7, tasks C7-10 to C7-14 -- the borrowed rate.

  10  **Basic Group I is a straight copy of the parent's FINISHED rate.**
  11  **Earthquake borrows `EQRate` and has no standalone premium file.**
  12  **ELEVEN values cross the boundary** -- the census said five, the
      golden case found six by hand, and an unfiltered regex finds eleven.
  13  The parent's failures propagate -- settled inside the sweep
      (`52_chunk7_enumerate_states.py`); re-asserted here in one line.
  14  **The shared `Factor` -- read by two forms, ignored by three.**

All figures derived by hand from the filed rows before the run. The baseline is
the chunk 7 golden case: Basic Group I **$39**, Basic Group II **$123**.

    10  parent ClassDescription -> Aircraft   parent rate 0.286
            r3(0.286 x 0.55) = 0.157                              $157
        parent LossCostMultiplier 2.0         parent rate 0.14
            r3(0.14 x 0.55) = 0.077                               $77

    12  the CHILD's own LossCostMultiplier 5.0
            Group I  unchanged at $39   -- the rate step is a COPY
            Group II r3(r3(0.028x5)x8) = 1.12 -> r3(0.616) = 0.616 $616
        **One field, inert in one form and five-fold in another.**

    14  TypeOfRisk Manufacturing      0.71  -> r3(0.0497) = 0.05   $50
        MaxPeriod "Yes"               1.15  -> r3(0.0805) = 0.081  $81
        CovType Extra Expense Only    1.7   -> r3(0.119)          $119
        and Broad / Special hold at $23 / $47 through all of it

    python scripts/cf/54_chunk7_borrowed.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")

SC, BI, ASOF = g7.SC, g7.BI, g7.ASOF
P7 = {f: g7._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
P6 = {f: g6._P % f for f in ("BasicGroupI", "BasicGroupII")}
LOC = ("CommercialPropertyTable/CommercialProperty/"
       "CommercialPropertyLocationTable/CommercialPropertyLocation")
RULES = "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"
AIRCRAFT = "Aircraft Stored in the Open"


def record(sub):
    return (g6.item(sub)["CommercialPropertySpecialClassBusnIncomeTable"]
            ["CommercialPropertySpecialClassBusnIncome"][0])


def run(state, col="Basic", item=None, rec=None, loc=None):
    sub = g7.submission(col)
    if item:
        g6.item(sub).update(item)
    if rec:
        record(sub).update(rec)
    if loc:
        (sub["CommercialPropertyTable"]["CommercialProperty"][0]
         ["CommercialPropertyLocationTable"]
         ["CommercialPropertyLocation"][0]).update(loc)
    ip = Interpreter(book_for(state, ASOF), rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", sub)
    ip.run(data)
    return data


#: id, item overrides, record overrides, loc overrides,
#: (BI parent-rate, BI Group I, BI Group II, item Group I), why
CASES = [
    ("10  baseline", {}, {}, {}, ("0.07", "39", "123", "66"), "the reference"),

    ("10  parent class -> Aircraft", {"ClassDescription": AIRCRAFT}, {}, {},
     ("0.286", "157", "123", "267"),
     "**the borrow, proven by moving it.** Nothing in the Business Income "
     "record changed; the parent's rate went 0.07 -> 0.286 and the premium "
     "followed $39 -> $157. Group II is untouched because it does its own "
     "lookup on a symbol the class code does not touch"),

    ("10  parent LCM 2.0", {"LossCostMultiplier": "2.0"}, {}, {},
     ("0.14", "77", "123", "130"),
     "**the parent's LCM reaches the child and the parent's deductible does "
     "not** -- because the copy happens after the LCM and before the "
     "deductible. Two fields on the same record, one visible downstream and "
     "one not"),

    ("12  the CHILD's own LCM 5.0", {}, {"LossCostMultiplier": "5.0"}, {},
     ("0.07", "39", "616", "66"),
     "**one field, inert in one form and five-fold in another.** Group I's "
     "rate step is a pure copy and never multiplies by anything, so its own "
     "loss cost multiplier does nothing at all. Group II's rate step is "
     "`base x LCM x the parent's numeric value` and takes the full 5x"),

    ("12  Group II territory, moved", {}, {},
     {"BasicGroupIIRatingTerr": "Portland"},
     ("0.07", "39", "0", "66"),
     "**the borrowed INPUT, moved.** Oregon files Group II rows only for "
     "`Entire State`, so a different territory misses and Group II prices at "
     "zero -- while Group I, which borrows an ANSWER rather than an input, "
     "holds at $39"),
]

#: C7-14: id, record overrides, (Factor, Group I premium), why
FACTOR = [
    ("baseline -- Mercantile", {}, ("0.55", "39"), "the reference"),
    ("TypeOfRisk Manufacturing", {"TypeOfRisk": "Manufacturing"},
     ("0.71", "50"), "the risk-classification key, 29% dearer"),
    ("MaxPeriod Yes", {"MaxPeriod": "Yes"}, ("1.15", "81"),
     "**branch 1 wins by priority** -- and it is a LOAD, not a credit"),
    ("Extra Expense Only", {"CovType": "Extra Expense Only",
                            "ExtraExpenseLimitOnLossPayment": "40%,80%,100%"},
     ("1.7", "119"),
     "**branch 3, and the field it keys on is NOT the one the table column "
     "is named after.** The column is `ExtraExpnLimitOnLossPymts`; the datadef "
     "is `ExtraExpenseLimitOnLossPayment`. Chunk 4 met the same pair of names "
     "and the first draft of this test used the column name, so the factor "
     "came back 0 and the premium with it"),
]


def main() -> int:
    ok = True

    print("=== 10 / 12  The borrow, moved one value at a time\n")
    for name, item, rec, loc, want, _ in CASES:
        data = run("OR", "Basic", item, rec, loc)
        got = (str(read(f"{BI}/BasicGroupIRate", data)),
               str(read(P7["BasicGroupI"], data)),
               str(read(P7["BasicGroupII"], data)),
               str(read(P6["BasicGroupI"], data)))
        good = got == want
        ok &= good
        print(f"  {name:34s} BIrate={got[0]:>6s}  BI {got[1]:>4s}/{got[2]:>4s}"
              f"  item {got[3]:>4s}"
              + ("" if good else f"   <-- expected {want}"))

    # ---- C7-12, the six values enumerated
    print("\n=== 12  Six values cross the boundary, and no base rate among them")
    body = (book_for("OR", ASOF).parent.package.content / "Rules"
            / RULES).read_text(encoding="utf-8-sig")
    borrowed = sorted(set(re.findall(r'FromDataDef="\.\./\.\./(\w+)"', body)))
    # **ELEVEN, not five and not six.** The opening census filtered its
    # pattern to names containing Rate/Symbol/Terr/Factor and reported five;
    # the golden case found a sixth by hand. An UNFILTERED regex finds eleven.
    # **A filtered enumeration is not an enumeration** -- and this one was
    # filtered by a guess about what a borrowed value would be called.
    expect = ["BasicGroupIINumericValue", "BasicGroupIIRatingTerr",
              "BasicGroupIISymbol", "BasicGroupIRate", "ClassCode",
              "EQDeductibleTier", "EQRate", "EQTerr", "LossCostMultiplier",
              "SpecialClassDescConvertedOption", "UnitNumber"]
    good = borrowed == expect
    ok &= good
    print(f"    values read from the Special Class item : {len(borrowed)}")
    for b_ in borrowed:
        print(f"        {b_}")
    print(f"    (expected exactly {expect}) "
          f"{'OK' if good else 'MISMATCH'}")
    n_base = body.count("BasicGroupIBaseRate")
    good = n_base == 0
    ok &= good
    print(f"    mentions of `BasicGroupIBaseRate` anywhere in this ruleset : "
          f"{n_base}  (expected 0) {'OK' if good else 'MISMATCH'}")
    print("    **The opening census said FIVE. The golden case found a sixth")
    print("    by hand. An unfiltered regex finds ELEVEN.** The census matched")
    print("    only names containing Rate/Symbol/Terr/Factor -- a guess about")
    print("    what a borrowed value would be called -- and that guess cost")
    print("    `ClassCode`, `EQDeductibleTier`, `LossCostMultiplier`,")
    print("    `SpecialClassDescConvertedOption` and `UnitNumber`.")
    print("    **A filtered enumeration is not an enumeration.** The one that")
    print("    mattered was `BasicGroupIINumericValue`: it is why removing the")
    print("    parent's ClassDescription reaches TWO child forms, not one.")

    # ---- C7-11
    print("\n=== 11  Earthquake borrows the rate and has nowhere to charge it")
    d = book_for("OR", ASOF).parent.package.content / "Rules"
    plain = d / "CommercialPropertySpecialClassBusnIncomeEarthquakeCoverageRules.Rule.xml"
    variants = sorted(p.name for p in
                      d.glob("CommercialPropertySpecialClassBusnIncome*Earthquake*.xml"))
    data = run("OR")
    eq_rate = read(f"{BI}/EQRate", data)
    good = not plain.exists() and len(variants) == 2
    ok &= good
    print(f"    plain Earthquake coverage file exists : {plain.exists()}  "
          f"(expected False)")
    print(f"    Earthquake premium files that DO exist : {len(variants)}")
    for v in variants:
        print(f"        {v}")
    print(f"    EQRate on a Basic submission : {eq_rate}   "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **A rate chain with nowhere to send its answer, for the second")
    print("    time.** Chunk 5 found the same asymmetry on plain Business")
    print("    Income; two instances make it a pattern rather than a quirk --")
    print("    Earthquake charges through Agreed Value and Extended Period of")
    print("    Indemnity, and through nothing else.")

    # ---- C7-13
    print("\n=== 13  The parent's failures, re-asserted")
    for j, want in (("FL", "0"), ("NY", "0"), ("AZ", "0"), ("OR", "39")):
        got = str(read(P7["BasicGroupI"], run(j)))
        good = got == want
        ok &= good
        print(f"    {j}: Business Income Group I = {got:>3s}  "
              f"(expected {want}) {'OK' if good else 'MISMATCH'}")
    print("    Settled inside the sweep and repeated here because it is the")
    print("    chunk's defining consequence: **three jurisdictions where a")
    print("    perfectly well-formed Business Income record prices at zero**,")
    print("    for three reasons that all belong to a different coverage.")

    # ---- C7-14
    print("\n=== 14  The shared Factor -- read by two forms, ignored by three")
    for name, rec, want, _ in FACTOR:
        data = run("OR", "Basic", rec=rec)
        got = (str(read(f"{BI}/Factor", data)),
               str(read(P7["BasicGroupI"], data)))
        good = got == want
        ok &= good
        print(f"    {name:30s} Factor={got[0]:>5s}  Group I={got[1]:>4s}"
              + ("" if good else f"   <-- expected {want}"))
    for col, want in (("Broad", "23"), ("Special", "47")):
        data = run("OR", col, rec={"MaxPeriod": "Yes"})
        fac = str(read(f"{BI}/Factor", data))
        got = str(read(P7[col], data))
        good = got == want and fac == "1.15"
        ok &= good
        print(f"    {col:8s} with MaxPeriod elected: Factor={fac}, premium="
              f"{got}  (expected {want}, unchanged) "
              f"{'OK' if good else 'MISMATCH'}")
    res = CFEditionResolver()
    own = [j for j in sorted(res.jurisdictions)
           if book_for(j, ASOF, resolver=res).declares("BusnIncomeFactor")
           == "state"]
    good = own == ["FL"]
    ok &= good
    print(f"    jurisdictions filing their own BusnIncomeFactor : {own}  "
          f"(expected ['FL']) {'OK' if good else 'MISMATCH'}")
    print("    **The Factor is computed for every form and read by two.**")
    print("    Electing max-period more than doubles Basic Group I and leaves")
    print("    Broad and Special exactly where they were -- the same shape")
    print("    chunk 5 proved on plain Business Income, now on a second group.")

    print("\nWhat each case proves")
    for name, _, _, _, _, why in CASES[1:]:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
