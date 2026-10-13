#!/usr/bin/env python3
"""Gate point 3 -- every jurisdiction enumerated, not sampled.

The gate asks for "n of N" with N taken from the corpus, and for a negative
claim to say what was enumerated and how. Chunk 1's three golden cases prove the
mechanism in Oregon; this proves the corpus.

For every jurisdiction the corpus holds, this:

  1. resolves the book -- state package over its DECLARED parent;
  2. reports, per chain table, which layer owns it and how many rows it has,
     so a header-only table is visible as a fact rather than as a zero;
  3. builds that state's OWN equivalent of golden case A -- its own territory,
     read out of its own filed table rather than assumed -- and rates it;
  4. independently recomputes the expected premium from the resolved rows, and
     compares.

Step 4 is the point. Rating 47 states and reporting that 47 numbers came out is
not evidence of anything; the numbers have to be *predicted*. The prediction
here reads the same rows the engine reads but applies the rate chain directly,
so it is independent of the interpreter -- it would not follow the interpreter
into a wrong branch, a mis-ordered key or a dropped factor.

    python scripts/cf/03_enumerate_states.py [--asof YYYYMMDD] [--verbose]

Exit 0 when every jurisdiction either rates as predicted or is skipped for a
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

golden = import_module("01_golden_case")
chunk0 = import_module("00_chunk0_checks")

CLASS, CONSTRUCTION, CONSTR_CODE = "0951", "Frame", 1
PROT_CLASS, COINS, DEDUCTIBLE = "3", "90%", "1,000"
LIMIT = 100000

#: Rules on the chunk 1 chain, for the override census. A state that defines
#: any of these is not running the countrywide chain, and the prediction below
#: -- which implements the countrywide chain -- may legitimately disagree.
CHAIN_RULES = [
    "SetBasicGroupIBaseRate", "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment", "SetCoinsuranceFactor",
    "SetBasicGroupILOIFactor", "SetAdjustedBasicGroupIRate",
    "SetDeductibleFactorBasicGroupI", "SetFinalBasicGroupIRate",
    "SetProtectionClassFactor", "SetSprinklerLeakageExclNonSprinkleredBldgRate",
    "SetVacantBuildingRate", "SetSubStdConditionRate", "SetClassCodeToUse",
    "SetConstructionCode", "SetTotAmtInsurance", "SetPremium",
]
RULE_FILES = ["CommercialPropertyStructureRules",
              "CommercialPropertyStructureBuildingBasicGroupICoverageRules",
              "CommercialPropertyLocationRules"]

#: Inputs a state's own override REQUIRES that countrywide does not, with the
#: rule that demands it. Found by enumeration, not anticipated.
STATE_INPUTS = {
    # Arizona's `SetBasicGroupIRate` override multiplies the base rate by a
    # Location-level `BasicGroupIReductionCredit` that countrywide's formula
    # has no term for. It is read through `FirstValue FromConstant="0.0"`, so
    # ABSENT MEANS ZERO: without it every Arizona building prices at zero, and
    # nothing raises. That is a state-specific instance of gate point 4.
    "AZ": {"location": {"BasicGroupIReductionCredit": "1.0"}},
}

#: Jurisdictions that cannot rate for a reason in ISO's own content. Stated
#: here rather than discovered as a failure each run.
#:
#: **Empty since 2026-09-17.** New York was the only entry. It refused because
#: a rule filed in exactly one package in the corpus subtracts policy-level
#: `Premium` with no null guard, at a point where `Premium` is not yet
#: computed. ISO's own service rates that risk at $396, so the engine was what
#: needed to change -- and the change was made on evidence, not by
#: special-casing New York: `cf_engine.config.NULL_ARITHMETIC = "propagate"`.
#: New York now rates, and is predicted and checked like every other
#: jurisdiction below.
BLOCKED = {}

STRUCT = golden.CHAIN and ("CommercialPropertyTable/CommercialProperty/"
                          "CommercialPropertyLocationTable/"
                          "CommercialPropertyLocation/"
                          "CommercialPropertyStructureTable/"
                          "CommercialPropertyStructure")
PREMIUM = (STRUCT +
           "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium")


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def predict(book, juris):
    """The expected premium for this state's case A, from its own rows.

    Returns `(premium, parts)` or `(None, reason)`. Every lookup goes through
    the resolved book, so a state override wins exactly as it does in a rating.
    """
    def exact(name, keys, col):
        t = book.table(name)
        if t.is_empty:
            return None
        return chunk0._exact(t, keys, col)

    st = juris

    base = exact("BasicGroupIRate", [st, CLASS, CONSTR_CODE,
                                     "Not Applicable", "Building"], "Rate")
    if base is None:
        return None, f"no BasicGroupIRate row for class {CLASS}/{CONSTRUCTION}"

    terr_t = book.table("RatingTerritoryGroupIFactor")
    if terr_t.is_empty:
        return None, "RatingTerritoryGroupIFactor is header-only in both layers"
    terr_name = terr_t.rows[0][terr_t.col("BasicGroupIRatingTerritory")]
    terr = terr_t.rows[0][terr_t.col("Factor")]

    owner = "state" if book.declares("ProtectionClassFactor") == "state" else "CW"
    pc = exact("ProtectionClassFactor",
               [st if owner == "state" else "CW", PROT_CLASS, CONSTR_CODE],
               "Factor")
    if pc is None:
        return None, f"no ProtectionClassFactor row for class {PROT_CLASS}"

    co = exact("CoinsuranceFactor",
               [st if book.declares("CoinsuranceFactor") == "state" else "CW",
                COINS], "Factor")
    if co is None:
        return None, f"no CoinsuranceFactor row for {COINS}"

    loi_t = book.table("BasicGroupILOIFactorBldg")
    loi_state = book.declares("BasicGroupILOIFactorBldg") == "state"
    loi = chunk0._banded(loi_t, [st if loi_state else "CW"], CONSTR_CODE,
                         LIMIT, "Factor")
    if loi is None:
        return None, "no BasicGroupILOIFactorBldg band for the limit"

    ded_t = book.table("DeductibleFactor")
    ded_state = book.declares("DeductibleFactor") == "state"
    ded = chunk0._banded(ded_t, [st if ded_state else "CW", DEDUCTIBLE],
                         "Basic Group I", LIMIT, "Factor")
    if ded is None:
        return None, f"no DeductibleFactor band for a {DEDUCTIBLE} deductible"

    # The rate chain, with ISO's own rounding nesting (see the golden case doc).
    rate = r3(r3(Decimal(base) * 1) * Decimal(terr) * Decimal(pc))
    col = r3(rate)
    adj = r3(r3(col * Decimal(co)) * Decimal(loi))
    final = r3(r3(adj * 1) * Decimal(ded))
    prem = r0(final * Decimal(LIMIT) / 100)
    return prem, {"terr_name": terr_name, "base": base, "terr": terr, "pc": pc,
                  "coins": co, "loi": loi, "ded": ded, "rate": rate,
                  "final": final}


def overrides(book) -> list:
    """Which chunk 1 chain rules this state package defines for itself."""
    found = set()
    for f in RULE_FILES:
        p = book.state.package.content / "Rules" / f"{f}.Rule.xml"
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8-sig", errors="replace")
        found |= {r for r in CHAIN_RULES if f'Rule Name="{r}"' in txt}
    return sorted(found)


def rate_state(juris, asof, terr_name, resolver=None):
    sub = golden.submission(LIMIT, 0)
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["BasicGroupIRatingTerr"] = terr_name
    loc["ProtectClass"] = PROT_CLASS
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    st["ClassCode"] = CLASS
    st["ConstructionType"] = CONSTRUCTION
    st["Coinsurance"] = COINS
    st["Deductible"] = DEDUCTIBLE

    extra = STATE_INPUTS.get(juris, {})
    loc.update(extra.get("location", {}))
    st.update(extra.get("structure", {}))

    book = book_for(juris, asof, resolver=resolver)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return read(PREMIUM, data), read(f"{STRUCT}/FinalBasicGroupIRate", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default=golden.ASOF)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    resolver = CFEditionResolver()
    jurisdictions = resolver.jurisdictions
    print(f"Property chunk 1 -- gate point 3, every jurisdiction enumerated")
    print(f"as-of {a.asof};  N = {len(jurisdictions)} jurisdictions in the "
          f"corpus, {len(resolver.packages)} packages\n")

    print(f"{'':4s} {'package':22s} {'terr (own table)':22s} "
          f"{'final':>7s} {'pred':>6s} {'engine':>7s}  overrides")
    matched, skipped, failed, blocked = [], [], [], []
    override_census = {}
    for j in jurisdictions:
        try:
            book = book_for(j, a.asof, resolver=resolver)
        except EngineError as exc:
            skipped.append((j, f"does not resolve: {exc}"))
            print(f"{j:4s} -- does not resolve")
            continue

        ov = overrides(book)
        if ov:
            override_census[j] = ov

        if j in BLOCKED:
            blocked.append((j, BLOCKED[j]))
            print(f"{j:4s} {book.state.pkg_id:22s} BLOCKED by a filed state rule "
                  f"-- see below")
            continue

        expect, parts = predict(book, j)
        if expect is None:
            skipped.append((j, parts))
            print(f"{j:4s} {book.state.pkg_id:22s} SKIP  {parts}")
            continue
        try:
            got, final = rate_state(j, a.asof, parts["terr_name"], resolver)
        except EngineError as exc:
            failed.append((j, f"RAISED {type(exc).__name__}: {exc}"))
            print(f"{j:4s} {book.state.pkg_id:22s} RAISED {exc}")
            continue

        ok = got is not None and Decimal(got) == expect
        (matched if ok else failed).append(
            (j, "" if ok else f"engine {got}, predicted {expect}"))
        print(f"{j:4s} {book.state.pkg_id:22s} {parts['terr_name'][:22]:22s} "
              f"{final:>7s} {str(expect):>6s} {str(got):>7s} "
              f"{'' if ok else '  <-- MISMATCH'}  {len(ov) or ''}")
        if a.verbose:
            print(f"     base={parts['base']} terr={parts['terr']} "
                  f"pc={parts['pc']} coins={parts['coins']} loi={parts['loi']} "
                  f"ded={parts['ded']}")

    n = len(jurisdictions)
    print(f"\n{len(matched)} of {n} jurisdictions rate exactly as predicted "
          f"from their own filed rows.")
    if skipped:
        print(f"\n{len(skipped)} of {n} skipped, each for a stated reason "
              f"(facts about the corpus, not failures):")
        for j, why in skipped:
            print(f"   {j}: {why}")
    if blocked:
        print(f"\n{len(blocked)} of {n} BLOCKED by ISO's own content:")
        for j, why in blocked:
            print(f"   {j}: {why}\n")
    if failed:
        print(f"\n{len(failed)} of {n} FAILED -- unexplained, and a defect "
              f"until explained:")
        for j, why in failed:
            print(f"   {j}: {why}")

    # The override census. Reported whether or not anything failed, because
    # "42 states agreed with the countrywide formula" is only meaningful
    # alongside "and 18 of them do not run the countrywide chain".
    print(f"\n{len(override_census)} of {n} jurisdictions override at least one "
          f"chunk 1 chain rule:")
    for j, rules in sorted(override_census.items()):
        print(f"   {j}: {', '.join(rules)}")
    print("\n   An override that agrees with the countrywide prediction is not")
    print("   a no-op -- it agrees FOR THIS RISK. A different class, limit or")
    print("   election may reach the branch that differs. This census is the")
    print("   population chunk 2 and every later chunk have to re-ask.")

    print(f"\nN comes from the corpus -- {n} jurisdiction codes discovered by "
          f"walking it, not from a list.")
    print("Absent from the corpus entirely, and so not in N: HI, ID, LA, MS, WA.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
