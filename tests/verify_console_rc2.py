#!/usr/bin/env python3
"""The test console's screens, RC-2 (docs/TC-PLAN.md TC-14..TC-19). No ISO calls.

  A  console shell: seven tabs, the call-cap strip, the shared legend (TC-14)
  B  /api/console/readiness: cells, columns, cap, totals; recomputed when an input changes (TC-15)

    python tests/verify_console_rc2.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. console shell (TC-14)")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["RAAS_LEDGER_DIR"] = tmp           # a ledger of our own, so the real one is never read or written
        from console import ledger, status
        from ui import console_page, tester

        code, html, kind = tester.dispatch("GET", "/console", {}, None)
        check("A1 /console is served through the ui mount", code == 200 and kind == "html")
        check("A2 the seven screens, in the brief's order", [label for _, label, _ in console_page.SCREENS] == [
            "Coverage Board", "Readiness Matrix", "Test Plan Builder", "Trace Diff", "Scenario Workbench",
            "Regression Library", "Queue & Run Log"] and html.count('class="tab"') == 7)
        check("A3 no external fonts, scripts or stylesheets (D7)",
              not any(s in html for s in ("<link", "src=\"http", "@import", "fonts.googleapis")))

        c = console_page.cap()
        check("A4 cap strip: 250 in lanes 150 / 50 / 50 (D2)",
              c["cap"] == 250 and [(l["key"], l["cap"]) for l in c["lanes"]] == [("active", 150), ("refresh", 50), ("adhoc", 50)])
        check("A5 empty ledger: 0 used, 250 left, nothing queued", (c["used"], c["left"], c["queued"]) == (0, 250, 0))
        ledger.record(lane="adhoc", origin="test", outcome="rated")
        ledger.record(lane="active", origin="test", outcome="refused", override="test reason")
        c = console_page.cap()
        check("A6 cap strip follows the ledger, per lane and overrides",
              (c["used"], c["left"], c["overrides"]) == (2, 248, 1)
              and {l["key"]: l["used"] for l in c["lanes"]} == {"active": 1, "refresh": 0, "adhoc": 1}, c)
        code, body, kind = tester.dispatch("GET", "/api/console/cap", {}, None)
        check("A7 /api/console/cap returns the same", code == 200 and json.loads(body)["used"] == 2)

        summer = console_page.cap(datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc))
        winter = console_page.cap(datetime(2026, 12, 7, 12, 0, tzinfo=timezone.utc))
        check("A8 resets at 00:00 Eastern, daylight and standard time",
              summer["resets_at"] == "2026-10-08T04:00:00Z" and winter["resets_at"] == "2026-12-08T05:00:00Z",
              (summer["resets_at"], winter["resets_at"]))
        check("A9 the legend is TC-08's vocabulary, every state",
              [g["key"] for g in console_page.legend()] == [s.key for s in status.ALL]
              and all(f'chip.{s.key}' in html for s in status.ALL))
        check("A10 the shell spends no call: no POST route", console_page.dispatch("POST", "/console", {}, {}) is None)
        import re, shutil, subprocess
        node = shutil.which("node")
        if node:
            js = Path(tmp) / "page.js"
            js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
            res = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
            check("A11 the page's script parses (node --check)", res.returncode == 0, res.stderr.strip()[-300:])
        else:
            print("  skip A11 the page's script parses: node not found")
        os.environ.pop("RAAS_LEDGER_DIR")


def _cell(readiness, coverage, line="CP", state="OH"):
    return {x["coverage"]: x for x in readiness.get(lob=line, state=state)["cells"]}[coverage]


def part_b():
    print("B. readiness endpoint (TC-15)")
    from console import evidence, ledger, mismatch, paths, readiness, store
    from ui import tester
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        saved = (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD)
        evidence.STORE, mismatch.STORE, store.INDEX = t / "ev.jsonl", t / "cl.jsonl", t / "index.json"
        readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD = t / "rd.json", t / "so.jsonl", t / "build.json"
        os.environ["RAAS_LEDGER_DIR"] = tmp
        readiness._MEM.clear()

        def index(old_freshness):
            store.INDEX.write_text(json.dumps({"references": [{"hash": "h-fresh", "freshness": "fresh"},
                                                              {"hash": "h-old", "freshness": old_freshness}]}))
        try:
            index("stale")
            bldg = paths.in_scope("CP", "OH", "Building")
            r = readiness.get()
            cells = {(c["lob"], c["state"], c["coverage"]): c for c in r["cells"]}
            n = sum(len(paths.states(l)) * len(paths.coverages(l)) for l in paths.lines())
            check("B1 one cell per (line, state, coverage), both lines", len(cells) == n == len(r["cells"]), (len(cells), n))
            check("B2 columns are the coverages per line", r["columns"]["CP"][0] == "Building" and len(r["columns"]["GL"]) == 5)
            oh = cells[("CP", "OH", "Building")]
            check("B3 no evidence: every applicable cell untested, the rest n/a",
                  {c["status"] for c in r["cells"]} <= {"untested", "na"} and oh["status"] == "untested")
            check("B4 §5 fields on a cell", {"lob", "state", "coverage", "status", "paths", "openMismatches",
                  "estRemainingCalls", "contentVersion", "lastChangedAt", "signedOffBy", "signedOffAt"} <= set(oh))
            check("B5 content version is the package in force", oh["contentVersion"].startswith("CF_OH_"), oh["contentVersion"])
            check("B6 cap is the ledger's", r["cap"]["daily"] == 250 and r["cap"]["activeLane"] == 150)

            evidence.add(scenario="s1", line="CP", state="OH", walked=bldg, ours="100", iso="100", request_hash="h-fresh")
            c = readiness.get(lob="CP", state="OH")
            b = {x["coverage"]: x for x in c["cells"]}["Building"]
            check("B7 new evidence recomputes: every path agrees on a fresh answer -> Passed",
                  b["status"] == "verified" and b["paths"]["raasVerified"] == len(bldg), b["status"])
            check("B8 lob / state filter", {(x["lob"], x["state"]) for x in c["cells"]} == {("CP", "OH")}
                  and list(c["columns"]) == ["CP"])
            check("B9 totals count Passed per line", c["totals"]["CP"]["passed"] == 1)

            evidence.add(scenario="s2", line="CP", state="OH", walked=bldg[:1], ours="105", iso="100", request_hash="h-fresh")
            b = _cell(readiness, "Building")
            check("B10 an unclassified difference is an open mismatch", b["status"] == "mismatch"
                  and b["openMismatches"] == [{"scenarioId": "s2", "category": "unclassified", "delta": "5"}], b["openMismatches"])
            mismatch.classify("s2", "version_skew", ours="105", iso="100")
            b = _cell(readiness, "Building")
            check("B11 a classification recomputes (version skew has no band: still open, now categorised)",
                  b["status"] == "mismatch" and b["openMismatches"][0]["category"] == "version_skew")
            evidence.add(scenario="s2", line="CP", state="OH", walked=bldg[:1], ours="100.60", iso="100", request_hash="h-fresh")
            mismatch.classify("s2", "rounding", ours="100.60", iso="100")
            check("B12 classified within tolerance does not block Passed", _cell(readiness, "Building")["status"] == "verified")

            readiness.sign_off("CP", "OH", "Building", "Dan")
            check("B13 sign-off shows on a Passed cell (D4)", _cell(readiness, "Building")["signedOffBy"] == "Dan")
            evidence.add(scenario="s3", line="CP", state="OH", walked=bldg[1:2], ours="100", iso="100", request_hash="h-old")
            b = _cell(readiness, "Building")
            check("B14 a stale reference -> stale, and the sign-off falls away",
                  b["status"] == "stale" and b["signedOffBy"] is None and b["estRemainingCalls"] == 1,
                  (b["status"], b["signedOffBy"]))
            index("fresh")
            check("B15 an index rebuild (ingest / stored answer) recomputes", _cell(readiness, "Building")["status"] == "verified")

            before = readiness.get()["generatedAt"]
            readiness._MEM.clear()
            check("B16 unchanged inputs: served from the disk cache, not recomputed", readiness.get()["generatedAt"] == before)
            time.sleep(1.1)
            readiness.LAST_BUILD.write_text("{}")
            check("B17 a build marker recomputes", readiness.get()["generatedAt"] != before)

            evidence.add(scenario="s4", line="CP", state="OH", walked=paths.in_scope("CP", "OH", "Business income")[:1])
            bi = _cell(readiness, "Business income")
            check("B18 engine-only evidence -> internal, calls still owed",
                  bi["status"] == "internal" and bi["estRemainingCalls"] >= 1, bi["status"])
            evidence.add(scenario="s5", line="CP", state="OH", walked=paths.in_scope("CP", "OH", "Extra expense"), inert=True)
            check("B19 an INERT scenario counts toward nothing (D15)", _cell(readiness, "Extra expense")["status"] == "untested")
            full = readiness.get()
            tt = full["totals"]
            check("B20 totals strip (§8): passed per line, still to test, calls, days at 150",
                  tt["stillToTest"] == sum(c["status"] not in ("verified", "na") for c in full["cells"])
                  and tt["daysAtActiveLane"] == round(tt["estCallsToFinish"] / 150, 1))
            code, body, _ = tester.dispatch("GET", "/api/console/readiness", {"lob": "CP", "state": "OH"}, None)
            check("B21 served at /api/console/readiness", code == 200 and json.loads(body)["cells"][0]["state"] == "OH")
            check("B22 no call spent", ledger.used()["total"] == 0)
        finally:
            (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD) = saved
            readiness._MEM.clear()
            os.environ.pop("RAAS_LEDGER_DIR", None)


def part_c():
    print("C. Readiness Matrix screen (TC-16)")
    from console import evidence, mismatch, paths, readiness, store
    from ui import console_page, tester
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        saved = (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD,
                 store.current_package)
        evidence.STORE, mismatch.STORE, store.INDEX = t / "ev.jsonl", t / "cl.jsonl", t / "index.json"
        readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD = t / "rd.json", t / "so.jsonl", t / "build.json"
        os.environ["RAAS_LEDGER_DIR"] = tmp
        readiness._MEM.clear()
        lookups = []
        real_pkg = saved[-1]
        store.current_package = lambda *a: (lookups.append(a), real_pkg(*a))[1]
        try:
            store.INDEX.write_text(json.dumps({"references": [{"hash": "f", "freshness": "fresh"}]}))
            html = console_page.page()
            check("C1 the matrix screen is built (no placeholder), with its grid, totals, trend and side panel",
                  'id="s-matrix"' in html and "Built in TC-16" not in html
                  and all(i in html for i in ('id="mx-grid"', 'id="mx-stats"', 'id="mx-chart"', 'id="mx-side"')))
            check("C2 every state has a name for its row", all(s in console_page.STATE_NAMES
                  for l in paths.lines() for s in paths.states(l)))
            check("C3 the legend carries §6's needs text", {g["key"]: g["needs"] for g in console_page.legend()}["stale"]
                  == "Refresh stale references")

            bldg = paths.in_scope("CP", "OH", "Building")
            for sc, ours in (("a", "100"), ("b", "120"), ("b", "100")):
                evidence.add(scenario=sc, line="CP", state="OH", walked=bldg, ours=ours, iso="100", request_hash="f")
            lines = evidence.STORE.read_text().splitlines()
            fixed = []
            for raw, day in zip(lines, ("2026-10-01", "2026-10-01", "2026-10-02")):
                x = json.loads(raw); x["at"] = day + "T09:00:00"; fixed.append(json.dumps(x))
            evidence.STORE.write_text("\n".join(fixed) + "\n")
            ag = readiness.get()["agreement"]
            check("C4 agreement over time (D18): per day, latest record per scenario as of that day",
                  ag.get("CP") == [{"day": "2026-10-01", "compared": 2, "agreed": 1},
                                   {"day": "2026-10-02", "compared": 2, "agreed": 2}], ag)
            r = readiness.get(lob="CP", state="OH")
            b = {c["coverage"]: c for c in r["cells"]}["Building"]
            check("C5 path labels for every path in a cell", set(b["paths"]["byPath"]) <= set(r["pathLabels"]["CP"]))

            code, body, _ = tester.dispatch("POST", "/api/console/signoff",
                                            {}, {"lob": "CP", "state": "OH", "coverage": "BPP", "by": "Dan"})
            check("C6 sign-off refused on a cell that is not Passed (D4)", code == 409, (code, body))
            n0 = len(lookups)
            code, body, _ = tester.dispatch("POST", "/api/console/signoff",
                                            {}, {"lob": "CP", "state": "OH", "coverage": "Building", "by": "Dan"})
            b = _cell(readiness, "Building")
            check("C7 sign-off accepted on a Passed cell and shown", code == 200 and b["signedOffBy"] == "Dan", (code, body))
            check("C8 the recompute after a sign-off reuses the day's content versions (no engine reload)",
                  len(lookups) == n0 and b["contentVersion"].startswith("CF_OH_"), len(lookups) - n0)
            tester.dispatch("POST", "/api/console/signoff", {}, {"lob": "CP", "state": "OH", "coverage": "Building", "by": ""})
            check("C9 an empty name withdraws the sign-off", _cell(readiness, "Building")["signedOffBy"] is None)
            code, _, _ = tester.dispatch("POST", "/api/console/signoff", {}, {"lob": "CP", "state": "OH", "coverage": "Nope", "by": "x"})
            check("C10 an unknown cell is a 404", code == 404)
            n1 = len(lookups)
            time.sleep(0.05)
            store.INDEX.write_text(json.dumps({"references": [{"hash": "f", "freshness": "fresh"}], "x": 1}))
            readiness.get()
            check("C11 a new reference index (a corpus ingest) looks the content versions up again", len(lookups) > n1)
        finally:
            (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD,
             store.current_package) = saved
            readiness._MEM.clear()
            os.environ.pop("RAAS_LEDGER_DIR", None)


def part_d():
    print("D. Still to test (TC-17)")
    from console import evidence, mismatch, paths, readiness, store
    from ui import console_page
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        saved = (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD)
        evidence.STORE, mismatch.STORE, store.INDEX = t / "ev.jsonl", t / "cl.jsonl", t / "index.json"
        readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD = t / "rd.json", t / "so.jsonl", t / "build.json"
        os.environ["RAAS_LEDGER_DIR"] = tmp
        readiness._MEM.clear()
        try:
            store.INDEX.write_text(json.dumps({"references": [{"hash": "f", "freshness": "fresh"}, {"hash": "o", "freshness": "stale"}]}))
            sc = lambda cov, st="OH": paths.in_scope("CP", st, cov)
            evidence.add(scenario="m", line="CP", state="OH", walked=sc("Building")[:1], ours="120", iso="100", request_hash="f")
            evidence.add(scenario="s", line="CP", state="OH", walked=sc("BPP")[:2], ours="100", iso="100", request_hash="o")
            evidence.add(scenario="i", line="CP", state="OH", walked=sc("Business income")[:1])
            evidence.add(scenario="v", line="CP", state="OH", walked=sc("Extra expense"), ours="1", iso="1", request_hash="f")
            r = readiness.get()
            L = r["stillToTest"]
            oh = [g for g in L if g["lob"] == "CP" and g["state"] == "OH"]
            check("D1 one entry per cell neither Passed nor n/a", len(L) == sum(c["status"] not in ("verified", "na") for c in r["cells"]))
            check("D2 Passed cells are left out", not any(g["coverage"] == "Extra expense" and g["state"] == "OH" and g["lob"] == "CP" for g in L))
            order = [g["status"] for g in L]
            rank = {"mismatch": 0, "stale": 1, "internal": 2, "untested": 3}
            check("D3 status priority: mismatch, stale, internal, untested (§6, no wave key)",
                  order == sorted(order, key=rank.get) and order[:3] == ["mismatch", "stale", "internal"], order[:4])
            unt = [g["calls"] for g in L if g["status"] == "untested"]
            check("D4 within a status, the most calls first", unt == sorted(unt, reverse=True))
            check("D5 needs text per status (§6)", {g["status"]: g["needs"] for g in oh} == {
                "mismatch": "Triage + re-verify", "stale": "Refresh stale references",
                "internal": "RaaS pairwise + edges", "untested": "Tier 0, then RaaS"}, {g["status"]: g["needs"] for g in oh})
            check("D6 stale work is the refresh lane's, the rest the active lane's",
                  all(g["lane"] == ("refresh" if g["status"] == "stale" else "active") for g in L))
            check("D7 calls: one per stale reference and per open mismatch, not per path (§6)",
                  [g["calls"] for g in oh if g["status"] in ("mismatch", "stale")] == [1, 1], [(g["status"], g["calls"]) for g in oh][:2])
            tt = r["totals"]
            check("D8 days at 150/day, and stale refreshes at 50/day shown apart",
                  tt["daysAtActiveLane"] == round(tt["estCallsToFinish"] / 150, 1) and tt["daysAtRefreshLane"] == round(1 / 50, 1))
            f = readiness.get(lob="CP", state="OH")["stillToTest"]
            check("D9 the list follows the lob / state filter", f == oh)
            readiness._MEM.clear()
            cached = json.loads(readiness.CACHE.read_text()); cached["inputs"]["schema"] = 1; cached.pop("stillToTest")
            readiness.CACHE.write_text(json.dumps(cached))
            check("D10 a saved result from older code is not served (schema)", "stillToTest" in readiness.get())
            html = console_page.page()
            check("D11 the side panel lists them, with the build-a-plan button", "function mxList" in html
                  and "Build a test plan from these gaps" in html)
        finally:
            (evidence.STORE, mismatch.STORE, store.INDEX, readiness.CACHE, readiness.SIGNOFFS, readiness.LAST_BUILD) = saved
            readiness._MEM.clear()
            os.environ.pop("RAAS_LEDGER_DIR", None)


def main() -> int:
    part_a(); part_b(); part_c(); part_d()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
