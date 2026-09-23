#!/usr/bin/env python3
"""Chunk 11 C11-23 -- does ISO refuse (or price) where our engine returns $0?

Every C11-04 zero case (`117_chunk11_c11-04_zero_cases.py`), plus the golden
case and Group B's Special-with-Theft-Exclusion as controls, is built as an
engine submission, run through OUR engine, then translated to the RAaS JSON
shape chunks 8/9 proved ISO accepts, and sent to ISO's live rating service.
ISO's answer is predicted in `docs/CF-CHUNK11-ZERO-CASES.md` ("What C11-23
has to ask ISO") before this runs.

EffectiveDateTime is sent as 2026-09-17, and every engine submission's EffDate
is moved to 09/17/2026 to match. The first attempt sent 2027-01-01 (the golden
case's EffDate) and ISO priced Basic Group I at $67 against our $268: at
2027-01-01 ISO serves a NEWER Oregon rate edition than our local corpus holds
(BasicGroupIBaseRate 0.125 vs 0.498 for class 0951 Frame -- confirmed by
sending chunk 2's plain Building risk at the same date: also 0.125). Our
engine resolves editions as of 20260917, so the like-for-like comparison is
at that date. The annuity itself matched ISO to the digit at 2027-01-01.
Evidence: results/cf-raas/chunk11_C0_at20270101_*.json.

    python scripts/cf/118_chunk11_c11-23_raas.py [--dry-run] [--only Z6,...]

Requests and responses are saved to results/cf-raas/chunk11_*. Exit 2 if the
call cannot be made (no credentials/network); otherwise 0. This script
REPORTS agreement and divergence -- a divergence is a finding, not a failure.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

import raas as raas_mod                                        # noqa: E402
from gl_engine.interp.tree import read                         # noqa: E402
from gl_engine.interp.values import InterpretError             # noqa: E402

g = import_module("114_chunk11_golden_case")
z = import_module("117_chunk11_c11-04_zero_cases")
b = import_module("116_chunk11_groupB_subcoverages")
newyork = import_module("06_raas_newyork")

PRODUCT = newyork.PRODUCT
EFFECTIVE = "2026-09-17T00:00:00"
ENGINE_EFFDATE = "09/17/2026"
LIREC = "CommercialPropertyLeaseholdInterestCoverageForm"
CELLS = {f"{s}/{f}": f"{LIREC}{s}Coverage{f}Coverage"
         for s in g.SUBCOV for f in g.FORMS}

#: Fields ISO's STC payloads send as JSON numbers; everything else is a string.
NUMERIC = {"Limit", "FullBldgValue", "IRPMFactor", "LossCostMultiplier",
           "PackageModFactor", "MultiPremiumAndDispersionCreditFactor",
           "TenantsGrossLeaseholdInt", "BonusPaymentsMonthlyLeaseholdInt",
           "ImprovementsAndBettermentsMonthly", "PrepaidRentMonthly",
           "EQDeductibleTier"}
DATES = {"LeaseEffDate", "LeaseExpDate"}


def _num(v):
    f = float(v)
    return int(f) if f == int(f) else f


def _date(v):
    m, d, y = v.split("/")
    return f"{y}-{m}-{d}"


def to_raas(node):
    """Engine submission dict -> RAaS JSON: `XTable: {X: [...]}` collapses to
    `X: [...]`, numbers and dates retyped the way ISO's STC payloads type
    them."""
    if isinstance(node, list):
        return [to_raas(n) for n in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k.endswith("Table") and isinstance(v, dict) and len(v) == 1:
            (inner_k, inner_v), = v.items()
            out[inner_k] = to_raas(inner_v)
        elif k in NUMERIC and isinstance(v, str):
            out[k] = _num(v)
        elif k in DATES and isinstance(v, str):
            out[k] = _date(v)
        else:
            out[k] = to_raas(v)
    return out


def payload(sub: dict) -> dict:
    sub = copy.deepcopy(sub)
    for k in ("EffDate", "ExpDate"):       # EffDate travels in SchemeKeys;
        sub.pop(k, None)                   # ExpDate is EffDate + 1y (C11-04 Z5)
    cps = to_raas(sub)["CommercialProperty"]
    for cp in cps:
        cp["State"] = "OR"
    return {"header": {"quoteback": "", "authorization": {}},
            "body": {"SchemeKeys": {"ProductName": PRODUCT.format(state="OR"),
                                    "EffectiveDateTime": EFFECTIVE},
                     "CommercialProperty": cps}}


def cases():
    out = [("C0", "golden case at 09/17/2026 (control)", g.submission(),
            "ISO predicted: same as ours")]
    for cid, tier, label, sub, kind in z.CASES:
        if cid in ("Z5", "Z5b"):
            continue                       # ExpDate is never an input
        out.append((cid, label, sub, {
            "Z6": "OI-102 fixed: ISO and ours both = C0's premiums",
            "Z8": "D2: ISO predicted refusal or $0",
            "Z9": "D2: ISO predicted refusal or $0",
            "Z13": "OI-104 fixed: ISO and ours both $0 (0^0 = 1)",
            "B1": "ISO predicted: same as ours",
            "Z11": "ISO predicted: same as ours (EQ cell $0)",
        }.get(cid, "ISO predicted $0 (same rule)")))
    out.append(("Z12", "Special, no Theft Exclusion (OI-101)",
                b.build(subs=["TenantsLease"], cause="Special"),
                "OI-101: ISO predicted: same as ours (Special $0)"))
    out.append(("S3", "Special + Theft Exclusion (control)",
                b.build(subs=["TenantsLease"], cause="Special", theft_excl=True),
                "ISO predicted: same as ours (Special nonzero)"))
    return out


def at_date(sub):
    sub = copy.deepcopy(sub)
    sub["EffDate"] = ENGINE_EFFDATE
    return sub


def ours(sub):
    try:
        data, _ = g.run(sub)
    except InterpretError as exc:
        return {"_refused": str(exc)[:90]}
    return {k: read(f"{g.LI}/{v}/Premium", data) for k, v in CELLS.items()}


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


def iso_cells(resp):
    """Premium per LI grid cell, or {} if ISO returned no LI record."""
    got = {}
    for k, tag in CELLS.items():
        hits = find(resp, tag)
        for h in (hits if isinstance(hits, list) else [hits]):
            for rec in (h if isinstance(h, list) else [h]):
                if isinstance(rec, dict) and "Premium" in rec:
                    got[k] = rec["Premium"]
    return got


def show(d):
    if "_refused" in d:
        return "REFUSED " + d["_refused"]
    nz = {k: v for k, v in d.items() if v not in (None, "0", 0, 0.0, "0.0")}
    return ", ".join(f"{k.replace('TenantsLease/', 'TL/')}={_num(v)}" for k, v in nz.items()) or "all $0"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    todo = [c for c in cases() if not only or c[0] in only]

    if a.dry_run:
        print(json.dumps(payload(at_date(todo[0][2])), indent=2))
        return 0
    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2

    out = Path(__file__).resolve().parents[2] / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    print(f"Chunk 11 C11-23 -- live ISO, EffectiveDateTime {EFFECTIVE}\n")
    for cid, label, sub, predicted in todo:
        sub = at_date(sub)
        mine = ours(sub)
        req = payload(sub)
        (out / f"chunk11_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
            (out / f"chunk11_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            iso = iso_cells(resp)
            msgs = [m for m in find(resp, "Text") + find(resp, "Message") if isinstance(m, str)]
            iso_s = show(iso) if iso else "NO LI RECORD RETURNED"
            mine_has = "_refused" not in mine and any(v is not None for v in mine.values())
            if not iso and not mine_has and "_refused" not in mine:
                same = True                 # neither side kept an LI record (Z1)
            else:
                same = mine_has and bool(iso) and all(
                    float(iso.get(k) or 0) == float(mine.get(k) or 0) for k in CELLS)
        except raas_mod.RaaSError as exc:
            (out / f"chunk11_{cid}_refusal.json").write_text(str(exc.body), encoding="utf-8")
            iso_s, msgs = f"ISO REFUSED status={exc.status}: {str(exc.body)[:160]}", []
            same = "_refused" in mine
        print(f"  {cid:4s} {label}")
        print(f"       ours : {show(mine)}")
        print(f"       ISO  : {iso_s}")
        print(f"       pred : {predicted}")
        print(f"       {'AGREE' if same else 'DIVERGE'}"
              + (f"   messages: {msgs[:3]}" if msgs else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
