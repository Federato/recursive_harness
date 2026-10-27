#!/usr/bin/env python3
"""Chunk 28 C28-10 (set C): OI-114, a `<rul:Null/>` operand of `And` / `Or` in ISO's older builds. No engine change.

ISO's 2019 / 2020 countrywide builds replaced invalid paths with `<rul:Null/>` inside an `And` in
`Structure.DoMessageAtLeastOneBuildingOrPersonalPropertyRecordMustBeBlanketRatedToApplyMarginClause` (and four rules in
CW 2019, FL 2019, NC 2023-08 / 2024-02). Ours refuses the test ("a condition evaluated to NoneType"), so every policy on
those parents raises; ISO rates. Readings for a null operand of `And` / `Or`:
  F  false          T  true
In the margin clause rule the same `And` also holds `Equal(<Null/>, "Yes")`, false under any reading, so F and T give
the same answer there: no filed probe separates them on that rule (the register asked for one; this is the finding).
A variant only touches a request that raises today, so the stored back-dated requests ISO rated are the whole
population: ours under F and under T, every premium and (level, message) against ISO's response.

    python scripts/cf/252_chunk28_c28-10_oi114_null_in_and.py
"""
from __future__ import annotations

import collections
import glob
import json
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

from gl_engine.interp import nodes                                       # noqa: E402

c23 = import_module("221_chunk23_rc3")
rep, TAGGED, lvl, OUT = c23.rep, c23.TAGGED, c23.lvl, c23.gc.OUT
ORIG = nodes._operand_bools


def variant(as_bool):
    def ob(ip, el, ch, fr):
        if ch.tag.split("}", 1)[-1] == "Null":
            return [as_bool]
        return ORIG(ip, el, ch, fr)
    return ob


def ours(req):
    TAGGED.clear()
    data, ip = rep.cmp.rate(req)
    return collections.Counter((lvl(t), x) for t, x in TAGGED), rep.our_prem(data)


def main():
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json"))
                  if Path(f[:-len("_request.json")] + "_response.json").exists())
    affected = []
    for f in reqs:
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        nodes._operand_bools = ORIG
        try:
            ours(req)
        except Exception as exc:                      # noqa: BLE001
            if "NoneType, not a boolean" in str(exc):
                affected.append(f)
    print(f"{len(reqs)} stored requests ISO rated; {len(affected)} raise today on a null condition (OI-114)\n")
    fail = 0
    for f in affected:
        name = Path(f).name[:-len("_request.json")]
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        resp = json.loads(Path(f[:-len("_request.json")] + "_response.json").read_text(encoding="utf-8"))
        isos, ipr = collections.Counter(c23.iso_tagged(resp)), rep.iso_prem(resp)
        for tag, b in (("F", False), ("T", True)):
            nodes._operand_bools = variant(b)
            try:
                msgs, prem = ours(req)
            except Exception as exc:                  # noqa: BLE001
                print(f"  {name:22s} {tag}: raises {type(exc).__name__}: {str(exc)[:110]}")
                fail += 1
                continue
            dd = [k for k in ipr if not rep.cmp.same(ipr[k], prem.get(k))]
            print(f"  {name:22s} {tag}: premiums {len(ipr) - len(dd)} of {len(ipr)} equal to ISO; messages "
                  f"{'equal' if msgs == isos else 'DIFFER'} (ISO {sum(isos.values())}, ours {sum(msgs.values())})"
                  + "".join(f"\n        {k[-80:]} ISO {ipr[k]} ours {prem.get(k)}" for k in dd[:4])
                  + "".join(f"\n        ISO only {x[:100]}" for (_, x) in (isos - msgs))
                  + "".join(f"\n        ours only {x[:100]}" for (_, x) in (msgs - isos)))
    nodes._operand_bools = ORIG
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
