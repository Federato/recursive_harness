#!/usr/bin/env python3
"""Chunk 11's golden case (C11-01) -- the first Leasehold Interest submission
rated end to end. Tenants Lease, on chunk 2's own risk (Oregon, class 0951,
Frame, Portland) turned into a `CovType = Leasehold Interest` structure -- the
only shape the Structure's attach rule keeps an LI record on. Chunk 2's own
$261 / $32 are protected by re-running chunk 2's script, not by this one.

The derivation, written BEFORE this ran, is in
`docs/CF-CHUNK11-GOLDEN-CASE.md`. Every expected value below is copied from
that table, not computed here, so a disagreement is a finding rather than a
fresh run agreeing with itself.

Leasehold Interest is the one coverage whose exposure is computed rather than
entered: the monthly leasehold advantage is discounted to present value over
the remaining lease months, at inception and at policy expiration, and the two
are averaged. The discounting is the only `rul:Power` in the corpus.

    python scripts/cf/114_chunk11_golden_case.py [--trace] [--dump]

Exit 0 means every intermediate and every premium matched.
"""
from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, dump, read

chunk2 = import_module("09_chunk2_golden_case")
golden = import_module("01_golden_case")
JURIS, ASOF = golden.JURIS, golden.ASOF

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
LI = STRUCT + ("/CommercialPropertyLeaseholdInterestCoverageFormTable"
               "/CommercialPropertyLeaseholdInterestCoverageForm")
PFX = "CommercialPropertyLeaseholdInterestCoverageForm"
SUBCOV = ["TenantsLease", "BonusPayments", "Improvements", "PrepaidRent"]
FORMS = ["BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake"]


def cell(sub: str, form: str) -> str:
    return f"{LI}/{PFX}{sub}Coverage{form}Coverage"


#: The four LI inputs plus the policy ExpDate, per the derivation doc.
LI_RECORD = {
    "PercentInterest": "10%",
    "LeaseEffDate": "01/01/2025",
    "LeaseExpDate": "01/01/2037",
    "TenantsGrossLeaseholdInt": "1500",
}
EXP_DATE = "01/01/2028"


def submission(li: dict | None = None, exp_date: str | None = EXP_DATE,
               as_building: bool = False) -> dict:
    """Chunk 2's golden risk turned into a Leasehold Interest structure, with
    one LI record under it. `li` replaces the record's fields;
    `exp_date=None` omits the policy ExpDate; `as_building=True` leaves the
    structure as chunk 2's Building (the first run's shape, which the
    Structure's attach rule silently deletes)."""
    sub = chunk2.submission()
    if exp_date is not None:
        sub["ExpDate"] = exp_date
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    st = (cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
          ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    if not as_building:
        # AttachFormCommercialPropertyLeaseholdInterestCoverageForm keeps the
        # LI record only for this PolicyType and CovType; values per the
        # DomainCovTypeBldg / DomainCoinsuranceBldg / DomainLimitBldg rows.
        cp["PolicyType"] = "Commercial Property Policy"
        st["CovType"] = "Leasehold Interest"
        st["Coinsurance"] = "Not Applicable"
        st.pop("Limit", None)
        # The domain-correct "not elected" value (DomainEQCovIndicatorBldg).
        # NOT blank: each LI Earthquake cell's gate is
        # EQCovIndicator != "No Coverage" AND != "Not Applicable", which a
        # blank satisfies -- the first corrected run switched the Tenants EQ
        # cell ON (premium $0) with this field unset. See the golden-case doc,
        # finding 8.
        st["EQCovIndicator"] = "No Coverage"
    st["CommercialPropertyLeaseholdInterestCoverageFormTable"] = {
        "CommercialPropertyLeaseholdInterestCoverageForm":
            [dict(LI_RECORD if li is None else li)],
    }
    return sub


def run(sub: dict, trace: bool = False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)
    return data, ip


#: (label, path, expected) -- expected copied from CF-CHUNK11-GOLDEN-CASE.md.
CHECKS = [
    ("1  AnnuityConstant", LI + "/AnnuityConstant", "125.40537"),
    ("2  DiscFactor", LI + "/DiscFactor", "0.99208894"),
    ("3  NumOfMonthsRemainingAtInception", LI + "/NumOfMonthsRemainingAtInception", "120"),
    ("4  NumOfMonthsRemainingAtExpiration", LI + "/NumOfMonthsRemainingAtExpiration", "108"),
    ("8  NetLeaseholdInterestFactorAtInception", LI + "/NetLeaseholdInterestFactorAtInception", "77.0562"),
    ("9  NetLeaseholdInterestFactorAtExpiration", LI + "/NetLeaseholdInterestFactorAtExpiration", "72.2213"),
    ("10 TenantsNetLeaseholdInterestAtInception", LI + "/TenantsNetLeaseholdInterestAtInception", "115584"),
    ("11 TenantsNetLeaseholdInterestAtExpiration", LI + "/TenantsNetLeaseholdInterestAtExpiration", "108332"),
    ("12 TenantsNetLeaseholdInt", LI + "/TenantsNetLeaseholdInt", "111958"),
    ("13 TotCoveredLeaseholdIntNet", LI + "/TotCoveredLeaseholdIntNet", "111958"),
    ("14 BasicGroupICauseOfLossAdjmt", LI + "/BasicGroupICauseOfLossAdjmt", "0.239"),
    ("15 BasicGroupIICauseOfLossAdjmt", LI + "/BasicGroupIICauseOfLossAdjmt", "0.027"),
    ("16 Tenants BGI Premium", cell("TenantsLease", "BasicGroupI") + "/Premium", "268"),
    ("17 Tenants BGII Premium", cell("TenantsLease", "BasicGroupII") + "/Premium", "30"),
    ("20 LI ErcCalculatedTotalPremium", LI + "/ErcCalculatedTotalPremium", "298"),
]

#: Steps 5-7 are unrounded; checked to the 10 places the derivation wrote.
PREFIX_CHECKS = [
    ("5  DiscFactorRaisedTo...AtInception",
     LI + "/DiscFactorRaisedToNumOfMonthsRemainingAtInception", "0.3855431286"),
    ("6  ComplimentOfDiscFactorIncep", LI + "/ComplimentOfDiscFactorIncep", "0.6144568713"),
    ("7  ComplimentOfDiscFactorExpir", LI + "/ComplimentOfDiscFactorExpir", "0.5759025407"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    data, ip = run(submission(), a.trace)

    ok = True
    for label, path, want in CHECKS:
        got = read(path, data)
        good = got == want
        ok &= good
        print(f"  {label:44s} = {str(got):>14s}"
              + ("" if good else f"   <-- expected {want}"))
    for label, path, want in PREFIX_CHECKS:
        got = str(read(path, data))
        good = got.startswith(want)
        ok &= good
        print(f"  {label:44s} = {got[:14]:>14s}"
              + ("" if good else f"   <-- expected {want}..."))

    # Step 18/19: every other grid cell must be switched off and price $0.
    print("\n  Grid (CoverageOnPolicyIndicator / Premium):")
    for sub in SUBCOV:
        row = []
        for form in FORMS:
            on = read(cell(sub, form) + "/CoverageOnPolicyIndicator", data)
            prem = read(cell(sub, form) + "/Premium", data)
            want_on = "1" if (sub, form) in {("TenantsLease", "BasicGroupI"),
                                             ("TenantsLease", "BasicGroupII")} else "0"
            good = on == want_on
            ok &= good
            row.append(f"{form[:6]:>6s} {on}/{prem}" + ("" if good else "!"))
        print(f"    {sub:14s} " + "  ".join(row))

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}):")
        for m in ip.messages[:20]:
            print(f"    - {m}")
    if a.trace:
        print(ip.trace_text())
    if a.dump:
        print(dump(data))

    print()
    if ok:
        print("Leasehold Interest golden case matches: every intermediate "
              "traces to its hand-derived value -- $268 Basic Group I + $30 "
              "Basic Group II, and every other grid cell switched off.")
        return 0
    print("MISMATCH -- compare against docs/CF-CHUNK11-GOLDEN-CASE.md. "
          "No engine code is changed here without the user's go.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
