#!/usr/bin/env python3
"""Chunk 9, task C9-13 -- ISO confirmation, attempted.

Census section 6 (`67_chunk9_census.py`) already established that 0 of 924
ISO STC payloads elect blanket (`IncludedInBlkt="Yes"`) or carry any
`CommercialPropertyBlanketRating*` record -- re-confirmed directly by this
task (see `docs/CF-CHUNK9-GATE.md`). **That is a fixture question: does ISO's
own request corpus ever ask this question at all?** It does not, so there is
nothing in STC to replay.

This script asks the DIFFERENT, RAaS question chunk 8's `63_chunk8_raas.py`
asked for its own hand-built cases (blanket-elected, builders-risk-with-form
-- also never seen in STC): if we hand-build the request ourselves, in the
same JSON shape chunk 8 already validated against ISO, and send it, does
ISO's live rating service accept a populated blanket submission and rate it?

This is C9-01's golden case (two structures, Building Basic Group I, one
shared `BlktIDNum`, `IncludedInBlkt="Yes"` on both, `BlktRated="Yes"` /
`MUBlktRated="No"` on the policy, a `CommercialPropertyBlanketRating`/
`Detail` record with `TotalLimit=300000`) translated from the engine's own
Node-tree submission shape into the flat RAaS JSON shape `raas.py` sends.

    python scripts/cf/79_chunk9_c9-13_raas.py [--dry-run]

Exit 0 if ISO rates the submission and returns the two premiums the fixed
engine now produces ($255 / $510); exit 2 if the call cannot be made at all
(no credentials/network); exit 1 on any other disagreement or refusal.
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

newyork = import_module("06_raas_newyork")
g9 = import_module("68_chunk9_golden_case")

PRODUCT, EFFECTIVE = newyork.PRODUCT, newyork.EFFECTIVE

BUILDING = {
    "RatingType": "Class",
    "ClassCode": "0951",
    "ConstructionType": "Frame",
    "CovType": "Building",
    "CauseOfLoss": "Basic Group I",
    "Coinsurance": "90%",
    "Deductible": "1,000",
    "LossCostMultiplier": 1.0,
    "IncludedInBlkt": "Yes",
    "BlktIDNum": g9.BLKT_ID,
    "PackageModFactor": 1.0,
    "MultiPremiumAndDispersionCreditFactor": 1.0,
}


def structure(full_value: int) -> dict:
    return dict(BUILDING, Limit=full_value, FullBldgValue=full_value)


def payload() -> dict:
    """C9-01's golden case, in the RAaS JSON shape `60_/63_chunk8_raas.py`
    already proved ISO accepts -- not the engine's internal Node-tree shape
    `68_chunk9_golden_case.py` uses to drive `Interpreter.run` directly."""
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state="OR"),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": "OR",
                "IRPMFactor": 1.0,
                "PolicyType": "Commercial Property Policy",
                # Gate 1 of C9-01's finding 2A: without this,
                # `AttachFormBlanketRating`'s Else deletes the record below.
                "BlktRated": "Yes",
                "MUBlktRated": "No",
                "CommercialPropertyBlanketRating": [{
                    "CommercialPropertyBlanketRatingDetail": [{
                        "UnitNumber": g9.BLKT_ID,
                        "Type": "Building Only",
                        "TypeOfBlanketRating": "Average",
                        "CauseOfLoss": "Basic Group I",
                        "Coinsurance": "90%",
                        "TotalLimit": g9.BLKT_LIMIT,
                    }],
                }],
                "CommercialPropertyLocation": [{
                    "ProtectClass": "3",
                    "BasicGroupIRatingTerr": "Portland",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "CommercialPropertyStructure": [
                        structure(g9.VALUE_A),
                        structure(g9.VALUE_B),
                    ],
                }],
            }],
        },
    }


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

    want_a, want_b = str(g9.PREMIUM_A), str(g9.PREMIUM_B)
    print("Chunk 9, task C9-13 -- ISO confirmation, attempted\n")
    print(f"  predicted (fixed engine): Structure A ${want_a}, "
          f"Structure B ${want_b}\n")

    if a.dry_run:
        print("--- payload -- would be sent, no call made " + "-" * 20)
        print(json.dumps(payload(), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    try:
        resp = client.rate(payload())
    except raas_mod.RaaSError as exc:
        print(f"ISO REFUSED  status={exc.status}")
        print(str(exc.body)[:600])
        (out / "OR_chunk9_blanket_refusal.json").write_text(
            str(exc.body), encoding="utf-8")
        return 1

    prem = find(resp, "Premium")
    nonzero = [p for p in prem if str(p) not in ("0", "0.0")]
    total = find(resp, "ErcCalculatedTotalPremium")
    print(f"  ISOrated : total={total[:1]}  non-zero premiums={nonzero[:6]}")
    hit_a = any(abs(float(p) - float(g9.PREMIUM_A)) < 0.005 for p in prem)
    hit_b = any(abs(float(p) - float(g9.PREMIUM_B)) < 0.005 for p in prem)
    print(f"  ${want_a} present: {'MATCH' if hit_a else 'NO MATCH'}   "
          f"${want_b} present: {'MATCH' if hit_b else 'NO MATCH'}")

    (out / "OR_chunk9_blanket_request.json").write_text(
        json.dumps(payload(), indent=2), encoding="utf-8")
    (out / "OR_chunk9_blanket_response.json").write_text(
        json.dumps(resp, indent=2), encoding="utf-8")

    return 0 if (hit_a and hit_b) else 1


if __name__ == "__main__":
    raise SystemExit(main())
