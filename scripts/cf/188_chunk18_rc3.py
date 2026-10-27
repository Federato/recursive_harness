#!/usr/bin/env python3
"""Chunk 18, RC-3 (C18-12 to C18-15): zero cases, messages, shared names, exclusion records.

Every case is one of RC-2's policies (187_) with one thing changed. Each record's expected
premium is predicted before the run: $0 where a rule forces it, otherwise a hand evaluation of
the filed rule with the family's own factor from its table (175_'s method). Message cases name
the message that must appear (or must not); --live compares every premium field for field and
the WHOLE message set with ISO's.

C18-12  ZERO CASES
  Z1  Agreed Value "Yes" with no AgreedValueLimit      -> every unblanketed form $0, no message (RC-1)
  Z2  Agreed Value "No" with a limit                   -> switched off, $0
  Z3  Inflation Guard "Not Applicable" / blank         -> $0
  Z4  Inflation Guard "Blanket Inflation Guard Value Applies", not blanketed -> factor 0.0, $0
  Z5  Functional Valuation containers on a "Replacement Cost" building -> DELETED (no record, no premium)
  Z6  Functional Valuation, post-loss option "No"      -> building 1.30 - 1 = 0.30 (not 0.326): priced by hand
  Z7  Rebuilding percentage blank                      -> converted 0.0 -> $0
  Z8  Vacancy period blank                             -> pro-rata never set -> 0.0 -> $0
  Z9  Vacancy period of zero days (From = To)          -> pro-rata 0.000 -> $0
  Z10 Vacancy period reversed (To 30 days before From) -> pro-rata -0.082 -> NEGATIVE premiums by hand
                                                          (+ "Period From date can not be after Period To date")
  Z11 Peak Season period blank                         -> $0
  Z12 Peak Season limit 0                              -> no difference -> $0
C18-13  MESSAGES (each triggered; ISO's full message set must equal ours)
  M1  Agreed Value on BI / SCBI + dependent-properties Broad (CP 15 08), Limited (CP 15 09), premium
      adjustment (CP 15 20) and SCBI limited international (CP 15 01)
  M2  Agreed Value on contents + Additional Locations special coinsurance (CP 13 20)
  M3  Agreed Value on a building with a Builders Risk renovations record (CP 11 05 / Builders Risk)
  M4  Vacancy Permit on a "No Coverage" building and a Legal Liability contents form
  M5  Vacancy Permit + Vacancy Changes (CP 04 60) on the same building and contents
  M6  Vacancy Permit, vandalism and sprinkler exclusions attached, their checkboxes "No"
  M7  Vacancy periods outside the policy term (From before, To after)
  M8  Peak Season + Value Reporting (CP 13 10, which attaches only on a reporting-frequency coinsurance)
  M8b Peak Season on a Legal Liability contents form (CovForm set on the occupancy)
  M9  Peak Season period reversed / outside the term
  M10 KS: Functional Valuation with the Public Institutional Plan
  M11 SC: ValuationLaw "Exemption Does Not Apply" (attaches CP 01 10): Functional Valuation; Agreed Value
C18-14  SHARED NAMES: probes
  S1  Agreed Value Factor 1.20 SUBMITTED on the building record  -> round3(1.20 - 1) = 0.20 is used
  S2  Vacancy pro-rata 0.5 SUBMITTED                              -> 0.5 is used (IsNull-guarded)
C18-15  EXCLUSION RECORDS
  X0  A1 at an agreed limit of 1,000,000 (control)
  X1  X0 + cyber-incident exclusion                  -> Agreed Value x 0.995 per group
  X2  I1 + cyber-incident exclusion                  -> Inflation Guard is a % of the FINISHED premium, which
                                                        already carries the exclusion: no second 0.995

    python scripts/cf/188_chunk18_rc3.py [--live] [--cases Z1,M5]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
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

g = import_module("187_chunk18_rc2")
r3 = import_module("176_chunk16_rc3")
r2, gc, rc1, rep, cmp, r16, r11 = g.r2, g.gc, g.rc1, g.rep, g.cmp, g.r16, g.r11
r11.NUMERIC |= {"Factor", "VacancyPermitProRateFactor"}       # the probes submit decimals
P = g.P
ZERO = r3.ZERO
mod, setp, setc, chain = r3.mod, r3.setp, r3.setc, r3.chain
q, row = g.q, g.row
CYBER = {f"CyberIncidentExclusionFactor{k}": row("CyberIncidentExclusionFactors", "Factor", StateCode="CW",
                                                 CausesOfLossOrPerilGroupPremium=n)
         for k, n in (("BGI", "Basic Group I"), ("BGII", "Basic Group II"), ("Broad", "Broad"),
                      ("Special", "Special"), ("EQ", "Earthquake"))}
REFUSE = "REFUSE:"
FAIL = []


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def at(sub):
    return rc1.node_dicts(sub)


def rec_on(parent, name, fields=None):
    """attach an empty (or filled) record table under a coverage record."""
    def fn(sub):
        at(sub)[P + parent][P + name + "Table"] = {P + name: [dict(fields or {})]}
    return fn


def vp_period(parent, name, fr, to):
    def fn(sub):
        g.r2.container(sub, parent, name).update({"PermitPeriodFrom": fr, "PermitPeriodTo": to})
    return fn


def drop(parent, name, *fields):
    """remove input fields from a container (a blank date must be ABSENT: ISO refuses "")."""
    def fn(sub):
        c = g.r2.container(sub, parent, name)
        for f in fields:
            c.pop(f, None)
    return fn


def ps_detail(**kw):
    def fn(sub):
        pp = at(sub)[P + "PersonalProperty"]
        det = pp[P + "PeakSeasonLimitOfInsuranceTable"][P + "PeakSeasonLimitOfInsurance"][0][
            P + "PeakSeasonLimitOfInsuranceDetailTable"][P + "PeakSeasonLimitOfInsuranceDetail"][0]
        for k, v in kw.items():
            if v is None:
                det.pop(k, None)
            else:
                det[k] = v
    return fn


def big_agreed(sub):
    for k in g.PARENTS:
        at(sub)[P + k]["AgreedValueLimit"] = "1000000"


def state_base(j):
    """175_'s policy made portable to state j (as 177_): for the KS / SC message cases."""
    def build():
        sub = r2.base(j)
        if j == "FL":
            at(sub)[P + "SpecialClass"]["ClassDescription"] = "Cooling Towers - Metal"
        return sub
    return build


A1B, A1R = g.av_case("Special")
AVSTR = {r: v for r, v in A1R.items() if r.startswith("StructureAgreedVal")}
VPB = [f"VacancyPermit{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Special")]
VPP = [f"VacancyPermitPrsnlProp{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Special")]
PSR = [f"PeakSeasonLimitOfInsuranceDetail{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Special")]
REB = [f"{g.RE}{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Special")]
FVB = [f"FunctionalBuildingValuation{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Special")]
IGALL = list(g.I1_RECS)
AVUNBL = [r for r in A1R if not r.endswith("EarthquakeCoverage")]


def vp_neg():
    """To 30 days BEFORE From: DateDifference is negative, pro-rata round3(-30 / 365) = -0.082."""
    return {r: {"../VacancyPermitProRateFactor": q(Decimal(-30) / Decimal(g.TERM), 3)} for r in VPB}


def cases():
    return {
        "Z1": ("C18-12", "Agreed Value Yes, no agreed limit", "OR",
               mod(A1B, chain(*[setp(k, AgreedValueLimit=None) for k in g.PARENTS])),
               dict.fromkeys(AVUNBL, ZERO), [], []),
        "Z2": ("C18-12", "Agreed Value No, with a limit", "OR",
               mod(A1B, chain(*[setp(k, AgreedValueOption="No") for k in g.PARENTS])),
               dict.fromkeys(AVUNBL, ZERO), [], []),
        "Z3": ("C18-12", "Inflation Guard Not Applicable (building) / blank (contents, special class)", "OR",
               mod(g.i1, chain(setp("Structure", InflationGuard="Not Applicable"),
                               setp("PersonalProperty", InflationGuard=None), setp("SpecialClass", InflationGuard=None))),
               dict.fromkeys(IGALL, ZERO), [], []),
        "Z4": ("C18-12", "Inflation Guard 'Blanket Inflation Guard Value Applies', not blanketed", "OR",
               mod(g.i1, chain(*[setp(k, InflationGuard="Blanket Inflation Guard Value Applies")
                                 for k in ("Structure", "PersonalProperty", "SpecialClass")])),
               dict.fromkeys(IGALL, ZERO), [], []),
        "Z5": ("C18-12", "Functional Valuation containers on Replacement Cost property (deleted)", "OR",
               mod(g.f1, chain(setp("Structure", ValuationType="Replacement Cost"),
                               setp("PersonalProperty", ValuationType="Replacement Cost"))),
               dict.fromkeys(list(g.F1_RECS), ZERO), [], []),
        "Z6": ("C18-12", "Functional Valuation, post-loss option No (1.30 - 1, not 1.326 - 1)", "OR",
               mod(g.f1, setc("Structure", "FunctionalBuildingValuation", PostLossOrdinanceOrLawOption="No")),
               {r: {"../Factor": g.FVF("Building"), "../PostLossFactor": Decimal("1.0")} for r in FVB}, [], []),
        "Z7": ("C18-12", "Rebuilding percentage blank", "OR",
               mod(g.r1, chain(setc("Structure", g.RE, AdditionalExpenseCoveragePercentage=""),
                               setc("SpecialClass", g.RE_SC, AdditionalExpenseCoveragePercentage=""))),
               dict.fromkeys(list(g.R1_RECS), ZERO), [], []),
        "Z8": ("C18-12", "Vacancy period blank", "OR",
               # the dates OMITTED: ISO refuses an empty string as "not a valid DateTime" (live run 1)
               mod(g.v1, chain(drop("Structure", "VacancyPermit", "PermitPeriodFrom", "PermitPeriodTo"),
                               drop("PersonalProperty", "VacancyPermitPrsnlProp", "PermitPeriodFrom", "PermitPeriodTo"))),
               dict.fromkeys(VPB + VPP, ZERO), [], []),
        "Z9": ("C18-12", "Vacancy period of zero days (From = To)", "OR",
               mod(g.v1, vp_period("Structure", "VacancyPermit", "11/01/2026", "11/01/2026")),
               dict.fromkeys(VPB, ZERO), [], []),
        "Z10": ("C18-12", "Vacancy period reversed (To 30 days before From): negative", "OR",
                mod(g.v1, vp_period("Structure", "VacancyPermit", "12/01/2026", "11/01/2026")),
                vp_neg(), ["CP 04 50 - Period From date can not be after Period To date"], []),
        "Z11": ("C18-12", "Peak Season period blank (dates omitted)", "OR", mod(g.p1, ps_detail(PeriodFrom=None, PeriodTo=None)),
                dict.fromkeys(PSR, ZERO), [], []),
        "Z12": ("C18-12", "Peak Season limit 0", "OR", mod(g.p1, ps_detail(Limit="0", FullValue="0")),
                dict.fromkeys(PSR, ZERO), [], []),
        "M1": ("C18-13", "Agreed Value + dependent properties / premium adjustment forms (BI, SCBI)", "OR",
               mod(A1B, chain(rec_on("BusinessIncome", "BusinessIncomeFromDependentPropertiesBroadForm"),
                              rec_on("BusinessIncome", "BusinessIncomeFromDependentPropertiesLimitedForm"),
                              rec_on("BusinessIncome", "BusinessIncomePremiumAdjustmentForm"),
                              rec_on("SpecialClassBusnIncome", "BusnIncomeFromDependentPropertiesLimitedInternationalCovSpclClassBusnIncome"),
                              rec_on("SpecialClassBusnIncome", "BusinessIncomeFromDependentPropertiesBroadFormSpclClassBusnIncome"))),
               {}, ["Agreed Value Coverage is not valid with CP 15 08", "Agreed Value Coverage is not valid with CP 15 09",
                    "Agreed Value Coverage is not valid with CP 15 20", "Agreed Value Coverage is not valid with CP 15 01"], []),
        "M2": ("C18-13", "Agreed Value on contents + Additional Locations special coinsurance (CP 13 20)", "OR",
               mod(A1B, rec_on("PersonalProperty", "AdditionalLocationsSpecialCoinsuranceProvisions")),
               {}, ["Agreed Value Coverage is not valid with CP 13 20"], []),
        "M3": ("C18-13", "Agreed Value on a building with a Builders Risk renovations record", "OR",
               mod(A1B, rec_on("Structure", "BuildersRiskRenovations")),
               {}, ["Agreed Value Coverage is not valid with"], []),
        "M4": ("C18-13", "Vacancy Permit on a No Coverage building; contents on the Legal Liability form", "OR",
               mod(g.v1, chain(setp("Structure", CovType="No Coverage"),
                               setp("PersonalProperty", CovForm="Legal Liability Coverage Form"))),
               {}, ["CP 04 50 not valid with selected Coverage"], []),
        "M5": ("C18-13", "Vacancy Permit + Vacancy Changes (CP 04 60), building and contents", "OR",
               mod(g.v1, chain(rec_on("Structure", "VacancyChanges"), rec_on("PersonalProperty", "VacancyChangesPrsnlProp"))),
               {}, ["CP 04 60 and CP 04 50 cannot be written on the same property"], []),
        "M6": ("C18-13", "Vacancy Permit, vandalism / sprinkler exclusions attached, checkboxes No", "OR",
               mod(g.v1, chain(rec_on("Structure", "VandalismExclusion"), rec_on("Structure", "SprinklerLeakageExclusion"),
                               setc("Structure", "VacancyPermit", Vandalism="No", SprinklerLeakage="No"))),
               {}, ["The Excepted Causes of Loss - Vandalism checkbox must be checked",
                    "The Excepted Causes of Loss - Sprinkler Leakage checkbox must be checked"], []),
        "M7": ("C18-13", "Vacancy periods outside the policy term", "OR",
               mod(g.v1, chain(vp_period("Structure", "VacancyPermit", "08/01/2026", "01/30/2027"),
                               vp_period("PersonalProperty", "VacancyPermitPrsnlProp", "10/01/2026", "12/31/2027"))),
               {}, ["CP 04 50 - Period From date must be within policy period",
                    "CP 04 50 - Period To date must be within policy period"], []),
        # Value Reporting (CP 13 10) attaches only on a reporting-frequency coinsurance and is deleted
        # otherwise; a contents row's CovForm is copied from its OCCUPANCY (C15 lesson). Engine pass 1
        # set neither and both messages stayed silent.
        "M8": ("C18-13", "Peak Season + Value Reporting (CP 13 10: contents coinsurance Monthly Reporting)", "OR",
               mod(g.p1, setp("PersonalProperty", Coinsurance="Monthly Reporting")),
               {}, ["CP 12 30 not valid with CP 13 10"], []),
        "M8b": ("C18-13", "Peak Season on the Legal Liability form (set on the occupancy)", "OR",
                mod(g.p1, setp("OccupClass", CovForm="Legal Liability Coverage Form")),
                {}, ["CP 12 30 not valid with the selected Coverage Form"], []),
        "M9": ("C18-13", "Peak Season period reversed, and outside the term", "OR",
               mod(g.p1, ps_detail(PeriodFrom="12/31/2027", PeriodTo="11/01/2027")),
               {}, ["CP 12 30 - Period From date can not be after Period To date",
                    "CP 12 30 - Period From date must be within policy period"], []),
        "M10": ("C18-13", "KS: Functional Valuation with the Public Institutional Plan", "KS",
                mod(state_base("KS"), chain(setp("Structure", ValuationType="Functional Valuation", PublicInstitutionalPlanApply="Yes"),
                                            lambda sub: g.put(sub, "FunctionalBuildingValuationBasicGroupICoverage", state="KS"))),
                {}, ["Functional Valuation is not valid when Public And Institutional Property Plan Applies"], []),
        "M11": ("C18-13", "SC: Functional Valuation (valuation law in force); Agreed Value + CP 01 10", "SC",
                # CP 01 10 (Changes - Valuation) attaches itself when ValuationLaw is "Exemption Does Not Apply"
                mod(state_base("SC"), chain(setp("Structure", ValuationType="Functional Valuation", ValuationLaw="Exemption Does Not Apply"),
                                            setp("SpecialClass", AgreedValueOption="Yes", AgreedValueLimit="80000",
                                                 ValuationLaw="Exemption Does Not Apply"),
                                            lambda sub: g.put(sub, "FunctionalBuildingValuationBasicGroupICoverage", state="SC"))),
                {}, ["Functional Valuation not valid with CP 01 10", "Agreed Value coverage does not apply with CP 01 10"], []),
        "S1": ("C18-14", "Agreed Value Factor 1.20 submitted on the building's forms", "OR",
               mod(A1B, lambda sub: [at(sub)[P + "Structure"][P + r].__setitem__("Factor", "1.20") for r in AVSTR]),
               {r: {"Factor": Decimal("1.20")} for r in AVSTR if not r.endswith("EarthquakeCoverage")}, [], []),
        "S2": ("C18-14", "Vacancy pro-rata 0.5 submitted", "OR",
               mod(g.v1, setc("Structure", "VacancyPermit", VacancyPermitProRateFactor="0.5")),
               {r: {"../VacancyPermitProRateFactor": Decimal("0.5")} for r in VPB}, [], []),
        "X0": ("C18-15", "Agreed Value at an agreed limit of 1,000,000 (control)", "OR", mod(A1B, big_agreed),
               {r: A1R[r] for r in AVUNBL}, [], []),
        "X1": ("C18-15", "X0 + cyber-incident exclusion", "OR", mod(A1B, chain(big_agreed, r3.cyber)),
               {r: dict(A1R[r], **CYBER) for r in AVUNBL}, [], []),
        "X2": ("C18-15", "Inflation Guard + cyber exclusion: no second 0.995", "OR", mod(g.i1, r3.cyber),
               {r: v for r, v in g.I1_RECS.items() if not r.endswith("EarthquakeCoverage")}, [], []),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, label, state, build, recs, must, mustnot)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), state)
        except InterpretError as exc:
            print(f"{cid:4s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, o in recs.items():
            res, checks = r3.expect(data, rec, o, state)
            nodes_ = rc1.find(data, P + rec)
            if not o.get("__zero__") and nodes_ and all(
                    n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0"
                    for n in nodes_):
                res = [(Decimal(0), e) for _, e in res]
            fac_bad = [(f, e, v) for f, e, v in checks if not r2.same(e, v)]
            if o.get("__zero__"):
                ok = all(r3.zeroish(e) for _, e in res)
                preds[cid][rec] = "ZERO"
            else:
                ok = bool(res) and all(not str(h).startswith("hand") and r2.same(h, e) for h, e in res) and not fac_bad
                preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:66]:66s} predicted "
                         f"{'$0' if o.get('__zero__') else [str(h) for h, _ in res]} engine {[e for _, e in res]}"
                         + (f"  factor {fac_bad[:2]}" if fac_bad else ""))
            if not ok:
                bad.append(rec)
        msgs = set(ip.messages)
        mb = [m for m in must if not any(m in x for x in msgs)] + [f"not: {m}" for m in mustnot if any(m in x for x in msgs)]
        print(f"{cid:4s} {task} {label}: engine {'as derived' if not bad and not mb else 'DIFFERS'}"
              + (f"; messages as predicted ({len(must)})" if must and not mb else "")
              + "".join(f"\n      message missing: {m}" for m in mb))
        if lines:
            print("\n".join(lines))
        if bad or mb:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, the whole message set):")
        for i, (cid, (task, label, state, build, recs, must, mustnot)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = state
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=state)
            (gc.OUT / f"chunk18_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,220})', str(exc.body))
                print(f"  {cid:4s} ISO REFUSES {m.group(0)[:240] if m else str(exc.body)[:240]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk18_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.get(cid, {}).items():
                iso = r2.iso_of(resp, rec)
                if want == "ZERO":
                    if not all(r3.zeroish(x) for x in iso):
                        pbad.append((rec, iso, "$0"))
                elif sorted(Decimal(str(x)) for x in iso if not r3.zeroish(x)) != sorted(Decimal(str(w)) for w in want if not r3.zeroish(w)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = [m for m in must if not any(m in x for x in mi)] + [m for m in mustnot if any(m in x for x in mi)]
            ok = not pbad and not d and mi == mo and not mb
            print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds.get(cid, {})) - len(pbad)} of "
                  f"{len(preds.get(cid, {}))} records; {len(ipr) - len(d)} of {len(ipr)} premiums; messages "
                  f"{'equal' if mi == mo else 'DIFFER'}" + ("; ISO raises the predicted messages" if must and not mb else "")
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:5])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
