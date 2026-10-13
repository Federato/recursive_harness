#!/usr/bin/env python3
"""Chunk 2, gate point 4 -- every Group II `0` against its consuming branch.

Group II carries more zeros than Group I, and they enter at different places:

  * the base rate needs BOTH a symbol and a territory, and gives `0.0` if
    either is blank -- two distinct causes, one value;
  * the cause-of-loss adjustment is forced to `0.0` outright on a fire-only
    cause of loss, however good the rate underneath it is;
  * the LOI factor assigns `0.0` when its lookup misses.

Each case moves ONE input and asserts the whole Group II chain, because several
produce the same premium by different mechanisms. **Group I is asserted in
every case too** -- it must not move, and if it does the two chains are coupled
somewhere neither document says they are.

    python scripts/cf/10_chunk2_zero_cases.py

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
chunk2 = import_module("09_chunk2_golden_case")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII


def structure(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]
            ["CommercialPropertyStructure"][0])


def location(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]
            ["CommercialPropertyLocation"][0])


def spp(sub):
    """Make it a Standard Property Policy with a fire-only cause of loss.

    The fire-only options are a Standard Property Policy's, not a Commercial
    Property Policy's -- so this switches BOTH, which is why Group I moves too.
    """
    structure(sub)["CauseOfLoss"] = "Fire"
    sub["CommercialPropertyTable"]["CommercialProperty"][0][
        "PolicyType"] = "Standard Property Policy"
    structure(sub)["PolicyType"] = "Standard Property Policy"


#: id, mutation, (symbol, base, rate, coladj, final, BGII premium, BGI premium)
CASES = [
    ("baseline", lambda s: None,
     ("B", "0.028", "0.027", "0.027", "0.032", "32", "261"),
     "the reference the others are read against"),

    ("Z1  blank BasicGroupIIRatingTerr",
     lambda s: location(s).pop("BasicGroupIIRatingTerr"),
     ("B", "0", "0", "0", "0", "0", "261"),
     "the base-rate gate needs a territory. **This is exactly what chunk 1's "
     "submission did by accident** -- it supplied Group I's territory and not "
     "Group II's, so Group II priced at zero and nothing said so. The symbol "
     "still resolves, which is what tells this apart from Z2"),

    ("Z2  blank NumStories",
     lambda s: structure(s).pop("NumStories"),
     ("", "0", "0", "0", "0", "0", "261"),
     "no stories means no construction SYMBOL, and the base rate needs both "
     "symbol and territory. Distinguishable from Z1 only by the symbol being "
     "empty -- the premium is identical"),

    ("Z3  fire-only cause of loss (SPP)", spp,
     ("B", "0.028", "0.027", "0", "0", "0", "242"),
     "**the rate is fine and the premium is still zero.** A fire-only cause "
     "of loss buys no Group II perils, so `SetBasicGroupIICauseOfLoss"
     "Adjustment` forces 0.0 whatever the rate underneath says.\n"
     "    Group I moves to 242, and the derivation was wrong first time: it "
     "predicted 255 from the Standard Property Policy factor (0.98) alone and "
     "forgot that `VandalismExclFactor` fires AUTOMATICALLY on an SPP "
     "fire-only form -- 0.95 for class 0951. Both apply:\n"
     "      r3(0.239 x 1.0) = 0.239 ; x 0.95 = 0.227 ; x 0.98 = 0.222\n"
     "      adjusted r3(0.222 x 0.95) = 0.211 ; x 1.172 = 0.247\n"
     "      final    r3(0.247 x 0.98) = 0.242\n"
     "    The vandalism behaviour was already documented in "
     "`BasicGroupI_ERC_Tables.md`; the engine had it and the prediction did "
     "not"),

    ("Z4  BCEG absent", lambda s: structure(s).pop("BCEG"),
     ("B", "0.028", "0", "0", "0", "0", "261"),
     "**an absent Building Code Effectiveness Grade prices Group II at ZERO, "
     "silently.** This case was written expecting the opposite -- that the "
     "factor would default to 1.0 -- and the engine proved otherwise.\n"
     "    `SetBCEGFactor` assigns only when BasicGroupIIRatingTerr AND BCEG "
     "are both non-blank. With BCEG absent the factor is never written, and "
     "`SetBasicGroupIIRate` reads it through `FirstValue FromConstant=\"0.0\"` "
     "-- so it is 0, and it multiplies the whole rate away. The base rate "
     "still resolves (0.028), which is what makes it look healthy.\n"
     "    Third member of a family now: Arizona's BasicGroupIReductionCredit, "
     "an unrecognised ConstructionType, and this. Absent means zero, and "
     "nothing raises"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    print(f"{'case':36s} {'sym':>4s} {'base':>6s} {'rate':>6s} {'coladj':>7s} "
          f"{'final':>6s} {'BGII':>5s} {'BGI':>5s}")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk2.submission()
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:36s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/BasicGroupIISymbolToUse", data) or "",
               read(f"{STRUCT}/BasicGroupIIBaseRate", data),
               read(f"{STRUCT}/BasicGroupIIRate", data),
               read(f"{STRUCT}/BasicGroupIICauseOfLossAdjustment", data),
               read(f"{STRUCT}/FinalBasicGroupIIRate", data),
               read(BGII, data), read(BGI, data))
        good = got == expect
        ok &= good
        print(f"{name:36s} {got[0]:>4s} {got[1]:>6s} {got[2]:>6s} {got[3]:>7s} "
              f"{got[4]:>6s} {got[5]:>5s} {got[6]:>5s}"
              + ("" if good else f"   MISMATCH expected {expect}"))

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
