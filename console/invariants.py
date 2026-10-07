"""Tier 0 (TC-28): properties of our own engine that hold whatever ISO answers, checked at zero calls.

Not `qa.py`'s T0 (a live smoke run, TC-02): these are invariants, rated on today's engine only.

  * **limits**      premium never falls as a limit rises (GL each-occurrence; CP building limit)
  * **deductibles** premium never rises as a deductible rises (GL Prem/Ops PD; CP building deductible)
  * **floor**       the premium is a number, not negative (a minimum-premium floor holds: GL files $0, D9)
  * **no nulls**    no premium was written as 0 because something upstream was null (OI-109's mark in the trace)
  * **classes**     a sample of the state's class codes all resolve (GL: per premium basis; CP: per category)

A refusal by decision (C28-17 and the like) on a varied value is reported, not failed: it is the engine declining, as
designed, and Trace Diff is where it is judged against ISO.
"""
from __future__ import annotations

from decimal import Decimal

from . import catalog as C
from . import workbench as WB


def _prem(line: str, cfg: dict, state: str) -> tuple:
    """(premium | None, refusal | None, trace kinds)."""
    try:
        p = C.build(line, state, cfg)
    except Exception as exc:                                  # noqa: BLE001 -- not expressible here
        return None, f"not applicable: {exc}"[:200], set()
    if line == "GL":
        r = WB._kernel("strict-erc", "ROUND_HALF_UP").rate(p)
        if not r.complete:
            return None, f"stopped: {r.stopped}"[:200], {t.kind for t in r.trace}
        return r.premium, None, {t.kind for t in r.trace}
    from . import worksheet as W
    try:
        _, trace, tot = W.rate("CP", p)
    except Exception as exc:                                  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"[:200], set()
    return (Decimal(str(tot)) if tot is not None else None), None, {t.kind for t in trace}


def _monotone(line, state, dim, values, rising: bool) -> dict:
    pts, notes = [], []
    for v in values:
        prem, why, _ = _prem(line, {dim: v}, state)
        if prem is None:
            notes.append(f"{v}: {why}")
            continue
        pts.append((v, prem))
    bad = [(a, b) for a, b in zip(pts, pts[1:]) if (b[1] < a[1] if rising else b[1] > a[1])]
    return {"ok": not bad, "points": [(v, str(p)) for v, p in pts], "skipped": notes[:5],
            "detail": "; ".join(f"{a[0]} {a[1]} -> {b[0]} {b[1]}" for a, b in bad)[:300]}


LIMIT = {"GL": "occurrence_limit", "CP": "bldg_limit"}
DEDUCTIBLE = {"GL": "premops_pd_deductible", "CP": "bldg_deductible"}


def _num(v) -> float:
    s = "".join(ch for ch in str(v) if ch.isdigit() or ch == ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def check_state(line: str, state: str, classes: int = 6) -> list:
    """Every Tier 0 check for one line and state, as {check, ok, detail}."""
    dims = {d["id"]: d for d in C.dimensions(line, state)}
    out = []
    lim = sorted(dims[LIMIT[line]]["values"], key=_num)
    if len(lim) > 6:
        lim = [lim[i * (len(lim) - 1) // 5] for i in range(6)]
    r = _monotone(line, state, LIMIT[line], lim, rising=True)
    out.append({**r, "check": "limits", "detail": r["detail"] or f"{len(r['points'])} limits, premium non-decreasing"})
    ded = [v for v in dims[DEDUCTIBLE[line]]["values"] if _num(v) or v == "No Deductible"]
    ded = sorted(ded, key=_num)
    ded = ded if len(ded) <= 6 else [ded[i * (len(ded) - 1) // 5] for i in range(6)]
    r = _monotone(line, state, DEDUCTIBLE[line], ded, rising=False)
    out.append({**r, "check": "deductibles", "detail": r["detail"] or f"{len(r['points'])} deductibles, premium non-increasing"})
    prem, why, kinds = _prem(line, {}, state)
    out.append({"check": "floor", "ok": prem is not None and prem >= 0,
                "detail": f"base premium {prem}" if prem is not None else f"base risk does not rate: {why}"})
    nulls = kinds & {"null-premium-zeroed"}          # OI-109's mark; a null propagating through a non-premium step is normal
    out.append({"check": "no nulls", "ok": prem is not None and not nulls,
                "detail": "no null premium steps" if not nulls else f"trace shows {sorted(nulls)}"})
    cls = list(dims["class_code"]["values"])
    sample = [cls[i * (len(cls) - 1) // max(1, classes - 1)] for i in range(min(classes, len(cls)))] if cls else []
    failed = []
    for c in dict.fromkeys(sample):
        cfg = {"class_code": c}
        if line == "GL":
            cfg = {}                                          # a class must come with its basis: let variants pick
            for b in dims["premium_basis"]["values"][:1]:
                cfg = {"premium_basis": b}
            codes = C.dimensions("GL", state, cfg)
            cls_b = next(d for d in codes if d["id"] == "class_code")["values"]
            if c not in cls_b:
                continue
            cfg["class_code"] = c
        p, why, _ = _prem(line, cfg, state)
        if p is None and not (why or "").startswith("not applicable"):
            failed.append(f"{c}: {why}")
    out.append({"check": "classes", "ok": not failed, "detail": f"{len(sample)} sampled class codes resolve"
                if not failed else "; ".join(failed)[:300]})
    return out


def run(line: str, states: list, classes: int = 6) -> dict:
    rows = []
    for st in states:
        try:
            for c in check_state(line, st, classes):
                rows.append({"state": st, **{k: v for k, v in c.items() if k in ("check", "ok", "detail")}})
        except Exception as exc:                              # noqa: BLE001 -- a state whose base risk cannot be built
            rows.append({"state": st, "check": "build", "ok": False, "detail": f"{type(exc).__name__}: {exc}"[:200]})
    return {"line": line, "checks": len(rows), "passed": sum(r["ok"] for r in rows),
            "failed": [r for r in rows if not r["ok"]], "rows": rows}


CHECKS_PER_STATE = 5
