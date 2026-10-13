#!/usr/bin/env python3
"""Chunk 4, tasks C4-21 to C4-23 -- Contents Broad, the shortest chain built.

Personal Property's Broad chain is **5 steps**, against Building's 6 and Basic
Group I's 9. What it leaves out is the point of all three tasks.

  21  **There is no `SetDeductibleFactorBroad` rule in the PP ruleset at all.**
      `SetFinalBroadRate` reads `../../../../DeductibleFactorBroad` directly --
      four levels up, no local `Copy`, no `Lookup`. What happens when that
      ancestor is absent?
  22  **No roof-surfacing ACV factor anywhere in Personal Property.** Building
      folds one into its adjusted-rate step. Enumerate the absence rather than
      asserting a silence.
  23  **PersProp base rates are 0.021 / 0.011**, against Building's 0.015 /
      0.010 -- the same shared table, different rows. A case on each tier.

Derived by hand from Oregon's filed rows before the run, on chunk 4's golden
case (one Contents item at 100,000, LOI 0.790, coinsurance 0.95, the
structure's deductible factor 0.98 at a 200,000 location total):

    Frame           base 0.021 -> adjusted 0.016 -> final 0.016 -> $16
    Fire Resistive  base 0.011 -> adjusted 0.008 -> final 0.008 -> $8

**The fire-resistive tier is a rounding probe.** Rounding once across the
adjusted-rate step gives `r3(0.790 x 0.011 x 0.95)` = 0.008; rounding after
every factor gives 0.009 and a $9 premium. Basic Group I was found to round
once (chunk 4's golden case), so 0.008 is the prediction -- and a $9 would say
the two PP chains do not share a rounding shape either.

    python scripts/cf/29_chunk4_broad.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
chunk4 = import_module("22_chunk4_golden_case")
zeros4 = import_module("25_chunk4_zero_cases")

PP = chunk4.PP
PREM = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBroadCoverage/Premium"
BLDG_BROAD = (chunk2.STRUCT +
              "/CommercialPropertyStructureBuildingBroadCoverage/Premium")

FR = "Fire Resistive - Reinforced Masonry - Light Steel"

#: id, mutation, (base, adjusted, STRUCTURE's deductible factor,
#: Contents premium), why. The Contents record's own `DeductibleFactorBroad` is
#: asserted separately, and it is always absent -- see C4-21 below.
CASES = [
    ("baseline  Frame", lambda s: None,
     ("0.021", "0.016", "0.98", "16"),
     "the reference. Contents Broad is 0.021 where Building's is 0.015 -- the "
     "same shared `BroadFormBaseRate` table, a different `CovType` row"),

    ("23  Fire Resistive -- the second tier",
     lambda s: zeros4.struct_of(s).__setitem__("ConstructionType", FR),
     ("0.011", "0.008", "0.98", "8"),
     "**the other tier, and a rounding probe.** 0.011 against 0.021, and the "
     "adjusted rate lands on 0.008 only if the step rounds ONCE. Rounding "
     "after every factor gives 0.009 and a $9 premium"),

    ("21  structure Deductible removed",
     lambda s: zeros4.struct_of(s).pop("Deductible", None),
     ("0.021", "0.016", "0", "0"),
     "**the ancestor cannot be null, and that is why the missing rule is "
     "safe.** Building's own `SetDeductibleFactorBroad` ends in an `Otherwise` "
     "worth 0.0, so a blank deductible gives Contents a ZERO rather than a "
     "null -- the premium collapses silently instead of being refused. The "
     "design depends on a guarantee that lives in a different datadef group. "
     "And note what the value column shows: the Contents record has NO "
     "`DeductibleFactorBroad` of its own in any case. The ancestor is read in "
     "place, so the figure above is the STRUCTURE's"),

    ("21  ITEM Deductible changed to 25,000",
     lambda s: zeros4.item_of(s).__setitem__("Deductible", "25,000"),
     ("0.021", "0.016", "0.98", "16"),
     "**the Contents deductible does not affect the Contents premium.** The "
     "factor is copied from the structure, so only the BUILDING's deductible "
     "reaches Broad. A submission that prices contents with their own "
     "deductible is accepted and ignored -- the seventh inherited field in "
     "this chunk"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk4.submission("Broad")
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:42s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{PP}/BroadBaseRate", data),
               read(f"{PP}/AdjustedBroadRate", data),
               read(f"{chunk2.STRUCT}/DeductibleFactorBroad", data),
               read(PREM, data))
        # **The factor never materialises on the Contents record.** There is no
        # rule to write it -- `SetFinalBroadRate` reads the ancestor in place.
        # So a trace of a Contents Broad premium cannot show the deductible
        # factor at all; it can only be inferred from the arithmetic.
        local = read(f"{PP}/DeductibleFactorBroad", data)
        ok &= local is None
        if local is not None:
            print(f"    <-- the item now HAS a DeductibleFactorBroad ({local}); "
                  f"a local rule has appeared")
        good = got == expect
        ok &= good
        print(f"{name:42s} base={str(got[0]):>6s} adj={str(got[1]):>6s} "
              f"ded={str(got[2]):>5s} contents={str(got[3]):>3s}  "
              f"building={read(BLDG_BROAD, data)}"
              + ("" if good else f"   <-- expected {expect}"))

    # ---- C4-22, enumerated rather than asserted
    print("\n=== 22  No roof-surfacing ACV factor anywhere in Personal Property")
    res = CFEditionResolver()
    found = []
    for j in ["CW"] + list(res.jurisdictions):
        b = book if j == "CW" else book_for(j, chunk2.ASOF, resolver=res)
        pkg = b.parent.package if j == "CW" else b.state.package
        f = pkg.content / "Rules" / "CommercialPropertyPersonalPropertyRules.Rule.xml"
        if f.exists() and "LimitationsOnCovForRoofSurfacing" in \
                f.read_text(encoding="utf-8-sig"):
            found.append(j)
    n = len(res.jurisdictions)
    good = not found
    ok &= good
    print(f"    jurisdictions whose PP ruleset mentions the roof-surfacing "
          f"factor (of {n} + CW): {len(found)}  "
          f"(expected 0) {'OK' if good else 'MISMATCH ' + str(found)}")
    print("    Building folds the factor into its adjusted-rate step and chunk")
    print("    3 proved it inert there anyway -- 0 of 6 filed Building base")
    print("    rates survive the 3dp rounding. Here it is absent outright, and")
    print("    contents have no roof, so nothing substitutes for it.")

    print("\nWhat each case proves")
    for name, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match, and the absence is enumerated.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
