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

from . import evidence, ledger, mismatch, paths, rollup, status, store

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "results" / "tc"
CACHE = TC / "readiness.json"
SIGNOFFS = TC / "signoffs.jsonl"
DESCOPED = Path(__file__).resolve().parent / "config" / "descoped.json"
LAST_BUILD = TC / "last_build.json"

#: Bumped when the shape of the result changes, so a saved result from older code is never served.
SCHEMA = 4

_LOCK = threading.Lock()
_MEM: dict = {}


def _stamp(f) -> str:
    f = Path(f)
    return f"{f.stat().st_size}:{f.stat().st_mtime_ns}" if f.exists() else "absent"


def inputs() -> dict:
    """The files the matrix depends on, with their size and modification time: the recompute trigger."""
    files = {"references": store.INDEX, "classifications": mismatch.STORE, "evidence": evidence.STORE,
             "signoffs": SIGNOFFS, "descoped": DESCOPED, "paths": paths.CONFIG, "build": LAST_BUILD}
    out = {}
    for k, f in files.items():
        out[k] = _stamp(f)
    out["day"] = ledger.day()
    out["schema"] = SCHEMA
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


def compute(today: str | None = None, versions: dict | None = None) -> dict:
    """`versions`: (line|state) -> package in force, carried over from the last result of the same day, so a
    recompute after a sign-off or a classification does not load both engines again."""
    today = today or ledger.day()
    versions = dict(versions or {})
    latest = mismatch.classifications()
    freshness = store.freshness()
    recs = evidence.records()
    by_cell: dict = {}
    for r in recs:
        by_cell.setdefault((r["line"], r["state"]), []).append(r)
    sos, desc = signoffs(), descoped()

    cells = []
    path_cells: dict = {}       # line -> state -> path -> [state, scenarios walking it, affected] (the board, TC-18)
    for line in paths.lines():
        for state in paths.states(line):
            rs = by_cell.get((line, state), [])
            evs = [evidence.resolve(r, latest, freshness) for r in rs]
            ps = rollup.path_states(line, state, evs)
            d0 = {**desc.get(line, {}).get("*", {}), **desc.get(line, {}).get(state, {})}
            row = path_cells.setdefault(line, {}).setdefault(state, {})
            for pid, pst in ps.items():
                walkers = [e for e in evs if not e.inert and pid in e.walked]
                affected = (sum(e.iso == "open-mismatch" for e in walkers) if pst == "mismatch" else
                            sum(e.iso != "none" and not e.fresh for e in walkers) if pst == "stale" else 0)
                row[pid] = ["descoped" if pid in d0 and pst != "na" else pst, len(walkers), affected]
            d = {**desc.get(line, {}).get("*", {}), **desc.get(line, {}).get(state, {})}
            vk = f"{line}|{state}"
            if vk not in versions:
                versions[vk] = store.current_package(line, state, today) or ""
            version = versions[vk]
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
                # §6: a stale cell needs one call per stale reference and a mismatched one one per open mismatch
                # (re-verify after the fix), not one per path: one answer often walks several of a cell's paths
                est = {"mismatch": len(open_mm),
                       "stale": len({r.get("hash") or r["scenario"] for r, e in mine if e.iso != "none" and not e.fresh}),
                       }.get(c.status, c.est_remaining_calls)
                cells.append({
                    "lob": line, "state": state, "coverage": cov, "status": c.status,
                    "paths": {"inScope": c.counts["in_scope"], "walked": c.counts["walked"],
                              "raasVerified": c.counts["verified"], "mismatched": c.counts["mismatch"],
                              "stale": c.counts["stale"],
                              "descoped": [{"pathId": x["path"], "reason": x["reason"]} for x in c.descoped],
                              "byPath": {p: ps.get(p, "untested") for p in c.in_scope}},
                    "scenarios": len(mine),
                    "openMismatches": open_mm,
                    "estRemainingCalls": est,
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
                   "daysAtActiveLane": round(calls / ledger.LANES["active"], 1),
                   "daysAtRefreshLane": round(sum(c["estRemainingCalls"] for c in todo if c["status"] == "stale")
                                              / ledger.LANES["refresh"], 1)})
    return {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "columns": {line: paths.coverages(line) for line in paths.lines()},
            "pathLabels": {line: {p: v["label"] for p, v in paths.paths(line).items()} for line in paths.lines()},
            "cells": cells, "totals": totals, "stillToTest": still_to_test(cells), "pathCells": path_cells, "evidence": len(recs), "agreement": agreement(latest),
            "versions": {"day": today, "paths": _stamp(paths.CONFIG), "references": _stamp(store.INDEX), "map": versions}}


def still_to_test(cells: list) -> list:
    """§6 without the wave key (D3): every cell neither Passed nor n/a, by status priority (mismatch, stale, internal,
    untested), then most calls first, then state and coverage; each with what it needs and its calls (TC-17)."""
    todo = [c for c in cells if c["status"] not in ("verified", "na")]
    todo.sort(key=lambda c: (rollup.PRIORITY[c["status"]], -c["estRemainingCalls"], c["state"], c["lob"], c["coverage"]))
    return [{"lob": c["lob"], "state": c["state"], "coverage": c["coverage"], "status": c["status"],
             "needs": status.NEEDS[c["status"]], "lane": "refresh" if c["status"] == "stale" else "active",
             "calls": c["estRemainingCalls"]} for c in todo]


def agreement(latest: dict | None = None) -> dict:
    """Agreement over time (D18): per line, on each day evidence arrived, the share of compared scenarios (their latest
    record as of that day, INERT ones left out) that agree with ISO under today's classifications."""
    latest = mismatch.classifications() if latest is None else latest
    agrees: dict = {}            # line -> scenario -> agrees? (compared scenarios only, as of the record being read)
    days: dict = {}
    for r in evidence.history():
        mine = agrees.setdefault(r["line"], {})
        mine.pop(r["scenario"], None)
        if not r.get("inert") and r.get("iso") is not None and r.get("ours") is not None:
            mine[r["scenario"]] = not mismatch.is_open(r["scenario"], r["ours"], r["iso"], latest)
        d = r["at"][:10]
        days.setdefault(r["line"], {})[d] = {"day": d, "compared": len(mine), "agreed": sum(mine.values())}
    return {line: list(v.values()) for line, v in days.items()}


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
                prev = (cached or _MEM).get("versions") or {}
                # the package in force moves with the day, the path config and a corpus ingest (which rebuilds the index)
                same = (prev.get("day"), prev.get("paths"), prev.get("references")) == (key["day"], key["paths"], key["references"])
                carry = prev.get("map") if same else None
                out = compute(key["day"], carry)
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
        res["pathCells"] = {ln: {st: v for st, v in by.items() if not sts or st in sts}
                            for ln, by in res.get("pathCells", {}).items() if not lobs or ln in lobs}
        res["stillToTest"] = [g for g in res.get("stillToTest", [])
                              if (not lobs or g["lob"] in lobs) and (not sts or g["state"] in sts)]
    return res
