#!/usr/bin/env python3
"""Chunk 4, tasks C4-14 to C4-18 -- the five Contents-only Basic Group I rules.

Every figure derived by hand from Oregon's filed rows before the run. The
baseline throughout is chunk 4's golden case: class 0951, Frame, Protection
Class 3, one Contents item at 100,000, which prices at **$223**.

  14  `FireSafeVaultFactor` -- no Building equivalent. 0.50 in an approved
      fire-rated vault, 1.0 otherwise, **0.0 when the risk is not class-rated**.
  15  The base rate keys on the occupancy **GROUP letter** (A/B/C/YARD) where
      Building passes the constant `"Not Applicable"`. A documented **two-key**
      mechanism: the class code gates, a separate field picks the letter.
  16  `YARD` **substitutes a hardcoded construction code** (1 or 3) from
      `YardPropertyIndicator`, bypassing the building's own construction.
  17  Class `1150` is **EXCLUDED** from the class-rate path, where Building
      *routes* it to the Builders Risk rows.
  18  `SetProtectionClassFactor` has **two different fallbacks** -- 0.0 when the
      inner gate misses, 1.0 when the outer gate fails.

**Two predictions were wrong, both on the same gate.** The YARD protection-class
condition is `Group <> "YARD" OR YardPropertyIndicator <> "Yard Property - Non
Combustible"`, so the lookup is skipped ONLY for a non-combustible yard. The
algorithms page states it the other way round; corrected there.

    python scripts/cf/27_chunk4_bgi_structure.py

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

PP = chunk4.PP
PREM = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium"
VAULT = "Personal Property in a Vault with an Approved Fire Rating"

#: id, occupancy overrides, item overrides, (base, vault, protClass, premium),
#: why
#: id, structure/occupancy class code, item overrides,
#: (group, base, protClass, premium), why
CASES = [
    ("baseline  class 0951", "0951", {},
     ("Not Applicable", "0.548", "0.96", "223"), "the reference"),

    ("14  CovType = vault", "0951", {"CovType": VAULT},
     ("Not Applicable", "0.548", "0.96", "110"),
     "**a rule Building does not have.** The 0.50 credit multiplies straight "
     "into the rate -- r3(0.548 x 0.5 x 0.96 x 0.499) = 0.131 -- and $223 "
     "becomes $110, almost exactly half, because every factor after it is "
     "shared"),

    ("15  class 0321 -> group A", "0321", {},
     ("A", "0.457", "0.96", "185"),
     "**the group letter is DERIVED, not submitted.** Class 0321 files three "
     "rows, one per letter (A 0.457, B and C both 0.533), and a 17,000-"
     "character rule at the occupancy picks the letter from the class code "
     "alone. A `Group` supplied in the payload is overwritten. Building passes "
     "the constant `Not Applicable` and never sees this dimension"),

    ("16  class 1400, no yard indicator", "1400", {},
     ("Not Applicable", "0.487", "0.96", "196"),
     "class 1400 files rows under BOTH `Not Applicable` and `YARD`. Without "
     "the indicator on the ITEM the plain row applies"),

    ("16  1400 + Yard Property - Non Combustible", "1400",
     {"YardPropertyIndicator": "Yard Property - Non Combustible"},
     ("YARD", "0.059", "1", "25"),
     "**the substitution, proven.** The building is FRAME -- construction code "
     "1 -- and the YARD branch passes code **3** instead, giving 0.059 where "
     "code 1 gives 0.607. The building's own construction is discarded. "
     "And this is the case that LOSES the protection-class credit: the "
     "gate excludes the lookup only when the group is YARD **and** the "
     "property is NON-combustible"),

    ("16  1400 + Yard Property - Combustible", "1400",
     {"YardPropertyIndicator": "Yard Property - Combustible"},
     ("YARD", "0.607", "0.96", "246"),
     "code **1** substituted, which here coincides with the building's own. "
     "A combustible yard KEEPS the 0.96 protection-class credit. "
     "**The algorithms page had this backwards** -- it reads the "
     "non-combustible indicator as the exception that keeps the lookup, where "
     "the filed rule makes it the one case that loses it. Corrected there"),

    ("17  class 1150", "1150", {},
     ("Not Applicable", "0", "0.96", "0"),
     "**the opposite of Building.** Building routes 1150 to the Builders Risk "
     "rows; Personal Property's base-rate gate requires a class code other "
     "than 1150 and returns 0.0. Belt-and-braces: Oregon files **no PersProp "
     "rows for 1150 at all**, so even without the gate the lookup would miss"),

    ("18  class 1751 -- protection class gated OUT", "1751", {},
     ("Not Applicable", "0.164", "1", "69"),
     "**the other fallback.** 1751 and 1752 are excluded from the "
     "protection-class lookup and take **1.0**, where a missing protection "
     "class takes **0.0** (zero case Z2). One rule, two fallbacks, one neutral "
     "and one fatal. At 0.96 the premium would be $66"),
]


def submission(cls, item_over):
    """The class code has to be set on the STRUCTURE.

    `BldgClassCode` on the item is a `Copy` from the occupancy's, and the
    occupancy's is a `Copy` from `../../ClassCode` -- the building's. **Contents
    rate off the building's class code, not their own**, through two levels of
    inheritance. The occupancy copy is set here too because it also drives
    `OccupCategoryRiskSeverity`.

    `YardPropertyIndicator`, by contrast, IS read on the item.
    """
    sub = chunk4.submission("Basic")
    zeros4.struct_of(sub)["ClassCode"] = cls
    zeros4.occ_of(sub)["ClassCode"] = cls
    zeros4.item_of(sub).update(item_over)
    return sub


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, cls, item, expect, why in CASES:
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", submission(cls, item))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:48s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{PP}/Group", data),
               read(f"{PP}/BasicGroupIBaseRate", data),
               read(f"{PP}/ProtectionClassFactor", data),
               read(PREM, data))
        good = got == expect
        ok &= good
        print(f"{name:44s} group={str(got[0]):>14s} base={str(got[1]):>6s} "
              f"prot={str(got[2]):>5s} premium={str(got[3]):>4s}"
              + ("" if good else f"   <-- expected {expect}"))

    print("\nWhat each case proves")
    for name, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
