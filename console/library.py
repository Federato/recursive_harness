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
    out = [json.loads(x) for x in STORE.read_text(encoding="utf-8").splitlines() if x.strip()]
    for e in out:                                             # forward slashes, whichever system wrote them
        for k in ("request_file", "response_file"):
            if e.get(k):
                e[k] = e[k].replace("\\", "/")
    return out


def promote(*, scenario: str, line: str, state: str, origin: str, request_hash: str = "", request: dict | None = None,
            ours=None, by: str = "", note: str = "", fixture: str = "", fixture_file: str = "",
            response_file: str = "") -> dict:
    """Add a scenario to the library. Returns the entry, with `already` when it was there. A reference is a stored
    answer (request hash), one of ISO's STC fixtures with its own response (rebuilt as `157_` sends it), or, for a
    request ISO never answered, the request kept with our premium."""
    have = next((e for e in entries() if e["scenario"] == scenario), None)
    if have:
        return {**have, "already": True}
    if not request_hash and request is None and not (fixture and response_file):
        raise ValueError("a library entry needs a stored ISO answer (request hash), a fixture, or a request to keep")
    iso = bool(request_hash or fixture)
    e = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": scenario, "line": line, "state": state,
         "origin": origin, "reference": "iso" if iso else "ours", "hash": request_hash, "by": by, "note": note}
    if fixture:
        e.update(fixture=fixture, fixture_file=fixture_file, response_file=response_file)
    if request is not None and (not iso or fixture):         # a fixture keeps its rebuilt request: no corpus path needed
        PAYLOADS.mkdir(parents=True, exist_ok=True)
        f = PAYLOADS / (re.sub(r"[^A-Za-z0-9_.-]", "_", scenario) + ".json")
        f.write_text(json.dumps(request, indent=1), encoding="utf-8")
        e["request_file"] = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else str(f)
        if not iso:
            e["ours"] = None if ours is None else str(ours)
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(e) + "\n")
    return e
