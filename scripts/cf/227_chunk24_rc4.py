#!/usr/bin/env python3
"""Chunk 24, RC-4 (C24-18..C24-21): Builders Risk in the states, the editions and the built readers. Live ISO.

How each figure is derived before it runs:
  * a record whose state uses the countrywide SetPremium: 224_'s hand model (container rates by hand where the state does
    not rewrite the container's rate rules, 225_)
  * a record whose state REWRITES its SetPremium (FL premium adjustment / renovations / reporting form, KS NY VT renovations,
    TX renovations EQ, ...): 174_'s independent evaluator on THAT STATE's own rule text (the engine is not consulted)
  * container rates in a state that rewrites the container's rate rules (renovations and premium adjustment base rates in 16
    states): read from the engine and checked by ISO -- stated, not derived
  Every premium the policy carries is then compared with ISO field for field, and the (level, message) multiset.

  C24-18  the 16 rewriting states, one fuller policy each: a Builders Risk building (reporting form 400,000, theft 50,000,
          collapse option 3, materials of others 250, three premium adjustment periods: two from the effective date and one
          from 03/17/2027, now priced with OI-121's fix) and an ordinary building (renovations 300,000 Frame, CP 10 44 40,000)
  C24-19  the editions: the only family differences are the preceding-period rule in the 2023 V02 / V03 parents (MO; CA NC),
          which BREAK at the first earlier period with UnitNumber - 1 where 2026 keeps the LAST: probed with two periods
          sharing unit number 1 in MO and in OR (predicted: MO's period 2 reads the first, OR's the second)
  C24-20  all 46 states on the same policy (batched: --states)
  C24-21  the built readers with Builders Risk on: Business Income under a class 1150 building (BuildersRiskFactor 2 and the
          EQ factor), antennas' BI, unmanned aircraft, each against an ordinary-building control

    python scripts/cf/227_chunk24_rc4.py [--live] [--cases ...] [--states AK,AL] [--all]
"""
from __future__ import annotations

import argparse
import copy
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

c3 = import_module("226_chunk24_rc3")
c2, x, t2 = c3.c2, c3.x, c3.t2
m, rc1, rep, cmp, gc, r11 = x.m, x.rc1, x.rep, x.cmp, x.gc, c3.r11
P, D, val, d = x.P, Decimal, x.val, x.d
TH, MO, CP1044, RF, RN, PA, PAD, COL = x.TH, x.MO, x.CP1044, x.RF, x.RN, x.PA, x.PAD, x.COL
s18 = import_module("164_chunk14_c14-18_all_states")
no_eq = import_module("217_chunk22_rc4").no_eq
FL_SC = import_module("177_chunk16_rc4").FL_SC
r11.NUMERIC |= {"LimitOfInsurance"}            # the unmanned aircraft detail's limit is an Int32 at ISO (first sent as text)
FAIL = []
STATES16 = ["AK", "AL", "AR", "CA", "DC", "FL", "GA", "IL", "KS", "KY", "MT", "NJ", "NY", "RI", "TX", "VT"]
CONTAINER_FILES = {RF: RF, RN: RN, PA: PA}


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ the fuller policy

def full_policy(j):
    def build():
        sub = x.br_tree(j=j, recs={RF: {"Limit": "400000"}, TH: {"Limit": "50000"}, COL: {"CollapseOptionConverted": "Option3"},
                                    MO: {"Indicator": "Yes", "ManualPremium": "250"}})
        x.add_periods(sub, [{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026"},
                            {"UnitNumber": "2", "NewValue": "650000", "ComputedFromDate": "09/17/2026"},
                            {"UnitNumber": "3", "NewValue": "800000", "ComputedFromDate": "03/17/2027"}])
        if j == "NY":
            # NY submits its symbols (its own rule is empty): U on the Builders Risk building, and the completed building's
            # symbol that NY's LookupCompletedBldrsRiskBaseRate keys on (blank: ISO refuses, ours priced -- OI-103)
            c3.st(sub).update({"BasicGroupIISymbol": "U", "CompletedBasicGroupIISymbol": "B"})
        ordinary = x.br_tree(j=j, recs={RN: {"Limit": "300000", "ConstructionType": "Frame", "RatingType": "Class", "EQClass": "A1"},
                                         CP1044: {"Limit": "40000", "SpecialDed": "1,000"}}, building=True)
        b2 = c3.st(ordinary)
        b2["ConstructionType"] = "Frame"
        if j == "NY":
            # NY derives no symbol (its rule is empty): an ordinary building submits one, and "Not Applicable" for the
            # completed-building symbol, which NY's SetCompletedBldrsRiskBaseRate otherwise looks up blank on EVERY
            # building (ISO refuses the blank key, ours priced: OI-103)
            b2.update({"BasicGroupIISymbol": "B", "CompletedBasicGroupIISymbol": "Not Applicable"})
        sts = sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0][P + "StructureTable"][P + "Structure"]
        sts.append(b2)
        if j == "FL":
            no_eq(sub)                     # 208_'s Florida recipe (EQ class A1 not filed in FL: ISO refuses, OI-103)

            def fl_sc(o):                  # FL files no "Towers - Broadcasting Antennas" (C15-16): 177_'s FL_SC
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k == P + "SpecialClassTable":
                            for sc in v[P + "SpecialClass"]:
                                sc["ClassDescription"] = FL_SC
                        fl_sc(v)
                elif isinstance(o, list):
                    for v in o:
                        fl_sc(v)
            fl_sc(sub)
        loc = sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0]
        if not loc.get("BasicGroupIIRatingTerr"):
            # the portable policy carries a Group II territory only in OR; renovations look their Builders Risk Group II
            # rate up by it and ISO REFUSES a blank key (first sent 2026-10-01: AK AL AR refused, ours priced: OI-103)
            rows = c2.rows(j, "BasicGroupIIRate") or c2.rows(j, "BasicGroupIIRateNonResidential")   # FL's older package
            if rows:
                loc["BasicGroupIIRatingTerr"] = rows[0]["BasicGroupIIRatingTerr"]
        return sub
    return build


def edition_probe(j):
    """two periods sharing unit number 1, then period 2: the old Break takes the FIRST, 2026 the LAST."""
    def build():
        sub = x.br_tree(j=j, recs={RF: {"Limit": "400000"}})
        x.add_periods(sub, [{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026"},
                            {"UnitNumber": "1", "NewValue": "900000", "ComputedFromDate": "09/17/2026"},
                            {"UnitNumber": "2", "NewValue": "1000000", "ComputedFromDate": "09/17/2026"}])
        return sub
    return build


# ------------------------------------------------------------------ readers (C24-21)

def bi_on(br):
    """192_'s portable building with its Business Income: br turns the building into a class 1150 Builders Risk one
    (keeping the occupancy, so BI's own premium records stay)."""
    def build():
        sub = x.br_tree(j="OR", keep_occ=True, building=not br)
        if br:
            c3.st(sub)["Limit"] = "100000"            # no reporting form: a Builders Risk building carries its limit
        return sub
    return build


def antennas(br):
    a1 = import_module("192_chunk19_rc2").a1

    def build():
        sub = a1()
        if br:
            c3.st(sub).update({"CovType": "Builders Risk", "ClassCode": "1150"})
        return sub
    return build


UAB = "LimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoverage"


def drone(br):
    """the BUILDING-level unmanned aircraft detail (its EQ rate reads ../../../../BuildersRiskEQFactor, the building's);
    137_'s drone, 1,000,000 limit and a 5% EQ deductible so the EQ factor moves a dollar."""
    ua = import_module("137_chunk12_drone_golden_case")

    def build():
        det = dict(ua.DETAIL, LimitOfInsurance="1000000", EQDeductible="5%")
        return x.br_tree(j="OR", recs={UAB + "Detail": det}, building=not br, st_over={"Limit": "100000"} if br else None)
    return build


READERS = {
    "R-BI": ("OR", "Business Income under a class 1150 building (BuildersRiskFactor 2)", bi_on(True)),
    "R-BI0": ("OR", "control: the same Business Income under an ordinary building (factor 1)", bi_on(False)),
    "R-ANT": ("OR", "antennas' BI on a Builders Risk building", antennas(True)),
    "R-ANT0": ("OR", "control: antennas' BI on an ordinary building", antennas(False)),
    "R-UA": ("OR", "unmanned aircraft on a Builders Risk building", drone(True)),
    "R-UA0": ("OR", "control: unmanned aircraft on an ordinary building", drone(False)),
}


def cases(states):
    out = {}
    for j in states:
        out[f"S-{j}"] = ("C24-18" if j in STATES16 else "C24-20", j, f"{j}: fuller Builders Risk policy", full_policy(j))
    out["E-MO"] = ("C24-19", "MO", "MO (2023 V02 parent): duplicate unit 1, period 2 reads the FIRST", edition_probe("MO"))
    out["E-OR"] = ("C24-19", "OR", "OR (2026 parent): duplicate unit 1, period 2 reads the LAST", edition_probe("OR"))
    for cid, (j, label, build) in READERS.items():
        out[cid] = ("C24-21", j, label, build)
    return out


# ------------------------------------------------------------------ prediction

def rewrites(j):
    """the family files j's in-force package rewrites (rule text differs from the countrywide parent's)."""
    st_rules = x.state_rules(j)
    return {n for n, t in st_rules.items() if t != x.RULES.get(n)}


def own_setpremium(j, rec):
    own = x.state_rules(j).get(rec)
    return own is not None and m.cen.set_premium(own) != m.cen.set_premium(x.RULES[rec])


def container_checks(data, j, lines, bad):
    rw = rewrites(j)
    for st in rc1.find(data, P + "Structure"):
        has_rn = bool(rc1.find(st, P + RN))
        for rf in rc1.find(st, P + RF):
            if RF in rw or (has_rn and RN in rw):
                lines.append(f"      reporting form rates: {j} rewrites the rate rules -> engine-read {[val(rf, k) for k in ('BasicGroupIRate', 'BasicGroupIIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}")
                continue
            want = c2.rf_rates(j, st, rf)
            for k in ("BasicGroupIRate", "BasicGroupIIRate", "BroadRate", "SpecialRate", "EQRate"):
                if not m.same(want[k], val(rf, k)):
                    bad.append(f"reporting form {k} hand {want[k]} engine {val(rf, k)}")
        for rn in rc1.find(st, P + RN):
            if RN in rw:
                lines.append(f"      renovations rates: {j} rewrites the rate rules -> engine-read {[val(rn, k) for k in ('BasicGroupIRate', 'BasicGroupIIRate', 'BroadRate', 'SpecialRate', 'EQRate')]}")
                continue
            want = c2.rn_rates(j, st, rn)
            for k in ("BasicGroupIRate", "BroadRate", "SpecialRate", "EQRate"):
                if not m.same(want[k], val(rn, k)):
                    bad.append(f"renovations {k} hand {want[k]} engine {val(rn, k)}")
        for pa in rc1.find(st, P + PA):
            if PA in rw or has_rn:
                lines.append(f"      premium adjustment rates: {'state rewrite' if PA in rw else 'beside renovations'} -> engine-read")
                continue
            for k, v in c2.pa_rates(j, st).items():
                if not m.same(v, val(pa, k)):
                    bad.append(f"premium adjustment {k} hand {v} engine {val(pa, k)}")


def predict(cid, case):
    task, j, label, build = case
    req = t2.state_req(t2.m20.payload(build()), j)
    data, ip = cmp.rate(req)
    lines, bad, preds, how = [], [], {}, {"hand": 0, "state evaluator": 0, "engine only": 0}
    container_checks(data, j, lines, bad)
    for rec in x.PREMIUM_RECS:
        res = x.predict(data, rec)
        state_rule = own_setpremium(j, rec)
        preds[rec] = []
        for hv, ev, e in res:
            if state_rule:
                deriv, kind = ev, "state evaluator"
            else:
                deriv, kind = hv, "hand"
            if deriv is None or isinstance(deriv, str):
                deriv, kind = None, "engine only"
            how[kind] += 1
            ok = deriv is None or m.same(deriv, e)
            if not state_rule and ev is not None and not isinstance(ev, str) and not m.same(ev, e):
                ok = False
            preds[rec].append(deriv if deriv is not None else e)
            if not ok:
                bad.append(f"{rec[-50:]} {kind} {deriv} evaluator {ev} engine {e}")
            if not m.same(e, 0) or not ok:
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-58:]:58s} {kind:15s} {deriv} engine {e}")
    if cid.startswith("E-"):
        dets = rc1.find(data, P + PAD)
        two = [dt for dt in dets if val(dt, "UnitNumber") == "2"]
        ones = [dt for dt in dets if val(dt, "UnitNumber") == "1"]
        if two and len(ones) == 2:
            cov = lambda dt: dt.first(P + PAD + "BasicGroupICoverage")
            prev = val(cov(two[0]), "AnnualPremiumOfPrecedingReportingPeriod")
            first, last = val(cov(ones[0]), "FormAnnualPremium"), val(cov(ones[1]), "FormAnnualPremium")
            want = first if cid == "E-MO" else last
            ok = m.same(prev, want)
            lines.append(f"      period 2 preceding {prev}: the first unit-1 period's FormAnnual {first}, the last's {last} -> "
                         f"predicted {'FIRST' if cid == 'E-MO' else 'LAST'} {'ok' if ok else 'FAIL'}")
            if not ok:
                bad.append("edition: preceding period")
    if cid.startswith("R-"):
        r = x.r
        brf_want = x.m.table_val("OR", "BldrsRiskFactorBusnIncome", "Factor", Constant="Y")
        for bi in rc1.find(data, P + "BusinessIncome"):
            want = brf_want if cid in ("R-BI", "R-ANT", "R-UA") else D("1")     # every class 1150 building's BI
            if not m.same(val(bi, "BuildersRiskFactor"), want):
                bad.append(f"BI BuildersRiskFactor {val(bi, 'BuildersRiskFactor')} (predicted {want})")
            # BI's Group I cause-of-loss adjustment: r3(r3(r3(r3(rate - sprinkler NS) x sprinkler) x vandalism) x BuildersRiskFactor)
            inner = r(r(r(d(bi, "BasicGroupIRate") - d(bi, "SprinklerLeakageExclNonSprinkleredRate"), 3) * d(bi, "SprinklerLeakageExclSprinkleredFactor"), 3)
                      * d(bi, "VandalismExclFactor"), 3)
            hv = r(inner * want, 3)
            ok = m.same(hv, val(bi, "BasicGroupICauseOfLossAdjustment"))
            lines.append(f"      {'ok  ' if ok else 'FAIL'} BI Group I adjustment by hand {hv} (factor {want}) engine {val(bi, 'BasicGroupICauseOfLossAdjustment')}")
            if not ok:
                bad.append("BI adjustment")
            for ant in rc1.find(bi, P + "RadioOrTelevisionAntennasBusinessIncomeOrExtraExpense"):
                a_in = r(r(r(r(d(ant, "BasicGroupIBaseRate") * d(bi, "LossCostMultiplier"), 3) - d(bi, "SprinklerLeakageExclNonSprinkleredRate"), 3)
                           * d(bi, "SprinklerLeakageExclSprinkleredFactor"), 3) * d(ant, "VandalismExclFactor"), 3)
                hv = r(r(a_in * want, 3) * d(bi, "Factor"), 3)
                ok = m.same(hv, val(ant, "BasicGroupIRate"))
                lines.append(f"      {'ok  ' if ok else 'FAIL'} antennas BI Group I rate by hand {hv} (x BI factor {want} x {val(bi, 'Factor')}) engine {val(ant, 'BasicGroupIRate')}")
                if not ok:
                    bad.append("antennas BI rate")
        for det in rc1.find(data, P + UAB + "Detail"):
            up4 = det.parent.parent.parent.parent                       # ../../../../ as the rule writes it: the Structure
            f = [d(up4, k) for k in ("SoftStoryModificationFactor", "EQSprinkleredRiskFactor", "BldgHeightFactor", "BCEGEQFactor",
                                     "PctOfMasonryVeneerEQFactor", "BuildersRiskEQFactor")]
            v = r(r(d(det, "EQBaseRate") * d(up4, "LossCostMultiplier"), 3) * d(up4, "LimitationsOnCovForRoofSurfacingACVFactor"), 3)
            for k in f:
                v *= k
            hv = r(v, 3)
            breqf = x.m.table_val("OR", "BldrsRiskEQFactor", "Factor", EQClass=val(up4, "EQClass")) if cid == "R-UA" else D(1)
            ok = m.same(hv, val(det, "EQRate")) and m.same(val(up4, "BuildersRiskEQFactor"), breqf)
            eqp = [val(c, "Premium") for c in det.children if c.tag.endswith("EQCov")]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} unmanned aircraft (building-level) EQ rate by hand {hv} with the building's "
                         f"BuildersRiskEQFactor {val(up4, 'BuildersRiskEQFactor')} (table {breqf}) engine {val(det, 'EQRate')}; EQ premium {eqp}")
            if not ok:
                bad.append("unmanned aircraft EQ rate")
        lines.append(f"      BI BuildersRiskFactor {[val(bi, 'BuildersRiskFactor') for bi in rc1.find(data, P + 'BusinessIncome')]}; "
                     f"building BuildersRiskEQFactor {[val(s_, 'BuildersRiskEQFactor') for s_ in rc1.find(data, P + 'Structure')]}")
    print(f"{cid:7s} {task} {j} {label}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:3])}  "
          f"[{how['hand']} by hand, {how['state evaluator']} by the state's own rule, {how['engine only']} engine only]")
    print("\n".join(lines[:14]))
    if bad:
        FAIL.append(cid)
    return req, data, ip, preds


def live(client, raas_mod, cid, req, data, ip, preds):
    (gc.OUT / f"chunk24_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:7s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return None
    (gc.OUT / f"chunk24_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if not m.same(v, 0))
        w = sorted(D(str(v)) for v in want if v is not None and not isinstance(v, str) and not m.same(v, 0))
        if iso != w:
            pbad.append((rec, iso, w))
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not dd and not pbad and mi == mo
    print(f"  {cid:7s} {'AGREE' if ok else 'DIFFER'}: Builders Risk records as derived {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
          + "".join(f"\n        derived {rr[-50:]}: ISO {[str(v) for v in i_]} ours {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:5])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:5])
          + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
    if not ok:
        FAIL.append(f"{cid} live")
    return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    ap.add_argument("--states", help="comma list for the state policies (default: the 16 rewriting states)")
    ap.add_argument("--all", action="store_true", help="all 46 states")
    a = ap.parse_args()
    states = s18.STATES if a.all else (a.states.split(",") if a.states else STATES16)
    cs = cases(states)
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    elif a.states or a.all:
        cs = {k: v for k, v in cs.items() if k.startswith("S-")}
    client = raas_mod = None
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
    for i, (cid, case) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"{cid}")
        try:
            req, data, ip, preds = predict(cid, case)
        except Exception as exc:
            print(f"{cid}: RAISED {type(exc).__name__}: {str(exc)[:200]}")
            FAIL.append(cid)
            continue
        if a.live:
            live(client, raas_mod, cid, req, data, ip, preds)
        del data, ip
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C24-18..C24-21): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
