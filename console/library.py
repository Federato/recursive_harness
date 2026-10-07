"""The Regression Library's store (TC-24 promotes into it; TC-33 shows it; TC-34 re-runs it on every build).

Append-only `results/tc/library.jsonl`, one entry per scenario (a second promote of the same scenario is a no-op):

  * **ISO reference**: a stored answer (by request hash) -- the library re-rates its request and compares with ISO;
  * **our reference**: a Workbench scenario that never went to ISO -- its request is kept under
    `results/tc/library/<scenario>.json` with our premium at promotion, so a later build that moves it is seen. It is
    labelled as ours: agreeing with ourselves is regression, not verification.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "results" / "tc" / "library.jsonl"
PAYLOADS = ROOT / "results" / "tc" / "library"


def entries() -> list:
    if not STORE.exists():
        return []
    return [json.loads(x) for x in STORE.read_text(encoding="utf-8").splitlines() if x.strip()]


def promote(*, scenario: str, line: str, state: str, origin: str, request_hash: str = "", request: dict | None = None,
            ours=None, by: str = "", note: str = "") -> dict:
    """Add a scenario to the library. Returns the entry, with `already` when it was there."""
    have = next((e for e in entries() if e["scenario"] == scenario), None)
    if have:
        return {**have, "already": True}
    if not request_hash and request is None:
        raise ValueError("a library entry needs a stored ISO answer (request hash) or a request to keep")
    e = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": scenario, "line": line, "state": state,
         "origin": origin, "reference": "iso" if request_hash else "ours", "hash": request_hash, "by": by, "note": note}
    if request is not None and not request_hash:
        PAYLOADS.mkdir(parents=True, exist_ok=True)
        f = PAYLOADS / (re.sub(r"[^A-Za-z0-9_.-]", "_", scenario) + ".json")
        f.write_text(json.dumps(request, indent=1), encoding="utf-8")
        e["request_file"] = str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f)
        e["ours"] = None if ours is None else str(ours)
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(e) + "\n")
    return e
