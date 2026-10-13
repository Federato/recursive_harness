#!/usr/bin/env python3
"""The test console, RC-5 (docs/TC-PLAN.md TC-33..TC-35): the Regression Library. No ISO calls.

  A  the library: ISO's fixtures, the golden cases, the samples (TC-33, D22)
  B  the gate: a re-run of the whole library at zero calls, today's results (293 of 293 fixtures) (TC-34)
  C  a divergence is caught, and remembered: first / last seen (D18)
  D  the gate: a corpus change marks exactly the affected answers stale (TC-07, TC-35)
  E  a stale refresh goes out in the refresh lane, and a stale answer is never taken as answered (TC-35)
  F  the screen

    python tests/verify_console_rc5.py
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="tc-rc5-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"

from console import dispatcher as D, evidence, ledger, library, plans as P, readiness, regression as R, runlog, store  # noqa: E402

R.RUNS, R.PROGRESS = TMP / "runs", TMP / "runs" / "current.json"
readiness.LAST_BUILD = TMP / "last_build.json"
P.PLANS, runlog.STORE, D.OVERRIDE, evidence.STORE = TMP / "plans", TMP / "runlog.jsonl", TMP / "ov.json", TMP / "ev.jsonl"
store.build = lambda: None
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. the library (TC-33)")
    E = library.entries()
    by = {}
    for e in E:
        by[e["origin"]] = by.get(e["origin"], 0) + 1
    check("A1 ISO's 293 STC fixtures, each with its own response", by.get("fixture") == 293
          and all(e["reference"] == "iso" and e["response_file"] for e in E if e["origin"] == "fixture"))
    check("A2 the chunk golden cases with an ISO answer", by.get("golden", 0) >= 5)
    s = [e for e in E if e["origin"] == "sample"]
    check("A3 the samples, both lines (D22's all-samples check)", {e["line"] for e in s} == {"CP", "GL"} and len(s) >= 90)
    check("A4 a sample ISO has answered is referenced to ISO; one it has not, to our premium, labelled ours",
          any(e["reference"] == "iso" for e in s) and all(e["reference"] == "iso" or e.get("ours") for e in s))
    return E


def part_b(E):
    print("B. gate: re-run at zero calls (TC-34)")
    calls = ledger.used()["total"]
    r = R.run(E, workers=7, progress=False)
    fx = [x for x in r["results"] if x["scenario"].startswith("FX-")]
    check("B1 every ISO fixture passes on every premium: 293 of 293, as 157_ --all", len(fx) == 293
          and all(x["result"] in ("pass", "fields") for x in fx), r["counts"])
    check("B2 the whole library passes", all(x["result"] in ("pass", "fields") for x in r["results"]), r["counts"])
    check("B3 zero calls", r["callsSpent"] == 0 and ledger.used()["total"] == calls)
    check("B4 the run is kept with its build, and the readiness build marker is written",
          (R.RUNS / f"{r['run']}.json").exists() and r["build"] != "unknown"
          and json.loads(readiness.LAST_BUILD.read_text())["run"] == r["run"])
    return r


def part_c(E):
    print("C. a divergence is caught and remembered (D18)")
    fx = next(e for e in E if e["origin"] == "fixture")
    resp = json.loads((ROOT / fx["response_file"]).read_text(encoding="utf-8"))
    bad = copy.deepcopy(resp)
    cp = bad["Body"]["CommercialProperty"]
    (cp[0] if isinstance(cp, list) else cp)["ErcCalculatedTotalPremium"] = 1
    f = TMP / "tampered_response.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    t = {**fx, "scenario": "FX-tampered", "response_file": str(f)}
    x = R.check(t)
    check("C1 an ISO answer that differs on a premium: diverged, at that field",
          x["result"] == "diverged" and x["first"] == "/CommercialProperty/ErcCalculatedTotalPremium", x)
    ours = next(e for e in E if e["reference"] == "ours")
    x = R.check({**ours, "ours": "1"})
    check("C2 an our-reference entry whose premium moved: diverged, saying so", x["result"] == "diverged" and "moved" in x["detail"])
    R.run([t], workers=1, progress=False)
    R.run([fx | {"scenario": "FX-tampered"}], workers=1, progress=False)
    h = R.history()["FX-tampered"]
    check("C3 first and last seen kept; fixed now, so not open", h["firstSeen"] and h["lastSeen"] and not h["open"]
          and h["last"]["result"] == "pass")


def part_d():
    print("D. gate: a corpus change marks exactly the affected answers stale (TC-07)")
    idx = json.loads(store.INDEX.read_text(encoding="utf-8"))
    base = {e["hash"]: e["freshness"] for e in R.restale(copy.deepcopy(idx))["references"]}
    real = store.current_package
    store.current_package = lambda line, state, date: (real(line, state, date) + "-NEW"
                                                       if (line, state) == ("CP", "OH") else real(line, state, date))
    try:
        moved = {e["hash"]: e for e in R.restale(copy.deepcopy(idx))["references"]}
    finally:
        store.current_package = real
    changed = {h for h, e in moved.items() if e["freshness"] != base[h]}
    want = {h for h, e in moved.items() if e["line"] == "CP" and e["state"] == "OH" and e.get("iso_package")
            and base[h] == "fresh"}
    check("D1 a new OH Property package: every OH answer ISO gave on the old one goes stale, and nothing else",
          changed and changed == want, (len(changed), len(want)))
    return idx


class StandIn:
    calls = []

    def __init__(self, override=None):
        pass

    def rate(self, payload):
        from console import worksheet as W
        StandIn.calls.append(payload)
        _, _, tot = W.rate("CP", payload)
        store.save_answer(payload, {"Body": {"CommercialProperty": [{"ErcCalculatedTotalPremium": float(tot)}]}}, None)
        return {}


def part_e(idx):
    print("E. a stale refresh in the refresh lane (TC-35)")
    store.ANSWERS = TMP / "answers"
    from console import catalog as C
    sample_hash = store.request_hash(C.cp_build("OH", {}))       # the OH sample: ISO answered it (RC-1's ledger call)
    target = next(e for e in idx["references"] if e["hash"] == sample_hash and e["outcome"] == "rated")
    t = copy.deepcopy(idx)
    for e in t["references"]:
        if e["hash"] == target["hash"]:
            e["freshness"], e["stale_reason"] = "stale", "answered on the old package (test)"
    store.INDEX = TMP / "index.json"
    store.INDEX.write_text(json.dumps(t), encoding="utf-8")
    st = R.stale()
    check("E1 the stale answers are listed, with what can be re-sent", any(a["hash"] == target["hash"] for a in st["answers"])
          and st["sendable"] >= 1)
    plan = R.refresh_plan(by="test")
    check("E2 a refresh plan in the refresh lane, queued (nothing spent until started)", plan["lane"] == "refresh"
          and plan["status"] == "queued" and any(s["hash"] == target["hash"] for s in plan["scenarios"]))
    row = P.expand({"line": "CP", "states": ["OH"], "dims": {}})["rows"][0]
    check("E3 a stale stored answer is not counted as answered by a plan", row["hash"] == target["hash"] and not row["stored"])
    for _ in range(ledger.LANES["refresh"]):
        ledger.record(lane="refresh", origin="test", outcome="rated")
    P.control(plan["id"], "start")
    check("E4 a full refresh lane holds the refresh (the active lane's room is not borrowed)",
          D.tick(StandIn) == [(plan["id"], "capped")] and not StandIn.calls)
    open(ledger._file(ledger.day()), "w").close()
    D.tick(StandIn)
    check("E5 the stale answer is re-sent, not taken as answered", len(StandIn.calls) == 1
          and store.request_hash(StandIn.calls[0]) == target["hash"])
    e = store.lookup(C.cp_build("OH", {}))
    check("E6 the new answer is the one found now: fresh, newer than the stale one, from the ledger's answers",
          e and e["freshness"] == "fresh" and e["stored_at"] > target["stored_at"]
          and any(str(TMP) in f for f in e["files"]), e and (e["freshness"], e["stored_at"], target["stored_at"]))


def part_e2(idx):
    ny = next((e for e in idx["references"] if e["line"] == "GL" and e["state"] == "NY" and e.get("freshness") == "stale"), None)
    if ny is None:
        print("  skip E7: no stale NY GL answer today")
        return
    check("E7 an answer ISO gave on a package newer than our corpus (NY GL V02) is a corpus refresh, never re-sent",
          R.remedy(ny) == "corpus" and not R._sendable(ny))


def part_f():
    print("F. the screen")
    from ui import console_page as CP
    html = CP.page()
    check("F1 the Regression Library screen is built", 'id="lb-table"' in html and "Built in TC-33" not in html)
    node = shutil.which("node")
    if node:
        js = TMP / "page.js"
        js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
        res = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        check("F2 the page's script parses", res.returncode == 0, res.stderr[-300:])
    code, body, _ = CP.dispatch("GET", "/api/console/library", {}, None)
    v = json.loads(body)
    check("F3 the view: every entry with its content version, verified date, last result and defect history",
          code == 200 and len(v["entries"]) == len(library.entries()) and v["lastRun"]
          and all(k in v["entries"][0] for k in ("contentVersion", "verified", "last", "firstSeen", "open")))


def main() -> int:
    try:
        E = part_a(); part_b(E); part_c(E); idx = part_d(); part_e2(copy.deepcopy(idx)); part_e(idx); part_f()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
