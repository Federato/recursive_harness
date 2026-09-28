#!/usr/bin/env python3
"""Chunk 18, RC-4 (C18-16 to C18-19): the states and the editions.

C18-19  ALL 46 STATES. Each state gets one policy made portable (177_ / 183_'s way: chunk 7's
        five-coverage policy, chunk 15's modifiers, no earthquake election), dated 09/17/2026 -
        09/17/2027, carrying every chunk 18 family at once:
          Building (limit 1,000,000)  Agreed Value (agreed 80,000), Inflation Guard 6%, Functional
                                      Valuation (post-loss option), Rebuilding 25%, Vacancy Permit
                                      (11/01/2026 - 01/30/2027)
          Contents                    Agreed Value, Inflation Guard 20%, Functional Valuation,
                                      Leased Property Agreed Value (item 200,000), Vacancy Permit
                                      (10/01/2026 - 03/31/2027), Peak Season (+30,000, 60 days)
          Business Income, SCBI       Agreed Value
          Special class (1,000,000)   Agreed Value, Inflation Guard 12%, Rebuilding 25%
        Every coverage on the Special cause. EVERY record is predicted from THAT state's own
        SetPremium (its file if it rewrites it, else its countrywide edition's: MO 2023 V02, whose
        Agreed Value and Functional Valuation formulas differ; CA NC V03; FL RI MA VT V04) and THAT
        state's own tables (its file if it files rows): the family factor looked up independently,
        the premium by hand (177_'s evaluator). A state file that sets its switch to a bare 0 (CT and
        WV Functional Valuation, FL Rebuilding) or empties ErcRate is predicted not priced.
C18-16  VACANCY PERMIT'S NINE STATES are in the sweep (KS VT own factors, KS NY VT SetPremium, NY no
        vandalism part, FL vandalism rates, AL AR DC NY RI sublines, CT coinsurance), plus
          P-spp-OR / KS / NY / DC   Standard Property Policy, "Fire, Vandalism and Allied Lines",
                                    vandalism not excepted: the SPP factor 0.40 (KS NY file their own) and
                                    the SPP vandalism rate (DC KS NY file their own)
C18-17  THE OTHER REWRITES are in the sweep (FL Agreed Value Group II, FL Functional Valuation with its
        post-loss rule emptied, CT WV Functional off, FL Rebuilding off, FL Peak Season rates).
        CA's two rewrites are EARTHQUAKE-ONLY (Inflation Guard EQ, Peak Season EQ calcs): earthquake stays
        out of the state sweep as in chunks 16-17 (no CA EQ territory setup is built); recorded as a gap.
C18-18  EDITIONS: every state stands on its own countrywide edition in the sweep.

    python scripts/cf/189_chunk18_rc4.py [--live] [--all] [--states CT,MO] [--probes-only]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import functools
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
r4 = import_module("177_chunk16_rc4")                  # its pkgs() is cached (2026-09-28)
x17 = import_module("183_chunk17_rc4")
r2, rc1, gc, rep, cmp, r11, r16, s18 = r4.r2, r4.rc1, r4.gc, r4.rep, r4.cmp, r4.r11, r4.r16, r4.s18
r11.NUMERIC |= {"AgreedValueLimit", "UnitNumber", "BlktIDNum", "TotalLimit", "FullValue",
                # the submitted portable parent rates: ISO refuses them as strings (first live run)
                "BasicGroupIIBaseRate", "BasicGroupIIRate", "BasicGroupIBaseRate"}
P = "CommercialProperty"
q, val, pkgs = r4.q, r4.val, r4.pkgs
FAIL = []
#: every state that rewrites a chunk 18 file or files one of its tables, every countrywide edition in
#: force (MO V02; CA NC V03; FL RI MA VT V04), and OR. `--all` runs the 46.
SAMPLE = ["OR", "AL", "AR", "CA", "CT", "DC", "FL", "GA", "KS", "MA", "MO", "NC", "NY", "RI", "SC", "TX", "VT", "WV"]
CPP = "Commercial Property Policy"
EFF, EXP = g.EFF, g.EXP
L = lambda n, f: f"{n}{f}Coverage"
F3 = ("BasicGroupI", "BasicGroupII", "Special")
RE, RE_SC = g.RE, g.RE_SC


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


# ---------------------------------------------------------------- the policy

def build(j, extra=None):
    sub = r2.grp.five()
    at = rc1.node_dicts(sub)
    at[P].update(r2.rc2.POLICY)
    sub["EffDate"], sub["ExpDate"] = EFF, EXP
    at[P].update({"EffectiveDt": EFF, "ExpirationDt": EXP})
    st = at[P + "Structure"]
    st["MultiPremiumAndDispersionCreditFactor"] = r2.rc2.BUILDING_CREDIT
    st.setdefault("WindstormOrHailDeductible", "1,000")
    if j != "OR":
        at[P]["State"] = j
        loc = at[P + "Location"]
        loc.pop("BasicGroupIRatingTerr", None)
        loc.pop("BasicGroupIIRatingTerr", None)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc.update(s18.STATE_LOC.get(j, {}))
    if j == "FL":
        at[P + "SpecialClass"]["ClassDescription"] = r4.FL_SC
    if j != "OR":
        # PORTABLE PARENT RATES (found by the first engine pass, 2026-09-28): outside Oregon the portable
        # policy's Group II rate is 0 (Oregon's "Entire State" Group II territory is not another state's),
        # and the contents Special rate with it; CA's Group I base rate is 0 (district-split tables). Both
        # base rates are IsNull-guarded, so a submitted value stands (the way 164_ made Group I portable
        # with a territory factor of 1.0); every family built on those rates then prices in every state.
        at[P + "SpecialClass"].setdefault("BasicGroupIIBaseRate", "0.030")
        # the building's and contents' Group II rate also needs the symbol / numeric-value chain, which the
        # portable policy leaves unresolved: their (IsNull-guarded) BasicGroupIIRate is submitted instead
        for k in ("Structure", "PersonalProperty"):
            at[P + k].setdefault("BasicGroupIIRate", "0.030")
        # the contents Special rate multiplies by a contents territory multiplier keyed on the location's
        # SpecialRatingTerr. Chunk 7's Oregon value ("Multnomah ...") is not another state's row: ISO REFUSES
        # the policy (no row), our engine prices it with a 0 multiplier (OI-103, first live run 2026-09-28).
        # Every state files its own PrsnlPropTerrMultiplier: carry that state's first territory.
        terr = r4.rows(j, "PrsnlPropTerrMultiplier")
        if terr:
            at[P + "Location"]["SpecialRatingTerr"] = terr[0]["SpecialRatingTerr"]
        else:
            at[P + "Location"].pop("SpecialRatingTerr", None)
        # BI / SCBI take their Group II base from the building's symbol chain: submit it (guarded)
        for k in ("BusinessIncome", "SpecialClassBusnIncome"):
            at[P + k].setdefault("BasicGroupIIBaseRate", "0.030")
        if j == "CA":
            for k in ("Structure", "PersonalProperty"):
                at[P + k].setdefault("BasicGroupIBaseRate", "0.300")
    for k in g.PARENTS:
        at[P + k].update({"CauseOfLoss": "Special", "AgreedValueOption": "Yes", "AgreedValueLimit": "80000"})
    st.update({"Limit": "1000000", "FullBldgValue": "1000000", "InflationGuard": "6%",
               "ValuationType": "Functional Valuation"})
    at[P + "PersonalProperty"].update({"InflationGuard": "20%", "ValuationType": "Functional Valuation"})
    at[P + "SpecialClass"].update({"Limit": "1000000", "InflationGuard": "12%"})
    put = lambda rec: r2.put(sub, rec, {}, state=j)
    for f in F3:
        for k in g.PARENTS:
            put(L(g.AVREC[k], f))
        for k in ("Structure", "PersonalProperty", "SpecialClass"):
            put(L(g.IGREC[k], f))
        put(L("FunctionalBuildingValuation", f))
        put(L("FunctionalPersonalPropertyValuationOtherThanStock", f))
        put(f"{RE}{f}Cov")
        put(f"{RE_SC}{f}Cov")
        put(L("VacancyPermit", f))
        put(L("VacancyPermitPrsnlProp", f))
        put(L("PeakSeasonLimitOfInsuranceDetail", f))
    con = lambda parent, name: r2.container(sub, parent, name)
    con("Structure", "FunctionalBuildingValuation")["PostLossOrdinanceOrLawOption"] = "Yes"
    con("Structure", RE)["AdditionalExpenseCoveragePercentage"] = "25%"
    con("SpecialClass", RE_SC)["AdditionalExpenseCoveragePercentage"] = "25%"
    con("Structure", "VacancyPermit").update({"PermitPeriodFrom": "11/01/2026", "PermitPeriodTo": "01/30/2027",
                                               "Vandalism": "Yes", "SprinklerLeakage": "Yes"})
    con("PersonalProperty", "VacancyPermitPrsnlProp").update({"PermitPeriodFrom": "10/01/2026", "PermitPeriodTo": "03/31/2027",
                                                              "Vandalism": "No", "SprinklerLeakage": "No"})
    pp = at[P + "PersonalProperty"]
    pp[P + "PeakSeasonLimitOfInsuranceTable"][P + "PeakSeasonLimitOfInsurance"][0][
        P + "PeakSeasonLimitOfInsuranceDetailTable"][P + "PeakSeasonLimitOfInsuranceDetail"][0].update(
        {"Limit": "30000", "FullValue": "30000", "PeriodFrom": g.PS_PERIOD[0], "PeriodTo": g.PS_PERIOD[1]})
    pp[P + "LeasedPropertyTable"] = {P + "LeasedProperty": [{P + "LeasedPropertyDetailTable": {
        P + "LeasedPropertyDetail": [{"AgreeValueOption": "Yes", "Limit": "200000",
                                      **{f"{P}LeasedPropertyDetailAgreedValue{f}Cov": {} for f in F3}}]}}]}
    if extra:
        extra(sub)
    return sub


# ------------------------------------------------------------- expectations

def state_rule(j, rec, name):
    for pk in pkgs(j):
        f = pk / "Rules" / f"{P}{rec}Rules.Rule.xml"
        if f.exists():
            m = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
            if m:
                return m.group(0)
    return None


def expectations(j, probe=None):
    spp = probe is not None and probe.startswith("P-spp")
    av = val(j, "AgreedValueFactor", "Factor", Constant="Y")
    av_bi = val(j, "AgreedValueFactorBusnIncome", "Factor", Constant="Y")
    ig = lambda p: val(j, "InflationGuardBldg", "Factor", InflationGuardBldg=p)
    fv = lambda c: val(j, "FunctionalValuationFactor", "Factor", CovType=c)
    postloss = val(j, "PostLossOrdinanceOrLawOptionFactor", "Factor", Constant="Y")
    ref = lambda c: val(j, "RebuildingExpensesFactor", "Factor", CauseOfLoss=c)
    repct = val(j, "AdditionalExpenseCoveragePercentageConverted", "Percentage", AdditionalExpenseCoveragePercentage="25%")
    vpf = lambda c: val(j, "VacancyPermitFactors", "Factor", PolicyType="Standard Property Policy" if spp else CPP,
                        VacancyCauseOfLoss=c)
    exp = {}
    for f in F3:
        for k in g.PARENTS:
            exp[L(g.AVREC[k], f)] = {"Factor": av_bi if k in ("BusinessIncome", "SpecialClassBusnIncome") else av}
        for k, pct in (("Structure", "6%"), ("PersonalProperty", "20%"), ("SpecialClass", "12%")):
            exp[L(g.IGREC[k], f)] = {"Factor": ig(pct)}
        # FL empties SetPostLossFactor: the factor is then whatever its own rule leaves, read from the tree
        pl = state_rule(j, "FunctionalBuildingValuation", "SetPostLossFactor")
        fb = {"../Factor": fv("Building")}
        if pl and "RunRule" in pl:
            fb["../PostLossFactor"] = postloss
        exp[L("FunctionalBuildingValuation", f)] = fb
        pers = fv("PersProp")
        exp[L("FunctionalPersonalPropertyValuationOtherThanStock", f)] = {"../Factor": q(pers - 1, 3) if pers is not None else None}
        for n in (RE, RE_SC):
            exp[f"{n}{f}Cov"] = {g.RE_FACTOR_FIELD[f]: ref(g.FORMS[f]), "../AdditionalExpenseCoveragePercentageConverted": repct}
        exp[L("VacancyPermit", f)] = {"../VacancyPermitProRateFactor": g.prorate("11/01/2026", "01/30/2027")}
        exp[L("VacancyPermitPrsnlProp", f)] = {"../VacancyPermitProRateFactor": g.prorate("10/01/2026", "03/31/2027")}
        exp[L("PeakSeasonLimitOfInsuranceDetail", f)] = {"../PeakSeasonProRateFactor": g.prorate(*g.PS_PERIOD)}
        exp[f"LeasedPropertyDetailAgreedValue{f}Cov"] = {"../AgreedValueFactor": q(av - 1, 3)}
    for n in ("VacancyPermit", "VacancyPermitPrsnlProp"):
        exp[L(n, "BasicGroupI")]["../BasicGroupIFactor"] = vpf("Basic Group I")
        exp[L(n, "BasicGroupII")]["../BasicGroupIIFactor"] = vpf("Basic Group II")
        # the Special factor independently too: the first live run read it from the tree, so the prediction
        # copied the engine's $0 in VT (VT's header-only table; ISO uses the CW row -- fixed in CFResolvedBook)
        if not spp:
            exp[L(n, "Special")]["../SpecialFactor"] = vpf("Special")
    for rec in list(exp):
        text, src = r4.rule_text(j, rec)
        if text is None or r4.forced_zero(j, rec) or x17.empty_ercrate(j, rec):
            exp[rec] = "NONE"
    return exp


def _spp(sub):
    at = rc1.node_dicts(sub)
    at[P]["PolicyType"] = "Standard Property Policy"
    for k in ("Structure", "PersonalProperty"):
        at[P + k]["CauseOfLoss"] = "Fire, Vandalism and Allied Lines"
    r2.container(sub, "Structure", "VacancyPermit")["Vandalism"] = "No"


PROBES = {f"P-spp-{j}": (j, "Standard Property Policy: Vacancy SPP factor and vandalism rate", _spp)
          for j in ("OR", "KS", "NY", "DC")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    ap.add_argument("--probes-only", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    runs = []
    if not a.probes_only:
        for j in (a.states.split(",") if a.states else (s18.STATES if a.all else SAMPLE)):
            runs.append((j, j, "sweep", None))
    for pid, (j, label, fn) in PROBES.items():
        if not a.states or j in a.states.split(","):
            runs.append((pid, j, label, fn))
    print(f"engine pass: {len(runs)} policies ({', '.join(r[0] for r in runs)})")
    results = {}
    for i, (rid, j, label, fn) in enumerate(runs, 1):
        progress(i, len(runs), f"engine {rid} ({label})")
        try:
            data, ip = gc.run(build(j, fn), j)
        except (InterpretError, LookupError) as exc:
            print(f"  {rid:9s} RAISED {str(exc)[:150]}")
            FAIL.append(rid)
            continue
        exp = expectations(j, rid if rid.startswith("P-") else None)
        bad, detail, n, preds = r4.evaluate(j, data, exp)
        results[rid] = (j, fn, preds)
        notp = sorted({re.sub(r"(BasicGroupI+|Special)Cov(erage)?$", "", r16.short(r))[:36] for r, v in exp.items() if v == "NONE"})
        priced = sum(1 for v in preds.values() if v != "NONE" and any(not r2.same(x, 0) for x in v))
        print(f"  {rid:9s} {pkgs(j)[1].name[-12:]:12s} engine {'as derived' if not bad else 'DIFFERS'}: {n - len(bad)} of {n} "
              f"records, {priced} priced" + (f" (not priced here: {', '.join(notp)})" if notp else "")
              + (f"  [{label}]" if label != "sweep" else ""))
        for d in detail[:6]:
            print(d)
        if bad:
            FAIL.append(rid)
    print(f"\nengine: {len(runs) - len(FAIL)} of {len(runs)} as derived")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every predicted record, every premium field for field, messages):")
        for i, (rid, (j, fn, preds)) in enumerate(results.items(), 1):
            progress(i, len(results), f"ISO {rid}")
            req = r11.payload(build(j, fn))
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk18_rc4_{rid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,180})', str(exc.body))
                print(f"  {rid:9s} ISO REFUSES {m.group(0)[:190] if m else str(exc.body)[:190]}")
                FAIL.append(f"{rid} live")
                continue
            (gc.OUT / f"chunk18_rc4_{rid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.items():
                iso = r2.iso_of(resp, rec)
                if want == "NONE":
                    if not all(r4.zeroish(x) for x in iso):
                        pbad.append((rec, iso, "not priced"))
                elif sorted(Decimal(str(x)) for x in iso if not r2.same(x, 0)) != sorted(Decimal(str(w)) for w in want if not r2.same(w, 0)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            agree += ok
            print(f"  {rid:9s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds) - len(pbad)} of {len(preds)}; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:58]}: ISO {x}, derived {w}" for r, x, w in pbad[:5])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{rid} live")
        print(f"\n  live: {agree} of {len(results)} agree")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
