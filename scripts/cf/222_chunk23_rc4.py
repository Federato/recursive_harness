#!/usr/bin/env python3
"""Chunk 23, RC-4 (C23-16..C23-18): each family on a fuller state policy, the state-only list closed, older packages.

C23-16  FULL POLICIES, ISO live (every record predicted three ways first, 219_'s hand models):
  F-MA  two locations; location 1 with two buildings (one with heating-oil remediation, 2 tanks + 1 extra building; one
        without) and the Pollutant Clean Up credit "Yes"; tenant relocation on both buildings (4 / 8 units); location 2 the
        same Pollutant record but NO remediation anywhere: its credit is off and its CP 04 44 message fires
  F-AK  a Legal Liability building with its contents (fees on both), a second ORDINARY building whose fee record is
        removed, and the policy fee on Mortgageholders E&O
  F-CA  two buildings (150,000 / 600,000) with Limited EQ on each, contents and BI Limited EQ, Additional EQ on both
  F-VA  three buildings: the state broad form on 1, the countrywide CP 04 05 on 2 (another building: no same-building
        message), the tenants' form on 3 (an I&B item)
C23-17  THE STATE-ONLY LIST: 904_'s ownership enumeration re-run; 80 files, none unassigned; MT's glass files price nothing;
        WV's two flood files belong to chunk 25; each owner chunk's task list names its files
C23-18  OLDER PACKAGES, ISO live at their own dates: MA 2022-07-01 (CF MA 20220601 V01: tenant relocation has NO premium
        rule), AK 2022-07-01 (CF AK 20200601 V02: building / contents fees have none), VA 2021-07-01 (CF VA 20210501 V03:
        neither VA form has one). Predicted: each such record prices nothing (no premium, or 0), the rest as the engine
        rates the old package; the chunk 23 records are compared strictly, the rest of the policy reported

    python scripts/cf/222_chunk23_rc4.py [--live] [--cases F-MA,O-VA]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
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

t3 = import_module("221_chunk23_rc3")
t2, m = t3.t2, t3.m
r2, rc1, gc, rep, cmp, r11 = m.r2, m.rc1, m.gc, m.rep, m.cmp, m.r11
P, D = m.P, m.D
FAIL = []
from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.interpreter import Interpreter                     # noqa: E402
from gl_engine.interp.tree import Node                                    # noqa: E402


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def locs(sub):
    return sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"]


def sts(loc):
    return loc[P + "StructureTable"][P + "Structure"]


def strip_children(d):
    for k in [k for k in d if k.endswith("Table")]:
        d.pop(k)
    return d


# ------------------------------------------------------------------ C23-16 trees

def f_ma():
    sub = m.ma_tree(tanks="2", extra="1", units="4")
    loc = locs(sub)[0]
    b2 = copy.deepcopy(sts(loc)[0])
    b2.pop(P + m.HO + "Table", None)
    b2[P + m.TR + "Table"][P + m.TR][0]["NumberOfUnits"] = "8"
    b2.update({"Limit": "250000", "FullBldgValue": "250000"})
    sts(loc).append(b2)
    loc2 = copy.deepcopy(loc)
    loc2["LocationNumber"] = "2"
    for s_ in sts(loc2):
        s_.pop(P + m.HO + "Table", None)
    locs(sub).append(loc2)
    return sub


def f_ak():
    sub = t2.ak()()
    loc = locs(sub)[0]
    b2 = strip_children(copy.deepcopy(sts(loc)[0]))
    b2.update({"CovType": "Building", "Limit": "300000", "FullBldgValue": "300000"})
    b2[P + m.AKS + "Table"] = {P + m.AKS: [{"Limit": "900000"}]}
    sts(loc).append(b2)
    return sub


def f_ca():
    sub = m.ca_tree(manual="300", lim=("120000", "50000", "40000"))
    loc = locs(sub)[0]
    b2 = strip_children(copy.deepcopy(sts(loc)[0]))
    b2.update({"Limit": "600000", "FullBldgValue": "600000"})
    b2[P + m.LEQ + "BuildingTable"] = {P + m.LEQ + "Building": [{"Limit": "500000"}]}
    b2[P + m.ADDEQ + "Table"] = {P + m.ADDEQ: [{"ManualPremium": "450"}]}
    sts(loc).append(b2)
    return sub


def f_va():
    sub = t2.va(cw=False)()
    loc = locs(sub)[0]
    b1 = sts(loc)[0]
    tenants = b1.pop(P + m.VAT + "Table")
    b2 = strip_children(copy.deepcopy(b1))
    b2.update({"Limit": "300000", "FullBldgValue": "300000"})
    b2[P + "OrdinanceOrLawCoverageTable"] = {P + "OrdinanceOrLawCoverage": [{
        "CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
        "PostLossOrdinanceOrLawOption": "No"}]}
    b3 = strip_children(copy.deepcopy(b1))
    b3.update({"Limit": "80000", "FullBldgValue": "80000", "CovType": "Improvements and Betterments"})
    b3[P + m.VAT + "Table"] = tenants
    sts(loc).extend([b2, b3])
    return sub


# ------------------------------------------------------------------ C23-18: older packages

no_eq = import_module("217_chunk22_rc4").no_eq      # the portable policy's EQ deductible tier "1" is not filed in these
                                                     # old packages (ISO refused EarthquakeDeductibleTier CW, 1): drop all EQ
#: what the OLD package's rule text predicts for the census's "no premium rule" records (2026-10-01): MA 2022's tenant
#: relocation file really has no premium writer ($0); AK 2020's fee files and VA 2021's form files DO price -- inside a
#: rule named ErcRate, not SetPremium, which the census's SetPremium-only test missed (in-force packages: none like it)
EXPECT = {"O-MA": "zero", "O-AK": "priced", "O-VA": "priced"}
OLD = {"O-MA": ("MA", "20220701", lambda: no_eq(m.ma_tree()), [m.HO, m.HOC, m.TR], [m.TR]),
       "O-AK": ("AK", "20220701", lambda: no_eq(t2.ak()()), [m.AKS, m.AKP, m.AKF], [m.AKS, m.AKP]),
       "O-VA": ("VA", "20210701", lambda: no_eq(t2.va()()), m.PREMIUM_RECS["VA"], m.PREMIUM_RECS["VA"])}


def run_at(sub, j, date):
    ip = Interpreter(book_for(j, date), rounding=gc.ROUNDING, null_arithmetic=gc.NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{j}", sub)
    ip.run(data)
    return data, ip


def cases():
    return {
        "F-MA": ("C23-16", "MA", "two locations, two buildings, credit on / off by location", f_ma, t2.MA_RECS),
        "F-AK": ("C23-16", "AK", "Legal Liability building + contents, an ordinary second building, policy fee", f_ak, t2.AK_RECS),
        "F-CA": ("C23-16", "CA", "two buildings with Limited EQ and Additional EQ, contents and BI Limited EQ", f_ca, t2.CA_RECS),
        "F-VA": ("C23-16", "VA", "broad form / countrywide CP 04 05 / tenants' form on three buildings", f_va, t2.VA_RECS),
    }


# ------------------------------------------------------------------ C23-17

def state_only_list():
    progress(0, 0, "C23-17 the state-only list (904_ re-run)")
    out = subprocess.run([sys.executable, "-u", str(ROOT / "scripts" / "cf" / "904_chunk23_census.py")], capture_output=True, text=True, cwd=ROOT).stdout
    sec = out.split("[1/5")[0]
    total = int(re.search(r"(\d+) in-force state-only premium files", sec).group(1))
    owners = re.findall(r"^  (chunk \d+[^\n]*?)\s{2,}(\d+)\s+(.*)$", sec, re.M)
    unassigned = "UNASSIGNED" in sec
    print(f"  {total} in-force state-only premium files; owners: " + "; ".join(f"{o.split(' (')[0]} {n} [{st}]" for o, n, st in owners))
    ok = total == 80 and not unassigned and sum(int(n) for _, n, _ in owners) == 80
    print(f"    [{'ok' if ok else 'FAIL'}] 80 files, none unassigned")
    if not ok:
        FAIL.append("state-only list")
    mt = re.search(r"MT BuildingGlassTenantsPolicy", sec)
    print(f"    [{'ok' if mt else 'FAIL'}] MT's glass file is listed only as a totals file (no SetPremium): it prices nothing")
    if not mt:
        FAIL.append("MT glass")
    wv = re.search(r"chunk 25 \(flood\)\s+2\s+WV:2", sec)
    print(f"    [{'ok' if wv else 'FAIL'}] WV's two flood files belong to chunk 25")
    if not wv:
        FAIL.append("WV flood")
    names = {"12": ["VA"], "15": ["Y2K", "VA"], "16": ["Mine Subsidence"], "19": ["FL", "glass"], "20": ["NC"], "21": ["FL"], "25": ["WV"]}
    for ch, words in names.items():
        f = ROOT / "docs" / f"CF-CHUNK{ch}-TASKS.md"
        t = f.read_text(encoding="utf-8") if f.exists() else ""
        hit = all(w.lower() in t.lower() for w in words)
        print(f"    [{'ok' if hit else 'FAIL'}] chunk {ch}'s task list names its state-only files ({', '.join(words)})")
        if not hit:
            FAIL.append(f"chunk {ch} names")


def predict_tree(j, data, recs):
    preds, lines, bad = {}, [], []
    for rec in recs:
        res = m.predict(j, data, rec)
        ok = all(m.same(hv, e) and m.same(ev, e) for hv, ev, e in res)
        preds[rec] = [hv for hv, _, _ in res]
        if res and not all(m.same(e, 0) for _, _, e in res) or not ok:
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-58:]:58s} hand {[str(x) for x, _, _ in res]} engine {[e for _, _, e in res]}")
        if not ok:
            bad.append(rec)
    return preds, lines, bad


def live_compare(client, raas_mod, cid, req, recs, preds, data, ip, strict_all=True):
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,260})', str(exc.body))
        print(f"  {cid:5s} ISO REFUSES {mm_.group(0)[:280] if mm_ else str(exc.body)[:280]}")
        FAIL.append(f"{cid} live")
        return None
    (gc.OUT / f"chunk23_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    pbad = []
    for rec in recs:
        want = [w for w in preds.get(rec, []) if not m.same(w, 0)]
        iso = [x for x in r2.iso_of(resp, rec) if not m.same(x, 0)]
        if sorted(D(str(x)) for x in iso) != sorted(D(str(w)) for w in want):
            pbad.append((rec, iso, [str(w) for w in want]))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not pbad and (not strict_all or (not dd and mi == mo))
    print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: chunk 23 records {len(recs) - len(pbad)} of {len(recs)} as predicted; "
          f"policy premiums {len(ipr) - len(dd)} of {len(ipr)} equal, messages {'equal' if mi == mo else 'DIFFER'}"
          + ("" if strict_all else " (reported, not gated: the old package outside the build's as-of date)")
          + "".join(f"\n        predicted {rr[-55:]}: ISO {x}, derived {w}" for rr, x, w in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
    if not ok:
        FAIL.append(f"{cid} live")
    return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    olds = dict(OLD)
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
        olds = {k: v for k, v in olds.items() if k in a.cases.split(",")}
    else:
        state_only_list()
    preds, runs = {}, {}
    for i, (cid, (task, j, label, build, recs)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        data, ip, err = m.rated(build(), j)
        if err:
            print(f"{cid} {task} {j} {label}: RAISED {err}")
            FAIL.append(cid)
            continue
        preds[cid], lines, bad = predict_tree(j, data, recs)
        print(f"{cid} {task} {j} {label}: {'as predicted' if not bad else 'DIFFERS'}")
        print("\n".join(lines))
        if bad:
            FAIL.append(cid)
    for cid, (j, date, build, recs, unruled) in olds.items():
        progress(0, 0, f"engine {cid} at {date} ({book_for(j, date).state.package.content.name})")
        try:
            data, ip = run_at(build(), j, date)
        except Exception as exc:
            # OI-120 (2026-10-01): the 2020 countrywide package (parent of every state package in force before 2022-10)
            # carries <rul:Null/> as an operand of an And (ISO's own build replaced an invalid path, its comment says so)
            # in Structure.DoMessageAtLeastOneBuilding...MarginClause; our engine refuses a non-boolean condition, so no
            # pre-2022-10 policy rates in our engine. Recorded, not fixed (old editions; an engine change needs a go).
            known = "not a boolean" in str(exc)
            print(f"{cid} C23-18 {j} at {date}: engine RAISED{' (OI-120, pinned)' if known else ''}: {str(exc)[:120]}")
            if not known:
                FAIL.append(cid)
            runs[cid] = None
            continue
        runs[cid] = (data, ip)
        got = {rec: [m.val(n, "Premium") for n in m.find(data, rec)] for rec in unruled}
        ok = all(all(p in (None, "0", "0.0") for p in ps) for ps in got.values())
        print(f"{cid} C23-18 {j} at {date}: records with no premium rule price nothing: {'yes' if ok else 'NO'} "
              f"{ {r_[-30:]: v for r_, v in list(got.items())[:4]} }")
        if not ok:
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live (C23-16 at 2026-09-17; C23-18 at each old package's date):")
        for i, (cid, (task, j, label, build, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = t2.state_req(t2.m20.payload(build()), j)
            (gc.OUT / f"chunk23_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            live_compare(client, raas_mod, cid, req, recs, preds.get(cid, {}), data, ip)
        for cid, (j, date, build, recs, unruled) in olds.items():
            if cid not in runs:
                continue
            if runs[cid] is None:            # OI-120: ISO side only -- the no-premium-rule records must price nothing
                progress(0, 0, f"ISO {cid} at {date} (ISO side only: OI-120)")
                req = t2.state_req(t2.m20.payload(build()), j)
                req["body"]["SchemeKeys"]["EffectiveDateTime"] = f"{date[:4]}-{date[4:6]}-{date[6:]}T00:00:00"
                (gc.OUT / f"chunk23_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                try:
                    resp = client.rate(req)
                except raas_mod.RaaSError as exc:
                    mm_ = re.search(r'"Message":"([^"]{0,260})', str(exc.body))
                    print(f"  {cid:5s} ISO REFUSES {mm_.group(1)[:260] if mm_ else str(exc.body)[:260]}")
                    FAIL.append(f"{cid} live")
                    continue
                (gc.OUT / f"chunk23_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
                got = {rec: r2.iso_of(resp, rec) for rec in unruled}
                zero = all(all(m.same(x, 0) for x in v) for v in got.values())
                ok = zero if EXPECT[cid] == "zero" else not zero
                tot = rep.iso_prem(resp).get(t2.m.r2.gc.__dict__.get("TOTAL", "CommercialProperty[0]/Premium"))
                priced = {r_[-40:]: v for r_, v in got.items() if not all(m.same(x, 0) for x in v)}
                print(f"  {cid:5s} {'AGREE' if ok else 'DIFFER'}: ISO prices the policy at {date}; predicted from the old package's rule text: "
                      f"{EXPECT[cid]}; ISO {'prices nothing on them' if zero else 'prices ' + str(priced)}")
                if not ok:
                    FAIL.append(f"{cid} live")
                continue
            progress(0, 0, f"ISO {cid} at {date}")
            req = t2.state_req(t2.m20.payload(build()), j)
            req["body"]["SchemeKeys"]["EffectiveDateTime"] = f"{date[:4]}-{date[4:6]}-{date[6:]}T00:00:00"
            (gc.OUT / f"chunk23_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            data, ip = runs[cid]
            pr = {rec: [D(0)] * len(m.find(data, rec)) for rec in unruled}
            resp = live_compare(client, raas_mod, cid, req, unruled, pr, data, ip, strict_all=False)
            if resp is not None:
                iso = {rec[-30:]: r2.iso_of(resp, rec) for rec in unruled[:4]}
                print(f"        ISO on the no-premium-rule records: {iso}")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C23-16..C23-18): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
