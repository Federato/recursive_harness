#!/usr/bin/env python3
"""Chunk 17, RC-3 (C17-12 to C17-15): zero cases, messages, shared names, exclusion records.

Every case is one of RC-2's policies (181_) with one thing changed. Each record's
expected premium is predicted before the run: $0 where a rule forces it, otherwise a
hand evaluation of the filed rule with the family's own factor from its table (175_'s
method). Message cases name the message that must appear (or must not); --live compares
every premium field for field and the WHOLE message set with ISO's.

C17-12  ZERO CASES (and the blanks that are NOT zero)
  Z1  payroll 180 days on BI (1.00 -> Factor 0)          -> BI payroll $0; SCBI (90 days) priced
  Z2  payroll days BLANK on BI                           -> NOT zero: FirstValue defaults the key to 0,
                                                            so 0 days' 1.12 (0.12) prices
  Z3  Mining option "None"                               -> rate 0 -> $0
  Z4  Mining option blank                                -> rate defaults 0.0 -> $0
  Z5  Watercraft construction option blank               -> Factor 0.0 -> $0
  Z6  Watercraft option "Not Applicable"                 -> converts to "Not Applicable", no factor row:
                                                            ours $0; ISO REFUSES the policy (first live run,
                                                            2026-09-28), matrix WatercraftExclBuybackFactor: OI-103
  Z7  Off-Premises extended period blank                 -> ExtendedBICovFactor 0.0 -> both $0
  Z7b Off-Premises extended period "Not Applicable"      -> factor 1.00 -> priced by hand
  Z8  Off-Premises collision "No"                        -> Collision $0, OTC priced
  Z9  Landlord on BI limit 0                              -> Landlord BGI / BGII / Broad read the
                                                            LANDLORD's limit (priced); EQ reads BI's EQ limit -> $0
  Z10 Power-heat and Landlord with BI earthquake "No Coverage" -> EQ riders $0, the rest priced
  Z11 Power-heat EQ at chunk 10's class A1 (FinalEQRate 0.005) -> round3(0.005 x 0.06) = 0 -> EQ $0
  Z12 Landlord coinsurance blank                         -> type-of-risk 0.0 -> BGI / BGII / EQ $0;
                                                            Broad does not read it (priced)
  Z13 Landlord on a Standard Property Policy             -> Broad / Special $0 (the If in SetPremium)
  Z14 Landlord two keys: BI Special, the landlord's own CauseOfLoss Broad -> Broad ON (priced),
                                                            Special OFF ($0)
C17-13  MESSAGES (each triggered; ISO's full message set must equal ours)
  M1  BI + SCBI "Extra Expense Only" + Ordinary Payroll   -> CP 15 10 ... Extra Expense (BI and SCBI texts)
  M2  BI + SCBI "Extra Expense Only" + Power-heat         -> CP 15 11 ... Extra Expense
  M3  BI + SCBI "No Coinsurance" + Ordinary Payroll       -> Minimum 50% Coinsurance required with CP 15 10
  M4  BI + SCBI "No Coinsurance" + Power-heat             -> ... with CP 15 11
  M5  Off-Premises on BI and SCBI, cause Basic            -> CP 15 06 is not valid with selected Cause of Loss
  M5s the same on cause Special                           -> silent
  M6  Waterfront "Yes" on cause Broad (BI and SCBI)       -> Waterfront Coverage is not Valid ... (found by
                                                            form search: the census's record-name search missed it)
  M7  Waterfront "Yes" + CP 10 35 (BI and SCBI)           -> CP 10 35 is not Valid with the Selected Coverage
  M8  FL, Off-Premises, building class 0311 (residential) -> CP 15 06 ... Residential Class Code
  M8s FL, building class 0951                              -> silent
C17-14  SHARED NAMES: who writes Factor, BaseFactor, LimitToUse, TypeOfRiskFactor, the base rates,
        the Off-Premises factors and CoverageOnPolicyIndicator on the families' records (CW + 46),
        and which writes are IsNull-guarded. Probes:
  S1  Ordinary Payroll Factor 0.5 SUBMITTED on BI       -> guarded: 0.5 is used
  S2  Ordinary Payroll BaseFactor 1.3 SUBMITTED on BI   -> Factor = 0.3
C17-15  EXCLUSION RECORDS
  X0  L1 at a landlord limit of 1,000,000 (control)
  X1  X0 + cyber-incident exclusion                     -> BGI / BGII / Broad x 0.995; EQ x 1.00
  X2  O1 + cyber-incident exclusion                     -> Off-Premises has NO cyber factor: unchanged
  X3  O1 + windstorm-or-hail exclusion on BI            -> OTC x 1.01 (EQ) x 0.95; Collision unchanged

    python scripts/cf/182_chunk17_rc3.py [--live] [--cases Z1,M5]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import book_for
import functools                                               # noqa: E402
# book_for re-discovers the whole ERC corpus (~1.8 s) on every call and this script calls it per
# state and family; the packages do not change within a run (profiled 2026-09-28, see 183_)
book_for = functools.lru_cache(maxsize=None)(book_for)
from gl_engine.interp.values import InterpretError
import _iso_refusals as _iso                                    # noqa: E402

g = import_module("181_chunk17_rc2")
si = import_module("_state_inputs")                       # C28-17: a state's own Group II territory
r3 = import_module("176_chunk16_rc3")
r2, gc, rc1, rep, cmp, r16, r11 = g.r2, g.gc, g.rc1, g.rep, g.cmp, g.r16, g.r11
r11.NUMERIC |= {"Factor", "BaseFactor"}          # S1 / S2 submit factors: ISO types them as decimals
P = g.P
ZERO = r3.ZERO
mod, setp, setc, chain = r3.mod, r3.setp, r3.setc, r3.chain
CYBER = {f"CyberIncidentExclusionFactor{k}": r2.row("CyberIncidentExclusionFactors", "Factor", StateCode="CW",
                                                    CausesOfLossOrPerilGroupPremium=n)
         for k, n in (("BGI", "Basic Group I"), ("BGII", "Basic Group II"), ("Broad", "Broad"),
                      ("Special", "Special"), ("EQ", "Earthquake"))}
FL_SC = "Cooling Towers - Metal"               # FL files no "Towers - Broadcasting Antennas" (C15-16)
FAIL = []
#: a "must" entry naming the table ISO is predicted to REFUSE on (OI-103: ours prices, ISO refuses)
REFUSE = "REFUSE:"

LL, LL_SC, PAY, PAY_SC, PHR, PHR_SC = g.LL, g.LL_SC, g.PAY, g.PAY_SC, g.PHR, g.PHR_SC
MIN, MIN_SC, WC, WC_SC, OP, OP_SC = g.MIN, g.MIN_SC, g.WC, g.WC_SC, g.OP, g.OP_SC
L = lambda n, f: f"{n}{f}Coverage"
PAYBI = [L(PAY, f) for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
PAYSC = [L(PAY_SC, f) for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
MIN4 = [L(n, f) for n in (MIN, MIN_SC) for f in ("BasicGroupI", "BasicGroupII")]
OPBI = [f"{OP}DetailCollision", f"{OP}DetailOTC"]
OPSC = [f"{OP_SC}DetailCollision", f"{OP_SC}DetailOTC"]


# ---------------------------------------------------------- RC-2's predictions

def rc2_recs(cid):
    return g.cases()[cid][4]


def ov(cid, rec, **extra):
    d = dict(rc2_recs(cid)[rec])
    d.update(extra)
    return d


def ll_bi(parent="BusinessIncome", name=LL):
    return name


def watercraft(**bi):
    def fn(sub):
        a = g.at(sub)
        a[P + "BusinessIncome"].update(bi)
        sc = {("WaterFrontProperty" if k == "WaterfrontProperty" else k): v for k, v in bi.items()}
        a[P + "SpecialClassBusnIncome"].update(sc)
        for k in ("BusinessIncome", "SpecialClassBusnIncome"):
            for f in [f for f, v in bi.items() if v is None]:
                a[P + k].pop(f, None)
                a[P + k].pop("WaterFrontProperty" if f == "WaterfrontProperty" else f, None)
    return fn


def op_container(sub, parent, name, **kw):
    r2.container(sub, parent, name).update(kw)


def fl_offprem(class_code):
    def build():
        # chunk 16's FL policy (177_): no earthquake election -- FL's building-height EQ table
        # has no row for 175_'s EQ inputs and ISO refuses (BldgHeightFactor CW, 1-3, A1, 1)
        sub = r2.grp.five()
        a = g.at(sub)
        a[P].update(r2.rc2.POLICY)
        a[P + "Structure"]["MultiPremiumAndDispersionCreditFactor"] = r2.rc2.BUILDING_CREDIT
        a[P + "Structure"].setdefault("WindstormOrHailDeductible", "1,000")
        a[P]["State"] = "FL"
        loc = a[P + "Location"]
        loc.pop("BasicGroupIRatingTerr", None)
        loc.pop("BasicGroupIIRatingTerr", None)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc.update(r2.s18.STATE_LOC.get("FL", {}))
        si.localize_group2(sub, "FL")
        a[P + "SpecialClass"]["ClassDescription"] = FL_SC
        a[P + "Structure"]["ClassCode"] = class_code
        a[P + "BusinessIncome"]["CauseOfLoss"] = "Special"
        for f in ("Collision", "OTC"):
            r2.put(sub, f"{OP}Detail{f}", state="FL")
        r2.container(sub, "BusinessIncome", OP).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "150"})
        d = r2.container(sub, "BusinessIncome", OP)[P + OP + "DetailTable"][P + OP + "Detail"][0]
        d.update({"Limit": "37500", "Option": "Option A"})
        return sub
    return build


def l_two_keys():
    sub, a = g.landlord("BusinessIncome", "Special", ("BasicGroupI", "Broad", "Special"),
                        {"Limit": "60000", "Coinsurance": "80%"})
    a[P + "BusinessIncome"]["SpecialIncludingTheftTypeRisk"] = g.OTHER
    r2.container(sub, "BusinessIncome", LL)["CauseOfLoss"] = "Broad"
    return sub


def submit(**kw):
    def fn(sub):
        r2.container(sub, "BusinessIncome", PAY).update(kw)
    return fn


def h1_low_eq():
    """H1 without eq_high: chunk 10's class A1 / 10% deductible, BI limits 100,000."""
    sub = r2.base()
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        r2.put(sub, f"{PHR}{f}Coverage")
        r2.put(sub, f"{PHR_SC}{f}Coverage")
    return sub


def both(**kw):
    return chain(setp("BusinessIncome", **kw), setp("SpecialClassBusnIncome", **kw))


# id -> (task, label, state, build, {record: expectation}, [must], [must not])
def cases():
    pay_bi0 = {r: {"../Factor": g.payroll(0)} for r in PAYBI}
    pay_sc90 = {r: {"../Factor": g.payroll(90)} for r in PAYSC}
    o1 = rc2_recs("O1")
    phr_eq = [L(PHR, "Earthquake"), L(PHR_SC, "Earthquake")]
    phr_rest = [L(n, f) for n in (PHR, PHR_SC) for f in ("BasicGroupI", "BasicGroupII")]
    l1 = rc2_recs("L1")
    big = setc("BusinessIncome", LL, Limit="1000000")
    return {
        "Z1": ("C17-12", "payroll 180 days on BI", "OR", mod(g.p1, setc("BusinessIncome", PAY, NumOfDays="180")),
               {**dict.fromkeys(PAYBI, ZERO), **pay_sc90}, [], []),
        "Z2": ("C17-12", "payroll days blank on BI (defaults to 0 days: priced)", "OR",
               mod(g.p1, lambda sub: r2.container(sub, "BusinessIncome", PAY).pop("NumOfDays")),
               {**pay_bi0, **pay_sc90}, [], []),
        "Z3": ("C17-12", "Mining option None", "OR",
               mod(g.m1, chain(setc("BusinessIncome", MIN, MiningCoverageOption="None"),
                               setc("SpecialClassBusnIncome", MIN_SC, MiningCoverageOption="None"))),
               dict.fromkeys(MIN4, ZERO), [], []),
        "Z4": ("C17-12", "Mining option blank", "OR",
               mod(g.m1, chain(setc("BusinessIncome", MIN, MiningCoverageOption=""),
                               setc("SpecialClassBusnIncome", MIN_SC, MiningCoverageOption=""))),
               dict.fromkeys(MIN4, ZERO), [], []),
        "Z5": ("C17-12", "Watercraft construction option blank", "OR",
               mod(g.w1, watercraft(WatercraftExclBuybackConstrctnOption=None)), {WC: ZERO, WC_SC: ZERO}, [], []),
        "Z6": ("C17-12", "Watercraft option 'Not Applicable' (no factor row)", "OR",
               mod(g.w1, watercraft(WatercraftExclBuybackConstrctnOption="Not Applicable")), {WC: ZERO, WC_SC: ZERO},
               [REFUSE + "WatercraftExclBuybackFactor"], []),
        "Z7": ("C17-12", "Off-Premises extended period blank", "OR", mod(g.o1, setc("BusinessIncome", OP, ExtendedPeriod="")),
               dict.fromkeys(OPBI, ZERO), [], []),
        "Z7b": ("C17-12", "Off-Premises extended period 'Not Applicable' (1.00)", "OR",
                mod(g.o1, setc("BusinessIncome", OP, ExtendedPeriod="Not Applicable")),
                {r: dict(o1[r], **{"../../../ExtendedBICovFactor": Decimal("1")}) for r in OPBI}, [], []),
        "Z8": ("C17-12", "Off-Premises collision 'No'", "OR", mod(g.o1, setc("BusinessIncome", OP, CollisionCovCOL="No")),
               {OPBI[0]: ZERO, OPBI[1]: o1[OPBI[1]]}, [], []),
        "Z9": ("C17-12", "Landlord on BI limit 0 (landlord limit 60,000)", "OR",
               mod(g.l1, setp("BusinessIncome", Limit="0")),
               {**{r: l1[r] for r in list(l1)[:3]}, L(LL, "Earthquake"): ZERO}, [], []),
        "Z10": ("C17-12", "Power-heat and Landlord with BI earthquake 'No Coverage'", "OR",
                mod(g.h1, chain(both(EQCovIndicator="No Coverage"),
                                lambda sub: [r2.put(sub, L(LL, f)) for f in ("BasicGroupI", "Earthquake")],
                                setc("BusinessIncome", LL, Limit="60000", Coinsurance="80%", CauseOfLoss="Basic"))),
                {**dict.fromkeys(phr_eq, ZERO), **{r: {"../Factor": g.PHR_F} for r in phr_rest},
                 L(LL, "BasicGroupI"): {"../TypeOfRiskFactor": g.trf("80%")}, L(LL, "Earthquake"): ZERO}, [], []),
        "Z11": ("C17-12", "Power-heat EQ at class A1 (rounds to $0)", "OR", h1_low_eq,
                {**dict.fromkeys(phr_eq, ZERO), **{r: {"../Factor": g.PHR_F} for r in phr_rest}}, [], []),
        "Z12": ("C17-12", "Landlord coinsurance blank", "OR", mod(g.l1, setc("BusinessIncome", LL, Coinsurance="")),
                {L(LL, "BasicGroupI"): ZERO, L(LL, "BasicGroupII"): ZERO, L(LL, "Earthquake"): ZERO,
                 L(LL, "Broad"): l1[L(LL, "Broad")]}, [], []),
        "Z13": ("C17-12", "Landlord Broad on a Standard Property Policy", "OR",
                mod(g.l1, setp("", PolicyType="Standard Property Policy")), {L(LL, "Broad"): ZERO}, [], []),
        "Z14": ("C17-12", "Landlord two keys: BI Special, landlord's own cause Broad", "OR", l_two_keys,
                {L(LL, "BasicGroupI"): {"../TypeOfRiskFactor": g.trf("80%")},
                 L(LL, "Broad"): {"../BroadBaseRate": g.broad_rate("Frame")}, L(LL, "Special"): ZERO}, [], []),
        "M1": ("C17-13", "Extra Expense Only + Ordinary Payroll (BI, SCBI)", "OR", mod(g.p1, both(CovType="Extra Expense Only")),
               {}, ["CP 15 10 is not valid with Extra Expense Coverage Form (CP 00 50)",
                    "CP 15 10 not valid with Extra Expense Coverage Form (CP 00 50)"], []),
        "M2": ("C17-13", "Extra Expense Only + Power-heat (BI, SCBI)", "OR", mod(g.h1, both(CovType="Extra Expense Only")),
               {}, ["CP 15 11 is not valid with Extra Expense Coverage Form (CP 00 50)",
                    "CP 15 11 not valid with Extra Expense Coverage Form (CP 00 50)"], []),
        "M3": ("C17-13", "No Coinsurance + Ordinary Payroll (BI, SCBI)", "OR", mod(g.p1, both(Coinsurance="No Coinsurance")),
               {}, ["Minimum 50% Coinsurance required with CP 15 10"], []),
        "M4": ("C17-13", "No Coinsurance + Power-heat (BI, SCBI)", "OR", mod(g.h1, both(Coinsurance="No Coinsurance")),
               {}, ["Minimum 50% Coinsurance required with CP 15 11"], []),
        "M5": ("C17-13", "Off-Premises on BI and SCBI, cause Basic", "OR",
               mod(g.o1, lambda sub: [r2.put(sub, f"{OP_SC}Detail{f}") for f in ("Collision", "OTC")]),
               {}, ["CP 15 06 is not valid with selected Cause of Loss"], []),
        "M5s": ("C17-13", "Off-Premises on BI and SCBI, cause Special", "OR",
                mod(g.o1, chain(lambda sub: [r2.put(sub, f"{OP_SC}Detail{f}") for f in ("Collision", "OTC")],
                                both(CauseOfLoss="Special"))),
                {}, [], ["CP 15 06 is not valid with selected Cause of Loss"]),
        "M6": ("C17-13", "Waterfront Yes on cause Broad (BI, SCBI)", "OR", mod(g.w1, both(CauseOfLoss="Broad")),
               {WC: ZERO, WC_SC: ZERO}, ["Waterfront Coverage is not Valid with the Selected Cause of Loss"], []),
        "M7": ("C17-13", "Waterfront Yes + CP 10 35 (BI, SCBI)", "OR",
               mod(g.w1, lambda sub: [g.at(sub)[P + k].__setitem__(P + x + "Table", {P + x: [{}]}) for k, x in
                                      (("BusinessIncome", "WatercraftExclusionBusnIncome"),
                                       ("SpecialClassBusnIncome", "WatercraftExclusionSpclClassBusnIncome"))]),
               {WC: ZERO, WC_SC: ZERO}, ["CP 10 35 is not Valid with the Selected Coverage"], []),
        "M8": ("C17-13", "FL Off-Premises on a residential building class (0311)", "FL", fl_offprem("0311"),
               {}, ["CP 15 06 is not valid with selected Residential Class Code"], []),
        "M8s": ("C17-13", "FL Off-Premises on building class 0951", "FL", fl_offprem("0951"),
                {}, [], ["CP 15 06 is not valid with selected Residential Class Code"]),
        "S1": ("C17-14", "Ordinary Payroll Factor 0.5 submitted on BI", "OR", mod(g.p1, submit(Factor="0.5")),
               {**{r: {"../Factor": Decimal("0.5")} for r in PAYBI}, **pay_sc90}, [], []),
        "S2": ("C17-14", "Ordinary Payroll BaseFactor 1.3 submitted on BI", "OR", mod(g.p1, submit(BaseFactor="1.3")),
               {**{r: {"../Factor": Decimal("0.3")} for r in PAYBI}, **pay_sc90}, [], []),
        "X0": ("C17-15", "L1 at landlord limit 1,000,000 (control)", "OR", mod(g.l1, big), l1, [], []),
        "X1": ("C17-15", "L1 at 1,000,000 + cyber-incident exclusion", "OR", mod(g.l1, chain(big, r3.cyber)),
               {r: dict(v, **CYBER) for r, v in l1.items()}, [], []),
        "X2": ("C17-15", "O1 + cyber-incident exclusion (Off-Premises reads none)", "OR", mod(g.o1, r3.cyber), o1, [], []),
        "X3": ("C17-15", "O1 + windstorm-or-hail exclusion on BI", "OR",
               mod(g.o1, lambda sub: g.at(sub)[P + "BusinessIncome"].__setitem__(
                   P + "WindstormOrHailExclusionBusnIncomeTable", {P + "WindstormOrHailExclusionBusnIncome": [{}]})),
               {OPBI[0]: o1[OPBI[0]],
                OPBI[1]: dict(o1[OPBI[1]], **{"../../../WindHailExclFactor": g.op_f(
                    "OffPremEndtsModifyingCovdCOLFactor", "Endorsement", "Windstorm Or Hail Exclusion")})}, [], []),
    }


# ------------------------------------------------------------ C17-14 names

def shared_names():
    print("\n" + "=" * 90 + "\nC17-14  SHARED NAMES (CW + 46 in-force states)\n" + "-" * 90)
    cw = book_for("OR", r2.ASOF).parent.package.content
    pat = re.compile("|".join(p for _, p in r16.cen.FAMILIES).replace("OrdinaryPayroll", "OrdinaryPayroll"))
    fams = import_module("179_chunk17_census").FAMILIES
    pat = re.compile("|".join(p for _, p in fams))
    pkgs = {"CW": cw, **{j: book_for(j, r2.ASOF).state.package.content for j in r2.s18.STATES}}
    fields = ("Factor", "BaseFactor", "LimitToUse", "Limit", "TypeOfRiskFactor", "BroadBaseRate", "SpecialBaseRate",
              "BasicGroupIRate", "BasicGroupIIRate", "ExtendedBICovFactor", "BusnIncCovWaitingPeriodFactor",
              "InsToExposureFactor", "WindHailExclFactor", "EQCovFactor", "FloodCovFactor", "LossCostOTC",
              "LossCostCollision", "CoverageOnPolicyIndicator", "Premium")
    writers = collections.defaultdict(set)
    guarded = collections.defaultdict(set)
    for j, pk in pkgs.items():
        rd = pk / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            if not pat.search(f.name):
                continue
            s = f.read_text(encoding="utf-8-sig", errors="replace")
            for m in re.finditer(r'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', s, re.S):
                name, grp_, body = m.groups()
                for fld in fields:
                    if re.search(rf'ToDataDef="{fld}"', body):
                        writers[fld].add(f"{name}{'' if j == 'CW' else '@' + j}")
                        if re.search(rf'IsNull>\s*<rul:Value[^>]*FromDataDef="{fld}"', body):
                            guarded[fld].add(name)
    for fld in fields:
        w = sorted(writers[fld])
        print(f"  {fld:30s} written by {len(w)} rule(s): {', '.join(w[:6])}{' ...' if len(w) > 6 else ''}"
              if w else f"  {fld:30s} written by no rule: an input")
        if guarded[fld]:
            print(f"  {'':30s} IsNull-guarded (a submitted value survives): {', '.join(sorted(guarded[fld])[:6])}")


# ---------------------------------------------------------------- run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for cid, (task, label, state, build, recs, must, mustnot) in cs.items():
        try:
            data, ip = gc.run(build(), state)
        except InterpretError as exc:
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                continue
            print(f"{cid:4s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, o in recs.items():
            res, checks = r3.expect(data, rec, o, state)
            fac_bad = [(f, e, v) for f, e, v in checks if not r2.same(e, v)]
            if o.get("__zero__"):
                ok = all(r3.zeroish(e) for _, e in res)
                preds[cid][rec] = "ZERO"
            else:
                ok = bool(res) and all(not str(h).startswith("hand error") and r2.same(h, e) and not r3.zeroish(e)
                                       for h, e in res) and not fac_bad
                preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:72]:72s} predicted "
                         f"{'$0' if o.get('__zero__') else [str(h) for h, _ in res]} engine {[e for _, e in res]}"
                         + (f"  factor {fac_bad[:2]}" if fac_bad else ""))
            if not ok:
                bad.append(rec)
        msgs = set(ip.messages)
        refuse = [m[len(REFUSE):] for m in must if m.startswith(REFUSE)]
        must = [m for m in must if not m.startswith(REFUSE)]
        mb = [m for m in must if not any(m in x for x in msgs)] + [f"not: {m}" for m in mustnot if any(m in x for x in msgs)]
        print(f"{cid:4s} {task} {label}: engine {'as derived' if not bad and not mb else 'DIFFERS'}"
              + (f"; messages as predicted: {must}" if must and not mb else "")
              + (f"; silent as predicted" if mustnot and not mb else "")
              + "".join(f"\n      message {m}" for m in mb))
        if lines:
            print("\n".join(lines))
        if bad or mb:
            FAIL.append(cid)
    if not a.cases:
        shared_names()

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, the whole message set):")
        for cid, (task, label, state, build, recs, must, mustnot) in cs.items():
            req = r11.payload(build())
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = state
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=state)
            (gc.OUT / f"chunk17_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                refuse = [x[len(REFUSE):] for x in must if x.startswith(REFUSE)]
                expected = bool(refuse) and m is not None and m.group(1) in refuse
                print(f"  {cid:4s} ISO REFUSES {m.group(0)[:220] if m else str(exc.body)[:220]}"
                      + ("  -- as predicted (OI-103: our engine prices, ISO refuses)" if expected else ""))
                if not expected:
                    FAIL.append(f"{cid} live")
                continue
            if any(x.startswith(REFUSE) for x in must):
                print(f"  {cid:4s} DIFFER: predicted an ISO refusal, ISO priced")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk17_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.get(cid, {}).items():
                iso = r2.iso_of(resp, rec)
                if want == "ZERO":
                    if not all(r3.zeroish(x) for x in iso):
                        pbad.append((rec, iso, "$0"))
                elif sorted(Decimal(str(x)) for x in iso if not r3.zeroish(x)) != sorted(w for w in want if not r3.zeroish(w)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = [m for m in must if not any(m in x for x in mi)] + [m for m in mustnot if any(m in x for x in mi)]
            ok = not pbad and not d and mi == mo and not mb
            print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds.get(cid, {})) - len(pbad)} of "
                  f"{len(preds.get(cid, {}))} records; {len(ipr) - len(d)} of {len(ipr)} premiums; messages "
                  f"{'equal' if mi == mo else 'DIFFER'}"
                  + ("; ISO raises the predicted message" if must and not mb else "")
                  + ("; ISO silent as predicted" if mustnot and not mb else "")
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    print(f"\nRC-3: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
