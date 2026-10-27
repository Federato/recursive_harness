#!/usr/bin/env python3
"""Chunk 2's golden case -- Building, Basic Group II, class-rated, scheduled.

Specified in `docs/CF-CHUNK2-GOLDEN-CASE.md`, which carries the rule-by-rule
and row-by-row derivation written BEFORE this ran.

Built **differentially against chunk 1**: the same Oregon building, plus the
three inputs Group II needs and Group I does not. One submission, two premiums.

    Group I   $261   unchanged -- chunk 1 re-proved, not replaced
    Group II  $32    the new chain

Group I's premium moving would be the most valuable thing this case could find:
its chain never reads `CauseOfLoss`, and the three new inputs are Group II's
alone, so movement would mean the two chains are coupled somewhere neither
document says they are.

    python scripts/cf/09_chunk2_golden_case.py [--trace]

Exit 0 when both premiums match.
"""
from __future__ import annotations

import argparse
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

JURIS, ASOF = golden.JURIS, golden.ASOF

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
BGI = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
BGII = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupIICoverage/Premium"

#: The Group II chain, in the order the rules compute it, with what the
#: derivation says each value must be. `None` means "report it, do not assert".
CHAIN = [
    ("BasicGroupIISymbolToUse", "B", "symbol   Frame + 1-3 stories [CW]"),
    ("BasicGroupIIRatingTerr", "Entire State", "territory  Group II's OWN field"),
    ("BasicGroupIINumericValue", "1", "step 1   numeric value"),
    ("BasicGroupIIBaseRate", "0.028", "step 2   base rate        [OR]"),
    ("LowestBasicGroupIIBaseRate", "0.028", "step 3   lowest (unused here)"),
    ("BCEGFactor", "0.96", "         BCEG grade 4     [OR]"),
    ("BasicGroupIIRate", "0.027", "step 4   rate"),
    ("BasicGroupIICauseOfLossAdjustment", "0.027", "step 5   COL adjustment"),
    ("BasicGroupIICoinsuranceFactor", "0.95", "step 6   coinsurance -- COPIED from Group I"),
    ("BasicGroupIILOIFactor", "1.266", "step 7   limit of insce   [CW]"),
    ("AdjustedBasicGroupIIRate", "0.033", "step 8   adjusted rate"),
    ("BGIIDeductibleByLocationFactor", "1", "step 9   ded by location"),
    ("DeductibleFactorBasicGroupII", "0.98", "step 10  deductible       [OR]"),
    ("FinalBasicGroupIIRate", "0.032", "step 11  final rate"),
]


def submission():
    """Chunk 1 case A, plus the three inputs Group II needs."""
    sub = golden.submission(100000, 0)
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    # Group II has its OWN territory field, and in Oregon its own (coarser)
    # scheme: one territory for Group II against three for Group I. The two
    # are unrelated, and supplying only Group I's is what made Group II price
    # at zero in chunk 1 -- silently.
    loc["BasicGroupIIRatingTerr"] = "Entire State"
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    # `"Basic Group I"` is NOT in ISO's domain -- the filed options for a
    # Commercial Property Policy building are Basic / Broad / Special. It did
    # no harm in chunk 1 (nothing reads it but a non-blank gate) and ISO
    # accepted it, but a golden case should not carry an off-domain value.
    st["CauseOfLoss"] = "Basic"
    st["NumStories"] = "1-3"          # with Frame, resolves symbol B
    st["BCEG"] = "4"                  # factor 0.96, deliberately not 1.0
    return sub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")
    ip = Interpreter(book, rounding=ROUNDING, trace=True,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    try:
        ip.run(data)
    except Exception as exc:
        print(f"RAISED {type(exc).__name__}: {exc}")
        return 1

    ok = True
    print("Basic Group II chain")
    for dd, want, label in CHAIN:
        got = read(f"{STRUCT}/{dd}", data)
        good = want is None or got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"   {label:44s} {dd:34s} = {got}{flag}")

    print()
    for name, path, want in (("GROUP II", BGII, Decimal(32)),
                             ("GROUP I ", BGI, Decimal(261))):
        got = read(path, data)
        good = got is not None and Decimal(got) == want
        ok &= good
        note = "" if name.strip() == "GROUP II" else "  (unchanged from chunk 1)"
        print(f"   {name} PREMIUM = {got}   (expected {want})"
              f" {'OK' if good else 'MISMATCH'}{note}")

    if a.trace:
        print(ip.trace_text())
    if ip.messages:
        print(f"\n   ISO validation messages ({len(ip.messages)}):")
        for m in ip.messages[:20]:
            print(f"      - {m}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
