#!/usr/bin/env python3
"""The test console, RC-4 (docs/TC-PLAN.md TC-26..TC-32): planning and spending calls. No ISO calls: a stand-in answers.

  A  dimension catalog from ISO's own files, both lines (TC-26, D20)
  B  Tier 0 invariants at zero calls, and a check that they can fail (TC-28)
  C  plan counters: cartesian, pairwise, edges, reduced grid, allowance, dedupe, not expressible (TC-27)
  D  commit, information value, run controls (TC-29, D14)
  E  dispatcher: dedupe before every call, value order, the lane cap, override, evidence, pass 3 (TC-30, TC-32, D15)
  F  the screens, the report (D17), refusals (D16), run files (D17)

    python tests/verify_console_rc4.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="tc-rc4-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")          # a ledger of our own: the real one is never read or written
os.environ["TC_DISPATCH"] = "0"

from console import catalog as C, dispatcher as D, evidence, invariants as I, ledger, plans as P, runlog, store  # noqa: E402

P.PLANS, runlog.STORE, D.OVERRIDE = TMP / "plans", TMP / "runlog.jsonl", TMP / "override.json"
evidence.STORE = TMP / "evidence.jsonl"
store.ANSWERS = TMP / "answers"
store.build = lambda: None                                    # a finished plan would rebuild the index: not in a test
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. dimension catalog (TC-26)")
    gl = {d["id"]: d for d in C.dimensions("GL", "OH")}
    check("A1 GL: variants' controls with ISO's legal values", len(gl) >= 20 and len(gl["occurrence_limit"]["values"]) > 5)
    by_basis = {d["id"]: d for d in C.dimensions("GL", "OH", {"premium_basis": gl["premium_basis"]["values"][0]})}
    check("A2 GL basis-first (D20): the class codes narrow once a premium basis is chosen",
          0 < len(by_basis["class_code"]["values"]) < len(gl["class_code"]["values"]))
    check("A3 GL multi-class (D20) and the effective date as the state's package dates",
          "classifications" in gl and all(re.match(r"\d{8}$", v) for v in gl["effective_date"]["values"]))
    cp = {d["id"]: d for d in C.dimensions("CP", "OH")}
    check("A4 CP: construction, coinsurance, deductibles, territory... from the state's domain tables",
          len(cp["construction"]["values"]) >= 20 and "Akron" in cp["group1_territory"]["values"] and len(cp["bldg_deductible"]["values"]) > 5)
    check("A5 CP: blanket-only values are left out", not any("Blanket" in v for d in cp.values() for v in d["values"]))
    codes = C.cp_class_codes("OH", "Offices")
    check("A6 CP basis-first: a category's class codes, only those the state rates by class (no 0300 in OH)",
          codes and "0300" not in codes and "0951" in codes)
    check("A7 CP territory is per state", cp["group1_territory"]["perState"]
          and set(C.cp_values("group1_territory", "PA")).isdisjoint(cp["group1_territory"]["values"]))
    check("A8 CP effective dates are the state's own package dates", "2026-07-01" in C.cp_values("effective_date", "OH"))
    q = C.cp_build("OH", {"cause_of_loss": "Basic", "bldg_limit": "2000000", "protect_class": "8"})
    st = q["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]["CommercialPropertyStructure"][0]
    check("A9 cp_build applies a config to the state's sample (and moves the full value with the limit)",
          st["CauseOfLoss"] == "Basic" and st["Limit"] == st["FullBldgValue"] == 2000000
          and q["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]["ProtectClass"] == "8")


def part_b():
    print("B. Tier 0 (TC-28)")
    for line in ("GL", "CP"):
        r = I.run(line, ["OH"])
        check(f"B1 {line} OH: the five invariants hold at zero calls", r["checks"] == 5 and not r["failed"], r["failed"])
    saved = I._prem
    I._prem = lambda line, cfg, st: ((I.Decimal(1000) if cfg.get(I.LIMIT[line]) is None else
                                       I.Decimal(10 ** 7 / (1 + I._num(cfg[I.LIMIT[line]])))), None, set())
    try:
        r = I.check_state("GL", "OH", classes=1)
        check("B2 the limit check fails when a premium falls as the limit rises (its denominator works)",
              not next(c for c in r if c["check"] == "limits")["ok"])
    finally:
        I._prem = saved


def part_c():
    print("C. plan counters (TC-27)")
    dims = {"cause_of_loss": ["Basic", "Broad", "Special"], "bldg_coinsurance": ["80%", "90%", "100%"],
            "valuation": ["Actual Cash Value", "Replacement Cost"]}
    spec = {"line": "CP", "states": ["OH", "PA"], "dims": dims, "edges": True}
    sc = [s for s in P.scenarios(spec) if s["state"] == "OH" and s["kind"] == "pairwise"]
    pairs = {(a, s["config"][a], b, s["config"][b]) for s in sc for a, b in combinations(sorted(s["config"]), 2)}
    want = {(a, va, b, vb) for a, b in combinations(sorted(dims), 2) for va in dims[a] for vb in dims[b]}
    check("C1 pairwise: every pair of chosen values appears together", want <= pairs and len(sc) < 18)
    pv = P.preview(spec)
    check("C2 counters: cartesian, pairwise, edges", pv["cartesian"] == 18 * 2 and pv["pairwise"] == 2 * len(sc)
          and pv["edges"] > 0, pv)
    check("C3 already answered: stored answers are counted and not spent", pv["alreadyAnswered"] >= 1
          and pv["calls"] == pv["scenarios"] - pv["alreadyAnswered"])
    check("C4 days at the active lane (150/day)", pv["days"] == round(pv["calls"] / 150, 1))
    red = P.preview({**spec, "reduced": True})
    check("C5 reduced grid (D20): each dimension to its edges", red["cartesian"] == 8 * 2 and red["calls"] < pv["calls"])
    thin = P.preview({**spec, "states": ["OH", "PA", "NY", "TX"], "allowance": 5})
    check("C6 allowance (D20): at most N calls, and never a state dropped", thin["calls"] <= 5 and thin["statesKept"] == 4
          and thin["thinned"] > 0, thin)
    na = P.preview({"line": "GL", "states": ["OH"], "dims": {"occurrence_limit": ["1000000"]}, "edges": False})
    check("C7 a value not expressible in a state is counted, not spent", na["notApplicable"] == 1 and na["calls"] == 0, na)
    terr = [s for s in P.scenarios({"line": "CP", "states": ["OH", "PA"], "dims": {"group1_territory": ["x", "y"]}})
            if s["kind"] == "edge"]
    check("C8 a per-state dimension takes each state's own edges", {s["config"]["group1_territory"] for s in terr if s["state"] == "PA"}
          <= set(C.cp_values("group1_territory", "PA")))


def part_d():
    print("D. commit and controls (TC-29, D14)")
    spec = {"line": "CP", "states": ["OH"], "dims": {"cause_of_loss": ["Basic", "Special"], "bldg_coinsurance": ["80%", "100%"]},
            "edges": False}
    plan = P.commit(spec, by="test", name="rc4 test")
    sc = plan["scenarios"]
    check("D1 committed: every scenario rated free, with paths and a score", sc and all(s.get("ours") and s["paths"] and s["score"] for s in sc))
    check("D2 a stored answer is marked for reuse, not a call", any(s["status"] == "reuse" for s in sc)
          and all(s["status"] in ("reuse", "queued") for s in sc))
    check("D3 the queue is ordered by information value", [s["score"] for s in sc] == sorted((s["score"] for s in sc), reverse=True))
    check("D4 saved, queued", P.load(plan["id"])["status"] == "queued")
    P.control(plan["id"], "start")
    P.control(plan["id"], "pause")
    try:
        P.control(plan["id"], "pause")
        check("D5 an impossible control is refused", False)
    except ValueError:
        check("D5 an impossible control is refused", True)
    P.control(plan["id"], "resume")
    check("D6 start / pause / resume", P.load(plan["id"])["status"] == "running")
    p2 = P.commit(spec, name="to stop")
    P.control(p2["id"], "stop")
    s2 = P.summary(P.load(p2["id"]))
    check("D7 stop-and-keep: what was never reached is listed", s2["status"] == "stopped" and s2["notReached"] == len(p2["scenarios"]))
    return plan["id"]


class StandIn:
    """A RaaS stand-in: answers like ISO, through the store as the ledgered client would, spending nothing."""
    calls: list = []

    def __init__(self, override=None):
        self.override = override

    def rate(self, payload):
        from console import worksheet as W
        StandIn.calls.append((payload, self.override))
        _, _, tot = W.rate("CP", payload)
        store.save_answer(payload, {"Body": {"CommercialProperty": [{"ErcCalculatedTotalPremium": float(tot)}]}}, None)
        return {}


def part_e(pid):
    print("E. dispatcher (TC-30, TC-32, D15)")
    plan = P.load(pid)
    queued = [s for s in plan["scenarios"] if s["status"] == "queued"]
    first = D.tick(StandIn)
    check("E1 a stored answer is reused first, no call", first == [(pid, "dedupe")] and not StandIn.calls)
    D.tick(StandIn)
    check("E2 then calls go out, highest value first", len(StandIn.calls) == 1)
    payload = StandIn.calls[0][0]
    check("E3 ...the scenario sent first is the one with the top score", store.request_hash(payload) ==
          max(queued, key=lambda s: s["score"])["hash"])
    # Fill the active lane: the next step must stop at the cap, not call
    for _ in range(ledger.LANES["active"]):
        ledger.record(lane="active", origin="test", outcome="rated")
    n = len(StandIn.calls)
    check("E4 a full lane: capped, no call, logged once", D.tick(StandIn) == [(pid, "capped")] and len(StandIn.calls) == n
          and sum(1 for e in runlog.entries() if e["event"] == "capped") == 1)
    D.set_override("gate test", 1, by="test")
    D.tick(StandIn)
    check("E5 an override lets one call through, with its reason, and is logged (TC-32)",
          len(StandIn.calls) == n + 1 and StandIn.calls[-1][1] and "gate test" in StandIn.calls[-1][1]
          and any(e["event"] == "override" for e in runlog.entries()))
    check("E6 the override is used up", D.tick(StandIn) == [(pid, "capped")] and D.override() is None)
    with open(ledger._file(ledger.day()), "w", encoding="utf-8"):
        pass                                                  # a new day: the lane is empty again
    for _ in range(10):
        r = D.tick(StandIn)
        if r and r[0][1] == "done":
            break
    s = P.summary(P.load(pid))
    check("E7 the plan runs to done; every scenario has a result", s["status"] == "done" and s["queued"] == 0
          and s["match"] + s["mismatch"] + s["refused"] == s["scenarios"], s)
    ev = [r for r in evidence.records() if r.get("plan") == pid]
    check("E8 each answer is evidence (the matrix moves): paths, both premiums", len(ev) == s["scenarios"]
          and all(r["walked"] and r["ours"] and r["iso"] for r in ev))
    kinds = {e["event"] for e in runlog.entries(pid)}
    check("E9 the run log has the plan's life", {"start", "pause", "resume", "dedupe", "sent", "capped", "override", "done"} <= kinds, kinds)
    gl = P.commit({"line": "GL", "states": ["OH", "NJ"], "dims": {"occurrence_limit": ["1000000"]}, "edges": False}, name="na")
    P.control(gl["id"], "start")
    D.tick(StandIn)
    p3 = P.load(gl["id"]).get("pass3") or {}
    check("E10 pass 3 (D15) after a GL plan reviews what it found not expressible", p3.get("results")
          and all(r["verdict"] in ("CONFIRMED", "CONTRADICTED", "UNVERIFIED") for r in p3["results"]), p3.get("counts"))


def part_f(pid):
    print("F. the screens, the report, refusals, run files")
    from ui import console_page as CP
    html = CP.page()
    check("F1 the Test Plan Builder and the Queue & Run Log are built",
          all(i in html for i in ('id="pl-states"', 'id="pl-dims"', 'id="qu-plans"', 'id="qu-log"')) and "Built in TC-27" not in html
          and "Built in TC-31" not in html)
    node = shutil.which("node")
    if node:
        js = TMP / "page.js"
        js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
        res = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        check("F2 the page's script parses", res.returncode == 0, res.stderr[-300:])
    code, body, kind = CP.dispatch("GET", f"/console/report/{pid}", {}, None)
    check("F3 a plan's report (D17): read-only HTML, no script", code == 200 and kind == "html" and "<script" not in body
          and "rc4 test" in body)
    code, body, _ = CP.dispatch("GET", "/api/console/refused", {}, None)
    check("F4 the refused payloads (D16), each a Trace Diff away", code == 200 and json.loads(body)["total"] > 100)
    code, body, _ = CP.dispatch("GET", "/api/console/runs", {}, None)
    j = json.loads(body)
    check("F5 earlier run files stay browsable (D17)", code == 200 and j["total"] > 100)
    code, body, _ = CP.dispatch("GET", "/api/console/runs", {"id": next(r["id"] for r in j["runs"] if r["total"])}, None)
    check("F6 ...each with its rows", code == 200 and json.loads(body).get("rows"))
    code, body, _ = CP.dispatch("POST", "/api/console/override", {}, {"reason": "", "calls": 2})
    check("F7 an override without a reason is refused", code == 400)
    check("F8 no real call was made: the stand-in only, the real ledger untouched",
          all(e.get("origin") == "test" for e in ledger.entries()))


def main() -> int:
    try:
        part_a(); part_b(); part_c(); pid = part_d(); part_e(pid); part_f(pid)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
