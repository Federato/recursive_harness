#!/usr/bin/env python3
"""Chunk 12, C12-11 -- the Ordinance or Law golden case.

Specified in `docs/CF-CHUNK12-ORDINANCE-OR-LAW.md`, derivation written BEFORE
this ran. Chunk 2's Oregon building (ISO-confirmed $261 + $32) plus one
`CommercialPropertyOrdinanceOrLawCoverage` record:

    CovType "Coverages A and B & C Separate", CovB demolition 20,000,
    CovC increased construction 30,000, PostLossOrdinanceOrLawOption "No".

    Cov A  BGI  round3((1.15 x 1.0 - 1) x 0.261) = 0.039 x 1,000          $39
    Cov A  BGII round3(0.15 x 0.032) = 0.005 x 1,000, x cyber 0.995        $5
    Cov B  BGI  0.239 x 1.0 -> x1.172 = 0.280 -> x0.98 x1.0 = 0.274 x 200  $55
    Cov B  BGII 0.027 -> x1.266 = 0.034 -> x0.98 = 0.033 x 200, x 0.995    $7
    Cov C  BGI  0.274 x 300                                                $82
    Cov C  BGII 0.033 x 300 = 9.9, x 0.995                                 $10
    Broad, Special, Earthquake cells                                       $0
    Ordinance or Law total                                                 $198

Coverage A is priced off the building's FINAL rate and FULL limit (an
increase on the building premium); B and C off the building's cause-of-loss
adjustment with the LOI and deductible re-applied, on their own limits.

    python scripts/cf/130_chunk12_ordinance_golden_case.py [--trace]
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
chunk2 = g.chunk2
JURIS, ASOF = g.JURIS, g.ASOF
STRUCT = g.STRUCT
PFX = "CommercialPropertyOrdinanceOrLawCoverage"
OL = STRUCT + f"/{PFX}Table/{PFX}"
COVS = ["CovA", "CovB", "CovC", "CovBAndC"]
FORMS = g.FORMS

RECORD = {
    "CovType": "Coverages A and B & C Separate",
    "CovBDemolitionLimit": "20000",
    "CovCIncreasedConstructionLimit": "30000",
    "PostLossOrdinanceOrLawOption": "No",
}


def cell(cov: str, form: str) -> str:
    return f"{OL}/CommercialPropertyOrdinanceOrLaw{cov}Coverage{form}Coverage"


def submission(record: dict | None = None, structure: dict | None = None) -> dict:
    sub = chunk2.submission()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    st = (cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
          ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    # CP 04 05 Coverage C requires Replacement Cost valuation (a filed
    # DoMessage); the domain-correct value, so the case carries no avoidable error.
    st["ValuationType"] = "Replacement Cost"
    st.update(structure or {})
    st[f"{PFX}Table"] = {PFX: [dict(RECORD if record is None else record)]}
    return sub


def run(sub, trace=False, juris=JURIS):
    return g.run(sub, trace, juris)


CHECKS = [
    ("PostLossFactor", OL + "/PostLossFactor", "1.0"),
    ("Cov A Factor", OL + "/CommercialPropertyOrdinanceOrLawCovACoverage/Factor", "1.15"),
    ("building LimitToUse", STRUCT + "/LimitToUse", "100000"),
    ("building FinalBasicGroupIRate", STRUCT + "/FinalBasicGroupIRate", "0.261"),
    ("building FinalBasicGroupIIRate", STRUCT + "/FinalBasicGroupIIRate", "0.032"),
    ("Cov A BGI", cell("CovA", "BasicGroupI") + "/Premium", "39"),
    ("Cov A BGII", cell("CovA", "BasicGroupII") + "/Premium", "5"),
    ("Cov B BGI", cell("CovB", "BasicGroupI") + "/Premium", "55"),
    ("Cov B BGII", cell("CovB", "BasicGroupII") + "/Premium", "7"),
    ("Cov C BGI", cell("CovC", "BasicGroupI") + "/Premium", "82"),
    ("Cov C BGII", cell("CovC", "BasicGroupII") + "/Premium", "10"),
    ("Cov B+C BGI (not this CovType)", cell("CovBAndC", "BasicGroupI") + "/CoverageOnPolicyIndicator", "0"),
    ("OL total", OL + "/ErcCalculatedTotalPremium", "198"),
    ("Building BGI unmoved", chunk2.BGI, "261"),
    ("Building BGII unmoved", chunk2.BGII, "32"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    print(f"{book_for(JURIS, ASOF)}\n")
    data, ip = run(submission(), a.trace)
    ok = True
    for label, path, want in CHECKS:
        got = read(path, data)
        good = g.num_eq(got, want)
        ok &= good
        print(f"  {label:34s} = {str(got):>10s}   want {want:>8s}  {'ok' if good else 'MISMATCH'}")
    print(f"\n  messages ({len(set(ip.messages))}): {sorted(set(ip.messages))}")
    if a.trace:
        print(ip.trace_text())
    print("\nALL MATCH" if ok else "\nMISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
