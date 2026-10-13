#!/usr/bin/env python3
"""Chunk 16, RC-3 (C16-13 to C16-16): zero cases, messages, shared names, exclusion records.

Every case is one of RC-2's policies (175_) with one thing changed. Each record's
expected premium is predicted before the run: $0 where a rule forces it, otherwise a
hand evaluation of the filed rule with the family's own factor from its table (175_'s
method). Messages: each case names the message it must raise (or must not); --live
compares every premium field for field and the WHOLE message set with ISO's.

C16-13  ZERO CASES
  Z1  EPI "Not Applicable"               -> the four EPI forms $0 (switch off)
  Z2  EPI blank                           -> $0
  Z3  no waiting period, time period blank (BI side) -> BaseFactor defaults, Factor 0 -> BI forms $0;
                                             the Special Class BI side unchanged
  Z4  Civil Authority period blank        -> the rate forms $0; Radius (manual) still $1,013
  Z5  Business Income limit 0             -> every EPI form $0 (LimitToUse 0)
  Z6  EPI with Business Income earthquake "No Coverage" -> EPI EQ $0, the other three priced
  Z7  Pollutant Clean Up limit 10,000     -> (Limit - 10,000) = 0 -> every form $0
  Z8  Pollutant Clean Up limit 5,000      -> (Limit - 10,000) < 0 -> NEGATIVE premiums, by hand
  Z9  Pollutant Clean Up deductible blank -> DeductibleFactor 0.0 -> $0
  Z10 Spoilage description blank          -> no class, no rate -> $0
  Z11 Spoilage selling price "No"         -> factor 1.0 -> by hand
  Z12 Mine Subsidence IL "No Coverage"    -> $0
C16-14  MESSAGES (each triggered; ISO's full message set must equal ours)
  M1  Business Income "Extra Expense Only" + no waiting period -> CP 15 56
  M2a Pollutant Clean Up where NOTHING at the location qualifies -> CP 04 07 ... underlying Coverage
      (the rule clears it if any building, contents row or special class carries real coverage:
      the first version of this case kept a contents row and a special class, and was silent)
  M2b Pollutant Clean Up on a location with no building and no special class -> CP 04 07 needs ...
  M3  Spoilage limit 0                                          -> CP 04 40 Limit is required
  M4  Standard Property Policy + Spoilage                       -> CP 04 40 ... Standard Property Policy
  M5  every coverage on the Special cause + Molten Material ×5  -> CP 10 60 ×5, Molten by hand (Else branch)
  M6  Molten Material on a "No Coverage" building               -> CP 10 60 requires ... building coverage
  M7  building deductible "Not Applicable" + Molten Material    -> Deductible cannot be Not Applicable ...
  M8  IL scheduled buildings, no building limit                 -> ... There Must be One Limit Entered ...
  M9  IL scheduled buildings, every building scheduled          -> IL 09 03 ... not valid if all buildings ...
  M10 IL building limit 200,000 over a 100,000 building          -> ... cannot be greater than property limit
  M11 IN all buildings, County "Clay" (eligible) / "Marion" (not) -> County is not Eligible ... only on Marion
  M12 IL + Mortgageholders E&O (CP 00 70)                        -> Mine Subsidence not valid with CP 00 70
      (first live run: the E&O record carried no Limit, its rate lookup found no row, and ISO REFUSED
      the policy in IL and WV while our engine priced it: an OI-103 case. The record now carries a
      filed per-mortgage limit, 25,000. M12w asks the same question in WV, on CW 2026)
  M13 OK manual premium on a "No Coverage" building              -> Mine Subsidence not valid with selected Coverage
C16-15  SHARED NAMES: who writes Factor, BaseFactor, LimitToUse, Rate, Limit, SellingPriceFactor,
        CoverageOnPolicyIndicator on the families' records (CW + 46 states), and which writes are
        IsNull-guarded (a submitted value would survive). Probe:
  S1  EPI with Factor 2.0 SUBMITTED: the rule only looks the factor up when blank, so the
      prediction is (2.0 - 1) x the rate; ISO decides whether a submission survives
C16-16  EXCLUSION RECORDS: the cyber-incident exclusion is a policy record
  X1  RC-2's G6 + CyberIncidentExclusion -> each peril group's factor 0.995 (its table),
      the four EPI forms re-priced by hand

    python scripts/cf/176_chunk16_rc3.py [--live] [--cases Z1,M5]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import copy
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
from gl_engine.interp.values import InterpretError

r2 = import_module("175_chunk16_rc2")
r16, rc1, gc, rep, cmp, r11 = r2.r16, r2.rc1, r2.gc, r2.rep, r2.cmp, r2.r11
cen = r16.cen
P = "CommercialProperty"
ASOF = r2.ASOF
ZERO = {"__zero__": True}
CYBER = {f"CyberIncidentExclusionFactor{g}": r2.row("CyberIncidentExclusionFactors", "Factor", StateCode="CW",
                                                    CausesOfLossOrPerilGroupPremium=n)
         for g, n in (("BGI", "Basic Group I"), ("BGII", "Basic Group II"), ("Broad", "Broad"), ("Special", "Special"))}
FAIL = []
r11.NUMERIC |= {"Factor"}          # S1 submits a factor: ISO types it as a decimal (a string is refused on type)


def at(sub):
    return rc1.node_dicts(sub)


def mod(build, fn):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


def setp(parent, **kw):
    def fn(sub):
        d = at(sub)[P + parent]
        for k, v in kw.items():
            if v is None:
                d.pop(k, None)
            else:
                d[k] = v
    return fn


def setc(parent, name, **kw):
    def fn(sub):
        c = r2.container(sub, parent, name)
        c.update(kw)
    return fn


def chain(*fns):
    def fn(sub):
        for f in fns:
            f(sub)
    return fn


E = lambda f: f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"
EPI4 = [E(f) for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake")]
NW, NW_SC, CA, PC = r2.NW, r2.NW_SC, r2.CA, r2.PC
NWBI = [f"{NW}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
NWSC = [f"{NW_SC}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Earthquake")]
CAR = [f"{CA}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Special", "Earthquake")]
PC5 = [f"{PC}{f}Coverage" for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake")]
MOLT = ["MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome", "MoltenMaterialSpecialClass",
        "MoltenMaterialSpclClassBusnIncome"]
PC_OV = {f"{PC}BasicGroupICoverage": {"BasicGroupIFactor": r2.POLL_RATE["GroupI"], "HighestPollutantBGIRate": "LAST_BGI"},
         f"{PC}BasicGroupIICoverage": {"BasicGroupIIFactor": r2.POLL_RATE["GroupII"]},
         f"{PC}BroadCoverage": {"BroadRate": r2.POLL_RATE["Broad"]},
         f"{PC}SpecialCoverage": {"SpecialRate": r2.POLL_RATE["Special"]},
         f"{PC}EarthquakeCoverage": {"EQFactor": r2.POLL_RATE["Earthquake"]}}
MS, SMS = r2.MS, r2.SMS


def mortgageholders(sub):
    at(sub)[P][P + "MortgageholdersErrorsAndOmissionsCoverageFormTable"] = {
        P + "MortgageholdersErrorsAndOmissionsCoverageForm": [{"Limit": "25,000"}]}    # a filed per-mortgage limit


def cyber(sub):
    at(sub)[P][P + "CyberIncidentExclusionTable"] = {P + "CyberIncidentExclusion": [{}]}


def all_special(sub):
    for k in ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome"):
        at(sub)[P + k]["CauseOfLoss"] = "Special"


def spoil(**kw):
    def build():
        sub = r2.base()
        f = dict(r2.SPOIL)
        f.update(kw)
        r2.put(sub, "SpoilageCoverage", f)
        return sub
    return build


def il(pol, struct=None, extra=None):
    def build():
        sub = r2.mine("IL", pol, struct=struct, recs=(MS, SMS))()
        if extra:
            extra(sub)
        return sub
    return build


# id -> (task, label, state, build, {record: expectation}, [messages that must appear], [must not])
def cases():
    e270 = {r: {"Factor": r2.EPI_F["270"]} for r in EPI4}
    return {
        "Z1": ("C16-13", "EPI 'Not Applicable'", "OR", mod(r2.g6, setp("BusinessIncome", ExtendedPeriod="Not Applicable")),
               dict.fromkeys(EPI4, ZERO), [], []),
        "Z2": ("C16-13", "EPI blank", "OR", mod(r2.g6, setp("BusinessIncome", ExtendedPeriod=None)),
               dict.fromkeys(EPI4, ZERO), [], []),
        "Z3": ("C16-13", "no waiting period, BI time period blank", "OR",
               mod(r2.g7c, setc("BusinessIncome", NW, TimePeriod="")),
               {**dict.fromkeys(NWBI, ZERO), **{r: {"../Factor": r2.TIME_F["Replaced By 24 Hours"]} for r in NWSC}}, [], []),
        "Z4": ("C16-13", "Civil Authority period blank (Radius manual stays)", "OR",
               mod(r2.g8a, setc("BusinessIncome", CA, IncreasedCoveragePeriod="")),
               {**dict.fromkeys(CAR, ZERO), f"{CA}RadiusCoverage": {}}, [], []),
        "Z5": ("C16-13", "Business Income limit 0", "OR", mod(r2.g6, setp("BusinessIncome", Limit="0")),
               dict.fromkeys(EPI4, ZERO), [], []),
        "Z6": ("C16-13", "EPI with BI earthquake 'No Coverage'", "OR", mod(r2.g6, setp("BusinessIncome", EQCovIndicator="No Coverage")),
               {**{r: e270[r] for r in EPI4[:3]}, EPI4[3]: ZERO}, [], []),
        "Z7": ("C16-13", "Pollutant Clean Up limit 10,000", "OR", mod(r2.g9, setc("Location", PC, Limit="10000")),
               dict.fromkeys(PC5, ZERO), [], []),
        "Z8": ("C16-13", "Pollutant Clean Up limit 5,000 (negative)", "OR", mod(r2.g9, setc("Location", PC, Limit="5000")),
               PC_OV, [], []),
        "Z9": ("C16-13", "Pollutant Clean Up deductible blank", "OR", mod(r2.g9, setc("Location", PC, Deductible="")),
               dict.fromkeys(PC5, ZERO), [], []),
        "Z10": ("C16-13", "Spoilage description blank", "OR", spoil(Description=""), {"SpoilageCoverage": ZERO}, [], []),
        "Z11": ("C16-13", "Spoilage selling price 'No'", "OR", spoil(SellingPrice="No"),
                {"SpoilageCoverage": {"Rate": r2.spoilage_factors("Florists", r2.SPOIL["SpoilageCauseOfLoss"],
                                                                  r2.SPOIL["RefrigerationMaintenanceAgreement"], "No")[1],
                                      "SellingPriceFactor": Decimal("1.0")}}, [], []),
        "Z12": ("C16-13", "Mine Subsidence IL 'No Coverage'", "IL",
                il({"MineSubsidenceCoverage": "No Coverage", "MineSubsidenceLimit": "50000",
                    "MineSubsidenceRatingOption": "Option A3.D.2"}), {MS: ZERO}, [], []),
        "M1": ("C16-14", "BI 'Extra Expense Only' + no waiting period", "OR",
               mod(r2.g7c, setp("BusinessIncome", CovType="Extra Expense Only")), {},
               ["CP 15 56 is not valid with Extra Expense Coverage Form (CP 00 50)"], []),
        "M2a": ("C16-14", "Pollutant Clean Up where nothing qualifies (buildings 'No Coverage', no contents, no special class)", "OR",
                mod(r2.g9, _nothing_qualifies), {}, ["CP 04 07 is not valid with the underlying Coverage selected"], []),
        "M2b": ("C16-14", "Pollutant Clean Up on a location with no building and no special class", "OR",
                mod(r2.g9, _no_buildings), {}, ["CP 04 07 needs a Building or Special class to be valid"], []),
        "M3": ("C16-14", "Spoilage limit 0", "OR", spoil(Limit="0"), {"SpoilageCoverage": ZERO}, ["CP 04 40 Limit is required"], []),
        "M4": ("C16-14", "Standard Property Policy + Spoilage", "OR",
               mod(spoil(), setp("", PolicyType="Standard Property Policy")), {},
               ["CP 04 40 is not valid with the Standard Property Policy"], []),
        "M5": ("C16-14", "every coverage on the Special cause + Molten Material", "OR", mod(r2.g10, all_special),
               {r: {"Factor": r2.MOLTEN_F} for r in MOLT}, ["CP 10 60"], []),
        "M6": ("C16-14", "Molten Material on a 'No Coverage' building", "OR", mod(r2.g10, setp("Structure", CovType="No Coverage")),
               {}, ["CP 10 60 requires some type of building coverage to be valid"], []),
        "M7": ("C16-14", "building deductible 'Not Applicable' + Molten Material", "OR",
               mod(r2.g10, setp("Structure", Deductible="Not Applicable")), {},
               ["Deductible cannot be Not Applicable for the Endorsement Selected"], []),
        "M8": ("C16-14", "IL scheduled buildings, no building limit", "IL",
               il({"MineSubsidenceCoverage": "Scheduled Buildings", "MineSubsidenceRatingOption": "Option A3.D.2"}),
               {}, ["There Must be One Limit Entered"], []),
        "M9": ("C16-14", "IL scheduled buildings, every building scheduled", "IL",
               il({"MineSubsidenceCoverage": "Scheduled Buildings", "MineSubsidenceRatingOption": "Option A3.D.2"},
                  struct={"MineSubsidenceLimit": "50000"}), {}, ["IL 09 03"], []),
        "M10": ("C16-14", "IL building Mine Subsidence limit over the building limit", "IL",
                il({"MineSubsidenceCoverage": "Scheduled Buildings", "MineSubsidenceRatingOption": "Option A3.D.2"},
                   struct={"MineSubsidenceLimit": "200000"}), {}, ["cannot be greater than property limit"], []),
        "M11a": ("C16-14", "IN all buildings, County 'Clay' (eligible)", "IN",
                 r2.mine("IN", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS,), rec_fields={MS: {"ManualPremium": "250"}}),
                 {MS: {"__expect__": {"Premium": Decimal(250)}}}, [], ["County is not Eligible for Mine Subsidence Coverage"]),
        "M11b": ("C16-14", "IN all buildings, County 'Marion' (not eligible)", "IN",
                 mod(r2.mine("IN", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS,), rec_fields={MS: {"ManualPremium": "250"}}),
                     setp("Location", County="Marion")),
                 {MS: {"__expect__": {"Premium": Decimal(250)}}}, ["County is not Eligible for Mine Subsidence Coverage"], []),
        "M12": ("C16-14", "IL + Mortgageholders E&O (CP 00 70)", "IL",
                il({"MineSubsidenceCoverage": "All Buildings", "MineSubsidenceLimit": "50000",
                    "MineSubsidenceRatingOption": "Option A3.D.2"}, extra=mortgageholders), {},
                ["Mine Subsidence not valid with CP 00 70"], []),
        "M12w": ("C16-14", "WV + Mortgageholders E&O (CP 00 70)", "WV",
                 mod(r2.mine("WV", {"MineSubsidenceCoverage": "All Buildings"}, recs=(MS,),
                             rec_fields={MS: {"ManualPremium": "310"}}), mortgageholders), {},
                 ["Mine Subsidence not valid with CP 00 70"], []),
        "M13": ("C16-14", "OK manual premium on a 'No Coverage' building", "OK",
                mod(r2.mine("OK", {"MineSubsidenceCoverage": "Scheduled Buildings"}, recs=(MS, SMS),
                            struct={"MineSubsidenceManualPremium": "300"}), setp("Structure", CovType="No Coverage")),
                {}, ["Mine Subsidence not valid with selected Coverage"], []),
        "S1": ("C16-15", "EPI with Factor 2.0 submitted", "OR",
               lambda: _submit_factor(), {r: {"Factor": Decimal("2.0")} for r in EPI4}, [], []),
        "X1": ("C16-16", "G6 + cyber-incident exclusion (0.995 per peril group)", "OR", mod(r2.g6, cyber),
               {r: {"Factor": r2.EPI_F["270"], **CYBER} for r in EPI4}, [], []),
        # X1 lands on the same whole dollars as G6 ($33/3/7/2): x 0.995 cannot move a $33 premium, so it
        # proves nothing. X2 / X3: Business Income limit 1,000,000, without and with the exclusion, where
        # the factor must move the dollar.
        "X2": ("C16-16", "G6 at BI limit 1,000,000, no exclusion", "OR",
               mod(r2.g6, setp("BusinessIncome", Limit="1000000")),
               {r: {"Factor": r2.EPI_F["270"]} for r in EPI4}, [], []),
        "X3": ("C16-16", "G6 at BI limit 1,000,000 + cyber-incident exclusion", "OR",
               mod(r2.g6, chain(setp("BusinessIncome", Limit="1000000"), cyber)),
               {r: {"Factor": r2.EPI_F["270"], **CYBER} for r in EPI4}, [], []),
    }


def _nothing_qualifies(sub):
    loc = at(sub)[P + "Location"]
    for st in loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"]:
        st["CovType"] = "No Coverage"
        st.pop("CommercialPropertyOccupClassTable", None)
    loc.pop("CommercialPropertySpecialClassTable", None)


def _no_buildings(sub):
    loc = at(sub)[P + "Location"]
    loc.pop("CommercialPropertyStructureTable", None)
    loc.pop("CommercialPropertySpecialClassTable", None)


def _submit_factor():
    sub = r2.g6()
    bi = at(sub)[P + "BusinessIncome"]
    for r in EPI4:
        bi[P + r]["Factor"] = "2.0"
    return sub


# fix M11a: the county has to be set on the location
_orig = cases


def cases():
    cs = _orig()
    t, l, st, b, recs, must, mustnot = cs["M11a"]
    cs["M11a"] = (t, l, st, mod(b, setp("Location", County="Clay")), recs, must, mustnot)
    return cs


def expect(data, rec, ov, state):
    """(prediction, engine) pairs for rec: ZERO -> each $0 or absent; else 175_'s predict."""
    if ov.get("__zero__"):
        nodes_ = rc1.find(data, P + rec)
        eng = [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]
        return [(Decimal(0), e) for e in eng] or [(Decimal(0), None)], []
    return r2.predict(data, rec, ov, state)


def zeroish(v):
    return v in (None, "") or Decimal(str(v)) == 0


def shared_names():
    print("\n" + "=" * 90 + "\nC16-15  SHARED NAMES (CW + 46 in-force states)\n" + "-" * 90)
    fams = r16.population()
    recs = {r for rs in fams.values() for r in rs}
    cw = book_for("OR", ASOF).parent.package.content
    containers = {P + "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod",
                  P + "BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriodSpclClassBusnIncome",
                  P + CA, P + CA + "SpclClassBusnIncome", P + PC}
    groups = recs | containers
    pkgs = {"CW": cw, **{j: book_for(j, ASOF).state.package.content for j in r2.s18.STATES}}
    fields = ("Factor", "BaseFactor", "LimitToUse", "Rate", "Limit", "SellingPriceFactor", "CoverageOnPolicyIndicator",
              "ManualPremium", "Premium")
    writers = collections.defaultdict(set)
    guarded = collections.defaultdict(set)
    for j, pk in pkgs.items():
        rd = pk / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            s = f.read_text(encoding="utf-8-sig", errors="replace")
            for m in re.finditer(r'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', s, re.S):
                name, grp, body = m.groups()
                if grp not in groups:
                    continue
                for fld in fields:
                    if re.search(rf'ToDataDef="{fld}"', body):
                        writers[fld].add(name)
                        if re.search(rf'IsNull>\s*<rul:Value[^>]*FromDataDef="{fld}"', body):
                            guarded[fld].add(name)
    for fld in fields:
        print(f"  {fld:26s} written by {sorted(writers[fld])[:8] or 'no rule (an input)'}"
              + (f"\n  {'':26s} IsNull-guarded (a submitted value survives): {sorted(guarded[fld])[:8]}" if guarded[fld] else ""))


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
            print(f"{cid:5s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, ov in recs.items():
            res, checks = expect(data, rec, ov, state)
            fac_bad = [(f, e, v) for f, e, v in checks if not r2.same(e, v) and f != "HighestPollutantBGIRate"]
            if ov.get("__zero__"):
                ok = all(zeroish(e) for _, e in res)
                preds[cid][rec] = "ZERO"
            elif "__expect__" in ov:
                ok = all(r2.same(h, e) for h, e in res) and not fac_bad
                preds[cid][rec] = [h for h, _ in res]
            else:
                ok = bool(res) and all(not str(h).startswith("hand error") and r2.same(h, e) for h, e in res) and not fac_bad
                preds[cid][rec] = [h for h, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:66]:66s} predicted "
                         f"{'$0' if ov.get('__zero__') else [str(h) for h, _ in res]} engine {[e for _, e in res]}"
                         + (f"  factor {fac_bad[:2]}" if fac_bad else ""))
            if not ok:
                bad.append(rec)
        msgs = set(ip.messages)
        mb = [m for m in must if not any(m in x for x in msgs)] + [f"not: {m}" for m in mustnot if any(m in x for x in msgs)]
        print(f"{cid:5s} {task} {label}: engine {'as derived' if not bad and not mb else 'DIFFERS'}"
              + (f"; messages as predicted: {must}" if must and not mb else "")
              + "".join(f"\n      message {m}" for m in mb))
        print("\n".join(lines)) if lines else None
        if bad or mb:
            FAIL.append(cid)
    shared_names()

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, the whole message set):")
        for cid, (task, label, state, build, recs, must, mustnot) in cs.items():
            sub = build()
            # a policy-level field: read the policy directly (not every case has the occupancy node_dicts needs)
            eo = sub["CommercialPropertyTable"]["CommercialProperty"][0].get(P + "MortgageholdersErrorsAndOmissionsCoverageFormTable")
            if eo:                                    # survives the numeric Limit conversion, restored below
                for rec in eo[P + "MortgageholdersErrorsAndOmissionsCoverageForm"]:
                    rec["Limit"] = "25000"
            req = r11.payload(sub)
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = state
                # the E&O per-mortgage Limit is a domain code ("25,000"), not the numeric Limit the
                # payload converter types every other Limit as
                for rec in cp.get(P + "MortgageholdersErrorsAndOmissionsCoverageForm", []) or []:
                    if "Limit" in rec:
                        rec["Limit"] = "25,000"
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=state)
            (gc.OUT / f"chunk16_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid:5s} ISO REFUSES {m.group(0)[:170] if m else str(exc.body)[:170]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk16_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.get(cid, {}).items():
                iso = r2.iso_of(resp, rec)
                if want == "ZERO":
                    if not all(zeroish(x) for x in iso):
                        pbad.append((rec, iso, "$0"))
                elif sorted(Decimal(str(x)) for x in iso if not zeroish(x)) != sorted(w for w in want if not zeroish(w)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = [m for m in must if not any(m in x for x in mi)]
            ok = not pbad and not d and mi == mo and not mb
            print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds.get(cid, {})) - len(pbad)} of "
                  f"{len(preds.get(cid, {}))} records; {len(ipr) - len(d)} of {len(ipr)} premiums; messages "
                  f"{'equal' if mi == mo else 'DIFFER'}{'; ISO raises the predicted message' if must and not mb else ''}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    print(f"\nRC-3: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
