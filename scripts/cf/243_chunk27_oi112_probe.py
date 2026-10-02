#!/usr/bin/env python3
"""Chunk 27 C27-14, OI-112: why ISO clears the multiple-deductible form's cause-of-loss answers on older editions. Live ISO.

Found 2026-10-02: no rule in any package writes AllCoveredCausesOfLoss / AllCoveredCausesOfLossExceptTheft / Theft, and
the DataDef declares them alike in every edition; but the FORM FIELD definitions differ: CW 2026 V01 makes them RADIO with
the YesNo domain (default "No"), CW 2023 V02 / V03 / V04 make them CHECKBOX with no domain. The message rule tests "Yes"
in every edition.

Readings, each predicting something different on one state per edition (MA: 2023 V04; OR: 2026 V01 control):
  (a) ISO's request view coerces a CHECKBOX field to a boolean and drops a value it cannot read: "Yes" cleared (message
      fires, echo omits it), and no value can satisfy the "Yes" test on 2023 editions (message fires for every value)
  (b) the same, but a checkbox value it can read ("True" / "1") is kept as that text: still not "Yes", message fires,
      but the echo carries "True" / "1"
  (c) not the form field at all: OR clears "Yes" too
Ours keeps any value and fires the message unless it is "Yes".

    python scripts/cf/243_chunk27_oi112_probe.py [--live]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

c4 = import_module("237_chunk26_rc4")
r2 = import_module("239_chunk27_rc2")
c23, t2, rep, gc, P, TAGGED, lvl = r2.c23, r2.t2, r2.rep, r2.gc, r2.P, r2.TAGGED, r2.lvl
MD = P + "MultipleDeductibleFormFixedDollarDeductibles"
MSG = "Please select at least one Covered Cause Of Loss"
FIELDS = ("AllCoveredCausesOfLoss", "Deductible")


def tree(j, value):
    def b():
        sub = c4.state_policy(j)()
        st = c4.m.at(sub)[P + "Structure"]
        st[MD + "Table"] = {MD: [{"AllCoveredCausesOfLoss": value, "Deductible": "1,000"}]}
        return sub
    return b


CASES = {f"{j}-{v}": (j, v) for j, vals in (("OR", ("Yes",)), ("MA", ("Yes", "True", "1", "Y"))) for v in vals}


def echo(resp):
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == MD:
                    for r in (v if isinstance(v, list) else [v]):
                        out.append({f: r.get(f) for f in FIELDS})
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(resp.get("Body", resp))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    import raas as raas_mod
    client = raas_mod.RaaS() if a.live else None
    for cid, (j, v) in CASES.items():
        req = t2.state_req(t2.m20.payload(tree(j, v)()), j)
        TAGGED.clear()
        data, ip = rep.cmp.rate(req)
        ours = MSG in [x for _, x in TAGGED]
        line = f"{cid:9s} sent AllCoveredCausesOfLoss {v!r}: ours message {'FIRES' if ours else 'silent'}"
        if client:
            (gc.OUT / f"chunk27_oi112_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = r2.rate_retry(client, req)
            except raas_mod.RaaSError as exc:
                print(line + f"; ISO REFUSES {str(exc.body)[:200]}")
                continue
            (gc.OUT / f"chunk27_oi112_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            isos = [x for _, x in c23.iso_tagged(resp)]
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [k for k, v_ in ipr.items() if not rep.cmp.same(v_, opr.get(k))]
            line += (f"; ISO message {'FIRES' if MSG in isos else 'silent'}, echo {echo(resp)}; "
                     f"premiums {len(ipr) - len(dd)} of {len(ipr)} equal; scheme {resp.get('Header', {}).get('Scheme')}")
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
