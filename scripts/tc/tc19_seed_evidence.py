#!/usr/bin/env python3
"""TC-19: seed the console's evidence (`results/tc/evidence.jsonl`) from the ISO answers already held. No ISO calls.

Every stored answer is re-rated on **today's** engine (free) so the matrix says where the engine stands now, against
the answer ISO gave then:

  * **CP**: every rated answer in the reference index whose request we can rebuild -- the request file it was sent
    as, or, for ISO's STC fixtures, the request `157_` sends. Our rating's path signature (`console.signature`) is
    what it walked; every `Premium` and `ErcCalculatedTotalPremium` is compared with ISO's as `157_` does. The record
    carries the policy totals, or, when the totals agree and a part does not, the worst-differing field (named in
    `field`), so a hidden difference is never recorded as agreement.
  * **GL**: every compared row in the run store (the QA runs): the config rebuilt for that state and date
    (`variants.build`, as `sweep.py` does), re-rated, its trace's signature; ISO's premium from the row. The latest run
    per (config, state, date) stands; a row the run marked INERT VALUE counts toward nothing (D15).

Answers we cannot re-rate (344 CP responses kept without their request; ISO refusals) add no evidence and are counted
in the report. A rating our engine refuses or stops on is kept with no paths and an `error`, and counted.

Each record is dated with the answer's own date, so agreement over time (D18) is history, not the day of seeding.
Re-running appends a fresh record per scenario (the latest wins).

    python scripts/tc/tc19_seed_evidence.py [--workers 6] [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

REPORT = ROOT / "results" / "tc" / "tc19_seed_report.json"
STC = re.compile(r"fixture (STC_CP\d+)")
GL_COMPARED = ("MATCH", "DIFF", "PREMIUM ONLY", "ENGINE STOPPED")

_W: dict = {}


def _dec(v):
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


# ---- CP -------------------------------------------------------------------------------------------------------------

def _cp_init():
    from importlib import import_module
    _W["cmp"] = import_module("154_chunk13_rc5_fields_messages")
    _W["r157"] = import_module("157_chunk14_c14-02_total_replay")
    from console import signature
    _W["sig"] = signature


def cp_task(t: dict) -> dict:
    if not _W:
        _cp_init()
    cmp, r157, sig = _W["cmp"], _W["r157"], _W["sig"]
    out = {"scenario": f"CP-{t['state']}-{t['hash'][:10]}", "line": "CP", "state": t["state"], "hash": t["hash"],
           "at": t["at"], "source": t["source"]}
    try:
        data, _ = cmp.rate(t["request"])
    except Exception as exc:                                  # noqa: BLE001 -- our refusal where ISO rated
        return {**out, "walked": [], "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    resp = json.loads(Path(t["response"]).read_text(encoding="utf-8"))
    iso, ours = r157.iso_prem(resp), r157.our_prem(data)
    total = "CommercialProperty[0]/ErcCalculatedTotalPremium"
    diffs = [(k, v, ours.get(k)) for k, v in iso.items() if not cmp.same(v, ours.get(k))]
    rec = {**out, "walked": sorted(sig.cp_signature(data)), "fields": len(iso), "differ": len(diffs)}
    it, ot = iso.get(total), ours.get(total)
    if not diffs:
        return {**rec, "iso": str(it if it is not None else 0), "ours": str(ot if ot is not None else it or 0)}
    if it is not None and not cmp.same(it, ot):
        return {**rec, "iso": str(it), "ours": str(ot if ot is not None else 0), "field": total}
    k, iv, ov = max(diffs, key=lambda d: abs((_dec(d[1]) or 0) - (_dec(d[2]) or 0)))
    return {**rec, "iso": str(iv), "ours": str(ov if ov is not None else 0), "field": k}


def cp_tasks(limit: int | None) -> tuple[list, dict]:
    from console import store
    idx = store.load()
    r157 = __import__("importlib").import_module("157_chunk14_c14-02_total_replay")
    fixtures = None
    tasks, skipped = [], {"refused": 0, "no_request": 0, "no_response": 0}
    for e in idx["references"]:
        if e["line"] != "CP":
            continue
        if e["outcome"] != "rated":
            skipped["refused"] += 1
            continue
        resp = [f for f in e["files"] if f.endswith("_response.json")]
        if not resp:
            skipped["no_response"] += 1
            continue
        reqf = [f for f in e["files"] if f.endswith("_request.json")]
        if reqf:
            req = json.loads((ROOT / reqf[0]).read_text(encoding="utf-8"))
        else:
            m = STC.search(e.get("note", ""))
            if not m:
                skipped["no_request"] += 1
                continue
            if fixtures is None:
                fixtures = r157.fixture_index()
            fx = fixtures.get(m.group(1))
            if fx is None:
                skipped["no_request"] += 1
                continue
            d = json.loads(fx.read_text(encoding="utf-8-sig"))
            req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                         "EffectiveDateTime": e["date"] + "T00:00:00"},
                                          "CommercialProperty": d["CommercialProperty"]}}
        tasks.append({"hash": e["hash"], "state": e["state"], "at": e.get("stored_at") or "", "request": req,
                      "response": str(ROOT / resp[-1]), "source": ", ".join(Path(f).name for f in resp)})
    tasks.sort(key=lambda t: t["at"])
    return (tasks[:limit] if limit else tasks), skipped


# ---- GL -------------------------------------------------------------------------------------------------------------

def gl_task(t: dict) -> dict:
    import variants as V
    from console import signature
    from gl_engine.rating import Kernel
    if "kernel" not in _W:
        _W["kernel"] = {}
    k = _W["kernel"].setdefault(t["mode"], Kernel(mode=t["mode"]))
    out = {"scenario": f"GL-{t['state']}-{t['fingerprint']}-{t['asof']}", "line": "GL", "state": t["state"],
           "hash": t["hash"], "at": t["at"], "source": f"run {t['run']}", "inert": t["inert"]}
    try:
        d = V.Declared(t["state"], t["asof"], t.get("version"))
        payload = V.build(t["config"], d)
        r = k.rate(payload, version=t.get("version"))
    except Exception as exc:                                  # noqa: BLE001
        return {**out, "walked": [], "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    if not r.complete:
        return {**out, "walked": [], "error": f"engine stopped: {str(r.stopped)[:160]}", "iso": t["iso"]}
    rec = {**out, "walked": sorted(signature.gl_signature(r)), "ours": str(r.premium), "iso": t["iso"],
           "ours_then": t["ours_then"], "run_status": t["status"]}
    # The run kept ISO's premium, not the request it sent; the request is rebuilt here with today's `variants`. When
    # today's rebuild rates differently from what the run recorded for us, the request (or our engine) has moved and
    # ISO's old answer cannot vouch for this one: keep it as engine-only evidence, saying why. (Found in RC-3: the
    # 2027-04-01 runs predate OI-97's stopgap, which now adds ProdsCompldOpsExclusion to the rebuilt request.)
    if t.get("ours_then") is not None and _dec(t["ours_then"]) != r.premium:
        rec.update(iso=None, not_comparable=f"rebuilt request rates {r.premium}, the run recorded {t['ours_then']} "
                                            f"for ISO's {t['iso']}: the request has changed since (OI-97's stopgap?)")
    return rec


def gl_tasks(limit: int | None) -> tuple[list, dict]:
    import glob
    latest: dict = {}
    skipped = {"not_compared": 0, "no_iso": 0}
    for f in sorted(glob.glob(str(ROOT / "results" / "runs-*.jsonl"))):
        for raw in Path(f).read_text(encoding="utf-8").splitlines():
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            s = line.get("summary") or {}
            if not s.get("compared"):
                continue
            inert = set(s.get("inert_value") or [])
            for r in line.get("rows") or []:
                if r.get("status") not in GL_COMPARED:
                    skipped["not_compared"] += 1
                    continue
                if r.get("iso") in (None, ""):
                    skipped["no_iso"] += 1
                    continue
                asof = r.get("asof") or s.get("asof", "")
                cfg = {**(s.get("config") or {}), **(r.get("resolved") or {})}
                key = (s.get("fingerprint"), r["juris"], asof)
                t = {"state": r["juris"], "asof": asof, "version": r.get("package_version"), "config": cfg,
                     "mode": s.get("mode") or "strict-erc", "iso": str(r["iso"]), "ours_then": r.get("ours"),
                     "status": r.get("status"), "run": line.get("id"), "at": line.get("at_iso") or "",
                     "fingerprint": s.get("fingerprint", ""), "hash": f"gl:{line.get('id')}:{r['juris']}",
                     "inert": r["juris"] in inert}
                if key not in latest or t["at"] >= latest[key]["at"]:
                    latest[key] = t
    tasks = sorted(latest.values(), key=lambda t: t["at"])
    return (tasks[:limit] if limit else tasks), skipped


# ---- GL full answers (every call the ledger saved, D21) ----------------------------------------------------------

def gl_answer_task(t: dict) -> dict:
    from console import signature
    from gl_engine.rating import Kernel
    if "kernel" not in _W:
        _W["kernel"] = {}
    k = _W["kernel"].setdefault("strict-erc", Kernel(mode="strict-erc"))
    out = {"scenario": f"GL-{t['state']}-{t['hash'][:10]}", "line": "GL", "state": t["state"], "hash": t["hash"],
           "at": t["at"], "source": t["source"]}
    req = json.loads(Path(t["request"]).read_text(encoding="utf-8"))
    resp = json.loads(Path(t["response"]).read_text(encoding="utf-8"))
    iso = ((resp.get("Body") or {}).get("GeneralLiability") or [{}])[0].get("Premium")
    try:
        r = k.rate(req)
    except Exception as exc:                                  # noqa: BLE001
        return {**out, "walked": [], "error": f"{type(exc).__name__}: {str(exc)[:160]}", "iso": iso}
    if not r.complete:
        return {**out, "walked": [], "error": f"engine stopped: {str(r.stopped)[:160]}", "iso": iso}
    return {**out, "walked": sorted(signature.gl_signature(r)), "ours": str(r.premium), "iso": str(iso)}


def gl_answer_tasks(limit: int | None) -> tuple[list, dict]:
    from console import store
    tasks, skipped = [], {"refused": 0, "no_files": 0}
    for e in store.load()["references"]:
        if e["line"] != "GL":
            continue
        if e["outcome"] != "rated":
            skipped["refused"] += 1
            continue
        req = next((f for f in e["files"] if f.endswith("_request.json")), None)
        resp = [f for f in e["files"] if f.endswith("_response.json")]
        if not (req and resp):
            skipped["no_files"] += 1
            continue
        tasks.append({"hash": e["hash"], "state": e["state"], "at": e.get("stored_at") or "",
                      "request": str(ROOT / req), "response": str(ROOT / resp[-1]),
                      "source": ", ".join(Path(f).name for f in resp)})
    tasks.sort(key=lambda t: t["at"])
    return (tasks[:limit] if limit else tasks), skipped


# ---- run ------------------------------------------------------------------------------------------------------------

def run(fn, tasks, workers, label):
    out, t0 = [], time.monotonic()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fn, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            out.append(f.result())
            if i == 1 or i % 100 == 0 or i == len(futs):
                m, s = divmod(int(time.monotonic() - t0), 60)
                print(f"  [{label} {i}/{len(futs)}  {m}m{s:02d}s]", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 1)))
    ap.add_argument("--limit", type=int, help="first N per line (a trial run)")
    ap.add_argument("--dry-run", action="store_true", help="re-rate and report; write no evidence")
    ap.add_argument("--line", choices=("CP", "GL"), help="one line only")
    ap.add_argument("--only", choices=("gl-answers",), help="just GL's full stored answers (added in RC-3)")
    a = ap.parse_args()
    from console import evidence, ledger

    calls_before = ledger.used()["total"]
    recs, report = [], {"at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if a.only == "gl-answers":
        tasks, skipped = gl_answer_tasks(a.limit)
        print(f"GL full answers: {len(tasks)} to re-rate; skipped {skipped}")
        recs += run(gl_answer_task, tasks, a.workers, "GL answers")
        report["GL"] = {"tasks": len(tasks), "skipped": skipped, "only": "gl-answers"}
    if a.only is None and a.line in (None, "GL"):
        tasks, skipped = gl_tasks(a.limit)
        print(f"GL: {len(tasks)} compared rows to re-rate (latest per config, state and date); skipped {skipped}")
        recs += run(gl_task, tasks, a.workers, "GL")
        report["GL"] = {"tasks": len(tasks), "skipped": skipped}
    if a.only is None and a.line in (None, "CP"):
        tasks, skipped = cp_tasks(a.limit)
        print(f"CP: {len(tasks)} stored answers to re-rate; skipped {skipped}")
        recs += run(cp_task, tasks, a.workers, "CP")
        report["CP"] = {"tasks": len(tasks), "skipped": skipped}

    for line in ("GL", "CP"):
        rs = [r for r in recs if r["line"] == line]
        if not rs:
            continue
        rated = [r for r in rs if "error" not in r]
        agree = [r for r in rated if r.get("iso") is not None and _dec(r.get("ours")) == _dec(r.get("iso"))]
        report[line].update({
            "records": len(rs), "rated": len(rated), "agree": len(agree),
            "differ": sum(1 for r in rated if r.get("iso") is not None) - len(agree),
            "not_comparable": sum(1 for r in rs if r.get("not_comparable")), "engine_refused": len(rs) - len(rated),
            "walked_nothing": sum(1 for r in rated if not r["walked"]),
            "inert": sum(1 for r in rs if r.get("inert")),
            "states": len({r["state"] for r in rs}),
            "examples_differ": [{k: r.get(k) for k in ("scenario", "ours", "iso", "field", "source")}
                                for r in rated if r not in agree][:15],
            "examples_refused": [{k: r.get(k) for k in ("scenario", "error", "source")} for r in rs if "error" in r][:10],
        })
    report["calls_spent"] = ledger.used()["total"] - calls_before
    print(json.dumps({k: {x: y for x, y in v.items() if not x.startswith("examples")} if isinstance(v, dict) else v
                      for k, v in report.items()}, indent=1))
    if not a.dry_run:
        for r in sorted(recs, key=lambda r: r["at"]):
            evidence.add(scenario=r["scenario"], line=r["line"], state=r["state"], walked=r["walked"],
                         ours=r.get("ours") if "error" not in r else None, iso=r.get("iso"),
                         request_hash=r.get("hash", ""), inert=r.get("inert", False), source=r["source"], at=r["at"],
                         seed="TC-19", **{k: r[k] for k in ("field", "error", "differ", "fields", "ours_then", "run_status",
                                                             "not_comparable")
                                         if k in r})
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        rep_file = REPORT.with_name("tc19_seed_report_gl_answers.json") if a.only else REPORT
        rep_file.write_text(json.dumps(report, indent=1), encoding="utf-8")
        print(f"wrote {len(recs)} records to {evidence.STORE.relative_to(ROOT)}; report {rep_file.relative_to(ROOT)}")
    return 0 if report["calls_spent"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
