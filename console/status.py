"""The cell-state vocabulary every screen shares (TC-08; design spec §2, the user's D5 for n/a).

Keys, glyphs and colours are fixed; only labels differ by screen (the board says "RaaS-verified", the matrix "Passed").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    key: str
    board: str        # Coverage Board label
    matrix: str       # Readiness Matrix label
    glyph: str
    colour: str
    meaning: str


VERIFIED = State("verified", "RaaS-verified", "Passed", "✓", "#2f7d4f",
                 "every in-scope path RaaS-verified within tolerance; no open mismatches; nothing stale")
INTERNAL = State("internal", "Internal-only pass", "Internal only", "○", "#5b7083",
                 "walked internally; at least one path has no RaaS reference")
MISMATCH = State("mismatch", "Mismatch", "Mismatch", "×", "#b3261e",
                 "at least one open mismatch outside tolerance (any category, unclassified included)")
STALE = State("stale", "Stale", "Stale", "↻", "#a15c00",
              "a reference exists but the content in force has changed since")
UNTESTED = State("untested", "Untested", "Untested", "–", "#8a8f98",
                 "no scenario has walked any path here")
NA = State("na", "n/a", "n/a", "·", "#c5c9cf",
           "the state files no such path (D5); never a gap")

ALL = (VERIFIED, INTERNAL, MISMATCH, STALE, UNTESTED, NA)
BY_KEY = {s.key: s for s in ALL}

#: "Still to test" order (§6, no wave key: D3), most urgent first.
PRIORITY = ("mismatch", "stale", "internal", "untested")

#: What a cell in each state needs next (§6).
NEEDS = {
    "mismatch": "Triage + re-verify",
    "stale": "Refresh stale references",
    "internal": "RaaS pairwise + edges",
    "untested": "Tier 0, then RaaS",
}


def get(key: str) -> State:
    return BY_KEY[key]
