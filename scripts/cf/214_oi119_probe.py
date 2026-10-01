#!/usr/bin/env python3
"""OI-119 probe: which contents limit does ISO's `SetMaxPrsnlPropLimitForMLARCalc` keep?

The rule reads its own parameter `maxLimit` inside the binding that defines it. Three readings, each predicted
by hand BEFORE the call, and the probe is built so all three give different dollars:

    FIRST   the unbound read is blank, every row passes, FirstNonNull keeps the first row's Limit / 100
    MAX     a true running maximum: the largest row's Limit / 100
    LAST    each row overwrites: the last row's Limit / 100

P1  three locations, contents 100,000 / 500,000 / 200,000, reported 20,000 each (total 600 < every candidate,
    so MLARLimit = the candidate): MLARLimit 1,000 / 5,000 / 2,000.
P2  control, largest first (500,000 / 100,000 / 200,000): FIRST and MAX agree (5,000), LAST 2,000.

For each reading the Group I / Group II / Special MLARs and every VR premium are derived from the contents'
own final rates (read off our engine, which rates them before the MLAR exists and is already ISO-confirmed
for contents rates), then compared with ISO.

RESULT 2026-10-01 (ISO at 2026-09-17): P1 and P2 both REFUSED, HTTP 400 "No value found in Params (FromParam=maxLimit)
for Value rule at line 2780 in RuleSet CommercialPropertyValueReportingFormGeneralInformationRules (Project CF CW 20260601
V01)". ISO fails exactly where our engine fails: none of the three readings is ISO's; "Used" is unpriceable (OI-119).
(First attempt refused earlier, on payload typing: SpecificIns etc. are xs:int; 213_ now adds them to r11.NUMERIC.)

    python scripts/cf/214_oi119_probe.py            # predictions only
    python scripts/cf/214_oi119_probe.py --live     # and ISO at 2026-09-17
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

h = import_module("213_chunk22_rc1")
r2 = h.r2
gc, r11 = r2.gc, r2.r11
P, VR, r = h.P, h.VR, h.r
GROUPS = (("BasicGroupI", "BGI"), ("BasicGroupII", "BGII"), ("Special", "Special"))
CASES = {"P1": ("smaller first", ("100000", "500000", "200000")),
         "P2": ("largest first (control)", ("500000", "100000", "200000"))}
AVG = Decimal(20000)


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def build(limits):
    sub = h.two_locations(vr="Used", limit2=limits[1], vrf={"AvgVal": str(AVG)})
    ls = h.locations(sub)
    ls.append(copy.deepcopy(ls[1]))
    ls[2]["LocationNumber"] = "3"
    h.contents(ls[0])["Limit"], h.contents(ls[2])["Limit"] = limits[0], limits[2]
    return sub


def predict(data, limits):
    """per reading: MLARLimit, MLARs, and each row's VR premium per group."""
    cp = h.rc1.find(data, P)[0]
    pps = h.nodes(data, "PersonalProperty")
    tv = int(sum(min(AVG, h.num(pp, "Limit")) for pp in pps) / 100)
    cands = [int(Decimal(x) / 100) for x in limits]
    out = {}
    for reading, mx in (("FIRST", cands[0]), ("MAX", max(cands)), ("LAST", cands[-1])):
        lim = mx if tv < mx else tv
        mlar, prem = {}, {}
        for g, cy in GROUPS:
            times = sum(r(AVG / 100 * h.num(pp, f"Final{g}Rate"), 3) for pp in pps)
            mlar[g] = r(times / lim, 3)
            rows = []
            for pp in pps:
                x = r(mlar[g] * h.num(pp, "LimitToUse") / 100, 0)
                for fac in (h.num(cp, "PackageModFactor"), h.num(pp, "MultiPremiumAndDispersionCreditFactor"),
                            h.num(cp, "IRPMFactor"), h.num(cp, f"CyberIncidentExclusionFactor{cy}"),
                            h.num(cp, f"CyberIncidentExclusionCOLExcptnsFactor{cy}")):
                    x = r(x * fac, 0)
                rows.append(x)
            prem[g] = rows
        out[reading] = (lim, mlar, prem)
    return tv, out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--live", action="store_true")
    a = a.parse_args()
    preds = {}
    for cid, (label, limits) in CASES.items():
        with h.hypothesis_blank_maxlimit():          # contents rates only; the MLAR itself is predicted by hand
            data, ip, err = h.rated(build(limits))
        assert err is None, err
        tv, out = predict(data, limits)
        preds[cid] = out
        print(f"{cid} {label}: contents {limits}, reported {AVG} each -> TotalValueForMLARCalc {tv}")
        for reading, (lim, mlar, prem) in out.items():
            print(f"    {reading:5s} MLARLimit {lim:5d}  MLARs {[str(v) for v in mlar.values()]}  "
                  f"VR premiums {{{', '.join(f'{g}: {[str(x) for x in p]}' for g, p in prem.items())}}}")
        gi = h.nodes(data, VR + "GeneralInformation")[0]
        print(f"    engine under the FIRST hypothesis: MLARLimit {h.txt(gi, 'MLARLimit')}  "
              f"MLARs {[h.txt(gi, g + 'MLAR') for g, _ in GROUPS]}")
    if not a.live:
        return 0
    import raas as raas_mod
    client = raas_mod.RaaS()
    verdict = {}
    for i, (cid, (label, limits)) in enumerate(CASES.items(), 1):
        progress(i, len(CASES), f"ISO {cid}")
        with h.hypothesis_blank_maxlimit():
            req = r2.payload(build(limits)) if hasattr(r2, "payload") else r11.payload(build(limits))
        (gc.OUT / f"oi119_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            print(f"  {cid} ISO REFUSES: {str(exc.body)[:400]}")
            verdict[cid] = "REFUSED"
            continue
        (gc.OUT / f"oi119_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        iso = {g: [Decimal(str(x)) for x in r2.iso_of(resp, f"{VR}{g}Coverage")] for g, _ in GROUPS}
        found = []

        def walk(o):
            if isinstance(o, dict):
                if "MLARLimit" in o or "BasicGroupIMLAR" in o:
                    found.append({k: o.get(k) for k in ("MLARLimit", "MaxPrsnlPropLimitForMLARCalc", "TotalValueForMLARCalc",
                                                        "BasicGroupIMLAR", "BasicGroupIIMLAR", "SpecialMLAR") if k in o})
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(resp["Body"])
        print(f"  {cid} ISO VR premiums {{{', '.join(f'{g}: {[str(x) for x in p]}' for g, p in iso.items())}}}")
        for f in found[:2]:
            print(f"      ISO echoes {f}")
        match = [rd for rd, (lim, mlar, prem) in preds[cid].items()
                 if all(sorted(iso[g]) == sorted(prem[g]) for g, _ in GROUPS)]
        print(f"  {cid} ISO matches reading(s): {match or 'NONE'}")
        verdict[cid] = match
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nOI-119 probe: {verdict}  ({m}m{s:02d}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
