#!/usr/bin/env python3
"""Chunk 1's golden case, rated end to end.

The three cases are specified in `docs/CF-CHUNK1-GOLDEN-CASE.md`, which also
carries the rule-by-rule and row-by-row derivation of each expected value:

    A   $261   the primary case
    B   $263   contents at the location -- the deductible keys on the location
               total, not the building limit
    C   $288   a limit at a band midpoint -- the LOI factor interpolates

The submission below is built as a plain dict and turned into ISO's data tree.
It is deliberately minimal: the point of a first golden case is the shortest
path that still exercises every shared mechanism, so every optional coverage,
endorsement and election is absent rather than set to a no-op value.

    python scripts/cf/01_golden_case.py [--case A|B|C|all] [--trace]

Exit 0 when every requested case matches its expected premium.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _state_inputs as _si                                     # noqa: E402  C28-17: Oregon's own Group II inputs
from gl_engine.interp.tree import Node, dump, read

JURIS, ASOF = "OR", "20260917"

#: The chain values the gate wants traced, in the order the rules compute them.
#: Named by datadef so they are read out of the tree rather than scraped from
#: the trace text.
CHAIN = [
    ("ClassCodeToUse", "0951", "input   class code"),
    ("ConstructionCode", "1", "input   construction"),
    ("TotAmtInsurance", None, "derived location total"),
    ("BasicGroupIBaseRate", "0.498", "step 1  base rate       [OR]"),
    ("BasicGroupIRate", "0.239", "step 2  x terr x prot cls"),
    ("BasicGroupICauseOfLossAdjustment", "0.239", "step 3  COL adjustment"),
    ("CoinsuranceFactor", "0.95", "step 4  coinsurance     [CW]"),
    ("BasicGroupILOIFactor", None, "step 4  limit of insce  [CW]"),
    ("AdjustedBasicGroupIRate", None, "step 4  adjusted rate"),
    ("DeductibleFactorBasicGroupI", None, "step 5  deductible      [OR]"),
    ("FinalBasicGroupIRate", None, "step 5  final rate"),
]


def submission(limit: int, contents: int = 0) -> dict:
    """One policy, one location, one scheduled class-rated building.

    Three fields are NOT what the golden-case document first supposed, and each
    was corrected against the rule that sets it rather than against a guess:

    * **`ClassCode`, not `ClassCodeToUse`.** `SetClassCodeToUse` is a straight
      `Copy` from `ClassCode`, so supplying the derived field is silently
      overwritten with the blank source field -- and a blank class code fails
      `SetBasicGroupIBaseRate`'s gate, producing a base rate of `0.0` and a
      premium of zero with no error anywhere.
    * **`ConstructionType`, not `ConstructionCode`.** The code is looked up from
      the type's TEXT (`ConstructionCode.RateTable.csv`: Frame 1, Joisted
      Masonry 2, ... Fire Resistive 6), so the golden case's "construction
      code 1" is a Frame building.
    * **`TotAmtInsurance` is DERIVED, not supplied.** `SetTotAmtInsurance` sums
      `StructureLimitToUse + OccupancyTotAmtInsuranceSum +
      SpecialClassRiskTotAmtInsurance`. So the deductible key cannot be set
      directly: case B has to put real contents at the location and let ISO
      total them, which is the honest version of that test anyway.
    """
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        # A submission input, NOT derived by any rule: the
                        # rules read `BasicGroupIRatingTerr` directly and only
                        # guard on it being non-empty. The City -> territory
                        # domain table is a dropdown constraint, not a
                        # derivation the engine performs.
                        "BasicGroupIRatingTerr": "Portland",
                        # `ProtectClass` lives on the LOCATION and is read by
                        # the structure as `../../ProtectClass`. A protection
                        # class set on the structure is simply never seen, and
                        # the factor quietly stays 1.0.
                        "ProtectClass": "3",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [{
                                "RatingType": "Class",
                                "ClassCode": "0951",
                                "ConstructionType": "Frame",
                                "CovType": "Building",
                                "CauseOfLoss": "Basic Group I",
                                "Coinsurance": "90%",
                                "Limit": str(limit),
                                "FullBldgValue": str(limit),
                                "Deductible": "1,000",
                                "LossCostMultiplier": "1.0",
                                "IncludedInBlkt": "No",
                                "PackageModFactor": "1.0",
                                "MultiPremiumAndDispersionCreditFactor": "1.0",
                                # ISO refuses a policy with contents unless the
                                # BUILDING carries this: the contents rule looks
                                # it up `SingleResult` (CW + blank: no row), and
                                # ours now refuses there too (chunk 28 C28-05,
                                # OI-103). The building's own deductible; every
                                # pinned figure unchanged (measured 2026-10-02).
                                **({"WindstormOrHailDeductible": "1,000"}
                                   if contents else {}),
                                # Contents at the same structure. Present only
                                # for case B: the building chain never reads
                                # them, but `SetTotAmtInsurance` sums them into
                                # the location total the DEDUCTIBLE keys on.
                                **({"CommercialPropertyOccupClassTable": {
                                    "CommercialPropertyOccupClass": [{
                                        "CommercialPropertyPersonalPropertyTable": {
                                            "CommercialPropertyPersonalProperty": [{
                                                "Limit": str(contents),
                                                "CovType": "Personal Property",
                                                # `SetLimitToUse` only fires on
                                                # a non-blanketed item; without
                                                # this the contents total zero
                                                # and the location total is
                                                # unchanged.
                                                "IncludedInBlkt": "No",
                                            }],
                                        },
                                    }],
                                }} if contents else {}),
                            }],
                        },
                    }],
                },
            }],
        },
    }


#: limit, contents at the location, expected premium, what it isolates
CASES = {
    "A": (100000, 0, Decimal(261), "the primary case"),
    "B": (100000, 100000, Decimal(263), "contents at the location"),
    "C": (112500, 0, Decimal(288), "LOI interpolation at a band midpoint"),
}


def rate(limit: int, contents: int, trace: bool):
    book = book_for(JURIS, ASOF)
    ip = Interpreter(book, rounding=ROUNDING, trace=True,
                          null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict("MasterCFOR", _si.localize(submission(limit, contents), JURIS, ASOF))
    ip.run(data)
    return ip, data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="all", choices=["A", "B", "C", "all"])
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true", help="print the data tree")
    a = ap.parse_args()

    names = ["A", "B", "C"] if a.case == "all" else [a.case]
    book = book_for(JURIS, ASOF)
    print(f"{book}\n")
    ok = True
    for name in names:
        limit, contents, expect, why = CASES[name]
        print(f"case {name} -- {why}  (Limit {limit:,}, "
              f"contents {contents:,})")
        try:
            ip, data = rate(limit, contents, a.trace)
        except Exception as exc:
            print(f"  RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue

        struct = "CommercialPropertyTable/CommercialProperty/" \
                 "CommercialPropertyLocationTable/CommercialPropertyLocation/" \
                 "CommercialPropertyStructureTable/CommercialPropertyStructure"
        for dd, want, label in CHAIN:
            got = read(f"{struct}/{dd}", data)
            flag = "" if want is None or got == want else f"  << expected {want}"
            print(f"    {label:32s} {dd:36s} = {got}{flag}")
        prem = read(f"{struct}/"
                    "CommercialPropertyStructureBuildingBasicGroupICoverage/"
                    "Premium", data)
        good = prem is not None and Decimal(prem) == expect
        ok &= good
        print(f"    {'PREMIUM':32s} {'':36s} = {prem}   "
              f"(expected {expect}) {'OK' if good else 'MISMATCH'}")
        if a.trace:
            print(ip.trace_text())
        if a.dump:
            print(dump(data))
        if ip.messages:
            print(f"    ISO validation messages ({len(ip.messages)}):")
            for m in ip.messages[:20]:
                print(f"      - {m}")
        print()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
