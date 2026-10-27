#!/usr/bin/env python3
"""TC-34: re-run the Regression Library on this build, at zero calls.

Every entry re-rated on today's engine and compared with its reference (`console.regression`): ISO's fixtures as
`157_ --all` does (a premium that differs fails), every other number reported; the samples (D22's all-samples check);
the golden cases; promoted scenarios. Writes the run under `results/tc/library_runs/`, with the build (git commit), and
the readiness build marker. Exits 1 if any entry diverged.

    python scripts/tc/tc34_rerun_library.py [--workers 7]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from console import regression  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    r = regression.run(workers=a.workers)
    print(f"run {r['run']} on {r['build']}: {r['entries']} entries in {r['seconds']} s, {r['callsSpent']} calls; {r['counts']}")
    fx = [x for x in r["results"] if x["scenario"].startswith("FX-")]
    print(f"ISO fixtures: {sum(x['result'] in ('pass', 'fields') for x in fx)} of {len(fx)} pass on every premium "
          f"({sum(x['result'] == 'pass' for x in fx)} clean on every number)")
    for x in r["results"]:
        if x["result"] not in ("pass", "fields"):
            print(f"  {x['result']:9} {x['scenario']}: {x.get('detail', '')[:150]}")
    return 1 if any(x["result"] == "diverged" for x in r["results"]) else 0


if __name__ == "__main__":
    sys.exit(main())
