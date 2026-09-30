#!/usr/bin/env python3
"""Chunk 19, RC-3 (C19-13, C19-14): zero cases and messages.

Every case is one of RC-2's policies (192_) with one thing changed. Each record's premium is predicted
before the run: an explicit $0 where a rule forces it (the competing reading is named), otherwise a hand
evaluation of the filed rule on the tree (175_'s evaluator). Every case also names the messages that
must appear and must not; --live compares every premium field for field and the WHOLE message set.

C19-13  ZERO CASES
  Z1  tenants' unscheduled, both deductibles BLANK   -> every record $0, no message (the factor lookup finds
                                                        no row; the competing reading, "blank = no deductible",
                                                        would price at 1.10 / 1.15)
  Z2  tenants' unscheduled, glass limit 0            -> glass $0 (LOI factor not looked up), other than glass priced
  Z3  tenants' EQCovIndicator Yes, the building's earthquake OFF -> the EQ forms $0 (they read the building's EQRate)
  Z4  antennas: detail limit blank                   -> the detail's forms $0
  Z5  trees: AllItemLimit 0                          -> $0
  Z6  signs: a DETACHED sign at 2,000 (< the 2,500 built in): EVERY form prices on (limit - 2,500) / 100 = -5:
                                                        NEGATIVE premiums (the first reading put Group I / II on
                                                        limit / 100; the hand evaluation of the filed rule and the
                                                        engine both give -$3 / -$1)
  Z7  Brands: the contents' limit 0 (LimitToUse 0)   -> $0
  Z8  Temporarily Away: the contents' EQSprinklerLeakageOnly "Not Applicable" -> EQ factor 0.0 -> EQ $0 (C19-04)
  Z9  Manufacturers: the contents' CovType "Not Applicable" -> factor 1.00 - 1 = 0 -> $0, and the coverage-type message
  Z10 Household on the Broad cause                   -> Special $0 (switched off), Broad priced on the contents' rate
  Z11 Leased Property item limit 0                   -> $0
C19-14  MESSAGES (21: each triggered, and silent where RC-2's golden case already rated it)
  M1  tenants' scheduled AND unscheduled on one building    -> "Cannot have forms CP 14 01 and CP 14 02 ..."
  M2  scheduled, other than glass, no Detail rows           -> "Detail page(s) are needed ..."
  M3  scheduled, glass only, with Detail rows               -> "Detail page(s) are not applicable ..."
  M4  the occupancy on the Legal Liability Coverage Form with Antennas, Trees, Signs, Brands, Leased and
      Manufacturers attached -> CP 14 50 / 14 30 / 14 40 (building) and CP 04 01 / 14 60 / 99 02 (contents)
  M5  trees with EachTreeLimit 1,000                        -> "Please enter per item limit(s)" SILENT (every RC-2
                                                               trees case, with none set, fires it)
  M6  trees on a Standard Property Policy, the building "Blanket Cause of Loss Applies", the trees' own cause
      differing from the blanket's                          -> "Cause of Loss selected needs to be the same ..."
  M7  the building's Deductible "Not Applicable" with Brands -> "Deductible cannot be Not Applicable ..."
  M8  Household on a habitational class (0311) with "All Personal Property" -> both CP 99 92 messages SILENT
      (H1, on chunk 7's class and coverage type, fires both)
  M9  CT: Household on a Standard Property Policy          -> "CP 99 92 not valid with the Standard Property Policy"
  M10 Manufacturers, the contents' coinsurance 70% / 80% / 90% -> 70%: both minimum-80% messages; 80%: ONLY the
      "... in Blanket is required" one (its test is "not blanketed and not 90% / 100%", so it fires on an
      unblanketed 80% contents row); 90%: neither
  M11 Public Institutional Plan with 80% coinsurance: AL contents; KS scheduled tenants'; RI contents and tenants'
  M12 NY: an Entirely Metal sign described "Billboards and Roof Signs - Wood" -> NY's construction message
  R1  Manufacturers on chunk 7's contents type "Personal Property" (no row in its factor table): ISO REFUSES the
      policy; our engine prices $0 with the coverage-type message (OI-103's shape; found by M4's first live run,
      which now uses a listed type)

    python scripts/cf/193_chunk19_rc3.py [--live] [--cases Z1,M4]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
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

from gl_engine.interp.values import InterpretError                       # noqa: E402

g = import_module("192_chunk19_rc2")
r2, rc1, gc, rep, cmp, r11, r16 = g.r2, g.rc1, g.gc, g.rep, g.cmp, g.r11, g.r16
P, same = g.P, g.same
r11.NUMERIC |= {"EachTreeLimit"}
FAIL = []
UNS, SCH, ANT, TREE, SIGN, BRAND, HH, TA, MC = g.UNS, g.SCH, g.ANT, g.TREE, g.SIGN, g.BRAND, g.HH, g.TA, g.MC
ZERO = "zero"                    # the record must be $0 on every node


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def at(sub):
    return rc1.node_dicts(sub)


def con(sub, parent, name):
    return r2.container(sub, parent, name)


def change(build, fn):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


# ---------------------------------------------------------------- zero cases

def z1(sub):
    c = con(sub, "Structure", UNS)
    c.pop("DeductibleOnBuildingGlass")
    c.pop("DeductibleOnBuildingPropertyOtherThanGlass")


def z3():
    """T1's tenants' container on a policy WITHOUT the building's earthquake election."""
    sub = g.with_cause(g.portable("OR"), "Special")
    st = at(sub)[P + "Structure"]
    for k in ("EQCovIndicator", "EQClass", "EQCoinsurance", "EQDeductible", "EQSprinklerLeakageOnly"):
        st.pop(k, None)
    st[P + UNS + "Table"] = g.t1()["CommercialPropertyTable"]["CommercialProperty"][0][
        "CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"][
        "CommercialPropertyStructure"][0][P + UNS + "Table"]
    return sub


def z6():
    sub = g.with_cause(g.portable("OR"), "Special")
    at(sub)[P + "Structure"][P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [
        g.sign_det("Special", "Detached", "Entirely Metal", "2000")]}}]}
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
        r2.put(sub, f"{SIGN}Detail{f}Coverage")
    return sub


def z10():
    sub = g.h1()
    for k in ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome"):
        at(sub)[P + k]["CauseOfLoss"] = "Broad"
    return sub


def leased_limit0(sub):
    at(sub)[P + "PersonalProperty"][P + "LeasedPropertyTable"][P + "LeasedProperty"][0][
        P + "LeasedPropertyDetailTable"][P + "LeasedPropertyDetail"][0]["Limit"] = "0"


def zc(recs):
    return {r: ZERO for r in recs}


# ---------------------------------------------------------------- message cases

def m1():
    sub = g.t1()
    st = at(sub)[P + "Structure"]
    st[P + SCH + "Table"] = g.t2()["CommercialPropertyTable"]["CommercialProperty"][0][
        "CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"][
        "CommercialPropertyStructure"][0][P + SCH + "Table"]
    return sub


def m2(sub):
    c = con(sub, "Structure", SCH)
    c["CovType"] = "Building Property Other Than Glass"
    c.pop(P + SCH + "DetailTable")


def m3(sub):
    con(sub, "Structure", SCH)["CovType"] = "Building Glass"


def m4():
    """six families on one policy, the occupancy on the Legal Liability Coverage Form (chunk 18's M8b: the
    contents' CovForm is set on the occupancy)."""
    sub = g.a1()
    at(sub)[P + "OccupClass"]["CovForm"] = "Legal Liability Coverage Form"
    st, pp = at(sub)[P + "Structure"], at(sub)[P + "PersonalProperty"]
    st[P + TREE + "Table"] = {P + TREE: [{"AllItemLimit": "25000", "CauseOfLoss": "Special", "VehExcl": "No"}]}
    st[P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [
        g.sign_det("Special", "Detached", "Entirely Metal", "30000")]}}]}
    pp[P + BRAND + "Table"] = {P + BRAND: [{}]}
    pp[P + MC + "Table"] = {P + MC: [{}]}
    # a listed contents type: on chunk 7's "Personal Property" (no row in the Manufacturers factor table) ISO
    # REFUSES the whole policy (first live run, 2026-09-29; R1 keeps that as its own probe)
    pp["CovType"] = "Stock"
    pp[P + "LeasedPropertyTable"] = {P + "LeasedProperty": [{P + "LeasedPropertyDetailTable": {
        P + "LeasedPropertyDetail": [{"Limit": "50000"}]}}]}
    return sub


def trees_with(**kw):
    def f(sub):
        con(sub, "Structure", TREE).update(kw)
    return f


def m6():
    sub = g.tree_case("OR", "No")()
    at(sub)[P]["PolicyType"] = "Standard Property Policy"
    at(sub)[P + "Structure"]["CauseOfLoss"] = "Blanket Cause of Loss Applies"
    con(sub, "Structure", TREE)["CauseOfLoss"] = "Fire"
    return sub


def m7():
    sub = g.brands("Special")()
    at(sub)[P + "Structure"]["Deductible"] = "Not Applicable"
    return sub


def m8(sub):
    """the contents' ClassCode is COPIED from the occupancy's ClassCodeToUse, which on class rating is its
    BldgClassCode, itself COPIED from the building's ClassCode: a class submitted on the contents or the occupancy
    is overwritten (first two runs, 2026-09-29). The habitational class goes on the BUILDING."""
    at(sub)[P + "Structure"]["ClassCode"] = "0311"
    at(sub)[P + "PersonalProperty"]["CovType"] = "All Personal Property"


def m9():
    sub = g.with_cause(g.portable("CT"), "Fire, Vandalism and Allied Lines")
    at(sub)[P]["PolicyType"] = "Standard Property Policy"
    at(sub)[P + "PersonalProperty"][P + HH + "Table"] = {P + HH: [{P + HH + "DetailTable": {P + HH + "Detail": [{"Limit": "50000"}]}}]}
    return sub


def m10(coins):
    def f(sub):
        at(sub)[P + "PersonalProperty"].update({"Coinsurance": coins, "IncludedInBlkt": "No"})
    return f


def pip(j, tenants):
    def b():
        sub = g.with_cause(g.portable(j), "Special")
        # the AL / RI contents messages read ../../PublicInstitutionalPlanApply: from the contents row that is the
        # OCCUPANCY (Table wrappers count; first run, 2026-09-29), not the building
        for k in ("Structure", "OccupClass", "PersonalProperty", "SpecialClass"):
            at(sub)[P + k]["PublicInstitutionalPlanApply"] = "Yes"
        at(sub)[P + "PersonalProperty"]["Coinsurance"] = "80%"
        if tenants:
            at(sub)[P + "Structure"][P + SCH + "Table"] = {P + SCH: [{
                "CovType": g.BOTH, "CausesOfLoss": "Special", "EQCovIndicator": "No", "Coinsurance": "80%", "Limit": "45000",
                "DeductibleOnBuildingGlass": "1,000", "DeductibleOnBuildingPropertyOtherThanGlass": "1,000",
                "PublicInstitutionalPlanApply": "Yes",
                P + SCH + "DetailTable": {P + SCH + "Detail": [{"Limit": "40000"}]}}]}
        return sub
    return b


def m12():
    sub = g.with_cause(g.portable("NY"), "Special")
    det = g.sign_det("Special", "Detached", "Entirely Metal", "30000")
    det["SignsDescriptionCharacter"] = "Billboards and Roof Signs - Wood"
    at(sub)[P + "Structure"][P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [det]}}]}
    return sub


# ---------------------------------------------------------------- the cases

TEN_T1, TEN_T2 = g.T1_RECS, g.T2_RECS
MSG = {"1401": "Cannot have forms CP 14 01 and CP 14 02", "needed": "Detail page(s) are needed",
       "notapp": "Detail page(s) are not applicable", "1450": "CP 14 50 not valid", "1430": "CP 14 30 not valid",
       "1440": "CP 14 40 not valid", "0401": "CP 04 01 not valid", "1460": "CP 14 60 not valid",
       "9902form": "CP 99 02 not valid with the selected Coverage Form", "9902type": "CP 99 02 not valid with the selected property",
       "items": "Please enter per item limit(s) on CP 14 30", "blanket": "Cause of Loss selected needs to be the same",
       "ded": "Deductible cannot be Not Applicable", "hab": "CP 99 92 only valid for habitational",
       "app": "CP 99 92 only valid with All Personal", "ct": "CP 99 92 not valid with the Standard",
       "min80": "Minimum 80% Coinsurance requirement with CP 99 02", "min80b": "Minimum 80% Coinsurance in Blanket",
       "pip": "Public Institutional Plan Applies Coinsurance", "pipri": "When Public Institutional Plan Applies coinsurance",
       "ny": "does not coincide with the selected Sign"}


def cases():
    """id -> (task, state, label, build, {rec: ZERO | None (hand)}, messages that must appear, must not appear)."""
    hand = lambda recs: {r: None for r in recs}
    uns_glass = [r for r in TEN_T1 if "BuildingGlass" in r]
    uns_otg = [r for r in TEN_T1 if "OtherThanGlass" in r]
    eq_ten = [r for r in TEN_T1 if r.endswith(("EarthquakeCov", "EQCov"))]
    return {
        "Z1": ("C19-13", "OR", "tenants' unscheduled, both deductibles blank", change(g.t1, z1), zc(TEN_T1), [], []),
        "Z2": ("C19-13", "OR", "tenants' unscheduled, glass limit 0",
               change(g.t1, lambda s: con(s, "Structure", UNS).update({"LimitOnBuildingGlass": "0"})),
               {**zc(uns_glass), **hand(uns_otg)}, [], []),
        "Z3": ("C19-13", "OR", "tenants' EQ Yes, the building's earthquake OFF", z3,
               {**hand([r for r in TEN_T1 if r not in eq_ten]), **zc(eq_ten)}, [], []),
        "Z4": ("C19-13", "OR", "antennas: the broadcasting tower's limit blank",
               change(g.a1, lambda s: at(s)[P + "Structure"][P + ANT + "Table"][P + ANT][0][P + ANT + "DetailTable"][
                   P + ANT + "Detail"][0].pop("Limit")),
               # the detail premium reads ../Limit with no default: blank is 0 on the first tower; the second prices
               {**{r: [ZERO, None] for r in g.A1_RECS if "Detail" in r}, **hand([r for r in g.A1_RECS if "Detail" not in r])},
               [], []),
        "Z5": ("C19-13", "OR", "trees: AllItemLimit 0", change(g.tree_case("OR", "No"), trees_with(AllItemLimit="0")),
               zc(g.TREE_RECS), [MSG["items"]], []),
        "Z6": ("C19-13", "OR", "signs: a detached sign at 2,000 (< the built-in 2,500)", z6, hand(g.SIGN_RECS), [], []),
        "Z7": ("C19-13", "OR", "Brands: the contents' limit 0",
               change(g.brands("Special"), lambda s: at(s)[P + "PersonalProperty"].update({"Limit": "0"})), zc(g.BRAND_RECS), [], []),
        "Z8": ("C19-13", "OR", "Temporarily Away: the contents' EQSprinklerLeakageOnly Not Applicable",
               change(g.ta(False), lambda s: at(s)[P + "PersonalProperty"].update({"EQSprinklerLeakageOnly": "Not Applicable"})),
               {**hand([r for r in g.TA_RECS if "Earthquake" not in r]), **zc([r for r in g.TA_RECS if "Earthquake" in r])}, [], []),
        "Z9": ("C19-13", "OR", "Manufacturers: the contents' CovType Not Applicable", g.mc("Not Applicable"), zc(g.MC_RECS),
               [MSG["9902type"]], []),
        "Z10": ("C19-13", "OR", "Household on the Broad cause", z10, hand(g.HH_RECS), [], []),
        "Z11": ("C19-13", "OR", "Leased Property item limit 0", change(g.g18.a4, leased_limit0), zc(g.LEASED_RECS), [], []),
        "M1": ("C19-14", "OR", "scheduled AND unscheduled tenants' on one building", m1, hand(TEN_T1 + TEN_T2), [MSG["1401"]], []),
        "M2": ("C19-14", "OR", "scheduled, other than glass, no Detail rows", change(g.t2, m2), hand(TEN_T2), [MSG["needed"]], [MSG["notapp"]]),
        "M3": ("C19-14", "OR", "scheduled, glass only, with Detail rows", change(g.t2, m3), hand(TEN_T2), [MSG["notapp"]], [MSG["needed"]]),
        "M4": ("C19-14", "OR", "Legal Liability form: Antennas, Trees, Signs, Brands, Leased, Manufacturers", m4, {},
               [MSG[k] for k in ("1450", "1430", "1440", "0401", "1460", "9902form")], []),
        "M5": ("C19-14", "OR", "trees with EachTreeLimit 1,000 (per-item message silent)",
               change(g.tree_case("OR", "No"), trees_with(EachTreeLimit="1000")), hand(g.TREE_RECS), [], [MSG["items"]]),
        "M6": ("C19-14", "OR", "trees: SPP, building on the blanket cause, trees' own cause Fire", m6, {}, [MSG["blanket"]], []),
        "M7": ("C19-14", "OR", "the building's Deductible Not Applicable with Brands", m7, {}, [MSG["ded"]], []),
        "M8": ("C19-14", "OR", "Household on class 0311, All Personal Property (both CP 99 92 messages silent)",
               change(g.h1, m8), hand(g.HH_RECS), [], [MSG["hab"], MSG["app"]]),
        "M9": ("C19-14", "CT", "CT: Household on a Standard Property Policy", m9, {}, [MSG["ct"]], []),
        "M10a": ("C19-14", "OR", "Manufacturers, contents coinsurance 70%", change(g.mc("Stock"), m10("70%")), {},
                 [MSG["min80"], MSG["min80b"]], []),
        "M10b": ("C19-14", "OR", "Manufacturers, contents coinsurance 80% (only the blanket message)", change(g.mc("Stock"), m10("80%")), {},
                 [MSG["min80b"]], [MSG["min80"]]),
        "M10c": ("C19-14", "OR", "Manufacturers, contents coinsurance 90% (neither)", change(g.mc("Stock"), m10("90%")), {},
                 [], [MSG["min80"], MSG["min80b"]]),
        "M11a": ("C19-14", "AL", "AL: Public Institutional Plan, contents at 80%", pip("AL", False), {}, [MSG["pip"]], []),
        "M11b": ("C19-14", "KS", "KS: Public Institutional Plan, scheduled tenants' at 80%", pip("KS", True), {}, [MSG["pip"]], []),
        "M11c": ("C19-14", "RI", "RI: Public Institutional Plan, contents and tenants' at 80%", pip("RI", True), {},
                 [MSG["pip"], MSG["pipri"]], []),
        "M12": ("C19-14", "NY", "NY: Entirely Metal sign described as a wood billboard", m12, {}, [MSG["ny"]], []),
        # predicted: ISO REFUSES (no factor row for the contents type) -- the OI-103 shape (found by M4's first
        # live run). Ours: BaseFactor is blank (no row), and since OI-115 (2026-09-30) Property's Subtract skips a
        # blank operand as ISO does, so Factor = Round(blank - 1) = 1 and the four records price at the contents'
        # own rate (was $0 before OI-115). ISO never reaches that Subtract: it refuses at the lookup. OI-103.
        "R1": ("C19-13", "OR", "Manufacturers on chunk 7's contents type 'Personal Property' (no factor row)",
               g.mc("Personal Property"),
               {r: (Decimal({"BasicGroupI": 198, "BasicGroupII": 21, "Earthquake": 8, "Special": 123}[k]) if k != "Broad" else ZERO)
                for r in g.MC_RECS for k in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special")
                if r.endswith(f"Assumption{k}Coverage")},
               [MSG["9902type"]], []),
    }

#: cases where ISO is predicted to refuse the policy: the refusal must name this table
REFUSE = {"R1": "ManufacturersConsequentialLossAssumptionFactor"}


# ------------------------------------------------------------------- run

def has(msgs, frag):
    return any(frag in m for m in msgs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), j)
        except InterpretError as exc:
            print(f"{cid:5s} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        lines, bad = [], []
        preds[cid] = {}
        for rec, want in recs.items():
            nodes_ = rc1.find(data, P + rec)
            eng = [n.first("Premium").text if n.first("Premium") is not None else None for n in nodes_]
            if want == ZERO:
                hv = [Decimal(0)] * max(len(nodes_), 1)
            else:
                res, _ = r2.predict(data, rec, {}, j)
                off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
                hv = [Decimal(0) if o else h for (h, _), o in zip(res, off)] if len(off) == len(res) else [h for h, _ in res]
                if isinstance(want, list):              # per node: ZERO forces that node's $0, None keeps the hand value
                    hv = [Decimal(0) if w == ZERO else h for w, h in zip(want, hv)]
            ok = all(not str(h).startswith("hand") for h in hv) and (
                [Decimal(str(e or 0)) for e in eng] == [Decimal(str(h)) for h in hv] if eng else all(same(h, 0) for h in hv))
            preds[cid][rec] = hv
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:70]:70s} predicted {[str(h) for h in hv]} engine {eng}"
                         + ("  (forced $0)" if want == ZERO else "  (per node: $0 / hand)" if isinstance(want, list) else ""))
            if not ok:
                bad.append(rec)
        msgs = set(ip.messages)
        mbad = [f"missing: {m}" for m in must if not has(msgs, m)] + [f"unexpected: {m}" for m in mustnt if has(msgs, m)]
        print(f"{cid:5s} {task} {j} {label}: {'as derived' if not bad and not mbad else 'DIFFERS'}"
              f" ({len(recs)} records predicted; messages: {len(must)} required, {len(mustnt)} forbidden"
              f"{', ' + '; '.join(mbad) if mbad else ' -- ok'})")
        if lines:
            print("\n".join(lines))
        fam_msgs = sorted(m for m in msgs if any(v in m for v in MSG.values()))
        if fam_msgs:
            print(f"      chunk 19 messages on this policy: {fam_msgs}")
        if bad or mbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, the whole message set):")
        for i, (cid, (task, j, label, build, recs, must, mustnt)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            if j != "OR":
                for cp in req["body"]["CommercialProperty"]:
                    cp["State"] = j
                req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk19_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                predicted = cid in REFUSE and REFUSE[cid] in str(exc.body)
                print(f"  {cid:5s} ISO REFUSES {'(as predicted) ' if predicted else ''}{m.group(0)[:220] if m else str(exc.body)[:220]}")
                if not predicted:
                    FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk19_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            if cid in REFUSE:
                print(f"  {cid:5s} DIFFER: ISO was predicted to refuse and rated the policy")
                FAIL.append(f"{cid} live")
                continue
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
            mreq = [m for m in must if not has(mi, m)] + [m for m in mustnt if has(mi, m)]
            ok = not pbad and not d and mi == mo and not mreq
            print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + (f"; ISO's messages miss the prediction {mreq}" if mreq else "")
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C19-13, C19-14): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
