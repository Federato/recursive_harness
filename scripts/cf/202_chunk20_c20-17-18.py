#!/usr/bin/env python3
"""Chunk 20, RC-3 (C20-17, C20-18): shared names and the cyber-incident exclusion factors.

C20-17  SHARED NAMES. A static diff over every chunk 20 countrywide rule file: each Set rule's written field,
        IsNull-GUARDED (a submitted value survives) or UNCONDITIONAL (overwritten), and any value COPIED from a
        parent. Then probes on 200_'s Oregon policy, each predicted before its ISO call from that classification,
        each against a value that gives a different dollar:
  S1  Fire Department Factor 0.8 submitted (guarded)               -> used: (25,000 - 1,000) / 100 x 0.8
  S2  Fire Department LimitToUse 40,000 submitted (guarded)        -> used over its own 25,000
  S3  Tobacco rate 100 submitted (guarded)                         -> used (the band's is 53)
  S4  Mortgageholders First500Rate 0.2 (guarded) and First500Mortgages 100 (unconditional) submitted
                                                                   -> the rate used; the count OVERWRITTEN (500)
  S5  jewelry BaseSpecialLimit 5,000 submitted (guarded), "Worth $100 or less" (table 0) -> used
  S6  Pier (building) Rate 0.5 submitted (guarded)                 -> used; Pier on BI IncludedInBlkt "Yes"
      submitted (unconditional copy of BI's "No")                  -> OVERWRITTEN: LimitToUse is BI's 100,000,
                                                                      not the record's own 40,000
  S7  EB OccupancyGroupNumber 7 submitted (unconditional)          -> OVERWRITTEN (3); EB building LossCost 100
      (guarded) -> used; EB BI WaitingPeriod 0.5 (unconditional)   -> OVERWRITTEN (0.15)
  S8  the BI fungus records' IncreasedPeriodOfRestoration 180 submitted (unconditional copy of the policy
      record's 90)                                                 -> OVERWRITTEN: factor 0.03, not 0.08
  S9  CoverageOnPolicyIndicator 1 submitted on Tobacco, ordinary form (unconditional switch) -> 0, $0
  S10 Food FoodRate 0.5 and ACP WatercraftExclBuybackRate 0.1 submitted (guarded) -> used
  S11 Fungus ExcessOfSubLimitRate 0.5 (guarded) -> used; IncrementalCalc 99 (unconditional) -> overwritten
  S12 the contents' LossCostMultiplier 1.2: Tobacco reads the contents' LCM (read-through, not a copy) -> x 1.2
  S13 ACP (option 1) with the building's chunk 17 watercraft exclusion record -> ACP $0 (it prices only when
      the building has NO watercraft exclusion; the two families share the construction-option table)
C20-18  THE CYBER-INCIDENT EXCLUSION, four factor names, at limits where the factor moves a dollar:
  X0  control: Fire Department 500,000, Mortgageholders 20,000 at 1,000,000, ACP on a 10,000,000 building,
      EB (Industrial, group 7) on it, BI 2,000,000
  X1  X0 + CP 10 75: Fire Department x CyberIncidentExclusionFactorBGI 0.995, Mortgageholders x ...Mortgageholders
      0.999, ACP x ...FactorSpecial 0.995, EB x ...FactorEquipmentBreakdown 0.999
  X2  X0 + CP 10 76 (Sublimit, aggregate Yes): x the COLExcptns factors (BGI 0.997, Special 0.996, EB 0.999);
      Mortgageholders reads none of them (unmoved)

    python scripts/cf/202_chunk20_c20-17-18.py [--live] [--cases S1,X1]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
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
gc, rc1, rep, cmp, r16, r11, r2 = m.gc, m.rc1, m.rep, m.cmp, m.r16, m.r11, m.r2
P, put, at, same, val = m.P, m.put, m.at, m.same, m.val
cen = m.cen20
# fields a rule normally computes, submitted by the probes: declared xs:int / xs:decimal in the DataDef XSD
# (the first live run: ISO refused all eight as strings). WaitingPeriod is text elsewhere, decimal on the EB record.
r11.NUMERIC |= {"Factor", "LimitToUse", "TobaccoInSalesWarehousesRate", "First500Rate", "First500Mortgages",
                "BaseSpecialLimit", "LossCost", "OccupancyGroupNumber", "WaitingPeriod", "FoodRate",
                "WatercraftExclBuybackRate", "ExcessOfSubLimitRate", "IncrementalCalc"}
FAIL = []
EB_INTER = {m.EBB: {"OccupancyCategory": "Institutional", "OccupancyGroup": "All other institutional risks"}}


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def cp_of(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


# ------------------------------------------------------------ C20-17 static diff

def writers():
    """(record, field) -> (guarded | UNCONDITIONAL, copied-from paths), from every Set rule in the chunk 20 CW files."""
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    out = {}
    for fam, pat in cen.FAMILIES:
        for f in sorted(cw.glob("*.xml")):
            if not re.search(pat, f.name) or cen.EXCLUDE.search(f.name):
                continue
            t = f.read_text(encoding="utf-8-sig")
            rec = f.name[len(P):-len("Rules.Rule.xml")]
            for mm in re.finditer(r'<rul:Rule Name="(Set\w+)"[^>]*>(.*?)</rul:Rule>', t, re.S):
                body = mm.group(2)
                for fld in set(re.findall(r'ToDataDef="(\w+)"', body)):
                    if fld in ("Premium", "PremiumIndicator", "TotalPremium") or fld.startswith("Subline") or fld.endswith("Code"):
                        continue
                    guarded = re.search(rf'<rul:IsNull>\s*<rul:Value[^>]*FromDataDef="{fld}"', body) is not None
                    src = set(re.findall(rf'<rul:Copy[^>]*ToDataDef="{fld}"[^>]*FromDataDef="([^"]+)"', body))
                    prev = out.get((rec, fld), ("guarded", set()))
                    kind = "guarded" if guarded and prev[0] == "guarded" else "UNCONDITIONAL"
                    out[(rec, fld)] = (kind, prev[1] | {s for s in src if s.startswith("..")})
    return out


def static_diff():
    w = writers()
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for (rec, fld), (kind, src) in w.items():
        by[fld][kind].append(rec + (" <- " + ",".join(sorted(src))[:70] if src else ""))
    print("C20-17  who writes each field in the chunk 20 files (guarded: a submitted value survives; <- copied from a parent)")
    for fld in sorted(by):
        for kind in ("guarded", "UNCONDITIONAL"):
            recs = sorted(by[fld][kind])
            if recs:
                print(f"    {fld:44s} {kind:13s} {len(recs):2d}: {'; '.join(r16.short(r) if '<-' not in r else r for r in recs)[:170]}")
    return w


# ------------------------------------------------------------ probes

def with_(build, fn):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


def fire(**extra):
    return with_(m.base, lambda s: put(s, "LocationFireDepartmentCharge",
                                      {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes", "Limit": "25000", **extra}))


def s6(sub):
    put(sub, m.PIER[0], {"Construction": m.PIER1, "Limit": "40000", "Rate": "0.5"})
    put(sub, m.PIER[1], {"Construction": m.PIER1, "Limit": "40000", "IncludedInBlkt": "Yes"})


def s7(sub):
    put(sub, m.EBB + "EBCov", inter={m.EBB: {**EB_INTER[m.EBB], "OccupancyGroupNumber": "7", "LossCost": "100"}})
    put(sub, m.EBI + "Coverage", inter={m.EBI: {"WaitingPeriod": "0.5"}})
    put(sub, m.EBI + "WaitingPeriodCoverage")
    at(sub)[P + "BusinessIncome"][P + m.NOWAIT + "Table"] = {P + m.NOWAIT: [{"TimePeriod": "Eliminated"}]}


def s8(sub):
    cp_of(sub)["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
    put(sub, m.FUNGUS, {"SubLimit": "50000", "IncreasedPeriodOfRestoration": "90"})
    at(sub)[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
    for r in m.BIF:
        put(sub, r, {"IncreasedPeriodOfRestoration": "180"})


def s10(sub):
    put(sub, m.FOOD[0], {"FoodLimit": "10000", "FoodRate": "0.5"})
    put(sub, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "WatercraftExclBuybackConstrctnOption": m.PIER1,
                                                 "Limit": "30000", "WatercraftExclBuybackRate": "0.1"})


def s11(sub):
    cp_of(sub)["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
    put(sub, m.FUNGUS, {"SubLimit": "50000", "IncreasedPeriodOfRestoration": "Not Applicable",
                        "ExcessOfSubLimitRate": "0.5", "IncrementalCalc": "99"})


def s12(sub):
    at(sub)[P + "OccupClass"]["CovForm"] = "Tobacco Sales Warehouse Coverage Form"
    at(sub)[P + "PersonalProperty"]["LossCostMultiplier"] = "1.2"
    put(sub, "PersonalPropertyTobaccoSalesWarehousesCoverage")


def s13(sub):
    put(sub, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "WatercraftExclBuybackConstrctnOption": m.PIER1, "Limit": "30000"})
    at(sub)[P + "Structure"][P + "WatercraftExclusionTable"] = {P + "WatercraftExclusion": [{}]}


# ------------------------------------------------------------ C20-18

def exclusion(kind):
    def b():
        sub = m.base()
        cp = cp_of(sub)
        st = at(sub)[P + "Structure"]
        st.update({"Limit": "10000000", "FullBldgValue": "10000000"})
        at(sub)[P + "BusinessIncome"]["Limit"] = "2000000"
        put(sub, "LocationFireDepartmentCharge", {"FireIncreaseLimitApplyOnPolicyIndicator": "Yes", "Limit": "500000"})
        put(sub, m.MORT, {"Limit": "1,000,000", "NumberMortgages": "20000"})
        put(sub, "AdditionalCoveredPropertyDetail", {"Type": m.BULK, "WatercraftExclBuybackConstrctnOption": m.PIER1, "Limit": "30000"})
        inter = {m.EBB: {"OccupancyCategory": "Industrial and Processing", "OccupancyGroup": "All other industrial and processing risks"}}
        put(sub, m.EBB + "EBCov", inter=inter)
        put(sub, m.EBI + "Coverage")
        if kind == "75":
            cp[P + "CyberIncidentExclusionTable"] = {P + "CyberIncidentExclusion": [{}]}
        elif kind == "76":
            cp[P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptionsTable"] = {
                P + "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions": [{}]}
            cp.update({"CyberTypeOfLimitPropertyDamage": "Sublimit", "CyberIsAggregateLimit": "Yes"})
        return sub
    return b


X_RECS = ["LocationFireDepartmentCharge", m.MORT, "AdditionalCoveredPropertyDetail", m.EBB + "EBCov", m.EBI + "Coverage"]


def expect_x(kind):
    def e(data, j):
        if kind == "75":
            f = lambda g: val(j, "CyberIncidentExclusionFactors", "Factor", CausesOfLossOrPerilGroupPremium=g)
            return {"__policy__": {"CyberIncidentExclusionFactorBGI": f("Basic Group I"), "CyberIncidentExclusionFactorSpecial": f("Special"),
                                   "CyberIncidentExclusionFactorEquipmentBreakdown": f("Equipment Breakdown"),
                                   "CyberIncidentExclusionFactorMortgageholdersErrorsAndOmissions":
                                       val(j, "CyberIncidentExclusionFactorMortgageholdersErrorsAndOmissions", "Factor", Constant="Y")}}
        if kind == "76":
            f = lambda g: val(j, "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors", "Factor",
                              CausesOfLossOrPerilGroupPremium=g, TypeOfLimit="Sublimit", AggregateLimit="Yes")
            return {"__policy__": {"CyberIncidentExclusionCOLExcptnsFactorBGI": f("Basic Group I"),
                                   "CyberIncidentExclusionCOLExcptnsFactorSpecial": f("Special"),
                                   "CyberIncidentExclusionCOLExcptnsFactorEquipmentBreakdown": f("Equipment Breakdown")}}
        return {}
    return e


def fields(recfield):
    """{(record, idx): {field: expected}} as a builder-independent expectation."""
    return lambda data, j: recfield


def cases():
    """id -> (task, label, build, records, expect(data, j), control id or None)."""
    TOB = ["PersonalPropertyTobaccoSalesWarehousesCoverage"]
    return {
        "S1": ("C20-17", "Fire Department Factor 0.8 submitted (guarded -> used)", fire(Factor="0.8"), ["LocationFireDepartmentCharge"],
               fields({"LocationFireDepartmentCharge": {"Factor": "0.8"}}), None),
        "S2": ("C20-17", "Fire Department LimitToUse 40,000 submitted (guarded -> used)", fire(LimitToUse="40000"), ["LocationFireDepartmentCharge"],
               fields({"LocationFireDepartmentCharge": {"LimitToUse": "40000"}}), None),
        "S3": ("C20-17", "Tobacco rate 100 submitted (guarded -> used)", with_(m.tobacco("100000"), lambda s: at(s)[P + "PersonalProperty"][
               P + "PersonalPropertyTobaccoSalesWarehousesCoverage"].update({"TobaccoInSalesWarehousesRate": "100"})), TOB,
               fields({TOB[0]: {"TobaccoInSalesWarehousesRate": "100"}}), None),
        "S4": ("C20-17", "Mortgageholders First500Rate 0.2 (guarded) + First500Mortgages 100 (unconditional) submitted",
               with_(m.mortgage(1001, "50,000"), lambda s: [d.update({"First500Rate": "0.2", "First500Mortgages": "100"})
                                                           for k, d in m.walk(s) if k == P + m.MORT]), [m.MORT],
               fields({m.MORT: {"First500Rate": "0.2", "First500Mortgages": "500"}}), None),
        "S5": ("C20-17", "jewelry BaseSpecialLimit 5,000 submitted (guarded -> used; the table's is 0)",
               with_(m.base, lambda s: put(s, m.JEWEL, {"Indicator": "Yes", "Limit": "10000", "ValueIndicator": "Worth $100 or less per item",
                                                        "BaseSpecialLimit": "5000"})), [m.JEWEL], fields({m.JEWEL: {"BaseSpecialLimit": "5000"}}), None),
        "S6": ("C20-17", "Pier Rate 0.5 (guarded -> used); Pier on BI IncludedInBlkt Yes (unconditional -> No, parent's limit)",
               with_(m.base, s6), m.PIER[:2], fields({m.PIER[0]: {"Rate": "0.5"}, m.PIER[1]: {"IncludedInBlkt": "No", "LimitToUse": "100000"}}), None),
        "S7": ("C20-17", "EB group 7 (unconditional -> 3), building LossCost 100 (guarded -> used), BI WaitingPeriod 0.5 (unconditional -> 0.15)",
               with_(m.base, s7), [m.EBB + "EBCov", m.EBI + "Coverage", m.EBI + "WaitingPeriodCoverage"],
               fields({m.EBB: {"OccupancyGroupNumber": "3", "LossCost": "100"}, m.EBI: {"WaitingPeriod": "0.15"}}), None),
        "S8": ("C20-17", "BI fungus records' period 180 submitted (unconditional copy of the policy's 90)", with_(m.base, s8), [m.FUNGUS],
               fields({(r, 0): {"IncreasedPeriodOfRestoration": "90", "Factor": "0.03"} for r in m.BIF}), None),
        "S9": ("C20-17", "Tobacco CoverageOnPolicyIndicator 1 submitted on the ordinary form (unconditional -> 0)",
               with_(m.base, lambda s: put(s, TOB[0], {"CoverageOnPolicyIndicator": "1"})), TOB,
               fields({TOB[0]: {"CoverageOnPolicyIndicator": "0"}}), None),
        "S10": ("C20-17", "Food FoodRate 0.5, ACP WatercraftExclBuybackRate 0.1 submitted (guarded -> used)", with_(m.base, s10),
                [m.FOOD[0], "AdditionalCoveredPropertyDetail"],
                fields({m.FOOD[0]: {"FoodRate": "0.5"}, "AdditionalCoveredPropertyDetail": {"WatercraftExclBuybackRate": "0.1"}}), None),
        "S11": ("C20-17", "Fungus ExcessOfSubLimitRate 0.5 (guarded -> used), IncrementalCalc 99 (unconditional -> 0)", with_(m.base, s11),
                [m.FUNGUS], fields({m.FUNGUS: {"ExcessOfSubLimitRate": "0.5", "IncrementalCalc": "0"}}), None),
        "S12": ("C20-17", "the contents' LossCostMultiplier 1.2 under Tobacco (read through)", with_(m.base, s12), TOB, fields({}), None),
        "S13": ("C20-17", "ACP with the building's watercraft exclusion record (chunk 17)", with_(m.base, s13),
                ["AdditionalCoveredPropertyDetail"], fields({"AdditionalCoveredPropertyDetail": {"Premium": "0"}}), None),
        "X0": ("C20-18", "Fire Department, Mortgageholders, ACP, EB at large limits (control)", exclusion(None), X_RECS, expect_x(None), None),
        "X1": ("C20-18", "X0 + CP 10 75", exclusion("75"), X_RECS, expect_x("75"), "X0"),
        "X2": ("C20-18", "X0 + CP 10 76 (Sublimit, aggregate Yes)", exclusion("76"), X_RECS, expect_x("76"), "X0"),
    }


# ------------------------------------------------------------ run

def field_checks(data, expect):
    out = []
    for key, flds in expect.items():
        if key == "__policy__":
            node = r16.find(data, "CommercialProperty")[0] if r16.find(data, "CommercialProperty") else None
            rec, idx = "CommercialProperty", 0
        else:
            rec, idx = key if isinstance(key, tuple) else (key, 0)
            nodes_ = r16.find(data, P + rec)
            node = nodes_[idx] if len(nodes_) > idx else None
        for f, want in flds.items():
            got = None if node is None or node.first(f) is None else node.first(f).text
            out.append((f"{r16.short(rec)[:48]}[{idx}]", f, got, want))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    progress(0, 1, "static diff")
    static_diff()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    print()
    for i, (cid, (task, label, build, recs, expect, ctrl)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), "OR")
        except InterpretError as exc:
            print(f"{cid:4s} RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        fc = field_checks(data, expect(data, "OR"))
        fbad = [c for c in fc if not same(c[2], c[3])]
        preds[cid], bad, lines = {}, [], []
        for rec in recs:
            res = m.predict(data, rec, "OR")
            nodes_ = rc1.find(data, P + rec)
            off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
            res = [(Decimal(0) if o else h, e) for (h, e), o in zip(res, off)]
            ok = bool(res) and all(not str(h).startswith("hand") and same(h, e or 0) for h, e in res)
            preds[cid][rec] = [h for h, _ in res]
            moved = ""
            if ctrl and ctrl in preds and rec in preds[ctrl]:
                moved = f"  control {[str(x) for x in preds[ctrl][rec]]} -> {'MOVES' if preds[ctrl][rec] != preds[cid][rec] else 'unmoved'}"
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:62]:62s} predicted {[str(h) for h, _ in res]} engine {[e for _, e in res]}{moved}")
            if not ok:
                bad.append(rec)
        print(f"{cid:4s} {task} {label}: {'as derived' if not bad and not fbad else 'DIFFERS'} "
              f"({len(fc) - len(fbad)} of {len(fc)} tree values = the classification's prediction)")
        for w, f, g, want in fc:
            print(f"      {'ok  ' if same(g, want) else 'FAIL'} {w:52s} {f:52s} tree {g}  predicted {want}")
        print("\n".join(lines))
        if bad or fbad:
            FAIL.append(cid)
    # every cyber factor must move a dollar somewhere, and CP 10 76 must leave Mortgageholders unmoved
    if "X0" in preds:
        for x, fam_moves in (("X1", X_RECS), ("X2", [r for r in X_RECS if r != m.MORT])):
            if x in preds:
                for rec in fam_moves:
                    if preds[x][rec] == preds["X0"][rec]:
                        print(f"      FAIL {x}: {r16.short(rec)} does not move a dollar")
                        FAIL.append(f"{x} {rec}")
        if "X2" in preds and preds["X2"][m.MORT] != preds["X0"][m.MORT]:
            FAIL.append("X2 mortgage moved")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, messages):")
        for i, (cid, (task, label, build, recs, expect, ctrl)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = m.payload(build())
            (gc.OUT / f"chunk20_c20-17-18_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r'"Message":"([^"]{0,240})', str(exc.body))
                print(f"  {cid:4s} ISO REFUSES {mm_.group(0) if mm_ else str(exc.body)[:240]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk20_c20-17-18_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C20-17, C20-18): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
