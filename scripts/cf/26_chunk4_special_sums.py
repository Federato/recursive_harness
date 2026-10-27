#!/usr/bin/env python3
"""Chunk 4, task C4-13 -- the two Special sums, finally told apart.

`SpecialTotAmtInsurance` and `SpecialIncludingTheftTotAmtInsurance` are the two
amount-of-insurance sums the Special deductible keys on. **Chunk 3 could not
separate them numerically** -- with no contents at the location both equalled
the building limit -- and logged the job here.

**Three things separate them, and the household-limit route is not one of them.**
The first draft read the two occupancy rules side by side, saw that the plain
sum adds `CommercialPropertyHouseholdPersonalPropertyCoverage[1]/Limit` and the
including-theft sum does not, and built the case on that. **It moved nothing** --
that branch is not reachable from this submission shape. What does separate
them, measured:

    cause of loss other than Special   plain 100,000   incl-theft 0
    CP 10 33 attached to the structure plain 200,000   incl-theft 100,000
    a separate theft deductible        no separation, but branch 1 fires

The second is the lever. The theft exclusion removes the occupancy's
contribution from the including-theft sum and leaves the plain sum alone --
and because the record sits on the STRUCTURE, the Personal Property theft
indicator stays 0, so branch 1 of `SetDeductibleFactorSpecial` can still fire.

Derived by hand from Oregon's filed rows before the run:

    Special + CP 10 33 + TheftDeductible 2,500
        plain sum 200,000, including-theft sum 100,000
        branch 1 keys on the INCLUDING-THEFT sum -> 2,500 @ 100,000 = 0.89
        final r3(0.140 x 0.89) = 0.125 -> $125

**$125 is the whole point.** Keyed on the plain 200,000 sum the factor would be
0.92 and the premium $129. **Four dollars is the entire observable difference
between the two sums**, and no submission without the theft exclusion attached
can produce it.

Also worth recording: **`TheftDeductible` is inherited too.** Setting it on the
Personal Property item does nothing -- the occupancy copies it from the
structure, and the item's own field is never populated. That is the **fifth**
inherited field this chunk has found, after `CovForm`, `BldgClassCode`,
`RatingType` and `OccupCategoryRiskSeverity`.

    python scripts/cf/26_chunk4_special_sums.py

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

PP, STRUCT = chunk4.PP, chunk2.STRUCT
SPECIAL = PP + "/CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage/Premium"
THEFT = "CommercialPropertyTheftExclusion"

#: id, cause of loss, CP 10 33 attached?, theft deductible,
#: (plain sum, incl-theft sum, deductible factor, premium), why
CASES = [
    ("baseline -- Special, nothing attached", "Special", False, None,
     ("200000", "200000", "0.98", "137"),
     "chunk 3's position: the two sums are EQUAL and no branch can tell them "
     "apart"),

    ("cause of loss Basic", "Basic", False, None,
     ("100000", "0", "0.97", "0"),
     "**the first separator.** The including-theft sum is gated on "
     "`CauseOfLossToUse = \"Special\"` and collapses to 0; the plain sum drops "
     "to the building limit alone. Neither is used, because Special is not "
     "rating -- which is exactly the trap chunk 3 fell into when it read a "
     "Special-only datadef out of a Basic run"),

    ("Special + CP 10 33 on the structure", "Special", True, None,
     ("200000", "100000", "0.98", "137"),
     "**the usable separator.** The theft exclusion removes the occupancy's "
     "contribution from the including-theft sum and leaves the plain sum "
     "alone. The premium does not move, because branch 4 is still running and "
     "it keys on the plain sum"),

    ("Special + theft deductible 2,500 only", "Special", False, "2,500",
     ("200000", "200000", "0.92", "129"),
     "branch 1 fires -- but both sums are still 200,000, so this proves WHICH "
     "BRANCH ran and nothing about which sum it read"),

    ("Special + CP 10 33 + theft deductible 2,500", "Special", True, "2,500",
     ("200000", "100000", "0.89", "125"),
     "**the decisive case.** 0.89 is the factor for 2,500 at 100,000. At "
     "200,000 it would be 0.92 and the premium $129. So branch 1 reads the "
     "INCLUDING-THEFT sum, as filed -- and $4 is the entire observable "
     "difference between the two"),
]


def submission(col, theft_record, theft_ded):
    sub = chunk4.submission(col)
    if theft_record:
        zeros4.struct_of(sub)[f"{THEFT}Table"] = {THEFT: [{}]}
    if theft_ded:
        # On the STRUCTURE -- the occupancy copies it down. Setting it on the
        # Personal Property item does nothing at all.
        zeros4.struct_of(sub)["TheftDeductible"] = theft_ded
    return sub


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, col, rec, ded, expect, why in CASES:
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}",
                              submission(col, rec, ded))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:46s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/SpecialTotAmtInsurance", data),
               read(f"{STRUCT}/SpecialIncludingTheftTotAmtInsurance", data),
               read(f"{PP}/DeductibleFactorSpecial", data),
               read(SPECIAL, data))
        good = got == expect
        ok &= good
        print(f"{name:46s}")
        print(f"    plain={str(got[0]):>8s} inclTheft={str(got[1]):>8s} "
              f"ded={str(got[2]):>5s} premium={str(got[3]):>5s}")
        if not good:
            print(f"    expected plain={expect[0]} inclTheft={expect[1]} "
                  f"ded={expect[2]} premium={expect[3]}   <-- MISMATCH")

    print("\nWhat each case proves")
    for name, _, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print("The two sums are separated, and branch 1 demonstrably reads the")
        print("including-theft one. C4-13 answers what chunk 3 logged forward.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
