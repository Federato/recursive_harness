"""Chunk 14, RC-4 (C14-17): state stat-code rules the stored ISO responses never reach.

C14-16 (161_) compares every stat field on 293 stored ISO responses, strictly. It
already covers most state mechanisms with real values (AL/AR/DC/NY/RI deductible
codes, NC protection class, NY coinsurance, AL/KY windstorm mitigation, AL state
exception, CA wildfire, FL sinkhole, VA exposure amount, AK/AZ terrorism coverage,
and the states that BLANK a code -- AK/NY mold, DC/NY BCEG -- where ISO's blank must
meet ours). What no stored response holds is an earthquake record in a state that
files its own earthquake stat table. Earthquake is gated (chunk 10), so it is tested
here, live.

The lookup is two-level: the state's row first (FirstResult), the countrywide row
second (SingleResult). So a state value the CW table lacks separates the readings:

  E0 Oregon (chunk 10's golden building): EQClass A1, deductible 10%
     -> ConstructionStatCode "15" (CW), DeductibleStatCode "10" (OR files the CW set)
  E1 Florida: FL files its own class scheme (1C..5C), EQClass 2A, territory 11, 10%
     -> ConstructionStatCode "21" (FL row; CW has no 2A -- a CW-only reading refuses);
        DeductibleStatCode "10" (FL files no deductible stat table: CW row)
  E2 Texas: EQClass A1, territory 1 (deductible tier 2), 10%
     -> ConstructionStatCode "15" (TX files no construction table: CW),
        DeductibleStatCode "10" (TX row)
  E3 Texas 7%: TX files stat code "97" for every off-grid percentage, but its
     EQPercentageDeductibleFactor has rows for 5%..40% by fives only, so the premium
     lookup misses first -> ISO REFUSES (OI-103 shape); the "97" rows are unreachable
     through the percentage form. Our engine prices. Pinned as a refusal.

Premiums are not re-derived (chunk 10 did the EQ chain); every Premium and every stat
field on every record goes to ISO by path, strictly.

    python scripts/cf/162_chunk14_rc4_state_statcodes.py [--live]
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
import _iso_refusals as _iso                                    # noqa: E402

eq = import_module("85_chunk10_golden_case")
gc = import_module("149_chunk13_golden_case")
sc = import_module("161_chunk14_c14-16_statcode_replay")
rep = sc.rep
r11 = gc.r11

REFUSES = {"E3"}


def build(juris, eq_class, eq_terr, tier, ded):
    sub = r11.at_date(eq.submission())
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    if juris != "OR":                                   # 152_'s portable building (OI-103)
        cp["State"] = juris
        loc.pop("BasicGroupIRatingTerr", None)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
    loc.update({"EQTerr": eq_terr, "EQDeductibleTier": tier})
    st.update({"EQClass": eq_class, "EQDeductible": ded})
    st.setdefault("WindstormOrHailDeductible", "1,000")    # ISO refuses it blank (C13-08)
    return sub


CASES = {
    "E0": ("OR", ("A1", "1", "1", "10%"), {"ConstructionStatCode": "15", "DeductibleStatCode": "10"}),
    "E1": ("FL", ("2A", "11", "1", "10%"), {"ConstructionStatCode": "21", "DeductibleStatCode": "10"}),
    "E2": ("TX", ("A1", "1", "2", "10%"), {"ConstructionStatCode": "15", "DeductibleStatCode": "10"}),
    "E3": ("TX", ("A1", "1", "2", "7%"), {"ConstructionStatCode": "15", "DeductibleStatCode": "97"}),
}


def eq_codes(data):
    """Stat codes on the Earthquake records, by field."""
    out = {}

    def walk(n, inside):
        here = inside or "Earthquake" in n.tag
        for c in n.children:
            if c.children:
                walk(c, here)
            elif here and c.tag in ("ConstructionStatCode", "DeductibleStatCode"):
                out.setdefault(c.tag, set()).add(c.text or "")
    walk(data, False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []
    for cid, (j, args, want) in CASES.items():
        try:
            data, ip = gc.run(build(j, *args), juris=j)
        except InterpretError as exc:
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                continue
            print(f"{cid} {j}: RAISED {exc}")
            fails.append(cid)
            continue
        got = eq_codes(data)
        bad = [(k, got.get(k), v) for k, v in want.items() if got.get(k) != {v}]
        print(f"{cid} {j} EQClass {args[0]} deductible {args[3]}: {len(want) - len(bad)} of {len(want)}"
              + "".join(f"\n      {k} got {g} want {v}   << expected" for k, g, v in bad))
        if bad:
            fails.append(cid)
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} as derived")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every Premium, and every stat field strictly, by path):")
        for cid, (j, args, want) in CASES.items():
            req = r11.payload(build(j, *args))
            for cp in req["body"]["CommercialProperty"]:          # r11.payload writes Oregon
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk14_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid}  ISO REFUSES {m.group(0) if m else str(exc.body)[:160]}"
                      + ("   (as pinned: OI-103)" if cid in REFUSES else ""))
                agree += cid in REFUSES
                continue
            if cid in REFUSES:
                print(f"  {cid}  ISO RATED -- expected a refusal; re-read the case")
            (gc.OUT / f"chunk14_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            iso_p, our_p = rep.iso_prem(resp), rep.our_prem(data)
            iso_s, our_s = rep.cmp.iso_all(resp), rep.cmp.ours_all(data)
            d = [(k, v, our_p.get(k)) for k, v in iso_p.items() if not rep.cmp.same(v, our_p.get(k))]
            d += [(k, v, our_s.get(k)) for k, v in iso_s.items() if not sc.same(v, our_s.get(k))]
            iso_eq = {k.rsplit("/", 1)[-1]: v for k, v in iso_s.items()
                      if "Earthquake" in k and k.rsplit("/", 1)[-1] in want}
            d += [(f"derived {k}", iso_eq.get(k), v) for k, v in want.items() if iso_eq.get(k) != v]
            ok = not d and cid not in REFUSES
            agree += ok
            print(f"  {cid}  {'AGREE ' if ok else 'DIFFER'}  ({len(iso_p)} premiums, {len(iso_s)} stat values; "
                  f"ISO EQ codes {iso_eq})"
                  + "".join(f"\n        {str(k)[-80:]} ISO {v!r} ours {o!r}" for k, v, o in d[:6]))
        print(f"\n  live: {agree} of {len(CASES)} as expected")
        if agree != len(CASES):
            fails.append("live")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
