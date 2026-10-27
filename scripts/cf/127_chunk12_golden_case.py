#!/usr/bin/env python3
"""Chunk 12, C12-05 -- the Debris Removal golden case.

Specified in `docs/CF-CHUNK12-DEBRIS-REMOVAL.md`, whose derivation was written
BEFORE this ran. Built differentially against chunk 2: the same Oregon
building (Basic, Frame, class 0951, limit 100,000, ISO-confirmed at
$261 BGI + $32 BGII), plus one `CommercialPropertyDebrisRemovalAdditionalInsurance`
record with `Limit` 60,000.

    Group I     round3(round3(0.239 x 0.5) x 1.172) x 350 = 0.141 x 350 -> $49
    Group II    round3(round3(0.027 x 0.5) x 1.266) x 350 = 0.018 x 350 -> $6
    Broad, Special, Earthquake                              -> $0 (not elected)
    Debris Removal total                                      $55
    Building unmoved                                          $261 / $32

The LOI factors are keyed by the BUILDING's limit (100,000), not Debris
Removal's own; only the exposure, (60,000 - 25,000) / 100, is its own.

    python scripts/cf/127_chunk12_golden_case.py [--trace] [--limit N]

Exit 0 when every figure matches.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
JURIS, ASOF = "OR", chunk2.golden.ASOF

STRUCT = chunk2.STRUCT
PFX = "CommercialPropertyDebrisRemovalAdditionalInsurance"
DR = STRUCT + f"/{PFX}Table/{PFX}"
FORMS = ["BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake"]


def cell(form: str) -> str:
    return f"{DR}/{PFX}{form}Coverage"


def submission(limit: int = 60000, record: dict | None = None, structure: dict | None = None,
               juris: str = JURIS) -> dict:
    """Chunk 2's building with one Debris Removal record under it.
    `record` replaces the record's fields; `structure` overlays the building."""
    sub = chunk2.submission()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    st = (cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
          ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    st.update(structure or {})
    rec = {"Limit": str(limit)} if record is None else dict(record)
    st[f"{PFX}Table"] = {PFX: [rec]}
    return sub


def run(sub: dict, trace: bool = False, juris: str = JURIS):
    ip = Interpreter(book_for(juris, ASOF), rounding=ROUNDING, trace=trace,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return data, ip


#: (label, path, expected) -- copied from the derivation, written before the run.
CHECKS = [
    ("MinimumLimit", DR + "/MinimumLimit", "25000"),
    ("BasicGroupIFactor", DR + "/BasicGroupIFactor", "0.5"),
    ("BasicGroupIIFactor", DR + "/BasicGroupIIFactor", "0.5"),
    ("BroadRate", DR + "/BroadRate", "0.01"),
    ("SpecialRate", DR + "/SpecialRate", "0.01"),
    ("EQFactor", DR + "/EQFactor", "0.75"),
    ("BasicGroupILOIFactor (building limit)", DR + "/BasicGroupILOIFactor", "1.172"),
    ("BasicGroupIILOIFactor (building limit)", DR + "/BasicGroupIILOIFactor", "1.266"),
    ("BroadLOIFactor", DR + "/BroadLOIFactor", "1.237"),
    ("SpecialLOIFactor", DR + "/SpecialLOIFactor", "1.237"),
    ("ExposureStatAmount", DR + "/ExposureStatAmount", "35"),
    ("BGI cell on policy", cell("BasicGroupI") + "/CoverageOnPolicyIndicator", "1"),
    ("BGII cell on policy", cell("BasicGroupII") + "/CoverageOnPolicyIndicator", "1"),
    ("Broad cell on policy", cell("Broad") + "/CoverageOnPolicyIndicator", "0"),
    ("Special cell on policy", cell("Special") + "/CoverageOnPolicyIndicator", "0"),
    ("EQ cell on policy", cell("Earthquake") + "/CoverageOnPolicyIndicator", "0"),
    ("DR BGI Premium", cell("BasicGroupI") + "/Premium", "49"),
    ("DR BGII Premium", cell("BasicGroupII") + "/Premium", "6"),
    ("DR total", DR + "/ErcCalculatedTotalPremium", "55"),
    ("Building BGI unmoved", chunk2.BGI, "261"),
    ("Building BGII unmoved", chunk2.BGII, "32"),
]


def num_eq(got, want) -> bool:
    try:
        return got is not None and float(got) == float(want)
    except ValueError:
        return got == want


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--limit", type=int, default=60000)
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    data, ip = run(submission(a.limit), a.trace)
    ok = True
    for label, path, want in CHECKS:
        got = read(path, data)
        good = num_eq(got, want)
        ok &= good
        print(f"  {label:40s} = {str(got):>10s}   want {want:>8s}  {'ok' if good else 'MISMATCH'}")
    print(f"\n  messages ({len(ip.messages)}):")
    for m in ip.messages:
        print(f"    - {m}")
    if a.trace:
        print(ip.trace_text())
    print("\nALL MATCH" if ok else "\nMISMATCH -- the derivation or the engine is wrong; find out which")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
