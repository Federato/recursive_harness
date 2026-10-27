#!/usr/bin/env python3
"""Chunk 12, C12-17 -- the Utility Services golden case, both halves.

Specified in `docs/CF-CHUNK12-UTILITY-SERVICES.md`, derivation written BEFORE
this ran.

DIRECT DAMAGE (CP 04 17) on chunk 2's Oregon building ($261 + $32): one
`UtilityServicesDirectDamageBldg` record, one Detail: Public Utilities, Water
Supply (no overhead lines), Limit 40,000, CauseOfLoss Basic.

    BGI   round3(0.038 x LCM 1.0) + 0 overhead = 0.038;  x 400 = 15.2   $15
    BGII  0.011 x 400 = 4.4 -> 4;  x cyber 0.995 = 3.98                  $4
    Broad / Special / EQ: not elected                                    $0

TIME ELEMENT (CP 15 45) on chunk 5's Business Income risk (BI $112 + $13):
one `UtilityServicesTimeElement` record, one Detail: Public Utilities, Water
Supply, Limit 40,000, WaitingPeriod "72 hours" (factor 1.0).

    BGI   0.022 x 1.0 x 400 = 8.8                                        $9
    BGII  0.011 x 1.0 x 400 = 4.4                                        $4

The rates are the family's OWN tables, not a slice of the building's rate
(C12-04): Utility Services never reads the core chain's rate.

    python scripts/cf/133_chunk12_utility_golden_case.py [--trace]
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g = import_module("127_chunk12_golden_case")
chunk2 = g.chunk2
chunk5 = import_module("32_chunk5_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
JURIS, ASOF, STRUCT = g.JURIS, g.ASOF, g.STRUCT
FORMS = g.FORMS

DD = "CommercialPropertyUtilityServicesDirectDamageBldg"
TE = "CommercialPropertyUtilityServicesTimeElement"
DDP = f"{STRUCT}/{DD}Table/{DD}/{DD}DetailTable/{DD}Detail"
TEP = f"{chunk5.BI}/{TE}Table/{TE}/{TE}DetailTable/{TE}Detail"

DD_DETAIL = {"UtilityType": "Public Utilities", "Utility": "Water Supply",
             "Limit": "40000", "CauseOfLoss": "Basic", "EQCovIndicator": "No"}
TE_DETAIL = {"UtilityType": "Public Utilities", "Utility": "Water Supply",
             "Limit": "40000", "WaitingPeriod": "72 hours"}


def dd_cell(form):
    return f"{DDP}/{DD}Detail{form}Coverage"


def te_cell(form):
    return f"{TEP}/{TE}Detail{form}Coverage"


def dd_submission(detail=None, structure=None):
    sub = chunk2.submission()
    st = gates.structure(sub)
    st.update(structure or {})
    st[f"{DD}Table"] = {DD: [{f"{DD}DetailTable": {f"{DD}Detail": [dict(DD_DETAIL if detail is None else detail)]}}]}
    return sub


def te_submission(detail=None, col="Basic"):
    sub = chunk5.submission(col)
    bi = gates.structure(sub)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
    bi[f"{TE}Table"] = {TE: [{f"{TE}DetailTable": {f"{TE}Detail": [dict(TE_DETAIL if detail is None else detail)]}}]}
    return sub


DD_CHECKS = [
    ("DD BasicGroupINonOverheadBaseRate", DDP + "/BasicGroupINonOverheadBaseRate", "0.038"),
    ("DD BasicGroupIRate", DDP + "/BasicGroupIRate", "0.038"),
    ("DD BasicGroupIIRate", DDP + "/BasicGroupIIRate", "0.011"),
    ("DD LimitToUse", DDP + "/LimitToUse", "40000"),
    ("DD BGI premium", dd_cell("BasicGroupI") + "/Premium", "15"),
    ("DD BGII premium", dd_cell("BasicGroupII") + "/Premium", "4"),
    ("Building BGI unmoved", chunk2.BGI, "261"),
    ("Building BGII unmoved", chunk2.BGII, "32"),
]
TE_CHECKS = [
    ("TE WaitingPeriodFactor", TEP + "/WaitingPeriodFactor", "1"),
    ("TE BasicGroupIRate", TEP + "/BasicGroupIRate", "0.022"),
    ("TE BasicGroupIIRate", TEP + "/BasicGroupIIRate", "0.011"),
    ("TE BGI premium", te_cell("BasicGroupI") + "/Premium", "9"),
    ("TE BGII premium", te_cell("BasicGroupII") + "/Premium", "4"),
    ("BI BGI unmoved", chunk5.BI + "/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium", "112"),
]


def check(label, sub, checks, trace=False, cellf=None):
    data, ip = g.run(sub, trace)
    ok = True
    print(f"  {label}")
    for name, path, want in checks:
        got = read(path, data)
        good = g.num_eq(got, want)
        ok &= good
        print(f"    {name:36s} = {str(got):>10s}   want {want:>8s}  {'ok' if good else 'MISMATCH'}")
    cells = {f: read(cellf(f) + "/Premium", data) for f in FORMS}
    print(f"    all cells: {cells}")
    print(f"    messages: {sorted(set(ip.messages))}\n")
    return ok, data, ip


def RAAS_CASES():
    """Cases for `132_chunk12_family_raas.py utility`."""
    return [
        ("D0", "direct damage golden (ours $15 + $4)", dd_submission()),
        ("D1", "direct damage, Power incl. overhead lines", dd_submission(dict(DD_DETAIL, Utility="Power Supply - Including Overhead Transmission Lines"))),
        ("D2", "direct damage, Other Than Public Utilities", dd_submission(dict(DD_DETAIL, UtilityType="Other Than Public Utilities"))),
        ("D3", "direct damage, detail CauseOfLoss Special", dd_submission(dict(DD_DETAIL, CauseOfLoss="Special"))),
        ("D4", "direct damage, detail CauseOfLoss blank", dd_submission(dict(DD_DETAIL, CauseOfLoss=""))),
        ("T0", "time element golden (ours $9 + $4)", te_submission()),
        ("T1", "time element, Other Than Public Utilities (filed rate 0)", te_submission(dict(TE_DETAIL, UtilityType="Other Than Public Utilities"))),
        ("T2", "time element, no WaitingPeriod (factor 0.0)", te_submission({k: v for k, v in TE_DETAIL.items() if k != "WaitingPeriod"})),
        ("T3", "time element, 24 hours (1.1)", te_submission(dict(TE_DETAIL, WaitingPeriod="24 hours"))),
        ("D5", "direct damage, detail Limit absent (ours: building's 100,000, $38 + $11)",
         dd_submission({k: v for k, v in DD_DETAIL.items() if k != "Limit"})),
        ("T4", "time element, unfiled WaitingPeriod '36 hours' (ours $0, a lookup miss)",
         te_submission(dict(TE_DETAIL, WaitingPeriod="36 hours"))),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    print(f"{book_for(JURIS, ASOF)}\n")
    ok1, *_ = check("DIRECT DAMAGE on chunk 2's building", dd_submission(), DD_CHECKS, a.trace, dd_cell)
    ok2, *_ = check("TIME ELEMENT on chunk 5's Business Income", te_submission(), TE_CHECKS, a.trace, te_cell)
    ok = ok1 and ok2
    print("ALL MATCH" if ok else "MISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
