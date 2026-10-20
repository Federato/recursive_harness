"""OI-139: the kernel's checks around ISO's rules are plain functions (`gl_engine/rating/checks.py`), and nothing moved.

  A  the kernel's methods call them: `RatingError`, `TOTAL`, `TOTAL_CHECK`, `LOED_HOSTS` are the same objects through
     the kernel and through `checks`; the four methods hand over to `checks` (a stand-in records the call)
  B  without a Kernel: each package sample of ten editions rated by the kernel, and again by ISO's rules run with only
     `checks` around them (no Kernel object alive while it runs), gives the same outcome, premium, coverages, ISO's
     messages and our notices
  C  the OI-134 switch is still the kernel's: `kernel.RATING_INPUTS_CHECK = "off"` skips the check

Run: python tests/verify_oi139.py
"""
from __future__ import annotations

import gc
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.interp import Interpreter  # noqa: E402
from gl_engine.rating import Kernel, Rating, checks, kernel as KM  # noqa: E402
from gl_engine.rating.submission import load as load_submission  # noqa: E402
from gl_engine.resolve import EditionResolver, ResolvedBook  # noqa: E402

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


print("A  the kernel calls the checks")
check(KM.RatingError is checks.RatingError and KM.TOTAL is checks.TOTAL and KM.TOTAL_CHECK is checks.TOTAL_CHECK
      and Kernel.LOED_HOSTS is checks.LOED_HOSTS, "RatingError, TOTAL, TOTAL_CHECK, LOED_HOSTS: the same objects")
seen = []
names = ("refuse_missing_rating_inputs", "ilf_override_needed", "refuse_null_loss_cost", "collect")
real = {n: getattr(checks, n) for n in names}
for n in names:
    setattr(checks, n, lambda *a, _n=n, **k: seen.append(_n))
try:
    K0 = Kernel()
    K0._refuse_missing_rating_inputs(None, None)
    K0._ilf_override_needed(None, None)
    K0._refuse_null_loss_cost(None)
    K0._collect(None)
finally:
    for n in names:
        setattr(checks, n, real[n])
check(seen == list(names), f"the four methods hand over to checks: {seen}")
del K0

R = EditionResolver()
PIDS = ("GL_IA_20261001_V01", "GL_IA_20270401_V04", "GL_TX_20261001_V01", "GL_NY_20260801_V02", "GL_CA_20241101_V01",
        "GL_IL_20261001_V01", "GL_FL_20261001_V01", "GL_CO_20261001_V03", "GL_WA_20261001_V01", "GL_AK_20261001_V01")
samples = []
for pid in PIDS:
    if pid in R.by_id:
        samples += sorted((R.by_id[pid].content / "STC").glob("*.json"))[:2]


def outcome(r):
    if not r.complete:
        return ("refused", type(r.stopped).__name__, str(r.stopped))
    return ("rated", str(r.premium), sorted((k, str(v)) for k, v in r.by_coverage.items()),
            [str(m) for m in r.messages], list(r.notices))


def without_kernel(path):
    """ISO's rules on the interpreter with only `checks` around them, as the kernel's `_rate_book` places them."""
    data, juris, asof = load_submission(path)
    book = ResolvedBook(R.resolve(juris, asof))
    interp = Interpreter(book)
    r = Rating(juris=juris, asof=asof, mode=KM.STRICT, book=book, tree=data, trace=interp.trace,
               messages=interp.messages)
    try:
        checks.refuse_missing_rating_inputs(data, book)
    except checks.RatingError as exc:
        r.stopped = exc
        return r
    try:
        interp.run(data)
        r.complete = True
    except Exception as exc:  # noqa: BLE001
        r.stopped = checks.ilf_override_needed(data, exc) or exc
        return r
    try:
        checks.refuse_null_loss_cost(r)
        checks.collect(r)
    except checks.RatingError as exc:
        r.complete, r.stopped = False, exc
        return r
    checks.add_notices(r)
    return r


print("B  the same ratings without a Kernel")
K = Kernel(resolver=R)
theirs = {p: outcome(K.rate(p)) for p in samples}
del K
gc.collect()
alive = sum(1 for o in gc.get_objects() if isinstance(o, Kernel))
ours = {p: outcome(without_kernel(p)) for p in samples}
alive_after = sum(1 for o in gc.get_objects() if isinstance(o, Kernel))
same = [p for p in samples if ours[p] == theirs[p]]
rated = sum(1 for p in samples if theirs[p][0] == "rated")
check(len(same) == len(samples) and samples,
      f"{len(samples)} package samples of {len(PIDS)} editions ({rated} rated, {len(samples) - rated} refused): "
      f"outcome, premium, coverages, messages and notices the same on {len(same)}"
      + (f"; differ on {[p.name for p in samples if p not in same][:4]}" if len(same) != len(samples) else ""))
check(alive == 0 and alive_after == 0, f"no Kernel alive while rating without one ({alive} before, {alive_after} after)")

print("C  the OI-134 switch")
data, juris, asof = load_submission(samples[0])
K = Kernel(resolver=R)
was, KM.RATING_INPUTS_CHECK = KM.RATING_INPUTS_CHECK, "off"
calls = []
real_fn = checks.refuse_missing_rating_inputs
checks.refuse_missing_rating_inputs = lambda *a, **k: calls.append(1)
try:
    K._refuse_missing_rating_inputs(data, ResolvedBook(R.resolve(juris, asof)))
    off = list(calls)
    KM.RATING_INPUTS_CHECK = "on"
    K._refuse_missing_rating_inputs(data, ResolvedBook(R.resolve(juris, asof)))
    on = list(calls)
finally:
    KM.RATING_INPUTS_CHECK = was
    checks.refuse_missing_rating_inputs = real_fn
check(off == [] and on == [1], "kernel.RATING_INPUTS_CHECK = 'off' skips the check; 'on' makes it")

fails = [label for ok, label in results if not ok]
print(f"\n{'PASS' if not fails else 'FAIL'}: {len(results) - len(fails)} of {len(results)}")
sys.exit(1 if fails else 0)
