#!/usr/bin/env python3
"""P3: prove carrier deviations against ISO's live service (DEVIATIONS-PLAN.md §5: T3; T8 retired with edition pins,
2026-10-16).

**ISO only ever rates TECHNICAL (D21, O6 decided 2026-10-09).** No request carrying a company's LCMs is sent:
the pattern is Technical (ours) / ISO (its answer to the same technical request) / Carrier (ours, proved against
technical by T4, T5 and T6, offline). The T5 split-check calls made earlier on 2026-10-09 are kept as historical
evidence in `docs/gates/GATE-DEVIATIONS.md`; `--with-t5-live` re-judges them from their stored answers.

    python scripts/deviations_p3.py --plan              # the cases and how many NEW calls they need (no calls)
    python scripts/deviations_p3.py --send              # send what is not already answered (lane: active)
    python scripts/deviations_p3.py --judge             # verdicts from the stored answers (no calls)
    python scripts/deviations_p3.py --promote           # add every answered request to the Regression Library

Every request goes through `scripts/raas.py`, so the ledger counts it and the answer store keeps ISO's reply by
request hash; a request already answered is never sent again. `--judge` reads those stored answers only, so the
verdicts can be recomputed at any time, for free (`tests/verify_deviations_proof.py` does).

The test companies live under `results/deviations/p3/carriers`, rebuilt from `tests/fixtures/deviations` on every
run: UFG's two companies (the P0 filing) and `P3CF` / `P3GL` (one constructed filing per T5 state). Nothing here
writes under CARRIERS_ROOT.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from deviations import proof as P                                   # noqa: E402
from deviations.engine import iso_request                          # noqa: E402

OUT = P.OUT
CARRIERS = OUT / "carriers"
FIX = ROOT / "tests" / "fixtures" / "deviations"

T5_CF_STATES = ("OR", "NY", "FL", "TX", "CA", "VA", "MO", "IL", "MA")
T5_GL_STATES = ("TX", "NY", "CA", "OH", "FL", "IL", "PA", "GA", "NC", "MI")
#: Historical only: the T5 split check sent carrier LCMs to ISO; D21 retired it (re-judged from stored answers).
WITH_T5_LIVE = False


# ---------------------------------------------------------------- the companies

def _approve_and_compile(path: Path) -> None:
    from deviations.compile import compile_filing
    from deviations.files import load_filing, log_action
    from deviations.validate import validate
    f = load_filing(path)
    log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
    log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
    rep = validate(f)
    if not rep.ok:
        raise SystemExit(f"{path.name}: {rep.errors[:3]}")
    compile_filing(rep)


def _company(code: str, extra: dict | None = None) -> Path:
    d = CARRIERS / "P3" / code
    d.mkdir(parents=True, exist_ok=True)
    (d / "company.json").write_text(json.dumps({"code": code, **(extra or {})}), encoding="utf-8")
    return d


def _filing(cdir: Path, name: str, line: str, juris: str, eff: str, rows: list) -> None:
    from deviations.files import write_json
    p = cdir / "authored" / f"{name}.v1.json"
    write_json(p, json.loads(json.dumps({"filing": name, "company": cdir.name, "line": line, "juris": [juris],
                                         "version": 1, "status": "approved", "new_eff": eff, "renewal_eff": eff,
                                         "rows": rows}), parse_float=Decimal))
    _approve_and_compile(p)


def _eff(req: dict) -> str:
    return req["body"]["SchemeKeys"]["EffectiveDateTime"][:10]


def _first_class(line: str, req: dict) -> str | None:
    found = []

    def visit(key, rec, chain):
        if not found and rec.get("ClassCode"):
            found.append(str(rec["ClassCode"]))
    block = "CommercialProperty" if line == "CF" else "GeneralLiability"
    P._walk(req["body"][block], block, [], visit)
    return found[0] if found else None


def build_carriers(t3: dict) -> None:
    if CARRIERS.exists():
        shutil.rmtree(CARRIERS)
    shutil.copytree(FIX / "UFG", CARRIERS / "UFG")
    for co in ("UFC", "ADD"):
        _approve_and_compile(CARRIERS / "UFG" / co / "authored" / "IA-CF-UNFG-134289779.v1.json")
    (CARRIERS / "P3").mkdir(parents=True, exist_ok=True)
    (CARRIERS / "P3" / "carrier.json").write_text(json.dumps({"carrier": "P3"}), encoding="utf-8")
    cf, gl = _company("P3CF"), _company("P3GL")
    for st in T5_CF_STATES:
        req = P.load(t3[("CF", st)]["request_file"])
        cls = _first_class("CF", req)
        rows = [{"target": "LCM:GroupI", "scope": {}, "value": "1.2", "mode": "replace"},
                {"target": "LCM:GroupII", "scope": {}, "value": "1.5", "mode": "replace"},
                {"target": "LCM:Broad", "scope": {}, "value": "1.5", "mode": "replace"},
                {"target": "LCM:Special", "scope": {}, "value": "1.5", "mode": "replace"},
                {"target": "LCM:Earthquake", "scope": {}, "value": "1.5", "mode": "replace"}]
        if cls:
            rows.append({"target": "LCM:GroupI", "scope": {"class": cls}, "value": "1.1", "mode": "multiply"})
        _filing(cf, f"{st}-CF-P3", "CF", st, _eff(req), rows)
    for st in T5_GL_STATES:
        req = P.load(t3[("GL", st)]["request_file"])
        cls = _first_class("GL", req)
        rows = [{"target": "LCM:PremOps", "scope": {}, "value": "1.15", "mode": "replace"},
                {"target": "LCM:ProdsCompldOps", "scope": {}, "value": "0.9", "mode": "replace"}]
        if cls:
            rows.append({"target": "LCM:PremOps", "scope": {"class": cls}, "value": "1.1", "mode": "multiply"})
        _filing(gl, f"{st}-GL-P3", "GL", st, _eff(req), rows)


# ---------------------------------------------------------------- the cases

def ia_bases() -> list:
    import property_rating as pr
    out = []
    s = pr.sample("IA", "2025-07-01")
    out.append(("sample-0951", s))
    b = copy.deepcopy(s)
    st = b["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]["CommercialPropertyStructure"][0]
    st["ClassCode"] = "0511"
    st["CommercialPropertyOccupClass"][0].update(ClassCode="0511", OccupCategory="Service")
    out.append(("sample-0511", b))
    for f in sorted((ROOT / "results" / "cf-raas").glob("chunk24_rc4_S-IA_request.json")):
        out.append(("stored-0951-1150", json.loads(f.read_text(encoding="utf-8"))))
    return out


_PICKS = OUT / "t3_picks.json"


def t3_picks() -> dict:
    """Per line and state, the stored request T3 uses: the newest one our engine rates with no company.
    Chosen once and kept (`t3_picks.json`) so a re-run judges the same requests ISO was sent."""
    if _PICKS.exists():
        return {tuple(k.split("|")): v for k, v in json.loads(_PICKS.read_text(encoding="utf-8")).items()}
    out = {}
    for line in ("CF", "GL"):
        for st, cands in sorted(P.stored_candidates(line).items()):
            pick = cands[0]
            for c in cands[:6]:
                r = P.rate(line, P.load(c["request_file"]))
                if (r.complete if line == "GL" else r.tree is not None):
                    pick = c
                    break
            out[(line, st)] = pick
    _PICKS.parent.mkdir(parents=True, exist_ok=True)
    _PICKS.write_text(json.dumps({"|".join(k): v for k, v in out.items()}, indent=1), encoding="utf-8")
    return out


def cases() -> list:
    t3 = t3_picks()
    out = []
    for (line, st), c in sorted(t3.items()):
        out.append({"id": f"T3-{line}-{st}", "test": "T3", "line": line, "state": st, "stored": c})
    if WITH_T5_LIVE:
        for co in ("UFC", "ADD"):
            for name, _ in ia_bases():
                out.append({"id": f"T5-CF-IA-{co}-{name}", "test": "T5", "line": "CF", "state": "IA",
                            "company": co, "base": name})
        for st in T5_CF_STATES:
            out.append({"id": f"T5-CF-{st}", "test": "T5", "line": "CF", "state": st, "company": "P3CF",
                        "stored": t3[("CF", st)]})
        for st in T5_GL_STATES:
            out.append({"id": f"T5-GL-{st}", "test": "T5", "line": "GL", "state": st, "company": "P3GL",
                        "stored": t3[("GL", st)]})
    return out, t3


def _base(case: dict) -> dict:
    if case.get("stored"):
        return P.load(case["stored"]["request_file"])
    if case.get("base"):
        return dict(ia_bases())[case["base"]]
    if case["line"] == "CF":
        import property_rating as pr
        return pr.sample(case["state"], "2025-07-01")
    from console import catalog
    return catalog.build("GL", case["state"], {})


def prepare(case: dict) -> dict:
    """Our side of a case (free) and the requests ISO must answer for it."""
    line = case["line"]
    base = _base(case)
    company = case.get("company") or "UFC"
    r = P.rate(line, P.with_company(base, company), root=CARRIERS, with_technical=True, waterfall=False)
    tech_req, warns = iso_request(P.with_company(base, company), line)
    reqs = [("technical", tech_req)]
    case = {**case, "company": company, "result": r, "base_request": base, "lcm_warnings": warns}
    if case["test"] == "T5":
        if line == "CF":
            from cf_engine.rating import rate as cf_rate        # noqa: F401  (book via the engine's plan)
            from deviations import engine as dv
            plan = dv.plan_for("CF", company, case["state"], _eff(base), "New", root=CARRIERS)
            book = dv.book_for(plan)
            for groups, req in P.cf_split_requests(plan, P.with_company(base, company), dv.iso_state_lcm(book, "CF")):
                reqs.append(("+".join(groups), req))
        else:
            from deviations import engine as dv
            plan = dv.plan_for("GL", company, case["state"], _eff(base), "New", root=CARRIERS)
            reqs.append(("carrier", P.gl_carrier_request(plan, P.with_company(base, company), dv.book_for(plan))))
    case["requests"] = reqs
    return case


# ---------------------------------------------------------------- answers

def answer(req: dict) -> tuple[str, dict | None]:
    """('rated', response) | ('refused', {'message'}) | ('missing', None), from the answer store."""
    from console import store
    e = store.lookup(req)
    if not e:
        return "missing", None
    if e["outcome"] == "rated":
        resp = [f for f in e["files"] if f.endswith("_response.json")]
        return "rated", P.load(resp[-1])
    ref = [f for f in e["files"] if f.endswith(("_refusal.json", "response.txt"))]
    return "refused", ({"message": P.load(ref[-1]).get("message", "")} if ref and ref[-1].endswith(".json")
                       else {"message": "refused"})


def send_all(prepared: list, override: str | None = None) -> dict:
    from raas import RaaS, RaaSError
    client = RaaS(lane="active", origin="deviations_p3", override=override)
    sent, failed = 0, []
    seen = set()
    from console import store
    for c in prepared:
        for label, req in c["requests"]:
            h = store.request_hash(req)
            if h in seen or answer(req)[0] != "missing":
                continue
            seen.add(h)
            try:
                client.rate(req)
            except RaaSError as exc:
                if "call not sent" in str(exc):
                    print(f"  STOP: {exc}")
                    return {"sent": sent, "failed": failed, "stopped": str(exc)}
                failed.append((c["id"], label, str(exc)[:160]))
            sent += 1
            print(f"  [{sent}] {c['id']} {label}")
    return {"sent": sent, "failed": failed}


# ---------------------------------------------------------------- verdicts

def _tree(line: str, r):
    return r.tree


def judge(case: dict) -> dict:
    line, r = case["line"], case["result"]
    tech = r.technical
    from console import store
    out = {"id": case["id"], "test": case["test"], "line": line, "state": case["state"],
           "hash": store.request_hash(case["requests"][0][1])}    # the technical request ISO answered: Trace Diff's
    ans = {label: answer(req) for label, req in case["requests"]}
    missing = [k for k, (s, _) in ans.items() if s == "missing"]
    if missing:
        return {**out, "verdict": "not run", "detail": f"no ISO answer yet for {missing}"}
    refused = {k: v for k, (s, v) in ans.items() if s == "refused"}
    if case["test"] == "T3":
        if refused:
            return {**out, "verdict": "fail", "detail": f"ISO refused the technical request: {refused}"}
        a = ans["technical"][1]
        stored = P.load(case["stored"]["response_file"])
        base_r = P.rate(line, case["base_request"])
        base_tree = base_r.tree
        ours_vs_stored = P.compare(line, base_tree, stored) if base_tree is not None else None
        tech_vs_a = P.compare(line, tech.tree, a) if tech is not None and tech.tree is not None else None
        iso_moved = P.iso_leaves_equal(a, stored)
        lcm_changed = bool(case["lcm_warnings"])
        new = sorted(set(tech_vs_a["differ"]) - set(ours_vs_stored["differ"])) if tech_vs_a and ours_vs_stored else ["(no tree)"]
        ok = not new and (lcm_changed or not iso_moved)
        return {**out, "verdict": "pass" if ok else "fail",
                "numbers": tech_vs_a["numbers"] if tech_vs_a else 0,
                "preexisting": len(ours_vs_stored["differ"]) if ours_vs_stored else None,
                "newDisagreements": new[:20], "isoAnswersDiffer": iso_moved[:20],
                "submittedLcmNot1": lcm_changed,
                "premium": {"ours_technical": P.premium_of(line, tech) if tech else None,
                            "iso": _iso_total(line, a)},
                "detail": "" if ok else (f"new: {new[:3]}" if new else f"ISO's two answers differ: {iso_moved[:3]}")}
    if case["test"] == "T5":
        if refused and all("LossCostMultiplierStatCode" in str(v) for v in refused.values())                 and all(_lcm_below_1(dict(case["requests"])[k]) for k in refused):
            return {**out, "verdict": "known", "detail": "ISO refuses every Property LCM below 1.00 at its LCM "
                    "stat-code lookup (it keys on '88.00' where the table files '88'); ours rates. Open item O6 "
                    f"in DEVIATIONS-PLAN.md. Refused: {sorted(refused)}"}
        if refused:
            return {**out, "verdict": "fail", "detail": f"ISO refused: {refused}"}
        baseline = set(P.compare(line, tech.tree, ans["technical"][1])["differ"])
        if line == "GL":
            c = P.compare(line, r.tree, ans["carrier"][1])
            new = sorted(set(c["differ"]) - baseline)
            return {**out, "verdict": "pass" if not new else "fail", "checked": c["numbers"],
                    "wrong": new[:20], "preexisting": len(baseline),
                    "premium": {"ours_carrier": P.premium_of(line, r), "ours_technical": P.premium_of(line, tech),
                                "iso_carrier_request": _iso_total(line, ans["carrier"][1])},
                    "detail": "" if not new else f"{new[:3]}"}
        answers = [(label.split("+"), resp) for label, (s, resp) in ans.items() if label != "technical"]
        j = P.judge_split(r.tree, answers, baseline)
        ok = not j["wrong"] and j["checked"] > 0
        return {**out, "verdict": "pass" if ok else "fail", **j, "preexisting": len(baseline),
                "premium": {"ours_carrier": r.premium, "ours_technical": tech.premium},
                "detail": "" if ok else f"{j['wrong'][:3]}"}
    return {**out, "verdict": "error", "detail": f"no judge for test {case['test']}"}


def _lcm_below_1(req: dict) -> bool:
    found = []

    def visit(key, rec, chain):
        v = rec.get("LossCostMultiplier")
        if v not in (None, "") and Decimal(str(v)) < 1:
            found.append(v)
    P._walk(req["body"], "body", [], visit)
    return bool(found)


def _iso_total(line: str, resp: dict | None):
    if not resp:
        return None
    body = resp.get("Body", resp)
    if line == "CF":
        cp = body.get("CommercialProperty")
        cp = cp[0] if isinstance(cp, list) and cp else cp or {}
        return cp.get("ErcCalculatedTotalPremium")
    gl = body.get("GeneralLiability")
    gl = gl[0] if isinstance(gl, list) and gl else gl or {}
    return gl.get("Premium")


def promote(prepared: list) -> int:
    from console import library, store
    n = 0
    for c in prepared:
        for label, req in c["requests"]:
            if answer(req)[0] != "rated" or c["test"] == "T5":     # carrier requests never join (D21)
                continue
            e = library.promote(scenario=f"dev-{c['id']}-{label}", line=P.LINE_NAME[c["line"]], state=c["state"],
                                origin="deviations-p3", request_hash=store.request_hash(req), by="deviations_p3",
                                note=f"DEVIATIONS-PLAN P3 {c['test']}: the {label} request ISO was sent")
            n += 0 if e.get("already") else 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--send", action="store_true")
    g.add_argument("--judge", action="store_true")
    g.add_argument("--promote", action="store_true")
    ap.add_argument("--only", help="case ids containing this")
    ap.add_argument("--override", help="a reason, to send past a full lane")
    ap.add_argument("--with-t5-live", action="store_true",
                    help="re-judge the retired T5 split-check calls from their stored answers (never sends)")
    a = ap.parse_args()
    global WITH_T5_LIVE
    WITH_T5_LIVE = a.with_t5_live
    if a.with_t5_live and a.send:
        raise SystemExit("T5's carrier requests are not sent any more (D21): --with-t5-live only re-judges")
    cs, t3 = cases()
    if a.only:
        cs = [c for c in cs if a.only in c["id"]]
    build_carriers(t3)
    prepared = []
    for c in cs:
        try:
            prepared.append(prepare(c))
        except Exception as exc:                                   # noqa: BLE001
            prepared.append({**c, "requests": [], "error": f"{type(exc).__name__}: {exc}"[:300]})
    if a.plan:
        from console import store
        need, seen = {}, set()
        for c in prepared:
            for _, req in c["requests"]:
                h = store.request_hash(req)
                if h not in seen and answer(req)[0] == "missing":
                    seen.add(h)
                    need[c["test"]] = need.get(c["test"], 0) + 1
        errs = [c for c in prepared if c.get("error")]
        print(f"{len(prepared)} cases; new ISO calls needed: {need} = {sum(need.values())}")
        for c in errs:
            print(f"  ERROR preparing {c['id']}: {c['error']}")
        return 1 if errs else 0
    if a.send:
        res = send_all(prepared, a.override)
        print(json.dumps(res, indent=1))
        return 0 if not res.get("stopped") else 2
    if a.promote:
        print(f"promoted {promote(prepared)} requests to the Regression Library")
        return 0
    verdicts = []
    for c in prepared:
        if c.get("error"):
            verdicts.append({"id": c["id"], "test": c["test"], "verdict": "error", "detail": c["error"]})
            continue
        try:
            verdicts.append(judge(c))
        except Exception as exc:                                   # noqa: BLE001
            verdicts.append({"id": c["id"], "test": c["test"], "verdict": "error",
                             "detail": f"{type(exc).__name__}: {exc}"[:300]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verdicts.json").write_text(json.dumps(verdicts, indent=1, default=str), encoding="utf-8")
    from collections import Counter
    by = Counter((v["test"], v["verdict"]) for v in verdicts)
    for k in sorted(by):
        print(f"  {k[0]} {k[1]:8s} {by[k]}")
    for v in verdicts:
        if v["verdict"] not in ("pass",):
            print(f"  {v['verdict'].upper():8s} {v['id']}: {str(v.get('detail', ''))[:200]}")
    return 0 if all(v["verdict"] in ("pass", "known") for v in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
