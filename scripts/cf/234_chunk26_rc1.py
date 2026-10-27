#!/usr/bin/env python3
"""Chunk 26, RC-1 (C26-02..C26-06): Specific and Tentative rating, evidence and plumbing. No ISO calls.

The branch, read from the rule text (CW 2026 V01 unless named):
  building Group I    Class: the class chain (chunks 1-3). Specific / Tentative (CA also "One-Term Loss Cost"):
                      CW / CA  r3(r3(SpecificGroupIRate x LCM) x SprinklerLeakageNotExcludedFactor x roof ACV factor)
                      FL NY WV and MO (CW 2023 V02)  r3(SpecificGroupIRate x sprinkler factor x LCM)   (no roof factor)
                      KY  r3(SpecificGroupIRate x sprinkler factor x LCM x roof ACV factor)
                      anything else: 1.0
  contents Group I    RatingType is COPIED from the building (Occupancy and Personal Property: SetRatingType); any value but
                      "Class" -> r3(the CONTENTS' OWN SpecificGroupIRate x LCM x its own sprinkler factor); blank -> 0
  BI Group I          r3(r3(r3(the BUILDING's SpecificGroupIRate x BI LCM) x the building's sprinkler factor) x BGI adjustment)
                      (after the operational-unit branch); MO (V02): r3(the building's BasicGroupIRate x BGI adjustment)
  Group II            countrywide: class only. The 36 states with RatingTypeBasicGroupII: "Class" -> the class chain;
                      "Specific" -> r3(r3(r3(SpecificGroupIIRate x LCM) x BCEG) x (1 - wind mitigation credits)) (BI: the
                      building's SpecificGroupIIRate x BGII adjustment); anything else, blank included -> 0.0
  Tentative           also attaches the Tentative Rate form record (removed otherwise)

    python scripts/cf/234_chunk26_rc1.py [--skip-replay]

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import copy
import csv
import hashlib
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

from cf_engine.resolve import book_for                                   # noqa: E402

m = import_module("219_chunk23_rc1")
rc1, rep, cmp = m.rc1, m.rep, m.cmp
s18 = import_module("164_chunk14_c14-18_all_states")
P, D, ASOF = m.P, Decimal, m.ASOF
r, val, d = m.r, m.val, m.d
FAIL = []
RES = ROOT / "results"
SPEC = ("Specific", "Tentative", "One-Term Loss Cost")
CW = book_for("OR", ASOF).parent.package.content
RT = re.compile(r'"(RatingType(?:BasicGroupII)?)"\s*:\s*"(Specific|Tentative|One-Term Loss Cost)"')


def progress(what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{mm}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def anc(n, tag):
    while n is not None and n.tag != P + tag:
        n = n.parent
    return n


def rule_text(pkg, f):
    p = pkg / "Rules" / f"{P}{f}Rules.Rule.xml"
    return p.read_text(encoding="utf-8-sig") if p.exists() else ""


def rule(t, name):
    mt = re.search(rf'<rul:Rule Name="{name}".*?</rul:Rule>', t, re.S)
    return mt.group(0) if mt else ""


def effective_rule(j, f, name):
    """the state's own rule if its package carries it, else its countrywide parent's."""
    b = book_for(j, ASOF)
    return rule(rule_text(b.state.package.content, f), name) or rule(rule_text(b.parent.package.content, f), name)


# ------------------------------------------------------------------ hand models

def bgi_variant(j):
    """which shape of the building's Specific branch the state runs (read from the rule text, not assumed)."""
    body = effective_rule(j, "Structure", "SetBasicGroupIRate")
    seg = body[body.find('FromDataDef="SpecificGroupIRate"') - 600: body.find('FromDataDef="SpecificGroupIRate"') + 700]
    inner = re.search(r'<rul:Product DecimalPlaces="3">\s*<rul:FirstValue[^>]*FromDataDef="SpecificGroupIRate"', seg) is not None
    roof = "LimitationsOnCovForRoofSurfacingACVFactor" in seg
    types = {t for t in SPEC if f"<rul:Constant Type=\"string\">{t}</rul:Constant>" in body}
    return ("nested" if inner else "single"), roof, types


def hand_building(j, st):
    shape, roof, types = bgi_variant(j)
    if val(st, "RatingType") == "Class":
        return None
    if val(st, "RatingType") not in types:
        return D("1.0")                                # Otherwise (blank or a type the state does not name) -> 1.0
    s, lcm, slne = d(st, "SpecificGroupIRate"), d(st, "LossCostMultiplier"), d(st, "SprinklerLeakageNotExcludedFactor")
    rf = d(st, "LimitationsOnCovForRoofSurfacingACVFactor") if roof else D(1)
    if shape == "nested":
        return r(r(s * lcm, 3) * slne * rf, 3)
    return r(s * slne * lcm * rf, 3)


def hand_contents(pp):
    if val(pp, "RatingType") == "Class":
        return None                                    # a blank copy is "not Class": the specific branch
    return r(d(pp, "SpecificGroupIRate") * d(pp, "LossCostMultiplier") * d(pp, "SprinklerLeakageNotExcludedFactor"), 3)


def hand_bi(j, bi):
    st = anc(bi, "Structure")
    if (val(bi, "MaxPeriod") == "Yes" or val(bi, "MonthlyLimitOfIndemnity") not in (None, "Not Applicable")
            or val(bi, "CovType") == "Extra Expense Only") and val(st, "BldgIncludedInOperationalUnit") == "Yes":
        return None                                    # the operational-unit branch (chunk 5), not this one
    body = effective_rule(j, "BusinessIncome", "SetBasicGroupIRate")
    if "bldgBasicGroupIRate" in body:                  # MO (V02): the building's rate x the adjustment, any rating type
        return r(d(st, "BasicGroupIRate") * d(bi, "BGIBaseRateAdjustmentFactor"), 3)
    if val(st, "RatingType") == "Class":
        return None
    if val(st, "RatingType") not in ("Specific", "Tentative"):
        return D("1.0")                                # Otherwise (blank, CA One-Term) -> 1.0
    x = r(r(d(st, "SpecificGroupIRate") * d(bi, "LossCostMultiplier"), 3) * d(st, "SprinklerLeakageNotExcludedFactor"), 3)
    return r(x * d(bi, "BGIBaseRateAdjustmentFactor"), 3)


def hand_bgii(j, node, kind):
    """Group II for a Specific RatingTypeBasicGroupII (states that carry the rule); None where the CW class chain runs."""
    f = {"st": "Structure", "pp": "PersonalProperty", "bi": "BusinessIncome"}[kind]
    body = effective_rule(j, f, "SetBasicGroupIIRate")
    if "RatingTypeBasicGroupII" not in body:
        return None
    st = anc(node, "Structure")
    rt = val(st, "RatingTypeBasicGroupII")
    if rt == "Class":
        return None
    if rt != "Specific":
        return D("0")                                  # the Otherwise branch: blank / anything else -> 0.0
    s2 = d(st if kind == "bi" else node, "SpecificGroupIIRate")
    if "PlasticGreenhouseLostCostFactor" in body[body.find("SpecificGroupIIRate") - 300:]:
        # NY: (rate + the building's plastic-greenhouse factor) x LCM, then x the windstorm protective devices factor
        # (building) or the BGII adjustment (BI); contents one rounding, no third factor
        x = (s2 + d(st, "PlasticGreenhouseLostCostFactor")) * d(node, "LossCostMultiplier")
        if kind == "st":
            return r(r(x, 3) * d(node, "WindstormProtectiveDevicesFactor"), 3)
        if kind == "bi":
            return r(r(x, 3) * d(node, "BGIIBaseRateAdjustmentFactor"), 3)
        return r(x, 3)
    x = r(r(s2 * d(node, "LossCostMultiplier"), 3) * d(node, "BCEGFactor"), 3)
    if kind == "bi":
        return r(x * d(node, "BGIIBaseRateAdjustmentFactor"), 3)
    return r(x * (1 - d(node, "WindstormLossMitigationCredits")), 3)


# ------------------------------------------------------------------ C26-02: replay the stored evidence

def evidence_files():
    out = []
    for p in sorted(RES.rglob("*request*.json")):
        if "failed-calls" in p.parts:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if not RT.search(t):
            continue
        rp = p.with_name(p.name.replace("request", "response"))
        out.append((p, rp if rp.exists() else None, t))
    return out


def replay():
    progress("C26-02  REPLAY THE STORED SPECIFIC / TENTATIVE EVIDENCE (no ISO calls)")
    files = evidence_files()
    seen, uniq = {}, []
    for p, rp, t in files:
        try:
            req = json.loads(t)
        except Exception:
            continue
        body = req.get("body", req)
        h = hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()
        if h in seen:
            continue
        seen[h] = p
        uniq.append((p, rp, req))
    with_resp = [u for u in uniq if u[1] is not None]
    print(f"    {len(files)} stored requests with a Specific / Tentative rating type; {len(uniq)} distinct; {len(with_resp)} with an ISO response")
    tally = collections.defaultdict(lambda: collections.Counter())
    bad, zero_gii, hand_bad, notes = [], [], [], collections.Counter()
    for i, (p, rp, req) in enumerate(with_resp, 1):
        if i == 1 or i % 25 == 0 or i == len(with_resp):
            progress(f"  [{i}/{len(with_resp)}] {p.relative_to(RES)}")
        try:
            resp = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:
            notes["unreadable response"] += 1
            continue
        j = (re.search(r"Commercial Property ([A-Z]{2})", json.dumps(req.get("body", req).get("SchemeKeys", {}))) or [None, "?"])[1]
        try:
            data, ip = cmp.rate(req)
        except Exception as exc:
            bad.append((str(p.relative_to(RES)), f"engine raised {type(exc).__name__}: {str(exc)[:120]}"))
            tally[j]["engine raised"] += 1
            continue
        iso, ours = rep.iso_prem(resp), rep.our_prem(data)
        if not iso:
            notes["response carries no premiums (an ISO error body)"] += 1
            continue
        diff = [(k, v, ours.get(k)) for k, v in iso.items() if not cmp.same(v, ours.get(k))]
        mi, mo = cmp.iso_messages(resp), set(ip.messages)
        tally[j]["policies"] += 1
        tally[j]["premiums"] += len(iso)
        tally[j]["agree"] += not diff
        tally[j]["messages equal"] += mi == mo
        if diff:
            bad.append((str(p.relative_to(RES)), diff[:3]))
        submitted = '"BasicGroupIRate"' in json.dumps(req)
        for st in rc1.find(data, P + "Structure"):
            if val(st, "RatingType") in SPEC:
                tally[j][f"building {val(st, 'RatingType')}"] += 1
                hv = None if submitted else hand_building(j, st)
                if hv is not None:
                    tally[j]["hand building"] += 1
                    if not m.same(hv, val(st, "BasicGroupIRate")):
                        hand_bad.append((j, "building", hv, val(st, "BasicGroupIRate"), str(p.relative_to(RES))))
            for pp in rc1.find(st, P + "PersonalProperty"):
                hv = None if submitted else hand_contents(pp)
                if hv is not None:
                    tally[j]["hand contents"] += 1
                    if not m.same(hv, val(pp, "BasicGroupIRate")):
                        hand_bad.append((j, "contents", hv, val(pp, "BasicGroupIRate"), str(p.relative_to(RES))))
            for bi in rc1.find(st, P + "BusinessIncome"):
                hv = None if submitted else hand_bi(j, bi)
                if hv is not None:
                    tally[j]["hand BI"] += 1
                    if not m.same(hv, val(bi, "BasicGroupIRate")):
                        hand_bad.append((j, "BI", hv, val(bi, "BasicGroupIRate"), str(p.relative_to(RES))))
            for kind, nodes in (("st", [st]), ("pp", rc1.find(st, P + "PersonalProperty")), ("bi", rc1.find(st, P + "BusinessIncome"))):
                for n in nodes:
                    hv = hand_bgii(j, n, kind)
                    if hv is not None:
                        tally[j]["hand Group II"] += 1
                        if not m.same(hv, val(n, "BasicGroupIIRate")):
                            hand_bad.append((j, f"Group II {kind}", hv, val(n, "BasicGroupIIRate"), str(p.relative_to(RES))))
            g2 = [k for k, v in iso.items() if "BuildingBasicGroupIICoverage" in k and k.endswith("/Premium") and m.same(v, 0)]
            if g2 and val(st, "RatingType") in SPEC:
                zero_gii.append((j, str(p.relative_to(RES)), val(st, "RatingTypeBasicGroupII"), val(st, "BasicGroupIIRate"),
                                 val(st, "CovType"), val(st, "CauseOfLossToUse")))
        if submitted:
            notes["requests submitting BasicGroupIRate (the rate rule is skipped: hand check not applied)"] += 1
    print(f"    {'state':5s} {'policies':>8s} {'agree':>6s} {'msgs=':>6s} {'premiums':>8s}  building types / hand checks")
    tot = collections.Counter()
    for j, c in sorted(tally.items()):
        tot.update(c)
        types = {k: v for k, v in c.items() if k.startswith(("building ", "hand ", "engine"))}
        print(f"    {j:5s} {c['policies']:8d} {c['agree']:6d} {c['messages equal']:6d} {c['premiums']:8d}  {types}")
    print(f"    TOTAL {tot['policies']} policies, {tot['premiums']} ISO premiums; every premium equal on {tot['agree']}; messages equal on {tot['messages equal']}")
    for k, v in notes.items():
        print(f"    note: {v} {k}")
    for b in bad[:8]:
        print(f"      DIFFER {b}")
    check(not bad, f"every stored Specific / Tentative policy re-rates with every premium equal to ISO ({tot['agree']} of {tot['policies']})")
    hb = tot["hand building"] + tot["hand contents"] + tot["hand BI"] + tot["hand Group II"]
    for h in hand_bad[:8]:
        print(f"      HAND {h}")
    check(not hand_bad and hb > 0, f"hand = engine on every Specific building ({tot['hand building']}), contents ({tot['hand contents']}), BI ({tot['hand BI']}) "
          f"Group I rate and every Group II rate under a RatingTypeBasicGroupII rule ({tot['hand Group II']})")
    print(f"    building Group II premium $0 at ISO on a Specific building: {len(zero_gii)}")
    why = collections.Counter((z[2], z[4], z[5]) for z in zero_gii)
    for k, v in why.most_common():
        print(f"      {v:3d}  RatingTypeBasicGroupII {k[0]!r}, building CovType {k[1]!r}, cause {k[2]!r}")
    return tally, zero_gii


def failed_calls():
    progress("C26-02  THE FAILED CALLS (ISO refused; ours re-run)")
    out = collections.Counter()
    for dd in sorted((RES / "failed-calls").iterdir()):
        rq = dd / "request.json"
        if not rq.exists():
            continue
        t = rq.read_text(encoding="utf-8", errors="replace")
        if not RT.search(t):
            continue
        rs = (dd / "response.txt").read_text(encoding="utf-8", errors="replace") if (dd / "response.txt").exists() else ""
        mt = re.search(r"Matrix: (\w+)", rs) or re.search(r"Element value \\u0027(\w+)\\u0027", rs)
        why = mt.group(1) if mt else rs[:60]
        try:
            req = json.loads(t)
            cmp.rate(req)
            ours = "ours prices"
        except Exception as exc:
            ours = f"ours raises {type(exc).__name__}"
        out[(why, ours)] += 1
    for (why, ours), n in out.most_common():
        print(f"    {n:3d}  ISO refused on {why!r:55s} {ours}")
    rt = [w for (w, _) in out if "Rating" in w or "Specific" in w]
    check(not rt, "no ISO refusal names a rating-type table or field (each is a missing row elsewhere or a payload type: OI-99 / OI-103's family)")


# ------------------------------------------------------------------ trees

def tree(j="OR", rt="Specific", s1="0.300", pp_s1="0.200", st_over=None, pp_over=None, bi_over=None):
    sub = m.portable(j, "Special")
    at = m.at(sub)
    at[P + "Structure"].update({"RatingType": rt, "SpecificGroupIRate": s1, **(st_over or {})})
    if pp_s1 is not None:
        at[P + "PersonalProperty"]["SpecificGroupIRate"] = pp_s1
    at[P + "PersonalProperty"].update(pp_over or {})
    at[P + "BusinessIncome"].update(bi_over or {})
    return sub


def rated(sub, j="OR"):
    data, ip, err = m.rated(sub, j)
    if err:
        check(False, f"engine raised {err}")
    return data


def branch_map():
    progress("C26-03  THE BRANCH MAP ON REAL TREES")
    out = {}
    for rt in ("Class", "Specific", "Tentative"):
        data = rated(tree(rt=rt))
        if data is None:
            return
        out[rt] = data
        st = rc1.find(data, P + "Structure")[0]
        oc = rc1.find(data, P + "OccupClass")[0]
        pp = rc1.find(data, P + "PersonalProperty")[0]
        tent = rc1.find(st, P + "TentativeRate")
        print(f"    {rt:9s}: Structure {val(st, 'RatingType')}, OccupClass {val(oc, 'RatingType')}, PersonalProperty {val(pp, 'RatingType')}; "
              f"Tentative Rate form {'attached' if tent else 'absent'}; RatingIdentificationCode {val(st, 'RatingIdentificationCode')}; "
              f"BGI rate {val(st, 'BasicGroupIRate')}")
        check(val(oc, "RatingType") == rt and val(pp, "RatingType") == rt, f"{rt}: the occupancy and the contents COPY the building's RatingType")
        check(bool(tent) == (rt == "Tentative"), f"{rt}: the Tentative Rate form attaches only on Tentative")
    cls, spec = out["Class"], out["Specific"]
    st_c, st_s = rc1.find(cls, P + "Structure")[0], rc1.find(spec, P + "Structure")[0]
    codes = {rt: val(rc1.find(out[rt], P + "Structure")[0], "RatingIdentificationCode") for rt in out}
    cw_ids = {}
    for name in ("ScheduleRatedRatingIdentificationCode", "ClassRatedRatingIdentificationCode"):
        rows_ = list(csv.DictReader(open(CW / "Rate Tables" / f"{name}.RateTable.csv", encoding="utf-8-sig"))) if (CW / "Rate Tables" / f"{name}.RateTable.csv").exists() else []
        cw_ids[name] = rows_[0] if rows_ else None
    print(f"    rating identification codes {codes}; CW tables {cw_ids}")
    check(codes["Specific"] == codes["Tentative"] != codes["Class"],
          "Specific and Tentative share the schedule-rated identification code; Class has its own")
    hv = hand_building("OR", st_s)
    check(m.same(hv, val(st_s, "BasicGroupIRate")), f"OR (CW branch) Specific building Group I by hand {hv} = engine {val(st_s, 'BasicGroupIRate')}")
    classonly = ["BasicGroupIBaseRate", "ProtectionClassFactor", "BasicGroupIRatingTerrFactor"]
    print(f"    class-only fields, Class vs Specific building: {[(f, val(st_c, f), val(st_s, f)) for f in classonly]}")
    check(not m.same(val(st_c, "BasicGroupIRate"), val(st_s, "BasicGroupIRate")),
          "the Specific rate replaces the class chain (the class-only factors are not in the Specific formula; C26-15 moves each one)")
    return out


def contents_bi(out):
    progress("C26-04  CONTENTS AND BI ON A SPECIFIC BUILDING")
    data = out["Specific"]
    st = rc1.find(data, P + "Structure")[0]
    pp = rc1.find(data, P + "PersonalProperty")[0]
    bi = rc1.find(data, P + "BusinessIncome")[0]
    own = hand_contents(pp)
    bld = r(d(st, "SpecificGroupIRate") * d(pp, "LossCostMultiplier") * d(pp, "SprinklerLeakageNotExcludedFactor"), 3)
    print(f"    contents: own SpecificGroupIRate 0.200 -> {own}; the building's 0.300 would give {bld}; engine {val(pp, 'BasicGroupIRate')}")
    check(m.same(own, val(pp, "BasicGroupIRate")) and not m.same(own, bld), "contents price on their OWN SpecificGroupIRate (not the building's)")
    hb = hand_bi("OR", bi)
    print(f"    BI: the building's SpecificGroupIRate -> {hb}; engine {val(bi, 'BasicGroupIRate')}")
    check(m.same(hb, val(bi, "BasicGroupIRate")), "BI prices on the BUILDING's SpecificGroupIRate (BI has no rate of its own)")
    data2 = rated(tree(pp_s1=None))
    if data2 is not None:
        pp2 = rc1.find(data2, P + "PersonalProperty")[0]
        prem = [val(c, "Premium") for c in pp2.children if c.tag.endswith("BasicGroupICoverage")]
        print(f"    contents on a Specific building with NO SpecificGroupIRate of their own: rate {val(pp2, 'BasicGroupIRate')}, Group I premium {prem}")
        check(m.same(val(pp2, "BasicGroupIRate"), 0), "contents with no own specific rate on a Specific building rate 0 (a silent $0 Group I: RC-3 probes it live)")


def group_ii():
    progress("C26-05  SPECIFIC GROUP II: THE STATE LAYER")
    states, shapes = [], collections.Counter()
    thresholds = collections.defaultdict(set)
    for j in s18.STATES:
        body = effective_rule(j, "Structure", "SetBasicGroupIIRate")
        if "RatingTypeBasicGroupII" not in body:
            continue
        states.append(j)
        seg = body[body.find('FromDataDef="SpecificGroupIIRate"') - 500: body.find('FromDataDef="SpecificGroupIIRate"') + 900]
        shapes[tuple(sorted(set(re.findall(r'FromDataDef="(\w+)"', seg)) - {"SpecificGroupIIRate", "BasicGroupIIRate"}))] += 1
        t = rule_text(book_for(j, ASOF).state.package.content, "Structure") or ""
        for mm in re.finditer(r'<rul:Rule Name="(Do\w*BasicGroupII\w*|DoMessage\w*BGII\w*)".*?</rul:Rule>', t, re.S):
            lv = re.findall(r"<rul:Constant[^>]*>(Severe|High|Medium|Low)</rul:Constant>", mm.group(0))
            sq = re.findall(r'SquareFootageOfBuilding"[^/]*/>\s*<rul:Constant[^>]*>(\d+)</rul:Constant>', mm.group(0))
            if lv and sq:
                thresholds[(lv[0], sq[0])].add(j)
    print(f"    {len(states)} states rate Specific Group II: {' '.join(states)}")
    for k, v in shapes.items():
        print(f"      Specific branch reads {k} in {v} states")
    for k, v in sorted(thresholds.items()):
        print(f"      message threshold {k}: {len(v)} states")
    check(len(states) == 36, f"36 states carry RatingTypeBasicGroupII on the building ({len(states)})")
    progress("C26-05  OK ON A TREE: Specific, Class and blank Group II")
    for rt2, want0 in (("Specific", False), ("Class", False), (None, True)):
        sub = tree(j="OK", st_over={"RatingTypeBasicGroupII": rt2, "SpecificGroupIIRate": "0.050"} if rt2 else {"SpecificGroupIIRate": "0.050"})
        if rt2 is None:
            m.at(sub)[P + "Structure"].pop("RatingTypeBasicGroupII", None)
        m.at(sub)[P + "PersonalProperty"]["SpecificGroupIIRate"] = "0.040"
        for k in ("Structure", "PersonalProperty"):            # 192_'s portable SUBMITS a Group II rate outside OR (IsNull-guarded)
            m.at(sub)[P + k].pop("BasicGroupIIRate", None)
        data = rated(sub, "OK")
        if data is None:
            continue
        st = rc1.find(data, P + "Structure")[0]
        pp = rc1.find(data, P + "PersonalProperty")[0]
        bi = rc1.find(data, P + "BusinessIncome")[0]
        got = [(k, hand_bgii("OK", n, k), val(n, "BasicGroupIIRate")) for k, n in (("st", st), ("pp", pp), ("bi", bi))]
        print(f"    OK RatingTypeBasicGroupII {rt2!r}: (record, hand, engine) {got}")
        ok = all(h is None or m.same(h, e) for _, h, e in got)
        if want0:
            ok = ok and all(m.same(e, 0) for _, _, e in got)
        check(ok, f"OK {rt2!r}: Group II by hand = engine{' (blank -> 0.0 on building, contents and BI: chunk 2s silent zero)' if want0 else ''}")


def domains():
    progress("C26-06  DOMAINS")
    dt = CW / "Domain Tables"
    hits = {}
    for f in sorted(dt.glob("*.csv")):
        t = f.read_text(encoding="utf-8-sig", errors="replace")
        if "Specific" in t or "Tentative" in t:
            hits[f.name] = t.count("Specific"), t.count("Tentative")
    print(f"    CW domain tables naming Specific / Tentative: {hits}")
    rows_ = [x for x in csv.DictReader(open(dt / "DomainCovForm.DomainTable.csv", encoding="utf-8-sig"))] if (dt / "DomainCovForm.DomainTable.csv").exists() else []
    print(f"    DomainCovForm columns {list(rows_[0].keys()) if rows_ else None}; rows {len(rows_)}")
    for j in ("FL", "GA", "KS", "NY", "CA"):
        sd = book_for(j, ASOF).state.package.content / "Domain Tables"
        own = sorted(f.name for f in sd.glob("*.csv") if re.search(r"ClassCode|CovForm|RatingType", f.name)) if sd.exists() else []
        one = sum(f.read_text(encoding="utf-8-sig", errors="replace").count("One-Term Loss Cost") for f in sd.glob("*.csv")) if sd.exists() else 0
        print(f"    {j}: own class-code / cov-form / rating-type domains {own[:6]}; 'One-Term Loss Cost' mentions {one}")
    check(bool(hits), "the rating-type values are domain-driven (listed above)")
    progress("C26-06  CA ONE-TERM LOSS COST ON A TREE")
    for rt in ("Specific", "One-Term Loss Cost"):
        data = rated(tree(j="CA", rt=rt), "CA")
        if data is None:
            continue
        st = rc1.find(data, P + "Structure")[0]
        pp = rc1.find(data, P + "PersonalProperty")[0]
        bi = rc1.find(data, P + "BusinessIncome")[0]
        hv = hand_building("CA", st)
        print(f"    CA {rt}: building BGI {val(st, 'BasicGroupIRate')} (hand {hv}); contents {val(pp, 'BasicGroupIRate')} (hand {hand_contents(pp)}); "
              f"BI {val(bi, 'BasicGroupIRate')} (hand {hand_bi('CA', bi)}); RatingIdentificationCode {val(st, 'RatingIdentificationCode')}")
        check(m.same(hv, val(st, "BasicGroupIRate")) and m.same(hand_contents(pp), val(pp, "BasicGroupIRate")),
              f"CA {rt}: building and contents Group I by hand = engine")
        if rt == "One-Term Loss Cost":
            hb = hand_bi("CA", bi)
            print(f"    CA One-Term: BI's countrywide branch tests only Specific / Tentative, so BI falls to Otherwise -> {val(bi, 'BasicGroupIRate')} (hand: {hb})")
            check(m.same(hb, 1) and m.same(val(bi, "BasicGroupIRate"), 1),
                  "CA One-Term Loss Cost: the building and contents price as Specific; BI's rule does not name it and sets 1.0 (to probe live in C26-11)")


def main():
    if "--skip-replay" not in sys.argv:
        replay()
        failed_calls()
    out = branch_map()
    if out:
        contents_bi(out)
    group_ii()
    domains()
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-1 (C26-02..C26-06): {'ALL CHECKS PASS' if not FAIL else 'FAILED: ' + '; '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
