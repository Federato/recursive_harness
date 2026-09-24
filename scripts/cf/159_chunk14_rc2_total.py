"""Chunk 14, RC-2 (C14-06 to C14-09): the policy total, derived by hand first.

Every figure below is a sum of premiums earlier chunks derived by hand and ISO
confirmed; the total adds them, and the run must reproduce it (engine) and ISO
must agree (--live).

C14-06  GOLDEN. Chunk 7's five-coverage policy (C7-26: building 263 / 32,
        contents 223 / 24, business income 112 / 13, special class 66 / 209,
        SC business income 39 / 123 = 1,104), plus terrorism in effect (chunk 13
        R1: 34) and Debris Removal 60,000 on the building (chunk 12: 49 + 6 = 55).
        Policy total 1,104 + 34 + 55 = **1,193**.
C14-07  WHAT THE TOTAL COUNTS (chunk 2's building, 261 + 32 = 293):
        Z1 Debris Removal 25,000 (exposure 0)          -> 293
        Z2 Debris Removal 10,000 (negative: -21 / -3)   -> 269
        Z3 terrorism elected, certified-acts answer blank (disclosure $0) -> 293
        Z4 terrorism override 500 on the building       -> 293 + 500 = 793
        Z5 building "No Coverage" + Debris Removal 60,000: the building is $0 and
           Debris Removal still charges 42 + 5 (chunk 12 Z5) -> 47
C14-08  MORE THAN ONE LOCATION OR BUILDING (terrorism in effect, Multnomah):
        M1 two locations, each chunk 2's building: 2 x (261 + 32 + 8)        = 602
        M2 two buildings on one location: each STRUCTURE's own total keys its
           deductible (TotAmtInsurance = the structure's limit + contents at that
           structure, chunk 1), so each stays at 100,000 -> 0.98 -> 261 / 32 / 8:
           2 x (261 + 32 + 8) = 602. (First prediction said 606, assuming the
           LOCATION total keys the band; the engine was right.)
        (ErcResetPrsnlPropPremiumForAdditionalLocations belongs to the Additional
        Locations Special Coinsurance endorsement -- 12 rule files, never built or
        gated, in no ISO fixture. Logged as a coverage gap, not tested here.)
C14-09  ROUNDING: the total adds WHOLE-DOLLAR premiums, never raw ones.
        R1 two buildings on one location, certified acts declined (IL 09 53),
           Remainder of State (tier 3, loss cost 0.001, Oregon fire exception 0.4):
           each 1000 x 0.0004 = 0.4 -> 0.384 -> 0.3648 -> x.98 = 0.357 -> $0.
           Sum of rounded: terrorism $0, total 2 x 293 = 586. Rounding the raw sum
           0.715 would give $1 and 587. The two readings disagree, so ISO decides.

    python scripts/cf/159_chunk14_rc2_total.py [--live]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
dr = import_module("127_chunk12_golden_case")
rep = import_module("157_chunk14_c14-02_total_replay")
r11, rp = gc.r11, gc.rp
r11.NUMERIC |= {"TerrorismSubLimit", "TerrorOverridePremium"}
POL, STRUCT = gc.POL, gc.STRUCT
TOTAL = f"{POL}/ErcCalculatedTotalPremium"
PFX = dr.PFX
DR1 = f"{STRUCT}/{PFX}Table/{PFX}/{PFX}BasicGroupICoverage/Premium"
DR2 = f"{STRUCT}/{PFX}Table/{PFX}/{PFX}BasicGroupIICoverage/Premium"
B1 = f"{STRUCT}/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
B2 = f"{STRUCT}/CommercialPropertyStructureBuildingBasicGroupIICoverage/Premium"
DISC = f"{POL}/{gc.DISC_TRIA}Table/{gc.DISC_TRIA}/Premium"


def locs(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]["CommercialPropertyLocation"]


def structs(loc):
    return loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]


def terror(sub, cert="Yes", territory="Multnomah County"):
    sub = r11.at_date(sub)
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp.update({"TerrorismIndicator": "Yes", "TRIAType": gc.IN_EFFECT})
    if cert:
        cp["CoverageForCertifiedActs"] = cert
    for loc in locs(sub):
        loc["TerrorismTerritory"] = territory
        for st in structs(loc):
            st.setdefault("WindstormOrHailDeductible", "1,000")    # ISO refuses it blank (C13-08)
    return sub


def with_dr(sub, limit=60000):
    st = structs(locs(sub)[0])[0]
    st[f"{PFX}Table"] = {PFX: [{"Limit": str(limit)}]}
    return sub


def two_locations():
    sub = gc.g2.submission()
    ls = locs(sub)
    ls.append(copy.deepcopy(ls[0]))
    return sub


def two_buildings():
    sub = gc.g2.submission()
    ss = structs(locs(sub)[0])
    ss.append(copy.deepcopy(ss[0]))
    return sub


def base():
    return r11.at_date(gc.g2.submission())


CASES = {
    "G0": ("C14-06 golden: five coverages + terrorism + Debris Removal",
           lambda: with_dr(terror(grp.five())),
           {B1: 263, B2: 32, DR1: 49, DR2: 6, DISC: 34, TOTAL: 1193}),
    "Z1": ("C14-07 Debris Removal 25,000: exposure 0", lambda: with_dr(base(), 25000), {DR1: 0, TOTAL: 293}),
    "Z2": ("C14-07 Debris Removal 10,000: negative -21 / -3", lambda: with_dr(base(), 10000),
           {DR1: -21, DR2: -3, TOTAL: 269}),
    "Z3": ("C14-07 terrorism, certified-acts answer blank", lambda: terror(gc.g2.submission(), cert=""),
           {DISC: 0, TOTAL: 293}),
    "Z4": ("C14-07 terrorism override 500 on the building", lambda: override(terror(gc.g2.submission())),
           {DISC: 500, TOTAL: 793}),
    "Z5": ("C14-07 building 'No Coverage' + Debris Removal", lambda: no_cov(with_dr(base())),
           {B1: 0, DR1: 42, DR2: 5, TOTAL: 47}),
    "M1": ("C14-08 two locations", lambda: terror(two_locations()), {TOTAL: 602, DISC: 16}),
    "M2": ("C14-08 two buildings, one location", lambda: terror(two_buildings()), {B1: 261, TOTAL: 602, DISC: 16}),
    "R1": ("C14-09 two buildings, terrorism $0.36 each: whole dollars added",
           lambda: terror(two_buildings(), cert="No", territory="Remainder of State"),
           {DISC: 0, TOTAL: 586}),
}


def override(sub):
    st = structs(locs(sub)[0])[0]
    st.update({"TerrorismOverride": "Yes", "TerrorOverridePremium": "500"})
    return sub


def no_cov(sub):
    structs(locs(sub)[0])[0]["CovType"] = "No Coverage"
    return sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []
    for cid, (label, build, want) in CASES.items():
        try:
            data, ip = gc.run(build())
        except InterpretError as exc:
            print(f"{cid}  {label}: RAISED {exc}")
            fails.append(cid)
            continue
        bad = []
        for k, v in want.items():
            got = gc.read(k, data)
            if not (gc.num_eq(got if got is not None else 0, v)):
                bad.append((k, got, v))
        print(f"{cid}  {label}: {len(want) - len(bad)} of {len(want)}"
              + "".join(f"\n      {k.rsplit('/', 2)[-2][-40:]}/{k.rsplit('/', 1)[-1]} got {g} want {v}   << expected"
                        for k, g, v in bad))
        if bad:
            fails.append(cid)
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} as derived")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every Premium and ErcCalculatedTotalPremium, by path):")
        for cid, (label, build, want) in CASES.items():
            req = r11.payload(build())
            (gc.OUT / f"chunk14_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,140})', str(exc.body))
                print(f"  {cid}  ISO REFUSES {m.group(0) if m else str(exc.body)[:140]}")
                continue
            (gc.OUT / f"chunk14_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            iso, ours = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if not rep.cmp.same(v, ours.get(k))]
            tot = iso.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
            agree += not d
            print(f"  {cid}  {'AGREE ' if not d else 'DIFFER'}  ISO total {tot}  ({len(iso)} premiums compared)"
                  + "".join(f"\n        {k[-80:]} ISO {v} ours {o}" for k, v, o in d[:4]))
        print(f"\n  live: {agree} of {len(CASES)} agree field for field")
        if agree != len(CASES):
            fails.append("live")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
