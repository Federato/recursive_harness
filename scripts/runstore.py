"""Every run, kept. The file *is* the long-term view.

One append-only JSON-lines file per month under `results/`. One line per run,
holding the configuration, the summary and every jurisdiction row.

**Append-only, and why.** A results store that is rewritten cannot answer *when
did this start disagreeing* -- the question the visualizations exist for. Nothing
here updates or deletes a line; a corrected run is a new line, and the old one
stays as the record of what was believed at the time.

**Stamped with what produced it**, so a row is interpretable a month later: the
engine version, the as-of date, the mode, whether ISO was called, and the
resolved package ids per jurisdiction. A premium without its rulebook edition is
not evidence.

    import runstore as store
    store.append(summary, rows)
    store.runs()                       # newest first
    store.coverage()                   # controls x jurisdictions ever exercised

**It lives in `scripts/` and not in `ui/`, and that is deliberate.** The run
store is a results store, not an interface concern: the command line writes to
it, the browser writes to it, and the live-call budget in `scripts/qa.py` counts
from it. Keeping it under `ui/` forced `sweep.py` to import the interface in
order to record a run, which inverts the one-way dependency this project
enforces -- `ui -> scripts -> gl_engine`. `tests/verify_tester.py` A5 caught it,
which is the whole reason that assertion exists.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

#: Schema version of a stored line. A reader must be able to tell an old shape
#: from a new one rather than guess from which keys are present.
LINE_VERSION = 1


def _month_file(when: float) -> Path:
    return RESULTS / f"runs-{time.strftime('%Y-%m', time.localtime(when))}.jsonl"


def append(summary: dict, rows: list, engine_version: str = "",
           label: str = "") -> dict:
    """Record one run. Returns the stored line, including its id."""
    now = time.time()
    line = {
        "v": LINE_VERSION,
        "id": f"{time.strftime('%Y%m%dT%H%M%S', time.localtime(now))}"
              f"-{summary.get('fingerprint', 'nofp')}",
        "at": now,
        "at_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "label": label,
        "engine_version": engine_version,
        "summary": summary,
        "rows": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = _month_file(now)
    # Append with a single write. Two concurrent runs must not interleave half
    # a line -- the file is the record and a torn line loses a whole run.
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, default=str) + "\n")
    return line


def _read_all() -> list:
    if not RESULTS.is_dir():
        return []
    out = []
    for p in sorted(RESULTS.glob("runs-*.jsonl")):
        for n, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except ValueError:
                # A torn or hand-edited line is skipped and SAID, not silently
                # dropped -- a results file that quietly loses runs is worse
                # than one that admits a bad line.
                out.append({"v": 0, "id": f"{p.name}:{n}", "at": 0,
                            "unreadable": True, "summary": {}, "rows": []})
    return out


def runs(limit: int = 200, fingerprint: str = "") -> list:
    """Stored runs, newest first, without their rows."""
    out = []
    for line in _read_all():
        if fingerprint and line.get("summary", {}).get("fingerprint") != fingerprint:
            continue
        out.append({k: v for k, v in line.items() if k != "rows"})
    out.sort(key=lambda r: r.get("at", 0), reverse=True)
    return out[:limit]


def run(run_id: str) -> dict | None:
    for line in _read_all():
        if line.get("id") == run_id:
            return line
    return None


def history(fingerprint: str = "") -> list:
    """`[{at_iso, agree, rated, not_applicable, differ, stopped, compared}]`.

    The series the agreement chart draws. Ordered oldest first, because a trend
    read right to left is a trend read wrong.
    """
    out = []
    for line in _read_all():
        s = line.get("summary") or {}
        if fingerprint and s.get("fingerprint") != fingerprint:
            continue
        out.append({
            "id": line.get("id"),
            "at": line.get("at", 0),
            "at_iso": line.get("at_iso", ""),
            "describes": s.get("describes", ""),
            "fingerprint": s.get("fingerprint", ""),
            "compared": bool(s.get("compared")),
            "total": s.get("total", 0),
            "rated": s.get("rated", 0),
            "agree": s.get("agree", 0),
            "differ": len(s.get("differ") or []),
            "not_applicable": len(s.get("not_applicable") or []),
            "stopped": len(s.get("engine_stopped") or []),
            "unmoved": len(s.get("unmoved") or []),
        })
    out.sort(key=lambda r: r["at"])
    return out


def coverage() -> dict:
    """Which controls have ever been exercised, in which jurisdictions.

    **This is the answer to "how narrow is the claim?"** and it is the reason
    the store exists. A control is counted for a jurisdiction only when a run
    that set it actually rated there -- a `NOT APPLICABLE` row proves the
    jurisdiction was asked and declined, which is worth knowing separately and
    is not coverage.
    """
    rated: dict = {}
    declined: dict = {}
    values: dict = {}
    for line in _read_all():
        s = line.get("summary") or {}
        cfg = s.get("config") or {}
        if not cfg:
            continue
        for cid, val in cfg.items():
            values.setdefault(cid, set()).add(str(val))
            for row in line.get("rows") or []:
                j, st = row.get("juris"), row.get("status")
                if not j:
                    continue
                if st in ("RATED", "MATCH", "PREMIUM ONLY", "DIFF"):
                    rated.setdefault(cid, set()).add(j)
                elif st == "NOT APPLICABLE":
                    declined.setdefault(cid, set()).add(j)
    return {
        "rated": {k: sorted(v) for k, v in rated.items()},
        "declined": {k: sorted(v) for k, v in declined.items()},
        "values": {k: sorted(v) for k, v in values.items()},
    }


def response_curve(control_id: str, compared_only: bool = False) -> dict:
    """`{juris: [(value, premium)]}` for one control across every run.

    The premium plotted against the thing that was varied. A jurisdiction whose
    curve kinks where the others do not is a defect you can see before you can
    explain it, which is the whole point of drawing it.
    """
    series: dict = {}
    for line in _read_all():
        s = line.get("summary") or {}
        cfg = s.get("config") or {}
        if control_id not in cfg:
            continue
        if compared_only and not s.get("compared"):
            continue
        # Only runs that varied THIS control alone are comparable; a curve
        # mixing configurations is not a curve.
        if len(cfg) != 1:
            continue
        val = str(cfg[control_id])
        for row in line.get("rows") or []:
            if not row.get("ours"):
                continue
            series.setdefault(row["juris"], {})[val] = {
                "ours": row["ours"], "iso": row.get("iso"),
                "status": row.get("status"),
            }
    return {j: [{"value": v, **d} for v, d in sorted(vals.items())]
            for j, vals in series.items()}


def defects() -> list:
    """Every jurisdiction/config that refused or disagreed, first and last seen.

    A defect that appears, is fixed and reappears must show all three, so this
    reports first-seen, last-seen and the number of runs -- not a current-state
    boolean.
    """
    seen: dict = {}
    for line in _read_all():
        s = line.get("summary") or {}
        at = line.get("at_iso", "")
        for row in line.get("rows") or []:
            st = row.get("status")
            if st not in ("DIFF", "ENGINE STOPPED", "ENGINE ERROR",
                          "BUILD ERROR", "RAAS FAILED", "PREMIUM ONLY"):
                continue
            key = (row.get("juris", ""), st, s.get("fingerprint", ""))
            e = seen.setdefault(key, {
                "juris": key[0], "status": st,
                "fingerprint": key[2], "describes": s.get("describes", ""),
                "first_seen": at, "last_seen": at, "runs": 0,
                "detail": str(row.get("detail") or
                              row.get("first_differences") or "")[:220]})
            e["runs"] += 1
            e["last_seen"] = at
            if at < e["first_seen"]:
                e["first_seen"] = at
    return sorted(seen.values(), key=lambda e: (e["last_seen"], e["juris"]),
                  reverse=True)

# ------------------------------------------------------------- the QA rollup

#: Worst-first. A jurisdiction that disagreed anywhere is reported as
#: disagreeing however much else agreed, because the summary exists to surface
#: the worst thing rather than to average it away.
_RANK = ("differs", "refused", "uncompared", "partial", "agrees", "untested")


def qa_rollup(tier: str = "", limit: int = 60) -> dict:
    """Per-jurisdiction outcome across recent runs, for the map and the verdict.

    Reads whole runs rather than summaries, because the per-jurisdiction status
    is on the rows. `tier` narrows to one tier's runs by label.
    """
    status, counts = {}, {"agrees": 0, "differs": 0, "not_applicable": 0,
                          "refused": 0, "uncompared": 0}
    seen_runs, scenarios, calls = [], 0, 0

    def worse(a, b):
        return a if _RANK.index(a) <= _RANK.index(b) else b

    for meta in runs(limit=limit):
        label = str(meta.get("label") or "")
        if tier and not label.startswith(f"qa {tier}"):
            continue
        if not tier and not label.startswith("qa "):
            continue
        full = run(meta["id"]) or {}
        rows = full.get("rows") or []
        if not rows:
            continue
        scenarios += 1
        calls += int((full.get("summary") or {}).get("live_calls", 0) or 0)
        seen_runs.append(meta["id"])
        for r in rows:
            j, st = r.get("juris"), r.get("status")
            if not j:
                continue
            if st in ("DIFF", "PREMIUM ONLY"):
                here, key = "differs", "differs"
            elif st in ("ENGINE STOPPED", "ENGINE ERROR", "BUILD ERROR",
                        "RAAS FAILED"):
                here, key = "refused", "refused"
            elif st == "MATCH":
                here, key = "agrees", "agrees"
            elif st == "RATED":
                here, key = "uncompared", "uncompared"
            elif st == "NOT APPLICABLE":
                # Never a failure, and never the reason a tile is coloured: it
                # only softens an otherwise-clean jurisdiction to "partial".
                counts["not_applicable"] += 1
                status[j] = worse(status.get(j, "untested"), "partial")
                continue
            else:
                continue
            counts[key] += 1
            status[j] = worse(status.get(j, "untested"), here)

    return {"status": status, "counts": counts, "scenarios": scenarios,
            "live_calls": calls, "runs": len(seen_runs)}
