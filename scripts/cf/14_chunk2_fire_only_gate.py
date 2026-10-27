#!/usr/bin/env python3
"""Chunk 2, task 6 -- the fire-only gate, across all eight SPP options.

A Standard Property Policy offers eight cause-of-loss forms, and Group II's
`SetBasicGroupIICauseOfLossAdjustment` opens with a gate that forces the
adjustment to `0.0` on four of them: a fire-only cause of loss buys no Group II
perils, so there is no Group II premium however good the rate underneath is.

The four it names are the four **without "Allied Lines"**. The algorithms doc
reasons that the other four fall through because Allied Lines includes
windstorm and hail under ISO's standard definition -- which is exactly what
Group II is. This exercises all eight rather than trusting that reasoning.

**Two independent dimensions, each hitting a different coverage group**, which
is the part worth having on record:

    Allied Lines in the name  ->  decides GROUP II  (0 without, priced with)
    Vandalism in the name     ->  decides GROUP I   (VandalismExclFactor)

`VandalismExclFactor` fires automatically on an SPP form that does NOT cover
vandalism -- 0.95 for class 0951 -- and is 1.0 on the forms that do. So the
eight options form a clean 2x2, and neither dimension touches the other's
group.

    python scripts/cf/14_chunk2_fire_only_gate.py

Exit 0 when all eight match.
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
zeros = import_module("10_chunk2_zero_cases")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII

#: All eight, from ISO's own domain table
#: (`DomainCauseOfLossByPolicyOptionalForms`, PolicyType = Standard Property
#: Policy). Enumerated from the corpus, not typed from the manual.
#:
#: option, expected (Group II coladj, Group II premium, vandalism factor,
#: Group I premium)
OPTIONS = [
    ("Fire", ("0", "0", "0.95", "242")),
    ("Fire and Sprinkler Leakage", ("0", "0", "0.95", "242")),
    ("Fire and Vandalism", ("0", "0", "1", "255")),
    ("Fire, Vandalism and Sprinkler Leakage", ("0", "0", "1", "255")),
    ("Fire and Allied Lines", ("0.026", "31", "0.95", "242")),
    ("Fire, Sprinkler Leakage and Allied Lines", ("0.026", "31", "0.95", "242")),
    ("Fire, Vandalism and Allied Lines", ("0.026", "31", "1", "255")),
    ("Fire, Vandalism, Sprinkler Leakage and Allied Lines",
     ("0.026", "31", "1", "255")),
]

#: The four the gate names, verbatim from `SetBasicGroupIICauseOfLossAdjustment`.
GATED = {"Fire", "Fire and Vandalism", "Fire and Sprinkler Leakage",
         "Fire, Vandalism and Sprinkler Leakage"}


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    print("A Standard Property Policy. Group II is $32 on a Commercial "
          "Property Policy;\nunder an SPP it is $31, because "
          "StdPropPolGroupIIFactor (0.98) applies.\n")
    print(f"{'cause of loss':52s} {'AL':>3s} {'coladj':>7s} {'GII':>4s} "
          f"{'vand':>5s} {'GI':>4s}")
    ok = True
    for option, expect in OPTIONS:
        sub = chunk2.submission()
        zeros.structure(sub).update(CauseOfLoss=option,
                                    PolicyType="Standard Property Policy")
        sub["CommercialPropertyTable"]["CommercialProperty"][0][
            "PolicyType"] = "Standard Property Policy"
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{option:52s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/BasicGroupIICauseOfLossAdjustment", data),
               read(BGII, data),
               read(f"{STRUCT}/VandalismExclFactor", data),
               read(BGI, data))
        good = got == expect
        ok &= good
        allied = "yes" if "Allied Lines" in option else "no"
        print(f"{option:52s} {allied:>3s} {got[0]:>7s} {got[1]:>4s} "
              f"{got[2]:>5s} {got[3]:>4s}"
              + ("" if good else f"   MISMATCH expected {expect}"))

    # The gate's own list must be exactly the options without Allied Lines --
    # asserted rather than eyeballed, because it is the whole claim.
    no_allied = {o for o, _ in OPTIONS if "Allied Lines" not in o}
    zeroed = {o for o, e in OPTIONS if e[1] == "0"}
    ok &= (no_allied == GATED == zeroed)
    print(f"\n  the 4 options the rule names  == the 4 without Allied Lines "
          f"== the 4 that price Group II at zero: "
          f"{no_allied == GATED == zeroed}")

    print("\n  Two independent dimensions, each hitting a different group:")
    print("     'Allied Lines' in the name -> Group II priced or zero")
    print("     'Vandalism'    in the name -> Group I's VandalismExclFactor")
    print("  Neither touches the other's group, so the eight options are a "
          "clean 2x2.")
    print()
    if ok:
        print(f"All {len(OPTIONS)} options match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
