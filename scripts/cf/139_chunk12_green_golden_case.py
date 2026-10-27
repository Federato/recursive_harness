#!/usr/bin/env python3
"""Chunk 12, C12-29 -- the Green Upgrades golden case (CP 04 23), and its
live-ISO cases (the family has NO ISO fixture: C12-34 rests on these).

Derivation written BEFORE this ran. Chunk 2's Oregon building (adjusted
rates BGI 0.266 / BGII 0.033, limit 100,000) plus one Green Upgrades record:
Limit 20,000, IncreasedCostOfLossPct "20%", RelatedExpenses 10,000.

    Ratio = round3(round3(20,000 / 100,000) / 0.2) = 1.000 -> RatioToUse 1,000
    RateModificationFactor at 1,000                                    0.5

    BGI   green    round3(0.5 x 0.266) = 0.133 x 200 = 26.6           $27
          related  round3(0.266 x 0.1) = 0.027 x 100 = 2.7            $3   -> $30
    BGII  green    round3(0.5 x 0.033) = 0.017 x 200 = 3.4, x 0.995   $3
          related  round3(0.033 x 0.1) = 0.003 x 100 = 0.3            $0   -> $3
    Broad / Special / EQ: the building is Basic                               $0
    Total                                                                     $33

Priced off the building's ADJUSTED rate (before the deductible), the way
Ordinance or Law's tenants variant is.

    python scripts/cf/139_chunk12_green_golden_case.py [--trace]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g = import_module("127_chunk12_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
c5 = import_module("32_chunk5_golden_case")
JURIS, ASOF, STRUCT = g.JURIS, g.ASOF, g.STRUCT

K = "CommercialPropertyIncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtBldg"
KBI = "CommercialPropertyIncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtBusInc"
GU = f"{STRUCT}/{K}Table/{K}"
RECORD = {"Limit": "20000", "IncreasedCostOfLossPct": "20%", "RelatedExpenses": "10000"}


def cell(form):
    return f"{GU}/{K}{form}Cov"


def submission(record=None, structure=None):
    sub = g.chunk2.submission()
    st = gates.structure(sub)
    st.update(structure or {})
    st[f"{K}Table"] = {K: [dict(RECORD if record is None else record)]}
    return sub


def bi_submission(record):
    sub = c5.submission()
    bi = gates.structure(sub)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
    bi[f"{KBI}Table"] = {KBI: [dict(record)]}
    return sub


CHECKS = [
    ("IncreasedCostOfLossPercentConverted", GU + "/IncreasedCostOfLossPercentConverted", "0.2"),
    ("Ratio", GU + "/Ratio", "1"),
    ("RatioToUse", GU + "/RatioToUse", "1000"),
    ("RateModificationFactor", GU + "/RateModificationFactor", "0.5"),
    ("RelatedExpensesFactor", GU + "/RelatedExpensesFactor", "0.1"),
    ("building AdjustedBasicGroupIRate", STRUCT + "/AdjustedBasicGroupIRate", "0.266"),
    ("BGI green", cell("BasicGroupI") + "/GreenUpgradesPremium", "27"),
    ("BGI related", cell("BasicGroupI") + "/RelatedExpensesPremium", "3"),
    ("BGI cell", cell("BasicGroupI") + "/Premium", "30"),
    ("BGII cell", cell("BasicGroupII") + "/Premium", "3"),
    ("Green Upgrades total", GU + "/ErcCalculatedTotalPremium", "33"),
    ("Building BGI unmoved", g.chunk2.BGI, "261"),
]


def RAAS_CASES():
    R = RECORD
    return [
        ("G0", "golden: limit 20,000, 20%, related 10,000 (ours $30 + $3)", submission()),
        ("G1", "increased-cost % blank (ratio 0 -> factor 1.0)", submission({k: v for k, v in R.items() if k != "IncreasedCostOfLossPct"})),
        ("G2", "no related expenses", submission({k: v for k, v in R.items() if k != "RelatedExpenses"})),
        ("G3", "limit = the building's (ratio 5.0 -> 0.5)", submission(dict(R, Limit="100000"))),
        ("G4", "limit 5,000 and 50% (ratio 0.1 -> RatioToUse 100)", submission(dict(R, Limit="5000", IncreasedCostOfLossPct="50%"))),
        ("G5", "Green Upgrades limit absent (null skipped)", submission({k: v for k, v in R.items() if k != "Limit"})),
        ("G6", "Special building", submission(structure={"CauseOfLoss": "Special"})),
        ("G7", "on chunk 5's Business Income, 20%, 20,000, restoration 60 days",
         bi_submission({"Limit": "20000", "IncreasedCostOfLossPct": "20%", "PeriodOfRestoration": "60", "RelatedExpenses": "10000"})),
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
        print(f"  {label:36s} = {str(got):>8s}   want {want:>7s}  {'ok' if good else 'MISMATCH'}")
    print(f"\n  cells: { {f: read(cell(f) + '/Premium', data) for f in g.FORMS} }")
    print(f"  messages: {sorted(set(ip.messages))}")
    if a.trace:
        print(ip.trace_text())
    print("\nALL MATCH" if ok else "\nMISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
