#!/usr/bin/env python3
"""OI-115 step 1: pin ISO's blank-operand rule for `Subtract` before the engine changes.

OI-115 (chunk 20 C20-15, `201_chunk20_rc3.py` Z2 / Z2b) showed ISO skips a blank FIRST operand of
`Subtract` (blank - 1,000 = 1,000), where our engine blanks the result. The user's decision
(2026-09-29): probe the other two shapes first, then fix, then the full regression.

1. **A blank `Divide` numerator is already answered, by OI-110's live, discriminating probes**
   (`results/cf-raas/chunk12_oi110_*`): `Product(rate 2.74, Divide(<blank limit>, 100))` priced
   **$3** at ISO. The three readings predict: Divide blank -> Product skips it: $3; Divide skips the
   blank numerator the way `Subtract` skips (leaving 100): $274; blank as 0: $0. So ISO's `Divide`
   with a blank numerator is blank, which is what our engine already does. No new call needed.

2. **A blank SECOND operand of `Subtract`** is the new probe. The Builders Risk Premium Adjustment
   Form detail prices
       If (FormAnnualPremium - AnnualPremiumOfPrecedingReportingPeriod) > 0:
           Premium = Round(FormAnnualPremium - AnnualPremiumOfPrecedingReportingPeriod) x ProRate x cyber
       Else Premium = 0
   and `AnnualPremiumOfPrecedingReportingPeriod` is copied from the detail with `UnitNumber - 1`
   (detail 1 copies the reporting form's premium). A detail numbered 2 with NO detail 1 leaves it
   blank. Predictions for that detail's Basic Group I premium:
       skip the blank (or blank as 0; for a SECOND operand they agree): FormAnnualPremium
       blank the Subtract (our engine today):                           whatever our engine gives
   The control sends details 1 and 2, so detail 2's operand is filled; both must agree there.

    python scripts/cf/205_oi115_probes.py [--live]

Without --live: engine only, predictions printed. With --live: ISO too, responses saved under
results/cf-raas/oi115_*.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(line_buffering=True)

from cf_engine.config import NULL_ARITHMETIC, ROUNDING                   # noqa: E402
from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.interpreter import Interpreter                     # noqa: E402
from gl_engine.interp.tree import Node                                   # noqa: E402
import raas as raas_mod                                                  # noqa: E402

r11 = import_module("118_chunk11_c11-23_raas")
r11.NUMERIC |= {"NewValue", "UnitNumber"}

JURIS, ASOF = "OR", "20260917"
OUT = ROOT / "results" / "cf-raas"
PAF = "CommercialPropertyBuildersRiskPremiumAdjustmentForm"
DET = PAF + "Detail"
PERILS = ("BasicGroupI", "BasicGroupII")


def submission(details):
    building = {
        "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
        "CovType": "Builders Risk", "CauseOfLoss": "Basic", "Coinsurance": "90%",
        "Limit": "100000", "FullBldgValue": "100000", "Deductible": "1,000",
        "LossCostMultiplier": "1.0", "IncludedInBlkt": "No", "PackageModFactor": "1.0",
        "MultiPremiumAndDispersionCreditFactor": "1.0", "NumStories": "1-3", "BCEG": "4",
        "CommercialPropertyBuildersRiskReportingFormTable": {"CommercialPropertyBuildersRiskReportingForm": [{}]},
        PAF + "Table": {PAF: [{DET + "Table": {DET: [
            {"UnitNumber": str(u), "NewValue": str(v), "CoveredCausesOfLoss": "Basic"} for u, v in details]}}]},
    }
    return {"EffDate": "09/17/2026", "CommercialPropertyTable": {"CommercialProperty": [{
        "IRPMFactor": "1.0", "PolicyType": "Commercial Property Policy",
        "CommercialPropertyLocationTable": {"CommercialPropertyLocation": [{
            "ProtectClass": "3", "BasicGroupIRatingTerr": "Portland", "BasicGroupIIRatingTerr": "Entire State",
            "CommercialPropertyStructureTable": {"CommercialPropertyStructure": [building]}}]}}]}}


def engine(sub):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", copy.deepcopy(sub))
    ip.run(data)
    out = {}
    for d in _find(data, DET):
        u = _txt(d, "UnitNumber")
        for p in PERILS:
            cov = d.first(f"{DET}{p}Coverage")
            if cov is None:
                continue
            out[(u, p)] = {k: _txt(cov, k) for k in ("FormAnnualPremium", "AnnualPremiumOfPrecedingReportingPeriod", "Premium")}
    return out, ip


def _find(n, tag):
    if n.tag == tag:
        yield n
    for c in n.children:
        yield from _find(c, tag)


def _txt(n, tag):
    c = n.first(tag)
    return None if c is None else c.text


def iso(sub, name):
    body = r11.payload(sub)
    (OUT / f"oi115_{name}_request.json").write_text(json.dumps(body, indent=1))
    raas_mod.load_env()
    try:
        resp = raas_mod.RaaS().rate(body)
    except raas_mod.RaaSError as e:
        (OUT / f"oi115_{name}_error.txt").write_text(e.body)
        return None, f"REFUSED {e.status}: {e.body[:400]}"
    (OUT / f"oi115_{name}_response.json").write_text(json.dumps(resp, indent=1))
    out = {}
    def walk(o):
        if isinstance(o, dict):
            if DET[len(P := "CommercialProperty"):] and "UnitNumber" in o and any(k.startswith(DET) for k in o):
                u = str(o.get("UnitNumber"))
                for p in PERILS:
                    cov = o.get(f"{DET}{p}Coverage")
                    if isinstance(cov, dict):
                        out[(u, p)] = {k: cov.get(k) for k in ("FormAnnualPremium", "AnnualPremiumOfPrecedingReportingPeriod", "Premium")}
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(resp["Body"])
    msgs = [f"{k}: {it.get('Description')}" for k, items in (resp["Body"].get("RatingMessages") or {}).items() for it in items or []]
    return out, msgs


CASES = [
    ("control", "details 1 and 2: detail 2's prior-period premium is filled", [(1, 150000), (2, 250000)]),
    ("probe", "detail 2 alone: its prior-period premium is BLANK (no detail 1)", [(2, 250000)]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    ok = True
    for i, (name, label, details) in enumerate(CASES, 1):
        sub = submission(details)
        eng, ip = engine(sub)
        print(f"[{i}/{len(CASES)}] {name}: {label}")
        for key, v in sorted(eng.items()):
            fap = v["FormAnnualPremium"]
            print(f"   ours  detail {key[0]} {key[1]:13s} FormAnnualPremium={fap} Prior={v['AnnualPremiumOfPrecedingReportingPeriod']} Premium={v['Premium']}")
        if name == "probe":
            for key, v in sorted(eng.items()):
                print(f"   PREDICTED detail {key[0]} {key[1]}: skip or blank-as-0 -> {v['FormAnnualPremium']}; ours today -> {v['Premium']}")
        if a.live:
            got, msgs = iso(sub, name)
            if got is None:
                print("   ISO", msgs)
                ok = False
                continue
            for key, v in sorted(got.items()):
                print(f"   ISO   detail {key[0]} {key[1]:13s} FormAnnualPremium={v['FormAnnualPremium']} Prior={v['AnnualPremiumOfPrecedingReportingPeriod']} Premium={v['Premium']}")
            for m in msgs:
                print("   ISO message:", m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
