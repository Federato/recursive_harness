#!/usr/bin/env python3
"""Chunk 28 C28-04 (set A): what the proposed rule would change, measured with the engine's own switch, no code change.

The proposal: a `SingleResult` lookup that matches no row refuses the policy (Property). The interpreter already carries
it as a measurement switch (`strict_single_result`, env ERC_STRICT_SINGLE_RESULT); this runs our stored requests both
ways. Predicted before the run (2026-10-02):
  RATED     the 1,690 stored requests ISO rated: no new refusal (the 4 old-edition probes already raise: OI-114)
  REFUSED   C28-02's 66 live refusals: ours refuses 65, at ISO's own table; VT E7 still prices (the empty-table fallback
            answers from countrywide, so no lookup misses)

    python scripts/cf/247_chunk28_c28-04_strict_impact.py [--rated] [--refused]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

from gl_engine.interp import interpreter as interp_mod

r2 = import_module("239_chunk27_rc2")
rep, gc = r2.rep, r2.gc
OUT = gc.OUT
STRICT = [False]
_init = interp_mod.Interpreter.__init__


def _init_strict(self, *a, **kw):
    _init(self, *a, **kw)
    self.strict_single_result = STRICT[0]


interp_mod.Interpreter.__init__ = _init_strict


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def rate(req, strict):
    STRICT[0] = strict
    try:
        data, ip = rep.cmp.rate(req)
        prem = rep.our_prem(data)
        return "prices", next((v for k, v in prem.items() if k.endswith("ErcCalculatedTotalPremium")), None)
    except Exception as exc:
        m = re.search(r"SingleResult matched NO row in '(\w+)'", str(exc))
        return ("REFUSES " + m.group(1)) if m else f"raises {type(exc).__name__}: {str(exc)[:90]}", None


def rated():
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json")) if Path(f[:-len("_request.json")] + "_response.json").exists())
    new, old = [], []
    for i, f in enumerate(reqs, 1):
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        a, _ = rate(req, False)
        b, _ = rate(req, True)
        if b.startswith("REFUSES") and not a.startswith(("REFUSES", "raises")):
            new.append((Path(f).name, b))
        elif not a.startswith("prices"):
            old.append((Path(f).name, a))
        if i % 200 == 0 or i == len(reqs):
            progress(i, len(reqs), f"rated by ISO; new strict refusals so far {len(new)}")
    print(f"\nRATED: {len(reqs)} requests ISO rated; NEW refusals under the rule: {len(new)}; already raising without it: {len(old)}")
    for x in new[:40]:
        print("   NEW", x)
    for x in old[:10]:
        print("   already", x)
    return new


def refused():
    rows = json.loads((OUT / "chunk28_c28-02_refusals.json").read_text(encoding="utf-8"))
    look = [r for r in rows if r["now"].get("kind") == "lookup, no row"]
    hit, miss = 0, []
    for i, r in enumerate(look, 1):
        req = json.loads((OUT / r["request"]).read_text(encoding="utf-8"))
        b, _ = rate(req, True)
        ok = b == f"REFUSES {r['now']['matrix']}"
        hit += ok
        if not ok:
            miss.append((r["case"], r["now"]["matrix"], b))
    print(f"\nREFUSED: {len(look)} live ISO refusals; ours under the rule refuses at ISO's own table in {hit}")
    for x in miss:
        print("   differs:", x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rated", action="store_true")
    ap.add_argument("--refused", action="store_true")
    a = ap.parse_args()
    if a.refused:
        refused()
    if a.rated:
        rated()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
