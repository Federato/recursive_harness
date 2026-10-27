"""Each deviation suite's last result, for the console's Deviations Proof board (P4).

A suite calls `record(name, checks)` as it finishes; the board reads `results/deviations/suites/<name>.json`.
Recording never fails a suite.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "results" / "deviations" / "suites"


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:                                          # noqa: BLE001
        return ""


def record(name: str, checks: list) -> None:
    """`checks`: [(label, ok)] in the order the suite ran them."""
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        (DIR / f"{name}.json").write_text(json.dumps({
            "suite": name, "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "commit": _commit(),
            "checks": [[str(lb), bool(ok)] for lb, ok in checks],
            "passed": all(ok for _, ok in checks)}, indent=1), encoding="utf-8")
    except Exception as exc:                                   # noqa: BLE001
        print(f"  (could not record the suite result: {exc})")


def load(name: str) -> dict | None:
    p = DIR / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
