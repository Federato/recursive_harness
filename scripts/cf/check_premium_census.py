#!/usr/bin/env python3
"""Does the premium-file census still see every premium file? (user, 2026-10-01: keep it "always in sync")

166_'s count (built of 546) and each chunk census find premium files by a rule named `SetPremium`. Chunk 23's C23-18
found older packages that price inside a rule named `ErcRate` instead -- invisible to that test. This scans every
in-force package (the countrywide parents of the 46 states and the 46 state packages) for any rule that writes a record's
`Premium` with a computed value (not the constant 0 a switched-off record gets) in a file that has no `SetPremium` rule.
The policy total (`CommercialPropertyRules.ErcCalculateTotalPremium`) is the one expected writer and is excluded.

    python scripts/cf/check_premium_census.py      # runs its selftest first (AK 2020's ErcRate writers must be found)

Exits 1 if any premium writer outside `SetPremium` exists in an in-force package (the census would miss it).
"""
from __future__ import annotations

import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
from cf_engine.resolve import book_for                                   # noqa: E402

ASOF = "20260917"
EXPECTED = {("CommercialPropertyRules.Rule.xml", "ErcCalculateTotalPremium")}


def scan(pkg: Path):
    hits = []
    for f in sorted((pkg / "Rules").glob("*.xml")):
        t = f.read_text(encoding="utf-8-sig", errors="ignore")
        if '<rul:Rule Name="SetPremium"' in t:
            continue
        for mm in re.finditer(r'<rul:Rule Name="(\w+)"[^>]*DataDefGroup="(\w+)"[^>]*>(.*?)</rul:Rule>', t, re.S):
            name, grp, body = mm.groups()
            if (f.name, name) in EXPECTED or f"{grp}Rules" not in f.name:
                continue
            writes = re.findall(r'<rul:(\w+)[^>]*ToDataDef="Premium"', body)
            if writes and any(w != "Constant" for w in writes):
                hits.append((f.name.replace("Rules.Rule.xml", ""), name))
    return hits


def selftest():
    """a check that finds nothing must be able to find something: AK's 2020 package prices its attorneys' fees in ErcRate."""
    pkg = book_for("AK", "20220701").state.package.content
    hits = scan(pkg)
    ok = any("ChangesAttorneysFeesStruct" in h[0] for h in hits) and any("ChangesAttorneysFeesPrsnlProp" in h[0] for h in hits)
    print(f"selftest on {pkg.name}: {len(hits)} premium writer(s) outside SetPremium found -> {'detects' if ok else 'BLIND'}")
    return ok


def main():
    if not selftest():
        print("SELFTEST FAILED: the scan cannot see an ErcRate premium writer")
        return 1
    states = import_module("164_chunk14_c14-18_all_states").STATES
    seen, missed = set(), []
    for j in states:
        b = book_for(j, ASOF)
        for pkg in (b.parent.package.content, b.state.package.content):
            if pkg.name in seen:
                continue
            seen.add(pkg.name)
            missed += [(pkg.name, *h) for h in scan(pkg)]
    print(f"{len(seen)} in-force packages scanned (46 states + their countrywide parents)")
    for m in missed:
        print(f"  MISSED BY THE CENSUS: {m[0]}  {m[1]}.{m[2]} writes Premium outside SetPremium")
    print("PREMIUM CENSUS IN SYNC: every in-force premium writer is a SetPremium rule (or the policy total)" if not missed
          else f"{len(missed)} premium writer(s) the census cannot see")
    return 1 if missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
