#!/usr/bin/env python3
"""Chunk 2, gate point 3 -- every jurisdiction enumerated for Basic Group II.

Same discipline as chunk 1's sweep: each jurisdiction gets ITS OWN case, built
from its own filed rows, and the premium is **predicted before the engine
runs**. Rating 47 states and reporting that 47 numbers came out proves nothing;
the numbers have to be predicted.

Group II makes this harder than Group I, and more worth doing:

  * the territory is Group II's own field with its own scheme -- Oregon files
    one Group II territory and three Group I ones;
  * the rate is keyed on a construction SYMBOL, resolved from construction type
    and storey count;
  * `BCEGFactor` is keyed on the Group II territory as well as the grade, so
    the grade that exists varies by state;
  * **`BasicGroupIIRate` is header-only countrywide**, so every one of these
    rates comes from a state filing or there is no rate at all.

    python scripts/cf/11_chunk2_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction either matches its prediction or is skipped for
a stated, enumerated reason.
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

golden = import_module("01_golden_case")
chunk0 = import_module("00_chunk0_checks")
chunk2 = import_module("09_chunk2_golden_case")

LIMIT, DEDUCTIBLE, COINS = 100000, "1,000", "90%"
CONSTRUCTION, STORIES = "Frame", "1-3"


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def inputs_for(book, juris):
    """This state's own Group II case: territory, symbol, BCEG grade."""
    sym_t = book.table("BasicGroupIIConstructionSymbol")
    if sym_t.is_empty:
        return None, "BasicGroupIIConstructionSymbol resolves to no rows"
    symbol = chunk0._exact(sym_t, [juris, CONSTRUCTION, STORIES], "Symbol") \
        or chunk0._exact(sym_t, ["CW", CONSTRUCTION, STORIES], "Symbol")
    if symbol is None:
        return None, f"no construction symbol for {CONSTRUCTION}/{STORIES}"

    rate_t = book.table("BasicGroupIIRate")
    if rate_t.is_empty:
        return None, "BasicGroupIIRate is header-only in both layers"
    hit = next((r for r in rate_t.rows
                if str(r[rate_t.col("BasicGroupIISymbol")]) == str(symbol)
                and str(r[rate_t.col("CovType")]) == "Bldg"), None)
    if hit is None:
        return None, f"no BasicGroupIIRate row for symbol {symbol}/Bldg"
    terr = hit[rate_t.col("BasicGroupIIRatingTerr")]
    base = hit[rate_t.col("Rate")]

    bceg_t = book.table("BCEGFactor")
    grade, bceg = None, Decimal(1)
    if not bceg_t.is_empty:
        row = next((r for r in bceg_t.rows
                    if str(r[bceg_t.col("BasicGroupIIRatingTerr")]) == str(terr)),
                   None)
        if row is not None:
            grade = row[bceg_t.col("BldgCodeEffectivenessGrade2")]
            bceg = row[bceg_t.col("Factor")]
    if grade is None:
        return None, "no BCEGFactor row for this territory (absent BCEG = 0)"
    return {"symbol": symbol, "terr": terr, "base": base,
            "grade": grade, "bceg": bceg}, None


def predict(book, juris, inp):
    coins = chunk0._exact(book.table("CoinsuranceFactor"),
                          [juris if book.declares("CoinsuranceFactor") == "state"
                           else "CW", COINS], "Factor")
    if coins is None:
        return None, f"no CoinsuranceFactor row for {COINS}"
    loi_t = book.table("BasicGroupIILOIFactorBldg")
    loi = chunk0._banded(
        loi_t, [juris if book.declares("BasicGroupIILOIFactorBldg") == "state"
                else "CW"], None, LIMIT, "Factor")
    if loi is None:
        return None, "no BasicGroupIILOIFactorBldg band for the limit"
    ded = chunk0._banded(
        book.table("DeductibleFactor"),
        [juris if book.declares("DeductibleFactor") == "state" else "CW",
         DEDUCTIBLE], "Basic Group II", LIMIT, "Factor")
    if ded is None:
        return None, f"no DeductibleFactor band for {DEDUCTIBLE}/Basic Group II"

    # Step 4 is a FIVE-DEEP left fold, rounding to 3dp after every factor --
    # not Group I's single Product with three children. LossCostMultiplier,
    # numeric value and both roof-surfacing factors are 1.0 here.
    rate = Decimal(inp["base"])
    for f in (1, 1, 1, 1, Decimal(inp["bceg"])):
        rate = r3(rate * Decimal(f))
    coladj = r3(rate * 1)                       # x StdPropPolGroupIIFactor
    adjusted = r3(r3(coladj * Decimal(coins)) * Decimal(loi))
    final = r3(r3(adjusted * 1) * Decimal(ded))
    return r0(final * Decimal(LIMIT) / 100), {
        "coins": coins, "loi": loi, "ded": ded, "rate": rate, "final": final}


def rate_state(juris, inp, resolver):
    sub = chunk2.submission()
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["BasicGroupIIRatingTerr"] = str(inp["terr"])
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    st["BCEG"] = str(inp["grade"])
    # **39 of 47 jurisdictions override `SetBasicGroupIIRate`, and 36 of those
    # gate it on `RatingTypeBasicGroupII` -- a Group II-specific rating type
    # countrywide does not have.** Leave it out and those 36 price Group II at
    # zero with nothing raised: the base rate resolves, every factor resolves,
    # and the rate is 0 because the state's `Choose` matched no branch.
    #
    # The countrywide rule has no such gate, so setting it is inert for the
    # other 8. Fourth member of the absent-means-zero family, after Arizona's
    # BasicGroupIReductionCredit, an unrecognised ConstructionType, and BCEG.
    st["RatingTypeBasicGroupII"] = "Class"
    st["Deductible"] = DEDUCTIBLE
    st["Coinsurance"] = COINS
    book = book_for(juris, chunk2.ASOF, resolver=resolver)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return read(chunk2.BGII, data), read(f"{chunk2.STRUCT}/FinalBasicGroupIIRate",
                                         data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    resolver = CFEditionResolver()
    js = resolver.jurisdictions
    print("Chunk 2, gate point 3 -- Basic Group II across every jurisdiction")
    print(f"as-of {chunk2.ASOF};  N = {len(js)} in the corpus\n")
    print(f"{'':4s} {'terr (own BGII scheme)':26s} {'sym':>4s} {'base':>6s} "
          f"{'bceg':>5s} {'final':>6s} {'pred':>5s} {'engine':>6s}")

    matched, skipped, failed = [], [], []
    for j in js:
        try:
            book = book_for(j, chunk2.ASOF, resolver=resolver)
        except EngineError as exc:
            skipped.append((j, f"does not resolve: {exc}"))
            continue
        inp, why = inputs_for(book, j)
        if inp is None:
            skipped.append((j, why))
            print(f"{j:4s} SKIP  {why}")
            continue
        expect, parts = predict(book, j, inp)
        if expect is None:
            skipped.append((j, parts))
            print(f"{j:4s} SKIP  {parts}")
            continue
        try:
            got, final = rate_state(j, inp, resolver)
        except EngineError as exc:
            failed.append((j, f"RAISED {type(exc).__name__}: {exc}"))
            print(f"{j:4s} RAISED {exc}")
            continue
        ok = got is not None and Decimal(got) == expect
        (matched if ok else failed).append(
            (j, "" if ok else f"engine {got}, predicted {expect}"))
        print(f"{j:4s} {str(inp['terr'])[:26]:26s} {str(inp['symbol']):>4s} "
              f"{str(inp['base']):>6s} {str(inp['bceg']):>5s} {final:>6s} "
              f"{str(expect):>5s} {str(got):>6s}"
              + ("" if ok else "   <-- MISMATCH"))
        if a.verbose:
            print(f"     grade={inp['grade']} coins={parts['coins']} "
                  f"loi={parts['loi']} ded={parts['ded']}")

    n = len(js)
    print(f"\n{len(matched)} of {n} jurisdictions rate Basic Group II exactly "
          f"as predicted from their own filed rows.")
    if skipped:
        print(f"\n{len(skipped)} of {n} skipped, each for a stated reason:")
        for j, why in skipped:
            print(f"   {j}: {why}")
    if failed:
        print(f"\n{len(failed)} of {n} FAILED -- a defect until explained:")
        for j, why in failed:
            print(f"   {j}: {why}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
