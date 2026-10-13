#!/usr/bin/env python3
"""Chunk 9, task C9-20 -- the cross-coverage leak, asked at the policy level.

Chunk 8's C8-25 (`66_chunk8_crossform.py`, "25 Six coverages on one
submission") found a leak WITHIN one building: switching the Building's
`CovType` to Legal Liability took the sibling PersonalProperty coverage's
own LOI factor from 0.898 to 1, on a coverage that stayed class-rated.
The mechanism was a parent-child relative path -- PersonalProperty sits
NESTED INSIDE the Structure in the DataDef tree, and its own LOI setter
reads `../CovType`, i.e. the Building's field, not its own. Changing the
parent changed what the child's OWN setter saw.

This task asks the same question one level up: two structures/items on the
SAME policy, one inside chunk 9's blanket group (`IncludedInBlkt="Yes"`,
part of the golden case) and one deliberately outside it
(`IncludedInBlkt="No"`, chunk 1's own ordinary class-rated risk, unrelated
`BlktIDNum` -- it carries none). Structures at the same LEVEL are siblings
under `CommercialPropertyStructureTable`, not parent-and-child the way
Structure and PersonalProperty are -- so there is no `../`-style shared
reference for a leak to travel through BY CONSTRUCTION, unlike C8-25's
case. That structural difference is stated up front, not assumed to settle
the question: both possible confounds are tested directly.

Two placements, both run:

  1. Same POLICY, DIFFERENT location -- the ordinary structure sits in its
     own `CommercialPropertyLocation`, entirely separate from the blanket
     pair's location. No location-level aggregate can possibly reach it.
  2. Same POLICY, SAME location as the two blanket structures -- the
     harder case. This project's own standing note
     (`project_deductiblefactor-uses-location-total-not-building-limit.md`)
     already flags that `DeductibleFactor` reads `TotAmtInsurance`, a
     LOCATION-level aggregate (`Bldg + Contents`), not a per-building limit
     -- exactly the kind of shared-location field that could carry a leak
     if it were computed by summing ACROSS structures rather than reading
     each structure's own value. Both placements are hand-derived to
     produce the SAME, chunk-1-proved premium ($261) before running.

    python scripts/cf/83_chunk9_c9-20_crosscoverage_leak.py

Exit 0 when both placements confirm the ordinary structure's premium is
unmoved and the two blanket structures' premiums are unmoved by its
presence.
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
import _state_inputs as _si                                     # noqa: E402
from gl_engine.interp.tree import Node, read

g9 = import_module("68_chunk9_golden_case")
g1 = import_module("01_golden_case")

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty"


def run_case(same_location: bool):
    sub = g9.submission()
    policy = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    ordinary_sub = g1.submission(100000, 0)
    ordinary_loc = (ordinary_sub["CommercialPropertyTable"]["CommercialProperty"][0]
                     ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])

    if same_location:
        # Harder case: the ordinary structure joins the blanket pair's OWN
        # location, so any location-scoped aggregate (TotAmtInsurance and
        # anything derived from it) is exercised too.
        blkt_loc = policy["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
        ordinary_struct = (ordinary_loc["CommercialPropertyStructureTable"]
                            ["CommercialPropertyStructure"][0])
        blkt_loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"].append(
            ordinary_struct)
        ord_path = (CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation[1]"
                    "/CommercialPropertyStructureTable/CommercialPropertyStructure[3]")
    else:
        policy["CommercialPropertyLocationTable"]["CommercialPropertyLocation"].append(
            ordinary_loc)
        ord_path = (CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation[2]"
                    "/CommercialPropertyStructureTable/CommercialPropertyStructure[1]")

    _si.localize(sub, JURIS, ASOF)      # C28-17: the state's own Group II territory
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)

    loc1 = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation[1]"
    s1 = loc1 + "/CommercialPropertyStructureTable/CommercialPropertyStructure[1]"
    s2 = loc1 + "/CommercialPropertyStructureTable/CommercialPropertyStructure[2]"
    p = "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
    return {
        "ordinary": read(ord_path + p, data),
        "blkt_a": read(s1 + p, data),
        "blkt_b": read(s2 + p, data),
        "messages": len(ip.messages),
    }


def main() -> int:
    ok = True
    print("Hand-derived before running: ordinary = 261 (chunk 1's own case "
          "A, unmoved), blkt A = 255, blkt B = 510 (chunk 9's own golden "
          "case, unmoved) -- in BOTH placements.\n")

    for label, same_loc in [
        ("1. Same policy, DIFFERENT location", False),
        ("2. Same policy, SAME location as the blanket pair (harder case)", True),
    ]:
        r = run_case(same_loc)
        good = (str(r["ordinary"]) == "261" and str(r["blkt_a"]) == "255"
                and str(r["blkt_b"]) == "510")
        ok &= good
        print(f"=== {label}")
        print(f"    ordinary structure Premium = {r['ordinary']:>4}  "
              f"(expected 261)  {'OK' if good else 'MISMATCH'}")
        print(f"    blanket Structure A Premium = {r['blkt_a']:>4}  "
              f"(expected 255)")
        print(f"    blanket Structure B Premium = {r['blkt_b']:>4}  "
              f"(expected 510)")
        print(f"    ISO validation messages: {r['messages']}\n")

    print()
    if ok:
        print("CLEAN ISOLATION, both placements, including the harder "
              "same-location case that could have exercised a "
              "TotAmtInsurance-style shared aggregate. C8-25's leak "
              "traveled through a parent-child relative path "
              "(PersonalProperty's `../CovType` reading its own parent "
              "Structure's field) -- structures at the same level are "
              "siblings, not parent-and-child, so there is no equivalent "
              "path for a leak to travel through here, and no leak was "
              "found by running it either. No engine gap.")
        return 0
    print("LEAK FOUND -- see mismatch above; do not paper over it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
