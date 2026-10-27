"""The run log (TC-31): every event a plan's dispatch produces, append-only `results/tc/runlog.jsonl`.

Events: `sent` (with ISO's outcome: `match`, `mismatch`, `refused`, `error`), `dedupe` (a stored answer reused, no call),
`override` (a call past a full lane, with its reason), `capped` (the lane or day is full: dispatch waits for the reset),
`reset` (a new day began), and the plan controls (`start`, `pause`, `resume`, `stop`, `done`, `pass3`). The ledger
remains the count of calls (D21); this is what each call was for and what came of it.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "results" / "tc" / "runlog.jsonl"


def add(*, plan: str, event: str, scenario: str = "", state: str = "", detail: str = "", by: str = "", **extra) -> dict:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "plan": plan, "event": event, "scenario": scenario, "state": state,
           "detail": detail, "by": by, **extra}
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def entries(plan: str | None = None, limit: int = 500) -> list:
    if not STORE.exists():
        return []
    out = [json.loads(x) for x in STORE.read_text(encoding="utf-8").splitlines() if x.strip()]
    if plan:
        out = [e for e in out if e["plan"] == plan]
    return out[-limit:]
