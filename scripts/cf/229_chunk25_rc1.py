#!/usr/bin/env python3
"""Chunk 25, RC-1 (C25-02..C25-07): Flood, evidence and plumbing. No ISO calls.

Every premium record is predicted three ways: a hand model written from the rule text below, 174_'s independent
SetPremium evaluator, and the engine. Inputs a hand model reads from the engine are parent values built and
ISO-confirmed in earlier chunks (a coverage's LossCostMultiplier, FullPrsnlPropValueToUse, CoinsuranceToUse, the BI
MaxPeriod / MonthlyLimit / ExtraExpense factors, the policy modifiers and cyber factors). Everything flood is derived
here from the filed tables.

  location record     attaches iff Location.FloodCovIndicator = "Yes"; CommunityRatingSystemFactor from the grade;
  (General Info)      MaxNFIP amounts (Building / Content); AK empties its ProcessCall, FL too
  property records    Deductible = the location record's; ITV = r4(Limit / own full value) (blanketed: the blanket
  (Bldg / BPP / SC)   detail's); pct = r2(ITV x 100); ToUse = round(pct) if >= 1, 1 if > 0, else 0
                      TotalPropertyValue = Location.FloodTotalPropertyValue (blanketed, not excess: the blanket's sum)
                      NOT excess: the deductible picks ONE of seven rate-modification tables (500 / 1,000 -> 1;
                        2,500 / 5,000 -> 2; 10,000 / 25,000 -> 3; 50,000 / 75,000 -> 4; 100,000 / 250,000 -> 5;
                        500,000 / 750,000 -> 6; 1,000,000 -> 7), keyed (deductible, ITV%, TPV), the factor
                        interpolated inside the ITV band, r4 then r3; 0 unless TPV > 0 and 1 <= ToUse <= 100
                      excess over NFIP: table 6 (deductible 750,000) or 7 (1,000,000) keyed on the OWN full value,
                        only when that value exceeds the NFIP maximum and 1 <= ToUse <= 100; any other deductible 0
                      annual aggregate 0.999 when Limit = AnnualAggregateLimit, else 1
                      base = loss cost (state rows, else CW) keyed (Building | Contents, construction, zone); Special
                        Class reads the FLOOD RECORD's own ConstructionType, Building / BPP the parent's ...ToUse
                      rate = r3(r3(r3(base x LCM) x aggregate) x (modification | excess factor))
                      adjusted = r3(rate x CRS factor) when the location record carries a CRS grade, else rate
                      premium = r0 chain: adjusted x Limit / 100, package mod, IRPM, cyber flood, cyber COL flood;
                        $0 when IncludedInBlkt is not "No"
  BI / SCBI           coinsurance = the parent's CoinsuranceToUse (blanketed: from the blanket's ITV); type-of-risk
                      factor from BusnIncomeFactor (combined types r3 of two weighted r3 terms); BI factor = the
                      MaxPeriod / MonthlyLimit / ExtraExpense factor or the type-of-risk factor; base = the loss
                      cost on the BUILDING row (BI: the building's construction, or the location's highest
                      operational-unit base rate for MaxPeriod / Monthly / EE-only in an operational unit; SCBI: its
                      flood record's own construction); rate = r3(r3(base x LCM) x aggregate); adjusted = r3(rate x
                      BI factor); no modification, excess or community rating; premium as above (cyber COL: the
                      parent's ...BusnIncomeFloodToUse)
  blanket detail      levels = sum of members' full values (excess: only those above the NFIP maximum); BI level =
                      members' Full100PctValue (AnnualNetIncome); average = r3(sum of members' r0(full x adjusted rate)
                      / total); premium = r0 chain: average x Limit / 100, package mod, IRPM, cyber, cyber COL
  AK, FL              all six premium files: r0(r0(ManualPremium x package mod) x IRPM); rates and stat codes emptied

    python scripts/cf/229_chunk25_rc1.py [--skip-stored]

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import copy
import csv
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

from cf_engine.resolve import book_for                                   # noqa: E402

m = import_module("219_chunk23_rc1")
rc1, r16, rep, cmp = m.rc1, m.r16, m.rep, m.cmp
s18 = import_module("164_chunk14_c14-18_all_states")
P, D, ASOF = m.P, Decimal, m.ASOF
r, val, d = m.r, m.val, m.d
FAIL = []
FL = "FloodCoverageEndorsement"
B, PP, SC, BI, SCBI = FL, FL + "PrsnlProp", FL + "SpecialClass", FL + "BusnIncome", FL + "SpclClassBusnIncome"
LOCR, BR, BRD = "FloodCovEndtLocation", "FloodCovEndtBlanketRating", "FloodCovEndtBlanketRatingDetail"
PROP = (B, PP, SC)
TE = (BI, SCBI)
FAMILY = PROP + TE + (LOCR, BR, BRD)
CW = book_for("OR", ASOF).parent.package.content
RULES = {n: (CW / "Rules" / f"{P}{n}Rules.Rule.xml").read_text(encoding="utf-8-sig") for n in FAMILY}
PREMIUM_RECS = [n for n in FAMILY if m.cen.set_premium(RULES[n])]
STC = "STC_CP000015648"
#: the full value each property record reads (../../ of the flood record) and its loss-cost row
FULL = {B: "FullBldgValue", PP: "FullPrsnlPropValueToUse", SC: "FullSpecialClassValue"}
LC_ROW = {B: "Building", PP: "Contents", SC: "Building", BI: "Building", SCBI: "Building"}
#: deductible -> rate-modification table (SetFloodModificationFactor)
MOD_TABLE = {"500": 1, "1,000": 1, "2,500": 2, "5,000": 2, "10,000": 3, "25,000": 3, "50,000": 4, "75,000": 4,
             "100,000": 5, "250,000": 5, "500,000": 6, "750,000": 6, "1,000,000": 7}
EXCESS_TABLE = {"750,000": 6, "1,000,000": 7}
#: submitted values (C25-16): {(record, field): value}. Every field below is IsNull-guarded in its Set rule, so a submitted
#: value replaces the computed one at that step and everything downstream uses it; the hand models read them from here,
#: never from the engine's output
SUB = {}


def sub(rec, field, v):
    return SUB.get((rec, field), v)


JM = "Joisted Masonry - Reinforced"                    # the building domain; ConstructionTypeToUse maps it to "Joisted Masonry"


def progress(what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{mm}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def anc(n, tag):
    while n is not None and n.tag != P + tag:
        n = n.parent
    return n


def rule(text, name):
    mt = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', text, re.S)
    return mt.group(0) if mt else ""


# ------------------------------------------------------------------ tables (state rows, else CW)

def rows(pkg, name):
    f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def trows(j, name):
    """the lookups are FirstNonNull(state row, CW row): the state's rows when it files any, else CW's."""
    b = book_for(j, ASOF)
    st = rows(b.state.package.content, name) or []
    return [x for x in st if x["StateCode"] == j] or [x for x in (rows(b.parent.package.content, name) or []) if x["StateCode"] == "CW"]


def one(j, name, col, **keys):
    for x in trows(j, name):
        if all(x.get(k) == v for k, v in keys.items()):
            return D(x[col])
    return None


def banded(j, n, ded, itv, tpv):
    """PropertyRateModificationFactors{n}: ITV band [From, ToLessThan) x TPV band, factor interpolated on ITV."""
    for x in trows(j, f"PropertyRateModificationFactors{n}"):
        if x["Deductible"] != ded:
            continue
        lo, hi = D(x["InsuranceToValueLevelPercentage_From"]), D(x["InsuranceToValueLevelPercentage_ToLessThan"])
        if lo <= D(itv) < hi and D(x["TotalPropertyValue_From"]) <= D(tpv) < D(x["TotalPropertyValue_ToLessThan"]):
            f0, f1 = D(x["Factor_From"]), D(x["Factor_ToLessThan"])
            return r(r(f0 + (f1 - f0) * (D(itv) - lo) / (hi - lo), 4), 3)
    return None


# ------------------------------------------------------------------ hand models

def loc_rec(loc):
    lr = rc1.find(loc, P + LOCR)
    return lr[0] if lr else None


def details(cp):
    return rc1.find(cp, P + BRD)


def detail_for(node):
    """the blanket detail a blanketed member belongs to (IncludedInBlkt Yes, BlanketIDNum = the detail's UnitNumber)."""
    if val(node, "IncludedInBlkt") != "Yes" or d(node, "BlanketIDNum") <= 0:
        return None
    for det in details(m.root(node)):
        if d(det, "UnitNumber") == d(node, "BlanketIDNum"):
            return det
    return None


def itv_touse(pct):
    if pct >= 1:
        return int(r(pct, 0))
    return 1 if pct > 0 else 0


def members(cp, det):
    """(record name, flood node) of every member of a blanket detail, every location."""
    out = []
    for rec in PROP + TE:
        for n in rc1.find(cp, P + rec):
            if val(n, "IncludedInBlkt") == "Yes" and d(n, "BlanketIDNum") == d(det, "UnitNumber"):
                out.append((rec, n))
    return out


#: the blanket detail's coverage switch per member record (SetBuildingLevel100PctValue ... in the detail file)
COV_FLAG = {B: "BldgCov", PP: "PrsnlPropCov", SC: "SpecialClassCov"}
NFIP_MAX = {B: "Building", PP: "Content", SC: "Building"}
BI_FLAG = {"Business Income With Extra Expense": "BusnIncomeWithExtraExpenseCov",
           "Business Income Without Extra Expense": "BusnIncomeWithoutExtraExpenseCov", "Extra Expense Only": "ExtraExpenseCov"}


def cov(node):
    """the coverage a flood record sits under (its parent is the ...Table wrapper)."""
    return node.parent.parent


def full_value(rec, node):
    return d(cov(node), FULL[rec])


def bi_full100(node):
    """SetFull100PctValue: blanketed and not Extra Expense Only -> AnnualNetIncome (the EE-only branch is not exercised)."""
    if val(node, "IncludedInBlkt") != "Yes":
        return D(0)
    return d(node, "AnnualNetIncome")


def level_values(j, det, cp):
    """100% values per level for a blanket detail, from the members (hand)."""
    excess = val(det, "ExcessOverMaxNFIPIndicator")
    lv = {B: D(0), PP: D(0), SC: D(0), BI: D(0), SCBI: D(0)}
    for rec, n in members(cp, det):
        if rec in PROP:
            fv = full_value(rec, n)
            mx = one(j, "MaxNFIPCoverageAmount", "Amount", Coverage=NFIP_MAX[rec])
            if excess == "No" or (excess == "Yes" and fv > mx):
                lv[rec] += fv
        elif val(det, BI_FLAG.get(val(cov(n), "CovType"), "-")) == "Yes":
            lv[rec] += bi_full100(n)
    return lv


def detail_itv(j, det, cp):
    total = sum(level_values(j, det, cp).values())
    itv = r(d(det, "Limit") / total, 4) if total > 0 else D(0)
    pct = r(itv * 100, 2)
    return total, itv, pct, itv_touse(pct)


def agg_factor(j, node, rec):
    det = detail_for(node)
    if det is not None:
        if rec in PROP:
            flag = val(det, COV_FLAG[rec]) == "Yes"
        else:
            flag = val(det, BI_FLAG.get(val(cov(node), "CovType"), "-")) == "Yes"
        if flag and d(det, "Limit") == d(det, "AggLimit"):
            return one(j, "AnnualAggregateFactor", "Factor", Constant="Y")
        return D(1)
    if val(node, "IncludedInBlkt") == "No" and d(node, "Limit") == d(node, "AnnualAggregateLimit"):
        return one(j, "AnnualAggregateFactor", "Factor", Constant="Y") or D(1)
    return D(1)


def edition(j):
    """the in-force countrywide parent: '2026', 'V04', 'V03' or 'V02' (MO)."""
    name = book_for(j, ASOF).parent.package.content.name
    return "2026" if "2026" in name else name[-3:]


_COUNTY = {}


def county_rule(j, rec):
    """the county states (MA NC NJ NY SC TX VA) rewrite SetFloodBaseRate: the listed counties / cities read the county
    table, every other location the all-other table (neither table has a county column). None elsewhere."""
    if (j, rec) not in _COUNTY:
        f = book_for(j, ASOF).state.package.content / "Rules" / f"{P}{rec}Rules.Rule.xml"
        t = f.read_text(encoding="utf-8-sig") if f.exists() else ""
        body = rule(t, "SetFloodBaseRate")
        tabs = sorted(set(re.findall(r'MatrixFromConstant="(FloodLossCost\w+)"', t)))
        if "ByCount" not in body or len(tabs) < 2:
            _COUNTY[(j, rec)] = None
        else:
            names = re.findall(r'FromDataDef="(?:\.\./)+(County|City)"[^>]*/>\s*<rul:Constant[^>]*>([^<]+)</rul:Constant>', body)
            _COUNTY[(j, rec)] = (names, next(x for x in tabs if "AllOther" not in x), next(x for x in tabs if "AllOther" in x))
    return _COUNTY[(j, rec)]


def loss_cost(j, rec, constr, zone, loc=None):
    if not constr or not zone:
        return D(0)
    cr = county_rule(j, rec)
    if cr is not None and loc is not None:
        names, by, other = cr
        listed = any(val(loc, f) == v for f, v in names)
        rs = rows(book_for(j, ASOF).state.package.content, by if listed else other) or []
        for x in rs:
            if x.get("CovType") == LC_ROW[rec] and x.get("Construction") == constr and x.get("FloodZone") == zone:
                return D(x["LossCost"])
        return D(0)
    return one(j, "FloodLossCost", "LossCost", CovType=LC_ROW[rec], Construction=constr, FloodZone=zone) or D(0)


def crs(j, node, rate):
    loc = anc(node, "Location")
    lr = loc_rec(loc)
    grade = val(lr, "CommunityRatingSystemCRSGrade") if lr is not None else None
    if lr is None or not grade:
        return rate, None
    f = SUB.get((LOCR, "CommunityRatingSystemFactor"), one(j, "CommunityRatingSystemFactor", "Factor", CommunityRatingSystemGrade=grade) or D(0))
    return r(rate * f, 3), f


def hand_prop(j, node, rec, parts=None):
    """the flood rate and premium of a Building / BPP / Special Class flood record."""
    parts = {} if parts is None else parts
    cp, par, loc = m.root(node), cov(node), anc(node, "Location")
    lr = loc_rec(loc)
    blk = val(node, "IncludedInBlkt")
    bid = d(node, "BlanketIDNum")
    dets = details(cp)
    flagged = next((x for x in dets if d(x, "UnitNumber") == bid and val(x, COV_FLAG[rec]) == "Yes"), None) if blk == "Yes" and bid > 0 else None
    loc_ded = (val(lr, "Deductible") if lr is not None else None) or ""
    # SetDeductible (IsNull-guarded, so a submitted one survives). Building: the location record's, always. Contents /
    # Special Class: blanketed -> the deductible of the detail with this BlanketIDNum AND its coverage flag "Yes", else
    # blank; unblanketed ("No") -> the location record's; anything else -> blank
    if rec == B or blk == "No" or edition(j) == "V02":
        ded = loc_ded                                  # V02 (MO): contents / Special Class take the location's too
    elif blk == "Yes" and bid > 0:
        ded = (val(flagged, "Deductible") or "") if flagged is not None else ""
    else:
        ded = ""
    ded = SUB.get((rec, "Deductible")) or ded
    # SetExcessOverMaxNFIPIndicatorToUse: blanketed with an id and ANY detail on the policy -> the flagged detail's
    # indicator, else "No"; otherwise a copy of the record's own
    if blk == "Yes" and bid > 0 and dets:
        excess = val(flagged, "ExcessOverMaxNFIPIndicator") if flagged is not None else "No"
    else:
        excess = val(node, "ExcessOverMaxNFIPIndicator")
    det = detail_for(node)                             # SetInsuranceToValuePercentageToUse: the detail with this id, no flag test
    fv = full_value(rec, node)
    if blk == "No":
        itv = r(d(node, "Limit") / fv, 4) if fv > 0 else D(0)
        touse = itv_touse(r(itv * 100, 2))
        # Location.SetFloodTotalPropertyValue runs only with FloodCovIndicator "Yes"
        tpv = (sum(full_value(rr, n) for rr in PROP for n in rc1.find(loc, P + rr) if val(n, "IncludedInBlkt") == "No")
               if val(loc, "FloodCovIndicator") == "Yes" else D(0))
    elif blk == "Yes" and bid > 0:
        touse = detail_itv(j, det, cp)[3] if det is not None else 0
        # SetTotalPropertyValue: blanketed, not excess -> every member with the same BlanketIDNum, detail or no detail;
        # V02 (MO) counts only the members at the record's own location (Structure LocUnitNumber = the location's UnitNumber)
        here = rc1.find(loc, P + "Structure") + rc1.find(loc, P + "SpecialClass") if edition(j) == "V02" else None
        tpv = (sum(full_value(rr, n) for rr in PROP for n in rc1.find(cp, P + rr)
                   if val(n, "IncludedInBlkt") == "Yes" and d(n, "BlanketIDNum") == bid
                   and (here is None or anc(n, "Location") is loc)) if excess == "No" else D(0))
    else:
        touse, tpv = 0, D(0)
    parts.update(ded=ded, excess=excess, touse=touse, tpv=tpv)
    if excess == "Yes":
        mx = one(j, "MaxNFIPCoverageAmount", "Amount", Coverage=NFIP_MAX[rec])
        if edition(j) == "V02":                        # MO: table 6 at the '500,000' row, whatever the deductible
            n, key = 6, "500,000"
        else:
            n, key = EXCESS_TABLE.get(ded), ded
        fac = banded(j, n, key, touse, fv) if n and fv > mx and 1 <= touse <= 100 else D(0)
    elif excess != "No":
        n, fac = None, D(0)                            # neither: SetFloodModificationFactor runs only on "No", the excess factor only on "Yes"
    else:
        n = MOD_TABLE.get(ded)
        fac = banded(j, n, ded, touse, tpv) if n and tpv > 0 and 1 <= touse <= 100 else D(0)
    fac = fac if fac is not None else D(0)
    if excess in ("Yes", "No"):
        fac = sub(rec, "FloodExcessFactor" if excess == "Yes" else "FloodModificationFactor", fac)
    # SC: the flood record's own ConstructionType; Building: ../../ (the Structure); BPP: ../../../../../../ (the Structure too)
    constr = val(node, "ConstructionType") if rec == SC else val(anc(node, "Structure"), "ConstructionTypeToUse")
    zone = val(lr, "FloodZone") if lr is not None else None
    base = sub(rec, "FloodBaseRate", loss_cost(j, rec, constr, zone, loc))
    agg = sub(rec, "AnnualAggregateFactor", agg_factor(j, node, rec))
    rate = sub(rec, "FloodRate", r(r(r(base * d(par, "LossCostMultiplier"), 3) * agg, 3) * fac, 3))
    adj, crsf = crs(j, node, rate)
    adj = sub(rec, "FloodAdjustedRate", adj)
    parts.update(table=n, factor=fac, base=base, agg=agg, rate=rate, crs=crsf, adjusted=adj)
    if val(node, "IncludedInBlkt") != "No":
        return D(0)
    return tail(adj * d(node, "Limit") / 100, cp)


def tail(x, cp, col=None):
    x = r(x, 0)
    for f in (d(cp, "PackageModFactor"), d(cp, "IRPMFactor"), d(cp, "CyberIncidentExclusionFactorFlood", "1"),
              col if col is not None else d(cp, "CyberIncidentExclusionCOLExcptnsFactorFlood", "1")):
        x = r(x * f, 0)
    return x


def busn_factor(j, node, tor):
    par = cov(node)
    return one(j, "BusnIncomeFactor", "Factor", CovTypeBusnIncome=val(par, "CovType"), TypeOfRisk=tor,
               CoinsuranceBusnIncome=val(node, "Coinsurance") or "") or D(0)


def hand_te(j, node, rec, parts=None):
    parts = {} if parts is None else parts
    cp, par, loc = m.root(node), cov(node), anc(node, "Location")
    lr = loc_rec(loc)
    det = detail_for(node)
    if det is not None:
        _, _, _, touse = detail_itv(j, det, cp)
        coins = ""
        if 0 < touse <= 125:
            for x in trows(j, "EQSubLimitPctToTimeElementCoinsurance"):
                if D(x["EQSubLimitPct_FromGreaterThan"]) < touse <= D(x["EQSubLimitPct_To"]):
                    coins = x["CoinsurancePct"]
        elif touse > 125:
            coins = "Greater than 125%"
    else:
        coins = val(par, "CoinsuranceToUse")
    covt, tor = val(par, "CovType"), val(par, "TypeOfRisk")
    ok_coins = coins not in (None, "", "Blanket Coinsurance Percentage Applies", "Not Applicable", "Greater than 125%")
    node_c = {"Coinsurance": coins}
    look = lambda t: one(j, "BusnIncomeFactor", "Factor", CovTypeBusnIncome=covt, TypeOfRisk=t, CoinsuranceBusnIncome=coins or "") or D(0)
    combos = {"Combined Manufacturing and Mercantile Operations": ("Manufacturing", "Mercantile and Non-manufacturing", "CombinedTypeOfRiskManufacturingPct", "CombinedTypeOfRiskMercantilePct"),
              "Combined Manufacturing and Rental Operations": ("Manufacturing", "Rental Properties", "CombinedTypeOfRiskManufacturingPct", "CombinedTypeOfRiskRentalPct"),
              "Combined Mercantile and Rental Operations": ("Mercantile and Non-manufacturing", "Rental Properties", "CombinedTypeOfRiskMercantilePct", "CombinedTypeOfRiskRentalPct"),
              "Combined Educational Institutes and Rental Operations": ("Mercantile and Non-manufacturing", "Rental Properties", "CombinedTypeOfRiskEducationalPct", "CombinedTypeOfRiskRentalPct")}
    tor_f = D(0)
    if covt not in ("Extra Expense Only", "", None, "Not Applicable") and ok_coins:
        if tor in combos:
            t1, t2, p1, p2 = combos[tor]
            tor_f = r(r(d(par, p1) / 100 * look(t1), 3) + r(d(par, p2) / 100 * look(t2), 3), 3)
        elif tor == "Educational Institutions":
            tor_f = look("Mercantile and Non-manufacturing")
        elif tor == "Seasonal Leases with Monthly Limit":
            tor_f = look("Rental Properties")
        elif tor not in ("Not Applicable", "", None):
            tor_f = look(tor)
    tor_f = sub(rec, "TypeOfRiskFactor", tor_f)
    if val(node, "IncludedInBlkt") == "Yes":
        bif = tor_f if (covt != "Extra Expense Only" and val(par, "MaxPeriod") != "Yes" and val(par, "MonthlyLimitOfIndemnity") == "Not Applicable") else D(1)
    elif val(par, "MaxPeriod") == "Yes":
        bif = d(par, "MaxPeriodOfIndemnityFactor")
    elif val(par, "MonthlyLimitOfIndemnity") != "Not Applicable":
        bif = d(par, "MonthlyLimitOfIndemnityFactor")
    elif covt == "Extra Expense Only":
        bif = d(par, "ExtraExpenseFactor")
    else:
        bif = tor_f
    zone = val(lr, "FloodZone") if lr is not None else None
    if rec == BI:
        st = anc(par, "Structure")
        special = val(par, "MaxPeriod") == "Yes" or val(par, "MonthlyLimitOfIndemnity") != "Not Applicable" or covt == "Extra Expense Only"
        if special and val(st, "BldgIncludedInOperationalUnit") == "Yes":
            base = highest_opunit_rate(j, loc)
            how = f"the location's operational-unit rate AS WRITTEN (intended reading: {highest_opunit_rate(j, loc, intended=True)})"
        else:
            base, how = loss_cost(j, rec, val(st, "ConstructionTypeToUse"), zone, loc), "own lookup"
    else:
        base, how = loss_cost(j, rec, val(node, "ConstructionType"), zone, loc), "own lookup (the flood record's construction)"
    bif = sub(rec, "BusinessIncomeFactor", bif)
    base = sub(rec, "FloodBaseRate", base)
    agg = sub(rec, "AnnualAggregateFactor", agg_factor(j, node, rec))
    rate = sub(rec, "FloodRate", r(r(base * d(par, "LossCostMultiplier"), 3) * agg, 3))
    adj = sub(rec, "FloodAdjustedRate", r(rate * bif, 3))
    parts.update(coins=coins, tor=tor_f, bif=bif, base=base, how=how, agg=agg, rate=rate, adjusted=adj)
    if val(node, "IncludedInBlkt") != "No":
        return D(0)
    return tail(adj * d(node, "Limit") / 100, cp, d(par, "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse", "1"))


def highest_opunit_rate(j, loc, intended=False):
    """Location.SetHighestBusnIncomeFloodBaseRate, AS WRITTEN: the rule first sets MaxCompareVariableFloodRateTemp to 0.0
    (it is blank), then computes max(0.0, each operational-unit building's r3(r3(OperationalUnitFloodBaseRate x LCM) x the
    location's CRS factor)) but stores it ONLY IF MaxCompareVariableFloodRateTemp is still blank, which it never is; the
    second pass copies a building's base rate where that product EQUALS the stored 0.0. So: 0 whenever the products are
    positive; with no CRS grade (factor 0.0) every product is 0 and the LAST operational-unit building's base rate wins.
    `intended=True` gives the reading the rule's names suggest (the highest building's base rate) for the ISO probe (OI-122)."""
    lr = loc_rec(loc)
    if lr is None or not val(lr, "FloodZone"):
        return D(0)
    crsf = d(lr, "CommunityRatingSystemFactor")
    cand = []
    for st in rc1.find(loc, P + "Structure"):
        if val(st, "BldgIncludedInOperationalUnit") != "Yes" or not val(st, "ConstructionTypeToUse"):
            continue
        base = loss_cost(j, B, val(st, "ConstructionTypeToUse"), val(lr, "FloodZone"), loc)
        cand.append((r(r(base * d(st, "LossCostMultiplier"), 3) * crsf, 3), base))
    if intended:
        return max(cand)[1] if cand else D(0)
    stored, out = D(0), D(0)
    for prod, base in cand:
        if prod == stored:
            out = base
    return out


def hand_blanket(j, det, parts=None):
    parts = {} if parts is None else parts
    cp = m.root(det)
    lv = level_values(j, det, cp)
    total = sum(lv.values())
    adj_total = D(0)
    for rec, n in members(cp, det):
        pr = {}
        (hand_prop if rec in PROP else hand_te)(j, n, rec, pr)
        fv = full_value(rec, n) if rec in PROP else bi_full100(n)
        adj_total += r(fv * pr["adjusted"], 0)
    avg = sub(BRD, "BlanketAverageRate", r(adj_total / total, 3) if total > 0 else D(0))
    parts.update(levels=lv, total=total, adjusted_total=adj_total, average=avg)
    return tail(avg * d(det, "Limit") / 100, cp)


def hand(j, node, rec, parts=None):
    if rec in PROP:
        return hand_prop(j, node, rec, parts)
    if rec in TE:
        return hand_te(j, node, rec, parts)
    if rec == BRD:
        return hand_blanket(j, node, parts)
    return f"no hand model for {rec}"


def hand_manual(node):
    """AK / FL: r0(r0(ManualPremium x package mod) x IRPM)."""
    cp = m.root(node)
    return r(r(d(node, "ManualPremium") * d(cp, "PackageModFactor"), 0) * d(cp, "IRPMFactor"), 0)


def predict(data, rec, j="OR"):
    body = m.cen.set_premium(RULES[rec])
    out = []
    for node in rc1.find(data, P + rec):
        try:
            ev = r16.hand(body, node)
        except Exception:
            ev = None                                  # a shape the independent evaluator does not cover (If on IncludedInBlkt)
        try:
            hv = hand(j, node, rec)
        except Exception as exc:
            hv = f"hand error {type(exc).__name__}: {exc}"
        out.append((node, hv, ev, val(node, "Premium")))
    return out


# ------------------------------------------------------------------ trees

def flood_tree(j="OR", ded="10,000", zone="A", crs_grade="5", full=("150000", "120000", "130000"), recs=None,
               lr_over=None, st_over=None, bi_over=None, scbi_over=None, keep=PROP + TE):
    """the portable policy (192_) with flood on every record: location record, building / contents / special class
    full values, and each flood record at 100,000 unblanketed (SC / SCBI with their own construction)."""
    sub = m.portable(j, "Special")
    at = m.at(sub)
    loc = at[P + "Location"]
    loc["FloodCovIndicator"] = "Yes"
    lrec = {"Deductible": ded, "FloodZone": zone}
    if crs_grade:
        lrec["CommunityRatingSystemCRSGrade"] = crs_grade
    lrec.update(lr_over or {})
    loc[P + LOCR + "Table"] = {P + LOCR: [lrec]}
    at[P + "Structure"]["FullBldgValue"], at[P + "PersonalProperty"]["FullPrsnlPropValue"], at[P + "SpecialClass"]["FullSpecialClassValue"] = full
    at[P + "Structure"].update(st_over or {})
    at[P + "BusinessIncome"].update(bi_over or {})
    at[P + "SpecialClassBusnIncome"].update(scbi_over or {})
    for rec in keep:
        f = {"Limit": "100000", "IncludedInBlkt": "No", "ExcessOverMaxNFIPIndicator": "No"}
        if rec in (SC, SCBI):
            f["ConstructionType"] = "Frame"
        f.update((recs or {}).get(rec, {}))
        m.put(sub, rec, f, j)
    return sub


def add_blanket(sub, dets, member_ids):
    """a flood blanket at the policy: FloodCovEndtBlktIndicator Yes and the given details; member_ids {rec: id}."""
    pol = sub[P + "Table"][P][0]
    pol["FloodCovEndtBlktIndicator"] = "Yes"
    pol[P + BR + "Table"] = {P + BR: [{P + BRD + "Table": {P + BRD: dets}}]}
    at = m.at(sub)
    for rec, bid in member_ids.items():
        parent = {B: "Structure", PP: "PersonalProperty", SC: "SpecialClass", BI: "BusinessIncome", SCBI: "SpecialClassBusnIncome"}[rec]
        for f in at[P + parent][P + rec + "Table"][P + rec]:
            f.update({"IncludedInBlkt": "Yes", "BlanketIDNum": str(bid)})
    return sub


def two_buildings(sub, second):
    """a second building at the location (a copy of the first, its flood record included), updated with `second`."""
    loc = m.at(sub)[P + "Location"]
    sts = loc[P + "StructureTable"][P + "Structure"]
    st2 = copy.deepcopy(sts[0])
    st2.update(second)
    st2["UnitNumber"] = "2"
    sts[0].setdefault("UnitNumber", "1")
    sts.append(st2)
    return sub


def trees():
    big = ("2000000", "1500000", "1000000")
    big_lim = {B: {"Limit": "1000000"}, PP: {"Limit": "1000000"}, SC: {"Limit": "800000"}}
    t = {
        "T1": ("deductible 10,000 (table 3), zone A, CRS grade 5, full 150k / 120k / 130k, limits 100k", lambda: flood_tree()),
        "T2": ("no CRS grade: the adjusted rate is the rate", lambda: flood_tree(crs_grade=None)),
        "T3": ("deductible 500 (table 1), zone X", lambda: flood_tree(ded="500", zone="X")),
        "T4": ("deductible 2,500 (table 2), zone X500", lambda: flood_tree(ded="2,500", zone="X500")),
        "T5": ("deductible 50,000 (table 4), zone D, large values", lambda: flood_tree(ded="50,000", zone="D", full=big, recs=big_lim)),
        "T6": ("deductible 100,000 (table 5), large values", lambda: flood_tree(ded="100,000", full=big, recs=big_lim)),
        "T7": ("deductible 500,000 (table 6), large values", lambda: flood_tree(ded="500,000", full=big, recs=big_lim)),
        "T8": ("deductible 1,000,000 (table 7), large values", lambda: flood_tree(ded="1,000,000", full=big, recs=big_lim)),
        "T9": ("ITV at the band edges: building 75,000 / 150,000 = 50%, contents 120,000 / 120,000 = 100%, SC 140,000 / 130,000 > 100%",
               lambda: flood_tree(recs={B: {"Limit": "75000"}, PP: {"Limit": "120000"}, SC: {"Limit": "140000"}})),
        "T10": ("annual aggregate = limit on every record (0.999)",
                lambda: flood_tree(recs={k: {"AnnualAggregateLimit": "100000"} for k in PROP + TE})),
        "T11": ("excess over NFIP, deductible 750,000: all three above the 500,000 maximum, ITV 50%, table 6 keyed on each own full "
                "value (4,000,000 / 3,000,000 / 2,500,000: three different full-value bands)",
                lambda: flood_tree(ded="750,000", full=("4000000", "3000000", "2500000"),
                                   recs={B: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "2000000"},
                                         PP: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "1500000"},
                                         SC: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "1250000"}})),
        "T12": ("excess over NFIP, deductible 1,000,000 (table 7); contents 400,000 at ITV 75% but UNDER the NFIP maximum: factor 0",
                lambda: flood_tree(ded="1,000,000", full=("4000000", "400000", "2500000"),
                                   recs={B: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "2000000"},
                                         PP: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "300000"},
                                         SC: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "1250000"}})),
        "T13": ("excess over NFIP with deductible 100,000: no excess table, factor 0",
                lambda: flood_tree(ded="100,000", full=big, recs={k: {"ExcessOverMaxNFIPIndicator": "Yes", **big_lim.get(k, {})} for k in PROP})),
        "T14": ("BI combined manufacturing 60% / mercantile 40%; SCBI Without Extra Expense, rental",
                lambda: flood_tree(bi_over={"TypeOfRisk": "Combined Manufacturing and Mercantile Operations", "CombinedTypeOfRiskManufacturingPct": "60",
                                            "CombinedTypeOfRiskMercantilePct": "40"},
                                   scbi_over={"CovType": "Business Income Without Extra Expense", "TypeOfRisk": "Rental Properties"})),
        "T15": ("BI maximum period of indemnity; SCBI Extra Expense Only",
                lambda: flood_tree(bi_over={"MaxPeriod": "Yes"}, scbi_over={"CovType": "Extra Expense Only", "Coinsurance": "No Coinsurance",
                                                                            "ExtraExpenseLimitOnLossPayment": "40%,80%,100%"})),
        "T16": ("operational unit, CRS grade 5: Frame and Joisted Masonry buildings, BI with maximum period on each; as written the "
                "highest-rate rule never stores its maximum, so BI's base is 0 (intended: the Frame building's 0.637) (OI-122)",
                lambda: two_buildings(flood_tree(st_over={"BldgIncludedInOperationalUnit": "Yes"}, bi_over={"MaxPeriod": "Yes"}),
                                      {"ConstructionType": JM, "BldgIncludedInOperationalUnit": "Yes"})),
        "T16b": ("the same with no CRS grade: the CRS factor is 0.0, every comparison equals the stored 0.0, and the LAST "
                 "operational-unit building's base rate (Joisted Masonry 0.472) is copied (intended: 0.637) (OI-122)",
                 lambda: two_buildings(flood_tree(crs_grade=None, st_over={"BldgIncludedInOperationalUnit": "Yes"}, bi_over={"MaxPeriod": "Yes"}),
                                       {"ConstructionType": JM, "BldgIncludedInOperationalUnit": "Yes"})),
        "T17": ("Joisted Masonry building; SC flood Frame vs SCBI flood Masonry Non-Combustible (each reads its own)",
                lambda: flood_tree(st_over={"ConstructionType": JM}, recs={SCBI: {"ConstructionType": "Masonry Non-Combustible"}})),
    }
    return t


def blanket_trees():
    det = lambda unit, lim, **kw: {"UnitNumber": str(unit), "Limit": lim, "ExcessOverMaxNFIPIndicator": "No", "Deductible": "10,000",
                                   "BldgCov": "No", "PrsnlPropCov": "No", "SpecialClassCov": "No", "BusnIncomeWithExtraExpenseCov": "No",
                                   "BusnIncomeWithoutExtraExpenseCov": "No", "ExtraExpenseCov": "No", **kw}
    return {
        "K1": ("blanket of two risks (building + contents), limit 200,000",
               lambda: add_blanket(flood_tree(), [det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes")], {B: 1, PP: 1})),
        "K2": ("blanket of three risks (+ special class), limit 300,000 = AggLimit (0.999)",
               lambda: add_blanket(flood_tree(), [det(1, "300000", AggLimit="300000", BldgCov="Yes", PrsnlPropCov="Yes", SpecialClassCov="Yes")],
                                   {B: 1, PP: 1, SC: 1})),
        "K3": ("blanket with business income (annual net income 200,000), limit 400,000",
               lambda: add_blanket(flood_tree(recs={BI: {"AnnualNetIncome": "200000"}}),
                                   [det(1, "400000", BldgCov="Yes", PrsnlPropCov="Yes", BusnIncomeWithExtraExpenseCov="Yes")], {B: 1, PP: 1, BI: 1})),
        "K4": ("excess blanket, deductible 750,000, limit 2,000,000: the 4,000,000 building counts, the 400,000 contents do not "
               "(under the NFIP maximum), so ITV = 2,000,000 / 4,000,000 = 50%",
               lambda: add_blanket(flood_tree(ded="750,000", full=("4000000", "400000", "2500000"),
                                              recs={B: {"Limit": "2000000"}, PP: {"Limit": "400000"}}),
                                   [det(1, "2000000", ExcessOverMaxNFIPIndicator="Yes", Deductible="750,000", BldgCov="Yes", PrsnlPropCov="Yes")],
                                   {B: 1, PP: 1})),
    }


# ------------------------------------------------------------------ C25-02 / C25-03: the stored evidence

def evidence():
    progress("C25-02 / C25-03  THE STORED EVIDENCE (every stored ISO response re-rated)")
    index = rep.fixture_index()
    paths = sorted(rep.RES.glob("chunk13_fixture_*_response.json"))
    n = same_all = 0
    flood_pol = []
    for i, rpath in enumerate(paths, 1):
        stem = rpath.name[len("chunk13_fixture_"):-len("_response.json")]
        if i == 1 or i % 50 == 0 or i == len(paths):
            progress(f"  [{i}/{len(paths)}] {stem}")
        fx = index.get(stem)
        if fx is None:
            continue
        dd = json.loads(fx.read_text(encoding="utf-8-sig"))
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": dd["SchemeKeys"]["ProductName"], "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": dd["CommercialProperty"]}}
        data, ip = cmp.rate(req)
        resp = json.loads(rpath.read_text(encoding="utf-8"))
        iso, ours = rep.iso_prem(resp), rep.our_prem(data)
        n += 1
        same_all += all(cmp.same(v, ours.get(k)) for k, v in iso.items())
        if any(rc1.find(data, P + rec) for rec in FAMILY):
            flood_pol.append((stem, data, iso, ours))
    print(f"    {n} stored responses re-rated; every premium equal to ISO on {same_all}")
    check(same_all == n, "all stored policies re-rate unchanged (every premium ISO returned equals ours)")
    print(f"    stored policies with any flood record: {[s for s, *_ in flood_pol]}")
    check([s for s, *_ in flood_pol] == [STC], f"only {STC} carries flood")
    if not flood_pol:
        return
    stem, data, iso, ours = flood_pol[0]
    j = data.tag[-2:]
    print(f"    {stem}: state {j} (AK files no flood loss cost; its own SetPremium prices the manual premium)")
    for rec in (B, PP, BI):
        for node in rc1.find(data, P + rec):
            isov = [v for k, v in iso.items() if f"/{P}{rec}[" in k and k.endswith("/Premium")]
            hv = hand_manual(node)
            ok = m.same(hv, val(node, "Premium")) and len(isov) == 1 and cmp.same(isov[0], val(node, "Premium"))
            check(ok, f"{rec[len(FL):] or 'Building'}: ManualPremium {val(node, 'ManualPremium')} x pkg {val(m.root(node), 'PackageModFactor')} "
                      f"x IRPM {val(m.root(node), 'IRPMFactor')}: hand {hv} = engine {val(node, 'Premium')} = ISO {isov}")
            computed = [f for f in ("FloodBaseRate", "FloodRate", "FloodAdjustedRate", "FloodModificationFactor", "SublineFloodCoverage") if val(node, f)]
            check(not computed, f"  AK empties ErcSetRatesAndFactors and the stat codes: no flood rate is computed ({computed or 'none'})")
    lr = rc1.find(data, P + LOCR)[0]
    lv = {f: val(lr, f) for f in ("Deductible", "FloodEffDate", "CommunityRatingSystemFactor", "DeductibleInt", "MaxNFIPBuildingCoverageAmount", "Premium")}
    print(f"    location record: {lv}")
    check(lv["CommunityRatingSystemFactor"] is None and lv["DeductibleInt"] is None and lv["MaxNFIPBuildingCoverageAmount"] is None,
          "the location record: AK empties ProcessCall, so no CRS factor, deductible number or NFIP maximum is written")
    loc = anc(lr, "Location")
    st = rc1.find(loc, P + "Structure")[0]
    akloc = (book_for(j, ASOF).state.package.content / "Rules" / f"{P}LocationRules.Rule.xml").read_text(encoding="utf-8-sig")
    akst = (book_for(j, ASOF).state.package.content / "Rules" / f"{P}StructureRules.Rule.xml").read_text(encoding="utf-8-sig")
    emptied = [x for t, x in ((akloc, "SetFloodTotalPropertyValue"), (akloc, "SetHighestBusnIncomeFloodBaseRate"), (akst, "SetOperationalUnitFloodBaseRate"))
               if "<rul:Sequence />" in rule(t, x)]
    check(len(emptied) == 3 and val(loc, "FloodTotalPropertyValue") is None and val(loc, "HighestBusnIncomeFloodBaseRate") is None
          and val(st, "OperationalUnitFloodBaseRate") is None,
          f"AK also empties the built touchpoints {emptied}: no FloodTotalPropertyValue, highest BI flood rate or operational-unit rate is written "
          f"({val(loc, 'FloodTotalPropertyValue')}, {val(loc, 'HighestBusnIncomeFloodBaseRate')}, {val(st, 'OperationalUnitFloodBaseRate')})")


# ------------------------------------------------------------------ C25-05 / C25-06: trees by hand

def show(parts):
    keep = ("ded", "excess", "touse", "tpv", "table", "factor", "coins", "tor", "bif", "base", "how", "agg", "rate", "crs", "adjusted",
            "levels", "total", "adjusted_total", "average")
    return " ".join(f"{k}={parts[k]}" for k in keep if k in parts and parts[k] not in (None, ""))


def engine_parts(node, rec):
    if rec in PROP:
        fs = ("Deductible", "InsuranceToValuePercentageToUse", "TotalPropertyValue", "FloodModificationFactor", "FloodExcessFactor",
              "FloodBaseRate", "AnnualAggregateFactor", "FloodRate", "FloodAdjustedRate")
    elif rec in TE:
        fs = ("Coinsurance", "TypeOfRiskFactor", "BusinessIncomeFactor", "FloodBaseRate", "AnnualAggregateFactor", "FloodRate", "FloodAdjustedRate")
    else:
        fs = ("BuildingLevel100PctValue", "PersonalPropLevel100PctValue", "SpecialClassLevel100PctValue", "BusinessIncLevel100PctValue",
              "TotalFull100PctValue", "TotalAdjustedFull100PctValue", "InsuranceToValuePercentageToUse", "BlanketAverageRate")
    return " ".join(f"{f}={val(node, f)}" for f in fs)


def parts_agree(rec, node, pr):
    """the hand's intermediate values against the engine's fields (the premium alone can hide two offsetting errors)."""
    if rec in PROP:
        pairs = [("touse", "InsuranceToValuePercentageToUse"), ("base", "FloodBaseRate"), ("agg", "AnnualAggregateFactor"),
                 ("rate", "FloodRate"), ("adjusted", "FloodAdjustedRate")]
        fac = "FloodExcessFactor" if pr.get("excess") == "Yes" else "FloodModificationFactor"
        pairs.append(("factor", fac))
        if val(node, "IncludedInBlkt") == "No" or pr.get("excess") == "No":
            pairs.append(("tpv", "TotalPropertyValue"))
    elif rec in TE:
        pairs = [("tor", "TypeOfRiskFactor"), ("bif", "BusinessIncomeFactor"), ("base", "FloodBaseRate"), ("agg", "AnnualAggregateFactor"),
                 ("rate", "FloodRate"), ("adjusted", "FloodAdjustedRate")]
        if (val(node, "Coinsurance") or "") != (pr.get("coins") or ""):
            return [("coins", pr.get("coins"), val(node, "Coinsurance"))]
    else:
        pairs = [("total", "TotalFull100PctValue"), ("adjusted_total", "TotalAdjustedFull100PctValue"), ("average", "BlanketAverageRate")]
    return [(k, pr.get(k), val(node, f)) for k, f in pairs if not m.same(pr.get(k), val(node, f) or "0")]


def run_trees(tdict, label):
    progress(label)
    results = {}
    for tid, (desc, build) in tdict.items():
        data, ip, err = m.rated(build(), "OR")
        if err:
            check(False, f"{tid} {desc}: engine raised {err}")
            continue
        results[tid] = data
        print(f"  {tid} {desc}:")
        bad = []
        cnt = 0
        for rec in PREMIUM_RECS:
            for node, hv, ev, e in predict(data, rec):
                pr = {}
                hand(data.tag[-2:], node, rec, pr)
                diff = parts_agree(rec, node, pr)
                ok = m.same(hv, e) and (ev is None or m.same(ev, e)) and not diff
                cnt += 1
                name = rec[len(FL):] or "Building"
                print(f"      {'ok  ' if ok else 'FAIL'} {name[:30]:30s} hand {hv} evaluator {ev} engine {e}   {show(pr)}")
                if not ok:
                    print(f"           engine: {engine_parts(node, rec)}   differing: {diff}")
                    bad.append(rec)
        check(not bad and cnt, f"{tid}: hand = evaluator = engine on every record and every intermediate value ({cnt} records)")
    return results


# ------------------------------------------------------------------ C25-03 / C25-04: touchpoints and attach map

def touchpoints(res):
    progress("C25-03  THE BUILT TOUCHPOINTS")
    data = res["T1"]
    loc = rc1.find(data, P + "Location")[0]
    want = sum(full_value(rec, n) for rec in PROP for n in rc1.find(loc, P + rec) if val(n, "IncludedInBlkt") == "No")
    check(m.same(val(loc, "FloodTotalPropertyValue"), want),
          f"Location writes FloodTotalPropertyValue = the unblanketed building + contents + special class full values ({val(loc, 'FloodTotalPropertyValue')} = {want})")
    k1 = rc1.find(blanket_cache["K1"], P + "Location")[0]
    want = sum(full_value(rec, n) for rec in PROP for n in rc1.find(k1, P + rec) if val(n, "IncludedInBlkt") == "No")
    check(m.same(val(k1, "FloodTotalPropertyValue"), want), f"... and leaves the blanketed ones out (K1: {val(k1, 'FloodTotalPropertyValue')} = {want}, the SC only)")
    for tid, want_h, want_intended in (("T16", "0", "0.637"), ("T16b", "0.472", "0.637")):
        dd = res.get(tid)
        if dd is None:
            check(False, f"{tid} did not rate")
            continue
        loc = rc1.find(dd, P + "Location")[0]
        sts = rc1.find(loc, P + "Structure")
        ou = [(val(s, "ConstructionTypeToUse"), val(s, "OperationalUnitFloodBaseRate")) for s in sts]
        want = [(c, str(loss_cost("OR", B, c, "A"))) for c, _ in ou]
        check(len(ou) == 2 and all(c for c, _ in ou) and all(m.same(a[1], b[1]) for a, b in zip(ou, want)),
              f"{tid}: Structure writes OperationalUnitFloodBaseRate from its own loss-cost lookup on each building in the unit {ou}")
        hb = val(loc, "HighestBusnIncomeFloodBaseRate")
        check(m.same(hb, highest_opunit_rate("OR", loc)) and m.same(hb, want_h),
              f"{tid}: Location writes HighestBusnIncomeFloodBaseRate = {hb} as written (MaxCompareVariableFloodRateTemp stays "
              f"{val(loc, 'MaxCompareVariableFloodRateTemp')}); the intended reading gives {want_intended} (OI-122, ISO probe in C25-10)")
        bis = [(val(anc(n, "Structure"), "ConstructionTypeToUse"), val(n, "FloodBaseRate")) for n in rc1.find(dd, P + BI)]
        check(bis and all(m.same(x, want_h) for _, x in bis), f"{tid}: BI with maximum period in the unit copies it on both buildings {bis}")
    t1 = rc1.find(data, P + "Structure")[0]
    check(val(t1, "OperationalUnitFloodBaseRate") is None, "and writes nothing on a building outside an operational unit (T1)")
    cp = m.root(t1)
    cy = {f: val(cp, f) for f in ("CyberIncidentExclusionFactorFlood", "CyberIncidentExclusionCOLExcptnsFactorFlood",
                                  "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFlood")}
    bi = rc1.find(data, P + "BusinessIncome")[0]
    cy["BI ...BusnIncomeFloodToUse"] = val(bi, "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse")
    print(f"    the main ruleset's flood cyber factors and BI's ...ToUse copy (no cyber exclusion on the policy): {cy}")
    check(all(v is not None for v in cy.values()), "the main ruleset writes the flood cyber factors and BI its ...BusnIncomeFloodToUse (moved in RC-3, C25-17)")
    code = val(cp, "FloodAttachmentIndicatorCode")
    print(f"    policy FloodAttachmentIndicatorCode = {code}")
    check(code is not None, "the main ruleset writes FloodAttachmentIndicatorCode (a stat code)")
    for rec, parent in ((B, "Structure"), (PP, "PersonalProperty"), (SC, "SpecialClass"), (BI, "BusinessIncome"), (SCBI, "SpecialClassBusnIncome")):
        n = rc1.find(data, P + rec)
        check(n and val(n[0], "FloodRate") is not None, f"{parent} runs its flood records' ProcessCall (SetInitializeFloodRating...): {rec[len(FL):] or 'Building'} has a FloodRate")
    progress("C25-03  STATE REWRITES OF THE TOUCHPOINT RULES (46 states)")
    trail = {"Structure": ["SetInitializeFloodRatingBuilding", "SetOperationalUnitFloodBaseRate", "LookupFloodLossCost"],
             "Location": ["SetFloodRating", "SetFloodTotalPropertyValue", "SetInitializeFloodRatingLocation", "SetHighestBusnIncomeFloodBaseRate",
                          "AttachFormCommercialPropertyFloodCovEndtLocation", "LookupFloodLossCost"],
             "PersonalProperty": ["SetInitializeFloodRatingPersonalProperty"], "SpecialClass": ["SetInitializeFloodRatingSpecialClass"],
             "BusinessIncome": ["SetInitializeFloodRatingBusinessIncome", "SetCyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse"],
             "SpecialClassBusnIncome": ["SetInitializeFloodRatingSpecialClassBusinessIncome", "SetCyberIncidentExclusionCOLExcptnsFactorBusnIncomeFloodToUse"],
             "": ["AttachFormFloodCovEndtBlanketRating", "SetCyberIncidentExclusionFactorFlood", "SetCyberIncidentExclusionCOLExcptnsFactorFlood",
                  "SetCyberIncidentExclusionCOLExcptnsFactorBusnIncomeFlood", "SetFloodAttachmentIndicatorCode", "ErcSetFloodBlanketLimit"]}
    found = {}
    for j in s18.STATES:
        pk = book_for(j, ASOF).state.package.content
        for f, names in trail.items():
            p = pk / "Rules" / f"{P}{f}Rules.Rule.xml"
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8-sig")
            hit = [nm for nm in names if f'Rule Name="{nm}"' in t]
            if hit:
                found.setdefault(f or "main ruleset", {})[j] = hit
    for f, js in found.items():
        print(f"    {f:24s} " + "; ".join(f"{j}: {','.join(h)}" for j, h in sorted(js.items())))
    states = sorted({j for js in found.values() for j in js})
    print(f"    {len(states)} states rewrite a touchpoint rule: {states}")
    check(bool(states), "the touchpoint rewrites are listed per rule and state (each priced in RC-4)")


blanket_cache = {}


def attach_map(res):
    progress("C25-04  ATTACH MAP, SWITCHES AND BLANK DEFAULTS")
    data = res["T1"]
    loc = rc1.find(data, P + "Location")[0]
    check(len(rc1.find(loc, P + LOCR)) == 1, "the location record (Flood Coverage General Information) is kept with FloodCovIndicator Yes")
    sub = flood_tree()
    m.at(sub)[P + "Location"]["FloodCovIndicator"] = "No"
    d0, _, err = m.rated(sub, "OR")
    left = {rec: [val(n, "Premium") for n in rc1.find(d0, P + rec)] for rec in (LOCR,) + PROP + TE} if err is None else err
    print(f"    FloodCovIndicator No: {left}")
    check(err is None and not left[LOCR], "FloodCovIndicator No removes the location record")
    sub = flood_tree()
    m.at(sub)[P + "Location"].pop(P + LOCR + "Table")
    d1, _, err = m.rated(sub, "OR")
    lr = rc1.find(d1, P + LOCR) if err is None else []
    prem = {rec[len(FL):] or "Building": [val(n, "Premium") for n in rc1.find(d1, P + rec)] for rec in PROP + TE} if err is None else err
    print(f"    FloodCovIndicator Yes, no location record submitted: attached {len(lr)}, premiums {prem}")
    check(err is None and len(lr) == 1, "FloodCovIndicator Yes with no location record: the Location attaches an empty one (no deductible, no zone)")
    check(err is None and all(m.same(p, 0) for v in prem.values() for p in v),
          "with it empty every flood record prices $0 (no zone: base rate 0; no deductible: no table)")
    kb = blanket_cache["K1"]
    check(len(rc1.find(kb, P + BR)) == 1, "FloodCovEndtBlktIndicator Yes keeps the policy's blanket rating record")
    sub = add_blanket(flood_tree(), [{"UnitNumber": "1", "Limit": "200000", "BldgCov": "Yes", "PrsnlPropCov": "Yes", "ExcessOverMaxNFIPIndicator": "No"}], {B: 1, PP: 1})
    sub[P + "Table"][P][0]["FloodCovEndtBlktIndicator"] = "No"
    d2, _, err = m.rated(sub, "OR")
    check(err is None and not rc1.find(d2, P + BR), "FloodCovEndtBlktIndicator No removes it (and its details)")
    if err is None:
        prem = {rec[len(FL):] or "Building": [val(n, "Premium") for n in rc1.find(d2, P + rec)] for rec in (B, PP)}
        print(f"    ... the members, still IncludedInBlkt Yes, price {prem}")
        check(all(m.same(p, 0) for v in prem.values() for p in v), "a member left IncludedInBlkt Yes with no blanket prices $0 (the premium rule needs 'No')")
    progress("C25-04  BLANK INPUTS")
    cases = {
        "blank zone": (lambda: flood_tree(zone=""), "base rate 0 -> $0"),
        "blank deductible": (lambda: flood_tree(ded=""), "no rate-modification table -> factor 0 -> $0 (property records); BI / SCBI still price"),
        "blank full building value": (lambda: flood_tree(st_over={"FullBldgValue": ""}), "building ITV 0 -> factor 0 -> $0; building drops out of TPV"),
        "blank IncludedInBlkt on the building": (lambda: flood_tree(recs={B: {"IncludedInBlkt": ""}}), "premium rule needs 'No' -> $0"),
        "blank ExcessOverMaxNFIPIndicator": (lambda: flood_tree(recs={k: {"ExcessOverMaxNFIPIndicator": ""} for k in PROP}),
                                             "neither excess nor primary -> both factors 0 -> $0"),
        "blank SC flood construction": (lambda: flood_tree(recs={SC: {"ConstructionType": ""}, SCBI: {"ConstructionType": ""}}),
                                        "Special Class / SCBI read their flood record's construction -> base 0 -> $0"),
    }
    for name, (build, why) in cases.items():
        data, _, err = m.rated(build(), "OR")
        if err:
            check(False, f"{name}: engine raised {err}")
            continue
        bad, out = [], []
        for rec in PREMIUM_RECS:
            for node, hv, ev, e in predict(data, rec):
                out.append(f"{rec[len(FL):] or 'Building'} {e}")
                if not m.same(hv, e):
                    bad.append((rec, hv, e))
        check(not bad, f"{name}: hand = engine on every record ({why}): {', '.join(out)} {bad or ''}")


# ------------------------------------------------------------------ C25-07: tables

TABLES = ["AdditionalFloodConstructionCode", "AllOtherConstructionStatCode", "AllOtherDeductibleStatCode", "AnnualAggregateFactor", "BusnIncomeFactor",
          "CommunityRatingSystemFactor", "DeductibleNumberConversion", "EQSubLimitPctToTimeElementCoinsurance",
          "FloodBlanketRatingIdentificationBlanketCode", "FloodBlanketRatingIdentificationCode", "FloodCommunityRatingSystemClassCode",
          "FloodFloorOfInterestCode", "FloodLossCost", "FloodNumberOfStoriesCode", "FloodRatingIdentificationBlanketCode", "FloodRatingIdentificationCode",
          "MaxNFIPCoverageAmount", "NFIPFloodZoneCode"] + [f"PropertyRateModificationFactors{i}" for i in range(1, 8)] + \
         ["SublineFloodCoverageWithNFIP", "SublineFloodCoverageWithoutNFIP"]
COUNTY = ("MA", "NC", "NJ", "NY", "SC", "TX", "VA")


def tables():
    progress("C25-07  TABLES AND LITERALS")
    check(len(TABLES) == 27, f"the census's 27 tables ({len(TABLES)})")
    for name in TABLES:
        cw = rows(CW, name)
        filed = {}
        for j in s18.STATES:
            rs = rows(book_for(j, ASOF).state.package.content, name)
            if rs:
                filed[j] = len(rs)
        print(f"    {name:44s} CW {len(cw) if cw is not None else 'absent':>5}  states {len(filed):2d} {'' if len(filed) > 8 else filed}")
    check(rows(CW, "FloodLossCost") == [], "the countrywide FloodLossCost is header-only")
    lc = [j for j in s18.STATES if rows(book_for(j, ASOF).state.package.content, "FloodLossCost")]
    check(len(lc) == 37 and not set(lc) & {"AK", "FL"} and not set(lc) & set(COUNTY),
          f"37 states file FloodLossCost; none of AK FL or the 7 county states ({len(lc)})")
    progress("C25-07  WHAT THE PRODUCTION RULES READ: zone / floor / stories")
    prem_rules = {n: "".join(rule(RULES[n], x) for x in ("ErcSetRatesAndFactors", "SetFloodModificationFactor", "SetFloodExcessFactor",
                                                         "SetFloodBaseRate", "SetFloodRate", "SetFloodAdjustedRate", "SetPremium",
                                                         "SetTotalPropertyValue", "SetInsuranceToValue")) for n in PROP + TE}
    stat_only = {f: [n[len(FL):] or "Building" for n, t in prem_rules.items() if f in t] for f in ("FloorLevel", "NumberOfStories", "NFIPFloodZone")}
    print(f"    rate rules reading FloorLevel / NumberOfStories / NFIPFloodZone: {stat_only}")
    check(not any(stat_only.values()),
          "floor of interest, number of stories and the NFIP zone feed stat codes only; the rate reads FloodZone (the loss-cost key), not "
          "the task list's 'seven rate-modification tables (flood zone, floor, stories)'")
    progress("C25-07  THE SEVEN RATE-MODIFICATION TABLES: deductibles, ITV bands, TPV bands")
    for i in range(1, 8):
        rs = rows(CW, f"PropertyRateModificationFactors{i}")
        deds = sorted({x["Deductible"] for x in rs}, key=lambda s: int(s.replace(",", "")))
        itv = sorted({(int(D(x["InsuranceToValueLevelPercentage_From"])), int(D(x["InsuranceToValueLevelPercentage_ToLessThan"]))) for x in rs})
        tpv = sorted({(int(x["TotalPropertyValue_From"]), int(x["TotalPropertyValue_ToLessThan"])) for x in rs})
        mine = sorted(k for k, v in MOD_TABLE.items() if v == i)
        per = {dd: sorted({int(x["TotalPropertyValue_From"]) for x in rs if x["Deductible"] == dd}) for dd in deds}
        zeros = sum(1 for x in rs if D(x["Factor_From"]) == 0)
        print(f"    table {i}: ITV bands {itv[0]}..{itv[-1]} ({len(itv)}); TPV bands by deductible {per}; rows filing factor 0: {zeros}")
        check(set(deds) == set(mine), f"table {i} holds exactly the deductibles SetFloodModificationFactor sends it ({mine})")
        gaps = [(a, b) for (a, b), (c, _) in zip(itv, itv[1:]) if b != c]
        check(itv[0][0] == 1 and itv[-1][1] >= 101 and not gaps, f"table {i}: ITV bands contiguous from 1 to {itv[-1][1]} (no gap)")
    zero_from, not_mono = {}, []
    for i in range(1, 8):
        for x in rows(CW, f"PropertyRateModificationFactors{i}"):
            key = (i, x["Deductible"], int(x["TotalPropertyValue_From"]))
            itv0 = int(D(x["InsuranceToValueLevelPercentage_From"]))
            if D(x["Factor_From"]) == 0:
                zero_from[key] = min(zero_from.get(key, 10 ** 9), itv0)
        for x in rows(CW, f"PropertyRateModificationFactors{i}"):
            key = (i, x["Deductible"], int(x["TotalPropertyValue_From"]))
            if key in zero_from and int(D(x["InsuranceToValueLevelPercentage_From"])) >= zero_from[key] and D(x["Factor_From"]) != 0:
                not_mono.append(key)
    print("    filed zero factors (table, deductible, band from) -> from ITV%: " + "; ".join(f"{k}: {v}" for k, v in sorted(zero_from.items())))
    check(zero_from and not not_mono and {k[0] for k in zero_from} <= {5, 6, 7},
          f"tables 5-7 file factor 0 in {len(zero_from)} (deductible, value-band) cells from some ITV upward and never non-zero again above it "
          "(the deductible near the insured value): flood prices $0 there by the table, not by a missing row; T11 / K4 avoid them")
    t6 = rows(CW, "PropertyRateModificationFactors6")
    check({x["Deductible"] for x in t6} >= {"750,000"} and {x["Deductible"] for x in rows(CW, "PropertyRateModificationFactors7")} == {"1,000,000"},
          "the excess factor reuses tables 6 (750,000) and 7 (1,000,000), keyed on the full value in place of TPV")
    progress("C25-07  THE COUNTY STATES AND THEIR FALLBACK")
    for j in COUNTY:
        pk = book_for(j, ASOF).state.package.content
        t = (pk / "Rules" / f"{P}{B}Rules.Rule.xml").read_text(encoding="utf-8-sig")
        tabs = sorted(set(re.findall(r'MatrixFromConstant="(FloodLossCost\w*)"', t)))
        counties = re.findall(r'FromDataDef="\.\./\.\./\.\./\.\./(?:County|City)"[^>]*/>\s*<rul:Constant[^>]*>([^<]+)</rul:Constant>', rule(t, "SetFloodBaseRate"))
        sizes = {x: len(rows(pk, x) or []) for x in tabs}
        keys = {x: sorted({v for row in rows(pk, x) or [] for k, v in row.items() if k not in ("StateCode", "CovType", "Construction", "FloodZone", "LossCost")}) for x in tabs}
        print(f"    {j}: tables {sizes}; counties named in SetFloodBaseRate: {counties} ({len(counties)}); table keys besides cov / construction / zone: {keys}")
        check(len(tabs) >= 2 and all(sizes.values()) and counties and not any(keys.values()),
              f"{j}: the rule names {len(counties)} counties / cities and picks the county table for them, the all-other table otherwise; "
              "neither table carries a county column")
    progress("C25-07  LITERAL KEYS SENT BY THE RULES HAVE ROWS")
    lits = {"AnnualAggregateFactor": one("OR", "AnnualAggregateFactor", "Factor", Constant="Y"),
            "MaxNFIP Building": one("OR", "MaxNFIPCoverageAmount", "Amount", Coverage="Building"),
            "MaxNFIP Content": one("OR", "MaxNFIPCoverageAmount", "Amount", Coverage="Content")}
    print(f"    {lits}")
    check(all(v is not None for v in lits.values()), "'Y', 'Building' and 'Content' each find a row")
    rs = trows("OR", "BusnIncomeFactor")
    tors = sorted({x["TypeOfRisk"] for x in rs})
    sent = {"Manufacturing", "Mercantile and Non-manufacturing", "Rental Properties"}
    check(sent <= set(tors), f"the type-of-risk literals the BI rules send have rows ({sorted(sent)} in {tors})")


def main():
    if "--skip-stored" not in sys.argv:
        evidence()
    for k, (desc, build) in blanket_trees().items():
        data, _, err = m.rated(build(), "OR")
        if data is not None:
            blanket_cache[k] = data
    res = run_trees(trees(), "C25-05  THE FLOOD RATE BY HAND (no ISO)")
    run_trees(blanket_trees(), "C25-06  THE FLOOD BLANKET BY HAND (no ISO)")
    if "T1" in res and "K1" in blanket_cache:
        touchpoints(res)
        attach_map(res)
    tables()
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-1 (C25-02..C25-07): {'ALL CHECKS PASS' if not FAIL else 'FAILED: ' + '; '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
