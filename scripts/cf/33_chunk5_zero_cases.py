#!/usr/bin/env python3
"""Chunk 5, task C5-03 -- every Business Income `0` against its branch.

Business Income has fewer zero sites than Building or Contents -- it has no
deductible factor and no limit factor to zero -- but the ones it has are the
most reachable in the project so far.

    Z1  Building's base rate zeroed   -> BI Basic Group I zeroes with it
    Z2  a COMBINED type of risk       -> Factor 0.0 from a FILED row
    Z3  an off-domain TypeOfRisk      -> the lookup misses, Factor NULL
    Z4  Coinsurance absent            -> CoinsuranceToUse blank, Factor 0.0

**Z2 is the one to read twice.** `BusnIncomeFactor` files the four "Combined"
risk types at **0** for every coinsurance percentage. A submitter choosing
`Combined Manufacturing and Mercantile Operations` -- a value ISO's own domain
offers, spelled correctly -- gets a premium of zero. The filed 0 is a
placeholder: those risks are meant to be a percentage-weighted blend of two
`LookupBusnIncomeFactor` results, held in the `TypeRiskCombination1Factor` and
`TypeRiskCombination2Factor` DATADEFS and weighted by
`CombinedTypeOfRiskManufacturingPct` and friends. **Without those percentage
fields the blend has nothing to weight and the placeholder is what reaches the
premium.**

(The algorithms page calls `TypeRiskCombination1Factor`/`2Factor` rate tables.
They are not -- no such tables exist in the corpus. They are intermediate
datadefs. Corrected there; it is C5-12's answer arriving early.)

**Z1 is the new shape for this chunk.** Business Income is arithmetically
downstream of Building, so every absent-means-zero finding from chunks 1-3 now
has a second consumer: an off-domain construction type zeroes the Building
premium AND the Business Income premium, from one field.

    python scripts/cf/33_chunk5_zero_cases.py

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
zeros2 = import_module("10_chunk2_zero_cases")
chunk5 = import_module("32_chunk5_golden_case")

BI, BGI, BGII = chunk5.BI, chunk2.BGI, chunk2.BGII
PREM = chunk5._P % "BasicGroupI"

COMBINED = "Combined Manufacturing and Mercantile Operations"

#: id, mutation, (BI base rate, Factor, BI premium, Building Group I), why.
#: A Factor of `None` means the datadef is never written -- which is a
#: different outcome from a written 0, and both are asserted.
CASES = [
    ("baseline", lambda s: None, ("0.203", "0.55", "112", "261"),
     "the reference the others are read against"),

    ("Z1  ConstructionType off-domain",
     lambda s: zeros2.structure(s).__setitem__(
         "ConstructionType", "Joisted Masonry"),
     ("0", "0.55", "0", "0"),
     "**one field, two coverages.** `Joisted Masonry` is the name the rate "
     "table is keyed on and NOT one of the 25 submission values (chunk 3's "
     "finding), so Building prices at zero -- and Business Income, which reads "
     "Building's computed base rate, goes with it. The Factor is still a "
     "healthy 0.55, which is what makes it look survivable"),

    ("Z2  TypeOfRisk = a COMBINED risk",
     lambda s: chunk5.submission and _set_risk(s, COMBINED),
     ("0.203", "0", "0", "261"),
     "**a filed row worth 0.0.** All four Combined risk types are filed at 0 "
     "for every coinsurance percentage, because they are meant to be a "
     "percentage-weighted blend of two lookups. Without the "
     "`CombinedTypeOfRisk...Pct` fields the blend has nothing to weight, and "
     "the placeholder reaches the premium. **A correctly-spelled value from "
     "ISO's own domain that prices at zero**"),

    ("Z3  TypeOfRisk off-domain",
     lambda s: _set_risk(s, "Mercantile"),
     ("0.203", None, "0", "261"),
     "`Mercantile` is not a filed value -- the filed one is `Mercantile and "
     "Non-manufacturing`. **And the Factor comes back NULL here, not 0** -- "
     "the datadef is never written at all, where Z2's filed row writes a 0 and "
     "Z4's blank key writes a 0. Three routes to the same $0 premium and two "
     "different values underneath. "
     "Worth noting against chunk 3: a null Factor does NOT trigger the "
     "null-premium guard. It reaches the premium as $0 rather than a refusal, "
     "so the loudest failure mode in the project does not apply here"),

    ("Z4  Coinsurance absent",
     lambda s: _bi(s).pop("Coinsurance", None),
     ("0.203", "0", "0", "261"),
     "`CoinsuranceToUse` is the third key of the Factor lookup, so a missing "
     "coinsurance percentage misses the row entirely. In Building a missing "
     "coinsurance would cost one factor; here it costs the whole premium"),
]


def _bi(sub):
    return zeros2.structure(sub)["CommercialPropertyBusinessIncomeTable"][
        "CommercialPropertyBusinessIncome"][0]


def _set_risk(sub, risk):
    _bi(sub)["TypeOfRisk"] = risk


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk5.submission("Basic")
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
        got = (read(f"{BI}/BasicGroupIRate", data),
               read(f"{BI}/Factor", data),
               read(PREM, data),
               read(BGI, data))
        good = got == tuple(expect)
        ok &= good
        print(f"{name:36s} rate={str(got[0]):>6s} Factor={str(got[1]):>5s} "
              f"BI={str(got[2]):>4s} Building={str(got[3]):>4s}"
              + ("" if good else f"   <-- expected {expect}"))

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
