"""Chunk 13, C13-08 / C13-09: terrorism on the other four coverage groups, and the roll-up.

Every group computes its own terrorism premium from its own record, with its
own factor set (read from CW 20260601, the in-effect branch of each group's
`SetTerrorismPremium`; Pre/Post-TRIA follow the same pattern):

  Building           Limit/100 x rate x ProtectionClass x Coinsurance x DedBGI
  Contents           Limit/100 x rate x ProtectionClass x Coinsurance x DedBGI
  Business Income    LimitToUse/100 x rate x the BUILDING's ProtectionClass x Factor
                     (no coinsurance or deductible; LimitToUse, so a sub-limit never applies)
  Special Class      Limit/100 x rate x Coinsurance x DedBGI          (no protection class)
  SC Business Inc.   LimitToUse/100 x rate x Factor                     (nothing else)

Oregon, Multnomah County (tier 1): program year 3 loss cost 0.009, full 0.01;
IL 09 52 (certified acts covered) -> factor 1.0 -> rate 0.009. Factors are the
ones chunks 1-7 proved: PC 0.96, coinsurance 0.95, deductible 0.98 (0.99 where
contents raise the location total to 200,000), BI Factor 0.55, SCBI Factor 0.55.

Derived by hand before the run (in effect):
  Building   1000 x .009 = 9 -> 8.64 -> 8.208 -> x.98 = 8.04 (x.99 = 8.13)   $8
  Contents   9 -> 8.64 -> 8.208 -> x.99 = 8.13                               $8
  BI         9 -> x.96 = 8.64 -> x.55 = 4.75                                 $5
  SC         9 -> x.95 = 8.55 -> x.98 = 8.38                                 $8
  SCBI       9 -> x.55 = 4.95                                                $5

  C13-08, one group at a time on each chunk's own submission:
    K4 building + contents         8 + 8      = disclosure $16
    K5 building + business income  8 + 5      = $13
    K6 building + special class    8 + 8      = $16
    K7 building + SC + SCBI        8 + 8 + 5  = $21
  C13-09, all five on one policy (chunk 7's C7-26 submission):
    R1 TRIA in effect               8+8+5+8+5 = disclosure $34
    R2 TRIA expiring 2027-06-01 (0.70 / 0.30), entire term, no conditional exclusion:
       Building  Pre 6.3->6.048->5.7456->x.99=5.69 $6   Post 3->2.88->2.736->x.99=2.71 $3
       Contents  same as building                  $6 / $3
       BI        Pre 6.3->6.048->x.55=3.33 $3       Post 3->2.88->x.55=1.58 $2
       SC        Pre 6.3->5.985->x.98=5.87 $6       Post 3->2.85->x.98=2.79 $3
       SCBI      Pre 6.3 x .55 = 3.47 $3            Post 3 x .55 = 1.65 $2
       estimated-premium disclosure: TotalPre 24 + TotalPost 13 = $37
    R3 TRIA expiring, calendar-year disclosure: only the pre-TRIA share is charged
       6 + 6 + 3 + 6 + 3 = $24 on the 12/31/05 disclosure record
    R4 TRIA expired, post-TRIA forms, "No Exclusion": full loss cost 0.01 x factor 1.0
       Building 10 -> 9.6 -> 9.12 -> x.99 = 9.03 $9 ; Contents $9 ; BI 10 -> 9.6 -> x.55 = 5.28 $5
       SC 10 -> 9.5 -> x.98 = 9.31 $9 ; SCBI 10 x .55 = 5.5 $6          PostTRIA roll-up $38
    R5 TRIA expired, IL 00 30 (exclude): Oregon's PostTRIAExclFactor = fire exception 0.1
       (CW: 0.0 -> $0) -> rate 0.001 -> $1 on each of the five               PostTRIA roll-up $5

    python scripts/cf/150_chunk13_c13-08-09_groups_rollup.py [--live]
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
r11 = gc.r11
rp = gc.rp

POL = gc.POL
LOC = gc.LOC
STRUCT = gc.STRUCT
PP = STRUCT + "/CommercialPropertyOccupClassTable/CommercialPropertyOccupClass/" \
              "CommercialPropertyPersonalPropertyTable/CommercialPropertyPersonalProperty"
BI = STRUCT + "/CommercialPropertyBusinessIncomeTable/CommercialPropertyBusinessIncome"
SC = LOC + "/CommercialPropertySpecialClassTable/CommercialPropertySpecialClass"
SCBI = SC + "/CommercialPropertySpecialClassBusnIncomeTable/CommercialPropertySpecialClassBusnIncome"
DT, DE = gc.DISC_TRIA, gc.DISC_EST
DISC_TRIA = f"{POL}/{DT}Table/{DT}/Premium"
DISC_EST = f"{POL}/{DE}Table/{DE}"
DISC_123 = "CommercialPropertyZzDisclosureOfPremiumThrough123105CertifiedActsTerrorismPursuantTerrorismAct2002"
PT = "CommercialPropertyPostTRIACoverage"


POST = "Has Already Expired, Use Post-TRIA Forms"
CALENDAR = "Certified Terrorism Premium Calculated Only Until End of This Calendar Year"


def terrorize(sub, tria=gc.IN_EFFECT, rating=gc.ENTIRE, post_excl=None):
    sub = r11.at_date(sub)
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp.update({"TerrorismIndicator": "Yes", "TRIAType": tria, "CoverageForCertifiedActs": "Yes"})
    if tria == gc.WILL_EXPIRE:
        cp.update({"TRIAExpirationDate": "06/01/2027", "ConditionalExclusionRatingOption": rating,
                   "TRIAConditionalExclusion": "No Exclusion"})
    if post_excl:
        cp["PostTRIAExclusion"] = post_excl
    for loc in cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"]:
        loc["TerrorismTerritory"] = "Multnomah County"
        # Chunk 4's building leaves WindstormOrHailDeductible blank; ISO then refuses the
        # contents' `WindstormOrHailDeductibleAsNumber` lookup (key CW, blank) where our
        # engine tolerates it -- the OI-103 shape, met before in C12-23 and set the same way.
        for st in loc.get("CommercialPropertyStructureTable", {}).get("CommercialPropertyStructure", []):
            st.setdefault("WindstormOrHailDeductible", "1,000")
    return sub


def five():
    """Chunk 7's C7-26 policy: building, contents, business income, special class, SCBI."""
    sub = chunk4.submission("Basic")
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
    st = zeros2.structure(sub)
    st["CommercialPropertyBusinessIncomeTable"] = (
        zeros2.structure(chunk5.submission("Basic"))["CommercialPropertyBusinessIncomeTable"])
    loc = sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"][
        "CommercialPropertyLocation"][0]
    loc["CommercialPropertySpecialClassTable"] = g6.location(g7.submission("Basic"))[
        "CommercialPropertySpecialClassTable"]
    return sub


T = "TerrorismPremium"
CASES = {
    "K4": ("C13-08 building + contents (chunk 4)", lambda: terrorize(chunk4.submission("Basic")),
           {f"{STRUCT}/{T}": 8, f"{PP}/{T}": 8, DISC_TRIA: 16}),
    "K5": ("C13-08 building + business income (chunk 5)", lambda: terrorize(chunk5.submission("Basic")),
           {f"{STRUCT}/{T}": 8, f"{BI}/{T}": 5, DISC_TRIA: 13}),
    "K6": ("C13-08 building + special class (chunk 6)", lambda: terrorize(g6.submission("Basic")),
           {f"{STRUCT}/{T}": 8, f"{SC}/{T}": 8, DISC_TRIA: 16}),
    "K7": ("C13-08 building + special class + SC business income (chunk 7)",
           lambda: terrorize(g7.submission("Basic")),
           {f"{STRUCT}/{T}": 8, f"{SC}/{T}": 8, f"{SCBI}/{T}": 5, DISC_TRIA: 21}),
    "R1": ("C13-09 all five coverages, TRIA in effect", lambda: terrorize(five()),
           {f"{STRUCT}/{T}": 8, f"{PP}/{T}": 8, f"{BI}/{T}": 5, f"{SC}/{T}": 8, f"{SCBI}/{T}": 5,
            DISC_TRIA: 34}),
    "R2": ("C13-09 all five coverages, TRIA expiring (0.70 / 0.30)",
           lambda: terrorize(five(), tria=gc.WILL_EXPIRE),
           {f"{STRUCT}/PreTRIAPremium": 6, f"{STRUCT}/PostTRIAPremium": 3,
            f"{PP}/PreTRIAPremium": 6, f"{PP}/PostTRIAPremium": 3,
            f"{BI}/PreTRIAPremium": 3, f"{BI}/PostTRIAPremium": 2,
            f"{SC}/PreTRIAPremium": 6, f"{SC}/PostTRIAPremium": 3,
            f"{SCBI}/PreTRIAPremium": 3, f"{SCBI}/PostTRIAPremium": 2,
            f"{DISC_EST}/TotalPreTRIAPremium": 24, f"{DISC_EST}/TotalPostTRIAPremium": 13,
            f"{DISC_EST}/Premium": 37}),
    "R3": ("C13-09 all five, TRIA expiring, calendar-year disclosure (pre-TRIA share only)",
           lambda: terrorize(five(), tria=gc.WILL_EXPIRE, rating=CALENDAR),
           {f"{STRUCT}/{T}": 6, f"{PP}/{T}": 6, f"{BI}/{T}": 3, f"{SC}/{T}": 6, f"{SCBI}/{T}": 3,
            f"{POL}/{DISC_123}Table/{DISC_123}/Premium": 24}),
    "R4": ("C13-09 all five, TRIA expired, post-TRIA forms, no exclusion (full loss cost 0.01)",
           lambda: terrorize(five(), tria=POST, post_excl="No Exclusion"),
           {f"{STRUCT}/{T}": 9, f"{PP}/{T}": 9, f"{BI}/{T}": 5, f"{SC}/{T}": 9, f"{SCBI}/{T}": 6,
            f"{POL}/{PT}/CoverageOnPolicyIndicator": 1, f"{POL}/{PT}/Premium": 38}),
    "R5": ("C13-09 all five, post-TRIA exclusion IL 00 30: Oregon fire exception 0.1 (CW: $0)",
           lambda: terrorize(five(), tria=POST, post_excl="Exclude"),
           {f"{STRUCT}/PostTRIAExclFactor": "0.1", f"{STRUCT}/PostTRIAExclusionRate": "0.001",
            f"{STRUCT}/{T}": 1, f"{PP}/{T}": 1, f"{BI}/{T}": 1, f"{SC}/{T}": 1, f"{SCBI}/{T}": 1,
            f"{POL}/{PT}/Premium": 5}),
}


def engine():
    fails = []
    for cid, (label, build, want) in CASES.items():
        try:
            data, ip = gc.run(build())
        except InterpretError as exc:
            print(f"{cid}  {label}\n    RAISED {exc}")
            fails.append(cid)
            continue
        bad = [(k, gc.read(k, data), v) for k, v in want.items() if not gc.num_eq(gc.read(k, data), v)]
        print(f"{cid}  {label}:  {len(want) - len(bad)} of {len(want)} figures match")
        for k, got, v in bad:
            print(f"    {k[-95:]}  got {got}  want {v}   << expected")
        if bad:
            fails.append(cid)
    return fails


def live():
    import raas as raas_mod
    client = raas_mod.RaaS()
    agree = 0
    for cid, (label, build, want) in CASES.items():
        req = r11.payload(build())
        (gc.OUT / f"chunk13_groups_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            print(f"  {cid}  ISO REFUSED {exc.status}: {str(exc.body)[:200]}")
            continue
        (gc.OUT / f"chunk13_groups_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        st, eff, ours = rp.replay(req, None)
        iso = rp.iso_fields(resp)
        diffs = [(k, v, ours.get(k)) for k, v in iso.items()
                 if rp.num(v) != rp.num(ours.get(k))
                 and not (rp.num(v) in (None, 0.0) and rp.num(ours.get(k)) in (None, 0.0))]
        terr = sorted((k.split("/")[-2].split("[")[0].replace("CommercialProperty", "")[:18], k.rsplit("/", 1)[-1], v)
                      for k, v in iso.items() if (rp.num(v) or 0) > 0 and k.endswith(("TerrorismPremium", "TRIAPremium", "/Premium")))
        agree += not diffs
        print(f"  {cid}  {'AGREE ' if not diffs else 'DIFFER'}  {terr}")
        for k, v, o in diffs:
            print(f"        {k[-90:]}  ISO {v}  ours {o}")
    print(f"\n  live: {agree} of {len(CASES)} agree field for field")
    return agree == len(CASES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = engine()
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} cases reproduce every pinned figure")
    ok = True
    if a.live:
        print("\nISO live at 2026-09-17:")
        ok = live()
    sys.exit(1 if fails or not ok else 0)


if __name__ == "__main__":
    main()
