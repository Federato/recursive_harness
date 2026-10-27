#!/usr/bin/env python3
"""Chunk 24, RC-3 (C24-14..C24-17): Builders Risk zero cases, messages, shared names and exclusions. Live ISO.

Every case is predicted before it runs, from the rule text: each Builders Risk premium three ways (224_ / 225_'s hand
models with the container rates by hand, 174_'s evaluator, the engine), plus the (level, message) pairs the rules must
and must not raise. Predictions run on the request ISO receives (225_'s path), so the policy dates match.

  C24-14 zero cases   Z1 theft with no limit; Z2 reporting form with no limit; Z3 a Builders Risk building limit beside
                      a reporting form (message, and the reporting form's rates move with the building's LOI); Z4 a
                      premium adjustment period from the expiration date (0 days: ProRate 0); Z5 a period that starts
                      AFTER expiration (ProRate negative: the premium goes negative, as written); Z6 a period of NewValue
                      0 (FormAnnual 0 < preceding: $0); Z7 materials of others on with no manual premium, and off with
                      one; Z8 collapse with no option, and on the Basic cause; Z9 renovations with no limit; Z10 CP 10 44
                      with no Special deductible (factor 0) and "Not Applicable" (the building's Special deductible
                      factor); Z11 EQ "No Coverage" on the reporting form
  C24-15 messages     M1 the five "only valid with Builders Risk Coverage" forms on an ordinary building; M2 CP 11 20 / 11 21
                      on a Standard Property Policy; M3 collapse on the Basic cause; M4 / M4b the $500 minimum (250 fires,
                      500 silent); M5 class 1150 on CovType Building; M6 renovations on "No Coverage"; M7 Agreed Value with
                      renovations, and with a reporting form; M8 a Builders Risk building with no limit and no reporting
                      form; M9 the 2% EQ deductible off class 1150; M10 CP 10 44 on Broad / on a Builders Risk building /
                      on a Standard Property Policy; M11 CP 10 44 Special deductible below the building's theft
                      deductible; M12 a period whose covered causes differ from the building's (and equal: silent);
                      M13 a Builders Risk blanket whose limit is not the sum of the reporting limits, and one mixing
                      CP 11 05 with no CP 11 05; NY U / V / W both ways; KS / AL / RI Public and Institutional Plan
  C24-16 shared names S1 a submitted reporting-form rate and Factor (IsNull: survive); S2 a submitted ProRate (survives);
                      S3 a submitted CompletedValueMultiplier (no IsNull: overwritten); S4 a submitted BuildersRiskTheftRate
                      (survives); S5 a submitted BuildersRiskFactor on Business Income (survives)
  C24-17 exclusions   X1 the plain cyber exclusion and X2 the ensuing-causes one on every Builders Risk record;
                      X3 the wind / hail exclusion on renovations (Group II's factor)

    python scripts/cf/226_chunk24_rc3.py [--live] [--cases Z1,M4]
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import re
import sys
import time
from datetime import date
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

import gl_engine.interp.interpreter as interp                             # noqa: E402

c2 = import_module("225_chunk24_rc2")
x, t2 = c2.x, c2.t2
m, rc1, rep, cmp, gc, r11 = x.m, x.rc1, x.rep, x.cmp, x.gc, c2.r11
P, D, val, d, r = x.P, Decimal, x.val, x.d, x.r
TH, MO, CP1044, RF, RN, PA, PAD, COL = x.TH, x.MO, x.CP1044, x.RF, x.RN, x.PA, x.PAD, x.COL
BR = x.BR
FAIL = []
ZERO = "zero"
r11.NUMERIC |= {"BuildersRiskTheftRate", "BasicGroupIRate", "Factor", "ProRate", "CompletedValueMultiplier", "BuildersRiskFactor"}
L = {"ST": P + "Structure", "POL": P, "PAD": P + PAD, "CP1044": P + CP1044, "OC": P + "OccupClass", "BI": P + "BusinessIncome"}

c23 = import_module("221_chunk23_rc3")               # imported first: it wraps MessageHelper too
lvl, iso_tagged = c23.lvl, c23.iso_tagged
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ builders

def st(sub, i=0):
    return sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0][P + "StructureTable"][P + "Structure"][i]


def cp(sub):
    return sub[P + "Table"][P][0]


def b(j="OR", cause="Special", recs=None, building=False, keep_occ=False, st_over=None, fns=()):
    def f():
        sub = x.br_tree(j=j, cause=cause, recs=recs, building=building, keep_occ=keep_occ, st_over=st_over)
        for fn in fns:
            fn(sub)
        return sub
    return f


def setst(**kw):
    return lambda sub: st(sub).update(kw)


def setcp(**kw):
    return lambda sub: cp(sub).update(kw)


def setrec(rec, **kw):
    def f(sub):
        tab = st(sub).get(P + rec + "Table")
        rows = tab[P + rec] if tab else [st(sub)[P + rec]]
        for row in rows:
            for k, v in kw.items():
                if v is None:
                    row.pop(k, None)
                else:
                    row[k] = v
    return f


def periods(rows):
    return lambda sub: x.add_periods(sub, rows)


def cyber(kind):
    tab = "CyberIncidentExclusion" if kind == "plain" else "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"
    return lambda sub: cp(sub).update({P + tab + "Table": {P + tab: [{}]}})


def blanket(total, mixed=False):
    """two Builders Risk buildings in one Average blanket of Type 'Builders Risk', each with a reporting form 400,000 /
    300,000 (mixed: the second without CP 11 05)."""
    def f(sub):
        cpd = cp(sub)
        cpd["BlktRated"], cpd["MUBlktRated"] = "Yes", "No"
        loc = cpd[P + "LocationTable"][P + "Location"][0]
        sts = loc[P + "StructureTable"][P + "Structure"]
        s2 = copy.deepcopy(sts[0])
        if mixed:
            s2.pop(P + RF + "Table", None)
            s2["Limit"] = "300000"
        else:
            s2[P + RF + "Table"][P + RF][0]["Limit"] = "300000"
        sts.append(s2)
        for s_ in sts:
            s_.update({"IncludedInBlkt": "Yes", "BlktIDNum": "100"})
        cpd[P + "BlanketRatingTable"] = {P + "BlanketRating": [{P + "BlanketRatingDetailTable": {P + "BlanketRatingDetail": [{
            "UnitNumber": "100", "TypeOfBlanketRating": "Average", "Type": "Builders Risk", "Coinsurance": "100%",
            "CauseOfLoss": "Special", "TotalLimit": str(total)}]}}]}
    return f


RFL = {RF: {"Limit": "400000"}}
FR = "Fire Resistive - Reinforced Masonry - Other Than Light Steel"
NOT_BR = "only valid with Builders Risk Coverage"


def cases():
    no_ = []
    return {
        # ---------------------------------------------------------------- C24-14 zero cases
        "Z1": ("C24-14", "OR", "theft with no limit", b(recs={**RFL, TH: {}}), [TH], no_, no_),
        "Z2": ("C24-14", "OR", "reporting form with no limit", b(recs={RF: {}}), [RF + g + "Coverage" for g in x.GROUPS],
               no_, [("ST", "When CP 11 05 is attached the entry for Building Limit should be 0")]),
        "Z3": ("C24-14", "OR", "a building limit 100,000 beside a reporting form: message; reporting rates on the building's LOI",
               b(recs=RFL, fns=[setst(Limit="100000")]), [], [("ST", "When CP 11 05 is attached the entry for Building Limit should be 0")], no_),
        "Z4": ("C24-14", "OR", "a period starting ON the expiration date (0 days: ProRate 0)",
               b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2027"}])]),
               [PAD + g + "Coverage" for g in x.GROUPS], no_, no_),
        "Z5": ("C24-14", "OR", "a period starting AFTER expiration (ProRate negative: negative premiums, as written)",
               b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "12/17/2027"}])]), [], no_, no_),
        "Z6": ("C24-14", "OR", "a period with NewValue 0 (FormAnnual 0 < preceding: $0)",
               b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "0", "ComputedFromDate": "09/17/2026"}])]),
               [PAD + g + "Coverage" for g in x.GROUPS], no_, no_),
        "Z7": ("C24-14", "OR", "materials of others on with no manual premium", b(recs={**RFL, MO: {"Indicator": "Yes"}}), [MO], no_, no_),
        "Z7b": ("C24-14", "OR", "materials of others OFF (Indicator No) with a manual premium 250",
                b(recs={**RFL, MO: {"Indicator": "No", "ManualPremium": "250"}}), [MO], no_, no_),
        "Z8": ("C24-14", "OR", "collapse with no option", b(recs={**RFL, COL: {}}), [COL], no_, no_),
        "Z8b": ("C24-14", "OR", "collapse on the Basic cause: $0 + message", b(cause="Basic", recs={**RFL, COL: {"CollapseOptionConverted": "Option3"}}),
                [COL], [("ST", "CP 11 20 not valid with selected Cause of Loss")], no_),
        "Z9": ("C24-14", "OR", "renovations with no limit", b(recs={RN: {"ConstructionType": "Frame", "RatingType": "Class"}}, building=True),
               [RN + g + "Coverage" for g in x.GROUPS], no_, no_),
        "Z10": ("C24-14", "OR", "CP 10 44 with no Special deductible (factor 0)", b(recs={CP1044: {"Limit": "40000"}}, building=True), [CP1044], no_, no_),
        "Z10b": ("C24-14", "OR", "CP 10 44 Special deductible 'Not Applicable' (the building's Special deductible factor)",
                 b(recs={CP1044: {"Limit": "40000", "SpecialDed": "Not Applicable"}}, building=True), [], no_, no_),
        "Z11": ("C24-14", "OR", "EQ 'No Coverage' on a reporting-form building", b(recs=RFL, fns=[setst(EQCovIndicator="No Coverage")]),
                [RF + "EarthquakeCoverage"], no_, no_),
        # ---------------------------------------------------------------- C24-15 messages
        "M1": ("C24-15", "OR", "CP 11 05 / 11 14 / 11 15 / 11 20 / 11 21 on an ordinary building",
               b(recs={**RFL, BR + "SeparateOrSubContractorsExclusion": {}, BR + "SeparateOrSubContractorsCoverage": {},
                       COL: {"CollapseOptionConverted": "Option3"}, TH: {"Limit": "50000"}}, building=True), [],
               [("ST", f"CP 11 05 {NOT_BR}"), ("ST", f"CP 11 14 {NOT_BR}"), ("ST", f"CP 11 15 {NOT_BR}"), ("ST", f"CP 11 20 {NOT_BR}"),
                ("ST", f"CP 11 21 {NOT_BR}")], no_),
        "M1b": ("C24-15", "OR", "the same five on a Builders Risk building: silent",
                b(recs={**RFL, BR + "SeparateOrSubContractorsExclusion": {}, BR + "SeparateOrSubContractorsCoverage": {},
                        COL: {"CollapseOptionConverted": "Option3"}, TH: {"Limit": "50000"}}), [], no_, [("ST", NOT_BR)]),
        "M2": ("C24-15", "OR", "CP 11 20 / 11 21 on a Standard Property Policy",
               b(recs={**RFL, COL: {"CollapseOptionConverted": "Option3"}, TH: {"Limit": "50000"}}, fns=[setcp(PolicyType="Standard Property Policy")]),
               [], [("ST", "CP 11 20 is not valid with the Standard Property Policy"), ("ST", "CP 11 21 is not valid with the Standard Property Policy")], no_),
        "M4": ("C24-15", "OR", "class 1150 with a 250 deductible", b(recs=RFL, fns=[setst(Deductible="250")]), [],
               [("ST", "Minimum deductible for Builders Risk is $500")], no_),
        "M4b": ("C24-15", "OR", "class 1150 with a 500 deductible: silent", b(recs=RFL, fns=[setst(Deductible="500")]), [], no_,
                [("ST", "Minimum deductible for Builders Risk")]),
        "M5": ("C24-15", "OR", "class 1150 on CovType Building", b(recs=RFL, fns=[setst(CovType="Building", Limit="100000")]), [],
               [("ST", "Class Code 1150 requires a Coverage type of either Builders Risk or No Coverage")], no_),
        "M6": ("C24-15", "OR", "renovations on CovType No Coverage", b(recs={RN: {"Limit": "300000", "ConstructionType": "Frame", "RatingType": "Class"}},
                                                                       building=True, fns=[setst(CovType="No Coverage")]), [],
               [("ST", "CP 11 13 Not Valid with Selected Coverage Type")], no_),
        "M7": ("C24-15", "OR", "Agreed Value on a building with renovations and a reporting form",
               b(recs={RN: {"Limit": "300000", "ConstructionType": "Frame", "RatingType": "Class"}, **RFL}, building=True,
                 fns=[setst(AgreedValueOption="Yes")]), [],
               [("ST", "Agreed Value Coverage is not valid with Builders Risk Coverage"), ("ST", "Agreed Value Coverage is not valid with CP 11 05")], no_),
        "M8": ("C24-15", "OR", "a Builders Risk building with no limit and no reporting form", b(recs={TH: {"Limit": "50000"}}), [],
               [("ST", "Please enter a valid entry for Building Limit")], no_),
        # EQ class C1: the only class EQPercentageDeductibleFactor files a 2% row for (on A1 ISO refuses and ours prices the EQ
        # endorsement $0 with no factor: OI-103's pattern, first sent 2026-10-01)
        "M9": ("C24-15", "OR", "the 2% EQ deductible on an ordinary building (EQ class C1)", b(building=True, fns=[setst(EQDeductible="2%", EQClass="C1")]), [],
               [("ST", "The 2% EQ Deductible applies only when Class Code is 1150 and EQ Construction Class is C1")], no_),
        "M9b": ("C24-15", "OR", "the 2% EQ deductible on class 1150, EQ class C1: silent", b(recs=RFL, fns=[setst(EQDeductible="2%", EQClass="C1")]), [], no_,
                [("ST", "The 2% EQ Deductible")]),
        "M10": ("C24-15", "OR", "CP 10 44 on the Broad cause", b(cause="Broad", recs={CP1044: {"Limit": "40000", "SpecialDed": "1,000"}}, building=True),
                [], [("ST", "CP 10 44 not valid with the selected Cause of Loss")], no_),
        "M10b": ("C24-15", "OR", "CP 10 44 on a Builders Risk building", b(recs={**RFL, CP1044: {"Limit": "40000", "SpecialDed": "1,000"}}), [],
                 [("ST", "CP 10 44 valid only with coverage types Building or Improvements and Betterments or Condominium Association")], no_),
        "M10c": ("C24-15", "OR", "CP 10 44 on a Standard Property Policy", b(recs={CP1044: {"Limit": "40000", "SpecialDed": "1,000"}}, building=True,
                                                                             fns=[setcp(PolicyType="Standard Property Policy")]), [],
                 [("ST", "CP 10 44 not valid with Standard Property Policy")], no_),
        "M11": ("C24-15", "OR", "CP 10 44 Special deductible 250 below the building's theft deductible 1,000",
                b(recs={CP1044: {"Limit": "40000", "SpecialDed": "250"}}, building=True, fns=[setst(TheftDeductible="1,000")]), [],
                [("CP1044", "Special Deductible cannot be smaller than Structure's Theft Deductible.")], no_),
        "M12": ("C24-15", "OR", "a period whose covered causes (Broad) differ from the building's (Special)",
                b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026", "CoveredCausesOfLoss": "Broad"}])]),
                [], [("PAD", "Covered Cause Of Loss selected needs to be the same as the Risk's Cause of Loss")], no_),
        "M12b": ("C24-15", "OR", "the same with Special: silent",
                 b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026", "CoveredCausesOfLoss": "Special"}])]),
                 [], no_, [("PAD", "Covered Cause Of Loss selected")]),
        "M13": ("C24-15", "OR", "a Builders Risk blanket of 600,000 over reporting limits 400,000 + 300,000",
                b(recs=RFL, fns=[blanket(600000)]), [], [("POL", "Please enter a Blanket Limit that equals the sum of all Builders Risk Reporting Form Limits")], no_),
        "M13b": ("C24-15", "OR", "the blanket at 700,000 (the sum): silent; the blanketed reporting form prices on the blanket average",
                 b(recs=RFL, fns=[blanket(700000)]), [], no_, [("POL", "Please enter a Blanket Limit")]),
        "M13c": ("C24-15", "OR", "a Builders Risk blanket mixing CP 11 05 with no CP 11 05",
                 b(recs=RFL, fns=[blanket(700000, mixed=True)]), [], [("POL", "If any item in a Builders Risk blanket has CP 11 05, then all items must have CP 11 05")], no_),
        "NY1": ("C24-15", "NY", "NY Builders Risk building with no Group II symbol", b(j="NY", recs=RFL), [],
                [("ST", "Builders Risk Structure must have a Basic Group II Symbol of U, V or W")], no_),
        "NY2": ("C24-15", "NY", "NY Builders Risk building with symbol U: silent", b(j="NY", recs=RFL, fns=[setst(BasicGroupIISymbol="U")]), [], no_,
                [("ST", "Basic Group II Symbol of U, V or W")]),
        "NY3": ("C24-15", "NY", "NY ordinary building with symbol V", b(j="NY", building=True, fns=[setst(BasicGroupIISymbol="V")]), [],
                [("ST", "Non Builders Risk Structure cannot have a Basic Group II Symbol of U, V or W")], no_),
        "KS1": ("C24-15", "KS", "KS Public and Institutional Plan on a Builders Risk building with CP 11 05",
                b(j="KS", recs=RFL, fns=[setst(PublicInstitutionalPlanApply="Yes")]), [],
                [("ST", "CP 11 05 is not valid when Public And Institutional Property Plan Applies"), ("ST", "Public And Institutional Property Plan is not valid with Builders Risk")], no_),
        "AL1": ("C24-15", "AL", "AL the same", b(j="AL", recs=RFL, fns=[setst(PublicInstitutionalPlanApply="Yes")]), [],
                [("ST", "CP 11 05 not valid when Public And Institutional Property Plan Apply is Yes"), ("ST", "Public Institutional Plan not valid with Builders Risk")], no_),
        "RI1": ("C24-15", "RI", "RI the same", b(j="RI", recs=RFL, fns=[setst(PublicInstitutionalPlanApply="Yes")]), [],
                [("ST", "CP 11 05 not valid when Public And Institutional Property Plan Apply Equals Yes"), ("ST", "Public Institutional Plan not valid with Builders Risk")], no_),
        # ---------------------------------------------------------------- C24-16 shared names
        "S1": ("C24-16", "OR", "submitted reporting-form Group I rate 0.1 and Factor 2.0 (IsNull guards: both survive)",
               b(recs={RF: {"Limit": "400000", "BasicGroupIRate": "0.1", "Factor": "2.0"}}), [], no_, no_),
        "S2": ("C24-16", "OR", "a submitted ProRate 0.5 on a period from the effective date (survives)",
               b(recs=RFL, fns=[periods([{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": "09/17/2026", "ProRate": "0.5"}])]), [], no_, no_),
        "S3": ("C24-16", "OR", "a submitted CompletedValueMultiplier 3.0 on renovations (no IsNull guard: overwritten to 1.36)",
               b(recs={RN: {"Limit": "300000", "ConstructionType": "Frame", "RatingType": "Class", "CompletedValueMultiplier": "3.0"}}, building=True), [], no_, no_),
        "S4": ("C24-16", "OR", "a submitted BuildersRiskTheftRate 0.02 (survives)", b(recs={**RFL, TH: {"Limit": "50000", "BuildersRiskTheftRate": "0.02"}}), [], no_, no_),
        # ---------------------------------------------------------------- C24-17 exclusions
        "X1": ("C24-17", "OR", "every Builders Risk record + the plain cyber exclusion",
               b(recs={**RFL, TH: {"Limit": "2000000"}, COL: {"CollapseOptionConverted": "Option1"}}, fns=[setrec(RF, Limit="20000000"), cyber("plain")]), [], no_, no_),
        "X2": ("C24-17", "OR", "the same + the ensuing-causes cyber exclusion",
               b(recs={**RFL, TH: {"Limit": "2000000"}, COL: {"CollapseOptionConverted": "Option1"}}, fns=[setrec(RF, Limit="20000000"), cyber("col")]), [], no_, no_),
        "X3": ("C24-17", "OR", "renovations + the wind / hail exclusion",
               b(recs={RN: {"Limit": "3000000", "ConstructionType": "Frame", "RatingType": "Class"}, "WindstormOrHailExclusion": {}}, building=True),
               [], no_, no_),
    }


# ------------------------------------------------------------------ checks

def count_hits(tagged, level, frag):
    return sum(1 for t, y in tagged if t == level and frag in y)


def check_msgs(tagged, must, mustnt):
    bad = []
    for (lv, frag), k in collections.Counter((L[a], f) for a, f in must).items():
        got = count_hits(tagged, lv, frag)
        if got != k:
            bad.append(f"{lv.replace(P, '') or 'policy'}: {frag[:70]} ({got}, predicted {k})")
    for a, f in mustnt:
        if count_hits(tagged, L[a], f):
            bad.append(f"unexpected {L[a].replace(P, '') or 'policy'}: {f[:70]}")
    return bad


def request(j, build):
    return t2.state_req(t2.m20.payload(build()), j)


def predict(cid, case):
    task, j, label, build, zero_recs, must, mustnt = case
    req = request(j, build)
    c2.RF_OVR.clear()
    if cid == "S1":                                    # the submitted rate and Factor survive (IsNull guards)
        c2.RF_OVR.update({"Factor": D("2.0"), "BasicGroupIRate": D("0.1")})
    TAGGED.clear()
    data, ip = cmp.rate(req)
    tagged = [(lvl(t), y) for t, y in TAGGED]
    lines, bad = [], []
    c2.container_checks(data, lines, bad)
    preds = {}
    for rec in x.PREMIUM_RECS:
        res = x.predict(data, rec)
        preds[rec] = [hv for hv, _, _ in res]
        for hv, ev, e in res:
            ok = m.same(hv, e) and (ev is None or m.same(ev, e) or "ConversionSyntax" in str(ev))
            if rec in zero_recs and not m.same(e, 0):
                ok = False
            if not ok:
                bad.append(f"{rec} hand {hv} evaluator {ev} engine {e}")
            if not m.same(e, 0) or not ok or rec in zero_recs:
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-60:]:60s} hand {hv} evaluator {ev} engine {e}")
    c2.RF_OVR.clear()
    mbad = check_msgs(tagged, must, mustnt)
    print(f"{cid:5s} {task} {j} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS ' + '; '.join((bad + mbad)[:4])}")
    print("\n".join(lines[:16]))
    if bad or mbad:
        FAIL.append(cid)
    return req, data, ip, preds


def live(client, raas_mod, cid, case, req, data, preds):
    task, j, label, build, zero_recs, must, mustnt = case
    (gc.OUT / f"chunk24_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:5s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk24_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    TAGGED.clear()
    data, ip = cmp.rate(req)
    ours = collections.Counter((lvl(t), y) for t, y in TAGGED)
    isos = collections.Counter(iso_tagged(resp))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if not m.same(v, 0))
        w = sorted(D(str(v)) for v in want if not isinstance(v, str) and not m.same(v, 0))
        if iso != w:
            pbad.append((rec, iso, w))
    mreq = check_msgs(list(isos.elements()), must, mustnt)
    ok = not pbad and not dd and ours == isos and not mreq
    print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: Builders Risk records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
          + (f"; against the prediction: {mreq}" if mreq else "")
          + "".join(f"\n        predicted {rr[-55:]}: ISO {[str(v) for v in i_]} derived {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + "".join(f"\n        ISO only {t.replace(P, '') or 'policy'}: {y[:100]} x{n}" for (t, y), n in (isos - ours).items())
          + "".join(f"\n        ours only {t.replace(P, '') or 'policy'}: {y[:100]} x{n}" for (t, y), n in (ours - isos).items()))
    if not ok:
        FAIL.append(f"{cid} live")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    got = {}
    for i, (cid, case) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"predict {cid}")
        try:
            got[cid] = predict(cid, case)
        except Exception as exc:
            print(f"{cid}: RAISED {type(exc).__name__}: {str(exc)[:200]}")
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (Builders Risk records as derived, every premium, the (level, message) multiset):")
        for i, (cid, case) in enumerate(cs.items(), 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                req, data, ip, preds = got[cid]
                live(client, raas_mod, cid, case, req, data, preds)
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C24-14..C24-17): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
