"""Test plans (TC-27 counters, TC-29 commit) and their run controls (D14).

A plan is a line, a set of states (no waves, D3) and, per dimension, the values to cover. Its scenarios, per state:

  * **pairwise** over the chosen values (`qa._allpairs`: every pair of values appears together at least once);
  * **edges**: each dimension at each of its edge values, the rest at the base risk (one factor at a time);

and the plan says, before anything is spent: the full cartesian product, how many Tier 0 checks run free, how many
scenarios ISO already answered (the dedupe: their answers are reused, not re-asked), what is not expressible in a
state, and so the calls it would spend and the days at the active lane (150 a day, D2). Two of D20's options shrink it:
a **reduced grid** (each dimension to its edges) and an **allowance** (thin the scenarios to at most N calls, taking
from the states with most, **never dropping a state**).

Committing writes `results/tc/plans/<id>.json`: every scenario with its request hash, kind and what it will cost; the
dispatcher (TC-30) works through it. A plan is `queued`, `running`, `paused`, `stopped` (stop-and-keep, D14: its
results stay, what it never reached is listed) or `done`.
"""
from __future__ import annotations

import itertools
import json
import sys
import threading
import time
from pathlib import Path

from . import catalog as C
from . import invariants, ledger, readiness, store

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "results" / "tc" / "plans"
if str(ROOT / "scripts") not in sys.path:
    sys.path.append(str(ROOT / "scripts"))
_LOCK = threading.RLock()


def _pairs(axes: dict) -> list:
    if len(axes) < 2:
        (k, vs), = axes.items() if axes else ((None, []),)
        return [{k: v} for v in vs] if k else [{}]
    from qa import _allpairs
    return _allpairs(axes)


def scenarios(spec: dict) -> list:
    """(state, config, kind) for every scenario the spec asks for, deduplicated per state."""
    line, states = spec["line"], spec.get("states") or []
    dims = {k: list(v) for k, v in (spec.get("dims") or {}).items() if v}
    if spec.get("reduced"):
        dims = {k: list(C.edges(v)) for k, v in dims.items()}
    out = []
    for st in states:
        seen = set()
        # A state-specific dimension (a territory exists only in its state) takes each state's own edge values, not
        # the reference state's: Alaska's territory in Ohio is not a test, it is a refusal manufactured by the plan.
        own = {k: (list(C.edges(C.cp_values(k, st))) if line == "CP" and k in C.STATE_SPECIFIC else v)
               for k, v in dims.items()}
        own = {k: v for k, v in own.items() if v}
        rows = [(cfg, "pairwise") for cfg in _pairs(own)] if own else [({}, "base")]
        if spec.get("edges", True):
            rows += [({k: v}, "edge") for k, vs in own.items() for v in C.edges(vs)]
        for cfg, kind in rows:
            key = json.dumps(cfg, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            out.append({"state": st, "config": cfg, "kind": kind})
    return out


def _index() -> dict:
    try:
        return {e["hash"]: e for e in store.load()["references"]}
    except FileNotFoundError:
        return {}


def _untested_paths(line: str) -> dict:
    """state -> set of paths not yet verified (untested, internal, stale or mismatched): where a call is worth most."""
    pc = readiness.get(lob=line).get("pathCells", {}).get(line, {})
    return {st: {p for p, v in row.items() if v[0] not in ("verified", "na", "descoped")} for st, row in pc.items()}


def expand(spec: dict, with_requests: bool = True) -> dict:
    """Every scenario built and costed (no calls): request hash, stored answer, expressible here or not."""
    line = spec["line"]
    idx = _index() if with_requests else {}
    rows, na = [], []
    for s in scenarios(spec):
        r = dict(s)
        if with_requests:
            try:
                req = C.build(line, s["state"], s["config"])
            except Exception as exc:                          # noqa: BLE001 -- not expressible in this state
                r.update(outcome="not applicable", detail=str(exc)[:240])
                na.append(r)
                continue
            h = store.request_hash(req)
            e = idx.get(h)
            r.update(hash=h, stored=bool(e and e["outcome"] in ("rated", "refused") and e.get("freshness") != "stale"),
                     storedOutcome=e and e["outcome"], fresh=bool(e and e.get("freshness") != "stale"))
        rows.append(r)
    return {"rows": rows, "notApplicable": na}


def _thin(rows: list, allowance: int) -> tuple[list, int]:
    """Keep at most `allowance` calls, cutting from the states with the most, never leaving a state with none."""
    need = [r for r in rows if not r.get("stored")]
    if allowance is None or len(need) <= allowance:
        return rows, 0
    by: dict = {}
    for r in need:
        by.setdefault(r["state"], []).append(r)
    keep = {st: rs[:1] for st, rs in by.items()}          # every state keeps one
    budget = max(allowance, len(keep)) - len(keep)
    rest = {st: rs[1:] for st, rs in by.items()}
    while budget > 0 and any(rest.values()):
        for st in sorted(rest, key=lambda s: len(keep[s])):
            if budget and rest[st]:
                keep[st].append(rest[st].pop(0))
                budget -= 1
    kept = {id(r) for rs in keep.values() for r in rs}
    out = [r for r in rows if r.get("stored") or id(r) in kept]
    return out, len(need) - sum(len(v) for v in keep.values())


def preview(spec: dict) -> dict:
    """The builder's live counters (TC-27). Builds every scenario's request to dedupe it; spends nothing."""
    line, states = spec["line"], spec.get("states") or []
    dims = {k: v for k, v in (spec.get("dims") or {}).items() if v}
    cart = 1
    for v in dims.values():
        cart *= len(C.edges(v) if spec.get("reduced") else v)
    ex = expand(spec)
    rows, thinned = _thin(ex["rows"], spec.get("allowance"))
    calls = sum(1 for r in rows if not r.get("stored"))
    left_today = max(0, ledger.LANES["active"] - ledger.used()["active"])
    return {"line": line, "states": len(states), "cartesian": cart * len(states),
            "tier0": invariants.CHECKS_PER_STATE * len(states),
            "pairwise": sum(1 for r in ex["rows"] if r["kind"] in ("pairwise", "base")),
            "edges": sum(1 for r in ex["rows"] if r["kind"] == "edge"),
            "scenarios": len(rows), "alreadyAnswered": sum(1 for r in rows if r.get("stored")),
            "notApplicable": len(ex["notApplicable"]), "thinned": thinned, "calls": calls,
            "days": round(calls / ledger.LANES["active"], 1), "activeLeftToday": left_today,
            "statesKept": len({r["state"] for r in rows})}


# ---- commit and controls ----------------------------------------------------------------------------------------

def _score(r: dict, line: str, open_paths: dict, walked: set) -> int:
    """Information value (TC-30): a scenario that walks a path not yet verified in its state is worth most, then one
    on content that changed (a stale reference), then an edge, then a pairwise row."""
    s = 0
    if walked & open_paths.get(r["state"], set()):
        s += 8
    if r.get("storedOutcome") and not r.get("fresh"):
        s += 4
    s += 2 if r["kind"] == "edge" else 1
    return s


def commit(spec: dict, by: str = "", name: str = "") -> dict:
    """Write the plan. Each scenario is rated once on our engine now (free): its paths give it an information value,
    and its premium is kept for the report. Stored answers are reused, not re-asked."""
    from . import signature, workbench as WB
    line = spec["line"]
    ex = expand(spec)
    rows, thinned = _thin(ex["rows"], spec.get("allowance"))
    open_paths = _untested_paths(line)
    for r in rows:
        req = C.build(line, r["state"], r["config"])
        rr = WB.rate(line, req)
        r["ours"] = rr.get("premium")
        r["oursOutcome"] = rr["outcome"]
        r["paths"] = rr.get("paths", [])
        r["score"] = _score(r, line, open_paths, set(r["paths"]))
        r["status"] = "reuse" if r.get("stored") else "queued"
    pid = time.strftime("%Y%m%d-%H%M%S") + "-" + line
    plan = {"id": pid, "name": name or f"{line} plan, {len(spec.get('states') or [])} state(s)", "line": line,
            "spec": spec, "by": by, "committed_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "queued",
            "lane": "active", "thinned": thinned, "scenarios": sorted(rows, key=lambda r: -r["score"]),
            "notApplicable": ex["notApplicable"], "events": [], "pass3": None}
    save(plan)
    return plan


def path(pid: str) -> Path:
    return PLANS / f"{pid}.json"


def save(plan: dict) -> None:
    with _LOCK:
        PLANS.mkdir(parents=True, exist_ok=True)
        tmp = path(plan["id"]).with_suffix(".tmp")
        tmp.write_text(json.dumps(plan, indent=1), encoding="utf-8")
        tmp.replace(path(plan["id"]))


def load(pid: str) -> dict:
    return json.loads(path(pid).read_text(encoding="utf-8"))


def all_plans() -> list:
    if not PLANS.exists():
        return []
    out = []
    for f in sorted(PLANS.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return out


def summary(plan: dict) -> dict:
    sc = plan["scenarios"]
    count = lambda *st: sum(1 for s in sc if s["status"] in st)    # noqa: E731
    return {"id": plan["id"], "name": plan["name"], "line": plan["line"], "status": plan["status"], "by": plan.get("by", ""),
            "committed_at": plan["committed_at"], "scenarios": len(sc), "queued": count("queued", "reuse"),
            "sent": sum(1 for s in sc if s.get("how") == "sent" or s["status"] == "error"),
            "reused": sum(1 for s in sc if s.get("how") == "dedupe"),
            "match": count("match"), "mismatch": count("mismatch"), "refused": count("refused"), "error": count("error"),
            "notReached": count("not reached"), "notApplicable": len(plan.get("notApplicable", [])),
            "states": len({s["state"] for s in sc}), "pass3": (plan.get("pass3") or {}).get("counts")}


def control(pid: str, action: str, by: str = "") -> dict:
    """D14: start / pause / resume / stop (stop-and-keep: results stay; what was never reached is marked)."""
    with _LOCK:
        plan = load(pid)
        st = plan["status"]
        nxt = {("start", "queued"): "running", ("pause", "running"): "paused", ("resume", "paused"): "running",
               ("resume", "queued"): "running", ("stop", "running"): "stopped", ("stop", "paused"): "stopped",
               ("stop", "queued"): "stopped"}.get((action, st))
        if nxt is None:
            raise ValueError(f"cannot {action} a plan that is {st}")
        plan["status"] = nxt
        if nxt == "stopped":
            for s in plan["scenarios"]:
                if s["status"] in ("queued", "reuse"):
                    s["status"] = "not reached"
        plan["events"].append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": action, "by": by})
        save(plan)
        from . import runlog
        runlog.add(plan=pid, event=action, detail=f"{st} -> {nxt}", by=by)
        return plan
