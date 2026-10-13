#!/usr/bin/env python3
"""Chunk 21, RC-1: evidence and plumbing, before any golden case. No ISO calls.

C21-02  ATTACH MAP AND SWITCHES. Each premium record's chain from its nearest known coverage record (the
        package's own DataDef XSD: countrywide for Sewer and the condo options, FLORIDA's for the five
        FL-only records); every on-switch (`SetCoverageOnPolicyIndicator`, the `CovForm` / `CovType` /
        `PolicyType` gates, each state's rewrite of a switch); every blank-input default that zeroes a
        premium (a rate / factor / premium a rule sets to 0, a `FirstValue` whose fallback is 0 on the
        premium chain); then each switch flipped on a real engine tree.
C21-03  BORROWED VALUES. Each sewer record priced by hand from its OWN rule file (the Building and Special
        Class records band their own deductible on TotAmtInsurance / LimitToUse; Personal Property borrows
        the Building sewer record's factor, else 1; BI reads its No Waiting Period record's Factor), every
        borrowed value read where its ../ path lands, the state's table before CW's; hand = engine on 33 cases.
C21-04  LOSS ASSESSMENT BY HAND. The 21 rules written out (tiers 0 / 1,000 / 5,000 / 10,000 / Over 10,000 at
        12,000 / 15,000 / 17,500 / 20,000; sub-limit bands 1,000 .. 20,000 incl. 5,500 and 11,500; three causes
        and the SPP path; deductibles 250 / N/A / table values / blank / a non-value); hand = engine on 33.
C21-05  TABLES AND LITERALS. Every lookup in the chunk's files in every in-force package: each literal and
        caller-passed key has a row, input-fed keys against their dropdowns; which tables price and which only
        code; FL's empty stubs; then all seven CW records on one policy in every state on the engine.

    python scripts/cf/207_chunk21_rc1.py

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import functools
import re
import sys
import time
from importlib import import_module
import _iso_refusals as _iso                                    # noqa: E402
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402

rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
s18 = import_module("164_chunk14_c14-18_all_states")
cen = import_module("902_chunk21_census")
ASOF = "20260917"
P = "CommercialProperty"
FAIL = []
short = r16.short
CW = book_for("OR", ASOF).parent.package.content
FLPKG = book_for("FL", ASOF).state.package.content


def progress(what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def population(content):
    """family -> {premium record (file stem): rule text} in one package."""
    out = {}
    for fam, pat in cen.FAMILIES:
        out[fam] = {}
        for f in sorted((content / "Rules").glob("*.xml")):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                t = f.read_text(encoding="utf-8-sig")
                if cen.set_premium(t):
                    out[fam][f.name[:-len("Rules.Rule.xml")]] = t
    return out


def rule_body(text, name):
    m = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', text, re.S)
    return m.group(0) if m else None


def switch_of(text):
    body = rule_body(text, "SetCoverageOnPolicyIndicator")
    if body is None:
        return "no switch rule"
    if "<rul:If>" not in body:
        return f"always {re.findall(r'ToDataDef=.CoverageOnPolicyIndicator.>(\\d)<', body)}"
    fields = [a or ("exists " + b.rsplit("/", 1)[-1]) for a, b in
              re.findall(r'FromDataDef="([^"]+)"|AtInputDataDef="([^"]+)"', body)]
    consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', body) if c not in ("0", "1")]
    return ", ".join(dict.fromkeys(f.rsplit("/", 1)[-1] for f in fields)) + f"  = {consts[:6]}"


def premium_gates(text):
    """Fields the SetPremium rule tests before writing a premium (its If tests)."""
    body = rule_body(text, "SetPremium") or ""
    tests = re.findall(r"<rul:Test>(.*?)</rul:Test>", body, re.S)
    fields = []
    for t in tests:
        fields += [f.rsplit("/", 1)[-1] for f in re.findall(r'FromDataDef="([^"]+)"', t)]
    return list(dict.fromkeys(fields))


def zero_defaults(text):
    """(field, how) pairs where a blank input becomes 0 on this file's rules."""
    out = set()
    for m in re.finditer(r'<rul:Constant Type="decimal" ToDataDef="(\w+)">0(?:\.0)?</rul:Constant>', text):
        out.add((m.group(1), "rule writes 0"))
    for m in re.finditer(r'<rul:FirstValue[^>]*FromConstant="0(?:\.0)?"[^>]*FromDataDef="([^"]+)"', text):
        out.add((m.group(1).rsplit("/", 1)[-1], "FirstValue falls back to 0"))
    for m in re.finditer(r'<rul:FirstValue[^>]*FromDataDef="([^"]+)"[^>]*FromConstant="0(?:\.0)?"', text):
        out.add((m.group(1).rsplit("/", 1)[-1], "FirstValue falls back to 0"))
    return sorted(out)


# ------------------------------------------------------------------ C21-02

def attach_and_switches():
    progress("C21-02  ATTACH MAP AND SWITCHES")
    print("\n" + "=" * 90 + "\nC21-02  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    cw = population(CW)
    fl = population(FLPKG)
    fl_only = {fam: {r: t for r, t in rs.items() if r not in cw.get(fam, {})} for fam, rs in fl.items()}
    n_cw = sum(len(rs) for rs in cw.values())
    n_fl = sum(len(rs) for rs in fl_only.values())
    check(n_cw == 7, f"7 countrywide premium records, as the census ({n_cw})")
    check(n_fl == 5, f"5 FL-only premium records, as the census ({n_fl})")
    xsd_cw = rc1.xsd_for(book_for("OR", ASOF))
    xsd_fl = rc1.xsd_for(book_for("FL", ASOF))
    unplaced = []
    for label, pop, xsd in (("countrywide", cw, xsd_cw), ("FL-only (FL's own schema)", fl_only, xsd_fl)):
        print(f"\n  {label}")
        for fam, rs in pop.items():
            for r, text in sorted(rs.items()):
                ch = r16.chain_down(xsd, short(r))
                where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(short(t) + ("[]" if tb else "") for t, tb in ch[1])
                if ch is None:
                    unplaced.append(short(r))
                print(f"    {fam[:22]:22s} {short(r)[:60]:60s} {where[:140]}")
                print(f"        switch: {switch_of(text)[:160]}")
                g = premium_gates(text)
                if g:
                    print(f"        SetPremium tests: {', '.join(g)[:160]}")
                z = zero_defaults(text)
                if z:
                    print(f"        blank -> 0: " + "; ".join(f"{f} ({h})" for f, h in z)[:200])
    check(not unplaced, f"every premium record has an attach point in its package's schema ({unplaced or 'all placed'})")
    print("\n  state rewrites of an on-switch or a premium rule (every in-force package):")
    names = {r for rs in list(cw.values()) + list(fl_only.values()) for r in rs}
    rewrites = collections.defaultdict(list)
    for j in s18.STATES:
        rd = book_for(j, ASOF).state.package.content / "Rules"
        if not rd.exists():
            continue
        for f in sorted(rd.glob("*.xml")):
            stem = f.name[:-len("Rules.Rule.xml")]
            if stem not in names:
                continue
            t = f.read_text(encoding="utf-8-sig", errors="replace")
            ruled = [n for n in ("SetCoverageOnPolicyIndicator", "SetPremium") if rule_body(t, n)]
            if ruled:
                rewrites[j].append(f"{short(stem)} ({', '.join(ruled)})")
    for j, lst in sorted(rewrites.items()):
        print(f"    {j}: {'; '.join(lst)[:220]}")
    containers = []
    print("\n  containers (no SetPremium) in the families, with their Set / Attach / Delete rules:")
    for content in (CW, FLPKG):
        for fam, pat in cen.FAMILIES:
            for f in sorted((content / "Rules").glob("*.xml")):
                if not re.search(pat, f.name) or cen.EXCLUDE.search(f.name):
                    continue
                t = f.read_text(encoding="utf-8-sig")
                if cen.set_premium(t):
                    continue
                sets = [x for x in cen.rule_names(t) if x.startswith(("Set", "Attach", "Delete"))]
                tag = "CW" if content == CW else "FL"
                containers.append((tag, short(f.name)))
                print(f"    {tag} {short(f.name)[:60]:60s} {len(sets):2d}: {', '.join(sets[:9])}{' ...' if len(sets) > 9 else ''}")
                z = zero_defaults(t)
                if z:
                    print(f"        blank -> 0: " + "; ".join(f"{f} ({h})" for f, h in z)[:200])
    return cw, fl_only


r2 = import_module("175_chunk16_rc2")
g19 = import_module("192_chunk19_rc2")
gc = import_module("149_chunk13_golden_case")
def portable(j, cause="Special"):
    """The portable policy in state `j` (chunk 28 C28-05). In Florida, as 209_ builds it: no earthquake inputs (FL's
    BldgHeightFactor files no EQ class "A1": ISO refuses, C28-06 P1) and Florida's own special class description (it
    files no countrywide "Towers - Broadcasting Antennas": ISO refuses, OI-99). Since C28-05 ours refuses both too, so
    a Florida case built on the bare portable policy would test nothing. Other states keep the earthquake inputs: SC
    looks up its BCEG earthquake factor whatever is elected, and refuses a blank EQ territory (ISO too, C28-06 P12)."""
    sub = g19.with_cause(g19.portable(j), cause)
    if j == "FL":
        def no_eq(o):
            if isinstance(o, dict):
                for k in [k for k in o if k.startswith("EQ")]:
                    del o[k]
                for v in o.values():
                    no_eq(v)
            elif isinstance(o, list):
                for x in o:
                    no_eq(x)
        no_eq(sub)
        rc1.node_dicts(sub)[P + "SpecialClass"]["ClassDescription"] = import_module("177_chunk16_rc4").FL_SC
    return sub


SEWER = {"DischargeFromSewerDrainOrSumpNotFloodReltd": "DischargeLimitPD",
         "DischargeFromSewerDrainOrSumpNotFloodReltdPrsnlProp": "DischargeLimitPD",
         "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClass": "DischargeLimitPD",
         "DischargeFromSewerDrainOrSumpNotFloodReltdBusnIncome": "DischargeLimitBI",
         "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClassBusnIncome": "DischargeLimitBI"}
OPT = "CondominiumCommercialUnitOwnersOptionalCoverages"
LA = "CondominiumCommercialUnitOwnersOptionalCovLossAssmtCoverage"
MRP = "CondominiumCommercialUnitOwnersOptionalCovMiscRealPropCoverage"
UO_FORM = "Condominium Commercial Unit Owners Coverage"


def premiums(data, rec):
    out = []
    for n in rc1.find(data, P + rec):
        p = n.first("Premium")
        out.append(None if p is None else p.text)
    return out


def rated(sub, j="OR"):
    try:
        data, ip = gc.run(sub, j)
        return data, ip, None
    except Exception as exc:                                  # a refusal is a finding here, not a crash
        return None, None, f"{type(exc).__name__}: {str(exc)[:140]}"


def flips(fl_only):
    progress("C21-02  SWITCHES FLIPPED ON REAL TREES")
    print("\n  Each switch flipped on 175_'s Oregon policy (FL records on FL's own), engine only:")
    # Sewer: the record's own limit is the switch (no SetCoverageOnPolicyIndicator)
    for rec, lim in SEWER.items():
        row = []
        for label, fields in (("limit 25,000", {lim: "25000"}), ("attached, no limit", {}), ("not attached", None)):
            sub = g19.with_cause(g19.portable("OR"), "Special")
            if fields is not None:
                r2.put(sub, rec, fields)
            data, ip, err = rated(sub)
            row.append(f"{label}: {err or premiums(data, rec)}")
        print(f"    {short(rec)[:52]:52s} " + " | ".join(row))
        on = row[0]
        check("'0'" not in on.split(":", 1)[1] and "None" not in on and "Error" not in on,
              f"{short(rec)[:40]} prices when its limit is sent ({on})")
    # Condo options: the container's limits switch the two records
    # LossAssessmentLimit is an ENUM (Domain Tables: 0 / 1,000 / 5,000 / 10,000 / Over 10,000 + the
    # Over10000 amount); "10000" is not a value and leaves the rate blank. LossAssessmentDeductible is
    # 250 / All Other / Not Applicable; blank -> DeductibleFactor 0 -> premium 0 (a blank-input zero).
    LA_OK = {"LossAssessmentLimit": "10,000", "LossAssessmentDeductible": "250"}
    cases = (("LA 10,000, ded 250", LA_OK, ("+", "0")),
             ("LA 10000 (not an enum value)", {"LossAssessmentLimit": "10000", "LossAssessmentDeductible": "250"},
              "LossAssessmentLimitConverted"),                       # C28-05: refuses, as ISO does (C28-06 P2)
             ("LA 10,000, no deductible", {"LossAssessmentLimit": "10,000"}, ("0", "0")),
             ("LA 10,000, ded All Other", {"LossAssessmentLimit": "10,000", "LossAssessmentDeductible": "All Other"},
              "DeductibleFactor"),                                   # C28-05: refuses, as ISO does (C28-06 P3)
             ("LA Over 10,000 (25,000), ded N/A", {"LossAssessmentLimit": "Over 10,000", "LossAssessmentLimitOver10000": "25000",
                                                 "LossAssessmentDeductible": "Not Applicable"}, ("+", "0")),
             ("MRP 20,000", {"MiscRealPropLimit": "20000"}, "LossAssessmentRate"),   # the LA record, blank: MRZ, C28-02
             ("both", dict(LA_OK, MiscRealPropLimit="20000"), ("+", "+")),
             ("neither", {}, "LossAssessmentRate"))                 # C28-05: refuses, as ISO does (MRZ, C28-02)
    for label, cont, want in cases:
        for form in (UO_FORM, None):
            sub = g19.with_cause(g19.portable("OR"), "Special")
            pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
            pp[P + OPT + "Table"] = {P + OPT: [dict(cont, **{P + LA: {}, P + MRP: {}})]}
            if form:
                rc1.node_dicts(sub)[P + "OccupClass"]["CovForm"] = form
            data, ip, err = rated(sub)
            got = (err,) if err else (premiums(data, LA), premiums(data, MRP))
            print(f"    condo options, {label:34s} CovForm {'unit owners' if form else 'as the policy':13s} "
                  f"LA {got[0]}  MRP {got[-1]}")
            sign = tuple("+" if g and g[0] not in ("0", None) else "0" for g in got) if not err else _iso.table_of(err)
            check(sign == want, f"condo {label} / {'UO' if form else 'policy'} form: LA/MRP {want} ({got})")
    # FL: the SetPremium gates (CovForm / CovType + PolicyType), with a manual premium
    for rec in sorted(r for rs in fl_only.values() for r in rs):
        s = short(rec)
        for label, gate in (("gate met", True), ("gate not met", False)):
            sub = portable("FL")
            at = rc1.node_dicts(sub)
            spp = "SPP" in s
            if gate:
                # the two SPP records are ISO AUTO-ATTACH forms (FL OccupClass / SpecialClass rules
                # AttachForm...SPP...): created when their test holds, REMOVED when it does not
                at[P]["PolicyType"] = "Standard Property Policy" if spp else "Commercial Property Policy"
                if s.endswith("OccupClass"):
                    at[P + "OccupClass"]["CovForm"] = UO_FORM
                    if spp:
                        at[P + "OccupClass"]["ClassCode"] = "0331"
                elif s.endswith("SpecClass"):
                    at[P + "SpecialClass"]["CovForm"] = UO_FORM
                    if spp:
                        at[P + "SpecialClass"]["ItemsBelongToResidentialCondo"] = "Yes"
                else:
                    at[P + "Structure"]["CovType"] = "Condominium Association"
            r2.put(sub, s, {"ManualPremium": "100"}, state="FL")
            data, ip, err = rated(sub, "FL")
            got = err or premiums(data, s)
            print(f"    FL {s[-58:]:58s} {label:12s} {got}")
            want = (["98"] if gate else (["0"] if not spp else []))
            check(got == want, f"FL {s[-40:]} {label}: {want} ({got})")


# ------------------------------------------------------------------ C21-03

from decimal import ROUND_HALF_UP, Decimal                                # noqa: E402

NWP = "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod"
MODS = ("PackageModFactor", "MultiPremiumAndDispersionCreditFactor", "IRPMFactor")


def r(x, dp):
    return Decimal(x).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def up(n, k):
    for _ in range(k):
        n = n.parent
    return n


def val(n, f):
    c = n.first(f)
    return None if c is None or c.text in (None, "") else c.text


ORPKG = book_for("OR", ASOF).state.package.content


def table_rows(name, juris="OR"):
    """ISO table resolution: the in-force state package's table when it has one, else the CW base; inside
    it, the state's rows first, then CW's (the rules' FirstNonNull of two lookups)."""
    pkg = ORPKG if (ORPKG / "Rate Tables" / f"{name}.RateTable.csv").exists() else CW
    rows = r2.csv_rows(name, pkg)
    own = [x for x in rows if x["StateCode"] == juris]
    return own, [x for x in rows if x["StateCode"] == "CW"], pkg.name


def ded_by_hand(ded, amount):
    """SetDeductibleFactor, written out: 250 -> Deductible250Factor 'All Other'; N/A, blank or a zero amount
    -> 1.0; else DeductibleFactor banded on the amount (FromGreaterThan < amount <= To), 'Other Cause Of Loss'."""
    if ded == "250":
        own, cw, _ = table_rows("Deductible250Factor")
        return next(Decimal(x["Factor"]) for x in own + cw if x["CauseOfLoss"] == "All Other")
    if ded in (None, "", "Not Applicable") or Decimal(amount or 0) == 0:
        return Decimal("1.0")
    own, cw, _ = table_rows("DeductibleFactor")
    for rows in (own, cw):
        for x in rows:
            if (x["Deductible"] == ded and x["CauseOfLossDeductible"] == "Other Cause Of Loss"
                    and Decimal(x["Limit_FromGreaterThan"]) < Decimal(amount) <= Decimal(x["Limit_To"])):
                return Decimal(x["Factor"])
    raise LookupError(f"no DeductibleFactor row {ded} {amount}")


#: per record, from its OWN rule file: where the deductible factor comes from, how far up the mods are,
#: and (BI) which No Waiting Period record its FinalRate reads
HOW = {"DischargeFromSewerDrainOrSumpNotFloodReltd": ("own", "TotAmtInsurance", 6, None),
       "DischargeFromSewerDrainOrSumpNotFloodReltdPrsnlProp": ("borrow", None, 10, None),
       "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClass": ("own", "LimitToUse", 6, None),
       "DischargeFromSewerDrainOrSumpNotFloodReltdBusnIncome": (None, None, 8, NWP),
       "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClassBusnIncome": (None, None, 8, NWP + "SpclClassBusnIncome")}


def sewer_by_hand(node, rec, limit):
    """Premium from the record's own rules, every borrowed value read where its ../ path lands."""
    ded_mode, amount_field, depth, nwp_rec = HOW[rec]
    bi = rec.endswith("BusnIncome")
    parent = up(node, 2)                                      # ../../ : the coverage the sewer record sits on
    top = up(node, depth)                                     # where the modifiers' ../ path lands
    own, cw, _ = table_rows("DischargeFromSewerDrainOrSump")
    blc = next(Decimal(x["Rate"]) for x in own + cw if x["Type"] == ("BI" if bi else "PD"))
    lcm = Decimal(val(parent, "LossCostMultiplier") or 0)
    rate = r(blc * lcm, 3)
    mods = {m: Decimal(val(top, m) or 0) for m in MODS}
    lim = Decimal(limit) / 100
    if bi:
        nwp = [c for c in parent.children if c.tag == P + nwp_rec + "Table"]
        f = val(nwp[0].children[0], "Factor") if nwp and nwp[0].children else None
        final = r(rate * Decimal(f), 3) if f is not None else rate
        prem = r(r(r(final * lim, 0) * mods["PackageModFactor"], 0) * mods["IRPMFactor"], 0)
        return {"top": top.tag, "BaseLossCost": blc, "Rate": rate, "FinalRate": final, "Premium": prem}
    out = {"top": top.tag, "BaseLossCost": blc, "Rate": rate}
    if ded_mode == "own":
        dedf = out["DeductibleFactor"] = ded_by_hand(val(parent, "Deductible"), val(parent, amount_field))
    else:                                                     # PP: the Building sewer record's factor, else 1
        bld = [c for c in up(node, 6).children if c.tag == P + "DischargeFromSewerDrainOrSumpNotFloodReltdTable"]
        f = val(bld[0].children[0], "DeductibleFactor") if bld and bld[0].children else None
        dedf = Decimal(f) if f is not None else Decimal(1)
        out["borrowed DeductibleFactor"] = dedf
    p = r(rate * dedf, 3)
    for k in ("lim",) + MODS:
        p = r(p * (lim if k == "lim" else mods[k]), 0)
    out["Premium"] = p
    return out


def borrowed():
    progress("C21-03  BORROWED VALUES")
    print("\n" + "=" * 90 + "\nC21-03  BORROWED VALUES: each sewer record by hand vs the engine\n" + "-" * 90)
    parent_of = {"DischargeFromSewerDrainOrSumpNotFloodReltd": "Structure",
                 "DischargeFromSewerDrainOrSumpNotFloodReltdPrsnlProp": "PersonalProperty",
                 "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClass": "SpecialClass",
                 "DischargeFromSewerDrainOrSumpNotFloodReltdBusnIncome": "BusinessIncome",
                 "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClassBusnIncome": "SpecialClassBusnIncome"}
    variants = (("as built", lambda at, par: None),
                ("parent deductible 250", lambda at, par: par.__setitem__("Deductible", "250")),
                ("parent deductible Not Applicable", lambda at, par: par.__setitem__("Deductible", "Not Applicable")),
                ("parent deductible 5,000", lambda at, par: par.__setitem__("Deductible", "5,000")),
                ("parent LCM 1.25", lambda at, par: par.__setitem__("LossCostMultiplier", "1.25")),
                ("policy mods 0.9 / 0.95 / 1.1", lambda at, par: at[P].update(
                    PackageModFactor="0.9", MultiPremiumAndDispersionCreditFactor="0.95", IRPMFactor="1.1")),
                ("No Waiting Period endorsement", "NWP"),
                ("Building sewer too, parent deductible 5,000", "BLDG"))
    n = 0
    for rec, lim in SEWER.items():
        for label, how in variants:
            if (how == "NWP" and not rec.endswith("BusnIncome")) or (how == "BLDG" and not rec.endswith("PrsnlProp")):
                continue
            sub = g19.with_cause(g19.portable("OR"), "Special")
            at = rc1.node_dicts(sub)
            if how == "NWP":
                r2.put(sub, HOW[rec][3], {})
            elif how == "BLDG":                               # PP sewer borrows the Building sewer's factor
                at[P + "Structure"]["Deductible"] = "5,000"
                r2.put(sub, "DischargeFromSewerDrainOrSumpNotFloodReltd", {"DischargeLimitPD": "25000"})
            else:
                how(at, at[P + parent_of[rec]])
            r2.put(sub, rec, {lim: "25000"})
            data, ip, err = rated(sub)
            if err and rec.endswith("SpclClass") and "Not Applicable" in label and _iso.table_of(err) == "DeductibleFactor":
                print(f"    {short(rec)[-38:]:38s} {label:32s} ours REFUSES as ISO does (DeductibleFactor; C28-06 P4)")
                n += 1                                       # C28-05: the special class's N/A deductible has no row
                continue
            if err:
                check(False, f"{short(rec)[-30:]} {label}: engine raised {err}")
                continue
            nodes = rc1.find(data, P + rec)
            if len(nodes) != 1:
                check(False, f"{short(rec)[-30:]} {label}: {len(nodes)} records")
                continue
            node = nodes[0]
            hand = sewer_by_hand(node, rec, "25000")
            eng = {k: val(node, k) for k in hand if k != "top" and not k.startswith("borrowed")}
            same = all(eng[k] is not None and Decimal(eng[k]) == hand[k] for k in eng)
            n += 1
            print(f"    {short(rec)[-38:]:38s} {label:32s} hand {', '.join(f'{k} {v}' for k, v in hand.items() if k != 'top')}"
                  + ("" if same else f"   ENGINE {eng}"))
            check(same, f"{short(rec)[-30:]} {label}: hand = engine (mods from {hand['top'][len(P):] or P})")
    check(n == 5 * 6 + 2 + 1, f"33 hand/engine cases ran ({n})")


# ------------------------------------------------------------------ C21-04

def la_row(name, keycol, key, cause):
    own, cw, _ = table_rows(name)
    for rows in (own, cw):
        for x in rows:
            if x[keycol] == key and x["CauseOfLoss"] == cause:
                return Decimal(x["Rate"])
    return None


def la_by_hand(cont, pp, cp):
    """The 21 loss assessment rules, written out (CW CondominiumCommercialUnitOwnersOptionalCovLossAssmtCoverage
    + the container's converted limit / limit-to-use / multiple-of checks)."""
    lim = cont.get("LossAssessmentLimit", "")
    over = cont.get("LossAssessmentLimitOver10000")
    sub = int(cont.get("LossAssessmentSubLimit") or 0)
    ded = cont.get("LossAssessmentDeductible", "")
    out = {}
    if lim == "0" or lim == "":
        out["CoverageOnPolicyIndicator"] = "0" if lim == "0" else "1"
        if lim == "0":
            out["Premium"] = Decimal(0)
            return out
    cause = "Basic" if val(cp, "PolicyType") == "Standard Property Policy" else val(pp, "CauseOfLossToUse")
    # container
    conv = {"0": 0, "1,000": 1000, "5,000": 5000, "10,000": 10000}.get(lim)
    to_use = int(over) if lim == "Over 10,000" and over else conv
    m5 = "Yes"
    if lim == "Over 10,000" and int(over or 0) >= 15000:
        m5 = "Yes" if int(over) % 5000 == 0 else "No"
    m1 = "Yes" if sub <= 10000 or sub % 1000 == 0 else "No"
    # rates
    base = la_row("LossAssessmentRate", "LossAssessmentLimit", lim, cause)
    r10k = la_row("LossAssessmentRate", "LossAssessmentLimit", "10,000", cause)
    if lim == "Over 10,000":
        final = r((Decimal(over or 0) / 5000 - 2) * (base or 0) + r10k, 3) if m5 == "Yes" else Decimal("0.0")
        rate = final
    else:
        rate = base
    n = (sub // 1000 - 1) if (sub > 1000 and m1 == "Yes") else 0
    r1, r2_, r3_ = (la_row("LossAssessmentSubLimitRate", "LossAssessmentSubLimit", b, cause)
                    for b in ("Upto5000", "From6000To10000", "Over10000"))
    up5 = r(n * r1 if n < 4 else 4 * r1, 3)
    mid = r((n - 4) * r2_, 3) if 4 < n <= 9 else (r(5 * r2_, 3) if n > 9 else Decimal("0.0"))
    top = r((n - 9) * r3_, 3) if n > 9 else Decimal("0.0")
    subrate = up5 + mid + top if n > 0 else Decimal("0.0")
    # deductible
    if ded == "250":
        dedf = next(Decimal(x["Factor"]) for x in sum(table_rows("Deductible250Factor")[:2], []) if x["CauseOfLoss"] == "All Other")
    elif ded == "Not Applicable":
        dedf = Decimal("1.0")
    elif ded == "":
        dedf = Decimal("0.0")
    else:
        limded = {"1,000": 1000, "5,000": 5000, "10,000": 10000}.get(lim, int(over) if over else 0)
        own, cwr, _ = table_rows("DeductibleFactor")
        dedf = next((Decimal(x["Factor"]) for rows in (own, cwr) for x in rows
                     if x["Deductible"] == ded and x["CauseOfLossDeductible"] == "Other Cause Of Loss"
                     and Decimal(x["Limit_FromGreaterThan"]) < limded <= Decimal(x["Limit_To"])), None)
    lcm = Decimal(val(pp, "LossCostMultiplier") or 0)
    mods = [Decimal(val(cp, "PackageModFactor") or 0), Decimal(val(pp, "MultiPremiumAndDispersionCreditFactor") or 0),
            Decimal(val(cp, "IRPMFactor") or 0)]
    p = r(r((rate + subrate) * lcm, 3) * (dedf or 0), 3)
    for f in mods:
        p = r(p * f, 0)
    out.update({"Rate": rate, "SubLimitAdditionalThousandsNumber": Decimal(n), "SubLimitRate": subrate,
                "DeductibleFactor": dedf, "Premium": p,
                # Truncate(Divide DecimalPlaces=0): the divide ROUNDS first, so 17,500 -> 18, not 17
                "ExposureStatAmount": r(Decimal(to_use) / 1000, 0) if to_use else Decimal(0)})
    msgs = []
    if sub > (to_use or 0):
        msgs.append("Loss Assessment Sub Limit cannot be greater")
    if m1 == "No":
        msgs.append("SubLimit needs to be multiple of 1000")
    if m5 == "No":
        msgs.append("Over $10,000 needs to be multiple of 5000")
    out["messages"] = msgs
    return out


def loss_assessment():
    progress("C21-04  LOSS ASSESSMENT BY HAND")
    print("\n" + "=" * 90 + "\nC21-04  LOSS ASSESSMENT BY HAND: every tier and band boundary, hand vs engine\n" + "-" * 90)
    O = "Over 10,000"
    cases = []
    for lim, over in (("0", None), ("1,000", None), ("5,000", None), ("10,000", None), (O, "15000"), (O, "20000"),
                      (O, "12000"), (O, "17500")):
        c = {"LossAssessmentLimit": lim, "LossAssessmentDeductible": "1,000"}
        if over:
            c["LossAssessmentLimitOver10000"] = over
        cases.append((f"limit {lim}{' ' + over if over else ''}", "Special", None, c))
    for cause in ("Broad", "Basic", "SPP"):
        for lim, over in (("10,000", None), (O, "20000")):
            c = {"LossAssessmentLimit": lim, "LossAssessmentDeductible": "Not Applicable", "LossAssessmentSubLimit": "7000"}
            if over:
                c["LossAssessmentLimitOver10000"] = over
            cases.append((f"{cause} {lim}{' ' + over if over else ''} sub 7,000", "Special" if cause == "SPP" else cause,
                          "Standard Property Policy" if cause == "SPP" else None, c))
    for s in ("1000", "2000", "5000", "5500", "6000", "10000", "11000", "11500", "14000", "20000"):
        cases.append((f"sub-limit {s}", "Special", None, {"LossAssessmentLimit": O, "LossAssessmentLimitOver10000": "20000",
                                                         "LossAssessmentDeductible": "250", "LossAssessmentSubLimit": s}))
    cases.append(("sub-limit 6,000 over a 5,000 limit", "Special", None,
                  {"LossAssessmentLimit": "5,000", "LossAssessmentDeductible": "250", "LossAssessmentSubLimit": "6000"}))
    for d in ("250", "Not Applicable", "500", "1,000", "2,500", "", "All Other"):
        c = {"LossAssessmentLimit": "5,000", "LossAssessmentDeductible": d}
        cases.append((f"deductible {d or 'blank'} at 5,000", "Special", None, {k: v for k, v in c.items() if v}))
    cases.append(("deductible 2,500 at Over 10,000 = 25,000", "Special", None,
                  {"LossAssessmentLimit": O, "LossAssessmentLimitOver10000": "25000", "LossAssessmentDeductible": "2,500"}))
    ok_n = 0
    for i, (label, cause, ptype, cont) in enumerate(cases, 1):
        sub = g19.with_cause(g19.portable("OR"), cause)
        at = rc1.node_dicts(sub)
        if ptype:
            at[P]["PolicyType"] = ptype
        at[P + "PersonalProperty"][P + OPT + "Table"] = {P + OPT: [dict(cont, **{P + LA: {}})]}
        data, ip, err = rated(sub)
        if err and cont.get("LossAssessmentDeductible") == "All Other" and _iso.table_of(err) == "DeductibleFactor":
            print(f"    [{i:2d}/{len(cases)}] {label:40s} ours REFUSES as ISO does (DeductibleFactor; C28-06 P3)")
            ok_n += 1                                        # C28-05: "All Other" has no deductible row
            continue
        if err:
            check(False, f"[{i}/{len(cases)}] {label}: engine raised {err}")
            continue
        node = rc1.find(data, P + LA)[0]
        cnode = node.parent
        pp = up(node, 3)
        cp = up(node, 11)
        hand = la_by_hand(cont, pp, cp)
        eng = {k: val(node, k) for k in hand if k != "messages"}
        diffs = {k: (str(hand[k]), eng[k]) for k in eng
                 if not ((hand[k] is None and eng[k] is None)
                         or (hand[k] is not None and eng[k] is not None and Decimal(str(hand[k])) == Decimal(eng[k])))}
        emsgs = [str(m) for m in ip.messages]
        mdiff = [m for m in hand.get("messages", []) if not any(m in e for e in emsgs)]
        extra = [e for e in emsgs if any(k in e for k in ("Sub Limit", "SubLimit", "multiple of 5000"))
                 and not any(m in e for m in hand.get("messages", []))]
        good = not diffs and not mdiff and not extra
        ok_n += good
        print(f"    [{i:2d}/{len(cases)}] {label:40s} {cause if not ptype else 'SPP':8s} "
              f"rate {hand.get('Rate')} sub {hand.get('SubLimitRate')} ded {hand.get('DeductibleFactor')} "
              f"-> {hand.get('Premium')}  msgs {len(hand.get('messages', []))}"
              + ("" if good else f"   DIFF {diffs} missing {mdiff} extra {extra}"))
        check(good, f"loss assessment {label} ({cause if not ptype else 'SPP'}): hand = engine")
    check(ok_n == len(cases), f"{len(cases)} loss assessment cases, hand = engine on all ({ok_n})")


# ------------------------------------------------------------------ C21-05

import csv                                                                 # noqa: E402
import xml.etree.ElementTree as ET                                         # noqa: E402

CHUNK_FILES = re.compile(r"DischargeFromSewer|CondominiumCommercialUnitOwnersOptional|"
                         r"ChangesCommercialUnitsInResidentialCondo")
CHUNK_TABLES = re.compile(r"Sewer|DischargeFrom|LossAssess|MiscRealProp|CondominiumCommercialUnit|"
                          r"CommercialUnitsInResidential", re.I)
CODE_TARGET = re.compile(r"(Code|Converted|Indicator)$|^Subline")
#: lookups a rule guards so a key value never reaches them: (table, key value) -> the guard
GUARDED = {("LossAssessmentLimitConverted", "Over 10,000"): "SetLossAssessmentLimitConverted skips 'Over 10,000'"}


def prices(targets):
    return any(not CODE_TARGET.search(x.rsplit("/", 1)[-1]) for x in targets)


def ln(tag):
    return tag.rsplit("}", 1)[-1]


def key_cols(pkg, table):
    """Positional key columns; a Range is ONE key position spanning two columns."""
    f = pkg / "Rate Tables" / f"{table}Def.RateTableDef.xml"
    if not f.exists():
        return None
    kc = next(e for e in ET.fromstring(f.read_text(encoding="utf-8-sig")) if ln(e.tag) == "KeyCols")
    return [("range", [k.attrib["Name"] for k in e]) if ln(e.tag) == "Range" else ("col", e.attrib["Name"])
            for e in kc]


def table_csv(pkg, table):
    f = pkg / "Rate Tables" / f"{table}.RateTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def lookups(pkg):
    """(file, rule, table, [key spec], callers' literal args, targets) for every Lookup in the chunk's files."""
    out, calls = [], collections.defaultdict(lambda: collections.defaultdict(set))
    targets = collections.defaultdict(set)
    rd = pkg / "Rules"
    files = [f for f in rd.glob("*.xml") if CHUNK_FILES.search(f.name)] if rd.exists() else []
    for f in files:
        root = ET.fromstring(f.read_text(encoding="utf-8-sig"))
        for rule in root:
            if ln(rule.tag) != "Rule":
                continue
            for rr in rule.iter():
                if ln(rr.tag) == "RunRule" and rr.attrib.get("Rule", "").startswith("Lookup"):
                    key = (rr.attrib.get("FileName") or f.name[:-len(".Rule.xml")], rr.attrib["Rule"])
                    if rr.attrib.get("ToDataDef"):
                        targets[key].add(rr.attrib["ToDataDef"])
                    for a in rr:
                        if ln(a.tag) == "Arg":
                            for c in a:
                                if ln(c.tag) == "Constant":
                                    calls[key][a.attrib["Param"]].add(c.text or "")
            for lk in rule.iter():
                if ln(lk.tag) != "Lookup":
                    continue
                keys = next(e for e in lk if ln(e.tag) == "Keys")
                spec = []
                for k in keys:
                    t = ln(k.tag)
                    if t == "Constant":
                        spec.append(("lit", k.text or ""))
                    elif k.attrib.get("FromParam"):
                        spec.append(("param", k.attrib["FromParam"]))
                    else:
                        spec.append(("field", k.attrib.get("FromDataDef", "?")))
                out.append((f.name[:-len(".Rule.xml")], rule.attrib["Name"], lk.attrib["MatrixFromConstant"], spec))
    return out, calls, targets


def domain_values(pkg, field):
    f = pkg / "Domain Tables" / f"Domain{field}.DomainTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return [r["DataValue"] for r in csv.DictReader(h) if r.get("StateCode") in ("CW", None)]


def tables_and_literals():
    progress("C21-05  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC21-05  TABLES AND LITERALS\n" + "-" * 90)
    pkgs = {"CW": CW}
    for j in s18.STATES:
        st = book_for(j, ASOF).state
        if st is not None:
            pkgs[j] = st.package.content
    used = {}
    bad = []
    for who, pkg in pkgs.items():
        lks, calls, targets = lookups(pkg)
        for fname, rule, table, spec in lks:
            if table == "Pages":                              # the form-name lookup (Form Pages), not a rate table
                continue
            used.setdefault(table, set()).update(targets.get((fname, rule), set()))
            cols = key_cols(pkg, table) or key_cols(CW, table)
            rows = [x for p in {pkg, CW} for x in (table_csv(p, table) or [])]
            if cols is None:
                bad.append(f"{who} {rule}: table {table} has no definition")
                continue
            if len(cols) != len(spec):
                bad.append(f"{who} {rule}: {table} {len(spec)} keys vs {len(cols)} key columns")
                continue
            for (kind, v), (ck, cname) in zip(spec, cols):
                if ck == "range":
                    continue
                have = {x[cname] for x in rows}
                if kind == "lit":
                    lits = {v}
                elif kind == "param":
                    lits = calls.get((fname, rule), {}).get(v, set())
                else:
                    field = v.rsplit("/", 1)[-1]
                    if cname == "StateCode":
                        continue
                    dom = domain_values(pkg, field) or domain_values(CW, field)
                    lits = {d for d in (dom or []) if d not in ("0",) or "0" in have}
                    if dom:
                        miss = sorted(x for x in lits - have if (table, x) not in GUARDED)
                        if not miss and lits - have:
                            miss_note = [GUARDED[(table, x)] for x in lits - have]
                            print(f"    {who:3s} {table[:44]:44s} {cname:26s} dropdown {field}: unkeyed but guarded: {miss_note}")
                            continue
                        print(f"    {who:3s} {table[:44]:44s} {cname:26s} dropdown {field}: {len(dom)} values"
                              + (f", NOT KEYED: {miss}" if miss else ", all keyed"))
                    continue
                miss = sorted(lits - have) if cname != "StateCode" else []
                if miss:
                    bad.append(f"{who} {rule}: {table}.{cname} has no row for {miss}")
    # every table the chunk touches, and every state package that files one under a chunk-like name
    print("\n  tables (CW rows; states filing their own):")
    names = set(used)
    for who, pkg in pkgs.items():
        rt = pkg / "Rate Tables"
        if rt.exists():
            names |= {f.name[:-len(".RateTable.csv")] for f in rt.glob("*.RateTable.csv") if CHUNK_TABLES.search(f.name)}
    for t in sorted(names):
        cw_rows = table_csv(CW, t)
        filers = [f"{who}({len(table_csv(p, t))})" for who, p in pkgs.items()
                  if who != "CW" and table_csv(p, t) is not None]
        role = ("prices" if prices(used.get(t, set())) else
                ("codes" if used.get(t) else "not looked up by this chunk"))
        print(f"    {t[:58]:58s} CW {len(cw_rows) if cw_rows is not None else '-':>4} rows  {role:30s} "
              f"{' '.join(filers)[:120]}")
    sewer = sorted(t for t in names if re.search("Sewer|DischargeFrom", t) and table_csv(CW, t) is not None)
    priced = [t for t in sewer if prices(used.get(t, set()))]
    print(f"\n  Sewer's CW tables: {len(sewer)}; price: {priced}; the rest only set codes")
    for b in sorted(set(bad)):
        print(f"    PROBLEM {b}")
    empty = sorted(t for t in names if table_csv(FLPKG, t) == [] and table_csv(CW, t))
    print(f"\n  FL files EMPTY copies of {len(empty)} tables the CW base fills: {empty}")
    print("  the engine falls back to CW for an empty state table; ISO refused on VT's empty EQ stub -> live probe (C21-06)")
    check(len(empty) == 7, f"FL's empty stubs: 6 sewer tables + the sub-limit rate ({len(empty)})")
    check(not bad, f"every literal and caller-passed key has a row in its table ({len(bad)} problems)")
    check(len(sewer) == 6 and priced == ["DischargeFromSewerDrainOrSump"],
          f"Sewer: 6 CW tables, one prices ({len(sewer)}, {priced})")


def every_state():
    """All seven CW premium records on one policy per state, engine only: which states leave one unpriced."""
    progress("C21-05  EVERY STATE ON THE ENGINE")
    print("\n  every in-force state, all seven CW premium records attached at once (engine only):")
    unpriced, raised = {}, {}
    states = [j for j in s18.STATES]
    for i, j in enumerate(states, 1):
        sub = portable(j)
        for rec, lim in SEWER.items():
            r2.put(sub, rec, {lim: "25000"}, state=j)
        rc1.node_dicts(sub)[P + "PersonalProperty"][P + OPT + "Table"] = {P + OPT: [{
            "LossAssessmentLimit": "10,000", "LossAssessmentDeductible": "250", "MiscRealPropLimit": "20000",
            P + LA: {}, P + MRP: {}}]}
        data, ip, err = rated(sub, j)
        if err:
            raised[j] = err
            print(f"    [{i}/{len(states)}] {j} RAISED {err}")
            continue
        got = {}
        for rec in list(SEWER) + [LA, MRP]:
            ps = premiums(data, rec)
            got[short(rec)[-22:]] = ps[0] if ps else "MISSING"
        miss = {k: v for k, v in got.items() if v in (None, "MISSING", "0")}
        if miss:
            unpriced[j] = miss
        print(f"    [{i}/{len(states)}] {j} " + " ".join(f"{v}" for v in got.values())
              + (f"   UNPRICED {sorted(miss)}" if miss else ""))
    print(f"  states leaving a record unpriced: {sorted(unpriced)}; raised: {sorted(raised)}")
    return unpriced, raised


def main():
    cw, fl_only = attach_and_switches()
    flips(fl_only)
    borrowed()
    loss_assessment()
    tables_and_literals()
    unpriced, raised = every_state()
    check(not raised, f"no state raises with the seven records attached ({sorted(raised)})")
    check(set(unpriced) == {"FL"}, f"only FL leaves a record unpriced (its parents never call it) ({sorted(unpriced)})")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1 (C21-02..C21-05): ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED: {FAIL}") + f"  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
