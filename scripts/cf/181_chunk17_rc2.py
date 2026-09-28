#!/usr/bin/env python3
"""Chunk 17, RC-2 (C17-06 to C17-11): golden cases for the 32 records ISO never priced.

Every case sits on 175_'s policy: chunk 7's five-coverage Oregon policy with chunk 15's
modifiers (package 0.85, IRPM 1.15, credit 0.9) and chunk 10's earthquake election on
every group, so the earthquake riders price. Inputs are chosen so the competing readings
give different dollars:

  Landlord Rental Value (C17-06)
    L1  BI, Broad, Frame, landlord limit 60,000 at 80% (type-of-risk 0.50), BI LCM 1.3:
        the Broad premium reads NO loss cost multiplier (0.011 x 600, not x 1.3); the EQ
        rider reads Business Income's EQ limit (100,000), not the landlord's 60,000.
    L2  BI, Special, the building Fire Resistive (Special base rate 0.027, Frame's 0.033). The
        building needs the full value ("Fire Resistive - Other Than Reinforced Masonry - ..."):
        a bare "Fire Resistive" has no ConstructionTypeToUse row and zeroes the building.
    L3  SCBI, Special, the special class Fire Resistive: the SCBI rules key the base rate
        on a HARDCODED "Frame" (0.033), not the risk's construction (0.027).
    L4  SCBI, Broad, coinsurance None -> "No Coinsurance" 1.61; Broad hardcoded Frame 0.011
        (Fire Resistive would be 0.007).
  Ordinary Payroll (C17-07)  P1  BI 0 days (1.12 -> 0.12), SCBI 90 days (1.06 -> 0.06), + EQ
        at class D3 (FinalEQRate 0.009; at A1's 0.005 a 0.06 rider rounds to $0), limits 500,000.
  Power, Heat and Refrigeration (C17-08)  H1  BI and SCBI (1.06 -> 0.06), + EQ at class D3, 500,000.
  Mining (C17-09)  M1  TypeOfRisk Mining on BI (Limited) and SCBI (Broad), LCM 1.3,
        the mining record's own limit 40,000 against the parent's 100,000.
  Watercraft (C17-10)  W1  Special, waterfront, BI Option2 (0.016), SCBI Option6 (0.024).
  Off-Premises (C17-11)
    O1  BI: Collision + OTC; no-waiting-period endorsement "Eliminated" (1.25); extended
        150 days (1.20); Option B, "Under 25%" (3.25); EQ on (OTC x 1.01); limit 37,500.
    O2  SCBI: no EQ; windstorm-or-hail exclusion (OTC x 0.95); waiting period default
        72 Hours (1.00); extended 730 (1.55); Option A (1.00); limit 12,345.
        (Flood's factor 1.02 needs the flood endorsement, chunk 25: not tested here.)

HOW EACH PREDICTION IS MADE: the family's own factors are looked up independently from
the filed CSVs and substituted on the tree; SetPremium is then evaluated by hand (174_'s
evaluator, half-up at each DecimalPlaces) with the parent coverage's rates read from the
tree (chunks 5-10, ISO-confirmed). The engine must equal it; --live ISO must equal it,
every premium on the policy compared field for field, messages compared.

    python scripts/cf/181_chunk17_rc2.py [--live] [--cases L1,O1]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError

r2 = import_module("175_chunk16_rc2")
gc, rc1, rep, cmp, r16, r11 = r2.gc, r2.rc1, r2.rep, r2.cmp, r2.r16, r2.r11
r11.NUMERIC |= {"NumOfDays"}            # ISO types the payroll days as Int32 (a string is refused)
P = r2.P
row, q, put, container, same = r2.row, r2.q, r2.put, r2.container, r2.same
FAIL = []

LL = "BusinessIncomeLandlordAsAdditionalInsuredRentalValue"
LL_SC = LL + "SpclClassBusnIncome"
PAY, PAY_SC = "OrdinaryPayrollLimitationOrExclusion", "OrdinaryPayrollLimitationOrExclusionSpclClassBusnIncome"
PHR, PHR_SC = "PowerHeatAndRefrigerationDeduction", "PowerHeatAndRefrigerationDeductionSpclClassBusnIncome"
MIN, MIN_SC = "MiningPropertiesBusinessIncome", "MiningPropertiesSpclClassBusnIncome"
WC, WC_SC = "BusinessIncomeWatercraftExclusionBuybackCoverage", "SpecialClassBusnIncomeWatercraftExclusionBuybackCoverage"
OP, OP_SC = "OffPremInterruptionOfBusnVehsMobileEquipmtBusnInc", "OffPremInterruptionOfBusnVehsMobileEquipmtSpclClassBusnIncome"
NW = "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod"
BIWO = "Business Income Without Extra Expense"
OTHER = "Other than Apartments and Condominiums"
OPT = {r["Value"]: r["WatercraftExclBuybackConstrctnOptions"]
       for r in r2.csv_rows("WatercraftExclusionBuybackConstructionOptionsConverted")}


# ------------------------------------------------------- independent factors

def trf(coins):
    return row("BusnIncomeFactor", "Factor", StateCode="CW", CovTypeBusnIncome=BIWO,
               TypeOfRisk="Rental Properties", CoinsuranceBusnIncome=coins)


def broad_rate(cons):
    return row("BroadFormBaseRate", "Rate", StateCode="CW", ConstructionTypeToUse=cons, CovType=BIWO)


def special_rate(cons, risk=OTHER):
    return row("SpecialFormIncldgTheftTimeElementBaseRate", "Rate", StateCode="CW", ConstructionTypeToUse=cons,
               CovTypeBusinessIncome=BIWO, SpecialIncldgTheftTypeRiskBusnIncome=risk)


def payroll(days):
    return q(row("PayrollExclusionAndLimitationFactor", "Factor", StateCode="CW", PayrollNumberOfDays=days) - 1, 3)


PHR_F = q(row("PowerHeatAndRefrigerationFactor", "Factor", StateCode="CW", Constant="Y") - 1, 3)


def mining(opt, cause):
    return row("MiningPropertiesBusnIncomeRate", "Rate", StateCode="CW", MiningCoverageOption=opt, MiningCauseOfLoss=cause)


def watercraft(option):
    return row("WatercraftExclBuybackFactor", "Factor", StateCode="CW", WatercraftExclBuybackConstrctnOptionsConverted=option)


def op_lc(covtype, cause):
    return row("OffPremInterruptionOfBusnVehsMobileEquipLossCost", "LossCost", StateCode="CW",
               CovTypeBusnIncome=covtype, CoveredCausesOfLossOption=cause)


def op_f(table, col, key):
    return row(table, "Factor", StateCode="CW", **{col: key})


# ---------------------------------------------------------------- the cases

def at(sub):
    return rc1.node_dicts(sub)


def landlord(parent, cause, forms, fields):
    name = LL if parent == "BusinessIncome" else LL_SC
    sub = r2.base()
    a = at(sub)
    a[P + parent]["CauseOfLoss"] = cause
    for f in forms:
        put(sub, f"{name}{f}Coverage")
    container(sub, parent, name).update(dict(fields, CauseOfLoss=cause))
    return sub, a


def l1():
    sub, a = landlord("BusinessIncome", "Broad", ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake"),
                      {"Limit": "60000", "Coinsurance": "80%"})
    a[P + "BusinessIncome"]["LossCostMultiplier"] = "1.3"
    return sub


def l2():
    sub, a = landlord("BusinessIncome", "Special", ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"),
                      {"Limit": "60000", "Coinsurance": "80%"})
    a[P + "Structure"]["ConstructionType"] = "Fire Resistive - Other Than Reinforced Masonry - Other Than Light Steel"
    a[P + "BusinessIncome"].update({"LossCostMultiplier": "1.3", "SpecialIncludingTheftTypeRisk": OTHER})
    return sub


def l3():
    sub, a = landlord("SpecialClassBusnIncome", "Special", ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"),
                      {"Limit": "45000", "Coinsurance": "50%"})
    a[P + "SpecialClass"]["ConstructionType"] = "Fire Resistive"
    a[P + "SpecialClassBusnIncome"].update({"LossCostMultiplier": "1.3", "SpecialIncludingTheftTypeRisk": OTHER})
    return sub


def l4():
    sub, a = landlord("SpecialClassBusnIncome", "Broad", ("BasicGroupI", "Broad"),
                      {"Limit": "30000", "Coinsurance": "None"})
    a[P + "SpecialClass"]["ConstructionType"] = "Fire Resistive"
    return sub


def eq_high(sub):
    """EQ class D3, 5% deductible, BI limits 500,000: Business Income's FinalEQRate becomes
    0.009, so round3(0.009 x 0.06) = 0.001 prices. At chunk 10's A1 / 10% (0.005) every
    0.06-factor EQ rider rounds to 0.000 and prices $0 -- a zero case for C17-12."""
    a = at(sub)
    for k in ("Structure", "SpecialClass"):
        a[P + k].update({"EQClass": "D3", "EQDeductible": "5%"})
    for k in ("BusinessIncome", "SpecialClassBusnIncome"):
        a[P + k]["Limit"] = "500000"
    return sub


def p1():
    sub = r2.base()
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        put(sub, f"{PAY}{f}Coverage")
        put(sub, f"{PAY_SC}{f}Coverage")
    container(sub, "BusinessIncome", PAY)["NumOfDays"] = "0"
    container(sub, "SpecialClassBusnIncome", PAY_SC)["NumOfDays"] = "90"
    return eq_high(sub)


def h1():
    sub = r2.base()
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        put(sub, f"{PHR}{f}Coverage")
        put(sub, f"{PHR_SC}{f}Coverage")
    return eq_high(sub)


def m1():
    sub = r2.base()
    a = at(sub)
    for k in ("BusinessIncome", "SpecialClassBusnIncome"):
        a[P + k].update({"TypeOfRisk": "Mining", "LossCostMultiplier": "1.3", "CauseOfLoss": "Special"})
    for f in ("BasicGroupI", "BasicGroupII"):
        put(sub, f"{MIN}{f}Coverage")
        put(sub, f"{MIN_SC}{f}Coverage")
    container(sub, "BusinessIncome", MIN).update({"MiningCoverageOption": "Limited", "Limit": "40000"})
    container(sub, "SpecialClassBusnIncome", MIN_SC).update({"MiningCoverageOption": "Broad", "Limit": "40000"})
    return sub


def w1():
    sub = r2.base()
    a = at(sub)
    a[P + "BusinessIncome"].update({"CauseOfLoss": "Special", "WaterfrontProperty": "Yes",
                                    "WatercraftExclBuybackConstrctnOption": OPT["Option2"]})
    a[P + "SpecialClassBusnIncome"].update({"CauseOfLoss": "Special", "WaterFrontProperty": "Yes",
                                            "WatercraftExclBuybackConstrctnOption": OPT["Option6"]})
    put(sub, WC)
    put(sub, WC_SC)
    return sub


def o1():
    sub = r2.base()
    for f in ("Collision", "OTC"):
        put(sub, f"{OP}Detail{f}")
    put(sub, f"{NW}BasicGroupICoverage")
    container(sub, "BusinessIncome", NW)["TimePeriod"] = "Eliminated"
    container(sub, "BusinessIncome", OP).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "150"})
    d = container(sub, "BusinessIncome", OP)[P + OP + "DetailTable"][P + OP + "Detail"][0]
    d.update({"Limit": "37500", "Option": "Option B", "PercentInsToExposure": "Under 25%"})
    return sub


def o2():
    sub = r2.base()
    a = at(sub)
    a[P + "SpecialClassBusnIncome"]["EQCovIndicator"] = "No Coverage"
    a[P + "SpecialClassBusnIncome"][P + "WindstormOrHailExclusionSpclClassBusnIncomeTable"] = {
        P + "WindstormOrHailExclusionSpclClassBusnIncome": [{}]}
    for f in ("Collision", "OTC"):
        put(sub, f"{OP_SC}Detail{f}")
    container(sub, "SpecialClassBusnIncome", OP_SC).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "730"})
    d = container(sub, "SpecialClassBusnIncome", OP_SC)[P + OP_SC + "DetailTable"][P + OP_SC + "Detail"][0]
    d.update({"Limit": "12345", "Option": "Option A"})
    return sub


def cases():
    L = lambda n, f: f"{n}{f}Coverage"
    WE = "Business Income With Extra Expense"
    o1f = {"../../../ExtendedBICovFactor": op_f("OffPremExtendedBusnIncCovFactor", "ExtendedPeriodBusnInc", "150"),
           "../../../BusnIncCovWaitingPeriodFactor": op_f("OffPremBusnIncCovWaitPeriodFactor", "TimePeriod", "Eliminated"),
           "../InsToExposureFactor": op_f("OffPremInsToExposureFactor", "PercentInsToExposure", "Under 25%")}
    o2f = {"../../../ExtendedBICovFactor": op_f("OffPremExtendedBusnIncCovFactor", "ExtendedPeriodBusnInc", "730"),
           "../../../BusnIncCovWaitingPeriodFactor": op_f("OffPremBusnIncCovWaitPeriodFactor", "TimePeriod", "72 Hours"),
           "../InsToExposureFactor": Decimal("1.0")}
    endt = lambda e: op_f("OffPremEndtsModifyingCovdCOLFactor", "Endorsement", e)
    return {
        "L1": ("C17-06", "Landlord on BI, Broad, Frame, 60,000 at 80%, LCM 1.3, + EQ", "OR", l1,
               {L(LL, "BasicGroupI"): {"../TypeOfRiskFactor": trf("80%")},
                L(LL, "BasicGroupII"): {"../TypeOfRiskFactor": trf("80%")},
                L(LL, "Broad"): {"../BroadBaseRate": broad_rate("Frame")},
                L(LL, "Earthquake"): {"../TypeOfRiskFactor": trf("80%")}}),
        "L2": ("C17-06", "Landlord on BI, Special, building Fire Resistive, LCM 1.3, + EQ", "OR", l2,
               {L(LL, "BasicGroupI"): {"../TypeOfRiskFactor": trf("80%")},
                L(LL, "BasicGroupII"): {"../TypeOfRiskFactor": trf("80%")},
                L(LL, "Special"): {"../SpecialBaseRate": special_rate("Fire Resistive")},
                L(LL, "Earthquake"): {"../TypeOfRiskFactor": trf("80%")}}),
        "L3": ("C17-06", "Landlord on SCBI, Special, special class Fire Resistive (rules say Frame), 45,000 at 50%", "OR", l3,
               {L(LL_SC, "BasicGroupI"): {"../TypeOfRiskFactor": trf("50%")},
                L(LL_SC, "BasicGroupII"): {"../TypeOfRiskFactor": trf("50%")},
                L(LL_SC, "Special"): {"../SpecialBaseRate": special_rate("Frame")},
                L(LL_SC, "Earthquake"): {"../TypeOfRiskFactor": trf("50%")}}),
        "L4": ("C17-06", "Landlord on SCBI, Broad, no coinsurance, special class Fire Resistive (rules say Frame)", "OR", l4,
               {L(LL_SC, "BasicGroupI"): {"../TypeOfRiskFactor": trf("No Coinsurance")},
                L(LL_SC, "Broad"): {"../BroadBaseRate": broad_rate("Frame")}}),
        "P1": ("C17-07", "Ordinary Payroll: BI 0 days, SCBI 90 days, + EQ (class D3), limits 500,000", "OR", p1,
               {**{L(PAY, f): {"../Factor": payroll(0)} for f in ("BasicGroupI", "BasicGroupII", "Earthquake")},
                **{L(PAY_SC, f): {"../Factor": payroll(90)} for f in ("BasicGroupI", "BasicGroupII", "Earthquake")}}),
        "H1": ("C17-08", "Power, Heat and Refrigeration on BI and SCBI, + EQ (class D3), limits 500,000", "OR", h1,
               {L(n, f): {"../Factor": PHR_F} for n in (PHR, PHR_SC) for f in ("BasicGroupI", "BasicGroupII", "Earthquake")}),
        "M1": ("C17-09", "Mining: BI Limited, SCBI Broad, LCM 1.3, mining limit 40,000", "OR", m1,
               {L(MIN, "BasicGroupI"): {"../BasicGroupIRate": mining("Limited", "Basic Group I")},
                L(MIN, "BasicGroupII"): {"../BasicGroupIIRate": mining("Limited", "Basic Group II")},
                L(MIN_SC, "BasicGroupI"): {"../BasicGroupIRate": mining("Broad", "Basic Group I")},
                L(MIN_SC, "BasicGroupII"): {"../BasicGroupIIRate": mining("Broad", "Basic Group II")}}),
        "W1": ("C17-10", "Watercraft buyback: BI Option2, SCBI Option6, Special, waterfront", "OR", w1,
               {WC: {"Factor": watercraft("Option2")}, WC_SC: {"Factor": watercraft("Option6")}}),
        "O1": ("C17-11", "Off-Premises on BI: no waiting period, 150 days, Option B under 25%, EQ, 37,500", "OR", o1,
               {f"{OP}DetailCollision": dict(o1f, **{"../../../LossCostCollision": op_lc(WE, "Collision")}),
                f"{OP}DetailOTC": dict(o1f, **{"../../../LossCostOTC": op_lc(WE, "Other Than Collision"),
                                               "../../../EQCovFactor": endt("Earthquake And Volcanic Eruption Coverage"),
                                               "../../../FloodCovFactor": Decimal("1.0"),
                                               "../../../WindHailExclFactor": Decimal("1.0")})}),
        "O2": ("C17-11", "Off-Premises on SCBI: wind-hail exclusion, no EQ, 730 days, Option A, 12,345", "OR", o2,
               {f"{OP_SC}DetailCollision": dict(o2f, **{"../../../LossCostCollision": op_lc(WE, "Collision")}),
                f"{OP_SC}DetailOTC": dict(o2f, **{"../../../LossCostOTC": op_lc(WE, "Other Than Collision"),
                                                  "../../../EQCovFactor": Decimal("1.0"),
                                                  "../../../FloodCovFactor": Decimal("1.0"),
                                                  "../../../WindHailExclFactor": endt("Windstorm Or Hail Exclusion")})}),
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
    preds = {}
    for cid, (task, label, state, build, recs) in cs.items():
        try:
            data, ip = gc.run(build(), state)
        except InterpretError as exc:
            print(f"{cid:4s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, ov in recs.items():
            res, checks = r2.predict(data, rec, ov, state)
            priced = [(h, e) for h, e in res if e not in (None, "") and Decimal(e) != 0]
            fac_bad = [(f, e, v) for f, e, v in checks if not same(e, v)]
            ok = bool(priced) and all(isinstance(h, Decimal) and same(h, e) for h, e in priced) and not fac_bad
            preds[cid][rec] = [h for h, _ in priced]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:74]:74s} predicted "
                         f"{[str(h) for h, _ in priced] or [str(h) for h, _ in res]} engine {[e for _, e in res]}"
                         + (f"  factor engine/independent {fac_bad[:2]}" if fac_bad else ""))
            if not ok:
                bad.append(rec)
        print(f"{cid:4s} {task} {label}: engine {'as derived' if not bad else 'DIFFERS'} ({len(recs)} records)")
        print("\n".join(lines))
        if bad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for cid, (task, label, state, build, recs) in cs.items():
            req = r11.payload(build())
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = state
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=state)
            (gc.OUT / f"chunk17_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid:4s} ISO REFUSES {m.group(0)[:170] if m else str(exc.body)[:170]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk17_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = preds.get(cid, {}).get(rec, [])
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:64]}: ISO {x}, derived {w}" for r, x, w in pbad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    print(f"\nRC-2: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
