"""Rate every payload we hold and reconcile against ISO's own answer.

**This is the offline half of Phase 2, available now.** The plan says the RAaS
comparison can begin before the connection exists, because 50 ISO-priced example
policies are already on disk with ISO's own output beside each input. This
script is that comparison.

It reports three things and hides none of them:

  MATCH   our premium equals ISO's, to the penny
  DIFF    both rated, and they disagree -- **our defect until proven otherwise**
  STOP    we could not produce a number at all

The doctrine from the build plan applies from here on: **any difference is our
defect until proven otherwise.** A DIFF is not a finding about ISO.

Writes out/reconciliation.csv so a run can be diffed against the last one.

    python scripts/rate_all_payloads.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver                       # noqa: E402
from gl_engine.rating import Kernel                         # noqa: E402

PAYLOADS = ROOT / "Payloads"
OUT = ROOT / "scripts" / "erc" / "out" / "reconciliation.csv"


def iso_premium(path: Path):
    """ISO's own answer, or None if it did not ship one."""
    if not path.exists():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8-sig"))["Body"]
        return Decimal(str(body["GeneralLiability"][0]["Premium"]))
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def main() -> int:
    if not PAYLOADS.is_dir():
        print(f"no payloads at {PAYLOADS}")
        return 1

    kernel = Kernel(resolver=EditionResolver())
    rows = []
    for d in sorted(p for p in PAYLOADS.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        want = iso_premium(d / "1. Output.json")
        try:
            r = kernel.rate(src)
        except Exception as exc:                            # noqa: BLE001
            rows.append([d.name, "STOP", "", want or "",
                         f"{type(exc).__name__}: {exc}", "", "", ""])
            continue
        if not r.complete:
            rows.append([d.name, "STOP", "", want or "", str(r.stopped),
                         "", "", ""])
            continue
        if want is None:
            status, delta = "RATED", ""
        elif r.premium == want:
            status, delta = "MATCH", "0"
        else:
            status, delta = "DIFF", str(r.premium - want)
        rows.append([d.name, status, str(r.premium), str(want or ""), "",
                     delta, " over ".join(r.packages), len(r.messages)])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "status", "ours", "iso", "stopped", "delta",
                    "packages", "iso_messages"])
        w.writerows(rows)

    tally = Counter(r[1] for r in rows)
    n = len(rows)
    print(f"RECONCILIATION AGAINST ISO'S OWN PRICED EXAMPLES  ({n} payloads)")
    print()
    for k in ("MATCH", "DIFF", "STOP", "RATED"):
        if tally[k]:
            print(f"    {k:6s} {tally[k]:3d} of {n}")
    print()
    print(f"    {'juris':6s} {'status':7s} {'ours':>10s} {'iso':>10s} "
          f"{'delta':>9s}")
    for r in rows:
        print(f"    {r[0]:6s} {r[1]:7s} {r[2]:>10s} {r[3]:>10s} {r[5]:>9s}"
              + (f"  {r[4][:60]}" if r[4] else ""))
    print()
    print("    Every DIFF is our defect until proven otherwise. That is what")
    print("    strict-erc mode is for.")
    print(f"\n[wrote {OUT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
