"""Mismatch categories, their tolerances, and the classifications people make (TC-11; spec §3, D15).

A difference between ours and ISO is **open** until classified. A classified difference **within its tolerance** does
not block Passed; one outside it, or a true engine defect (tolerance zero), or an unclassified one, does.

Classifications are append-only (`results/tc/classifications.jsonl`): reclassifying writes a new line, the latest wins,
the history stays.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "results" / "tc" / "classifications.jsonl"


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    abs_tol: Decimal | None      # dollars, either way
    rel_tol: Decimal | None      # fraction of ISO's premium
    meaning: str


CATEGORIES = (
    Category("rounding", "Rounding ±$1", Decimal(1), None, "ISO's step-level rounding applied at a different step"),
    Category("interpolation", "Interpolation ±0.5%", None, Decimal("0.005"), "a different method between table entries"),
    Category("version_skew", "Version skew", None, None, "a different loss cost or rule version was in effect"),
    Category("input_mapping", "Input mapping", None, None, "the same intent reached ISO and ours as different inputs"),
    Category("raas_anomaly", "RaaS anomaly", None, None, "ISO's service did something its own filing doesn't say"),
    Category("true_engine_defect", "True engine defect", Decimal(0), None, "our interpreter is wrong (tolerance zero)"),
    Category("refusal_vs_narrowing", "Our refusal vs ISO's narrowing", Decimal(0), None,
             "ours says not applicable where ISO rates (pass 3; the OI-91 shape) (D15)"),
)
BY_KEY = {c.key: c for c in CATEGORIES}

#: A scenario whose changed control moved nothing exercised nothing: it counts toward no path (D15).
INERT = "inert"


def within(category: str, ours: Decimal, iso: Decimal) -> bool:
    """Is this difference within the category's tolerance? Categories without a band never are (they need a fix)."""
    c = BY_KEY[category]
    delta = abs(Decimal(ours) - Decimal(iso))
    if c.abs_tol is not None:
        return delta <= c.abs_tol
    if c.rel_tol is not None:
        return Decimal(iso) != 0 and delta / abs(Decimal(iso)) <= c.rel_tol
    return False


def classify(scenario: str, category: str, note: str = "", by: str = "", ours=None, iso=None) -> dict:
    """Record a classification (append-only)."""
    if category not in BY_KEY:
        raise ValueError(f"unknown category {category!r}; one of {sorted(BY_KEY)}")
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": scenario, "category": category, "note": note,
           "by": by, "ours": None if ours is None else str(ours), "iso": None if iso is None else str(iso)}
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def classifications() -> dict:
    """scenario -> its latest classification."""
    out = {}
    if STORE.exists():
        for raw in STORE.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rec = json.loads(raw)
                out[rec["scenario"]] = rec
    return out


def is_open(scenario: str, ours, iso, latest: dict | None = None) -> bool:
    """An open mismatch blocks Passed: unclassified, or classified outside its tolerance."""
    if Decimal(str(ours)) == Decimal(str(iso)):
        return False
    rec = (latest if latest is not None else classifications()).get(scenario)
    if rec is None:
        return True
    return not within(rec["category"], Decimal(str(ours)), Decimal(str(iso)))
