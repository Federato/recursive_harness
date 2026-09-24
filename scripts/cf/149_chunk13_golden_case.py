"""Chunk 13, C13-06 / C13-07: the terrorism golden case, Oregon, derived by hand first.

Chunk 2's Oregon building (class 0951 Frame, limit 100,000, protection class 3,
90% coinsurance, $1,000 deductible; ISO-confirmed $261 + $32) with terrorism
elected. Every figure below was derived from the filed rows BEFORE the first
run and is pinned here; the run must reproduce it.

Filed rows used (CF OR 20260601 V01):
  TerrorismTerritoryTier   OR "Multnomah County" -> 1
  TerrorismLossCost        OR "Program Year 3", tier 1 -> 0.009 ; OR "Full", tier 1 -> 0.01
  TerrorismFireExcptnFactor OR tier 1 -> 0.1      (Oregon only; CW has no such factor)
  Building factors (chunk 1): ProtectionClassFactor 0.96, CoinsuranceFactor 0.95,
  DeductibleFactorBasicGroupI 0.98; TerrorismLimitToUse = LimitToUse 100,000.
  The location's LossCostMultiplier is COPIED from the policy's (CW table: 1.0);
  the building's own LossCostMultiplier input is a different field.

Premium arithmetic (SetTerrorismPremium / SetPreTRIAPremium / SetPostTRIAPremium):
  round0( round4( round4( round4( Limit/100 x rate [x proration] ) x PC ) x Coins ) x Ded )

Cases -- each variant chosen so that countrywide and Oregon rules, or the
proration branches, predict DIFFERENT answers:
  G0  TRIA in effect, certified acts covered (IL 09 52: factor 1.0)
      rate 0.009 -> 1000 x 0.009 = 9 -> 8.64 -> 8.208 -> x0.98 = 8.04  => $8
  F1  certified acts NOT covered (IL 09 53). CW: factor 0.0 -> $0.
      Oregon: factor = fire exception 0.1 -> rate 0.0009 -> 0.9 -> 0.864 -> 0.8208 -> 0.804 => $1
  F2  F1 at a policy LossCostMultiplier of 10 (so the difference is not a rounding accident):
      loss cost 0.09 -> rate 0.009 => $8 (CW would say $0)
  E1  TRIA will expire 2027-06-01 (257 days: factors 0.70 / 0.30), entire-term rating,
      conditional exclusion "No Exclusion" (no IL 09 95/96/97 -> factor 1.0):
      Pre  = 1000 x 0.009 x 0.70 = 6.3 -> 6.048 -> 5.7456 -> 5.6307 => $6
      Post = 1000 x 0.01  x 0.30 = 3.0 -> 2.88  -> 2.736  -> 2.6813 => $3   total $9
  E2  E1 with conditional exclusion "Exclude" (IL 09 95) at policy LCM 10. CW: factor 0.0.
      Oregon: factor = fire exception 0.1; conditional rate uses PROGRAM YEAR 3 when a
      conditional form is attached: 0.09 x 0.1 = 0.009.
      Pre  = 1000 x 0.09 x 0.70 = 63 -> 60.48 -> 57.456 -> 56.307 => $56
      Post = 1000 x 0.009 x 0.30 = 2.7 -> 2.592 -> 2.4624 -> 2.4132 => $2   total $58 (CW: $56)

The building's own premium must not move: $261 / $32 (and it does not, at LCM 10:
the building reads its own LossCostMultiplier input, 1.0).

    python scripts/cf/149_chunk13_golden_case.py            # engine vs the pinned figures
    python scripts/cf/149_chunk13_golden_case.py --live     # also ISO live (C13-07)
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

g2 = import_module("09_chunk2_golden_case")
r11 = import_module("118_chunk11_c11-23_raas")
rp = import_module("145_chunk13_c13-03_replay")
ASOF = "20260917"
OUT = ROOT / "results" / "cf-raas"

IN_EFFECT = "Is in Effect for the Next 12 Months"
WILL_EXPIRE = "Will Expire During the Next 12 Months"
ENTIRE = "Certified Terrorism Premium Calculated for Entire Term"
P = "CommercialProperty"
STRUCT = "CommercialPropertyTable/CommercialProperty/CommercialPropertyLocationTable/CommercialPropertyLocation/" \
         "CommercialPropertyStructureTable/CommercialPropertyStructure"
LOC = "CommercialPropertyTable/CommercialProperty/CommercialPropertyLocationTable/CommercialPropertyLocation"
POL = "CommercialPropertyTable/CommercialProperty"
DISC_TRIA = P + "ZzDisclosurePursuantToTerrorismRiskInsAct2002"
DISC_EST = P + "ZzDisclosureOfPremiumEstimatedPremiumCertifiedActsTerrorismPursuantTerrorismAct2002"


def submission(tria=IN_EFFECT, cert="Yes", cond=None, lcm=None, territory="Multnomah County"):
    sub = r11.at_date(g2.submission())               # EffDate 09/17/2026, as sent to ISO (OI-105)
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp["TerrorismIndicator"] = "Yes"
    cp["TRIAType"] = tria
    cp["CoverageForCertifiedActs"] = cert
    if tria == WILL_EXPIRE:
        cp["TRIAExpirationDate"] = "06/01/2027"
        cp["ConditionalExclusionRatingOption"] = ENTIRE
        cp["TRIAConditionalExclusion"] = cond or "No Exclusion"
    if lcm is not None:
        cp["LossCostMultiplier"] = str(lcm)
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc["TerrorismTerritory"] = territory
    return sub


#: id -> (label, submission kwargs, expected figures)
CASES = {
    "G0": ("golden: TRIA in effect, certified acts covered (IL 09 52)", {},
           {f"{LOC}/TerrorismTerritoryTier": 1, f"{LOC}/TerrorismLossCostProgramYear3": "0.009",
            f"{LOC}/TerrorismLossCostFull": "0.01", f"{LOC}/TerrorismFireExcptnFactor": "0.1",
            f"{STRUCT}/TRIAExclFactor": 1, f"{STRUCT}/TRIAExclusionRate": "0.009",
            f"{STRUCT}/TerrorismLimitToUse": 100000, f"{STRUCT}/ProtectionClassFactor": "0.96",
            f"{STRUCT}/CoinsuranceFactor": "0.95", f"{STRUCT}/DeductibleFactorBasicGroupI": "0.98",
            f"{STRUCT}/TerrorismPremium": 8, f"{POL}/{DISC_TRIA}Table/{DISC_TRIA}/Premium": 8,
            f"{STRUCT}/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium": 261,
            f"{STRUCT}/CommercialPropertyStructureBuildingBasicGroupIICoverage/Premium": 32}),
    "F1": ("certified acts not covered (IL 09 53): Oregon fire exception 0.1 (CW: $0)",
           {"cert": "No"},
           {f"{STRUCT}/TRIAExclFactor": "0.1", f"{STRUCT}/TRIAExclusionRate": "0.0009",
            f"{STRUCT}/TerrorismPremium": 1, f"{POL}/{DISC_TRIA}Table/{DISC_TRIA}/Premium": 1}),
    "F2": ("F1 at policy LCM 10 (CW: $0)", {"cert": "No", "lcm": 10},
           {f"{LOC}/LossCostMultiplier": 10, f"{LOC}/TerrorismLossCostProgramYear3": "0.09",
            f"{STRUCT}/TRIAExclusionRate": "0.009", f"{STRUCT}/TerrorismPremium": 8,
            f"{STRUCT}/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium": 261}),
    "E1": ("TRIA will expire 2027-06-01, entire term, no conditional exclusion",
           {"tria": WILL_EXPIRE},
           {f"{POL}/DaysUntilTRIAExpiration": 257, f"{POL}/TerrorismProratingProgYr3Factor": "0.7",
            f"{POL}/TerrorismProratingFullFactor": "0.3", f"{STRUCT}/TerrorismCondExclFactor": 1,
            f"{STRUCT}/ConditionalTerrorRate": "0.01", f"{STRUCT}/PreTRIAPremium": 6,
            f"{STRUCT}/PostTRIAPremium": 3, f"{STRUCT}/TerrorismPremium": 9,
            f"{POL}/{DISC_EST}Table/{DISC_EST}/Premium": 9}),
    "E2": ("E1 with conditional exclusion (IL 09 95) at LCM 10: Oregon fire exception (CW: $56)",
           {"tria": WILL_EXPIRE, "cond": "Exclude", "lcm": 10},
           {f"{STRUCT}/TerrorismCondExclFactor": "0.1", f"{STRUCT}/ConditionalTerrorRate": "0.009",
            f"{STRUCT}/PreTRIAPremium": 56, f"{STRUCT}/PostTRIAPremium": 2, f"{STRUCT}/TerrorismPremium": 58,
            f"{POL}/{DISC_EST}Table/{DISC_EST}/Premium": 58}),
}


def read(path, data):
    n = data
    for step in path.split("/"):
        n = n.first(step) if n is not None else None
    return None if n is None else n.text


def num_eq(got, want):
    try:
        return Decimal(str(got)) == Decimal(str(want))
    except Exception:
        return False


def run(sub, juris="OR"):
    ip = Interpreter(book_for(juris, ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return data, ip


def engine(verbose=True):
    fails = []
    for cid, (label, kw, want) in CASES.items():
        try:
            data, ip = run(submission(**kw))
        except InterpretError as exc:
            print(f"{cid}  {label}\n    RAISED {exc}")
            fails.append(cid)
            continue
        bad = [(k, read(k, data), v) for k, v in want.items() if not num_eq(read(k, data), v)]
        print(f"{cid}  {label}:  {len(want) - len(bad)} of {len(want)} figures match")
        if verbose or bad:
            for k, v in want.items():
                got = read(k, data)
                print(f"    {k.rsplit('/', 2)[-2][-28:]:>28s}/{k.rsplit('/', 1)[-1]:32s} {str(got):>8s}  want {v}"
                      f"{'' if num_eq(got, v) else '   << expected'}")
        if bad:
            fails.append(cid)
    return fails


def live():
    """C13-07: the same submissions at ISO; every terrorism field compared by path."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import raas as raas_mod
    client = raas_mod.RaaS()
    OUT.mkdir(parents=True, exist_ok=True)
    agree = 0
    for cid, (label, kw, want) in CASES.items():
        sub = submission(**kw)
        req = r11.payload(sub)
        (OUT / f"chunk13_golden_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            print(f"  {cid}  ISO REFUSED {exc.status}: {str(exc.body)[:200]}")
            continue
        (OUT / f"chunk13_golden_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        st, eff, ours = rp.replay(req, None)
        iso = rp.iso_fields(resp)
        diffs = [(k, v, ours.get(k)) for k, v in iso.items()
                 if rp.num(v) != rp.num(ours.get(k)) and not (rp.num(v) in (None, 0.0) and rp.num(ours.get(k)) in (None, 0.0))]
        nz = {k.split("/")[-2].split("[")[0].replace(P, "")[:22] + "." + k.rsplit("/", 1)[-1]: v
              for k, v in iso.items() if (rp.num(v) or 0) > 0}
        ok = not diffs
        agree += ok
        print(f"  {cid}  {'AGREE ' if ok else 'DIFFER'}  ISO non-zero terrorism fields: {nz}")
        for k, v, o in diffs:
            print(f"        {k[-90:]}  ISO {v}  ours {o}")
    print(f"\n  live: {agree} of {len(CASES)} agree field for field")
    return agree == len(CASES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    fails = engine(verbose=not a.quiet)
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} cases reproduce every pinned figure")
    ok_live = True
    if a.live:
        print("\nC13-07, ISO live at 2026-09-17:")
        ok_live = live()
    sys.exit(1 if fails or not ok_live else 0)


if __name__ == "__main__":
    main()
