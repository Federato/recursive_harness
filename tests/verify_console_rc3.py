#!/usr/bin/env python3
"""The test console, RC-3 (docs/TC-PLAN.md TC-20..TC-25): Trace Diff and the Scenario Workbench. No ISO calls.

  A  worksheet map: paths, stable IDs, agreement rule, the trace's ERC source, the catalog (TC-20)
  B  Trace Diff: first divergence, flows-from, collapsed records, seen before, brief, refusals (TC-21)
  C  classify a mismatch; the cell follows (TC-22)
  D  Scenario Workbench: build, rate free with mode / rounding, dedupe, send through a stand-in client (TC-23)
  E  promote to the Regression Library (TC-24)
  F  proof: OI-133 replayed before its fix, OI-116 as it stands (TC-25)
  G  the screens; the gate: Trace Diff on 10 stored scenarios per line, every row aligned; no call spent

    python tests/verify_console_rc3.py
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

from console import evidence, ledger, library, mismatch, readiness, store, tracediff as T, workbench as WB, worksheet as W  # noqa: E402

RESULTS = []
TMP = Path(tempfile.mkdtemp(prefix="tc-rc3-"))
CALLS_BEFORE = ledger.used()["total"]


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


# Everything the console writes goes to a scratch folder for the whole run; the reference index and evidence are read.
T.SEEN = TMP / "divergences.jsonl"
mismatch.STORE = TMP / "classifications.jsonl"
library.STORE, library.PAYLOADS = TMP / "library.jsonl", TMP / "library"
readiness.CACHE, readiness.SIGNOFFS = TMP / "readiness.json", TMP / "signoffs.jsonl"

OH, FL116, FL133 = "CP-OH-c473de0f0e", "CP-FL-865e8e3634", "CP-FL-a423e73917"


def part_a():
    print("A. worksheet map (TC-20)")
    check("A1 our XTable containers and [0] drop out of a path",
          W.normalise("/CommercialPropertyTable[0]/CommercialProperty[0]/X[1]/Premium") == "/CommercialProperty/X[1]/Premium")
    check("A2 a stable ID drops every index", W.stable_id("/CommercialProperty/X[1]/Y[2]/Premium") == "/CommercialProperty/X/Y/Premium")
    check("A3 agreement: numbers by value, dates by date, ISO's and our GUIDs never differ",
          W.same("7386", 7386.0) and W.same("10/01/2026", "2026-10-01T00:00:00")
          and W.same("00000002-0000-0000-0000-000000000000", "47e25df8-6318-4b1a-8882-c523117e74a0") and not W.same("1", "2"))
    check("A4 a field named as a code is a code, even when its value looks numeric",
          [W.kind("2", "RatingIdentificationCode"), W.kind("1", "SublineBasicGroupII"), W.kind("12.5", "Premium")] == ["code", "code", "number"])
    e = next(x for x in store.load()["references"] if T.scenario_id(x["line"], x["state"], x["hash"]) == OH)
    req = json.loads((ROOT / next(f for f in e["files"] if f.endswith("_request.json"))).read_text(encoding="utf-8"))
    resp = json.loads((ROOT / [f for f in e["files"] if f.endswith("_response.json")][-1]).read_text(encoding="utf-8"))
    tree, trace, total = W.rate("CP", req)
    writes = [t for t in trace if t.kind == "write"]
    check("A5 the trace's writes carry the node, rule file and package (the engine's one RC-3 change, data only)",
          writes and all({"node", "rule_file", "package"} <= set(t.data) for t in writes))
    rows = W.align("CP", tree, trace, W.body_of("CP", resp))
    both = [r for r in rows if r["in_iso"] and r["in_ours"]]
    check("A6 CP OH: over 1,500 fields aligned both sides, all agree", len(both) > 1500 and all(r["match"] for r in both), len(both))
    check("A7 premiums we write carry their rule file and package",
          all(r["rule_file"] and r["package"] for r in both if r["field"] == "Premium" and r["written"]))
    cat = W.catalog()
    check("A8 the catalog is versioned, per line, with each side's fields counted",
          re.match(r"\d{8}-[0-9a-f]{12}$", cat.get("version", "")) and set(cat["lines"]) == {"CP", "GL"}
          and all(v["counts"].get("both", 0) > 300 for v in cat["lines"].values()), cat.get("version"))


def part_b():
    print("B. Trace Diff (TC-21)")
    d = T.diff(OH)
    check("B1 an agreeing scenario: no divergent step, every record collapsed",
          d["counts"]["steps"] == 0 and d["roots"] == [] and all(r["collapsed"] for r in d["records"]))
    d = T.diff(FL116)
    r0 = d["roots"][0] if d["roots"] else {}
    check("B2 OI-116: the first divergence is the condo record's premium ISO's answer leaves out (ours 293, ISO absent)",
          r0.get("field") == "Premium" and "ResidentialCondos" in r0.get("path", "") and str(r0.get("ours")) == "293"
          and r0.get("iso") is None, r0)
    flows = [r for r in d["rows"] if r.get("role") == "flows"]
    check("B3 the totals above it flow from it, and say so",
          len(flows) == 4 and all(r["flowsFrom"] == r0["path"] for r in flows) and r0["downstream"] == 4)
    check("B4 the divergent records stay open; the rest collapse",
          [r["record"] for r in d["records"] if not r["collapsed"]] and sum(r["collapsed"] for r in d["records"]) > 100)
    check("B5 each divergence names the rule file that wrote it", r0.get("rule_file", "").endswith("Rules"))
    check("B6 the brief names the scenario, the totals and the first divergence",
          all(x in d["brief"] for x in (FL116, "1693", "FIRST divergence", "ResidentialCondos")))
    mismatch.classify(FL116, "raas_anomaly", note="OI-116, a question to ISO", by="test")
    T._CACHE.clear()
    T.remember("CP-FL-other", "CP", "FL", [{"id": r0["id"], "field": "Premium"}])
    d2 = T.diff(FL116)
    seen = d2["seenBefore"]
    check("B7 seen before (D16): another scenario that diverged at the same stable ID is named", any(s["scenario"] == "CP-FL-other" for s in seen))
    other_side = T.seen_before("CP-FL-other", [r0["id"]])
    check("B8 ...with its classification", any(s["scenario"] == FL116 and s["classification"]["category"] == "raas_anomaly" for s in other_side))
    T.remember(FL116, "CP", "FL", d2["roots"] * 3)
    ids = [(x["scenario"], x["id"]) for x in T._seen_all()]
    check("B9 a divergence is remembered once per scenario", len(ids) == len(set(ids)))
    gl = [s for s in T.scenarios("GL") if s["outcome"] == "rated"][:3]
    gds = [T.diff(s["hash"]) for s in gl]
    check("B10 GL answers: premiums agree, no numeric step differs; form names counted apart, as text",
          gds and all(g["counts"]["steps"] == 0 and g["counts"]["compared"] > 300 for g in gds))
    d = T.diff(FL133)
    check("B11 a refusal both sides make, at the same table, reads as agreement",
          d.get("bothRefuse") and d.get("sameTable") and "CyberIncidentExclusionFactors" in d["isoTables"])


def part_c():
    print("C. classify (TC-22)")
    from ui import console_page as CP
    code, _, _ = CP.dispatch("POST", "/api/console/classify", {}, {"scenario": OH, "category": "nonsense"})
    check("C1 an unknown category is refused", code == 400)
    ev_saved = evidence.STORE
    evidence.STORE = TMP / "evidence.jsonl"
    readiness._MEM.clear()
    try:
        sc = readiness.paths.in_scope("CP", "OH", "Building")
        evidence.add(scenario="c-agree", line="CP", state="OH", walked=sc, ours="100", iso="100")
        evidence.add(scenario="c-round", line="CP", state="OH", walked=sc[:1], ours="100.60", iso="100")
        cell = lambda: next(c for c in readiness.get(lob="CP", state="OH")["cells"] if c["coverage"] == "Building")
        check("C2 before: the 60-cent difference holds the cell at mismatch", cell()["status"] == "mismatch")
        code, body, _ = CP.dispatch("POST", "/api/console/classify", {}, {"scenario": "c-round", "category": "rounding",
                                                                           "note": "ISO rounds at the step", "by": "test"})
        j = json.loads(body)
        check("C3 classified from Trace Diff: stored, judged within its tolerance", code == 200 and j["withinTolerance"] is True and j["inEvidence"])
        check("C4 the cell follows: Passed", cell()["status"] == "verified")
        CP.dispatch("POST", "/api/console/classify", {}, {"scenario": "c-round", "category": "true_engine_defect", "by": "test"})
        check("C5 reclassified a true defect (tolerance zero): the cell goes back to mismatch", cell()["status"] == "mismatch")
    finally:
        evidence.STORE = ev_saved
        readiness._MEM.clear()


class StandIn:
    """A RaaS stand-in: records the call, answers like ISO would, spends nothing."""
    def __init__(self, fail=None):
        self.calls, self.fail = [], fail

    def rate(self, payload):
        self.calls.append(payload)
        if self.fail:
            from raas import RaaSError
            raise RaaSError(self.fail)
        return {"Body": {}}


def part_d():
    print("D. Scenario Workbench (TC-23)")
    p = WB.build("GL", "OH", {"occurrence_limit": "500,000 CSL"})
    up, down = WB.rate("GL", p), WB.rate("GL", p, rounding="ROUND_DOWN")
    check("D1 GL built from ISO's declared domains and rated free", up["outcome"] == "rated" and up["paths"])
    check("D2 mode and rounding (D22) reach the engine", up["premium"] != down["premium"], (up["premium"], down["premium"]))
    cp = WB.build("CP", "OH")
    r = WB.rate("CP", cp)
    check("D3 CP: the state's sample, rated free", r["outcome"] == "rated" and r["premium"])
    check("D4 dedupe: an exact stored answer is found (the OH sample ISO answered in RC-1)",
          r["stored"] and r["stored"]["outcome"] == "rated" and W.same(r["stored"]["iso"], r["premium"]), r["stored"])
    s = StandIn()
    out = WB.send("CP", cp, reuse=True, client=s)
    check("D5 Send with a stored answer reuses it and calls nobody", out["reused"] and not out["sent"] and not s.calls)
    out = WB.send("CP", cp, reuse=False, client=s)
    check("D6 asked to spend anyway: exactly one call", out["sent"] and len(s.calls) == 1)
    out = WB.send("GL", p, reuse=False, client=StandIn(fail="call not sent: the adhoc lane is full today (50 of 50)"))
    check("D7 a full lane comes back as capped, not sent", out["capped"] and not out["sent"])
    e = WB.every_state({"occurrence_limit": "1,000,000 CSL"}, ["OH", "NJ", "AK"])
    check("D8 run in every state (D19): rated free, calls to send counted", len(e["rows"]) == 3 and e["applicable"] == 3
          and e["callsToSend"] <= 3)
    from ui import console_page as CP
    code, body, _ = CP.dispatch("POST", "/api/console/workbench/where", {}, {"config": {"occurrence_limit": "1,000,000 CSL"}})
    j = json.loads(body)
    code2, body2, _ = CP.dispatch("POST", "/api/console/workbench/where", {}, {"config": {"occurrence_limit": "1000000"}})
    j2 = json.loads(body2)
    check("D9 check where it applies (D19): a declared limit applies in all 51; an undeclared one nowhere, each with a reason",
          code == 200 and len(j["applicable"]) == 51 and code2 == 200 and not j2["applicable"]
          and len(j2["not_applicable"]) == 51 and all("not declared legal" in v for v in j2["not_applicable"].values()))
    code, body, _ = CP.dispatch("GET", "/api/console/workbench/curve", {"control": "occurrence_limit"}, None)
    check("D10 response curves (D18) from the run store", code == 200 and json.loads(body)["series"])
    code, body, _ = CP.dispatch("GET", "/api/console/workbench/spec", {"lob": "GL"}, None)
    j = json.loads(body)
    check("D11 the spec offers GL's controls, modes and roundings", len(j["controls"]) >= 20 and j["modes"] and len(j["roundings"]) == 3)


def part_e():
    print("E. promote to the Regression Library (TC-24)")
    h = next(x for x in store.load()["references"] if T.scenario_id(x["line"], x["state"], x["hash"]) == OH)["hash"]
    e = library.promote(scenario=OH, line="CP", state="OH", origin="trace", request_hash=h, by="test")
    check("E1 from Trace Diff: kept with ISO's stored answer as its reference", e["reference"] == "iso" and e["hash"] == h)
    check("E2 promoting it again is a no-op", library.promote(scenario=OH, line="CP", state="OH", origin="trace", request_hash=h)["already"]
          and len(library.entries()) == 1)
    p = WB.build("GL", "OH", {"occurrence_limit": "500,000 CSL"})
    e = library.promote(scenario="GL-OH-wb-x", line="GL", state="OH", origin="workbench", request=p, ours="6371")
    kept = Path(e.get("request_file", ""))
    check("E3 from the Workbench with no ISO answer: the request kept, marked as our reference",
          e["reference"] == "ours" and e["ours"] == "6371" and (kept if kept.is_absolute() else ROOT / kept).exists())
    from ui import console_page as CP
    code, _, _ = CP.dispatch("POST", "/api/console/promote", {}, {"scenario": "x", "line": "GL", "state": "OH", "origin": "trace"})
    check("E4 neither a stored answer nor a request: refused", code == 400)


def part_f():
    print("F. proof: a known mismatch replayed (TC-25)")
    from cf_engine.resolve.book import CFResolvedBook as B
    saved = B.NO_EMPTY_FALLBACK_STATE
    B.NO_EMPTY_FALLBACK_STATE = frozenset()                  # OI-133 before its fix, in memory only
    try:
        T._CACHE.clear()
        d = T.diff(FL133)
    finally:
        B.NO_EMPTY_FALLBACK_STATE = saved
        T._CACHE.clear()
    r0 = d["roots"][0] if d.get("roots") else {}
    check("F1 OI-133 before its fix: ours rates where ISO refused", d.get("oursRates") and d.get("oursTotal") == "2774", d.get("oursTotal"))
    check("F2 ...and the first divergence is the step ISO names: CyberIncidentExclusionFactors at CW / Basic Group I",
          r0.get("field") == "CyberIncidentExclusionFactors" and "'Basic Group I'" in r0.get("tables", [""])[0]
          and "Keys: CW, Basic Group I" in d["isoRefused"], r0)
    check("F3 ...read from countrywide (the fallback the fix removed), 0.995",
          r0.get("package", "").startswith("CF_CW_") and str(r0.get("ours")) == "0.995", (r0.get("package"), r0.get("ours")))
    d = T.diff(FL133)
    check("F4 with the fix: both refuse at the same table", d.get("bothRefuse") and d.get("sameTable"))


def part_g():
    print("G. the screens and the gate")
    from ui import console_page as CP
    html = CP.page()
    check("G1 Trace Diff and the Workbench are built", all(i in html for i in ('id="td-body"', 'id="td-side"', 'id="wb-inputs"', 'id="wb-confirm"'))
          and "Built in TC-21" not in html and "Built in TC-23" not in html)
    node = shutil.which("node")
    if node:
        js = TMP / "page.js"
        js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
        res = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        check("G2 the page's script parses", res.returncode == 0, res.stderr[-300:])
    for line in ("CP", "GL"):
        sc = [s for s in T.scenarios(line) if s["outcome"] == "rated"]
        spread = sc[:: max(1, len(sc) // 10)] + sc          # a spread first, then the rest, until 10 rate in ours
        bad, n, seen = [], 0, set()
        for s in spread:
            if n == 10 or s["hash"] in seen:
                continue
            seen.add(s["hash"])
            d = T.diff(s["hash"])
            if d.get("refused") or not d["rows"]:
                continue                                      # ours refuses by decision (C28-17): nothing to align
            n += 1
            for r in d["rows"]:
                status = r["match"] is True or (r["in_iso"] != r["in_ours"]) or r["match"] is False or r["match"] is None
                differ_num = r["kind"] == "number" and r["match"] is False and r["in_iso"] and r["in_ours"]
                if not status or (differ_num and r.get("role") not in ("first", "divergence", "flows")):
                    bad.append((s["scenario"], r["path"]))
        check(f"G3 gate: Trace Diff on {n} stored {line} scenarios, every row aligned (a status each, every differing step placed)",
              n >= 10 and not bad, (n, bad[:3]))
    p = WB.build("CP", "OH")
    WB.rate("CP", p)
    WB.send("CP", p, reuse=True)
    check("G4 gate: the Workbench rated and reused a stored answer; the ledger counted no call",
          ledger.used()["total"] == CALLS_BEFORE, (CALLS_BEFORE, ledger.used()["total"]))


def main() -> int:
    try:
        part_a(); part_b(); part_c(); part_d(); part_e(); part_f(); part_g()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
