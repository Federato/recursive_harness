#!/usr/bin/env python3
"""Chunk 21, C21-12 shared names and C21-13 exclusions / stat codes, live ISO.

C21-12 SHARED NAMES. Static: every writer of Rate, FinalRate, DeductibleFactor, LimitToUse, ManualPremium,
CovForm, CovType, PolicyType and WindstormOrHailExcludedIndicator in the chunk's files and the parents
they read, in every in-force package, and whether the write is IsNull-guarded (a submitted value
survives) or unconditional (overwritten). Found (2026-09-30): every chunk write is guarded; ManualPremium,
PolicyType, CovType and the occupancy / special class CovForm have no writer (inputs); the parents'
LimitToUse writes are guarded; the contents' CovForm is copied from the occupancy UNCONDITIONALLY.
Live, each predicted with the submitted value standing, the "overwritten" reading giving another dollar:
  N1  building sewer Rate 1.000 submitted (overwritten: 0.77 -> 167)
  N2  sewer BI FinalRate 0.200 submitted (overwritten: 0.07 -> 17)
  N3  loss assessment DeductibleFactor 0.5 submitted (overwritten: 250 -> 1.1)
  N4  misc. real property Rate 1.000 submitted (overwritten: 0.528 -> 93)
  N5  the building's LimitToUse 50,000 submitted under a 100,000 limit, sewer 75,000: the cap message
      fires (the overwritten reading: silent) and the building's own premium moves
  N6  the special class LimitToUse 30,000 submitted: its sewer deductible bands on 30,000

C21-13 EXCLUSIONS AND STAT CODES. Static: no chunk premium rule reads a cyber field. The options
container's PerilExclusionIndicatorStatCode is looked up by (vandalism, sprinkler leakage, wind / hail
[, theft]) excluded indicators, each "Yes" when its exclusion record is on the contents; the Special
table (21-36) on Special, the Basic-and-Broad table (01-08) otherwise. AL tests its own record name; AR
DC NY RI set wind / hail "No" unless submitted; AR DC file tables with only "No" wind / hail rows.
  T1 OR Special, no exclusions: 36          T2 OR Special, wind / hail exclusion: 34
  T3 OR Broad, no exclusions: 08            T4 OR Broad, wind / hail exclusion: 07
  T5 AL Special, AL's direct-damage wind / hail record: 34; T6 AL with the CW record name: 36
  T7 AR Special, the wind / hail exclusion record: 36 (AR ignores it; CW's rule would give 34)
  T8 AR Special, indicator "Yes" SUBMITTED: AR's table REPLACES CW's and has no row for it, so the CW
     pass finds nothing: ours writes no code, ISO refuses (first predicted 34, the CW row)
  T9 DC Broad, vandalism exclusion: 04... (DC table, wind / hail No)

    python scripts/cf/210_chunk21_c21-12-13.py [--live] [--cases N1,T1]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import csv
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
import _iso_refusals as _iso                                    # noqa: E402

m9 = import_module("209_chunk21_c21-10-11")
m8, h21 = m9.m8, m9.h21
r2, rc1, r16, gc, rep, cmp, s18 = m8.r2, m8.rc1, m8.r16, m8.gc, m8.rep, m8.cmp, h21.s18
P, SEWER, LA, MRP, OPT = m8.P, m8.SEWER, m8.LA, m8.MRP, m8.OPT
BLDG, PP, SC, BI, SCBI = SEWER
same, at, portable, opts = r2.same, m9.at, m9.portable, m9.opts
r11 = m8.r11
r11.NUMERIC |= {"Rate", "FinalRate", "DeductibleFactor", "LimitToUse"}
FAIL = []
D = Decimal
ASOF = "20260917"
NAMES = ["Rate", "FinalRate", "DeductibleFactor", "LimitToUse", "ManualPremium", "CovForm", "CovType", "PolicyType",
         "WindstormOrHailExcludedIndicator"]
FILES = re.compile(r"DischargeFromSewer|CondominiumCommercialUnitOwnersOptional|ChangesCommercialUnitsInResidentialCondo")
PARENTS = {"CommercialPropertyRules": ["PolicyType"], "CommercialPropertyOccupClassRules": ["CovForm"],
           "CommercialPropertySpecialClassRules": ["CovForm", "LimitToUse"],
           "CommercialPropertyStructureRules": ["CovType", "LimitToUse"],
           "CommercialPropertyPersonalPropertyRules": ["CovForm", "LimitToUse"],
           "CommercialPropertyBusinessIncomeRules": ["LimitToUse"],
           "CommercialPropertySpecialClassBusnIncomeRules": ["LimitToUse"]}
WH = "WindstormOrHailExclusionPrsnlProp"
WH_AL = "WindstormOrHailExclusionDirectDamagePrsnlProp"
VAND = "VandalismExclusionPrsnlProp"


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def packages():
    pk = {"CW": h21.CW}
    for j in s18.STATES:
        st = book_for(j, ASOF).state
        if st is not None:
            pk[j] = st.package.content
    return pk


def writers(pk, file_filter, names_for):
    """(record, name) -> {'guarded'|'UNCONDITIONAL': {rule@package}}"""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for who, p in pk.items():
        rd = p / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            stem = f.name[:-len(".Rule.xml")]
            names = names_for(stem)
            if not names or not file_filter(stem):
                continue
            t = f.read_text(encoding="utf-8-sig", errors="replace")
            for m in re.finditer(r'<rul:Rule Name="(\w+)".*?</rul:Rule>', t, re.S):
                body = m.group(0)
                for n in names:
                    for w in re.finditer(rf'ToDataDef="{n}"', body):
                        g = bool(re.search(rf'<rul:IsNull>\s*<rul:Value[^>]*FromDataDef="{n}"', body[:w.start()]))
                        out[(stem.replace(P, "").replace("Rules", ""), n)]["guarded" if g else "UNCONDITIONAL"].add(
                            f"{m.group(1)}@{who}")
    return out


def static():
    progress(0, 0, "C21-12 / C21-13 static")
    print("\n" + "=" * 90 + "\nC21-12  WHO WRITES EACH SHARED NAME (every in-force package)\n" + "-" * 90)
    pk = packages()
    own = writers(pk, lambda s: bool(FILES.search(s)), lambda s: NAMES)
    par = writers(pk, lambda s: s in PARENTS, lambda s: PARENTS.get(s))
    for label, d in (("chunk records", own), ("parents they read", par)):
        print(f"  {label}:")
        for (rec, n), kinds in sorted(d.items()):
            print(f"    {rec[-52:]:52s} {n:34s} " + "; ".join(f"{k} {sorted(v)[:3]}{' +' + str(len(v) - 3) if len(v) > 3 else ''}"
                                                       for k, v in kinds.items()))
    unguarded_own = [(r, n) for (r, n), k in own.items() if "UNCONDITIONAL" in k]
    check(not unguarded_own, f"every write in the chunk's own files is IsNull-guarded ({unguarded_own or 'all'})")
    for n in ("ManualPremium", "CovType", "PolicyType"):
        check(not any(nn == n for (_, nn) in list(own) + list(par)), f"{n} has no writer anywhere searched: an input")
    pp_cov = par.get(("PersonalProperty", "CovForm"), {})
    check("UNCONDITIONAL" in pp_cov and "guarded" not in pp_cov,
          f"the contents' CovForm is copied unconditionally ({dict(pp_cov)})")
    lim = [k for (r, n), k in par.items() if n == "LimitToUse"]
    check(lim and all(set(k) == {"guarded"} for k in lim), "every parent's LimitToUse write is guarded")
    print("\n" + "=" * 90 + "\nC21-13  NO CYBER FACTOR IN ANY CHUNK FORMULA\n" + "-" * 90)
    hits = []
    for who, p in pk.items():
        rd = p / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            if FILES.search(f.name) and re.search("cyber", f.read_text(encoding="utf-8-sig", errors="replace"), re.I):
                hits.append(f"{who}:{f.name}")
    check(not hits, f"no chunk rule file in any package mentions cyber ({hits or 'none'})")


# ---------------------------------------------------------------- live cases

def stat_code(j, cause, vand, sprk, wh, theft):
    """the container's PerilExclusionIndicatorStatCode from the filed tables: state rows first, then CW's"""
    special = cause == "Special"
    name = "PerilExclusionIndicatorBasicAndSpecialStatCode" if special else "PerilExclusionIndicatorBasicAndBroadStatCode"
    key = {"VandalismExcluded": vand, "SprinklerLeakageExcluded": sprk, "WindHailExcluded": wh}
    if special:
        key["TheftExcluded"] = theft
    for pkg, sc in ((book_for(j, ASOF).state.package.content, j), (h21.CW, "CW")):
        f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
        if f.exists():
            for r in csv.DictReader(open(f, encoding="utf-8-sig")):
                if r["StateCode"] == sc and all(r[k] == v for k, v in key.items()):
                    return r["Code"]
    return None


GOOD = {"LossAssessmentLimit": "0", "MiscRealPropLimit": "20000"}


def container_case(j, cause, recs=(), submit=None):
    def b():
        sub = m9.portable(j, cause)
        cont = dict(GOOD, **(submit or {}))
        at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [dict(cont, **{P + MRP: {}})]}
        for rec in recs:
            r2.put(sub, rec, {}, state=j)
        return sub
    return b


def sub_value(rec, field, value, limit=25000, extra=None):
    def b():
        sub = portable("OR")
        if extra:
            extra(sub)
        if rec in SEWER:
            r2.put(sub, rec, {SEWER[rec]: str(limit), field: value})
        return sub
    return b


def cases():
    c = {}

    def add(cid, task, j, label, build, fields=None, fire=(), silent=(), codes=None, recs=(), refuse=None):
        c[cid] = dict(task=task, j=j, label=label, build=build, fields=fields or {}, fire=list(fire), silent=list(silent),
                      codes=codes, recs=list(recs), refuse=refuse)

    # C21-12: submitted values that survive (fields: (record, field) -> expected value on the tree)
    add("N1", "C21-12", "OR", "building sewer Rate 1.000 submitted (overwritten reading: 167)",
        sub_value(BLDG, "Rate", "1.000"), {(BLDG, "Rate"): "1.000"}, recs=[BLDG])
    add("N2", "C21-12", "OR", "sewer BI FinalRate 0.200 submitted (overwritten reading: 17)",
        sub_value(BI, "FinalRate", "0.200"), {(BI, "FinalRate"): "0.200"}, recs=[BI])

    def la_ded(sub):
        at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [{
            "LossAssessmentLimit": "10,000", "LossAssessmentDeductible": "250", P + LA: {"DeductibleFactor": "0.5"}, P + MRP: {}}]}
    add("N3", "C21-12", "OR", "loss assessment DeductibleFactor 0.5 submitted (overwritten reading: 250 -> 1.1)",
        m9.with_(lambda: portable("OR"), la_ded), {(LA, "DeductibleFactor"): "0.5"}, recs=[LA])

    def mrp_rate(sub):
        at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [dict(GOOD, **{P + MRP: {"Rate": "1.000"}, P + LA: {}})]}
    add("N4", "C21-12", "OR", "misc. real property Rate 1.000 submitted (overwritten reading: 93)",
        m9.with_(lambda: portable("OR"), mrp_rate), {(MRP, "Rate"): "1.000"}, recs=[MRP])
    add("N5", "C21-12", "OR", "building LimitToUse 50,000 submitted, sewer 75,000: the cap fires (overwritten: silent)",
        sub_value(BLDG, "DischargeLimitPD", "75000", 75000, lambda s: at(s, "Structure").__setitem__("LimitToUse", "50000")),
        {("Structure", "LimitToUse"): "50000"}, fire=[m9.CAPS[0]], recs=[BLDG])
    add("N6", "C21-12", "OR", "special class LimitToUse 30,000 submitted: its sewer deductible bands on 30,000",
        sub_value(SC, "DischargeLimitPD", "25000", 25000, lambda s: at(s, "SpecialClass").__setitem__("LimitToUse", "30000")),
        {("SpecialClass", "LimitToUse"): "30000"}, recs=[SC])

    # C21-13: the options container's stat code (predicted from the filed tables)
    N = "No"
    add("T1", "C21-13", "OR", "Special, no exclusions", container_case("OR", "Special"), codes=("Special", N, N, N, N))
    add("T2", "C21-13", "OR", "Special, wind / hail exclusion", container_case("OR", "Special", [WH]), codes=("Special", N, N, "Yes", N))
    add("T3", "C21-13", "OR", "Broad, no exclusions", container_case("OR", "Broad"), codes=("Broad", N, N, N, N))
    add("T4", "C21-13", "OR", "Broad, wind / hail exclusion", container_case("OR", "Broad", [WH]), codes=("Broad", N, N, "Yes", N))
    add("T5", "C21-13", "AL", "AL Special, AL's direct-damage wind / hail record", container_case("AL", "Special", [WH_AL]),
        codes=("Special", N, N, "Yes", N))
    add("T6", "C21-13", "AL", "AL Special, the CW record name (AL ignores it)", container_case("AL", "Special", [WH]),
        codes=("Special", N, N, N, N))
    add("T7", "C21-13", "AR", "AR Special, the wind / hail record (AR ignores it; CW's rule: 34)",
        container_case("AR", "Special", [WH]), codes=("Special", N, N, N, N))
    # First predicted 34 (the CW row). But AR files its own table, which REPLACES the CW base (the recorded
    # table-resolution rule: in-force package with rows, else CW), and it has no CW-keyed rows: the CW
    # SingleResult pass finds nothing. Engine: no stat code; ISO: a refusal (OI-103's shape). Probe: the
    # "falls back to the CW table" reading gives 34.
    add("T8", "C21-13", "AR", "AR Special, indicator Yes SUBMITTED: AR's table replaces CW's, no row (ISO refuses)",
        container_case("AR", "Special", submit={"WindstormOrHailExcludedIndicator": "Yes"}), codes=("NONE",),
        refuse="PerilExclusionIndicatorBasicAndSpecialStatCode")
    add("T9", "C21-13", "DC", "DC Broad, vandalism exclusion", container_case("DC", "Broad", [VAND]), codes=("Broad", "Yes", N, N, N))
    return c


def tree_value(data, rec, field):
    tag = P + rec
    nodes = rc1.find(data, tag)
    return h21.val(nodes[0], field) if nodes else None


def container_fields(data):
    n = rc1.find(data, P + OPT)
    return {f: h21.val(n[0], f) for f in ("PerilExclusionIndicatorStatCode", "WindstormOrHailExcludedIndicator",
                                          "VandalismExcludedIndicator")} if n else {}


def iso_container(resp):
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == P + OPT and isinstance(v, list) and v:
                    return v[0]
                got = walk(v)
                if got:
                    return got
        elif isinstance(o, list):
            for v in o:
                got = walk(v)
                if got:
                    return got
    return walk(resp) or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    if not a.cases:
        static()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    print("\n" + "=" * 90 + "\nENGINE\n" + "-" * 90)
    for i, (cid, c) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(c["build"](), c["j"])
        except InterpretError as exc:
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                continue
            print(f"{cid}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        bad = []
        for (rec, f), want in c["fields"].items():
            got = tree_value(data, rec, f)
            if got is None or not same(got, want):
                bad.append(f"{rec[-20:]}.{f} tree {got} want {want}")
        prem = {}
        for rec in c["recs"]:
            prem[rec] = [h for h, ev, e in m8.predict(data, rec)] if rec not in (BLDG, SC) or not c["fields"] else None
            # the submitted value stands: predict with 174_'s SetPremium evaluator on the tree (its operands
            # are exactly what the rule reads); the hand models recompute Rate and would give the OTHER reading
            res = m8.predict(data, rec)
            prem[rec] = [ev for _, ev, _ in res]
            if not all(same(ev, e) for _, ev, e in res):
                bad.append(f"{rec[-20:]} evaluator {[str(ev) for _, ev, _ in res]} engine {[e for *_, e in res]}")
        msgs = [str(x) for x in ip.messages]
        bad += m9.msg_check(msgs, c["fire"], c["silent"])
        code = None
        if c["codes"] == ("NONE",):
            got = container_fields(data).get("PerilExclusionIndicatorStatCode")
            if got is not None:
                bad.append(f"stat code {got} predicted none (no row in the state's table)")
        elif c["codes"]:
            code = stat_code(c["j"], *c["codes"])
            got = container_fields(data)
            if got.get("PerilExclusionIndicatorStatCode") != code:
                bad.append(f"stat code {got} predicted {code}")
        preds[cid] = (prem, code)
        print(f"{cid} {c['task']} {c['j']} {c['label']}: engine {'as predicted' if not bad else 'DIFFERS ' + str(bad)}"
              + (f"  premiums {({r16.short(k)[-24:]: [str(x) for x in v] for k, v in prem.items()})}" if prem else "")
              + (f"  stat code {code}" if code else ""))
        if bad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (every premium, the whole message set, the container's stat code):")
        for i, (cid, c) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = m8.payload(c["build"](), c["j"])
            (gc.OUT / f"chunk21_c21-12-13_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                what = mm.group(0)[:220] if mm else str(exc.body)[:220]
                if c["refuse"] and c["refuse"] in what:
                    print(f"  {cid} REFUSES AS PREDICTED (OI-103; ours rates): {what}")
                    continue
                print(f"  {cid} ISO REFUSES {what}")
                FAIL.append(f"{cid} live")
                continue
            if c["refuse"]:
                print(f"  {cid} ISO RATED where a refusal was predicted: stat code {iso_container(resp).get('PerilExclusionIndicatorStatCode')}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk21_c21-12-13_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            prem, code = preds.get(cid, ({}, None))
            pbad = []
            for rec, want in prem.items():
                w = [x for x in want if x is not None and not same(x, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(D(str(x)) for x in iso) != sorted(D(str(x)) for x in w):
                    pbad.append((rec, iso, [str(x) for x in w]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = m9.msg_check([str(x) for x in mi], c["fire"], c["silent"])
            ic = iso_container(resp)
            cbad = []
            if code is not None:
                if str(ic.get("PerilExclusionIndicatorStatCode")) != code:
                    cbad.append(f"ISO stat code {ic.get('PerilExclusionIndicatorStatCode')} predicted {code}")
                ours = container_fields(data)
                for f in ("PerilExclusionIndicatorStatCode", "WindstormOrHailExcludedIndicator"):
                    if str(ic.get(f)) != str(ours.get(f)):
                        cbad.append(f"{f} ISO {ic.get(f)} ours {ours.get(f)}")
            ok = not pbad and not d and mi == mo and not mb and not cbad
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: {len(ipr) - len(d)} of {len(ipr)} premiums; messages "
                  f"{'equal' if mi == mo else 'DIFFER'}" + (f"; stat code {ic.get('PerilExclusionIndicatorStatCode')}, "
                                                           f"wind / hail {ic.get('WindstormOrHailExcludedIndicator')}" if code else "")
                  + (f"; {mb}" if mb else "") + (f"; {cbad}" if cbad else "")
                  + "".join(f"\n        predicted {r16.short(r)[-50:]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(str(x)[:100] for x in mi - mo)[:3]}\n        ours only {sorted(str(x)[:100] for x in mo - mi)[:3]}"
                     if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC21-12 / C21-13: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
