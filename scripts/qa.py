"""The QA programme: tiers, a pairwise matrix, a cost estimate and a budget guard.

    python scripts/qa.py --tier T1 --plan        # the matrix, run nothing
    python scripts/qa.py --estimate              # cost of every tier
    python scripts/qa.py --tier T0 --offline     # free, no ISO calls
    python scripts/qa.py --tier T1               # live, budget-checked
    python scripts/qa.py --tiers                 # what the tiers are

Proposed in `docs/qa-plan-proposal_20260817.html`; this is phase 1 of it, and it
is **terminal only** -- no UI, and nothing here knows the UI exists.

### The one design decision worth reading

**Two matrices, not one.** A *value* sweep asks "is every filed rate returned
correctly" and needs no ISO call at all, because ISO's own files are the source
of truth for a rate. A *logic* matrix asks "does the engine behave correctly" and
is small, because the axes turn out to be keyed on one another -- both aggregate
limits are keyed on the occurrence limit, so 11,700 naive limit combinations are
really 464. The naive cross product is 1.94e16 and is quoted in the proposal only
as the argument against itself.

### Why pairwise rather than every combination

Every measured defect so far needed **two** things set at once to appear -- a
deductible *and* a limit, size-of-risk *and* a state whose table is countrywide.
None needed three. All-pairs covers every pair of axis values in a few hundred
scenarios where the cross product needs millions, and `_allpairs` below is a
plain greedy algorithm with no dependency.

### The budget guard is not advisory

Decision A6 (2026-08-17) sets **60 live calls a day standing, 150 absolute**.
`_spent_today` reads the real run store, and a tier that would exceed the
standing budget **refuses to start** rather than warning. `--force` raises it to
the ceiling; nothing raises it past the ceiling.
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sweep                                                   # noqa: E402
import variants as V                                           # noqa: E402
from raas import NO_ISO                                        # noqa: E402
from ui import store                                           # noqa: E402

#: Decision A6, 2026-08-17. Standing budget, then the absolute ceiling.
DAILY_STANDING = 60
DAILY_CEILING = 150

#: Measured 2026-08-17 from the stored run records, not from a constant in the
#: code: the 20s in `ui/tester.py` and `sweep.py` is wrong high.
SECONDS_PER_LIVE_CALL = 8.4
SECONDS_PER_OFFLINE_RATING = 0.5

#: The twelve core jurisdictions, each present for a measured structural reason
#: rather than for size. Documented in the proposal, section 4.8.
CORE = ("NY", "CA", "NJ", "OH", "TX", "FL", "PA", "GA", "RI", "MT", "WY", "DE")

WHY_CORE = {
    "NY": "20 territories; only Special Protective subline; no claims-made form",
    "CA": "own countrywide parent; loss costs in split sibling tables",
    "NJ": "own countrywide parent; base loss-cost table has zero rows",
    "OH": "base loss-cost table has zero rows (OI-69)",
    "TX": "own countrywide parent; territory by county and place",
    "FL": "territory by county and place; schedule rating applies here",
    "PA": "11 territories; declares territory 506 with no ZIP and no rate",
    "GA": "files no deductible factors of its own -- tests the layering",
    "RI": "one of three states where schedule rating moves the premium",
    "MT": "single territory; files no terrorism location",
    "WY": "single territory; files no terrorism location",
    "DE": "territory scheme visible only under a fifth table name",
}

# --------------------------------------------------------------------- axes

#: Axis values chosen to span the *shape* of each domain rather than to
#: enumerate it. Deductibles are three structural cases, not a grid: 960 of the
#: 961 (BI, PD) pairs admit only `No Deductible` as the combined value.
AXES = {
    "occurrence_limit": ["100,000 CSL", "500,000 CSL", "1,000,000 CSL",
                         "5,000,000 CSL"],
    "premops_pd_deductible": ["No Deductible", "1,000 Per Occurrence",
                              "5,000 Per Occurrence"],
    "prods_pd_deductible": ["No Deductible", "2,000 Per Occurrence"],
    "size_of_risk": ["No", "Yes"],
    "terrorism": ["No", "Yes"],
    "locations": [1, 2],
}

#: Run alongside the pairwise set rather than inside it: each needs a partner
#: control set in the same scenario, so pairing them independently would
#: produce configurations that are legal and inert.
PAIRED = [
    {"schedule_rating": "Yes", "schedule_pct": "10%"},
    {"schedule_rating": "Yes", "schedule_pct": "-10%"},
    {"coverage_form": "Claims Made", "claims_made_year": 1},
    {"coverage_form": "Claims Made", "claims_made_year": 4},
    {"premops_bipd_deductible": "1,000 Per Occurrence"},
]


def _allpairs(axes: dict) -> list:
    """Every pair of axis values covered, greedily, with no dependency.

    Not minimal -- a minimal covering array needs a solver. It is typically
    within a third of optimal, deterministic, and short enough to read.
    """
    names = list(axes)
    need = set()
    for a, b in itertools.combinations(names, 2):
        for va in axes[a]:
            for vb in axes[b]:
                need.add((a, va, b, vb))

    out = []
    while need:
        best, best_cover = None, -1
        # Seed each candidate from an uncovered pair, then fill greedily.
        a, va, b, vb = sorted(need)[0]
        for _ in range(1):
            cand = {a: va, b: vb}
            for n in names:
                if n in cand:
                    continue
                pick, pick_cover = axes[n][0], -1
                for v in axes[n]:
                    cover = sum(
                        1 for m, mv in cand.items()
                        if (min(m, n), (mv if m < n else v), max(m, n),
                            (v if m < n else mv)) in need)
                    if cover > pick_cover:
                        pick, pick_cover = v, cover
                cand[n] = pick
            cover = 0
            for x, y in itertools.combinations(names, 2):
                if (x, cand[x], y, cand[y]) in need:
                    cover += 1
            if cover > best_cover:
                best, best_cover = cand, cover
        for x, y in itertools.combinations(names, 2):
            need.discard((x, best[x], y, best[y]))
        out.append(best)
    return out


def _clean(cfg: dict) -> dict:
    """Drop no-op values so a scenario is described by what it actually sets."""
    return {k: v for k, v in cfg.items()
            if not (k in ("size_of_risk", "terrorism") and v == "No")
            and not (k == "locations" and v == 1)
            and not (k.endswith("deductible") and v == "No Deductible")}


# -------------------------------------------------------------------- tiers

def tier_t0():
    return [({}, None)]


def tier_t1():
    out = [(c, CORE) for c in (_clean(x) for x in _allpairs(AXES)) if c]
    out += [(dict(p), CORE) for p in PAIRED]
    return [({}, CORE)] + out


def tier_t2():
    return [(c, None) for c, _ in tier_t1()]


def tier_t4():
    return [(c, CORE) for c, _ in tier_t1()]


TIERS = {
    "T0": {"name": "Smoke", "build": tier_t0, "live": True,
           "what": "the base risk, unvaried, in every jurisdiction"},
    "T1": {"name": "Core logic", "build": tier_t1, "live": True,
           "what": "pairwise over limits, deductibles, size-of-risk, terrorism "
                   "and locations, in the 12 structurally-chosen states"},
    "T2": {"name": "Full logic", "build": tier_t2, "live": True,
           "what": "the T1 matrix across all 51 jurisdictions"},
    "T3": {"name": "Value sweep", "build": None, "live": False,
           "what": "every filed rate cell -- 278,054 -- offline, no ISO calls. "
                   "NOT BUILT: needs the per-class payload builder"},
    "T4": {"name": "Edition cliff", "build": tier_t4, "live": True,
           "what": "the T1 matrix at both sides of 2027-04-01. NOT RUNNABLE "
                   "until the as-of probe answers (decision A3)"},
}


# ------------------------------------------------------------------- budget

def _spent_today() -> int:
    """Live calls already made today, read from the real run store."""
    today = dt.date.today().isoformat()
    n = 0
    for r in store.runs(limit=500):
        at = (r.get("at_iso") or "")[:10]
        if at == today:
            n += int((r.get("summary") or {}).get("live_calls", 0) or 0)
    return n


def _budget_check(calls: int, force: bool) -> tuple:
    spent = _spent_today()
    cap = DAILY_CEILING if force else DAILY_STANDING
    room = cap - spent
    ok = calls <= room
    why = (f"{spent} live calls already spent today; "
           f"{'ceiling' if force else 'standing budget'} is {cap}, "
           f"so {max(0, room)} remain")
    return ok, room, why


# -------------------------------------------------------------------- plans

def scenarios_for(tier: str, jurisdictions=None):
    spec = TIERS[tier]
    if spec["build"] is None:
        return []
    out = []
    for cfg, js in spec["build"]():
        js = list(jurisdictions or js or V.Declared.jurisdictions())
        out.append((cfg, js))
    return out


def cost(tier: str, jurisdictions=None, offline: bool = False) -> dict:
    sc = scenarios_for(tier, jurisdictions)
    ratings = sum(len(js) for _, js in sc)
    live = 0 if offline else sum(
        len([j for j in js if j not in NO_ISO]) for _, js in sc)
    return {
        "tier": tier, "scenarios": len(sc), "ratings": ratings,
        "live_calls": live,
        "offline_seconds": round(ratings * SECONDS_PER_OFFLINE_RATING),
        "live_seconds": round(live * SECONDS_PER_LIVE_CALL),
    }


def _hm(seconds: float) -> str:
    s = int(seconds)
    h, m = divmod(s // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m} min"


# --------------------------------------------------------------------- main

def main(argv) -> int:
    ap = argparse.ArgumentParser(
        description="QA tiers for the GL rating engine.")
    ap.add_argument("--tier", choices=sorted(TIERS))
    ap.add_argument("--juris", action="append", default=[])
    ap.add_argument("--offline", action="store_true",
                    help="rate through our engine only; no ISO calls")
    ap.add_argument("--plan", action="store_true",
                    help="print the matrix and run nothing")
    ap.add_argument("--estimate", action="store_true",
                    help="cost every tier and run nothing")
    ap.add_argument("--tiers", action="store_true", help="describe the tiers")
    ap.add_argument("--force", action="store_true",
                    help=f"raise the daily budget from {DAILY_STANDING} to the "
                         f"{DAILY_CEILING} ceiling. Never above it")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)

    if a.tiers:
        print("QA tiers\n")
        for k in sorted(TIERS):
            t = TIERS[k]
            print(f"  {k}  {t['name']}")
            print(f"      {t['what']}")
        print(f"\n  The core {len(CORE)} jurisdictions, and why each is in:")
        for j in CORE:
            print(f"      {j}   {WHY_CORE[j]}")
        return 0

    if a.estimate:
        print(f"Cost per tier   (live {SECONDS_PER_LIVE_CALL}s, offline "
              f"{SECONDS_PER_OFFLINE_RATING}s, measured 2026-08-17)\n")
        print(f"  {'tier':5s} {'scenarios':>10s} {'ratings':>9s} "
              f"{'ISO calls':>10s} {'live time':>11s} {'offline':>9s}")
        for k in sorted(TIERS):
            if TIERS[k]["build"] is None:
                print(f"  {k:5s} {'--':>10s} {'--':>9s} {'--':>10s} "
                      f"{'--':>11s} {'--':>9s}   not built")
                continue
            c = cost(k, a.juris or None, a.offline)
            print(f"  {k:5s} {c['scenarios']:>10,} {c['ratings']:>9,} "
                  f"{c['live_calls']:>10,} {_hm(c['live_seconds']):>11s} "
                  f"{_hm(c['offline_seconds']):>9s}")
        spent = _spent_today()
        print(f"\n  Spent today: {spent} of {DAILY_STANDING} standing "
              f"({DAILY_CEILING} ceiling). Remaining: "
              f"{max(0, DAILY_STANDING - spent)}")
        return 0

    if not a.tier:
        ap.print_help()
        return 2

    spec = TIERS[a.tier]
    if spec["build"] is None:
        print(f"{a.tier} ({spec['name']}) is not built.\n  {spec['what']}")
        return 2

    sc = scenarios_for(a.tier, a.juris or None)
    c = cost(a.tier, a.juris or None, a.offline)

    print(f"QA {a.tier} -- {spec['name']}")
    print(f"  {spec['what']}\n")
    print(f"  scenarios      : {c['scenarios']:,}")
    print(f"  engine ratings : {c['ratings']:,}   ({_hm(c['offline_seconds'])})")
    print(f"  ISO calls      : {c['live_calls']:,}"
          + (f"   ({_hm(c['live_seconds'])})" if c["live_calls"] else
             "   offline"))

    if a.plan:
        print("\n  the matrix:")
        for i, (cfg, js) in enumerate(sc, 1):
            where = "all" if len(js) > len(CORE) else " ".join(js)
            print(f"    {i:3d}  {V.describe(cfg) or 'the base risk, unvaried'}")
            print(f"         -> {len(js)} jurisdictions: {where[:88]}")
        print("\n  nothing was run.")
        return 0

    if not a.offline:
        ok, room, why = _budget_check(c["live_calls"], a.force)
        print(f"\n  budget: {why}")
        if not ok:
            print(f"\n  REFUSED. This tier needs {c['live_calls']} calls and "
                  f"{max(0, room)} remain today.")
            print(f"  Run with --offline (free), narrow with --juris, or "
                  f"--force to use the {DAILY_CEILING} ceiling.")
            return 1

    started = time.time()
    runs, agree, differ, na, stopped = [], 0, 0, 0, 0
    for i, (cfg, js) in enumerate(sc, 1):
        desc = V.describe(cfg) or "the base risk, unvaried"
        print(f"\n  [{i}/{len(sc)}] {desc}")
        out = sweep.run_config(cfg, js, compare=not a.offline)
        s = out["summary"]
        agree += s["agree"]
        differ += len(s["differ"]) + len(s["premium_only"])
        na += len(s["not_applicable"])
        stopped += len(s["engine_stopped"])
        store.append(s, out["rows"], label=a.label or f"qa {a.tier}")
        runs.append(s)
        bits = [f"rated {s['rated']}/{s['total']}"]
        if not a.offline:
            bits.append(f"agree {s['agree']}")
        if s["differ"]:
            bits.append(f"DIFFER {','.join(s['differ'])}")
        if s["not_applicable"]:
            bits.append(f"n/a {len(s['not_applicable'])}")
        if s["engine_stopped"]:
            bits.append(f"refused {len(s['engine_stopped'])}")
        print(f"        {' | '.join(bits)}")

    calls = sum(r["live_calls"] for r in runs)
    print(f"\n  {a.tier} complete in {_hm(time.time() - started)}")
    print(f"    scenarios run     : {len(runs)}")
    if not a.offline:
        print(f"    agree with ISO    : {agree}")
    print(f"    disagree          : {differ}")
    print(f"    not applicable    : {na}   (a third outcome, never a failure)")
    print(f"    engine refused    : {stopped}")
    print(f"    ISO calls spent   : {calls}   "
          f"(today: {_spent_today()} of {DAILY_STANDING})")
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
