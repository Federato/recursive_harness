#!/usr/bin/env python3
"""Chunk 17, RC-4 (C17-16 to C17-19): the states and the editions.

C17-19  ALL 46 STATES. Each state gets one policy made portable (177_'s way: chunk 7's
        five-coverage policy, chunk 15's modifiers, no earthquake election) that carries
        every chunk 17 family at once (24 records):
          Business Income, Special, TypeOfRisk Mining, LCM 1.3, waterfront Option2
            Ordinary Payroll 90 days (BGI, BGII)       Power-heat (BGI, BGII)
            Mining Limited (BGI, BGII)                 Landlord, own cause Special, 60,000 at 80%
                                                       (BGI, BGII, Special)
            Watercraft buyback                         Off-Premises: Collision + OTC, 150 days,
                                                       Option B "Under 25%", 37,500
          Special Class BI, Special, TypeOfRisk Mining, LCM 1.3, waterfront Option6
            Ordinary Payroll 0 days                    Power-heat
            Mining Broad                               Landlord, own cause BROAD (two keys), 45,000
                                                       at 50% (BGI, BGII, Broad)
            Watercraft buyback                         Off-Premises: 730 days, Option A, 12,345
        EVERY record is predicted from THAT state's own SetPremium (its file if it rewrites it,
        else its countrywide edition's: MO 2023 V02, CA / NC V03, FL / RI / MA / VT V04) and
        THAT state's own tables (its file if it files rows, else its edition's): the family
        factor looked up independently, the premium by hand (177_'s evaluator). A state file
        that empties ErcRate (CT: Landlord Group I) is predicted not priced.
C17-16  LANDLORD'S STATES are in the sweep (CT's empty ErcRate; FL's sinkhole-adjusted Group II
        without the cyber factors, FL's own type-of-risk and Special tables; KS NY VT's SetPremium
        without the Standard Property Policy test, NY also without the policy cyber factor), plus
          P-std-OR / KS / NY / VT   Standard Property Policy: CW prices Landlord Broad and Special
                                    $0; KS and NY price both (their SetSpecialBaseRate drops the
                                    policy-type test too); VT prices Broad but its Special base
                                    rate (V04's rule) is still 0 -> Special $0
C17-17  OFF-PREMISES' STATES are in the sweep (AK drops insurance-to-exposure: the sweep's Option B
        3.25 discriminates; AR DC NY RI drop the wind-hail factor; FL's residential switch), plus
          P-wh-OR / AR / DC / NY / RI   wind-hail exclusion on BI and SCBI: OR's OTC x 0.95, the
                                        four states' unchanged
          P-FLres                       FL, building class 0311: Off-Premises switched off ($0)
C17-18  EDITIONS: every state stands on its own countrywide edition in the sweep (MO 2023 V02; CA
        NC V03; FL RI MA VT V04; the rest 2026 V01), each predicted from that edition's files.

    python scripts/cf/183_chunk17_rc4.py [--live] [--all] [--states CT,AK] [--probes-only]
    (default: the covering sample + the probes; --all: the 46 + the probes)

Exits 1 on any disagreement.
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

from gl_engine.interp.values import InterpretError

sys.stdout.reconfigure(line_buffering=True)     # progress shows as it happens, even through a pipe or a log file
T0 = time.monotonic()


def progress(i, n, what):
    """one line before each unit of work: [3/24  2m41s] CT sweep"""
    m, sec = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{sec:02d}s] {what}")

g = import_module("181_chunk17_rc2")
si = import_module("_state_inputs")                       # C28-17: a state's own Group II territory
r4 = import_module("177_chunk16_rc4")
r2, rc1, gc, rep, cmp, r11, r16, s18 = r4.r2, r4.rc1, r4.gc, r4.rep, r4.cmp, r4.r11, r4.r16, r4.s18
P = "CommercialProperty"
import functools                                # noqa: E402
# 177_'s pkgs() calls book_for, which re-discovers the whole ERC corpus (1.8 s) on every call:
# 123 calls per policy made a pass 2.5 min/policy, 98% of it discovery (profiled 2026-09-28).
# The packages a state stands on do not change within a run: cache it here (and in 177_'s
# module, whose rows / rule_text / forced_zero call it by global name).
r4.pkgs = functools.lru_cache(maxsize=None)(r4.pkgs)
q, val, pkgs = r4.q, r4.val, r4.pkgs
FL_SC = r4.FL_SC
FAIL = []
#: every state that rewrites a chunk 17 file or files one of its tables, every countrywide edition
#: in force (MO V02; CA NC V03; FL RI MA VT V04), and OR. `--all` runs the 46.
SAMPLE = ["OR", "AK", "AR", "CA", "CT", "DC", "FL", "KS", "MA", "MO", "NC", "NY", "RI", "VT"]

LL, LL_SC, PAY, PAY_SC, PHR, PHR_SC = g.LL, g.LL_SC, g.PAY, g.PAY_SC, g.PHR, g.PHR_SC
MIN, MIN_SC, WC, WC_SC, OP, OP_SC = g.MIN, g.MIN_SC, g.WC, g.WC_SC, g.OP, g.OP_SC
BIWO, OTHER, OPT = g.BIWO, g.OTHER, g.OPT
WE = "Business Income With Extra Expense"
L = lambda n, f: f"{n}{f}Coverage"


# ---------------------------------------------------------------- the policy

def build(j, extra=None):
    sub = r2.grp.five()
    at = rc1.node_dicts(sub)
    at[P].update(r2.rc2.POLICY)
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
        si.localize_group2(sub, j)
    if j == "FL":
        at[P + "SpecialClass"]["ClassDescription"] = FL_SC
    common = {"CauseOfLoss": "Special", "TypeOfRisk": "Mining", "LossCostMultiplier": "1.3",
              "SpecialIncludingTheftTypeRisk": OTHER}
    at[P + "BusinessIncome"].update(dict(common, WaterfrontProperty="Yes",
                                         WatercraftExclBuybackConstrctnOption=OPT["Option2"]))
    at[P + "SpecialClassBusnIncome"].update(dict(common, WaterFrontProperty="Yes",
                                                 WatercraftExclBuybackConstrctnOption=OPT["Option6"]))
    put = lambda rec: r2.put(sub, rec, {}, state=j)
    con = lambda parent, name: r2.container(sub, parent, name)
    for f in ("BasicGroupI", "BasicGroupII"):
        for n in (PAY, PAY_SC, PHR, PHR_SC, MIN, MIN_SC, LL, LL_SC):
            put(L(n, f))
    put(L(LL, "Special"))
    put(L(LL_SC, "Broad"))
    put(WC)
    put(WC_SC)
    for f in ("Collision", "OTC"):
        put(f"{OP}Detail{f}")
        put(f"{OP_SC}Detail{f}")
    con("BusinessIncome", PAY)["NumOfDays"] = "90"
    con("SpecialClassBusnIncome", PAY_SC)["NumOfDays"] = "0"
    con("BusinessIncome", MIN).update({"MiningCoverageOption": "Limited", "Limit": "40000"})
    con("SpecialClassBusnIncome", MIN_SC).update({"MiningCoverageOption": "Broad", "Limit": "40000"})
    con("BusinessIncome", LL).update({"Limit": "60000", "Coinsurance": "80%", "CauseOfLoss": "Special"})
    con("SpecialClassBusnIncome", LL_SC).update({"Limit": "45000", "Coinsurance": "50%", "CauseOfLoss": "Broad"})
    con("BusinessIncome", OP).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "150"})
    con("SpecialClassBusnIncome", OP_SC).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "730"})
    con("BusinessIncome", OP)[P + OP + "DetailTable"][P + OP + "Detail"][0].update(
        {"Limit": "37500", "Option": "Option B", "PercentInsToExposure": "Under 25%"})
    con("SpecialClassBusnIncome", OP_SC)[P + OP_SC + "DetailTable"][P + OP_SC + "Detail"][0].update(
        {"Limit": "12345", "Option": "Option A"})
    if extra:
        extra(sub)
    return sub


# ------------------------------------------------------------- expectations

def state_rule(j, rec, name):
    """the text of rule `name` in force for rec's file in state j (state file first, else edition)."""
    for pk in pkgs(j):
        f = pk / "Rules" / f"{P}{rec}Rules.Rule.xml"
        if f.exists():
            m = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
            if m:
                return m.group(0)
    return None


def empty_ercrate(j, rec):
    """the state's file replaces ErcRate with an empty Sequence (CT: Landlord Group I)."""
    t = state_rule(j, rec, "ErcRate")
    return t is not None and "RunRule" not in t


def expectations(j, probe=None):
    standard = probe is not None and probe.startswith("P-std")
    trf = lambda c: val(j, "BusnIncomeFactor", "Factor", CovTypeBusnIncome=BIWO, TypeOfRisk="Rental Properties",
                        CoinsuranceBusnIncome=c)
    broad = val(j, "BroadFormBaseRate", "Rate", ConstructionTypeToUse="Frame", CovType=BIWO)
    # Business Income DERIVES SpecialIncludingTheftTypeRisk from the building's class code and overwrites
    # the submitted value: class 0311 (P-FLres) is an apartment building -> "Apartments and Condominiums"
    # (FL 0.021, not the submitted "Other than" 0.044; found by the first engine pass, 2026-09-28)
    risk = "Apartments and Condominiums" if probe == "P-FLres" else OTHER
    special = val(j, "SpecialFormIncldgTheftTimeElementBaseRate", "Rate", ConstructionTypeToUse="Frame",
                  CovTypeBusinessIncome=BIWO, SpecialIncldgTheftTypeRiskBusnIncome=risk)
    if standard:
        # the Special base rate is 0.0 wherever the rule in force keeps the policy-type test
        for rec in (LL, LL_SC):
            t = state_rule(j, rec, "SetSpecialBaseRate")
            if t and "Standard Property Policy" in t:
                special = Decimal("0.0")
    pay = lambda d: q(val(j, "PayrollExclusionAndLimitationFactor", "Factor", PayrollNumberOfDays=d) - 1, 3)
    phr = q(val(j, "PowerHeatAndRefrigerationFactor", "Factor", Constant="Y") - 1, 3)
    mine = lambda o, c: val(j, "MiningPropertiesBusnIncomeRate", "Rate", MiningCoverageOption=o, MiningCauseOfLoss=c)
    wcf = lambda o: val(j, "WatercraftExclBuybackFactor", "Factor", WatercraftExclBuybackConstrctnOptionsConverted=o)
    lc = lambda c: val(j, "OffPremInterruptionOfBusnVehsMobileEquipLossCost", "LossCost", CovTypeBusnIncome=WE,
                       CoveredCausesOfLossOption=c)
    ext = lambda p: val(j, "OffPremExtendedBusnIncCovFactor", "Factor", ExtendedPeriodBusnInc=p)
    wait = val(j, "OffPremBusnIncCovWaitPeriodFactor", "Factor", TimePeriod="72 Hours")
    ins = val(j, "OffPremInsToExposureFactor", "Factor", PercentInsToExposure="Under 25%")
    wh = Decimal("1.0")
    if probe and probe.startswith("P-wh"):
        wh = val(j, "OffPremEndtsModifyingCovdCOLFactor", "Factor", Endorsement="Windstorm Or Hail Exclusion")
    exp = {}
    for f in ("BasicGroupI", "BasicGroupII"):
        exp[L(PAY, f)] = {"../Factor": pay("90")}
        exp[L(PAY_SC, f)] = {"../Factor": pay("0")}
        exp[L(PHR, f)] = {"../Factor": phr}
        exp[L(PHR_SC, f)] = {"../Factor": phr}
    exp[L(MIN, "BasicGroupI")] = {"../BasicGroupIRate": mine("Limited", "Basic Group I")}
    exp[L(MIN, "BasicGroupII")] = {"../BasicGroupIIRate": mine("Limited", "Basic Group II")}
    exp[L(MIN_SC, "BasicGroupI")] = {"../BasicGroupIRate": mine("Broad", "Basic Group I")}
    exp[L(MIN_SC, "BasicGroupII")] = {"../BasicGroupIIRate": mine("Broad", "Basic Group II")}
    for f in ("BasicGroupI", "BasicGroupII"):
        exp[L(LL, f)] = {"../TypeOfRiskFactor": trf("80%")}
        exp[L(LL_SC, f)] = {"../TypeOfRiskFactor": trf("50%")}
    exp[L(LL, "Special")] = {"../SpecialBaseRate": special}
    exp[L(LL_SC, "Broad")] = {"../BroadBaseRate": broad}
    exp[WC] = {"Factor": wcf("Option2")}
    exp[WC_SC] = {"Factor": wcf("Option6")}
    exp[f"{OP}DetailCollision"] = {"../../../LossCostCollision": lc("Collision"), "../../../ExtendedBICovFactor": ext("150"),
                                   "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": ins}
    exp[f"{OP}DetailOTC"] = {"../../../LossCostOTC": lc("Other Than Collision"), "../../../ExtendedBICovFactor": ext("150"),
                             "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": ins,
                             "../../../EQCovFactor": Decimal("1.0"), "../../../FloodCovFactor": Decimal("1.0"),
                             "../../../WindHailExclFactor": wh}
    exp[f"{OP_SC}DetailCollision"] = {"../../../LossCostCollision": lc("Collision"), "../../../ExtendedBICovFactor": ext("730"),
                                      "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": Decimal("1.0")}
    exp[f"{OP_SC}DetailOTC"] = {"../../../LossCostOTC": lc("Other Than Collision"), "../../../ExtendedBICovFactor": ext("730"),
                                "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": Decimal("1.0"),
                                "../../../EQCovFactor": Decimal("1.0"), "../../../FloodCovFactor": Decimal("1.0"),
                                "../../../WindHailExclFactor": wh}
    for rec in list(exp):
        text, src = r4.rule_text(j, rec)
        if text is None or r4.forced_zero(j, rec) or empty_ercrate(j, rec):
            exp[rec] = "NONE"
        if probe == "P-FLres" and OP in rec:
            exp[rec] = "NONE"
    return exp


def _standard(sub):
    rc1.node_dicts(sub)[P]["PolicyType"] = "Standard Property Policy"


def _wind_hail(sub):
    at = rc1.node_dicts(sub)
    at[P + "BusinessIncome"][P + "WindstormOrHailExclusionBusnIncomeTable"] = {P + "WindstormOrHailExclusionBusnIncome": [{}]}
    at[P + "SpecialClassBusnIncome"][P + "WindstormOrHailExclusionSpclClassBusnIncomeTable"] = {
        P + "WindstormOrHailExclusionSpclClassBusnIncome": [{}]}


def _residential(sub):
    rc1.node_dicts(sub)[P + "Structure"]["ClassCode"] = "0311"


PROBES = {
    **{f"P-std-{j}": (j, "Standard Property Policy: Landlord Broad / Special", _standard) for j in ("OR", "KS", "NY", "VT")},
    **{f"P-wh-{j}": (j, "wind-hail exclusion on BI and SCBI: Off-Premises OTC", _wind_hail)
       for j in ("OR", "AR", "DC", "NY", "RI")},
    "P-FLres": ("FL", "building class 0311: Off-Premises switched off", _residential),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    ap.add_argument("--probes-only", action="store_true")
    ap.add_argument("--all", action="store_true", help="all 46 states (chunk close-outs); default: the covering sample")
    a = ap.parse_args()
    runs = []
    if not a.probes_only:
        for j in (a.states.split(",") if a.states else (s18.STATES if a.all else SAMPLE)):
            runs.append((j, j, "sweep", None))
    for pid, (j, label, fn) in PROBES.items():
        if not a.states or j in a.states.split(","):
            runs.append((pid, j, label, fn))
    results = {}
    print(f"engine pass: {len(runs)} policies ({', '.join(r[0] for r in runs)})")
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
        notp = sorted(r16.short(r)[:34] for r, v in exp.items() if v == "NONE")
        ed = pkgs(j)[1].name
        print(f"  {rid:9s} {ed[-12:]:12s} engine {'as derived' if not bad else 'DIFFERS'}: {n - len(bad)} of {n} records"
              + (f" (not priced: {', '.join(notp)})" if notp else "") + (f"  [{label}]" if label != "sweep" else ""))
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
            (gc.OUT / f"chunk17_rc4_{rid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {rid:9s} ISO REFUSES {m.group(0)[:170] if m else str(exc.body)[:170]}")
                FAIL.append(f"{rid} live")
                continue
            (gc.OUT / f"chunk17_rc4_{rid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
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
    m, sec = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{sec:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
