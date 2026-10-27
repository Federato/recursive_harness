#!/usr/bin/env python3
"""Chunk 26, RC-2 (C26-07..C26-11): Specific and Tentative golden cases. Live ISO.

How each figure is derived before it runs:
  * every Specific / Tentative / One-Term Group I rate and Specific Group II rate by 234_'s hand models (read from the
    rule text of the state that runs it), checked against the engine first
  * every premium of the building, contents and BI coverage records by 174_'s independent evaluator on that state's own
    SetPremium rule (the parent values it reads -- LOI, deductible, cause-of-loss factors -- are chunks 1-8's, ISO-confirmed)
  * a COMPETING reading per case, priced the same way, so ISO's answer can match only one:
      G1 / G2  the class rate (the same building rated Class)
      G3       contents on the BUILDING's specific rate instead of their own
      S1-S3    Group II rated Class instead of Specific
      C1       CA One-Term Loss Cost with BI on the building's specific rate (the Specific reading) instead of 1.0
  Then every premium is compared with ISO field for field, and the messages.

Cases (OR unless named; ISO at 2026-09-17):
  G1  C26-07  building Specific Group I 0.300 (class rate 0.239), contents 0.200, BI
  G2  C26-08  the same Tentative (+ the Tentative Rate form record)
  G3  C26-09  contents' own rate 0.450 above the building's 0.300; BI on the building's
  S1  C26-10  SC Severe (Charleston), 10,000 sq ft (at the threshold: eligible), Specific Group II 0.060 / 0.050
  S2  C26-10  SC High (Aiken), 25,001 sq ft
  S3  C26-10  SC Medium (Abbeville), 50,001 sq ft
  C1  C26-11  CA One-Term Loss Cost: building and contents as Specific, BI's rate 1.0 as written

    python scripts/cf/235_chunk26_rc2.py [--live] [--cases G1,C1]
"""
from __future__ import annotations

import argparse
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

h = import_module("234_chunk26_rc1")
m, rc1, rep, cmp = h.m, h.rc1, h.rep, h.cmp
t2 = import_module("220_chunk23_rc2")
r11, gc = m.r11, m.gc
P, D, val, d = h.P, Decimal, h.val, h.d
FAIL = []
r11.NUMERIC |= {"SpecificGroupIRate", "SpecificGroupIIRate", "SquareFootageOfBuilding"}
OWN = ("Structure", "PersonalProperty", "BusinessIncome")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ trees

def gii_tree(level, county, sqft):
    def b():
        sub = h.tree(j="SC", st_over={"RatingTypeBasicGroupII": "Specific", "SpecificGroupIIRate": "0.060", "SquareFootageOfBuilding": str(sqft)})
        at = m.at(sub)
        at[P + "PersonalProperty"]["SpecificGroupIIRate"] = "0.050"
        at[P + "Location"]["GeographicWindHazardLevelTerritory"] = county
        # the BCEG factor (and the class Group II rate) key on the location's Group II territory, which 192_'s portable sets
        # only in OR (chunk 24 met the same gap). SC's BCEG table has 001 / Beach / Inland / Seacoast, its Group II rate table only
        # Beach / Inland / Seacoast: '001' made ISO refuse the class base-rate lookup, which runs even on a Specific Group II
        # building (first sent 2026-10-02; ours priced: OI-99), so 'Inland'
        at[P + "Location"]["BasicGroupIIRatingTerr"] = "Inland"
        for k in ("Structure", "PersonalProperty"):
            at[P + k].pop("BasicGroupIIRate", None)         # 192_'s portable submits one outside OR (IsNull-guarded)
        return sub
    return b


def with_(build, **edits):
    """the competing reading's tree: the same policy with the given (record: fields) edits."""
    def b():
        sub = build()
        for rec, f in edits.items():
            m.at(sub)[P + rec].update(f)
        return sub
    return b


G1 = lambda: h.tree()
CASES = {
    "G1": ("C26-07", "OR", "building Specific 0.300 (class 0.239), contents 0.200, BI", G1,
           ("the class rate", with_(G1, Structure={"RatingType": "Class"}))),
    "G2": ("C26-08", "OR", "the same Tentative (+ the Tentative Rate form)", lambda: h.tree(rt="Tentative"),
           ("the class rate", with_(G1, Structure={"RatingType": "Class"}))),
    "G3": ("C26-09", "OR", "contents' own 0.450 above the building's 0.300; BI on the building's", lambda: h.tree(pp_s1="0.450"),
           ("contents on the building's rate", lambda: h.tree(pp_s1="0.300"))),
    "S1": ("C26-10", "SC", "Severe (Charleston), 10,000 sq ft, Specific Group II 0.060 / 0.050", gii_tree("Severe", "Charleston", 10000),
           ("Group II rated Class", with_(gii_tree("Severe", "Charleston", 10000), Structure={"RatingTypeBasicGroupII": "Class"}))),
    "S2": ("C26-10", "SC", "High (Aiken), 25,001 sq ft", gii_tree("High", "Aiken", 25001),
           ("Group II rated Class", with_(gii_tree("High", "Aiken", 25001), Structure={"RatingTypeBasicGroupII": "Class"}))),
    "S3": ("C26-10", "SC", "Medium (Abbeville), 50,001 sq ft", gii_tree("Medium", "Abbeville", 50001),
           ("Group II rated Class", with_(gii_tree("Medium", "Abbeville", 50001), Structure={"RatingTypeBasicGroupII": "Class"}))),
    "C1": ("C26-11", "CA", "One-Term Loss Cost: building / contents as Specific, BI rate 1.0 as written", lambda: h.tree(j="CA", rt="One-Term Loss Cost"),
           ("BI on the building's specific rate (the Specific reading)", lambda: h.tree(j="CA", rt="Specific"))),
}


# ------------------------------------------------------------------ prediction

_SP = {}


def setpremium(j, tag):
    """the SetPremium body a record runs in state j: the state's own rule, else its countrywide parent's."""
    key = (j, tag)
    if key not in _SP:
        name = tag[len(P):]
        body = None
        for pk in (book(j).state.package.content, book(j).parent.package.content):
            f = pk / "Rules" / f"{P}{name}Rules.Rule.xml"
            if f.exists():
                body = m.cen.set_premium(f.read_text(encoding="utf-8-sig"))
                if body:
                    break
        _SP[key] = body
    return _SP[key]


def book(j):
    return h.book_for(j, h.ASOF)


def coverage_records(data):
    """every premium-bearing record directly under a building, its contents or its BI (the chains this chunk moves)."""
    out = []
    for parent in OWN:
        for pn in rc1.find(data, P + parent):
            for c in pn.children:
                core = re.fullmatch(P + r"(StructureBuilding|PersonalPropertyPrsnlProp|BusinessIncome)(BasicGroupI|BasicGroupII|Broad|Special)Coverage", c.tag)
                if c.first("Premium") is not None and core:
                    out.append((parent, c))
    return out


def derive(data, j):
    """(rates by hand vs engine, premiums by the state's own rule)."""
    bad, rates, prem = [], [], {}
    for st in rc1.find(data, P + "Structure"):
        for label, hv, e in (("building BGI", h.hand_building(j, st), val(st, "BasicGroupIRate")),
                             ("building BGII", h.hand_bgii(j, st, "st"), val(st, "BasicGroupIIRate"))):
            if hv is not None:
                rates.append((label, hv, e))
        for pp in rc1.find(st, P + "PersonalProperty"):
            for label, hv, e in (("contents BGI", h.hand_contents(pp), val(pp, "BasicGroupIRate")),
                                 ("contents BGII", h.hand_bgii(j, pp, "pp"), val(pp, "BasicGroupIIRate"))):
                if hv is not None:
                    rates.append((label, hv, e))
        for bi in rc1.find(st, P + "BusinessIncome"):
            hb = h.hand_bi(j, bi)                          # BI's rule names only Specific / Tentative: One-Term -> Otherwise 1.0
            for label, hv, e in (("BI BGI", hb, val(bi, "BasicGroupIRate")), ("BI BGII", h.hand_bgii(j, bi, "bi"), val(bi, "BasicGroupIIRate"))):
                if hv is not None:
                    rates.append((label, hv, e))
    for label, hv, e in rates:
        if not m.same(hv, e):
            bad.append(f"{label} hand {hv} engine {e}")
    for parent, c in coverage_records(data):
        body = setpremium(j, c.tag)
        if not body:
            continue
        try:
            ev = m.r16.hand(body, c)
        except Exception as exc:
            ev = f"evaluator {type(exc).__name__}"
        if isinstance(ev, str) and re.fullmatch(r"-?\d+(\.\d+)?", ev):
            ev = D(ev)                                 # a constant premium ('0.0') the evaluator returns as text
        e = val(c, "Premium")
        key = f"{parent}/{c.tag[len(P):]}"
        prem.setdefault(key, []).append((ev, e))
        if isinstance(ev, str) or not m.same(ev, e):
            bad.append(f"{key} evaluator {ev} engine {e}")
    return rates, prem, bad


def predict(cid):
    task, j, label, build, (alt_label, alt_build) = CASES[cid]
    req = t2.state_req(t2.m20.payload(build()), j)
    data, ip = cmp.rate(req)
    rates, prem, bad = derive(data, j)
    a_req = t2.state_req(t2.m20.payload(alt_build()), j)
    a_data, _ = cmp.rate(a_req)
    _, a_prem, _ = derive(a_data, j)
    moved = {k: ([str(v[0]) for v in vs], [str(v[0]) for v in a_prem.get(k, [])]) for k, vs in prem.items()
             if [str(v[0]) for v in vs] != [str(v[0]) for v in a_prem.get(k, [])]}
    lines = [f"      rates by hand = engine: {[(l_, str(hv)) for l_, hv, _ in rates]}"]
    for k, vs in prem.items():
        if any(not m.same(v[1], 0) for v in vs):
            lines.append(f"      {k[-62:]:62s} predicted {[str(v[0]) for v in vs]}  engine {[v[1] for v in vs]}")
    lines.append(f"      competing reading ({alt_label}) moves {len(moved)} records: "
                 + "; ".join(f"{k.split('/')[-1][-40:]} {a} vs {b}" for k, (a, b) in list(moved.items())[:5]))
    if cid == "G2":
        tent = rc1.find(rc1.find(data, P + "Structure")[0], P + "TentativeRate")
        lines.append(f"      Tentative Rate form record: {'attached' if tent else 'ABSENT'}")
        if not tent:
            bad.append("no Tentative Rate form")
    if not moved:
        bad.append("the competing reading moves no dollar: the case cannot discriminate")
    print(f"{cid} {task} {j} {label}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:4])}")
    print("\n".join(lines))
    if bad:
        FAIL.append(cid)
    preds = {k: [v[0] for v in vs] for k, vs in prem.items()}
    alts = {k: [v[0] for v in vs] for k, vs in a_prem.items()}
    return req, data, ip, preds, alts


def live(client, raas_mod, cid, req, data, ip, preds, alts):
    (gc.OUT / f"chunk26_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk26_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad, alt_hits = [], 0
    for key, want in preds.items():
        tag = key.split("/")[1]
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, tag) if v is not None)
        w = sorted(D(str(v)) for v in want if not isinstance(v, str))
        a = sorted(D(str(v)) for v in alts.get(key, []) if not isinstance(v, str))
        if iso != w:
            pbad.append((key, iso, w))
        if a != w and iso == a:
            alt_hits += 1
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not dd and not pbad and mi == mo
    print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums equal; messages {'equal' if mi == mo else 'DIFFER'}; "
          f"records where ISO matches the competing reading instead: {alt_hits}"
          + "".join(f"\n      predicted {k[-60:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for k, i_, w_ in pbad[:6])
          + "".join(f"\n      {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + (f"\n      ISO only {sorted(mi - mo)[:3]}\n      ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
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
        print("\nISO live at 2026-09-17 (records as predicted, every premium field for field, messages):")
        for i, cid in enumerate(cs, 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                live(client, raas_mod, cid, *got[cid])
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C26-07..C26-11): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
