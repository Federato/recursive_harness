#!/usr/bin/env python3
"""Snapshot regression: did ANY figure move? -- every stored ISO payload, one command, a few minutes.

The full regression (`104_`) re-runs 134 chunk scripts, each re-deriving its own figures; ~45 minutes.
This asks the narrower question an engine change needs first: **did anything the engine writes change?**

It takes every Commercial Property request this project has ever sent ISO (`results/cf-raas/*_request.json`,
each already ISO-checked when it was sent), turns each back into an engine submission, rates it, and records
every premium, rate, factor and on-switch the engine writes, plus the message list (or the refusal, if the
engine raises). `--baseline` saves that; `--check` rates again and lists every field that moved.

It complements `104_`, it does not replace it: `104_` checks figures against the numbers written down
before a change (and ISO); this checks that a change moved nothing it was not meant to. Use it after every
engine change; run `104_` at gates.

    python scripts/cf/206_snapshot_regression.py --baseline [--jobs 8]
    python scripts/cf/206_snapshot_regression.py --check    [--jobs 8] [--only chunk20]
    python scripts/cf/206_snapshot_regression.py --selftest            # proves --check can see a change

Progress streams as [i/n elapsed] lines. `--check` exits 1 if anything moved.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(line_buffering=True)

CORPUS = ROOT / "results" / "cf-raas"
SNAP = CORPUS / "snapshot"
BASELINE = SNAP / "baseline.json.gz"
KEEP_SUFFIX = ("Premium", "Rate", "Factor", "CoverageOnPolicyIndicator", "PremiumIndicator", "LimitToUse")
T0 = time.monotonic()


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def corpus(only=None):
    out = []
    for f in sorted(CORPUS.glob("*_request.json")):
        if only and only not in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = d.get("body", d)
        sk = body.get("SchemeKeys") or {}
        prod = str(sk.get("ProductName", ""))
        if not prod.startswith("Commercial Property ") or "CommercialProperty" not in body:
            continue
        out.append(f)
    return out


def to_engine(node):
    """RaaS JSON -> engine submission: an array of records `X: [...]` becomes `XTable: {X: [...]}`."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if isinstance(v, list) and all(isinstance(x, dict) for x in v):
                out[k + "Table"] = {k: [to_engine(x) for x in v]}
            else:
                out[k] = to_engine(v)
        return out
    if isinstance(node, bool):
        return "true" if node else "false"
    return node


def rate_one(path_str):
    """Worker: rate one stored request, return (name, snapshot)."""
    from cf_engine.config import NULL_ARITHMETIC, ROUNDING
    from cf_engine.iso_reader import as_iso_reads
    from cf_engine.resolve import book_for
    from gl_engine.interp.interpreter import Interpreter
    from gl_engine.interp.tree import Node
    f = Path(path_str)
    d = json.loads(f.read_text(encoding="utf-8"))
    body = d.get("body", d)
    sk = body["SchemeKeys"]
    juris = sk["ProductName"].split()[-1]
    eff = str(sk.get("EffectiveDateTime", "2026-09-17"))[:10]
    asof = eff.replace("-", "")
    snap = {"juris": juris, "asof": asof, "fields": {}, "messages": [], "raised": None}
    try:
        book = book_for(juris, asof)
        as_iso_reads(body["CommercialProperty"], book)   # a once-only record sent as a list (OI-145, OI-150)
        sub = {"EffDate": f"{eff[5:7]}/{eff[8:10]}/{eff[0:4]}",
               "CommercialPropertyTable": {"CommercialProperty": [to_engine(x) for x in body["CommercialProperty"]]}}
        ip = Interpreter(book, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
        tree = Node.from_dict(f"MasterCF{juris}", sub)
        ip.run(tree)
    except Exception as exc:                                   # a refusal is a result too
        snap["raised"] = f"{type(exc).__name__}: {str(exc)[:240]}"
        return f.name, snap
    fields = {}

    def walk(n, path):
        counts = {}
        for c in n.children:
            i = counts.get(c.tag, 0)
            counts[c.tag] = i + 1
            p = f"{path}/{c.tag}[{i}]"
            if c.children:
                walk(c, p)
            elif c.text not in (None, "") and c.tag.endswith(KEEP_SUFFIX):
                fields[p] = c.text
    walk(tree, "")
    snap["fields"] = fields
    snap["messages"] = sorted(str(m) for m in ip.messages)
    return f.name, snap


def rate_all(files, jobs):
    res = {}
    n = len(files)
    with ProcessPoolExecutor(max_workers=jobs, max_tasks_per_child=1) as ex:
        futs = {ex.submit(rate_one, str(f)): f for f in files}
        for i, fut in enumerate(as_completed(futs), 1):
            f = futs[fut]
            try:
                name, snap = fut.result()
            except Exception as exc:
                name, snap = f.name, {"raised": f"worker: {exc}", "fields": {}, "messages": []}
            res[name] = snap
            if i % 25 == 0 or i == n:
                progress(i, n, f"rated {name}")
    return res


def diff(base, now):
    moved = {}
    for name, b in base.items():
        a = now.get(name)
        if a is None:
            continue
        d = []
        if b.get("raised") != a.get("raised"):
            d.append(("RAISED", b.get("raised"), a.get("raised")))
        bf, af = b.get("fields", {}), a.get("fields", {})
        for k in sorted(set(bf) | set(af)):
            if bf.get(k) != af.get(k):
                d.append((k, bf.get(k), af.get(k)))
        if b.get("messages") != a.get("messages"):
            d.append(("MESSAGES", len(b.get("messages", [])), len(a.get("messages", []))))
        if d:
            moved[name] = d
    return moved


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--baseline", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("ERC_MAX_WORKERS", "2")))  # memory-bound machine
    ap.add_argument("--only")
    a = ap.parse_args()
    SNAP.mkdir(parents=True, exist_ok=True)

    if a.selftest:
        base = {"x": {"raised": None, "fields": {"/P[0]/Premium[0]": "261"}, "messages": []}}
        now = {"x": {"raised": None, "fields": {"/P[0]/Premium[0]": "262"}, "messages": []}}
        same = diff(base, base)
        moved = diff(base, now)
        ok = not same and moved == {"x": [("/P[0]/Premium[0]", "261", "262")]}
        print("selftest", "PASS: a moved premium is reported, an unchanged one is not" if ok else f"FAIL {moved} {same}")
        return 0 if ok else 1

    files = corpus(a.only)
    print(f"Snapshot regression -- {len(files)} stored Commercial Property requests, {a.jobs} at a time")
    now = rate_all(files, a.jobs)
    raised = sum(1 for s in now.values() if s.get("raised"))
    nfields = sum(len(s.get("fields", {})) for s in now.values())
    if a.baseline:
        with gzip.open(BASELINE, "wt", encoding="utf-8") as fh:
            json.dump(now, fh)
        print(f"BASELINE saved: {len(now)} requests, {nfields:,} fields, {raised} refusals -> {BASELINE}")
        return 0
    if not BASELINE.exists():
        print("no baseline; run --baseline first")
        return 2
    with gzip.open(BASELINE, "rt", encoding="utf-8") as fh:
        base = json.load(fh)
    missing = [k for k in now if k not in base]
    moved = diff(base, now)
    print(f"\nCHECKED {len(now)} requests, {nfields:,} fields; {len(missing)} not in the baseline (new since)")
    if not moved:
        print("SNAPSHOT CLEAN: nothing moved")
        return 0
    print(f"SNAPSHOT MOVED: {len(moved)} requests changed")
    for name, d in sorted(moved.items())[:40]:
        print(f"  {name}: {len(d)} fields")
        for k, b, x in d[:6]:
            print(f"      {k[-110:]}: {b} -> {x}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
