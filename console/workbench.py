"""The Scenario Workbench's server side (TC-23): build one scenario, rate it free, or spend one call on it.

  * **GL** is built from ISO's own declared domains (`variants.build`, the controls `/tester` offered: T14), for a
    state and effective date; **CP** starts from the state's sample risk (`property_rating.sample`) or a stored request,
    edited as the request itself until CP has a control catalog (TC-26).
  * **Rate internally** is free: today's engine, with `/`'s mode and rounding (D22) for GL.
  * **Send to RaaS** spends one call, through the RaaS client and so through the ledger (D21): ad hoc lane, origin
    `console`; a full lane needs a reason. Before it, the store is asked whether this exact request already has an
    answer (dedupe): the caller is told and must ask again with `reuse=false` to spend anyway.
  * **Run in every state** (D19) rates the same config across every state where it is legal, free, and counts what
    sending it would cost (states with no stored answer); committing it as a plan is RC-4's (TC-29).
"""
from __future__ import annotations

import copy
import sys
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from . import signature, store, tracediff, worksheet as W

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(_p) not in sys.path:
        sys.path.append(str(_p))

ROUNDINGS = ("ROUND_HALF_UP", "ROUND_HALF_EVEN", "ROUND_DOWN")


@lru_cache(maxsize=8)
def _kernel(mode: str, rounding: str):
    import variants as V
    from gl_engine.rating import Kernel
    return Kernel(mode=mode, rounding=rounding, resolver=V.Declared.resolver())


def modes() -> list:
    from gl_engine.rating import MODES
    return list(MODES)


def build(line: str, state: str, config: dict | None = None, request: dict | None = None) -> dict:
    """The request for one scenario. GL: the config applied to the state's declared base (its effective date, if set,
    is the date the domains are read at, as `sweep.py` does). CP: the given request, or the state's sample."""
    if line == "GL":
        from . import catalog                            # one build for GL everywhere: a class gets its basis's exposure
        return catalog.build("GL", state, config or {})
    if request:
        return copy.deepcopy(request)
    import property_rating as pr
    return pr.sample(state)


def rate(line: str, payload: dict, mode: str = "strict-erc", rounding: str = "ROUND_HALF_UP") -> dict:
    """Rate on today's engine, free. Also says whether ISO already answered this exact request."""
    out = {"line": line, "hash": store.request_hash(payload), "mode": mode, "rounding": rounding}
    try:
        if line == "GL":
            r = _kernel(mode, rounding).rate(payload)
            if not r.complete:
                return {**out, "outcome": "stopped", "detail": str(r.stopped)[:400], "stored": stored(payload)}
            from . import catalog
            out.update(premium=str(r.premium), packages=list(r.packages), juris=r.juris, asof=r.asof,
                       paths=sorted(signature.gl_signature(r)), referrals=len(r.referrals),
                       classification=catalog.gl_class_of(payload))
        else:
            tree, trace, total = W.rate("CP", payload)
            out.update(premium=total, paths=sorted(signature.cp_signature(tree)),
                       packages=sorted({t.data.get("package") for t in trace if t.kind == "write" and t.data.get("package")}))
    except Exception as exc:                                  # noqa: BLE001 -- a refusal is an answer, shown as one
        return {**out, "outcome": "refused", "detail": f"{type(exc).__name__}: {exc}"[:400], "stored": stored(payload)}
    return {**out, "outcome": "rated", "stored": stored(payload)}


def stored(payload: dict) -> dict | None:
    """The stored answer for exactly this request (the dedupe check), with ISO's premium when it rated."""
    e = store.lookup(payload)
    if not e:
        return None
    out = {"hash": e["hash"], "outcome": e["outcome"], "date": e["date"], "stored_at": e.get("stored_at", ""),
           "freshness": e.get("freshness", ""), "message": e.get("message", "")[:300],
           "scenario": tracediff.scenario_id(e["line"], e["state"], e["hash"])}
    resp = [f for f in e.get("files", []) if f.endswith("_response.json")]
    if e["outcome"] == "rated" and resp:
        import json
        body = json.loads((ROOT / resp[-1]).read_text(encoding="utf-8")).get("Body", {})
        if e["line"] == "GL":
            out["iso"] = str(((body.get("GeneralLiability") or [{}])[0]).get("Premium"))
        else:
            cp = body.get("CommercialProperty")
            cp = cp[0] if isinstance(cp, list) and cp else cp or {}
            out["iso"] = str(cp.get("ErcCalculatedTotalPremium"))
    return out


def send(line: str, payload: dict, reuse: bool = True, override: str | None = None, client=None) -> dict:
    """One call to ISO, unless an answer is stored and `reuse` is true. `client` is for tests (a stand-in RaaS)."""
    have = stored(payload)
    if have and reuse:
        return {"sent": False, "reused": True, "stored": have}
    if client is None:
        from raas import RaaS
        client = RaaS(lane="adhoc", origin="console", override=override or None)
    from raas import RaaSError
    try:
        client.rate(payload)
    except RaaSError as exc:
        return {"sent": False, "error": str(exc)[:400], "capped": "call not sent" in str(exc),
                "stored": stored(payload)}
    return {"sent": True, "reused": False, "stored": stored(payload)}


def identify(payload) -> dict:
    """An uploaded request's line, state and effective date, read the way ISO reads them: from `SchemeKeys`
    ("General Liability OH", "Commercial Property OH"). Raises ValueError for anything else."""
    keys = (payload.get("body") or {}).get("SchemeKeys") if isinstance(payload, dict) else None
    name = str((keys or {}).get("ProductName") or "").strip()
    for prefix, line, block in (("General Liability", "GL", "GeneralLiability"),
                                ("Commercial Property", "CP", "CommercialProperty")):
        if name.startswith(prefix):
            state = name[len(prefix):].strip().upper()
            if len(state) != 2 or not state.isalpha():
                raise ValueError(f"ProductName {name!r} names no state")
            if not payload["body"].get(block):
                raise ValueError(f"a {prefix} request with no body.{block}")
            return {"line": line, "state": state, "effective": str(keys.get("EffectiveDateTime") or "")[:10]}
    raise ValueError("not an ISO rating request: body.SchemeKeys.ProductName should start General Liability or "
                     f"Commercial Property (found {name!r})" if name else
                     "not an ISO rating request: it has no body.SchemeKeys.ProductName")


def every_state(config: dict, states: list, mode: str = "strict-erc", rounding: str = "ROUND_HALF_UP") -> dict:
    """D19 for GL: the config rated in each state where it is legal (free), and what sending it would cost."""
    import variants as V
    rows, calls = [], 0
    for st in states:
        try:
            p = build("GL", st, config)
        except V.VariantError as exc:
            rows.append({"state": st, "outcome": "not applicable", "detail": str(exc)[:200]})
            continue
        r = rate("GL", p, mode, rounding)
        need = r.get("stored") is None
        calls += need
        rows.append({"state": st, "outcome": r["outcome"], "premium": r.get("premium"), "detail": r.get("detail", ""),
                     "stored": r.get("stored"), "needsCall": need})
    agree = sum(1 for x in rows if x.get("stored") and x["stored"].get("iso") and x.get("premium")
                and Decimal(x["stored"]["iso"]) == Decimal(x["premium"]))
    return {"rows": rows, "callsToSend": calls, "storedAgree": agree,
            "applicable": sum(1 for x in rows if x["outcome"] != "not applicable")}
