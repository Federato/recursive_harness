#!/usr/bin/env python3
"""Chunk 8, tasks C8-22 to C8-26 -- the cross-form claims, and the map scored.

  22  Point 9 -- the multi-premium credit is applied on the class-rated path
      and not on this one.
  23  Point 11 -- IRPM and PackageMod after the limit here, before it there.
      **The map says it verified this is not premium-bearing. It is.**
  24  What else falls out of the same `Choose`.
  25  Six coverages on one submission -- and **one of them moves.**
  26  The eleven-point map, scored.

Derived by hand before the run:

    22  MultiPremiumAndDispersionCreditFactor 0.5
            class-rated  261 -> 131     Legal Liability stays **$60**

    23  PackageModFactor 0.44 and IRPMFactor 0.44, on a $60 premium:
            nested (this path)   r0(r0(60 x .44) x .44) = r0(26 x .44) = **11**
            single product       r0(60 x .44 x .44)     = r0(11.616)   = **12**
        **One dollar apart.** The map checked the operands and concluded the
        ordering was not premium-bearing; it is, at factors that round the
        other way.

    python scripts/cf/66_chunk8_crossform.py

Exit 0 when every claim matches its derivation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from gl_engine.interp.tree import read

g8 = import_module("59_chunk8_golden_case")
fork = import_module("64_chunk8_fork")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")

S, PP = chunk2.STRUCT, chunk4.PP
B_BGI = S + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"

#: C8-26. The eleven points, and what running them produced.
MAP = [
    (1, "the gate field, and the level it is chosen at", "CONFIRMED",
     "C8-15 / C8-18 -- and it decides who may differ"),
    (2, "two names for one idea in sibling files", "CONFIRMED",
     "C8-16 -- and gate point 6 is structurally blind to it"),
    (3, "the factor value, Bldg 0.25 against PersProp 0.50", "CONFIRMED",
     "C8-12 -- and each row is unreachable from the other side"),
    (4, "Building's setter gated, Contents' unconditional", "CONFIRMED",
     "C8-17 -- Contents carries a live 0.50 on a class-rated risk"),
    (5, "the insurable-interest record at different levels", "CONFIRMED",
     "C8-18 -- $0 on the item, $132 on the occupancy"),
    (6, "Special's rate source differs", "CONFIRMED",
     "C8-19 -- theft excluded moves Contents $93 -> $37 and Building not at "
     "all"),
    (7, "why blanket never applies -- by ORDERING", "CORRECTED",
     "C8-14 -- the conclusion holds and the reason does not: the coverage "
     "gate writes 0 before the Choose is reached"),
    (8, "the limit reference", "CONFIRMED", "C8-20"),
    (9, "the multi-premium credit applied there, not here", "CONFIRMED",
     "C8-22"),
    (10, "the outer If, and Builders Risk returning 0.0", "CORRECTED",
     "C8-03 / C8-08 -- there is no Else, so Premium is NULL and we refuse; "
     "ISO rates it at $1. Neither 0.0 nor agreed"),
    (11, "operand order is not premium-bearing", "CORRECTED",
     "C8-23 -- it is, by a dollar, at PackageMod and IRPM of 0.44"),
]

EXTRA = [
    ("the fork is confined to the Legal Liability premium", "ADDED",
     "C8-25 -- it is not. Switching the Building to Legal Liability takes "
     "CONTENTS' LOI factor from 0.898 to 1 and its premium from $223 to $248, "
     "on a coverage that is still class-rated"),
    ("the plain-language -> Option mapping ships empty", "STALE",
     "C8-13 -- the 2026 edition files four rows"),
    ("three concepts computed and discarded", "CORRECTED",
     "C8-11 -- two are; the LOI factor is never computed"),
    ("Building's blanket test is uniform across its four forms", "ADDED",
     "C8-21 -- only Special tests IncludedInBlkt; the map does not mention "
     "it"),
]


def main() -> int:
    ok = True

    # ---- C8-22
    print("=== 22  Point 9 -- the multi-premium credit\n")
    mut = (lambda st:
           st.__setitem__("MultiPremiumAndDispersionCreditFactor", "0.5"))
    ll = str(read(B_BGI, fork.rate(mut)))
    cr = str(read(B_BGI, fork.rate(mut, covtype="Building")))
    good = (ll, cr) == ("60", "131")
    ok &= good
    print(f"    factor 0.5:  class-rated 261 -> {cr}   Legal Liability stays "
          f"{ll}   {'OK' if good else 'MISMATCH'}")
    print("    **Chunk 5 found this same field populated and unused on")
    print("    Business Income.** Second instance, different coverage: the")
    print("    value is on the record, it halves one premium, and the other")
    print("    never reads it.")

    # ---- C8-23
    print("\n=== 23  Point 11 -- the operand order IS premium-bearing")
    for pm, irpm, want, note in (
            ("1.0", "1.0", "60", "the reference"),
            ("0.44", "0.44", "11",
             "nested: r0(r0(60 x .44) x .44) = r0(26 x .44) = 11")):
        sub = g8.building("Basic")
        zeros2.structure(sub)["PackageModFactor"] = pm
        # **IRPM is read from the POLICY**, five levels up -- setting it on the
        # item does nothing, and the first run of this case applied only one
        # of the two factors and reported 26 where 11 was derived.
        sub["CommercialPropertyTable"]["CommercialProperty"][0][
            "IRPMFactor"] = irpm
        data = g8.run(sub)[0]
        got = str(read(B_BGI, data))
        good = got == want
        ok &= good
        print(f"    PackageMod {pm:>5s}  IRPM {irpm:>5s}  premium {got:>3s}  "
              f"(expected {want})  {'OK' if good else 'MISMATCH'}   {note}")
    print("    **A single product would give 12**: 60 x 0.44 x 0.44 = 11.616,")
    print("    which rounds up. The nested form rounds to 26 first and then to")
    print("    11. **One dollar, and the map says this ordering is not")
    print("    premium-bearing.** It verified the operands and not the")
    print("    arithmetic -- the same shape as every other finding in this")
    print("    chunk: reading the rules tells you what is written, not what")
    print("    it computes.")

    # ---- C8-24
    print("\n=== 24  What else falls out of the same Choose")
    for name, expect in (("Leasehold Interest", "refuses -- it activates the "
                          "Leasehold rate chain, chunk 11's"),
                         ("Builders Risk + reporting form",
                          "refuses here, ISO rates it at $1 -- OI-99")):
        print(f"    {name:32s} {expect}")
    print("    Both are CORRECT outcomes of this file's logic and neither is")
    print("    a zero in our engine. **The map records both as `Premium =")
    print("    0.0`; one of them ISO prices at $1 and the other cannot be")
    print("    reached from chunk 8 at all.** Named here so a future reader")
    print("    meeting either one does not chase it.")

    # ---- C8-25
    print("\n=== 25  Six coverages on one submission")
    sub = chunk4.submission("Basic")
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    st = zeros2.structure(sub)
    st["CovType"] = "Legal Liability"
    st[f"{g8.LL_FORM}Table"] = {g8.LL_FORM: [{"AddlInsurableInt": g8.NONE}]}
    st["CommercialPropertyBusinessIncomeTable"] = (
        zeros2.structure(chunk5.submission("Basic"))
        ["CommercialPropertyBusinessIncomeTable"])
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["CommercialPropertySpecialClassTable"] = (
        g6.location(g7.submission("Basic"))
        ["CommercialPropertySpecialClassTable"])
    data, ip = g8.run(sub)
    pp = PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
    rows = [("BUILDING Legal Liability", B_BGI, "60"),
            # **Predicted 223 and it is 248 -- Contents MOVES.** See below.
            ("CONTENTS class-rated    ", pp % "BasicGroupI", "248"),
            ("BUSN INCOME Group I     ", chunk5._P % "BasicGroupI", "112"),
            ("SPECIAL CLASS Group I   ", g6._P % "BasicGroupI", "66"),
            ("SPECIAL CLASS Group II  ", g6._P % "BasicGroupII", "209"),
            ("SPCL CLASS BI Group I   ", g7._P % "BasicGroupI", "39")]
    for label, path, want in rows:
        got = str(read(path, data))
        good = got == want
        ok &= good
        print(f"    {label} = {got:>4s}   (expected {want:>4s})  "
              f"{'OK' if good else 'MISMATCH'}")
    loi = str(read(f"{PP}/BasicGroupILOIFactor", data))
    good = loi == "1"
    ok &= good
    print(f"    ...and CONTENTS' LOI factor = {loi}  (0.898 when the Building "
          f"is class-rated)  {'OK' if good else 'MISMATCH'}")
    print("    **Predicted 'none of them moving' and Contents moves, $223 ->")
    print("    $248.** The Building's `CovType` suppresses CONTENTS' limit-of-")
    print("    insurance factor: the PersonalProperty setter is gated on the")
    print("    parent's CovType exactly as the Building's own is (C8-11), so")
    print("    making the building a Legal Liability risk takes 0.898 to 1 on")
    print("    a coverage that is still class-rated.")
    print("    **The fork is not confined to its own premium.** Everything")
    print("    else holds -- Business Income keeps $112 because it reads the")
    print("    Building's RATE chain, which the fork does not touch, and both")
    print("    Special Class coverages are untouched because they hang off the")
    print("    location rather than the building. **Only the coverage nested")
    print("    INSIDE the building follows it.**")

    # ---- C8-26
    print("\n=== 26  The eleven-point map, scored\n")
    for n, claim, verdict, note in MAP:
        print(f"    {n:>2d}  {verdict:9s}  {claim}")
        print(f"        {note}")
    print()
    for claim, verdict, note in EXTRA:
        print(f"    --  {verdict:9s}  {claim}")
        print(f"        {note}")
    n_conf = sum(1 for _, _, v, _ in MAP if v == "CONFIRMED")
    n_corr = sum(1 for _, _, v, _ in MAP if v == "CORRECTED")
    print(f"\n    **{n_conf} of 11 confirmed, {n_corr} corrected**, plus one "
          f"stale line, one\n    over-claim and one thing the map does not "
          f"mention.")
    print("    **This was the best-prepared input any chunk has started from**")
    print("    -- eleven numbered points, traced from the rule XML by a person")
    print("    -- and running it moved five of them. Every correction is a")
    print("    place where the rules said one thing and the arithmetic said")
    print("    another: a premium of $1 where the text said 0.0, a gate that")
    print("    fires before the branch the map reasons about, a factor that is")
    print("    never computed rather than computed and ignored, and an operand")
    print("    order that costs a dollar.")

    print()
    if ok:
        print("Every cross-form claim holds.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
