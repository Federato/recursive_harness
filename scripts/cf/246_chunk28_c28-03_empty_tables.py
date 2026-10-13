#!/usr/bin/env python3
"""Chunk 28 C28-03 (set A): an EMPTY state table: does ISO fall back to countrywide's rows (rule E1) or refuse (E2)?

Our engine (since 2026-09-28) treats a state table filed with a header and no rows as not filed, so its countrywide
`SingleResult` pass finds countrywide's rows. Wherever that happens, E1 predicts ISO rates and E2 predicts ISO refuses:
the two rules disagree exactly there. Known so far: VT `VacancyPermitFactors` (ISO used countrywide's rows, C18-16) and
VT `EQSubLimitDeductibleTierCWTable` (ISO refused, C19-17 E7).

  --scan    every stored request ISO RATED (a saved response): each `SingleResult` lookup that found its row only because
            the state's table is empty. Each is a case where ISO tolerated an empty state table (evidence for E1).
  --live    probes predicted both ways before each call: VT vacancy re-sent (C18-16's request), and the earthquake tier
            stub tier 1 in every state that files it empty (195_'s builder), each first checked to reach the stub in ours.

    python scripts/cf/246_chunk28_c28-03_empty_tables.py [--scan] [--live]
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

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter

r2 = import_module("239_chunk27_rc2")
rep, gc = r2.rep, r2.gc
OUT = gc.OUT
ASOF = "20260917"
RES = CFEditionResolver()
EMPTY = {}
for j in RES.jurisdictions:
    b = book_for(j, ASOF, resolver=RES)
    sp, cp = Path(str(b.state.package.content)), Path(str(b.parent.package.content))
    for f in (sp / "Rate Tables").glob("*.RateTable.csv"):
        if sum(1 for _ in open(f, encoding="utf-8-sig")) <= 1 and (cp / "Rate Tables" / f.name).exists():
            if sum(1 for _ in open(cp / "Rate Tables" / f.name, encoding="utf-8-sig")) > 1:
                EMPTY.setdefault(j, set()).add(f.name[:-len(".RateTable.csv")])
STATE = [None]
HITS = []
_orig = Interpreter.lookup


def _lookup(self, name, col, keys, mode, typ, where):
    v = _orig(self, name, col, keys, mode, typ, where)
    if mode == "SingleResult" and v is not None and name in EMPTY.get(STATE[0], ()):
        HITS.append((name, [str(k) for k in keys], str(v)))
    return v


Interpreter.lookup = _lookup


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def state_of(req):
    sk = json.dumps(req.get("body", {}).get("SchemeKeys", {}))
    m = re.search(r"Commercial Property (?:- )?([A-Z]{2})\b|\b([A-Z]{2}) Commercial Property", sk)
    cp = req.get("body", {}).get("CommercialProperty")
    cp = cp[0] if isinstance(cp, list) else cp
    return (cp or {}).get("State") or (m and (m.group(1) or m.group(2)))


def ours(req):
    HITS.clear()
    STATE[0] = state_of(req)
    try:
        rep.cmp.rate(req)
        return "prices", list(HITS)
    except Exception as exc:
        return f"refuses ({type(exc).__name__})", list(HITS)


def scan():
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json")) if Path(f[:-len("_request.json")] + "_response.json").exists())
    found = collections.defaultdict(list)
    for i, f in enumerate(reqs, 1):
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        o, hits = ours(req)
        for name, keys, v in hits:
            found[(STATE[0], name)].append((Path(f).name, keys, v))
        if i % 200 == 0 or i == len(reqs):
            progress(i, len(reqs), f"{len(found)} (state, empty table) pairs reached so far")
    print(f"\nSCAN: {len(reqs)} requests ISO rated; (state, empty state table) pairs ours answered from countrywide: {len(found)}")
    for (j, name), xs in sorted(found.items()):
        print(f"  {j} {name:55s} {len(xs):4d} lookups in {len({x[0] for x in xs})} requests, e.g. {xs[0][0]} keys {xs[0][1]} -> {xs[0][2]}")
    (OUT / "chunk28_c28-03_empty_scan.json").write_text(json.dumps({f"{j} {n}": xs[:20] for (j, n), xs in found.items()}, indent=1), encoding="utf-8")


def live():
    import raas as raas_mod
    client = raas_mod.RaaS()
    eq = import_module("195_chunk19_c19-17_eq_tiers")
    probes = [("V-VT", "VT", "VacancyPermitFactors re-sent (C18-16)", json.loads((OUT / "chunk18_rc4_VT_request.json").read_text(encoding="utf-8")))]
    for j in sorted(js for js, ts in EMPTY.items() if "EQSubLimitDeductibleTierCWTable" in ts and js != "PR"):
        try:
            sub = eq.build(j, tier="1", pct="25")()
            probes.append((f"Q-{j}", j, "EQ sub-limit tier 1 on the state's empty stub", r2.t2.state_req(r2.t2.m20.payload(sub), j)))
        except Exception as exc:
            print(f"Q-{j}: cannot build ({type(exc).__name__}: {str(exc)[:80]})")
    print(f"\nLIVE at 2026-09-17: {len(probes)} probes. E1 (empty -> countrywide rows) predicts RATED; E2 (empty -> no rows) predicts REFUSED.")
    rows = []
    for i, (cid, j, label, req) in enumerate(probes, 1):
        o, hits = ours(req)
        reach = sorted({h[0] for h in hits})
        if not reach:
            progress(i, len(probes), f"{cid} {j} {label}: ours never reaches an empty table here; skipped (no disagreement to test)")
            rows.append({"case": cid, "state": j, "reached": [], "iso": "not sent"})
            continue
        (OUT / f"chunk28_c28-03_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = r2.rate_retry(client, req)
            iso = "RATED"
            (OUT / f"chunk28_c28-03_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        except raas_mod.RaaSError as exc:
            body = str(exc.body)
            m = re.search(r"Matrix: (\w+), Project: (CF [A-Z]{2} \d{8} V\d\d), Keys: ([^.]*)", body)
            iso = f"REFUSED {m.group(1)} ({m.group(2)}; {m.group(3)[:50]})" if m else f"REFUSED {body[body.find('Message'):][:150]}"
            (OUT / f"chunk28_c28-03_{cid}_refusal.json").write_text(body, encoding="utf-8")
        rows.append({"case": cid, "state": j, "reached": reach, "ours": o, "iso": iso})
        progress(i, len(probes), f"{cid} {j} {label}: ours reaches {reach} (answered from countrywide), ours {o}; ISO {iso}  "
                                 f"-> {'E1' if iso == 'RATED' else 'E2' if iso.startswith('REFUSED') and any(r in iso for r in reach) else 'neither / other refusal'}")
    (OUT / "chunk28_c28-03_empty_live.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    if a.live:
        live()
    if a.scan:
        scan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
