#!/usr/bin/env python3
"""Chunk 11 Group B -- the four sub-coverages, C11-16 to C11-20.

Every expected value is copied from `docs/CF-CHUNK11-GROUP-B.md`, written
before this ran. Each scenario is chunk 11's golden Leasehold Interest
structure (`114_chunk11_golden_case.py`) with sub-coverage amounts, a cause
of loss, a Theft Exclusion record or an EQ election added.

  S1-S5  C11-16 (and the other three in the same runs): every sub-coverage
         reaches a nonzero premium on each form it can be on -- except
         Special without a Theft Exclusion (S4), predicted $0 by ISO's own
         rules.
  S6     C11-17: Bonus Payments alone, with no interest rate -- its net is
         undiscounted, so it prices anyway.
  S7     C11-18: Improvements & Betterments alone.
  S8     C11-19: Prepaid Rent alone.
  S9     C11-18: a `CovType = Improvements and Betterments` structure
         deletes the LI record.
  S1     C11-20: the total is a sum, and nothing is rated off it.

    python scripts/cf/116_chunk11_groupB_subcoverages.py

Exit 0 means every scenario matched.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.tree import read

g = import_module("114_chunk11_golden_case")
LI, cell, SUBCOV, FORMS = g.LI, g.cell, g.SUBCOV, g.FORMS

AMOUNTS = {
    "TenantsLease": ("TenantsGrossLeaseholdInt", "1500"),
    "BonusPayments": ("BonusPaymentsMonthlyLeaseholdInt", "200"),
    "Improvements": ("ImprovementsAndBettermentsMonthly", "300"),
    "PrepaidRent": ("PrepaidRentMonthly", "400"),
}
NETS = {"TenantsLease": ("TenantsNetLeaseholdInt", "111958"),
        "BonusPayments": ("BonusPaymentsNetLeaseholdInt", "22800"),
        "Improvements": ("ImprovementsAndBettermentsNetLeaseholdInt", "34200"),
        "PrepaidRent": ("PrepaidRentNetLeaseholdInt", "45600")}
BASIC = {"TenantsLease": (268, 30), "BonusPayments": (54, 6),
         "Improvements": (82, 9), "PrepaidRent": (109, 12)}
BROAD = {"TenantsLease": 26, "BonusPayments": 5, "Improvements": 8, "PrepaidRent": 10}
SPECIAL = {"TenantsLease": 45, "BonusPayments": 9, "Improvements": 14, "PrepaidRent": 18}
EQ = {"TenantsLease": 10, "BonusPayments": 2, "Improvements": 3, "PrepaidRent": 4}


def build(subs, cause="Basic", theft_excl=False, eq=False, drop_interest=False,
          covtype=None):
    li = {k: v for k, v in g.LI_RECORD.items()
          if k not in ("TenantsGrossLeaseholdInt",)
          and not (drop_interest and k == "PercentInterest")}
    for s in subs:
        f, v = AMOUNTS[s]
        li[f] = v
    sub = g.submission(li=li)
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    st["CauseOfLoss"] = cause
    if covtype:
        # A priced structure type needs chunk 2's Limit and Coinsurance back;
        # without them its own coverage writes a null premium (first run).
        st["CovType"] = covtype
        st["Limit"] = "100000"
        st["Coinsurance"] = "90%"
    if theft_excl:
        st["CommercialPropertyTheftExclusionTable"] = {
            "CommercialPropertyTheftExclusion": [{}]}
    if eq:
        # Chunk 10's golden-case EQ inputs; BCEG stays chunk 2's "4".
        cp["EQSubLimitBlktIndicator"] = "No"
        loc["EQCauseOfLossForm"] = "Earthquake Form (CP 10 40)"
        loc["EQTerr"] = "1"
        loc["EQDeductibleTier"] = "1"
        st["EQCovIndicator"] = "Yes, Not Included in Blanket"
        st["EQClass"] = "A1"
        st["EQSprinklerLeakageOnly"] = "Not Applicable"
        st["SprinklerSystem"] = "None"
    return sub


def expected_grid(subs, cause, theft_excl, eq):
    """(on, premium) per cell, from the doc's tables."""
    out = {}
    for s in SUBCOV:
        active = s in subs
        for f in FORMS:
            on = active and (
                f in ("BasicGroupI", "BasicGroupII")
                or (f == "Broad" and cause == "Broad")
                or (f == "Special" and cause == "Special")
                or (f == "Earthquake" and eq))
            prem = 0
            if on:
                prem = {"BasicGroupI": BASIC[s][0], "BasicGroupII": BASIC[s][1],
                        "Broad": BROAD[s],
                        "Special": SPECIAL[s] if theft_excl else 0,
                        "Earthquake": EQ[s]}[f]
            out[(s, f)] = ("1" if on else "0", str(prem))
    return out


SCENARIOS = [
    # (id, task, label, kwargs, expected LI total, extra (path, value) checks)
    ("S1", "C11-16/20", "Basic, all four", dict(subs=SUBCOV), 570,
     [(LI + "/TotCoveredLeaseholdIntNet", "214558")]),
    ("S2", "C11-16", "Broad, all four", dict(subs=SUBCOV, cause="Broad"), 619,
     [(LI + "/BroadRate", "0.023")]),
    ("S3", "C11-16", "Special + Theft Exclusion",
     dict(subs=SUBCOV, cause="Special", theft_excl=True), 656,
     [(LI + "/SpecialRate", "0.047"), (LI + "/SpecialTheftExclusionFactor", "0.86"),
      (LI + "/SpecialCauseOfLossAdjustment", "0.040")]),
    ("S4", "C11-16", "Special, NO Theft Exclusion -> $0",
     dict(subs=SUBCOV, cause="Special"), 570,
     [(LI + "/SpecialRate", "0.047"), (LI + "/SpecialTheftExclusionFactor", "0.0"),
      (LI + "/SpecialCauseOfLossAdjustment", "0.0")]),
    ("S5", "C11-16", "Basic + EQ elected", dict(subs=SUBCOV, eq=True), 589,
     [(LI + "/EQCauseOfLossAdjustment", "0.009")]),
    ("S6", "C11-17", "Bonus only, no PercentInterest",
     dict(subs=["BonusPayments"], drop_interest=True), 60, []),
    ("S7", "C11-18", "Improvements only", dict(subs=["Improvements"]), 91, []),
    ("S8", "C11-19", "Prepaid Rent only", dict(subs=["PrepaidRent"]), 121, []),
]


def same(got, want: str) -> bool:
    try:
        return Decimal(str(got)) == Decimal(want)
    except Exception:
        return str(got) == want


def main() -> int:
    print(f"{book_for(g.JURIS, g.ASOF)}\n")
    ok = True
    for sid, task, label, kw, total, extra in SCENARIOS:
        subs = kw.get("subs")
        data, _ = g.run(build(**kw))
        bad = []
        want = expected_grid(subs, kw.get("cause", "Basic"),
                             kw.get("theft_excl", False), kw.get("eq", False))
        for (s, f), (won, wprem) in want.items():
            on = read(cell(s, f) + "/CoverageOnPolicyIndicator", data)
            prem = read(cell(s, f) + "/Premium", data)
            if on != won or not same(prem, wprem):
                bad.append(f"{s}/{f} got {on}/{prem} want {won}/{wprem}")
        for s in subs:
            f, w = NETS[s]
            got = read(f"{LI}/{f}", data)
            if not same(got, w):
                bad.append(f"{f}={got} want {w}")
        for path, w in extra:
            got = read(path, data)
            if not same(got, w):
                bad.append(f"{path.rsplit('/', 1)[-1]}={got} want {w}")
        got_total = read(LI + "/ErcCalculatedTotalPremium", data)
        if not same(got_total, str(total)):
            bad.append(f"LI total={got_total} want {total}")
        ok &= not bad
        print(f"  {sid} {task:9s} {label:36s} total {str(got_total):>5s}  "
              + ("MATCH" if not bad else "MISMATCH"))
        for b in bad:
            print(f"        - {b}")

    # S9: a CovType=Improvements and Betterments structure keeps no LI record.
    data, _ = g.run(build(subs=["Improvements"],
                          covtype="Improvements and Betterments"))
    kept = tree.select(LI, data)
    good = len(kept) == 0
    ok &= good
    print(f"  S9 C11-18    CovType 'Improvements and Betterments'   LI records "
          f"kept {len(kept)}  " + ("MATCH (deleted)" if good else "MISMATCH"))

    print()
    if ok:
        print("Group B matches: all four sub-coverages reach a premium on every "
              "form they can be on; three are undiscounted; each is rated on "
              "its own net; and Special without a Theft Exclusion is $0, as "
              "ISO's own rule predicts.")
        return 0
    print("MISMATCH -- compare against docs/CF-CHUNK11-GROUP-B.md.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
