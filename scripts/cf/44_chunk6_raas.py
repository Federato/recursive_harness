#!/usr/bin/env python3
"""Chunk 6, task C6-08 -- the chunk's claims, confirmed against ISO.

**Seven calls, each testing a different structural claim.** Not 47: a call per
state would confirm arithmetic the offline sweep already derived from the same
filed rows and would say nothing extra. What needs an outside opinion is the
handful of readings that are currently ours alone.

  OR Basic   CONTROL, and not optional. Basic Group I **$66** and Basic Group
             II **$209**. The Group II number carries the chunk's largest
             single claim: a numeric value of **8**, keyed on the RAW class
             description, multiplying the base rate outright. If that is wrong,
             every Special Class Group II premium in the project is wrong.
  OR Broad   **$14** -- and the base rate comes off a hardcoded `"Frame"`.
  OR Broad   the SAME item re-sent as **Fire Resistive**, predicted **$14
  (FR)       again**. **The call that matters.** Building's Broad moves 0.015
             -> 0.010 on this change; ours must not move at all. A disagreement
             here says the literal is not a literal.
  OR Special **$44**, read from `SpecialBuildingRate` -- the same table
             Building's Special uses, which files no countrywide row.
  FL Basic   **$0.** Florida drops this class from its own 68-row converter, so
             a class that rates countrywide cannot be rated there. A premium
             coming back would mean our N3 reading -- a declared table wins by
             name even when it lacks the row -- is wrong.
  AZ Basic   **$0.** Arizona rewrites the rate step around
             `BasicGroupIReductionCredit`, a LOCATION field read through
             `FromConstant="0.0"`, and the payload does not carry it.
  NY Basic   **$0.** New York files the converter header-only AND deletes the
             rule that reads it.

**Three of the seven predict nothing at all**, which is a shape no previous
chunk's ISO run has had. A zero is the weakest possible confirmation on its
own -- ISO returning no premium proves little -- so each zero is paired with
the control above it in the same run, under the same payload shape.

**PR is excluded, and its absence is a finding rather than an omission.** The
RAaS subscription does not cover Puerto Rico (`NO_ISO` in `scripts/raas.py`,
OI-86). PR is also the only jurisdiction filing a full 213-row Special Class
rate table of its own -- **so the state with the most distinctive filing is the
one that can never be checked.**

    python scripts/cf/44_chunk6_raas.py [--dry-run]

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
newyork = import_module("06_raas_newyork")
g = import_module("41_chunk6_golden_case")

PRODUCT, EFFECTIVE = newyork.PRODUCT, newyork.EFFECTIVE
FR = "Fire Resistive - Reinforced Masonry - Light Steel"

#: The Special Class item, once. Both builders read this, so the payload ISO
#: sees and the tree the engine runs cannot drift apart.
ITEM = {
    "ClassDescription": g.DESC,
    "CovType": "Bldg",
    "Limit": 100000,
    "FullSpecialClassValue": 100000,
    "Coinsurance": "90%",
    "Deductible": "1,000",
    "LossCostMultiplier": 1.0,
    "IncludedInBlkt": "No",
    "IncludedInBuilding": "No",
    "ConstructionType": "Frame",
    "BasicGroupIISymbol": "B",
    "BasicGroupIIRatingTerr": "Entire State",
    "PackageModFactor": 1.0,
    "MultiPremiumAndDispersionCreditFactor": 1.0,
}

#: Cases where ISO is predicted to REFUSE the request rather than return a
#: premium. **This is a divergence from our engine, recorded rather than edited
#: away.** A `rul:Lookup` that finds no row raises a 400 at ISO; our
#: interpreter lets the guarded rule fall through to its `Otherwise` and writes
#: 0.0. Both are readings of the same filing and only ISO's is authoritative --
#: logged as an open item rather than patched into the engine mid-chunk.
ISO_REFUSES = {"FL Basic"}

#: id, state, cause of loss, item overrides, {form: predicted premium}, why
CASES = [
    ("OR Basic", "OR", "Basic", {},
     {"BasicGroupI": 66, "BasicGroupII": 209},
     "control -- and the Group II number carries the chunk's largest claim: "
     "a numeric value of 8, keyed on the raw description"),
    ("OR Broad", "OR", "Broad", {}, {"Broad": 14},
     "the base rate off a hardcoded \"Frame\""),
    ("OR Broad FR", "OR", "Broad", {"ConstructionType": FR}, {"Broad": 14},
     "**the call that matters** -- the same item as Fire Resistive. Building's "
     "Broad moves 0.015 -> 0.010 on this change and ours must not move at all"),
    ("OR Special", "OR", "Special", {}, {"Special": 44},
     "SpecialBuildingRate -- the same table Building's Special uses, which "
     "files no countrywide row"),
    ("FL Basic", "FL", "Basic", {}, {"BasicGroupI": 0},
     "**Florida drops this class from its own converter.** Predicted: our "
     "engine returns $0 and **ISO REFUSES THE REQUEST OUTRIGHT** -- a missed "
     "`rul:Lookup` is an error there, not a zero"),
    ("AZ Basic", "AZ", "Basic", {}, {"BasicGroupI": 0},
     "Arizona rewrites the rate step around a LOCATION field defaulting to 0.0"),
    ("NY Basic", "NY", "Basic", {"loc:BasicGroupIIRatingTerr": "I"},
     {"BasicGroupI": 0, "BasicGroupII": 55},
     "New York files the converter header-only AND deletes the rule, so Group "
     "I cannot reach a rate -- while Group II rates at **$55** off NY's own "
     "120-row table: base 0.063 with **NO numeric multiplier at all**, because "
     "NY deletes both numeric rules AND rewrites the rate rule so it never "
     "reads them. A complete, self-consistent state override. **Territory I, not \"Entire State\"**: New York files "
     "territories I/II/III, and sending Oregon's name is the CA/AK trap chunk "
     "3 hit"),
]


def coverage_premiums(obj):
    """form -> Premium, read from each `...SpecialClass<Form>Coverage` node.

    ISO nests each form's premium under its own coverage element. Matching on
    "any premium field in the document" conflates forms -- and a form that
    prices at zero has NO premium field at all, so absence is the answer for a
    zero rather than a written 0.
    """
    out = {}

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if (k.startswith("CommercialPropertySpecialClass")
                        and k.endswith("Coverage")
                        and isinstance(v, dict) and "Premium" in v):
                    form = k[len("CommercialPropertySpecialClass"):-len("Coverage")]
                    out[form] = v["Premium"]
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(obj)
    return out


def split(over):
    """Item-level overrides, location-level overrides.

    Group II's rating territory is resolved on the LOCATION and copied down --
    setting it on the item is overwritten during shared prep, which is why the
    first New York attempt priced Group II at zero with a perfectly good
    territory in the payload. The `loc:` prefix says where a field really
    lives.
    """
    item = {k: v for k, v in over.items() if not k.startswith("loc:")}
    loc = {k[4:]: v for k, v in over.items() if k.startswith("loc:")}
    return item, loc


def payload(state, col, over):
    """ISO's flattened shape -- no `...Table` wrappers, decimals as numbers."""
    over, loc_over = split(over)
    item = dict(ITEM, CauseOfLoss=col, **over)
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state=state),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": state,
                "IRPMFactor": 1.0,
                # The field whose absence priced Broad and Special at zero in
                # C6-01, and it lives HERE -- four levels above the item.
                "PolicyType": "Commercial Property Policy",
                "CommercialPropertyLocation": [dict({
                    "ProtectClass": "3",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "CommercialPropertySpecialClass": [item],
                }, **loc_over)],
            }],
        },
    }


def tree(state, col, over):
    """The same item in our own shape -- strings, and `...Table` wrappers."""
    over, loc_over = split(over)
    item = {k: str(v) for k, v in dict(ITEM, **over).items()}
    item["CauseOfLoss"] = col
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {"CommercialProperty": [{
            "IRPMFactor": "1.0",
            "PolicyType": "Commercial Property Policy",
            "CommercialPropertyLocationTable": {
                "CommercialPropertyLocation": [dict({
                    "ProtectClass": "3",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "CommercialPropertySpecialClassTable": {
                        "CommercialPropertySpecialClass": [item]},
                }, **{k: str(v) for k, v in loc_over.items()})]},
        }]},
    }


def engine(state, col, over, forms):
    book = book_for(state, chunk2.ASOF)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", tree(state, col, over))
    ip.run(data)
    got = {f: read(g._P % f, data) for f in forms}
    return got, len(ip.messages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Chunk 6, task C6-08 -- ISO confirmation\n")
    print("PREDICTIONS, written before any call:\n")
    for tag, _, _, _, expect, why in CASES:
        vals = " + ".join(f"{k} ${v}" for k, v in expect.items())
        print(f"  {tag:14s} {vals}")
        print(f"     {why.replace('**', '')}\n")

    if a.dry_run:
        for tag, state, col, over, *_ in CASES:
            print(f"--- payload {tag} " + "-" * 44)
            print(json.dumps(payload(state, col, over), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    ok = True
    out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    for tag, state, col, over, expect, _ in CASES:
        name = f"{state}_chunk6_{col}" + ("_FR" if "FR" in tag else "")
        print("=" * 72)
        vals = " + ".join(f"{k} ${v}" for k, v in expect.items())
        print(f"{name} -- predicted {vals}")

        mine, nmsg = engine(state, col, over, expect)
        agree = all(str(mine[f]) == str(v) for f, v in expect.items())
        print(f"  engine : {mine}"
              + ("" if agree else "   <-- ENGINE DISAGREES WITH THE "
                 "PREDICTION, stop before reading ISO"))
        if not agree:
            ok = False
            continue

        try:
            resp = client.rate(payload(state, col, over))
        except raas_mod.RaaSError as exc:
            expected_refusal = tag in ISO_REFUSES
            print(f"  REFUSED  status={exc.status}"
                  + ("   <-- PREDICTED" if expected_refusal else "")
                  + f"\n  {str(exc.body)[:600]}")
            if expected_refusal:
                (out / f"{name}_refusal.json").write_text(
                    str(exc.body), encoding="utf-8")
                print("  **ISO refuses where we return $0.** A missed lookup "
                      "is an error there and a\n  zero here. Recorded as the "
                      "finding; the engine is not edited to match.")
                continue
            ok = False
            if state == "OR" and col == "Basic":
                print("\n  The control failed. Nothing can be concluded about "
                      "FL, AZ or NY from this run.")
                break
            continue

        prem = newyork.find_premium(resp)
        msgs = newyork.messages(resp)
        nonzero = [(k, v) for k, v in prem
                   if str(v) not in ("0", "0.0", "0.00", "None")]
        # **Read the FORM's own premium, not "any premium in the document".**
        # The first draft matched a zero by "no non-zero premium anywhere" and
        # called Arizona a disagreement, when Arizona's Group I is zero exactly
        # as predicted and its Group II legitimately carries $335. A weak
        # matcher turns an agreement into a finding, which is the one direction
        # this harness must never fail in.
        by_form = coverage_premiums(resp)
        good = True
        for form, want in expect.items():
            iso = by_form.get(form)
            hit = (iso is None and want == 0) or (
                iso is not None and abs(float(iso) - want) < 0.005)
            if not hit:
                good = False
            print(f"     {form:14s} expected ${want:<5d} ISO "
                  f"{'(absent)' if iso is None else iso}  "
                  f"{'MATCH' if hit else 'NO MATCH'}")
        ok &= good
        print(f"  ISO    : {len(prem)} premium fields "
              f"({len(nonzero)} non-zero), {len(msgs)} messages "
              f"(engine raised {nmsg})")
        for k, v in nonzero[:8]:
            print(f"     {k} = {v}")
        for k, v in msgs[:5]:
            print(f"     [{k}] {v}")
        (out / f"{name}_request.json").write_text(
            json.dumps(payload(state, col, over), indent=2), encoding="utf-8")
        (out / f"{name}_response.json").write_text(
            json.dumps(resp, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    if ok:
        print("ISO agrees with the engine on every case.")
        return 0
    print("DISAGREEMENTS above -- each one is a finding, not a bug to edit "
          "away.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
