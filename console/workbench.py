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


_GROUP_FIELD = {"GroupI": "GroupILCMApplied", "GroupII": "GroupIILCMApplied", "Broad": "BroadLCMApplied",
                "Special": "SpecialLCMApplied", "Earthquake": "EarthquakeLCMApplied"}


def _node_paths(tree) -> dict:
    """id(node) -> the normalised path of every record in a rated tree (the worksheet's path form)."""
    from . import worksheet as W
    out: dict = {}

    def walk(node, prefix):
        seen: dict = {}
        for c in node.children:
            i = seen.get(c.tag, 0)
            seen[c.tag] = i + 1
            p = f"{prefix}/{c.tag}[{i}]"
            if c.children:
                out[id(c)] = W.normalise(p)
                walk(c, p)
    walk(tree, "")
    return out


def _applied_lcms(t_tree, d_tree, carrier_trace, body, key) -> list:
    """One worksheet row per record and coverage group where the carrier applied a group LCM (D17): the value each
    group's rate was actually multiplied by, which no single tree field holds. Technical and ISO show the record's
    own LCM there (ISO applies one LCM to every group)."""
    from . import worksheet as W
    paths = _node_paths(d_tree)
    tech_leaves, _ = W.our_leaves(t_tree)
    iso_leaves = W.iso_leaves(body) if body is not None else {}
    rows, seen = [], set()
    for n, t in enumerate(carrier_trace):
        if t.kind != "company-group-lcm":
            continue
        d = t.data or {}
        rec = paths.get(d.get("node"))
        if rec is None or not rec.startswith(f"/{key}") or (rec, d["group"]) in seen:
            continue
        seen.add((rec, d["group"]))
        tech = tech_leaves.get(f"{rec}/LossCostMultiplier")
        iso = iso_leaves.get(f"{rec}/LossCostMultiplier")
        rows.append({"path": f"{rec}/{_GROUP_FIELD[d['group']]}", "record": rec,
                     "field": _GROUP_FIELD[d["group"]], "kind": "number", "technical": tech, "iso": iso,
                     "deviated": d["value"], "techIso": None if iso is None or tech is None else W.same(tech, iso),
                     "changed": not W.same(d["value"], tech), "rule": "company group LCM (D17), applied to "
                     + ", ".join(d.get("operands") or []), "tables": [d.get("explain", "")], "order": n,
                     "applied": True})
    return rows


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
    carrier_trace: list = []
    t_graph = d_graph = None
    if line == "GL":
        from gl_engine.rating import Kernel
        k = Kernel()
        if company:
            r = k.rate(req, with_technical=True, graph=True, **({"root": root} if root else {}))
            tech = r.technical
            t_tree, t_trace, t_prem = (tech.tree, tech.trace, str(tech.premium)) if tech and tech.complete else (None, [], None)
            d_tree, d_prem = (r.tree, str(r.premium)) if r.complete else (None, None)
            t_graph, d_graph = (tech.deps if tech else None), r.deps
            dev = r.deviation
        else:
            r = k.rate(req, graph=True)
            t_tree, t_trace, t_prem = (r.tree, r.trace, str(r.premium)) if r.complete else (None, [], None)
            d_tree = d_prem = None
            t_graph, d_graph = r.deps, None
    else:
        from cf_engine.rating import rate as cf_rate
        if company:
            r = cf_rate(req, with_technical=True, graph=True, **({"root": root} if root else {}))
            tech = r.technical
            t_tree, t_trace, t_prem = (tech.tree, tech.ip.trace, tech.premium) if tech and tech.complete else (None, [], None)
            d_tree, d_prem = (r.tree, r.premium) if r.complete else (None, None)
            carrier_trace = r.ip.trace if r.ip is not None else []
            t_graph, d_graph = (tech.graph if tech else None), r.graph
            dev = r.deviation
        else:
            r = cf_rate(req, graph=True)
            t_tree, t_trace, t_prem = (r.tree, r.ip.trace, r.premium) if r.complete else (None, [], None)
            d_tree = d_prem = None
            t_graph, d_graph = r.graph, None
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
    applied = _applied_lcms(t_tree, d_tree, carrier_trace, body, key) if (line == "CP" and d_tree is not None) else []
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
    out_rows += applied
    for r in out_rows:
        if line == "CP" and r["field"] == "LossCostMultiplier" and d_tree is not None:
            r["note"] = "the record's LCM: holds the Group I value (G2); each coverage group applies its own, "                         "shown as 'LCM applied' in that group's section"
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
            "sections": calculation_view(line, out_rows), "rows": _with_gids(out_rows, t_graph, d_graph),
            "graph": _keep_graphs(t_graph, d_graph, line)}


# ---- the worksheet's calculation view: coverage groups, in the order the engine computed them -----------------------

import re as _re

#: Property's coverage groups (the deviations engine's own matcher, D17) and GL's sublines, in display order.
_CF_GROUPS = (("GroupI", "Basic Group I"), ("GroupII", "Basic Group II"), ("Broad", "Broad"),
              ("Special", "Special"), ("Earthquake", "Earthquake"))
_GL_GROUPS = (("PremOps", "Premises/Operations", _re.compile(r"PremOps|PremisesOperations")),
              ("ProdsCompldOps", "Products/Completed Operations", _re.compile(r"ProdsCompldOps|ProdCompldOps|ProductsCompleted")),
              ("Liquor", "Liquor Liability", _re.compile(r"Liquor")),
              ("OCP", "Owners and Contractors Protective", _re.compile(r"OwnersContractors|OwnersContrctrs")),
              ("Railroad", "Railroad Protective", _re.compile(r"Railroad")),
              ("Pollution", "Pollution", _re.compile(r"Pollution")),
              ("ProductWithdrawal", "Product Withdrawal", _re.compile(r"ProductWithdrawal")),
              ("Terrorism", "Terrorism", _re.compile(r"Terror|TRIA|CertfdActs|CertifiedActs")))
#: The records a worksheet section belongs to (the item being rated), innermost wins.
_ITEMS = {"CommercialPropertyLocation": "Location", "CommercialPropertyStructure": "Building",
          "CommercialPropertyOccupClass": "Occupancy", "CommercialPropertyPersonalProperty": "Personal property",
          "CommercialPropertyBusinessIncome": "Business income", "CommercialPropertySpecialClass": "Special class",
          "CommercialPropertySpecialClassBusnIncome": "Special class business income",
          "GeneralLiabilityLocation": "Location", "GeneralLiabilityClassification": "Classification"}
_SEG = _re.compile(r"^(\w+?)(?:\[(\d+)\])?$")


def _group(line: str, path: str):
    """(key, label) of the coverage group a field belongs to, by its own name first, then its records'."""
    names = [p for p in path.strip("/").split("/")]
    names = [_SEG.match(n).group(1) if _SEG.match(n) else n for n in names]
    field, recs = names[-1], list(reversed(names[:-1]))
    if line == "CP":
        from deviations.engine import group_of
        for n in [field] + recs:
            g = group_of([n])
            if g:
                return g, dict(_CF_GROUPS)[g]
        return None, None
    for n in [field] + recs:
        for key, label, rx in _GL_GROUPS:
            if rx.search(n):
                return key, label
    return None, None


def _item(path: str) -> str:
    """'Location 2 › Building › Personal property' -- the rated item a field sits under (indices are 1-based)."""
    out = []
    for seg in path.strip("/").split("/")[:-1]:
        m = _SEG.match(seg)
        if not m or m.group(1) not in _ITEMS:
            continue
        label = _ITEMS[m.group(1)]
        out.append(f"{label} {int(m.group(2)) + 1}" if m.group(2) else label)
    return " › ".join(out) or "Policy"


_TRIM = _re.compile(r"^(CommercialProperty|GeneralLiability)(Structure|PersonalProperty|BusinessIncome|SpecialClass|"
                    r"Classification|Location|OccupClass)?")


def _label(path: str) -> str:
    """The field, prefixed by any record between the rated item and it: 'BuildingBasicGroupICoverage › Premium'."""
    segs = path.strip("/").split("/")
    last = max((i for i, sg in enumerate(segs[:-1]) if _SEG.match(sg) and _SEG.match(sg).group(1) in _ITEMS),
               default=-1)
    sub = [(_TRIM.sub("", _SEG.match(sg).group(1)) or _SEG.match(sg).group(1)) + (
        f" {int(_SEG.match(sg).group(2)) + 1}" if _SEG.match(sg).group(2) else "")
        for sg in segs[last + 1:-1] if _SEG.match(sg)]
    return " › ".join(sub + [segs[-1]])


def calculation_view(line: str, rows: list) -> list:
    """Give each worksheet row its section (item × coverage group) and an order inside it; returns the sections in
    display order. A section's rows run in the order our engine wrote them, so a group's chain reads top to bottom:
    base rate, LCM, adjustments, final rate, premium. Inputs (nothing wrote them) come first."""
    order = [k for k, *_ in (_CF_GROUPS if line == "CP" else _GL_GROUPS)]
    labels = dict((k, lab) for k, lab, *_ in (_CF_GROUPS if line == "CP" else _GL_GROUPS))
    first_seen: dict = {}
    for i, r in enumerate(rows):
        g, _ = _group(line, r["path"])
        item = _item(r["path"])
        key = f"{item}|{g or '~shared'}"
        r["section"] = key
        r["label"] = _label(r["path"])
        if r.get("applied"):
            r["label"] = r["label"].rsplit("›", 1)[0].strip() + " › LCM applied" if "›" in r["label"] else "LCM applied"
        r["sectionLabel"] = f"{item} · {labels[g]}" if g else f"{item} · shared factors and other fields"
        r["group"] = g
        first_seen.setdefault(item, i)
        r["_sort"] = (r["order"] is not None, r["order"] if r["order"] is not None else i)
    sections: dict = {}
    for r in rows:
        sections.setdefault(r["section"], {"key": r["section"], "label": r["sectionLabel"], "group": r["group"],
                                           "item": r["section"].split("|")[0], "rows": []})["rows"].append(r)
    for sec in sections.values():
        sec["rows"].sort(key=lambda r: r["_sort"])
    for r in rows:
        r.pop("_sort", None)
    gi = {k: n for n, k in enumerate(order)}
    out = sorted(sections.values(), key=lambda s: (first_seen[s["item"]],
                                                   gi.get(s["group"], len(order)) if s["group"] else -1))
    return [{"key": s["key"], "label": s["label"], "group": s["group"], "paths": [r["path"] for r in s["rows"]]}
            for s in out]



# ---- G2: why this value (docs/RATING-GRAPH-PLAN.md) ------------------------------------------------------------------

from collections import OrderedDict as _OD
import uuid as _uuid

#: The last few worksheets' graphs, by token: a drill-down reads them instead of rating again.
_GRAPHS = _OD()
_GRAPHS_KEEP = 8


def _keep_graphs(t_graph, d_graph, line: str):
    if t_graph is None:
        return None
    tok = _uuid.uuid4().hex[:16]
    affected = set()
    if d_graph is not None:
        comp = [n["id"] for n in d_graph.nodes if n["kind"] == "company" or
                (n["kind"] == "table" and n.get("company"))]
        affected = d_graph.reach(comp) | set(comp)
    _GRAPHS[tok] = {"technical": t_graph, "deviated": d_graph, "affected": affected, "line": line}
    while len(_GRAPHS) > _GRAPHS_KEEP:
        _GRAPHS.popitem(last=False)
    return tok


def _with_gids(rows: list, t_graph, d_graph) -> list:
    for r in rows:
        if t_graph is not None and r.get("technical") is not None and not r.get("applied"):
            r["tg"] = t_graph.final.get(r["path"])
        if d_graph is not None and r.get("deviated") is not None and not r.get("applied"):
            r["dg"] = d_graph.final.get(r["path"])
    return rows


def _decorate(a: dict, line: str, affected: set) -> dict:
    """Name a node the way the worksheet does, and say whether the carrier's filing reached it."""
    p = a.get("path") or ""
    if a["kind"] == "table":
        a["name"] = f"{a['table']}[{', '.join(a.get('keys') or [])}].{a['column']}"
    elif a["kind"] == "company":
        a["name"] = a.get("label") or "company source"
    else:
        a["name"] = _label(p) if p else a["kind"]
        a["item"] = _item(p) if p else ""
    a["affected"] = a["id"] in affected
    for c in a.get("from", []):
        _decorate(c, line, affected)
    return a


def why(token: str, side: str, gid: int, depth: int = 3) -> dict:
    """A value's ancestry (`depth` levels) and everything it ultimately came from, from a worksheet's graphs."""
    got = _GRAPHS.get(token)
    if got is None:
        return {"error": "this worksheet is no longer in memory: open it again"}
    g = got.get(side)
    if g is None or not (0 <= int(gid) < len(g.nodes)):
        return {"error": f"no {side} value with id {gid}"}
    aff = got["affected"] if side == "deviated" else set()
    tree_ = _decorate(g.ancestry(int(gid), max(0, min(int(depth), 8))), got["line"], aff)
    src = g.sources(int(gid))
    for x in src:
        _decorate(x, got["line"], aff)
    order = {"company": 0, "table": 1, "input": 2}
    src.sort(key=lambda x: (order.get(x["kind"], 3), x.get("name", "")))
    return {"side": side, "node": tree_, "sources": src}
