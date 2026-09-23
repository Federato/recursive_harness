#!/usr/bin/env python3
"""Chunk 12, C12-23 -- the Unmanned Aircraft golden case (CP 04 64).

Specified in `docs/CF-CHUNK12-UNMANNED-AIRCRAFT.md`, derivation written BEFORE
this ran. Chunk 4's Oregon Contents on the Special form (ISO-confirmed $137),
plus one `...PrsnlProp` drone record with one scheduled drone:

    TypeOfOperations "All Other"      -> Ordinary Risk Class, loss cost 1.625
    Deductible "Not Applicable"        -> UnmannedAircraftNoDeductibleFactor 1.15
    no newly-acquired extension        -> 1.0
    LimitOfInsurance 10,000            -> exposure 100

    round3(1.625 x LCM 1.0) = 1.625 -> x 1.0 -> round3(x 1.15) = 1.869
    x vandalism, sprinkler, wind, theft all 1.0 = 1.869;  x 100 = 186.9    $187
    Earthquake cell: not elected                                          $0

Drones are rated only on the Special form: the premium's outer `If` tests the
Contents record's `CauseOfLossToUse` = Special. The loss cost is the family's
own, not the Contents rate.

    python scripts/cf/137_chunk12_drone_golden_case.py [--trace]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g = import_module("127_chunk12_golden_case")
c4 = import_module("22_chunk4_golden_case")
JURIS, ASOF = g.JURIS, g.ASOF

UA = "CommercialPropertyLimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoveragePrsnlProp"
DET = UA + "Detail"
UAP = f"{c4.PP}/{UA}Table/{UA}"
DETP = f"{UAP}/{DET}Table/{DET}"
DRONE = f"{DETP}/{DET}DroneCov/Premium"
EQ = f"{DETP}/{DET}EQCov/Premium"

#: One scheduled drone. The descriptive fields (statistical codes only) are the
#: Georgia ISO fixture's own values, STC_CP000015474.
DETAIL = {
    "TypeOfOperations": "All Other",
    "LimitOfInsurance": "10000",
    "Deductible": "Not Applicable",
    "BlanketCoverageUnmannedAircraftAppliesToUnmannedAircraftNotIndividuallyDescribed": "No",
    "CoverageExtensionForNewlyAcquiredPropertyIncludingTemporarySubstitutePropertyAppliesToScheduledCoverageonly": "No",
    "UnmannedAircraftOwnershipAndOperation": "Unmanned aircraft owned and operated by the insured",
    "UnmannedAircraftRatingIdentification": "Drone (separate limit per drone)",
    "UnmannedAircraftMethodOfControl": "Autonomous drones",
    "UnknownSecurityFeaturesOfDrones": "Yes",
    "IndicateActualCashValueACVOrReplacementCostRC": "Actual Cash Value",
    "UnmannedAircraftPrimaryPlaceOfOperation": "Rural",
    "EQDeductible": "Not Applicable",
}


def submission(detail: dict | None = None, col: str = "Special", details: list | None = None) -> dict:
    sub = c4.submission(col)
    occ = (g.chunk2.submission and sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
           ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
           ["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0])
    # On the Special form ISO looks up the building's WindstormOrHailDeductible
    # and REFUSES a blank key (OI-103); our engine tolerates it. Chunk 4's
    # building never set it, so it is set here to its all-perils deductible
    # (1,000, a filed Oregon value), which moves nothing else.
    (sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
     ["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]
     ["CommercialPropertyStructure"][0])["WindstormOrHailDeductible"] = "1,000"
    pp = occ["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0]
    rows = details if details is not None else [dict(DETAIL if detail is None else detail)]
    pp[f"{UA}Table"] = {UA: [{f"{DET}Table": {DET: rows}}]}
    return sub


CHECKS = [
    ("RiskClass", DETP + "/RiskClass", "Ordinary Risk Class"),
    ("UnmannedAircraftBaseRate", DETP + "/UnmannedAircraftBaseRate", "1.625"),
    ("DeductibleFactor (none)", DETP + "/DeductibleFactor", "1.15"),
    ("NewlyAcquiredPropertyFactor", DETP + "/NewlyAcquiredPropertyFactor", "1.0"),
    ("WindstormOrHailExclFactor", DETP + "/WindstormOrHailExclFactor", "1.0"),
    ("LimitToUse", DETP + "/LimitToUse", "10000"),
    ("TotalScheduleLimit", UAP + "/TotalScheduleLimit", "10000"),
    ("Drone premium", DRONE, "187"),
    ("EQ premium (not elected)", EQ, "0"),
    ("Contents Special unmoved", c4.PP + "/CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage/Premium", "137"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    print(f"{book_for(JURIS, ASOF)}\n")
    data, ip = g.run(submission(), a.trace)
    ok = True
    for label, path, want in CHECKS:
        got = read(path, data)
        good = g.num_eq(got, want)
        ok &= good
        print(f"  {label:32s} = {str(got):>22s}   want {want:>20s}  {'ok' if good else 'MISMATCH'}")
    print(f"\n  messages: {sorted(set(ip.messages))}")
    print(f"  null operands skipped: {ip.null_skips}")
    if a.trace:
        print(ip.trace_text())
    print("\nALL MATCH" if ok else "\nMISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
