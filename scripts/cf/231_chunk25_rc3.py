#!/usr/bin/env python3
"""Chunk 25, RC-3 (C25-14..C25-17): Flood zero cases, messages, shared names and exclusions. Live ISO.

Every case is predicted before it runs, from the rule text: each flood premium three ways (229_'s hand models, 174_'s
evaluator, the engine) and the EXACT multiset of flood (level, message) pairs the rules raise (every flood message that
fires must be predicted, and every predicted one must fire). Then ISO: the flood records as predicted, every premium
field for field, the whole (level, message) multiset.

The message conditions, read from the rules (CW 2026 V01):
  property records   General Information missing (no location record); Limit > the full value (unblanketed); location
                     DeductibleInt >= TotalPropertyValue (unblanketed, primary); DeductibleInt >= the own full value
                     (excess); contents / Special Class in a blanket take the DETAIL's deductible (the building
                     always the location's: M8); a blanket member whose detail lacks its coverage flag ("Cannot be Included") or whose
                     BlanketIDNum finds no detail WITH the flag ("valid Flood Blanket ID"); BI / SCBI also "None of the
                     Blanket Covered Property matches" the CovType, and the blanket coinsurance "Greater than 125%"
  blanket detail     no coverage flag; fewer than 2 members; Limit > the 100% total; DeductibleInt >= the 100% total
  location record    a member's location FloodEffDate differs from its detail's; "Other Flood Insurance" fields missing under
                     ancestor::MasterCFCW/Policy, which the engine reads as the document root (as for the stat codes): fires
  parents            Location: FloodCovIndicator Yes with no flood record; Structure: flood on Builders Risk / No Coverage,
                     building and contents excess indicators differ; PP / BI: flood under a Builders Risk building, or
                     CovType Not Applicable under No Coverage; Special Class: SC and SCBI flood constructions differ
  policy             a detail with no coverage; a time-element flood blanket on a Standard Property Policy; a blanket
                     (flood included) with CP 00 70

Cases (Oregon; 229_'s flood_tree):
  C25-14 zero      Z1 deductible 500,000 >= total property value 400,000 (table 6 files 0 there, 3 messages); Z2 limits 1
                   over full value (3 messages, still priced at 100%); Z3 FloodCovIndicator No with flood records (5 General Information
                   messages, $0); Z4 FloodCovIndicator Yes with no flood record; Z5 a blanket of one risk; Z6 blank zone;
                   Z7 floor / stories set (statistics only: B1's dollars); Z8 flood on a Builders Risk building; Z9 on
                   No Coverage (contents / BI Not Applicable); Z10 IncludedInBlkt blank everywhere
  C25-15 messages  M1 limits = full value (silent); M2a / M2b deductible 100,000 = TPV (fires) / TPV + 1 (silent); M3 excess
                   deductible 750,000 = building / contents value (fires), SC value + 1 (silent); M4 building primary,
                   contents excess; M5a detail without BldgCov; M5b BlanketIDNum with no detail; M6 BI With EE in a
                   Without-EE blanket; M7a / M7b blanket limit over the 100% total (ITV 128%) / equal; M8 blanket
                   deductible 500,000 >= the total; M9 a detail with no coverage; M10 a time-element blanket on a Standard
                   Property Policy; M11a / M11b inception dates differ / equal; M12 SC Frame vs SCBI Masonry
                   Non-Combustible; M13 / M13b Other Flood Insurance "Primary (NFIP)" without / with insurer; M14 CP 00 70
                   with a flood blanket
  C25-16 names     S1 submitted FloodBaseRate, record Deductible, FloodModificationFactor, FloodAdjustedRate, location CRS
                   factor, BusinessIncomeFactor, TypeOfRiskFactor, AnnualAggregateFactor (all IsNull-guarded: survive);
                   S2 submitted TotalPropertyValue, InsuranceToValuePercentageToUse, ExcessOverMaxNFIPIndicatorToUse
                   (unguarded: overwritten, B1's dollars); S3 a submitted BlanketAverageRate (survives)
  C25-17 cyber     X1 CP 10 75 (plain) and X2 CP 10 76 (ensuing causes: property Sublimit / aggregate, BI Full Limit) on
                   large flood premiums (factor 0.999 from the table moves dollars); X3 X2 with SCBI extra expense only
                   (the ...ToUse copies the extra-expense factor); X4 the blanket detail under CP 10 75

    python scripts/cf/231_chunk25_rc3.py [--live] [--cases Z1,M5a]
"""
from __future__ import annotations

import argparse
import collections
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

import gl_engine.interp.interpreter as interp                             # noqa: E402

c2 = import_module("230_chunk25_rc2")
x, t2 = c2.x, c2.t2
m, rc1, rep, cmp, gc, r11 = x.m, x.rc1, x.rep, x.cmp, c2.gc, c2.r11
P, D, val, d = x.P, Decimal, x.val, x.d
B, PP, SC, BI, SCBI, LOCR, BR, BRD = x.B, x.PP, x.SC, x.BI, x.SCBI, x.LOCR, x.BR, x.BRD
FAIL = []
r11.NUMERIC |= {"FloodBaseRate", "FloodModificationFactor", "FloodAdjustedRate", "CommunityRatingSystemFactor", "BusinessIncomeFactor",
                "TypeOfRiskFactor", "AnnualAggregateFactor", "TotalPropertyValue", "InsuranceToValuePercentageToUse", "BlanketAverageRate",
                "AnnualNetIncome", "NumberMortgages"}

c23 = import_module("221_chunk23_rc3")               # imported first: it wraps MessageHelper too
lvl, iso_tagged = c23.lvl, c23.iso_tagged
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged

L = {"B": P + B, "PP": P + PP, "SC": P + SC, "BI": P + BI, "SCBI": P + SCBI, "LOCR": P + LOCR, "BRD": P + BRD,
     "ST": P + "Structure", "LOC": P + "Location", "PPC": P + "PersonalProperty", "BIC": P + "BusinessIncome",
     "SCC": P + "SpecialClass", "POL": P}
GI, LIMB, LIMP, LIMS = ("Flood Coverage General Information needs to be attached", "Full Building Value", "Full Property Value",
                        "Full Special Class Item Value")
DEDT, DEDR, CANB, VALID = "exceed the Total Property Value", "exceed the respective value", "Cannot be Included In Blanket", "valid Flood Blanket ID"
NONE, COIN, TWO, LIMBLK = "None of the Blanket Covered Property", "cannot be greater than 12", "attached at 2 or more risks", "sum of the 100 Percent Values"
DEDBLK, ONECOV, POLONE, TESPP = "Flood Blanket Rating Deductible", "Select at least one Applicable", "at least one coverage for each Flood Blanket", "Time Element Flood Blankets"
OTHER, INCEP, ATLEAST, CONSTR = "Other Flood Insurance fields", "Location flood inception date", "needs to be attached to at least one risk", "Flood Construction types"
SAME, BRST, BRUNDER, UNDER, CP0070 = ("All instances of form CP 10 65", "CP 10 65 is not valid with selected Coverage",
                                      "not valid under a Building with Builders Risk", "needs an underlying coverage", "not valid with CP 00 70")
FRAGS = [GI, LIMB, LIMP, LIMS, DEDT, DEDR, CANB, VALID, NONE, COIN, TWO, LIMBLK, DEDBLK, ONECOV, POLONE, TESPP, OTHER, INCEP, ATLEAST,
         CONSTR, SAME, BRST, BRUNDER, UNDER, CP0070]


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ builders

def cp(sub):
    return sub[P + "Table"][P][0]


def loc(sub):
    return cp(sub)[P + "LocationTable"][P + "Location"][0]


def ft(*fns, **kw):
    def f():
        sub = x.flood_tree(**kw)
        for fn in fns:
            fn(sub)
        return sub
    return f


def det(unit, lim, **kw):
    out = {"UnitNumber": str(unit), "Limit": lim, "ExcessOverMaxNFIPIndicator": "No", "Deductible": "10,000", "BldgCov": "No",
           "PrsnlPropCov": "No", "SpecialClassCov": "No", "BusnIncomeWithExtraExpenseCov": "No", "BusnIncomeWithoutExtraExpenseCov": "No",
           "ExtraExpenseCov": "No"}
    out.update(kw)
    return out


def blanket(dets, ids):
    return lambda sub: x.add_blanket(sub, dets, ids)


def setcp(**kw):
    return lambda sub: cp(sub).update(kw)


def setloc(**kw):
    return lambda sub: loc(sub).update(kw)


def setlr(**kw):
    return lambda sub: loc(sub)[P + LOCR + "Table"][P + LOCR][0].update(kw)


def setpar(parent, **kw):
    def f(sub):
        m.at(sub)[P + parent].update(kw)
    return f


def setrec(rec, **kw):
    parent = {B: "Structure", PP: "PersonalProperty", SC: "SpecialClass", BI: "BusinessIncome", SCBI: "SpecialClassBusnIncome"}[rec]

    def f(sub):
        for row in m.at(sub)[P + parent][P + rec + "Table"][P + rec]:
            for k, v in kw.items():
                if v is None:
                    row.pop(k, None)
                else:
                    row[k] = v
    return f


def cyber(kind):
    def f(sub):
        if kind == "plain":
            cp(sub)[P + "CyberIncidentExclusionTable"] = {P + "CyberIncidentExclusion": [{}]}
        else:
            cp(sub)[P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptionsTable"] = {
                P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions": [{}]}
            cp(sub).update({"CyberTypeOfLimitPropertyDamage": "Sublimit", "CyberIsAggregateLimit": "Yes",
                            "CyberTypeOfLimitBusinessIncome": "Full Limit"})
    return f


def mort(sub):
    m.put(sub, m.MORT, {"Limit": "25,000", "NumberMortgages": "100"}, "OR")


BIG = dict(ded="100,000", full=("2000000", "1500000", "1000000"),
           recs={B: {"Limit": "1000000"}, PP: {"Limit": "1000000"}, SC: {"Limit": "800000"}, BI: {"Limit": "400000"}, SCBI: {"Limit": "400000"}})
K1 = [det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes")]
K3 = lambda lim: [det(1, lim, BldgCov="Yes", PrsnlPropCov="Yes", BusnIncomeWithExtraExpenseCov="Yes")]
K3R = {BI: {"AnnualNetIncome": "200000"}}
ALL5 = ("B", "PP", "SC", "BI", "SCBI")
PROP3 = ("B", "PP", "SC")
NOEXC = {k: {"ExcessOverMaxNFIPIndicator": "Yes"} for k in (B, PP, SC)}


def cases():
    """id: (task, label, build, zero records, predicted flood (level, fragment) list, submitted values, cyber check)"""
    c = {}

    def add(cid, task, label, build, zero=(), must=(), subv=None, cy=None):
        c[cid] = (task, label, build, set(zero), list(must), subv or {}, cy)

    # ---------------------------------------------------------------- C25-14 zero cases
    add("Z1", "C25-14", "deductible 500,000 >= TPV 400,000: table 6 files 0 at ITV >= 40, three TPV messages",
        ft(ded="500,000"), zero=(B, PP, SC), must=[(k, DEDT) for k in PROP3])
    add("Z2", "C25-14", "limits 1 over the full values: three limit messages, but ITV r4(150,001 / 150,000) = 1.0000 -> 100%, so each "
        "STILL PRICES at the 100% row (the message does not stop the premium)",
        ft(recs={B: {"Limit": "150001"}, PP: {"Limit": "120001"}, SC: {"Limit": "130001"}}),
        must=[("B", LIMB), ("PP", LIMP), ("SC", LIMS)])
    add("Z3", "C25-14", "FloodCovIndicator No with flood records: no location record, every record $0, five General Information messages",
        ft(setloc(FloodCovIndicator="No")), zero=(B, PP, SC, BI, SCBI), must=[(k, GI) for k in ALL5])
    add("Z4", "C25-14", "FloodCovIndicator Yes with no flood record: the Location message", ft(keep=()), must=[("LOC", ATLEAST)])
    add("Z5", "C25-14", "a flood blanket of one risk (the building)", ft(blanket([det(1, "150000", BldgCov="Yes")], {B: 1})),
        zero=(B,), must=[("BRD", TWO)])
    add("Z6", "C25-14", "blank flood zone: every base rate 0", ft(zone=""), zero=(B, PP, SC, BI, SCBI))
    add("Z7", "C25-14", "floor of interest Basement, 4 stories on every record: statistics only, B1's dollars",
        ft(*(setrec(r_, FloorLevel="Basement", NumberOfStories="4") for r_ in (B, PP, SC, BI, SCBI))))
    add("Z8", "C25-14", "flood on a Builders Risk building (class 1150): Structure, contents and BI messages",
        ft(st_over={"CovType": "Builders Risk", "ClassCode": "1150"}), must=[("ST", BRST), ("PPC", BRUNDER), ("BIC", BRUNDER)])
    add("Z9", "C25-14", "building No Coverage, contents and BI CovType Not Applicable: three 'underlying coverage' messages",
        ft(setpar("PersonalProperty", CovType="Not Applicable"), setpar("BusinessIncome", CovType="Not Applicable"),
           st_over={"CovType": "No Coverage"}),
        must=[("ST", UNDER), ("PPC", UNDER), ("BIC", UNDER)])
    add("Z10", "C25-14", "IncludedInBlkt blank on every flood record: every premium rule needs 'No'",
        ft(*(setrec(r_, IncludedInBlkt=None) for r_ in (B, PP, SC, BI, SCBI))), zero=(B, PP, SC, BI, SCBI))
    # ---------------------------------------------------------------- C25-15 messages
    add("M1", "C25-15", "limits equal to the full values: silent",
        ft(recs={B: {"Limit": "150000"}, PP: {"Limit": "120000"}, SC: {"Limit": "130000"}}))
    small = ("40000", "30000", "30000")
    slim = {B: {"Limit": "20000"}, PP: {"Limit": "15000"}, SC: {"Limit": "15000"}}
    add("M2a", "C25-15", "deductible 100,000 = TPV 100,000: three TPV messages", ft(ded="100,000", full=small, recs=slim),
        must=[(k, DEDT) for k in PROP3])
    add("M2b", "C25-15", "deductible 100,000, TPV 100,001: silent", ft(ded="100,000", full=("40000", "30000", "30001"), recs=slim))
    add("M3", "C25-15", "excess, deductible 750,000 = building 750,000 and >= contents 600,000 (fire); SC 750,001 (silent)",
        ft(ded="750,000", full=("750000", "600000", "750001"),
           recs={B: {"Limit": "375000", "ExcessOverMaxNFIPIndicator": "Yes"}, PP: {"Limit": "300000", "ExcessOverMaxNFIPIndicator": "Yes"},
                 SC: {"Limit": "375000", "ExcessOverMaxNFIPIndicator": "Yes"}}),
        must=[("B", DEDR), ("PP", DEDR)])
    add("M4", "C25-15", "building primary, contents excess under the same building", ft(recs={PP: {"ExcessOverMaxNFIPIndicator": "Yes"}}),
        zero=(PP,), must=[("ST", SAME)])
    add("M5a", "C25-15", "blanket detail without BldgCov, building in it: 'Cannot be Included' and 'valid ID'",
        ft(blanket([det(1, "200000", PrsnlPropCov="Yes")], {B: 1, PP: 1})), zero=(B, PP), must=[("B", CANB), ("B", VALID)])
    add("M5b", "C25-15", "contents BlanketIDNum 2 with only detail 1: 'valid ID' only; detail 1 has one member",
        ft(blanket([det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes")], {B: 1, PP: 2})), zero=(B, PP),
        must=[("PP", VALID), ("BRD", TWO), ("BRD", LIMBLK)])
    add("M3b", "C25-15", "excess, deductible 750,000 = the Special Class value 750,000 (fires); building 750,001 (silent)",
        ft(ded="750,000", full=("750001", "600000", "750000"),
           recs={B: {"Limit": "375000", "ExcessOverMaxNFIPIndicator": "Yes"}, PP: {"Limit": "300000", "ExcessOverMaxNFIPIndicator": "Yes"},
                 SC: {"Limit": "375000", "ExcessOverMaxNFIPIndicator": "Yes"}}),
        must=[("SC", DEDR), ("PP", DEDR)])
    add("M5c", "C25-15", "a building-only detail with contents and Special Class in it: each 'Cannot be Included' and 'valid ID'",
        ft(blanket([det(1, "150000", BldgCov="Yes")], {B: 1, PP: 1, SC: 1})), zero=(B, PP, SC),
        must=[("PP", CANB), ("PP", VALID), ("SC", CANB), ("SC", VALID)])
    add("M6b", "C25-15", "SCBI (With EE) in a building / contents blanket: 'Cannot be Included', 'None ... matches', 'valid ID'",
        ft(blanket([det(1, "270000", BldgCov="Yes", PrsnlPropCov="Yes")], {B: 1, PP: 1, SCBI: 1}), recs={SCBI: {"AnnualNetIncome": "200000"}}),
        zero=(B, PP, SCBI), must=[("SCBI", CANB), ("SCBI", NONE), ("SCBI", VALID)])
    add("M6c", "C25-15", "BI (With EE) in a building / contents blanket: 'Cannot be Included', 'None ... matches', 'valid ID'",
        ft(blanket([det(1, "270000", BldgCov="Yes", PrsnlPropCov="Yes")], {B: 1, PP: 1, BI: 1}), recs=K3R),
        zero=(B, PP, BI), must=[("BI", CANB), ("BI", NONE), ("BI", VALID)])
    add("M7c", "C25-15", "SCBI in a With-EE blanket, limit 600,001 > the 470,000 total: detail and SCBI coinsurance messages",
        ft(blanket(K3("600001"), {B: 1, PP: 1, SCBI: 1}), recs={SCBI: {"AnnualNetIncome": "200000"}}), zero=(B, PP, SCBI),
        must=[("BRD", LIMBLK), ("SCBI", COIN)])
    add("M6", "C25-15", "BI With Extra Expense in a Without-EE blanket: 'None ... matches' and 'valid ID'",
        ft(blanket([det(1, "400000", BldgCov="Yes", PrsnlPropCov="Yes", BusnIncomeWithoutExtraExpenseCov="Yes")], {B: 1, PP: 1, BI: 1}),
           recs=K3R), zero=(B, PP, BI), must=[("BI", NONE), ("BI", VALID), ("BRD", LIMBLK), ("BI", COIN)])
    add("M7a", "C25-15", "blanket limit 600,001 > the 100% total 470,000 (ITV 128%): detail and BI coinsurance messages",
        ft(blanket(K3("600001"), {B: 1, PP: 1, BI: 1}), recs=K3R), zero=(B, PP, BI), must=[("BRD", LIMBLK), ("BI", COIN)])
    add("M7b", "C25-15", "blanket limit 470,000 = the total: silent", ft(blanket(K3("470000"), {B: 1, PP: 1, BI: 1}), recs=K3R), zero=(B, PP, BI))
    add("M8", "C25-15", "blanket deductible 500,000 >= the total 270,000; the CONTENTS member takes the detail's deductible (table 6, "
        "factor 0 at ITV 74%) while the building keeps the location's 10,000: the blanket average falls ($520, not K1's $1,273)",
        ft(blanket([det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes", Deductible="500,000")], {B: 1, PP: 1})), zero=(B, PP),
        must=[("BRD", DEDBLK)])
    add("M9", "C25-15", "a blanket detail with no coverage and no member: detail, policy and 'two risks' messages",
        ft(blanket([det(1, "100000")], {})), must=[("BRD", ONECOV), ("POL", POLONE), ("BRD", TWO), ("BRD", LIMBLK), ("BRD", DEDBLK)])
    add("M10", "C25-15", "a time-element flood blanket on a Standard Property Policy",
        ft(setcp(PolicyType="Standard Property Policy"), blanket(K3("400000"), {B: 1, PP: 1, BI: 1}), recs=K3R), zero=(B, PP, BI),
        must=[("POL", TESPP)])
    add("M11a", "C25-15", "location flood date 01/01/2027, blanket detail 02/01/2027: inception message",
        ft(setlr(FloodEffDate="01/01/2027"), blanket([det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes", FloodEffDate="02/01/2027")], {B: 1, PP: 1})),
        zero=(B, PP), must=[("LOCR", INCEP)])
    add("M11b", "C25-15", "the same dates: silent",
        ft(setlr(FloodEffDate="01/01/2027"), blanket([det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes", FloodEffDate="01/01/2027")], {B: 1, PP: 1})),
        zero=(B, PP))
    add("M12", "C25-15", "SC flood Frame, SCBI flood Masonry Non-Combustible", ft(recs={SCBI: {"ConstructionType": "Masonry Non-Combustible"}}),
        must=[("SCC", CONSTR)])
    add("M13", "C25-15", "Other Flood Insurance 'Primary (NFIP)' with no insurer: ancestor::MasterCFCW/Policy reads as the document "
        "root (the engine's ancestor rule, the same reading that writes ISO's stat codes), so it fires in a state too",
        ft(setlr(OtherFloodInsurance="Primary (NFIP)")), must=[("LOCR", OTHER)])
    add("M13b", "C25-15", "the same with insurer and policy number entered: silent",
        ft(setlr(OtherFloodInsurance="Primary (NFIP)", OtherFloodInsuranceInsurer="NFIP Direct", OtherFloodInsurancePolNum="FL-123")))
    add("M14", "C25-15", "CP 00 70 with a flood blanket", ft(mort, blanket(K1, {B: 1, PP: 1})), zero=(B, PP), must=[("POL", CP0070)])
    # ---------------------------------------------------------------- C25-16 shared names
    add("S1", "C25-16", "submitted guarded values: building base 1.0 and Deductible 500, contents modification 0.5, SC adjusted 0.3, "
        "CRS factor 0.9, BI factor 1.0, SCBI type-of-risk 0.8, contents aggregate 0.9",
        ft(setlr(CommunityRatingSystemFactor="0.9"),
           recs={B: {"FloodBaseRate": "1.0", "Deductible": "500"}, PP: {"FloodModificationFactor": "0.5", "AnnualAggregateFactor": "0.9"},
                 SC: {"FloodAdjustedRate": "0.3"}, BI: {"BusinessIncomeFactor": "1.0"}, SCBI: {"TypeOfRiskFactor": "0.8"}}),
        subv={(B, "FloodBaseRate"): D("1.0"), (B, "Deductible"): "500", (PP, "FloodModificationFactor"): D("0.5"),
              (PP, "AnnualAggregateFactor"): D("0.9"), (SC, "FloodAdjustedRate"): D("0.3"), (LOCR, "CommunityRatingSystemFactor"): D("0.9"),
              (BI, "BusinessIncomeFactor"): D("1.0"), (SCBI, "TypeOfRiskFactor"): D("0.8")})
    add("S2", "C25-16", "submitted unguarded values: TotalPropertyValue 1,000,000, ITV% to use 10, excess-to-use Yes (overwritten: B1)",
        ft(recs={B: {"TotalPropertyValue": "1000000", "InsuranceToValuePercentageToUse": "10", "ExcessOverMaxNFIPIndicatorToUse": "Yes"}}))
    add("S3", "C25-16", "a submitted BlanketAverageRate 1.0 on the blanket detail",
        ft(blanket([det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes", BlanketAverageRate="1.0")], {B: 1, PP: 1})), zero=(B, PP),
        subv={(BRD, "BlanketAverageRate"): D("1.0")})
    # ---------------------------------------------------------------- C25-17 exclusions
    add("X1", "C25-17", "CP 10 75 on large flood premiums (0.999)", ft(cyber("plain"), **BIG), cy="plain")
    add("X2", "C25-17", "CP 10 76 (property Sublimit, aggregate; BI Full Limit) on large flood premiums", ft(cyber("ensuing"), **BIG), cy="ensuing")
    add("X3", "C25-17", "X2 with SCBI extra expense only (the ...ToUse copies the extra-expense flood factor)",
        ft(cyber("ensuing"), setpar("SpecialClassBusnIncome", CovType="Extra Expense Only", Coinsurance="No Coinsurance",
                                    ExtraExpenseLimitOnLossPayment="40%,80%,100%"), **BIG), cy="ensuing")
    add("X4", "C25-17", "the blanket detail under CP 10 75 (K2's three risks at 1,000,000)",
        ft(cyber("plain"), blanket([det(1, "1000000", BldgCov="Yes", PrsnlPropCov="Yes", SpecialClassCov="Yes")], {B: 1, PP: 1, SC: 1}),
           full=("2000000", "1500000", "1000000")), zero=(B, PP, SC), cy="plain")
    return c


CASES = cases()


# ------------------------------------------------------------------ checks

def flood_msgs(tagged):
    out = collections.Counter()
    for t, y in tagged:
        for f in FRAGS:
            if f in y:
                out[(t, f)] += 1
    return out


def cyber_check(data, kind):
    """the policy's flood cyber factors from the table (CyberIncidentExclusionFactors / ...WithEnsuingCauseOf...)."""
    cpn = rc1.find(data, P)[0] if data.tag != P else data
    cpn = m.root(rc1.find(data, P + "Location")[0])
    if kind == "plain":
        want = {"CyberIncidentExclusionFactorFlood": x.one("OR", "CyberIncidentExclusionFactors", "Factor", CausesOfLossOrPerilGroupPremium="Flood"),
                "CyberIncidentExclusionCOLExcptnsFactorFlood": D(1)}
    else:
        f = lambda lim: x.one("OR", "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors", "Factor", CausesOfLossOrPerilGroupPremium="Flood",
                              TypeOfLimit=lim, AggregateLimit="Yes")
        want = {"CyberIncidentExclusionFactorFlood": D(1), "CyberIncidentExclusionCOLExcptnsFactorFlood": f("Sublimit"),
                "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFlood": f("Full Limit")}
    got = {k: val(cpn, k) for k in want}
    bad = [k for k, v in want.items() if not m.same(v, got[k])]
    for n in rc1.find(data, P + "BusinessIncome") + rc1.find(data, P + "SpecialClassBusnIncome"):
        src = "CyberIncidentExclusionCOLExcptnsFactorExtraExpenseFlood" if val(n, "CovType") == "Extra Expense Only" else "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFlood"
        if not m.same(val(n, "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse"), val(cpn, src) or "1"):
            bad.append(f"{n.tag[len(P):]} ...BusnIncomeFloodToUse {val(n, 'CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse')} != {src}")
    return f"cyber factors by table {dict((k, str(v)) for k, v in want.items())} engine {got}", bad


def request(build):
    return t2.state_req(t2.m20.payload(build()), "OR")


def predict(cid, case):
    task, label, build, zero, must, subv, cy = case
    req = request(build)
    x.SUB.clear()
    x.SUB.update(subv)
    TAGGED.clear()
    data, ip = cmp.rate(req)
    tagged = [(lvl(t), y) for t, y in TAGGED]
    lines, bad, preds = [], [], {}
    for rec in x.PREMIUM_RECS:
        preds[rec] = []
        for node, hv, ev, e in x.predict(data, rec):
            pr = {}
            x.hand("OR", node, rec, pr)
            diff = x.parts_agree(rec, node, pr)
            ok = m.same(hv, e) and (ev is None or m.same(ev, e)) and not diff
            if rec in zero and not m.same(e, 0):
                ok = False
            preds[rec].append(hv)
            name = rec[len(x.FL):] or "Building"
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {name[:28]:28s} predicted {hv}  engine {e}  {x.show(pr)[:150]}")
            if not ok:
                bad.append(f"{name} hand {hv} evaluator {ev} engine {e} {diff}")
    x.SUB.clear()
    if cy:
        line, cb = cyber_check(data, cy)
        lines.append("      " + line)
        bad += cb
    want = collections.Counter((L[a], f) for a, f in must)
    got = flood_msgs(tagged)
    mbad = [f"{t.replace(P, '') or 'policy'}: {f} fired {got[(t, f)]}, predicted {want[(t, f)]}" for t, f in set(want) | set(got) if want[(t, f)] != got[(t, f)]]
    print(f"{cid:5s} {task} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS ' + '; '.join((bad + mbad)[:4])}")
    print(f"      flood messages predicted {sorted((t.replace(P, '') or 'policy', f) for t, f in want.elements())}")
    print("\n".join(lines))
    if bad or mbad:
        FAIL.append(cid)
    return req, data, preds


def live(client, raas_mod, cid, case, req, data, preds):
    task, label, build, zero, must, subv, cy = case
    (gc.OUT / f"chunk25_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:5s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk25_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    TAGGED.clear()
    x.SUB.update(subv)
    data, ip = cmp.rate(req)
    x.SUB.clear()
    ours = collections.Counter((lvl(t), y) for t, y in TAGGED)
    isos = collections.Counter(iso_tagged(resp))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if v is not None and not m.same(v, 0))
        w = sorted(D(str(v)) for v in want if not isinstance(v, str) and not m.same(v, 0))
        if iso != w:
            pbad.append((rec, iso, w))
    want = collections.Counter((L[a], f) for a, f in must)
    isof = flood_msgs(list(isos.elements()))
    mreq = [f"{t.replace(P, '') or 'policy'}: {f} ISO {isof[(t, f)]}, predicted {want[(t, f)]}" for t, f in set(want) | set(isof) if want[(t, f)] != isof[(t, f)]]
    ok = not pbad and not dd and ours == isos and not mreq
    print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: flood records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
          + (f"; against the prediction: {mreq}" if mreq else "")
          + "".join(f"\n        predicted {rr[-45:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + "".join(f"\n        ISO only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (isos - ours).items())
          + "".join(f"\n        ours only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (ours - isos).items()))
    if not ok:
        FAIL.append(f"{cid} live")


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
            got[cid] = predict(cid, CASES[cid])
        except Exception as exc:
            print(f"{cid}: engine RAISED {type(exc).__name__}: {str(exc)[:200]}")
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (flood records as predicted, every premium field for field, every (level, message)):")
        for i, cid in enumerate(cs, 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                live(client, raas_mod, cid, CASES[cid], *got[cid])
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C25-14..C25-17): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
