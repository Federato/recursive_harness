"""The Deviations Proof board (DEVIATIONS-PLAN.md P4): T1-T10 as rows, each from the suite that proves it.

Nothing here rates or calls ISO. Each row is read from the last run of its suite (`deviations.suite_log`); T3 and
T8 also list every case ISO answered (`results/deviations/p3/verdicts.json`), each with its Trace Diff scenario.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERDICTS = ROOT / "results" / "deviations" / "p3" / "verdicts.json"

#: (test, claim, suite, check-label prefixes that belong to it; None = the whole suite)
TESTS = (
    ("T1", "No company: today's engine, field for field", "engine", ("A",)),
    ("T2", "Neutral deviations change nothing", "engine", ("C", "D")),
    ("T3", "Technical equals ISO's service", "proof", ("T3",)),
    ("T4", "Only what was deviated changes", "proof", ("T4",)),
    ("T5", "The LCMs applied are the ones filed", "proof", ("T5",)),
    ("T6", "A table override, to the digit", "proof", ("T6",)),
    ("T7", "Where and when a filing applies", "proof", ("T7",)),
    ("T8", "Edition pins match ISO", "proof", ("T8",)),
    ("T9", "A filing over an ISO revision", "proof", ("T9",)),
    ("T10", "The files say what people wrote", "files", None),
)
SUITE_CMD = {"files": "python tests/verify_deviations_files.py",
             "engine": "python tests/verify_deviations_engine.py",
             "proof": "python tests/verify_deviations_proof.py"}
LINE = {"CF": "CP", "GL": "GL"}


def _match(label: str, prefixes) -> bool:
    if prefixes is None:
        return True
    head = label.split()[0] if label else ""

    def one(p: str) -> bool:
        if len(p) == 1:                        # a section letter: "A1", "C12"
            return head[:1] == p and head[1:2].isdigit()
        nxt = head[len(p):len(p) + 1]          # a test id: "T7", "T7a" -- never "T1" for "T10"
        return head.startswith(p) and not nxt.isdigit()
    return any(one(p) for p in prefixes)


def proof() -> dict:
    from deviations import suite_log
    from . import tracediff
    suites = {k: suite_log.load(k) for k in SUITE_CMD}
    verdicts = json.loads(VERDICTS.read_text(encoding="utf-8")) if VERDICTS.exists() else []
    rows = []
    for tid, claim, suite, prefixes in TESTS:
        s = suites.get(suite)
        checks = [c for c in (s or {}).get("checks", []) if _match(c[0], prefixes)]
        status = "not run" if not checks else "pass" if all(ok for _, ok in checks) else "fail"
        cases = []
        if tid in ("T3", "T8"):
            for v in verdicts:
                if v.get("test") != tid:
                    continue
                sid = tracediff.scenario_id(LINE[v["line"]], v["state"], v["hash"]) if v.get("hash") else None
                cases.append({"id": v["id"], "line": LINE[v["line"]], "state": v["state"], "verdict": v["verdict"],
                              "scenario": sid, "detail": str(v.get("detail", ""))[:200],
                              "premium": v.get("premium") or {k: v.get(k) for k in ("pinned_technical", "iso_at_date")
                                                              if k in v}})
        rows.append({"test": tid, "claim": claim, "suite": suite, "command": SUITE_CMD[suite], "status": status,
                     "passed": sum(1 for _, ok in checks if ok), "total": len(checks),
                     "checks": checks, "ranAt": (s or {}).get("ran_at"), "commit": (s or {}).get("commit"),
                     "cases": cases})
    return {"tests": rows, "gate": "docs/gates/GATE-DEVIATIONS.md",
            "allPass": all(r["status"] == "pass" for r in rows),
            "snapshot": "python scripts/cf/206_snapshot_regression.py --check (the full T1 population; run apart)"}
