"""OI-135 — a Property rating must not depend on what the process rated before it.

OI-125's look-ahead rates a copy of the request and maps each written copy back to the submitted node by `id()`.
The copies were held only by the copied tree, so a rule's `Remove` freed some, and a node the pass created later
could take a freed copy's id: a write there blanked an unrelated submitted value. Whether an id was reused depended
on memory layout, so `chunk23_rc3_Z6`'s Personal Property `EQLimitToUse` came out None (ISO: 400000) after some
requests in the same process and not others -- 4 or 5 of the 78 chunk 23 requests, a different few each run.

  A  the look-ahead keeps every copy alive until it has read the writes (the fix, checked directly)
  B  Z6 after each chunk 23 request, a fresh process per pair: always ISO's 400000

    python tests/verify_oi135.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TARGET = "chunk23_rc3_Z6_request.json"
FIELD = "PersonalProperty[0]/EQLimitToUse[0]"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def _snap():
    spec = importlib.util.spec_from_file_location("snap", ROOT / "scripts" / "cf" / "206_snapshot_regression.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _eq(snapshot) -> list:
    return [v for k, v in snapshot["fields"].items() if k.endswith(FIELD)]


def _pair(args):
    sys.path.insert(0, str(ROOT))
    first, target = args
    s = _snap()
    s.rate_one(first)
    return os.path.basename(first), _eq(s.rate_one(target)[1])


def group_a():
    print("\nA  THE LOOK-AHEAD KEEPS ITS COPIES ALIVE")
    # Id reuse cannot be forced on demand, so the fix itself is pinned; B is the behaviour it buys.
    from cf_engine import run_checks
    src = Path(run_checks.__file__).read_text(encoding="utf-8")
    check("A1 ignore_submitted_owned holds every copy it maps by id (`keep.append(c)`)", "keep.append(c)" in src)


def group_b():
    print("\nB  Z6 AFTER EACH CHUNK 23 REQUEST, ONE FRESH PROCESS PER PAIR")
    files = [str(f) for f in _snap().corpus("chunk23")]
    target = next(f for f in files if f.endswith(TARGET))
    with ProcessPoolExecutor(max_workers=int(os.environ.get("ERC_MAX_WORKERS", "2")), max_tasks_per_child=1) as ex:
        got = list(ex.map(_pair, [(f, target) for f in files]))
    bad = [first for first, eq in got if eq != ["400000"]]
    check(f"B1 Z6's EQLimitToUse is ISO's 400000 after every one of the {len(files)} (it was None after 4-5)",
          not bad, ", ".join(bad[:5]))


def main() -> int:
    print("OI-135 -- a rating does not depend on what ran before it")
    group_a()
    group_b()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    for f in FAIL:
        print(f"  FAIL {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
