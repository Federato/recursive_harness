#!/usr/bin/env python3
"""Chunk 3, task 8 -- the sweep's findings, confirmed against ISO.

The golden cases are already ISO-confirmed (Broad $16, Special $54). What is
not confirmed is the **sweep**, and specifically the part of it that had to be
rewritten: FL and PR rate Special through their own overriding rule reading a
differently-named table, which the first pass read as "no rate filed".

That reading is currently ours alone. If it is wrong, every Special premium in
those jurisdictions is wrong and nothing in the corpus would say so.

**Five jurisdictions, chosen because each tests a different structural claim.**
Not 47: a call per state would confirm arithmetic that the offline sweep has
already derived from the same rows, and would say nothing extra.

  OR   CONTROL, and not optional. Already confirmed at $16/$54 in the golden
       case, re-sent because a FL or NY disagreement is unattributable without
       a control passing in the same run under the same payload shape.
  FL   **The call that matters.** `SpecialBuildingRate` finds no row for
       Florida, so a table-name reading says Florida cannot rate Special.
       Florida's own rule reads `SpecialBuildingRateNonResidential` instead,
       choosing it on a hardcoded list of 21 class codes. Predicted $38.
  NY   New York files no `DeductibleFactor` of its own, so the countrywide
       0.92 applies where Oregon's own filing gives 0.97. Tests the
       state-declares-it-or-not key choice that every prediction depends on.
  AL   Overrides `SetSpecialBaseRate`, `SetSpecialRate` and `SetBroadRate` and
       still matches a countrywide-shaped prediction. Tests the claim that an
       override is not automatically a divergence.
  OR+  Oregon with `CommercialPropertyTheftExclusion` attached -- task 18's
       0.88 credit, predicted $47. Confirms an endorsement record reaches ISO's
       premium the way it reaches ours.

**PR is excluded, and its absence is a finding rather than an omission.** The
RAaS subscription does not cover Puerto Rico (`NO_ISO` in `scripts/raas.py`,
closed as OI-86 on 2026-08-13). PR is also the jurisdiction whose Special
reading is most unusual -- its own cause-of-loss domain, its own
construction-keyed table -- so **the one state that most wants external
confirmation is the one that can never have it.** That has to be said wherever
a PR premium is presented.

    python scripts/cf/19_chunk3_raas_sweep.py [--dry-run]

`--dry-run` prints every payload and prediction and calls nothing.
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

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
chunk3 = import_module("15_chunk3_golden_case")
newyork = import_module("06_raas_newyork")

STRUCT = chunk2.STRUCT
BROAD, SPECIAL = chunk3.BROAD, chunk3.SPECIAL

PRODUCT = newyork.PRODUCT
EFFECTIVE = newyork.EFFECTIVE

#: state, cause of loss, theft record?, {form: predicted premium}, why
CASES = [
    ("OR", "Broad", False, 16, "control -- already confirmed, re-sent so a "
     "disagreement elsewhere in this run is attributable"),
    ("OR", "Special", False, 54, "control"),
    ("FL", "Broad", False, 16, "Florida's Broad comes off the countrywide "
     "table like everyone else's -- the control half of the FL pair"),
    ("FL", "Special", False, 38, "**the call that matters** -- "
     "`SpecialBuildingRateNonResidential`, reached only through Florida's own "
     "overriding rule. A table-name reading says Florida cannot rate Special "
     "at all"),
    ("NY", "Special", False, 58, "no NY `DeductibleFactor` filing, so the "
     "countrywide 0.92 applies where Oregon's own filing gives 0.97"),
    ("AL", "Special", False, 46, "overrides three rules and still matches a "
     "countrywide-shaped prediction"),
    ("OR", "Special", True, 47, "task 18 -- `CommercialPropertyTheftExclusion` "
     "attached, the 0.88 credit, the record hanging off the STRUCTURE"),
]

#: The building, once. Both builders below read this, so the payload ISO sees
#: and the tree the engine runs cannot drift apart.
BUILDING = {
    "RatingType": "Class",
    "ClassCode": "0951",
    "ConstructionType": "Frame",
    "CovType": "Building",
    "Coinsurance": "90%",
    "Limit": 100000,
    "FullBldgValue": 100000,
    "Deductible": "1,000",
    "LossCostMultiplier": 1.0,
    "IncludedInBlkt": "No",
    "PackageModFactor": 1.0,
    "MultiPremiumAndDispersionCreditFactor": 1.0,
}

THEFT = "CommercialPropertyTheftExclusion"


def payload(state, col, theft):
    """ISO's flattened shape -- no `...Table` wrappers, decimals as numbers.

    No rating territory is supplied, deliberately. Broad and Special key on
    neither, so leaving it out isolates the two forms under test and lets the
    Basic chains price at zero rather than carrying Oregon's territory into
    Florida, where it would mean nothing.
    """
    st = dict(BUILDING, CauseOfLoss=col)
    if theft:
        st[THEFT] = [{}]
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state=state),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": state,
                "IRPMFactor": 1.0,
                "CommercialPropertyLocation": [{
                    "CommercialPropertyStructure": [st],
                }],
            }],
        },
    }


def tree(state, col, theft):
    """The same building in our own shape -- strings, and `...Table` wrappers."""
    st = {k: str(v) for k, v in BUILDING.items()}
    st["CauseOfLoss"] = col
    if theft:
        st[f"{THEFT}Table"] = {THEFT: [{}]}
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {"CommercialProperty": [{
            "IRPMFactor": "1.0",
            "CommercialPropertyLocationTable": {
                "CommercialPropertyLocation": [{
                    "CommercialPropertyStructureTable": {
                        "CommercialPropertyStructure": [st]},
                }]},
        }]},
    }


def engine(state, col, theft):
    book = book_for(state, chunk2.ASOF)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", tree(state, col, theft))
    ip.run(data)
    path = BROAD if col == "Broad" else SPECIAL
    return read(path, data), len(ip.messages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Chunk 3, task 8 -- ISO confirmation of the sweep\n")
    print("PREDICTIONS, written before any call:\n")
    for state, col, theft, expect, why in CASES:
        tag = f"{state} {col}" + (" +theft" if theft else "")
        print(f"  {tag:18s} ${expect}")
        print(f"     {why}\n")

    if a.dry_run:
        for state, col, theft, *_ in CASES:
            print(f"--- payload {state} {col}" + " " + "-" * 44)
            print(json.dumps(payload(state, col, theft), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    ok, out = True, Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    for state, col, theft, expect, _ in CASES:
        tag = f"{state}_chunk3_{col}" + ("_theft" if theft else "")
        print("=" * 72)
        print(f"{tag} -- predicted ${expect}")

        mine, nmsg = engine(state, col, theft)
        print(f"  engine : {mine}"
              + ("" if str(mine) == str(expect) else "   <-- ENGINE DISAGREES "
                 "WITH THE PREDICTION, stop before reading ISO"))
        if str(mine) != str(expect):
            ok = False
            continue

        try:
            resp = client.rate(payload(state, col, theft))
        except raas_mod.RaaSError as exc:
            print(f"  REFUSED  status={exc.status}\n  {exc.body[:800]}")
            ok = False
            if state == "OR" and not theft:
                print("\n  The control failed. Nothing can be concluded about "
                      "FL, NY or AL from this run.")
                break
            continue

        prem = newyork.find_premium(resp)
        msgs = newyork.messages(resp)
        # The coverage premium, not the policy total: Broad and Special layer
        # ON TOP of Basic, and with no territory supplied Basic is zero here --
        # but that is a property of this payload, not something to rely on.
        want = str(expect)
        hit = [(k, v) for k, v in prem if str(v).rstrip("0").rstrip(".")
               == want or str(v) == f"{expect}.00"]
        good = bool(hit)
        ok &= good
        print(f"  ISO    : {'MATCH' if good else 'NO MATCH'} "
              f"-- {len(prem)} premium fields, {len(msgs)} messages "
              f"(engine raised {nmsg})")
        for k, v in prem[:10]:
            print(f"     {k} = {v}")
        for k, v in msgs[:6]:
            print(f"     [{k}] {v}")
        (out / f"{tag}_request.json").write_text(
            json.dumps(payload(state, col, theft), indent=2), encoding="utf-8")
        (out / f"{tag}_response.json").write_text(
            json.dumps(resp, indent=2), encoding="utf-8")
        print(f"  saved to results/cf-raas/{tag}_*.json")

    print("\n" + "=" * 72)
    print(f"ISO calls made this run: {client.calls}")
    print("PR is not in this run and cannot be: the subscription does not "
          "cover it (OI-86).")
    print("So the jurisdiction with the most unusual Special reading in the "
          "corpus is\nthe one jurisdiction that can never be externally "
          "confirmed.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
