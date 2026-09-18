#!/usr/bin/env python3
"""Gate point 4 -- every `0` tested against the branch that consumes it.

The Property gate asks for this because Property's zeros mean at least three
different things, and the engine must not blur them: a genuine factor, a "no
credit" rate, and a zero that collapses the premium. The three golden cases set
every optional term to its no-op and so exercise none of them.

Each case below moves ONE input and asserts the whole chain, not just the
premium -- because the interesting part is usually *where* the zero appears.
`Z3` and `Z4` produce the same premium as each other and as `Z1` and `Z2`, and
they are four different mechanisms; only the chain tells them apart.

    python scripts/cf/02_zero_cases.py

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

golden = import_module("01_golden_case")

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
PREMIUM = (STRUCT +
           "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium")


def structure(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]
            ["CommercialPropertyStructure"][0])


def policy(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


#: (id, mutation, expected base / LOI / final / premium, what it proves)
CASES = [
    ("baseline", lambda s: None,
     ("0.498", "1.172", "0.261", "261"),
     "the reference the others are read against"),

    ("Z1  Limit = 0", lambda s: structure(s).update(Limit="0", FullBldgValue="0"),
     ("0.498", "0", "0", "0"),
     "`SetBasicGroupILOIFactor` assigns 0.0 outright when the limit is zero. "
     "The base rate still resolves -- the zero enters at step 4, not step 1, "
     "and it is ISO's own gate rather than a missing lookup"),

    ("Z2  unknown ConstructionType",
     lambda s: structure(s).update(ConstructionType="Nonesuch"),
     ("0", "0", "0", "0"),
     "an unrecognised construction TYPE resolves to construction CODE 0, "
     "which fails both the base-rate gate and the LOI gate. **It does not "
     "raise** -- a typo'd construction type prices at zero, silently"),

    ("Z3  blank ClassCode", lambda s: structure(s).update(ClassCode=""),
     ("0", "1.172", "0", "0"),
     "the base-rate gate needs a non-blank class code. Distinguishable from "
     "Z2 only by the LOI factor, which still resolves here"),

    ("Z4  blank CauseOfLoss", lambda s: structure(s).update(CauseOfLoss=""),
     ("0.498", "1.172", "0.261", "0"),
     "**the whole rate chain computes correctly and the premium is still "
     "zero.** `SetCoverageOnPolicyIndicator` gates on `CauseOfLossToUse`, and "
     "a final rate of 0.261 sitting next to a premium of 0 is exactly the "
     "shape a silent defect would take. It is ISO's rule, not a defect -- but "
     "nothing except this test says so"),

    ("Z5  cyber exclusion elected",
     lambda s: policy(s).update(CommercialPropertyCyberIncidentExclusionTable={
         "CommercialPropertyCyberIncidentExclusion": [{}]}),
     ("0.498", "1.172", "0.261", "260"),
     "the opposite test: proves the cyber factor is LIVE rather than "
     "defaulting. 261 x 0.995 = 259.695 -> 260. Without the election the "
     "factor is 1.0; if its rule never ran at all the `FirstValue "
     "FromConstant=\"0.0\"` in the premium would make it zero"),
]


def main() -> int:
    book = book_for(golden.JURIS, golden.ASOF)
    print(f"{book}\n")
    print(f"{'case':32s} {'base':>7s} {'LOI':>7s} {'final':>7s} {'premium':>8s}")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = golden.submission(100000, 0)
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=True,
                          null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict("MasterCFOR", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:32s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/BasicGroupIBaseRate", data),
               read(f"{STRUCT}/BasicGroupILOIFactor", data),
               read(f"{STRUCT}/FinalBasicGroupIRate", data),
               read(PREMIUM, data))
        good = got == expect
        ok &= good
        print(f"{name:32s} {got[0]:>7s} {got[1]:>7s} {got[2]:>7s} {got[3]:>8s}"
              f"   {'OK' if good else 'MISMATCH expected ' + str(expect)}")

    print("\nWhat each case proves")
    for name, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
