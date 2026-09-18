#!/usr/bin/env python3
"""Chunk 4, tasks C4-24 to C4-28 -- Contents Special, the least like Building's.

Building's Special is a flat statewide constant with no class, construction,
territory or symbol. Personal Property's is a 14-step chain with an occupancy
dimension, a territory multiplier, two protective-safeguard credits and a
premium-side limit override -- none of which Building has.

All figures derived by hand from Oregon's filed rows before the run, against
chunk 4's golden Special case: base 0.153, territory multiplier 1.214, rate
0.186, LOI 0.790, coinsurance 0.95, deductible 0.98, premium **$137**.

  24  base rate keyed on **OccupCategory + OccupCategoryRiskSeverity**
  25  **`PrsnlPropTerrMultiplier`** -- a territory dimension Building lacks
  26  theft exclusion keyed on **OccupCategory**, not Building's flat 0.88
  27  **watchman and burglary-alarm credits Copied from the submission**
  28  **`SetLimitToUse`** replaces the exposure base outright

The theft figures are the ones to look at twice. **Building's theft credit is a
flat 0.88 countrywide. Oregon files Personal Property's between 0.2 and 0.6 by
occupancy** -- Offices at 0.4, a 60% reduction against Building's 12%. The two
coverages are not scaled versions of one another.

    python scripts/cf/30_chunk4_special.py

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
PREM = PP + "/CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage/Premium"
SAFEGUARDS = "CommercialPropertyBurglaryAndRobberyProtectiveSafeguards"
PP_THEFT = "CommercialPropertyTheftExclusionPrsnlProp"
ALCOHOL = "CommercialPropertyAlcoholicBeveragesTaxExclusion"


def occ_cat(sub, cat):
    if cat is None:
        zeros4.occ_of(sub).pop("OccupCategory", None)
    else:
        zeros4.occ_of(sub)["OccupCategory"] = cat


#: id, mutation, (base, terr multiplier, theft factor, premium), why
CASES = [
    ("baseline  Offices", lambda s: None,
     ("0.153", "1.214", "1", "137"), "the reference"),

    # ---- C4-24
    ("24  Residential Apartments and Condominiums",
     lambda s: occ_cat(s, "Residential Apartments and Condominiums"),
     ("0.178", "1.214", "1", "159"),
     "**a dimension Building's Special does not have.** The base rate is keyed "
     "on the occupancy category and its risk severity; Building's is one flat "
     "number for the whole state"),

    ("24  Motels and Hotels", lambda s: occ_cat(s, "Motels and Hotels"),
     ("0.121", "1.214", "1", "109"),
     "Oregon files eight categories between 0.069 and 0.316 -- a 4.6x spread "
     "that Building's single 0.047 cannot express at all"),

    ("24  OccupCategory blank", lambda s: occ_cat(s, None),
     ("0", "1.214", "1", "0"),
     "the gate needs both category and severity, and a blank category zeroes "
     "the base rate in silence"),

    # ---- C4-25
    ("25  territory = Remainder of State",
     lambda s: zeros4.loc_of(s).__setitem__(
         "SpecialRatingTerr", "Remainder of State"),
     ("0.153", "1", "1", "113"),
     "**the multiplier is the whole territory dimension.** Multnomah is 1.214 "
     "and the rest of Oregon is 1.000, so the same risk is 21% dearer in "
     "Portland -- and Building's Special has no equivalent lever anywhere"),

    ("25  territory removed",
     lambda s: zeros4.loc_of(s).pop("SpecialRatingTerr", None),
     ("0.153", "0", "1", "0"),
     "0.0 rather than 1.0 when blank, so it collapses the rate instead of "
     "leaving it unadjusted -- read six levels above the record being rated"),

    # ---- C4-26
    ("26  PP theft exclusion attached",
     lambda s: zeros4.item_of(s).__setitem__(
         f"{PP_THEFT}Table", {PP_THEFT: [{}]}),
     ("0.153", "1.214", "0.4", "54"),
     "**0.4 for Offices, against Building's flat 0.88.** Oregon files the "
     "Personal Property credit between 0.2 (Contractors) and 0.6 by "
     "occupancy: a 60% reduction where Building gets 12%. $137 becomes $54"),

    # ---- C4-27
    ("27  watchman credit 0.90 on the structure",
     lambda s: zeros4.struct_of(s).__setitem__(
         f"{SAFEGUARDS}Table",
         {SAFEGUARDS: [{"WatchmanCreditFactor": "0.90",
                        "TypeOfWatchmanSrvc": "Watchman with Clock",
                        "BurglaryAlarmCreditFactor": "1.0"}]}),
     ("0.153", "1.214", "1", "123"),
     "**a factor that arrives in the payload rather than from a rate table.** "
     "It is `Copy`d straight off the protective-safeguards schedule. This is "
     "the one place in the corpus so far where a submitter-supplied factor is "
     "what ISO intends -- everywhere else chunk 3 found that shape to be a "
     "hole. "
     "    The gate needs `TypeOfWatchmanSrvc` on the record as well as the "
     "factor. Supplying the factor alone leaves the credit at 1.0 and the "
     "premium unmoved -- a discount silently not given"),

    # ---- C4-28
    ("28  alcoholic-beverages tax exclusion, limit 60,000",
     lambda s: zeros4.item_of(s).__setitem__(
         f"{ALCOHOL}Table", {ALCOHOL: [{"Limit": "60000"}]}),
     ("0.153", "1.214", "1", "97"),
     "**the exposure base is replaced outright** -- `SetLimitToUse` copies the "
     "EXCLUSION record's limit over the item's own, so the premium is charged "
     "on 60,000 rather than 100,000. "
     "    **But that is not all it does, and $82 was the wrong prediction.** "
     "The same record also shrinks the occupancy amount-of-insurance sums, "
     "which RAISES the limit factor from 0.790 to 0.94 and moves the "
     "deductible from 0.98 to 0.97. Final rate 0.137 -> 0.161. A smaller "
     "exposure at a dearer rate: $137 -> $97, not the $97-vs-$82 a pure "
     "exposure change would give. One record, three effects"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk4.submission("Special")
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
        got = (read(f"{PP}/SpecialBaseRate", data),
               read(f"{PP}/PrsnlPropTerrMultiplier", data),
               read(f"{PP}/SpecialTheftExclusionFactor", data),
               read(PREM, data))
        good = got == expect
        ok &= good
        print(f"{name:46s} base={str(got[0]):>6s} terr={str(got[1]):>6s} "
              f"theft={str(got[2]):>4s} premium={str(got[3]):>4s}"
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
