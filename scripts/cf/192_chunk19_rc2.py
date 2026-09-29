#!/usr/bin/env python3
"""Chunk 19, RC-2 (C19-06 to C19-12): golden cases for all nine families.

Every case sits on 175_'s policy (chunk 7's five-coverage Oregon policy, chunk 15's modifiers:
package 0.85, IRPM 1.15, credit 0.9, building credit 0.95, and chunk 10's earthquake election on the
building). Each family's OWN values are looked up independently from the filed CSVs and checked on the
tree (field = independent value); SetPremium is then evaluated by hand (174_'s evaluator, half-up at
every DecimalPlaces) from the tree, whose parent rates are chunks 1-10's, ISO-confirmed. The engine
must equal it; --live ISO must equal it, every premium on the policy compared, messages compared.

  Tenants' (C19-06)  the container's own deductible factors decide the glass premium:
    T1  UNSCHEDULED, Special, the building's earthquake on, EQCovIndicator Yes: glass 45,000 with
        deductible "Not Applicable" (the NO-deductible factors: BGI / BGII 1.10, Special / Other 1.15),
        other than glass 50,000 at 1,000
    T2  SCHEDULED, Broad: glass 45,000 (the container's own Limit) at deductible "250" (Deductible250Factor:
        Basic 1.05, Broad 1.05; the EQ form reads the BROAD row), two items at 40,000 / 50,000
  Antennas (C19-07)  a broadcasting tower (special-class option 34a, Group II symbol AB) and a receiving
    A1  tower (34b, symbol B) on one policy, Special: Group I 0.07 both (the countrywide rows do not
        differ), Group II base rate by symbol (Oregon "Entire State": AB 0.024), x the family's symbol
        number (8); plus the Business Income record, 20,000
  Trees (C19-08)  Option 23 special-class rate by protection class; Group II symbol "B" x 8 x the
                  vehicle-exclusion factor (looked up only when VehExcl is "No": 1.15 in CT ME MA NH
                  RI VT, 1.00 elsewhere)
    TR1 Oregon, VehExcl No (1.00: the factor cannot move a dollar here)
    TR2 Vermont, VehExcl No (1.15)       } the pair where the factor moves the Group II premium
    TR3 Vermont, VehExcl Yes (not looked up: 1.0)
  Signs (C19-09)  SignPlacement decides the regime (read from the rules, 2026-09-29):
    S1  two DETACHED signs, Special + EQ: the sign's own rate, option 7a (Entirely Metal, 0.513) / 7b (other,
        1.188), Group II symbol "B" base x the metal / other-than-metal symbol number (4 / 8)
    S2  one ATTACHED sign, Broad: Group I / II COPY the building's adjusted rates; Broad reads the Broad base
        rate at the building's construction
        EVERY form prices on (Limit - 2,500) / 100: a built-in $2,500 deduction (193_'s Z6 corrected the first
        reading, 2026-09-29, which had it on Broad / Special / EQ only)
  Brands and Labels (C19-10)  rate per form = the smaller of the cap (BrandsAndLabelsMaxIncrease 0.053) and
                  round3(the contents' final rate x (1.10 - 1)), on the contents' LimitToUse
    B1  Special + the contents' own EQ election: 0.1 x the contents rates, no cap binds
    B2  Broad, the contents' IsNull-guarded FinalBasicGroupIRate submitted as 0.70: 0.070 > 0.053, the cap binds
  Household / Leased (C19-11)
    H1  Household 50,000, Special + the contents' own EQ: its own Special rate is the RESIDENTIAL apartments and
        condominiums contents rate (Oregon 0.178) x territory x LCM x the contents' adjustments; the other forms
        read the contents' final rates
    L1  chunk 18's A4 policy, rebuilt (item 200,000, contents AgreedValueOption Yes): the leased item's own
        premiums (limit / 100, rounded to a whole number, x the contents' final rates) predicted by hand, and its
        Agreed Value premiums on our engine now = what ISO returned for A4
  Temporarily Away / Manufacturers (C19-12)  two table rows each, chosen so the row decides the dollar:
    TA1 / TA2  Special factor 0.2 (theft covered) vs 0.1 (the contents' theft exclusion, TheftExclusionPrsnlProp)
    M1 / M2    the contents CovType: Stock 1.25 vs Machinery and Equipment 1.15 (factor = base - 1)

    python scripts/cf/192_chunk19_rc2.py [--live] [--cases T1,A1]

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

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

r2 = import_module("175_chunk16_rc2")
r4 = import_module("177_chunk16_rc4")
gc, rc1, rep, cmp, r16, r11, s18 = r2.gc, r2.rc1, r2.rep, r2.cmp, r2.r16, r2.r11, r4.s18
P = r2.P
q, row, same = r2.q, r2.row, r2.same
# ISO's own STC payloads send these as numbers
r11.NUMERIC |= {"LimitOnBuildingGlass", "LimitOnBuildingPropertyOtherThanGlass", "AllItemLimit", "Limit",
                "FinalBasicGroupIRate",
                # the portable policy's submitted rates (ISO refused them as strings; 189_ found the same)
                "BasicGroupIIBaseRate", "BasicGroupIIRate", "BasicGroupIBaseRate"}
FAIL = []
UNS, SCH = "UnscheduledBuildingPropertyTenantsPolicy", "ScheduledBuildingPropertyTenantsPolicy"
ANT, TREE = "RadioOrTelevisionAntennas", "OutdoorTreesShrubsAndPlants"
BROADCAST, RECEIVE = "Towers - Broadcasting Antennas (Radio and TV)", "Towers - Receiving Antennas (Radio and TV)"
BOTH = "Building Glass And Building Property Other Than Glass"


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def val(j, table, col, **keys):
    """the state's own row if it files one with rows, else the CW row (the in-force resolution)."""
    pk = book_for(j, r2.ASOF).state.package.content
    try:
        return row(table, col, pk, StateCode=j, **keys)
    except (LookupError, FileNotFoundError):
        return row(table, col, StateCode="CW", **keys)


# ---------------------------------------------------------------- policies

def portable(j):
    """175_'s policy; outside Oregon, 189_'s portable parents (territory factor 1.0, the state's own
    location fields and contents territory, submitted Group II rates)."""
    sub = r2.base(j)
    if j != "OR":
        at = rc1.node_dicts(sub)
        for k in ("Structure", "PersonalProperty"):
            at[P + k].setdefault("BasicGroupIIRate", "0.030")
        for k in ("BusinessIncome", "SpecialClassBusnIncome", "SpecialClass"):
            at[P + k].setdefault("BasicGroupIIBaseRate", "0.030")
        terr = r4.rows(j, "PrsnlPropTerrMultiplier")
        if terr:
            at[P + "Location"]["SpecialRatingTerr"] = terr[0]["SpecialRatingTerr"]
        else:
            at[P + "Location"].pop("SpecialRatingTerr", None)
    return sub


def with_cause(sub, cause):
    at = rc1.node_dicts(sub)
    for k in ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome"):
        at[P + k]["CauseOfLoss"] = cause
    return sub


def t1():
    sub = with_cause(portable("OR"), "Special")
    rc1.node_dicts(sub)[P + "Structure"][P + UNS + "Table"] = {P + UNS: [{
        "CovType": BOTH, "CausesOfLoss": "Special", "EQCovIndicator": "Yes", "Coinsurance": "80%",
        "LimitOnBuildingGlass": "45000", "DeductibleOnBuildingGlass": "Not Applicable",
        "LimitOnBuildingPropertyOtherThanGlass": "50000", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000"}]}
    return sub


def t2():
    sub = with_cause(portable("OR"), "Broad")
    rc1.node_dicts(sub)[P + "Structure"][P + SCH + "Table"] = {P + SCH: [{
        "CovType": BOTH, "CausesOfLoss": "Broad", "EQCovIndicator": "Yes", "Coinsurance": "80%", "Limit": "45000",
        "DeductibleOnBuildingGlass": "250", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000",
        P + SCH + "DetailTable": {P + SCH + "Detail": [{"Limit": "40000"}, {"Limit": "50000"}]}}]}
    return sub


def a1():
    sub = with_cause(portable("OR"), "Special")
    at = rc1.node_dicts(sub)
    det = lambda typ, lim: {"CauseOfLoss": "Special", "Coinsurance": "80%", "Limit": lim, "Type": typ,
                            "Height": "Not over 75 Feet in Height", "EQCovIndicator": "Yes"}
    at[P + "Structure"][P + ANT + "Table"] = {P + ANT: [{
        P + ANT + "DetailTable": {P + ANT + "Detail": [det(BROADCAST, "30000"), det(RECEIVE, "25000")]}}]}
    at[P + "BusinessIncome"][P + ANT + "BusinessIncomeOrExtraExpenseTable"] = {
        P + ANT + "BusinessIncomeOrExtraExpense": [{"Limit": "20000", "TypeOfRadioAndTVAntennas": BROADCAST}]}
    for rec in [f"{ANT}Detail{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")] + \
               [f"{ANT}BusinessIncomeOrExtraExpense{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]:
        r2.put(sub, rec)
    return sub


def tree_case(j, veh):
    def build():
        sub = with_cause(portable(j), "Special")
        c = {"AllItemLimit": "25000", "CauseOfLoss": "Special", "VehExcl": veh}
        if j != "OR":
            c["BasicGroupIIBaseRate"] = "0.030"      # the portable policy has no Group II territory (IsNull-guarded)
        rc1.node_dicts(sub)[P + "Structure"][P + TREE + "Table"] = {P + TREE: [c]}
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
            r2.put(sub, f"{TREE}{f}Coverage", state=j)
        return sub
    return build


# ------------------------------------------------------- independent values

NODED = lambda c: row("BuildingGlassNoDeductibleFactor", "Factor", StateCode="CW", CauseOfLossDeductible=c)
D250 = lambda c: row("Deductible250Factor", "Factor", StateCode="CW", CauseOfLoss=c)
COINS80 = row("CoinsuranceFactor", "Factor", StateCode="CW", CoinsuranceValue="80%")


def expect_t1(data, j):
    return {UNS: {"DeductibleOnBuildingGlassFactorBasicGroupI": NODED("Basic Group I"),
                  "DeductibleOnBuildingGlassFactorBasicGroupII": NODED("Basic Group II"),
                  "DeductibleOnBuildingGlassFactorSpecial": NODED("Special"),
                  "DeductibleOnBuildingGlassFactorBroad": NODED("Other"),
                  "DeductibleOnBuildingGlassFactorEQ": NODED("Other"),
                  "CoinsuranceFactor": COINS80}}


def expect_t2(data, j):
    return {SCH: {"DeductibleOnBuildingGlassFactorBasicGroupI": D250("Basic"),
                  "DeductibleOnBuildingGlassFactorBasicGroupII": D250("Basic"),
                  "DeductibleOnBuildingGlassFactorBroad": D250("Broad"),
                  "DeductibleOnBuildingGlassFactorEQ": D250("Broad"),
                  "DeductibleOnBuildingGlassFactorSpecial": D250("Special"),
                  "CoinsuranceFactor": COINS80}}


def pc_to_use(data):
    n = r16.find(data, P + "Structure")[0].first("ProtectionClassToUse")
    return n.text if n is not None else None


def expect_a1(data, j):
    pc = pc_to_use(data)
    terr = rc1.node_dicts  # noqa (the Oregon Group II territory is "Entire State", chunk 2)
    sc = lambda opt: val(j, "BasicGroupIRateSpecialClass", "Rate", SpecialClassDescConvertedOption=opt, ProtectionClassToUse=pc)
    b2 = lambda sym: val(j, "BasicGroupIIRate", "Rate", BasicGroupIIRatingTerr="Entire State", BasicGroupIISymbol=sym, CovType="Bldg")
    sym = val(j, "RadioOrTelevisionAntennasBasicGroupIISymbol", "Factor", Constant="Y")
    return {(ANT + "Detail", 0): {"BasicGroupIRate": sc("Option34a"), "BasicGroupIIBaseRate": b2("AB"), "BasicGroupIISymbolNum": sym},
            (ANT + "Detail", 1): {"BasicGroupIRate": sc("Option34b"), "BasicGroupIIBaseRate": b2("B"), "BasicGroupIISymbolNum": sym},
            ANT: {"ClassCode": val(j, "RadioOrTelevisionAntennasClassCode", "Code", Constant="Y")}}


def expect_tree(veh):
    def f(data, j):
        pc = pc_to_use(data)
        e = {"BasicGroupIBaseRate": val(j, "BasicGroupIRateSpecialClass", "Rate", SpecialClassDescConvertedOption="Option23",
                                        ProtectionClassToUse=pc),
             "BasicGroupIISymbolNum": val(j, "OutdoorTreeBasicGroupIISymbol", "Factor", Constant="Y"),
             "VehExclFactor": val(j, "VehExclFactorOutdoorTrees", "Factor", Constant="Y") if veh == "No" else Decimal("1.0")}
        if j == "OR":
            e["BasicGroupIIBaseRate"] = val(j, "BasicGroupIIRate", "Rate", BasicGroupIIRatingTerr="Entire State",
                                            BasicGroupIISymbol="B", CovType="Bldg")
        return {TREE: e}
    return f


TEN = lambda kind, forms: [f"{kind}{f}Cov" for f in forms]
T1_RECS = [f"{UNS}BuildingGlass{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")] + \
          [f"{UNS}BuildingPropertyOtherThanGlass{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "EQ", "Special")]
T2_RECS = [f"{SCH}BuildingGlass{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")] + \
          [f"{SCH}DetailBuildingPropertyOtherThanGlass{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "EQ", "Special")]
A1_RECS = [f"{ANT}Detail{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")] + \
          [f"{ANT}BusinessIncomeOrExtraExpense{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
TREE_RECS = [f"{TREE}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]


SIGN, BRAND = "OutsideSigns", "BrandsAndLabels"


def sign_det(cause, placement, constr, lim):
    return {"CauseOfLoss": cause, "Coinsurance": "80%", "Limit": lim, "ConstructionType": constr,
            "SignPlacement": placement, "EQCovIndicator": "Yes"}


def s1():
    """two DETACHED signs, Special + EQ: metal (option 7a, symbol table 4) and other than metal (7b, 8)."""
    sub = with_cause(portable("OR"), "Special")
    rc1.node_dicts(sub)[P + "Structure"][P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [
        sign_det("Special", "Detached", "Entirely Metal", "30000"), sign_det("Special", "Detached", "Other", "20000")]}}]}
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
        r2.put(sub, f"{SIGN}Detail{f}Coverage")
    return sub


def s2():
    """one ATTACHED sign, Broad: it copies the building's adjusted rates and reads the Broad base rate at the
    building's construction."""
    sub = with_cause(portable("OR"), "Broad")
    rc1.node_dicts(sub)[P + "Structure"][P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [
        sign_det("Broad", "Attached", "Entirely Metal", "30000")]}}]}
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
        r2.put(sub, f"{SIGN}Detail{f}Coverage")
    return sub


def brands(cause, final_bgi=None):
    """Brands and Labels on the contents, with the contents' own earthquake election (C19-04: EQGrade, the
    contents EQ endorsement record). final_bgi submits the contents' IsNull-guarded FinalBasicGroupIRate so the
    0.053 cap binds on Group I."""
    def build():
        sub = with_cause(portable("OR"), cause)
        at = rc1.node_dicts(sub)
        st, pp = at[P + "Structure"], at[P + "PersonalProperty"]
        pp.update({k: st[k] for k in ("EQCovIndicator", "EQCoinsurance", "EQDeductible") if k in st})
        pp.update({"EQGrade": "1", "EQSprinklerLeakageOnly": "No"})
        if final_bgi:
            pp["FinalBasicGroupIRate"] = final_bgi
        r2.put(sub, "EarthquakeAndVolcanicEruptionEndorsementPrsnlProp")
        pp[P + BRAND + "Table"] = {P + BRAND: [{}]}
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
            r2.put(sub, f"{BRAND}{f}Coverage")
        return sub
    return build


def expect_s1(data, j):
    pc = pc_to_use(data)
    sc = lambda opt: val(j, "BasicGroupIRateSpecialClass", "Rate", SpecialClassDescConvertedOption=opt, ProtectionClassToUse=pc)
    b2 = val(j, "BasicGroupIIRate", "Rate", BasicGroupIIRatingTerr="Entire State", BasicGroupIISymbol="B", CovType="Bldg")
    return {(SIGN + "Detail", 0): {"BasicGroupIRate": sc("Option7a"), "BasicGroupIIBaseRate": b2,
                                   "BasicGroupIISymbolNum": val(j, "OutsideSignsBasicGroupIISymbol", "Factor", Constant="Y")},
            (SIGN + "Detail", 1): {"BasicGroupIRate": sc("Option7b"), "BasicGroupIIBaseRate": b2,
                                   "BasicGroupIISymbolNum": val(j, "OutsideSignsBasicGroupIISymbolOtherThanMetal", "Factor", Constant="Y")}}


def expect_s2(data, j):
    stn = r16.find(data, P + "Structure")[0]
    g = lambda f: stn.first(f).text if stn.first(f) is not None else None
    return {(SIGN + "Detail", 0): {"BasicGroupIRate": g("BasicGroupICauseOfLossAdjustment"),
                                   "BasicGroupIIRate": g("BasicGroupIICauseOfLossAdjustment"),
                                   "BroadBaseRate": val(j, "BroadFormBaseRate", "Rate", ConstructionTypeToUse=g("ConstructionTypeToUse"),
                                                        CovType="Bldg")}}


def expect_brands(data, j):
    """rate per form = MaxIncrease if MaxIncrease <= round3(contents final rate x Factor), else that product."""
    pp = r16.find(data, P + "PersonalProperty")[0]
    mx = val(j, "BrandsAndLabelsMaxIncrease", "Rate", Constant="Y")
    fac = q(val(j, "BrandsAndLabelsFactor", "Factor", Constant="Y") - 1, 3)
    e = {"MaxIncrease": mx, "Factor": fac}
    for mine, theirs in (("BasicGroupIRate", "FinalBasicGroupIRate"), ("BasicGroupIIRate", "FinalBasicGroupIIRate"),
                         ("BroadRate", "FinalBroadRate"), ("SpecialRate", "FinalSpecialRate"), ("EQRate", "FinalEQRate")):
        n = pp.first(theirs)
        prod = q(Decimal(n.text if n is not None and n.text else 0) * fac, 3)
        e[mine] = mx if mx <= prod else prod
    return {BRAND: e}


SIGN_RECS = [f"{SIGN}Detail{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]
BRAND_RECS = [f"{BRAND}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]


HH, TA, MC = "HouseholdPersonalPropertyCoverage", "SpecifiedBusnPrsnlPropTempAwayFromPremises", "ManufacturersConsequentialLossAssumption"
g18 = import_module("187_chunk18_rc2")                   # chunk 18's A4 (Leased Property Agreed Value)


def contents_eq(sub, grade="1"):
    """the contents' OWN earthquake election (C19-04): the building's election copied, EQGrade, sprinkler-leakage
    only "No" (Temporarily Away's EQ factor needs "No" / "Yes"), and the contents EQ endorsement record."""
    at = rc1.node_dicts(sub)
    st, pp = at[P + "Structure"], at[P + "PersonalProperty"]
    pp.update({k: st[k] for k in ("EQCovIndicator", "EQCoinsurance", "EQDeductible") if k in st})
    pp.update({"EQGrade": grade, "EQSprinklerLeakageOnly": "No"})
    r2.put(sub, "EarthquakeAndVolcanicEruptionEndorsementPrsnlProp")
    return pp


def h1():
    sub = with_cause(portable("OR"), "Special")
    pp = contents_eq(sub)
    pp[P + HH + "Table"] = {P + HH: [{P + HH + "DetailTable": {P + HH + "Detail": [{"Limit": "50000"}]}}]}
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
        r2.put(sub, f"{HH}Detail{f}Coverage")
    return sub


def ta(theft_excluded):
    def build():
        sub = with_cause(portable("OR"), "Special")
        pp = contents_eq(sub)
        if theft_excluded:
            r2.put(sub, "TheftExclusionPrsnlProp")
        pp[P + TA + "Table"] = {P + TA: [{P + TA + "DetailTable": {P + TA + "Detail": [{"Limit": "100000"}]}}]}
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
            r2.put(sub, f"{TA}Detail{f}Cov")
        return sub
    return build


def mc(covtype):
    def build():
        sub = with_cause(portable("OR"), "Special")
        pp = contents_eq(sub)
        pp["CovType"] = covtype
        pp[P + MC + "Table"] = {P + MC: [{}]}
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
            r2.put(sub, f"{MC}{f}Coverage")
        return sub
    return build


def expect_h1(data, j):
    return {HH: {"SpecialBaseRate": val(j, "SpecialPrsnlPropRate", "Rate", OccupCategory="Residential Apartments and Condominiums",
                                        OccupCategorySeverity="Not Applicable")}}


def expect_l1(data, j):
    return {("LeasedPropertyDetail", 0): {"AgreeValueOption": "Yes",
                                          "AgreedValueFactor": q(val(j, "AgreedValueFactor", "Factor", Constant="Y") - 1, 3)}}


def expect_ta(theft_excluded):
    def f(data, j):
        tf = lambda c: val(j, "SpecifiedPropertyAwayFromPremisesAddlPremiumFactor", "Factor", CauseOfLoss=c)
        return {"PersonalProperty": {"SpecialTheftExclusionIndicator": "1" if theft_excluded else "0"},
                f"{TA}DetailBasicGroupICov": {"Factor": tf("BGI")},
                f"{TA}DetailBasicGroupIICov": {"Factor": tf("BGII")},
                f"{TA}DetailEarthquakeCov": {"Factor": tf("EQ")},
                f"{TA}DetailSpecialCov": {"Factor": tf("SpecialWhenTheftIsExcluded" if theft_excluded else "SpecialWhenTheftIsCovered")}}
    return f


def expect_mc(covtype):
    def f(data, j):
        base = val(j, "ManufacturersConsequentialLossAssumptionFactor", "Factor", CovTypePrsnlProp=covtype)
        return {MC: {"BaseFactor": base, "Factor": q(base - 1, 3)}}
    return f


HH_RECS = [f"{HH}Detail{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]
LEASED_RECS = [f"LeasedPropertyDetail{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]
LEASED_AV = [f"LeasedPropertyDetailAgreedValue{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Special")]
TA_RECS = [f"{TA}Detail{f}Cov" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]
MC_RECS = [f"{MC}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")]


def a4_agreement():
    """C19-11's tie to chunk 18: L1 IS chunk 18's A4 policy; its Leased Agreed Value premiums must equal what ISO
    returned for A4 (stored, chunk18_rc2_A4_response.json), on our engine now."""
    resp = json.loads((gc.OUT / "chunk18_rc2_A4_response.json").read_text(encoding="utf-8"))
    data, _ = gc.run(g18.a4(), "OR")
    out = []
    for rec in LEASED_AV:
        iso = [Decimal(str(x)) for x in r2.iso_of(resp, rec)]
        ours = [Decimal(n.first("Premium").text) for n in rc1.find(data, P + rec) if n.first("Premium") is not None]
        out.append((rec, iso, ours))
    return out


def cases():
    return {
        "T1": ("C19-06", "OR", "Tenants' unscheduled, Special + EQ: glass NO deductible, other than glass 1,000", t1, expect_t1, T1_RECS),
        "T2": ("C19-06", "OR", "Tenants' scheduled, Broad: glass $250 deductible, two items", t2, expect_t2, T2_RECS),
        "A1": ("C19-07", "OR", "Antennas: broadcasting (34a / AB) + receiving (34b / B) tower, Special + EQ; BI record", a1, expect_a1, A1_RECS),
        "TR1": ("C19-08", "OR", "Trees, Oregon, VehExcl No (factor 1.00)", tree_case("OR", "No"), expect_tree("No"), TREE_RECS),
        "TR2": ("C19-08", "VT", "Trees, Vermont, VehExcl No (factor 1.15)", tree_case("VT", "No"), expect_tree("No"), TREE_RECS),
        "TR3": ("C19-08", "VT", "Trees, Vermont, VehExcl Yes (not looked up: 1.0)", tree_case("VT", "Yes"), expect_tree("Yes"), TREE_RECS),
        "S1": ("C19-09", "OR", "Signs: two DETACHED signs, metal (7a, symbol 4) and other (7b, symbol 8), Special + EQ", s1, expect_s1, SIGN_RECS),
        "S2": ("C19-09", "OR", "Signs: one ATTACHED sign, Broad (the building's own adjusted rates)", s2, expect_s2, SIGN_RECS),
        "B1": ("C19-10", "OR", "Brands and Labels, Special + contents EQ: the cap does not bind", brands("Special"), expect_brands, BRAND_RECS),
        "B2": ("C19-10", "OR", "Brands and Labels, Broad, contents Group I rate 0.70 submitted: the cap BINDS on Group I",
               brands("Broad", "0.70"), expect_brands, BRAND_RECS),
        "H1": ("C19-11", "OR", "Household Personal Property 50,000, Special + contents EQ: the residential contents rate", h1, expect_h1, HH_RECS),
        "L1": ("C19-11", "OR", "Leased Property on chunk 18's A4 policy (item 200,000, the contents' Agreed Value Yes)", g18.a4, expect_l1,
               LEASED_RECS + LEASED_AV),
        "TA1": ("C19-12", "OR", "Temporarily Away 100,000, Special, theft covered (Special factor 0.2)", ta(False), expect_ta(False), TA_RECS),
        "TA2": ("C19-12", "OR", "Temporarily Away 100,000, Special, contents theft exclusion (Special factor 0.1)", ta(True), expect_ta(True), TA_RECS),
        "M1": ("C19-12", "OR", "Manufacturers Consequential Loss, contents CovType Stock (1.25 -> 0.25)", mc("Stock"), expect_mc("Stock"), MC_RECS),
        "M2": ("C19-12", "OR", "Manufacturers Consequential Loss, contents CovType Machinery and Equipment (1.15 -> 0.15)",
               mc("Machinery and Equipment"), expect_mc("Machinery and Equipment"), MC_RECS),
    }


# ------------------------------------------------------------------- run

def field_checks(data, expect):
    """(where, field, tree value, independent value) for every expected field."""
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
            res, _ = r2.predict(data, rec, {}, j)
            nodes_ = rc1.find(data, P + rec)
            off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
            res = [(Decimal(0) if o else h, e) for (h, e), o in zip(res, off)] if len(off) == len(res) else res
            ok = bool(res) and all(not str(h).startswith("hand") and same(h, e) for h, e in res)
            nz = [h for h, e in res if e not in (None, "") and not same(e, 0)]
            priced += bool(nz)
            preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:70]:70s} predicted {[str(h) for h, _ in res]}"
                         f" engine {[e for _, e in res]}" + ("" if nz else "  ($0)"))
            if not ok:
                bad.append(rec)
        print(f"{cid:3s} {task} {j} {label}: engine {'as derived' if not bad and not fbad else 'DIFFERS'} "
              f"({priced} of {len(recs)} priced; {len(fc) - len(fbad)} of {len(fc)} own values = independent)")
        for w, f, g, want in fc:
            print(f"      {'ok  ' if same(g, want) else 'FAIL'} {w[:52]:52s} {f:44s} tree {g}  independent {want}")
        print("\n".join(lines))
        if bad or fbad:
            FAIL.append(cid)

    if "L1" in cs:
        print("\nC19-11 x C18-06: Leased Property Agreed Value on A4's policy, our engine now vs ISO's stored A4 response")
        for rec, iso, ours in a4_agreement():
            ok = sorted(iso) == sorted(ours) and iso
            print(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:60]:60s} ISO (A4) {[str(x) for x in iso]}  ours {[str(x) for x in ours]}")
            if not ok:
                FAIL.append(f"A4 {rec}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, j, label, build, expect, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            if j != "OR":
                for cp in req["body"]["CommercialProperty"]:
                    cp["State"] = j
                req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk19_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {cid:3s} ISO REFUSES {m.group(0)[:220] if m else str(exc.body)[:220]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk19_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
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
    print(f"\nRC-2 (C19-06 to C19-12): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
