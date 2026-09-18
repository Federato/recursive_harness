#!/usr/bin/env python3
"""Chunk 4, tasks C4-04 and C4-31 -- every jurisdiction, Contents Basic Group I.

Same discipline as chunks 1-3: each jurisdiction gets its own case, built from
its own filed rows, and **the premium is predicted before the engine runs**.

**C4-31 first, because it gates this sweep.** `BasicGroupIRate` is header-only
countrywide and **AK, CA and PR file it in NO edition of the corpus** --
enumerated across all 415 copies of that file, not inferred. Chunk 3's first
pass would have skipped them as unrateable; chunk 3's *finding* says look for
the overriding rule first. All three have one, and all three read a
differently-named table:

    AK   SetBasicGroupIBaseRate -> BasicGroupIDistrictIRate / ...IIRate
         District chosen by BasicGroupIRatingTerr ('020','040','050','100')
    CA   same two tables, but the District comes from a `District` field
         SIX levels up, valued 'District I' / 'District II'
    PR   BasicGroupIRatePR -- and it is keyed on **ProtectClass**, a
         protection-class dimension in the BASE RATE that no other
         jurisdiction has

So the same shape as chunk 3's Florida, three times over, on the largest rate
table in the corpus. **Three different district mechanisms for two districts**
is the part that could not have been guessed.

The case: class 0951, Frame, Protection Class 3, one Contents item at 100,000
on a 100,000 building, 90% coinsurance, 1,000 deductible.

    python scripts/cf/24_chunk4_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction matches its prediction or is skipped for a
stated, enumerated reason.
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
chunk4 = import_module("22_chunk4_golden_case")

PP = chunk4.PP
PREM = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium"

CLASS, CC, PROT = "0951", 1, "3"
LIMIT, DEDUCTIBLE, COINS = 100000, "1,000", "90%"
TOTAL = 200000          # building 100,000 + contents 100,000


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def key(book, name, juris):
    return juris if book.declares(name) == "state" else "CW"


def base_rate(book, juris):
    """This jurisdiction's own route to a Contents Basic Group I base rate.

    Four shapes, not one -- and only the first was in the plan.
    """
    if juris in ("AK", "CA"):
        # **The two states choose the district differently, and the choice is
        # not ours to make.** AK tests `BasicGroupIRatingTerr` against four
        # literal codes -- '020', '040', '050', '100' -- and takes District I
        # only for those; its only filed territory is `Entire State`, which is
        # none of them, so AK is always District II on this case. CA reads a
        # `District` field six levels up, which the submission supplies.
        which = "II" if juris == "AK" else "I"
        t = book.table(f"BasicGroupIDistrict{which}Rate")
        return (chunk0._exact(t, [juris, CLASS, CC, "Not Applicable",
                                  "PersProp"], "Rate"),
                f"{juris}: BasicGroupIDistrict{which}Rate (District split)")
    if juris == "PR":
        # PR's own table files 83 class codes and protection classes 8, 9 and
        # 10 only. **Class 0951 is not among them** -- enumerated, not assumed,
        # so PR skips for a reason in ISO's content rather than in our reading.
        t = book.table("BasicGroupIRatePR")
        return (chunk0._exact(t, [juris, PROT, CLASS, CC, "Not Applicable",
                                  "PersProp"], "Rate"),
                "PR: BasicGroupIRatePR is keyed on ProtectClass and files "
                "classes 8/9/10 only -- class 0951 is not filed at all")
    t = book.table("BasicGroupIRate")
    if t.is_empty:
        return None, "BasicGroupIRate resolves to no rows"
    return (chunk0._exact(t, [juris, CLASS, CC, "Not Applicable", "PersProp"],
                          "Rate"), None)


def predict(book, juris):
    base, note = base_rate(book, juris)
    if base is None:
        return None, note or "no base rate row", None

    terr_t = book.table("RatingTerritoryGroupIFactor")
    if terr_t.is_empty:
        return None, "RatingTerritoryGroupIFactor is header-only", None
    terr_name = terr_t.rows[0][terr_t.col("BasicGroupIRatingTerritory")]
    terr = Decimal(terr_t.rows[0][terr_t.col("Factor")])

    pc = chunk0._exact(book.table("ProtectionClassFactor"),
                       [key(book, "ProtectionClassFactor", juris), PROT, CC],
                       "Factor")
    co = chunk0._exact(book.table("CoinsuranceFactor"),
                       [key(book, "CoinsuranceFactor", juris), COINS], "Factor")
    loi = chunk0._banded(book.table("BasicGroupILOIFactorPersProp"),
                         [key(book, "BasicGroupILOIFactorPersProp", juris), CC],
                         None, LIMIT, "Factor")
    ded = chunk0._banded(book.table("DeductibleFactor"),
                         [key(book, "DeductibleFactor", juris), DEDUCTIBLE],
                         "Basic Group I", TOTAL, "Factor")
    for v, why in ((pc, "ProtectionClassFactor"), (co, "CoinsuranceFactor"),
                   (loi, "BasicGroupILOIFactorPersProp"),
                   (ded, "DeductibleFactor")):
        if v is None:
            return None, f"no {why} row", None

    # PP rounds ONCE per rate step, where Building rounds at every Product --
    # chunk 4's golden case found that. And the adjusted rate applies
    # coinsurance BEFORE the limit factor, not after.
    rate = r3(Decimal(base) * 1 * Decimal(pc) * terr)
    adjusted = r3(r3(rate * Decimal(co)) * Decimal(loi))
    final = r3(r3(adjusted * 1) * Decimal(ded))
    return r0(final * LIMIT / 100), note, {
        "base": base, "terr": terr_name, "pc": pc, "loi": loi, "ded": ded,
        "final": final}


def rate_state(juris, terr_name, resolver):
    sub = chunk4.submission("Basic")
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["BasicGroupIRatingTerr"] = str(terr_name)
    loc["ProtectClass"] = PROT
    # AK picks its district from the territory; CA from a `District` field six
    # levels up. Supplying both is inert everywhere else.
    loc["District"] = "District I"
    # Arizona's `SetBasicGroupIRate` override multiplies by a location-level
    # `BasicGroupIReductionCredit` that the countrywide formula has no term
    # for, read through `FirstValue FromConstant="0.0"`. **Absent means zero**,
    # silently -- chunk 1 found it for Building, and it applies to Contents
    # unchanged. Supplied here for the same reason chunk 1's sweep supplies it.
    if juris == "AZ":
        loc["BasicGroupIReductionCredit"] = "1.0"
    book = book_for(juris, chunk2.ASOF, resolver=resolver)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return read(PREM, data), read(f"{PP}/BasicGroupIBaseRate", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    resolver = CFEditionResolver()
    js = resolver.jurisdictions
    print("Chunk 4, C4-04 -- Contents Basic Group I across every jurisdiction")
    print(f"as-of {chunk2.ASOF};  N = {len(js)} in the corpus\n")
    print(f"{'':4s} {'base':>6s} {'final':>6s} {'pred':>5s} {'eng':>5s}   notes")

    matched, skipped, failed = [], [], []
    for j in js:
        try:
            book = book_for(j, chunk2.ASOF, resolver=resolver)
        except EngineError as exc:
            skipped.append((j, f"does not resolve: {exc}"))
            continue
        expect, note, parts = predict(book, j)
        if expect is None:
            skipped.append((j, note))
            print(f"{j:4s} SKIP  {note}")
            continue
        try:
            got, base = rate_state(j, parts["terr"], resolver)
        except EngineError as exc:
            failed.append((j, f"RAISED {type(exc).__name__}: {exc}"))
            print(f"{j:4s} RAISED {str(exc)[:70]}")
            continue
        ok = got is not None and Decimal(got) == expect
        (matched if ok else failed).append(
            (j, "" if ok else f"engine {got}, predicted {expect}"))
        print(f"{j:4s} {str(parts['base']):>6s} {str(parts['final']):>6s} "
              f"{str(expect):>5s} {str(got):>5s}"
              + ("" if ok else "  <-- MISMATCH")
              + (f"   {note}" if note else ""))
        if a.verbose:
            print(f"     terr={parts['terr']} pc={parts['pc']} "
                  f"loi={parts['loi']} ded={parts['ded']} engine base={base}")

    n = len(js)
    print(f"\n{len(matched)} of {n} jurisdictions rate Contents Basic Group I "
          f"exactly as predicted from their own filed rows.")
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
