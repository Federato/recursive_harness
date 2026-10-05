#!/usr/bin/env python3
"""Chunk 26, RC-3 (C26-12..C26-15): Specific / Tentative zero cases, messages, shared names and the class-only factors.
Live ISO.

Every case is predicted before it runs: each Group I / Group II rate by 234_'s hand models, each premium of the building,
contents and BI coverage records by 174_'s evaluator on the state's own rule (235_'s derive), the EXACT multiset of the
chunk's messages, and -- where a case claims something does NOT move -- the premiums of a reference policy it must equal,
with a competing tree showing the same change DOES move a class-rated dollar.

The rules, read from the text:
  blank RatingType      building and BI: Otherwise -> rate 1.0; contents: "not Class" -> their own specific rate
  no SpecificGroupIRate building 0 -> Group I $0 on building AND BI (BI reads the building's rate); contents: own rate
  Group II              RatingTypeBasicGroupII blank -> Otherwise 0.0 on building, contents and BI, no message
  hazard messages       RatingTypeBasicGroupII Specific and hazard level Severe < 10,000 / High < 25,001 / Medium < 50,001
                        sq ft; Low: always (two wordings across states, with and without a final period); the message
                        does NOT stop the specific premium
  FL                    Specific Group II on 21 residential class codes (0074-0343): building and contents messages
  DC                    Class rating on the three boarding / fraternity descriptions: "Specific loss costs apply"
  copies                OccupClass / PersonalProperty RatingType := the building's (unguarded): a submitted copy is overwritten
  class-only            protection class, Group I territory factor, the contents' fire-safe vault factor and the seven
                        occupancy counts are read only on the Class path

    python scripts/cf/236_chunk26_rc3.py [--live] [--cases Z1,M5]
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import re
import sys
import time
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

import gl_engine.interp.interpreter as interp                             # noqa: E402

c2 = import_module("235_chunk26_rc2")
h, t2, m, rc1, rep, cmp, gc, r11 = c2.h, c2.t2, c2.m, c2.rc1, c2.rep, c2.cmp, c2.gc, c2.r11
P, D, val = c2.P, Decimal, c2.val
s4 = import_module("232_chunk25_rc4")
FAIL = []
r11.NUMERIC |= {"BasicGroupIRate", "FireSafeVaultFactor"}

c23 = import_module("221_chunk23_rc3")               # imported first: it wraps MessageHelper too
lvl, iso_tagged = c23.lvl, c23.iso_tagged
TAGGED = []
_orig = interp._BUILTINS["MessageHelper"]


def _tagged(ip, rule_name, args, frame, where):
    TAGGED.append((str(args.get("TableName") or ""), str(args.get("Message") or "")))
    return _orig(ip, rule_name, args, frame, where)


interp._BUILTINS["MessageHelper"] = _tagged

L = {"ST": P + "Structure", "PP": P + "PersonalProperty"}
SEV, HIGH, MED, LOW = "Severe Hazard Level", "High Hazard Level", "Medium Hazard Level", "Low Hazard Level"
NONRES, FRAT, APT = "Non-Residential Risk Program", "Fraternity or Sorority", "Only one Apartment without Mercantile"
FRAGS = [SEV, HIGH, MED, LOW, NONRES, FRAT, APT]
#: known, recorded differences (messages only). K4d (OI-125) closed by chunk 28 C28-08: ours no longer reads the
#: occupancies' submitted RatingType, which a rule writes later, so its count is 0 as ISO's is
KNOWN = {}
CORE = {"BI": "BusinessIncomeBasicGroupICoverage", "B1": "StructureBuildingBasicGroupICoverage", "B2": "StructureBuildingBasicGroupIICoverage",
        "C1": "PersonalPropertyPrsnlPropBasicGroupICoverage", "C2": "PersonalPropertyPrsnlPropBasicGroupIICoverage",
        "BI2": "BusinessIncomeBasicGroupIICoverage"}
SUBMITTED = {"S2": {"building BGI": D("0.500")}}
FRAT_DESC = "Boarding and Lodging Houses, Rooming Houses, Fraternities and Sororities, Dormitories - Up to 10 Units"
D0581 = "Mercantile - Multiple occupancy without class code 0564 (Furniture and Home Furnishings Other Than Appliances) occupant - Not la"


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ builders

def edit(build, **recs):
    def b():
        sub = build()
        for rec, f in recs.items():
            dd = m.at(sub)[P + rec]
            for k, v in f.items():
                if v is None:
                    dd.pop(k, None)
                else:
                    dd[k] = v
        return sub
    return b


def gii(j, county, sqft, terr, extra=None):
    """a Specific Group II building in state j (192_'s portable; its submitted Group II rates removed)."""
    def b():
        sub = h.tree(j=j, st_over={"RatingTypeBasicGroupII": "Specific", "SpecificGroupIIRate": "0.060", "SquareFootageOfBuilding": str(sqft),
                                   **(extra or {})})
        at = m.at(sub)
        at[P + "PersonalProperty"]["SpecificGroupIIRate"] = "0.050"
        at[P + "Location"].update({"GeographicWindHazardLevelTerritory": county, "BasicGroupIIRatingTerr": terr})
        for k in ("Structure", "PersonalProperty"):
            at[P + k].pop("BasicGroupIIRate", None)
        return s4.state_fixes(sub, j)
    return b


def two_apartments(rt, occ_rt=None):
    """two apartment occupancies (0311) on one building. The count rule reads each OCCUPANCY's RatingType, which the
    occupancy copies from the building only later in the run: unless the submitter sends it, the count is 0."""
    def b():
        sub = h.tree(rt=rt, st_over={"ClassCode": "0311"})
        oc = m.at(sub)[P + "Structure"][P + "OccupClassTable"][P + "OccupClass"]
        oc[0]["ClassCode"] = "0311"
        if occ_rt:
            oc[0]["RatingType"] = occ_rt
        second = copy.deepcopy(oc[0])
        oc.append(second)
        return sub
    return b


SC_G = lambda county, sqft: gii("SC", county, sqft, "Inland")
CASES = {
    # (task, j, label, build, zero core records, messages (level, fragment), reference build whose core premiums must be equal,
    #  competing build that must move them)
    "Z1": ("C26-12", "OR", "Specific with no SpecificGroupIRate: building AND BI Group I $0 (BI reads the building's rate)",
           edit(h.tree, Structure={"SpecificGroupIRate": None}), {"B1", "BI"}, [], None, None),
    "Z2": ("C26-12", "OR", "contents with no own SpecificGroupIRate on a Specific building: contents Group I $0, silent",
           lambda: h.tree(pp_s1=None), {"C1"}, [], None, None),
    "Z3": ("C26-12", "OR", "Specific on a class code the domain offers only for Class (0581): rated as written",
           edit(h.tree, Structure={"ClassCode": "0581", "ClassificationDescription": D0581}), set(), [], None, None),
    "Z4": ("C26-12", "SC", "RatingTypeBasicGroupII blank with a specific Group II rate: Group II $0 on building, contents, BI, silent",
           edit(SC_G("Charleston", 20000), Structure={"RatingTypeBasicGroupII": None}), {"B2", "C2", "BI2"}, [], None, None),
    "Z5": ("C26-12", "OR", "RatingType blank: building and BI rate 1.0 (Otherwise), contents on their own specific rate",
           edit(h.tree, Structure={"RatingType": None}), set(), [], None, None),
    "Z6": ("C26-12", "OR", "RatingType / SpecificGroupIRate sent on the Special Class: ignored (no branch)",
           edit(h.tree, SpecialClass={"RatingType": "Specific", "SpecificGroupIRate": "0.900"}), set(), [], h.tree, None),
    "M1": ("C26-13", "SC", "Severe at 9,999 sq ft: the Severe message, the specific Group II still priced", SC_G("Charleston", 9999), set(),
           [("ST", SEV)], None, None),
    "M2": ("C26-13", "SC", "High at 25,000 sq ft", SC_G("Aiken", 25000), set(), [("ST", HIGH)], None, None),
    "M3": ("C26-13", "SC", "Medium at 50,000 sq ft", SC_G("Abbeville", 50000), set(), [("ST", MED)], None, None),
    "M4": ("C26-13", "OK", "Severe at 9,999 sq ft (the wording with a final period)", gii("OK", "Entire State", 9999, "Entire State"), set(),
           [("ST", SEV)], None, None),
    "M5": ("C26-13", "MI", "Low (Alcona): never eligible (no period)", gii("MI", "Alcona", 99999, "Entire State"), set(), [("ST", LOW)], None, None),
    "M6": ("C26-13", "OH", "Low (Adams): the wording with a period", gii("OH", "Adams", 99999, "Entire State"), set(), [("ST", LOW)], None, None),
    "M7": ("C26-13", "FL", "Specific Group II on residential class 0311: FL building and contents non-residential messages",
           edit(gii("FL", "Entire State", 99999, "Inland"), Structure={"ClassCode": "0311"}, OccupClass={"ClassCode": "0311"}), set(),
           [("ST", NONRES), ("PP", NONRES)], None, None),
    "M8": ("C26-13", "DC", "Class rating, class 0074 'Up to 10 Units': the fraternity message",
           edit(lambda: h.tree(j="DC", rt="Class"), Structure={"ClassCode": "0074", "ClassificationDescription": FRAT_DESC}), set(),
           [("ST", FRAT)], None, None),
    "M8b": ("C26-13", "DC", "the same Specific: silent",
            edit(lambda: h.tree(j="DC"), Structure={"ClassCode": "0074", "ClassificationDescription": FRAT_DESC}), set(), [], None, None),
    "S1": ("C26-14", "OR", "submitted RatingType 'Class' on the occupancy and the contents: overwritten by the copy (G1's dollars)",
           edit(h.tree, OccupClass={"RatingType": "Class"}, PersonalProperty={"RatingType": "Class"}), set(), [], h.tree, None),
    "S2": ("C26-14", "OR", "a submitted building BasicGroupIRate 0.500 survives (IsNull); BI still reads SpecificGroupIRate",
           edit(h.tree, Structure={"BasicGroupIRate": "0.500"}), set(), [], None, None),
    "K1": ("C26-15", "OR", "protection class 10 on a Specific building: no Specific dollar moves",
           edit(h.tree, Location={"ProtectClass": "10"}), set(), [], h.tree,
           (edit(lambda: h.tree(rt="Class"), Location={"ProtectClass": "10"}), lambda: h.tree(rt="Class"))),
    "K2": ("C26-15", "OR", "Group I territory 'Balance of State' (factor 1.0 vs Portland 0.499) on a Specific building: nothing moves",
           edit(h.tree, Location={"BasicGroupIRatingTerr": "Balance of State"}), set(), [], h.tree,
           (edit(lambda: h.tree(rt="Class"), Location={"BasicGroupIRatingTerr": "Balance of State"}), lambda: h.tree(rt="Class"))),
    "K3": ("C26-15", "OR", "the contents' fire-safe vault factor 0.5 submitted on a Specific building: nothing moves",
           edit(h.tree, PersonalProperty={"FireSafeVaultFactor": "0.5"}), set(), [], h.tree,
           (edit(lambda: h.tree(rt="Class"), PersonalProperty={"FireSafeVaultFactor": "0.5"}), lambda: h.tree(rt="Class"))),
    "K4": ("C26-15", "OR", "two apartment occupancies submitted as 'Class' on a SPECIFIC building: the building gate keeps the count 0, silent",
           two_apartments("Specific", "Class"), set(), [], None, None),
    "K4c": ("C26-15", "OR", "the same Class-rated, nothing submitted on the occupancies: their RatingType is copied AFTER the count runs, "
                            "so the count is 0 and the message is silent (as written)",
            two_apartments("Class"), set(), [], None, None),
    "K4d": ("C26-15", "OR", "Class-rated with the occupancies' RatingType submitted 'Class': ISO counts 0 and is silent; since "
                            "chunk 28 C28-08 (OI-125) ours does not read a submitted value its rules write, so silent too",
            two_apartments("Class", "Class"), set(), [], None, None),
}


# ------------------------------------------------------------------ prediction

def core_prem(data):
    out = {}
    for parent, c in c2.coverage_records(data):
        out.setdefault(c.tag[len(P):], []).append(val(c, "Premium"))
    return out


def chunk_msgs(tagged):
    out = collections.Counter()
    for t, y in tagged:
        for f in FRAGS:
            if f in y:
                out[(t, f)] += 1
    return out


def rate(build, j):
    req = t2.state_req(t2.m20.payload(build()), j)
    TAGGED.clear()
    data, ip = cmp.rate(req)
    return req, data, ip, [(lvl(t), y) for t, y in TAGGED]


def predict(cid):
    task, j, label, build, zero, must, ref, comp = CASES[cid]
    req, data, ip, tagged = rate(build, j)
    rates, prem, bad = c2.derive(data, j)
    for label_, v in SUBMITTED.get(cid, {}).items():           # an IsNull-guarded submitted rate: the rule never runs
        bad = [b_ for b_ in bad if not b_.startswith(f"{label_} hand")]
        e = val(rc1.find(data, P + "Structure")[0], "BasicGroupIRate")
        if not m.same(v, e):
            bad.append(f"{label_} submitted {v} engine {e}")
    lines = [f"      rates by hand = engine: {[(l_, str(hv)) for l_, hv, _ in rates]}"]
    for key, vs in prem.items():
        if any(not m.same(v[1], 0) for v in vs) or any(k_ in key for k_ in [CORE[z] for z in zero]):
            lines.append(f"      {key[-60:]:60s} predicted {[str(v[0]) for v in vs]}  engine {[v[1] for v in vs]}")
    for z in zero:
        got = [v[1] for k, vs in prem.items() if k.endswith(CORE[z]) for v in vs]
        if not got or not all(m.same(g, 0) for g in got):
            bad.append(f"{CORE[z]} predicted $0, engine {got}")
    if cid == "Z5":
        st = rc1.find(data, P + "Structure")[0]
        lines.append(f"      blank RatingType: building rate {val(st, 'BasicGroupIRate')}, contents {val(rc1.find(data, P + 'PersonalProperty')[0], 'BasicGroupIRate')}, "
                     f"BI {val(rc1.find(data, P + 'BusinessIncome')[0], 'BasicGroupIRate')}")
    if cid == "S1":
        lines.append(f"      copies after rating: occupancy {val(rc1.find(data, P + 'OccupClass')[0], 'RatingType')}, contents "
                     f"{val(rc1.find(data, P + 'PersonalProperty')[0], 'RatingType')}")
    if cid in ("K4", "K4c"):
        lines.append(f"      AptsWOMercOccupCnt {val(rc1.find(data, P + 'Structure')[0], 'AptsWOMercOccupCnt')}")
    if ref is not None:
        _, rdata, _, _ = rate(ref, j)
        a, b_ = core_prem(data), core_prem(rdata)
        moved = {k: (b_.get(k), v) for k, v in a.items() if v != b_.get(k)}
        lines.append(f"      equal to the reference policy on every core premium: {'yes' if not moved else moved}")
        if moved:
            bad.append("moved against the reference")
    if comp is not None:
        _, ca, _, _ = rate(comp[0], j)
        _, cb, _, _ = rate(comp[1], j)
        a, b_ = core_prem(ca), core_prem(cb)
        moved = {k: (b_.get(k), v) for k, v in a.items() if v != b_.get(k)}
        lines.append(f"      the same change on a Class building moves {len(moved)} records: {list(moved.items())[:3]}")
        if not moved:
            bad.append("the competing class tree does not move: the case cannot discriminate")
    want = collections.Counter((L[a], f) for a, f in must)
    got = chunk_msgs(tagged)
    mbad = [f"{t.replace(P, '')}: {f} fired {got[(t, f)]}, predicted {want[(t, f)]}" for t, f in set(want) | set(got) if want[(t, f)] != got[(t, f)]]
    print(f"{cid:4s} {task} {j} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS ' + '; '.join((bad + mbad)[:4])}")
    print(f"      messages predicted {sorted((t.replace(P, ''), f) for t, f in want.elements())}")
    print("\n".join(lines[:14]))
    if bad or mbad:
        FAIL.append(cid)
    return req, data, {k: [v[0] for v in vs] for k, vs in prem.items()}


def live(client, raas_mod, cid, req, data, preds):
    task, j, label, build, zero, must, ref, comp = CASES[cid]
    (gc.OUT / f"chunk26_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:4s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk26_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    TAGGED.clear()
    data2, ip = cmp.rate(req)
    ours = collections.Counter((lvl(t), y) for t, y in TAGGED)
    isos = collections.Counter(iso_tagged(resp))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data2)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for key, want in preds.items():
        tag = key.split("/")[1]
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, tag) if v is not None)
        w = sorted(D(str(v)) for v in want if not isinstance(v, str))
        if iso != w:
            pbad.append((key, iso, w))
    wantm = collections.Counter((L[a], f) for a, f in must)
    isof = chunk_msgs(list(isos.elements()))
    mreq = [f"{t.replace(P, '')}: {f} ISO {isof[(t, f)]}, predicted {wantm[(t, f)]}" for t, f in set(wantm) | set(isof) if wantm[(t, f)] != isof[(t, f)]]
    ok = not dd and not pbad and ours == isos and not mreq
    if not ok and cid in KNOWN and not dd and not pbad and all(KNOWN[cid][1] in y for (t, y) in (ours - isos) | (isos - ours)):
        print(f"  {cid:4s} KNOWN ({KNOWN[cid][0]}): every premium equal; ours raises '{KNOWN[cid][1]}...' and ISO does not "
              f"(ISO's count 0): recorded, messages only")
        return
    print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: records as predicted {'yes' if not pbad else 'NO'}; {len(ipr) - len(dd)} of {len(ipr)} "
          f"premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
          + (f"; against the prediction: {mreq}" if mreq else "")
          + "".join(f"\n        predicted {k[-55:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for k, i_, w_ in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + "".join(f"\n        ISO only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (isos - ours).items())
          + "".join(f"\n        ours only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (ours - isos).items()))
    if not ok:
        FAIL.append(f"{cid} live")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = [c for c in CASES if not a.cases or c in a.cases.split(",")]
    got = {}
    for i, cid in enumerate(cs, 1):
        progress(i, len(cs), f"predict {cid}")
        try:
            got[cid] = predict(cid)
        except Exception as exc:
            print(f"{cid}: RAISED {type(exc).__name__}: {str(exc)[:240]}")
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (records as predicted, every premium field for field, every (level, message)):")
        for i, cid in enumerate(cs, 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                live(client, raas_mod, cid, *got[cid])
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C26-12..C26-15): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
