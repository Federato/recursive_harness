#!/usr/bin/env python3
"""The test console's results inspection: a person's pass / fail / excuse on each plan result, beside ISO's agreement.
No ISO calls; every store is a temporary one.

  A  the record: what each verdict needs, undo, the latest verdict counts
  B  a plan's view: counts, pass-all-matches (matches only), sign-off (refused while anything awaits; needs a name)
  C  the board layer: plan results nobody inspected are awaiting; seeded history is not; a verdict clears it;
     ISO's ✓ is unchanged by inspection (choice (b))
  D  the routes and the page: the API end to end, the buttons and the views on the page, the JS parses

    python tests/verify_console_inspection.py
"""
from __future__ import annotations

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
TMP = Path(tempfile.mkdtemp(prefix="tc-insp-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"

from console import board as B, evidence, inspection as I, plans as P  # noqa: E402
from ui import console_page as CP  # noqa: E402

I.STORE, evidence.STORE, P.PLANS = TMP / "insp.jsonl", TMP / "ev.jsonl", TMP / "plans"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def refused(fn):
    try:
        fn()
    except I.InspectionError:
        return True
    return False


PLAN = {"id": "T-plan", "name": "test plan", "line": "GL", "status": "done", "committed_at": "2026-10-07T15:00:00", "scenarios": [
    {"scenario": "GL-OH-aaaa", "state": "OH", "config": {"class_code": "11127"}, "status": "match", "ours": "100", "iso": "100.0"},
    {"scenario": "GL-NY-bbbb", "state": "NY", "config": {}, "status": "match", "ours": "200", "iso": "200.0"},
    {"scenario": "GL-PR-cccc", "state": "PR", "config": {}, "status": "refused", "ours": "716", "iso": None,
     "message": '{"Body":{"Message":"Permission is not granted to GL PR for rating."}}'},
    {"scenario": "GL-TX-dddd", "state": "TX", "config": {}, "status": "mismatch", "ours": "300", "iso": "301.0"},
    {"scenario": "GL-CA-eeee", "state": "CA", "config": {}, "status": "queued"}]}


def part_a():
    print("A  the record")
    check("A1 a fail without a category is refused", refused(lambda: I.record("GL-TX-dddd", "fail", reason="wrong")))
    check("A2 a fail without a reason is refused", refused(lambda: I.record("GL-TX-dddd", "fail", category="true_engine_defect")))
    check("A3 an excuse without a reason is refused", refused(lambda: I.record("GL-PR-cccc", "excuse")))
    check("A4 an unknown verdict is refused", refused(lambda: I.record("GL-PR-cccc", "maybe")))
    I.record("GL-OH-aaaa", "pass", by="Dan")
    check("A5 a pass needs nothing else; the latest verdict counts", I.latest()["GL-OH-aaaa"]["verdict"] == "pass")
    I.record("GL-OH-aaaa", "undo", by="Dan")
    check("A6 undo withdraws it", "GL-OH-aaaa" not in I.latest())
    I.record("GL-OH-aaaa", "fail", by="Dan", reason="ELP wrong", category="true_engine_defect")
    I.record("GL-OH-aaaa", "pass", by="Dan")
    check("A7 a later verdict replaces an earlier one; the history keeps both",
          I.latest()["GL-OH-aaaa"]["verdict"] == "pass" and len(I.history()) == 4)
    I.record("GL-OH-aaaa", "undo")


def part_b():
    print("B  a plan's view")
    v = I.plan_view(PLAN)
    c = v["counts"]
    check("B1 only results are inspectable (a queued row is not)", c["total"] == 4 and c["awaiting"] == 4, c)
    check("B2 awaiting rows first, mismatches before refusals before matches",
          [r["result"] for r in v["rows"]] == ["mismatch", "refused", "match", "match"], [r["result"] for r in v["rows"]])
    check("B3 sign-off is refused while anything awaits", refused(lambda: I.signoff(PLAN, by="Dan")))
    n = I.pass_matches(PLAN, by="Dan")
    v = I.plan_view(PLAN)
    check("B4 pass-all-matches passes the two matches and nothing else",
          n == 2 and v["counts"]["pass"] == 2 and v["counts"]["awaiting"] == 2, v["counts"])
    check("B5 pass-all-matches again passes nothing", I.pass_matches(PLAN, by="Dan") == 0)
    I.record("GL-PR-cccc", "excuse", by="Dan", reason="GL PR not in our RaaS subscription", plan=PLAN["id"])
    I.record("GL-TX-dddd", "fail", by="Dan", reason="ILF off by a dollar", category="rounding", plan=PLAN["id"])
    check("B6 sign-off needs a name", refused(lambda: I.signoff(PLAN, by="")))
    s = I.signoff(PLAN, by="Dan")
    v = I.plan_view(PLAN)
    check("B7 signed off with the counts", v["signoff"] and "2 passed · 1 failed · 1 excused" in s["reason"], s)
    check("B8 the excuse and the fail keep their reasons and category",
          v["rows"][0]["verdict"]["reason"] and any(r["verdict"]["category"] == "rounding" for r in v["rows"]))


def part_c():
    print("C  the board layer")
    walked = ["gl.po.basis.sales", "gl.po.ilf.direct"]
    evidence.add(scenario="GL-OH-seed", line="GL", state="OH", walked=walked, ours="5", iso="5", source="run 2026-09-01")
    evidence.add(scenario="GL-OH-plan1", line="GL", state="OH", walked=walked, ours="7", iso="7", source="plan P1", plan="P1")
    evidence.add(scenario="GL-WY-plan2", line="GL", state="WY", walked=walked, ours=None, iso=None, source="plan P1", plan="P1")
    aw = I.awaiting("GL")
    check("C1 plan results nobody inspected are awaiting; seeded history is not",
          sorted(aw["scenarios"]) == ["GL-OH-plan1", "GL-WY-plan2"], aw["scenarios"])
    check("C2 the cells carry the count", aw["cells"]["OH"]["gl.po.basis.sales"] == 1 and "WY" in aw["cells"])
    b = B.board("GL")
    check("C3 the board reports it", b["summary"]["awaitingInspection"] == 2 and b["awaiting"]["OH"]["gl.po.ilf.direct"] == 1)
    cell = B.cell("GL", "OH", "gl.po.basis.sales")
    rows = {x["scenario"]: x for x in cell["scenarios"]}
    check("C4 the cell panel marks plan results inspectable, history not",
          rows["GL-OH-plan1"]["inspectable"] and not rows["GL-OH-seed"]["inspectable"])
    before = B.cell("GL", "OH", "gl.po.basis.sales")["status"]
    I.record("GL-OH-plan1", "pass", by="Dan")
    I.record("GL-WY-plan2", "excuse", by="Dan", reason="test")
    after = B.cell("GL", "OH", "gl.po.basis.sales")
    check("C5 a verdict clears it", I.awaiting("GL")["count"] == 0 and B.board("GL")["summary"]["awaitingInspection"] == 0)
    check("C6 ISO's ✓ is unchanged by inspection (choice (b))", after["status"] == before, (before, after["status"]))
    check("C7 the cell panel shows the verdict",
          {x["scenario"]: x for x in after["scenarios"]}["GL-OH-plan1"]["verdict"]["verdict"] == "pass")


def part_d():
    print("D  the routes and the page")
    P.PLANS.mkdir(parents=True, exist_ok=True)
    plan2 = {**PLAN, "id": "T-plan2", "scenarios": [dict(s, scenario=s.get("scenario", "") + "-2") for s in PLAN["scenarios"]]}
    (P.PLANS / "T-plan2.json").write_text(json.dumps(plan2), encoding="utf-8")
    call = lambda m, path, q=None, b=None: json.loads(CP.dispatch(m, path, q or {}, b)[1])   # noqa: E731
    v = call("GET", "/api/console/inspect/plan", {"id": "T-plan2"})
    check("D1 GET a plan's results", v.get("counts", {}).get("total") == 4, v)
    r = call("POST", "/api/console/inspect", b={"scenario": "GL-TX-dddd-2", "verdict": "fail", "reason": "x"})
    check("D2 a bad verdict comes back as an error, not a crash", "error" in r, r)
    r = call("POST", "/api/console/inspect/pass-matches", b={"plan": "T-plan2", "by": "Dan"})
    check("D3 pass-all-matches through the route", r.get("passed") == 2, r)
    r = call("POST", "/api/console/inspect/signoff", b={"plan": "T-plan2", "by": "Dan"})
    check("D4 sign-off through the route is refused while two await", "error" in r and "2" in r["error"], r)
    r = call("GET", "/api/console/inspect/verdicts", {"ids": "GL-OH-aaaa-2,GL-PR-cccc-2"})
    check("D5 verdicts for a list", r["GL-OH-aaaa-2"]["verdict"] == "pass" and r["GL-PR-cccc-2"] is None, r)
    check("D6 GET only for writes", CP.dispatch("GET", "/api/console/inspect", {}, None)[0] == 405)
    ps = call("GET", "/api/console/plans")
    check("D7 the plans list carries each plan's inspection counts",
          any(p.get("inspection", {}).get("awaiting") == 2 for p in ps["plans"]), ps)
    h = CP.page()
    check("D8 the page has the Queue's inspection view, Trace Diff's slot and the board's stat",
          all(x in h for x in ('id="qu-insp"', "insp-slot", "Awaiting inspection", "Pass all ", "Sign off this plan",
                               "data-iv=\"excuse\"")))
    js = TMP / "page.js"
    js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", h, re.S)), encoding="utf-8")
    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        check("D9 the page's JS parses", r.returncode == 0, r.stderr[:300])
    else:
        check("D9 the page's JS parses (node not found: skipped)", True)


if __name__ == "__main__":
    try:
        part_a(); part_b(); part_c(); part_d()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    n = sum(ok for _, ok in RESULTS)
    print(f"\n{n}/{len(RESULTS)} passed")
    sys.exit(0 if n == len(RESULTS) else 1)
