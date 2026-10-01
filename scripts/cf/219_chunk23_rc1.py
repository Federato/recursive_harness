#!/usr/bin/env python3
"""Chunk 23, RC-1 (C23-02..C23-06): the state-only families, evidence and plumbing. No ISO calls.

Each family runs on its own state's portable policy (192_), from its own state's schema and package. Every premium
record is predicted three ways: a hand model written from the rule text below, 174_'s independent SetPremium
evaluator, and the engine. Inputs a hand model reads from the engine are parent values built and ISO-confirmed in
earlier chunks (a building's final / adjusted rates, LOI factors and cause-of-loss adjustments, a coverage's own
premiums, the Mortgageholders E&O premium, the Pollutant Clean Up premiums).

  MA heating oil   remediation = base + (tanks - 1) x tank rate + extra buildings x building rate, each through the
                   modifiers; the location credit is ON only if a building at the location has a remediation record,
                   and = -min(credit, max discount) through the modifiers, where the credit (on MA's own Pollutant Clean
                   Up location record, when its RemediationForReleaseOfHeatingOilAdditionalBuildings = "Yes") is
                   min(deduction, that record's five premiums), deduction = r0(r0(Limit / 10,000 x base discount) x LCM)
                   with base discount = r0(table x LCM): the loss-cost multiplier is applied TWICE, as written
  MA relocation    per unit min(max premium, factor x r3(building Group I rate x Group I LOI factor)), x units, r0:
                   the cap is PER UNIT, so the number of units never reaches it
  AK fees          building / contents: r0(total cause-of-loss premium x (Limit / the coverage's LimitToUse - 1) x factor);
                   policy: r0((trunc(Limit / limit per mortgage) - 1) x factor x the Mortgageholders E&O premium)
  CA earthquake    Additional EQ = r0(manual premium); Limited EQ = r0(r0(Limit / 100 x final EQ rate) x cyber x cyber);
                   the cyber factors from the policy; BI's ensuing-causes factor from BI's own ...BusnIncomeEQToUse
  VA O&L forms     Cov A r0(r3((Factor x PostLoss - 1) x adjusted rate) x LimitToUse / 100); B / C / B&C
                   r0(r3(r3(COL adjustment x PostLoss) x LOI factor) x limit / 100) (Broad: the Broad rate); EQ the
                   same shapes on the EQ fields; then package mod, the contents' MPDC, IRPM and (broad form only) the
                   two cyber factors; pollutant clean-up = the container's PollutantCleanupPremium

    python scripts/cf/219_chunk23_rc1.py

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402

rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
r2 = import_module("175_chunk16_rc2")
g19 = import_module("192_chunk19_rc2")
h21 = import_module("207_chunk21_rc1")
cen = import_module("904_chunk23_census")
gc, rep, cmp, r11 = r2.gc, r2.rep, r2.cmp, r2.r11
ASOF = "20260917"
P = "CommercialProperty"
ERC = Path(r"C:\Projects\ISO_ERC_Files\CF")
FAIL = []
D = Decimal
HO, HOC, TR = "RemediationForReleaseOfHeatingOil", "LocationRemediationForReleaseOfHeatingOilPollutantCleanUpCreditCoverage", "MassachusettsTenantRelocationExpense"
PC = "PollutantCleanUpAndRemovalAdditionalAggregateLimitOfInsuranceLocation"
AKF, AKS, AKP = "ChangesAttorneysFees", "ChangesAttorneysFeesStruct", "ChangesAttorneysFeesPrsnlProp"
MORT = "MortgageholdersErrorsAndOmissionsCoverageForm"
LEQ = "CauseOfLossLimitedEarthquakeEndorsementCaliforniaResidentialPropertyLessorsRisk"
ADDEQ = "AdditionalEarthquakeCoverageCalifornia"
VABF, VAT = "OrdinanceOrLawCoverageStateBroadForm", "OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsVA"
STATES = {"MA": "MA heating-oil remediation", "AK": "AK Changes: Attorneys' Fees", "CA": "CA Additional / Limited Earthquake",
          "VA": "VA Ordinance or Law state forms (chunk 12 open cases)"}


def progress(what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{mm}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def r(x, dp):
    return D(str(x)).quantize(D(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def val(n, f):
    c = n.first(f) if n is not None else None
    return None if c is None or c.text in (None, "") else c.text


def d(n, f, default="0"):
    return D(val(n, f) or default)


def up(n, k):
    for _ in range(k):
        n = n.parent
    return n


def root(n):
    while n.tag != P:
        n = n.parent
    return n


def find(data, rec):
    return rc1.find(data, P + rec)


# ------------------------------------------------------------------ the families' files, from each state's own package

def family_files(j):
    b = book_for(j, ASOF)
    st, cw = b.state.package.content, b.parent.package.content
    pat = next(p for fam, jj, p, _ in cen.FAMILIES if jj == j and (j != "MA" or True))
    pats = [p for fam, jj, p, _ in cen.FAMILIES if jj == j]
    out = {}
    for f in sorted((st / "Rules").glob("*.xml")):
        if any(re.search(p, f.name) for p in pats) and not (cw / "Rules" / f.name).exists():
            out[f.name[:-len("Rules.Rule.xml")].replace(P, "")] = f.read_text(encoding="utf-8-sig")
    return out


FILES = {j: family_files(j) for j in STATES}
PREMIUM_RECS = {j: [n for n, t in fs.items() if cen.set_premium(t)] for j, fs in FILES.items()}


def numeric_inputs():
    """xs:int / xs:decimal fields of every family record in its state's schema: sent as numbers (chunk 22's gap 2)."""
    out = set()
    for j, fs in FILES.items():
        xs = next((book_for(j, ASOF).state.package.content / "DataDefs").glob("*.xsd")).read_text(encoding="utf-8-sig")
        for rec in list(fs) + [PC, MORT]:
            m = re.search(rf'<xs:complexType name="{P}{rec}">(.*?)</xs:complexType>', xs, re.S)
            if m:
                out |= {e for e, t in re.findall(r'<xs:element name="(\w+)"[^>]*type="xs:(int|decimal|integer|long)"', m.group(1))}
    return out


r11.NUMERIC |= numeric_inputs() - {"Limit"} | {"Limit"}


def rated(sub, j):
    try:
        data, ip = gc.run(sub, j)
        return data, ip, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {str(exc)[:160]}"


def put(sub, rec, fields, j):
    r2.put(sub, rec, fields, state=j)


def at(sub):
    return rc1.node_dicts(sub)


def portable(j, cause="Special"):
    return g19.with_cause(g19.portable(j), cause)


# ------------------------------------------------------------------ hand models

def mods(x, cp, mpdc_node):
    for f in (d(cp, "PackageModFactor"), d(mpdc_node, "MultiPremiumAndDispersionCreditFactor"), d(cp, "IRPMFactor")):
        x = r(x * f, 0)
    return x


def table_val(j, name, col, **keys):
    for row in h21.rows_state(j, name) if hasattr(h21, "rows_state") else ROWS(j, name):
        if all(row.get(k) == v for k, v in keys.items()):
            return D(row[col])
    return None


def ROWS(j, name):
    b = book_for(j, ASOF)
    for pkg in (b.state.package.content, b.parent.package.content):
        f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
        if f.exists():
            with open(f, encoding="utf-8-sig") as h:
                rows = list(csv.DictReader(h))
            if rows:
                return rows
    return []


def hand_ma(node, rec):
    cp = root(node)
    if rec == HO:
        st, lcm = up(node, 2), d(up(node, 2), "LossCostMultiplier")
        base = mods(r(table_val("MA", "BasePremium", "Premium", Constant="Y") * lcm, 0), cp, cp)
        tanks = d(node, "NumberOfTanks")
        tank_rate = r(table_val("MA", "NumberOfTanksRate", "Rate", Constant="Y") * lcm, 0) if tanks > 0 else D(0)
        add_t = D(0)
        if tanks > 0:
            add_t = r(r(r((tanks - 1) * tank_rate * d(cp, "PackageModFactor"), 0) * d(cp, "MultiPremiumAndDispersionCreditFactor"), 0) * d(cp, "IRPMFactor"), 0)
        add_b = D(0)
        if val(node, "TanksServingAdditionalBuildings") == "Yes":
            b_rate = r(table_val("MA", "AdditionalBuildingsRate", "Rate", Constant="Y") * lcm, 0)
            add_b = mods(d(node, "AdditionalBuildings") * b_rate, cp, cp)
        return base + add_t + add_b
    if rec == HOC:
        loc = up(node, 1) if node.parent.tag == P + "Location" else up(node, 2)
        on = any(rc1.find(s_, P + HO) for s_ in rc1.find(loc, P + "Structure"))
        if not on:
            return D(0)
        lcm = d(loc, "LossCostMultiplier")
        maxd = r(table_val("MA", "PollutantCleanupMaxDiscount", "Discount", Constant="Y") * lcm, 0)
        credit = D(0)
        for pcn in rc1.find(loc, P + PC):
            if val(pcn, "RemediationForReleaseOfHeatingOilAdditionalBuildings") != "Yes":
                continue
            based = r(table_val("MA", "PollutantCleanupBaseDiscount", "Discount", Constant="Y") * lcm, 0)
            ded = r(r(d(pcn, "Limit") / 10000 * based, 0) * lcm, 0)
            prem = sum(d(c, "Premium") for c in pcn.children if c.tag.startswith(P + PC) and c.tag.endswith("Coverage"))
            credit += prem if ded > prem else ded
        x = maxd if credit > maxd else credit
        return -mods(x, cp, cp)
    if rec == TR:
        st = up(node, 2)
        calc = table_val("MA", "TenantRelocationExpenseFactor", "Factor", Constant="Y") * r(d(st, "BasicGroupIRate") * d(st, "BasicGroupILOIFactor"), 3)
        mx = table_val("MA", "TenantRelocationMaxPremium", "Premium", Constant="Y")
        ev = calc if mx > calc else mx
        return r(ev * d(node, "NumberOfUnits"), 0)


def hand_ak(node, rec):
    cp = root(node)
    lim = d(node, "Limit")
    if rec == AKF:
        if lim <= 0:
            return D(0)
        mort = rc1.find(cp, P + MORT)[0]
        per = table_val("AK", "MortgageholdersLimitOfInsPerMortgAmount", "Limit", **{"MortgageholdersLimitOfInsPerMortg": val(mort, "Limit")}) \
            if ROWS("AK", "MortgageholdersLimitOfInsPerMortgAmount") and "MortgageholdersLimitOfInsPerMortg" in ROWS("AK", "MortgageholdersLimitOfInsPerMortgAmount")[0] else None
        if per is None:
            keycol = [k for k in ROWS("AK", "MortgageholdersLimitOfInsPerMortgAmount")[0] if k not in ("StateCode", "Limit")][0]
            per = table_val("AK", "MortgageholdersLimitOfInsPerMortgAmount", "Limit", **{keycol: val(mort, "Limit")})
        f = table_val("AK", "AttorneyFeesMortgageHoldersFactor", "Factor", Constant="Y")
        return r(((lim / per).to_integral_value(rounding=ROUND_DOWN) - 1) * f * d(mort, "Premium"), 0)
    parent = up(node, 2)
    if lim == 0:
        return D(0)
    f = table_val("AK", "AttorneyFeesLegalLiabilityFactor", "Factor", Constant="Y")
    pre = "StructureBuilding" if rec == AKS else "PersonalPropertyPrsnlProp"
    covs = [parent.first(P + pre + g + "Coverage") for g in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
    if any(c is None or val(c, "Premium") is None for c in covs):
        return D(0)
    eqrec = "EarthquakeAndVolcanicEruptionEndorsement" + ("" if rec == AKS else "PrsnlProp")
    eq = D(0)
    for name in (eqrec, eqrec.replace("Endorsement", "EndorsementSubLimitForm")):
        hit = rc1.find(parent, P + name)
        if hit and val(hit[0], "Premium") is not None:
            eq = d(hit[0], "Premium")
            break
    total = sum(d(c, "Premium") for c in covs) + eq
    return r(total * (lim / d(parent, "LimitToUse") - 1) * f, 0)


def hand_ca(node, rec):
    if rec == ADDEQ:
        return r(d(node, "ManualPremium"), 0)
    parent = up(node, 2)
    blanket = val(parent, "EQCovIndicator") == "Yes, Included in Blanket"
    if val(parent, "EQCovIndicator") in (None, "No Coverage", "Not Applicable"):
        return D(0)
    if blanket:
        base = r(D(val(parent, "EQLimitToUse") or 0) / 100 * d(parent, "BlktEQAvgRate"), 0)
    else:
        base = r(d(node, "Limit") / 100 * d(parent, "FinalEQRate"), 0)
    cp = root(node)                      # the building (6 up), contents (10 up) and BI (8 up) paths all land on the policy
    c1 = d(cp, "CyberIncidentExclusionFactorEQ")
    c2 = d(parent, "CyberIncidentExclusionCOLExcptnsFactorBusnIncomeEQToUse") if rec.endswith("BusnIncome")         else d(cp, "CyberIncidentExclusionCOLExcptnsFactorEQ")
    return r(r(base * c1, 0) * c2, 0)


GROUP = {"BasicGroupI": ("AdjustedBasicGroupIRate", "BasicGroupICauseOfLossAdjustment", "BasicGroupILOIFactor", "BGI"),
         "BasicGroupII": ("AdjustedBasicGroupIIRate", "BasicGroupIICauseOfLossAdjustment", "BasicGroupIILOIFactor", "BGII"),
         "Broad": ("AdjustedBroadRate", "BroadRate", "BroadLOIFactor", "Broad"),
         "Special": ("AdjustedSpecialRate", "SpecialCauseOfLossAdjustment", "SpecialLOIFactor", "Special")}
TGROUP = {"BGI": "BasicGroupI", "BGII": "BasicGroupII", "Broad": "Broad", "Special": "Special", "EQ": "Earthquake"}


def va_parse(rec):
    """(form, coverage, group) from the record name."""
    if rec.startswith("OrdinanceOrLawBroadForm"):
        m = re.match(r"OrdinanceOrLawBroadForm(Cov(?:BAndC|A|B|C))Coverage(\w+)Coverage$", rec)
        return "BF", m.group(1).replace("BAndC", "BandC"), m.group(2)
    m = re.match(rf"{VAT}(Cov(?:BandC|A|B|C))(\w+)Coverage$", rec)
    return "T", m.group(1), TGROUP[m.group(2)]


def va_on(cov, group, cont, st):
    ct = val(cont, "CovType")
    eq_on = val(st, "EQCovIndicator") in ("Yes, Included in Blanket", "Yes, Not Included in Blanket")
    if group == "Earthquake":
        if not eq_on:
            return False
    elif group in ("Broad", "Special") and val(st, "CauseOfLossToUse") != group:
        return False
    return {"CovA": ct not in (None, "Coverage C Only"),
            "CovB": ct in ("Coverages A and B", "Coverages A and B & C Separate"),
            "CovC": ct in ("Coverage C Only", "Coverages A and B & C Separate"),
            "CovBandC": ct == "Coverages A and B & C Combined"}[cov]


def hand_va(node, rec):
    if rec == "OrdinanceOrLawCovBroadFormPolluntantCleanupCoverage":
        cont = node.parent
        return d(cont, "PollutantCleanupPremium") if d(cont, "PollutantCleanupPremium") != 0 else D(0)
    form, cov, group = va_parse(rec)
    cont, st = node.parent, up(node, 3)
    cp = root(node)
    if not va_on(cov, group, cont, st):
        return D(0)
    # the container's factors BY HAND from the filed tables (not read off the engine): PostLossFactor 1.02 when
    # PostLossOrdinanceOrLawOption is "Yes", else 1.0; Factor / CovAFactor 1.15 and EQFactor / CovAEQFactor 1.85 unless "Coverage C
    # Only" (then 1.0; EQ also 1.0 without an EQ election)
    ct = val(cont, "CovType")
    pl = table_val("VA", "PostLossOrdinanceOrLawOptionFactor", "Factor", Constant="Y") if val(cont, "PostLossOrdinanceOrLawOption") == "Yes" else D(1)
    fa = table_val("VA", "OrdinanceOrLawCoverageAFactor", "Factor", Constant="Y") if ct != "Coverage C Only" else D(1)
    eq_el = val(st, "EQCovIndicator") not in (None, "No Coverage", "Not Applicable")
    fe = table_val("VA", "OrdinanceOrLawCovAEQFactor", "Factor", Constant="Y") if ct != "Coverage C Only" and eq_el else D(1)
    for f_, want in (("PostLossFactor", pl), ("Factor" if form == "BF" else "CovAFactor", fa), ("EQFactor" if form == "BF" else "CovAEQFactor", fe)):
        if d(cont, f_) != want:
            raise ValueError(f"container {f_} engine {val(cont, f_)} hand {want}")
    lim_f = {"CovB": "CovBDemolitionLimit", "CovC": "CovCIncreasedConstructionLimit", "CovBandC": "CombinedBAndCDemolitionAndIncrdConstrctnLimit"}
    if group == "Earthquake":
        if cov == "CovA":
            f = fe
            x = r(r((f * pl - 1) * d(st, "AdjustedEQRate"), 3) * D(val(st, "EQLimitToUse") or 0) / 100, 0)
        else:
            x = r(r(d(st, "EQCauseOfLossAdjustment") * pl, 3) * d(cont, lim_f[cov]) / 100, 0)
        if form == "BF":
            x = r(r(x * d(cp, "CyberIncidentExclusionFactorEQ"), 0) * d(cp, "CyberIncidentExclusionCOLExcptnsFactorEQ"), 0)
        return x
    adj, col, loi, cy = GROUP[group]
    if cov == "CovA":
        f = fa
        x = r(r((f * pl - 1) * d(st, adj), 3) * d(st, "LimitToUse") / 100, 0)
        cy = "BGI" if (form == "BF" and group == "Special") else cy           # broad form Special Cov A reads the Group I cyber pair
    else:
        x = r(r(r(d(st, col) * pl, 3) * d(st, loi), 3) * d(cont, lim_f[cov]) / 100, 0)
    x = mods(x, cp, st)
    if form == "BF":
        x = r(r(x * d(cp, f"CyberIncidentExclusionFactor{cy}"), 0) * d(cp, f"CyberIncidentExclusionCOLExcptnsFactor{cy}"), 0)
    return x


HAND = {"MA": hand_ma, "AK": hand_ak, "CA": hand_ca, "VA": hand_va}


def predict(j, data, rec):
    body = cen.set_premium(FILES[j][rec])
    out = []
    for node in find(data, rec):
        prem = node.first("Premium")
        if val(node, "CoverageOnPolicyIndicator") == "0":
            ev = D(0)
        elif "<rul:Copy " in body:            # the evaluator has no Copy: the one Copy premium reads its FromDataDef directly
            ev = val(node.parent, re.search(r'<rul:Copy[^>]*FromDataDef="\.\./(\w+)"', body).group(1))
        else:
            ev = r16.hand(body, node)
        try:
            hv = HAND[j](node, rec)
        except Exception as exc:
            hv = f"hand error {type(exc).__name__}: {exc}"
        out.append((hv, ev, None if prem is None else prem.text))
    return out


def same(a, b):
    try:
        return D(str(a or 0)) == D(str(b or 0))
    except Exception:
        return False


def check_tree(label, j, sub, recs, expect_on=None):
    data, ip, err = rated(sub, j)
    if err:
        check(False, f"{label}: engine raised {err}")
        return None, None
    bad, lines = [], []
    for rec in recs:
        res = predict(j, data, rec)
        ok = bool(res) and all(same(hv, e) and same(ev, e) for hv, ev, e in res)
        lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-62:]:62s} hand {[str(x) for x, _, _ in res]} evaluator {[str(x) for _, x, _ in res]} engine {[e for _, _, e in res]}")
        if not ok:
            bad.append(rec)
    print(f"  {label}:")
    print("\n".join(lines))
    check(not bad, f"{label}: hand = evaluator = engine on every record ({len(recs)} records)")
    return data, ip


# ------------------------------------------------------------------ trees

def ma_tree(remediation=True, credit_yes=True, tanks="3", extra="2", units="4", pollutant=True):
    sub = portable("MA")
    if pollutant:
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake"):
            put(sub, f"{PC}{f}Coverage", {}, "MA")
        c = at(sub)[P + "Location"][P + PC + "Table"][P + PC][0]
        c.update({"Limit": "60000", "Deductible": "2,500"})
        if credit_yes:
            c["RemediationForReleaseOfHeatingOilAdditionalBuildings"] = "Yes"
    if remediation:
        put(sub, HO, {"NumberOfTanks": tanks, "TanksServingAdditionalBuildings": "Yes" if extra else "No",
                      "AdditionalBuildings": extra or "0"}, "MA")
    put(sub, HOC, {}, "MA")
    if units is not None:
        put(sub, TR, {"NumberOfUnits": units}, "MA")
    return sub


def ak_tree(struct_lim="400000", pp_lim="150000", fee="100000", mort=True, ll=True):
    """the fees attach ONLY on Legal Liability: AK's AttachFormChangesAttorneysFeesStruct keeps the building record when
    the building's CovType is "Legal Liability", SetAttachFormChangesAttorneysFeesPrsnlProp the contents record when the
    occupancy has the Legal Liability coverage-form record; otherwise both REMOVE it (chunk 8's Legal Liability recipe)."""
    sub = portable("AK")
    st, pp = at(sub)[P + "Structure"], at(sub)[P + "PersonalProperty"]
    if ll:
        sub[P + "Table"][P][0]["PolicyType"] = "Commercial Property Policy"
        st["CovType"] = "Legal Liability"
        st[P + "LegalLiabilityCoverageFormTable"] = {P + "LegalLiabilityCoverageForm": [{"AddlInsurableInt": "None"}]}
        oc = at(sub)[P + "OccupClass"]
        oc["CovForm"] = "Legal Liability Coverage Form"
        oc[P + "LegalLiabilityCoverageFormOccupClassTable"] = {P + "LegalLiabilityCoverageFormOccupClass": [{"AddlInsurableInt": "None"}]}
    put(sub, AKS, {"Limit": struct_lim}, "AK")
    put(sub, AKP, {"Limit": pp_lim}, "AK")
    if mort:
        put(sub, MORT, {"Limit": "25,000", "NumberMortgages": "500"}, "AK")
    put(sub, AKF, {"Limit": fee}, "AK")
    return sub


def ca_tree(blanket=False, manual="250", lim=("150000", "60000", "40000")):
    sub = portable("CA")
    a = at(sub)
    a[P + "Location"]["EQCauseOfLossForm"] = "Limited Earthquake Endorsement (CP 10 43)"
    st = a[P + "Structure"]
    a[P + "PersonalProperty"].update({k: st[k] for k in ("EQCovIndicator", "EQCoinsurance", "EQDeductible") if k in st})
    a[P + "PersonalProperty"].update({"EQGrade": "2", "EQSprinklerLeakageOnly": "Not Applicable"})
    put(sub, LEQ + "Building", {"Limit": lim[0]}, "CA")
    put(sub, LEQ + "PrsnlProp", {"Limit": lim[1]}, "CA")
    put(sub, LEQ + "BusnIncome", {"Limit": lim[2]}, "CA")
    if manual is not None:
        put(sub, ADDEQ, {"ManualPremium": manual}, "CA")
    return sub


def va_tree(covtype="Coverages A and B & C Separate", cause="Special", post="No", tenants=True, pollutant="150"):
    sub = portable("VA", cause)
    bf = {"CovType": covtype, "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
          "CombinedBAndCDemolitionAndIncrdConstrctnLimit": "50000", "PostLossOrdinanceOrLawOption": post}
    if pollutant:
        bf["PollutantCleanupPremium"] = pollutant
    st = at(sub)[P + "Structure"]
    st[P + VABF + "Table"] = {P + VABF: [bf]}
    if tenants:
        st[P + VAT + "Table"] = {P + VAT: [{k: v for k, v in bf.items() if k != "PollutantCleanupPremium"}]}
    return sub


# ------------------------------------------------------------------ C23-02

def stored_credit():
    progress("C23-02  MA's STORED CREDIT RECORD")
    print("\n" + "=" * 90 + "\nC23-02  MA's STORED CREDIT RECORD\n" + "-" * 90)
    resp_files = sorted(f for f in gc.OUT.glob("*_response.json") if HOC in f.read_text(encoding="utf-8", errors="ignore"))
    n = agree = 0
    for rp in resp_files:
        qp = Path(str(rp).replace("_response.json", "_request.json"))
        if not qp.exists():
            continue
        req, resp = json.loads(qp.read_text(encoding="utf-8")), json.loads(rp.read_text(encoding="utf-8"))
        iso = [o for o in _walk(resp, P + HOC)]
        has_rem = bool(list(_walk(req, P + HO)))
        try:
            data, ip = cmp.rate(req)
        except Exception as exc:
            print(f"    {rp.name}: ours raised {str(exc)[:100]}")
            continue
        ours = [(val(x, "Premium"), val(x, "CoverageOnPolicyIndicator")) for x in find(data, HOC)]
        isov = [(o.get("Premium"), o.get("CoverageOnPolicyIndicator")) for o in iso]
        n += 1
        ok = all(same(a[0], b[0]) and str(b[1]) in ("0", "None") for a, b in zip(ours, isov)) and not has_rem
        agree += ok
        print(f"    {rp.name[:-14]:42s} remediation record sent: {has_rem}; ISO {isov} ours {ours}")
    check(n >= 9 and agree == n, f"{agree} of {n} stored MA responses carry the credit record unpriced at ISO and ours: no "
                                 f"building there has a remediation record, so the credit's switch is 0")


def _walk(o, tag, k=None):
    if isinstance(o, dict):
        if k == tag:
            yield o
        for kk, v in o.items():
            if isinstance(v, (dict, list)):
                yield from _walk(v, tag, kk)
    elif isinstance(o, list):
        for x in o:
            yield from _walk(x, tag, k)


# ------------------------------------------------------------------ C23-03

def attach_map():
    progress("C23-03  ATTACH MAP AND SWITCHES (each state's own schema)")
    print("\n" + "=" * 90 + "\nC23-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    unplaced = []
    for j, recs in PREMIUM_RECS.items():
        xsd = rc1.xsd_for(book_for(j, ASOF))
        print(f"  {j} ({book_for(j, ASOF).state.package.content.name}): {len(recs)} premium records")
        for rec in recs:
            ch = r16.chain_down(xsd, rec)
            where = "NOT IN XSD" if ch is None else r16.short(ch[0]) + " > " + " > ".join(r16.short(t) + ("[]" if tb else "") for t, tb in ch[1])
            if ch is None:
                unplaced.append(rec)
            if j != "VA" or rec.endswith("BasicGroupICoverage") or rec.endswith("BGICoverage") or "Polluntant" in rec:
                print(f"    {rec[-70:]:70s} {where[:80]}\n        switch: {h21.switch_of(FILES[j][rec])[:110]}"
                      f"\n        zeroes: {h21.zero_defaults(FILES[j][rec])[:4]}")
    check(not unplaced, f"every premium record is placed by its state's schema ({unplaced or 'all'})")


# ------------------------------------------------------------------ C23-04 (+ the switch flips of C23-03)

def borrowed():
    progress("C23-04  BORROWED VALUES: hand = evaluator = engine on real trees")
    print("\n" + "=" * 90 + "\nC23-04  BORROWED VALUES (and the switches flipped)\n" + "-" * 90)
    ma = [HO, HOC, TR]
    check_tree("MA1 remediation 3 tanks + 2 buildings, credit 'Yes' on Pollutant Clean Up 60,000, 4 units", "MA", ma_tree(), ma)
    check_tree("MA2 the credit's switch off: no remediation record (the stored fixtures' shape)", "MA", ma_tree(remediation=False), [HOC, TR])
    check_tree("MA3 remediation on, the Pollutant record's heating-oil answer blank (deduction 0)", "MA", ma_tree(credit_yes=False), ma)
    check_tree("MA4 one tank, no extra buildings, 40 units", "MA", ma_tree(tanks="1", extra=None, units="40"), ma)
    ak = [AKS, AKP, AKF]
    check_tree("AK1 building fee 400,000, contents 150,000, policy 100,000 on Mortgageholders 25,000 x 500", "AK", ak_tree(), ak)
    check_tree("AK2 fees at the coverage limits (ratio 1 -> $0) and policy fee 0", "AK", ak_tree("100000", "100000", "0"), ak)
    d3 = rated(ak_tree(mort=False), "AK")[0]
    print(f"  AK3 policy fee with no Mortgageholders E&O record: policy fee records kept {len(find(d3, AKF))}")
    check(len(find(d3, AKF)) == 0, "AK3: the main ruleset's AttachFormChangesAttorneysFees keeps the policy fee only with a "
                                   "Mortgageholders E&O record; without one it is REMOVED")
    d0 = rated(ak_tree(ll=False), "AK")[0]
    n_s, n_p = len(find(d0, AKS)), len(find(d0, AKP))
    print(f"  AK4 the same fees on an ordinary (not Legal Liability) building and contents: records kept {n_s} / {n_p}")
    check(n_s == 0 and n_p == 0, "AK4: off Legal Liability the building and contents fee records are REMOVED (attach rules' Else)")
    ca = [LEQ + "Building", LEQ + "PrsnlProp", LEQ + "BusnIncome", ADDEQ]
    check_tree("CA1 Limited EQ 150,000 / 60,000 / 40,000 + Additional EQ manual 250", "CA", ca_tree(), ca)
    check_tree("CA2 Additional EQ manual 249.5 (rounds to 250), no Limited EQ limits", "CA", ca_tree(manual="249.5", lim=("0", "0", "0")), ca)
    va = PREMIUM_RECS["VA"]
    check_tree("VA1 broad + tenants, A and B & C Separate, Special, EQ on, pollutant 150", "VA", va_tree(), va)
    check_tree("VA2 A and B & C Combined, Broad cause, post-loss option Yes", "VA", va_tree("Coverages A and B & C Combined", "Broad", "Yes"), va)
    check_tree("VA3 Coverage C Only, Basic, no pollutant premium", "VA", va_tree("Coverage C Only", "Basic", pollutant=None), va)
    check_tree("VA4 Coverages A and B, Special", "VA", va_tree("Coverages A and B"), va)


# ------------------------------------------------------------------ C23-05

def tables():
    progress("C23-05  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC23-05  TABLES AND LITERALS\n" + "-" * 90)
    missing = []
    for j, fs in FILES.items():
        names = {}
        for rec, t in fs.items():
            for m in re.finditer(r'MatrixFromConstant="(\w+)"(.*?)</rul:Lookup>', t, re.S):
                keys = re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(2))
                names.setdefault(m.group(1), set()).update(k for k in keys if k)
        print(f"  {j}: {len(names)} tables read by the family files")
        for name, keys in sorted(names.items()):
            rows = ROWS(j, name)
            st_own = (book_for(j, ASOF).state.package.content / "Rate Tables" / f"{name}.RateTable.csv").exists()
            cols = list(rows[0]) if rows else []
            banded = [c for c in cols if re.search(r"From|To$|ToLessThan|GreaterThan", c)]
            lits = [k for k in keys if k not in ("CW",)]
            miss = [k for k in lits if rows and not any(k in row.values() for row in rows)]
            missing += [(j, name, k) for k in miss]
            print(f"    {name:52s} {len(rows):3d} rows ({'state' if st_own else 'CW'}); keys {sorted(lits)[:4]}; banded columns {banded or 'none'}")
    check(not missing, f"every literal key has a row ({missing or 'none missing'})")
    print("  -> no family lookup is banded: chunk 10's two-range fix is not on these paths (MA's heating-oil tables are "
          "one-row 'Y' lookups)")
    print(f"  numeric input fields sent as numbers (from each state's schema): {sorted(numeric_inputs())[:30]}")


# ------------------------------------------------------------------ C23-06

def packages(j):
    out = []
    for p in ERC.glob(f"*/CF {j} *"):
        m = re.match(rf"CF {j} (\d{{8}}) V(\d+)", p.name)
        if m and (p / "Rules").exists():
            out.append((m.group(1), int(m.group(2)), p))
    return sorted(out)


def edition_timing():
    progress("C23-06  EDITION TIMING (OI-105)")
    print("\n" + "=" * 90 + "\nC23-06  EDITION TIMING\n" + "-" * 90)
    builds = {"MA": (ma_tree, [HO, HOC, TR]), "AK": (ak_tree, [AKS, AKP, AKF]), "CA": (ca_tree, [LEQ + "Building", LEQ + "PrsnlProp", LEQ + "BusnIncome", ADDEQ]),
              "VA": (va_tree, PREMIUM_RECS["VA"])}
    for j in STATES:
        pk = packages(j)
        inforce = book_for(j, ASOF).state.package.content.name
        later = [(dt, v, p) for dt, v, p in pk if dt > ASOF]
        print(f"  {j}: {len(pk)} packages, in force at {ASOF}: {inforce}; later: {[p.name for _, _, p in later] or 'none'}")
        base = {n: t for n, t in FILES[j].items()}
        for dt, v, p in later:
            diffs = []
            for name, text in base.items():
                f = p / "Rules" / f"{P}{name}Rules.Rule.xml"
                if not f.exists():
                    diffs.append(f"{name}: no file")
                    continue
                a = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in re.finditer(r'<rul:Rule Name="(\w+)".*?</rul:Rule>', text, re.S)}
                bb = {m.group(1): re.sub(r"\s+", " ", m.group(0)) for m in re.finditer(r'<rul:Rule Name="(\w+)".*?</rul:Rule>', f.read_text(encoding="utf-8-sig"), re.S)}
                diffs += [f"{name}.{k}" for k in sorted(set(a) | set(bb)) if re.sub(r' MetadataCodes="[^"]*"', "", a.get(k, "")) != re.sub(r' MetadataCodes="[^"]*"', "", bb.get(k, ""))]
            print(f"    {p.name}: {len(diffs)} family rule difference(s) {diffs[:6]}")
            if diffs:
                bld, recs = builds[j]
                b_now, b_later = book_for(j, ASOF), book_for(j, dt)
                if b_later.state.package.content != p:
                    print(f"      (book_for at {dt} resolves to {b_later.state.package.content.name})")
                d_now = gc.run(bld(), j)[0]
                from gl_engine.interp.interpreter import Interpreter
                from gl_engine.interp.tree import Node
                ip2 = Interpreter(b_later, rounding=gc.ROUNDING, null_arithmetic=gc.NULL_ARITHMETIC)
                d_later = Node.from_dict(f"MasterCF{j}", bld())
                ip2.run(d_later)
                moved = [(rec, [val(x, "Premium") for x in find(d_now, rec)], [val(x, "Premium") for x in find(d_later, rec)]) for rec in recs]
                moved = [m_ for m_ in moved if m_[1] != m_[2]]
                print(f"      the same tree on {p.name}: premiums that move {moved or 'none'}")
    print("  -> which package ISO serves is settled live at RC-2: every golden case is sent at 2026-09-17 and compared field for field")


def main():
    print(f"premium records: " + ", ".join(f"{j} {len(v)}" for j, v in PREMIUM_RECS.items()))
    check(sum(len(v) for v in PREMIUM_RECS.values()) == 51, f"51 premium records (MA 3, AK 3, CA 4, VA 41): "
                                                            f"{ {j: len(v) for j, v in PREMIUM_RECS.items()} }")
    stored_credit()
    attach_map()
    borrowed()
    tables()
    edition_timing()
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1 (C23-02..C23-06): ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED: {FAIL}") + f"  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
