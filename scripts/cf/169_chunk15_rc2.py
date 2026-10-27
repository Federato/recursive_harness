#!/usr/bin/env python3
"""Chunk 15, RC-2 (C15-06 to C15-10): golden cases, one per formula variant, derived by hand first.

Every case sits on chunk 7's five-coverage Oregon policy (grp.five(), chunk 4's
contents included) with the SAME inputs, chosen by search so that every rival
reading gives a different dollar (1090 is the first manual premium that does):

    ManualPremium 1,090 on every record
    policy  PackageModFactor 0.85, IRPMFactor 1.15, multi-premium credit (user) 0.9
    building MultiPremiumAndDispersionCreditFactor 0.95 (its own; PackageModFactor 1.0 as chunk 2)

The three steps, half-up to whole dollars (cf_engine.config.ROUNDING):
    1090 x 0.85 = 926.5  -> 927
    927  x 0.95 = 880.65 -> 881       (building credit)   927 x 0.9 = 834.3 -> 834 (contents / policy credit)
    881  x 1.15 = 1013.15 -> 1013                          834 x 1.15 = 959.1 -> 959

C15-06  VARIANT A, Valuable Papers (its own Contents row, CovType = Valuable Papers).
        Filed path reads the BUILDING's credit (RC-1, C15-03): 1,013.
        Rivals: Contents row's credit 959; rounding once 1090 x .85 x .95 x 1.15 = 1012.2 -> 1012.
C15-07  VARIANT B, Discretionary Payroll Expense (Business Income): no credit.
        927 x 1.15 = 1066.05 -> 1,066. Rivals: credit applied 959; once 1065.275 -> 1065.
C15-08  VARIANT C, Interruption of Computer Operations (BI; switch Yes, limit 10,000):
        ONE Product of three operands, rounded once: 1090 x 1.15 x 0.85 = 1065.475 -> 1,065.
        Rival: step rounding 1090 x 1.15 = 1253.5 -> 1254, x 0.85 = 1065.9 -> 1066.
C15-09  VARIANT D, Newly Acquired or Constructed Property (building, factor-first order):
        innermost is still ManualPremium x package discount, then the building credit, then
        IRPM: same as C15-06, 1,013.
C15-10  EVERY FILE ONCE: all 23 countrywide records on one policy, each predicted from where
        its modifiers land (C15-03):
          building credit 0.95  -> 1,013 : Cannabis building x2, Newly Acquired Property, Valuable Papers
          contents / special class / policy credit 0.9 -> 959 : Cannabis contents x2, Limited
              International x2, Cannabis special class x2, Newly Acquired Location, Portable
              Storage, Electronic Commerce x2
          no credit (B) -> 1,066 : Cannabis BI x2, Cannabis SCBI x2, Discretionary Payroll x2
          Business Income's own credit, always 1.0 (A) -> 927 x 1 = 927, x 1.15 -> 1,066 : Y2K
          one rounding (C) -> 1,065 : Interruption of Computer Operations x2

    python scripts/cf/169_chunk15_rc2.py [--live]

--live sends each case to ISO at 2026-09-17 and compares EVERY Premium and
ErcCalculatedTotalPremium field for field, plus the predicted records. Exits 1
on any disagreement.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import book_for
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
rc1 = import_module("168_chunk15_rc1")
r11 = gc.r11
r11.NUMERIC |= {"ManualPremium", "MultiPremiumAndDispersionCreditFactorUser"}
P = "CommercialProperty"
MANUAL = "1090"
POLICY = {"PackageModFactor": "0.85", "IRPMFactor": "1.15", "MultiPremiumAndDispersionCreditFactorUser": "0.9"}
BUILDING_CREDIT = "0.95"

VP = rc1.VP
DPE = "DiscretionaryPayrollExpense"
ICO = "BusinessIncomeInterruptionOfComputerOperationsCoverage"
NAP = "NewlyAcquiredOrConstructedPropertyIncreasedLimit"

#: C15-10 predictions, record -> premium
ALL = {
    "CannabisExclusionBuilding": 1013, "CannabisExclusionWithHempExceptionBuilding": 1013, NAP: 1013, VP: 1013,
    "CannabisExclusionPersonalProperty": 959, "CannabisExclusionWithHempExceptionPersonalProperty": 959,
    "BusnPrsnlPropLimitedInternationalCov": 959, "PropInProcessOfMfrByOthersLimitedInternationalCov": 959,
    "CannabisExclusionSpecialClass": 959, "CannabisExclusionWithHempExceptionSpecialClass": 959,
    "LocationNewlyAcquiredLocationTimeElement": 959, "OccupClassTemporarilyInPortableStorageUnits": 959,
    "ElectronicCommerceLossOfBusinessIncomeCov": 959, "ElectronicCommerceLossOfDataCov": 959,
    "CannabisExclusionBusinessIncome": 1066, "CannabisExclusionWithHempExceptionBusinessIncome": 1066,
    "CannabisExclusionSpecialClassBusinessIncome": 1066,
    "CannabisExclusionWithHempExceptionSpecialClassBusinessIncome": 1066,
    DPE: 1066, "DiscretionaryPayrollExpenseSpclClassBusnIncome": 1066,
    "BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems": 1066,
    ICO: 1065, "SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverage": 1065,
}
assert set(ALL) == set(rc1.CW_RECORDS)

CASES = {
    "G6": ("C15-06 variant A, Valuable Papers (reads the building's credit)", [VP], {VP: 1013}),
    "G7": ("C15-07 variant B, Discretionary Payroll (no credit)", [DPE], {DPE: 1066}),
    "G8": ("C15-08 variant C, Interruption of Computer Operations (one rounding)", [ICO], {ICO: 1065}),
    "G9": ("C15-09 variant D, Newly Acquired Property (factor-first)", [NAP], {NAP: 1013}),
    "G10": ("C15-10 all 23 countrywide records on one policy", list(ALL), ALL),
}


def build(recs):
    sub = grp.five()
    sub["CommercialPropertyTable"]["CommercialProperty"][0].update(POLICY)
    st = rc1.node_dicts(sub)[P + "Structure"]
    st["MultiPremiumAndDispersionCreditFactor"] = BUILDING_CREDIT
    st.setdefault("WindstormOrHailDeductible", "1,000")    # ISO refuses it blank (C13-08, OI-103)
    rc1.MANUAL = MANUAL
    rc1.place(sub, rc1.xsd_for(book_for("OR", gc.ASOF)), recs, dict(rc1.SWITCH))
    return sub


def premiums(data, rec):
    """Premium on every filled record of this type (the engine also creates empty ones)."""
    return [x.first("Premium").text if x.first("Premium") is not None else None
            for x in rc1.find(data, P + rec) if x.first("ManualPremium") is not None]


def iso_premiums(resp, rec):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + rec and o.get("ManualPremium") not in (None, "", 0):
                out.append(o.get("Premium"))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return out


def eq(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return False


def messages(resp):
    return sorted(set(re.findall(r'"(?:Message|ErrorMessage|Text)"\s*:\s*"([^"]{0,160})"', json.dumps(resp))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []
    for cid, (label, recs, want) in CASES.items():
        try:
            data, ip = gc.run(build(recs))
        except InterpretError as exc:
            print(f"{cid}  {label}: RAISED {exc}")
            fails.append(cid)
            continue
        bad = [(r, premiums(data, r), v) for r, v in want.items()
               if not premiums(data, r) or not all(eq(g, v) for g in premiums(data, r))]
        got = sorted({g for r in want for g in premiums(data, r) if g not in (None, "")}, key=float)
        print(f"{cid}  {label}: engine {len(want) - len(bad)} of {len(want)} as derived; premiums {' '.join(got)}"
              + "".join(f"\n      {r}: got {g}, derived {v}" for r, g, v in bad))
        if bad:
            fails.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, then every Premium and the total, by path):")
        for cid, (label, recs, want) in CASES.items():
            req = r11.payload(build(recs))
            (gc.OUT / f"chunk15_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid}  ISO REFUSES {m.group(0) if m else str(exc.body)[:160]}")
                fails.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk15_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pred_bad = [(r, iso_premiums(resp, r), v) for r, v in want.items()
                        if not iso_premiums(resp, r) or not all(eq(x, v) for x in iso_premiums(resp, r))]
            data, ip = rep.cmp.rate(req)
            iso, ours = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if not rep.cmp.same(v, ours.get(k))]
            tot = iso.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
            print(f"  {cid}  predicted {len(want) - len(pred_bad)} of {len(want)}; "
                  f"{'AGREE ' if not d else 'DIFFER'} on all {len(iso)} premiums; ISO total {tot}"
                  + "".join(f"\n        predicted {r}: ISO {x}, derived {v}" for r, x, v in pred_bad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:6]))
            msgs = messages(resp)
            if msgs:
                print(f"        ISO messages: {msgs[:6]}")
            if pred_bad or d:
                fails.append(f"{cid} live")
    print(f"\nRC-2: {'ALL AGREE' if not fails else 'FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
