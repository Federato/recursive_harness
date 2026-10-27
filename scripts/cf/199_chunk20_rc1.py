#!/usr/bin/env python3
"""Chunk 20, RC-1 (C20-02 to C20-05): evidence and plumbing, before any golden case.

C20-02  THE $0 RECORDS. Fire Department (on all 364 stored buildings), Tobacco and the four special-limit
        records (206 contents rows) and the Business Income fungus records (82) price $0 on every stored
        policy. Each stored ISO response carrying them is re-rated: ISO's premium, ours, and the input that
        decides it. Then each on-switch is flipped on chunk 7's Oregon policy. Read from the rules first
        (2026-09-29):
          Fire Department  its own FireIncreaseLimitApplyOnPolicyIndicator "Yes"; prices (limit - the base
                           fire department limit) / 100 x factor
          Tobacco          the contents' CovForm "Tobacco Sales Warehouse Coverage Form"
          furs / jewelry / patterns / stamps   the record's Indicator "Yes" (or a higher-limits record);
                           prices only the limit ABOVE its base special limit, at the contents' theft rate
          BI fungus        the Business Income's increased-period-of-restoration indicator "Yes"
        No ISO calls.
C20-03  ATTACH MAP AND SWITCHES: each premium record's chain (DataDef XSD), each container's Set rules,
        every on-switch shape and the state rewrites of it, every rule that writes 0 into a rate / factor.
C20-04  BORROWED VALUES: every record placed on real trees with its inputs (from the rules and the Domain
        Tables); hand = engine on every node (174_'s evaluator). A blanket tree for Radioactive
        Contamination (it reads the blanket average rate, chunk 9).
C20-05  TABLES AND LITERALS: every table the family files read, CW and each state's own, header-only ones,
        state tables under any family name that no family file reads, the literals the tests compare.

    python scripts/cf/199_chunk20_rc1.py [--skip-stored]

Progress streams as [i/n elapsed] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import argparse
import collections
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

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

book_for = functools.lru_cache(maxsize=None)(book_for)

gc = import_module("149_chunk13_golden_case")
rep = import_module("157_chunk14_c14-02_total_replay")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
r2 = import_module("175_chunk16_rc2")
cen = import_module("901_chunk20_census")
ASOF = "20260917"
P = "CommercialProperty"
RES = ROOT / "results" / "cf-raas"
FAIL = []
short = r16.short
CW = book_for("OR", ASOF).parent.package.content


def progress(what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def money(v):
    return Decimal(str(v)) if v not in (None, "") else Decimal(0)


def population():
    """family -> {premium record (file stem): CW rule text}."""
    out = {}
    for fam, pat in cen.FAMILIES:
        out[fam] = {}
        for f in sorted((CW / "Rules").glob("*.xml")):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                t = f.read_text(encoding="utf-8-sig")
                if cen.set_premium(t):
                    out[fam][f.name[:-len("Rules.Rule.xml")]] = t
    return out


def domain(name, col=1):
    f = CW / "Domain Tables" / f"{name}.DomainTable.csv"
    with open(f, encoding="utf-8-sig") as h:
        return [r[col] for r in list(csv.reader(h))[1:]]


# ------------------------------------------------------------------ C20-02

ZERO_FAMILIES = {
    "LocationFireDepartmentCharge": ("Location", ["FireIncreaseLimitApplyOnPolicyIndicator", "Limit"]),
    "PersonalPropertyTobaccoSalesWarehousesCoverage": ("PersonalProperty", ["CovForm"]),
    "PersonalPropertySpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFur": (None, ["Indicator", "Limit"]),
    "PersonalPropertySpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetals": (None, ["Indicator", "Limit"]),
    "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms": (None, ["Indicator", "Limit"]),
    "PersonalPropertySpecialCOLStampsTicketsAndLettersOfCredit": (None, ["Indicator", "Limit"]),
    "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageBasicGroupICoverage": ("BusinessIncome", ["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"]),
    "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageBasicGroupIICoverage": ("BusinessIncome", ["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"]),
    "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageEarthquakeCoverage": ("BusinessIncome", ["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"]),
}


def zero_records(skip_stored):
    progress("C20-02  THE $0 RECORDS")
    print("=" * 90 + "\nC20-02  THE $0 RECORDS (no ISO calls)\n" + "-" * 90)
    index = rep.fixture_index()
    stored = [] if skip_stored else sorted(RES.glob("chunk13_fixture_*_response.json"))
    reasons = collections.Counter()
    n = ok_n = 0
    recs = [P + r for r in ZERO_FAMILIES]
    for i, rp in enumerate(stored, 1):
        stem = rp.name[len("chunk13_fixture_"):-len("_response.json")]
        if i % 50 == 0:
            progress(f"  stored fixture {i}/{len(stored)}")
        fx = index.get(stem)
        if fx is None:
            continue
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
        if not iso:
            continue
        d = json.loads(fx.read_text(encoding="utf-8-sig"))
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        try:
            data, _ = rep.cmp.rate(req)
        except InterpretError as exc:
            check(False, f"{stem}: ours raised {str(exc)[:100]}")
            continue
        n += 1
        ok = True
        for r in iso:
            ours = [money(x.first("Premium").text if x.first("Premium") is not None else None) for x in r16.find(data, r)]
            ok &= all(money(x) == 0 for x in iso[r]) and all(o == 0 for o in ours)
            parent, fields = ZERO_FAMILIES[r[len(P):]]
            for node in r16.find(data, r):
                src = node.parent if parent else node
                if parent and not src.tag.endswith(parent):
                    src = next((a for a in [node.parent, node.parent.parent if node.parent is not None else None]
                                if a is not None and a.tag.endswith(parent)), node.parent)
                g = lambda f: (src.first(f).text if src.first(f) is not None else None)
                why = ", ".join(f"{f}={g(f)!r}" for f in fields)
                reasons[(re.sub(r"(BasicGroupI+|Earthquake)Coverage$", "*", short(r))[:48], why)] += 1
        ok_n += ok
    if skip_stored:
        print("  (stored responses skipped: --skip-stored)")
    else:
        check(ok_n == n and n > 0, f"{n} stored responses carry these records: ISO $0 and ours $0 on {ok_n}")
    print("  why they price $0 (read from our rated tree; records per reason):")
    for (r, why), k in sorted(reasons.items(), key=lambda x: -x[1])[:16]:
        print(f"    {k:5d} x {r:48s} {why}")


def base(cause="Special"):
    sub = r2.base()
    at = rc1.node_dicts(sub)
    for k in ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome"):
        at[P + k]["CauseOfLoss"] = cause
    return sub


def flips():
    print("\n  Flip each switch on the Oregon policy (175_'s, Special):")
    at = rc1.node_dicts
    cases = []

    def fire(on, limit):
        def b():
            sub = base()
            at(sub)[P + "Location"][P + "LocationFireDepartmentCharge"] = {"FireIncreaseLimitApplyOnPolicyIndicator": on, "Limit": limit}
            return sub
        return b
    cases += [("Fire Department: indicator Yes, limit 25,000", fire("Yes", "25000"), "LocationFireDepartmentCharge", True),
              ("Fire Department: indicator No, limit 25,000", fire("No", "25000"), "LocationFireDepartmentCharge", False),
              ("Fire Department: indicator Yes, limit at the base", fire("Yes", "BASE"), "LocationFireDepartmentCharge", False)]

    def tobacco(form):
        def b():
            sub = base()
            pp = at(sub)[P + "PersonalProperty"]
            if form:
                # the contents' CovForm is COPIED from the occupancy's (SetCovForm: ../../CovForm; first run)
                at(sub)[P + "OccupClass"]["CovForm"] = form
            pp[P + "PersonalPropertyTobaccoSalesWarehousesCoverage"] = {}
            return sub
        return b
    cases += [("Tobacco: contents CovForm Tobacco Sales Warehouse", tobacco("Tobacco Sales Warehouse Coverage Form"),
               "PersonalPropertyTobaccoSalesWarehousesCoverage", True),
              ("Tobacco: chunk 7's contents form", tobacco(None), "PersonalPropertyTobaccoSalesWarehousesCoverage", False)]

    def special(ind, limit):
        def b():
            sub = base()
            at(sub)[P + "PersonalProperty"][P + "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms"] = {"Indicator": ind, "Limit": limit}
            return sub
        return b
    cases += [("patterns and dies: Indicator Yes, limit 20,000", special("Yes", "20000"), "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms", True),
              ("patterns and dies: Indicator No, limit 20,000", special("No", "20000"), "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms", False),
              ("patterns and dies: Indicator Yes, limit 1,000 (under the base)", special("Yes", "1000"),
               "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms", False)]

    def fungus(bi_ind, period="90"):
        """the increased period comes from the POLICY-level fungus record (the BI record reads
        ../../../../../../../ChangesFungusWetRotDryRotBacteria[1]/IncreasedPeriodOfRestoration; first run)."""
        def b():
            sub = base()
            at(sub)[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = bi_ind
            at(sub)[P][P + "ChangesFungusWetRotDryRotBacteriaTable"] = {P + "ChangesFungusWetRotDryRotBacteria": [
                {"IncreasedPeriodOfRestoration": period, "FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator": bi_ind}]}
            r2.put(sub, "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageBasicGroupICoverage")
            return sub
        return b
    cases += [("BI fungus: increased period Yes (90 days)", fungus("Yes"),
               "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageBasicGroupICoverage", None),
              ("BI fungus: increased period No", fungus("No"),
               "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverageBasicGroupICoverage", False)]
    base_fire = None
    for label, build, rec, want in cases:
        sub = build()
        if "BASE" in json.dumps(sub):
            if base_fire is None:
                d0, _ = gc.run(fire("Yes", "25000")(), "OR")
                n0 = r16.find(d0, P + "LocationFireDepartmentCharge")[0]
                base_fire = n0.first("FireDepartmentLimit").text if n0.first("FireDepartmentLimit") is not None else "0"
            rc1.node_dicts(sub)[P + "Location"][P + "LocationFireDepartmentCharge"]["Limit"] = base_fire
            label = label.replace("at the base", f"at the base ({base_fire})")
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"{label}: raised {str(exc)[:120]}")
            continue
        nodes_ = r16.find(data, P + rec)
        prem = [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]
        extra = ""
        if nodes_:
            n0 = nodes_[0]
            extra = " " + ", ".join(f"{k.tag}={k.text}" for k in n0.children if not k.children and k.tag in (
                "CoverageOnPolicyIndicator", "FireDepartmentLimit", "LimitToUse", "Factor", "BaseSpecialLimit",
                "TobaccoInSalesWarehousesRate", "TotalPremium", "IncreasedPeriodOfRestoration"))
        priced = any(money(p) != 0 for p in prem)
        if want is None:            # the BI fungus records compute a TOTAL for the policy-level record, no Premium
            print(f"    [info] {label:52s} premium {prem}{extra}")
        else:
            check(priced == want, f"{label:52s} premium {prem}{extra}")


# ------------------------------------------------------------------ C20-03

def attach_and_switches(pop, xsd):
    progress("C20-03  ATTACH MAP AND SWITCHES")
    print("\n" + "=" * 90 + "\nC20-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    shapes = collections.defaultdict(list)
    unplaced = []
    for fam, rs in pop.items():
        print(f"  {fam}")
        for r, text in sorted(rs.items()):
            ch = r16.chain_down(xsd, short(r))
            where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(short(t) + ("[]" if tb else "") for t, tb in ch[1])
            if ch is None:
                unplaced.append(short(r))
            print(f"    {short(r)[:78]:78s} {where[:120]}")
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', text, re.S)
            gate = "always on"
            if m and "<rul:If>" in m.group(0):
                tests = [a or ("exists " + b.rsplit("/", 1)[-1]) for a, b in
                         re.findall(r'FromDataDef="([^"]+)"|AtInputDataDef="([^"]+)"', m.group(0))]
                consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(0)) if c not in ("0", "1")]
                gate = ", ".join(dict.fromkeys(t.rsplit("/", 1)[-1] for t in tests)) + f" = {consts[:4]}"
            elif m is None:
                gate = "no switch rule"
            shapes[(fam, gate)].append(short(r))
    print(f"\n  records without an attach point in the XSD: {unplaced or 'none'}")
    print("\n  on-switch shapes (SetCoverageOnPolicyIndicator), paths shortened:")
    for (fam, gte), rs in sorted(shapes.items()):
        print(f"    {fam[:30]:30s} {len(rs):2d} files: {gte[:180]}")
    print("\n  state rewrites of the on-switch (every in-force package):")
    names = {r for rs in pop.values() for r in rs}
    for j in s18.STATES:
        rd = book_for(j, ASOF).state.package.content / "Rules"
        if not rd.exists():
            continue
        for f in sorted(rd.glob("*.xml")):
            stem = f.name[:-len("Rules.Rule.xml")]
            if stem not in names:
                continue
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
            if m:
                bare = "<rul:If>" not in m.group(0)
                val = re.findall(r'ToDataDef="CoverageOnPolicyIndicator">(\d)<', m.group(0))
                fields = sorted(set(x.rsplit("/", 1)[-1] for x in re.findall(r'FromDataDef="([^"]+)"', m.group(0))))
                print(f"    {j} {short(stem)[:66]:66s} " + (f"always {val}" if bare else f"{fields}"))
    zero = set()
    print("\n  containers (no SetPremium) and their Set rules:")
    for fam, pat in cen.FAMILIES:
        for f in sorted((CW / "Rules").glob("*.xml")):
            if not re.search(pat, f.name) or cen.EXCLUDE.search(f.name):
                continue
            t = f.read_text(encoding="utf-8-sig")
            for m in re.finditer(r'<rul:Constant Type="decimal" ToDataDef="(\w+)">0(?:\.0)?</rul:Constant>', t):
                if m.group(1) != "Premium":
                    zero.add((short(f.name), m.group(1)))
            if not cen.set_premium(t):
                sets = [x for x in cen.rule_names(t) if x.startswith(("Set", "Attach", "Delete"))]
                print(f"    {short(f.name)[:62]:62s} {len(sets):2d}: {', '.join(sets[:8])}{' ...' if len(sets) > 8 else ''}")
    print("  rates / factors a rule sets to 0 (a $0 with no switch):")
    for f, what in sorted(zero):
        print(f"    {f[:62]:62s} {what}")


# ------------------------------------------------------------------ C20-04

PIER = "Fire Resistive Including Pier Deck and Pier Platform, but Without Superstructure"


def container_fields():
    """container (short name) -> its inputs, from the rules that read them and the Domain Tables."""
    rc = {"Limit": "50000", "Rate": "0.100"}
    pw = {"Construction": PIER, "Limit": "40000"}
    acp = {"Type": "Bulkheads, Pilings, Piers, Wharves or Docks", "WatercraftExclBuybackConstrctnOption": PIER,
           "Limit": "30000"}
    return {
        "RadioactiveContamination": rc, "RadioactiveContaminationPrsnlProp": rc, "RadioactiveContaminationBusnIncome": rc,
        "RadioactiveContaminationSpecialClass": rc, "RadioactiveContaminationSpclClassBusnIncome": rc,
        "PierAndWharfAdditionalCoveredCausesOfLossStruct": pw, "PierAndWharfAdditionalCoveredCausesOfLoss": pw,
        "PierAndWharfAdditionalCoveredCausesOfLossSpecialClass": pw, "PierAndWharfAdditionalCoveredCausesOfLossSpclClassBusnIncome": pw,
        "LocationFireDepartmentCharge": {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes", "Limit": "25000"},
        "PersonalPropertySpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFur": {"Indicator": "Yes", "Limit": "20000"},
        "PersonalPropertySpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetals": {
            "Indicator": "Yes", "Limit": "20000", "ValueIndicator": "Worth more than $100 per item"},  # switch: ValueIndicator not blank
        "PersonalPropertySpecialCOLPatternsDiesMoldsAndForms": {"Indicator": "Yes", "Limit": "20000"},
        "PersonalPropertySpecialCOLStampsTicketsAndLettersOfCredit": {"Indicator": "Yes", "Limit": "20000"},
        "AdditionalCoveredPropertyDetail": acp, "AdditionalCoveredPropertySpecialClassDetail": acp,
        "FoodContaminationBusinessInterruptionAndExtraExpenseAddlAdvCov": {"AdvertisingLimit": "10000"},
        "FoodContaminationBusinessInterruptionAndExtraExpenseFoodOnlyCov": {"FoodLimit": "10000"},
        "FoodContaminationBusinessInterruptionAndExtraExpenseSpclClassBusnIncomeAddlAdvCov": {"AdvertisingLimit": "10000"},
        "FoodContaminationBusinessInterruptionAndExtraExpenseSpclClassBusnIncomeFoodOnlyCov": {"FoodLimit": "10000"},
        "MortgageholdersErrorsAndOmissionsCoverageForm": {"Limit": "25,000", "NumberMortgages": "600"},
        "ChangesFungusWetRotDryRotBacteria": {"SubLimit": "50000", "FungusWetRotDryRotBacteriaCovLocApply": "Policy Limit",
                                              "IncreasedPeriodOfRestoration": "90",
                                              "FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator": "Yes"},
        # the occupancy group number keys on the building's class (0951): Institutional / "All other" -> group 3
        "EquipmentBreakdownCauseOfLossBldg": {"OccupancyCategory": "Institutional", "OccupancyGroup": "All other institutional risks"},
        "EquipmentBreakdownCauseOfLossBusnInc": {"OccupancyCategory": "Institutional", "OccupancyGroup": "All other institutional risks"},
        "EquipmentBreakdownCauseOfLossBldgAmmoniaContaminationCov": {"AmmoniaContamination": "50000"},  # switch: > 25,000, so 25,000 stays off
        "EquipmentBreakdownCauseOfLossBldgHazardousSubstanceOtherThanAmmoniaCov": {
            "HazardousSubstanceOtherThanAmmonia": "50000", "HazardousSubstanceOtherThanAmmoniaManualPremium": "100"},
    }


def family_tree(pop, xsd, cause, tobacco=False):
    """175_'s Oregon policy with every chunk 20 record placed, each container given its inputs; the Business
    Income increased-period indicator on (the BI fungus records feed the policy fungus record)."""
    sub = base(cause)
    at = rc1.node_dicts(sub)
    at[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
    # the EB waiting-period record switches on only when BI carries the no-waiting-period endorsement with a TimePeriod
    nw = P + "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod"
    at[P + "BusinessIncome"][nw + "Table"] = {nw: [{"TimePeriod": "Eliminated"}]}
    if tobacco:
        at[P + "OccupClass"]["CovForm"] = "Tobacco Sales Warehouse Coverage Form"
    cf = container_fields()
    recs = [r for rs in pop.values() for r in rs] + [
        P + "BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverage" + f + "Coverage" for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
    for r in recs:
        ch = r16.chain_down(xsd, short(r))
        if ch is None:
            continue
        top, steps = ch
        d = rc1.node_dicts(sub)[top]
        for t, table in steps:
            if table:
                lst = d.setdefault(t + "Table", {t: []})[t]
                if not lst:
                    lst.append({})
                d = lst[-1]
            else:
                d = d.setdefault(t, {})
            for k, v in cf.get(short(t), {}).items():
                d.setdefault(k, v)
    return sub


def borrowed(pop, xsd):
    progress("C20-04  BORROWED VALUES")
    print("\n" + "=" * 90 + "\nC20-04  BORROWED VALUES (hand = engine on the Oregon policy, every node)\n" + "-" * 90)
    priced, zero, notsetup = set(), collections.defaultdict(set), {}
    trees = [("Special", False), ("Broad", False), ("Basic", False), ("Special", True)]
    for i, (cause, tob) in enumerate(trees, 1):
        label = f"cause {cause}" + (", occupancy on the Tobacco Sales Warehouse form" if tob else "")
        progress(f"  [{i}/{len(trees)}] tree: {label}")
        try:
            data, _ = gc.run(family_tree(pop, xsd, cause, tob), "OR")
        except InterpretError as exc:
            check(False, f"{label}: tree raised {str(exc)[:160]}")
            continue
        n = n_ok = 0
        for fam, rs in pop.items():
            for r in sorted(rs):
                body = cen.set_premium(rs[r])
                nodes_ = r16.find(data, r)
                if not nodes_:
                    zero[short(r)].add(f"{cause}{'/tob' if tob else ''}: not on the rated tree")
                    continue
                for node in nodes_:
                    prem = node.first("Premium")
                    eng = money(prem.text if prem is not None else None)
                    cov = node.first("CoverageOnPolicyIndicator")
                    if cov is not None and cov.text == "0":
                        zero[short(r)].add(f"{cause}{'/tob' if tob else ''}: switched off")
                        continue
                    h = r16.hand(body, node)
                    try:
                        hv = Decimal(str(h))
                    except ArithmeticError:
                        hv = None
                    if hv is None and eng == 0:
                        notsetup[short(r)] = str(h)[:70]
                        continue
                    n += 1
                    if hv == eng:
                        n_ok += 1
                        if eng == 0:
                            zero[short(r)].add(f"{cause}{'/tob' if tob else ''}: $0 with the switch on")
                        else:
                            priced.add(short(r))
                    else:
                        check(False, f"{short(r)} ({label}): hand {h}, engine {eng}")
        check(n_ok == n, f"{label}: hand = engine on {n_ok} of {n} switched-on nodes")
    total = sum(len(v) for v in pop.values())
    print(f"\n  records priced (> $0, hand = engine) on at least one tree: {len(priced)} of {total}")
    check(len(priced) == total, f"every chunk 20 record prices > $0 with hand = engine on some tree: {len(priced)} of {total}")
    for fam, rs in pop.items():
        print(f"    {fam[:40]:40s} {sum(1 for r in rs if short(r) in priced)} of {len(rs)}")
    if notsetup:
        print("  hand met a blank the engine read as 0 (an input not set up here):")
        for r, why in sorted(notsetup.items()):
            print(f"    {r[:70]:70s} {why}")
    print("  records not priced on any tree, and why:")
    for r, why in sorted(zero.items()):
        if r not in priced:
            print(f"    {r[:74]:74s} {'; '.join(sorted(why))[:110]}")
    return priced


# ------------------------------------------------------------------ C20-05

WORDS = {"Radioactive Contamination": ["Radioactive"], "Pier and Wharf": ["PierAndWharf", "Watercraft"],
         "Fire Department Service Charge": ["FireDepartment"], "Tobacco Sales Warehouses": ["Tobacco"],
         "Special Cause of Loss (furs, jewelry, patterns, stamps)": ["SpecialLimit", "BaseSpecialLimit", "PreciousMetal", "Furs", "Stamps", "Patterns"],
         "Additional Covered Property": ["AdditionalCovered", "Watercraft"],
         "Food Contamination": ["FoodContamination", "AdditionalAdvertising"],
         "Mortgageholders E&O": ["Mortgage"], "Fungus, Wet Rot, Dry Rot changes": ["Fungus"],
         "Equipment Breakdown": ["EquipmentBreakdown", "OccupancyGroup", "Ammonia", "HazardousSubstance"]}


def tables_and_literals():
    progress("C20-05  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC20-05  TABLES AND LITERALS\n" + "-" * 90)
    header_only = []
    for fam, pat in cen.FAMILIES:
        texts = [f.read_text(encoding="utf-8-sig") for f in (CW / "Rules").glob("*.xml")
                 if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        stexts = []
        for j in s18.STATES:
            rd = book_for(j, ASOF).state.package.content / "Rules"
            if rd.exists():
                stexts += [f.read_text(encoding="utf-8-sig", errors="replace") for f in rd.glob("*.xml")
                           if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        tabs = sorted(set(t for s in texts + stexts for t in re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
        print(f"  {fam}")
        for t in tabs:
            f = CW / "Rate Tables" / f"{t}.RateTable.csv"
            n = cen.rows(f) if f.exists() else None
            filers = []
            for j in s18.STATES:
                sf = book_for(j, ASOF).state.package.content / "Rate Tables" / f"{t}.RateTable.csv"
                if sf.exists():
                    filers.append(f"{j}:{cen.rows(sf)}")
                    if cen.rows(sf) == 0:
                        header_only.append(f"{j} {t}")
            joined = " ".join(filers)
            print(f"    reads {t:56s} CW rows {n if n is not None else 'NOT FILED'}"
                  + (f"; states {joined[:70]}{' ...' if len(joined) > 70 else ''}" if filers else ""))
        filed = collections.defaultdict(list)
        for j in s18.STATES:
            td = book_for(j, ASOF).state.package.content / "Rate Tables"
            if td.exists():
                for f in td.glob("*.RateTable.csv"):
                    name = f.name[:-len(".RateTable.csv")]
                    if name not in tabs and any(w in name for w in WORDS[fam]):
                        filed[name].append(f"{j}:{cen.rows(f)}")
        for t, js in sorted(filed.items()):
            print(f"    state-filed, NOT read by a family file: {t:44s} {' '.join(js)[:60]}")
        lits = collections.Counter()
        for s in texts:
            for m in re.finditer(r'<rul:(Equal|NotEqual)>(.*?)</rul:\1>', s, re.S):
                for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(2)):
                    lits[c] += 1
        print(f"    literals compared in tests: {', '.join(repr(k) for k, _ in lits.most_common(18))}")
    print("\n  header-only state tables a family file reads (the engine falls back to CW rows; ISO does not always, C19-17):")
    print("    " + (", ".join(sorted(set(header_only))) if header_only else "none"))


def blanket(pop):
    """Radioactive Contamination on chunk 9's two-building blanket (A3's), rates 0.100 / 0.200 so the blanket
    average differs from either building's own rate. The blanket detail's RadioactiveContamination picks the
    reading: "Yes" prices each building at the blanket's average rate x its blanketed LimitToUse; "No" at its
    own rate x its own limit. Hand = engine on every node, and the two readings must differ."""
    progress("C20-04  BLANKET RADIOACTIVE")
    print("\n  Blanket (chunk 9's A3, two buildings in one blanket), Radioactive Contamination on each:")
    g = import_module("187_chunk18_rc2")
    out = {}
    for flag in ("Yes", "No"):
        sub = g.a3()
        cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
        cp["CommercialPropertyBlanketRatingTable"]["CommercialPropertyBlanketRating"][0][
            "CommercialPropertyBlanketRatingDetailTable"]["CommercialPropertyBlanketRatingDetail"][0]["RadioactiveContamination"] = flag
        sts = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]
        for st, rate in zip(sts, ("0.100", "0.200")):
            st[P + "RadioactiveContaminationTable"] = {P + "RadioactiveContamination": [{"Limit": st["Limit"], "Rate": rate}]}
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"blanket, detail RadioactiveContamination {flag}: raised {str(exc)[:160]}")
            continue
        body = cen.set_premium({r: t for rs in pop.values() for r, t in rs.items()}[P + "RadioactiveContamination"])
        prems = []
        for node in r16.find(data, P + "RadioactiveContamination"):
            prem = node.first("Premium")
            eng = money(prem.text if prem is not None else None)
            h = r16.hand(body, node)
            st = node.parent.parent
            avg = st.first("BlktRadioactiveContaminationAvgRate")
            print(f"    detail {flag:3s}: own rate {node.first('Rate').text:6s} blanket avg "
                  f"{avg.text if avg is not None else None!s:8s} LimitToUse {st.first('LimitToUse').text:>8s}: hand {h}, engine {eng}")
            check(Decimal(str(h)) == eng and eng > 0, f"blanket {flag}: hand = engine > $0 ({h} / {eng})")
            prems.append(eng)
        out[flag] = prems
    check(len(out) == 2 and out["Yes"] != out["No"], f"the two readings price differently: average {out.get('Yes')} vs own {out.get('No')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-stored", action="store_true", help="skip C20-02's re-rating of the stored responses")
    a = ap.parse_args()
    pop = population()
    xsd = rc1.xsd_for(book_for("OR", ASOF))
    total = sum(len(rs) for rs in pop.values())
    print(f"{book_for('OR', ASOF)}\n" + "\n".join(f"  {fam}: {len(rs)} premium records" for fam, rs in pop.items()) + f"\n  total {total}")
    check(total == 28, f"28 countrywide premium records, as the census ({total})")
    zero_records(a.skip_stored)
    flips()
    attach_and_switches(pop, xsd)
    borrowed(pop, xsd)
    blanket(pop)
    tables_and_literals()
    m, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1 (C20-02 to C20-05): ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED") + f"  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
