"""P3's proof against ISO's live service: the cases, the requests ISO is sent, and how its answers are judged.

Three tests spend ISO calls (DEVIATIONS-PLAN.md §5); everything else is our engine against itself.

  * **T3 technical still equals ISO.** One stored request per state per line, sent as a writing company's
    TECHNICAL request (our header fields and submitted LCMs removed). ISO must rate it, its answer must match
    its stored answer to the original request field for field, and our technical must agree with it exactly as
    well as our ISO-only rating agreed with the original (no new disagreement).
  * **T5 LCMs against ISO.** The carrier's LCMs written onto the request ISO is sent. GL carries one LCM per
    coverage record, so one call checks the whole carrier tree. Property carries one per record while a filing
    may set one per coverage group (D17), so Property uses the **split check**: one call per distinct set of
    record LCMs -- the Group I set, the Group II set, ... -- and each of our carrier fields is judged against the
    call made with its own group's LCMs. A field that belongs to no group is judged in the Group I call (the
    record's LCM is the Group I value, G2); a roll-up that mixes groups can match no single call and is listed
    as a roll-up rather than hidden.
  * **T8 pins.** ISO takes no edition pin: its effective date chooses the edition (O2). So a pinned rating is
    compared with ISO's answer to the technical request dated inside the pinned edition.

Calls go through `scripts/raas.py` (the ledger, the answer store) in the `active` lane. A request whose exact
hash already has an answer is not sent again, so a re-run spends only what is new.
"""
from __future__ import annotations

import copy
import json
import re
from decimal import Decimal
from pathlib import Path

from .engine import group_of, iso_request

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "deviations" / "p3"
LINE_NAME = {"CF": "CP", "GL": "GL"}          # the console's names for the lines


# ------------------------------------------------------------------ stored requests

def stored_cases(line: str) -> list:
    """One stored, ISO-rated request per state (the newest fresh one), for T3."""
    import sys
    sys.path.insert(0, str(ROOT))
    from console import store
    best: dict = {}
    for e in store.load()["references"]:
        if e["line"] != LINE_NAME[line] or e["outcome"] != "rated":
            continue
        req = [f for f in e.get("files", []) if f.endswith("request.json")]
        resp = [f for f in e.get("files", []) if f.endswith("_response.json")]
        if not (req and resp):
            continue
        rank = (e.get("freshness") != "stale", e.get("date", ""), e["hash"])
        if e["state"] not in best or rank > best[e["state"]][0]:
            best[e["state"]] = (rank, e, req[-1], resp[-1])
    out = []
    for st in sorted(best):
        _, e, rq, rs = best[st]
        out.append({"line": line, "state": st, "hash": e["hash"], "request_file": rq, "response_file": rs,
                    "iso_package": e.get("iso_package", "")})
    return out


def stored_candidates(line: str) -> dict:
    """state -> every stored, ISO-rated request (newest fresh first), for picking one our engine rates."""
    import sys
    sys.path.insert(0, str(ROOT))
    from console import store
    by: dict = {}
    for e in store.load()["references"]:
        if e["line"] != LINE_NAME[line] or e["outcome"] != "rated":
            continue
        req = [f for f in e.get("files", []) if f.endswith("request.json")]
        resp = [f for f in e.get("files", []) if f.endswith("_response.json")]
        if req and resp:
            by.setdefault(e["state"], []).append(((e.get("freshness") != "stale", e.get("date", ""), e["hash"]),
                                                  {"line": line, "state": e["state"], "hash": e["hash"],
                                                   "request_file": req[-1], "response_file": resp[-1],
                                                   "iso_package": e.get("iso_package", "")}))
    return {st: [c for _, c in sorted(xs, key=lambda x: x[0], reverse=True)] for st, xs in by.items()}


def load(rel: str) -> dict:
    p = Path(rel)
    return json.loads((p if p.is_absolute() else ROOT / p).read_text(encoding="utf-8"))


def with_company(request: dict, company: str, policy_type: str = "New") -> dict:
    out = copy.deepcopy(request)
    out.setdefault("header", {})
    out["header"]["WritingCompany"] = company
    out["header"]["PolicyType"] = policy_type
    return out


# ------------------------------------------------------------------ rating

def rate(line: str, request: dict, root: Path | None = None, **kw):
    """Our rating of a request (company or not). Returns the engine's own result object."""
    if line == "CF":
        from cf_engine.rating import rate as cf_rate
        return cf_rate(request, root=root, **kw)
    from gl_engine.rating import Kernel
    return _kernel().rate(request, root=root, **kw)


_K = None


def _kernel():
    global _K
    if _K is None:
        from gl_engine.rating import Kernel
        _K = Kernel()
    return _K


def premium_of(line: str, r) -> str | None:
    if line == "CF":
        return r.premium
    return str(r.premium) if r.complete else None


# ------------------------------------------------------------------ comparing with ISO

def compare(line: str, tree, response: dict) -> dict:
    """Our tree against ISO's response, the Regression Library's way (`console.worksheet.align`)."""
    from console import worksheet as W
    ln = LINE_NAME[line]
    rows = W.align(ln, tree, [], W.body_of(ln, response))
    num = [r for r in rows if r["kind"] == "number" and r["in_iso"] and r["in_ours"]]
    prem = ("Premium", "ErcCalculatedTotalPremium")
    return {"numbers": len(num),
            "differ": sorted(r["path"] for r in num if not r["match"]),
            "premiumsDiffer": sorted(r["path"] for r in num if not r["match"] and r["field"] in prem),
            "rows": {r["path"]: (r["ours"], r["iso"]) for r in num}}


def iso_leaves_equal(a: dict, b: dict) -> list:
    """Paths where two ISO answers differ (numbers by value, identifiers and timestamps aside)."""
    from console import worksheet as W
    la, lb = W.iso_leaves(a.get("Body", a)), W.iso_leaves(b.get("Body", b))
    skip = re.compile(r"(Guid|Id|Timestamp|Time|Date)$")
    return sorted(p for p in set(la) | set(lb)
                  if not skip.search(p.rsplit("/", 1)[-1]) and not W.same(la.get(p), lb.get(p)))


# ------------------------------------------------------------------ writing LCMs onto ISO's request

_CF_RECORDS = ("CommercialPropertyStructure", "CommercialPropertyOccupClass",
               "CommercialPropertyPersonalProperty", "CommercialPropertyBusinessIncome",
               "CommercialPropertySpecialClass", "CommercialPropertySpecialClassBusnIncome")
_GL_RECORDS = {"GeneralLiabilityClassificationPremOpsCoverage": "PremOps",
               "GeneralLiabilityClassificationProdsCompldOpsCoverage": "ProdsCompldOps"}


def _walk(obj, key, chain, visit):
    if isinstance(obj, dict):
        visit(key, obj, chain)
        for k, v in obj.items():
            _walk(v, k, chain + [obj], visit)
    elif isinstance(obj, list):
        for x in obj:
            _walk(x, key, chain, visit)


def _up(rec: dict, chain: list, field: str):
    for d in [rec] + list(reversed(chain)):
        v = d.get(field)
        if v not in (None, ""):
            return str(v)
    return None


def _final(entry, iso_lcm: Decimal) -> Decimal:
    v, mode, _ = entry
    return v if mode == "replace" else iso_lcm * v


def cf_vectors(plan, request: dict, iso_lcm: Decimal) -> dict:
    """{group: {record position: LCM}} -- for each coverage group, the LCM each classed record carries."""
    from .config import LCM_TARGETS
    out = {}
    for g in LCM_TARGETS["CF"]:
        vec = {}

        def visit(key, rec, chain, g=g, vec=vec):
            if key not in _CF_RECORDS:
                return
            cls = _up(rec, chain, "ClassCode")
            if cls is None:
                return
            rt = (_up(rec, chain, "RatingTypeBasicGroupII") if g == "GroupII" else None) or _up(rec, chain, "RatingType")
            basis = "Specific" if rt == "Specific" else "Class"
            e = plan.group_lcm.get((g, basis, cls))
            if e is not None:
                vec[id(rec)] = _final(e, iso_lcm)
        _walk(request["body"]["CommercialProperty"], "CommercialProperty", [], visit)
        out[g] = vec
    return out


def cf_split_requests(plan, request: dict, iso_lcm: Decimal) -> list:
    """[(groups, request)] -- one ISO request per distinct set of record LCMs (the split check)."""
    base, _ = iso_request(request, "CF")
    seen: dict = {}
    for g, vec in cf_vectors(plan, base, iso_lcm).items():
        key = tuple(sorted((k, str(v)) for k, v in vec.items()))
        seen.setdefault(key, []).append(g)
    out = []
    for key, groups in seen.items():
        req = copy.deepcopy(base)
        vec = cf_vectors(plan, req, iso_lcm)[groups[0]]

        def visit(k, rec, chain, vec=vec):
            if id(rec) in vec:
                rec["LossCostMultiplier"] = float(vec[id(rec)])
        _walk(req["body"]["CommercialProperty"], "CommercialProperty", [], visit)
        out.append((groups, req))
    return out


def gl_carrier_request(plan, request: dict, book) -> dict:
    """ISO's request with the carrier's LCM on every GL coverage record (one call checks the whole tree)."""
    from .engine import GL_LCM_RECORDS, _state_value
    req, _ = iso_request(request, "GL")
    iso_lcm = {cov: _state_value(book, t, "Rate") for cov, t in GL_LCM_RECORDS.values()}

    def visit(key, rec, chain):
        cov = _GL_RECORDS.get(key)
        if cov is None:
            return
        cls = _up(rec, chain, "ClassCode")
        e = plan.lcm.get((cov, cls)) if cls else None
        if e is not None:
            rec["LCM"] = float(_final(e, iso_lcm[cov]))
    _walk(req["body"]["GeneralLiability"], "GeneralLiability", [], visit)
    return req


# ------------------------------------------------------------------ judging the split check

_ROLLUP = re.compile(r"Premium|Total|Sum")


def leaf_group(path: str) -> str | None:
    parts = [p.split("[")[0] for p in path.strip("/").split("/")]
    for name in reversed(parts):
        g = group_of([name])
        if g:
            return g
    return None


def judge_split(ours_tree, answers: list, baseline: set) -> dict:
    """`answers`: [(groups, ISO response)]. Every field ISO publishes is judged in its own group's call."""
    by_group = {}
    rows_by_call = []
    for groups, resp in answers:
        c = compare("CF", ours_tree, resp)
        rows_by_call.append((groups, c))
        for g in groups:
            by_group[g] = c
    checked, wrong, rollups, unjudged = 0, [], [], []
    paths = set()
    for _, c in rows_by_call:
        paths |= set(c["rows"])
    for p in sorted(paths):
        if p in baseline:
            continue                     # ours already differs from ISO here with no company at all
        g = leaf_group(p) or "GroupI"
        c = by_group.get(g)
        if c is None or p not in c["rows"]:
            unjudged.append(p)
            continue
        checked += 1
        if p in c["differ"]:
            if leaf_group(p) is None and _ROLLUP.search(p.rsplit("/", 1)[-1]):
                rollups.append(p)        # mixes groups: no single call can price it
            else:
                wrong.append(p)
    return {"checked": checked, "wrong": wrong, "rollups": rollups, "unjudged": len(unjudged),
            "calls": [g for g, _ in rows_by_call]}
