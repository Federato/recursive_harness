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

#: Pairs whose output is not an oracle for the input beside it (OI-78). Each is
#: established by `scripts/check_payload_pairs.py` from the files themselves --
#: never from the premium, which would be fitting the answer.
#:
#: `Payloads/AZ/1. Output.json` carries `State: AK`. It is Alaska's output,
#: mis-filed, and it is the one CONSISTENT with Alaska's input: the file in the
#: AK folder is missing `GeneralLiabilityMedPayCoverage/Limit`, which the input
#: supplies, and that single field is the whole of the difference between the
#: two (403 of 412 fields are identical).
ORACLE_OVERRIDE = {"AK": "AZ"}

#: No usable oracle exists, with the reason. Excluded from the comparable
#: population rather than counted as a difference -- comparing against an
#: output that did not come from this input manufactures a defect.
NO_ORACLE = {
    "AZ": "its output file is Alaska's (State: AK); no AZ output exists",
}
# OK was excluded until 2026-08-13: ISO rated it with GL_OK_20260801_V01, which
# the corpus did not hold. That filing was supplied and unpacked (OI-79), the
# resolver now picks exactly the package ISO's header names, and OK reconciles
# to the penny. The exclusion was a statement about the corpus, not the engine,
# and it was removed the moment the corpus changed.


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
                         f"{type(exc).__name__}: {exc}", "", "", "", "", ""])
            continue
        if not r.complete:
            rows.append([d.name, "STOP", "", want or "", str(r.stopped),
                         "", "", "", "", ""])
            continue
        if want is None:
            status, delta = "RATED", ""
        elif r.premium == want:
            status, delta = "MATCH", "0"
        else:
            status, delta = "DIFF", str(r.premium - want)

        # Third view: against the oracle that actually corresponds to this
        # input, excluding the pairs where none does.
        if d.name in NO_ORACLE:
            comparable = ""
        else:
            oracle = (PAYLOADS / ORACLE_OVERRIDE[d.name] / "1. Output.json"
                      if d.name in ORACLE_OVERRIDE else d / "1. Output.json")
            alt2 = reconciled(src, oracle)
            try:
                r3 = kernel.rate(alt2) if alt2 is not None else r
                w3 = iso_premium(oracle)
                comparable = ("MATCH" if r3.complete and r3.premium == w3
                              else f"DIFF {r3.premium} vs {w3}")
            except Exception as exc:                        # noqa: BLE001
                comparable = f"STOP {type(exc).__name__}"

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
                     delta, " over ".join(r.packages), len(r.messages), recon,
                     comparable])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "status", "ours", "iso", "stopped", "delta",
                    "packages", "iso_messages", "reconciled", "comparable"])
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
    comp = [r for r in rows if r[9]]
    comp_match = sum(1 for r in comp if r[9] == "MATCH")
    print(f"    AGAINST USABLE ORACLES ONLY     : {comp_match} of {len(comp)} match"
          f"   ({len(NO_ORACLE)} excluded, OI-78)")
    for s2, why in sorted(NO_ORACLE.items()):
        print(f"        {s2}: {why}")
    print()
    print("    Every DIFF that survives the third line is our defect until")
    print("    proven otherwise. That is what strict-erc mode is for.")
    print(f"\n[wrote {OUT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
