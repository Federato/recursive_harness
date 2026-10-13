"""Results inspection: a person's verdict on each result a plan brought back (the user's ask, 2026-10-07).

After a plan's results come back from ISO, someone reviews each one and records **pass** (our result is right),
**fail** (it is wrong: a reason and a category from `console.mismatch`) or **excuse** (not a test of our engine, e.g.
ISO refused for want of a subscription: a reason). A plan whose results all carry a verdict can be signed off.

Inspection is a layer beside ISO's agreement, never a gate on it (the user's choice (b)): a Coverage Board cell is
still ✓ when ISO matches; a result nobody has inspected only adds a dot and counts toward "Awaiting inspection".
It covers results from console plans; the evidence seeded from earlier runs predates inspection and is not counted.

One line per action in `results/tc/inspections.jsonl`, append-only; the latest verdict per scenario counts, and
`undo` withdraws it. Sign-offs are lines too (`verdict: "signoff"`, keyed by plan).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import evidence, mismatch

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "results" / "tc" / "inspections.jsonl"
VERDICTS = ("pass", "fail", "excuse")
RESULTS = ("match", "mismatch", "refused", "error")     # plan rows that came back with something to inspect


class InspectionError(ValueError):
    pass


def _append(rec: dict, store: Path | None = None) -> dict:
    f = store or STORE
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def history(store: Path | None = None) -> list:
    f = store or STORE
    if not f.exists():
        return []
    return [json.loads(raw) for raw in f.read_text(encoding="utf-8").splitlines() if raw.strip()]


def record(scenario: str, verdict: str, by: str = "", reason: str = "", category: str = "", plan: str = "",
           store: Path | None = None) -> dict:
    """One verdict (or `undo`). Fail needs a reason and a category; excuse needs a reason."""
    reason, category = (reason or "").strip(), (category or "").strip()
    if not scenario:
        raise InspectionError("no scenario")
    if verdict not in VERDICTS + ("undo",):
        raise InspectionError(f"unknown verdict {verdict!r}")
    if verdict == "fail" and (not reason or category not in mismatch.BY_KEY):
        raise InspectionError("a fail needs a reason and a category")
    if verdict == "excuse" and not reason:
        raise InspectionError("an excuse needs a reason")
    return _append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": scenario, "verdict": verdict,
                    "by": (by or "").strip(), "reason": reason, "category": category if verdict == "fail" else "",
                    "plan": plan}, store)


def latest(store: Path | None = None) -> dict:
    """scenario -> its current verdict record (undone ones dropped)."""
    out: dict = {}
    for rec in history(store):
        if rec["verdict"] == "signoff":
            continue
        if rec["verdict"] == "undo":
            out.pop(rec["scenario"], None)
        else:
            out[rec["scenario"]] = rec
    return out


def signoffs(store: Path | None = None) -> dict:
    return {rec["plan"]: rec for rec in history(store) if rec["verdict"] == "signoff"}


def plan_view(plan: dict, store: Path | None = None) -> dict:
    """A plan's results with their verdicts, the counts and its sign-off."""
    v = latest(store)
    rows = []
    for s in plan["scenarios"]:
        if s.get("status") not in RESULTS or not s.get("scenario"):
            continue
        rows.append({"scenario": s["scenario"], "state": s["state"], "config": s.get("config") or {},
                     "kind": s.get("kind", ""), "result": s["status"], "ours": s.get("oursNow") or s.get("ours"),
                     "iso": s.get("iso"), "message": (s.get("message") or "")[:400], "verdict": v.get(s["scenario"])})
    c = {k: sum(1 for r in rows if r["verdict"] and r["verdict"]["verdict"] == k) for k in VERDICTS}
    c["awaiting"] = sum(1 for r in rows if not r["verdict"])
    c["total"] = len(rows)
    c["inspected"] = c["total"] - c["awaiting"]
    order = {"mismatch": 0, "error": 1, "refused": 2, "match": 3}
    rows.sort(key=lambda r: (r["verdict"] is not None, order.get(r["result"], 9), r["state"]))
    return {"plan": plan["id"], "name": plan["name"], "line": plan["line"], "status": plan["status"], "rows": rows,
            "counts": c, "signoff": signoffs(store).get(plan["id"]),
            "categories": [{"key": k.key, "label": k.label} for k in mismatch.CATEGORIES]}


def pass_matches(plan: dict, by: str = "", store: Path | None = None) -> int:
    """Pass every result that matched ISO and has no verdict yet. Returns how many."""
    v = latest(store)
    n = 0
    for s in plan["scenarios"]:
        if s.get("status") == "match" and s.get("scenario") and s["scenario"] not in v:
            record(s["scenario"], "pass", by=by, reason="matched ISO; passed in bulk", plan=plan["id"], store=store)
            v[s["scenario"]] = True
            n += 1
    return n


def signoff(plan: dict, by: str = "", store: Path | None = None) -> dict:
    view = plan_view(plan, store)
    if view["counts"]["awaiting"]:
        raise InspectionError(f"{view['counts']['awaiting']} result(s) still awaiting inspection")
    if not (by or "").strip():
        raise InspectionError("a sign-off needs a name")
    c = view["counts"]
    return _append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": "", "verdict": "signoff", "by": by.strip(),
                    "plan": plan["id"], "reason": f"{c['pass']} passed · {c['fail']} failed · {c['excuse']} excused"}, store)


def awaiting(line: str, store: Path | None = None) -> dict:
    """Plan results on this line nobody has inspected: {"count": n, "cells": {state: {path: n}}, "scenarios": [...]}."""
    v = latest(store)
    cells: dict = {}
    sids = []
    for rec in evidence.records():
        if rec["line"] != line or not str(rec.get("source", "")).startswith("plan ") or rec["scenario"] in v:
            continue
        sids.append(rec["scenario"])
        for p in rec["walked"]:
            cells.setdefault(rec["state"], {})[p] = cells.get(rec["state"], {}).get(p, 0) + 1
    return {"count": len(sids), "cells": cells, "scenarios": sids}
