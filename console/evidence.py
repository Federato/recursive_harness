"""What each scenario proved, for the roll-up (TC-15; filled from real runs by TC-19, then by every plan).

One line per scenario in `results/tc/evidence.jsonl`, append-only, the latest line per scenario wins:

    {"scenario": "CP-OH-sample", "line": "CP", "state": "OH", "walked": ["building.group1", ...],
     "ours": "5204", "iso": "5204", "hash": "<request hash>", "inert": false, "at": "...", "source": "..."}

`iso` is ISO's premium, or null when only our engine rated it. Nothing here is a verdict: whether a scenario agrees,
is an open mismatch or is stale is derived when it is read, from the classifications (`console.mismatch`) and the
reference index (`console.store`), so classifying a mismatch or a corpus refresh changes the matrix without
rewriting this file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import mismatch
from .rollup import Evidence

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "results" / "tc" / "evidence.jsonl"


def add(*, scenario: str, line: str, state: str, walked, ours=None, iso=None, request_hash: str = "",
        inert: bool = False, source: str = "", store: Path | None = None) -> dict:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": scenario, "line": line, "state": state,
           "walked": sorted(walked), "ours": None if ours is None else str(ours),
           "iso": None if iso is None else str(iso), "hash": request_hash, "inert": bool(inert), "source": source}
    f = store or STORE
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def records(store: Path | None = None) -> list:
    """The latest record per scenario."""
    f = store or STORE
    out = {}
    if f.exists():
        for raw in f.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rec = json.loads(raw)
                out[rec["scenario"]] = rec
    return list(out.values())


def resolve(rec: dict, latest: dict, freshness: dict) -> Evidence:
    """One record as roll-up evidence: agreement from the classifications, freshness from the reference index."""
    if rec.get("iso") is None or rec.get("ours") is None:
        iso = "none"
    else:
        iso = "open-mismatch" if mismatch.is_open(rec["scenario"], rec["ours"], rec["iso"], latest) else "agree"
    return Evidence(rec["scenario"], set(rec["walked"]), iso,
                    fresh=freshness.get(rec.get("hash") or "", "fresh") != "stale", inert=bool(rec.get("inert")))
