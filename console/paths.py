"""The rating paths per line, the coverages they count toward, and which states file them (TC-09).

Read from `console/config/paths.json` (built by `scripts/tc/tc09_build_paths.py` from TC-05's census). Configuration,
not code: when ISO's content changes, the file is regenerated, not this module.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "config" / "paths.json"


@lru_cache(maxsize=1)
def config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def lines() -> list:
    return list(config()["lines"])


def coverages(line: str) -> list:
    return list(config()["lines"][line]["coverages"])


def paths(line: str, coverage: str | None = None) -> dict:
    """path id -> {label, coverages}, optionally only those counting toward `coverage`."""
    allp = config()["lines"][line]["paths"]
    return {k: v for k, v in allp.items() if coverage is None or coverage in v["coverages"]}


def states(line: str) -> list:
    return sorted(config()["lines"][line]["states"])


def applies(line: str, state: str, path_id: str) -> tuple[bool, str]:
    """(applies, reason). A path absent from the state's census does not apply."""
    v = config()["lines"][line]["states"].get(state, {}).get(path_id)
    if v is None:
        return False, "not in the census for this state"
    return (v.startswith("applies"), "" if v == "applies" else v.split(":", 1)[-1].strip())


def in_scope(line: str, state: str, coverage: str) -> list:
    """The coverage's paths that apply in this state (the cell's denominator before descoping)."""
    return [p for p in paths(line, coverage) if applies(line, state, p)[0]]
