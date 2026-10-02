#!/usr/bin/env python3
"""Chunk 28 C28-02 (set A): every ISO refusal on record in one table, re-sent live, beside the empty lookups ISO tolerates.

Two halves, one instrument: `Interpreter.lookup` is wrapped so every lookup that finds NO row is recorded (matrix, keys,
mode, the rule location). Our engine returns null there and carries on; ISO sometimes refuses the whole policy.

  REFUSED    every `*_refusal.json` with its request, and every `*_request.json` with no saved response (the scripts write
             the request before the call). Each request is re-sent live at its own SchemeKeys date; ISO's answer parsed
             (refusal kind, matrix, keys, rule file and line); ours run on the same request: refuses / prices, the total,
             and whether ISO's failing matrix is among OUR no-row lookups (same table, same keys).
  TOLERATED  every stored request ISO RATED (a saved `*_response.json`), run through ours: each no-row lookup recorded.
             ISO priced those policies, so each such miss is one ISO tolerated (or never reached on its side).

Outputs: results/cf-raas/chunk28_c28-02_refusals.json, chunk28_c28-02_tolerated.json; the table in
docs/CF-CHUNK28-REFUSALS.md is written from them.

    python scripts/cf/245_chunk28_c28-02_refusals.py [--refused] [--tolerated] [--only chunk12]
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

r2 = import_module("239_chunk27_rc2")
rep, gc = r2.rep, r2.gc
from gl_engine.interp.interpreter import Interpreter

OUT = gc.OUT
MISSES = []
_orig_lookup = Interpreter.lookup


def _lookup(self, name, col, keys, mode, typ, where):
    v = _orig_lookup(self, name, col, keys, mode, typ, where)
    if v is None:
        MISSES.append({"matrix": name, "keys": [None if k is None else str(k) for k in keys], "mode": mode,
                       "where": str(where)[:160]})
    return v


Interpreter.lookup = _lookup


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def parse_iso_error(body: str) -> dict:
    out = {"text": body[body.find("Message"):][:400]}
    m = re.search(r"Matrix: (\w+), Project: (CF [A-Z]{2} \d{8} V\d\d), Keys: (.*?)\. No results", body)
    if m:
        out.update(kind="lookup, no row", matrix=m.group(1), project=m.group(2),
                   keys=[k.strip() for k in m.group(3).split(",")])
    elif "Error reading view" in body:
        out["kind"] = "payload type (the request view)"
    elif "No value found" in body:
        out["kind"] = "unbound value"
    elif re.search(r"[Cc]onvert", body):
        out["kind"] = "conversion"
    else:
        out["kind"] = "other"
    m = re.search(r"at line (\d+) in RuleSet (\w+) \(Project (CF [A-Z]{2} \d{8} V\d\d)\)", body)
    if m:
        out.update(line=int(m.group(1)), ruleset=m.group(2), rule_project=m.group(3))
    return out


def ours(req):
    MISSES.clear()
    try:
        data, ip = rep.cmp.rate(req)
        prem = rep.our_prem(data)
        tot = next((v for k, v in prem.items() if k.endswith("ErcCalculatedTotalPremium")), None)
        return {"outcome": "prices", "total": tot}, list(MISSES)
    except Exception as exc:
        return {"outcome": "refuses", "error": f"{type(exc).__name__}: {str(exc)[:200]}"}, list(MISSES)


def refused(only):
    cases = {}
    for f in sorted(glob.glob(str(OUT / "*_refusal.json"))):
        stem = f[:-len("_refusal.json")]
        cases[Path(stem).name] = (stem + "_request.json", f)
    for f in sorted(glob.glob(str(OUT / "*_request.json"))):
        stem = f[:-len("_request.json")]
        if not Path(stem + "_response.json").exists():
            cases.setdefault(Path(stem).name, (f, None))
    cases = {k: v for k, v in cases.items() if not only or k.startswith(only)}
    import raas as raas_mod
    client = raas_mod.RaaS()
    rows = []
    for i, (cid, (reqf, reff)) in enumerate(sorted(cases.items()), 1):
        row = {"case": cid, "request": Path(reqf).name if Path(reqf).exists() else None,
               "recorded": parse_iso_error(Path(reff).read_text(encoding="utf-8")) if reff else None}
        if not Path(reqf).exists():
            row["now"] = {"kind": "no request on file"}
            rows.append(row)
            progress(i, len(cases), f"{cid}: no request on file")
            continue
        req = json.loads(Path(reqf).read_text(encoding="utf-8"))
        row["state"] = (re.search(r"Commercial Property (\w\w)|CF (\w\w) ", json.dumps(req.get("body", {}).get("SchemeKeys", {}))) or [None])
        sk = req.get("body", {}).get("SchemeKeys", {})
        row["date"] = str(sk.get("EffectiveDateTime", ""))[:10]
        row["product"] = sk.get("ProductName")
        try:
            resp = r2.rate_retry(client, req)
            row["now"] = {"kind": "RATED now", "scheme": (resp.get("Header") or {}).get("Scheme")}
        except raas_mod.RaaSError as exc:
            row["now"] = parse_iso_error(str(exc.body))
        o, misses = ours(req)
        row["ours"] = o
        row["our_misses"] = misses[:40]
        if row["now"].get("matrix"):
            # ISO's failing table among ours' no-row lookups (the same table; keys printed beside it for the eye)
            hit = [m_ for m_ in misses if m_["matrix"] == row["now"]["matrix"]]
            row["ours_saw_it"] = bool(hit)
            row["ours_keys"] = hit[0]["keys"] if hit else None
        rows.append(row)
        n = row["now"]
        progress(i, len(cases), f"{cid} [{row['date']}]: ISO {n.get('kind')} {n.get('matrix', '')} {n.get('keys', '')}; ours {o['outcome']}"
                                + (f" ({o.get('total')})" if o["outcome"] == "prices" else "") + (f"; ours saw the miss: {row.get('ours_saw_it')}" if "ours_saw_it" in row else ""))
    (OUT / "chunk28_c28-02_refusals.json").write_text(json.dumps(rows, indent=1, default=str), encoding="utf-8")
    kinds = collections.Counter(r["now"].get("kind") for r in rows)
    print(f"\nREFUSED half: {len(rows)} cases; ISO now: {dict(kinds)}")
    look = [r for r in rows if r["now"].get("kind") == "lookup, no row"]
    print(f"  lookup refusals: {len(look)}; ours prices {sum(1 for r in look if r['ours']['outcome'] == 'prices')}, "
          f"ours refuses {sum(1 for r in look if r['ours']['outcome'] == 'refuses')}; ours saw ISO's miss {sum(1 for r in look if r.get('ours_saw_it'))}")
    by = collections.Counter(r["now"]["matrix"] for r in look)
    for mtx, n in by.most_common():
        print(f"    {n:3d}  {mtx}")


def tolerated(only):
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json"))
                  if Path(f[:-len("_request.json")] + "_response.json").exists() and (not only or Path(f).name.startswith(only)))
    agg = collections.defaultdict(lambda: {"n": 0, "modes": collections.Counter(), "cases": [], "keys": []})
    raised = []
    for i, f in enumerate(reqs, 1):
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        o, misses = ours(req)
        if o["outcome"] == "refuses":
            raised.append((Path(f).name, o["error"]))
        for m_ in misses:
            a = agg[m_["matrix"]]
            a["n"] += 1
            a["modes"][m_["mode"]] += 1
            if len(a["cases"]) < 6 and Path(f).name not in a["cases"]:
                a["cases"].append(Path(f).name)
            if len(a["keys"]) < 4 and m_["keys"] not in a["keys"]:
                a["keys"].append(m_["keys"])
        if i % 100 == 0 or i == len(reqs):
            progress(i, len(reqs), f"rated by ISO, run through ours; {len(agg)} matrices missed so far")
    out = {k: {"n": v["n"], "modes": dict(v["modes"]), "cases": v["cases"], "keys": v["keys"]} for k, v in agg.items()}
    (OUT / "chunk28_c28-02_tolerated.json").write_text(json.dumps({"requests": len(reqs), "ours_raised": raised, "matrices": out},
                                                                  indent=1, default=str), encoding="utf-8")
    single = {k: v for k, v in out.items() if v["modes"].get("SingleResult")}
    print(f"\nTOLERATED half: {len(reqs)} requests ISO rated; matrices with a no-row lookup in ours: {len(out)}, "
          f"of them SingleResult: {len(single)}; ours raised on {len(raised)}")
    for k, v in sorted(single.items(), key=lambda kv: -kv[1]["modes"]["SingleResult"])[:40]:
        print(f"    {v['modes']['SingleResult']:5d}  {k:55s} e.g. {v['keys'][0]}  ({v['cases'][0]})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refused", action="store_true")
    ap.add_argument("--tolerated", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    if a.refused:
        refused(a.only)
    if a.tolerated:
        tolerated(a.only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
