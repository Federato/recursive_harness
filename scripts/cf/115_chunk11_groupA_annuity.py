#!/usr/bin/env python3
"""Chunk 11 Group A companions -- C11-11, C11-12, C11-13.

Each case is chunk 11's golden case (`114_chunk11_golden_case.py`) with ONE
input changed. Every expected value is copied from the "Group A companions"
table in `docs/CF-CHUNK11-GOLDEN-CASE.md`, written before this ran.

  C11-11  the annuity, traced -- incl. the day-of-month adjustment in
          `SetNumberOfMonths`, and the two rate tables checked against the
          closed form they should come from.
  C11-12  a submission populating a derived field -- three guarded
          injection points (the `rul:Power` output, `DiscFactor`, a net
          factor) all move the premium; the unguarded `AnnuityConstant` is
          the control and must NOT.
  C11-13  `PercentInterest` and lease term are live inputs.

Inputs whose average lands on an exact half were avoided on purpose, so no
case here depends on the rounding rule.

    python scripts/cf/115_chunk11_groupA_annuity.py

Exit 0 means every case matched its prediction.
"""
from __future__ import annotations

import csv
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g = import_module("114_chunk11_golden_case")
LI, cell = g.LI, g.cell

#: (task, label, LI-record overrides, policy overrides, expected dict)
CASES = [
    ("C11-11", "A  golden, unchanged", {}, {},
     dict(mi="120", me="108", fi="77.0562", fe="72.2213", net="111958", b1="268", b2="30")),
    ("C11-11", "B  day adjustment (122/110)",
     {"LeaseExpDate": "06/10/2037"}, {"EffDate": "03/15/2027", "ExpDate": "03/15/2028"},
     dict(mi="122", me="110", fi="77.8182", fe="73.0594", net="113158", b1="270", b2="31")),
    ("C11-12", "A  inject rul:Power output = 0.5",
     {"DiscFactorRaisedToNumOfMonthsRemainingAtInception": "0.5"}, {},
     dict(fi="62.7027", fe="72.2213", net="101193", b1="242", b2="27")),
    ("C11-12", "B  inject DiscFactor = 0.99", {"DiscFactor": "0.99"}, {},
     dict(fi="87.8615", fe="83.0492", net="128183", b1="306", b2="35")),
    ("C11-12", "C  inject NetFactorAtInception = 100",
     {"NetLeaseholdInterestFactorAtInception": "100"}, {},
     dict(fi="100", fe="72.2213", net="129166", b1="309", b2="35")),
    ("C11-12", "D  control: AnnuityConstant = 200 (unguarded)",
     {"AnnuityConstant": "200"}, {},
     dict(fi="77.0562", fe="72.2213", net="111958", b1="268", b2="30")),
    ("C11-13", "A  PercentInterest 13%", {"PercentInterest": "13%"}, {},
     dict(fi="68.9091", fe="65.1680", net="100558", b1="240", b2="27")),
    ("C11-13", "B  lease ends 01/01/2032 (60/48)", {"LeaseExpDate": "01/01/2032"}, {},
     dict(mi="60", me="48", fi="47.5385", fe="39.7518", net="65468", b1="156", b2="18")),
]

PATHS = {
    "mi": LI + "/NumOfMonthsRemainingAtInception",
    "me": LI + "/NumOfMonthsRemainingAtExpiration",
    "fi": LI + "/NetLeaseholdInterestFactorAtInception",
    "fe": LI + "/NetLeaseholdInterestFactorAtExpiration",
    "net": LI + "/TenantsNetLeaseholdInt",
    "b1": cell("TenantsLease", "BasicGroupI") + "/Premium",
    "b2": cell("TenantsLease", "BasicGroupII") + "/Premium",
}


def same(got, want: str) -> bool:
    """Numeric equality, so a filed `68.9091` and a written `68.9091` or a
    trailing-zero `65.1680` compare equal; anything non-numeric compares as
    text."""
    try:
        return Decimal(str(got)) == Decimal(want)
    except Exception:
        return str(got) == want


def table_check() -> bool:
    """Both rate tables against the closed form: v = (1+i)^(-1/12) and
    A = v/(1-v). Float tolerances, because this checks where the filed
    numbers came from, not the engine."""
    tables = book_for(g.JURIS, g.ASOF).parent.package.content / "Rate Tables"
    rd = lambda n: {r["LeaseholdInterestPct"]: float(r["Factor"]) for r in
                    csv.DictReader(open(tables / f"{n}.RateTable.csv",
                                        encoding="utf-8-sig"))}
    ann, disc = rd("LeaseholdInterestAnnuityConstant"), rd("LeaseholdInterestDiscFactor")
    ok = sorted(ann) == sorted(disc) and len(ann) == 11
    worst_v = worst_a = 0.0
    for pct, v in disc.items():
        i = int(pct.rstrip("%")) / 100
        v_exact = (1 + i) ** (-1 / 12)
        worst_v = max(worst_v, abs(v - v_exact))
        worst_a = max(worst_a, abs(ann[pct] - v_exact / (1 - v_exact)))
    ok &= worst_v < 1e-8 and worst_a < 1e-4
    print(f"  C11-11  tables: {len(disc)} rates {min(disc, key=lambda p: int(p[:-1]))}"
          f"-{max(disc, key=lambda p: int(p[:-1]))}; worst |v - (1+i)^(-1/12)| = "
          f"{worst_v:.1e}, worst |A - v/(1-v)| = {worst_a:.1e}"
          + ("" if ok else "   <-- NOT the closed form"))
    return ok


def main() -> int:
    print(f"{book_for(g.JURIS, g.ASOF)}\n")
    ok = table_check()
    print()
    for task, label, li_over, pol_over, want in CASES:
        li = dict(g.LI_RECORD, **li_over)
        sub = g.submission(li=li, exp_date=pol_over.get("ExpDate", g.EXP_DATE))
        if "EffDate" in pol_over:
            sub["EffDate"] = pol_over["EffDate"]
        data, _ = g.run(sub)
        bad = []
        for k, w in want.items():
            got = read(PATHS[k], data)
            if not same(got, w):
                bad.append(f"{k}={got} (expected {w})")
        ok &= not bad
        got_prem = f"{read(PATHS['b1'], data)} / {read(PATHS['b2'], data)}"
        print(f"  {task}  {label:44s} {got_prem:>10s}  "
              + ("MATCH" if not bad else "MISMATCH: " + "; ".join(bad)))
    print()
    if ok:
        print("Group A matches: the annuity traces as derived, three guarded "
              "fields accept an injected value and move the premium while the "
              "unguarded AnnuityConstant does not, and both interest rate and "
              "lease term are live.")
        return 0
    print("MISMATCH -- compare against docs/CF-CHUNK11-GOLDEN-CASE.md.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
