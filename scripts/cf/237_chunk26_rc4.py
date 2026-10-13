#!/usr/bin/env python3
"""Chunk 26, RC-4 (C26-16..C26-19): Specific rating in the states and the editions. Live ISO.

How each figure is derived before it runs:
  * every Specific Group I rate (building, contents, BI) and every Specific Group II rate by 234_'s hand models, which
    read the SHAPE from the rule each state actually runs (its own rewrite, else its countrywide parent's edition):
    CW / CA / AK AZ DC IL NJ  r3(r3(rate x LCM) x sprinkler x roof ACV);  FL NY WV MO (V02)  r3(rate x sprinkler x LCM),
    no roof factor;  KY  r3(rate x sprinkler x LCM x roof ACV);  BI on the building's rate (MO V02: the building's FINAL
    rate x the BI adjustment);  Group II: BCEG (32 states), + wind mitigation (3), NY's greenhouse / protective devices
  * every premium of the building, contents and BI core coverage records by 174_'s evaluator on the state's own SetPremium
  Then every premium is compared with ISO field for field, and the whole (level, message) multiset.

The building submits LimitationsOnCovForRoofSurfacingACVFactor 0.900 (IsNull-guarded, ISO honours it): the states whose
Specific shape carries the roof factor price Group I on 0.270, the others on 0.300, so each state's shape shows in dollars.

  C26-16/17/19  S-<j>  all 46 states: Specific building 0.300 (roof factor 0.900), contents 0.200, BI; Specific Group II
                       0.060 / 0.050 where the state carries RatingTypeBasicGroupII (its first filed Group II territory and
                       wind-hazard territory, 99,999 sq ft)
  C26-18        E-MO1  MO (CW 2023 V02): the roof factor is not in MO's Specific formula ($ at 0.300; the 2026 reading 0.270)
                E-MO2  MO: a submitted building BasicGroupIRate 0.500: MO's BI reads the building's FINAL rate (0.500 x
                       adjustment); the 2026 reading keeps BI on SpecificGroupIRate (0.300)
                       (NC is V03 and IL V04: their S- cases are the V03 / V04 probes)

    python scripts/cf/237_chunk26_rc4.py [--live] [--cases E-MO1] [--states AK,AL]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
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

c3 = import_module("236_chunk26_rc3")                   # wraps MessageHelper (TAGGED)
c2, h, t2, m, rc1, rep, cmp, gc, r11 = c3.c2, c3.h, c3.t2, c3.m, c3.rc1, c3.rep, c3.cmp, c3.gc, c3.r11
P, D, val, d, r = c3.P, Decimal, c3.val, h.d, h.r
s4 = c3.s4
s18 = h.s18
FAIL = []
r11.NUMERIC |= {"LimitationsOnCovForRoofSurfacingACVFactor"}
ROOF = "0.900"


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def rows(j, name):
    b = h.book_for(j, h.ASOF)
    for pk in (b.state.package.content, b.parent.package.content):
        p = pk / "Rate Tables" / f"{name}.RateTable.csv"
        if p.exists():
            rs = [x for x in csv.DictReader(open(p, encoding="utf-8-sig")) if x.get("StateCode") in (j, "CW")]
            if rs:
                return rs
    return []


def has_gii(j):
    return "RatingTypeBasicGroupII" in h.effective_rule(j, "Structure", "SetBasicGroupIIRate")


def state_policy(j, st_over=None):
    def b():
        over = {"LimitationsOnCovForRoofSurfacingACVFactor": ROOF, **(st_over or {})}
        if has_gii(j):
            over.update({"RatingTypeBasicGroupII": "Specific", "SpecificGroupIIRate": "0.060", "SquareFootageOfBuilding": "99999"})
        sub = h.tree(j=j, st_over=over)
        at = m.at(sub)
        loc = at[P + "Location"]
        if has_gii(j):
            at[P + "PersonalProperty"]["SpecificGroupIIRate"] = "0.050"
            for k in ("Structure", "PersonalProperty"):
                at[P + k].pop("BasicGroupIIRate", None)
            g2 = rows(j, "BasicGroupIIRate") or rows(j, "BasicGroupIIRateNonResidential")
            if g2:
                loc["BasicGroupIIRatingTerr"] = g2[0]["BasicGroupIIRatingTerr"]
            hz = rows(j, "GeographicWindHazardLevel")
            if hz:
                loc["GeographicWindHazardLevelTerritory"] = hz[0]["GeographicWindHazardLevelTerritory"]
        return s4.state_fixes(sub, j)
    return b


def cases(states):
    out = {}
    for j in states:
        out[f"S-{j}"] = ("C26-16" if j in ("AK", "AZ", "CA", "DC", "FL", "IL", "KY", "NJ", "NY", "WV") else
                         "C26-17" if j in ("ME", "NV", "OR", "UT", "VT") else "C26-19", j,
                         f"{j} ({h.bgi_variant(j)[0]}, roof {'in' if h.bgi_variant(j)[1] else 'not in'} the formula"
                         f"{', Specific Group II' if has_gii(j) else ''})", state_policy(j))
    out["E-MO1"] = ("C26-18", "MO", "MO (V02): the roof factor 0.900 is not in MO's Specific formula", state_policy("MO"))
    out["E-MO2"] = ("C26-18", "MO", "MO (V02): submitted building BasicGroupIRate 0.500: BI reads the building's FINAL rate",
                    state_policy("MO", {"BasicGroupIRate": "0.500"}))
    return out


def predict(cid, case):
    task, j, label, build = case
    req = t2.state_req(t2.m20.payload(build()), j)
    c3.TAGGED.clear()
    data, ip = cmp.rate(req)
    rates, prem, bad = c2.derive(data, j)
    st = rc1.find(data, P + "Structure")[0]
    if cid == "E-MO2":                                 # the submitted building rate survives: the rule never runs
        bad = [b_ for b_ in bad if not b_.startswith("building BGI hand")]
        if not m.same(val(st, "BasicGroupIRate"), "0.5"):
            bad.append(f"building BGI submitted 0.500 engine {val(st, 'BasicGroupIRate')}")
    alt = ""
    if j == "MO":
        bi = rc1.find(data, P + "BusinessIncome")[0]
        rf = d(st, "LimitationsOnCovForRoofSurfacingACVFactor")
        b26 = r(r(d(st, "SpecificGroupIRate") * d(st, "LossCostMultiplier"), 3) * d(st, "SprinklerLeakageNotExcludedFactor") * rf, 3)
        bi26 = r(r(r(d(st, "SpecificGroupIRate") * d(bi, "LossCostMultiplier"), 3) * d(st, "SprinklerLeakageNotExcludedFactor"), 3)
                 * d(bi, "BGIBaseRateAdjustmentFactor"), 3)
        alt = (f"      the 2026 reading in MO: building {b26 if cid != 'E-MO2' else '0.500 (submitted)'} vs V02 {val(st, 'BasicGroupIRate')}; "
               f"BI {bi26} vs V02 {val(bi, 'BasicGroupIRate')}")
        if (cid == "E-MO1" and m.same(b26, val(st, "BasicGroupIRate"))) or (cid == "E-MO2" and m.same(bi26, val(bi, "BasicGroupIRate"))):
            bad.append("the edition probe cannot discriminate")
    lines = [f"      rates by hand = engine: {[(l_, str(hv)) for l_, hv, _ in rates]}"]
    for key, vs in prem.items():
        if "BasicGroupI" in key and any(not m.same(v[1], 0) for v in vs):
            lines.append(f"      {key[-58:]:58s} predicted {[str(v[0]) for v in vs]}  engine {[v[1] for v in vs]}")
    if alt:
        lines.append(alt)
    print(f"{cid:6s} {task} {label}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:4])}")
    print("\n".join(lines[:10]))
    if bad:
        FAIL.append(cid)
    return req, data, {k: [v[0] for v in vs] for k, vs in prem.items()}


def live(client, raas_mod, cid, req, data, preds):
    (gc.OUT / f"chunk26_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:6s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk26_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    c3.TAGGED.clear()
    data2, ip = cmp.rate(req)
    ours = collections.Counter((c3.lvl(t), y) for t, y in c3.TAGGED)
    isos = collections.Counter(c3.iso_tagged(resp))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data2)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for key, want in preds.items():
        tag = key.split("/")[1]
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, tag) if v is not None)
        w = sorted(D(str(v)) for v in want if not isinstance(v, str))
        if iso != w:
            pbad.append((key, iso, w))
    ok = not dd and not pbad and ours == isos
    known = [y for (t, y), n in ((ours - isos) + (isos - ours)).items()]
    oi123 = known and all("CP 10 65" in y for y in known)
    print(f"  {cid:6s} {'AGREE' if ok else 'DIFFER'}: records as predicted {'yes' if not pbad else 'NO'}; {len(ipr) - len(dd)} of {len(ipr)} "
          f"premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
          + "".join(f"\n        predicted {k[-55:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for k, i_, w_ in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + "".join(f"\n        ISO only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (isos - ours).items())
          + "".join(f"\n        ours only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (ours - isos).items()))
    if not ok:
        FAIL.append(f"{cid} live")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    ap.add_argument("--states")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    states = s18.STATES if a.all else ([x.strip() for x in a.states.split(",")] if a.states else [])
    cs = cases(states)
    if a.cases:
        cs = {k: v for k, v in cases(s18.STATES).items() if k in a.cases.split(",")}
    elif states:
        cs = {k: v for k, v in cs.items() if k.startswith("S-")}
    else:
        cs = {k: v for k, v in cs.items() if k.startswith("E-")}
    client = raas_mod = None
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
    for i, (cid, case) in enumerate(cs.items(), 1):
        progress(i, len(cs), cid)
        try:
            req, data, preds = predict(cid, case)
        except Exception as exc:
            print(f"{cid}: RAISED {type(exc).__name__}: {str(exc)[:240]}")
            FAIL.append(cid)
            continue
        if a.live:
            live(client, raas_mod, cid, req, data, preds)
        del data
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C26-16..C26-19): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
