#!/usr/bin/env python3
"""The test console, RC-6 (docs/TC-PLAN.md TC-36, TC-37): the parity check and the switch-over. No ISO calls.

  A  the gaps TC-36 found, closed: run files served, tiers and layers as presets, INERT flagged, what changed since
     the last run, an old run's rows, one config across every state as a plan
  B  the switch-over (TC-37): the console mounted on its own, the old pages gone, `/` pointing at the console

    python tests/verify_console_rc6.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="tc-rc6-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"

from console import catalog as C, dispatcher as D, evidence, plans as P, presets, regression as R, runlog, store  # noqa: E402
from ui import console_page as CP  # noqa: E402

P.PLANS, runlog.STORE, evidence.STORE, D.OVERRIDE = TMP / "plans", TMP / "runlog.jsonl", TMP / "ev.jsonl", TMP / "ov.json"
store.build = lambda: None
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. TC-36: the gaps the parity check found, closed")
    code, body, kind = CP.dispatch("GET", "/runs/index.html", {}, None)
    check("A1 R7 / L8: the standalone run files are served by the console (the index and a file)",
          code == 200 and kind == "html" and "L1-base-" in body)
    name = sorted(p.name for p in (store.RES / "runs").glob("L1-base-*.html"))[0]
    check("A2 ...a run file itself", CP.dispatch("GET", f"/runs/{name}", {}, None)[0] == 200)
    check("A3 ...and nothing outside that folder", CP.dispatch("GET", "/runs/..%5Capp.py", {}, None)[0] == 404
          and CP.dispatch("GET", "/runs/nope.html", {}, None)[0] == 404)
    ps = {p["id"]: p for p in presets.presets()}
    import qa
    import layers
    check("A4 T1: the QA tiers are presets, read from qa.py (T1 = its core states, its configs)",
          {"qa-T0", "qa-T1", "qa-T2", "qa-T4"} <= set(ps) and ps["qa-T1"]["spec"]["states"] == sorted(qa.CORE)
          and len(ps["qa-T1"]["spec"]["configs"]) == len(qa.scenarios_for("T1")))
    check("A5 L1: the layers are presets, read from layers.py", {"layer-L1", "layer-L3", "layer-L4"} <= set(ps)
          and ps["layer-L4"]["spec"]["configs"] == layers._configs("L4"))
    pv = P.preview({**ps["layer-L3"]["spec"], "states": ["OH"]})
    check("A6 ...L3's positions (@lowest...) resolve per state, as /tests did", pv["presets"] == 12 and pv["notApplicable"] == 0, pv)
    plan = P.commit({"line": "GL", "states": ["OH"], "dims": {}, "configs": [{"terrorism": "No"}, {"occurrence_limit": "100,000 CSL"}],
                     "edges": False}, name="inert test")
    inert = {json.dumps(s["config"]): s.get("inert", False) for s in plan["scenarios"]}
    check("A7 T5: a scenario that rates as the base risk through the same paths is flagged INERT (D15); one that moves is not",
          inert.get('{"terrorism": "No"}') is True and inert.get('{"occurrence_limit": "100,000 CSL"}') is False, inert)
    R.RUNS = TMP / "runs"
    R.RUNS.mkdir()
    for i, (res, ours) in enumerate((("pass", "100"), ("diverged", "105"))):
        (R.RUNS / f"2026010{i}-000000.json").write_text(json.dumps({"run": f"r{i}", "build": "b", "at": "t", "counts": {},
                                                                    "results": [{"scenario": "s", "result": res, "ours": ours},
                                                                                {"scenario": "t", "result": "diverged" if i == 0 else "pass", "ours": "1"}]}))
    c = R.changes()
    check("A8 T8 / L6: what changed since the last run: newly failing, fixed, our premium moved",
          c["new"] == ["s"] and c["fixed"] == ["t"] and c["premiumMoved"] == [{"scenario": "s", "was": "100", "now": "105"}], c)
    code, body, _ = CP.dispatch("GET", "/api/console/runs", {}, None)
    rid = json.loads(body)["runs"][0]["id"]
    code, body, _ = CP.dispatch("GET", "/api/console/runs", {"id": rid}, None)
    check("A9 V1 / L8: an old run's rows open from the console", code == 200 and json.loads(body)["rows"])
    p = P.preview({"line": "GL", "states": ["OH", "NJ"], "dims": {}, "configs": [{"occurrence_limit": "500,000 CSL"}], "edges": False})
    check("A10 T16: one config across every state is a plan (D19)", p["scenarios"] == 2 and p["presets"] == 2 and p["pairwise"] == 0)
    html = CP.page()
    check("A11 the screens offer them: Start from, Build a plan from this, the run files link, changes",
          all(s in html for s in ('id="pl-preset"', "wb-toplan", "/runs/index.html", "function lbChanges")))


def part_b():
    print("B. TC-37: the switch-over")
    gone = [f for f in ("ui/tester.py", "ui/tests_page.py", "ui/review_page.py", "ui/runfile.py", "scripts/reviews.py")
            if (ROOT / f).exists()]
    if gone:
        print(f"  skip B: TC-37 not done yet ({len(gone)} old module(s) still here)")
        return
    import importlib
    app = importlib.import_module("app")
    check("B1 the old modules are gone", not gone)
    for path in ("/tester", "/tests", "/review/x.html", "/api/tester/spec", "/api/tests/spec"):
        out = CP.dispatch("GET", path, {}, None)
        check(f"B2 {path} is not served", out is None or out[0] == 404)
    check("B3 / points at the console, not the old pages", "/console" in app.PAGE and "/tester" not in app.PAGE
          and 'href="/tests"' not in app.PAGE)
    check("B4 the console is mounted on its own", "console_page" in (ROOT / "app.py").read_text(encoding="utf-8"))
    check("B5 the run files and the run store are still on disk", (store.RES / "runs" / "index.html").exists()
          and list(store.RES.glob("runs-*.jsonl")))


def main() -> int:
    try:
        part_a(); part_b()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
