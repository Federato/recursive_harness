#!/usr/bin/env python3
"""Chunk 7, tasks C7-15 to C7-21 -- the per-form specifics.

  15  **One multiplier, not four.** Basic Group I's whole cause-of-loss
      adjustment is `rate x VandalismExclFactor`.
  16  **Basic Group II looks its own base rate up**, on tables that are
      header-only countrywide.
  17  The lowest-rate biconditional -- settled inside the sweep, re-asserted.
  18  **Broad is construction-blind and covType-live**, in the same lookup.
  19  **Special's apartment key is pinned here and live in plain Business
      Income**, on the same physical table.
  20  **BOTH dimensions are dead, not one -- the algorithms page is wrong.**
  21  **No Builders Risk branch**, and a filed table with no consumer.

All figures derived by hand before the run. Baseline: Basic Group I **$39**,
Basic Group II **$123**, Broad **$23**, Special **$47**.

    15  vandalism excluded, parent ClassCode 0951 -> factor 0.95
            r3(0.07 x 0.95) = 0.067 -> r3(0.067 x 0.55) = 0.037    $37

    18  parent construction Fire Resistive   -> still 0.023         $23
        CovType Without Extra Expense        -> 0.011               $11
        **construction is pinned and covType is not, in ONE lookup**

    19  parent ClassCode 0311 (apartments)   -> still 0.047         $47
        plain Business Income, same class     -> 0.029              $29

    20  theft excluded                        -> factor 0.86
            r3(0.047 x 0.86) = 0.04                                 $40
        ...and 0.86 whatever ApartmentCondoIndicator says

    python scripts/cf/55_chunk7_perform.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.tree import read

borrow = import_module("54_chunk7_borrowed")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")

SC, BI, ASOF = g7.SC, g7.BI, g7.ASOF
P7 = borrow.P7
FR = "Fire Resistive - Reinforced Masonry - Light Steel"
VANDALISM = "CommercialPropertyVandalismExclusionSpclClassBusnIncome"
THEFT = "CommercialPropertyTheftExclusionSpclClassBusnIncome"
RULES = "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"
PLAIN = "CommercialPropertyBusinessIncomeRules.Rule.xml"
PARENT = "CommercialPropertySpecialClassRules.Rule.xml"


def with_record(sub, name):
    rec = borrow.record(sub)
    rec[f"{name}Table"] = {name: [{}]}
    return sub


def run_rec(col, name=None, item=None, rec=None):
    """Like `borrow.run`, with an optional endorsement record attached."""
    sub = g7.submission(col)
    if item:
        g6.item(sub).update(item)
    if rec:
        borrow.record(sub).update(rec)
    if name:
        with_record(sub, name)
    from cf_engine.config import NULL_ARITHMETIC, ROUNDING
    from gl_engine.interp.interpreter import Interpreter
    from gl_engine.interp.tree import Node
    ip = Interpreter(book_for("OR", ASOF), rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict("MasterCFOR", sub)
    ip.run(data)
    return data


def main() -> int:
    ok = True
    book = book_for("OR", ASOF)
    d = book.parent.package.content / "Rules"
    mine = (d / RULES).read_text(encoding="utf-8-sig")
    plain = (d / PLAIN).read_text(encoding="utf-8-sig")
    parent = (d / PARENT).read_text(encoding="utf-8-sig")

    # ---- C7-15
    print("=== 15  One multiplier, not four\n")
    cases15 = [
        ("baseline", None, {}, ("1", "0.07", "39")),
        ("vandalism excluded, class 0951", VANDALISM, {"ClassCode": "0951"},
         ("0.95", "0.067", "37")),
        ("vandalism excluded, class 0311", VANDALISM, {"ClassCode": "0311"},
         ("0.98", "0.069", "38")),
    ]
    for name, rec_name, item, want in cases15:
        data = run_rec("Basic", rec_name, item=item)
        got = (str(read(f"{BI}/VandalismExclFactor", data)),
               str(read(f"{BI}/BasicGroupICauseOfLossAdjustment", data)),
               str(read(P7["BasicGroupI"], data)))
        good = got == want
        ok &= good
        print(f"  {name:34s} factor={got[0]:>5s} COLadj={got[1]:>6s} "
              f"premium={got[2]:>3s}"
              + ("" if good else f"   <-- expected {want}"))
    print()
    print(f"  {'term':26s} {'here':>5s} {'plain BI':>9s} {'SC Bldg':>8s}")
    for term in ("StdPropPolGroupIFactor", "BuildersRiskFactor",
                 "SprinklerLeakage"):
        here, bi, sc = (mine.count(term), plain.count(term),
                        parent.count(term))
        good = here == 0
        ok &= good
        print(f"  {term:26s} {here:>5d} {bi:>9d} {sc:>8d}   "
              f"{'OK' if good else 'MISMATCH'}")
    print("  **Each absence has a DIFFERENT contrast, and the census only")
    print("  drew one of them.** `StdPropPolGroupIFactor` is absent from")
    print("  plain Business Income too -- it is Special Class BUILDING that")
    print("  applies it 5 times. `BuildersRiskFactor` and sprinkler leakage")
    print("  are the opposite: plain Business Income names them 10 and 86")
    print("  times and neither Special Class group has the concept at all.")
    print("  **The vandalism factor keys on the PARENT's ClassCode** -- one of")
    print("  the eleven borrowed values C7-12 enumerated -- so an exclusion")
    print("  elected on the Business Income record is priced from a field on")
    print("  a record two levels up. 0951 gives 0.95 and 0311 gives 0.98.")

    # ---- C7-16
    print("\n=== 16  Group II looks its own base rate up, on empty CW tables")
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    for t, want_n in (("BasicGroupIIRate", 45), ("LowestBasicGroupIIRate", 39)):
        cw = len(book.parent_table(t).rows)
        own = [j for j in juris
               if book_for(j, ASOF, resolver=res).declares(t) == "state"]
        good = cw == 0 and len(own) == want_n
        ok &= good
        print(f"    {t:26s} CW rows={cw}   states filing={len(own)} "
              f"(expected 0 / {want_n}) {'OK' if good else 'MISMATCH'}")
    print("    **Unresolvable at countrywide for the third coverage group")
    print("    running** -- Building, plain Business Income and this one all")
    print("    read the same two empty tables, and all three depend entirely")
    print("    on a state filing.")

    # ---- C7-17
    print("\n=== 17  The lowest-rate biconditional -- settled in the sweep")
    print("    Six states DELETE the rule (AR, DC, KS, NY, RI, TX) and they")
    print("    are six of the eight filing no table. **FL and PR go a third")
    print("    way**: they leave the rule alone and file no table, so they")
    print("    reach a read with nothing to read. Chunk 6's biconditional")
    print("    does NOT hold here -- see 52_chunk7_enumerate_states.py.")

    # ---- C7-18
    print("\n=== 18  Broad -- construction pinned, covType live, one lookup")
    cases18 = [
        ("baseline -- Frame, With EE", {}, {}, ("0.023", "23")),
        ("parent construction Fire Resistive", {"ConstructionType": FR}, {},
         ("0.023", "23")),
        ("CovType Without Extra Expense", {},
         {"CovType": "Business Income Without Extra Expense"},
         ("0.011", "11")),
    ]
    for name, item, rec, want in cases18:
        data = run_rec("Broad", item=item, rec=rec)
        got = (str(read(f"{BI}/BroadBaseRate", data)),
               str(read(P7["Broad"], data)))
        good = got == want
        ok &= good
        print(f"  {name:36s} base={got[0]:>6s} premium={got[1]:>3s}"
              + ("" if good else f"   <-- expected {want}"))
    print("  **Both keys are in the SAME lookup and only one of them is a")
    print("  literal.** Construction is pinned to \"Frame\", so the table's two")
    print("  Fire Resistive rows at 0.012 are unreachable here -- while plain")
    print("  Business Income reads them and prices the same risk at $12.")

    # ---- C7-19 and C7-20
    print("\n=== 19 / 20  Special -- and BOTH dimensions are dead")
    cases19 = [
        ("baseline", None, {}, {}, ("1", "0.047", "47")),
        ("parent ClassCode 0311 (apartments)", None, {"ClassCode": "0311"},
         {}, ("1", "0.047", "47")),
        ("ApartmentCondoIndicator Yes on the record", None, {},
         {"ApartmentCondoIndicator": "Yes"}, ("1", "0.047", "47")),
        ("theft excluded", THEFT, {}, {}, ("0.86", "0.04", "40")),
        ("theft excluded + apartments", THEFT, {"ClassCode": "0311"},
         {"ApartmentCondoIndicator": "Yes"}, ("0.86", "0.04", "40")),
    ]
    for name, rec_name, item, rec, want in cases19:
        data = run_rec("Special", rec_name, item=item, rec=rec)
        got = (str(read(f"{BI}/SpecialTheftExclusionFactor", data)),
               str(read(f"{BI}/SpecialCauseOfLossAdjustment", data)),
               str(read(P7["Special"], data)))
        good = got == want
        ok &= good
        print(f"  {name:42s} theft={got[0]:>5s} COLadj={got[1]:>6s} "
              f"premium={got[2]:>3s}"
              + ("" if good else f"   <-- expected {want}"))
    print("  **The algorithms page says the theft factor still varies by")
    print("  `ApartmentCondoIndicator` while the base rate cannot. It does")
    print("  not.** `SpecialLeaseHoldTimeElementTheftExclusionFactor` files")
    print("  two rows -- Yes 0.96, No 0.86 -- and the lookup is pinned to")
    print("  \"No\" from every site that reads it. **Both dimensions are dead,")
    print("  and the 0.96 row is unreachable from this coverage entirely.**")
    print("  The table's `Apartments and Condominiums` base rows (0.029 and")
    print("  0.016) are unreachable too -- while plain Business Income reads")
    print("  them, on the same physical table, and prices the apartments")
    print("  version of this risk at $29.")

    # ---- C7-21
    print("\n=== 21  No Builders Risk branch, and a filed table with no consumer")
    a, b_ = (mine.count("SpecialFormBldrsRiskTimeElementBaseRate"),
             plain.count("SpecialFormBldrsRiskTimeElementBaseRate"))
    good = a == 0 and b_ > 0
    ok &= good
    print(f"    named in this ruleset          : {a}   (expected 0)")
    print(f"    named in plain Business Income : {b_}   (expected > 0)  "
          f"{'OK' if good else 'MISMATCH'}")
    rows = len(book.table("SpecialFormBldrsRiskTimeElementBaseRate").rows)
    own = [j for j in juris
           if book_for(j, ASOF, resolver=res).declares(
               "SpecialFormBldrsRiskTimeElementBaseRate") == "state"]
    print(f"    the table itself: {rows} countrywide row(s), {len(own)} "
          f"states filing their own")
    data = run_rec("Special", item={"ClassCode": "1150"})
    got = str(read(P7["Special"], data))
    good = got == "47"
    ok &= good
    print(f"    parent ClassCode 1150 -> premium {got}  (expected 47, "
          f"unchanged) {'OK' if good else 'MISMATCH'}")
    print("    **Class 1150 is plain Business Income's Builders Risk trigger")
    print("    and it does nothing here** -- the third coverage group in two")
    print("    chunks where that code is inert. A countrywide row is filed,")
    print("    no state files its own, and this group never names it.")

    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
