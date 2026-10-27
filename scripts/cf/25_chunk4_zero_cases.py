#!/usr/bin/env python3
"""Chunk 4, task C4-03 -- every Contents `0` against its consuming branch.

Personal Property files more zero sites than Building, and three of them are in
rules Building does not have at all -- so no case from chunks 1-3 covers them.

    Z1  RatingType not "Class"     -> FireSafeVaultFactor 0.0   (PP-only rule)
    Z2  ProtectClass blank         -> ProtectionClassFactor 0.0 (inner gate)
    Z3  CovType Valuable Papers    -> COL adjustment 0.0        (PP-only gate)
    Z4  occupancy ClassCode absent -> OccupCategoryRiskSeverity blank
                                      -> Special base rate 0.0
    Z5  SpecialRatingTerr blank    -> PrsnlPropTerrMultiplier 0.0 (PP-only)

Each moves ONE input and asserts the affected form AND Building, because
Contents and Building share the deductible key, the coinsurance factor and the
protection class -- and a zero that reached Building would be the more serious
finding.

**Every one prices at zero in silence.** That is the ninth through thirteenth
members of the absent-means-zero family, and Z2 is the one worth pausing on: a
blank protection class is a routine data-entry omission, and it takes the
premium to nothing with no message.

    python scripts/cf/25_chunk4_zero_cases.py

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

BGI, BGII = chunk2.BGI, chunk2.BGII
PP = chunk4.PP
VP = "Valuable Papers and Records - Other Than Electronic Data"


def occ_of(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
            ["CommercialPropertyOccupClassTable"]
            ["CommercialPropertyOccupClass"][0])


def item_of(sub):
    return occ_of(sub)["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][0]


def struct_of(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]
            ["CommercialPropertyStructure"][0])


def loc_of(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])


#: Building's premiums per case. **Z2 is the one to read twice**: the same
#: blank protection class prices Contents at ZERO and Building HIGHER, because
#: Building's factor falls back to 1.0 where Contents' falls back to 0.0. One
#: missing field, two coverages, opposite directions.
BUILDING = {"Z1b STRUCTURE RatingType not Class": ("0", "32"),
            "Z2  ProtectClass blank": ("275", "32")}

#: id, cause of loss, mutation, watched datadef, expected value, expected
#: premium for that form, why
CASES = [
    ("baseline  Basic", "Basic", lambda s: None,
     "FireSafeVaultFactor", "1", "223",
     "the reference the Basic cases are read against"),

    ("Z1a per-ITEM RatingType is ignored", "Basic",
     lambda s: item_of(s).__setitem__("RatingType", "Specific"),
     "FireSafeVaultFactor", "1", "223",
     "**the mutation does nothing, and that is the finding.** `SetRatingType` "
     "is a `Copy` from four levels up -- the STRUCTURE's. A per-item rating "
     "type in the submission is silently overruled, exactly as a per-item "
     "class code is. Third inherited field found in this chunk, after "
     "`BldgClassCode` and `CovForm`"),

    ("Z1b STRUCTURE RatingType not Class", "Basic",
     lambda s: struct_of(s).__setitem__("RatingType", "Specific"),
     "FireSafeVaultFactor", "0", "0",
     "**a rule Building does not have.** `SetFireSafeVaultFactor` returns 0.0 "
     "-- not 1.0 -- when the risk is not class-rated, and it multiplies "
     "directly into the Basic Group I rate. Building Group I moves to 0 too, "
     "because it is the structure's own rating type that changed -- so this case "
     "cannot isolate Contents, and says so"),

    ("Z2  ProtectClass blank", "Basic",
     lambda s: loc_of(s).pop("ProtectClass", None),
     "ProtectionClassFactor", "0", "0",
     "the inner gate misses and yields 0.0, where failing the OUTER gate "
     "yields 1.0 -- two fallbacks in one rule, one fatal and one neutral. "
     "**A blank protection class is routine data entry**, and it takes the "
     "premium to nothing with no message"),

    ("Z3  CovType Valuable Papers", "Basic",
     lambda s: item_of(s).__setitem__("CovType", VP),
     "BasicGroupICauseOfLossAdjustment", "0", "0",
     "a PP-only carve-out with no Building equivalent: separately rated "
     "coverage types are zeroed out of the standard math so they do not "
     "double-rate. The RATE is untouched at 0.263 -- only the adjustment is 0"),

    ("Z4  occupancy ClassCode absent", "Special",
     lambda s: occ_of(s).pop("ClassCode", None),
     "SpecialBaseRate", "0", "0",
     "`OccupCategoryRiskSeverity` is DERIVED from OccupCategory + the "
     "occupancy's ClassCode. Without the class code it is blank, and Special's "
     "base-rate gate needs both. **Two levels of indirection between the "
     "missing input and the zero**"),

    ("Z5  SpecialRatingTerr blank", "Special",
     lambda s: loc_of(s).pop("SpecialRatingTerr", None),
     "PrsnlPropTerrMultiplier", "0", "0",
     "**a territory dimension Building's Special does not have at all**, read "
     "six levels above the record being rated, and 0.0 when blank -- so it "
     "collapses the rate rather than leaving it unadjusted"),
]

FORM = {"Basic": "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium",
        "Special": "/CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage/Premium"}


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, col, mutate, dd, want, prem, why in CASES:
        sub = chunk4.submission(col)
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:34s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = read(f"{PP}/{dd}", data)
        gp = read(PP + FORM[col], data)
        gi, gii = read(BGI, data), read(BGII, data)
        wb = BUILDING.get(name, ("263", "32"))
        good = got == want and gp == prem and (gi, gii) == wb
        ok &= good
        print(f"{name:34s} {dd:34s}={str(got):>6s}  premium={str(gp):>4s} "
              f"(want {want}/{prem})  Building {gi}/{gii} (want {wb[0]}/{wb[1]}) "
              f"{'OK' if good else 'MISMATCH'}")

    print("\nWhat each case proves")
    for name, _, _, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match, and Building never moved.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
