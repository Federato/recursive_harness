#!/usr/bin/env python3
"""Chunk 12, C12-35 -- the Dependent Properties golden case (CP 15 08), and its
live-ISO cases (the family has NO ISO fixture: C12-40 rests on these).

Derivation written BEFORE this ran. Chunk 5's Oregon Business Income (Basic,
Limit 100,000, ISO-confirmed $112 + $13) plus one Broad-form record with one
dependent property:

    BasicGroupIRate 0.200 / BasicGroupIIRate 0.030   SUBMITTED: the dependent
                                                      property's own rates
    NatureOfDependency "Not the Only Readily Available Source..."  -> 0.4
    no secondary location                                          -> 1.0

    BGI   round3(round3(0.2 x LCM 1.0) x 0.4) = 0.080 -> max over details 0.080
          round3(0.080 x 1.0) x BI LimitToUse 100,000/100 = 80            $80
    BGII  round3(0.03 x 0.4) = 0.012 x 1,000 = 12, x cyber 0.995 = 11.94  $12

The rate is taken from the dependent property, not the insured's own building;
the exposure is the insured's Business Income limit.

    python scripts/cf/141_chunk12_dependent_golden_case.py [--trace]
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
JURIS, ASOF = g.JURIS, g.ASOF

P = "CommercialProperty"
BF = f"{P}BusinessIncomeFromDependentPropertiesBroadForm"
LF = f"{P}BusinessIncomeFromDependentPropertiesLimitedForm"
EE = f"{P}ExtraExpenseFromDependentProperties"
INTL = f"{P}BusnIncomeFromDependentPropertiesLimitedInternationalCov"
BFP = f"{c5.BI}/{BF}Table/{BF}"
NOT_ONLY = "Not the Only Readily Available Source, Manufacturer or Outlet of Product"
ONLY = "Only Readily Available Source, Manufacturer or Outlet of Product"

DETAIL = {"BasicGroupIRate": "0.2", "BasicGroupIIRate": "0.03", "ConstructionType": "Frame",
          "NatureOfDependency": NOT_ONLY, "SecondaryContributingLocation": "No",
          "SecondaryRecipientLocation": "No"}


def submission(key=BF, record=None, details=None, col="Basic"):
    sub = c5.submission(col)
    bi = gates.structure(sub)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
    rec = dict(record or {})
    if details is not False:
        rec[f"{key}DetailTable"] = {f"{key}Detail": details if details is not None else [dict(DETAIL)]}
    bi[f"{key}Table"] = {key: [rec]}
    return sub


CHECKS = [
    ("detail NatureOfDependentPropFactor", f"{BFP}/{BF}DetailTable/{BF}Detail/NatureOfDependentPropFactor", "0.4"),
    ("detail AdjustedBasicGroupIRate", f"{BFP}/{BF}DetailTable/{BF}Detail/AdjustedBasicGroupIRate", "0.08"),
    ("record BasicGroupIRate (max)", BFP + "/BasicGroupIRate", "0.08"),
    ("SecondaryLocationDependenciesFactor", BFP + "/SecondaryLocationDependenciesFactor", "1"),
    ("BGI premium", f"{BFP}/{BF}BasicGroupICoverage/Premium", "80"),
    ("BGII premium", f"{BFP}/{BF}BasicGroupIICoverage/Premium", "12"),
    ("BI BGI unmoved", c5.BI + "/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium", "112"),
]


def RAAS_CASES():
    D = DETAIL
    return [
        ("P0", "golden: Broad form, one dependent property (ours $80 + $12)", submission()),
        ("P1", "Broad, the ONLY source (1.0)", submission(details=[dict(D, NatureOfDependency=ONLY)])),
        ("P2", "Broad, secondary contributing location (1.5)", submission(details=[dict(D, SecondaryContributingLocation="Yes")])),
        ("P3", "Broad, two dependent properties (the max rate wins)",
         submission(details=[dict(D), dict(D, BasicGroupIRate="0.5", NatureOfDependency=ONLY)])),
        ("P4", "Broad, dependent property rate absent", submission(details=[{k: v for k, v in D.items() if k != "BasicGroupIRate"}])),
        ("P5", "Broad, nature of dependency blank", submission(details=[dict(D, NatureOfDependency="")])),
        ("P6", "Limited form, detail limit 40,000", submission(LF, details=[dict(D, Limit="40000")])),
        ("P7", "Extra Expense, contributing locations 30,000",
         submission(EE, details=[dict(D, TypeOfDependentProp="Contributing Locations", ContributingLocationsLimit="30000")])),
        ("P8", "Limited International, manual premium 250", submission(INTL, record={"ManualPremium": "250"}, details=False)),
        ("P9", "Broad form on the Special form BI", submission(col="Special")),
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
        print(f"  {label:38s} = {str(got):>8s}   want {want:>6s}  {'ok' if good else 'MISMATCH'}")
    print(f"\n  messages: {sorted(set(ip.messages))}")
    if a.trace:
        print(ip.trace_text())
    print("\nALL MATCH" if ok else "\nMISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
