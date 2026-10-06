#!/usr/bin/env python3
"""Chunk 8's golden cases -- Legal Liability, Building and Contents.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK8-GOLDEN-CASE.md`.

Built differentially: **chunk 1-4's own risks**, with the coverage switched to
Legal Liability. Every rate row through the cause-of-loss adjustment is shared,
so the numbers below are the numbers those chunks already produced, taken three
steps earlier and multiplied by two small factors.

    Premium = r0( r0( r0( r0( r0( r3( r3(RATE x LegalLiabilityFactor)
                                     x LegalLiabAddlInsurableIntFactor )
                                 x Limit/100 )
                             x PackageModFactor ) x IRPMFactor )
                     x CyberBGI ) x CyberCOLExcptnsBGI )

    BUILDING  factor 0.25 [CW, "Bldg"]
      Basic Group I    COLadj 0.239 -> r3(0.05975)=0.060 -> $60
      Basic Group II   COLadj 0.027 -> r3(0.00675)=0.007 -> $7
      Broad            BroadRate    0.015 -> r3(0.00375)=0.004 -> $4
      Special          SpecialRate  0.047 -> r3(0.01175)=0.012 -> $12

    CONTENTS  factor 0.50 [CW, "PersProp"] -- the same two-row table, the
              other row, and **twice the money**
      Basic Group I    COLadj 0.263 -> r3(0.1315)=0.132 -> $132
      Basic Group II   COLadj 0.030 -> r3(0.015)  =0.015 -> $15
      Broad            BroadRate    0.021 -> r3(0.0105)=0.011 -> $11
      Special          SpecialCOLadj 0.186 -> r3(0.093)=0.093 -> $93

**Building's Special reads the raw `SpecialRate` and Contents' reads
`SpecialCauseOfLossAdjustment`** -- point 6 of the traced map, and the one that
moves money once a theft exclusion is elected (C8-19).

**The additional-insurable-interest record is not optional.** Its factor
defaults to **0.0**, not 1.0, so without a record carrying a non-blank option
every premium above is zero. The golden case elects `"None"` -> Option4 -> 1.0,
which is neutral and lets the arithmetic be read.

    python scripts/cf/59_chunk8_golden_case.py [--trace]

Exit 0 when all eight premiums match.

**Two things had to be right before a single premium appeared, and getting
one of them wrong nearly cost an engine change.**

  A  **`PolicyType` must be set on the POLICY.**
     `AttachFormCommercialPropertyLegalLiabilityCoverageForm` gates on
     `PolicyType = "Commercial Property Policy"` AND
     `CovType = "Legal Liability"`, and its `Else` branch is a bare
     `<rul:Remove ... RemoveMultiple="true" />`. **Without `PolicyType`, ISO's
     own rule DELETES the coverage-form record you submitted**, the
     insurable-interest factor falls to its 0.0 default, and every premium is
     $0.

     The first run of this script had `PolicyType` in its ISO payload and not
     in its engine submission, so the two sides received different inputs and
     the difference read as an engine defect. **A control that passes without
     exercising the variable under test is not a control** -- the control here
     was a class-rated building, which never touches `PolicyType`. Recorded
     rather than quietly fixed: the proposed remedy was a change to the shared
     interpreter, and chunks 1-7 would have been re-run for nothing.

     This is **C6-01's trap for the second time, one chunk later**. There an
     absent `PolicyType` gated two forms shut; here it makes ISO delete a
     record the submitter supplied.

  B  **`CovForm` must be set on the OCCUPANCY CLASS, not the item.**
     `SetCovForm` is an unguarded `Copy` from `../../CovForm`, so a value set
     on the Personal Property record is overwritten and Contents never enters
     the Legal Liability branch at all. **That is point 1 of the traced map** --
     the gate is not merely a different field from Building's, it is a
     different LEVEL -- arriving early and by accident.
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
import _state_inputs as _si                                     # noqa: E402
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")

JURIS, ASOF = chunk2.JURIS, chunk2.ASOF
STRUCT, OCCUP, PP = chunk2.STRUCT, chunk4.OCCUP, chunk4.PP

LL_FORM = "CommercialPropertyLegalLiabilityCoverageForm"
LL_OCC = "CommercialPropertyLegalLiabilityCoverageFormOccupClass"
NONE = "None"                      # -> Option4 -> factor 1.0

_B = STRUCT + "/CommercialPropertyStructureBuilding%sCoverage/Premium"
_C = PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"

#: side, cause of loss, form, premium path, the rate it starts from, expected
CASES = [
    ("BUILDING", "Basic", "BasicGroupI", _B, "BasicGroupICauseOfLossAdjustment",
     "0.239", "60"),
    ("BUILDING", "Basic", "BasicGroupII", _B,
     "BasicGroupIICauseOfLossAdjustment", "0.027", "7"),
    ("BUILDING", "Broad", "Broad", _B, "BroadRate", "0.015", "4"),
    ("BUILDING", "Special", "Special", _B, "SpecialRate", "0.047", "12"),
    ("CONTENTS", "Basic", "BasicGroupI", _C, "BasicGroupICauseOfLossAdjustment",
     "0.263", "132"),
    ("CONTENTS", "Basic", "BasicGroupII", _C,
     "BasicGroupIICauseOfLossAdjustment", "0.03", "15"),
    ("CONTENTS", "Broad", "Broad", _C, "BroadRate", "0.021", "11"),
    ("CONTENTS", "Special", "Special", _C, "SpecialCauseOfLossAdjustment",
     "0.186", "93"),
]


def building(col="Basic", option=NONE, record=True):
    """Chunk 2's building, switched to Legal Liability.

    The gate is `CovType` **on the item** -- point 1 of the traced map, and the
    half of it that lets two buildings on one location disagree.
    """
    sub = chunk2.submission()
    # Without this the form-attachment rule takes its Else branch and REMOVES
    # the record below -- see note A in the module docstring.
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    st = zeros2.structure(sub)
    st["CauseOfLoss"] = col
    st["CovType"] = "Legal Liability"
    if record:
        st[f"{LL_FORM}Table"] = {LL_FORM: [{"AddlInsurableInt": option}]}
    return sub


def contents(col="Basic", option=NONE, record=True):
    """Chunk 4's contents, switched to the Legal Liability coverage form.

    The gate is `CovForm`, and the additional-insurable-interest record hangs
    off the **occupancy class**, not the item -- points 1 and 5.
    """
    sub = chunk4.submission(col)
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    occ = (zeros2.structure(sub)["CommercialPropertyOccupClassTable"]
           ["CommercialPropertyOccupClass"][0])
    # **On the OCCUPANCY CLASS, not the item.** `SetCovForm` is an unguarded
    # Copy from `../../CovForm`; a value set on the Personal Property record is
    # overwritten and the Legal Liability branch is never taken.
    occ["CovForm"] = "Legal Liability Coverage Form"
    if record:
        occ[f"{LL_OCC}Table"] = {LL_OCC: [{"AddlInsurableInt": option}]}
    return sub


def run(sub, trace=False):
    _si.localize(sub, JURIS, ASOF)      # C28-17: the state's own Group II territory
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)
    return data, ip


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    ok = True
    cache = {}
    for side, col, form, path, rate_dd, rate, want in CASES:
        key = (side, col)
        if key not in cache:
            sub = building(col) if side == "BUILDING" else contents(col)
            cache[key] = run(sub, a.trace)
        data, ip = cache[key]
        base = STRUCT if side == "BUILDING" else PP
        got_rate = str(read(f"{base}/{rate_dd}", data))
        got = str(read(path % form, data))
        fac = str(read(f"{base}/"
                       + ("LegalLiabilityFactor" if side == "BUILDING"
                          else "LegalLiabFactor"), data))
        add = str(read(f"{base}/LegalLiabAddlInsurableIntFactor", data))
        good = got == want and got_rate == rate
        ok &= good
        print(f"  {side:9s} {form:13s} {rate_dd:34s}={got_rate:>6s}  "
              f"x{fac:>5s} x{add:>4s}  PREMIUM={got:>4s}"
              + ("" if good else f"   <-- expected {rate} / {want}"))

    print("\n  What the eight numbers say")
    print("  **Contents is double.** One two-row table, keyed \"Bldg\" 0.25 and")
    print("  \"PersProp\" 0.50 -- and the premium is exactly twice what the same")
    print("  rate would earn on a building, before any other difference.")
    print("  **Building's Special starts from the raw rate and Contents' from")
    print("  the cause-of-loss adjustment** -- identical here because the theft")
    print("  factor defaults to 1.0, which is why C8-19 exists.")
    for (side, col), (data, ip) in sorted(cache.items()):
        if ip.messages:
            print(f"  {side} {col}: {len(ip.messages)} validation message(s)")
    print()
    if ok:
        print("All eight Legal Liability premiums match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
