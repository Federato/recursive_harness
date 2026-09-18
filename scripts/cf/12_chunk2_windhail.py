#!/usr/bin/env python3
"""Chunk 2 -- the windstorm/hail-excluded branch, the trap the build order flagged.

When a wind/hail exclusion is scheduled, Group II does not adjust the rate it
just built. **It throws it away and rebuilds from a different table**:

    normal    BasicGroupIIRate            x StdPropPolGroupIIFactor
    excluded  LowestBasicGroupIIBaseRate  x LCM x roof ACV x roof cosmetic
                                          x WindstormOrHailExclFactor
                                          x StdPropPolGroupIIFactor

`LowestBasicGroupIIRate` is keyed on symbol ALONE -- no territory -- so it is a
statewide floor rate. And the rebuilt form **drops `BasicGroupIINumericValue`
and `BCEGFactor` entirely**, which is the build order's "silently drops the
class hazard load".

Three cases, because the interesting claims are structural rather than numeric:

  W1  the branch itself
  W2  the same case with BCEG REMOVED -- must give the identical premium,
      which proves BCEG really is dropped. Contrast chunk 2's zero case Z4,
      where removing BCEG on the normal branch takes the premium to 0.
  W3  the same case in an INELIGIBLE state

    python scripts/cf/12_chunk2_windhail.py

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
zeros = import_module("10_chunk2_zero_cases")

STRUCT, BGII = chunk2.STRUCT, chunk2.BGII

#: The 8 jurisdictions that file neither `LowestBasicGroupIIRate` nor a
#: populated `WindstormOrHailExclFactor`. The algorithms doc reads them as
#: states that "plausibly don't permit excluding wind/hail at all".
#:
#: **That is right for half of them and wrong for the rest.** All 8 override
#: `SetBasicGroupIICauseOfLossAdjustment`, and the overrides split three ways:
#:
#:   FL, KS, PR      their OWN mechanism -- a direct
#:                   `BasicGroupIIWindstormOrHailExclRate` (a rate) instead of
#:                   countrywide's factor applied to the lowest base rate. The
#:                   exclusion IS available and IS priced, differently. Kansas
#:                   also adds a `PublicInstitutionalPlanFactor` branch.
#:   AR, DC, NY, RI  their override never tests for the exclusion record at
#:                   all, so scheduling it changes nothing -- the normal rate
#:                   applies. This is the "not permitted" reading, and it is
#:                   the only group it fits.
#:   TX              a fourth shape: references `WindstormOrHailExclFactor`
#:                   but likewise does not test the record. Not yet traced.
#:
#: So the empty `WindstormOrHailExclFactor` override is not evidence of
#: ineligibility. It means "this state does not use the COUNTRYWIDE
#: mechanism" -- which for three of them is because they have their own.
INELIGIBLE = ("AR", "DC", "FL", "KS", "NY", "PR", "RI", "TX")
OWN_MECHANISM = ("FL", "KS", "PR")
IGNORES_EXCLUSION = ("AR", "DC", "NY", "RI")


def exclude(sub):
    st = zeros.structure(sub)
    st["CommercialPropertyWindstormOrHailExclusionTable"] = {
        "CommercialPropertyWindstormOrHailExclusion": [{}]}


#: id, jurisdiction, mutation, (numeric, coladj, final, premium), what it proves
CASES = [
    ("W0  baseline, no exclusion", "OR", lambda s: None,
     ("1", "0.027", "0.032", "32"),
     "the normal branch, for contrast"),

    ("W1  wind/hail excluded", "OR", exclude,
     ("1", "0.009", "0.011", "11"),
     "rebuilt from the statewide LOWEST rate (0.028, symbol only -- no "
     "territory) x wind/hail 0.315 for symbol B. The territory-rated 0.027 is "
     "discarded, not adjusted"),

    ("W2  ...and BCEG removed", "OR",
     lambda s: (exclude(s), zeros.structure(s).pop("BCEG")),
     ("1", "0.009", "0.011", "11"),
     "**identical to W1** -- which is the proof that BCEG is dropped on this "
     "branch. On the NORMAL branch removing BCEG takes the premium to zero "
     "(zero case Z4); here it changes nothing at all"),

    ("W3a Kansas, no exclusion", "KS", lambda s: None,
     ("1", "0.399", "0.47", "470"),
     "Kansas on its normal branch, for contrast with W3b. Note its override "
     "also drops `StdPropPolGroupIIFactor`, which countrywide applies"),

    ("W3b Kansas, wind/hail excluded", "KS", exclude,
     ("1", "0.023", "0.027", "27"),
     "**$470 to $27 -- Kansas prices the exclusion, it does not ignore it.**\n"
     "    This case was written twice and wrong both times, which is the "
     "point of asserting rather than observing. First guess: the premium "
     "collapses to 0, because an empty `WindstormOrHailExclFactor` override "
     "makes the factor 0. Second guess: nothing changes, because Kansas's "
     "override has no wind/hail branch. Neither.\n"
     "    Kansas overrides `SetBasicGroupIICauseOfLossAdjustment` with a "
     "STRUCTURALLY DIFFERENT mechanism: a direct "
     "`BasicGroupIIWindstormOrHailExclRate` -- a rate, not a factor on the "
     "lowest base rate -- plus a `PublicInstitutionalPlanFactor` branch "
     "countrywide has no concept of.\n"
     "    So the empty countrywide table is not evidence of ineligibility. "
     "It means Kansas does not use the COUNTRYWIDE mechanism, because it has "
     "its own"),
]


def main() -> int:
    ok = True
    print(f"{'case':36s} {'juris':5s} {'numeric':>8s} {'coladj':>7s} "
          f"{'final':>6s} {'BGII':>5s}")
    for name, juris, mutate, expect, why in CASES:
        sub = chunk2.submission()
        # Every state but Oregon needs its own territory and the Group II
        # rating type; Kansas is one of the 36 that override the rate rule.
        if juris != "OR":
            book0 = book_for(juris, chunk2.ASOF)
            t = book0.table("BasicGroupIIRate")
            row = next((r for r in t.rows
                        if str(r[t.col("BasicGroupIISymbol")]) == "B"
                        and str(r[t.col("CovType")]) == "Bldg"), None)
            if row is not None:
                zeros.location(sub)["BasicGroupIIRatingTerr"] = str(
                    row[t.col("BasicGroupIIRatingTerr")])
            zeros.structure(sub)["RatingTypeBasicGroupII"] = "Class"
        mutate(sub)
        book = book_for(juris, chunk2.ASOF)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{juris}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:36s} {juris:5s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/BasicGroupIINumericValue", data),
               read(f"{STRUCT}/BasicGroupIICauseOfLossAdjustment", data),
               read(f"{STRUCT}/FinalBasicGroupIIRate", data),
               read(BGII, data))
        good = got == expect
        ok &= good
        print(f"{name:36s} {juris:5s} {got[0]:>8s} {got[1]:>7s} {got[2]:>6s} "
              f"{got[3]:>5s}" + ("" if good else f"   MISMATCH expected {expect}"))

    print("\nWhat each case proves")
    for name, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print(f"\nThe {len(INELIGIBLE)} jurisdictions without the countrywide "
          f"mechanism split three ways -- all 8 override the rule:")
    print(f"   own excluded RATE, priced differently : "
          f"{', '.join(OWN_MECHANISM)}")
    print(f"   exclusion never tested, so ignored    : "
          f"{', '.join(IGNORES_EXCLUSION)}")
    print( "   a fourth shape, not yet traced        : TX")
    print()
    if ok:
        print(f"All {len(CASES)} cases match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
