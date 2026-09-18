#!/usr/bin/env python3
"""Settle the rounding mode -- find a case where the modes disagree, then ask ISO.

ISO declares `DecimalPlaces` on every rounding operator and **never declares a
MODE**, anywhere in either corpus. Half-up, half-even and truncate differ on
exactly the half-cent a rating engine meets constantly, so the engine cannot
avoid choosing. Half-up was directed as the working assumption.

Every case rated so far -- nine Property cases, 47 jurisdictions, and Oregon
against ISO's own service -- is **consistent with all three modes**, because not
one of them lands on a tie. A matching premium is not evidence about rounding
unless the case was built to produce one. So this builds one.

Method:

  1. Replicate the Basic Group I chain in plain arithmetic with the rounding
     mode as a parameter -- the same replication `03_enumerate_states.py` uses
     to predict, so it is independent of the interpreter.
  2. Sweep the inputs that move the arithmetic (limit, deductible, class) and
     keep every case where the three modes DISAGREE on the final premium.
  3. Confirm the best candidate through the real engine under each mode.
  4. Call ISO once. Whichever premium comes back names the mode.

    python scripts/cf/07_rounding_tie.py [--search-only] [--limit-max N]

This is the case GL's OI-70 has wanted since it was raised.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_DOWN
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

golden = import_module("01_golden_case")
chunk0 = import_module("00_chunk0_checks")
states = import_module("03_enumerate_states")

JURIS, ASOF, TERRITORY = "OR", golden.ASOF, "Portland"

MODES = {"ROUND_HALF_UP": ROUND_HALF_UP,
         "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
         "ROUND_DOWN": ROUND_DOWN}


def chain(mode, base, terr, pc, coins, loi, ded, limit):
    """The Basic Group I chain, with ISO's rounding nesting and one mode.

    Mirrors `CauseOfLoss_Building_RatingAlgorithms.md` step for step: every
    `rul:Product` carries its own `DecimalPlaces`, so rounding happens at each
    level of the nest rather than once at the end.
    """
    m = MODES[mode]

    def r3(x):
        return Decimal(x).quantize(Decimal("0.001"), rounding=m)

    def r0(x):
        return Decimal(x).quantize(Decimal("1"), rounding=m)

    rate = r3(r3(Decimal(base) * 1) * Decimal(terr) * Decimal(pc))
    col = r3(rate)
    adj = r3(r3(col * Decimal(coins)) * Decimal(loi))
    final = r3(r3(adj * 1) * Decimal(ded))
    return r0(final * Decimal(limit) / 100), final


def candidates(book, classes, limits, deductibles):
    """Every (class, limit, deductible) where the three modes disagree."""
    terr_t = book.rating_table("RatingTerritoryGroupIFactor")
    terr = next(r[terr_t.col("Factor")] for r in terr_t.rows
                if r[terr_t.col("BasicGroupIRatingTerritory")] == TERRITORY)
    pc = chunk0._exact(book.rating_table("ProtectionClassFactor"),
                       ["CW", states.PROT_CLASS, states.CONSTR_CODE], "Factor")
    coins = chunk0._exact(book.rating_table("CoinsuranceFactor"),
                          ["CW", states.COINS], "Factor")
    base_t = book.rating_table("BasicGroupIRate")
    loi_t = book.rating_table("BasicGroupILOIFactorBldg")
    ded_t = book.rating_table("DeductibleFactor")

    out = []
    for cls in classes:
        base = chunk0._exact(base_t, [JURIS, cls, states.CONSTR_CODE,
                                      "Not Applicable", "Building"], "Rate")
        if base is None:
            continue
        for limit in limits:
            loi = chunk0._banded(loi_t, ["CW"], states.CONSTR_CODE, limit,
                                 "Factor")
            if loi is None:
                continue
            for ded in deductibles:
                d = chunk0._banded(ded_t, [JURIS, ded], "Basic Group I",
                                   limit, "Factor")
                if d is None:
                    continue
                prem = {m: chain(m, base, terr, pc, coins, loi, d, limit)[0]
                        for m in MODES}
                if len(set(prem.values())) > 1:
                    out.append({"class": cls, "limit": limit, "ded": ded,
                                "base": base, "terr": terr, "pc": pc,
                                "coins": coins, "loi": loi, "dedf": d,
                                "premiums": prem})
    return out


def rate_engine(mode, cls, limit, ded):
    sub = golden.submission(limit, 0)
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["BasicGroupIRatingTerr"] = TERRITORY
    loc["ProtectClass"] = states.PROT_CLASS
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    st["ClassCode"] = cls
    st["Deductible"] = ded
    ip = Interpreter(book_for(JURIS, ASOF), rounding=mode, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict("MasterCFOR", sub)
    ip.run(data)
    return read(states.PREMIUM, data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--search-only", action="store_true")
    ap.add_argument("--limit-max", type=int, default=400000)
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    base_t = book.rating_table("BasicGroupIRate")
    classes = sorted({r[base_t.col("ClassCode")] for r in base_t.rows
                      if r[base_t.col("CovType")] == "Building"
                      and r[base_t.col("ConstructionCode")] == states.CONSTR_CODE})
    limits = list(range(50000, a.limit_max + 1, 2500))
    deds = ["500", "1,000", "2,500", "5,000"]
    print(f"Searching {len(classes)} classes x {len(limits)} limits x "
          f"{len(deds)} deductibles = "
          f"{len(classes) * len(limits) * len(deds):,} combinations "
          f"in {JURIS}/{TERRITORY}\n")

    found = candidates(book, classes, limits, deds)
    print(f"{len(found):,} combinations where the three modes DISAGREE\n")
    if not found:
        print("No discriminating case in this search space. Widen it.")
        return 1

    # Prefer a case where all three modes give three DIFFERENT answers -- one
    # call then names the mode outright instead of only halving the field.
    three_way = [c for c in found if len(set(c["premiums"].values())) == 3]
    pool = three_way or found
    print(f"{len(three_way):,} of those separate all THREE modes")

    # TWO cases, because a mode could in principle differ by SCALE. The chain
    # rounds to 3 decimals at every `rul:Product` in the rate build-up and to 0
    # at the premium, and a case that ties at one scale says nothing about the
    # other.
    #
    #   premium-tie  half-up and half-even agree on the RATE and differ only on
    #                the whole-dollar premium (0.077 x 500 = 38.5 exactly)
    #   rate-tie     they differ at a 3-DECIMAL step and the premium inherits it
    rate_ties = []
    for c in found:
        up = chain("ROUND_HALF_UP", c["base"], c["terr"], c["pc"], c["coins"],
                   c["loi"], c["dedf"], c["limit"])
        ev = chain("ROUND_HALF_EVEN", c["base"], c["terr"], c["pc"],
                   c["coins"], c["loi"], c["dedf"], c["limit"])
        if up[1] != ev[1] and up[0] != ev[0]:
            rate_ties.append(c)
    print(f"{len(rate_ties):,} of those tie at a 3-DECIMAL RATE step\n")

    picks = [("ties at the PREMIUM (0 dp)",
              min(pool, key=lambda c: (c["limit"], c["class"])))]
    if rate_ties:
        picks.append(("ties at a RATE step (3 dp)",
                      min(rate_ties, key=lambda c: (c["limit"], c["class"]))))

    for why, pick in picks:
        show(why, pick)

    if a.search_only:
        return 0

    return ask_iso(picks)


def show(why, pick):
    print(f"Chosen case -- {why}")
    print(f"   class {pick['class']}  construction Frame  {TERRITORY}  "
          f"protection class {states.PROT_CLASS}")
    print(f"   limit {pick['limit']:,}  deductible {pick['ded']}  "
          f"coinsurance {states.COINS}")
    print(f"   base={pick['base']} terr={pick['terr']} pc={pick['pc']} "
          f"coins={pick['coins']} loi={pick['loi']} ded={pick['dedf']}")
    print("\n   predicted premium, by rounding mode:")
    for m in MODES:
        prem, final = chain(m, pick["base"], pick["terr"], pick["pc"],
                            pick["coins"], pick["loi"], pick["dedf"],
                            pick["limit"])
        got = rate_engine(m, pick["class"], pick["limit"], pick["ded"])
        agree = "" if str(prem) == got else f"   <-- ENGINE SAYS {got}"
        print(f"      {m:16s} final rate {final}   premium ${prem}{agree}")

    print()


def ask_iso(picks):
    """One call per case. Whichever premium comes back names the mode."""
    scripts_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(scripts_dir))
    import raas as raas_mod

    raas_case = import_module("06_raas_newyork")
    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    verdicts = []
    for why, pick in picks:
        payload = raas_case.payload(JURIS, TERRITORY)
        st = (payload["body"]["CommercialProperty"][0]
              ["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructure"][0])
        st["ClassCode"] = pick["class"]
        st["Limit"] = pick["limit"]
        st["FullBldgValue"] = pick["limit"]
        st["Deductible"] = pick["ded"]

        print(f"Calling ISO -- {why}")
        try:
            resp = client.rate(payload)
        except raas_mod.RaaSError as exc:
            print(f"  REFUSED status={exc.status}: {exc.body[:400]}")
            return 2

        prem = [v for k, v in raas_case.find_premium(resp) if k == "Premium"]
        iso = Decimal(str(prem[0])) if prem else None
        winner = [m for m, v in pick["premiums"].items() if v == iso]
        print(f"  ISO returns {iso}  ->  "
              + (winner[0] if len(winner) == 1
                 else f"AMBIGUOUS {winner or 'no mode matches'}"))
        verdicts.append((why, iso, winner))

        out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
        out.mkdir(parents=True, exist_ok=True)
        tag = "premiumtie" if "PREMIUM" in why else "ratetie"
        (out / f"OR_{tag}_request.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        (out / f"OR_{tag}_response.json").write_text(
            json.dumps(resp, indent=2), encoding="utf-8")

    print("\n" + "=" * 64)
    modes = {w[0] for _, _, w in verdicts if len(w) == 1}
    if len(modes) == 1 and len(modes) == len(set(len(w) for _, _, w in verdicts)):
        mode = modes.pop()
        print(f"  ISO'S ROUNDING MODE IS {mode}, at BOTH scales --")
        print("  the 3-decimal rate steps and the whole-dollar premium.")
        return 0
    print(f"  Inconclusive or inconsistent: {verdicts}")
    print("  Do not pick a mode from this; widen the search instead.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
