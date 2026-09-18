#!/usr/bin/env python3
"""Chunk 7, task C7-08 -- the chunk's claims, confirmed against ISO.

**Five calls, each testing a different structural claim.**

  OR Basic    CONTROL. Basic Group I **$39** and Basic Group II **$123** --
              the first carrying the borrowed FINISHED rate, the second the
              borrowed numeric value of 8.
  OR Broad    **$23**, off a hardcoded `"Frame"`.
  OR Special  **$47**, off `"Frame"` AND `"Other than Apartments and
              Condominiums"`.
  OR, parent  **THE CALL THAT MATTERS.** Remove the Special Class item's
  no ded      deductible: the ITEM prices at **$0 / $0** and Business Income
              **stays at $39 / $123**. The deductible is applied at the
              parent's final-rate step and Business Income copies the rate two
              steps earlier. If ISO disagrees, the whole borrowed-rate reading
              is wrong.
  FL Basic    **$0**, inherited from chunk 6 -- and predicted to be REFUSED,
              the same OI-99 divergence chunk 6 recorded.

**PR is excluded** (OI-86) and is also the only jurisdiction filing its own
Broad base rate and leasehold theft factor for this group.

    python scripts/cf/53_chunk7_raas.py [--dry-run]

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

raas6 = import_module("44_chunk6_raas")
newyork = import_module("06_raas_newyork")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")

PRODUCT, EFFECTIVE = newyork.PRODUCT, newyork.EFFECTIVE
BI = g7.BI
P7 = {f: g7._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
P6 = {f: g6._P % f for f in ("BasicGroupI", "BasicGroupII")}

ISO_REFUSES = {"FL Basic"}

#: id, state, cause of loss, item overrides, {form: premium}, {item form: premium}, why
CASES = [
    ("OR Basic", "OR", "Basic", {},
     {"BasicGroupI": 39, "BasicGroupII": 123}, {"BasicGroupI": 66,
                                                "BasicGroupII": 209},
     "control -- the borrowed finished rate and the borrowed numeric value"),
    ("OR Broad", "OR", "Broad", {}, {"Broad": 23}, {},
     "a hardcoded \"Frame\""),
    ("OR Special", "OR", "Special", {}, {"Special": 47}, {},
     "\"Frame\" AND \"Other than Apartments and Condominiums\""),
    ("OR no ded", "OR", "Basic", {"Deductible": None},
     {"BasicGroupI": 39, "BasicGroupII": 123},
     {"BasicGroupI": 0, "BasicGroupII": 0},
     "**the call that matters** -- the parent prices at zero and the child "
     "does not move"),
    ("FL Basic", "FL", "Basic", {}, {"BasicGroupI": 0}, {},
     "inherited from chunk 6, and predicted to be REFUSED (OI-99)"),
]


def payload(state, col, over):
    item = dict(raas6.ITEM, CauseOfLoss=col)
    for k, v in over.items():
        if v is None:
            item.pop(k, None)
        else:
            item[k] = v
    rec = {k: (int(v) if k == "Limit" else v)
           for k, v in dict(g7.RECORD, CauseOfLoss=col).items()}
    rec["LossCostMultiplier"] = 1.0
    item["CommercialPropertySpecialClassBusnIncome"] = [rec]
    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": PRODUCT.format(state=state),
                           "EffectiveDateTime": EFFECTIVE},
            "CommercialProperty": [{
                "State": state,
                "IRPMFactor": 1.0,
                "PolicyType": "Commercial Property Policy",
                "CommercialPropertyLocation": [{
                    "ProtectClass": "3",
                    "BasicGroupIIRatingTerr": "Entire State",
                    "CommercialPropertySpecialClass": [item],
                }],
            }],
        },
    }


def tree(state, col, over):
    sub = g7.submission(col)
    item = g6.item(sub)
    for k, v in over.items():
        if v is None:
            item.pop(k, None)
        else:
            item[k] = str(v)
    return sub


def engine(state, col, over, forms, item_forms):
    book = book_for(state, g7.ASOF)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", tree(state, col, over))
    ip.run(data)
    return ({f: read(P7[f], data) for f in forms},
            {f: read(P6[f], data) for f in item_forms}, len(ip.messages))


def coverage_premiums(obj, prefix, suffix="Coverage"):
    out = {}

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if (k.startswith(prefix) and k.endswith(suffix)
                        and isinstance(v, dict) and "Premium" in v):
                    out[k[len(prefix):-len(suffix)]] = v["Premium"]
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(obj)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print("Chunk 7, task C7-08 -- ISO confirmation\n")
    print("PREDICTIONS, written before any call:\n")
    for tag, _, _, _, exp, item_exp, why in CASES:
        vals = " + ".join(f"{k} ${v}" for k, v in exp.items())
        extra = ("   item: " + " + ".join(f"{k} ${v}"
                                          for k, v in item_exp.items())
                 if item_exp else "")
        print(f"  {tag:12s} {vals}{extra}")
        print(f"     {why.replace('**', '')}\n")

    if a.dry_run:
        for tag, state, col, over, *_ in CASES:
            print(f"--- payload {tag} " + "-" * 40)
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
    for tag, state, col, over, exp, item_exp, _ in CASES:
        name = f"{state}_chunk7_{col}" + ("_noded" if over else "")
        print("=" * 72)
        print(f"{name} -- predicted "
              + " + ".join(f"{k} ${v}" for k, v in exp.items()))

        mine, item_mine, nmsg = engine(state, col, over, exp, item_exp)
        agree = (all(str(mine[f]) == str(v) for f, v in exp.items())
                 and all(str(item_mine[f]) == str(v)
                         for f, v in item_exp.items()))
        print(f"  engine : BI {mine}" + (f"  item {item_mine}" if item_exp else "")
              + ("" if agree else "   <-- ENGINE DISAGREES, stop"))
        if not agree:
            ok = False
            continue

        try:
            resp = client.rate(payload(state, col, over))
        except raas_mod.RaaSError as exc:
            expected = tag in ISO_REFUSES
            print(f"  REFUSED  status={exc.status}"
                  + ("   <-- PREDICTED" if expected else "")
                  + f"\n  {str(exc.body)[:420]}")
            if expected:
                (out / f"{name}_refusal.json").write_text(str(exc.body),
                                                          encoding="utf-8")
                print("  **ISO refuses where we return $0** -- OI-99, reached "
                      "here through a PARENT\n  that cannot rate rather than "
                      "through this coverage's own lookup.")
                continue
            ok = False
            continue

        by_bi = coverage_premiums(
            resp, "CommercialPropertySpecialClassBusnIncome")
        by_item = coverage_premiums(resp, "CommercialPropertySpecialClass")
        for form, want in exp.items():
            iso = by_bi.get(form)
            hit = (iso is None and want == 0) or (
                iso is not None and abs(float(iso) - want) < 0.005)
            ok &= hit
            print(f"     BI {form:14s} expected ${want:<5d} ISO "
                  f"{'(absent)' if iso is None else iso}  "
                  f"{'MATCH' if hit else 'NO MATCH'}")
        for form, want in item_exp.items():
            iso = by_item.get(form)
            hit = (iso is None and want == 0) or (
                iso is not None and abs(float(iso) - want) < 0.005)
            ok &= hit
            print(f"     ITEM {form:12s} expected ${want:<5d} ISO "
                  f"{'(absent)' if iso is None else iso}  "
                  f"{'MATCH' if hit else 'NO MATCH'}")
        msgs = newyork.messages(resp)
        print(f"  ISO    : {len(msgs)} messages (engine raised {nmsg})")
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
