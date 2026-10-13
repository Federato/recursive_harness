#!/usr/bin/env python3
"""Chunk 28 C28-07 (set C): OI-123's discriminating probe on an IN-FORCE package, GA 2026-06-01 V01.

GA's `Structure.DoMessageCP1053ShouldBeUsedRatherThanCP1054WhenWindstormOrHailIsExcludedOnlyForDirectDamage` tests
`And(CovType not Leasehold / No Coverage, Exist(WindstormOrHailExclusion record), NotExist())`: the last `NotExist`
carries no path (the same build artefact as MO's flood message, OI-123). Two readings:
  ours  an empty NotExist selects the current node: false, so the message NEVER fires
  C     an empty NotExist selects nothing: true, so the message fires on every GA building with the exclusion record
Predicted before the run (2026-10-05): ISO fires it on G1 (C), not on G0; every premium equal on both.

  G0  GA portable building, no windstorm or hail exclusion record            (control)
  G1  the same with a WindstormOrHailExclusion record on the structure

    python scripts/cf/250_chunk28_c28-07_oi123_probe.py [--live]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

c23 = import_module("221_chunk23_rc3")
rep, TAGGED, lvl = c23.rep, c23.TAGGED, c23.lvl
v249 = import_module("249_chunk28_c28-07_variants")
m207 = import_module("207_chunk21_rc1")
P = m207.P
OUT = ROOT / "results" / "cf-raas"
MSG = "CP 10 53 should be used rather than CP 10 54"


def g(excl):
    def b():
        sub = m207.portable("GA")
        if excl:
            m207.rc1.node_dicts(sub)[P + "Structure"][P + "WindstormOrHailExclusionTable"] = {
                P + "WindstormOrHailExclusion": [{}]}
        return sub
    return b


CASES = {"G0": ("GA, no windstorm or hail exclusion (control)", g(False), False),
         "G1": ("GA, a WindstormOrHailExclusion record on the building", g(True), True)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fail, reqs = [], {}
    for cid, (label, build, fires_c) in CASES.items():
        req = rep.cmp.state_req("GA", build())
        reqs[cid] = req
        for v in ("now", "C"):
            v249.use(v)
            msgs, _ = v249.ours(req)
            hit = any(MSG in x for (_, x) in msgs)
            print(f"  {cid} {label}: ours ({v}) {'FIRES' if hit else 'no'} the CP 10 53 message")
        v249.use("now")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17:")
        for cid, (label, build, fires_c) in CASES.items():
            req = reqs[cid]
            (OUT / f"chunk28_c28-07_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:200]}")
                fail.append(cid)
                continue
            (OUT / f"chunk28_c28-07_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            isos = collections.Counter(c23.iso_tagged(resp))
            hit = any(MSG in x for (_, x) in isos)
            data, _ = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [k for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            print(f"  {cid} ISO {'FIRES' if hit else 'does not fire'} the CP 10 53 message "
                  f"({'= C' if hit == fires_c else '!= C'}); premiums {len(ipr) - len(dd)} of {len(ipr)} equal")
            if hit != fires_c or dd:
                fail.append(cid)
    print(f"\nC28-07 OI-123 probe: {'AS PREDICTED' if not fail else 'DIFFER: ' + ', '.join(fail)}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
