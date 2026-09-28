#!/usr/bin/env python3
"""Chunk 17, RC-1 (C17-02 to C17-05): evidence and plumbing, before any golden case.

C17-02  THE $0 FIXTURES. Every stored ISO response on a fixture carrying Watercraft
        Exclusion Buyback or Mining Properties BI is re-rated (157_'s request): ISO's
        premium, ours, and the inputs on the parent that decide it. Then each on-switch
        is flipped, one at a time, on chunk 7's Oregon policy: the record must price
        with every gate open and price $0 with any one closed. No ISO calls.
C17-03  ATTACH MAP AND SWITCHES. Each premium record's chain up to Business Income /
        Special Class BI (DataDef XSD), each container's own rules, every on-switch
        shape, and every rule in the family's files that defaults a rate or factor to 0
        (a blank input that zeroes the premium without an on-switch).
C17-04  BORROWED VALUES. All 32 premium records placed on the Oregon policy with every
        input set (three trees: cause Special, cause Broad, cause Basic), the engine
        run, every SetPremium operand resolved from the record node in its own loop
        context (owner record exists, not a Table wrapper), and SetPremium evaluated by
        hand (174_'s evaluator, half-up at each DecimalPlaces) from the landed values:
        hand must equal the engine on every record. A value read before it is set would
        break that. Records that price $0 on these trees are listed for RC-2 / RC-3.
C17-05  TABLES AND LITERALS. Every table the family files read (premium files,
        containers, the state files), countrywide rows, and every state-filed table
        under ANY name that belongs to the family (the sibling-table rule); every string
        literal the family's tests compare against, and every lookup key literal that
        has no row in its table.

    python scripts/cf/180_chunk17_rc1.py

Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import copy
import csv
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
cen = import_module("179_chunk17_census")
ASOF = "20260917"
P = "CommercialProperty"
RES = ROOT / "results" / "cf-raas"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
FAIL = []
short = r16.short
WATERCRAFT = [P + "BusinessIncomeWatercraftExclusionBuybackCoverage",
              P + "SpecialClassBusnIncomeWatercraftExclusionBuybackCoverage"]
OPTION1 = "Fire Resistive Including Pier Deck and Pier Platform, but Without Superstructure"
OPTION5 = "All Other Construction - Substructure Including Superstructure, All Sides Enclosed"


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def population():
    """family -> {premium record stem: CW rule text}."""
    cw = book_for("OR", ASOF).parent.package.content
    out = {}
    for fam, pat in cen.FAMILIES:
        out[fam] = {}
        for f in sorted((cw / "Rules").glob("*.xml")):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                t = f.read_text(encoding="utf-8-sig")
                if cen.set_premium(t):
                    out[fam][f.name[:-len("Rules.Rule.xml")]] = t
    return out


def prem_of(data, tag):
    return [n.first("Premium").text if n.first("Premium") is not None else None for n in r16.find(data, tag)]


def money(v):
    return Decimal(v) if v not in (None, "") else Decimal(0)


# ------------------------------------------------------------------ the trees

#: container record -> its own inputs (by the rules that read them)
CONTAINER_FIELDS = {
    "OrdinaryPayrollLimitationOrExclusion": {"NumOfDays": "90"},
    "OrdinaryPayrollLimitationOrExclusionSpclClassBusnIncome": {"NumOfDays": "90"},
    "MiningPropertiesBusinessIncome": {"MiningCoverageOption": "Limited", "Limit": "40000"},
    "MiningPropertiesSpclClassBusnIncome": {"MiningCoverageOption": "Broad", "Limit": "40000"},
    "BusinessIncomeLandlordAsAdditionalInsuredRentalValue": {"Limit": "60000", "Coinsurance": "80%"},
    "BusinessIncomeLandlordAsAdditionalInsuredRentalValueSpclClassBusnIncome": {"Limit": "60000", "Coinsurance": "80%"},
    "OffPremInterruptionOfBusnVehsMobileEquipmtBusnInc": {"CollisionCovCOL": "Yes", "ExtendedPeriod": "90"},
    "OffPremInterruptionOfBusnVehsMobileEquipmtSpclClassBusnIncome": {"CollisionCovCOL": "Yes", "ExtendedPeriod": "120"},
    "OffPremInterruptionOfBusnVehsMobileEquipmtBusnIncDetail": {"Limit": "50000", "Option": "Option B",
                                                                 "PercentInsToExposure": "50% to 74.9%"},
    "OffPremInterruptionOfBusnVehsMobileEquipmtSpclClassBusnIncomeDetail": {"Limit": "50000", "Option": "Option B",
                                                                            "PercentInsToExposure": "25% to 49.9%"},
}


def place(sub, xsd, rec, fields):
    """rec placed under its known coverage record, creating (or reusing) each container
    on the way; `fields` (short type -> dict) fills any record on the chain."""
    top, steps = r16.chain_down(xsd, rec)
    d = rc1.node_dicts(sub)[top]
    for i, (t, table) in enumerate(steps):
        if table:
            lst = d.setdefault(t + "Table", {t: []})[t]
            if not lst:
                lst.append({})
            d = lst[-1]
        else:
            d = d.setdefault(t, {})
        for k, v in fields.get(short(t), {}).items():
            d.setdefault(k, v)
    return short(top) + " > " + " > ".join(short(t) + ("[]" if tb else "") for t, tb in steps)


LANDLORD = ("BusinessIncomeLandlordAsAdditionalInsuredRentalValue",
            "BusinessIncomeLandlordAsAdditionalInsuredRentalValueSpclClassBusnIncome")


def tree(cause, pop, xsd, bi_extra=None, fields=None, only=None, mining=False):
    """chunk 7's Oregon policy, BI and SCBI on `cause`, every family record placed.
    Business Income DELETES the Mining rows unless its TypeOfRisk is Mining (its
    conditional-mandatory rule), so Mining records go only on a `mining` tree.
    Special Class BI spells the waterfront input WaterFrontProperty (capital F); the
    Landlord record carries its own CauseOfLoss (the Broad / Special switches read it)."""
    sub = grp.five()
    at = rc1.node_dicts(sub)
    for k in (P + "BusinessIncome", P + "SpecialClassBusnIncome"):
        at[k]["CauseOfLoss"] = cause
        at[k].update(bi_extra or {})
        if mining:
            at[k]["TypeOfRisk"] = "Mining"
    sc = at[P + "SpecialClassBusnIncome"]
    if "WaterfrontProperty" in sc:
        sc["WaterFrontProperty"] = sc.pop("WaterfrontProperty")
    f = copy.deepcopy(fields if fields is not None else CONTAINER_FIELDS)
    for k in LANDLORD:
        f.setdefault(k, {}).setdefault("CauseOfLoss", cause)
    where = {}
    for fam, rs in pop.items():
        for r in rs:
            if only and r not in only:
                continue
            if fam.startswith("Mining") != mining and not only:
                continue
            where[r] = place(sub, xsd, short(P + r), f)
    return sub, where


WATERFRONT_ON = {"WaterfrontProperty": "Yes", "WatercraftExclBuybackConstrctnOption": OPTION1,
                 "SpecialIncludingTheftTypeRisk": "Other than Apartments and Condominiums"}


# ------------------------------------------------------------------ C17-02

def zero_fixtures(pop, xsd):
    print("\n" + "=" * 90 + "\nC17-02  THE $0 FIXTURES (no ISO calls)\n" + "-" * 90)
    index = rep.fixture_index()
    mining = [P + "MiningPropertiesBusinessIncome" + s for s in ("BasicGroupICoverage", "BasicGroupIICoverage")]
    carried = collections.Counter()
    reasons = collections.Counter()
    n_resp = n_ok = 0
    for stem, path in sorted(index.items()):
        t = path.read_text(encoding="utf-8-sig", errors="replace")
        if "WatercraftExclusionBuyback" not in t and "MiningProperties" not in t:
            continue
        rp = RES / f"chunk13_fixture_{stem}_response.json"
        recs = [r for r in WATERCRAFT + mining if f'"{r}"' in t]
        carried.update(recs)
        if not rp.exists():
            continue
        n_resp += 1
        resp = json.loads(rp.read_text(encoding="utf-8"))
        iso = collections.defaultdict(list)

        def walk(o, k=None):
            if isinstance(o, dict):
                if k in recs:
                    iso[k].append(o.get("Premium"))
                for kk, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, kk)
            elif isinstance(o, list):
                for x in o:
                    walk(x, k)
        walk(resp["Body"])
        d = json.loads(t)
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        try:
            data, _ = rep.cmp.rate(req)
        except InterpretError as exc:
            check(False, f"{stem}: ours raised {str(exc)[:100]}")
            continue
        ok = True
        for r in recs:
            isos = [money(x) for x in iso[r]]
            ours = [money(x) for x in prem_of(data, r)]
            ok &= all(x == 0 for x in isos) and all(x == 0 for x in ours) and bool(ours)
            for n in r16.find(data, r):
                par = n.parent
                if r in WATERCRAFT:
                    wf = par.first("WaterfrontProperty") or par.first("WaterFrontProperty")
                    cl = par.first("CauseOfLossToUse")
                    ex = par.first(P + "WatercraftExclusionBusnIncomeTable")
                    why = []
                    if wf is None or wf.text != "Yes":
                        why.append("WaterfrontProperty not Yes")
                    if cl is None or cl.text != "Special":
                        why.append(f"cause {cl.text if cl is not None else None}")
                    if ex is not None:
                        why.append("Watercraft Exclusion present")
                    reasons[(short(r), "; ".join(why) or "ALL GATES OPEN")] += 1
                else:
                    opt = par.first("MiningCoverageOption")
                    reasons[(short(r), f"MiningCoverageOption = {opt.text if opt is not None else None}")] += 1
        n_ok += ok
    for r, n in sorted(carried.items()):
        print(f"  {short(r)}: on {n} fixtures")
    check(n_ok == n_resp, f"{n_resp} fixtures with a stored ISO response: ISO $0 and ours $0 on every "
                          f"Watercraft / Mining record on {n_ok}")
    print("  why each record priced $0 (read from our rated tree):")
    for (r, why), n in sorted(reasons.items()):
        print(f"    {n:3d} x {r}: {why}")
    check(not any("ALL GATES OPEN" in w for _, w in reasons), "no stored fixture opens every Watercraft gate")

    # the switches, one at a time
    print("\n  Watercraft: every gate open prices; any one closed prices $0 (Oregon policy):")
    open_ = dict(WATERFRONT_ON)
    variants = [("all gates open (Option1, 0.016)", "Special", open_, None),
                ("Option5 (0.024)", "Special", dict(open_, WatercraftExclBuybackConstrctnOption=OPTION5), None),
                ("WaterfrontProperty = No", "Special", dict(open_, WaterfrontProperty="No"), None),
                ("WaterfrontProperty blank", "Special", {k: v for k, v in open_.items() if k != "WaterfrontProperty"}, None),
                ("cause Broad", "Broad", open_, None),
                ("cause Special Including Theft", "Special Including Theft", open_, None),
                ("Watercraft Exclusion (CP 10 35) present", "Special", open_, "excl"),
                ("construction option blank", "Special",
                 {k: v for k, v in open_.items() if k != "WatercraftExclBuybackConstrctnOption"}, None),
                ("construction option Not Applicable", "Special",
                 dict(open_, WatercraftExclBuybackConstrctnOption="Not Applicable"), None)]
    for label, cause, extra, mode in variants:
        sub, _ = tree(cause, pop, xsd, extra, only=set(short(P + r) for r in WATERCRAFT) | {r[len(P):] for r in WATERCRAFT})
        if mode == "excl":
            # each parent checks its own exclusion record's name
            for k, x in ((P + "BusinessIncome", "WatercraftExclusionBusnIncome"),
                         (P + "SpecialClassBusnIncome", "WatercraftExclusionSpclClassBusnIncome")):
                rc1.node_dicts(sub)[k][P + x + "Table"] = {P + x: [{}]}
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            print(f"    {label:45s} RAISED {str(exc)[:110]}")
            if "Not Applicable" in label:
                print("      (the conversion table maps 'Not Applicable' to 'Not Applicable', which has no factor row)")
            else:
                check(False, f"Watercraft {label}: raised")
            continue
        vals = {short(r): prem_of(data, r) for r in WATERCRAFT}
        facs = {short(r): [n.first("Factor").text if n.first("Factor") is not None else None
                           for n in r16.find(data, r)] for r in WATERCRAFT}
        each = [bool(v) and money(v[0]) > 0 for v in vals.values()]
        want_on = label.startswith(("all gates", "Option5"))
        check(all(x == want_on for x in each), f"{label:45s} premiums {vals}  factors {facs}")

    print("\n  Mining: rows survive only on a Mining risk; option None prices $0, Limited and Broad price:")
    recs = [r for r in pop["Mining Properties BI"]]
    sub, _ = tree("Special", pop, xsd, WATERFRONT_ON, only=set(recs), mining=False)
    data, _ = gc.run(sub, "OR")
    gone = {short(r): len(r16.find(data, r)) for r in recs}
    check(not any(gone.values()), f"TypeOfRisk Mercantile: Business Income removes every Mining row ({gone})")
    for opt in ("None", "Limited", "Broad", None):
        f = copy.deepcopy(CONTAINER_FIELDS)
        for k in ("MiningPropertiesBusinessIncome", "MiningPropertiesSpclClassBusnIncome"):
            if opt is None:
                f[k].pop("MiningCoverageOption")
            else:
                f[k]["MiningCoverageOption"] = opt
        sub, _ = tree("Special", pop, xsd, WATERFRONT_ON, f, only=set(recs), mining=True)
        data, _ = gc.run(sub, "OR")
        vals = {short(r): prem_of(data, r) for r in recs}
        on = all(v and money(v[0]) > 0 for v in vals.values())
        check(on == (opt in ("Limited", "Broad")), f"TypeOfRisk Mining, option {str(opt):8s} {vals}")


# ------------------------------------------------------------------ C17-03

def attach_and_switches(pop, xsd):
    print("\n" + "=" * 90 + "\nC17-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    shapes = collections.defaultdict(list)
    for fam, rs in pop.items():
        print(f"  {fam}")
        for r, text in sorted(rs.items()):
            ch = r16.chain_down(xsd, short(P + r))
            where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(
                short(t) + ("[]" if tb else "") for t, tb in ch[1])
            check(ch is not None, f"{short(r)}: {where}")
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', text, re.S)
            gate = "always on"
            if m and "<rul:If>" in m.group(0):
                tests = re.findall(r'FromDataDef="([^"]+)"|AtInputDataDef="([^"]+)"', m.group(0))
                consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(0)) if c not in ("0", "1")]
                gate = ", ".join(a or ("no " + b.rsplit("/", 1)[-1]) for a, b in tests) + f" = {consts}"
            # a premium that is itself conditional
            body = cen.set_premium(text)
            if re.search(r"<rul:If>", body):
                cond = re.findall(r'FromDataDef="([^"]+)"', body.split("<rul:Then>")[0])
                gate += f"; SetPremium only if {', '.join(c.rsplit('/', 1)[-1] for c in cond)} (else $0)"
            shapes[gate].append(short(r))
    print("\n  on-switch shapes (SetCoverageOnPolicyIndicator; ErcProcess forces Premium 0 when it is 0):")
    for g, rs in sorted(shapes.items(), key=lambda x: -len(x[1])):
        print(f"    {len(rs):2d} files: {g}")
        print(f"         {', '.join(rs[:4])}{' ...' if len(rs) > 4 else ''}")

    cw = book_for("OR", ASOF).parent.package.content / "Rules"
    print("\n  containers (no SetPremium): their own rules; every rate / factor that defaults to 0 when an input is blank:")
    zero_defaults = []
    for fam, pat in cen.FAMILIES:
        for n in sorted(cw.glob("*.xml")):
            if not re.search(pat, n.name) or cen.EXCLUDE.search(n.name):
                continue
            t = n.read_text(encoding="utf-8-sig")
            for m in re.finditer(r'<rul:Constant Type="decimal" ToDataDef="(\w+)">0(?:\.0)?</rul:Constant>', t):
                if m.group(1) != "Premium":
                    zero_defaults.append((short(n.name), m.group(1)))
            for m in re.finditer(r'<rul:Rule Name="(Set\w*Factor)".*?</rul:Rule>', t, re.S):
                if "<rul:Subtract>" in m.group(0):
                    zero_defaults.append((short(n.name), f"{m.group(1)} = BaseFactor - 1 (a base of 1.00 prices $0)"))
            if not cen.set_premium(t):
                rules = [x for x in cen.rule_names(t) if x not in cen.STANDARD and not x.startswith(("Lookup", "Set", "Do"))]
                sets = [x for x in cen.rule_names(t) if x.startswith("Set")]
                print(f"    {short(n.name)}: {len(sets)} Set rules ({', '.join(sets[:9])}{' ...' if len(sets) > 9 else ''})")
    print("  defaults that zero a premium without any on-switch:")
    for f, what in sorted(set(zero_defaults)):
        print(f"    {f}: {what}")


# ------------------------------------------------------------------ C17-04

def borrowed(pop, xsd):
    print("\n" + "=" * 90 + "\nC17-04  BORROWED VALUES (hand = engine on the Oregon policy)\n" + "-" * 90)
    priced = set()
    zero = collections.defaultdict(list)
    for cause, mining in (("Special", False), ("Broad", False), ("Basic", False), ("Special", True), ("Basic", True)):
        sub, where = tree(cause, pop, xsd, WATERFRONT_ON, mining=mining)
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"cause {cause}: tree raised {str(exc)[:120]}")
            continue
        print(f"  cause {cause}{', TypeOfRisk Mining (Mining records only)' if mining else ''}:")
        for fam, rs in pop.items():
            if fam.startswith("Mining") != mining:
                continue
            for r in sorted(rs):
                nodes_ = r16.find(data, r)
                if not nodes_:
                    check(False, f"{short(r)}: not on the rated tree")
                    continue
                body = cen.set_premium(rs[r])
                ops = r16.operands(body, nodes_[0])
                bad = [f"{op} -> {w}" for op, w in ops if w == "NOWHERE" or "WRAPPER" in w]
                prem = nodes_[0].first("Premium")
                eng = money(prem.text if prem is not None else None)
                cov = nodes_[0].first("CoverageOnPolicyIndicator")
                if cov is not None and cov.text == "0":
                    zero[short(r)].append(f"{cause}: switched off")
                    continue
                h = r16.hand(body, nodes_[0])
                hv = h if isinstance(h, Decimal) else None
                ok = not bad and hv is not None and hv == eng
                if eng == 0:
                    zero[short(r)].append(f"{cause}: $0 with the switch on")
                    if not ok:
                        check(False, f"{short(r)} ({cause}): hand {h}, engine {eng}" + (f"; {bad}" if bad else ""))
                    continue
                priced.add(short(r))
                check(ok, f"{short(r):78s} ${eng}  (hand {h}; {len(ops)} operands, every owner exists)"
                      + (f"; {bad}" if bad else ""))
    print("\n  records priced (> $0, hand = engine) on at least one tree:", len(priced), "of",
          sum(len(v) for v in pop.values()))
    print("  records $0 on every tree where they are switched on (their inputs are RC-2's):")
    for r, why in sorted(zero.items()):
        if r not in priced:
            print(f"    {r}: {'; '.join(why)}")


# ------------------------------------------------------------------ C17-05

def tables_and_literals(pop):
    print("\n" + "=" * 90 + "\nC17-05  TABLES AND LITERALS\n" + "-" * 90)
    cw = book_for("OR", ASOF).parent.package.content
    words = {"Ordinary Payroll Limitation": ["Payroll"],
             "Power, Heat and Refrigeration Deduction": ["PowerHeat"],
             "Mining Properties BI": ["Mining"],
             "Landlord as Additional Insured (Rental Value)": ["Landlord", "BusnIncomeFactor", "BroadFormBaseRate",
                                                                "SpecialFormIncldgTheftTimeElement"],
             "Watercraft Exclusion Buyback": ["Watercraft"],
             "Off-Premises Interruption (vehicles)": ["OffPrem"]}
    for fam, pat in cen.FAMILIES:
        files = [f for f in (cw / "Rules").glob("*.xml") if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        texts = [f.read_text(encoding="utf-8-sig") for f in files]
        state_texts = []
        for j in s18.STATES:
            rd = book_for(j, ASOF).state.package.content / "Rules"
            if rd.exists():
                state_texts += [(j, f.read_text(encoding="utf-8-sig", errors="replace")) for f in rd.glob("*.xml")
                                if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        # the BI files set the Watercraft conversion
        if fam.startswith("Watercraft"):
            texts.append((cw / "Rules" / f"{P}BusinessIncomeRules.Rule.xml").read_text(encoding="utf-8-sig"))
        tabs = sorted(set(t for s in texts + [s for _, s in state_texts]
                          for t in re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
        if fam.startswith("Watercraft"):
            tabs = [t for t in tabs if "Watercraft" in t]
        print(f"  {fam}")
        for t in tabs:
            f = cw / "Rate Tables" / f"{t}.RateTable.csv"
            print(f"    reads {t:58s} CW rows {cen.rows(f) if f.exists() else 'NOT FILED'}")
        filed = collections.defaultdict(list)
        for j in s18.STATES:
            td = book_for(j, ASOF).state.package.content / "Rate Tables"
            if not td.exists():
                continue
            for f in td.glob("*.RateTable.csv"):
                if any(w in f.name for w in words[fam]):
                    filed[f.name[:-len(".RateTable.csv")]].append(f"{j}:{cen.rows(f)}")
        for t, js in sorted(filed.items()):
            flag = "" if t in tabs else "   <-- not read by any family file"
            print(f"    state-filed {t:52s} {' '.join(js)}{flag}")
        cw_unread = sorted(f.name[:-len(".RateTable.csv")] for f in (cw / "Rate Tables").glob("*.RateTable.csv")
                           if any(w in f.name for w in words[fam][:1]) and f.name[:-len(".RateTable.csv")] not in tabs)
        if cw_unread:
            print(f"    countrywide tables with the family's name that no family file reads: {cw_unread}")
        lits = collections.Counter()
        for s in texts:
            for m in re.finditer(r'<rul:(Equal|NotEqual)>(.*?)</rul:\1>', s, re.S):
                for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(2)):
                    lits[c] += 1
        print(f"    literals compared in tests: {', '.join(repr(k) for k, _ in lits.most_common(20))}")

    # every value a chunk 17 lookup can be keyed with, vs the table's rows
    print("\n  lookup keys a user can send that have no row (a SingleResult miss):")
    conv = cw / "Rate Tables" / "WatercraftExclusionBuybackConstructionOptionsConverted.RateTable.csv"
    fac = cw / "Rate Tables" / "WatercraftExclBuybackFactor.RateTable.csv"
    with open(conv, encoding="utf-8-sig") as h:
        outs = {r["Value"] for r in csv.DictReader(h)}
    with open(fac, encoding="utf-8-sig") as h:
        keys = {r["WatercraftExclBuybackConstrctnOptionsConverted"] for r in csv.DictReader(h)}
    miss = sorted(outs - keys)
    print(f"    Watercraft: conversion outputs with no factor row: {miss}")
    ext = cw / "Rate Tables" / "OffPremExtendedBusnIncCovFactor.RateTable.csv"
    with open(ext, encoding="utf-8-sig") as h:
        eks = [r["ExtendedPeriodBusnInc"] for r in csv.DictReader(h)]
    print(f"    Off-Premises extended period: rows {eks}; a BLANK period is not looked up, it sets the factor 0.0")


def main():
    pop = population()
    xsd = rc1.xsd_for(book_for("OR", ASOF))
    print(f"{book_for('OR', ASOF)}\n" + "\n".join(f"  {fam}: {len(rs)} premium records" for fam, rs in pop.items()))
    zero_fixtures(pop, xsd)
    attach_and_switches(pop, xsd)
    borrowed(pop, xsd)
    tables_and_literals(pop)
    print("\n" + ("RC-1: ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED"))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
