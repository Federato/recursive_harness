#!/usr/bin/env python3
"""Chunk 3's golden cases -- Building, Broad and Special.

Each form gates its base rate on `CauseOfLossToUse`, so chunk 3 needs a separate
submission per form -- unlike chunk 2, which stacked Group II onto chunk 1's
submission and got two premiums from one building.

That made the cross-form check (task 23) part of the golden case rather than a
separate exercise -- and **the premise behind it was wrong, which is the most
useful thing this case produced.**

The expectation was that the forms are mutually exclusive, so Basic pricing
alongside Broad would be a double count. ISO settled it the other way: they are
**cumulative**. Basic Group I and II rate whenever class, construction and
territory are present, because those perils are always in force; the cause of
loss gates only the Broad and Special increments on top. Confirmed against ISO
for all three selections, coverage by coverage and on the policy total.

Derivation, from the same Oregon building as chunks 1 and 2 (Frame, class 0951,
limit 100,000, deductible 1,000, coinsurance 90%):

    BROAD       base 0.015 [CW]  -- two-tier: 0.015 combustible, 0.010 fire
                                    resistive; keyed on construction type
                rate = r3(base x LCM)                          = 0.015
                adjusted = r3(r3(r3(rate x roofACV) x coins) x LOI)
                         = r3(r3(0.015 x 0.95)=0.014 x 1.237)  = 0.017
                final    = r3(r3(adj x dedByLoc) x ded x multiRes)

    SPECIAL     base 0.047 [OR]  -- a FLAT statewide constant. No class, no
                                    construction, no territory, no symbol.
                                    Header-only countrywide, so Oregon's own
                                    row is the only reason this rates at all
                rate = r3(base x LCM)                          = 0.047
                coladj = r3(r3(rate x theft 1.0) x roofACV)    = 0.047
                adjusted = r3(r3(coladj x coins)=0.045 x 1.237) = 0.056
                final    = r3(r3(adj x dedByLoc) x ded x multiRes)

Broad and Special **share one LOI table** (`BroadSpecialLOIFactorBldg`), 1.237
at a 100,000 limit -- different from Group I's 1.172 and Group II's 1.266.

    python scripts/cf/15_chunk3_golden_case.py

Exit 0 when both forms match.
"""
from __future__ import annotations

import sys
from decimal import Decimal
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
zeros = import_module("10_chunk2_zero_cases")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII
BROAD = STRUCT + "/CommercialPropertyStructureBuildingBroadCoverage/Premium"
SPECIAL = STRUCT + "/CommercialPropertyStructureBuildingSpecialCoverage/Premium"

#: form -> (cause of loss, chain datadefs to report, expected premium)
FORMS = {
    "Broad": {
        "col": "Broad",
        "premium_path": BROAD,
        "chain": [("BroadBaseRate", "0.015", "step 1  base rate       [CW]"),
                  ("BroadRate", "0.015", "step 2  rate"),
                  ("BroadLOIFactor", "1.237", "step 3  LOI (shared table)"),
                  ("AdjustedBroadRate", "0.017", "step 4  adjusted rate"),
                  ("DeductibleFactorBroad", None, "step 5  deductible"),
                  ("FinalBroadRate", None, "step 6  final rate")],
        "expect": Decimal(16),
    },
    "Special": {
        "col": "Special",
        "premium_path": SPECIAL,
        "chain": [("SpecialTheftExclusionFactor", "1", "step 1  theft excl"),
                  ("SpecialBaseRate", "0.047", "step 2  base rate       [OR]"),
                  ("SpecialRate", "0.047", "step 3  rate"),
                  ("SpecialCauseOfLossAdjustment", "0.047", "step 4  COL adj"),
                  ("SpecialLOIFactor", "1.237", "step 5  LOI (shared table)"),
                  ("AdjustedSpecialRate", "0.056", "step 6  adjusted rate"),
                  ("DeductibleFactorSpecial", None, "step 8  deductible"),
                  ("FinalSpecialRate", None, "step 9  final rate")],
        "expect": Decimal(54),
    },
}


def submission(col):
    """Chunk 2's building, with the cause of loss switched to this form."""
    sub = chunk2.submission()
    zeros.structure(sub)["CauseOfLoss"] = col
    return sub


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for form, spec in FORMS.items():
        print(f"=== {form}  (CauseOfLoss = {spec['col']!r})")
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", submission(spec["col"]))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"    RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        for dd, want, label in spec["chain"]:
            got = read(f"{STRUCT}/{dd}", data)
            good = want is None or got == want
            ok &= good
            flag = "" if good else f"   <-- expected {want}"
            print(f"    {label:32s} {dd:30s} = {got}{flag}")

        prem = read(spec["premium_path"], data)
        good = prem is not None and Decimal(prem) == spec["expect"]
        ok &= good
        print(f"    {'PREMIUM':32s} {'':30s} = {prem}   "
              f"(expected {spec['expect']}) {'OK' if good else 'MISMATCH'}")

        # Task 23. The premise was that the forms are MUTUALLY EXCLUSIVE and
        # that Basic pricing alongside Broad would be a double count. **ISO
        # settled it the other way: they are CUMULATIVE.**
        #
        #     CauseOfLoss=Basic    GI 261 + GII 32                  = 293
        #     CauseOfLoss=Broad    GI 261 + GII 32 + Broad   16     = 309
        #     CauseOfLoss=Special  GI 261 + GII 32 + Special 54     = 347
        #
        # ISO returns exactly those, coverage by coverage and as the policy
        # total, and the engine matches all three. Which is the right insurance
        # reading: a Broad cause-of-loss form COVERS the Basic Group I and II
        # perils and adds to them, so the premium is built up in layers rather
        # than swapped. The cause of loss gates only the Broad and Special
        # increments -- Basic rates whenever class, construction and territory
        # are present, because those perils are always in force.
        gi, gii = read(BGI, data), read(BGII, data)
        basic_ok = (gi, gii) == ("261", "32")
        ok &= basic_ok
        total = (Decimal(gi) + Decimal(gii) + Decimal(prem)) if basic_ok else None
        print(f"    cumulative: Basic Group I {gi} + Basic Group II {gii} + "
              f"{form} {prem} = {total}  "
              f"{'OK' if basic_ok else '<-- Basic moved, which it must not'}")
        print()

    if ok:
        print("Both forms match, and both layer onto Basic exactly as ISO does.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
