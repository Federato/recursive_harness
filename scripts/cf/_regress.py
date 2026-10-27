"""Regression-mode sampling for the slow exhaustive scripts.

The full regression (`104_`) sets `CF_REGRESSION_SAMPLE=1` for its regular tier. A script that sweeps a
large grid (answer combinations, all 46 states, every stored response) then runs every k-th item plus the
first and the last, instead of all of them. `104_ --gate` leaves the variable unset, so every chunk gate
still runs each grid in full. Run directly, a script always runs in full.

The sample is deterministic (same items every run), keeps both ends of the grid, and is never smaller
than `floor` items, so a run that passed yesterday checks the same cases today.
"""
from __future__ import annotations

import os

SAMPLED = os.environ.get("CF_REGRESSION_SAMPLE") == "1"


def sample(seq, every: int = 4, floor: int = 8):
    """Every `every`-th item plus the last, when sampling is on; the whole sequence otherwise."""
    items = list(seq)
    if not SAMPLED or len(items) <= max(floor, every * 2):
        return items
    idx = sorted(set(range(0, len(items), every)) | {len(items) - 1})
    return [items[i] for i in idx]


def note(total: int, used: int) -> str:
    """One line a sampled script prints, so its log says it was sampled."""
    return (f"(regression sample: {used} of {total}; the full grid runs at gates)"
            if used < total else "")
