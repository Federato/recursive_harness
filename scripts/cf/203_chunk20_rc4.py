#!/usr/bin/env python3
"""Chunk 20, RC-4 (C20-19 to C20-22): states and editions.

EDITIONS (C20-21, static)  every rule of every chunk 20 family file (premium and container files) compared across
        the four countrywide editions (chunk 19's lesson: diff every rule, not only SetPremium).
ALL STATES (C20-22)  one policy per state: the portable policy (192_; FL on chunks 15-19's FL special class, no
        earthquake keys), Special, the occupancy on the Tobacco form, every chunk 20 record placed with RC-1's inputs
        (199_), the policy's fungus cover "Policy Limit". Each record predicted from THE STATE's rule (its own file if
        it files a SetPremium, else its countrywide EDITION's), hand-evaluated on the tree; a record whose rule the
        state empties (ErcRate an empty Sequence: TX Mortgageholders, NC ACP, AK / NY fungus) or switches off must
        price nothing. NC also carries its own six ACP records (CP 14 11), AK / NY their own fungus records.
PROBES (C20-19, C20-20, C20-21), each against a contrast that moves a dollar:
  P-pip-AL / KS / RI  the Public Institutional Plan on (90% coinsurance): radioactive, pier and ACP x 0.85; the
                      same state's plain run is the contrast (every one of those records must move)
  P-FL-ded / P-OR-ded the building's deductibles-by-location record (factor 0.995), radioactive rate 1.0: FL's
                      rewrite drops the factor (FL unmoved vs P-FL-nod), countrywide multiplies (OR moves)
  P-FL-fd             the location's higher limit 50,000 over the charge's own 25,000: FL's LimitToUse is its
                      own limit (25,000); the countrywide rule (F2, C20-06) takes 50,000
  P-VA-vol            VA's volunteer fire department: FireDepartmentLimit from VA's volunteer table, LimitToUse the
                      record's VolunteerLimit (30,000)
  P-VA-ol             VA's own broad-form Ordinance or Law on the building: the BI fungus records' TotalPremium $0
                      (FinalBusinessIncomeFungusPremium 0)
  P-NY-cy / P-OR-cy   CP 10 75 with Mortgageholders 20,000 at 1,000,000 and BI 2,000,000: NY's Mortgageholders and
                      EB BI rules read no cyber factor (unmoved vs P-NY-nc); OR's move
  E-FD-OR / MA / NC / MO  the location's higher limit 50,000 over the charge's own 25,000: the 2023 editions (V02
                      MO, V03 NC, V04 MA) set LimitToUse BEFORE FireDepartmentLimit, so the higher limit is compared
                      with a BLANK (found by the every-rule diff). Ours reads the blank as 0 -> 50,000 ($173), as 2026;
                      the competing reading (comparison false) -> 25,000 ($85). ISO settles it
  E-FU-OR / E-FU-MO   fungus Separate Limits, sub-limit 25,000: MO's 2023 V02 charges the excess only on "Policy
                      Limit" (ExcessOfSublimitCalc 0); 2026 charges it (found by the every-rule diff)
  E-MO / E-OR / E-NC / E-MA   Pier and Wharf on BI with LimitToUse 60,000 SUBMITTED: MO's 2023 V02 computes the
                      limit inline with no IsNull guard -> BI's 100,000; 2026 (OR), V03 (NC) and V04 (MA) keep the
                      submitted 60,000 (guarded)

    python scripts/cf/203_chunk20_rc4.py [--live] [--all] [--runs OR,P-FL-fd] [--no-editions]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import copy
import functools
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

m = import_module("200_chunk20_rc2")
rc1m = import_module("199_chunk20_rc1")
r4 = import_module("177_chunk16_rc4")
x17 = import_module("183_chunk17_rc4")
s18 = import_module("164_chunk14_c14-18_all_states")
g19 = m.g19
gc, rc1, rep, cmp, r16, r11, r2 = m.gc, m.rc1, m.rep, m.cmp, m.r16, m.r11, m.r2
P, same, val = m.P, m.same, m.val
cen = m.cen20
r11.NUMERIC |= {"LimitToUse", "VolunteerLimit", "Rate"}
FAIL = []
DEFAULT = ["OR", "AL", "AZ", "FL", "KS", "NY", "RI", "TX", "VA", "AK", "NC", "MO", "MA"]
EQ_KEYS = ("EQCovIndicator", "EQClass", "EQCoinsurance", "EQDeductible", "EQSprinklerLeakageOnly", "EQGrade")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


@functools.lru_cache(maxsize=None)
def xsd(j):
    return rc1.xsd_for(book_for(j, r2.ASOF))


@functools.lru_cache(maxsize=None)
def pop():
    return rc1m.population()


def records(j):
    """the CW premium records + the state's own premium files of the families' patterns."""
    recs = {r[len(P):] for rs in pop().values() for r in rs}
    for f in (book_for(j, r2.ASOF).state.package.content / "Rules").glob("*.xml"):
        if any(re.search(pat, f.name) for _, pat in cen.FAMILIES) and not cen.EXCLUDE.search(f.name):
            if cen.set_premium(f.read_text(encoding="utf-8-sig", errors="replace")):
                recs.add(f.name[len(P):-len("Rules.Rule.xml")])
    return sorted(recs)


# ------------------------------------------------------------ editions (static)

def edition_diff():
    eds = cen.EDITIONS
    base = eds["CW 2026 V01"] / "Rules"
    rules = lambda path: {mm.group(1): cen.norm(mm.group(0)) for mm in re.finditer(
        r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', path.read_text(encoding="utf-8-sig", errors="replace"), re.S)}
    files = sorted(f.name for f in base.glob("*.xml")
                   if any(re.search(pat, f.name) for _, pat in cen.FAMILIES) and not cen.EXCLUDE.search(f.name))
    print(f"C20-21  every rule in the {len(files)} chunk 20 family files, across the four countrywide editions")
    differ = []
    for name in files:
        ref = rules(base / name)
        for ed, root in eds.items():
            if ed == "CW 2026 V01":
                continue
            f = root / "Rules" / name
            if not f.exists():
                print(f"    {name[len(P):-14]:66s} NOT FILED in {ed}")
                differ.append((name, ed))
                continue
            other = rules(f)
            gone, new = sorted(set(ref) - set(other)), sorted(set(other) - set(ref))
            changed = sorted(r for r in set(ref) & set(other) if ref[r] != other[r])
            if gone or new or changed:
                differ.append((name, ed))
                print(f"    {name[len(P):-14]:66s} {ed}: changed {changed[:4]} only-2026 {gone[:3]} only-{ed[-3:]} {new[:3]}")
    print(f"    files x editions that differ: {len(differ)}")
    return differ


# ------------------------------------------------------------ policies

def put(sub, j, rec, fields=None, inter=None, idx=0):
    top, steps = r16.chain_down(xsd(j), rec)
    tops = [d for k, d in m.walk(sub) if k == top]
    d = tops[idx]
    for t, table in steps:
        if table:
            lst = d.setdefault(t + "Table", {t: []})[t]
            if not lst:
                lst.append({})
            d = lst[-1]
        else:
            d = d.setdefault(t, {})
        for k, v in ((inter or {}).get(r16.short(t), {})).items():
            d.setdefault(k, v)
    d.update(fields or {})
    return d


def state_base(j):
    sub = g19.with_cause(g19.portable(j), "Special")
    at = rc1.node_dicts(sub)
    if j == "FL":
        # FL does not file the five-coverage policy's special class description (OI-103); and its own EQ class scheme
        at[P + "SpecialClass"]["ClassDescription"] = r4.FL_SC
        for k in ("Structure", "SpecialClass", "BusinessIncome", "SpecialClassBusnIncome"):
            for f in EQ_KEYS:
                at[P + k].pop(f, None)
        for f in ("EQCauseOfLossForm", "EQTerr", "EQDeductibleTier"):
            at[P + "Location"].pop(f, None)
    return sub


def family(j, families=True):
    """every chunk 20 record placed with RC-1's inputs (199_'s container_fields and tree), on the state's policy."""
    sub = state_base(j)
    if not families:
        return sub
    at = rc1.node_dicts(sub)
    at[P + "OccupClass"]["CovForm"] = "Tobacco Sales Warehouse Coverage Form"
    at[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
    at[P + "BusinessIncome"][P + m.NOWAIT + "Table"] = {P + m.NOWAIT: [{"TimePeriod": "Eliminated"}]}
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
    cf = rc1m.container_fields()
    cf["ChangesFungusWetRotDryRotBacteria"] = {"SubLimit": "50000", "IncreasedPeriodOfRestoration": "90"}
    for r in records(j) + m.BIF:
        if r16.chain_down(xsd(j), r) is None:
            continue
        top, steps = r16.chain_down(xsd(j), r)
        d = rc1.node_dicts(sub)[top]
        for t, table in steps:
            if table:
                lst = d.setdefault(t + "Table", {t: []})[t]
                if not lst:
                    lst.append({})
                d = lst[-1]
            else:
                d = d.setdefault(t, {})
            for k, v in cf.get(r16.short(t), {}).items():
                d.setdefault(k, v)
    if j == "NC":            # NC's own six ACP records (CP 14 11): no premium rule
        for lv, parent in (("Bldg", "Structure"), ("SpecialClass", "SpecialClass"), ("PrsnlProp", "PersonalProperty")):
            rec = "NorthCarolinaChangesAdditionalCoveredProperty" + lv
            at[P + parent][P + rec + "Table"] = {P + rec: [{P + rec + "DetailTable": {P + rec + "Detail": [
                {"Description": m.BULK, "Limit": "30000"}]}}]}
    if j in ("AK", "NY"):    # their own fungus records (premium-less)
        own = {"AK": "AlaskaChangesFungusWetRotAndDryRot", "NY": "ChangesFungusWetRotAndDryRot"}[j]
        if r16.chain_down(xsd(j), own):
            put(sub, j, own)
    return sub


def with_(fn, build):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


def plan(sub):
    for k in ("Structure", "OccupClass", "PersonalProperty", "SpecialClass"):
        rc1.node_dicts(sub)[P + k]["PublicInstitutionalPlanApply"] = "Yes"


def ded_by_loc(on):
    def f(sub):
        for d in [d for k, d in m.walk(sub) if k == P + "RadioactiveContamination"]:
            d["Rate"] = "1.0"
        if on:
            rc1.node_dicts(sub)[P + "Structure"][P + "DeductiblesByLocationBldgTable"] = {
                P + "DeductiblesByLocationBldg": [{"Deductible": "5,000"}]}
    return f


def higher_fire(sub):
    rc1.node_dicts(sub)[P + "Location"][P + "HigherLimitsLocationTable"] = {P + "HigherLimitsLocation": [
        {"FireDepartmentChargeIndicator": "Yes", "FireDepartmentChargeLimit": "50000"}]}


def volunteer(sub):
    for d in [d for k, d in m.walk(sub) if k == P + "LocationFireDepartmentCharge"]:
        d.update({"FireDepartmentTypeApplyOnPolicyIndicator": "Yes", "VolunteerLimit": "30000"})


def ordinance_va(sub):
    rc1.node_dicts(sub)[P + "Structure"][P + "OrdinanceOrLawCoverageStateBroadFormTable"] = {
        P + "OrdinanceOrLawCoverageStateBroadForm": [{}]}


def cyber(on):
    def f(sub):
        for d in [d for k, d in m.walk(sub) if k == P + m.MORT]:
            d.update({"Limit": "1,000,000", "NumberMortgages": "20000"})
        rc1.node_dicts(sub)[P + "BusinessIncome"]["Limit"] = "2000000"
        for d in [d for k, d in m.walk(sub) if k == P + m.EBB]:     # group 7 (0.026): big enough for 0.999 to move
            d.update({"OccupancyCategory": "Industrial and Processing", "OccupancyGroup": "All other industrial and processing risks"})
        if on:
            sub["CommercialPropertyTable"]["CommercialProperty"][0][P + "CyberIncidentExclusionTable"] = {
                P + "CyberIncidentExclusion": [{}]}
    return f


def pier_bi(j):
    def b():
        sub = state_base(j)
        put(sub, j, m.PIER[1], {"Construction": m.PIER1, "Limit": "40000", "LimitToUse": "60000"})
        put(sub, j, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "WatercraftExclBuybackConstrctnOption": m.PIER1, "Limit": "30000"})
        return sub
    return b


def fire_only(j):
    sub = state_base(j)
    put(sub, j, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes", "Limit": "25000"})
    return sub


def fungus_sep(j):
    """200_'s FU2 on the state's policy: Separate Limits, sub-limit 25,000, two buildings applying, BI 120 days."""
    def b():
        sub = state_base(j)
        cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
        cp["FungusWetRotDryRotBacteriaCov"] = "Separate Limits"
        loc = rc1.node_dicts(sub)[P + "Location"]
        loc["FungusWetRotDryRotBacteriaCovLocApply"] = "No"
        sts = loc[P + "StructureTable"][P + "Structure"]
        sts.append(copy.deepcopy(sts[0]))
        for st in sts:
            st["FungusWetRotDryRotBacteriaCovStructApply"] = "Yes"
        put(sub, j, m.FUNGUS, {"SubLimit": "25000", "IncreasedPeriodOfRestoration": "120", "SeparatePremisesOrLocationsOption": "Yes"})
        for bi in [d for k, d in m.walk(sub) if k == P + "BusinessIncome"]:
            bi["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
        for i in range(2):
            for r in m.BIF:
                put(sub, j, r, idx=i)
        return sub
    return b


def gv(n, f):
    return n.first(f).text if n is not None and n.first(f) is not None else None


def node(data, rec, i=0):
    ns = r16.find(data, P + rec)
    return ns[i] if len(ns) > i else None


def probe_checks(pid, data, j):
    out = []
    if pid.startswith("P-pip"):
        out.append(("building PublicInstitutionalPlanFactor", gv(node(data, "Structure"), "PublicInstitutionalPlanFactor"),
                    val(j, "PublicInstitutionalPlanFactor", "Factor", Constant="Y")))
    if pid in ("P-FL-ded", "P-OR-ded"):
        # FL's own package EMPTIES SetDeductibleByLocationFactor (and InitializeDeductiblesByLocation): no factor at all
        out.append(("building DeductibleByLocationFactor", gv(node(data, "Structure"), "DeductibleByLocationFactor"),
                    None if j == "FL" else val(j, "DeductibleByLocationFactor", "Factor", Constant="Y")))
    if pid.startswith("E-FD"):
        # 2026 sets FireDepartmentLimit BEFORE LimitToUse; the 2023 editions (V02 / V03 / V04) the other way round, so
        # "higher limit 50,000 > FireDepartmentLimit" is evaluated while FireDepartmentLimit is still BLANK. Our
        # comparison reads the blank as 0 (true: 50,000, the same as 2026); the competing reading (a comparison with
        # a blank is false) gives 25,000, $85 against $173. The live premium comparison settles which ISO uses.
        out.append(("Fire Department LimitToUse (ours: blank read as 0; competing: 25,000)",
                    gv(node(data, "LocationFireDepartmentCharge"), "LimitToUse"), "50000"))
    if pid.startswith("E-FU"):
        # MO's 2023 V02 charges the excess of the sub-limit only on "Policy Limit"; 2026 on any cover
        mo = j == "MO"
        # 2026: 0.09 x (25,000 - 15,000) / 100 = 9, through the modifiers (0.85, 0.9, 1.15) = 8
        out.append(("fungus ExcessOfSublimitCalc", gv(node(data, m.FUNGUS), "ExcessOfSublimitCalc"), "0.0" if mo else "8"))
    if pid == "P-FL-fd":
        out.append(("Fire Department LimitToUse (own, not the higher 50,000)", gv(node(data, "LocationFireDepartmentCharge"), "LimitToUse"), "25000"))
    if pid == "P-VA-vol":
        out.append(("Fire Department FireDepartmentLimit (VA volunteer table)", gv(node(data, "LocationFireDepartmentCharge"), "FireDepartmentLimit"),
                    val(j, "FireDepartmentIncreasedLimitVolunteer", "Limit", Constant="Y")))
        out.append(("Fire Department LimitToUse (VolunteerLimit)", gv(node(data, "LocationFireDepartmentCharge"), "LimitToUse"), "30000"))
    if pid == "P-VA-ol":
        out.append(("fungus FinalBusinessIncomeFungusPremium", gv(node(data, m.FUNGUS), "FinalBusinessIncomeFungusPremium"), "0"))
    if pid in ("E-MO", "E-OR", "E-NC", "E-MA"):
        out.append(("Pier on BI LimitToUse stored", gv(node(data, m.PIER[1]), "LimitToUse"), "60000"))   # MO: the submitted value stays on the record, unused
    return out


def runs(a):
    states = a.runs.split(",") if a.runs else (s18.STATES if a.all else DEFAULT)
    out = {j: (j, lambda j=j: family(j)) for j in states if not j.startswith(("P-", "E-"))}
    probes = {
        "P-pip-AL": ("AL", with_(plan, lambda: family("AL"))), "P-pip-KS": ("KS", with_(plan, lambda: family("KS"))),
        "P-pip-RI": ("RI", with_(plan, lambda: family("RI"))),
        "P-FL-nod": ("FL", with_(ded_by_loc(False), lambda: family("FL"))), "P-FL-ded": ("FL", with_(ded_by_loc(True), lambda: family("FL"))),
        "P-OR-nod": ("OR", with_(ded_by_loc(False), lambda: family("OR"))), "P-OR-ded": ("OR", with_(ded_by_loc(True), lambda: family("OR"))),
        "P-FL-fd": ("FL", with_(higher_fire, lambda: family("FL"))),
        "P-VA-vol": ("VA", with_(volunteer, lambda: family("VA"))),
        "P-VA-ol": ("VA", with_(ordinance_va, lambda: family("VA"))),
        "P-NY-nc": ("NY", with_(cyber(False), lambda: family("NY"))), "P-NY-cy": ("NY", with_(cyber(True), lambda: family("NY"))),
        "P-OR-nc": ("OR", with_(cyber(False), lambda: family("OR"))), "P-OR-cy": ("OR", with_(cyber(True), lambda: family("OR"))),
        "E-FD-OR": ("OR", with_(higher_fire, lambda: fire_only("OR"))),
        "E-FD-MA": ("MA", with_(higher_fire, lambda: fire_only("MA"))), "E-FD-NC": ("NC", with_(higher_fire, lambda: fire_only("NC"))),
        "E-FD-MO": ("MO", with_(higher_fire, lambda: fire_only("MO"))),
        "E-FU-OR": ("OR", fungus_sep("OR")), "E-FU-MO": ("MO", fungus_sep("MO")),
        "E-MO": ("MO", pier_bi("MO")), "E-OR": ("OR", pier_bi("OR")), "E-NC": ("NC", pier_bi("NC")), "E-MA": ("MA", pier_bi("MA")),
    }
    if a.runs:
        probes = {k: v for k, v in probes.items() if k in states}
    out.update(probes)
    return out


#: (probe, contrast, records that MUST move between them, records that must NOT)
CONTRASTS = [("P-pip-AL", "AL", m.RADIO[:1] + [m.RADIO[1], m.RADIO[3]] + [m.PIER[0], m.PIER[2]] + m.ACP, []),
             ("P-pip-KS", "KS", m.RADIO[:1] + [m.RADIO[1], m.RADIO[3]] + [m.PIER[0], m.PIER[2]] + m.ACP, []),
             ("P-pip-RI", "RI", m.RADIO[:1] + [m.RADIO[1], m.RADIO[3]] + [m.PIER[0], m.PIER[2]] + m.ACP, []),
             ("P-FL-ded", "P-FL-nod", [], ["RadioactiveContamination"]),
             ("P-OR-ded", "P-OR-nod", ["RadioactiveContamination"], []),
             ("P-NY-cy", "P-NY-nc", [], [m.MORT, m.EBI + "Coverage"]),
             ("P-OR-cy", "P-OR-nc", [m.MORT, m.EBI + "Coverage"], [])]


# ------------------------------------------------------------ predictions

def rule_file(j, rec):
    bk = book_for(j, r2.ASOF)
    for pk, where in ((bk.state.package.content, "state"), (bk.parent.package.content, "edition")):
        f = pk / "Rules" / f"{P}{rec}Rules.Rule.xml"
        if f.exists():
            body = cen.set_premium(f.read_text(encoding="utf-8-sig", errors="replace"))
            if body:
                return body, where
    return None, None


def predict(j, data, rec):
    """'NONE' (must price nothing) or [hand per node]."""
    body, where = rule_file(j, rec)
    nodes_ = rc1.find(data, P + rec)
    if body is None or x17.empty_ercrate(j, rec) or not nodes_:
        return "NONE", where, [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]
    out = []
    for n in nodes_:
        cov = n.first("CoverageOnPolicyIndicator")
        b = body
        if 'FromParam="LimitToUseParam"' in b:
            # MO's 2023 V02 computes LimitToUse inline (rule LimitToUse, no IsNull guard): own Limit if blanketed,
            # else the parent's Limit -- substituted by hand, the one construct 174_'s evaluator does not run
            src = "Limit" if gv(n, "IncludedInBlkt") == "Yes" else "../../Limit"
            b = re.sub(r'<rul:Value[^>]*FromParam="LimitToUseParam"\s*/>', f'<rul:FirstValue FromDataDef="{src}" />', b)
            b = re.sub(r'<rul:Arg[^>]*Param="LimitToUseParam"[^>]*>.*?</rul:Arg>', "", b, flags=re.S)
        out.append(Decimal(0) if cov is not None and cov.text == "0" else r16.hand(b, n))
    return out, where, [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--all", action="store_true", help="C20-22: all 46 in-force states (Puerto Rico excluded)")
    ap.add_argument("--runs")
    ap.add_argument("--no-editions", action="store_true")
    a = ap.parse_args()
    if not a.no_editions:
        progress(0, 1, "edition diff")
        edition_diff()
        print()
    rs = runs(a)
    results = {}
    for i, (rid, (j, build)) in enumerate(rs.items(), 1):
        progress(i, len(rs), f"engine {rid}")
        try:
            data, ip = gc.run(build(), j)
        except (InterpretError, LookupError) as exc:
            print(f"  {rid:9s} RAISED {str(exc)[:160]}")
            FAIL.append(rid)
            continue
        preds, bad, on_state, priced = {}, [], 0, 0
        for rec in records(j):
            p, where, eng = predict(j, data, rec)
            preds[rec] = p
            on_state += where == "state"
            if p == "NONE":
                if not all(r4.zeroish(e) for e in eng):
                    bad.append((rec, "nothing", eng))
                continue
            if any(str(h).startswith("hand") for h in p) or [Decimal(str(e or 0)) for e in eng] != [Decimal(str(h)) for h in p]:
                bad.append((rec, [str(h) for h in p], eng))
            priced += any(not same(h, 0) for h in p)
        fc = probe_checks(rid, data, j)
        fbad = [c for c in fc if not same(c[1], c[2])]
        results[rid] = (j, build, preds)
        none = sorted(r16.short(r) for r, v in preds.items() if v == "NONE")
        print(f"  {rid:9s} {book_for(j, r2.ASOF).parent.package.content.name[-12:]:12s} engine {'as derived' if not bad and not fbad else 'DIFFERS'}: "
              f"{len(preds) - len(bad)} of {len(preds)} records ({on_state} on the state's own SetPremium), {priced} priced"
              + (f"; price nothing: {', '.join(none)[:170]}" if none else ""))
        for name, got, want in fc:
            print(f"      {'ok  ' if same(got, want) else 'FAIL'} {name:58s} tree {got}  independent {want}")
        for r, w, e in bad[:6]:
            print(f"      FAIL {r16.short(r)[:60]:60s} predicted {w} engine {e}")
        if bad or fbad:
            FAIL.append(rid)
    for pid, cid, move, still in CONTRASTS:
        if pid in results and cid in results:
            a_, b_ = results[pid][2], results[cid][2]
            for rec in move:
                if a_.get(rec) == b_.get(rec):
                    print(f"      FAIL {pid} vs {cid}: {r16.short(rec)} does not move ({a_.get(rec)})")
                    FAIL.append(f"{pid} {rec}")
            for rec in still:
                if a_.get(rec) != b_.get(rec):
                    print(f"      FAIL {pid} vs {cid}: {r16.short(rec)} moved ({b_.get(rec)} -> {a_.get(rec)})")
                    FAIL.append(f"{pid} {rec}")
            print(f"      contrast {pid} vs {cid}: " + "; ".join(f"{r16.short(r)[:34]} {b_.get(r)} -> {a_.get(r)}" for r in (move + still)[:5]))

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every predicted record, every premium field for field, messages):")
        for i, (rid, (j, build, preds)) in enumerate(results.items(), 1):
            progress(i, len(results), f"ISO {rid}")
            req = m.payload(build())
            if j != "OR":
                for c in req["body"]["CommercialProperty"]:
                    c["State"] = j
                req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk20_rc4_{rid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,240})', str(exc.body))
                print(f"  {rid:9s} ISO REFUSES {mm_.group(0)[:240] if mm_ else str(exc.body)[:240]}")
                FAIL.append(f"{rid} live")
                continue
            (gc.OUT / f"chunk20_rc4_{rid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.items():
                iso = r2.iso_of(resp, rec)
                if want == "NONE":
                    if not all(r4.zeroish(x) for x in iso):
                        pbad.append((rec, iso, "nothing"))
                elif sorted(Decimal(str(x)) for x in iso if not same(x, 0)) != sorted(Decimal(str(w)) for w in want if not same(w, 0)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            agree += ok
            print(f"  {rid:9s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds) - len(pbad)} of {len(preds)}; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:58]}: ISO {x}, derived {w}" for r, x, w in pbad[:5])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{rid} live")
        print(f"\n  live: {agree} of {len(results)} agree")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C20-19 to C20-22): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
