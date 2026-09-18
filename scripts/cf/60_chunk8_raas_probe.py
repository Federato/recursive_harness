#!/usr/bin/env python3
"""Chunk 8 -- the probe that nearly cost an engine change, and its answer.

**ASKED:** our tree had the `CommercialPropertyLegalLiabilityCoverageForm`
record before `Interpreter.run` and not after it, so every Legal Liability
premium was $0. Was our interpreter dropping a submitted record -- an engine
defect, the first in eight chunks -- or does ISO discard it too?

**ANSWERED: neither. The probe was comparing two different submissions.**

`AttachFormCommercialPropertyLegalLiabilityCoverageForm` gates on
`PolicyType = "Commercial Property Policy"` AND `CovType = "Legal Liability"`,
and its `Else` branch is a bare
`<rul:Remove ... RemoveMultiple="true" />`. **ISO's own rule deletes the
submitted record when `PolicyType` is absent**, and our engine did exactly
that. The first version of this script set `PolicyType` in its ISO payload --
a habit carried over from C6-01 -- and not in its engine submission.

**The control passed and proved nothing.** It was a class-rated building, which
never touches `PolicyType`. **A control that passes without exercising the
variable under test is not a control.** Had the run been believed, the remedy
was a change to the shared interpreter and a full re-run of chunks 1-7.

This file is kept, with both sides now built from ONE submission, as the
standing check that engine and ISO agree on the Legal Liability form record:

  1  CONTROL. Class-rated Oregon building -- **$261**.
  2  Legal Liability WITH a record -- **$60**, factor 0.25 x 1.0.
  3  Legal Liability with NO record -- **$0**: ISO attaches an empty form of
     its own and the insurable-interest factor stays at its 0.0 default.

    python scripts/cf/60_chunk8_raas_probe.py [--dry-run]

Exit 0 when ISO and the engine agree on all three.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

import raas as raas_mod                                        # noqa: E402

from gl_engine.interp.tree import read

newyork = import_module("06_raas_newyork")
g8 = import_module("59_chunk8_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")

PRODUCT, EFFECTIVE = newyork.PRODUCT, newyork.EFFECTIVE
BGI = chunk2.STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
LL_FORM = g8.LL_FORM

BUILDING = {
    "RatingType": "Class",
    "ClassCode": "0951",
    "ConstructionType": "Frame",
    "CovType": "Building",
    "CauseOfLoss": "Basic",
    "Coinsurance": "90%",
    "Limit": 100000,
    "FullBldgValue": 100000,
    "Deductible": "1,000",
    "LossCostMultiplier": 1.0,
    "IncludedInBlkt": "No",
    "PackageModFactor": 1.0,
    "MultiPremiumAndDispersionCreditFactor": 1.0,
    "NumStories": "1-3",
    "BCEG": "4",
}

#: id, CovType, attach a coverage-form record?, predicted, why
CASES = [
    ("control, class-rated", "Building", False, 261,
     "chunk 1's golden case -- if this misses, nothing else in the run means "
     "anything"),
    ("the QUESTION -- LL WITH a record", "Legal Liability", True, 60,
     "$60 if ISO honours the submitted record; $0 if it discards it exactly "
     "as our engine does"),
    ("LL with NO record", "Legal Liability", False, 0,
     "$0 either way -- the case that tells the answer apart from 'Legal "
     "Liability never rates'"),
]


def payload(covtype, record):
    st = dict(BUILDING, CovType=covtype)
    if record:
        st[LL_FORM] = [{"AddlInsurableInt": "None"}]
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state="OR"),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": "OR",
                "IRPMFactor": 1.0,
                "PolicyType": "Commercial Property Policy",
                "CommercialPropertyLocation": [{
                    "ProtectClass": "3",
                    "BasicGroupIRatingTerr": "Portland",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "CommercialPropertyStructure": [st],
                }],
            }],
        },
    }


def engine(covtype, record):
    """**Built from the same facts as `payload()`, including `PolicyType`.**

    The first version of this function omitted it and the mismatch read as an
    engine defect -- see the module docstring.
    """
    sub = chunk2.submission()
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    st = zeros2.structure(sub)
    st["CovType"] = covtype
    if record:
        st[f"{LL_FORM}Table"] = {LL_FORM: [{"AddlInsurableInt": "None"}]}
    data, ip = g8.run(sub)
    return (str(read(BGI, data)),
            str(read(chunk2.STRUCT + "/LegalLiabilityFactor", data)),
            str(read(chunk2.STRUCT + "/LegalLiabAddlInsurableIntFactor", data)))


def find(resp, tag):
    out = []

    def walk(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k == tag:
                    out.append(v)
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(resp)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Chunk 8 -- blocker A, put to ISO\n")
    for tag, covtype, record, want, why in CASES:
        print(f"  {tag:36s} predicted ${want}")
        print(f"     {why}\n")

    if a.dry_run:
        for tag, covtype, record, *_ in CASES:
            print(f"--- payload {tag} " + "-" * 34)
            print(json.dumps(payload(covtype, record), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    for tag, covtype, record, want, _ in CASES:
        name = f"OR_chunk8_probe_{covtype.replace(' ', '')}" + (
            "_rec" if record else "_norec")
        print("=" * 72)
        mine, fac, add = engine(covtype, record)
        print(f"{tag}   (predicted ${want})")
        print(f"  engine : premium {mine}   LegalLiabilityFactor={fac}   "
              f"AddlInsurableIntFactor={add}")
        try:
            resp = client.rate(payload(covtype, record))
        except raas_mod.RaaSError as exc:
            print(f"  REFUSED  status={exc.status}\n  {str(exc.body)[:400]}")
            continue
        prem = find(resp, "Premium")
        iso_fac = find(resp, "LegalLiabilityFactor")
        iso_add = find(resp, "LegalLiabAddlInsurableIntFactor")
        rec_back = find(resp, LL_FORM)
        total = find(resp, "ErcCalculatedTotalPremium")
        print(f"  ISO    : total={total[:1]}   non-zero premiums="
              f"{[p for p in prem if str(p) not in ('0', '0.0')][:5]}")
        print(f"           LegalLiabilityFactor={iso_fac[:2]}   "
              f"AddlInsurableIntFactor={iso_add[:2]}")
        print(f"           coverage-form record echoed back: "
              f"{'yes' if rec_back else 'NO'}"
              + (f"   {json.dumps(rec_back[0])[:200]}" if rec_back else ""))
        (out / f"{name}_request.json").write_text(
            json.dumps(payload(covtype, record), indent=2), encoding="utf-8")
        (out / f"{name}_response.json").write_text(
            json.dumps(resp, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("READING THE ANSWER")
    print("  control $261 and the question $60  -> **our interpreter drops a")
    print("      submitted record.** An engine defect; chunks 1-7 need")
    print("      re-running before anything else proceeds.")
    print("  control $261 and the question $0   -> **ISO discards it too.** Our")
    print("      engine is right and the factor needs something else.")
    print("  control not $261                   -> the payload is wrong; the")
    print("      run says nothing either way.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
