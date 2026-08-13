"""Build-order item 11 — state-specific rating coverages.

The item was scoped from `PHASE-SIZING.md` §5 as *"four coverages in three
states"*, with a note that *"NJ and RI lead coverages were checked and do not
rate."* This re-derives the population instead of trusting that list, and the
list moves.

The population is **every DataDefGroup that appears in no countrywide edition**
— computed by differencing the groups seen across all 10 countrywide packages
against those seen across the 51 resolved jurisdictions, not by matching state
names in group names, which is how three earlier gates missed New York's
Special Protective and Highway coverage in the first place.

    python 39_state_specific_align.py 20260812 [--verbose]

Exit code 1 if any assertion fails.
"""
from __future__ import annotations

import csv
import glob
import importlib.util
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)

# The five that rate, and the state that files each. Named rather than derived
# so the check is falsifiable: if a sixth appears, the enumeration below fails.
RATING = {
    "GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage": "NY",
    "GeneralLiabilityMarylandChangesLiabilityForHazardsOfLeadClassLvl": "MD",
    "GeneralLiabilityMassachusettsChangesLeadPoisoningEndorsementClassLvl": "MA",
    "GeneralLiabilityMassachusettsChangesSupplementalCovLeadPoisoningClassLvl": "MA",
    "GeneralLiabilityRhodeIslandChangesLeadPoisoningClassLvl": "RI",
}

failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    cw = {p: c for _e, p, _x, c in pk["CW"]}
    res = {j: r for j in pk if j != "CW"
           for r in [A.resolve(pk[j], asof)] if r}

    cwg: set[str] = set()
    for c in cw.values():
        for f in glob.glob(os.path.join(c, "Rules", "*.xml")):
            cwg |= {m.group(2) for m in RULE.finditer(A._read(f))}
    jg: dict[str, set[str]] = defaultdict(set)
    rules: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for j, r in res.items():
        for f in glob.glob(os.path.join(r[3], "Rules", "*.xml")):
            for m in RULE.finditer(A._read(f)):
                jg[m.group(2)].add(j)
                rules[m.group(2)].append((j, m.group(1)))

    state_only = {g: sorted(v) for g, v in jg.items() if g not in cwg}
    print(f"state-specific census as of {asof}: {len(cwg)} countrywide groups, "
          f"{len(jg)} jurisdiction groups, "
          f"**{len(state_only)} present in no countrywide edition**\n")

    verd = {r["DataDefGroup"]: r["verdict"] for r in
            csv.DictReader(open(os.path.join(HERE, "out",
                                             "rating_vs_capture.csv"),
                                encoding="utf-8"))}
    by_v: dict[str, list[str]] = defaultdict(list)
    for g in state_only:
        by_v[verd.get(g, "(not premium-writing)")].append(g)
    for v in sorted(by_v):
        print(f"  {v:<24} {len(by_v[v]):>4}")

    # ---- 1. exactly four are RATE_DRIVEN, and a fifth rates anyway
    rd = sorted(by_v.get("RATE_DRIVEN", []))
    check("four state-only groups are RATE_DRIVEN — and the classifier is one short",
          set(rd) == set(RATING) - {"GeneralLiabilityRhodeIslandChangesLeadPoisoningClassLvl"},
          f"{len(rd)} RATE_DRIVEN: {[g.replace('GeneralLiability', '') for g in rd]} · "
          f"Rhode Island rates too and is filed OTHER, because its premium comes "
          f"from `LeadLiabilityRate` — a name `25_rating_vs_capture.RATE_SRC` "
          f"does not match. **Fourth blind spot in that list.**")

    # ---- 2. Rhode Island rates; New Jersey does not. PHASE-SIZING said neither did.
    ri = [n for j, n in rules["GeneralLiabilityRhodeIslandChangesLeadPoisoningClassLvl"]]
    ri_prem = next((b for f in glob.glob(os.path.join(res["RI"][3], "Rules", "*.xml"))
                    for m in RULE.finditer(A._read(f))
                    for b in [m.group(3)]
                    if m.group(2).endswith("RhodeIslandChangesLeadPoisoningClassLvl")
                    and m.group(1) == "SetPremium"), "")
    nj_groups = sorted(g for g in state_only if "Lead" in g and state_only[g] == ["NJ"])
    nj_capture = []
    for f in glob.glob(os.path.join(res["NJ"][3], "Rules", "*.xml")):
        for m in RULE.finditer(A._read(f)):
            if m.group(2) in nj_groups and 'ToDataDef="Premium"' in m.group(3):
                nj_capture.append("ManualPremium" in m.group(3))
    check("Rhode Island rates lead; New Jersey captures it — PHASE-SIZING said neither rates",
          len(ri) == 13 and "ManualPremium" not in ri_prem
          and len(ri_prem) > 10000 and nj_capture and all(nj_capture),
          f"RI: {len(ri)} rules, a {len(ri_prem):,}-character `SetPremium` branching on "
          f"classes 67510/67511 and four lead-safety levels, no `ManualPremium` · "
          f"NJ: {len(nj_groups)} lead groups, {len(nj_capture)} write a Premium and "
          f"{sum(nj_capture)} of those read `ManualPremium` — capture, as recorded")

    # ---- 3. the five, sized
    print("\n  the five state-specific rating coverages:")
    total = 0
    for g, j in sorted(RATING.items(), key=lambda kv: (kv[1], kv[0])):
        n = len([x for x in rules[g] if x[0] == j])
        total += n
        d = os.path.join(res[j][3], "Rate Tables")
        key = "SpecialProtectiveHighway" if "SpecialProtective" in g else "Lead"
        tabs = [t[:-len(".RateTable.csv")] for t in sorted(os.listdir(d))
                if t.endswith(".RateTable.csv") and key in t]
        pop = [t for t in tabs
               if A.table(res[j][3], "Rate Tables", t + ".RateTable.csv")]
        print(f"    {j}  {g.replace('GeneralLiability', '')[:58]:<58} "
              f"{n:>3} rules · {len(pop)}/{len(tabs)} tables populated")
    check("item 11 is five coverages in four states, not four in three",
          total == 88 and len(set(RATING.values())) == 4,
          f"{total} rules across {len(RATING)} coverages in "
          f"{len(set(RATING.values()))} states — MD, MA (×2), NY, RI")

    # ---- 4. New York's Special Protective and Highway prices at zero by design
    ny = res["NY"][3]

    def col(t: str, i: int) -> list[str]:
        return [r[i].strip() for r in A.table(ny, "Rate Tables", t + ".RateTable.csv")]

    lc, elp, sel = (col("SpecialProtectiveHighwayLossCost", 2),
                    col("SpecialProtectiveHighwayELP", 2),
                    col("SpecialProtectiveHighwayELPText", 2))
    check("NY Special Protective and Highway is a REFER coverage, not a rateable one",
          set(lc) == {"0"} and set(elp) == {"0"} and set(sel) == {"Company"}
          and len(sel) == 3,
          f"all {len(lc)} filed classes carry loss cost `0` AND expected loss "
          f"potential `0`, and the N17 selector reads `Company` on every row — "
          f"which N17 establishes means *refer to company*. `SetBaseRate` "
          f"branches on `LossCost == 0` to the ELP path, and the ELP is `0` too, "
          f"so the chain computes **0**. Same shape as Railroad Protective")

    print(f"\n{'FAILED' if failures else 'all state-specific checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
