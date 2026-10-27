#!/usr/bin/env python3
"""OI-108 -- ISO's own answer for a blanket drone's TotalScheduleLimit.

ISO fixture STC_CP000015474 (GA), its one Contents drone switched to blanket
(BlanketLimitOfInsurance 99,000), sent live at 2026-09-17 as CA, NC and MO
(20230801 V02/V03 parents, where our engine reads 0) and as GA and OR
(20260601, where it reads 99,000). Compares TotalScheduleLimit and the drone
premiums, ours against ISO's.

    python scripts/cf/135_chunk12_oi108_raas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

import raas as raas_mod                                        # noqa: E402

fam = import_module("132_chunk12_family_raas")
ops = fam.ops
UA = ops.UA_PP
ISO_CF = ops.ISO_CF


#: A CA, NC and MO fixture that ISO rates cleanly at 2026-09-17 (EQTerr moved
#: to a filed territory), each with a Contents record to hang the drone on.
BASES = {"CA": "STC_CP000013263.json", "NC": "STC_CP000014290.json",
         "MO": "STC_CP000011876.json", "GA": "STC_CP000015474.json"}


def _load(name):
    import re
    p = next(ISO_CF.rglob(f"STC/{name}"))
    t = p.read_text(encoding="utf-8-sig")
    st = json.loads(t)["SchemeKeys"]["ProductName"].split()[-1]
    terr = (fam.filed_eqterrs(st) or ["1"])[0]
    return json.loads(re.sub(r'("EQTerr"\s*:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{terr}"', t))


def _first(o, key):
    stack = [o]
    while stack:
        x = stack.pop(0)
        if isinstance(x, dict):
            if key in x:
                return x
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)


def payload(st: str, blanket: bool) -> dict:
    """The Georgia fixture's Contents drone record, grafted onto a real `st`
    fixture's first Contents record; switched to blanket when asked."""
    drone = json.loads(json.dumps(_first(_load(BASES["GA"]), UA)[UA]))
    det = drone[0][UA + "Detail"][0]
    if blanket:
        det["BlanketCoverageUnmannedAircraftAppliesToUnmannedAircraftNotIndividuallyDescribed"] = "Yes"
        det["BlanketLimitOfInsurance"] = det["LimitOfInsurance"]
    d = _load(BASES[st])
    pp = _first(d, "CommercialPropertyPersonalProperty")["CommercialPropertyPersonalProperty"]
    (pp[0] if isinstance(pp, list) else pp)[UA] = drone
    return d


def ours(st, d):
    """TotalScheduleLimit and drone premiums from our engine on the same payload."""
    from cf_engine.config import NULL_ARITHMETIC, ROUNDING
    from cf_engine.resolve import book_for
    from gl_engine.interp.interpreter import Interpreter
    from gl_engine.interp.tree import Node
    esub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
    esub.update(ops.to_engine({"CommercialProperty": d["CommercialProperty"]}))
    ip = Interpreter(book_for(st, "20260917"), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{st}", esub)
    ip.run(data)
    stack, tsl = [data], None
    while stack:
        n = stack.pop()
        if n.tag == UA:
            tsl = next((c.text for c in n.children if c.tag == "TotalScheduleLimit"), None)
        stack.extend(n.children)
    return tsl, {k: v for k, v in fam.ours_premiums(data, "UnmannedAircraft").items() if fam.dr.num(v)}


def iso_tsl(resp):
    vals = [r.get("TotalScheduleLimit") for r in (fam.r11.find(resp, UA) or [])
            for r in (r if isinstance(r, list) else [r]) if isinstance(r, dict)]
    return vals[0] if vals else None


def main() -> int:
    client = raas_mod.RaaS()
    out = fam.OUT
    for st in ("CA", "NC", "MO", "GA"):
        for blanket in (False, True):
            d = payload(st, blanket)
            o_tsl, o_prem = ours(st, d)
            req = {"header": {"quoteback": "", "authorization": {}},
                   "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                           "EffectiveDateTime": fam.EFFECTIVE},
                            "CommercialProperty": d["CommercialProperty"]}}
            tag = f"chunk12_oi108_{st}_{'blanket' if blanket else 'scheduled'}"
            (out / f"{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
                (out / f"{tag}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
                iso = iso_tsl(resp)
                prem = {k: v for k, v in fam.iso_premiums(resp, "UnmannedAircraft").items() if v}
            except raas_mod.RaaSError as exc:
                (out / f"{tag}_refusal.json").write_text(str(exc.body), encoding="utf-8")
                iso, prem = f"REFUSED {str(exc.body)[:200]}", {}
            print(f"  {st} {'blanket  ' if blanket else 'scheduled'}  TotalScheduleLimit ours {o_tsl}  ISO {iso}")
            print(f"        premiums ours {o_prem}")
            print(f"        premiums ISO  {prem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
