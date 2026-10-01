#!/usr/bin/env python3
"""Chunk 22, RC-3 (C22-13..C22-16): zero cases, messages, shared names and exclusion records, every one a
multi-location ISO probe.

Every case is 215_'s two-location Oregon policy (or a state's portable policy) with one thing changed. Each
chunk 22 record is predicted before the run (215_'s hand model, 174_'s evaluator and the engine; an explicit
figure where the case overrides a field). Each case names the messages that must appear and must not, as
(level, text) pairs: the level is the table that raised it (MessageHelper's TableName, captured here; on ISO's
side the node carrying the message's ErcMessageTableId). --live compares the predicted records, every premium
field for field, and the whole (level, message) multiset.

C22-13  ZERO CASES                                            C22-14  MESSAGES (40 in scope; see the census)
  Z1  VR Form, no General Information                           M1-M4  CP 10 45 / CP 10 29 with CP 13 10 and with CP 13 20
  Z2  contents indicator "Used" submitted on row 1 only          M5  CP 12 30 with CP 13 10
      (GI "Not Used"): row 1 reads the GI's MLAR 0 -> $0         M6/M7  CP 13 10 / CP 13 20 on the Legal Liability form
  Z3  Estimated Average Value on "Not Used"                      M8a/b  SPP form: silent in OR, fires in KS (state rewrite)
  Z4  Average Value blank on "Not Used" (prices on Limit)        M9  both forms; M10 AL EQ mismatch; M11 AL coinsurance
  Z5  AL General Information, no Provisions                     M12/b  CP 13 30 without / with CP 13 10; M13 CP 13 30 form
  Z6  AL on blanketed contents   Z7  AL with Agreed Value        M14/M15  CP 99 10 limit 0 / on the Legal Liability form
  Z8  AL Provisions, no General Information                     M16/b  contents EQ coinsurance 70%: silent on VR, fires off it
  Z9  VR General Information, no VR Form (90%)                  M17  AL cause mismatch; M18 VR blanket vs GI cause
  Z10 AL OverallLimit 0                                         M19/M20  alcoholic beverage tax values without / with CP 99 10
                                                                M21-M23  Public Institutional Plan with CP 13 10 (AL KS RI)
  Behind OI-119 (a "Used" policy is refused at ISO): the new-business Average Value, the cause-of-loss-same-on-every-
  VR-record rule, and the two "average limit available" rules. No case: they cannot fire on a priced policy.
  CA CP 10 43 (2 messages): C22-17.
C22-15  SHARED NAMES: S1 AL GI CoinsuranceFactor 1.5 submitted (IsNull-guarded: survives), S2 VR GI TotalIncLocsLimit
        50,000 submitted over 10,000 of components (guarded: survives), S3 contents LimitToUse 50,000 on row 1 under
        VR (guarded: survives), S4 AL GI BasicGroupIMLAR 0.5 submitted (no guard: overwritten). Both readings differ.
C22-16  EXCLUSIONS at large limits: X0 VR Broad, no cyber (control); X1 VR Broad + the cyber exclusion (the VR Form's
        Broad record reads CyberIncidentExclusionFactorBroad TWICE: x 0.995 x 0.995, not x 0.995 x 1); X2 the same
        with the ensuing-causes cyber form (its Broad COL factor is never read: x 1 x 1); X3 AL Special + cyber;
        W1 VR + the contents' windstorm-or-hail exclusion: the GI's indicator and peril stat code.

    python scripts/cf/216_chunk22_rc3.py [--live] [--cases Z1,M9]
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

m = import_module("215_chunk22_rc2")
h, r2, rc1, g19, gc, rep, cmp, r11 = m.h, m.r2, m.rc1, m.g19, m.gc, m.rep, m.cmp, m.r11
P, VR, AL, r, same = m.P, m.VR, m.AL, m.r, m.same
r11.NUMERIC |= {"EQSubLimitPercent", "TotalIncLocsLimit", "LimitToUse", "EstdAvgValIncldgValOfAlcoholicBeverageTaxes",
                "AvgValIncldgValOfAlcoholicBeverageTaxes", "CoinsuranceFactor", "BasicGroupIMLAR"}
FAIL = []
ZERO = "zero"
L = {"PP": P + "PersonalProperty", "CP": P, "VRF": P + VR, "ST": P + "Structure"}
VR_ALL = m.VR_RECS + [VR + "GeneralInformation"]
AL_ALL = m.AL_GI_RECS + m.AL_PR_RECS
LL = "Legal Liability Coverage Form"

# ---------------------------------------------------------------- the level each message was raised at
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ---------------------------------------------------------------- trees

def tree(j="OR", vr=None, al=False, cause="Special", limits=("100000", "500000"), gi=None, vrf=None, eq=False,
         coins="Monthly Reporting", al_coins="90%", al_gi=True, al_prov=True, vr_gi=True, vr_form=True, pre=None, full=None):
    """215_'s tree, state-aware, with each form's two halves switchable and a hook run before the location copy."""
    sub = g19.with_cause(g19.portable(j), cause)
    if eq:
        m.eq_contents(sub)
    if pre:
        pre(sub)
    pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
    if vr is not None:
        pp["Coinsurance"] = coins
        if vr_gi:
            r2.put(sub, VR + "GeneralInformation", dict(h.VR_GI, MultiLocAvgRates=vr, CauseOfLoss=cause,
                                                         EQCauseOfLoss="Yes" if eq else "No", **(gi or {})), state=j)
        if vr_form:
            r2.put(sub, VR, dict({"AvgVal": "40000", "SpecificIns": "0", "SeasonalRisk": "No"}, **(vrf or {})), state=j)
    if al:
        if al_gi:
            r2.put(sub, AL + "GeneralInformation", dict(h.AL_GI, CauseOfLoss=cause, Coinsurance=al_coins, **(gi or {})), state=j)
        if al_prov:
            r2.put(sub, AL + "Provisions", {"FullValue": "0"}, state=j)
            pp["Coinsurance"] = al_coins
    ls = h.locations(sub)
    for k in range(1, len(limits)):
        ls.append(copy.deepcopy(ls[0]))
        ls[k]["LocationNumber"] = str(k + 1)
    for k, lim in enumerate(limits):
        c = h.contents(ls[k])
        c["Limit"] = lim
        if al and al_prov:
            fv = (full or limits)[k]
            c[P + AL + "ProvisionsTable"][P + AL + "Provisions"][0]["FullValue"] = fv
            c["FullPrsnlPropValue"] = fv
    return sub


def each(sub, level, **fields):
    for loc in h.locations(sub):
        st = loc[P + "StructureTable"][P + "Structure"][0]
        oc = st[P + "OccupClassTable"][P + "OccupClass"][0]
        node = {"Location": loc, "Structure": st, "OccupClass": oc, "PersonalProperty": h.contents(loc)}[level]
        node.update(fields)
    return sub


def with_(build, *fns):
    def b():
        sub = build()
        for fn in fns:
            fn(sub)
        return sub
    return b


def T(**kw):
    return lambda: tree(**kw)


def eq_sublimit(flat):
    def pre(sub):
        at = rc1.node_dicts(sub)
        at[P + "Structure"]["EQSubLimitPercent"] = "25"
        at[P + "Location"]["EQCauseOfLossForm"] = "Earthquake Sub-Limit Form (CP 10 29)" if flat else "Earthquake Sub-Limit Form (CP 10 45)"
        if flat:      # every EQ-elected coverage on the flat form carries a flat deductible (195_'s first live run)
            for k in ("Structure", "PersonalProperty", "SpecialClass"):
                at[P + k]["EQDeductible"] = "5,000"
    return pre


def put0(rec, fields=None):
    return lambda sub: r2.put(sub, rec, dict(fields or {}))


def blanket(coins):
    def f(sub):
        m.blanket(sub)
        sub[P + "Table"][P][0][P + "BlanketRatingTable"][P + "BlanketRating"][0][P + "BlanketRatingDetailTable"][
            P + "BlanketRatingDetail"][0]["Coinsurance"] = coins
    return f


def row1_indicator_used(sub):
    h.contents(h.locations(sub)[0])["MultiLocAvgRatesIndicator"] = "Used"


def row1_limit_to_use(sub):
    h.contents(h.locations(sub)[0])["LimitToUse"] = "50000"


def cyber(kind):
    def f(sub):
        tab = "CyberIncidentExclusion" if kind == "plain" else "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"
        sub[P + "Table"][P][0][P + tab + "Table"] = {P + tab: [{}]}
    return f


def pip(sub):
    for lv in ("Structure", "OccupClass", "PersonalProperty"):
        each(sub, lv, PublicInstitutionalPlanApply="Yes")


# ---------------------------------------------------------------- explicit predictions (overrides)

def z2_vr(data, rec):
    """row 1's indicator was submitted "Used": its VR records read the VR Form's MLAR (the GI's, 0 on "Not Used")."""
    out = []
    for n in rc1.find(data, P + rec):
        pp = m.up(n, 3)
        out.append(Decimal(0) if m.val(pp, "MultiLocAvgRatesIndicator") == "Used" else m.vr_hand(n, rec))
    return out


def s1_al(data, rec):
    keep = m.ALSC_90
    m.ALSC_90 = Decimal("1.5")
    try:
        return [m.al_hand(n, rec) for n in rc1.find(data, P + rec)]
    finally:
        m.ALSC_90 = keep


def s2_gi(data, rec):
    twin = m.h.rated(tree(vr="Not Used", gi={"YourBusnPrsnlPropInc": "50000"}))[0]
    return [m.vr_gi_hand(n) for n in rc1.find(twin, P + rec)]


def s3_vr(data, rec):
    out = []
    g = rec[len(VR):-len("Coverage")]
    for n in rc1.find(data, P + rec):
        pp, cp = m.up(n, 3), m.root(n)
        if m.val(pp, "LimitToUse") == "50000" and g in ("BasicGroupI", "BasicGroupII", "Special"):
            out.append(m.mods(r(m.d(pp, f"Final{g}Rate") * 50000 / 100, 0), cp, pp, m.GRP[g]))
        else:
            out.append(m.vr_hand(n, rec))
    return out


# ---------------------------------------------------------------- cases

def cases():
    al = dict(al=True, full=("200000", "100000"))
    big_vr = dict(vr="Not Used", cause="Broad", limits=("1000000", "5000000"))
    big_al = dict(al=True, limits=("1000000", "5000000"), gi={"YourBusnPrsnlPropInc": "100000", "OverallLimit": "6000000"})
    no_ = []
    return {
        # ------------------------------------------------------------ C22-13 zero cases
        "Z1": ("C22-13", "OR", "VR Form, no General Information", T(vr="Not Used", vr_gi=False), {r_: None for r_ in m.VR_RECS},
               [("PP", "Value Reporting General Information must be attached")] * 2, [("CP", "Missing required occurrence of CP 13 10")]),
        "Z2": ("C22-13", "OR", "contents indicator 'Used' submitted on row 1, GI 'Not Used'",
               with_(T(vr="Not Used"), row1_indicator_used), {r_: z2_vr for r_ in m.VR_RECS[:4]},
               [("VRF", "An Average Value is only valid when Multiple Location Average Rates selection is Used")], no_),
        "Z3": ("C22-13", "OR", "Estimated Average Value 30,000 on 'Not Used'", T(vr="Not Used", vrf={"EstdAvgVal": "30000"}),
               {r_: None for r_ in VR_ALL},
               [("VRF", "An Estimated Average Value cannot be entered when Multiple Location Average Rates selection is Not Used")] * 2, no_),
        "Z4": ("C22-13", "OR", "Average Value blank on 'Not Used' (priced on the Limit)",
               with_(T(vr="Not Used"), lambda s: [h.contents(lc)[P + VR + "Table"][P + VR][0].pop("AvgVal") for lc in h.locations(s)]),
               {r_: None for r_ in VR_ALL}, no_, [("VRF", "An Average Value is only valid")]),
        "Z5": ("C22-13", "OR", "AL General Information, no Provisions", T(al=True, al_prov=False), {r_: None for r_ in m.AL_GI_RECS},
               [("CP", "Missing required occurrence of CP 13 20")], no_),
        "Z6": ("C22-13", "OR", "AL on blanketed contents (90% blanket)", with_(T(**al), blanket("90%")), {r_: None for r_ in AL_ALL},
               [("PP", "CP 13 20 not valid with Blanket Rating")] * 2, no_),
        "Z7": ("C22-13", "OR", "AL with Agreed Value on the contents", with_(T(**al), lambda s: each(s, "PersonalProperty", AgreedValueOption="Yes")),
               {r_: None for r_ in AL_ALL}, [("PP", "Agreed Value Coverage is not valid with CP 13 20")] * 2, no_),
        "Z8": ("C22-13", "OR", "AL Provisions, no General Information", T(al=True, al_gi=False), {r_: ZERO for r_ in m.AL_PR_RECS},
               [("PP", "Additional Locations Special Coinsurance General Information must be attached")] * 2, no_),
        "Z9": ("C22-13", "OR", "VR General Information, contents at 90% (no VR Form survives)", T(vr="Not Used", coins="90%"),
               {VR + "GeneralInformation": None}, [("CP", "Missing required occurrence of CP 13 10")], no_),
        "Z10": ("C22-13", "OR", "AL OverallLimit 0", T(al=True, full=("200000", "100000"), gi={"OverallLimit": "0"}),
                {r_: None for r_ in m.AL_PR_RECS}, no_, no_),
        # ------------------------------------------------------------ C22-14 messages
        "M1": ("C22-14", "OR", "VR + EQ sub-limit CP 10 45", T(vr="Not Used", eq=True, pre=eq_sublimit(False)), {},
               [("PP", "CP 10 45 not valid with CP 13 10")] * 2, no_),
        "M2": ("C22-14", "OR", "AL + EQ sub-limit CP 10 45", T(eq=True, pre=eq_sublimit(False), **al), {},
               [("PP", "CP 13 20 not valid with Earthquake Sub-Limit Form (CP 10 45)")] * 2, no_),
        "M3": ("C22-14", "OR", "VR + EQ sub-limit CP 10 29", T(vr="Not Used", eq=True, pre=eq_sublimit(True)), {},
               [("PP", "CP 10 29 not valid with CP 13 10")] * 2, no_),
        "M4": ("C22-14", "OR", "AL + EQ sub-limit CP 10 29", T(eq=True, pre=eq_sublimit(True), **al), {},
               [("PP", "CP 13 20 not valid with Earthquake Sub-Limit Form (CP 10 29)")] * 2, no_),
        "M5": ("C22-14", "OR", "VR + Peak Season (CP 12 30)", T(vr="Not Used", pre=put0("PeakSeasonLimitOfInsurance")), {},
               [("PP", "CP 12 30 not valid with CP 13 10")] * 2, no_),
        "M6": ("C22-14", "OR", "VR on the Legal Liability form", with_(T(vr="Not Used"), lambda s: each(s, "OccupClass", CovForm=LL)), {},
               [("PP", "CP 13 10 not valid with selected Coverage Form")] * 2, no_),
        "M7": ("C22-14", "OR", "AL on the Legal Liability form", with_(T(**al), lambda s: each(s, "OccupClass", CovForm=LL)), {},
               [("PP", "CP 13 20 not valid with selected Coverage Form")] * 2, no_),
        "M8a": ("C22-14", "OR", "VR on an SPP (CW accepts the SPP form)",
                with_(T(vr="Not Used"), lambda s: s[P + "Table"][P][0].update(PolicyType="Standard Property Policy"),
                      lambda s: each(s, "OccupClass", CovForm="Standard Property Policy")), {},
                no_, [("PP", "CP 13 10 not valid with selected Coverage Form")]),
        "M8b": ("C22-14", "KS", "VR on an SPP in KS (KS's rewrite drops the SPP form)",
                with_(T(j="KS", vr="Not Used"), lambda s: s[P + "Table"][P][0].update(PolicyType="Standard Property Policy"),
                      lambda s: each(s, "OccupClass", CovForm="Standard Property Policy")), {},
                [("PP", "CP 13 10 not valid with selected Coverage Form")] * 2, no_),
        # the contents stay on Monthly Reporting (else the VR Form is removed), so the AL coinsurance check fires too
        "M9": ("C22-14", "OR", "both forms on every row", with_(T(vr="Not Used", **al), lambda s: each(s, "PersonalProperty", Coinsurance="Monthly Reporting")),
               {}, [("PP", "CP 13 10 and CP 13 20 are not valid together")] * 2
               + [("PP", "Coinsurance selections must be identical between CP DS 04")] * 2, no_),
        "M10": ("C22-14", "OR", "AL GI EQ 'No', contents EQ elected", T(eq=True, gi={"EQCovIndicator": "No"}, **al), {},
                [("PP", "EQ coverage selection must be the same for all instances of CP 13 20")] * 2, no_),
        "M11": ("C22-14", "OR", "AL GI 90%, contents 80%", with_(T(**al), lambda s: each(s, "PersonalProperty", Coinsurance="80%")), {},
                [("PP", "Coinsurance selections must be identical between CP DS 04")] * 2, no_),
        "M12": ("C22-14", "OR", "CP 13 30 without CP 13 10", T(pre=put0("AgriculturalProductsStorage")), {},
                [("PP", "CP 13 30 not valid without CP 13 10")] * 2, no_),
        "M12b": ("C22-14", "OR", "CP 13 30 with CP 13 10", T(vr="Not Used", pre=put0("AgriculturalProductsStorage")), {},
                 no_, [("PP", "CP 13 30 not valid without CP 13 10")]),
        "M13": ("C22-14", "OR", "CP 13 30 on the Legal Liability form",
                with_(T(vr="Not Used", pre=put0("AgriculturalProductsStorage")), lambda s: each(s, "OccupClass", CovForm=LL)), {},
                [("PP", "CP 13 30 not valid with selected Coverage Form")] * 2, no_),
        "M14": ("C22-14", "OR", "CP 99 10 with limit 0", T(vr="Not Used", pre=put0("AlcoholicBeveragesTaxExclusion", {"Limit": "0"})), {},
                [("PP", "CP 99 10 Limit must be greater than 0")] * 2, no_),
        "M15": ("C22-14", "OR", "CP 99 10 on the Legal Liability form",
                with_(T(vr="Not Used", pre=put0("AlcoholicBeveragesTaxExclusion", {"Limit": "10000"})), lambda s: each(s, "OccupClass", CovForm=LL)),
                {}, [("PP", "CP 99 10 not valid with the selected Coverage Form")] * 2, no_),
        "M16": ("C22-14", "OR", "contents EQ coinsurance 70% under VR (silent: the rule needs no VR Form)",
                with_(T(vr="Not Used", eq=True), lambda s: each(s, "PersonalProperty", EQCoinsurance="70%")), {},
                no_, [("PP", "Minimum 80% Coinsurance requirement")]),
        "M16b": ("C22-14", "OR", "contents EQ coinsurance 70%, no VR (fires)",
                 with_(T(eq=True), lambda s: each(s, "PersonalProperty", EQCoinsurance="70%")), {},
                 [("PP", "Minimum 80% Coinsurance requirement")] * 2, no_),
        "M17": ("C22-14", "OR", "AL GI Special, contents Broad", with_(T(**al), lambda s: each(s, "PersonalProperty", CauseOfLoss="Broad")), {},
                [("PP", "Cause of Loss selections must be the same on all Personal Property records regarding Additional Locations")] * 2, no_),
        "M18": ("C22-14", "OR", "VR blanket at Broad, GI at Special",
                with_(T(vr="Not Used", limits=("100000", "500000", "200000")), blanket("Monthly Reporting"),
                      lambda s: s[P + "Table"][P][0][P + "BlanketRatingTable"][P + "BlanketRating"][0][P + "BlanketRatingDetailTable"][
                          P + "BlanketRatingDetail"][0].update(CauseOfLoss="Broad")), {},
                [("CP", "Cause of Loss values must be identical between Value Reporting Blanket and Value Reporting General Information")], no_),
        "M19": ("C22-14", "OR", "alcoholic beverage tax values, no CP 99 10",
                T(vr="Not Used", vrf={"EstdAvgValIncldgValOfAlcoholicBeverageTaxes": "30000", "AvgValIncldgValOfAlcoholicBeverageTaxes": "30000"}), {},
                [("VRF", "An Estimated Average Value - Including Value of Alcoholic Beverage Taxes cannot be entered if Form CP 99 10 is not attached")] * 2
                + [("VRF", "An Average Value - Including Value of Alcoholic Beverage Taxes cannot be entered if Form CP 99 10 is not attached")] * 2
                + [("VRF", "An Average Value - Including Value of Alcoholic Beverage Taxes is only valid")] * 2, no_),
        "M20": ("C22-14", "OR", "alcoholic beverage tax values with CP 99 10, 'Not Used'",
                T(vr="Not Used", pre=put0("AlcoholicBeveragesTaxExclusion", {"Limit": "10000"}),
                  vrf={"EstdAvgValIncldgValOfAlcoholicBeverageTaxes": "30000", "AvgValIncldgValOfAlcoholicBeverageTaxes": "30000"}), {},
                [("VRF", "cannot be entered if Multiple Location Average Rates is Not Used on a New Bus")] * 2
                + [("VRF", "An Average Value - Including Value of Alcoholic Beverage Taxes is only valid")] * 2,
                [("VRF", "Form CP 99 10 is not attached")]),
        "M21": ("C22-14", "AL", "VR with the Public Institutional Plan (AL)", with_(T(j="AL", vr="Not Used"), pip), {},
                [("PP", "CP 13 10 not valid when Public And Institutional Property Plan Apply is Yes")] * 2, no_),
        "M22": ("C22-14", "KS", "VR with the Public Institutional Plan (KS)", with_(T(j="KS", vr="Not Used"), pip), {},
                [("PP", "CP 13 10 is not valid when Public And Institutional Property Plan Applies")] * 2, no_),
        "M23": ("C22-14", "RI", "VR with the Public Institutional Plan (RI)", with_(T(j="RI", vr="Not Used"), pip), {},
                [("PP", "CP 13 10 not valid when Public And Institutional Property Plan Apply Equals Yes")] * 2, no_),
        # ------------------------------------------------------------ C22-15 shared names
        "S1": ("C22-15", "OR", "AL GI CoinsuranceFactor 1.5 submitted (guarded: survives)",
               T(gi={"CoinsuranceFactor": "1.5"}, **al), {r_: s1_al for r_ in AL_ALL}, no_, no_),
        "S2": ("C22-15", "OR", "VR GI TotalIncLocsLimit 50,000 submitted over 10,000 of components (guarded: survives)",
               T(vr="Not Used", gi={"TotalIncLocsLimit": "50000"}), {VR + "GeneralInformation": s2_gi}, no_, no_),
        "S3": ("C22-15", "OR", "contents LimitToUse 50,000 submitted on row 1 under VR (guarded: survives)",
               with_(T(vr="Not Used"), row1_limit_to_use), {r_: s3_vr for r_ in m.VR_RECS}, no_, no_),
        "S4": ("C22-15", "OR", "AL GI BasicGroupIMLAR 0.5 submitted (no guard: overwritten)",
               T(gi={"BasicGroupIMLAR": "0.5"}, **al), {r_: None for r_ in AL_ALL}, no_, no_),
        # ------------------------------------------------------------ C22-16 exclusions
        "X0": ("C22-16", "OR", "VR Broad, contents 1,000,000 / 5,000,000, no cyber (control)", T(**big_vr), {r_: None for r_ in m.VR_RECS}, no_, no_),
        "X1": ("C22-16", "OR", "VR Broad + cyber exclusion (Broad reads the factor twice)", with_(T(**big_vr), cyber("plain")),
               {r_: None for r_ in m.VR_RECS}, no_, no_),
        "X2": ("C22-16", "OR", "VR Broad + cyber with ensuing-causes exceptions", with_(T(**big_vr), cyber("col")),
               {r_: None for r_ in m.VR_RECS}, no_, no_),
        "X3": ("C22-16", "OR", "AL Special at 1,000,000 / 5,000,000 + cyber exclusion", with_(T(**big_al), cyber("plain")),
               {r_: None for r_ in AL_ALL}, no_, no_),
        "W1": ("C22-16", "OR", "VR + the contents' windstorm-or-hail exclusion",
               T(vr="Not Used", pre=put0("WindstormOrHailExclusionPrsnlProp")), {r_: None for r_ in VR_ALL}, no_, no_),
    }


# ---------------------------------------------------------------- checks

def lv(k):
    return L[k]


def count_hits(tagged, level, frag):
    return sum(1 for t, x in tagged if t == level and frag in x)


def check_msgs(tagged, must, mustnt):
    bad = []
    for (level, frag), k in collections.Counter((lv(a), b) for a, b in must).items():
        got = count_hits(tagged, level, frag)
        if got != k:
            bad.append(f"{level.replace(P, '') or 'policy'}: {frag[:70]} ({got}, predicted {k})")
    for a, b in mustnt:
        if count_hits(tagged, lv(a), b):
            bad.append(f"unexpected {lv(a).replace(P, '') or 'policy'}: {b[:70]}")
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


def predictions(data, recs):
    out, lines, bad = {}, [], []
    for rec, how in recs.items():
        keep = m.hand
        if how is not None:                     # zero / explicit: the case's own prediction replaces the hand model
            m.hand = lambda node, rec_: Decimal(0)
        try:
            res = m.predict(data, rec)
        finally:
            m.hand = keep
        eng = [e for _, _, e in res]
        if how == ZERO:
            hv = [Decimal(0)] * len(res)
        elif callable(how):
            hv = how(data, rec)
        else:
            hv = [x for x, _, _ in res]
        ok = bool(res) and all(same(x, e) and same(ev, e) for x, (_, ev, e) in zip(hv, res))
        out[rec] = hv
        lines.append(f"      {'ok  ' if ok else 'FAIL'} {m.short(rec):40s} predicted {[str(x) for x in hv]}  "
                     f"evaluator {[str(ev) for _, ev, _ in res]}  engine {eng}")
        if not ok:
            bad.append(rec)
    return out, lines, bad


def state_req(req, j):
    if j != "OR":
        for c in req["body"]["CommercialProperty"]:
            c["State"] = j
        req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
    return req


STAT = ("WindstormOrHailExcludedIndicator", "VandalismExcludedIndicator", "PerilExclusionIndicatorStatCode", "Subline")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds, stat = {}, {}
    for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        TAGGED.clear()
        try:
            data, ip = gc.run(build(), j)
        except Exception as exc:
            print(f"{cid:5s} {task} {label}: RAISED {str(exc)[:160]}")
            FAIL.append(cid)
            continue
        tagged = list(TAGGED)
        preds[cid], lines, bad = predictions(data, recs)
        mbad = check_msgs(tagged, must, mustnt)
        print(f"{cid:5s} {task} {j} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS'} "
              f"({len(recs)} records; messages {len(must)} required, {len(mustnt)} forbidden{': ' + '; '.join(mbad) if mbad else ', ok'})")
        if lines:
            print("\n".join(lines))
        if cid == "W1":
            g = rc1.find(data, P + VR + "GeneralInformation")[0]
            stat[cid] = {f: m.val(g, f) for f in STAT}
            ok = stat[cid]["WindstormOrHailExcludedIndicator"] == "Yes"
            print(f"      {'ok  ' if ok else 'FAIL'} VR GI stat fields {stat[cid]} (indicator 'Yes' predicted)")
            bad = bad or ([] if ok else ["W1 indicator"])
        if bad or mbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, the (level, message) multiset):")
        for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = state_req(r11.payload(build()), j)
            (gc.OUT / f"chunk22_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,240})', str(exc.body))
                print(f"  {cid:5s} ISO REFUSES {mm_.group(0)[:260] if mm_ else str(exc.body)[:260]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk22_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
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
            extra = ""
            if cid in stat:
                iso_stat = {f: (m.iso_field(resp, VR + "GeneralInformation", f) or [None])[0] for f in STAT}
                extra = f"; stat ISO {iso_stat} ours {stat[cid]}"
                if any(str(iso_stat[f]) != str(stat[cid][f]) for f in STAT if iso_stat[f] is not None):
                    pbad.append(("stat fields", iso_stat, stat[cid]))
            ok = not pbad and not d and ours == isos and not mreq
            print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} "
                  f"({sum(isos.values())} ISO){extra}"
                  + (f"; against the prediction: {mreq}" if mreq else "")
                  + "".join(f"\n        predicted {m.short(str(rr))[:60]}: ISO {x}, derived {w}" for rr, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (isos - ours).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (ours - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C22-13..C22-16): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
