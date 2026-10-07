"""The Coverage Board's data (TC-18): one line, state x rating path, a readiness verdict per state, the scenarios
behind each cell, and the control x state grid beside it (D18).

Path states come from the readiness result (`console.readiness`, the same roll-up the matrix uses), so the board and
the matrix can never disagree about a path.

**The verdict per state** (the prototype's rule, over the state's applicable paths, n/a and descoped left out):
  * Go         -- every applicable path RaaS-verified
  * Hold       -- an open mismatch or a stale reference, or some paths verified and the rest not yet
  * Not ready  -- nothing verified yet (walked only by our engine, or not walked at all)
"""
from __future__ import annotations

from decimal import Decimal

from . import evidence, ledger, mismatch, paths, readiness, store


def columns(line: str) -> list:
    """Paths grouped under the most specific coverage they count toward (the one with the fewest paths, so a
    Prem/Ops deductible sits under Deductibles), coverages in the configuration's order. Each path appears once."""
    allp = paths.paths(line)
    covs = paths.coverages(line)
    size = {c: len(paths.paths(line, c)) for c in covs}
    home = {p: min(v["coverages"], key=lambda c: (size.get(c, 1 << 30), covs.index(c) if c in covs else 99))
            for p, v in allp.items()}
    return [{"coverage": c, "paths": [{"id": p, "label": allp[p]["label"], "coverages": allp[p]["coverages"]}
                                      for p in allp if home[p] == c]}
            for c in covs if any(home[p] == c for p in allp)]


def verdict(states: list) -> dict:
    """Go / Hold / Not ready over one state's path states (n/a and descoped already left out)."""
    c = {k: states.count(k) for k in ("verified", "internal", "mismatch", "stale", "untested")}
    n = len(states)
    if not n:
        return {"verdict": "n/a", "note": "no path filed here", "counts": c}
    if c["mismatch"]:
        return {"verdict": "Hold", "counts": c, "note": f"{c['mismatch']} mismatch path{'s' if c['mismatch'] > 1 else ''}"
                + (f" · {c['stale']} stale" if c["stale"] else "")}
    if c["stale"]:
        return {"verdict": "Hold", "counts": c, "note": f"{c['stale']} stale path{'s' if c['stale'] > 1 else ''} to refresh"}
    if c["verified"] == n:
        return {"verdict": "Go", "counts": c, "note": f"{n}/{n} paths RaaS-verified"}
    if c["verified"]:
        return {"verdict": "Hold", "counts": c, "note": f"{n - c['verified']} of {n} paths not yet RaaS-verified"}
    if c["internal"]:
        return {"verdict": "Not ready", "counts": c, "note": f"internal only · {c['untested']} untested"}
    return {"verdict": "Not ready", "counts": c, "note": "no path run yet"}


def board(line: str) -> dict:
    r = readiness.get(lob=line)
    pc = r.get("pathCells", {}).get(line, {})
    rows = []
    applicable = walked = verified = 0
    for state in paths.states(line):
        cells = pc.get(state, {})
        live = [v[0] for v in cells.values() if v[0] not in ("na", "descoped")]
        applicable += len(live)
        walked += sum(s != "untested" for s in live)
        verified += sum(s == "verified" for s in live)
        rows.append({"state": state, **verdict(live), "cells": cells})
    mm: dict = {}
    seen = set()
    for c in r["cells"]:
        for m in c["openMismatches"]:
            if m["scenarioId"] not in seen:
                seen.add(m["scenarioId"])
                mm[m["category"]] = mm.get(m["category"], 0) + 1
    calls = sum(g["calls"] for g in r["stillToTest"])
    return {
        "line": line, "generatedAt": r["generatedAt"], "columns": columns(line), "rows": rows, "cap": r["cap"],
        "summary": {"applicable": applicable, "walked": walked, "verified": verified,
                    "openMismatches": sum(mm.values()), "byCategory": mm,
                    "categories": [{"key": c.key, "label": c.label} for c in mismatch.CATEGORIES],
                    "calls": calls, "days": round(calls / ledger.LANES["active"], 1),
                    "verdicts": {v: sum(x["verdict"] == v for x in rows) for v in ("Go", "Hold", "Not ready")}},
    }


def cell(line: str, state: str, path: str) -> dict:
    """The scenarios behind one board cell: every scenario of that line and state whose latest record walked the path."""
    latest = mismatch.classifications()
    fresh = store.freshness()
    out = []
    for rec in evidence.records():
        if rec["line"] != line or rec["state"] != state or path not in rec["walked"]:
            continue
        e = evidence.resolve(rec, latest, fresh)
        if e.inert:
            st = "inert"
        elif e.iso == "open-mismatch":
            st = "mismatch"
        elif e.iso != "none" and not e.fresh:
            st = "stale"
        elif e.iso == "agree":
            st = "verified"
        else:
            st = "internal"
        delta = str(Decimal(rec["ours"]) - Decimal(rec["iso"])) if rec.get("ours") is not None and rec.get("iso") is not None else None
        cls = latest.get(rec["scenario"])
        out.append({"scenario": rec["scenario"], "status": st, "ours": rec.get("ours"), "iso": rec.get("iso"),
                    "delta": delta, "category": cls["category"] if cls else None, "at": rec["at"],
                    "source": rec.get("source", ""), "paths": len(rec["walked"])})
    rank = {"mismatch": 0, "stale": 1, "internal": 2, "verified": 3, "inert": 4}
    out.sort(key=lambda x: (rank[x["status"]], x["scenario"]))
    pcs = readiness.get(lob=line, state=state).get("pathCells", {}).get(line, {}).get(state, {})
    st = (pcs.get(path) or ["untested", 0, 0])[0]
    ok, why = paths.applies(line, state, path)
    return {"line": line, "state": state, "path": path, "label": paths.paths(line).get(path, {}).get("label", path),
            "status": st, "applies": ok, "why": why, "scenarios": out}

