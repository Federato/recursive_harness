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


#: The one field on which `Payloads/` inputs disagree with their own outputs.
#: See OI-77: 34 of 50 pairs carry `TerrorismCoverage="Yes"` on the input and
#: `"No"` on the output, while **every other echoed field agrees**. The evidence
#: says the outputs were produced from inputs with terrorism off and the inputs
#: were altered afterwards -- taking ISO's echoed value lifts agreement from
#: 28 of 50 to 47 of 50, which a wrong engine could not do.
#:
#: **Both runs are always reported.** Substituting ISO's own answer into the
#: input and printing only that is fitting the oracle, and it would hide a real
#: defect the day one appears here.
ECHOED_DISPUTE = "TerrorismCoverage"


def iso_body(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))["Body"]
    except (KeyError, ValueError):
        return None


def iso_premium(path: Path):
    """ISO's own answer, or None if it did not ship one."""
    body = iso_body(path)
    if body is None:
        return None
    try:
        return Decimal(str(body["GeneralLiability"][0]["Premium"]))
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def reconciled(src: Path, out: Path):
    """The submission with `TerrorismCoverage` taken from ISO's own output.

    Returns None when the pair does not dispute it, so the second run is only
    ever different where the dispute is real.
    """
    body = iso_body(out)
    if body is None:
        return None
    payload = json.loads(src.read_text(encoding="utf-8-sig"))
    try:
        want = body["GeneralLiability"][0].get(ECHOED_DISPUTE)
    except (KeyError, IndexError):
        return None
    if want is None:
        return None
    changed = False
    for gl in payload.get("body", {}).get("GeneralLiability", []):
        if gl.get(ECHOED_DISPUTE) != want:
            gl[ECHOED_DISPUTE] = want
            changed = True
    return payload if changed else None


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
                         f"{type(exc).__name__}: {exc}", "", "", "", ""])
            continue
        if not r.complete:
            rows.append([d.name, "STOP", "", want or "", str(r.stopped),
                         "", "", "", ""])
            continue
        if want is None:
            status, delta = "RATED", ""
        elif r.premium == want:
            status, delta = "MATCH", "0"
        else:
            status, delta = "DIFF", str(r.premium - want)

        # Second run, only where the pair disputes TerrorismCoverage.
        recon = ""
        alt = reconciled(src, d / "1. Output.json")
        if alt is not None and want is not None:
            try:
                r2 = kernel.rate(alt)
                recon = ("MATCH" if r2.complete and r2.premium == want
                         else f"DIFF {r2.premium}")
            except Exception as exc:                        # noqa: BLE001
                recon = f"STOP {type(exc).__name__}"

        rows.append([d.name, status, str(r.premium), str(want or ""), "",
                     delta, " over ".join(r.packages), len(r.messages), recon])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "status", "ours", "iso", "stopped", "delta",
                    "packages", "iso_messages", "reconciled"])
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
    # A row is counted once: it matches as filed, or it is disputed and matches
    # once TerrorismCoverage is taken from ISO. Summing the two columns
    # double-counts the rows that do both, and printed "59 of 50".
    disputed = sum(1 for r in rows if r[8])
    with_iso = sum(1 for r in rows
                   if r[1] == "MATCH" or (r[8] == "MATCH" and r[1] == "DIFF"))
    print()
    print(f"    AS FILED                        : {tally['MATCH']} of {n} match")
    print(f"    WITH ISO'S OWN TerrorismCoverage: {with_iso} of {n} match  "
          f"({disputed} pairs dispute that one field -- OI-77)")
    print()
    print("    Every DIFF that survives the second column is our defect until")
    print("    proven otherwise. That is what strict-erc mode is for.")
    print(f"\n[wrote {OUT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
