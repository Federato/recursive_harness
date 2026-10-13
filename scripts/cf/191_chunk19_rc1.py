#!/usr/bin/env python3
"""Chunk 19, RC-1 (C19-02 to C19-05): evidence and plumbing, before any golden case.

C19-02  THE 6 RECORDS ISO ALREADY PRICED. One stored policy (STC_CP000015565, NM) carries the
        UNSCHEDULED tenants' container with glass (450,000) and other than glass (500,000), cause
        Special, no earthquake: ISO priced Group I, Group II and Special for both kinds (6 records)
        and $0 on Broad and EQ (4). Re-rated as stored (at 2026-09-17, as every chunk 13 fixture):
        ISO = ours on all 10, and each SetPremium evaluated by hand from the landed values (174_'s
        evaluator): hand = engine. Then which input turns each record on, flipped one at a time on
        chunk 7's Oregon policy (read from the rules first, 2026-09-29):
          scheduled vs unscheduled   which container sits on the Structure (Scheduled... has a Detail
                                     row per item with its own Limit; Unscheduled... carries the two
                                     limits itself)
          glass / other than glass   the container's CovType ("Building Glass", "Building Property
                                     Other Than Glass", "Building Glass And Building Property Other
                                     Than Glass"); blank switches both off
          Broad vs Special           the container's OWN CausesOfLoss (not the building's CauseOfLoss)
          earthquake                 the container's EQCovIndicator AND the building's earthquake
                                     election (the EQ forms read the building's EQRate: chunk 10)
          deductibles                a blank glass / other-than-glass deductible prices $0 (its factor
                                     lookup finds no row), with no switch and no message
        Found by the first run: the SCHEDULED glass limit is the container's own Limit; each Detail row
        (an item) carries its own Limit for other than glass. Each flip's count of priced records is
        asserted. No ISO calls.
C19-03  ATTACH MAP AND SWITCHES. Each premium record's chain up to its coverage record (DataDef XSD),
        each container's own Set rules, every on-switch shape (SetCoverageOnPolicyIndicator, and FL's
        state rewrites of it), and every rule that writes a 0 into a rate / factor (a $0 with no switch).
C19-04  BORROWED VALUES. Every record placed on 175_'s Oregon policy (chunk 7 + 15 + chunk 10's
        earthquake election) with its container's inputs, on three trees (Basic, Broad, Special) plus two
        with the contents row in a blanket (Manufacturers' switch); every SetPremium operand resolved
        from its node in its loop context, evaluated by hand (174_'s evaluator) on EVERY node (the
        scheduled items are lists): hand must equal engine. Records at $0 are listed with the reason.
C19-05  TABLES AND LITERALS. Every table the family files read (CW and every state's own files), CW
        rows, which states file their own rows (header-only ones named), every state-filed table under
        ANY family name that no family file reads, the literals the tests compare, and the key rows
        RC-2 needs.

    python scripts/cf/191_chunk19_rc1.py

Progress streams as [i/n elapsed] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
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

book_for = functools.lru_cache(maxsize=None)(book_for)                  # see 180_ / 183_ (2026-09-28)

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
cen = import_module("900_chunk19_census")
r2 = import_module("175_chunk16_rc2")                  # its base(): chunk 7 + 15 modifiers + chunk 10 EQ
ASOF = "20260917"
P = "CommercialProperty"
RES = ROOT / "results" / "cf-raas"
FAIL = []
short = r16.short
FIXTURE = "STC_CP000015565"
UNS = "UnscheduledBuildingPropertyTenantsPolicy"
SCH = "ScheduledBuildingPropertyTenantsPolicy"
KINDS = ("BuildingGlass", "BuildingPropertyOtherThanGlass")
FORMS = ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")


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
    """family -> {premium record (file stem, 'CommercialProperty...'): CW rule text}."""
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


def uns_rec(kind, form):
    """the unscheduled record names: glass uses 'Earthquake', other than glass 'EQ'."""
    f = "EQ" if (form == "Earthquake" and kind != "BuildingGlass") else form
    return f"{P}{UNS}{kind}{f}Cov"


def hand_vs_engine(pop, data, rec):
    """(engine premium, hand premium or reason) for the first node of rec on a rated tree."""
    text = next((rs[rec] for rs in pop.values() if rec in rs), None)
    nodes_ = r16.find(data, rec)
    if text is None or not nodes_:
        return None, "no node"
    prem = nodes_[0].first("Premium")
    eng = money(prem.text if prem is not None else None)
    cov = nodes_[0].first("CoverageOnPolicyIndicator")
    if cov is not None and cov.text == "0":
        return eng, "switched off"
    h = r16.hand(cen.set_premium(text), nodes_[0])
    try:
        return eng, Decimal(str(h))
    except ArithmeticError:
        return eng, str(h)[:60]


# ------------------------------------------------------------------ C19-02

def stored_six(pop):
    progress("C19-02  THE 6 RECORDS ISO ALREADY PRICED")
    print("=" * 90 + f"\nC19-02  THE RECORDS ISO ALREADY PRICED ({FIXTURE}, no ISO calls)\n" + "-" * 90)
    fx = rep.fixture_index()[FIXTURE]
    d = json.loads(fx.read_text(encoding="utf-8-sig"))
    req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                 "EffectiveDateTime": "2026-09-17T00:00:00"},
                                  "CommercialProperty": d["CommercialProperty"]}}
    resp = json.loads((RES / f"chunk13_fixture_{FIXTURE}_response.json").read_text(encoding="utf-8"))
    iso = {}

    def walk(o, k=None):
        if isinstance(o, dict):
            if k and k.startswith(P + UNS) and "Premium" in o:
                iso[k] = o.get("Premium")
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    data, _ = rep.cmp.rate(req)
    cont = r16.find(data, P + UNS)[0]
    g = lambda f: cont.first(f).text if cont.first(f) is not None else None
    print(f"  {d['SchemeKeys']['ProductName']}: container inputs CovType={g('CovType')!r}, CausesOfLoss={g('CausesOfLoss')!r}, "
          f"EQCovIndicator={g('EQCovIndicator')!r}, Coinsurance={g('Coinsurance')!r}; glass {g('LimitOnBuildingGlass')} "
          f"ded {g('DeductibleOnBuildingGlass')}, other than glass {g('LimitOnBuildingPropertyOtherThanGlass')} "
          f"ded {g('DeductibleOnBuildingPropertyOtherThanGlass')}")
    priced = 0
    for kind in KINDS:
        for form in FORMS:
            r = uns_rec(kind, form)
            eng, h = hand_vs_engine(pop, data, r)
            iv = money(iso.get(r))
            priced += iv > 0
            ok = eng == iv and (h == eng or (h == "switched off" and eng == 0))
            check(ok, f"{short(r)[:66]:66s} ISO ${iv}  ours ${eng}  hand {h}")
    check(priced == 6, f"{priced} of the 10 records carry a non-zero ISO premium (the census's 6)")
    ctot = cont.first("ErcCalculatedTotalPremium")
    print(f"  container total: ISO {resp and _container_total(resp)}, ours {ctot.text if ctot is not None else None}")
    for f in ("CoinsuranceFactor", "BuildingGlassBGILOIFactor", "BuildingPropertyOtherThanGlassBGILOIFactor",
              "SpecialBaseRate", "DeductibleOnBuildingGlassFactorBasicGroupI", "DeductibleOnBldgPropOTGFactorSpecial"):
        print(f"    {f:48s} ours {g(f)}")
    return data


def _container_total(resp):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + UNS:
                out.append(o.get("ErcCalculatedTotalPremium"))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return out[0] if out else None


def tenants_tree(scheduled, cov_type, causes, eq="No", items=1, deductibles=True, eq_building=False):
    """chunk 7's Oregon policy (175_'s, with chunk 10's earthquake election on the building, when
    eq_building) + one tenants' container on the building. SCHEDULED: the glass limit is the
    container's own Limit and each Detail row is an item with its own Limit (other than glass);
    UNSCHEDULED: the container carries both limits (read from the rules, first run 2026-09-29)."""
    sub = r2.base() if eq_building else grp.five()
    st = rc1.node_dicts(sub)[P + "Structure"]
    st.setdefault("WindstormOrHailDeductible", "1,000")
    c = {"CovType": cov_type, "CausesOfLoss": causes, "EQCovIndicator": eq, "Coinsurance": "80%"}
    if deductibles:
        c.update({"DeductibleOnBuildingGlass": "1,000", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000"})
    if scheduled:
        c["Limit"] = "45000"
        c[P + SCH + "DetailTable"] = {P + SCH + "Detail": [{"Limit": str(40000 + 10000 * i)} for i in range(items)]}
        st[P + SCH + "Table"] = {P + SCH: [c]}
    else:
        c.update({"LimitOnBuildingGlass": "45000", "LimitOnBuildingPropertyOtherThanGlass": "50000"})
        st[P + UNS + "Table"] = {P + UNS: [c]}
    return sub


def flips(pop):
    print("\n  Flip each switch on the Oregon policy (the tenants' container on chunk 7's building):")
    fam = pop["Tenants' Building Property / Glass"]
    both = "Building Glass And Building Property Other Than Glass"
    # (label, scheduled, CovType, CausesOfLoss, EQCovIndicator, extra tenants_tree arguments)
    cases = [
    # the last element: how many records price > $0 (predicted from the switch rules above)
        ("unscheduled, both kinds, Special", False, both, "Special", "No", {}, 6),
        ("unscheduled, glass only, Special", False, "Building Glass", "Special", "No", {}, 3),
        ("unscheduled, other than glass only, Special", False, "Building Property Other Than Glass", "Special", "No", {}, 3),
        ("unscheduled, CovType blank", False, "", "Special", "No", {}, 0),
        ("unscheduled, both kinds, Broad", False, both, "Broad", "No", {}, 6),
        ("unscheduled, both kinds, CausesOfLoss blank", False, both, "", "No", {}, 4),
        ("unscheduled, EQ Yes, NO building earthquake", False, both, "Special", "Yes", {}, 6),
        ("unscheduled, EQ Yes, building earthquake (ch 10)", False, both, "Special", "Yes", {"eq_building": True}, 8),
        ("unscheduled, EQ No, building earthquake (ch 10)", False, both, "Special", "No", {"eq_building": True}, 6),
        ("unscheduled, deductibles blank", False, both, "Special", "No", {"deductibles": False}, 0),
        ("scheduled, both kinds, Special, 2 items", True, both, "Special", "No", {}, 9),
        ("scheduled, glass only, 2 items", True, "Building Glass", "Special", "No", {}, 3),
        ("scheduled, CovType blank, 2 items", True, "", "Special", "No", {}, 0),
        ("scheduled, deductibles blank, 2 items", True, both, "Special", "No", {"deductibles": False}, 0),
    ]
    for label, sch, ct, col, eq, kw, want in cases:
        try:
            data, _ = gc.run(tenants_tree(sch, ct, col, eq, items=2, **kw), "OR")
        except InterpretError as exc:
            check(False, f"{label}: raised {str(exc)[:120]}")
            continue
        on, bad = [], []
        for r in fam:
            if (SCH in r) != sch:
                continue
            text = pop["Tenants' Building Property / Glass"][r]
            for n in r16.find(data, r):
                p = money(n.first("Premium").text if n.first("Premium") is not None else None)
                if p:
                    on.append(re.sub(rf"^{P}(Uns|S)cheduledBuildingPropertyTenantsPolicy(Detail)?", "", r) + f" ${p}")
                cov = n.first("CoverageOnPolicyIndicator")
                if cov is not None and cov.text == "0":
                    continue
                h = r16.hand(cen.set_premium(text), n)          # every node: the scheduled items are a list
                try:
                    hv = Decimal(str(h))
                except ArithmeticError:
                    hv = None
                if hv is not None and hv != p:
                    bad.append(f"{short(r)} hand {hv} engine {p}")
        check(len(on) == want, f"{label:48s} {len(on)} priced (predicted {want}): {', '.join(on) if on else 'none'}")
        for b in bad:
            check(False, b)


# ------------------------------------------------------------------ C19-03

def attach_and_switches(pop, xsd):
    progress("C19-03  ATTACH MAP AND SWITCHES")
    print("\n" + "=" * 90 + "\nC19-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    shapes = collections.defaultdict(list)
    unplaced = []
    for fam, rs in pop.items():
        print(f"  {fam}")
        for r, text in sorted(rs.items()):
            ch = r16.chain_down(xsd, short(P + r[len(P):]))
            where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(
                short(t) + ("[]" if tb else "") for t, tb in ch[1])
            if ch is None:
                unplaced.append(r)
            print(f"    {short(r):78s} {where}")
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', text, re.S)
            gate = "always on"
            if m and "<rul:If>" in m.group(0):
                tests = [a or ("exists " + b.rsplit("/", 1)[-1]) for a, b in
                         re.findall(r'FromDataDef="([^"]+)"|AtInputDataDef="([^"]+)"', m.group(0))]
                consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(0)) if c not in ("0", "1")]
                gate = ", ".join(dict.fromkeys(t for t in tests)) + f" = {consts}"
            body = cen.set_premium(text)
            if re.search(r"<rul:(If|Choose)>", body):
                cond = sorted(set(c.rsplit("/", 1)[-1] for c in re.findall(r'FromDataDef="([^"]+)"',
                              "".join(re.findall(r"<rul:Test>(.*?)</rul:Test>", body, re.S)))))
                gate += f"; SetPremium branches on {', '.join(cond)}"
            shapes[(fam, re.sub(r"\.\./", "", gate))].append(short(r))
    check(not unplaced, f"every premium record has an attach point in the DataDef XSD ({len(unplaced)} without: {unplaced[:3]})")
    print("\n  on-switch shapes (SetCoverageOnPolicyIndicator; ErcProcess writes $0 when it is 0), paths shortened:")
    for (fam, gte), rs in sorted(shapes.items()):
        print(f"    {fam[:26]:26s} {len(rs):2d} files: {gte[:200]}")
    # FL's state rewrites of the switch (the census: Tenants', Temporarily Away)
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
            t = f.read_text(encoding="utf-8-sig", errors="replace")
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', t, re.S)
            if m:
                fields = sorted(set(x.rsplit("/", 1)[-1] for x in re.findall(r'FromDataDef="([^"]+)"', m.group(0))))
                consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(0)) if c not in ("0", "1")]
                bare = "<rul:If>" not in m.group(0)
                val = re.findall(r'ToDataDef="CoverageOnPolicyIndicator">(\d)<', m.group(0))
                print(f"    {j} {short(stem)[:66]:66s} " + (f"always {val}" if bare else f"{fields} vs {consts[:4]}"))
    cw = book_for("OR", ASOF).parent.package.content / "Rules"
    zero = set()
    print("\n  containers (no SetPremium) and their Set rules:")
    for fam, pat in cen.FAMILIES:
        for f in sorted(cw.glob("*.xml")):
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
    # the blank-input defaults: every FirstValue default of 0 on a factor the premium multiplies by
    print("  a blank operand defaults to 0 in every SetPremium (FirstValue FromConstant 0 / 0.0): "
          f"{sum(1 for rs in pop.values() for t in rs.values() if 'FromConstant=\"0' in cen.set_premium(t))} of "
          f"{sum(len(rs) for rs in pop.values())} files")


# ------------------------------------------------------------------ C19-04

#: container (short name) -> its own inputs, from the rules that read them and the Domain Tables
#: (DomainTypeRadioTVAntenna, DomainHeightOfRadioAntenna, DomainOutsideSignConstrctnType / Placement)
def container_fields(cause):
    tc = cause if cause != "Basic" else "Special"          # the tenants' own CausesOfLoss (Broad / Special)
    both = "Building Glass And Building Property Other Than Glass"
    return {
        UNS: {"CovType": both, "CausesOfLoss": tc, "EQCovIndicator": "Yes", "Coinsurance": "80%",
              "LimitOnBuildingGlass": "45000", "DeductibleOnBuildingGlass": "1,000",
              "LimitOnBuildingPropertyOtherThanGlass": "50000", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000"},
        SCH: {"CovType": both, "CausesOfLoss": tc, "EQCovIndicator": "Yes", "Coinsurance": "80%", "Limit": "45000",
              "DeductibleOnBuildingGlass": "1,000", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000"},
        SCH + "Detail": {"Limit": "40000"},
        "RadioOrTelevisionAntennas": {"Limit": "30000"},
        "RadioOrTelevisionAntennasDetail": {"CauseOfLoss": cause, "Coinsurance": "80%", "Limit": "30000",
                                            "Type": "Towers - Broadcasting Antennas (Radio and TV)",
                                            "Height": "Not over 75 Feet in Height", "EQCovIndicator": "Yes"},
        "RadioOrTelevisionAntennasBusinessIncomeOrExtraExpense": {
            "Limit": "20000", "TypeOfRadioAndTVAntennas": "Towers - Broadcasting Antennas (Radio and TV)"},
        "OutdoorTreesShrubsAndPlants": {"AllItemLimit": "25000", "CauseOfLoss": cause, "VehExcl": "No"},
        "OutsideSignsDetail": {"CauseOfLoss": cause, "Coinsurance": "80%", "Limit": "15000", "ConstructionType": "Entirely Metal",
                               "SignPlacement": "Attached", "EQCovIndicator": "Yes"},
        "HouseholdPersonalPropertyCoverageDetail": {"Limit": "15000"},
        "LeasedPropertyDetail": {"Limit": "200000"},
        # 100,000: at 10,000 the Group II and Broad forms round to $0 (first run, 2026-09-29)
        "SpecifiedBusnPrsnlPropTempAwayFromPremisesDetail": {"Limit": "100000"},
    }


def family_tree(pop, xsd, cause, contents=None):
    """175_'s Oregon policy (chunk 7's five coverages, chunk 15's modifiers, chunk 10's earthquake
    election) with every chunk 19 record placed, each container given its inputs."""
    sub = r2.base()
    at = rc1.node_dicts(sub)
    at[P + "Structure"].setdefault("WindstormOrHailDeductible", "1,000")
    for k in ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome"):
        at[P + k]["CauseOfLoss"] = cause
    # the contents' OWN earthquake election: Brands, Household, Leased and Temporarily Away read the contents
    # row's EQCovIndicator / FinalEQRate, and 175_'s base elects earthquake on the building only (first run)
    st = at[P + "Structure"]
    at[P + "PersonalProperty"].update({k: st[k] for k in ("EQCovIndicator", "EQCoinsurance", "EQDeductible") if k in st})
    # the contents EQ base rate is also keyed on EQGrade, which the building never tests (chunk 10's C10-06);
    # Manufacturers' factor is keyed on the contents CovType (Stock 1.25; unlisted -> (1 - 1) = $0)
    at[P + "PersonalProperty"].update({"EQGrade": "2", "CovType": "Stock", "EQSprinklerLeakageOnly": "Not Applicable"})
    # and the contents' own earthquake endorsement record: without it the contents EQ deductible factor is 0
    # (SetEQDeductibleFactor reads the endorsement tables; chunk 10's contents case, 95_, carries it)
    r2.put(sub, "EarthquakeAndVolcanicEruptionEndorsementPrsnlProp")
    at[P + "PersonalProperty"].update(contents or {})
    cf = container_fields(cause)
    where = {}
    for rs in pop.values():
        for r in rs:
            ch = r16.chain_down(xsd, short(r))
            if ch is None:
                where[r] = None
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
            where[r] = short(top)
    return sub, where


def borrowed(pop, xsd):
    progress("C19-04  BORROWED VALUES")
    print("\n" + "=" * 90 + "\nC19-04  BORROWED VALUES (hand = engine on the Oregon policy, every node)\n" + "-" * 90)
    priced, zero, notsetup, wrappers = set(), collections.defaultdict(set), {}, []
    trees = [(c, None) for c in ("Basic", "Broad", "Special")]
    # Manufacturers switches OFF when the contents row is in a blanket (IncludedInBlkt NotEqual "Yes": the census
    # shape read "= Yes", the rule reads NotEqual); one tree shows it
    trees += [("Special", {"IncludedInBlkt": "Yes"})]
    # Temporarily Away EQ looks its factor up only when the contents' EQSprinklerLeakageOnly is "No" (row "EQ")
    # or "Yes" (row "Other"); chunk 10's "Not Applicable" sets it to 0. Brands' EQ rate is round3(contents
    # FinalEQRate x 0.1): at grade 2 (0.004 -> 0.0004) it rounds to 0; grade 1 (loss cost 0.008) clears it
    trees += [("Special", {"EQSprinklerLeakageOnly": "No", "EQGrade": "1"})]
    for i, (cause, contents) in enumerate(trees, 1):
        label = f"cause {cause}" + (", contents " + ", ".join(f"{k} {v}" for k, v in contents.items()) if contents else "")
        progress(f"  [{i}/{len(trees)}] tree: {label}")
        sub, where = family_tree(pop, xsd, cause, contents)
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"{label}: tree raised {str(exc)[:160]}")
            continue
        n_ok = n = 0
        for fam, rs in pop.items():
            for r in sorted(rs):
                nodes_ = r16.find(data, r)
                if not nodes_:
                    zero[short(r)].add(f"{cause}: not on the rated tree")
                    continue
                body = cen.set_premium(rs[r])
                for node in nodes_:
                    ops = r16.operands(body, node)
                    wrappers += [f"{short(r)}: {op}" for op, w in ops if "WRAPPER" in w]
                    prem = node.first("Premium")
                    eng = money(prem.text if prem is not None else None)
                    cov = node.first("CoverageOnPolicyIndicator")
                    if cov is not None and cov.text == "0":
                        zero[short(r)].add(f"{cause}: switched off")
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
                    ok = hv == eng
                    n_ok += ok
                    if not ok:
                        check(False, f"{short(r)} ({label}): hand {h}, engine {eng}")
                    elif eng == 0:
                        zero[short(r)].add(f"{cause}: $0 with the switch on")
                    else:
                        priced.add(short(r))
        check(n_ok == n, f"{label}: hand = engine on {n_ok} of {n} switched-on nodes")
    check(not wrappers, f"no operand lands on a Table wrapper ({len(wrappers)}: {wrappers[:2]})")
    total = sum(len(v) for v in pop.values())
    print(f"\n  records priced (> $0, hand = engine) on at least one tree: {len(priced)} of {total}")
    check(len(priced) == total, f"every premium record prices > $0 on at least one tree ({len(priced)} of {total})")
    for fam, rs in pop.items():
        got = sorted(short(r) for r in rs if short(r) in priced)
        print(f"    {fam[:34]:34s} {len(got)} of {len(rs)}")
    if notsetup:
        print("  parent not set up on this policy (hand met a blank the engine read as 0):")
        for r, why in sorted(notsetup.items()):
            print(f"    {r[:70]:70s} {why}")
    print("  records not priced on any tree, and why:")
    for r, why in sorted(zero.items()):
        if r not in priced:
            print(f"    {r[:74]:74s} {'; '.join(sorted(why))[:110]}")
    return priced


# ------------------------------------------------------------------ C19-05

#: words that mark a state-filed table as belonging to a family (any name, not only the ones read)
WORDS = {"Tenants' Building Property / Glass": ["BuildingGlass", "Tenants", "Deductible250", "NoDeductible"],
         "Radio / TV Antennas": ["Antenna", "EQSubLimitDeductible", "EQSubLimit"],
         "Outdoor Trees, Shrubs and Plants": ["OutdoorTrees", "VehExcl"],
         "Outside Signs": ["OutsideSign", "Sign"],
         "Brands and Labels": ["BrandsAndLabels"],
         "Household Personal Property": ["Household", "SpecialPrsnlPropRate"],
         "Leased Property": ["LeasedProperty", "AgreedValueFactor"],
         "Property Temporarily Away": ["AwayFromPremises", "TempAway"],
         "Manufacturers Consequential Loss": ["ManufacturersConsequential"]}


def family_texts(pat, j=None):
    """the family's rule files: countrywide (j None) or state j's own package."""
    rd = (book_for("OR", ASOF).parent.package.content if j is None else book_for(j, ASOF).state.package.content) / "Rules"
    if not rd.exists():
        return []
    return [f.read_text(encoding="utf-8-sig", errors="replace") for f in rd.glob("*.xml")
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]


def tables_and_literals(pop):
    progress("C19-05  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC19-05  TABLES AND LITERALS\n" + "-" * 90)
    cw = book_for("OR", ASOF).parent.package.content
    header_only_read = []
    for fam, pat in cen.FAMILIES:
        texts = family_texts(pat)
        stexts = {j: family_texts(pat, j) for j in s18.STATES}
        tabs = sorted(set(t for s in texts + [x for v in stexts.values() for x in v]
                          for t in re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
        print(f"  {fam}")
        for t in tabs:
            f = cw / "Rate Tables" / f"{t}.RateTable.csv"
            n = cen.rows(f) if f.exists() else None
            filers = []
            for j in s18.STATES:
                sf = book_for(j, ASOF).state.package.content / "Rate Tables" / f"{t}.RateTable.csv"
                if sf.exists():
                    filers.append(f"{j}:{cen.rows(sf)}")
                    if cen.rows(sf) == 0:
                        header_only_read.append(f"{j} {t}")
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
        print(f"    literals compared in tests: {', '.join(repr(k) for k, _ in lits.most_common(20))}")
    print("\n  header-only state tables a family file reads (the engine falls back to CW rows: CFResolvedBook,"
          " 2026-09-28):")
    print("    " + (", ".join(sorted(set(header_only_read))) if header_only_read else "none"))
    print("\n  key rows (CW) for RC-2:")
    for t in ("BrandsAndLabelsFactor", "BrandsAndLabelsMaxIncrease", "ManufacturersConsequentialLossAssumptionFactor",
              "SpecifiedPropertyAwayFromPremisesAddlPremiumFactor", "VehExclFactorOutdoorTrees", "Deductible250Factor",
              "BuildingGlassNoDeductibleFactor"):
        f = cw / "Rate Tables" / f"{t}.RateTable.csv"
        if f.exists():
            rows = f.read_text(encoding="utf-8-sig").strip().splitlines()
            print(f"    {t} ({len(rows) - 1} rows): {' | '.join(rows[:9])[:230]}")
        else:
            print(f"    {t}: not filed countrywide")


def main():
    pop = population()
    xsd = rc1.xsd_for(book_for("OR", ASOF))
    print(f"{book_for('OR', ASOF)}\n" + "\n".join(f"  {fam}: {len(rs)} premium records" for fam, rs in pop.items())
          + f"\n  total {sum(len(rs) for rs in pop.values())}")
    check(sum(len(rs) for rs in pop.values()) == 63, "63 countrywide premium records, as the census")
    stored_six(pop)
    flips(pop)
    attach_and_switches(pop, xsd)
    borrowed(pop, xsd)
    tables_and_literals(pop)
    m, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1 (C19-02 to C19-05): ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED") + f"  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
