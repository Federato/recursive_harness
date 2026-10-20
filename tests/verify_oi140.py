"""OI-140: the `/api/rate` answer is built in `console/rate_answer.py`, and `app.py` returns what it returned before.

  A  `app.py` keeps every name it had (`_subline_premiums`, `_chain`, `_rating`, `_factors`, `_is_stat`,
     `FACTOR_KINDS`, `MILESTONES`), the same objects as `console.rate_answer`'s
  B  importing `console.rate_answer` makes no `Kernel` (`app.py` makes two when it loads)
  C  `answer` on a kernel's rating equals `app.rate` for the same request: every package sample in `Engine_Payloads`,
     both modes; a carrier request with and without its technical rating
  D  the comparison with ISO lands where it did: with `compare`, `iso` comes after `deviation` / `payloads` /
     `technical` and before `premium` (a stand-in comparison, no call to ISO), technical compared on a carrier

The byte-for-byte check of `app.rate` before and after the move (118 answers: 51 samples in both modes, 10 refusals,
3 carriers with and without technical) was run when it was made (2026-10-20).

Run: python tests/verify_oi140.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


print("B  importing console.rate_answer makes no Kernel")
probe = ("import gc, sys; sys.path.insert(0, '.'); import console.rate_answer; from gl_engine.rating import Kernel; "
         "gc.collect(); print(sum(1 for o in gc.get_objects() if isinstance(o, Kernel)))")
alive = subprocess.run([sys.executable, "-c", probe], cwd=ROOT, capture_output=True, text=True).stdout.strip()
check(alive == "0", f"a fresh process importing console.rate_answer holds {alive} Kernel(s)")

import app  # noqa: E402
from console import rate_answer as RA  # noqa: E402

print("A  app.py keeps its names")
names = ("_subline_premiums", "_chain", "_rating", "_factors", "_is_stat", "FACTOR_KINDS", "MILESTONES")
check(all(getattr(app, n) is getattr(RA, n) for n in names), f"{', '.join(names)}: the same objects")

print("C  answer = app.rate")
subs = sorted((ROOT / "Engine_Payloads").glob("*/submission.json"))
same, n = 0, 0
for p in subs:
    payload = json.loads(p.read_text(encoding="utf-8-sig"))
    for mode in app.MODES:
        r = app.KERNELS[mode].rate(payload)
        n += 1
        same += json.dumps(RA.answer(r, payload, "ROUND_HALF_UP", app.RESOLVER), default=str) == \
            json.dumps(app.rate(payload, mode, "ROUND_HALF_UP"), default=str)
check(same == n and n, f"{n} answers ({len(subs)} samples x {len(app.MODES)} modes): answer = app.rate on {same}")

from console import catalog  # noqa: E402
carrier = catalog.build("GL", "IA", {"class_code": "18501", "effective_date": "20250715"})
carrier["header"].update(WritingCompany="UFC", PolicyType="New")     # DEV-003's U8 risk, as the deviations tests
if carrier is not None:
    for wt in (False, True):
        r = app.KERNELS[app.STRICT].rate(carrier, with_technical=wt)
        a = RA.answer(r, carrier, "ROUND_HALF_UP", app.RESOLVER, wt)
        b = app.rate(carrier, app.STRICT, "ROUND_HALF_UP", with_technical=wt)
        check(json.dumps(a, default=str) == json.dumps(b, default=str),
              f"carrier {carrier['header']['WritingCompany']}, technical={wt}: answer = app.rate "
              f"(premium {b.get('premium')}, {'with' if 'technical' in b else 'no'} technical)")

print("D  the comparison with ISO in its place")
real = app.compare_with_iso
seen = []
app.compare_with_iso = lambda pl, rating: (seen.append(rating), {"available": True, "stand_in": True})[1]
try:
    plain = json.loads(subs[0].read_text(encoding="utf-8-sig"))
    a = app.rate(plain, app.STRICT, "ROUND_HALF_UP", compare=True)
    keys = list(a)
    check(a.get("iso") == {"available": True, "stand_in": True} and keys.index("iso") < keys.index("premium")
          and keys.index("rounding") < keys.index("iso"), f"a plain request: iso between rounding and premium ({keys[:9]})")
    if carrier is not None:
        seen.clear()
        b = app.rate(carrier, app.STRICT, "ROUND_HALF_UP", compare=True)
        kb = list(b)
        check(b.get("iso", {}).get("compared") == "technical" and seen and seen[0] is not None
              and kb.index("deviation") < kb.index("iso") < kb.index("premium"),
              f"a carrier: technical compared, iso after deviation and before premium")
finally:
    app.compare_with_iso = real

fails = [label for ok, label in results if not ok]
print(f"\n{'PASS' if not fails else 'FAIL'}: {len(results) - len(fails)} of {len(results)}")
sys.exit(1 if fails else 0)
