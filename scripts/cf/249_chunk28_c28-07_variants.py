#!/usr/bin/env python3
"""Chunk 28 C28-07 (set C): OI-126 and OI-123, each candidate reading measured against ISO's messages. No engine change.

OI-126. `Location.SetMultipleDiffDeductibleSpclIndicator` compares each special class item's deductible to the first
one's, falling back to a filed `<Constant></Constant>`. One item, no deductible: ISO says "No", ours "Yes" (one extra
CP 03 20 message, chunk 27 C7nd). Two readings fit ISO:
  A  ISO's `FirstNonNull` returns a filed "" Constant (ours skips "" from every branch)
  B  ISO's `Equal` treats null and "" as equal (ours: a null equals only a null)
A census of CW 2026 V01 (2026-10-05) found no rule that compares a bare field to "": ISO always supplies "" itself
(`FirstValue FromConstant=""`, 893 sites, or a param bound to "" in an `Else`). So no single filed rule separates A from
B; this measures both on everything ISO has rated.

OI-123. ISO's MO build (CW 2023 V02) strips the paths from five `NotExist` tests; ISO fires the message on every flood
location. Candidate:
  C  an `Exist` / `NotExist` with no path selects nothing (Exist false, NotExist true); ours selects the current node

For every stored request ISO rated (a saved `*_response.json`), ours is run as built and under each variant; the
(level, message) multiset is compared with ISO's, and every premium is checked unchanged. Predicted before the run
(2026-10-05): A and B each turn C7nd equal and break nothing; C turns the four MO flood cases equal and breaks nothing.

    python scripts/cf/249_chunk28_c28-07_variants.py [--only chunk27]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

from gl_engine.interp import nodes, tree                                  # noqa: E402

c23 = import_module("221_chunk23_rc3")                    # wraps MessageHelper (TAGGED), iso_tagged
rep, gc, TAGGED, lvl = c23.rep, c23.gc, c23.TAGGED, c23.lvl
OUT = gc.OUT

ORIG = {"FirstNonNull": nodes.EVAL["FirstNonNull"], "Exist": nodes.EVAL["Exist"], "NotExist": nodes.EVAL["NotExist"]}
ORIG_EQUAL = nodes.equal


def fnn_a(ip, el, fr):
    """Reading A: a filed "" Constant branch is returned as "", not skipped. Every other branch as today."""
    for idx, ch in enumerate(nodes._kids(el)):
        if ch.tag.split("}", 1)[-1] == "Constant" and (ch.text or "") == "":
            return ""
        try:
            vals = nodes.flatten(ip.eval(ch, fr))
        except nodes.NullInArithmetic as exc:
            ip.trace_branch_abandoned(el, idx, exc)
            continue
        for v in vals:
            if v is not None and v != "":
                return v
    ip.trace_exhausted(el)
    return None


def equal_b(a, b):
    """Reading B: null and "" are equal."""
    a = None if a == "" else a
    b = None if b == "" else b
    return ORIG_EQUAL(a, b)


def exist_c(ip, el, fr):
    path = el.attrib.get("AtInputDataDef", "")
    return bool(path) and bool(tree.select(path, fr.data))


def not_exist_c(ip, el, fr):
    path = el.attrib.get("AtInputDataDef", "")
    return not path or not tree.select(path, fr.data)


def use(variant):
    nodes.EVAL.update(ORIG)
    nodes.equal = ORIG_EQUAL
    if variant == "A":
        nodes.EVAL["FirstNonNull"] = fnn_a
    elif variant == "B":
        nodes.equal = equal_b
    elif variant == "C":
        nodes.EVAL["Exist"], nodes.EVAL["NotExist"] = exist_c, not_exist_c


def ours(req):
    TAGGED.clear()
    data, ip = rep.cmp.rate(req)
    return collections.Counter((lvl(t), x) for t, x in TAGGED), rep.our_prem(data)


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json"))
                  if Path(f[:-len("_request.json")] + "_response.json").exists() and (not a.only or a.only in Path(f).name))
    variants = ("now", "A", "B", "C")
    equal_n = collections.Counter()
    fixed, broke, moved, raised = (collections.defaultdict(list) for _ in range(4))
    for i, f in enumerate(reqs, 1):
        name = Path(f).name[:-len("_request.json")]
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        resp = json.loads(Path(f[:-len("_request.json")] + "_response.json").read_text(encoding="utf-8"))
        isos = collections.Counter(c23.iso_tagged(resp))
        got = {}
        for v in variants:
            use(v)
            try:
                got[v] = ours(req)
            except Exception as exc:                      # noqa: BLE001 -- counted, never hidden
                got[v] = None
                raised[v].append((name, f"{type(exc).__name__}: {str(exc)[:80]}"))
        use("now")
        if got["now"] is None:
            continue
        base_eq = got["now"][0] == isos
        for v in variants:
            if got[v] is None:
                continue
            eq = got[v][0] == isos
            equal_n[v] += eq
            if v != "now":
                if eq and not base_eq:
                    fixed[v].append(name)
                if base_eq and not eq:
                    broke[v].append(name)
                if got[v][1] != got["now"][1]:
                    moved[v].append(name)
        if i % 200 == 0 or i == len(reqs):
            progress(i, len(reqs), f"messages equal to ISO: " + ", ".join(f"{v} {equal_n[v]}" for v in variants))
    print(f"\n{len(reqs)} stored requests ISO rated; (level, message) multiset equal to ISO:")
    for v in variants:
        print(f"  {v:4s} {equal_n[v]:5d}" + ("" if v == "now" else
              f"   fixed {len(fixed[v])}  broke {len(broke[v])}  premiums moved {len(moved[v])}  raised {len(raised[v])}"))
        for k, lst in (("fixed", fixed[v]), ("broke", broke[v]), ("moved", moved[v]), ("raised", raised[v])):
            for x in lst[:12]:
                print(f"       {k:6s} {x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
