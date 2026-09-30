#!/usr/bin/env python3
"""Chunk 20, RC-3 (C20-15, C20-16): zero cases and messages, every message tied to the level that raised it.

Every case is RC-2's Oregon policy (200_) or a state's portable policy (192_) with one thing changed. Each
chunk 20 record's premium is predicted before the run: an explicit $0 where a rule forces it, otherwise the
hand evaluation of the filed rule on the tree. Each case names the messages that must appear and must not,
as (level, text) pairs: the level is the table that raised it (MessageHelper's TableName argument on our
side, captured by this script only; on ISO's side the node carrying the message's ErcMessageTableId), so
the same text raised at five levels is five separate checks. --live compares every premium and the whole
(level, message) multiset.

C20-15  ZERO CASES (read from the rules, 2026-09-29)
  Z1  Fire Department at the base limit (1,000)          -> $0 ((1,000 - 1,000) / 100)
  Z2  Fire Department, limit blank                       -> $3, ISO $3 (OI-115, fixed 2026-09-30: ISO skips a blank first operand
      of Subtract: (blank - 1,000) = 1,000). Z2b the same with Factor 2.0: $17 at ISO and ours (blank-as-zero would be -$17)
  Z3  Tobacco, the contents on the ordinary form         -> switched off, $0
  Z4  Mortgageholders, 0 mortgages                       -> every layer 0, $0
  Z5  EB BI records with NO building EB record           -> occupancy group 0 -> loss cost 0 -> $0
  Z6  special-limit items at or under their base (furs 2,500, jewelry "> $100" 2,000, patterns 1,000,
      stamps 250)                                        -> $0 each (only the limit ABOVE the base prices)
  Z7  Fungus, Policy Limit, sub-limit exactly 15,000, BI indicator off -> $0
  Z8  EB ammonia exactly 25,000                          -> switched off (> 25,000 only), $0
  Z9  Pier and Wharf, construction blank                 -> rate 0.0, $0 (4 records)
  Z10 ACP on the Broad cause                             -> $0 (Special only)
  Z11 Food, both limits 0                                -> $0
C20-16  MESSAGES (95 rule instances: 77 CW, the rest NC VA NY CT AK IL)
  Radioactive (27)    MR1 unblanketed, own limits, TypeOfCov Limited on Special -> "Limit not required" and
                          "Limited option not valid", 5 levels each
                      MR2 blanket (all five levels), detail No, limits 0 -> "Limit required" x5
                      MR3 blanket, detail Yes, rates 0 -> "Missing required rate" x5
                      MR4 blanket, detail Yes, no radioactive records -> "needs to be attached" x5
                      MR5 the building CovType "No Coverage" -> "requires some type of building coverage"
                      MR6 the building deductible "Not Applicable" -> "Deductible cannot be Not Applicable"
  Pier (8)            MP1 pier on four levels, Special, no ACP -> "CP 10 70 not valid" x4, "CP 14 10 is
                          required with CP 10 70" x2; MP2 Broad with ACP -> all silent
  Fire Department (3) MF1 the location's higher-limits indicator Yes, the charge not selected; MF2 higher
                          limit 10,000 under the own 25,000 (message; LimitToUse 10,000, a LOWER premium);
                          MF3 no building / occupancy coverage form (Legal Liability) -> the form message
  Special limits (15) MS1 the contents' theft exclusion (CP 10 33) x4; MS2 contents blanketed on Broad x4;
                      MS3 higher-limits indicators on Broad x4; MS4 higher limits not above the record's x4
  ACP (22)            MA1 watercraft exclusion, no ACP (building, special class); MA2 watercraft + an ACP
                          detail of another type -> "Valid Type" x2; MA3 Builders Risk building with ACP;
                          MA4 contents ACP on the Legal Liability form; NC1-NC3 and VA1-VA3 the state versions
  Mortgageholders (17) MM1-MM8 CW (a NUMBERED location (UnitNumber > 0), TRIP, missing location, SPP, blanket, CP 10 76, cyber pair,
                          TRIP No); NY1-NY4 the CP 10 77 / 78 versions and NY's fire-department form rule; KS1 / VT1 their copies of it; IL1 mine subsidence; CT1; AK1
  Fungus (5)          MU1 Policy Limit with no fungus record; MU2 / MU3 the separate-premises pair; MU4 / MU5
                          the BI period pair, set on the POLICY record (it overwrites BI's own field)
  EB (2)              ME1 EB on Broad; ME2 CP 10 47 without CP 10 46

    python scripts/cf/201_chunk20_rc3.py [--live] [--cases Z1,MR1]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
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

import gl_engine.interp.interpreter as interp                             # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

m = import_module("200_chunk20_rc2")
g19 = m.g19
gc, rc1, rep, cmp, r16, r11, r2 = m.gc, m.rc1, m.rep, m.cmp, m.r16, m.r11, m.r2
P, put, at, same = m.P, m.put, m.at, m.same
# the contents' higher-limits record: every item limit is xs:int (MS3 / MS4's first live run: ISO refused the strings)
r11.NUMERIC |= {"Factor", "SpecialCOLPatternsDiesMoldsAndFormsLimit", "SpecialCOLStampsTicketsAndLettersOfCreditLimit",
                "SpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetalLimit"}
FAIL = []
ZERO = "zero"
LEVELS = ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome")
RADIO_AT = dict(zip(LEVELS, ["RadioactiveContamination", "RadioactiveContaminationPrsnlProp", "RadioactiveContaminationBusnIncome",
                             "RadioactiveContaminationSpecialClass", "RadioactiveContaminationSpclClassBusnIncome"]))

# ---------------------------------------------------------------- the level each message was raised at (test-side capture)
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ---------------------------------------------------------------- policies

def base(cause="Special", j="OR"):
    return m.base(cause) if j == "OR" else g19.with_cause(g19.portable(j), cause)


def cp_of(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


def blanket_all(flag, cause="Special"):
    """the Oregon policy with all five coverages blanketed: building + contents + special class in one
    "Building & Personal Property Combined" blanket, BI + SCBI in a "Business Income With Extra Expense" one."""
    sub = base(cause)
    cp = cp_of(sub)
    cp["BlktRated"], cp["MUBlktRated"] = "Yes", "No"
    det = lambda unit, typ, lim: {"UnitNumber": unit, "Type": typ, "TypeOfBlanketRating": "Average", "CauseOfLoss": cause,
                                  "Coinsurance": "90%", "TotalLimit": lim, "RadioactiveContamination": flag}
    cp["CommercialPropertyBlanketRatingTable"] = {"CommercialPropertyBlanketRating": [{"CommercialPropertyBlanketRatingDetailTable": {
        "CommercialPropertyBlanketRatingDetail": [det("100", "Building & Personal Property Combined", "300000"),
                                                  det("200", "Business Income With Extra Expense", "200000")]}}]}
    for k, u in (("Structure", "100"), ("PersonalProperty", "100"), ("SpecialClass", "100"),
                 ("BusinessIncome", "200"), ("SpecialClassBusnIncome", "200")):
        at(sub)[P + k].update({"IncludedInBlkt": "Yes", "BlktIDNum": u})
    return sub


def with_(build, fn):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


def radios(sub, **fields):
    for r in m.RADIO:
        put(sub, r, dict(fields))


# ---------------------------------------------------------------- zero cases

def z_fire(limit, factor=None):
    def b():
        sub = base()
        f = {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes"}
        if limit:
            f["Limit"] = limit
        if factor:
            f["Factor"] = factor
        put(sub, "LocationFireDepartmentCharge", f)
        return sub
    return b


def z_special_col(sub):
    put(sub, m.FURS, {"Indicator": "Yes", "Limit": "2500"})
    put(sub, m.JEWEL, {"Indicator": "Yes", "Limit": "2000", "ValueIndicator": "Worth more than $100 per item"})
    put(sub, m.PATT, {"Indicator": "Yes", "Limit": "1000"})
    put(sub, m.STAMPS, {"Indicator": "Yes", "Limit": "250"})


def z_fungus(sub):
    cp_of(sub)["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
    put(sub, m.FUNGUS, {"SubLimit": "15000", "IncreasedPeriodOfRestoration": "Not Applicable"})


def z_eb_bi_only(sub):
    put(sub, m.EBI + "Coverage")


# ---------------------------------------------------------------- message cases

def higher_fire(ind_on_charge, hl_limit):
    def b():
        sub = base()
        put(sub, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": ind_on_charge, "Limit": "25000"})
        at(sub)[P + "Location"][P + "HigherLimitsLocationTable"] = {P + "HigherLimitsLocation": [
            {"FireDepartmentChargeIndicator": "Yes", "FireDepartmentChargeLimit": hl_limit}]}
        return sub
    return b


def legal_liability(sub):
    at(sub)[P + "Structure"]["CovType"] = "Legal Liability"
    at(sub)[P + "OccupClass"]["CovForm"] = "Legal Liability Coverage Form"


def spcol_all(sub, ind="Yes"):
    for r, lim in ((m.FURS, "20000"), (m.PATT, "20000"), (m.STAMPS, "5000")):
        put(sub, r, {"Indicator": ind, "Limit": lim})
    put(sub, m.JEWEL, {"Indicator": ind, "Limit": "10000", "ValueIndicator": "Worth more than $100 per item"})


HL_FIELDS = {"Furs": "SpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFur",
             "Jewel": "SpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetal",
             "Patterns": "SpecialCOLPatternsDiesMoldsAndForms", "Stamps": "SpecialCOLStampsTicketsAndLettersOfCredit"}


def higher_pp(limit):
    return {P + "HigherLimitsPersonalProperty": [{**{v + "Indicator": "Yes" for v in HL_FIELDS.values()},
                                                  **{v + "Limit": limit for v in HL_FIELDS.values()}}]}


def watercraft(sub, acp_type=None, state=None):
    for lvl in ("Structure", "SpecialClass"):
        suffix = "" if lvl == "Structure" else "SpecialClass"
        at(sub)[P + lvl][P + "WatercraftExclusion" + suffix + "Table"] = {P + "WatercraftExclusion" + suffix: [{}]}
    if acp_type:
        acp = {"Type": acp_type, "WatercraftExclBuybackConstrctnOption": m.PIER1, "Limit": "30000"}
        put(sub, "AdditionalCoveredPropertyDetail", acp)
        put(sub, "AdditionalCoveredPropertySpecialClassDetail", acp)


def nc_acp(sub, desc, levels=("Bldg", "SpecialClass")):
    for lv in levels:
        parent = {"Bldg": "Structure", "SpecialClass": "SpecialClass", "PrsnlProp": "PersonalProperty"}[lv]
        rec = "NorthCarolinaChangesAdditionalCoveredProperty" + lv
        at(sub)[P + parent][P + rec + "Table"] = {P + rec: [{P + rec + "DetailTable": {P + rec + "Detail": [
            {"Description": desc, "Limit": "30000"}]}}]}


def mortgage_only(extra=None, terror=None, spp=False, blanket=False, j="OR"):
    def b():
        sub = base(j=j)
        cp = cp_of(sub)
        cp.pop("CommercialPropertyLocationTable", None)
        put(sub, m.MORT, {"Limit": "25,000", "NumberMortgages": "500"})
        if terror:
            cp["TerrorismIndicator"] = terror
        if spp:
            cp["PolicyType"] = "Standard Property Policy"
        if blanket:
            cp["BlktRated"] = "Yes"
        for k, v in (extra or {}).items():
            cp[k] = v
        return sub
    return b


def no_mortgage(extra=None, terror=None, j="OR", no_location=False):
    def b():
        sub = base(j=j)
        cp = cp_of(sub)
        if no_location:
            cp.pop("CommercialPropertyLocationTable", None)
        if terror:
            cp["TerrorismIndicator"] = terror
        for k, v in (extra or {}).items():
            cp[k] = v
        return sub
    return b


CYBER = {P + "CyberIncidentExclusionTable": {P + "CyberIncidentExclusion": [{}]}}
CYBER_ENS = {P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptionsTable": {P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions": [{}]}}


def fungus_msg(cov, sep_opt=None, with_record=True):
    def b():
        sub = base()
        cp_of(sub)["FungusWetRotDryRotBacteriaCov"] = cov
        if with_record:
            f = {"SubLimit": "50000"}
            if sep_opt:
                f["SeparatePremisesOrLocationsOption"] = sep_opt
            put(sub, m.FUNGUS, f)
        return sub
    return b


def bi_period(period, indicator):
    """BI's own period field is OVERWRITTEN from the policy fungus record's IncreasedPeriodOfRestoration
    (SetFungusWetRotDryRotBacteriaIncrdPeriodRestoration: copied when the record exists and is not "Not
    Applicable", else "Not Applicable"), so the period is set on the policy record."""
    def b():
        sub = base()
        cp_of(sub)["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
        put(sub, m.FUNGUS, {"SubLimit": "50000", "IncreasedPeriodOfRestoration": period})
        at(sub)[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = indicator
        return sub
    return b


def unit(build):
    """the location numbered (UnitNumber 1): the CP 00 70 location message tests UnitNumber > 0."""
    return with_(build, lambda s: at(s)[P + "Location"].update({"UnitNumber": "1"}))


# ---------------------------------------------------------------- message texts (fragments)

T = {"notreq": "CP 10 37 Limit not required", "req": "CP 10 37 Limit required", "limited": "CP 10 37 Limited option",
     "rate": "Missing required", "attach": "Radioactive Contamination form CP 10 37 needs to be attached",
     "bldgcov": "CP 10 37 requires some type of building coverage", "dedna": "Deductible cannot be Not Applicable for the Endorsement",
     "1070col": "CP 10 70 not valid with", "1410w1070": "CP 14 10 is required with CP 10 70",
     "fdhl": "Higher Limit for Fire Department Service Charge cannot be increased", "fdinc": "Fire Department Charge Limit entered is not increasing",
     "fdform": "When Fire Department Charge is Selected at least one of these forms",
     "1033": "is invalid with CP 10 33", "blktcol": "is invalid with the Blanket Cause of Loss selected",
     "hlspecial": "cannot be increased without the selection of Special Cause Of Loss", "revised": "is not increasing the specified amount",
     "1410w1035": "CP 14 10 is required with CP 10 35", "type1410": "Valid Type required for CP 14 10",
     "1410nv": "CP 14 10 not valid with selected Coverage",
     "1411w1035": "CP 14 11 is required with CP 10 35", "type1411": "Valid Type required for CP 14 11", "1411nv": "CP 14 11 not valid with selected Coverage",
     "1412w1035": "CP 14 12 is required with CP 10 35", "1412w1070": "CP 14 12 is required with CP 10 70",
     "type1412": "Valid Type required for CP 14 12", "1412nv": "CP 14 12 not valid with selected Coverage",
     "locnv": "Location and subsequent levels are not valid with CP 00 70", "trip": "CP 00 70 is not valid with Terrorism",
     "missloc": "Missing required Location record", "spp": "CP 00 70 is not valid with the Standard Property Policy",
     "blkt": "Blanket Rating is not valid with CP 00 70", "1076": "CP 00 70 is not valid with CP 10 76",
     "both": "CP 10 75 And CP 10 76 cannot be both", "either": "Either CP 10 75 Or CP 10 76 must be attached",
     "only": "CP 10 75 should be attached", "tripyes": "Terrorism Risk Insurance Program Applies Must Be Yes",
     "1078": "CP 00 70 is not valid with CP 10 78", "both77": "CP 10 77 And CP 10 78 cannot be both",
     "either77": "Either CP 10 77 Or CP 10 78", "only77": "CP 10 77 should be attached",
     "mine": "Mine Subsidence not valid with CP 00 70", "ct": "CP 04 61 not valid without CP 00 70",
     "ak": "Attorney Fee Limit must be greater than CP 00 70", "0431": "CP 04 31 Must Be Attached",
     "sepyes": "needs to be Yes when Fungus Coverage is Separate Limits", "seponly": "only applicable if Fungus Coverage is Separate Limits",
     "bina": "When Fungus Wet Rot Dry Rot Bacteria Incrd Period Restoration Is Not Applicable", "bimust": "When CP 04 31 BI/Extra Expense",
     "1046": "CP 10 46 does not apply", "1047": "then CP 10 47 form cannot be attached"}
L = {"S": P + "Structure", "C": P + "PersonalProperty", "B": P + "BusinessIncome", "K": P + "SpecialClass",
     "KB": P + "SpecialClassBusnIncome", "L": P + "Location", "H": P + "HigherLimitsLocation",
     "HP": P + "HigherLimitsPersonalProperty", "CP": P.rstrip("y") + "y", "F": P + "ChangesFungusWetRotDryRotBacteria",
     "AK": P + "ChangesAttorneysFees"}
L["CP"] = "CommercialProperty"
ALL5 = ("S", "C", "B", "K", "KB")


def at5(key):
    return [(lv, T[key]) for lv in ALL5]


def cases():
    """id -> (task, state, label, build, {record: ZERO | None}, must [(level, text)], must-not [(level, text)])."""
    hand = lambda recs: {r: None for r in recs}
    zc = lambda recs: {r: ZERO for r in recs}
    SPC = [m.FURS, m.JEWEL, m.PATT, m.STAMPS]
    return {
        # ---------------------------------------------------------- C20-15
        "Z1": ("C20-15", "OR", "Fire Department at the base limit 1,000", z_fire("1000"), zc(["LocationFireDepartmentCharge"]), [], [("L", T["fdform"])]),
        "Z2": ("C20-15", "OR", "Fire Department, limit blank (OI-115, fixed: blank - 1,000 = 1,000)", z_fire(None), {"LocationFireDepartmentCharge": Decimal(3)}, [], []),
        "Z2b": ("C20-15", "OR", "Fire Department, limit blank, Factor 2.0 submitted (the OI-115 probe)", z_fire(None, "2.0"),
                {"LocationFireDepartmentCharge": Decimal(17)}, [], []),
        "Z3": ("C20-15", "OR", "Tobacco on the ordinary contents form",
               with_(base, lambda s: put(s, "PersonalPropertyTobaccoSalesWarehousesCoverage")), zc(["PersonalPropertyTobaccoSalesWarehousesCoverage"]), [], []),
        "Z4": ("C20-15", "OR", "Mortgageholders, 0 mortgages (location numbered 1)", unit(m.mortgage(0, "25,000")), zc([m.MORT]), [("L", T["locnv"])], []),
        "Z5": ("C20-15", "OR", "EB BI record without the building's EB", with_(base, z_eb_bi_only), zc([m.EBI + "Coverage"]), [], []),
        "Z6": ("C20-15", "OR", "furs 2,500 / jewelry (> $100) 2,000 / patterns 1,000 / stamps 250: at or under the base",
               with_(base, z_special_col), zc(SPC), [], []),
        "Z7": ("C20-15", "OR", "Fungus Policy Limit, sub-limit 15,000, BI indicator off", with_(base, z_fungus), zc([m.FUNGUS]), [], [("CP", T["0431"])]),
        "Z8": ("C20-15", "OR", "EB ammonia exactly 25,000 (switch is > 25,000)",
               with_(base, lambda s: put(s, m.EBB + "AmmoniaContaminationCov", {"AmmoniaContamination": "25000"},
                                        inter={m.EBB: {"OccupancyCategory": "Institutional", "OccupancyGroup": "All other institutional risks"}})),
               {m.EBB + "AmmoniaContaminationCov": ZERO}, [], []),
        "Z9": ("C20-15", "OR", "Pier and Wharf, construction blank (Broad, with ACP)",
               with_(lambda: base("Broad"), lambda s: ([put(s, r, {"Limit": "40000"}) for r in m.PIER],
                                                      put(s, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "Limit": "30000"}),
                                                      put(s, "AdditionalCoveredPropertySpecialClassDetail", {"Type": m.BULK, "Limit": "30000"}))),
               zc(m.PIER), [], [("S", T["1070col"])]),
        "Z10": ("C20-15", "OR", "ACP on the Broad cause", with_(lambda: base("Broad"), lambda s: [
                put(s, r, {"Type": m.BULK, "WatercraftExclBuybackConstrctnOption": m.PIER1, "Limit": "30000"}) for r in m.ACP]),
                zc(m.ACP), [], []),
        "Z11": ("C20-15", "OR", "Food Contamination, both limits 0", with_(base, lambda s: [
                put(s, r, {"FoodLimit": "0"} if "FoodOnly" in r else {"AdvertisingLimit": "0"}) for r in m.FOOD]), zc(m.FOOD), [], []),
        # ---------------------------------------------------------- C20-16 radioactive
        "MR1": ("C20-16", "OR", "radioactive unblanketed, own limits, TypeOfCov Limited on Special",
                with_(base, lambda s: radios(s, Limit="40000", Rate="0.100", TypeOfCov="Limited")), hand(m.RADIO),
                at5("notreq") + at5("limited"), at5("req") + at5("rate")),
        "MR1s": ("C20-16", "OR", "radioactive unblanketed, no own limit, Broad, TypeOfCov Limited (silent)",
                 with_(lambda: base("Broad"), lambda s: radios(s, Rate="0.100", TypeOfCov="Limited")), hand(m.RADIO),
                 [], at5("limited")),
        "MR2": ("C20-16", "OR", "blanket (five levels), detail No, radioactive limits 0",
                with_(lambda: blanket_all("No"), lambda s: radios(s, Limit="0", Rate="0.100")), hand(m.RADIO), at5("req"), at5("notreq")),
        "MR3": ("C20-16", "OR", "blanket, detail Yes, radioactive rates 0",
                with_(lambda: blanket_all("Yes"), lambda s: radios(s, Rate="0.0")), hand(m.RADIO), at5("rate"), at5("attach")),
        "MR4": ("C20-16", "OR", "blanket, detail Yes, no radioactive records", lambda: blanket_all("Yes"), {}, at5("attach"), []),
        "MR5": ("C20-16", "OR", "the building CovType No Coverage with radioactive",
                with_(base, lambda s: (at(s)[P + "Structure"].update({"CovType": "No Coverage"}), put(s, "RadioactiveContamination", {"Rate": "0.100"}))),
                {}, [("S", T["bldgcov"])], []),
        "MR6": ("C20-16", "OR", "the building deductible Not Applicable with radioactive",
                with_(base, lambda s: (at(s)[P + "Structure"].update({"Deductible": "Not Applicable"}), put(s, "RadioactiveContamination", {"Rate": "0.100"}))),
                {}, [("S", T["dedna"])], []),
        # pier
        "MP1": ("C20-16", "OR", "pier on four levels, Special, no ACP",
                with_(base, lambda s: [put(s, r, {"Construction": m.PIER1, "Limit": "40000"}) for r in m.PIER]), hand(m.PIER),
                [(lv, T["1070col"]) for lv in ("S", "B", "K", "KB")] + [("S", T["1410w1070"]), ("K", T["1410w1070"])], []),
        "MP2": ("C20-16", "OR", "pier on four levels, Broad, with ACP (silent)",
                with_(lambda: base("Broad"), lambda s: ([put(s, r, {"Construction": m.PIER1, "Limit": "40000"}) for r in m.PIER],
                                                       [put(s, r, {"Type": m.BULK, "Limit": "30000"}) for r in m.ACP])),
                hand(m.PIER), [], [(lv, T["1070col"]) for lv in ("S", "B", "K", "KB")] + [("S", T["1410w1070"]), ("K", T["1410w1070"])]),
        # fire department
        "MF1": ("C20-16", "OR", "location higher limit on, the charge itself not selected", higher_fire("No", "50000"),
                {"LocationFireDepartmentCharge": ZERO}, [("H", T["fdhl"])], [("H", T["fdinc"])]),
        "MF2": ("C20-16", "OR", "higher limit 10,000 under the own 25,000 (LimitToUse 10,000)", higher_fire("Yes", "10000"),
                hand(["LocationFireDepartmentCharge"]), [("H", T["fdinc"])], [("H", T["fdhl"])]),
        "MF3": ("C20-16", "OR", "Fire Department on a Legal Liability building (no BPP form)",
                with_(z_fire("25000"), legal_liability), {}, [("L", T["fdform"])], []),
        # special-limit items
        "MS1": ("C20-16", "OR", "the four items with the contents' theft exclusion (CP 10 33)",
                with_(base, lambda s: (spcol_all(s), at(s)[P + "PersonalProperty"].update(
                    {P + "TheftExclusionPrsnlPropTable": {P + "TheftExclusionPrsnlProp": [{}]}}))),
                {}, [("C", T["1033"])] * 4, []),
        "MS2": ("C20-16", "OR", "the four items, contents blanketed on Broad", with_(lambda: blanket_all("No", "Broad"), spcol_all),
                {}, [("C", T["blktcol"])] * 4, []),
        "MS3": ("C20-16", "OR", "the contents' higher-limits indicators on Broad", with_(lambda: base("Broad"), lambda s: at(s)[
                P + "PersonalProperty"].update({P + "HigherLimitsPersonalPropertyTable": higher_pp("30000")})),
                {}, [("HP", T["hlspecial"])] * 4, []),
        "MS4": ("C20-16", "OR", "higher limits 15,000 under the records' own (Special)", with_(base, lambda s: (spcol_all(s), at(s)[
                P + "PersonalProperty"].update({P + "HigherLimitsPersonalPropertyTable": higher_pp("4000")}))),
                hand(SPC), [("HP", T["revised"])] * 4, [("HP", T["hlspecial"])]),
        # ACP
        "MA1": ("C20-16", "OR", "watercraft exclusion, no ACP (building and special class)", with_(base, watercraft), {},
                [("S", T["1410w1035"]), ("K", T["1410w1035"])], []),
        "MA2": ("C20-16", "OR", "watercraft exclusion + an ACP detail of another type", with_(base, lambda s: watercraft(s, "Retaining Walls x")),
                {}, [("S", T["type1410"]), ("K", T["type1410"])], [("S", T["1410w1035"])]),
        "MA3": ("C20-16", "OR", "Builders Risk building with ACP", with_(base, lambda s: (at(s)[P + "Structure"].update({"CovType": "Builders Risk"}),
                put(s, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "Limit": "30000"}))), {}, [("S", T["1410nv"])], []),
        "MA4": ("C20-16", "OR", "contents ACP on the Legal Liability form", with_(base, lambda s: (legal_liability(s), at(s)[P + "PersonalProperty"].update(
                {P + "AdditionalCoveredPropertyPrsnlPropTable": {P + "AdditionalCoveredPropertyPrsnlProp": [{}]}}))), {}, [("C", T["1410nv"])], []),
        "NC1": ("C20-16", "NC", "NC: watercraft exclusion, no NC ACP", with_(lambda: base(j="NC"), watercraft), {},
                [("S", T["1411w1035"]), ("K", T["1411w1035"])], []),
        "NC2": ("C20-16", "NC", "NC: watercraft + NC ACP details of another description",
                with_(lambda: base(j="NC"), lambda s: (watercraft(s), nc_acp(s, "Other Property"))), {},
                [("S", T["type1411"]), ("K", T["type1411"])], []),
        "NC3": ("C20-16", "NC", "NC: Builders Risk building and Legal Liability contents with NC ACP",
                with_(lambda: base(j="NC"), lambda s: (legal_liability(s), at(s)[P + "Structure"].update({"CovType": "Builders Risk"}),
                                                       nc_acp(s, m.BULK, ("Bldg", "PrsnlProp")))), {},
                [("S", T["1411nv"]), ("C", T["1411nv"])], []),
        "VA1": ("C20-16", "VA", "VA: watercraft and pier, no ACP", with_(lambda: base(j="VA"), lambda s: (watercraft(s), [
                put(s, r, {"Construction": m.PIER1, "Limit": "40000"}) for r in (m.PIER[0], m.PIER[2])])), {},
                [("S", T["1412w1035"]), ("K", T["1412w1035"]), ("S", T["1412w1070"]), ("K", T["1412w1070"])], []),
        "VA2": ("C20-16", "VA", "VA: watercraft + an ACP detail of another type", with_(lambda: base(j="VA"), lambda s: watercraft(s, "Retaining Walls x")),
                {}, [("S", T["type1412"]), ("K", T["type1412"])], []),
        "VA3": ("C20-16", "VA", "VA: Builders Risk building and Legal Liability contents with ACP",
                with_(lambda: base(j="VA"), lambda s: (legal_liability(s), at(s)[P + "Structure"].update({"CovType": "Builders Risk"}),
                                                       put(s, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "Limit": "30000"}),
                                                       at(s)[P + "PersonalProperty"].update({P + "AdditionalCoveredPropertyPrsnlPropTable": {
                                                           P + "AdditionalCoveredPropertyPrsnlProp": [{}]}}))), {},
                [("S", T["1412nv"]), ("C", T["1412nv"])], []),
        # Mortgageholders
        "MM1": ("C20-16", "OR", "Mortgageholders on the location policy (location numbered 1)", unit(m.mortgage(500, "25,000")), hand([m.MORT]),
                [("L", T["locnv"]), ("CP", T["only"])], [("CP", T["missloc"]), ("CP", T["either"])]),
        "MM2": ("C20-16", "OR", "Mortgageholders alone, terrorism Yes", mortgage_only(terror="Yes"), hand([m.MORT]),
                [("CP", T["trip"])], [("CP", T["missloc"]), ("L", T["locnv"])]),
        "MM3": ("C20-16", "OR", "no Mortgageholders, no location", no_mortgage(no_location=True), {}, [("CP", T["missloc"])], []),
        "MM4": ("C20-16", "OR", "Mortgageholders on a Standard Property Policy", mortgage_only(spp=True), hand([m.MORT]), [("CP", T["spp"])], []),
        "MM5": ("C20-16", "OR", "Mortgageholders with blanket rating", mortgage_only(blanket=True), hand([m.MORT]), [("CP", T["blkt"])], []),
        "MM6": ("C20-16", "OR", "Mortgageholders with CP 10 76", mortgage_only(extra=CYBER_ENS), hand([m.MORT]), [("CP", T["1076"])], []),
        "MM7": ("C20-16", "OR", "no Mortgageholders, both cyber exclusions", no_mortgage(extra={**CYBER, **CYBER_ENS}), {},
                [("CP", T["both"])], [("CP", T["either"])]),
        "MM8": ("C20-16", "OR", "no Mortgageholders, terrorism No", no_mortgage(terror="No"), {}, [("CP", T["tripyes"]), ("CP", T["either"])], []),
        "NY1": ("C20-16", "NY", "NY: Mortgageholders alone, no cyber exclusion", mortgage_only(j="NY"), hand([m.MORT]), [("CP", T["only77"])], []),
        "NY2": ("C20-16", "NY", "NY: Mortgageholders with CP 10 78", mortgage_only(extra=CYBER_ENS, j="NY"), hand([m.MORT]), [("CP", T["1078"])], []),
        "NY3": ("C20-16", "NY", "NY: no Mortgageholders, both cyber exclusions", no_mortgage(extra={**CYBER, **CYBER_ENS}, j="NY"), {},
                [("CP", T["both77"])], [("CP", T["either77"])]),
        "NY4": ("C20-16", "NY", "NY: Fire Department on a Legal Liability building, no Mortgageholders or cyber exclusion",
                with_(lambda: base(j="NY"), lambda s: (put(s, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes",
                                                                                               "Limit": "25000"}), legal_liability(s))),
                {}, [("L", T["fdform"]), ("CP", T["either77"])], []),
        "KS1": ("C20-16", "KS", "KS: Fire Department on a Legal Liability building (KS's own copy of the rule)",
                with_(lambda: base(j="KS"), lambda s: (put(s, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes",
                                                                                               "Limit": "25000"}), legal_liability(s))),
                {}, [("L", T["fdform"])], []),
        "VT1": ("C20-16", "VT", "VT: Fire Department on a Legal Liability building (VT's own copy of the rule)",
                with_(lambda: base(j="VT"), lambda s: (put(s, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes",
                                                                                               "Limit": "25000"}), legal_liability(s))),
                {}, [("L", T["fdform"])], []),
        "IL1": ("C20-16", "IL", "IL: Mortgageholders with mine subsidence", mortgage_only(extra={"MineSubsidenceCoverage": "Yes"}, j="IL"),
                hand([m.MORT]), [("CP", T["mine"])], []),
        "CT1": ("C20-16", "CT", "CT: CP 04 61 without Mortgageholders",
                no_mortgage(extra={P + "VacancyChangesPolicyTable": {P + "VacancyChangesPolicy": [{}]}}, j="CT"), {}, [("CP", T["ct"])], []),
        "AK1": ("C20-16", "AK", "AK: attorney fee limit 10,000 under the Mortgageholders limit",
                mortgage_only(extra={P + "ChangesAttorneysFeesTable": {P + "ChangesAttorneysFees": [{"Limit": "10000"}]}}, j="AK"),
                hand([m.MORT]), [("AK", T["ak"])], []),
        # fungus
        "MU1": ("C20-16", "OR", "Fungus Policy Limit with no fungus record", fungus_msg("Policy Limit", with_record=False), {}, [("CP", T["0431"])], []),
        "MU2": ("C20-16", "OR", "Fungus Separate Limits, separate-premises option No", fungus_msg("Separate Limits", "No"), hand([m.FUNGUS]),
                [("F", T["sepyes"])], [("F", T["seponly"])]),
        "MU3": ("C20-16", "OR", "Fungus Policy Limit, separate-premises option Yes", fungus_msg("Policy Limit", "Yes"), hand([m.FUNGUS]),
                [("F", T["seponly"])], [("F", T["sepyes"])]),
        "MU4": ("C20-16", "OR", "BI fungus period Not Applicable, indicator Yes", bi_period("Not Applicable", "Yes"), {}, [("B", T["bina"])], [("B", T["bimust"])]),
        "MU5": ("C20-16", "OR", "BI fungus period 90, indicator No", bi_period("90", "No"), {}, [("B", T["bimust"])], [("B", T["bina"])]),
        # EB
        "ME1": ("C20-16", "OR", "EB on the Broad cause", with_(lambda: base("Broad"), lambda s: put(s, m.EBB + "EBCov", inter={m.EBB: {
                "OccupancyCategory": "Institutional", "OccupancyGroup": "All other institutional risks"}})), {}, [("S", T["1046"])], []),
        "ME2": ("C20-16", "OR", "CP 10 47 without CP 10 46", with_(base, lambda s: at(s)[P + "Structure"].update({
                P + "SuspensionOrReinstatementOfCovForLossCausedByBreakdownOfCertainEquipmentTable": {
                    P + "SuspensionOrReinstatementOfCovForLossCausedByBreakdownOfCertainEquipment": [{}]}})), {}, [("S", T["1047"])], []),
    }


#: OI-115, recorded and NOT fixed (engine change needs the user's go): ISO skips a blank FIRST operand of
#: Subtract (Subtract(<blank LimitToUse>, 1,000) = 1,000), the way our Product skips one (OI-110); our Subtract
#: propagates the blank and the Fire Department charge prices $0. Pinned per case: ISO must equal the SKIP
#: reading's figure (hand: 1,000 / 100 x Factor, then the modifiers) and ours must stay $0. The competing
#: readings give $0 (propagate, ours) and the negative figure (blank as zero), so the probe can disagree.
#: (record, ISO under the skip reading, ours): ours is the product of the REMAINING operands (Product skips the
#: blank Divide, OI-110), i.e. Factor x the modifiers: 0.4 rounds to $0, 2.0 to $2.
#: OI-115 CLOSED 2026-09-30 (user's go, 205_oi115_probes.py): Property's Subtract now skips a single blank
#: operand as ISO does, so Z2 / Z2b are ordinary agree cases ($3, $17). Nothing is pinned as known any more.
KNOWN = {}


# ------------------------------------------------------------------- run

def lv(k):
    return L[k]


def count_hits(tagged, level, frag):
    return sum(1 for t, x in tagged if t == level and frag in x)


def check_msgs(tagged, must, mustnt):
    bad = []
    need = collections.Counter((lv(a), b) for a, b in must)
    for (level, frag), k in need.items():
        got = count_hits(tagged, level, frag)
        if got < k:
            bad.append(f"missing {level.replace(P, '')}: {frag} ({got} of {k})")
    for a, b in mustnt:
        if count_hits(tagged, lv(a), b):
            bad.append(f"unexpected {lv(a).replace(P, '')}: {b}")
    return bad


def iso_tagged(resp):
    """(level, message) for every ISO message: the level is the node whose ErcMessageTableId the message carries."""
    ids = {}

    def walk(o, k=None):
        if isinstance(o, dict):
            if "ErcMessageTableId" in o and k and k != "RatingMessages" and not isinstance(o.get("ErcMessageTableId"), (dict, list)):
                ids.setdefault(o["ErcMessageTableId"], k)
            for kk, v in o.items():
                if kk != "RatingMessages":
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp.get("Body", resp))
    out = []
    for rm in r11.find(resp, "RatingMessages"):
        for kind in (rm.values() if isinstance(rm, dict) else []):
            for e in (kind if isinstance(kind, list) else []):
                if isinstance(e, dict) and e.get("Description"):
                    out.append((ids.get(e.get("ErcMessageTableId"), "?"), e["Description"]))
    return out


def predictions(data, recs, j):
    out, lines, bad = {}, [], []
    for rec, want in recs.items():
        nodes_ = rc1.find(data, P + rec)
        eng = [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]
        if want == ZERO:
            hv = [Decimal(0)] * max(len(nodes_), 1)
        elif isinstance(want, Decimal):          # an explicit figure (the hand evaluator cannot read a blank Subtract)
            hv = [want] * max(len(nodes_), 1)
        else:
            res = m.predict(data, rec, j)
            off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
            hv = [Decimal(0) if o else h for (h, _), o in zip(res, off)]
        ok = all(not str(h).startswith("hand") for h in hv) and (
            [Decimal(str(e or 0)) for e in eng] == [Decimal(str(h)) for h in hv] if eng else all(same(h, 0) for h in hv))
        out[rec] = hv
        lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:66]:66s} predicted {[str(h) for h in hv]} engine {eng}"
                     + ("  (forced $0)" if want == ZERO else ""))
        if not ok:
            bad.append(rec)
    return out, lines, bad


def state_req(req, j):
    if j != "OR":
        for c in req["body"]["CommercialProperty"]:
            c["State"] = j
        req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
    return req


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        TAGGED.clear()
        try:
            data, ip = gc.run(build(), j)
        except InterpretError as exc:
            print(f"{cid:5s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        tagged = list(TAGGED)
        preds[cid], lines, bad = predictions(data, recs, j)
        mbad = check_msgs(tagged, must, mustnt)
        print(f"{cid:5s} {task} {j} {label}: {'as derived' if not bad and not mbad else 'DIFFERS'} "
              f"({len(recs)} records; messages {len(must)} required, {len(mustnt)} forbidden{': ' + '; '.join(mbad) if mbad else ', ok'})")
        if lines:
            print("\n".join(lines))
        mine = sorted({(t.replace(P, ""), x[:90]) for t, x in tagged if any(v in x for v in T.values())})
        for t, x in mine:
            print(f"      msg {t:34s} {x}")
        if bad or mbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, the (level, message) multiset):")
        for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = state_req(m.payload(build()), j)
            (gc.OUT / f"chunk20_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,220})', str(exc.body))
                print(f"  {cid:5s} ISO REFUSES {mm_.group(0)[:240] if mm_ else str(exc.body)[:240]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk20_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            TAGGED.clear()
            data, ip = rep.cmp.rate(req)
            ours = collections.Counter(TAGGED)
            isos = collections.Counter(iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mreq = check_msgs(list(isos.elements()), must, mustnt)
            if cid in KNOWN:
                rec, fig, ours_fig = KNOWN[cid]
                iso_v = [Decimal(str(x)) for x in r2.iso_of(resp, rec)]
                our_v = [Decimal(str(n.first("Premium").text or 0)) for n in rc1.find(data, P + rec)]
                as_recorded = iso_v == [fig] and our_v == [ours_fig] and ours == isos
                print(f"  {cid:5s} {'DIFFERS AS RECORDED (OI-115)' if as_recorded else 'DIFFER, NOT AS RECORDED'}: {r16.short(rec)} "
                      f"ISO {[str(x) for x in iso_v]} (the skip reading predicts {fig}; blank-as-zero -{fig}), ours {[str(x) for x in our_v]}; "
                      f"(level, message) {'equal' if ours == isos else 'DIFFER'}")
                if not as_recorded:
                    FAIL.append(f"{cid} live")
                continue
            ok = not pbad and not d and ours == isos and not mreq
            print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} "
                  f"({sum(isos.values())} ISO)"
                  + (f"; against the prediction: {mreq}" if mreq else "")
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (isos - ours).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (ours - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C20-15, C20-16): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
