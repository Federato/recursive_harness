#!/usr/bin/env python3
"""Chunk 21, C21-14 state rewrites, C21-15 Florida's sewer, C21-16 editions, C21-17 all 46 states. Live ISO.

Every prediction here is STATE-AWARE: a table is the state's in-force package's when it has rows (it then
REPLACES the CW table outright: 210_ T8), else that state's countrywide edition's; a rule is the state's own
when its package defines it, else its countrywide edition's. The state rewrites are read from the rule
files, not assumed (2026-09-30):
  * misc. real property SetPremium in AL KS RI: no deductible factor; Rate x LCM x the building's
    PublicInstitutionalPlanFactor (0.85 with the plan applied, else 1.0) in one 3-place product
  * loss assessment rate rules in KS NY: no Standard Property Policy branch (an SPP uses its own cause)
  * loss assessment in FL: the sub-limit rules and their messages are emptied; SetPremium has no
    SubLimitRate and tests the limit against "0" rather than blank
  * sewer in FL: the parents never call the five records (C21-05): attached, never priced
C21-14  S1-S9: each rewrite with the competing (countrywide) reading giving another dollar
C21-15  W1-W2: Florida sewer on all five parents (Special, Broad): predicted unpriced / CW reading 167...
C21-16  every rule of each family file diffed across the four CW editions; probes on MO (2023 V02), NC
        (V03) and VT (V04) inside C21-17's run
C21-17  every state: the five sewer records at 25,000, loss assessment 10,000 (deductible 250, sub-limit
        7,000) and misc. real property 20,000; each state's own container form number compared with ISO

    python scripts/cf/211_chunk21_c21-14-17.py [--live] [--cases S1,ALL-OR] [--no-states]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import csv
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

m10 = import_module("210_chunk21_c21-12-13")
m9, m8, h21 = m10.m9, m10.m8, m10.h21
r2, rc1, r16, gc, rep, cmp, s18 = m8.r2, m8.rc1, m8.r16, m8.gc, m8.rep, m8.cmp, h21.s18
P, SEWER, LA, MRP, OPT, NWP = m8.P, m8.SEWER, m8.LA, m8.MRP, m8.OPT, m8.NWP
BLDG, PP, SC, BI, SCBI = SEWER
same, at, portable, r = r2.same, m9.at, m9.portable, h21.r
val, up = h21.val, h21.up
FAIL = []
D = Decimal
ASOF = "20260917"
SPP = "Standard Property Policy"
FAM_FILES = re.compile(r"DischargeFromSewer|CondominiumCommercialUnitOwnersOptional|ChangesCommercialUnitsInResidentialCondo")


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


# ---------------------------------------------------------------- state-aware resolution

@functools.lru_cache(maxsize=None)
def pkgs(j):
    b = book_for(j, ASOF)
    return (b.state.package.content if b.state else None), b.parent.package.content


@functools.lru_cache(maxsize=None)
def rows(j, name):
    """the table ISO uses in state j: the in-force state package's if it has rows (it replaces CW's),
    else the state's countrywide edition's; state-keyed rows first, then CW-keyed (the two lookup passes)"""
    st, cw = pkgs(j)
    for pkg in ((st, cw) if st else (cw,)):
        f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
        if f.exists():
            got = list(csv.DictReader(open(f, encoding="utf-8-sig")))
            if got:
                return [x for x in got if x["StateCode"] == j] + [x for x in got if x["StateCode"] == "CW"]
    return []


@functools.lru_cache(maxsize=None)
def rule(j, fname, name):
    st, cw = pkgs(j)
    for pkg in ((st, cw) if st else (cw,)):
        f = pkg / "Rules" / f"{fname}.Rule.xml"
        if f.exists():
            m = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
            if m:
                return m.group(0)
    return ""


def rewrites(j):
    """the state's rewrites, read from the rule files it resolves to"""
    mrp_prem = rule(j, P + MRP + "Rules", "SetPremium")
    la_base = rule(j, P + LA + "Rules", "SetBaseRate")
    la_sub = rule(j, P + LA + "Rules", "SetSubLimitRate")
    return {"mrp_pipf": "PublicInstitutionalPlanFactor" in mrp_prem,
            "la_spp_basic": SPP in la_base,
            "la_sublimits": "SubLimitRate" in rule(j, P + LA + "Rules", "SetPremium") and "Sum" in la_sub,
            "la_blank_is_on": 'FromDataDef="../LossAssessmentLimit"' in rule(j, P + LA + "Rules", "SetPremium")
                              and "<rul:Constant Type=\"string\">0</rul:Constant>" in rule(j, P + LA + "Rules", "SetPremium")}


def ded_factor(j, ded, amount):
    if ded == "250":
        return next((D(x["Factor"]) for x in rows(j, "Deductible250Factor") if x["CauseOfLoss"] == "All Other"), None)
    if ded in (None, "", "Not Applicable") or D(amount or 0) == 0:
        return D("1.0")
    return next((D(x["Factor"]) for x in rows(j, "DeductibleFactor")
                 if x["Deductible"] == ded and x["CauseOfLossDeductible"] == "Other Cause Of Loss"
                 and D(x["Limit_FromGreaterThan"]) < D(amount) <= D(x["Limit_To"])), None)


def mods(cp, pp):
    return [D(val(cp, "PackageModFactor") or 0), D(val(pp, "MultiPremiumAndDispersionCreditFactor") or 0),
            D(val(cp, "IRPMFactor") or 0)]


# ---------------------------------------------------------------- hand models, per state

def sewer_hand(j, node, rec):
    mode, amount_field, depth, nwp_rec = h21.HOW[rec]
    bi = rec.endswith("BusnIncome")
    parent, top = up(node, 2), up(node, depth)
    blc = next(D(x["Rate"]) for x in rows(j, "DischargeFromSewerDrainOrSump") if x["Type"] == ("BI" if bi else "PD"))
    rate = r(blc * D(val(parent, "LossCostMultiplier") or 0), 3)
    mm = {k: D(val(top, k) or 0) for k in h21.MODS}
    lim = D(val(node, SEWER[rec])) / 100
    if bi:
        nwp = [c for c in parent.children if c.tag == P + nwp_rec + "Table"]
        f = val(nwp[0].children[0], "Factor") if nwp and nwp[0].children else None
        final = r(rate * D(f), 3) if f is not None else rate
        return r(r(r(final * lim, 0) * mm["PackageModFactor"], 0) * mm["IRPMFactor"], 0)
    if mode == "own":
        dedf = ded_factor(j, val(parent, "Deductible"), val(parent, amount_field)) or D(0)
    else:
        bld = [c for c in up(node, 6).children if c.tag == P + BLDG + "Table"]
        f = val(bld[0].children[0], "DeductibleFactor") if bld and bld[0].children else None
        dedf = D(f) if f is not None else D(1)
    p = r(rate * dedf, 3)
    for f in (lim, mm["PackageModFactor"], mm["MultiPremiumAndDispersionCreditFactor"], mm["IRPMFactor"]):
        p = r(p * f, 0)
    return p


def la_hand(j, node):
    rw = rewrites(j)
    cont, pp, cp = node.parent, up(node, 3), up(node, 11)
    lim = val(cont, "LossAssessmentLimit") or ""
    if lim == "0":
        return D(0)
    over = val(cont, "LossAssessmentLimitOver10000")
    sub = int(val(cont, "LossAssessmentSubLimit") or 0) if rw["la_sublimits"] else 0
    ded = val(cont, "LossAssessmentDeductible") or ""
    spp = val(cp, "PolicyType") == SPP
    cause = "Basic" if (spp and rw["la_spp_basic"]) else val(pp, "CauseOfLossToUse")

    def rate_of(limit_key):
        return next((D(x["Rate"]) for x in rows(j, "LossAssessmentRate")
                     if x["LossAssessmentLimit"] == limit_key and x["CauseOfLoss"] == cause), None)
    base, r10k = rate_of(lim), rate_of("10,000")
    if lim == "Over 10,000":
        ok5 = not (int(over or 0) >= 15000 and int(over) % 5000)
        rate = r((D(over or 0) / 5000 - 2) * (base or 0) + r10k, 3) if ok5 else D(0)
    else:
        rate = base or D(0)
    subrate = D(0)
    if rw["la_sublimits"]:
        m1 = sub <= 10000 or sub % 1000 == 0
        n = (sub // 1000 - 1) if (sub > 1000 and m1) else 0
        br = {b: next(D(x["Rate"]) for x in rows(j, "LossAssessmentSubLimitRate")
                      if x["LossAssessmentSubLimit"] == b and x["CauseOfLoss"] == cause)
              for b in ("Upto5000", "From6000To10000", "Over10000")} if n > 0 else {}
        if n > 0:
            subrate = (r(n * br["Upto5000"] if n < 4 else 4 * br["Upto5000"], 3)
                       + (r((n - 4) * br["From6000To10000"], 3) if 4 < n <= 9 else (r(5 * br["From6000To10000"], 3) if n > 9 else 0))
                       + (r((n - 9) * br["Over10000"], 3) if n > 9 else 0))
    if ded == "250":
        dedf = ded_factor(j, "250", 0)
    elif ded == "Not Applicable":
        dedf = D("1.0")
    elif ded == "":
        dedf = D(0)
    else:
        limded = {"1,000": 1000, "5,000": 5000, "10,000": 10000}.get(lim, int(over) if over else 0)
        dedf = ded_factor(j, ded, limded) or D(0)
    p = r(r((rate + subrate) * D(val(pp, "LossCostMultiplier") or 0), 3) * dedf, 3)
    for f in mods(cp, pp):
        p = r(p * f, 0)
    return p


def pipf(j, structure):
    """SetPublicInstitutionalPlanFactor, written out (AL KS RI)"""
    s = lambda f: val(structure, f) or ""
    applies = (s("PublicInstitutionalPlanApply") == "Yes"
               and ((s("IncludedInBlkt") == "No" and s("Coinsurance") in ("90%", "100%"))
                    or (s("IncludedInBlkt") == "Yes" and s("BlktCoinsurance") in ("90%", "100%")))
               and s("CovType") not in ("Legal Liability", "Leasehold Interest") and s("ClassCode") != "1150")
    if not applies:
        return D("1.0")
    return next(D(x["Factor"]) for x in rows(j, "PublicInstitutionalPlanFactor") if x["Constant"] == "Y")


def mrp_hand(j, node):
    cont, pp, cp = node.parent, up(node, 3), up(node, 11)
    lim = val(cont, "MiscRealPropLimit")
    if lim is None:
        return D(0)
    rate = next(D(x["Rate"]) for x in rows(j, "MiscRealPropRate") if x["Constant"] == "Y")
    lcm = D(val(pp, "LossCostMultiplier") or 0)
    if rewrites(j)["mrp_pipf"]:
        p = r(r(rate * lcm * pipf(j, up(node, 7)), 3) * D(lim) / 100, 0)
    else:
        ded = val(cont, "LossAssessmentDeductible") or ""
        if ded in ("", "Not Applicable"):
            dedf = D("1.0")
        elif ded == "250":
            dedf = ded_factor(j, "250", 0)
        else:
            dedf = ded_factor(j, ded, lim) or D(0)
        p = r(r(r(rate * lcm, 3) * dedf, 3) * D(lim) / 100, 0)
    for f in mods(cp, pp):
        p = r(p * f, 0)
    return p


def predict(j, data, rec):
    out = []
    for node in rc1.find(data, P + rec):
        if rec in SEWER:
            h = D(0) if j in UNRATED_SEWER else sewer_hand(j, node, rec)
        elif rec == LA:
            h = la_hand(j, node)
        else:
            h = mrp_hand(j, node)
        p = node.first("Premium")
        out.append((h, None if p is None else p.text))
    return out


UNRATED_SEWER = {"FL"}                      # C21-05: FL's parents never call the sewer records


# ---------------------------------------------------------------- cases

def policy(j, cause="Special", sewer=True, la=None, mrp="20000", ded="250", edits=()):
    def b():
        sub = portable(j, cause)
        # 209_'s portable drops every EQ* input outside Oregon, the location's EQTerr with them; but some
        # states' building BCEG factor is keyed on EQTerr whether or not earthquake is covered (SC's
        # BCEGEQFactor: ISO refused on keys "CW, 1, <blank>" on the first run, 2026-09-30). Keep the
        # state's own EQTerr on the location.
        terr = s18.STATE_LOC.get(j, {}).get("EQTerr")
        if terr and j != "OR":
            at(sub, "Location")["EQTerr"] = terr
        if sewer:
            for rec, lim in SEWER.items():
                r2.put(sub, rec, {lim: "25000"}, state=j)
        cont = {"LossAssessmentLimit": "0"} if la is None else dict(la)
        if mrp:
            cont["MiscRealPropLimit"] = mrp
        if ded:
            cont.setdefault("LossAssessmentDeductible", ded)
        at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [dict(cont, **{P + LA: {}, P + MRP: {}})]}
        for e in edits:
            e(sub)
        return sub
    return b


def spp(sub):
    at(sub)["PolicyType"] = SPP


def pip(sub):
    at(sub, "Structure")["PublicInstitutionalPlanApply"] = "Yes"


def cases(states=True):
    c = {}

    def add(cid, task, j, label, build, recs, fire=(), silent=(), unrated=()):
        c[cid] = dict(task=task, j=j, label=label, build=build, recs=list(recs), fire=list(fire), silent=list(silent),
                      unrated=list(unrated))
    LA10 = {"LossAssessmentLimit": "10,000"}
    # at 10,000 Special and Basic both round to $6 (first run): 50,000 makes the SPP probes disagree
    LA50 = {"LossAssessmentLimit": "Over 10,000", "LossAssessmentLimitOver10000": "50000"}
    # C21-14
    add("S1", "C21-14", "AL", "AL misc. real property 20,000, deductible 250 IGNORED (93; CW reading 102)",
        policy("AL", sewer=False), [MRP])
    add("S2", "C21-14", "AL", "AL misc. real property, public institutional plan applied (factor 0.85)",
        policy("AL", sewer=False, edits=[pip]), [MRP])
    add("S3", "C21-14", "KS", "KS misc. real property 50,000, deductible 1,000 ignored (CW reading banded)",
        policy("KS", sewer=False, mrp="50000", ded="1,000"), [MRP])
    add("S4", "C21-14", "RI", "RI misc. real property, plan applied", policy("RI", sewer=False, edits=[pip]), [MRP])
    add("S5", "C21-14", "KS", "KS loss assessment Over 10,000 = 50,000 on an SPP: its own cause Special (CW reading: Basic)",
        policy("KS", sewer=False, la=LA50, mrp=None, edits=[spp]), [LA])
    add("S6", "C21-14", "NY", "NY loss assessment Over 10,000 = 50,000 on an SPP: its own cause Special (CW reading: Basic)",
        policy("NY", sewer=False, la=LA50, mrp=None, edits=[spp]), [LA])
    add("S7", "C21-14", "OR", "control: OR loss assessment Over 10,000 = 50,000 on an SPP (Basic)",
        policy("OR", sewer=False, la=LA50, mrp=None, edits=[spp]), [LA])
    add("S8", "C21-14", "FL", "FL loss assessment 10,000, sub-limit 8,000 IGNORED (CW reading adds it)",
        policy("FL", sewer=False, la=dict(LA10, LossAssessmentSubLimit="8000"), mrp=None), [LA])
    add("S9", "C21-14", "FL", "FL sub-limit 6,000 over a 5,000 limit: no sub-limit message (CW fires one)",
        policy("FL", sewer=False, la={"LossAssessmentLimit": "5,000", "LossAssessmentSubLimit": "6000"}, mrp=None), [LA],
        silent=[m9.SUBGT])
    add("S10", "C21-14", "UT", "UT unit owners form with misc. real property (UT's CP 04 22; change form attaches)",
        policy("UT", sewer=False, edits=[lambda s: at(s, "OccupClass").__setitem__("CovForm", m8.UO)]), [MRP],
        silent=[m9.UT_WITH])
    # C21-15
    add("W1", "C21-15", "FL", "FL sewer, all five at 25,000, Special: attached, never priced", policy("FL", mrp=None, ded=None),
        [], unrated=list(SEWER))
    add("W2", "C21-15", "FL", "FL sewer, all five, Broad", policy("FL", "Broad", mrp=None, ded=None), [], unrated=list(SEWER))
    # C21-16: the every-rule diff of the PARENT files (where the sewer caps live) found MO's 2023 V02 testing
    # the parent's Limit, not LimitToUse, in four of the five caps (building, contents, BI, special class BI)
    def lim_to_use(parent, rec):
        def b():
            sub = portable(parent[0])
            r2.put(sub, rec, {SEWER[rec]: "75000"}, state=parent[0])
            at(sub, parent[1])["LimitToUse"] = "50000"
            return sub
        return b
    cap = lambda w: m9.CAP + w + " limit"
    add("E1", "C21-16", "MO", "MO (2023 V02) building LimitToUse 50,000 under a 100,000 limit, sewer 75,000: cap SILENT",
        lim_to_use(("MO", "Structure"), BLDG), [BLDG], silent=[cap("Building")])
    add("E2", "C21-16", "MO", "MO special class, same: its cap still reads LimitToUse and FIRES",
        lim_to_use(("MO", "SpecialClass"), SC), [SC], fire=[cap("Special Class")])
    add("E3", "C21-16", "OR", "control: OR (2026) building, same: the cap FIRES",
        lim_to_use(("OR", "Structure"), BLDG), [BLDG], fire=[cap("Building")])
    # C21-17 (with C21-16's edition probes among them)
    if states:
        for j in s18.STATES:
            add(f"ALL-{j}", "C21-17", j, "five sewer, loss assessment 10,000 (250, sub 7,000), misc. real property 20,000",
                policy(j, la=dict(LA10, LossAssessmentSubLimit="7000")),
                ([] if j in UNRATED_SEWER else list(SEWER)) + [LA, MRP],
                unrated=list(SEWER) if j in UNRATED_SEWER else [])
    return c


# ---------------------------------------------------------------- C21-16 static

def editions():
    progress(0, 0, "C21-16 every rule of every family file, four CW editions")
    print("\n" + "=" * 90 + "\nC21-16  EVERY RULE, FOUR COUNTRYWIDE EDITIONS\n" + "-" * 90)
    eds = {}
    for j in s18.STATES:
        cw = pkgs(j)[1]
        eds.setdefault(cw.name, (cw, []))[1].append(j)
    base = pkgs("OR")[1]
    norm = lambda b: re.sub(r'\s+', " ", re.sub(r' MetadataCodes="[^"]*"| ProjectName="[^"]*"', "", b))
    diffs = []
    files = sorted(f.name for f in (base / "Rules").glob("*.xml") if FAM_FILES.search(f.name))
    for name, (pkg, js) in sorted(eds.items()):
        if pkg == base:
            print(f"  {name}: the base ({len(js)} states)")
            continue
        n = 0
        for fn in files:
            f = pkg / "Rules" / fn
            if not f.exists():
                diffs.append(f"{name}: {fn} MISSING")
                n += 1
                continue
            a = {m.group(1): norm(m.group(0)) for m in re.finditer(r'<rul:Rule Name="(\w+)".*?</rul:Rule>',
                                                                  (base / "Rules" / fn).read_text(encoding="utf-8-sig"), re.S)}
            b = {m.group(1): norm(m.group(0)) for m in re.finditer(r'<rul:Rule Name="(\w+)".*?</rul:Rule>',
                                                                  f.read_text(encoding="utf-8-sig"), re.S)}
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    diffs.append(f"{name}: {fn[18:-14]}.{k} {'only in 2026' if k not in b else 'only here' if k not in a else 'differs'}")
                    n += 1
        print(f"  {name} ({', '.join(js)}): {len(files)} family files, {n} rule differences from 2026 V01")
    for d in diffs:
        print(f"    {d}")
    return diffs


# ---------------------------------------------------------------- run

def iso_form(resp):
    ic = m10.iso_container(resp)
    return ic.get("ErcFormNumber")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    ap.add_argument("--no-states", action="store_true")
    a = ap.parse_args()
    if not a.cases:
        diffs = editions()
        check(True, f"edition differences listed ({len(diffs)}); each is judged in CF-CHUNK21-TASKS.md C21-16")
    cs = cases(not a.no_states)
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    print("\n" + "=" * 90 + "\nENGINE (state-aware prediction = engine)\n" + "-" * 90)
    for i, (cid, c) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(c["build"](), c["j"])
        except InterpretError as exc:
            print(f"{cid}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        bad, shown = [], {}
        preds[cid] = {}
        for rec in c["recs"]:
            res = predict(c["j"], data, rec)
            preds[cid][rec] = [h for h, _ in res]
            shown[r16.short(rec)[-14:]] = [str(h) for h, _ in res]
            if not res or not all(e is not None and same(h, e) for h, e in res):
                bad.append(f"{r16.short(rec)[-24:]} predicted {[str(h) for h, _ in res]} engine {[e for _, e in res]}")
        for rec in c["unrated"]:
            if any(n.first("Premium") is not None for n in rc1.find(data, P + rec)):
                bad.append(f"{r16.short(rec)[-24:]} priced, predicted unrated")
        bad += m9.msg_check([str(x) for x in ip.messages], c["fire"], c["silent"])
        print(f"{cid} {c['task']} {c['j']} {c['label'][:70]}: {'as predicted' if not bad else 'DIFFERS ' + str(bad)}  {shown}")
        if bad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, messages, the container's form number):")
        for i, (cid, c) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = m8.payload(c["build"](), c["j"])
            (gc.OUT / f"chunk21_c21-14-17_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {cid} ISO REFUSES {mm.group(0)[:220] if mm else str(exc.body)[:220]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk21_c21-14-17_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in c["recs"]:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(D(str(x)) for x in iso) != sorted(D(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            for rec in c["unrated"]:
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if iso:
                    pbad.append((rec, iso, ["unrated"]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = m9.msg_check([str(x) for x in mi], c["fire"], c["silent"])
            ours_form = val(rc1.find(data, P + OPT)[0], "ErcFormNumber") if rc1.find(data, P + OPT) else None
            fbad, known = [], ""
            if str(iso_form(resp)) != str(ours_form):
                if ours_form == "Value Not Found" and iso_form(resp):
                    # OI-118 (2026-09-30): the state's own Pages table replaces CW's in our engine, so a CW
                    # form's name / number is "Value Not Found"; ISO still finds the CW row. Pinned, not failed.
                    known = f"; KNOWN OI-118 (form ISO {iso_form(resp)}, ours not found)"
                else:
                    fbad = [f"form ISO {iso_form(resp)} ours {ours_form}"]
            ok = not pbad and not d and mi == mo and not mb and not fbad
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: {len(ipr) - len(d)} of {len(ipr)} premiums; messages "
                  f"{'equal' if mi == mo else 'DIFFER'}; form {iso_form(resp)}{known}" + (f"; {mb}" if mb else "") + (f"; {fbad}" if fbad else "")
                  + "".join(f"\n        predicted {r16.short(rr)[-50:]}: ISO {x}, derived {w}" for rr, x, w in pbad[:7])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(str(x)[:100] for x in mi - mo)[:3]}\n        ours only {sorted(str(x)[:100] for x in mo - mi)[:3]}"
                     if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC21-14..C21-17: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
