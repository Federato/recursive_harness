"""The Regression Library's runs (TC-33, TC-34) and the stale refresh (TC-35).

Each library entry (`console.library`) is re-rated on today's engine, free, and compared with its reference:

  * **ISO's answer** (a stored answer by request hash, or one of ISO's STC fixtures with its own response, rebuilt as
    `157_` sends it) -- compared field by field as Trace Diff does (`console.worksheet`). An entry **passes** when
    every premium (`Premium`, `ErcCalculatedTotalPremium`, `157_`'s fields) agrees; it is **clean** when every number
    ISO publishes agrees too. A number other than a premium that differs is reported, not hidden;
  * **our own premium** at promotion (a Workbench scenario ISO never answered, or a sample with no stored answer) --
    regression, not verification, and labelled so.

A run is kept under `results/tc/library_runs/<run>.json` with the build it ran on (the git commit), and writes the
readiness `last_build.json` marker so the matrix recomputes (TC-15's "build" event). Across runs each entry has a
**defect history** (D18): the run its divergence was first seen, the last run it was seen, and whether it is open.

The **stale refresh** (TC-35) lists every stored answer ISO gave on a package no longer in force and queues the ones
whose request is on disk as a plan in the **refresh lane**; GL's premium-level rows hold no request and are listed for
a QA re-run instead.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from decimal import Decimal
from pathlib import Path

from . import library, ledger, readiness, store

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "tc" / "library_runs"
PROGRESS = RUNS / "current.json"
PREMIUM_FIELDS = ("Premium", "ErcCalculatedTotalPremium")


def _p(f) -> Path:
    f = Path(f)
    return f if f.is_absolute() else ROOT / f


def request_for(e: dict, idx: dict | None = None) -> dict:
    """The request an entry re-rates: its kept file, its fixture rebuilt as 157_ sends it, or the stored request."""
    if e.get("request_file"):
        return json.loads(_p(e["request_file"]).read_text(encoding="utf-8"))
    if e.get("fixture"):
        d = json.loads(Path(e["fixture_file"]).read_text(encoding="utf-8-sig"))
        return {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                      "EffectiveDateTime": "2026-09-17T00:00:00"},
                                       "CommercialProperty": d["CommercialProperty"]}}
    ref = (idx or {}).get(e["hash"]) or next((x for x in store.load()["references"] if x["hash"] == e["hash"]), None)
    if ref is None:
        raise KeyError(f"{e['scenario']}: no stored answer {e['hash']}")
    req = next((f for f in ref["files"] if f.endswith("request.json")), None)
    if req is None:
        raise KeyError(f"{e['scenario']}: the request is not on disk")
    return json.loads(_p(req).read_text(encoding="utf-8"))


def reference_for(e: dict, idx: dict | None = None) -> tuple[str, dict | None]:
    """('iso', ISO's response body) | ('ours', None)."""
    if e.get("reference") == "ours":
        return "ours", None
    if e.get("response_file"):
        return "iso", json.loads(_p(e["response_file"]).read_text(encoding="utf-8"))
    ref = (idx or {}).get(e["hash"]) or next((x for x in store.load()["references"] if x["hash"] == e["hash"]), None)
    resp = [f for f in (ref or {}).get("files", []) if f.endswith("_response.json")]
    if not resp:
        return "iso", None
    return "iso", json.loads(_p(resp[-1]).read_text(encoding="utf-8"))


def check(e: dict, idx: dict | None = None) -> dict:
    """Re-rate one entry and compare it with its reference. Never raises."""
    from . import worksheet as W
    out = {"scenario": e["scenario"], "line": e["line"], "state": e["state"]}
    try:
        req = request_for(e, idx)
        kind, resp = reference_for(e, idx)
    except Exception as exc:                                  # noqa: BLE001
        return {**out, "result": "error", "detail": f"{type(exc).__name__}: {exc}"[:240]}
    try:
        tree, trace, ours = W.rate(e["line"], req)
    except Exception as exc:                                  # noqa: BLE001 -- ours refuses
        return {**out, "result": "refused", "detail": f"{type(exc).__name__}: {exc}"[:240]}
    if kind == "ours":
        same = W.same(ours, e.get("ours"))
        return {**out, "result": "pass" if same else "diverged", "ours": ours, "reference": e.get("ours"),
                "against": "ours", "detail": "" if same else f"ours moved: {e.get('ours')} -> {ours}"}
    if resp is None:
        return {**out, "result": "error", "detail": "ISO's answer is not on disk"}
    rows = W.align(e["line"], tree, trace, W.body_of(e["line"], resp))
    num = [r for r in rows if r["kind"] == "number" and r["in_iso"] and r["in_ours"]]
    prem_bad = [r for r in num if r["field"] in PREMIUM_FIELDS and not r["match"]]
    prem_missing = [r for r in rows if r["field"] in PREMIUM_FIELDS and r["in_iso"] and not r["in_ours"]
                    and W._num(r["iso"]) not in (None, 0)]
    other_bad = [r for r in num if r["field"] not in PREMIUM_FIELDS and not r["match"]]
    iso_total = next((r["iso"] for r in rows if r["path"] in ("/CommercialProperty/ErcCalculatedTotalPremium",
                                                             "/GeneralLiability/Premium")), None)
    first = sorted(prem_bad + prem_missing + other_bad, key=lambda r: (r["order"] is None, r["order"] or 0))
    result = "diverged" if (prem_bad or prem_missing) else "fields" if other_bad else "pass"
    return {**out, "result": result, "ours": ours, "reference": None if iso_total is None else str(iso_total),
            "against": "iso", "premiums": sum(1 for r in num if r["field"] in PREMIUM_FIELDS),
            "premiumsDiffer": len(prem_bad) + len(prem_missing), "numbers": len(num), "numbersDiffer": len(other_bad),
            "first": first[0]["id"] if first else None,
            "detail": (f"{first[0]['path']}: ours {first[0]['ours']} vs ISO {first[0]['iso']}" if first else "")[:240]}


def _job(e: dict) -> dict:
    return check(e)


def _build_id() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=10).stdout.strip() or "unknown"
    except Exception:                                         # noqa: BLE001
        return "unknown"


def run(entries: list | None = None, workers: int | None = None, progress: bool = True) -> dict:
    """Re-run the library (zero calls). Writes the run, the progress file while it runs, and the build marker."""
    entries = entries if entries is not None else library.entries()
    rid = time.strftime("%Y%m%d-%H%M%S")
    RUNS.mkdir(parents=True, exist_ok=True)
    n = 1
    while (RUNS / f"{rid}.json").exists():                    # two runs in one second must not overwrite each other
        rid = f"{time.strftime('%Y%m%d-%H%M%S')}-{n}"
        n += 1
    build = _build_id()
    calls_before = ledger.used()["total"]
    RUNS.mkdir(parents=True, exist_ok=True)
    out, t0 = [], time.monotonic()
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 1))

    def note(done):
        if progress:
            PROGRESS.write_text(json.dumps({"run": rid, "build": build, "done": done, "total": len(entries),
                                            "seconds": round(time.monotonic() - t0)}), encoding="utf-8")
    note(0)
    if workers == 1:
        for i, e in enumerate(entries, 1):
            out.append(check(e))
            if i % 10 == 0:
                note(i)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_job, e) for e in entries]
            for i, f in enumerate(as_completed(futs), 1):
                out.append(f.result())
                if i % 10 == 0 or i == len(futs):
                    note(i)
    counts: dict = {}
    for r in out:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    rec = {"run": rid, "build": build, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.monotonic() - t0),
           "entries": len(entries), "counts": counts, "callsSpent": ledger.used()["total"] - calls_before,
           "results": sorted(out, key=lambda r: r["scenario"])}
    (RUNS / f"{rid}.json").write_text(json.dumps(rec), encoding="utf-8")
    readiness.LAST_BUILD.parent.mkdir(parents=True, exist_ok=True)
    readiness.LAST_BUILD.write_text(json.dumps({"run": rid, "build": build, "at": rec["at"], "counts": counts}),
                                    encoding="utf-8")
    if progress and PROGRESS.exists():
        PROGRESS.unlink()
    return rec


def runs() -> list:
    if not RUNS.exists():
        return []
    out = []
    for f in RUNS.glob("2*.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue
    # oldest first by when they ran, then by id (`...-1` after its same-second sibling), not by how file names sort
    return sorted(out, key=lambda r: (r.get("at", ""), len(r["run"]), r["run"]))


def changes() -> dict | None:
    """What changed since the previous run (T8, L6): fixed, newly failing, still failing, newly refusing, and our
    premium moved (pass or fail alike), per scenario both runs hold."""
    rs = runs()
    if len(rs) < 2:
        return None
    a, b = rs[-2], rs[-1]
    prev = {x["scenario"]: x for x in a["results"]}
    bad = ("diverged", "refused", "error")
    out = {"from": {k: a[k] for k in ("run", "build", "at")}, "to": {k: b[k] for k in ("run", "build", "at")},
           "fixed": [], "new": [], "still": [], "newlyRefusing": [], "premiumMoved": [], "added": []}
    for x in b["results"]:
        p = prev.get(x["scenario"])
        if p is None:
            out["added"].append(x["scenario"])
            continue
        if p["result"] in bad and x["result"] not in bad:
            out["fixed"].append(x["scenario"])
        elif p["result"] not in bad and x["result"] in bad:
            out["new"].append(x["scenario"])
        elif x["result"] in bad:
            out["still"].append(x["scenario"])
        if x["result"] == "refused" and p["result"] != "refused":
            out["newlyRefusing"].append(x["scenario"])
        if p.get("ours") is not None and x.get("ours") is not None and str(p["ours"]) != str(x["ours"]):
            out["premiumMoved"].append({"scenario": x["scenario"], "was": p["ours"], "now": x["ours"]})
    return out


def history() -> dict:
    """scenario -> {last, firstSeen, lastSeen, open}: the defect history across runs (D18)."""
    out: dict = {}
    for r in runs():
        for x in r["results"]:
            h = out.setdefault(x["scenario"], {"firstSeen": None, "lastSeen": None})
            bad = x["result"] in ("diverged", "refused", "error")
            if bad:
                h["firstSeen"] = h["firstSeen"] or {"run": r["run"], "build": r["build"], "at": r["at"]}
                h["lastSeen"] = {"run": r["run"], "build": r["build"], "at": r["at"]}
            h["last"] = {**x, "run": r["run"], "build": r["build"], "at": r["at"]}
            h["open"] = bad
    return out


_FX: dict = {}


def _fixture_ref(response_file: str, line: str) -> dict:
    """A fixture's content version and date, from its own response (it is not in the index by hash)."""
    if response_file not in _FX:
        f = _p(response_file)
        try:
            text = f.read_text(encoding="utf-8")
            _FX[response_file] = {"iso_package": store._state_pkg(text, line) or "", "stored_at": store._mtime(f),
                                  "freshness": ""}
        except OSError:
            _FX[response_file] = {}
    return _FX[response_file]


def view() -> dict:
    """The library as the screen shows it: every entry, its reference's content version and date, last result and
    defect history; the last run's summary."""
    idx = {e["hash"]: e for e in store.load()["references"]}
    hist = history()
    rows = []
    for e in library.entries():
        ref = idx.get(e.get("hash") or "") or (_fixture_ref(e["response_file"], e["line"]) if e.get("response_file") else {})
        h = hist.get(e["scenario"], {})
        rows.append({**{k: e.get(k) for k in ("scenario", "line", "state", "origin", "reference", "at", "note")},
                     "contentVersion": ref.get("iso_package") or e.get("iso_package") or "",
                     "verified": ref.get("stored_at") or e.get("verified") or "",
                     "freshness": ref.get("freshness") or e.get("freshness") or "",
                     "last": h.get("last"), "firstSeen": h.get("firstSeen"), "lastSeen": h.get("lastSeen"),
                     "open": h.get("open", False)})
    rs = runs()
    last = rs[-1] if rs else None
    return {"entries": rows, "lastRun": last and {k: last[k] for k in ("run", "build", "at", "seconds", "entries", "counts",
                                                                       "callsSpent")},
            "runs": [{k: r[k] for k in ("run", "build", "at", "counts")} for r in rs[-20:]],
            "changes": changes(),
            "progress": json.loads(PROGRESS.read_text(encoding="utf-8")) if PROGRESS.exists() else None}


# ---- staleness and the refresh lane (TC-35) ------------------------------------------------------------------------

def restale(idx: dict | None = None) -> dict:
    """Recompute every stored answer's freshness against the packages in force now (`store.staleness`), without
    rescanning the files: what a corpus ingest does to the index, and what the gate checks moves exactly."""
    idx = idx or store.load()
    for e in idx["references"] + idx.get("gl_premium_rows", []):
        e["freshness"], e["stale_reason"] = store.staleness(e)
    return idx


def _pkg_key(pkg: str) -> tuple:
    """GL_NY_20260801_V02 -> ('20260801', 2), so two packages of one state compare by date, then version."""
    parts = (pkg or "").split("_")
    try:
        return parts[2], int(parts[3].lstrip("V"))
    except (IndexError, ValueError):
        return "", 0


def remedy(e: dict) -> str:
    """'resend' when our corpus moved past the package ISO answered on (asking again gets the current answer);
    'corpus' when ISO answered on a package newer than any we hold (asking again changes nothing: our corpus needs
    the package -- NY GL's V02 today)."""
    now = store.current_package(e["line"], e["state"], e["date"]) or ""
    return "corpus" if _pkg_key(e.get("iso_package", "")) > _pkg_key(now) else "resend"


def _sendable(e: dict) -> bool:
    return any(f.endswith("request.json") for f in e["files"]) and remedy(e) == "resend"


def stale(idx: dict | None = None) -> dict:
    idx = idx or store.load()
    full = [e for e in idx["references"] if e.get("freshness") == "stale"]
    rows = [e for e in idx.get("gl_premium_rows", []) if e.get("freshness") == "stale"]
    sendable = [e for e in full if _sendable(e)]
    return {"answers": [{**{k: e.get(k) for k in ("hash", "line", "state", "date", "iso_package", "stale_reason", "stored_at")},
                         "remedy": remedy(e)} for e in full],
            "sendable": len(sendable), "corpus": sum(1 for e in full if remedy(e) == "corpus"),
            "premiumRows": [{k: e.get(k) for k in ("hash", "line", "state", "date", "iso_package", "stale_reason", "run")}
                            for e in rows]}


def refresh_plan(by: str = "") -> dict:
    """Queue every stale answer whose request is on disk into the refresh lane, as a plan (spends only when started)."""
    from . import plans as P
    idx = store.load()
    rows = []
    for e in idx["references"]:
        if e.get("freshness") != "stale" or not _sendable(e):
            continue
        req = next(f for f in e["files"] if f.endswith("request.json"))
        rows.append({"state": e["state"], "config": {}, "kind": "refresh", "hash": e["hash"], "request_file": req,
                     "stored": False, "status": "queued", "score": 4, "paths": [], "ours": None, "line": e["line"]})
    if not rows:
        raise ValueError("no stale answer that a re-send would refresh (with its request on disk, and our corpus "
                         "past the package ISO answered on)")
    lines = {r["line"] for r in rows}
    pid = time.strftime("%Y%m%d-%H%M%S") + "-refresh"
    plan = {"id": pid, "name": f"Stale refresh, {len(rows)} answer(s)", "line": "/".join(sorted(lines)),
            "spec": {"refresh": True}, "by": by, "committed_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "queued",
            "lane": "refresh", "thinned": 0, "scenarios": rows, "notApplicable": [], "events": [], "pass3": None}
    P.save(plan)
    return plan
