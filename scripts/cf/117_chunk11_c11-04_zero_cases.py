#!/usr/bin/env python3
"""Chunk 11 C11-04 -- every way a Leasehold Interest submission reaches $0.

Every expected value is copied from `docs/CF-CHUNK11-ZERO-CASES.md`, written
before this ran. Each case is the golden case (`114_chunk11_golden_case.py`,
$268 / $30) with one thing changed. The point is not that each is zero but
WHERE each zero comes from: seven tiers, T0 (record deleted) to T6 (engine
refuses), plus one boundary case that must NOT be zero.

    python scripts/cf/117_chunk11_c11-04_zero_cases.py

Exit 0 means every case landed exactly where the derivation said.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.tree import read
from gl_engine.interp.values import InterpretError
import _iso_refusals as _iso                                    # noqa: E402

g = import_module("114_chunk11_golden_case")
LI, cell, SUBCOV, FORMS = g.LI, g.cell, g.SUBCOV, g.FORMS
BGI = cell("TenantsLease", "BasicGroupI")
BGII = cell("TenantsLease", "BasicGroupII")
EQC = cell("TenantsLease", "Earthquake")


def li_without(*keys, **changes):
    li = {k: v for k, v in g.LI_RECORD.items() if k not in keys}
    li.update(changes)
    return li


def case_sub(li=None, exp_date=g.EXP_DATE, as_building=False, eq_blank=False):
    sub = g.submission(li=li, exp_date=exp_date, as_building=as_building)
    if eq_blank:
        st = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
              ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
        st.pop("EQCovIndicator", None)
    return sub


#: (id, tier, label, submission, expectation)
#: expectation kinds: ("deleted",) | ("all_off",) | ("on_zero", months_or_None)
#:   | ("prem", bgi, bgii, extra) | ("refuse", substring)
CASES = [
    ("Z1", "T0", "LI under a Building structure",
     case_sub(as_building=True), ("deleted",)),
    ("Z2", "T1", "all four amounts absent",
     case_sub(li=li_without("TenantsGrossLeaseholdInt")), ("all_off",)),
    ("Z3", "T2", "LeaseExpDate absent",
     case_sub(li=li_without("LeaseExpDate")), ("on_zero", ("0", "0"))),
    ("Z4", "T2", "lease ended before the policy",
     case_sub(li=li_without(LeaseExpDate="06/01/2026")), ("on_zero", ("0", "0"))),
    # Z5 was predicted $0 and came back $268/$30: the Default block in
    # `Overall Rating.Rule.xml` sets ExpDate = EffDate + 1 year on every run,
    # so a missing (or different) ExpDate is not an input at all. Kept as a
    # NOT-zero check, both shapes.
    ("Z5", "--", "policy ExpDate absent -> EffDate + 1y (NOT zero)",
     case_sub(exp_date=None), ("prem", "268", "30", ("120", "108", "111958"))),
    ("Z5b", "--", "policy ExpDate 07/01/2027 -> overwritten (NOT zero)",
     case_sub(exp_date="07/01/2027"), ("prem", "268", "30", ("120", "108", "111958"))),
    # Z6 was $0 until the OI-102 fix (2026-09-22): the `01/01/0001` fallback
    # compared as null -> False. ISO reads it as DateTime.MinValue and prices
    # normally ($272/$31 live at 2026-09-17). Now it orders as date.min too,
    # so a missing LeaseEffDate is NOT a zero case.
    ("Z6", "--", "LeaseEffDate absent -> earliest date (NOT zero, OI-102)",
     case_sub(li=li_without("LeaseEffDate")), ("prem", "268", "30", ("120", "108", "111958"))),
    ("Z7", "T3", "PercentInterest absent",
     case_sub(li=li_without("PercentInterest")), ("on_zero", ("120", "108"))),
    ("Z8", "T3", "PercentInterest 10.5% (D2)",
     case_sub(li=li_without(PercentInterest="10.5%")), ("on_zero", ("120", "108"))),
    ("Z9", "T3", "PercentInterest '10' without % (D2)",
     case_sub(li=li_without(PercentInterest="10")), ("on_zero", ("120", "108"))),
    ("Z10", "T4", "TenantsGrossLeaseholdInt -1500",
     case_sub(li=li_without(TenantsGrossLeaseholdInt="-1500")), ("on_zero", ("120", "108"))),
    ("Z11", "T5", "EQCovIndicator blank",
     case_sub(eq_blank=True), ("prem", "268", "30", "eq_on_zero")),
    # Z13 refused on 0^0 until the OI-104 fix (2026-09-22): Decimal raises,
    # .NET returns 1. ISO priced it $0 live (C11-23). Now 0^0 = 1, so it is a
    # plain months-and-annuity zero, T2/T3, and agrees with ISO.
    ("Z13", "T3", "PercentInterest absent + lease ended (0^0 = 1, OI-104)",
     case_sub(li=li_without("PercentInterest", LeaseExpDate="06/01/2026")),
     ("on_zero", ("0", "0"))),
    ("B1", "--", "lease ends mid-policy (NOT zero)",
     case_sub(li=li_without(LeaseExpDate="06/01/2027")),
     ("prem", "9", "1", ("5", "0", "3662"))),
]


def check(kind, data):
    """Return a list of disagreements for one case."""
    bad = []
    records = tree.select(LI, data)
    if kind[0] == "deleted":
        if records:
            bad.append(f"{len(records)} LI record(s) kept")
        return bad
    if not records:
        return ["LI record missing"]
    ons = {(s, f): read(cell(s, f) + "/CoverageOnPolicyIndicator", data)
           for s in SUBCOV for f in FORMS}
    total = read(LI + "/ErcCalculatedTotalPremium", data)
    if kind[0] == "all_off":
        on = [k for k, v in ons.items() if v != "0"]
        if on:
            bad.append(f"cells on: {on}")
        if total not in ("0", None):
            bad.append(f"total {total}")
        return bad
    b1, b2 = read(BGI + "/Premium", data), read(BGII + "/Premium", data)
    if kind[0] == "on_zero":
        if (ons[("TenantsLease", "BasicGroupI")], ons[("TenantsLease", "BasicGroupII")]) != ("1", "1"):
            bad.append("Tenants BGI/BGII not both on")
        if (b1, b2) != ("0", "0"):
            bad.append(f"premium {b1}/{b2}, expected 0/0")
        months = (read(LI + "/NumOfMonthsRemainingAtInception", data),
                  read(LI + "/NumOfMonthsRemainingAtExpiration", data))
        if kind[1] and months != kind[1]:
            bad.append(f"months {months}, expected {kind[1]}")
        return bad
    if kind[0] == "prem":
        if (b1, b2) != (kind[1], kind[2]):
            bad.append(f"premium {b1}/{b2}, expected {kind[1]}/{kind[2]}")
        extra = kind[3]
        if extra == "eq_on_zero":
            eq = (read(EQC + "/CoverageOnPolicyIndicator", data), read(EQC + "/Premium", data))
            if eq != ("1", "0"):
                bad.append(f"EQ cell {eq}, expected on/$0")
        elif extra:
            got = (read(LI + "/NumOfMonthsRemainingAtInception", data),
                   read(LI + "/NumOfMonthsRemainingAtExpiration", data),
                   read(LI + "/TenantsNetLeaseholdInt", data))
            if got != extra:
                bad.append(f"months/net {got}, expected {extra}")
        return bad
    return [f"unknown expectation {kind}"]


def main() -> int:
    print(f"{book_for(g.JURIS, g.ASOF)}\n")
    ok = True
    for cid, tier, label, sub, kind in CASES:
        try:
            data, _ = g.run(sub)
        except InterpretError as exc:
            if kind[0] == "refuse" and kind[1] in str(exc) and "Power(" in str(exc):
                print(f"  {cid:4s}{tier}  {label:50s} REFUSED as predicted")
                continue
            if _iso.refused_as_iso(__file__, cid, exc, indent="  "):   # C28-05: ours refuses where ISO does
                continue
            ok = False
            print(f"  {cid:4s}{tier}  {label:50s} MISMATCH: refused -- {str(exc)[:120]}")
            continue
        if kind[0] == "refuse":
            ok = False
            print(f"  {cid:4s}{tier}  {label:50s} MISMATCH: ran, expected a refusal")
            continue
        bad = check(kind, data)
        ok &= not bad
        print(f"  {cid:4s}{tier}  {label:50s} " + ("MATCH" if not bad else "MISMATCH"))
        for b in bad:
            print(f"          - {b}")
    print()
    if ok:
        print("C11-04 matches: every zero landed in the tier the derivation "
              "named, and the mid-policy boundary is not zero.")
        return 0
    print("MISMATCH -- compare against docs/CF-CHUNK11-ZERO-CASES.md.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
