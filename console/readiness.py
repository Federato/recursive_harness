"""The Readiness Matrix's data: `GET /api/console/readiness` (TC-15; spec §5, §8; D3 no waves, D4, D5).

    { generatedAt, inputs, cap: {...}, columns: {GL: [...], CP: [...]}, cells: [...], totals: {...} }

Each cell follows §5's `StateCoverageCell`, without the wave (D3) and with n/a (D5). Its status is derived (§3,
`console.rollup`), never hand-set.

**Recomputed on the four events §5 names, by watching their files** rather than by each writer remembering to call
here: a stored answer or a corpus ingest (the reference index, rebuilt by `store.build`), a classification
(`classifications.jsonl`), new evidence (`evidence.jsonl`), a build (`last_build.json`, written by the Regression
Library's re-run, TC-34). Sign-offs, descoping and the path configuration count too, and so does the day, since the
package in force moves with the date. While none of them changes, the last result is served from
`results/tc/readiness.json`, so a cold start does not pay the ~20 s of loading both engines for content versions.
"""
from __future__ import annotations

import json
import threading
import time
from decimal import Decimal
from pathlib import Path

from . import evidence, ledger, mismatch, paths, rollup, store

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "results" / "tc"
CACHE = TC / "readiness.json"
SIGNOFFS = TC / "signoffs.jsonl"
DESCOPED = Path(__file__).resolve().parent / "config" / "descoped.json"
LAST_BUILD = TC / "last_build.json"

_LOCK = threading.Lock()
_MEM: dict = {}


def inputs() -> dict:
    """The files the matrix depends on, with their size and modification time: the recompute trigger."""
    files = {"references": store.INDEX, "classifications": mismatch.STORE, "evidence": evidence.STORE,
             "signoffs": SIGNOFFS, "descoped": DESCOPED, "paths": paths.CONFIG, "build": LAST_BUILD}
    out = {}
    for k, f in files.items():
        f = Path(f)
        out[k] = f"{f.stat().st_size}:{f.stat().st_mtime_ns}" if f.exists() else "absent"
    out["day"] = ledger.day()
    return out


def signoffs() -> dict:
    """(line, state, coverage) -> {by, at}; append-only, the latest wins; an entry with no `by` withdraws it."""
    out = {}
    if SIGNOFFS.exists():
        for raw in SIGNOFFS.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                r = json.loads(raw)
                out[(r["line"], r["state"], r["coverage"])] = r if r.get("by") else None
    return {k: v for k, v in out.items() if v}


def sign_off(line: str, state: str, coverage: str, by: str) -> dict:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": line, "state": state, "coverage": coverage, "by": by}
    SIGNOFFS.parent.mkdir(parents=True, exist_ok=True)
    with SIGNOFFS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def descoped() -> dict:
    """line -> state ('*' for every state) -> path id -> reason. Recorded with a reason, per §3."""
    return json.loads(DESCOPED.read_text(encoding="utf-8")).get("lines", {}) if DESCOPED.exists() else {}


def _cap() -> dict:
    u = ledger.used()
    return {"daily": ledger.CAP, "used": u["total"], "left": max(0, ledger.CAP - u["total"]),
            "lanes": {k: {"cap": c, "used": u.get(k, 0)} for k, c in ledger.LANES.items()},
            "activeLane": ledger.LANES["active"]}


def compute(today: str | None = None) -> dict:
    today = today or ledger.day()
    latest = mismatch.classifications()
    try:
        refs = store.load()["references"]
    except FileNotFoundError:
        refs = []
    freshness = {e["hash"]: e.get("freshness", "unknown") for e in refs}
    recs = evidence.records()
    by_cell: dict = {}
    for r in recs:
        by_cell.setdefault((r["line"], r["state"]), []).append(r)
    sos, desc = signoffs(), descoped()

    cells = []
    for line in paths.lines():
        for state in paths.states(line):
            rs = by_cell.get((line, state), [])
            evs = [evidence.resolve(r, latest, freshness) for r in rs]
            ps = rollup.path_states(line, state, evs)
            d = {**desc.get(line, {}).get("*", {}), **desc.get(line, {}).get(state, {})}
            version = store.current_package(line, state, today) or ""
            for cov in paths.coverages(line):
                c = rollup.cell(line, state, cov, ps, descoped={p: r for p, r in d.items()
                                                                if p in paths.paths(line, cov)},
                                signoff=sos.get((line, state, cov)))
                scope = set(c.in_scope)
                mine = [(r, e) for r, e in zip(rs, evs) if not e.inert and e.walked & scope]
                open_mm = [{"scenarioId": r["scenario"],
                            "category": (latest.get(r["scenario"]) or {}).get("category", "unclassified"),
                            "delta": str(Decimal(r["ours"]) - Decimal(r["iso"]))}
                           for r, e in mine if e.iso == "open-mismatch"]
                cells.append({
                    "lob": line, "state": state, "coverage": cov, "status": c.status,
                    "paths": {"inScope": c.counts["in_scope"], "walked": c.counts["walked"],
                              "raasVerified": c.counts["verified"], "mismatched": c.counts["mismatch"],
                              "stale": c.counts["stale"],
                              "descoped": [{"pathId": x["path"], "reason": x["reason"]} for x in c.descoped],
                              "byPath": {p: ps.get(p, "untested") for p in c.in_scope}},
                    "scenarios": len(mine),
                    "openMismatches": open_mm,
                    "estRemainingCalls": c.est_remaining_calls,
                    "contentVersion": version,
                    "lastChangedAt": max((r["at"] for r, _ in mine), default=None),
                    "signedOffBy": c.signed_off_by, "signedOffAt": c.signed_off_at,
                })

    counted = [c for c in cells if c["status"] != "na"]
    todo = [c for c in counted if c["status"] != "verified"]
    calls = sum(c["estRemainingCalls"] for c in todo)
    totals = {
        line: {"passed": sum(c["status"] == "verified" for c in counted if c["lob"] == line),
               "cells": sum(c["lob"] == line for c in counted),
               "signedOff": sum(bool(c["signedOffBy"]) for c in counted if c["lob"] == line),
               "na": sum(c["status"] == "na" for c in cells if c["lob"] == line)}
        for line in paths.lines()}
    totals.update({"stillToTest": len(todo), "estCallsToFinish": calls,
                   "staleCalls": sum(c["estRemainingCalls"] for c in todo if c["status"] == "stale"),
                   "daysAtActiveLane": round(calls / ledger.LANES["active"], 1)})
    return {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "columns": {line: paths.coverages(line) for line in paths.lines()},
            "cells": cells, "totals": totals, "evidence": len(recs)}


def get(lob: str | None = None, state: str | None = None, force: bool = False) -> dict:
    """The matrix, recomputed only when an input changed; `lob` / `state` filter the cells (comma lists)."""
    with _LOCK:
        key = inputs()
        if force or _MEM.get("inputs") != key:
            cached = None
            if not force and CACHE.exists():
                try:
                    cached = json.loads(CACHE.read_text(encoding="utf-8"))
                except ValueError:
                    cached = None
            if cached and cached.get("inputs") == key:
                _MEM.clear(); _MEM.update(cached)
            else:
                out = compute(key["day"])
                out["inputs"] = key
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                CACHE.write_text(json.dumps(out), encoding="utf-8")
                _MEM.clear(); _MEM.update(out)
        res = dict(_MEM)
    res["cap"] = _cap()          # the ledger moves call by call; never cached
    lobs = {x.strip().upper() for x in lob.split(",")} if lob else None
    sts = {x.strip().upper() for x in state.split(",")} if state else None
    if lobs or sts:
        res["cells"] = [c for c in res["cells"] if (not lobs or c["lob"] in lobs) and (not sts or c["state"] in sts)]
        res["columns"] = {k: v for k, v in res["columns"].items() if not lobs or k in lobs}
    return res
