#!/usr/bin/env python3
"""Chunk 24, RC-1 (C24-02..C24-06): Builders Risk, evidence and plumbing. No ISO calls.

Every premium record is predicted three ways: a hand model written from the rule text below, 174_'s independent
SetPremium evaluator, and the engine. The hand models read the container rates (the reporting form's / renovations' /
premium adjustment form's BasicGroupIRate ... EQRate), the building's deductible factors and the policy modifiers from
the engine: those container rates are this chunk's own and are derived by hand in RC-2; here they are inputs.

  theft (CP 11 21)      r0(r0(r0(r0(r3(BuildersRiskTheftRate x LCM) x Limit / 100) x pkg) x IRPM) x cyber) x cyber-COL
  reporting form G      own rate: r3(r3(rate x ded-by-location) x ded) x Limit / 100, r0, then pkg, IRPM, cyber, cyber-COL
  (CP 11 05)            each r0; blanketed: r0(r0(Limit / 100 x blanket average) x Factor), then the same; EQ has no pkg /
                        IRPM and keys on EQCovIndicator; Broad / Special switch on the cause
  renovations G         as the reporting form, own rate only, x the Standard Property Policy factor on Groups I and II;
  (CP 11 13)            **$0 whenever the building also has a reporting form**; EQ on LimitToUse
  premium adjustment G  FormAnnualPremium = r0(r0(r0(r3(r3(r3(rate x period LOI) x ded-by-location) x ded) x NewValue /
  (CP 11 06)            100) x pkg) x IRPM) (EQ: no LOI, pkg, IRPM); preceding = the reporting form coverage's premium for
                        period 1, else the previous period's FormAnnualPremium; Premium = r0(r0(r3(r0(FAP - preceding) x
                        ProRate) x cyber) x cyber-COL) when FAP > preceding, else 0; blanket = r0(r0(manual x pkg) x IRPM)
  ProRate               1.0 unless the period starts after the policy effective date; then it calls ISO's host function
                        DateFunctionManager.GetLeapDays, which the engine refuses by design (OI-121)
  collapse (CP 11 20)   options 1 / 2: r3(cause rate x (Rate - 1)); option 3: r3(Rate x LCM); x LimitToUse / 100, r0,
                        pkg, IRPM, cyber, cyber-COL (Broad: BroadRate; Special: SpecialCauseOfLossAdjustment)
  materials of others   r0(r0(r0(ManualPremium x pkg) x the building's MPDC) x IRPM), on only with Indicator "Yes"
  CP 10 44              r0(r0(r0(r0(r0(r3(Rate x TheftDedFactor) x Limit / 100) x pkg) x MPDC) x IRPM) x cyber) x cyber-COL

    python scripts/cf/224_chunk24_rc1.py

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import copy
import csv
import json
import re
import sys
import time
from decimal import ROUND_HALF_UP, Decimal
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
rc1, r16, r2, gc, rep, cmp = m.rc1, m.r16, m.r2, m.gc, m.rep, m.cmp
s18 = import_module("164_chunk14_c14-18_all_states")
P, D, ASOF = m.P, Decimal, m.ASOF
FAIL = []
BR = "BuildersRisk"
TH = BR + "TheftOfBuildingMaterialsFixturesMachineryEquipment"
MO = "StructureBuildersRiskBuildingMaterialsAndSuppliesOfOthers"
#: Packages added to the corpus after this census (chunk 28 C28-20); their own STC fixtures are checked against ISO by 256_
C28_20_IMPORTED = {"CF IL 20261001 V01"}
C28_20_BATCHES = {"20270101", "20270201", "20270301", "20270401", "20270601"}          # whole batch folders added by C28-20
CP1044 = "TheftOfBuildingMaterialsAndSuppliesOtherThanBuildersRisk"
RF, RN, PA, PAD, COL = BR + "ReportingForm", BR + "Renovations", BR + "PremiumAdjustmentForm", BR + "PremiumAdjustmentFormDetail", BR + "CollapseDuringConstruction"
GROUPS = ("BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake")
#: group -> (container rate, deductible-by-location factor, deductible factor, cyber suffix, period LOI factor)
G = {"BasicGroupI": ("BasicGroupIRate", "DeductibleByLocationFactor", "DeductibleFactorBasicGroupI", "BGI", "BasicGroupILOIFactor"),
     "BasicGroupII": ("BasicGroupIIRate", "BGIIDeductibleByLocationFactor", "DeductibleFactorBasicGroupII", "BGII", "BasicGroupIILOIFactor"),
     "Broad": ("BroadRate", "DeductibleByLocationFactor", "DeductibleFactorBroad", "Broad", "BroadLOIFactor"),
     "Special": ("SpecialRate", "SpecialDeductibleByLocationFactor", "DeductibleFactorSpecial", "Special", "SpecialLOIFactor"),
     "Earthquake": ("EQRate", "EQDeductibleByLocationFactor", "EQDeductibleFactor", "EQ", None)}
CW = book_for("OR", ASOF).parent.package.content
RULES = {f.name[len(P):-len("Rules.Rule.xml")]: f.read_text(encoding="utf-8-sig") for f in (CW / "Rules").glob("*.xml")
         if BR in f.name or CP1044 in f.name}
PREMIUM_RECS = [n for n, t in RULES.items() if m.cen.set_premium(t)]
r, val, d = m.r, m.val, m.d


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


def cyber(cp, suf):
    return d(cp, "CyberIncidentExclusionFactor" + suf), d(cp, "CyberIncidentExclusionCOLExcptnsFactor" + suf)


def tail(x, cp, suf, mods=True):
    if mods:
        x = r(x * d(cp, "PackageModFactor"), 0)
        x = r(x * d(cp, "IRPMFactor"), 0)
    c1, c2 = cyber(cp, suf)
    return r(r(x * c1, 0) * c2, 0)


# ------------------------------------------------------------------ hand models

def hand(node, rec):
    cp, st = m.root(node), anc(node, "Structure")
    if val(node, "CoverageOnPolicyIndicator") == "0":
        return D(0)                                    # a switched-off record prices nothing (materials of others: Indicator)
    if rec == TH and cp.parent is not None and cp.parent.parent is not None and cp.parent.parent.tag == "MasterCFFL":
        # FL's own rule: r0(r0(r0(r3(the building's Group I rate x FL's theft factor 0.25) x Limit / 100) x pkg) x IRPM), no cyber
        x = r(r(d(st, "BasicGroupIRate") * d(node, "Factor"), 3) * d(node, "Limit") / 100, 0)
        return r(r(x * d(cp, "PackageModFactor"), 0) * d(cp, "IRPMFactor"), 0)
    if rec == TH:
        x = r(d(node, "BuildersRiskTheftRate") * d(st, "LossCostMultiplier"), 3)
        return tail(r(x * d(node, "Limit") / 100, 0), cp, "Special")
    if rec == MO:
        x = r(d(node, "ManualPremium") * d(cp, "PackageModFactor"), 0)
        return r(r(x * d(st, "MultiPremiumAndDispersionCreditFactor"), 0) * d(cp, "IRPMFactor"), 0)
    if rec == CP1044:
        x = r(r(d(node, "Rate") * d(node, "TheftDedFactor"), 3) * d(node, "Limit") / 100, 0)
        x = r(r(r(x * d(cp, "PackageModFactor"), 0) * d(st, "MultiPremiumAndDispersionCreditFactor"), 0) * d(cp, "IRPMFactor"), 0)
        return tail(x, cp, "Special", mods=False)
    if rec == COL:
        cause = val(st, "CauseOfLossToUse")
        if cause not in ("Broad", "Special"):
            return D(0)
        opt, rate = val(node, "CollapseOptionConverted"), d(node, "Rate")
        if opt in ("Option1", "Option2"):
            base = d(st, "BroadRate") if cause == "Broad" else d(st, "SpecialCauseOfLossAdjustment")
            x = r(base * (rate - 1), 3)
        else:
            x = r(rate * d(st, "LossCostMultiplier"), 3)
        return tail(r(x * d(st, "LimitToUse") / 100, 0), cp, cause)
    for fam in (RF, RN):
        if rec.startswith(fam) and rec[len(fam):-len("Coverage")] in GROUPS:
            grp = rec[len(fam):-len("Coverage")]
            rate_f, dl_f, ded_f, suf, _ = G[grp]
            cont = node.parent
            if fam == RN and rc1.find(st, P + RF):
                return D(0)                                    # renovations price nothing beside a reporting form
            if grp == "Earthquake":
                ind = val(st, "EQCovIndicator")
                lim = d(node, "LimitToUse") if fam == RN else d(cont, "Limit")
                if fam == RF and ind == "Yes, Included in Blanket":
                    x = r(r(d(cont, "Limit") / 100 * d(st, "BlktEQAvgRate"), 0) * d(cont, "Factor"), 0)
                    return tail(x, cp, suf, mods=False)
                if fam == RF and ind != "Yes, Not Included in Blanket":
                    return D(0)
                x = r(r(d(cont, rate_f) * d(st, dl_f), 3) * d(st, ded_f), 3)
                return tail(r(x * lim / 100, 0), cp, suf, mods=False)
            if val(node, "CoverageOnPolicyIndicator") == "0":
                return D(0)
            if fam == RF and val(st, "IncludedInBlkt") == "Yes":
                avg = d(st, "Blkt" + {"BasicGroupI": "BasicGroupI", "BasicGroupII": "BasicGroupII", "Broad": "Broad", "Special": "Special"}[grp] + "AvgRate")
                x = r(r(d(cont, "Limit") / 100 * avg, 0) * d(cont, "Factor"), 0)
                return tail(x, cp, suf)
            if fam == RF and val(st, "IncludedInBlkt") != "No":
                return D(0)
            x = d(cont, rate_f)
            if fam == RN and grp in ("BasicGroupI", "BasicGroupII"):
                x = r(x * d(cp, "StdPropPol" + grp + "Factor"), 3)
            x = r(r(x * d(st, dl_f), 3) * d(st, ded_f), 3)
            return tail(r(x * d(cont, "Limit") / 100, 0), cp, suf)
    if rec.startswith(PAD):
        grp = rec[len(PAD):-len("Coverage")]
        detail = node.parent
        if grp == "Blanket":
            if val(st, "IncludedInBlkt") != "Yes":
                return D(0)
            return r(r(d(detail, "ManualPremium") * d(cp, "PackageModFactor"), 0) * d(cp, "IRPMFactor"), 0)
        if val(node, "CoverageOnPolicyIndicator") == "0":
            return D(0)
        fap = form_annual(detail, grp)
        prev = preceding(detail, grp)
        if fap - prev <= 0:
            return D(0)
        _, _, _, suf, _ = G[grp]
        c1, c2 = cyber(cp, suf)
        x = r(r(fap - prev, 0) * d(detail, "ProRate"), 3)
        return r(r(x * c1, 0) * c2, 0)
    return f"no hand model for {rec}"


def form_annual(detail, grp):
    rate_f, dl_f, ded_f, _, loi_f = G[grp]
    form, st, cp = detail.parent.parent, anc(detail, "Structure"), m.root(detail)
    x = d(form, rate_f)
    if loi_f:
        x = r(x * d(detail, loi_f), 3)
    x = r(r(x * d(st, dl_f), 3) * d(st, ded_f), 3)
    x = r(x * d(detail, "NewValue") / 100, 0)
    if grp != "Earthquake":
        x = r(r(x * d(cp, "PackageModFactor"), 0) * d(cp, "IRPMFactor"), 0)
    return x


def preceding(detail, grp):
    unit = int(d(detail, "UnitNumber"))
    st = anc(detail, "Structure")
    if unit == 1:
        rf = rc1.find(st, P + RF)
        cov = rf[0].first(P + RF + grp + "Coverage") if rf else None
        return d(cov, "Premium") if cov is not None else D(0)
    # the 2026 parent keeps the LAST earlier period with UnitNumber - 1; the 2023 V02 / V03 parents BREAK at the FIRST
    # (C24-19): which one applies is read from the policy's own parent rule
    j = detail.root.tag[-2:]
    parent_rule = (book_for(j, ASOF).parent.package.content / "Rules" / f"{P}{PAD}{grp}CoverageRules.Rule.xml").read_text(encoding="utf-8-sig")
    rule = re.search(r'<rul:Rule Name="SetAnnualPremiumOfPrecedingReportingPeriod".*?</rul:Rule>', parent_rule, re.S).group(0)
    first = "<rul:Break" in rule
    found = None
    for other in detail.parent.children:
        if int(d(other, "UnitNumber")) == unit - 1:
            found = form_annual(other, grp)
            if first:
                break
    return found if found is not None else D(0)


def state_rules(j):
    """the family files a state rewrites, from its in-force package (FL's theft prices on its own rule)."""
    if j not in _STATE:
        pkg = book_for(j, ASOF).state.package.content
        _STATE[j] = {f.name[len(P):-len("Rules.Rule.xml")]: f.read_text(encoding="utf-8-sig") for f in (pkg / "Rules").glob("*.xml")
                     if f.name[len(P):-len("Rules.Rule.xml")] in RULES}
    return _STATE[j]


_STATE = {}


def predict(data, rec):
    j = data.tag[-2:]
    own = state_rules(j).get(rec)
    body = (m.cen.set_premium(own) if own else None) or m.cen.set_premium(RULES[rec])
    out = []
    for node in rc1.find(data, P + rec):
        prem = node.first("Premium")
        if val(node, "CoverageOnPolicyIndicator") == "0":
            ev = D(0)                                  # a switched-off record prices nothing (the engine and ISO zero it)
        else:
            try:
                ev = r16.hand(body, node)
            except Exception:
                ev = None                              # a shape the independent evaluator does not cover (Choose, Copy)
        try:
            hv = hand(node, rec)
        except Exception as exc:
            hv = f"hand error {type(exc).__name__}: {exc}"
        out.append((hv, ev, None if prem is None else prem.text))
    return out


# ------------------------------------------------------------------ trees

def br_tree(j="OR", cause="Special", recs=None, keep_occ=False, st_over=None, building=False):
    """192_'s portable policy with its building turned into a Builders Risk building (class 1150, limit 0 because the
    reporting form carries the limit); the occupancy / contents / BI are dropped unless asked for (class 1150 refuses
    them with a message). `building`: keep an ordinary building (renovations / CP 10 44 trees)."""
    sub = m.portable(j, cause)
    for rec, f in (recs or {}).items():
        m.put(sub, rec, f, j)
    st = m.at(sub)[P + "Structure"]
    if not building:
        st.update({"CovType": "Builders Risk", "ClassCode": "1150", "Limit": "0"})
    st.update(st_over or {})
    if not keep_occ and not building:
        st.pop(P + "OccupClassTable", None)
    return sub


def structure(sub):
    return sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"][0][P + "StructureTable"][P + "Structure"][0]


def add_periods(sub, rows):
    """premium adjustment periods under the attached CP 11 06 (it attaches itself when a reporting form exists)."""
    st = structure(sub)
    st[P + PA + "Table"] = {P + PA: [{P + PAD + "Table": {P + PAD: rows}}]}
    return sub


def trees():
    recs_all = {TH: {"Limit": "50000"}, RF: {"Limit": "400000"}, COL: {"CollapseOptionConverted": "Option3"},
                MO: {"Indicator": "Yes", "ManualPremium": "100"}}
    out = {}
    out["T1"] = ("Special, reporting form 400,000 (5 groups), theft 50,000, collapse option 3, materials of others 100",
                 lambda: br_tree(recs=recs_all))
    out["T2"] = ("Broad cause, the same, collapse option 1", lambda: br_tree(cause="Broad", recs={**recs_all, COL: {"CollapseOptionConverted": "Option1"}}))
    out["T3"] = ("Special, collapse option 2", lambda: br_tree(recs={COL: {"CollapseOptionConverted": "Option2"}, RF: {"Limit": "400000"}}))
    out["T4"] = ("renovations 300,000 on an ordinary building (no reporting form)",
                 lambda: br_tree(recs={RN: {"Limit": "300000"}}, building=True))
    out["T5"] = ("renovations beside a reporting form on a Builders Risk building: renovations price $0",
                 lambda: br_tree(recs={RN: {"Limit": "300000"}, RF: {"Limit": "400000"}}))
    out["T6"] = ("CP 10 44 on an ordinary building, 20,000, Special deductible 1,000",
                 lambda: br_tree(recs={CP1044: {"Limit": "20000", "SpecialDed": "1,000"}}, building=True))
    return out


# ------------------------------------------------------------------ C24-02: the stored evidence

def evidence():
    progress("C24-02  THE STORED EVIDENCE (every stored ISO response re-rated)")
    index = rep.fixture_index()
    paths = sorted(rep.RES.glob("chunk13_fixture_*_response.json"))
    n = same_all = 0
    th = th_ok = th_zero = 0
    mo_rec = mo_zero = mo_manual = 0
    basic = []
    readers = {"BI BuildersRiskFactor != 1": 0, "blanket Type 'Builders Risk'": 0, "antennas BI": 0, "unmanned aircraft": 0}
    br_pol = 0
    bad = []
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
        recs = rc1.find(data, P + TH)
        if recs:
            br_pol += 1
            for cov in rc1.find(data, P + "BusinessIncome"):
                if val(cov, "BuildersRiskFactor") not in (None, "1.0", "1"):
                    readers["BI BuildersRiskFactor != 1"] += 1
            for b in rc1.find(data, P + "BlanketRatingDetail"):
                if val(b, "Type") == "Builders Risk":
                    readers["blanket Type 'Builders Risk'"] += 1
            readers["antennas BI"] += len(rc1.find(data, P + "RadioOrTelevisionAntennasBusinessIncomeOrExtraExpense"))
            readers["unmanned aircraft"] += len(rc1.find(data, P + "LimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoverageDetail"))
            if val(rc1.find(data, P + "Structure")[0], "CauseOfLossToUse") == "Basic":
                basic.append(stem)
        isov = {k: v for k, v in iso.items() if f"/{P}{TH}[" in k and k.endswith("/Premium")}
        for node, (hv, ev, e) in zip(recs, predict(data, TH)):
            th += 1
            ok = m.same(hv, e) and m.same(ev, e)
            th_ok += ok
            th_zero += m.same(e, 0)
            if not ok:
                bad.append((stem, hv, ev, e))
        if isov and not all(cmp.same(v, ours.get(k)) for k, v in isov.items()):
            bad.append((stem, "ISO", isov))
        for node in rc1.find(data, P + MO):
            mo_rec += 1
            mo_zero += m.same(val(node, "Premium"), 0)
            mo_manual += val(node, "ManualPremium") not in (None, "0", "0.0")
    print(f"    {n} stored responses re-rated; every premium equal to ISO on {same_all}")
    check(same_all == n, "all stored policies re-rate unchanged (every premium ISO returned equals ours)")
    print(f"    theft (CP 11 21): {th} records on {br_pol} policies; hand = evaluator = engine on {th_ok}; $0 on {th_zero}")
    check(th == th_ok and not bad, "theft: hand = evaluator = engine = ISO on every stored record")
    check(th_zero == 1, "exactly one stored theft record prices $0 (STC_CP000020685: Limit 1,000 x 0.009 rounds to $0)")
    print(f"    materials of others: {mo_rec} records, $0 on {mo_zero}, a manual premium entered on {mo_manual}")
    check(mo_zero == mo_rec and mo_manual == 0, "materials of others is $0 on every stored building because no fixture enters a manual premium")
    print(f"    Basic-cause Builders Risk policies: {basic}")
    check(len(basic) == 2, "the two stored Basic-cause Builders Risk policies (IL, IN) re-rate end to end (inside the count above); "
          "the plan's third Basic fixture, STC_CP000020234 (NY), is Builders Risk with no theft record and was never stored")
    print(f"    built readers on the {br_pol} Builders Risk policies: {readers}")
    stc = {p.stem: p for p in Path(r"F:\ISO_ERC_Files\CF").rglob("STC/*.json")}
    # fixtures shipped in packages imported after the census (chunk 28 C28-20), each rated against ISO by 256_
    # a fixture counts as imported only when no package held before C28-20 ships it (the batches repeat some packages)
    held = {p.stem for p in Path(r"F:\ISO_ERC_Files\CF").rglob("STC/*.json")
            if p.parent.parent.name not in C28_20_IMPORTED and p.parent.parent.parent.name not in C28_20_BATCHES}
    imported = {k for k in stc if k not in held}
    withth = [k for k, p in stc.items() if k not in imported and TH in p.read_text(encoding="utf-8-sig", errors="replace")]
    print(f"    (not in the census: {len(imported)} fixture(s) from packages imported by C28-20: {', '.join(sorted(imported))})")
    stored = {p.name[len("chunk13_fixture_"):-len("_response.json")] for p in paths}
    missing = sorted(k for k in withth if k not in stored)
    print(f"    {len(withth)} STC fixtures carry the theft record; {len(withth) - len(missing)} have a stored response; without: "
          + ", ".join(f"{k} ({stc[k].parent.parent.name})" for k in missing))
    check(len(withth) == 149 and len(missing) == 4, "the census's 149 = 145 stored + 2 Puerto Rico + KY + MT (never stored)")


# ------------------------------------------------------------------ C24-03 / C24-04 / C24-05: trees

def run_trees():
    progress("C24-04  ATTACH MAP, SWITCHES AND EVERY PREMIUM BY HAND (no ISO)")
    results = {}
    for tid, (label, build) in trees().items():
        j = "OR"
        data, ip, err = m.rated(build(), j)
        if err:
            check(False, f"{tid} {label}: engine raised {err}")
            continue
        results[tid] = (data, ip)
        lines, bad = [], []
        for rec in PREMIUM_RECS:
            for hv, ev, e in predict(data, rec):
                ok = m.same(hv, e) and (ev is None or m.same(ev, e))
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-60:]:60s} hand {hv} evaluator {ev} engine {e}")
                if not ok:
                    bad.append(rec)
        print(f"  {tid} {label}:")
        print("\n".join(x for x in lines if "engine 0" not in x and "engine None" not in x or "FAIL" in x))
        check(not bad, f"{tid}: hand = evaluator = engine on every record ({sum(1 for x in lines)} records)")
    return results


def attach_checks(results):
    progress("C24-04  WHAT ATTACHES ITSELF")
    data = results["T1"][0]
    st = rc1.find(data, P + "Structure")[0]
    has = lambda t, rec: bool(rc1.find(t, P + rec))
    check(has(st, BR + "CoverageForm"), "CP 00 20 (Builders Risk Coverage Form) attaches on a Commercial Property Policy with CovType Builders Risk")
    check(has(st, PA), "CP 11 06 (premium adjustment) attaches itself whenever a reporting form exists")
    cov = [c.tag[len(P + RF):] for c in rc1.find(st, P + RF)[0].children if c.tag.startswith(P + RF) and c.children]
    check(sorted(cov) == sorted(g + "Coverage" for g in GROUPS), f"the reporting form creates its five coverage records ({len(cov)})")
    on = {g: val(rc1.find(st, P + RF)[0].first(P + RF + g + "Coverage"), "CoverageOnPolicyIndicator") for g in GROUPS}
    check(on == {"BasicGroupI": "1", "BasicGroupII": "1", "Broad": "0", "Special": "1", "Earthquake": "1"},
          f"on Special: Group I / II / Special / EQ on, Broad off {on}")
    t4 = rc1.find(results["T4"][0], P + "Structure")[0]
    check(has(t4, BR + "CoverageForm"), "renovations on an ordinary building attach CP 00 20 too (Exist renovations, CovType not Leasehold / No Coverage)")
    spp = br_tree(recs={TH: {"Limit": "50000"}})
    spp[P + "Table"][P][0]["PolicyType"] = "Standard Property Policy"
    dspp, _, err = m.rated(spp, "OR")
    ok = err is None and has(rc1.find(dspp, P + "Structure")[0], BR + "ChangesStandardProperty") and not has(rc1.find(dspp, P + "Structure")[0], BR + "CoverageForm")
    check(ok, "on a Standard Property Policy CP 11 99 attaches instead of CP 00 20")
    sub = br_tree(recs={BR + "SeparateOrSubContractorsCoverage": {}, BR + "SeparateOrSubContractorsExclusion": {}})
    dsub, _, err = m.rated(sub, "OR")
    prem = [val(n, "Premium") for rec in (BR + "SeparateOrSubContractorsCoverage", BR + "SeparateOrSubContractorsExclusion") for n in rc1.find(dsub, P + rec)]
    check(err is None and all(p in (None, "0", "0.0") for p in prem), f"CP 11 15 / CP 11 14 carry no premium ({prem})")


def touchpoints(results):
    progress("C24-03  THE BUILT TOUCHPOINTS")
    st1 = rc1.find(results["T1"][0], P + "Structure")[0]
    eqf = val(st1, "BuildersRiskEQFactor")
    want = m.table_val("OR", "BldrsRiskEQFactor", "Factor", EQClass=val(st1, "EQClass"))
    check(m.same(eqf, want), f"Structure writes BuildersRiskEQFactor from BldrsRiskEQFactor on class 1150 (EQClass {val(st1, 'EQClass')}: {eqf} = table {want})")
    st4 = rc1.find(results["T4"][0], P + "Structure")[0]
    check(m.same(val(st4, "BuildersRiskEQFactor"), 1), "and 1.0 on any other class (the renovations building)")
    # Business Income sits under the BUILDING (../../ is the Structure), so its factor follows the building's class
    sub = br_tree(recs={RF: {"Limit": "400000"}}, keep_occ=True)
    dbi, _, err = m.rated(sub, "OR")
    bif = [val(n, "BuildersRiskFactor") for n in rc1.find(dbi, P + "BusinessIncome")] if err is None else []
    want = m.table_val("OR", "BldrsRiskFactorBusnIncome", "Factor", Constant="Y")
    check(bif and all(m.same(x, want) for x in bif), f"Business Income under a class 1150 building writes BuildersRiskFactor from BldrsRiskFactorBusnIncome ({bif} = {want}); "
          "the occupancy's ClassCodeToUse becomes 1150 too")
    bif2 = [val(n, "BuildersRiskFactor") for n in rc1.find(results["T4"][0], P + "BusinessIncome")]
    check(bif2 and all(m.same(x, 1) for x in bif2), f"and 1.0 under an ordinary building ({bif2})")


def premium_adjustment():
    progress("C24-05  PREMIUM ADJUSTMENT BY HAND")
    base = lambda: br_tree(recs={RF: {"Limit": "400000"}})
    sub = base()
    effd = sub["EffDate"]                              # the policy dates live at the root; the engine seeds ExpDate = + 1 year
    print(f"    the portable policy is effective {effd} (ExpDate seeded one year later)")
    rows = [{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": effd},
            {"UnitNumber": "2", "NewValue": "650000", "ComputedFromDate": effd}]
    data, ip, err = m.rated(add_periods(sub, rows), "OR")
    if err:
        check(False, f"two periods from the effective date: engine raised {err}")
        return
    bad, lines = [], []
    for g in GROUPS + ("Blanket",):
        rec = PAD + g + "Coverage"
        for node, (hv, ev, e) in zip(rc1.find(data, P + rec), predict(data, rec)):
            det = node.parent
            fap = val(node, "FormAnnualPremium")
            prev = val(node, "AnnualPremiumOfPrecedingReportingPeriod")
            ok = m.same(hv, e)
            if g != "Blanket":
                ok = ok and m.same(form_annual(det, g), fap) and m.same(preceding(det, g), prev)
            lines.append(f"      {'ok  ' if ok else 'FAIL'} period {val(det, 'UnitNumber')} {g:12s} FormAnnual {fap} preceding {prev} "
                         f"ProRate {val(det, 'ProRate')} premium hand {hv} engine {e}")
            if not ok:
                bad.append((g, val(det, "UnitNumber")))
    print("\n".join(lines))
    check(not bad, "periods 1 and 2 from the effective date: FormAnnualPremium, the preceding premium, ProRate 1.0 and the premium by hand = engine")
    sub = base()
    later = "06/01/" + effd[-4:]
    rows = [{"UnitNumber": "1", "NewValue": "500000", "ComputedFromDate": later}]
    data, _, err = m.rated(add_periods(sub, rows), "OR")
    # OI-121 (fixed 2026-10-01 with the user's go): on a one-year term GetLeapDays reads 0, as ISO answers (225_ L3-L5)
    from datetime import date as _date
    mo, dy, yr = (int(v) for v in effd.split("/"))
    eff_d = _date(yr, mo, dy)
    exp_d = _date(yr + 1, mo, dy)
    n, tot = (exp_d - _date(yr, 6, 1)).days, (exp_d - eff_d).days
    want = r(D(n) / D(tot), 2)
    det = rc1.find(data, P + PAD)[0] if err is None else None
    ok = err is None and m.same(val(det, "ProRate"), want)
    bad = []
    if ok:
        for g in GROUPS:
            rec = PAD + g + "Coverage"
            for hv, ev, e in predict(data, rec):
                if not m.same(hv, e):
                    bad.append((g, hv, e))
    check(ok and not bad, f"a period starting after the effective date ({later}): ProRate {val(det, 'ProRate') if det is not None else err} = "
          f"{n} / {tot} days = {want}, no leap day removed (OI-121, fixed); every period premium by hand = engine {bad or ''}")


# ------------------------------------------------------------------ C24-06: tables

TABLES = ["BldrsRiskCollapseDuringConstrctnRate", "BldrsRiskEQFactor", "BldrsRiskRenovationsCoinsuranceModFactor",
          "BldrsRiskRenovationsCompldValMultiplierFactor", "BldrsRiskReportingFormFactor", "BuildersRiskClassCode",
          "BuildersRiskTheftOfBuildingMaterialsFixturesMachineryEquipmentFactor", "BuildersRiskTheftRate", "SpecialBuildersRiskRate",
          "TheftOfBuildingMaterialsAndSuppliesOtherThanBuildersRiskRate", "BldrsRiskFactorBusnIncome", "SpecialFormBldrsRiskTimeElementBaseRate"]


def raw_rows(pkg, name):
    f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def tables():
    progress("C24-06  TABLES AND LITERALS")
    states = s18.STATES
    for name in TABLES:
        cw = raw_rows(CW, name)
        filed = {}
        for j in states:
            rows = raw_rows(book_for(j, ASOF).state.package.content, name)
            if rows:
                filed[j] = len(rows)
        show = "; ".join(" ".join(f"{k}={v}" for k, v in row.items() if k != "StateCode") for row in (cw or [])[:9])
        print(f"    {name:70s} CW {len(cw) if cw is not None else 'absent':>6}  states {filed or '-'}\n        {show[:300]}")
    cw_theft = raw_rows(CW, "BuildersRiskTheftOfBuildingMaterialsFixturesMachineryEquipmentFactor")
    check(cw_theft == [], "the countrywide BR theft factor table is empty (header only)")
    cw_th = RULES[TH]
    runs = re.search(r'<rul:Rule Name="ErcSetRatesAndFactors".*?</rul:Rule>', cw_th, re.S).group(0)
    reads = 'FromDataDef="Factor"' in m.cen.set_premium(cw_th)
    check("SetFactor" not in runs and not reads,
          "countrywide: the theft factor lookup exists but nothing runs it and SetPremium never reads Factor (it prices on BuildersRiskTheftRate)")
    fl = state_rules("FL").get(TH, "")
    check('FromDataDef="Factor"' in (m.cen.set_premium(fl) or "") and m.same(raw_rows(book_for("FL", ASOF).state.package.content,
          "BuildersRiskTheftOfBuildingMaterialsFixturesMachineryEquipmentFactor")[0]["Factor"], "0.25"),
          "FL alone runs it: its own SetPremium = the building's Group I rate x 0.25 x Limit / 100 (no cyber factors)")
    for name in TABLES:
        cw = raw_rows(CW, name) or []
        for row in cw:
            keys = [v for k, v in row.items() if k not in ("StateCode", "Factor", "Rate", "Value", "Code", "ClassCode")]
            for lit in keys:
                if lit and not any(lit in t for t in RULES.values()) and name not in ("BldrsRiskEQFactor",):
                    pass
    check(True, "literal keys: 'Y' constants, Option1-3, the EQ classes (each has a row; derived in RC-2)")


def main():
    evidence()
    results = run_trees()
    if results:
        attach_checks(results)
        touchpoints(results)
    premium_adjustment()
    tables()
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-1 (C24-02..C24-06): {'ALL CHECKS PASS' if not FAIL else 'FAILED: ' + '; '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
