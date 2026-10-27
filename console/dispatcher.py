"""The dispatcher (TC-30) and the cap override (TC-32).

Works through running plans one call at a time, in information-value order (a scenario walking a path not yet
verified in its state, then content that changed, then an edge, then a pairwise row: `plans._score`), inside the
active lane and the daily cap (D2). Before **every** call the store is asked again for this exact request (dedupe): a
plan committed yesterday may find today that someone else's call already answered it.

Each answer: re-rated on our engine, compared (`console.worksheet.same` on the premium), its paths taken from our
rating (`console.signature`), recorded as evidence (so the matrix and board move), logged (`console.runlog`). The
call itself goes through the RaaS client, so the ledger counts it and the store keeps ISO's answer (D21).

A full lane stops dispatch for the day (`capped`, logged once) unless an **override** is set for today: a reason, a
number of calls and who set it (`results/tc/override.json`); each call it lets through is logged as an override, in
the ledger and the run log (TC-32).

When a plan has nothing left, it is `done`; for GL, **pass 3** (D15) then reviews every scenario the plan found not
expressible in a state (`qa_review.review_not_applicable`: CONFIRMED / CONTRADICTED / UNVERIFIED).
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from . import catalog as C
from . import evidence, ledger, plans as P, runlog, signature, store, worksheet as W

ROOT = Path(__file__).resolve().parent.parent
OVERRIDE = ROOT / "results" / "tc" / "override.json"
_STATE = {"thread": None, "stop": False, "capped_day": None, "last_day": None}
_LOCK = threading.Lock()


# ---- override (TC-32) ---------------------------------------------------------------------------------------------

def override() -> dict | None:
    """Today's override, if one is set and has calls left."""
    if not OVERRIDE.exists():
        return None
    o = json.loads(OVERRIDE.read_text(encoding="utf-8"))
    if o.get("day") != ledger.day() or o.get("left", 0) <= 0:
        return None
    return o


def set_override(reason: str, calls: int, by: str = "") -> dict:
    if not reason.strip() or calls <= 0:
        raise ValueError("an override needs a reason and a number of calls")
    o = {"day": ledger.day(), "reason": reason.strip(), "calls": int(calls), "left": int(calls), "by": by,
         "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE.write_text(json.dumps(o, indent=1), encoding="utf-8")
    runlog.add(plan="", event="override-set", detail=f"{calls} call(s): {reason.strip()}", by=by)
    return o


def _use_override() -> str | None:
    o = override()
    if not o:
        return None
    o["left"] -= 1
    OVERRIDE.write_text(json.dumps(o, indent=1), encoding="utf-8")
    return f"{o['reason']} (by {o['by'] or '?'})"


# ---- one step -----------------------------------------------------------------------------------------------------

def _path(f) -> Path:
    f = Path(f)
    return f if f.is_absolute() else ROOT / f


def _premium(line: str, resp: dict):
    b = resp.get("Body", {})
    if line == "GL":
        return ((b.get("GeneralLiability") or [{}])[0]).get("Premium")
    cp = b.get("CommercialProperty")
    cp = cp[0] if isinstance(cp, list) and cp else cp or {}
    return cp.get("ErcCalculatedTotalPremium")


def _iso_answer(e: dict) -> tuple[str, object, str]:
    """(outcome, premium, message) of a stored answer."""
    if e["outcome"] != "rated":
        return "refused", None, e.get("message", "")
    resp = [f for f in e["files"] if f.endswith("_response.json")]
    body = json.loads(_path(resp[-1]).read_text(encoding="utf-8")) if resp else {}
    return "rated", _premium(e["line"], body), ""


def _record(plan: dict, s: dict, req: dict, e: dict, how: str) -> None:
    """Compare ours with ISO's stored answer, record the evidence, mark the scenario."""
    line = s.get("line") or plan["line"]
    outcome, iso, msg = _iso_answer(e)
    sid = f"{line}-{s['state']}-{e['hash'][:10]}"
    try:
        if line == "GL":
            from . import workbench as WB
            r = WB._kernel("strict-erc", "ROUND_HALF_UP").rate(req)
            ours, walked = (str(r.premium), signature.gl_signature(r)) if r.complete else (None, set())
        else:
            tree, _, ours = W.rate("CP", req)
            walked = signature.cp_signature(tree)
    except Exception as exc:                                  # noqa: BLE001 -- ours refuses
        ours, walked, msg = None, set(), f"ours refuses: {exc}"[:300]
    if outcome == "refused":
        status = "refused"
    elif ours is None:
        status = "mismatch"
    else:
        status = "match" if W.same(ours, iso) else "mismatch"
    evidence.add(scenario=sid, line=line, state=s["state"], walked=walked, ours=ours,
                 iso=None if outcome == "refused" else iso, request_hash=e["hash"], source=f"plan {plan['id']}",
                 inert=bool(s.get("inert")), plan=plan["id"], kind=s["kind"])
    if s.get("inert"):
        runlog.add(plan=plan["id"], event="inert", scenario=sid, state=s["state"],
                   detail=f"exercised nothing: rates as the base risk through the same paths ({', '.join(f'{k}={v}' for k, v in s['config'].items())})")
    s.update(status=status, iso=None if iso is None else str(iso), oursNow=ours, scenario=sid, how=how,
             message=msg[:300], at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    runlog.add(plan=plan["id"], event="dedupe" if how == "dedupe" else "sent", scenario=sid, state=s["state"],
               detail=f"{status}: ours {ours} · ISO {iso if outcome == 'rated' else 'refused'}", outcome=status,
               hash=e["hash"])


def step(plan_id: str, client_factory=None) -> str:
    """Dispatch one scenario of a running plan. Returns what happened: 'sent', 'dedupe', 'capped', 'idle', 'done'."""
    plan = P.load(plan_id)
    if plan["status"] != "running":
        return "idle"
    queue = [s for s in plan["scenarios"] if s["status"] in ("queued", "reuse")]
    if not queue:
        plan["status"] = "done"
        plan["events"].append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": "done"})
        if plan["line"] == "GL" and plan.get("notApplicable"):
            plan["pass3"] = pass3(plan)
            runlog.add(plan=plan_id, event="pass3", detail=json.dumps(plan["pass3"]["counts"]))
        P.save(plan)
        sm = P.summary(plan)
        runlog.add(plan=plan_id, event="done", detail=f"{sm['sent']} sent · {sm['reused']} reused · {sm['match']} match · "
                                                      f"{sm['mismatch']} mismatch · {sm['refused']} refused · {sm['error']} error")
        # the plan's answers join the reference index (staleness, counts) without anyone running store.build by hand
        threading.Thread(target=store.build, name="tc-index", daemon=True).start()
        return "done"
    s = max(queue, key=lambda x: (x["status"] == "reuse", x.get("score", 0)))
    line = s.get("line") or plan["line"]
    lane = plan.get("lane", "active")
    # a refresh scenario re-sends the request it was answered on; a plan scenario is built from its config
    req = (json.loads(_path(s["request_file"]).read_text(encoding="utf-8")) if s.get("request_file")
           else C.build(line, s["state"], s["config"]))
    e = store.lookup(req)
    if e and e["outcome"] in ("rated", "refused") and e.get("freshness") != "stale":   # dedupe before every call
        _record(plan, s, req, e, "dedupe")
        P.save(plan)
        return "dedupe"
    used = ledger.used()
    full = used[lane] >= ledger.LANES[lane] or used["total"] >= ledger.CAP
    reason = None
    if full:
        reason = _use_override()
        if reason is None:
            if _STATE["capped_day"] != ledger.day():
                _STATE["capped_day"] = ledger.day()
                runlog.add(plan=plan_id, event="capped", detail=f"{lane} lane {used[lane]} of {ledger.LANES[lane]}, "
                                                                 f"{used['total']} of {ledger.CAP}: waiting for the reset")
            return "capped"
    if client_factory is None:
        import sys
        sys.path.append(str(ROOT / "scripts"))
        from raas import RaaS

        def client_factory(ov):
            return RaaS(lane=lane, origin=f"plan:{plan_id}", override=ov)
    from raas import RaaSError
    try:
        client_factory(reason).rate(req)
    except RaaSError as exc:
        if "call not sent" in str(exc):
            runlog.add(plan=plan_id, event="capped", detail=str(exc)[:200])
            return "capped"
        e = store.lookup(req)                                 # a refusal is stored as an answer
        if not (e and e["outcome"] == "refused"):
            s.update(status="error", message=str(exc)[:300], at=time.strftime("%Y-%m-%dT%H:%M:%S"))
            runlog.add(plan=plan_id, event="sent", scenario=s.get("scenario", ""), state=s["state"],
                       detail=f"error: {str(exc)[:200]}", outcome="error")
            P.save(plan)
            return "sent"
    e = store.lookup(req)
    if reason:
        runlog.add(plan=plan_id, event="override", state=s["state"], detail=reason)
    if e is None:                                             # the answer was not kept: count it as an error
        s.update(status="error", message="ISO answered but the answer was not stored", at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        P.save(plan)
        return "sent"
    _record(plan, s, req, e, "sent")
    P.save(plan)
    return "sent"


def pass3(plan: dict) -> dict:
    """D15: every scenario this GL plan found not expressible, reviewed independently against ISO's own CSVs."""
    import sys
    sys.path.append(str(ROOT / "scripts"))
    import qa_review as QR
    out = []
    for r in plan.get("notApplicable", []):
        try:
            v = QR.review_not_applicable(r["state"], r["config"], r.get("detail", ""))
        except Exception as exc:                              # noqa: BLE001
            v = {"verdict": "UNVERIFIED", "findings": [{"why": f"review failed: {exc}"}]}
        out.append({"state": r["state"], "config": r["config"], "verdict": v["verdict"],
                    "why": (v.get("cause") or (v.get("findings") or [{}])[0]).get("why", "")})
    counts: dict = {}
    for x in out:
        counts[x["verdict"]] = counts.get(x["verdict"], 0) + 1
    return {"counts": counts, "results": out}


# ---- the loop -------------------------------------------------------------------------------------------------------

def tick(client_factory=None) -> list:
    """One pass over the running plans (oldest first): one scenario each. Logs a reset when the day turns."""
    d = ledger.day()
    if _STATE["last_day"] and _STATE["last_day"] != d:
        runlog.add(plan="", event="reset", detail=f"new day {d}: lanes reset")
        _STATE["capped_day"] = None
    _STATE["last_day"] = d
    out = []
    for p in sorted(P.all_plans(), key=lambda x: x["committed_at"]):
        if p["status"] == "running":
            out.append((p["id"], step(p["id"], client_factory)))
    return out


def start(interval: float = 2.0) -> None:
    """The background loop, once per process (the app). Idle when no plan runs."""
    with _LOCK:
        t = _STATE["thread"]
        if t is not None and t.is_alive():
            return

        def loop():
            while not _STATE["stop"]:
                try:
                    did = tick()
                except Exception as exc:                      # noqa: BLE001 -- logged, never kills the loop
                    runlog.add(plan="", event="error", detail=f"dispatcher: {type(exc).__name__}: {exc}"[:300])
                    did = []
                busy = any(x[1] in ("sent", "dedupe") for x in did)
                time.sleep(0.2 if busy else interval)

        _STATE["stop"] = False
        _STATE["thread"] = threading.Thread(target=loop, name="tc-dispatcher", daemon=True)
        _STATE["thread"].start()
