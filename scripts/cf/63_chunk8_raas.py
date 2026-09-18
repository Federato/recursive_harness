#!/usr/bin/env python3
"""Chunk 8, task C8-08 -- ISO confirmation.

Building's $60 and $7 are already confirmed by `60_chunk8_raas_probe.py`, so
this run asks the four things that are still ours alone:

  1  **Contents at $132** -- the `"PersProp"` row of the same two-row table,
     and the half of C8-12 no call has touched.
  2  **Building Broad $4 and Special $12** -- the two forms whose Legal
     Liability branch starts from a RAW rate rather than a cause-of-loss
     adjustment.
  3  **Builders Risk with a Reporting Form record.** Our engine REFUSES:
     the outer `If` has no `Else`, so `Premium` is never written and the
     null-premium guard fires. **The traced map says `Premium = 0.0`.**
     Unwritten and zero are different things -- does ISO return a number or a
     400? This is OI-99 asked from a new direction, and the map's point 10
     depends on the answer.
  4  **Blanket elected on a Legal Liability item** -- `IncludedInBlkt = "Yes"`
     must change nothing, because the Legal Liability branch is matched first.
     Predicted **$60**, identical to the scheduled case (C8-14).

    python scripts/cf/63_chunk8_raas.py [--dry-run]

Exit 0 when ISO agrees with the engine on every case.
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
probe = import_module("60_chunk8_raas_probe")
g8 = import_module("59_chunk8_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")

PRODUCT, EFFECTIVE = newyork.PRODUCT, newyork.EFFECTIVE
BR_FORM = "CommercialPropertyBuildersRiskReportingForm"
_B = chunk2.STRUCT + "/CommercialPropertyStructureBuilding%sCoverage/Premium"
_C = (chunk4.PP
      + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium")

ISO_REFUSES = set()          # filled in by the run, not predicted


def building_payload(covtype="Legal Liability", col="Basic", blkt=False,
                     reporting=False):
    st = dict(probe.BUILDING, CovType=covtype, CauseOfLoss=col)
    if blkt:
        st["IncludedInBlkt"] = "Yes"
    if reporting:
        st[BR_FORM] = [{}]
    if covtype == "Legal Liability":
        st[g8.LL_FORM] = [{"AddlInsurableInt": g8.NONE}]
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state="OR"),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": "OR", "IRPMFactor": 1.0,
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


def contents_payload():
    """Chunk 4's occupancy, with the Legal Liability form on the OCCUPANCY."""
    st = dict(probe.BUILDING, CovType="Building", CauseOfLoss="Basic")
    st.pop(BR_FORM, None)
    st["CommercialPropertyOccupClass"] = [{
        "OccupCategory": "Offices",
        "ClassCode": "0951",
        "CovForm": "Legal Liability Coverage Form",
        g8.LL_OCC: [{"AddlInsurableInt": g8.NONE}],
        "CommercialPropertyPersonalProperty": [{
            "Limit": 100000, "CovType": "Personal Property",
            "IncludedInBlkt": "No", "RatingType": "Class",
            "BldgClassCode": "0951", "LossCostMultiplier": 1.0,
            "Coinsurance": "90%", "Deductible": "1,000",
            "CauseOfLoss": "Basic",
            # Chunk 4 already recorded this: a Contents payload without a
            # wind/hail deductible is refused by ISO on a blank-key lookup of
            # `WindstormOrHailDeductibleAsNumber`. A known payload
            # requirement, not a chunk 8 finding.
            "WindstormOrHailDeductible": "1,000",
        }],
    }]
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state="OR"),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": "OR", "IRPMFactor": 1.0,
                "PolicyType": "Commercial Property Policy",
                "CommercialPropertyLocation": [{
                    "ProtectClass": "3",
                    "BasicGroupIRatingTerr": "Portland",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "SpecialRatingTerr":
                        "Multnomah (including entire city of Portland)",
                    "CommercialPropertyStructure": [st],
                }],
            }],
        },
    }


#: id, payload, engine submission, premium path, form, predicted, why
CASES = [
    ("CONTENTS Basic Group I", contents_payload,
     lambda: g8.contents("Basic"), _C, "BasicGroupI", 132,
     "the PersProp row of the same two-row table -- the half of C8-12 no call "
     "has touched"),
    ("BUILDING Broad", lambda: building_payload(col="Broad"),
     lambda: g8.building("Broad"), _B, "Broad", 4,
     "a RAW BroadRate, not a cause-of-loss adjustment"),
    ("BUILDING Special", lambda: building_payload(col="Special"),
     lambda: g8.building("Special"), _B, "Special", 12,
     "a RAW SpecialRate -- map point 6, Building's half"),
    ("BUILDING blanket elected", lambda: building_payload(blkt=True),
     lambda: _blkt(), _B, "BasicGroupI", 0,
     "**predicted $60 and it is $0 -- on BOTH sides, so they agree and the "
     "PREDICTION was wrong.** The map says a Legal Liability item marked "
     "`IncludedInBlkt = \"Yes\"` still matches branch 2 and rates as "
     "scheduled. It does match branch 2 -- and the premium is nevertheless "
     "zero. **Blanket is not merely unreachable here; electing it zeroes the "
     "coverage.** Engine and ISO agree exactly, which is what makes this a "
     "finding about the map rather than about either of them (C8-14)"),
    ("BUILDERS RISK + reporting form",
     lambda: building_payload(covtype="Builders Risk", reporting=True),
     lambda: _reporting(), _B, "BasicGroupI", None,
     "**the open question.** Our engine refuses -- the outer If has no Else, "
     "so Premium is never written. The map says 0.0. Does ISO return a number "
     "or a 400?"),
]


def _blkt():
    sub = g8.building("Basic")
    zeros2.structure(sub)["IncludedInBlkt"] = "Yes"
    return sub


def _reporting():
    sub = g8.building("Basic")
    st = zeros2.structure(sub)
    st["CovType"] = "Builders Risk"
    st[f"{BR_FORM}Table"] = {BR_FORM: [{}]}
    return sub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Chunk 8, task C8-08 -- ISO confirmation\n")
    for tag, _, _, _, _, want, why in CASES:
        print(f"  {tag:30s} predicted "
              + ("a REFUSAL or a number -- the question" if want is None
                 else f"${want}"))
        print(f"     {why}\n")
    if a.dry_run:
        for tag, pay, *_ in CASES:
            print(f"--- payload {tag} " + "-" * 30)
            print(json.dumps(pay(), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    ok = True
    out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    for tag, pay, sub_fn, path, form, want, _ in CASES:
        print("=" * 72)
        print(tag)
        mine, raised = None, None
        try:
            data, ip = g8.run(sub_fn())
            mine = str(read(path % form, data))
        except Exception as exc:
            raised = f"{type(exc).__name__}"
        print(f"  engine : "
              + (f"REFUSES ({raised})" if raised else f"premium {mine}"))
        try:
            resp = client.rate(pay())
        except raas_mod.RaaSError as exc:
            print(f"  ISO    : REFUSED  status={exc.status}")
            print(f"           {str(exc.body)[:260]}")
            agree = raised is not None
            ok &= agree
            print(f"           {'BOTH REFUSE -- agreed' if agree else 'ISO REFUSES AND WE DO NOT'}")
            (out / f"OR_chunk8_{form}_{tag.split()[0]}_refusal.json").write_text(
                str(exc.body), encoding="utf-8")
            continue
        prem = probe.find(resp, "Premium")
        nonzero = [p for p in prem if str(p) not in ("0", "0.0")]
        total = probe.find(resp, "ErcCalculatedTotalPremium")
        if want is None:
            print(f"  ISO    : RATED. total={total[:1]}  non-zero={nonzero[:4]}")
            print("           **ISO returns a number where we refuse** -- the "
                  "map is right and\n           OI-99 gains a second, opposite "
                  "instance. Recorded, not patched.")
            ok &= raised is None
        else:
            hit = any(abs(float(p) - want) < 0.005 for p in prem)
            ok &= hit and mine == str(want)
            print(f"  ISO    : total={total[:1]}  non-zero={nonzero[:4]}   "
                  f"${want} present: {'MATCH' if hit else 'NO MATCH'}")
        name = f"OR_chunk8_{tag.replace(' ', '_')}"
        (out / f"{name}_request.json").write_text(json.dumps(pay(), indent=2),
                                                  encoding="utf-8")
        (out / f"{name}_response.json").write_text(json.dumps(resp, indent=2),
                                                   encoding="utf-8")

    print("\n" + "=" * 72)
    print("ISO agrees with the engine on every case." if ok
          else "DISAGREEMENTS above -- each one is a finding.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
