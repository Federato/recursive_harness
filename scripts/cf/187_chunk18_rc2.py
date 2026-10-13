#!/usr/bin/env python3
"""Chunk 18, RC-2 (C18-06 to C18-11): golden cases for the 84 records ISO never priced.

Every case sits on 175_'s policy (chunk 7's five-coverage Oregon policy, chunk 15's modifiers:
package 0.85, IRPM 1.15, credit 0.9, building credit 0.95, and chunk 10's earthquake election),
dated 09/17/2026 - 09/17/2027 (365 days) for the two period-rated families. The family's own
factors are looked up independently from the filed CSVs and substituted on the tree; SetPremium is
evaluated by hand (174_'s evaluator, half-up at every DecimalPlaces) with the parent coverage's rates
read from the tree (chunks 1-10, ISO-confirmed). The engine must equal it; --live ISO must equal it,
every premium on the policy compared field for field, messages compared.

  Agreed Value (C18-06)   factor 1.05 (BI / SCBI 1.10): round3(factor - 1) x rate x limit / 100
    A1  unblanketed, Special + EQ, all five coverages; AgreedValueLimit 80,000 (the coverage limits are
        100,000: the premium must read the AGREED limit, not LimitToUse)
    A2  the same on the Broad cause
    A3  blanketed: chunk 9's two-building blanket with the detail's AgreedVal "Yes" -> the blanket's
        ...AvgRateAgreedVal x LimitToUse (read from the tree, chunk 9's machinery; ISO settles)
    A4  Leased Property (contents -> LeasedProperty -> LeasedPropertyDetail): switched on by the CONTENTS
        row's AgreedValueOption (the detail copies it), 0.05 x the contents' final rate x the item's limit
  Inflation Guard (C18-07)  a factor x the coverage record's FINISHED premium:
    I1  building 6% (0.03), contents 20% (0.10), special class 12% (0.06); Special + EQ
  Functional Valuation (C18-08)  rate x (Factor x PostLossFactor - 1) x limit / 100
    F1  building 1.30 with the post-loss ordinance option (1.02: 1.326 - 1), contents 1.25; Special
        (ValuationType "Functional Valuation" attaches the containers, C18-03)
  Increase in Rebuilding Expenses (C18-09)  adjustment x form factor (BGI 0.10, BGII 0.15, ...) x
    the additional-expense amount / 100, the amount = value x the converted percentage
    R1  building and special class at 1,000,000, 25% (0.25): 7% of 100,000 rounds Group II / Special to $0
  Vacancy Permit (C18-10)  round0(vacancy rate x limit / 100 + vandalism premium x package) x credit
    x IRPM x pro-rata x cyber; vacancy rate = max(min rate, adjusted rate x 0.13 / 0.04 / 0.053 ...)
    V1  building 11/01/2026 - 01/30/2027 (90 days: 0.247), contents 10/01/2026 - 03/31/2027 (181: 0.496)
  Peak Season (C18-11)  (premium at the total limit - at the base limit) x the season's pro-rata
    P1  contents, 30,000 extra, 11/01/2026 - 12/31/2026 (60 days: round3(60 / 365) = 0.164)

    python scripts/cf/187_chunk18_rc2.py [--live] [--cases A1,V1]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from gl_engine.interp.values import InterpretError                       # noqa: E402

r2 = import_module("175_chunk16_rc2")
bl = import_module("68_chunk9_golden_case")
gc, rc1, rep, cmp, r16, r11 = r2.gc, r2.rc1, r2.rep, r2.cmp, r2.r16, r2.r11
P = r2.P
row, q, put, same = r2.row, r2.q, r2.put, r2.same
# ISO types these as numbers and refuses a string (first live run, 2026-09-28); chunk 9's live script
# already sent the blanket's UnitNumber / BlktIDNum / TotalLimit as integers
r11.NUMERIC |= {"AgreedValueLimit", "UnitNumber", "BlktIDNum", "TotalLimit", "FullValue"}
FAIL = []
EFF, EXP = "09/17/2026", "09/17/2027"
TERM = (date(2027, 9, 17) - date(2026, 9, 17)).days                   # 365


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def days(a, b):
    ma, da, ya = map(int, a.split("/"))
    mb, db, yb = map(int, b.split("/"))
    return (date(yb, mb, db) - date(ya, ma, da)).days


def prorate(a, b):
    return q(Decimal(days(a, b)) / Decimal(TERM), 3)


# ------------------------------------------------------- independent factors

AV = row("AgreedValueFactor", "Factor", StateCode="CW", Constant="Y")
AV_BI = row("AgreedValueFactorBusnIncome", "Factor", StateCode="CW", Constant="Y")
IG = lambda pct: row("InflationGuardBldg", "Factor", StateCode="CW", InflationGuardBldg=pct)
FVF = lambda cov: row("FunctionalValuationFactor", "Factor", StateCode="CW", CovType=cov)
POSTLOSS = row("PostLossOrdinanceOrLawOptionFactor", "Factor", StateCode="CW", Constant="Y")
REF = lambda cause: row("RebuildingExpensesFactor", "Factor", StateCode="CW", CauseOfLoss=cause)
REPCT = lambda pct: row("AdditionalExpenseCoveragePercentageConverted", "Percentage", StateCode="CW",
                        AdditionalExpenseCoveragePercentage=pct)
VPF = lambda cause: row("VacancyPermitFactors", "Factor", StateCode="CW", PolicyType="Commercial Property Policy",
                        VacancyCauseOfLoss=cause)
FORMS = {"BasicGroupI": "Basic Group I", "BasicGroupII": "Basic Group II", "Broad": "Broad", "Special": "Special",
         "Earthquake": "Earthquake"}
PARENTS = ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome")
AVREC = {"Structure": "StructureAgreedVal", "PersonalProperty": "PersonalPropertyAgreedVal",
         "BusinessIncome": "BusinessIncomeAgreedVal", "SpecialClass": "SpecialClassAgreedVal",
         "SpecialClassBusnIncome": "SpecialClassBusnIncomeAgreedVal"}
IGREC = {"Structure": "StructureInflationGuard", "PersonalProperty": "PersonalPropertyInflationGuard",
         "SpecialClass": "SpecialClassInflationGuard"}


# ---------------------------------------------------------------- policies

def at(sub):
    return rc1.node_dicts(sub)


def base(cause="Special", dated=False):
    sub = r2.base()
    a = at(sub)
    for k in PARENTS:
        a[P + k]["CauseOfLoss"] = cause
    if dated:
        sub["EffDate"], sub["ExpDate"] = EFF, EXP
        a[P].update({"EffectiveDt": EFF, "ExpirationDt": EXP})
    return sub


def forms_for(cause):
    return ["BasicGroupI", "BasicGroupII", {"Broad": "Broad", "Special": "Special"}.get(cause), "Earthquake"]


def av_case(cause):
    def build():
        sub = base(cause)
        a = at(sub)
        for k in PARENTS:
            a[P + k].update({"AgreedValueOption": "Yes", "AgreedValueLimit": "80000"})
            for f in forms_for(cause):
                if f:
                    put(sub, f"{AVREC[k]}{f}Coverage")
        return sub
    recs = {f"{AVREC[k]}{f}Coverage": {"Factor": AV_BI if k in ("BusinessIncome", "SpecialClassBusnIncome") else AV}
            for k in PARENTS for f in forms_for(cause) if f}
    return build, recs


def a3():
    sub = bl.submission()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp.update(r2.rc2.POLICY)
    det = cp["CommercialPropertyBlanketRatingTable"]["CommercialPropertyBlanketRating"][0][
        "CommercialPropertyBlanketRatingDetailTable"]["CommercialPropertyBlanketRatingDetail"][0]
    det["AgreedVal"] = "Yes"
    for st in cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0][
            "CommercialPropertyStructureTable"]["CommercialPropertyStructure"]:
        st.setdefault("WindstormOrHailDeductible", "1,000")
        st[P + "StructureAgreedValBasicGroupICoverage"] = {}
    return sub


def a4():
    """the detail COPIES its AgreeValueOption from the contents row's AgreedValueOption (../../../../),
    overwriting its own (engine pass 1: the detail's input vanished and every form priced $0)."""
    sub = base("Special")
    pp = at(sub)[P + "PersonalProperty"]
    pp["AgreedValueOption"] = "Yes"
    pp[P + "LeasedPropertyTable"] = {P + "LeasedProperty": [{
        P + "LeasedPropertyDetailTable": {P + "LeasedPropertyDetail": [{
            "AgreeValueOption": "Yes", "Limit": "200000",
            **{f"{P}LeasedPropertyDetailAgreedValue{f}Cov": {} for f in ("BasicGroupI", "BasicGroupII", "Special")}}]}}]}
    return sub


def i1():
    sub = base("Special")
    a = at(sub)
    pcts = {"Structure": "6%", "PersonalProperty": "20%", "SpecialClass": "12%"}
    for k, pct in pcts.items():
        a[P + k]["InflationGuard"] = pct
        for f in forms_for("Special"):
            put(sub, f"{IGREC[k]}{f}Coverage")
    return sub


I1_RECS = {f"{IGREC[k]}{f}Coverage": {"Factor": IG(p)}
           for k, p in {"Structure": "6%", "PersonalProperty": "20%", "SpecialClass": "12%"}.items()
           for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}


def f1():
    sub = base("Special")
    a = at(sub)
    a[P + "Structure"]["ValuationType"] = "Functional Valuation"
    a[P + "PersonalProperty"]["ValuationType"] = "Functional Valuation"
    for f in forms_for("Special"):
        put(sub, f"FunctionalBuildingValuation{f}Coverage")
        put(sub, f"FunctionalPersonalPropertyValuationOtherThanStock{f}Coverage")
    r2.container(sub, "Structure", "FunctionalBuildingValuation")["PostLossOrdinanceOrLawOption"] = "Yes"
    return sub


F1_RECS = {**{f"FunctionalBuildingValuation{f}Coverage": {"../Factor": FVF("Building"), "../PostLossFactor": POSTLOSS}
              for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")},
           # the CONTENTS container stores round3(BaseFactor - 1) (0.25); the BUILDING container keeps the raw
           # 1.30 and its premium subtracts 1 after the post-loss factor -- the two forms differ (engine pass 1)
           **{f"FunctionalPersonalPropertyValuationOtherThanStock{f}Coverage": {"../Factor": q(FVF("PersProp") - 1, 3)}
              for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}}

RE, RE_SC = "IncreaseInRebuildingExpensesFollowingDisaster", "IncreaseInRebuildingExpensesFollowingDisasterSpecialClass"
RE_FACTOR_FIELD = {"BasicGroupI": "RebuildingExpensesBGIFactor", "BasicGroupII": "RebuildingExpensesBGIIFactor",
                   "Broad": "RebuildingExpensesBroadFactor", "Special": "RebuildingExpensesSpecialFactor",
                   "Earthquake": "RebuildingExpensesEQFactor"}


def r1():
    """25% of a 1,000,000 building / special class: at 7% of 100,000 the Group II and Special forms round
    to $0 (0.004 x 7,000 / 100 = $0.28), which proves nothing (engine pass 1)."""
    sub = base("Special")
    a = at(sub)
    a[P + "Structure"].update({"Limit": "1000000", "FullBldgValue": "1000000"})
    a[P + "SpecialClass"].update({"Limit": "1000000"})
    for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"):
        put(sub, f"{RE}{f}Cov")
        put(sub, f"{RE_SC}{f}Cov")
    r2.container(sub, "Structure", RE)["AdditionalExpenseCoveragePercentage"] = "25%"
    r2.container(sub, "SpecialClass", RE_SC)["AdditionalExpenseCoveragePercentage"] = "25%"
    return sub


R1_RECS = {f"{n}{f}Cov": {RE_FACTOR_FIELD[f]: REF(FORMS[f]), "../AdditionalExpenseCoveragePercentageConverted": REPCT("25%")}
           for n in (RE, RE_SC) for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}

VP_PERIOD = {"VacancyPermit": ("11/01/2026", "01/30/2027"), "VacancyPermitPrsnlProp": ("10/01/2026", "03/31/2027")}


def v1():
    sub = base("Special", dated=True)
    for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"):
        put(sub, f"VacancyPermit{f}Coverage")
        put(sub, f"VacancyPermitPrsnlProp{f}Coverage")
    (fr, to) = VP_PERIOD["VacancyPermit"]
    r2.container(sub, "Structure", "VacancyPermit").update(
        {"PermitPeriodFrom": fr, "PermitPeriodTo": to, "Vandalism": "Yes", "SprinklerLeakage": "Yes"})
    (fr, to) = VP_PERIOD["VacancyPermitPrsnlProp"]
    r2.container(sub, "PersonalProperty", "VacancyPermitPrsnlProp").update(
        {"PermitPeriodFrom": fr, "PermitPeriodTo": to, "Vandalism": "No", "SprinklerLeakage": "No"})
    return sub


V1_RECS = {f"{n}{f}Coverage": {"../VacancyPermitProRateFactor": prorate(*VP_PERIOD[n])}
           for n in ("VacancyPermit", "VacancyPermitPrsnlProp") for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}
for n in ("VacancyPermit", "VacancyPermitPrsnlProp"):
    V1_RECS[f"{n}BasicGroupICoverage"]["../BasicGroupIFactor"] = VPF("Basic Group I")
    V1_RECS[f"{n}BasicGroupIICoverage"]["../BasicGroupIIFactor"] = VPF("Basic Group II")

PS_PERIOD = ("11/01/2026", "12/31/2026")


def p1():
    sub = base("Special", dated=True)
    for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"):
        put(sub, f"PeakSeasonLimitOfInsuranceDetail{f}Coverage")
    pp = at(sub)[P + "PersonalProperty"]
    det = pp[P + "PeakSeasonLimitOfInsuranceTable"][P + "PeakSeasonLimitOfInsurance"][0][
        P + "PeakSeasonLimitOfInsuranceDetailTable"][P + "PeakSeasonLimitOfInsuranceDetail"][0]
    det.update({"Limit": "30000", "FullValue": "30000", "PeriodFrom": PS_PERIOD[0], "PeriodTo": PS_PERIOD[1]})
    return sub


P1_RECS = {f"PeakSeasonLimitOfInsuranceDetail{f}Coverage": {"../PeakSeasonProRateFactor": prorate(*PS_PERIOD)}
           for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}


def cases():
    a1b, a1r = av_case("Special")
    a2b, a2r = av_case("Broad")
    return {
        "A1": ("C18-06", "Agreed Value, unblanketed, Special + EQ, five coverages, agreed limit 80,000", a1b, a1r),
        "A2": ("C18-06", "Agreed Value, unblanketed, Broad + EQ, five coverages", a2b, a2r),
        "A3": ("C18-06", "Agreed Value, blanketed (chunk 9's two-building blanket, AgreedVal Yes)", a3,
               {"StructureAgreedValBasicGroupICoverage": {"Factor": AV}}),
        "A4": ("C18-06", "Leased Property Agreed Value (contents), item limit 200,000", a4,
               {f"LeasedPropertyDetailAgreedValue{f}Cov": {"../AgreedValueFactor": q(AV - 1, 3)}
                for f in ("BasicGroupI", "BasicGroupII", "Special")}),
        "I1": ("C18-07", "Inflation Guard: building 6%, contents 20%, special class 12%, Special + EQ", i1, I1_RECS),
        "F1": ("C18-08", "Functional Valuation: building 1.30 x post-loss 1.02, contents 1.25, Special + EQ", f1, F1_RECS),
        "R1": ("C18-09", "Increase in Rebuilding Expenses 25%, building and special class at 1,000,000, Special + EQ", r1, R1_RECS),
        "V1": ("C18-10", "Vacancy Permit: building 90 days (vandalism, sprinkler), contents 181 days", v1, V1_RECS),
        "P1": ("C18-11", "Peak Season: contents +30,000 for 60 days", p1, P1_RECS),
    }


# ------------------------------------------------------------------- run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds, priced_total, rec_total = {}, 0, 0
    for i, (cid, (task, label, build, recs)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), "OR")
        except InterpretError as exc:
            print(f"{cid:3s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad, priced = [], [], 0
        preds[cid] = {}
        for rec, ov in recs.items():
            res, checks = r2.predict(data, rec, ov, "OR")
            # a record whose own switch is off is predicted $0 (ErcProcess writes 0), not hand-evaluated
            nodes_ = rc1.find(data, P + rec)
            if nodes_ and all(n.first("CoverageOnPolicyIndicator") is not None
                              and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_):
                res = [(Decimal(0), e) for _, e in res]
            fac_bad = [(f, e, v) for f, e, v in checks if not same(e, v)]
            ok = bool(res) and all(not str(h).startswith("hand") and same(h, e) for h, e in res) and not fac_bad
            nz = [h for h, e in res if e not in (None, "") and not same(e, 0)]
            priced += bool(nz)
            preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:66]:66s} predicted {[str(h) for h, _ in res]}"
                         f" engine {[e for _, e in res]}" + (f"  factor engine/independent {fac_bad[:2]}" if fac_bad else "")
                         + ("" if nz else "  ($0)"))
            if not ok:
                bad.append(rec)
        priced_total += priced
        rec_total += len(recs)
        print(f"{cid:3s} {task} {label}: engine {'as derived' if not bad else 'DIFFERS'} ({priced} of {len(recs)} priced)")
        print("\n".join(lines))
        if bad:
            FAIL.append(cid)
    print(f"\nengine: {priced_total} of {rec_total} predicted records price > $0")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, label, build, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            (gc.OUT / f"chunk18_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {cid:3s} ISO REFUSES {m.group(0)[:220] if m else str(exc.body)[:220]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk18_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid:3s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
