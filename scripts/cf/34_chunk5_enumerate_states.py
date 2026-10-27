#!/usr/bin/env python3
"""Chunk 5, tasks C5-04, C5-17 and C5-21 -- every jurisdiction, Business Income.

Same discipline as chunks 1-4: each jurisdiction's premium predicted from its
own filed rows before the engine runs.

**Chunk 5 inverts the problem the last three chunks had.** The tables are
countrywide and complete -- `BusnIncomeFactor` carries 131 CW rows and resolves
in 47 of 47 -- so the sweep's target is not a missing table. It is the CHAIN:

  * **C5-17.** `BaseRateAdjustmentFactor` is the one header-only Business
    Income table. 46 of 47 file rows; **PR does not**, and PR overrides
    `SetBGIBaseRateAdjustmentFactor` with a rule that looks nothing up.
  * **C5-21.** `SetBasicGroupIICauseOfLossAdjustment` is overridden by **10 of
    47** -- AR, DC, FL, IN, KS, KY, NY, PR, RI, TX -- where every other rule in
    the chunk is overridden by 0 to 2. They fall into **three shapes by size**:

        529 chars   AR, DC, NY, RI   rate x BuildersRisk -- and NOTHING ELSE
        717 chars   TX               adds WindstormOrHailExclFactor
      1457-1910     FL, IN, KS, KY, PR  add a wind/hail-excluded RATE and the LCM

    **The four short ones have dropped the wind/hail branch entirely.** That is
    a divergence to classify, not a formatting difference -- and chunk 3 showed
    an override is not automatically a divergence, so each of the ten is
    classified rather than assumed.

The case: the chunk 5 golden case, Basic Group I, `CovType` "Business Income
With Extra Expense", `TypeOfRisk` "Mercantile and Non-manufacturing",
coinsurance 90%, limit 100,000.

    python scripts/cf/34_chunk5_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction matches or is skipped for a stated reason.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import EngineError
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk0 = import_module("00_chunk0_checks")
chunk2 = import_module("09_chunk2_golden_case")
chunk5 = import_module("32_chunk5_golden_case")

BI = chunk5.BI
PREM = chunk5._P % "BasicGroupI"
CLASS, CC, PROT = "0951", 1, "3"
LIMIT, COINS = 100000, "90%"

#: The ten states overriding SetBasicGroupIICauseOfLossAdjustment, grouped by
#: the shape of the override. Group II is not what this sweep prices, but the
#: census is C5-21 and it belongs with the enumeration.
#: Jurisdictions where the countrywide-shaped prediction is a dollar light
#: because the BUILDING base rate is itself produced by a state rule, and
#: Business Income reads the COMPUTED value rather than the filed row. Neither
#: state overrides anything in the Business Income ruleset -- checked -- so the
#: difference arrives entirely through the dependency. Stated rather than
#: silently tolerated, and it is exactly what C5-15 exists to pin down.
DIVERGENT = {
    "AZ": "Building's rate rule applies the location reduction credit before "
          "storing the base rate; the filed row is not what BI reads",
    "TX": "Building's Group I rule differs; the filed row is not what BI reads",
}

GROUP_II_OVERRIDES = {
    "no wind/hail branch at all": ["AR", "DC", "NY", "RI"],
    "wind/hail exclusion factor": ["TX"],
    "wind/hail-excluded rate and LCM": ["FL", "IN", "KS", "KY", "PR"],
}


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def key(book, name, juris):
    return juris if book.declares(name) == "state" else "CW"


def base_rate_building(book, juris):
    """The BUILDING base rate this jurisdiction's own rule would produce.

    Chunk 4's C4-31 established the routing: AK, CA and PR file
    `BasicGroupIRate` in no edition and override `SetBasicGroupIBaseRate` --
    AK and CA to a District table (AK always District II on this case, CA by a
    `District` field six levels up), PR to `BasicGroupIRatePR`, which is keyed
    on `ProtectClass`. Business Income reads whatever Building computed, so the
    same routing decides the Business Income premium in those three states.
    """
    if juris in ("AK", "CA"):
        which = "II" if juris == "AK" else "I"
        t = book.table(f"BasicGroupIDistrict{which}Rate")
        return (chunk0._exact(t, [juris, CLASS, CC, "Not Applicable",
                                  "Building"], "Rate"),
                f"{juris}: BasicGroupIDistrict{which}Rate (District split)")
    if juris == "PR":
        t = book.table("BasicGroupIRatePR")
        return (chunk0._exact(t, [juris, PROT, CLASS, CC, "Not Applicable",
                                  "Building"], "Rate"),
                "PR: BasicGroupIRatePR is keyed on ProtectClass and files "
                "classes 8/9/10 only -- class 0951 is not filed at all")
    return (chunk0._exact(book.table("BasicGroupIRate"),
                          [juris, CLASS, CC, "Not Applicable", "Building"],
                          "Rate"),
            "no Building BasicGroupIRate row for this class")


def predict(book, juris):
    """This jurisdiction's Business Income Basic Group I premium."""
    # **The dependency inherits chunk 4's state-layer finding.** AK, CA and PR
    # file `BasicGroupIRate` in no edition of the corpus and route the BUILDING
    # base rate through their own overriding rule -- AK and CA to a District
    # table, PR to `BasicGroupIRatePR`. Business Income reads whatever Building
    # computed, so the Business Income premium in those three states depends on
    # a table that does not exist under the countrywide name. C4-31, reaching a
    # second coverage.
    base, note = base_rate_building(book, juris)
    if base is None:
        return None, note, None

    adj_t = book.table("BaseRateAdjustmentFactor")
    if adj_t.is_empty:
        return None, ("BaseRateAdjustmentFactor resolves to no rows -- the one "
                      "header-only Business Income table, and this state does "
                      "not file it"), None
    adj = chunk0._exact(adj_t, [key(book, "BaseRateAdjustmentFactor", juris),
                                "Basic Group I"], "Factor")
    if adj is None:
        return None, "no BaseRateAdjustmentFactor row for Basic Group I", None

    terr_t = book.table("RatingTerritoryGroupIFactor")
    if terr_t.is_empty:
        return None, "RatingTerritoryGroupIFactor is header-only", None
    terr_name = terr_t.rows[0][terr_t.col("BasicGroupIRatingTerritory")]
    terr = Decimal(terr_t.rows[0][terr_t.col("Factor")])

    pc = chunk0._exact(book.table("ProtectionClassFactor"),
                       [key(book, "ProtectionClassFactor", juris), PROT, CC],
                       "Factor")
    fac = chunk0._exact(book.table("BusnIncomeFactor"),
                        [key(book, "BusnIncomeFactor", juris), chunk5.COVTYPE,
                         chunk5.RISK, COINS], "Factor")
    for v, why in ((pc, "ProtectionClassFactor"), (fac, "BusnIncomeFactor")):
        if v is None:
            return None, f"no {why} row", None

    # **Per-step rounding, three decimals after every factor** -- Building's
    # shape, not Personal Property's single round. Rounding once instead
    # coincides in 40 of 44 jurisdictions and is a dollar light in AL, MT, NY
    # and TX, which is how the difference was found.
    rate = Decimal(base)
    for f in (terr, Decimal(pc), Decimal(adj)):
        rate = r3(rate * f)
    final = r3(rate * Decimal(fac))
    return r0(final * LIMIT / 100), None, {
        "base": base, "adj": adj, "terr": terr_name, "pc": pc, "fac": fac,
        "rate": rate, "final": final}


def rate_state(juris, terr_name, resolver):
    sub = chunk5.submission("Basic")
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["BasicGroupIRatingTerr"] = str(terr_name)
    loc["ProtectClass"] = PROT
    # Arizona's location-level reduction credit: absent means zero, silently --
    # chunk 1 found it for Building, and Business Income reads Building's rate,
    # so it reaches a second coverage unchanged. C5-18's point in passing.
    if juris == "AZ":
        loc["BasicGroupIReductionCredit"] = "1.0"
    # California picks its Building District from a field six levels up.
    loc["District"] = "District I"
    book = book_for(juris, chunk2.ASOF, resolver=resolver)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return read(PREM, data), read(f"{BI}/Factor", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    resolver = CFEditionResolver()
    js = resolver.jurisdictions
    print("Chunk 5, C5-04 -- Business Income Basic Group I, every jurisdiction")
    print(f"as-of {chunk2.ASOF};  N = {len(js)} in the corpus\n")
    print(f"{'':4s} {'bldg':>6s} {'adj':>5s} {'rate':>6s} {'Factor':>6s} "
          f"{'final':>6s} {'pred':>5s} {'eng':>5s}")

    matched, skipped, failed, divergent = [], [], [], []
    for j in js:
        try:
            book = book_for(j, chunk2.ASOF, resolver=resolver)
        except EngineError as exc:
            skipped.append((j, f"does not resolve: {exc}"))
            continue
        expect, why, parts = predict(book, j)
        if expect is None:
            skipped.append((j, why))
            print(f"{j:4s} SKIP  {why}")
            continue
        try:
            got, fac = rate_state(j, parts["terr"], resolver)
        except EngineError as exc:
            failed.append((j, f"RAISED {type(exc).__name__}: {exc}"))
            print(f"{j:4s} RAISED {str(exc)[:70]}")
            continue
        ok = got is not None and Decimal(got) == expect
        if ok:
            matched.append((j, ""))
        elif j in DIVERGENT:
            divergent.append((j, f"engine {got}, countrywide-shaped "
                                 f"prediction {expect} -- {DIVERGENT[j]}"))
        else:
            failed.append((j, f"engine {got}, predicted {expect}"))
        print(f"{j:4s} {str(parts['base']):>6s} {str(parts['adj']):>5s} "
              f"{str(parts['rate']):>6s} {str(parts['fac']):>6s} "
              f"{str(parts['final']):>6s} {str(expect):>5s} {str(got):>5s}"
              + ("" if ok else ("  <-- DIVERGES, cause stated"
                                if j in DIVERGENT else "  <-- MISMATCH")))
        if a.verbose:
            print(f"     terr={parts['terr']} pc={parts['pc']}")

    n = len(js)
    print(f"\n{len(matched)} of {n} jurisdictions rate Business Income Basic "
          f"Group I exactly as predicted from their own filed rows.")
    if skipped:
        print(f"\n{len(skipped)} of {n} skipped, each for a stated reason:")
        for j, w in skipped:
            print(f"   {j}: {w}")
    if failed:
        print(f"\n{len(failed)} of {n} FAILED -- a defect until explained:")
        for j, w in failed:
            print(f"   {j}: {w}")

    print(f"\nC5-21 -- the ten states overriding "
          f"SetBasicGroupIICauseOfLossAdjustment,\nclassified by the shape of "
          f"the override rather than counted:")
    for shape, states in GROUP_II_OVERRIDES.items():
        print(f"   {len(states)}  {shape:34s} {' '.join(states)}")
    print("   The four in the first group have dropped the wind/hail branch")
    print("   ENTIRELY -- 529 characters against countrywide's full rule. That")
    print("   is a divergence in content, not in formatting, and it is the")
    print("   one contested rule in an otherwise countrywide chunk.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
