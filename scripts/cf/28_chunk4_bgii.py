#!/usr/bin/env python3
"""Chunk 4, tasks C4-19 and C4-20 -- Contents Basic Group II.

**C4-19 -- the Copies.** Personal Property does not resolve its own Group II
symbol or territory. `SetBasicGroupIISymbol` is a `Copy` from four levels up and
`SetBasicGroupIIRatingTerr` from **six**; the resolution logic lives in the
Structure and Location context and is shared with Building. Chunk 2's symbol
work should therefore carry over entirely.

**Verify it, rather than assume it.** A `Copy` from six levels up is exactly the
path that silently yields null, and chunk 2 proved a null symbol prices Group II
at zero with nothing raised. The claim is not just "the golden case works" -- it
is that the two coverages read the SAME source, so removing the ancestor field
must zero BOTH.

**C4-20 -- the numeric value keys on `BldgClassCode`**, Personal Property's own
field name, where Building's rule uses `ClassCodeToUse`. Both descend from the
structure's `ClassCode`, so they should agree; the test is that Contents
responds at all.

Derived by hand from Oregon's filed rows before the run:

    baseline      class 0951, symbol B, Entire State
                  numeric value 1, base 0.031            -> $24
    class 0580    GroupIINumericValue[CW, 0580, 1] = 4
                  rate r3(0.031 x 4 x BCEG 0.96) = 0.119
                  adjusted r3(r3(0.119 x 0.95) x LOI 0.843) = 0.095
                  final r3(0.095 x ded 0.98) = 0.093      -> $93

    python scripts/cf/28_chunk4_bgii.py

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
chunk4 = import_module("22_chunk4_golden_case")
zeros4 = import_module("25_chunk4_zero_cases")

PP, BGII = chunk4.PP, chunk2.BGII
PREM = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupIICoverage/Premium"

#: id, mutation, (symbol, territory, numeric value, base, PP premium,
#: Building Group II premium), why
CASES = [
    ("baseline", lambda s: None,
     ("B", "Entire State", "1", "0.031", "24", "32"),
     "the reference. The symbol and territory arrive by Copy from four and six "
     "levels up, and the Contents base rate is 0.031 where Building's is 0.028 "
     "on the same symbol and territory"),

    ("C4-19a  NumStories removed from the structure",
     lambda s: zeros4.struct_of(s).pop("NumStories", None),
     ("", "Entire State", "1", "0", "0", "0"),
     "**the Copy is a genuine share, not a duplicate.** Storey count is a "
     "STRUCTURE field; removing it leaves no construction symbol, and BOTH "
     "coverages price Group II at zero. One missing field, two coverages, and "
     "nothing raised -- chunk 2's Z2 reached through a four-level Copy"),

    ("C4-19b  Group II territory removed from the location",
     lambda s: zeros4.loc_of(s).pop("BasicGroupIIRatingTerr", None),
     ("B", "", "1", "0", "0", "0"),
     "the same again through a **six-level** Copy. The symbol still resolves, "
     "which is what tells this apart from the case above -- and is why the "
     "symbol and the territory both have to be asserted, not just the premium"),

    ("C4-20  class 0580 -- the numeric value bites",
     lambda s: (zeros4.struct_of(s).__setitem__("ClassCode", "0580"),
                zeros4.occ_of(s).__setitem__("ClassCode", "0580")),
     ("B", "Entire State", "4", "0.031", "93", "127"),
     "**`GroupIINumericValue[CW, 0580, 1] = 4`**, and it multiplies the base "
     "rate before every other factor: $24 becomes $93. Personal Property keys "
     "it on `BldgClassCode` and Building on `ClassCodeToUse`, but both descend "
     "from the structure's `ClassCode`, so the two move together -- Building's "
     "Group II goes to $127, the same figure chunk 2 measured"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk4.submission("Basic")
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:46s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{PP}/BasicGroupIISymbol", data) or "",
               read(f"{PP}/BasicGroupIIRatingTerr", data) or "",
               read(f"{PP}/BasicGroupIINumericValue", data),
               read(f"{PP}/BasicGroupIIBaseRate", data),
               read(PREM, data),
               read(BGII, data))
        good = got == expect
        ok &= good
        print(f"{name:46s} sym={str(got[0]):>3s} terr={str(got[1])[:13]:13s} "
              f"nv={str(got[2]):>3s} base={str(got[3]):>6s} "
              f"contents={str(got[4]):>4s} building={str(got[5]):>4s}"
              + ("" if good else f"\n    <-- expected {expect}"))

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
