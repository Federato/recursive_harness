"""Chunk 14, RC-5 (C14-19, gate 4): every 0 and every blank in the policy modifiers,
against the branch that consumes it. Derived by hand first, on chunk 2's Oregon
building (261 + 32 = 293).

The rules treat a "0" two different ways, which is the point of these cases:
  * a PackageModFactor of 0 and a supplied IRPMFactor of 0 are NOT blank (the
    default rules are IsNull-guarded), so they stay 0 and zero the premium;
  * a MultiPremiumAndDispersionCreditFactorUser of 0 and a CPPIRPMFactor of 0 ARE
    read as "not given" (the rules test FirstValue(... , 0.0) == 0.0 first), so the
    factor defaults to 1.0.
A reading that treats every 0 alike gets half of these wrong.

  Z1 policy PackageModFactor "0", building blank     -> building copies 0 -> $0 + $0 = 0
  Z2 PackageModFactor blank on policy and building   -> policy default 1.0 -> 293
  Z3 vacant building, building PackageModFactor blank, policy 0.8
                                                     -> vacant buildings take 1.0, NOT the
                                                        policy's 0.8 (premium: ISO decides;
                                                        vacancy moves the rate)
  Z4 MultiPremium...User "0", building blank         -> read as blank -> 1.0 -> 293
  Z5 MPD blank everywhere                            -> 1.0 -> 293
  Z6 IRPMApplies No, CPPIRPMFactor "0"               -> read as blank -> IRPMFactor 1.0 -> 293
  Z7 IRPMApplies blank, no IRPM factor of any kind   -> 1.0 -> 293
  Z8 IRPMApplies No, IRPMFactor "0" supplied          -> kept -> $0 + $0 = 0
  Z9 building "No Coverage", nothing else            -> total 0

ISO, live, refused Z1 and Z8 (found by running, 2026-09-24): the POLICY's stat code
TotalRatingModificationStatCode is looked up by int(r3(r3(r3(PM x MPD) x IRPM) / 10)
x 1000), i.e. the combined modifier in hundredths, in a CW table with rows 1..199
only. A combined modifier of 0 has no row, so ISO refuses the policy before any
premium; ours prices $0 (OI-103 shape). The same bound predicts a refusal at the top:
  Z10 policy PM 1.6, IRPM 1.25 (building PM 1.0)      -> 2.000 -> key 200: ISO refuses
  Z11 policy PM 1.59, IRPM 1.25                       -> 1.9875 -> 1.988 -> 0.199 -> 199:
      rates, stat code "199"; premium 326 + 40 = 366 (the building's own PM 1.0)
Z1, Z8 and Z10 are pinned as refusals (a refusal there is the expected result).

    python scripts/cf/163_chunk14_c14-19_zero_cases.py [--live]
"""
from __future__ import annotations

import argparse
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

m3 = import_module("160_chunk14_rc3_modifiers")
gc, t2, rep, r11 = m3.gc, m3.t2, m3.rep, m3.r11
POL, STRUCT, TOTAL, B1, B2 = m3.POL, m3.STRUCT, m3.TOTAL, m3.B1, m3.B2
PM_B = f"{STRUCT}/PackageModFactor"
MPD_B = f"{STRUCT}/MultiPremiumAndDispersionCreditFactor"
IRPMF = m3.IRPMF


def edit(pol=None, bldg=None, drop_pol=(), drop_bldg=()):
    def build():
        sub = t2.base()
        cp, st = m3.pol(sub), m3.bldg(sub)
        for k in drop_pol:
            cp.pop(k, None)
        for k in drop_bldg:
            st.pop(k, None)
        cp.update(pol or {})
        st.update(bldg or {})
        return sub
    return build


CASES = {
    "Z1": ("policy package mod 0 reaches the building", edit({"PackageModFactor": "0"}, drop_bldg=("PackageModFactor",)),
           {PM_B: 0, B1: 0, B2: 0, TOTAL: 0}),
    "Z2": ("package mod blank everywhere", edit(drop_pol=("PackageModFactor",), drop_bldg=("PackageModFactor",)),
           {PM_B: 1.0, TOTAL: 293}),
    "Z3": ("vacant building ignores the policy's package mod",
           edit({"PackageModFactor": "0.8"}, {"VacantBuilding": "Yes"}, drop_bldg=("PackageModFactor",)),
           {PM_B: 1.0}),
    "Z4": ("multi-premium user 0 is read as blank",
           edit({"MultiPremiumAndDispersionCreditFactorUser": "0"}, drop_bldg=("MultiPremiumAndDispersionCreditFactor",)),
           {MPD_B: 1.0, TOTAL: 293}),
    "Z5": ("multi-premium blank everywhere", edit(drop_bldg=("MultiPremiumAndDispersionCreditFactor",)),
           {MPD_B: 1.0, TOTAL: 293}),
    "Z6": ("CPPIRPMFactor 0 is read as blank",
           edit({"IRPMApplies": "No", "CPPIRPMFactor": "0"}, drop_pol=("IRPMFactor",)),
           {IRPMF: 1.0, TOTAL: 293}),
    "Z7": ("no IRPM input at all", edit(drop_pol=("IRPMFactor",)), {IRPMF: 1.0, TOTAL: 293}),
    "Z8": ("supplied IRPMFactor 0 is kept", edit({"IRPMApplies": "No", "IRPMFactor": "0"}),
           {IRPMF: 0, B1: 0, B2: 0, TOTAL: 0}),
    "Z9": ("building not covered, nothing else", edit(bldg={"CovType": "No Coverage"}), {B1: 0, TOTAL: 0}),
    "Z10": ("combined modifier 2.00: no stat-code row", edit({"PackageModFactor": "1.6", "IRPMApplies": "No", "IRPMFactor": "1.25"}),
            {B1: 326, B2: 40, TOTAL: 366}),
    "Z11": ("combined modifier 1.988 -> stat code 199", edit({"PackageModFactor": "1.59", "IRPMApplies": "No", "IRPMFactor": "1.25"}),
            {B1: 326, B2: 40, TOTAL: 366, f"{POL}/TotalRatingModificationStatCode": 199}),
}
REFUSES = {"Z1", "Z8", "Z10"}      # ISO refuses on TotalRatingModicationStatCode; ours prices (OI-103)


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
        bad = [(k, gc.read(k, data), v) for k, v in want.items()
               if not gc.num_eq(gc.read(k, data) if gc.read(k, data) is not None else 0, v)]
        print(f"{cid}  {label}: {len(want) - len(bad)} of {len(want)}"
              + "".join(f"\n      {k.rsplit('/', 1)[-1]} got {g} want {v}   << expected" for k, g, v in bad))
        if bad:
            fails.append(cid)
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} as derived")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every Premium, the total, and the modifier fields, by path):")
        for cid, (label, build, want) in CASES.items():
            req = r11.payload(build())
            (gc.OUT / f"chunk14_zero_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid}  ISO REFUSES {mm.group(0) if mm else str(exc.body)[:160]}"
                      + ("   (as pinned: OI-103)" if cid in REFUSES else ""))
                agree += cid in REFUSES
                continue
            if cid in REFUSES:
                print(f"  {cid}  ISO RATED -- expected a refusal; re-read the case")
                continue
            (gc.OUT / f"chunk14_zero_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            iso, ours = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if not rep.cmp.same(v, ours.get(k))]
            body = json.dumps(resp)
            for f in ("PackageModFactor", "MultiPremiumAndDispersionCreditFactor", "IRPMFactor"):
                iv = re.findall(r'"%s": ("?[^,}"]*"?)' % f, body)
                ov = []

                def walk(n):
                    for c in n.children:
                        if c.children:
                            walk(c)
                        elif c.tag == f:
                            ov.append(c.text)
                walk(data)
                iv = sorted(float(x.strip('"')) for x in iv if x.strip('"'))
                ovn = sorted(float(x) for x in ov if x not in (None, ""))
                if iv != ovn:
                    d.append((f, iv, ovn))
            want_code = want.get(f"{POL}/TotalRatingModificationStatCode")
            if want_code is not None:
                iso_code = re.findall(r'"TotalRatingModificationStatCode": "?([^,}"]*)', body)
                if iso_code != [str(want_code)]:
                    d.append(("TotalRatingModificationStatCode", iso_code, str(want_code)))
            tot = iso.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
            agree += not d
            print(f"  {cid}  {'AGREE ' if not d else 'DIFFER'}  ISO total {tot}  ({len(iso)} premiums)"
                  + "".join(f"\n        {str(k)[-80:]} ISO {v} ours {o}" for k, v, o in d[:4]))
        print(f"\n  live: {agree} of {len(CASES)} agree")
        if agree != len(CASES):
            fails.append("live")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
