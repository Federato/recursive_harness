#!/usr/bin/env python3
"""Chunk 28 C28-19, measured (no engine change): where does the corpus stop being known-current, per state?

Inputs: `242_`'s live comparison (`results/cf-raas/chunk27_c27-13_editions.json`: for each state and six dates, the
package ISO used and the one our resolver picks) and the corpus itself (the latest package held per state).

For each state:
  * `held`     -- the latest package the corpus holds (its edition date)
  * `stale_from` -- the earliest edition of a package ISO served that the corpus lacks (None if ISO served nothing
                    newer at any date checked); from that date ours rates on an older package than ISO
  * `checked_to` -- the latest date `242_` compared (beyond it nothing is known either way)

Then the reach: every stored request (`results/cf-raas/*_request.json`) whose date is on or after its state's
`stale_from`, or after `checked_to`.

    python scripts/cf/255_chunk28_c28-19_coverage.py
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from cf_engine.erc.discovery import discover

EDITIONS = ROOT / "results" / "cf-raas" / "chunk27_c27-13_editions.json"
REQUESTS = ROOT / "results" / "cf-raas"
TODAY = "2026-10-06"


def iso_date(edition: str) -> str:
    return f"{edition[:4]}-{edition[4:6]}-{edition[6:]}"


def boundaries() -> dict:
    d = json.loads(EDITIONS.read_text(encoding="utf-8"))
    held: dict[str, str] = {}
    for p in discover():
        j = p.identity.juris
        if j != "CW":
            held[j] = max(held.get(j, ""), p.identity.edition)
    out = {}
    for st, by_date in d.items():
        missing = sorted({x["iso"] for x in by_date.values() if x["iso"] != x["ours"]})
        stale = min((m.split()[2] for m in missing), default=None)
        out[st] = {"held": held.get(st), "stale_from": iso_date(stale) if stale else None,
                   "checked_to": max(by_date), "missing": missing}
    return out


def reach(b: dict) -> list:
    hits = []
    for f in sorted(glob.glob(str(REQUESTS / "*_request.json"))):
        t = Path(f).read_text(encoding="utf-8")
        m = re.search(r'"EffectiveDateTime"\s*:\s*"(\d{4}-\d{2}-\d{2})', t)
        s = re.search(r'"Jurisdiction"\s*:\s*"([A-Z]{2})"', t) or re.search(r'"State\w*"\s*:\s*"([A-Z]{2})"', t)
        if not (m and s) or s.group(1) not in b:
            continue
        date, st = m.group(1), s.group(1)
        row = b[st]
        why = ("stale" if row["stale_from"] and date >= row["stale_from"]
               else "unchecked" if date > row["checked_to"] else None)
        if why:
            hits.append((Path(f).name, st, date, why))
    return hits


def main() -> int:
    b = boundaries()
    print(f"{'st':3} {'held':9} {'stale from':11} {'checked to':11} missing packages")
    for st in sorted(b):
        r = b[st]
        print(f"{st:3} {r['held'] or '-':9} {r['stale_from'] or '-':11} {r['checked_to']:11} {len(r['missing'])}")
    n_missing = len({m for r in b.values() for m in r["missing"]})
    stale = [st for st, r in b.items() if r["stale_from"]]
    today = [st for st, r in b.items() if r["stale_from"] and r["stale_from"] <= TODAY]
    print(f"\n{len(b)} states; {n_missing} packages ISO serves that the corpus lacks; {len(stale)} states go stale "
          f"within the dates checked; stale already today ({TODAY}): {', '.join(today) or 'none'}")
    hits = reach(b)
    print(f"\nstored requests past their state's boundary: {len(hits)}")
    for h in hits:
        print("  ", *h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
