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


# ---- carrier deviations on Upload & Compare (DEVIATIONS-PLAN.md P4) ---------------------------------------------------

def companies(root=None) -> list:
    """Every writing company with a compiled filing: its code, name, carrier, and the filings it can rate under
    (approved now, by the file and the workflow log). Read from CARRIERS_ROOT; nothing is written."""
    from deviations.config import CARRIERS_ROOT
    from deviations.files import carrier_json, read_json, workflow_status
    root = Path(root or CARRIERS_ROOT)
    out = []
    for cj in sorted(root.glob("*/*/company.json")):
        cdir, carrier = cj.parent, cj.parent.parent
        info = read_json(cj)
        need = int(carrier_json(carrier).get("approval", {}).get("signoffs", 1))
        filings = []
        for m in sorted(cdir.glob("compiled/*/*/*/manifest.json")):
            man = read_json(m)
            st = workflow_status(cdir, man["filing"], man["version"], need)["status"]
            filings.append({"line": man["line"], "juris": man["juris"], "filing": man["filing"],
                            "version": man["version"], "new_eff": man["new_eff"], "renewal_eff": man["renewal_eff"],
                            "approved": st == "approved" and man["header"].get("status") == "approved"})
        out.append({"code": info.get("code", cdir.name), "name": info.get("name", cdir.name),
                    "carrier": carrier.name, "filings": filings})
    return out


def rate_company(line: str, payload: dict, company: str, policy_type: str = "New", root=None) -> dict:
    """Technical / ISO / Carrier for one request (D21). `premium` and `outcome` are TECHNICAL's -- the rating set
    beside ISO's answer, as an upload without a company is -- and `stored` is ISO's answer to the NON-DEVIATED
    payload, the only one ISO is ever sent. `carrier` is our rating of the deviated payload, never sent."""
    from deviations.engine import iso_request
    req = copy.deepcopy(payload)
    req.setdefault("header", {})
    req["header"]["WritingCompany"] = company
    req["header"]["PolicyType"] = policy_type or "New"
    ln = "CF" if line == "CP" else "GL"
    plain, _ = iso_request(req, ln)
    if line == "GL":
        from gl_engine.rating import Kernel
        r = Kernel().rate(req, with_technical=True, **({"root": root} if root else {}))
        t = r.technical
        tech = (str(t.premium), "rated") if t is not None and t.complete else (None, "refused")
        car = (str(r.premium), "rated") if r.complete else (None, "refused")
        detail = "" if r.complete else str(r.stopped or (r.deviation or {}).get("refused", ""))[:400]
    else:
        from cf_engine.rating import rate as cf_rate
        r = cf_rate(req, with_technical=True, **({"root": root} if root else {}))
        t = r.technical
        tech = (t.premium, "rated") if t is not None and t.complete else (None, "refused")
        car = (r.premium, "rated") if r.complete else (None, "refused")
        detail = "" if r.complete else "; ".join(x.get("detail", "") for x in r.outcome.get("reasons", []))[:400]
    dev = r.deviation or {}
    return {"line": line, "company": company, "policyType": req["header"]["PolicyType"],
            "hash": store.request_hash(plain), "premium": tech[0], "outcome": tech[1],
            "detail": detail if tech[1] != "rated" else "",
            "carrier": {"premium": car[0], "outcome": car[1], "detail": detail},
            "deviation": {k: dev.get(k) for k in ("writingCompany", "policyType", "edition", "pinned", "filings",
                                                  "technicalPremium", "carrierPremium", "waterfall", "warnings",
                                                  "refused")}
                         | {"changedFields": len(dev.get("changedPaths") or [])},
            "stored": stored(plain)}


def send_technical(line: str, payload: dict, company: str, reuse: bool = True, override: str | None = None,
                   client=None) -> dict:
    """Ask ISO about a company request: the NON-DEVIATED payload only (D21)."""
    from deviations.engine import iso_request
    req = copy.deepcopy(payload)
    req.setdefault("header", {})["WritingCompany"] = company
    plain, _ = iso_request(req, "CF" if line == "CP" else "GL")
    return send(line, plain, reuse=reuse, override=override, client=client)


def worksheet(line: str, payload: dict, company: str = "", policy_type: str = "New", root=None) -> dict:
    """The rating worksheet for one request: every field, record by record, as Technical | ISO | Deviated.

    * **Technical** -- our engine, pure ISO, on the non-deviated payload (with no company: the request as given);
    * **ISO** -- ISO's stored answer to that same payload, if it was ever asked (opening a worksheet never calls ISO);
    * **Deviated** -- our engine through the company's filing (only with a company; never sent to ISO).

    Rows are `console.worksheet.align`'s (Trace Diff's alignment, with the rule file and tables that wrote each
    technical value), plus the deviated value at the same path. Free: two ratings, no calls.
    """
    from . import worksheet as W
    ln = "CF" if line == "CP" else "GL"
    req = copy.deepcopy(payload)
    if company:
        from deviations.engine import iso_request
        req.setdefault("header", {})
        req["header"]["WritingCompany"] = company
        req["header"]["PolicyType"] = policy_type or "New"
        plain, _ = iso_request(req, ln)
    else:
        plain = req
    dev = None
    if line == "GL":
        from gl_engine.rating import Kernel
        k = Kernel()
        if company:
            r = k.rate(req, with_technical=True, **({"root": root} if root else {}))
            tech = r.technical
            t_tree, t_trace, t_prem = (tech.tree, tech.trace, str(tech.premium)) if tech and tech.complete else (None, [], None)
            d_tree, d_prem = (r.tree, str(r.premium)) if r.complete else (None, None)
            dev = r.deviation
        else:
            r = k.rate(req)
            t_tree, t_trace, t_prem = (r.tree, r.trace, str(r.premium)) if r.complete else (None, [], None)
            d_tree = d_prem = None
    else:
        from cf_engine.rating import rate as cf_rate
        if company:
            r = cf_rate(req, with_technical=True, **({"root": root} if root else {}))
            tech = r.technical
            t_tree, t_trace, t_prem = (tech.tree, tech.ip.trace, tech.premium) if tech and tech.complete else (None, [], None)
            d_tree, d_prem = (r.tree, r.premium) if r.complete else (None, None)
            dev = r.deviation
        else:
            r = cf_rate(req)
            t_tree, t_trace, t_prem = (r.tree, r.ip.trace, r.premium) if r.complete else (None, [], None)
            d_tree = d_prem = None
    if t_tree is None:
        return {"line": line, "error": "our engine did not rate the technical request" + (
            f": {(dev or {}).get('refused', '')}" if dev else "")}

    e = store.lookup(plain)
    body, iso_prem, iso_state = None, None, "not asked"
    if e:
        if e["outcome"] == "rated":
            resp = [f for f in e["files"] if f.endswith("_response.json")]
            if resp:
                import json
                body = W.body_of(line, json.loads((ROOT / resp[-1]).read_text(encoding="utf-8")))
                iso_state = "rated"
        else:
            iso_state = "refused"
    key = "CommercialProperty" if line == "CP" else "GeneralLiability"
    rows = W.align(line, t_tree, t_trace, body if body is not None else {key: None})
    if body is not None:
        b = body.get(key)
        b = b[0] if isinstance(b, list) and b else b or {}
        iso_prem = b.get("ErcCalculatedTotalPremium") if line == "CP" else b.get("Premium")
    deviated = {}
    if d_tree is not None:
        deviated, _ = W.our_leaves(d_tree)
        tops = (f"/{key}",)
        deviated = {p: v for p, v in deviated.items() if p.startswith(tops)}
    out_rows, seen = [], set()
    for x in rows:
        if not x["in_ours"]:
            continue                          # an ISO-only field: listed after, with no technical value
        p = x["path"]
        seen.add(p)
        d = deviated.get(p) if d_tree is not None else None
        out_rows.append({"path": p, "record": x["record"], "field": x["field"], "kind": x["kind"],
                         "technical": x["ours"], "iso": x["iso"], "deviated": d,
                         "techIso": x["match"], "changed": (d_tree is not None and not W.same(d, x["ours"])),
                         "rule": x["rule_file"], "tables": x["tables"], "order": x["order"]})
    for p, v in deviated.items():             # fields only the deviated rating writes (e.g. a record's LCM)
        if p not in seen:
            out_rows.append({"path": p, "record": W.record_of(p), "field": p.rsplit("/", 1)[-1], "kind": W.kind(v),
                             "technical": None, "iso": None, "deviated": v, "techIso": None, "changed": True,
                             "rule": "", "tables": [], "order": None})
    for x in rows:
        # a field only ISO publishes: shown when it carries a value (an empty one is no difference), marked ISO-only
        if not x["in_ours"] and x["iso"] not in (None, ""):
            out_rows.append({"path": x["path"], "record": x["record"], "field": x["field"], "kind": x["kind"],
                             "technical": None, "iso": x["iso"], "deviated": deviated.get(x["path"]),
                             "techIso": False, "isoOnly": True, "changed": False, "rule": "(ISO only)", "tables": [],
                             "order": None})
    return {"line": line, "state": identify(payload)["state"], "company": company or None,
            "policyType": (policy_type or "New") if company else None,
            "premium": {"technical": t_prem, "iso": None if iso_prem is None else str(iso_prem), "deviated": d_prem},
            "iso": iso_state, "isoHash": store.request_hash(plain),
            "deviation": {k: (dev or {}).get(k) for k in ("filings", "edition", "waterfall", "warnings")} if dev else None,
            "rows": out_rows}
