"""OI-141: a `Schema` no longer outlives its use; `app.py` answering request after request stays flat.

  A  `Schema.legal_values` keeps its answers on the schema (`_legal`), not in a module-level cache that holds every
     schema it has seen; the same answer twice is the same object
  B  `app.rate` answering the package samples three times over: the `Schema` and `ResolvedBook` objects alive stay
     constant from the second round on, and memory stays within 60 MB (it grew ~3.6 MB an answer before)

The byte-for-byte check of `app.rate` before and after (118 answers: 51 package samples in both modes, 10 refusals,
3 carriers with and without technical) was run when the fix was made (2026-10-20).

Run: python tests/verify_oi141.py
"""
from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import psutil  # noqa: E402

import app  # noqa: E402
from gl_engine.resolve import ResolvedBook  # noqa: E402
from gl_engine.schema import Schema  # noqa: E402

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


subs = sorted((ROOT / "Engine_Payloads").glob("*/submission.json"))
payloads = [json.loads(p.read_text(encoding="utf-8-sig")) for p in subs]

print("A  legal values kept on the schema")
r = app.KERNELS[app.STRICT].rate(payloads[0])
s = Schema.for_book(ResolvedBook(app.RESOLVER.resolve(r.juris, r.asof)))
f = next(x for x in s if x.domain)
first = s.legal_values(f.table, f.column)
check(not hasattr(Schema.legal_values, "cache_info") and s.legal_values(f.table, f.column) is first
      and (f.table, f.column) in s._legal, f"{f.table}.{f.column}: {len(first)} values, kept on the schema")
del s, r

print("B  app.rate over and over")


def alive(cls):
    gc.collect()
    return sum(1 for o in gc.get_objects() if isinstance(o, cls))


mb = lambda: psutil.Process().memory_info().rss / 2 ** 20  # noqa: E731
rounds = []
for k in range(3):
    for p in payloads:
        app.rate(p, app.STRICT, "ROUND_HALF_UP")
    rounds.append((alive(Schema), alive(ResolvedBook), mb()))
(s1, b1, m1), (s3, b3, m3) = rounds[0], rounds[-1]
check(s3 <= s1 and b3 <= b1 and m3 - m1 < 60,
      f"{len(payloads)} answers a round, 3 rounds: Schema alive {[x[0] for x in rounds]}, ResolvedBook alive "
      f"{[x[1] for x in rounds]}, memory {[round(x[2]) for x in rounds]} MB")

fails = [label for ok, label in results if not ok]
print(f"\n{'PASS' if not fails else 'FAIL'}: {len(results) - len(fails)} of {len(results)}")
sys.exit(1 if fails else 0)
