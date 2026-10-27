#!/usr/bin/env python3
"""Settle the New York question against ISO's own rating service.

New York cannot be rated by this engine. `DoMessageTerrorismPremiumCannotExceed
25PercentOfTheTotalNonTerrorismPolicyPremium` -- filed in exactly one package in
the whole corpus, New York's -- subtracts policy-level `Premium` with no null
guard, and `Premium` is not written until `ErcCalculateTotalPremium`, which the
`Default` block runs AFTER `ErcProcess`. The rule therefore reads a null for
every New York submission. Contract 12.3 says a null reaching arithmetic is a
refusal, so the engine stops.

Two explanations fit every byte on disk, and they have opposite consequences:

  H1  ISO's runtime coerces null to zero in arithmetic.
      Then the rule is harmless -- `0 > (0-0) x 0.25` is false, no message, the
      rating completes. But contract 12.3 would be WRONG FOR THIS CORPUS, which
      is a far bigger finding than New York: it would mean nulls have been
      silently becoming zeros in ISO's engine everywhere, including GL.

  H2  The filed rule is defective.
      Then ISO's engine meets the same null we do, and New York property rating
      is broken at the source -- reportable to ISO, and not ours to fix.

**The predictions are written down BEFORE the call**, so the result is decisive
either way rather than something to interpret afterwards.

Three calls, in this order:

  1. OREGON, the control. The engine rates it to $261 and every intermediate
     matches a hand-derivation. If ISO disagrees with Oregon, the payload shape
     or the product name is wrong and the New York result means nothing. The
     control is not optional -- without it a New York failure is unattributable.

  2. NEW YORK, the question.

  3. NEW YORK with a terrorism premium, to separate H1a from H1b.

RESULT, 2026-09-17
------------------
  OR   ISO returns $261.00 -- IDENTICAL to the engine, and both of ISO's
       validation messages match both of ours. Chunk 1 is confirmed against
       the only authority that matters.
  NY   ISO returns $396.00 -- exactly the figure predicted from New York's own
       rows. So ISO does NOT refuse where we do, and the countrywide-chain
       prediction holds for New York despite its five rule overrides.
  NY+  Does not discriminate, for a reason worth more than the call: no rule
       anywhere writes `TerrorismPremium` at the POLICY level, so the rule's
       first operand is always 0 and the message can never fire under either
       hypothesis. See the notes on that case below.

**So H2 is dead and H1 is confirmed -- ISO completes where we stop -- but H1a
(null coerced to zero) versus H1b (their `Premium` is populated by then) is
still OPEN, and this rule cannot settle it.**

    python scripts/cf/06_raas_newyork.py [--dry-run]

`--dry-run` prints every payload and prediction and calls nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

scripts = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(scripts))
import raas as raas_mod                                        # noqa: E402

golden = import_module("01_golden_case")

EFFECTIVE = "2026-09-17T00:00:00"

#: ISO's product-name convention, from the GL payloads in `Payloads/<ST>/`:
#: `"General Liability OR"`. The Property equivalent is inferred, and if it is
#: wrong ISO says so in a way that is unmistakable (a scheme/product error, not
#: a rating one) -- which is itself worth knowing on the first call.
PRODUCT = "Commercial Property {state}"


def payload(state: str, territory: str, terror: float | None = None) -> dict:
    """Golden case A, as a RAaS submission.

    The `...Table` wrapper every path in the rules uses is NOT present in the
    JSON -- ISO's own GL payloads nest `GeneralLiabilityLocation` directly under
    `GeneralLiability`, not `GeneralLiabilityLocationTable/...`. The same
    flattening is assumed here, **and ISO confirmed it on the first call**: the
    only complaint was about value types, which means the product name, the
    message names and the whole nesting had already been accepted.

    **Decimal fields must be JSON numbers, not strings.** Our own data tree
    stores every value as text and coerces on read, so the first version of
    this sent `"1.0"` and ISO answered:

        Element value 'IRPMFactor' has unexpected type of 'String'
        (was expecting 'Decimal')

    ...for all four factor fields. Worth noting as a real difference in
    strictness: ISO's JSON binding is typed, our tree is not.
    """
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {
                "ProductName": PRODUCT.format(state=state),
                "EffectiveDateTime": EFFECTIVE,
            },
            "CommercialProperty": [{
                "State": state,
                "IRPMFactor": 1.0,
                "CommercialPropertyLocation": [{
                    "BasicGroupIRatingTerr": territory,
                    "ProtectClass": "3",
                    "CommercialPropertyStructure": [{
                        "RatingType": "Class",
                        "ClassCode": "0951",
                        "ConstructionType": "Frame",
                        "CovType": "Building",
                        "CauseOfLoss": "Basic Group I",
                        "Coinsurance": "90%",
                        "Limit": 100000,
                        "FullBldgValue": 100000,
                        "Deductible": "1,000",
                        "LossCostMultiplier": 1.0,
                        "IncludedInBlkt": "No",
                        "PackageModFactor": 1.0,
                        "MultiPremiumAndDispersionCreditFactor": 1.0,
                        # `SetTerrorismPremium` copies `TerrorOverridePremium`
                        # straight through when `TerrorismOverride` is "Yes" --
                        # the shortest way to put a known, small terrorism
                        # premium on the policy without modelling terrorism.
                        **({"TerrorismOverride": "Yes",
                            "TerrorOverridePremium": terror} if terror else {}),
                    }],
                }],
            }],
        },
    }


CASES = [
    ("OR", "Portland", 261,
     "CONTROL. Our engine rates this to $261 with every intermediate traced.\n"
     "     ISO agreeing confirms the payload shape, the product name and the\n"
     "     whole chunk 1 chain against the only authority that matters.\n"
     "     ISO disagreeing invalidates the New York call below -- fix this\n"
     "     first, and read nothing into New York until it passes."),
    ("NY", "Remainder of State", 396,
     "THE QUESTION. Our engine REFUSES this one. $396 is predicted from New\n"
     "     York's own filed rows using the COUNTRYWIDE chain -- and New York\n"
     "     overrides five of those rules, so the figure is a hypothesis, not a\n"
     "     certainty.\n"
     "       * a premium, no terrorism message  -> H1 (ISO coerces null to 0).\n"
     "         Contract 12.3 needs re-examining corpus-wide, GL included.\n"
     "       * an error, or that message fires   -> H2 (the filed rule is\n"
     "         defective). Reportable to ISO; New York stays blocked.\n"
     "       * 401 / not entitled                -> unanswerable this way."),
    ("NY", "Remainder of State", None,
     "THE DISCRIMINATOR, added after the first two calls came back.\n"
     "     $396 and no message is consistent with TWO different things, and\n"
     "     the difference matters enormously:\n"
     "       H1a ISO coerces null to zero. Then the test is\n"
     "           `T > (0 - T) x 0.25`, which for ANY T > 0 is TRUE, so the\n"
     "           message fires on every policy carrying terrorism premium.\n"
     "       H1b ISO's `Premium` is already populated when validation runs --\n"
     "           i.e. OUR RULE ORDERING is what differs, not ISO's treatment\n"
     "           of nulls. Then the test is the genuine 25% one and a small\n"
     "           terrorism premium produces NO message.\n"
     "     With TerrorOverridePremium = 10 against a ~$400 policy, 10 is far\n"
     "     under 25%, so:  message fires -> H1a.  No message -> H1b.\n"
     "     H1a would mean contract 12.3 is wrong corpus-wide, GL included.\n"
     "     H1b is a narrow ordering fix and leaves 12.3 untouched.", 10),
]


def find_premium(obj, depth=0):
    """Every `Premium`-ish leaf in ISO's response, with its path."""
    out = []
    if depth > 12:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (int, float, str)) and "premium" in k.lower():
                out.append((k, v))
            else:
                out += find_premium(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            out += find_premium(v, depth + 1)
    return out


def messages(resp):
    """ISO's own validation messages, as text.

    These are half the response and a comparison that ignores them compares
    half the answer -- which is the whole point of this particular run.
    """
    block = (resp.get("Body") or {}).get("RatingMessages") or {}
    out = []
    for kind, items in block.items():
        for item in items or []:
            if isinstance(item, dict):
                out.append((kind, item.get("Description", "")))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Property -- settling the New York null against ISO's service\n")
    for state, terr, expect, why, *_ in CASES:
        label = f"{state} ({terr})" + ("  +terrorism 10" if _ else "")
        print(f"  {label}, predicted " + (f"${expect}" if expect else "(no premium prediction)"))
        print(f"     {why}\n")

    if a.dry_run:
        for state, terr, *rest in CASES:
            print(f"--- payload {state} " + "-" * 50)
            print(json.dumps(payload(state, terr, rest[2] if len(rest) > 2 else None), indent=2))
        return 0

    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    results = {}
    for case in CASES:
        state, terr, expect, _ = case[:4]
        terror = case[4] if len(case) > 4 else None
        label = f"{state}{' +terrorism' if terror else ''}"
        print("=" * 72)
        print(f"{label} -- calling ISO")
        try:
            resp = client.rate(payload(state, terr, terror))
        except raas_mod.RaaSError as exc:
            print(f"  REFUSED  status={exc.status}")
            print(f"  {exc.body[:1200]}")
            results[label] = ("error", exc.status, exc.body[:400])
            if state == "OR" and not terror:
                print("\n  The control failed. Nothing can be concluded about "
                      "New York from this run.")
                break
            continue

        prem = find_premium(resp)
        msgs = messages(resp)
        print(f"  premium-ish fields ({len(prem)}):")
        for k, v in prem[:12]:
            print(f"     {k} = {v}")
        print(f"  rating messages ({len(msgs)}):")
        for k, v in msgs[:12]:
            print(f"     [{k}] {v}")
        terror_msg = any("Terrorism Premium cannot exceed" in v for _, v in msgs)
        if terror is not None:
            print(f"\n  >>> terrorism message fired: {terror_msg}")
            print("  >>> THIS CASE DOES NOT DISCRIMINATE, and saying so is the")
            print("      result. It was designed to, and it does not, because")
            print("      `TerrorOverridePremium` sets `TerrorismPremium` on the")
            print("      STRUCTURE, while the rule reads it at the POLICY level.")
            print("      Enumerated after the fact: **no rule anywhere in either")
            print("      package writes `TerrorismPremium` in the")
            print("      `CommercialProperty` datadef group** -- zero writers in")
            print("      countrywide, zero in New York. So the rule's first")
            print("      operand is ALWAYS null, always guarded to 0, and the")
            print("      test is always `0 > (Premium - 0) x 0.25`:")
            print("         Premium null-coerced to 0 -> 0 > 0      -> false")
            print("         Premium populated (396)    -> 0 > 99    -> false")
            print("      Both hypotheses predict no message. The rule can never")
            print("      fire for any submission, so it can never tell them")
            print("      apart. H1a vs H1b remains OPEN.")
        results[label] = ("ok", prem, msgs)

        out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
        out.mkdir(parents=True, exist_ok=True)
        tag = label.replace(" +", "_")
        (out / f"{tag}_response.json").write_text(
            json.dumps(resp, indent=2), encoding="utf-8")
        (out / f"{tag}_request.json").write_text(
            json.dumps(payload(state, terr, terror), indent=2), encoding="utf-8")
        print(f"  saved to results/cf-raas/{tag}_*.json")

    print("\n" + "=" * 72)
    print(f"ISO calls made this run: {client.calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
