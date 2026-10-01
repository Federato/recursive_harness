#!/usr/bin/env python3
"""Chunk 24, RC-2 (C24-07..C24-13): Builders Risk golden cases. Live ISO.

Every figure is predicted by hand before it runs: 224_'s premium hand models, PLUS the container rates derived here
from the filed tables and the building's built (ISO-confirmed) factors, not read off the engine:

  reporting form rate   Group I r3(r3(building BGI adjustment x building BGI LOI) x 1.82); II, Broad, Special the same on
                        their own adjustment / LOI (Broad: the building's BroadRate); EQ r3(EQ adjustment x 1.82); with
                        renovations on the building, it COPIES renovations' rates
  premium adjustment    r3(the building's adjustment x 1.82) per group (no LOI: each period applies its own, on NewValue)
  renovations           the larger of a Builders Risk rate (class 1150 base, x the completed-value multiplier 1.36 / 1.82)
                        and the completed building's rate (its own class, x coinsurance 0.9 x the modifier 0.75 / 1.0);
                        LOI on the renovations limit, or the reporting form's limit when one exists. Group I, Broad,
                        Special and EQ by hand; **Group II's container rate (symbols, numeric value, BCEG) is read from
                        the engine and left to ISO to check** (a stated simplification, not a derivation)
  LOI factors           banded, linear between the band edges, r4 then r3 (chunk 10's two-range reading)

Cases (Oregon unless noted, ISO at 2026-09-17):
  G1  C24-07/08/11/12  Special: reporting form 400,000, theft 50,000, collapse option 3, materials of others 250
  G2  C24-08/11        Broad: reporting form 400,000, collapse option 1
  G3  C24-11           Special: collapse option 2
  TS  C24-07           a stored theft fixture (STC_CP000016738) re-sent with a new limit (120,000) and deductible (2,500):
                       the deductible moves no dollar
  N1  C24-09           renovations 300,000 without a reporting form, Frame (the completed building's rate wins)
  N2  C24-09           renovations 300,000, Fire Resistive (the Builders Risk rate wins Group I)
  N3  C24-09/13        renovations beside a reporting form (rates copied, CVM 1.82, modifier 1.0; renovations $0), EQ class
  P1  C24-10           two premium adjustment periods from the effective date (ProRate 1.0), five groups
  E1  C24-13           EQ on a Builders Risk building of EQ class C1 (BR EQ factor 1.0) beside A1 (0.495)
  M1  C24-12           CP 10 44 on an ordinary building: Special deductible 250 (Deductible250Factor) and 1,000
  L1-L3  C24-10 / OI-121  ISO only (the engine refuses GetLeapDays): a term containing 29 February (2023-09-17), periods
                       from 12/01/2023 and 03/16/2024, and a 2026 control; ISO's ProRate against each leap-day reading

    python scripts/cf/225_chunk24_rc2.py [--live] [--cases G1,N2]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

x = import_module("224_chunk24_rc1")
t2 = import_module("220_chunk23_rc2")
m, rc1, rep, cmp, gc = x.m, x.rc1, x.rep, x.cmp, x.gc
r11 = m.r11
P, D, val, d, r = x.P, Decimal, x.val, x.d, x.r
FAIL = []
TH, MO, CP1044, RF, RN, PA, PAD, COL = x.TH, x.MO, x.CP1044, x.RF, x.RN, x.PA, x.PAD, x.COL
GROUPS = x.GROUPS
FIRE = ("Fire", "Fire and Vandalism", "Fire and Sprinkler Leakage", "Fire, Vandalism and Sprinkler Leakage")


def numeric():
    xs = next((x.CW / "DataDefs").glob("*.xsd")).read_text(encoding="utf-8-sig")
    out = set()
    for rec in [TH, MO, CP1044, RF, RN, PA, PAD, COL] + [RF + g + "Coverage" for g in GROUPS]:
        mm = re.search(rf'<xs:complexType name="{P}{rec}">(.*?)</xs:complexType>', xs, re.S)
        if mm:
            out |= {e for e, _ in re.findall(r'<xs:element name="(\w+)"[^>]*type="xs:(int|decimal|integer|long)"', mm.group(1))}
    return out


r11.NUMERIC |= numeric()


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ tables

def rows(j, name):
    return m.ROWS(j, name)


def tv(j, name, col, **keys):
    for row in rows(j, name):
        if all(row.get(k) == v for k, v in keys.items()):
            return D(row[col])
    return None


def banded(j, name, xval, **keys):
    """FromInclusiveToExclusive, linear between the band's factor edges, r4 then r3."""
    xv = D(str(xval))
    for row in rows(j, name):
        if all(row.get(k) == v for k, v in keys.items()) and D(row["Limit_From"]) <= xv < D(row["Limit_ToLessThan"]):
            lf, lt, ff, ft = (D(row[k]) for k in ("Limit_From", "Limit_ToLessThan", "Factor_From", "Factor_ToLessThan"))
            f = ff + (xv - lf) * (ft - ff) / (lt - lf)
            return r(r(f, 4), 3)
    return None


def ccode(j, ctype):
    ctu = next((row["Value"] for row in rows(j, "ConstructionTypeToUse") if row["ConstructionTypeBldg"] == ctype), None)
    cc = next((row["Value"] for row in rows(j, "ConstructionCode") if row["ConstructionTypeToUse"] == ctu), "0")
    return ctu, cc


# ------------------------------------------------------------------ container rates by hand

RF_OVR = {}            # submitted reporting-form values that survive their IsNull guards (226_ S1)


def rf_rates(j, st, rf):
    """the reporting form's five rates; with renovations it copies renovations' (by hand)."""
    rn = rc1.find(st, P + RN)
    if rn:
        return rn_rates(j, st, rn[0])
    f = RF_OVR.get("Factor", tv(j, "BldrsRiskReportingFormFactor", "Rate", Constant="Y"))
    cause = val(st, "CauseOfLossToUse")
    out = {"BasicGroupIRate": r(r(d(st, "BasicGroupICauseOfLossAdjustment") * d(st, "BasicGroupILOIFactor"), 3) * f, 3),
           "BasicGroupIIRate": D(0) if cause in FIRE else r(r(d(st, "BasicGroupIICauseOfLossAdjustment") * d(st, "BasicGroupIILOIFactor"), 3) * f, 3),
           "BroadRate": r(r(d(st, "BroadRate") * d(st, "BroadLOIFactor"), 3) * f, 3),
           "SpecialRate": r(r(d(st, "SpecialCauseOfLossAdjustment") * d(st, "SpecialLOIFactor"), 3) * f, 3),
           "EQRate": D(0) if val(st, "EQCovIndicator") in ("Not Applicable", "No Coverage") else r(d(st, "EQCauseOfLossAdjustment") * f, 3),
           "Factor": f}
    out.update(RF_OVR)
    return out


def pa_rates(j, st):
    # the rule reads the reporting form's own Factor (../../BuildersRiskReportingForm[1]/Factor): a submitted one flows in
    f = RF_OVR.get("Factor", tv(j, "BldrsRiskReportingFormFactor", "Rate", Constant="Y"))
    return {"BasicGroupIRate": r(d(st, "BasicGroupICauseOfLossAdjustment") * f, 3),
            "BasicGroupIIRate": r(d(st, "BasicGroupIICauseOfLossAdjustment") * f, 3),
            "BroadRate": r(d(st, "BroadRate") * f, 3), "SpecialRate": r(d(st, "SpecialCauseOfLossAdjustment") * f, 3),
            "EQRate": r(d(st, "EQCauseOfLossAdjustment") * f, 3)}


def rn_rates(j, st, rn):
    loc = st.parent.parent
    has_rf = bool(rc1.find(st, P + RF))
    ctu, cc = ccode(j, val(rn, "ConstructionType"))
    cvm = tv(j, "BldrsRiskRenovationsCompldValMultiplierFactor", "Factor",
             Option="Renovations with Reporting Form" if has_rf else "Renovations without Reporting Form")
    cmod = D(1) if has_rf else tv(j, "BldrsRiskRenovationsCoinsuranceModFactor", "Factor", Constant="Y")
    coins = tv(j, "CoinsuranceFactor", "Factor", CoinsuranceValue="100%")
    lim = d(rc1.find(st, P + RF)[0], "Limit") if has_rf else d(rn, "Limit")
    loi1 = banded(j, "BasicGroupILOIFactorBldg", lim, ConstructionCode=cc) if lim > 0 and cc != "0" else D(0)
    loib = banded(j, "BroadSpecialLOIFactorBldg", lim) if lim > 0 else D(0)
    lcm, sub, pc = d(st, "LossCostMultiplier"), d(st, "SubStdConditionRate"), d(st, "ProtectionClassFactor")
    sns, sf = d(st, "SprinklerLeakageExclNonSprinkleredBldgRate"), d(st, "SprinklerLeakageExclSprinkleredFactor", "1")
    van_br, van_c = d(rn, "VandalismExclFactorBuildersRiskRateCalculation", "1"), d(rn, "VandalismExclFactorCompletedBuildingRateCalculation", "1")
    base_br = tv(j, "BasicGroupIRate", "Rate", ClassCode="1150", ConstructionCode=cc, Group="Not Applicable", CovType="Building") or D(0)
    base_c = tv(j, "BasicGroupIRate", "Rate", ClassCode=val(st, "ClassCode"), ConstructionCode=cc, Group="Not Applicable", CovType="Building") or D(0)
    a = r(r(r(base_br * lcm, 3) + sub, 3) * d(st, "BasicGroupIRatingTerrFactor") * pc, 3)    # the BUILDING's terr factor
    br1 = r(r(r(r(r(a * cvm, 3) - sns, 3) * sf, 3) * van_br, 3) * loi1, 3)
    a = r((r(base_c * lcm, 3) + sub) * d(loc, "BasicGroupIRatingTerrFactor") * pc, 3)        # the LOCATION's terr factor
    c1 = r(r(r(r(r(r(a - sns, 3) * sf, 3) * van_c, 3) * loi1, 3) * coins, 3) * cmod, 3)
    bfb_br = tv(j, "BroadFormBaseRate", "Rate", ConstructionTypeToUse=ctu, CovType="BldrRisk") or D(0)
    bfb_c = tv(j, "BroadFormBaseRate", "Rate", ConstructionTypeToUse=ctu, CovType="Bldg") or D(0)
    brb = r(r(r(bfb_br * lcm, 3) * cvm, 3) * loib, 3)
    cb = r(r(r(r(bfb_c * lcm, 3) * loib, 3) * coins, 3) * cmod, 3)
    th = d(st, "SpecialTheftExclusionFactor", "1")
    sbr = r(r(r(r(tv(j, "SpecialBuildersRiskRate", "Rate", Constant="Y") * lcm, 3) * th, 3) * cvm, 3) * loib, 3)
    sc_base = tv(j, "SpecialBuildingRate", "Rate", Constant="Y") if val(st, "CauseOfLoss") == "Special" else D(0)
    sc = r(r(r(r(r(sc_base * lcm, 3) * th, 3) * loib, 3) * coins, 3) * cmod, 3)
    eqc = val(rn, "EQClass")
    if eqc and eqc != "Not Applicable":
        eqb = tv(j, "EQLossCostBldg", "LossCost", EQClass=eqc, EQTerr=val(st, "EQTerr") or val(loc, "EQTerr"))
        bre = tv(j, "BldrsRiskEQFactor", "Factor", EQClass=eqc) if val(st, "ClassCodeToUse") == "1150" else D(1)
        mods = r(eqb * lcm, 3) * bre
        for f in ("SoftStoryModificationFactor", "EQSprinkleredRiskFactor", "BldgHeightFactor", "BCEGEQFactor", "PctOfMasonryVeneerEQFactor"):
            mods *= d(st, f)
        inner = r(mods, 3)
        eqbr, eqcmp = r(inner * cvm, 3), r(inner * coins * cmod, 3)
    else:
        eqbr = eqcmp = D(0)
    pick = lambda b_, c_: b_ if b_ >= c_ else c_
    return {"BasicGroupIRate": pick(br1, c1), "BroadRate": pick(brb, cb), "SpecialRate": pick(sbr, sc), "EQRate": pick(eqbr, eqcmp),
            "BasicGroupIIRate": d(rn, "BasicGroupIIRate"),          # read from the engine (stated above), ISO-checked
            "_detail": {"BR Group I": br1, "completed Group I": c1, "BR Special": sbr, "completed Special": sc, "BR Broad": brb,
                        "completed Broad": cb, "BR EQ": eqbr, "completed EQ": eqcmp, "LOI I": loi1, "LOI B/S": loib, "CVM": cvm}}


def period_loi(j, st, det, grp):
    nv = d(det, "NewValue")
    if nv <= 0:
        return D(0)
    _, cc = ccode(j, val(st, "ConstructionType")) if val(st, "ConstructionCode") is None else (None, val(st, "ConstructionCode"))
    if grp == "BasicGroupI":
        return banded(j, "BasicGroupILOIFactorBldg", nv, ConstructionCode=cc)
    if grp == "BasicGroupII":
        return banded(j, "BasicGroupIILOIFactorBldg", nv)
    return banded(j, "BroadSpecialLOIFactorBldg", nv)


# ------------------------------------------------------------------ trees

def portable_br(cause="Special", recs=None, **kw):
    return x.br_tree(cause=cause, recs=recs, **kw)


def multi(sub, n, edit):
    """n copies of the building, edit(i, structure) on each."""
    loc = sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0]
    sts = loc[P + "StructureTable"][P + "Structure"]
    base = sts[0]
    sts[:] = [copy.deepcopy(base) for _ in range(n)]
    for i, s_ in enumerate(sts):
        edit(i, s_)
    return sub


def g1():
    return portable_br(recs={RF: {"Limit": "400000"}, TH: {"Limit": "50000"}, COL: {"CollapseOptionConverted": "Option3"},
                             MO: {"Indicator": "Yes", "ManualPremium": "250"}})


def g2():
    return portable_br(cause="Broad", recs={RF: {"Limit": "400000"}, COL: {"CollapseOptionConverted": "Option1"}})


def g3():
    return portable_br(recs={RF: {"Limit": "400000"}, COL: {"CollapseOptionConverted": "Option2"}})


def n1(ctype="Frame"):
    def b():
        sub = portable_br(recs={RN: {"Limit": "300000", "ConstructionType": ctype, "RatingType": "Class", "EQClass": "A1"}}, building=True)
        x.structure(sub)["ConstructionType"] = ctype
        return sub
    return b


def n3():
    sub = portable_br(recs={RN: {"Limit": "300000", "ConstructionType": "Frame", "RatingType": "Class", "EQClass": "A1"}, RF: {"Limit": "400000"}})
    return sub


def p1():
    sub = portable_br(recs={RF: {"Limit": "400000"}})
    rows_ = [{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026"},
             {"UnitNumber": "2", "NewValue": "650000", "ComputedFromDate": "09/17/2026"}]
    return x.add_periods(sub, rows_)


def e1():
    sub = portable_br(recs={RF: {"Limit": "400000"}})
    return multi(sub, 2, lambda i, s_: s_.update({"EQClass": ["A1", "C1"][i], "ConstructionType": ["Frame", "Fire Resistive - Reinforced Masonry - Other Than Light Steel"][i]}))


def mm1():
    sub = portable_br(recs={CP1044: {"Limit": "40000", "SpecialDed": "250"}}, building=True)
    sub = multi(sub, 2, lambda i, s_: None)
    st2 = sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0][P + "StructureTable"][P + "Structure"][1]
    st2[P + CP1044 + "Table"][P + CP1044][0]["SpecialDed"] = "1,000"
    return sub


def stored_theft():
    fx = rep.fixture_index()["STC_CP000016738"]
    dd = json.loads(fx.read_text(encoding="utf-8-sig"))
    body = copy.deepcopy(dd["CommercialProperty"])
    hits = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == P + TH:
                    hits.extend(v if isinstance(v, list) else [v])
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(body)
    for h in hits:
        h["Limit"] = 120000
        h["Deductible"] = "2,500"
    return {"header": {}, "body": {"SchemeKeys": {"ProductName": dd["SchemeKeys"]["ProductName"], "EffectiveDateTime": "2026-09-17T00:00:00"},
                                   "CommercialProperty": body}}


CASES = {
    "G1": ("C24-07/08/11/12", "Special: reporting form 400,000, theft 50,000, collapse option 3, materials of others 250", g1),
    "G2": ("C24-08/11", "Broad: reporting form 400,000, collapse option 1", g2),
    "G3": ("C24-11", "Special: collapse option 2", g3),
    "TS": ("C24-07", "stored theft fixture STC_CP000016738, new limit 120,000 and deductible 2,500", None),
    "N1": ("C24-09", "renovations 300,000 without a reporting form, Frame", n1("Frame")),
    "N2": ("C24-09", "renovations 300,000 without a reporting form, Fire Resistive", n1("Fire Resistive - Reinforced Masonry - Other Than Light Steel")),
    "N3": ("C24-09/13", "renovations beside a reporting form: rates copied, CVM 1.82, modifier 1.0, renovations $0", n3),
    "P1": ("C24-10", "premium adjustment: two periods from the effective date (500,000 / 650,000)", p1),
    "E1": ("C24-13", "two Builders Risk buildings, EQ class A1 (factor 0.495) and C1 (1.0)", e1),
    "M1": ("C24-12", "CP 10 44 on two ordinary buildings: Special deductible 250 and 1,000", mm1),
}


def request(cid):
    if cid == "TS":
        return stored_theft()
    return t2.state_req(t2.m20.payload(CASES[cid][2]()), "OR")


# ------------------------------------------------------------------ prediction

def container_checks(data, lines, bad):
    j = data.tag[-2:]
    for st in rc1.find(data, P + "Structure"):
        for rf in rc1.find(st, P + RF):
            want = rf_rates(j, st, rf)
            for k in ("BasicGroupIRate", "BasicGroupIIRate", "BroadRate", "SpecialRate", "EQRate"):
                ok = m.same(want[k], val(rf, k))
                if not ok:
                    bad.append(f"reporting form {k}")
            lines.append(f"      container reporting form rates by hand {[str(want[k]) for k in ('BasicGroupIRate', 'BasicGroupIIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}"
                         f" engine {[val(rf, k) for k in ('BasicGroupIRate', 'BasicGroupIIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}")
        for rn in rc1.find(st, P + RN):
            want = rn_rates(j, st, rn)
            for k in ("BasicGroupIRate", "BroadRate", "SpecialRate", "EQRate"):
                if not m.same(want[k], val(rn, k)):
                    bad.append(f"renovations {k}")
            lines.append(f"      container renovations by hand {{{', '.join(f'{k}: {v}' for k, v in want['_detail'].items())}}}"
                         f"\n        chosen I / Broad / Special / EQ hand {[str(want[k]) for k in ('BasicGroupIRate', 'BroadRate', 'SpecialRate', 'EQRate')]} "
                         f"engine {[val(rn, k) for k in ('BasicGroupIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}; Group II read {val(rn, 'BasicGroupIIRate')}")
        for pa in rc1.find(st, P + PA):
            if rc1.find(st, P + RN):
                # beside renovations the form takes renovations' Builders Risk / completed-building chains (without LOI):
                # not derived here; with no reporting period on the policy these rates price nothing
                lines.append(f"      premium adjustment rates beside renovations NOT derived (no period: no dollar): engine "
                             f"{[val(pa, k) for k in ('BasicGroupIRate', 'BasicGroupIIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}")
                continue
            want = pa_rates(j, st)
            for k, v in want.items():
                if not m.same(v, val(pa, k)):
                    bad.append(f"premium adjustment {k}")
            for det in rc1.find(pa, P + PAD):
                for g, (_, _, _, _, loi_f) in x.G.items():
                    if loi_f:
                        hv = period_loi(j, st, det, g)
                        if not m.same(hv, val(det, loi_f)):
                            bad.append(f"period {val(det, 'UnitNumber')} {loi_f} hand {hv} engine {val(det, loi_f)}")
            lines.append(f"      container premium adjustment rates by hand {[str(v) for v in want.values()]} engine {[val(pa, k) for k in want]}")


def predict(cid):
    req = request(cid)
    data, ip = cmp.rate(req)
    lines, bad, preds = [], [], {}
    container_checks(data, lines, bad)
    for rec in x.PREMIUM_RECS:
        res = x.predict(data, rec)
        preds[rec] = [hv for hv, _, _ in res]
        for hv, ev, e in res:
            ok = m.same(hv, e) and (ev is None or m.same(ev, e))
            if not ok:
                bad.append(f"{rec} hand {hv} evaluator {ev} engine {e}")
            if not m.same(e, 0) or not ok:
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-60:]:60s} hand {hv} evaluator {ev} engine {e}")
    print(f"{cid} {CASES[cid][0]} {CASES[cid][1]}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:4])}")
    print("\n".join(lines))
    if bad:
        FAIL.append(cid)
    return req, data, ip, preds


def live(client, raas_mod, cid, req, data, ip, preds):
    (gc.OUT / f"chunk24_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:3s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return None
    (gc.OUT / f"chunk24_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec))
        w = sorted(D(str(v)) for v in want if not isinstance(v, str))
        if [v for v in iso if v] != [v for v in w if v]:
            pbad.append((rec, iso, w))
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not dd and not pbad and mi == mo
    print(f"  {cid:3s} {'AGREE' if ok else 'DIFFER'}: Builders Risk records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums equal; messages {'equal' if mi == mo else 'DIFFER'}"
          + "".join(f"\n      predicted {rr[-50:]}: ISO {[str(v) for v in i_]} derived {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:6])
          + "".join(f"\n      {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + (f"\n      ISO only {sorted(mi - mo)[:3]}\n      ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
    if not ok:
        FAIL.append(f"{cid} live")
    return resp


# ------------------------------------------------------------------ OI-121: the leap-day probes (ISO only)

def r2(v):
    return D(v).quantize(D("0.01"), rounding=ROUND_HALF_UP)


LEAP = {  # case: (effective, period start)
    # L1 / L2 were chosen on the wrong sign (2026-10-01): DateDifference is second - first (OI-107), so both day counts in
    # the ProRate rule are NEGATIVE and removing L leap days gives (n + L) / (tot + L), not (n - L) / (tot - L). On L1 / L2
    # that reading rounds to the same 0.80 / 0.51 as L = 0: they cannot disagree. Kept as records; L4 / L5 discriminate.
    "L1": (date(2023, 9, 17), date(2023, 12, 1)),
    "L2": (date(2023, 9, 17), date(2024, 3, 16)),
    "L3": (date(2026, 9, 17), date(2027, 3, 17)),
    "L4": (date(2023, 9, 17), date(2023, 12, 23)),
    "L5": (date(2023, 9, 17), date(2024, 3, 9)),
}


def leap_readings(eff, frm):
    exp = date(eff.year + 1, eff.month, eff.day)
    tot, n = (exp - eff).days, (exp - frm).days
    feb29 = any(date(y, 2, 29) >= eff and date(y, 2, 29) <= exp for y in range(eff.year, exp.year + 1) if y % 4 == 0)
    # the rule: (DateDifference(Exp, From) - L) / (DateDifference(Exp, Eff) - L), DateDifference = second - first, so
    # (-n - L) / (-tot - L) = (n + L) / (tot + L)
    out = {"no leap day (L = 0)": r2(D(n) / D(tot))}
    out["Feb 29 in the term counted (L = 1)"] = r2(D(n + 1) / D(tot + 1)) if feb29 else out["no leap day (L = 0)"]
    out["inclusive day count"] = r2(D(n + 1) / D(tot + 1))
    return tot, n, out


def leap_req(eff, frm):
    sub = portable_br(recs={RF: {"Limit": "400000"}})
    sub = x.add_periods(sub, [{"UnitNumber": "1", "NewValue": "900000", "ComputedFromDate": frm.strftime("%m/%d/%Y")}])
    req = t2.state_req(t2.m20.payload(sub), "OR")
    req["body"]["SchemeKeys"]["EffectiveDateTime"] = eff.strftime("%Y-%m-%dT00:00:00")
    return req


def leap_probes(client, raas_mod, only=None):
    print("\nOI-121 leap-day probes (fixed 2026-10-01: the engine reads GetLeapDays as 0 on a one-year term, as ISO answers):")
    for cid, (eff, frm) in LEAP.items():
        if only and cid not in only:
            continue
        tot, n, reads = leap_readings(eff, frm)
        print(f"  {cid} term {eff} + 1 year ({tot} days), period from {frm} ({n} days to expiry); ProRate by reading: "
              + "; ".join(f"{k} {v}" for k, v in reads.items()))
        req = leap_req(eff, frm)
        (gc.OUT / f"chunk24_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
            print(f"     ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
            FAIL.append(f"{cid} live")
            continue
        (gc.OUT / f"chunk24_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        try:                                   # OI-121 fixed: the engine now rates these; every premium against ISO's
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ours_pr = [val(n_, "ProRate") for n_ in rc1.find(data, P + PAD)]
            print(f"     engine: ProRate {ours_pr}; {len(ipr) - len(dd)} of {len(ipr)} premiums equal to ISO"
                  + "".join(f"\n       {k[-80:]} ISO {v} ours {o}" for k, v, o in dd[:5]))
            if dd:
                FAIL.append(f"{cid} engine vs ISO")
        except Exception as exc:
            print(f"     engine RAISED {type(exc).__name__}: {str(exc)[:150]}")
            FAIL.append(f"{cid} engine")
        found = []

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == P + PAD:
                        found.extend(v if isinstance(v, list) else [v])
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(resp)
        for det in found:
            pr = det.get("ProRate")
            match = [k for k, v in reads.items() if pr is not None and D(str(pr)) == v]
            covs = {k[len(P + PAD):]: (v.get("FormAnnualPremium"), v.get("AnnualPremiumOfPrecedingReportingPeriod"), v.get("Premium"))
                    for k, v in det.items() if k.startswith(P + PAD) and isinstance(v, dict)}
            print(f"     ISO ProRate {pr}: matches {match or 'NO reading'}; coverages (FormAnnual, preceding, premium) {covs}")
            if pr is not None:
                for g, (fap, prev, prem) in covs.items():
                    if fap is None or prev is None or g == "BlanketCoverage":
                        continue
                    gg = g[:-len("Coverage")]
                    suf = x.G[gg][3]
                    hv = r(r(r(D(str(fap)) - D(str(prev)), 0) * D(str(pr)), 3), 0) if D(str(fap)) > D(str(prev)) else D(0)
                    if not m.same(hv, prem):
                        print(f"       {g}: premium {prem} vs r0(r0(FAP - preceding) x ProRate) = {hv} (cyber factors 1)")
            if not match:
                FAIL.append(f"{cid} no reading matches")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    only = set(a.cases.split(",")) if a.cases else None
    cs = [c for c in CASES if not only or c in only]
    got = {}
    for i, cid in enumerate(cs, 1):
        progress(i, len(cs), f"predict {cid}")
        try:
            got[cid] = predict(cid)
        except Exception as exc:
            print(f"{cid}: engine RAISED {type(exc).__name__}: {str(exc)[:200]}")
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (Builders Risk records as derived, every premium field for field, messages):")
        for i, cid in enumerate(cs, 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                live(client, raas_mod, cid, *got[cid])
        leap_probes(client, raas_mod, only)
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C24-07..C24-13): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
