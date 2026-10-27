#!/usr/bin/env python3
"""Chunk 20, RC-2 (C20-06 to C20-14): golden cases for all ten families.

Every case sits on 175_'s policy (chunk 7's five-coverage Oregon policy, chunk 15's modifiers: package
0.85, IRPM 1.15, credit 0.9, building credit 0.95; every limit 100,000), except the blanket radioactive
cases (chunk 9's two-building A3). Each family's OWN values are looked up independently from the filed
CSVs and checked on the tree (field = independent value); SetPremium is then evaluated by hand (174_'s
evaluator, half-up at every DecimalPlaces). The engine must equal it; --live ISO must equal it, every
premium on the policy compared, messages compared. Each pair is chosen so the competing reading gives a
different dollar (read from the rules, 2026-09-29):

  Fire Department (C20-06)  (LimitToUse - 1,000) / 100 x 0.4
    F1  its own limit 25,000
    F2  own limit 25,000 AND the location's higher-limits record (indicator Yes, 50,000): LimitToUse 50,000
  Tobacco (C20-07)  a flat rate by the CONTENTS limit band (from-greater-than / to):
    TB1 contents 50,000  -> 26 (a from-inclusive reading gives 40)
    TB2 contents 100,000 -> 53 (79 if the upper bound were exclusive)
  Mortgageholders E&O (C20-08)  five layers by mortgage count, each rate by the per-mortgage limit:
    MG1 500 at 25,000 (first layer only)       MG2 1,001 at 50,000 (1 in the next-4,000 layer)
    MG3 15,000 at 100,000 (full next-10,000)   MG4 20,000 at 1,000,000 (all five layers)
  Fungus (C20-09)  excess 0.09 x (SubLimit - 15,000) / 100 + incremental 10 x (forms - 1) (Separate Limits only;
                   10 x forms only on a CPP whose governing state is another state)
                   + the Business Income fungus premium (factor by increased period)
    FU1 Policy Limit, SubLimit 50,000, BI 90 days (0.03)
    FU2 Separate Limits, SubLimit 25,000, TWO buildings each applying (forms 2: one extra form charged), BI 120 days (0.04)
  Furs / jewelry / patterns / stamps (C20-10)  the contents' theft-limitation Special rate x (LimitToUse -
                   the base special limit) / 100
    SC1 furs 20,000, jewelry 10,000 "Worth $100 or less per item" (base 0), patterns 20,000, stamps 5,000 (base 250)
    SC2 jewelry 10,000 "Worth more than $100 per item" (base 2,500); furs through the contents' higher-limits
        record (30,000), its own record's indicator "No"
  Radioactive Contamination (C20-11)  the rate is an input
    RA1 all five coverages, own limit 40,000 vs the parents' 100,000: unblanketed, the PARENT's limit prices
    RA2 blanket, detail RadioactiveContamination "Yes": the blanket average rate x LimitToUse
    RA3 blanket, detail "No": each building's own rate x its OWN limit
  Pier and Wharf / ACP (C20-12)  construction option -> Pier 0.026 (options 1-4) / 0.04 (5-6); ACP 0.016 / 0.024
    PW1 option 1 on all four Pier records + ACP detail (Bulkheads) on the building and on the special class
    PW2 option 5
  Food Contamination (C20-13)  food 0.18, advertising 0.045, on BI and SCBI
    FC1 food 10,000 / advertising 20,000
  Equipment Breakdown (C20-14)  building: a flat premium by total insurance band x occupancy group; BI: loss
                   cost by group x LimitToUse / 100 (x the no-waiting-period factor - 1 for the waiting-period record);
                   ammonia 0.22 x (limit - 25,000) / 100; hazardous substance a manual premium
    EB1 Institutional (group 3), BI "Eliminated" (1.15 -> 0.15), ammonia 50,000, hazardous 100
    EB2 Industrial and Processing (group 7), BI "Replaced By 24 Hours" (1.10 -> 0.10), building deductible 250
        (Deductible250Factor "All Other" 1.10), ammonia 100,000, hazardous 250

    python scripts/cf/200_chunk20_rc2.py [--live] [--cases F1,TB1]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
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
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

r2 = import_module("175_chunk16_rc2")
g19 = import_module("192_chunk19_rc2")
g18 = import_module("187_chunk18_rc2")
gc, rc1, rep, cmp, r16, r11 = r2.gc, r2.rc1, r2.rep, r2.cmp, r2.r16, r2.r11
P = r2.P
same, val = r2.same, g19.val
# declared xs:int in the DataDef XSD
# (NOT IncreasedPeriodOfRestoration: xs:int on the BI fungus records, but TEXT on the policy fungus record we send)
r11.NUMERIC |= {"NumberMortgages", "FoodLimit", "AdvertisingLimit", "AmmoniaContamination", "SubLimit",
                "FireDepartmentChargeLimit", "HazardousSubstanceOtherThanAmmonia",
                "SpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFurLimit",
                # declared xs:decimal
                "Rate", "HazardousSubstanceOtherThanAmmoniaManualPremium"}
FAIL = []
XSD = rc1.xsd_for(book_for("OR", r2.ASOF))
PIER1 = "Fire Resistive Including Pier Deck and Pier Platform, but Without Superstructure"
PIER5 = "All Other Construction - Substructure Including Superstructure, All Sides Enclosed"
BULK = "Bulkheads, Pilings, Piers, Wharves or Docks"
NOWAIT = "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod"
JEWEL = "PersonalPropertySpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetals"
FURS = "PersonalPropertySpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFur"
PATT = "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms"
STAMPS = "PersonalPropertySpecialCOLStampsTicketsAndLettersOfCredit"
MORT = "MortgageholdersErrorsAndOmissionsCoverageForm"
FUNGUS = "ChangesFungusWetRotDryRotBacteria"
BIF = ["BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverage" + f + "Coverage" for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
RADIO = ["RadioactiveContamination", "RadioactiveContaminationPrsnlProp", "RadioactiveContaminationBusnIncome",
         "RadioactiveContaminationSpecialClass", "RadioactiveContaminationSpclClassBusnIncome"]
PIER = ["PierAndWharfAdditionalCoveredCausesOfLossStruct", "PierAndWharfAdditionalCoveredCausesOfLoss",
        "PierAndWharfAdditionalCoveredCausesOfLossSpecialClass", "PierAndWharfAdditionalCoveredCausesOfLossSpclClassBusnIncome"]
ACP = ["AdditionalCoveredPropertyDetail", "AdditionalCoveredPropertySpecialClassDetail"]
FOOD = ["FoodContaminationBusinessInterruptionAndExtraExpense" + s for s in
        ("FoodOnlyCov", "AddlAdvCov", "SpclClassBusnIncomeFoodOnlyCov", "SpclClassBusnIncomeAddlAdvCov")]
EBB = "EquipmentBreakdownCauseOfLossBldg"
EBI = "EquipmentBreakdownCauseOfLossBusnInc"
EB = [EBB + "EBCov", EBB + "AmmoniaContaminationCov", EBB + "HazardousSubstanceOtherThanAmmoniaCov",
      EBI + "Coverage", EBI + "WaitingPeriodCoverage"]


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


# ---------------------------------------------------------------- placing records

def put(sub, rec, fields=None, inter=None, idx=0):
    """place `rec` (short name) on the tree at its DataDef chain, below the idx-th top container; `fields`
    on the record, `inter` = {container short name: fields} on the containers passed through."""
    top, steps = r16.chain_down(XSD, rec)
    tops = [d for d in walk(sub) if d[0] == top]
    d = tops[idx][1]
    for t, table in steps:
        if table:
            lst = d.setdefault(t + "Table", {t: []})[t]
            if not lst:
                lst.append({})
            d = lst[-1]
        else:
            d = d.setdefault(t, {})
        for k, v in ((inter or {}).get(r16.short(t), {})).items():
            d[k] = v
    d.update(fields or {})
    return d


def walk(o, k=None):
    """(element name, dict) for every element dict on the submission tree, document order."""
    if isinstance(o, dict):
        if k is not None and not k.endswith("Table"):
            yield k, o
        for kk, v in o.items():
            if isinstance(v, list):
                for x in v:
                    yield from walk(x, kk)
            elif isinstance(v, dict):
                yield from walk(v, kk)


def sval(j, table, col, **keys):
    """a text column: the state's own row if it files one, else CW."""
    import csv
    for pk, sc in ((book_for(j, r2.ASOF).state.package.content, j), (r2.CW, "CW")):
        f = pk / "Rate Tables" / f"{table}.RateTable.csv"
        if f.exists():
            for r in csv.DictReader(open(f, encoding="utf-8-sig")):
                if r["StateCode"] == sc and all(r[k] == v for k, v in keys.items()):
                    return r[col]


def base(cause="Special"):
    return g19.with_cause(r2.base(), cause)


def at(sub):
    return rc1.node_dicts(sub)


# ---------------------------------------------------------------- C20-06 Fire Department

def fire(higher):
    def b():
        sub = base()
        put(sub, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes", "Limit": "25000"})
        if higher:
            at(sub)[P + "Location"][P + "HigherLimitsLocationTable"] = {P + "HigherLimitsLocation": [
                {"FireDepartmentChargeIndicator": "Yes", "FireDepartmentChargeLimit": "50000"}]}
        return sub
    return b


def expect_fire(higher):
    def e(data, j):
        return {"LocationFireDepartmentCharge": {
            "FireDepartmentLimit": val(j, "FireDepartmentIncreasedLimit", "Limit", Constant="Y"),
            "Factor": val(j, "FireDepartmentIncreasedFactor", "Factor", Constant="Y"),
            "LimitToUse": "50000" if higher else "25000"}}
    return e


# ---------------------------------------------------------------- C20-07 Tobacco

def tobacco(limit):
    def b():
        sub = base()
        at(sub)[P + "OccupClass"]["CovForm"] = "Tobacco Sales Warehouse Coverage Form"
        at(sub)[P + "PersonalProperty"]["Limit"] = limit
        put(sub, "PersonalPropertyTobaccoSalesWarehousesCoverage")
        return sub
    return b


def band(j, limit):
    import csv
    f = book_for(j, r2.ASOF).parent.package.content / "Rate Tables" / "TobaccoInSalesWarehousesRate.RateTable.csv"
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r["StateCode"] == "CW" and Decimal(r["Limit_FromGreaterThan"]) < Decimal(limit) <= Decimal(r["Limit_To"]):
            return r["Rate"]


def expect_tobacco(limit):
    return lambda data, j: {"PersonalPropertyTobaccoSalesWarehousesCoverage": {"TobaccoInSalesWarehousesRate": band(j, limit)}}


# ---------------------------------------------------------------- C20-08 Mortgageholders

LAYERS = [("First500", "First 500", 0, 500), ("Next500", "Next 500", 500, 1000), ("Next4000", "Next 4,000", 1000, 5000),
          ("Next10000", "Next 10,000", 5000, 15000), ("Over15000", "Over 15,000", 15000, None)]


def mortgage(n, limit):
    def b():
        sub = base()
        put(sub, MORT, {"Limit": limit, "NumberMortgages": str(n)})
        return sub
    return b


def expect_mortgage(n, limit):
    def e(data, j):
        out = {}
        for key, label, lo, hi in LAYERS:
            cnt = max(0, min(n, hi if hi else n) - lo)
            out[key + "Mortgages"] = str(cnt)
            if cnt or key == "First500":
                out[key + "Rate"] = val(j, "MortgageholdersErrorsAndOmissRate", "Rate", NumOfMortgages=label,
                                        MortgageholdersLimitOfInsPerMortg=limit)
        return {MORT: out}
    return e


# ---------------------------------------------------------------- C20-09 Fungus

def fungus(separate):
    def b():
        sub = base()
        cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
        cp["FungusWetRotDryRotBacteriaCov"] = "Separate Limits" if separate else "Policy Limit"
        loc = at(sub)[P + "Location"]
        if separate:
            loc["FungusWetRotDryRotBacteriaCovLocApply"] = "No"
            sts = loc[P + "StructureTable"][P + "Structure"]
            sts.append(copy.deepcopy(sts[0]))
            for st in sts:
                st["FungusWetRotDryRotBacteriaCovStructApply"] = "Yes"
        put(sub, FUNGUS, {"SubLimit": "25000" if separate else "50000",
                          "IncreasedPeriodOfRestoration": "120" if separate else "90",
                          "SeparatePremisesOrLocations": "Yes" if separate else "Not Applicable"})
        for bi in [d for k, d in walk(sub) if k == P + "BusinessIncome"]:
            bi["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
        for i in range(2 if separate else 1):
            for r in BIF:
                put(sub, r, idx=i)
        return sub
    return b


def expect_fungus(separate):
    def e(data, j):
        # the BI fungus records carry a TotalPremium (not a Premium) that the policy record sums
        days = "120" if separate else "90"
        tot = sum(Decimal(n.first("TotalPremium").text) for r in BIF for n in r16.find(data, P + r))
        out = {FUNGUS: {"ExcessOfSubLimitRate": val(j, "FungusExcessOfSubLimitRate", "Rate", Constant="Y"),
                        "IncrementalRate": val(j, "FungusIncrementalRate", "Rate", Constant="Y"),
                        "FinalBusinessIncomeFungusPremium": str(tot)}}
        for r in BIF:
            for i in range(len(r16.find(data, P + r))):
                out[(r, i)] = {"Factor": val(j, "FungusIncrdPeriodFactor", "Factor", IncrdPeriodOfRestorationFungus=days)}
        return out
    return e


# ---------------------------------------------------------------- C20-10 furs / jewelry / patterns / stamps

def special_col(v):
    def b():
        sub = base()
        if v == 1:
            put(sub, FURS, {"Indicator": "Yes", "Limit": "20000"})
            put(sub, JEWEL, {"Indicator": "Yes", "Limit": "10000", "ValueIndicator": "Worth $100 or less per item"})
            put(sub, PATT, {"Indicator": "Yes", "Limit": "20000"})
            put(sub, STAMPS, {"Indicator": "Yes", "Limit": "5000"})
        else:
            put(sub, JEWEL, {"Indicator": "Yes", "Limit": "10000", "ValueIndicator": "Worth more than $100 per item"})
            put(sub, FURS, {"Indicator": "No"})
            at(sub)[P + "PersonalProperty"][P + "HigherLimitsPersonalPropertyTable"] = {P + "HigherLimitsPersonalProperty": [
                {"SpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFurIndicator": "Yes",
                 "SpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFurLimit": "30000"}]}
        return sub
    return b


def expect_special_col(v):
    def e(data, j):
        jw = "Worth $100 or less per item" if v == 1 else "Worth more than $100 per item"
        out = {JEWEL: {"BaseSpecialLimit": val(j, "PreciousMetalsBaseSpecialLimit", "SpecialLimit", JewelryAndWatchesIndicator=jw),
                       "LimitToUse": "10000"},
               FURS: {"BaseSpecialLimit": val(j, "FurBaseSpecialLimit", "SpecialLimit", Constant="Y"),
                      "LimitToUse": "20000" if v == 1 else "30000"}}
        if v == 1:
            out[PATT] = {"BaseSpecialLimit": val(j, "PatternsBaseSpecialLimit", "SpecialLimit", Constant="Y"), "LimitToUse": "20000"}
            out[STAMPS] = {"BaseSpecialLimit": val(j, "StampsBaseSpecialLimit", "SpecialLimit", Constant="Y"), "LimitToUse": "5000"}
        return out
    return e


# ---------------------------------------------------------------- C20-11 Radioactive

def radio_plain():
    sub = base()
    for r in RADIO:
        put(sub, r, {"Limit": "40000", "Rate": "0.100"})
    return sub


def radio_blanket(flag):
    def b():
        sub = g18.a3()
        cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
        cp["CommercialPropertyBlanketRatingTable"]["CommercialPropertyBlanketRating"][0][
            "CommercialPropertyBlanketRatingDetailTable"]["CommercialPropertyBlanketRatingDetail"][0]["RadioactiveContamination"] = flag
        sts = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]
        for st, rate in zip(sts, ("0.100", "0.200")):
            st[P + "RadioactiveContaminationTable"] = {P + "RadioactiveContamination": [{"Limit": st["Limit"], "Rate": rate}]}
        return sub
    return b


def expect_radio_blanket(flag):
    def e(data, j):
        # the limit-weighted average of the blanketed buildings' own rates: (0.1 x 100,000 + 0.2 x 200,000) / 300,000
        return {("Structure", 0): {"BlktRadioactiveContaminationAvgRate": "0.167"},
                ("Structure", 1): {"BlktRadioactiveContaminationAvgRate": "0.167"}}
    return e


# ---------------------------------------------------------------- C20-12 Pier and Wharf / ACP

def pier(constr):
    def b():
        sub = base()
        for r in PIER:
            put(sub, r, {"Construction": constr, "Limit": "40000"})
        acp = {"Type": BULK, "WatercraftExclBuybackConstrctnOption": constr, "Limit": "30000"}
        put(sub, "AdditionalCoveredPropertyDetail", acp)
        put(sub, "AdditionalCoveredPropertySpecialClassDetail", acp)
        return sub
    return b


def expect_pier(constr):
    def e(data, j):
        opt = sval(j, "WatercraftExclusionBuybackConstructionOptionsConverted", "Value", WatercraftExclBuybackConstrctnOptions=constr)
        rate = val(j, "PierAndWharfRates", "Rate", WatercraftExclBuybackConstrctnOptionsConverted=opt)
        acp = val(j, "WatercraftExclBuybackFactor", "Factor", WatercraftExclBuybackConstrctnOptionsConverted=opt)
        out = {PIER[0]: {"Rate": rate}, PIER[2]: {"Rate": rate}, PIER[1]: {"Factor": rate}, PIER[3]: {"Factor": rate}}
        out.update({r: {"WatercraftExclBuybackRate": acp} for r in ACP})
        return out
    return e


# ---------------------------------------------------------------- C20-13 Food

def food():
    sub = base()
    for r in FOOD:
        put(sub, r, {"FoodLimit": "10000"} if "FoodOnly" in r else {"AdvertisingLimit": "20000"})
    return sub


def expect_food(data, j):
    fr = val(j, "FoodContaminationRate", "Rate", Constant="Y")
    ar = val(j, "FoodContaminationAdditionalAdvertisingExpenseRate", "Rate", Constant="Y")
    return {r: ({"FoodRate": fr} if "FoodOnly" in r else {"AdvertisingRate": ar}) for r in FOOD}


# ---------------------------------------------------------------- C20-14 Equipment Breakdown

EB_CASES = {1: ("Institutional", "All other institutional risks", "Eliminated", "50000", "100", None),
            2: ("Industrial and Processing", "All other industrial and processing risks", "Replaced By 24 Hours", "100000", "250", "250")}


def eb(v):
    cat, grp, period, amm, haz, ded = EB_CASES[v]

    def b():
        sub = base()
        if ded:
            at(sub)[P + "Structure"]["Deductible"] = ded
        inter = {EBB: {"OccupancyCategory": cat, "OccupancyGroup": grp}}
        put(sub, EBB + "EBCov", inter=inter)
        put(sub, EBB + "AmmoniaContaminationCov", {"AmmoniaContamination": amm}, inter=inter)
        put(sub, EBB + "HazardousSubstanceOtherThanAmmoniaCov",
            {"HazardousSubstanceOtherThanAmmonia": "50000", "HazardousSubstanceOtherThanAmmoniaManualPremium": haz}, inter=inter)
        put(sub, EBI + "Coverage")
        put(sub, EBI + "WaitingPeriodCoverage")
        at(sub)[P + "BusinessIncome"][P + NOWAIT + "Table"] = {P + NOWAIT: [{"TimePeriod": period}]}
        return sub
    return b


def expect_eb(v):
    cat, grp, period, amm, haz, ded = EB_CASES[v]

    def e(data, j):
        g = val(j, "OccupancyGroupNumber", "GroupNumber", OccupCategory=cat, ClassCode="0951", OccupancyGroup=grp)
        st = r16.find(data, P + "Structure")[0]
        tot = Decimal(st.first("TotAmtInsurance").text)
        import csv
        f = book_for(j, r2.ASOF).parent.package.content / "Rate Tables" / "EquipmentBreakdownPropertyDamagePremium.RateTable.csv"
        prem = next(r["Premium"] for r in csv.DictReader(open(f, encoding="utf-8-sig")) if r["StateCode"] == "CW"
                    and r["GroupNumber"] == str(g) and Decimal(r["TotalPropertyLimit_From"]) <= tot < Decimal(r["TotalPropertyLimit_ToLessThan"]))
        out = {EBB: {"OccupancyGroupNumber": g, "LossCost": prem},
               EBI: {"OccupancyGroupNumber": g, "LossCost": val(j, "EquipmentBreakdownTimeElementLossCost", "LossCost", GroupNumber=g),
                     # the BI no-waiting-period record's Factor = its table row - 1 (SetFactor), copied as WaitingPeriod
                     "WaitingPeriod": val(j, "BusnIncomeChangesTimePeriod", "Factor", TimePeriod=period) - 1},
               EBB + "AmmoniaContaminationCov": {"AmmoniaContaminationRate": val(j, "AmmoniaContamination", "LossCost", Constant="Y")}}
        if ded:
            out[EBB]["DeductibleFactor"] = val(j, "Deductible250Factor", "Factor", CauseOfLoss="All Other")
        return out
    return e


# ---------------------------------------------------------------- cases

def cases():
    return {
        "F1": ("C20-06", "OR", "Fire Department, own limit 25,000", fire(False), expect_fire(False), ["LocationFireDepartmentCharge"]),
        "F2": ("C20-06", "OR", "Fire Department, own 25,000 + the location's higher-limits record 50,000", fire(True), expect_fire(True),
               ["LocationFireDepartmentCharge"]),
        "TB1": ("C20-07", "OR", "Tobacco, contents 50,000 (band 0-50,000: 26)", tobacco("50000"), expect_tobacco("50000"),
                ["PersonalPropertyTobaccoSalesWarehousesCoverage"]),
        "TB2": ("C20-07", "OR", "Tobacco, contents 100,000 (band 75,000-100,000: 53)", tobacco("100000"), expect_tobacco("100000"),
                ["PersonalPropertyTobaccoSalesWarehousesCoverage"]),
        "MG1": ("C20-08", "OR", "Mortgageholders 500 mortgages at 25,000", mortgage(500, "25,000"), expect_mortgage(500, "25,000"), [MORT]),
        "MG2": ("C20-08", "OR", "Mortgageholders 1,001 at 50,000", mortgage(1001, "50,000"), expect_mortgage(1001, "50,000"), [MORT]),
        "MG3": ("C20-08", "OR", "Mortgageholders 15,000 at 100,000", mortgage(15000, "100,000"), expect_mortgage(15000, "100,000"), [MORT]),
        "MG4": ("C20-08", "OR", "Mortgageholders 20,000 at 1,000,000 (all five layers)", mortgage(20000, "1,000,000"),
                expect_mortgage(20000, "1,000,000"), [MORT]),
        "FU1": ("C20-09", "OR", "Fungus, Policy Limit, sub-limit 50,000, BI 90 days", fungus(False), expect_fungus(False), [FUNGUS]),
        "FU2": ("C20-09", "OR", "Fungus, Separate Limits, sub-limit 25,000, two buildings applying, BI 120 days", fungus(True),
                expect_fungus(True), [FUNGUS]),
        "SC1": ("C20-10", "OR", "Furs 20,000, jewelry 10,000 (<= $100 per item: base 0), patterns 20,000, stamps 5,000 (base 250)",
                special_col(1), expect_special_col(1), [FURS, JEWEL, PATT, STAMPS]),
        "SC2": ("C20-10", "OR", "Jewelry 10,000 (> $100 per item: base 2,500); furs through the contents' higher-limits record 30,000",
                special_col(2), expect_special_col(2), [FURS, JEWEL]),
        "RA1": ("C20-11", "OR", "Radioactive, all five coverages, own limit 40,000, rate 0.100, unblanketed", radio_plain,
                lambda data, j: {}, RADIO),
        "RA2": ("C20-11", "OR", "Radioactive on chunk 9's blanket, detail Yes (average rate)", radio_blanket("Yes"),
                expect_radio_blanket("Yes"), ["RadioactiveContamination"]),
        "RA3": ("C20-11", "OR", "Radioactive on chunk 9's blanket, detail No (own rates, own limits)", radio_blanket("No"),
                expect_radio_blanket("No"), ["RadioactiveContamination"]),
        "PW1": ("C20-12", "OR", "Pier and Wharf x4 + ACP x2, construction option 1", pier(PIER1), expect_pier(PIER1), PIER + ACP),
        "PW2": ("C20-12", "OR", "Pier and Wharf x4 + ACP x2, construction option 5", pier(PIER5), expect_pier(PIER5), PIER + ACP),
        "FC1": ("C20-13", "OR", "Food Contamination: food 10,000, advertising 20,000, on BI and SCBI", food, expect_food, FOOD),
        "EB1": ("C20-14", "OR", "Equipment Breakdown, Institutional (group 3), no waiting period Eliminated, ammonia 50,000",
                eb(1), expect_eb(1), EB),
        "EB2": ("C20-14", "OR", "Equipment Breakdown, Industrial (group 7), Replaced By 24 Hours, deductible 250, ammonia 100,000",
                eb(2), expect_eb(2), EB),
    }


# ------------------------------------------------------------------- run

cen20 = import_module("901_chunk20_census")


def predict(data, rec, j):
    """(hand, engine) per node: SetPremium (chunk 20's census reader, which also reads a Sum) evaluated by hand
    on the rated tree, the state's own rule if it files one."""
    f = book_for(j, r2.ASOF).state.package.content / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if not f.exists() or not cen20.set_premium(f.read_text(encoding="utf-8-sig", errors="replace")):
        f = r2.CW / "Rules" / f"{P}{rec}Rules.Rule.xml"
    body = cen20.set_premium(f.read_text(encoding="utf-8-sig", errors="replace"))
    out = []
    for node in rc1.find(data, P + rec):
        prem = node.first("Premium")
        out.append((r16.hand(body, node), None if prem is None else prem.text))
    return out


def payload(sub, localize=True):
    """r11's payload, except Mortgageholders' Limit: that record declares Limit as TEXT (the domain value
    "25,000", the rate table's key) where every other Limit is xs:int, so it is sent unconverted."""
    sub = copy.deepcopy(sub)
    for k, d in walk(sub):
        if k == P + MORT and "Limit" in d:
            d["MORTLIMIT__"] = d.pop("Limit")
    req = r11.payload(sub, localize=localize)

    def fix(o):
        if isinstance(o, dict):
            if "MORTLIMIT__" in o:
                o["Limit"] = o.pop("MORTLIMIT__")
            for v in o.values():
                fix(v)
        elif isinstance(o, list):
            for v in o:
                fix(v)
    fix(req)
    return req


def field_checks(data, expect):
    out = []
    for key, fields in expect.items():
        rec, idx = key if isinstance(key, tuple) else (key, 0)
        nodes_ = r16.find(data, P + rec)
        node = nodes_[idx] if len(nodes_) > idx else None
        for f, want in fields.items():
            got = None if node is None or node.first(f) is None else node.first(f).text
            out.append((f"{rec}[{idx}]", f, got, want))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, expect, recs)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), j)
        except InterpretError as exc:
            print(f"{cid:3s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        fc = field_checks(data, expect(data, j))
        fbad = [c for c in fc if not same(c[2], c[3])]
        lines, bad, priced = [], [], 0
        preds[cid] = {}
        for rec in recs:
            res = predict(data, rec, j)
            nodes_ = rc1.find(data, P + rec)
            off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
            res = [(Decimal(0) if o else h, e) for (h, e), o in zip(res, off)] if len(off) == len(res) else res
            ok = bool(res) and all(not str(h).startswith("hand") and same(h, e) for h, e in res)
            nz = [h for h, e in res if e not in (None, "") and not same(e, 0)]
            priced += bool(nz)
            preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:70]:70s} predicted {[str(h) for h, _ in res]}"
                         f" engine {[e for _, e in res]}" + ("" if nz else "  ($0)"))
            if not ok or not nz:
                bad.append(rec)
        print(f"{cid:3s} {task} {j} {label}: engine {'as derived' if not bad and not fbad else 'DIFFERS'} "
              f"({priced} of {len(recs)} priced; {len(fc) - len(fbad)} of {len(fc)} own values = independent)")
        for w, f, g, want in fc:
            print(f"      {'ok  ' if same(g, want) else 'FAIL'} {w[:52]:52s} {f:40s} tree {g}  independent {want}")
        print("\n".join(lines))
        if bad or fbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, j, label, build, expect, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = payload(build())
            (gc.OUT / f"chunk20_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {cid:3s} ISO REFUSES {m.group(0)[:220] if m else str(exc.body)[:220]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk20_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
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
    print(f"\nRC-2 (C20-06 to C20-14): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
