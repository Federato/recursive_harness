#!/usr/bin/env python3
"""Chunk 23, RC-3 (C23-12..C23-15): zero cases, messages, shared names and exclusion records, each an ISO probe.

Every case is a family's own state's policy (219_ / 220_ trees) with one thing changed. Each record is predicted before
the run (219_'s hand models, 174_'s evaluator, the engine; a submitted value that survives its guard goes through 219_'s
OVR table); each case names the messages that must appear (with their count) and must not, as (level, text): the level
is the table that raised it (MessageHelper's TableName, captured here; on ISO's side the node carrying the message).
--live compares the predicted records, every premium field for field, and the whole (level, message) multiset.

C23-12 ZERO CASES   Z1 MA no tanks, no extra buildings (base only); Z2 the credit with no remediation record ($0 + CP 04 44
                    message); Z3 0 units; Z4 AK fee limits 0; Z5 AK fee limits UNDER the coverage limits (negative fees,
                    as written, + the three CP 00 40 / 00 70 messages); Z6 CA earthquake off; Z7 CA Additional EQ 0;
                    Z8 VA B / C limits blank; Z9 VA pollutant 0; Z10 VA CovType blank (broad Cov A ON, tenants' Cov A OFF)
C23-13 MESSAGES     MA both (Z1, Z2) and silent (MS); AK all three (Z5) and silent (K1 in RC-2); CA: sub-limit over the risk
                    limit x3, residential class silent (0074; 0951 fires: RC-2), sprinkler-leakage-only x2, the Legal
                    Liability form (contents: CP 10 43; building: CP 01 41), CP 01 41 with CP 10 45 / CP 10 29, deductible
                    20% (over 15%), CP 10 41 without an EQ form; VA: Builders Risk, 50% coinsurance x2, actual cash value x2
                    and replacement cost silent, CP 04 05 + CP 04 06, I&B with CP 04 06, I&B blanketed personal property,
                    CP 04 26 + CP 04 27
                    Not fired here: VA's two "80% in Blanket" rules (need a blanketed building with a blanket coinsurance
                    outside the domain), CA's 1310 / 1320 pair (chunk 22 RC-4)
C23-14 SHARED NAMES S1 VA broad-form Factor 2.0, S2 VA PostLossFactor 1.5 (option "No"), S3 AK building fee LimitToUse 3,
                    S4 MA HeatingOilBaseLossCost 100, S5 MA TotalPollutantCleanUpCredit 5, S6 MA BasePremium 500: each
                    IsNull-guarded, so each SURVIVES (the alternative, overwritten, gives RC-2's figures)
C23-15 EXCLUSIONS   X1 VA + cyber at large limits (the broad form's pair moves; the tenants' form reads none); X2 VA + the
                    ensuing-causes cyber form; X3 CA + cyber; X4 AK + cyber; X5 MA + cyber (MA reads no cyber factor)

    python scripts/cf/221_chunk23_rc3.py [--live] [--cases Z1,MC1]
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

import gl_engine.interp.interpreter as interp                             # noqa: E402

t2 = import_module("220_chunk23_rc2")
m = t2.m
r2, rc1, gc, rep, cmp, r11 = m.r2, m.rc1, m.gc, m.rep, m.cmp, m.r11
P, D = m.P, m.D
FAIL = []
ZERO = "zero"
r11.NUMERIC |= {"FullPrsnlPropValue", "EQSubLimitPercent", "TotalPollutantCleanUpCredit", "HeatingOilBaseLossCost", "BasePremium", "Factor",
                "PostLossFactor", "LimitToUse"}
L = {"ST": P + "Structure", "PP": P + "PersonalProperty", "LOC": P + "Location", "PC": P + m.PC, "AKF": P + m.AKF,
     "LEQB": P + m.LEQ + "Building", "LEQP": P + m.LEQ + "PrsnlProp", "LEQBI": P + m.LEQ + "BusnIncome"}
MA, AK, CA, VA = t2.MA_RECS, t2.AK_RECS, t2.CA_RECS, t2.VA_RECS
LL_FORM, LL_OCC = "LegalLiabilityCoverageForm", "LegalLiabilityCoverageFormOccupClass"
CW_TENANTS = "OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBetterments"

# ---------------------------------------------------------------- the level each message was raised at
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged


def lvl(t):
    return t if t.startswith(P) or t == "?" else P + t


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ---------------------------------------------------------------- tree helpers

def with_(build, *fns):
    def b():
        sub = build()
        for fn in fns:
            fn(sub)
        return sub
    return b


def at(sub):
    return m.at(sub)


def st_set(**f):
    return lambda sub: at(sub)[P + "Structure"].update(f)


def pp_set(**f):
    return lambda sub: at(sub)[P + "PersonalProperty"].update(f)


def oc_set(**f):
    return lambda sub: at(sub)[P + "OccupClass"].update(f)


def loc_set(**f):
    return lambda sub: at(sub)[P + "Location"].update(f)


def cyber(kind):
    def f(sub):
        tab = "CyberIncidentExclusion" if kind == "plain" else "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"
        sub[P + "Table"][P][0][P + tab + "Table"] = {P + tab: [{}]}
    return f


def va_cont(form, **f):
    def g(sub):
        st = at(sub)[P + "Structure"]
        c = st[P + (m.VABF if form == "BF" else m.VAT) + "Table"][P + (m.VABF if form == "BF" else m.VAT)][0]
        for k, v in f.items():
            if v is None:
                c.pop(k, None)
            else:
                c[k] = v
    return g


def va_only_bf(cov="Coverages A and B & C Separate", cause="Special", **kw):
    """the broad form alone (no tenants' form on a Building item, so CP 04 27's coverage message stays silent)."""
    def b():
        sub = t2.va(cov, cause, **kw)()
        at(sub)[P + "Structure"].pop(P + m.VAT + "Table", None)
        return sub
    return b


def va_tenants_ib(**kw):
    """the tenants' form alone on an Improvements and Betterments item (its own coverage, so CP 04 27 is valid)."""
    def b():
        sub = t2.va(**kw)()
        st = at(sub)[P + "Structure"]
        st.pop(P + m.VABF + "Table", None)
        st["CovType"] = "Improvements and Betterments"
        return sub
    return b


def ak_limits(frac_s, frac_p, fee):
    def b():
        sub = m.portable("AK")
        a = at(sub)
        sl, pl = int(a[P + "Structure"]["Limit"]), int(a[P + "PersonalProperty"]["Limit"])
        sub0 = m.ak_tree(struct_lim=str(int(sl * frac_s)), pp_lim=str(int(pl * frac_p)), fee=fee)
        return sub0
    return b


def ca_eq_off(sub):
    a = at(sub)
    for k in ("Structure", "PersonalProperty", "BusinessIncome"):
        a[P + k]["EQCovIndicator"] = "No Coverage"


def ca_sublimit(flat):
    def f(sub):
        a = at(sub)
        a[P + "Location"]["EQCauseOfLossForm"] = "Earthquake Sub-Limit Form (CP 10 29)" if flat else "Earthquake Sub-Limit Form (CP 10 45)"
        a[P + "Structure"]["EQSubLimitPercent"] = "25"
        if flat:
            for k in ("Structure", "PersonalProperty", "SpecialClass"):
                a[P + k]["EQDeductible"] = "5,000"
    return f


def ll_structure(sub):
    st = at(sub)[P + "Structure"]
    sub[P + "Table"][P][0]["PolicyType"] = "Commercial Property Policy"
    st["CovType"] = "Legal Liability"
    st[P + LL_FORM + "Table"] = {P + LL_FORM: [{"AddlInsurableInt": "None"}]}


def ll_contents(sub):
    oc = at(sub)[P + "OccupClass"]
    sub[P + "Table"][P][0]["PolicyType"] = "Commercial Property Policy"
    oc["CovForm"] = "Legal Liability Coverage Form"
    oc[P + LL_OCC + "Table"] = {P + LL_OCC: [{"AddlInsurableInt": "None"}]}


def inception(sub):
    a = at(sub)
    a[P + "Location"]["EQCauseOfLossForm"] = "Not Applicable"
    m.put(sub, "EarthquakeInceptionExtension", {}, "CA")


def cw_ol(sub):
    at(sub)[P + "Structure"][P + "OrdinanceOrLawCoverageTable"] = {P + "OrdinanceOrLawCoverage": [{
        "CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
        "PostLossOrdinanceOrLawOption": "No"}]}


def cw_tenants(sub):
    at(sub)[P + "Structure"][P + CW_TENANTS + "Table"] = {P + CW_TENANTS: [{
        "CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
        "PostLossOrdinanceOrLawOption": "No"}]}


def pp_blanket(sub):
    """the contents in a "Personal Property Only" blanket: the countrywide CP 04 26 message rule RE-COMPUTES the building's
    PersPropertyIncludedInBlanket from the contents rows' IncludedInBlkt (unguarded), and VA's CP 04 27 rule reads it."""
    cp = sub[P + "Table"][P][0]
    cp["BlktRated"], cp["MUBlktRated"] = "Yes", "No"
    pp = at(sub)[P + "PersonalProperty"]
    cp[P + "BlanketRatingTable"] = {P + "BlanketRating": [{P + "BlanketRatingDetailTable": {P + "BlanketRatingDetail": [{
        "UnitNumber": "100", "TypeOfBlanketRating": "Average", "Type": "Personal Property Only", "Coinsurance": "90%",
        "CauseOfLoss": pp.get("CauseOfLoss", "Special"), "TotalLimit": pp["Limit"], "RadioactiveContamination": "No"}]}}]}
    pp.update({"IncludedInBlkt": "Yes", "BlktIDNum": "100", "FullPrsnlPropValue": pp["Limit"]})


def hand(recs):
    return {r_: None for r_ in recs}


def zero(recs):
    return {r_: ZERO for r_ in recs}


# ---------------------------------------------------------------- cases

def cases():
    no_ = []
    ca_base = t2.ca()
    VA_MSG_BF = "CP 04 06"
    return {
        # ------------------------------------------------------------ C23-12 zero cases (+ their messages)
        "Z1": ("C23-12", "MA", "no tanks, no extra buildings: base only", t2.ma(tanks="0", extra=None), hand(MA),
               [("LOC", "There are more buildings with CP 04 07 attached")], no_, {}),
        "Z2": ("C23-12", "MA", "credit 'Yes' with no remediation record: $0 + CP 04 44 message", lambda: m.ma_tree(remediation=False),
               {m.HOC: ZERO, m.TR: None}, [("PC", "CP 04 44 must be attached to apply the Pollutant Cleanup Credit"),
                                           ("LOC", "There are more buildings with CP 04 07 attached")], no_, {}),
        "Z3": ("C23-12", "MA", "0 units", t2.ma(units="0"), {m.TR: ZERO}, no_, no_, {}),
        "Z4": ("C23-12", "AK", "fee limits 0", lambda: m.ak_tree("0", "0", "0"), zero(AK), no_,
               [("ST", "Attorney Fee Limit"), ("PP", "Attorney Fee Limit"), ("AKF", "Attorney Fee Limit")], {}),
        "Z5": ("C23-12", "AK", "fee limits UNDER the coverage limits (negative fees) + all three messages",
               ak_limits(0.5, 0.5, "20000"), hand(AK),
               [("ST", "Attorney Fee Limit must be greater than CP 00 40 Limit"), ("PP", "Attorney Fee Limit must be greater than CP 00 40 Limit"),
                ("AKF", "Attorney Fee Limit must be greater than CP 00 70 Limit")], no_, {}),
        "Z6": ("C23-12", "CA", "earthquake off on building, contents, BI", with_(ca_base, ca_eq_off), hand(CA), no_, no_, {}),
        "Z7": ("C23-12", "CA", "Additional EQ manual 0", t2.ca(manual="0"), hand(CA), no_, no_, {}),
        "Z8": ("C23-12", "VA", "B and C limits blank", with_(t2.va(), va_cont("BF", CovBDemolitionLimit=None, CovCIncreasedConstructionLimit=None),
                                                           va_cont("T", CovBDemolitionLimit=None, CovCIncreasedConstructionLimit=None)), hand(VA), no_, no_, {}),
        "Z9": ("C23-12", "VA", "pollutant clean-up premium 0", with_(t2.va(), va_cont("BF", PollutantCleanupPremium="0")), hand(VA), no_, no_, {}),
        "Z10": ("C23-12", "VA", "CovType blank: broad Cov A ON, tenants' Cov A OFF", with_(t2.va(), va_cont("BF", CovType=None), va_cont("T", CovType=None)),
                hand(VA), no_, no_, {}),
        # ------------------------------------------------------------ C23-13 messages
        "MS": ("C23-13", "MA", "remediation with 2 extra buildings and the credit: both MA messages silent", t2.ma(), hand(MA), no_,
               [("PC", "CP 04 44 must be attached"), ("LOC", "There are more buildings")], {}),
        "MC1": ("C23-13", "CA", "Limited EQ sub-limits over the risk limits", t2.ca(lim=("9000000", "9000000", "9000000")), hand(CA),
                [("LEQB", "The Sub Limit entered cannot be greater than the Risk Level Limit"),
                 ("LEQP", "The Sub Limit entered cannot be greater than the Risk Level Limit"),
                 ("LEQBI", "The Sub Limit entered cannot be greater than the Risk Level Limit")], no_, {}),
        "MC2": ("C23-13", "CA", "residential class 0074: the class messages silent", with_(ca_base, st_set(ClassCode="0074"), oc_set(ClassCode="0074")),
                hand(CA), no_, [("ST", "only valid with residential class codes"), ("PP", "only valid with property in residential class codes")], {}),
        "MC3": ("C23-13", "CA", "EQ sprinkler leakage only on building and contents", with_(ca_base, st_set(EQSprinklerLeakageOnly="Yes"),
                                                                                            pp_set(EQSprinklerLeakageOnly="Yes")), hand(CA),
                [("ST", "EQ Sprinkler Leakage only is not valid with CP 10 43"), ("PP", "EQ Sprinkler Leakage only is not valid with CP 10 43")], no_, {}),
        "MC4": ("C23-13", "CA", "contents on the Legal Liability form (Limited EQ's Legal Liability branch)", with_(ca_base, ll_contents), hand(CA),
                [("PP", "CP 10 43 not valid with selected Coverage")], no_, {}),
        "MC5": ("C23-13", "CA", "building Legal Liability with Additional EQ", with_(ca_base, ll_structure), hand(CA),
                [("ST", "CP 01 41 not valid with selected Coverage")], no_, {}),
        "MC6": ("C23-13", "CA", "Additional EQ with CP 10 45", with_(t2.ca(lim=("0", "0", "0")), ca_sublimit(False)), {m.ADDEQ: None},
                [("ST", "CP 01 41 not valid with CP 10 45")], no_, {}),
        "MC7": ("C23-13", "CA", "Additional EQ with CP 10 29", with_(t2.ca(lim=("0", "0", "0")), ca_sublimit(True)), {m.ADDEQ: None},
                [("ST", "CP 01 41 not valid with CP 10 29")], no_, {}),
        "MC8": ("C23-13", "CA", "EQ deductible 20% with Limited EQ", with_(ca_base, st_set(EQDeductible="20%")), hand(CA),
                [("ST", "EQ Deductible can only be up to 15% when CP 1043 is attached")], no_, {}),
        "MC9": ("C23-13", "CA", "CP 10 41 with no earthquake form", with_(t2.ca(lim=("0", "0", "0"), manual=None), inception), {},
                [("LOC", "CP 10 41 is not valid without an Earthquake Cause of Loss Form")], no_, {}),
        "MV1": ("C23-13", "VA", "CP 04 06 on Builders Risk", with_(va_only_bf(), st_set(CovType="Builders Risk")), hand(VA),
                [("ST", "CP 04 06 not valid with selected Coverage")], no_, {}),
        "MV2": ("C23-13", "VA", "coinsurance 50% with both forms (tenants' on I&B)", with_(va_tenants_ib(), st_set(Coinsurance="50%")), hand(VA),
                [("ST", "Minimum 80% Coinsurance requirement with CP 04 27")], [("ST", "Minimum 80% Coinsurance requirement with CP 04 06")], {}),
        "MV2b": ("C23-13", "VA", "coinsurance 50% with the broad form", with_(va_only_bf(), st_set(Coinsurance="50%")), hand(VA),
                 [("ST", "Minimum 80% Coinsurance requirement with CP 04 06")], no_, {}),
        "MV3": ("C23-13", "VA", "actual cash value with Coverage C (broad form)", with_(va_only_bf(), st_set(ValuationType="Actual Cash Value")), hand(VA),
                [("ST", "Replacement Cost Valuation is required when Coverage C - Increased Cost of Construction applies to CP 04 06")], no_, {}),
        "MV3b": ("C23-13", "VA", "replacement cost: silent (both forms' rules)", with_(va_only_bf(), st_set(ValuationType="Replacement Cost")), hand(VA),
                 no_, [("ST", "Replacement Cost Valuation is required")], {}),
        "MV3c": ("C23-13", "VA", "actual cash value with Coverage C (tenants' form)", with_(va_tenants_ib(), st_set(ValuationType="Actual Cash Value")), hand(VA),
                 [("ST", "Replacement Cost Valuation is required when Coverage C - Increased Cost of Construction applies to CP 04 27")], no_, {}),
        "MV4": ("C23-13", "VA", "CP 04 06 beside the countrywide CP 04 05", with_(va_only_bf(), cw_ol), hand(VA),
                [("ST", "CP 04 06 and CP 04 05 cannot be attached on the same Building")], no_, {}),
        "MV5": ("C23-13", "VA", "CP 04 06 on an I&B item", with_(va_only_bf(), st_set(CovType="Improvements and Betterments")), hand(VA),
                [("ST", "Form CP 04 06 cannot be attached with the coverage selected")], no_, {}),
        "MV6": ("C23-13", "VA", "CP 04 27 on a Building item", with_(t2.va(), lambda s: at(s)[P + "Structure"].pop(P + m.VABF + "Table")), hand(VA),
                [("ST", "Form CP 04 27 cannot be attached with the coverage selected")], no_, {}),
        "MV7": ("C23-13", "VA", "I&B with CP 04 27 and the contents in a blanket", with_(va_tenants_ib(), pp_blanket),
                hand(VA), [("ST", "Coverage Improvements And Betterments cannot be written as part of an item also covering Personal Property")], no_, {}),
        "MV7b": ("C23-13", "VA", "I&B with CP 04 27, PersPropertyIncludedInBlanket 'Yes' SUBMITTED, contents not blanketed: overwritten, silent",
                 with_(va_tenants_ib(), st_set(PersPropertyIncludedInBlanket="Yes")), hand(VA), no_,
                 [("ST", "Coverage Improvements And Betterments cannot be written")], {}),
        "MV8": ("C23-13", "VA", "CP 04 26 beside CP 04 27", with_(va_tenants_ib(), cw_tenants), hand(VA),
                [("ST", "CP 04 26 and CP 04 27 cannot be attached on the same Building")], no_, {}),
        # ------------------------------------------------------------ C23-14 shared names: submitted values survive
        "S1": ("C23-14", "VA", "broad-form Factor 2.0 submitted", with_(va_only_bf(), va_cont("BF", Factor="2.0")), hand(VA), no_, no_,
               {("BF", "Factor"): D("2.0")}),
        "S2": ("C23-14", "VA", "broad-form PostLossFactor 1.5 submitted (option 'No')", with_(va_only_bf(), va_cont("BF", PostLossFactor="1.5")), hand(VA),
               no_, no_, {("BF", "PostLossFactor"): D("1.5")}),
        "S3": ("C23-14", "AK", "building fee LimitToUse 3 submitted", with_(t2.ak(), lambda s: at(s)[P + "Structure"][P + m.AKS + "Table"][P + m.AKS][0].update(LimitToUse="3")),
               hand(AK), no_, no_, {(m.AKS, "LimitToUse"): D(3)}),
        "S4": ("C23-14", "MA", "HeatingOilBaseLossCost 100 submitted", with_(t2.ma(), lambda s: at(s)[P + "Structure"][P + m.HO + "Table"][P + m.HO][0].update(HeatingOilBaseLossCost="100")),
               hand(MA), no_, no_, {"HeatingOilBaseLossCost": D(100)}),
        "S5": ("C23-14", "MA", "TotalPollutantCleanUpCredit 5 submitted", with_(t2.ma(), lambda s: at(s)[P + "Location"][P + m.HOC].update(TotalPollutantCleanUpCredit="5")),
               hand(MA), no_, no_, {"TotalPollutantCleanUpCredit": D(5)}),
        "S6": ("C23-14", "MA", "BasePremium 500 submitted", with_(t2.ma(), lambda s: at(s)[P + "Structure"][P + m.HO + "Table"][P + m.HO][0].update(BasePremium="500")),
               hand(MA), no_, no_, {"BasePremium": D(500)}),
        # ------------------------------------------------------------ C23-15 exclusions
        "X1": ("C23-15", "VA", "both VA forms + cyber exclusion, B / C / B&C 2,000,000 / 3,000,000 / 5,000,000",
               with_(t2.va(), va_cont("BF", CovBDemolitionLimit="2000000", CovCIncreasedConstructionLimit="3000000"),
                     va_cont("T", CovBDemolitionLimit="2000000", CovCIncreasedConstructionLimit="3000000"), cyber("plain")), hand(VA), no_, no_, {}),
        "X2": ("C23-15", "VA", "the same with the ensuing-causes cyber form",
               with_(t2.va(), va_cont("BF", CovBDemolitionLimit="2000000", CovCIncreasedConstructionLimit="3000000"),
                     va_cont("T", CovBDemolitionLimit="2000000", CovCIncreasedConstructionLimit="3000000"), cyber("col")), hand(VA), no_, no_, {}),
        "X3": ("C23-15", "CA", "Limited / Additional EQ + cyber exclusion", with_(t2.ca(), cyber("plain")), hand(CA), no_, no_, {}),
        "X4": ("C23-15", "AK", "fees + cyber exclusion", with_(t2.ak(), cyber("plain")), hand(AK), no_, no_, {}),
        "X5": ("C23-15", "MA", "heating oil + relocation + cyber exclusion", with_(t2.ma(), cyber("plain")), hand(MA), no_, no_, {}),
    }


# ---------------------------------------------------------------- checks

def count_hits(tagged, level, frag):
    return sum(1 for t, x in tagged if t == level and frag in x)


def check_msgs(tagged, must, mustnt):
    bad = []
    for (level, frag), k in collections.Counter((L[a], b) for a, b in must).items():
        got = count_hits(tagged, level, frag)
        if got != k:
            bad.append(f"{level.replace(P, '') or 'policy'}: {frag[:70]} ({got}, predicted {k})")
    for a, b in mustnt:
        if count_hits(tagged, L[a], b):
            bad.append(f"unexpected {L[a].replace(P, '')}: {b[:70]}")
    return bad


def iso_tagged(resp):
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
                    out.append((lvl(ids.get(e.get("ErcMessageTableId"), "?")), e["Description"]))
    return out


def predictions(j, data, recs, ovr):
    m.OVR.clear()
    m.OVR.update(ovr)
    out, lines, bad = {}, [], []
    try:
        for rec, how in recs.items():
            res = m.predict(j, data, rec)
            eng = [e for _, _, e in res]
            if how == ZERO:
                hv = [D(0)] * len(res)
                ok = all(m.same(e, 0) for e in eng)
            elif not res:                                 # the record was not attached (or was removed): no premium
                hv, ok = [], True
            else:
                hv = [x for x, _, _ in res]
                # 174_'s evaluator cannot skip a blank operand the way ISO and the engine do (OI-110): where it fails on a
                # blank, the hand model and the engine must still agree
                ok = all(m.same(x, e) and (m.same(ev, e) or "ConversionSyntax" in str(ev)) for x, ev, e in res)
            out[rec] = hv
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-58:]:58s} predicted {[str(x) for x in hv]} evaluator {[str(x) for _, x, _ in res]} engine {eng}")
            if not ok:
                bad.append(rec)
    finally:
        m.OVR.clear()
    return out, lines, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, recs, must, mustnt, ovr)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        TAGGED.clear()
        data, ip, err = m.rated(build(), j)
        if err:
            print(f"{cid:5s} {task} {j} {label}: RAISED {err}")
            FAIL.append(cid)
            continue
        tagged = [(lvl(t), x) for t, x in TAGGED]
        preds[cid], lines, bad = predictions(j, data, recs, ovr)
        mbad = check_msgs(tagged, must, mustnt)
        print(f"{cid:5s} {task} {j} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS'} "
              f"({len(recs)} records; messages {len(must)} required, {len(mustnt)} forbidden{': ' + '; '.join(mbad) if mbad else ', ok'})")
        shown = [x for x in lines if not ("engine ['0']" in x and x.lstrip().startswith("ok")) and "engine []" not in x] if j == "VA" else lines
        if shown:
            print("\n".join(shown[:14]))
        if bad or mbad:
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, the (level, message) multiset):")
        for i, (cid, (task, j, label, build, recs, must, mustnt, ovr)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = t2.state_req(t2.m20.payload(build()), j)
            (gc.OUT / f"chunk23_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,260})', str(exc.body))
                print(f"  {cid:5s} ISO REFUSES {mm_.group(0)[:280] if mm_ else str(exc.body)[:280]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk23_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not m.same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not m.same(x, 0)]
                if sorted(D(str(x)) for x in iso) != sorted(D(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            TAGGED.clear()
            data, ip = rep.cmp.rate(req)
            ours = collections.Counter((lvl(t), x) for t, x in TAGGED)
            isos = collections.Counter(iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mreq = check_msgs(list(isos.elements()), must, mustnt)
            ok = not pbad and not dd and ours == isos and not mreq
            print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(dd)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
                  + (f"; against the prediction: {mreq}" if mreq else "")
                  + "".join(f"\n        predicted {rr[-55:]}: ISO {x}, derived {w}" for rr, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (isos - ours).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (ours - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C23-12..C23-15): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
