#!/usr/bin/env python3
"""Chunk 16, RC-2 (C16-06 to C16-12): golden cases for the 27 records ISO never priced.

Every case sits on chunk 7's five-coverage Oregon policy with chunk 15's modifiers
(package discount 0.85, IRPM 1.15, credit 0.9, the building's own credit 0.95) and
chunk 10's earthquake election on every group (so the EQ forms price). Mine
Subsidence runs each of its five states on that policy made portable.

HOW EACH PREDICTION IS MADE, before the engine's answer is compared:
  * the family's OWN factor is looked up independently from its filed table (CSV)
    and its container's arithmetic done by hand:
      no waiting period   Factor = round3(time-period factor - 1): "Eliminated" 1.15 -> 0.15,
                          "Replaced By 24 Hours" 1.10 -> 0.10
      Civil Authority     Factor = round3(period factor - 1): 60 -> 0.10, 90 -> 0.15, 180 -> 0.25
      EPI                 Factor = ExtendedPeriodFactor (the premium uses round3(Factor - 1)):
                          90 -> 1.05, 180 -> 1.25, 270 -> 1.30
      Molten Material     Factor = 0.1
      Spoilage            class from the description, rate from (class, cause, agreement),
                          selling-price factor 1.4 when "Yes"
      Pollutant Clean Up  Group I / II rate 0.5, Broad / Special 0.006, EQ 0.75; deductible
                          factor from its row. The location's "highest" Group I rate, AS
                          WRITTEN: SetHighestBldgPollutantBGIRate binds the running highest
                          as a WithArgs parameter ONCE, before its ForEach over buildings, so
                          every building beats the starting 0 and the LAST building wins.
                          G9: last building 0.097 x 1.039 = 0.101 -> Group I $22; the
                          name's reading (true max, 0.239 x 1.172 = 0.280) would give $60.
                          First predicted the max ($60); the engine gave $22; ISO settles.
                          G9b swaps the buildings, so both readings give 0.280 and $60.
      Mine Subsidence     IL Option A3.D.2: $19.91 + $2.84 per additional $10,000 (50,000:
                          31.27 -> $31); IL A3.D.1 at 100,000 (where the options differ): the
                          dwelling table row; KY: its row by type and limit; IN / OK / WV: the
                          manual premium (OK through the modifiers). The building record carries
                          its figure in MineSubsidencePremium / the base-premium fields, and
                          the POLICY record carries the Premium (a sum over buildings).
  * the premium is then evaluated BY HAND from the filed SetPremium (174_'s evaluator,
    half-up at every DecimalPlaces), with those independent factors substituted and the
    parent coverage's own rates (chunks 5-10, ISO-confirmed) read from the tree.
  * the engine must equal it, and --live ISO must equal it, with every premium on the
    policy compared field for field and the message sets compared.

    python scripts/cf/175_chunk16_rc2.py [--live] [--cases G6,G12IL]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
cmp = import_module("154_chunk13_rc5_fields_messages")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
rc2 = import_module("169_chunk15_rc2")
eqg = import_module("95_chunk10_c10-11_all_groups_chain")
r16 = import_module("174_chunk16_rc1")
r11 = gc.r11
r11.NUMERIC |= {"ManualPremium", "MultiPremiumAndDispersionCreditFactorUser", "MineSubsidenceLimit",
                "MineSubsidenceManualPremium"}
ASOF = "20260917"
P = "CommercialProperty"
CW = book_for("OR", ASOF).parent.package.content
EQ_ON = "Yes, Not Included in Blanket"
FAIL = []


def q(x, dp):
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-dp), ROUND_HALF_UP)


def csv_rows(name, pkg=CW):
    with open(pkg / "Rate Tables" / f"{name}.RateTable.csv", encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def row(name, col, pkg=CW, **keys):
    for r in csv_rows(name, pkg):
        if all(str(r[k]) == str(v) for k, v in keys.items()):
            return Decimal(r[col])
    raise LookupError(f"{name}: no row {keys}")


# ---------------------------------------------------------------- the policy

def base(state="OR"):
    sub = grp.five()
    at = rc1.node_dicts(sub)
    at[P].update(rc2.POLICY)
    at[P + "Structure"]["MultiPremiumAndDispersionCreditFactor"] = rc2.BUILDING_CREDIT
    at[P + "Structure"].setdefault("WindstormOrHailDeductible", "1,000")
    at[P + "Location"].update(eqg.LOC_EQ)
    at[P + "Structure"].update(eqg.EQ_ELECTION)
    at[P + "SpecialClass"].update(eqg.EQ_ELECTION)
    at[P + "BusinessIncome"]["EQCovIndicator"] = EQ_ON
    at[P + "SpecialClassBusnIncome"]["EQCovIndicator"] = EQ_ON
    if state != "OR":
        at[P]["State"] = state
        loc = at[P + "Location"]
        loc.pop("BasicGroupIRatingTerr", None)
        loc.pop("BasicGroupIIRatingTerr", None)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc.update(s18.STATE_LOC.get(state, {}))
    return sub


_XSD = {}


def put(sub, rec, fields=None, state="OR"):
    if state not in _XSD:                       # the DataDef XSD is large: parse it once per state
        _XSD[state] = rc1.xsd_for(book_for(state, ASOF))
    r16.place(sub, _XSD[state], rec, fields or {})


def container(sub, parent, name):
    d = rc1.node_dicts(sub)[P + parent]
    return d[P + name + "Table"][P + name][0]


# ------------------------------------------------------- independent factors

EPI_F = {p: row("ExtendedPeriodFactor", "Factor", StateCode="CW", ExtendedPeriod=p) for p in ("90", "180", "270")}
TIME_F = {t: q(row("BusnIncomeChangesTimePeriod", "Factor", StateCode="CW", TimePeriod=t) - 1, 3)
          for t in ("Eliminated", "Replaced By 24 Hours")}
CIVIL_F = {p: q(row("CivilAuthorityIncreasedCoveragePeriodEndtFactor", "Factor", StateCode="CW",
                    CivilAuthorityIncreasedCoveragePeriod=p) - 1, 3) for p in ("60", "90", "180")}
MOLTEN_F = row("MoltenMaterialFactor", "Factor", StateCode="CW", Constant="Y")
POLL_RATE = {f: row("PollutantCleanUpAndRemovalRate", "Rate", StateCode="CW", CauseOfLossOptionalForm=f)
             for f in ("GroupI", "GroupII", "Broad", "Special", "Earthquake")}
POLL_DED = {d: row("PollutantCleanUpAndRemovalDeductibleFactor", "Factor", StateCode="CW", PollutantDeductible=d)
            for d in ("1,000", "2,500")}


def spoilage_factors(desc, cause, agreement, selling):
    cls = next(r["Value"] for r in csv_rows("SpoilageClassification") if r["SpoilageDesc"] == desc)
    rate = row("SpoilageCovRate", "Rate", StateCode="CW", SpoilageClassification=cls,
               SpoilageCauseOfLoss=cause, RefrigerationMaintenanceAgreement=agreement)
    spf = row("SpoilageSellingPriceFactor", "Factor", StateCode="CW", Constant="Y") if selling == "Yes" else Decimal(1)
    return cls, rate, spf


# ---------------------------------------------------------------- the cases
#: id -> (task, label, state, build(), {record: {field: independent value}} , min premium records)

def g6():
    sub = base()
    bi = rc1.node_dicts(sub)[P + "BusinessIncome"]
    bi.update({"CauseOfLoss": "Broad", "ExtendedPeriod": "270"})
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake"):
        put(sub, f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage")
    return sub


def g7a():
    sub = base()
    scbi = rc1.node_dicts(sub)[P + "SpecialClassBusnIncome"]
    scbi.update({"CauseOfLoss": "Special", "ExtendedPeriod": "180"})
    for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"):
        put(sub, f"SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage")
    return sub


def g7b():
    sub = base()
    rc1.node_dicts(sub)[P + "SpecialClassBusnIncome"].update({"CauseOfLoss": "Broad", "ExtendedPeriod": "90"})
    put(sub, "SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverageBroadCoverage")
    return sub


NW = "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod"
NW_SC = "BusnIncomeChangesBeginningOfThePerOfRestrtnNoWaitingPerSpclClassBusnIncome"


def g7c():
    sub = base()
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        put(sub, f"{NW}{f}Coverage")
        put(sub, f"{NW_SC}{f}Coverage")
    container(sub, "BusinessIncome", NW)["TimePeriod"] = "Eliminated"
    container(sub, "SpecialClassBusnIncome", NW + "SpclClassBusnIncome")["TimePeriod"] = "Replaced By 24 Hours"
    return sub


CA = "CivilAuthorityIncreasedCoveragePeriod"


def g8a():
    sub = base()
    rc1.node_dicts(sub)[P + "BusinessIncome"]["CauseOfLoss"] = "Special"
    for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake"):
        put(sub, f"{CA}{f}Coverage")
    put(sub, f"{CA}RadiusCoverage", {"ManualPremium": rc2.MANUAL})
    container(sub, "BusinessIncome", CA)["IncreasedCoveragePeriod"] = "180"
    return sub


def g8b():
    sub = base()
    rc1.node_dicts(sub)[P + "SpecialClassBusnIncome"]["CauseOfLoss"] = "Broad"
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake"):
        put(sub, f"{CA}SpclClassBusnIncome{f}Coverage")
    put(sub, f"{CA}SpclClassBusnIncomeRadiusCoverage", {"ManualPremium": rc2.MANUAL})
    container(sub, "SpecialClassBusnIncome", CA + "SpclClassBusnIncome")["IncreasedCoveragePeriod"] = "60"
    return sub


def g8c():
    sub = base()
    rc1.node_dicts(sub)[P + "SpecialClassBusnIncome"]["CauseOfLoss"] = "Special"
    put(sub, f"{CA}SpclClassBusnIncomeSpecialCoverage")
    container(sub, "SpecialClassBusnIncome", CA + "SpclClassBusnIncome")["IncreasedCoveragePeriod"] = "90"
    return sub


PC = "PollutantCleanUpAndRemovalAdditionalAggregateLimitOfInsuranceLocation"


def g9():
    """Two buildings whose Group I rates differ (class 0951 vs 0311, limits 100,000 / 200,000),
    one Broad and one Special, so every form prices and 'highest' has a real choice."""
    sub = base()
    at = rc1.node_dicts(sub)
    loc = at[P + "Location"]
    b1 = at[P + "Structure"]
    b1["CauseOfLoss"] = "Broad"
    b2 = copy.deepcopy(b1)
    b2.update({"ClassCode": "0311", "Limit": "200000", "FullBldgValue": "200000", "CauseOfLoss": "Special"})
    b2.pop("CommercialPropertyBusinessIncomeTable", None)
    b2.pop("CommercialPropertyOccupClassTable", None)
    loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"].append(b2)
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake"):
        put(sub, f"{PC}{f}Coverage")
    c = container(sub, "Location", PC)
    c.update({"Limit": "60000", "Deductible": "2,500"})
    return sub


def g9b():
    sub = g9()
    loc = rc1.node_dicts(sub)[P + "Location"]
    lst = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]
    b1, b2 = lst
    # move the business income / occupancy to the new first building, keep each building's own fields
    b2["CommercialPropertyBusinessIncomeTable"] = b1.pop("CommercialPropertyBusinessIncomeTable")
    b2["CommercialPropertyOccupClassTable"] = b1.pop("CommercialPropertyOccupClassTable")
    lst[:] = [b2, b1]
    return sub


def g10():
    sub = base()
    for r in ("MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome",
              "MoltenMaterialSpecialClass", "MoltenMaterialSpclClassBusnIncome"):
        put(sub, r)
    return sub


SPOIL = dict(Description="Florists", SpoilageCauseOfLoss="Both Breakdown or Contamination and Power Outage",
             RefrigerationMaintenanceAgreement="Not Applicable", SellingPrice="Yes", Limit="25000")


def g11():
    sub = base()
    put(sub, "SpoilageCoverage", dict(SPOIL))
    return sub


def mine(state, pol, struct=None, recs=(), rec_fields=None):
    def build():
        sub = base(state)
        at = rc1.node_dicts(sub)
        at[P].update(pol)
        if struct:
            at[P + "Structure"].update(struct)
        for r in recs:
            put(sub, r, (rec_fields or {}).get(r, {}), state=state)
        return sub
    return build


MS, SMS = "MineSubsidenceCoverage", "StructureMineSubsidenceCoverage"
ALE, ALES = "MineSubsidenceAdditionalLivingExpenseCoverage", "MineSubsidenceAdditionalLivingExpenseStructureCoverage"
IL_PKG = book_for("IL", ASOF).state.package.content
KY_PKG = book_for("KY", ASOF).state.package.content


def il_d2(limit):
    first = row("MineSubsidenceFirst10000Coverage", "Premium", IL_PKG, StateCode="IL", Constant="Y")
    each = row("MineSubsidenceEachAdditional10000", "Premium", IL_PKG, StateCode="IL", Constant="Y")
    return first, each


def il_d1(limit, cons="Frame"):
    for r in csv_rows("MineSubsidenceDwellingPremium", IL_PKG):
        if r["ConstructionTypeToUse"] == cons and Decimal(r["Limit_From"]) <= limit < Decimal(r["Limit_ToLessThan"]):
            return Decimal(r["Premium"])
    raise LookupError("IL dwelling row")


def ky(limit, typ):
    for r in csv_rows("MineSubsidencePremium", KY_PKG):
        if r["MineSubsidenceStructType"] == typ and Decimal(r["Limit_From"]) <= limit < Decimal(r["Limit_ToLessThan"]):
            return Decimal(r["Premium"])
    raise LookupError("KY row")


def cases():
    E = lambda f: f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"
    ES = lambda f: f"SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"
    fl, fe = il_d2(50000)
    return {
        "G6": ("C16-06", "EPI on Business Income, Broad + EQ, 270 days", "OR", g6,
               {E(f): {"Factor": EPI_F["270"]} for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake")}),
        "G7a": ("C16-07", "EPI on Special Class BI, Special + EQ, 180 days", "OR", g7a,
                {ES(f): {"Factor": EPI_F["180"]} for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")}),
        "G7b": ("C16-07", "EPI on Special Class BI, Broad, 90 days", "OR", g7b,
                {ES("Broad"): {"Factor": EPI_F["90"]}}),
        "G7c": ("C16-07", "no waiting period: BI 'Eliminated', SCBI '24 hours', with EQ", "OR", g7c,
                {**{f"{NW}{f}Coverage": {"../Factor": TIME_F["Eliminated"]} for f in ("BasicGroupI", "BasicGroupII", "Earthquake")},
                 **{f"{NW_SC}{f}Coverage": {"../Factor": TIME_F["Replaced By 24 Hours"]} for f in ("BasicGroupI", "BasicGroupII", "Earthquake")}}),
        "G8a": ("C16-08", "Civil Authority on BI, Special + EQ + Radius, 180 days", "OR", g8a,
                {**{f"{CA}{f}Coverage": {"../Factor": CIVIL_F["180"]} for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")},
                 f"{CA}RadiusCoverage": {}}),
        "G8b": ("C16-08", "Civil Authority on SCBI, Broad + EQ + Radius, 60 days", "OR", g8b,
                {**{f"{CA}SpclClassBusnIncome{f}Coverage": {"../Factor": CIVIL_F["60"]} for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake")},
                 f"{CA}SpclClassBusnIncomeRadiusCoverage": {}}),
        "G8c": ("C16-08", "Civil Authority on SCBI, Special, 90 days", "OR", g8c,
                {f"{CA}SpclClassBusnIncomeSpecialCoverage": {"../Factor": CIVIL_F["90"]}}),
        "G9": ("C16-09", "Pollutant Clean Up, two buildings (Broad, Special) + EQ, limit 60,000, deductible 2,500", "OR", g9,
               {f"{PC}BasicGroupICoverage": {"BasicGroupIFactor": POLL_RATE["GroupI"], "DeductibleFactor": POLL_DED["2,500"], "HighestPollutantBGIRate": "LAST_BGI"},
                f"{PC}BasicGroupIICoverage": {"BasicGroupIIFactor": POLL_RATE["GroupII"], "DeductibleFactor": POLL_DED["2,500"]},
                f"{PC}BroadCoverage": {"BroadRate": POLL_RATE["Broad"], "DeductibleFactor": POLL_DED["2,500"]},
                f"{PC}SpecialCoverage": {"SpecialRate": POLL_RATE["Special"], "DeductibleFactor": POLL_DED["2,500"]},
                f"{PC}EarthquakeCoverage": {"EQFactor": POLL_RATE["Earthquake"], "DeductibleFactor": POLL_DED["2,500"]}}),
        "G9b": ("C16-09", "Pollutant Clean Up, the same two buildings in the other order", "OR", g9b,
                {f"{PC}BasicGroupICoverage": {"BasicGroupIFactor": POLL_RATE["GroupI"], "DeductibleFactor": POLL_DED["2,500"], "HighestPollutantBGIRate": "LAST_BGI"}}),
        "G10": ("C16-10", "Molten Material on building, contents, BI, special class, SCBI", "OR", g10,
                {r: {"Factor": MOLTEN_F} for r in ("MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome",
                                                  "MoltenMaterialSpecialClass", "MoltenMaterialSpclClassBusnIncome")}),
        "G11": ("C16-11", "Spoilage, Florists (Class 3), both causes, no agreement, selling price, 25,000", "OR", g11,
                {"SpoilageCoverage": dict(zip(("Class", "Rate", "SellingPriceFactor"),
                                              spoilage_factors("Florists", SPOIL["SpoilageCauseOfLoss"],
                                                               SPOIL["RefrigerationMaintenanceAgreement"], "Yes")))}),
        "G12IL2": ("C16-12", "Mine Subsidence IL, Option A3.D.2, all buildings, 50,000", "IL",
                   mine("IL", {"MineSubsidenceCoverage": "All Buildings", "MineSubsidenceLimit": "50000",
                               "MineSubsidenceRatingOption": "Option A3.D.2"}, recs=(MS, SMS)),
                   {SMS: {"__expect__": {"MineSubsidenceBasePremium": fl, "EachAdditional10000TotalPremium": q(fe * 4, 2)}},
                    MS: {"__expect__": {"Premium": q(fl + fe * 4, 0)}}}),
        "G12IL1": ("C16-12", "Mine Subsidence IL, Option A3.D.1 (dwelling table, Frame), 100,000", "IL",
                   mine("IL", {"MineSubsidenceCoverage": "All Buildings", "MineSubsidenceLimit": "100000",
                               "MineSubsidenceRatingOption": "Option A3.D.1"}, recs=(MS, SMS)),
                   {MS: {"__expect__": {"Premium": il_d1(Decimal(100000))}}}),
        "G12KY": ("C16-12", "Mine Subsidence KY, non-dwelling, all buildings, 50,000", "KY",
                  mine("KY", {"MineSubsidenceCoverage": "All Buildings", "MineSubsidenceLimit": "50000"},
                       struct={"MineSubsidenceType": "Non Dwelling Structure"}, recs=(MS, SMS)),
                  {SMS: {"__expect__": {"MineSubsidenceBasePremium": ky(Decimal(50000), "Non Dwelling Structure")}},
                   MS: {"__expect__": {"Premium": ky(Decimal(50000), "Non Dwelling Structure")}}}),
        "G12IN": ("C16-12", "Mine Subsidence IN, all buildings + living expense, manual premiums", "IN",
                  mine("IN", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS, ALE),
                       rec_fields={MS: {"ManualPremium": "250"}, ALE: {"ManualPremium": "75", "AdditionalLivingExpense": "Yes"}}),
                  {MS: {"__expect__": {"Premium": Decimal(250)}}, ALE: {"__expect__": {"Premium": Decimal(75)}}}),
        "G12INs": ("C16-12", "Mine Subsidence IN, scheduled buildings + structure living expense", "IN",
                   mine("IN", {"MineSubsidenceCoverage": "Scheduled Buildings"}, recs=(SMS, ALES),
                        rec_fields={SMS: {"ManualPremium": "180"}, ALES: {"ManualPremium": "40", "AdditionalLivingExpense": "Yes"}}),
                   {SMS: {"__expect__": {"Premium": Decimal(180)}}, ALES: {"__expect__": {"Premium": Decimal(40)}}}),
        "G12OK": ("C16-12", "Mine Subsidence OK, manual premium through the modifiers", "OK",
                  mine("OK", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS, SMS),
                       rec_fields={MS: {"ManualPremium": "1090"}},
                       struct={"MineSubsidenceManualPremium": "300"}),
                  {MS: {}}),
        "G12WV": ("C16-12", "Mine Subsidence WV, manual premium", "WV",
                  mine("WV", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS,),
                       rec_fields={MS: {"ManualPremium": "310"}}),
                  {MS: {"__expect__": {"Premium": Decimal(310)}}}),
    }


# --------------------------------------------------------------- prediction

def bgi_products(data):
    out = []
    for st in rc1.find(data, P + "Structure"):
        a, l = st.first("BasicGroupICauseOfLossAdjustment"), st.first("BasicGroupILOIFactor")
        if a is not None and l is not None and a.text and l.text:
            out.append(q(Decimal(a.text) * Decimal(l.text), 3))
    return out


def last_bgi(data):
    """AS WRITTEN: the running highest is a WithArgs parameter bound once before the ForEach,
    so each building with a product above the STARTING 0 overwrites it: the last one wins."""
    ps = [x for x in bgi_products(data) if x > 0]
    return ps[-1] if ps else Decimal(0)


def highest_bgi(data):
    """max over the location's buildings of round3(BasicGroupICauseOfLossAdjustment x BasicGroupILOIFactor)."""
    best = Decimal(0)
    for st in rc1.find(data, P + "Structure"):
        a, l = st.first("BasicGroupICauseOfLossAdjustment"), st.first("BasicGroupILOIFactor")
        if a is not None and l is not None and a.text and l.text:
            best = max(best, q(Decimal(a.text) * Decimal(l.text), 3))
    return best


def predict(data, rec, overrides, state):
    """hand evaluation of SetPremium with the independent factors substituted on the tree.
    An override key that is itself a path in the rule replaces exactly that path; a bare
    name replaces the paths ending in it. "__expect__" instead checks named fields directly
    against independently derived values (Mine Subsidence)."""
    if "__expect__" in overrides:
        out, checks = [], []
        for node in rc1.find(data, P + rec):
            for field, val in overrides["__expect__"].items():
                hit = node.first(field)
                checks.append((field, None if hit is None else hit.text, val))
            prem = node.first("Premium")
            want = overrides["__expect__"].get("Premium")
            out.append((want, None if prem is None else prem.text))
        return out, checks
    f = CW / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if state != "OR":
        sf = book_for(state, ASOF).state.package.content / "Rules" / f"{P}{rec}Rules.Rule.xml"
        if sf.exists() and r16.cen.set_premium(sf.read_text(encoding="utf-8-sig", errors="replace")):
            f = sf
    body = r16.cen.set_premium(f.read_text(encoding="utf-8-sig", errors="replace"))
    paths = set(re.findall(r'FromDataDef="([^"]+)"', body))
    out, checks = [], []
    for node in rc1.find(data, P + rec):
        saved = []
        for key, val in overrides.items():
            if val == "LAST_BGI":
                val = last_bgi(data)
            targets = [key] if key in paths else [x for x in paths if x.rsplit("/", 1)[-1] == key]
            for path in targets:
                hit = tree.select_one(path, node)
                if hit is not None:
                    checks.append((key, hit.text, val))
                    saved.append((hit, hit.text))
                    hit.text = str(val)
        h = r16.hand(body, node)
        for hit, old in saved:
            hit.text = old
        prem = node.first("Premium")
        out.append((h, None if prem is None else prem.text))
    return out, checks


def same(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return str(a) == str(b)


def iso_of(resp, rec):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + rec:
                out.append(o.get("Premium"))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return [x for x in out if x not in (None, "")]


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
            print(f"{cid:7s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, ov in recs.items():
            res, checks = predict(data, rec, ov, state)
            expect_only = "__expect__" in ov and "Premium" not in ov["__expect__"]
            priced = [(h, e) for h, e in res if e not in (None, "") and Decimal(e) != 0]
            fac_bad = [(f, e, v) for f, e, v in checks if not same(e, v) and f not in ("HighestPollutantBGIRate",)]
            hi_bad = [(f, e, v) for f, e, v in checks if f == "HighestPollutantBGIRate" and not same(e, v)]
            if expect_only:
                ok = bool(checks) and not fac_bad
            else:
                ok = bool(priced) and all(isinstance(h, Decimal) and same(h, e) for h, e in priced) and not fac_bad and not hi_bad
            preds[cid][rec] = None if expect_only else [h for h, _ in priced]
            if cid in ("G9", "G9b") and rec.endswith("BasicGroupICoverage"):
                lines.append(f"      note building products {[str(x) for x in bgi_products(data)]}: as written (last) "
                             f"{last_bgi(data)}, the name's reading (max) {highest_bgi(data)}")
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:70]:70s} predicted {[str(h) for h, _ in priced] or [str(h) for h, _ in res]}"
                         f" engine {[e for _, e in res]}" + (f"  factor engine/independent {fac_bad[:2]}" if fac_bad else "")
                         + (f"  highest engine/independent {hi_bad[:1]}" if hi_bad else ""))
            if not ok:
                bad.append(rec)
        print(f"{cid:7s} {task} {label}: engine {'as derived' if not bad else 'DIFFERS'} ({len(recs)} records)")
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
            (gc.OUT / f"chunk16_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid:7s} ISO REFUSES {m.group(0)[:170] if m else str(exc.body)[:170]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk16_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = preds.get(cid, {}).get(rec, [])
                if want is None:
                    continue                         # checked by its fields, not a Premium
                iso = [x for x in iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid:7s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    print(f"\nRC-2: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
