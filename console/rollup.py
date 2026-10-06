"""Path states into coverage cells (TC-13; spec §3, §6; the user's D4 sign-off and D5 n/a).

**A path's state** comes from the scenarios that walked it (`console.signature`):

  * `mismatch`  -- a scenario walking it has an open mismatch with ISO (`console.mismatch.is_open`)
  * `stale`     -- a reference for it was answered on a package no longer in force (`console.store.staleness`)
  * `verified`  -- a scenario walking it agrees with a fresh ISO answer, within tolerance
  * `internal`  -- walked, but only by our engine (no ISO answer)
  * `untested`  -- nothing walked it
  INERT scenarios (D15) count toward nothing.

**A cell** (line, state, coverage) rolls its in-scope paths up, first match wins (§3):
  1. any path `mismatch` -> mismatch;  2. any path `stale` -> stale;  3. no path walked -> untested;
  4. every in-scope path `verified` -> verified (Passed);  5. otherwise internal.
A cell with no in-scope path is **n/a** (D5). A sign-off (D4) is kept only while the cell is Passed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import paths as P


@dataclass
class Evidence:
    """One scenario's bearing on paths: what it walked and how ISO answered."""
    scenario: str
    walked: set
    iso: str            # 'agree' | 'open-mismatch' | 'none' (engine only)
    fresh: bool = True  # False when its ISO reference is stale
    inert: bool = False


def path_status(evs: list) -> str:
    evs = [e for e in evs if not e.inert]
    if not evs:
        return "untested"
    if any(e.iso == "open-mismatch" for e in evs):
        return "mismatch"
    if any(e.iso != "none" and not e.fresh for e in evs):
        return "stale"
    if any(e.iso == "agree" and e.fresh for e in evs):
        return "verified"
    return "internal"


def path_states(line: str, state: str, evidence: list) -> dict:
    """path id -> state, for every path the line has (n/a ones included, as 'na')."""
    out = {}
    for pid in P.paths(line):
        if not P.applies(line, state, pid)[0]:
            out[pid] = "na"
            continue
        out[pid] = path_status([e for e in evidence if pid in e.walked])
    return out


@dataclass
class Cell:
    line: str
    state: str
    coverage: str
    status: str
    in_scope: list
    counts: dict
    est_remaining_calls: int
    signed_off_by: str | None = None
    signed_off_at: str | None = None
    descoped: list = field(default_factory=list)


def cell(line: str, state: str, coverage: str, states: dict, descoped: dict | None = None,
         signoff: dict | None = None) -> Cell:
    """Roll one coverage's paths into its cell. `descoped`: path id -> reason (listed in the cell detail, D5)."""
    descoped = descoped or {}
    scope = [p for p in P.in_scope(line, state, coverage) if p not in descoped]
    st = [states.get(p, "untested") for p in scope]
    counts = {k: st.count(k) for k in ("verified", "internal", "mismatch", "stale", "untested")}
    counts["in_scope"] = len(scope)
    counts["walked"] = len(scope) - counts["untested"]
    if not scope:
        status = "na"
    elif counts["mismatch"]:
        status = "mismatch"
    elif counts["stale"]:
        status = "stale"
    elif counts["walked"] == 0:
        status = "untested"
    elif counts["verified"] == len(scope):
        status = "verified"
    else:
        status = "internal"
    # §6 estimates: unverified paths need a call each (pairwise later shrinks this); stale and mismatched need a re-call
    est = {"mismatch": counts["mismatch"], "stale": counts["stale"]}.get(
        status, counts["internal"] + counts["untested"])
    c = Cell(line, state, coverage, status, scope, counts, 0 if status in ("verified", "na") else est,
             descoped=[{"path": p, "reason": r} for p, r in descoped.items()])
    if signoff and status == "verified":
        c.signed_off_by, c.signed_off_at = signoff.get("by"), signoff.get("at")
    return c


def matrix(line: str, evidence_by_state: dict, signoffs: dict | None = None) -> list:
    """Every (state, coverage) cell for a line. `evidence_by_state`: state -> [Evidence]."""
    signoffs = signoffs or {}
    out = []
    for state in P.states(line):
        ps = path_states(line, state, evidence_by_state.get(state, []))
        for cov in P.coverages(line):
            out.append(cell(line, state, cov, ps, signoff=signoffs.get((line, state, cov))))
    return out


PRIORITY = {"mismatch": 0, "stale": 1, "internal": 2, "untested": 3}


def still_to_test(cells: list) -> list:
    """§6 without the wave key (D3): every cell not Passed and not n/a, by status priority then calls (descending)."""
    todo = [c for c in cells if c.status not in ("verified", "na")]
    return sorted(todo, key=lambda c: (PRIORITY[c.status], -c.est_remaining_calls, c.state, c.coverage))
