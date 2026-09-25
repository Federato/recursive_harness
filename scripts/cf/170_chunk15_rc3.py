#!/usr/bin/env python3
"""Chunk 15, RC-3 (C15-11 to C15-14): zero cases, the exclusion, messages, shared names.

Every case starts from RC-2's policy (169_: chunk 7's five coverages in Oregon,
policy package discount 0.85, IRPM 1.15, credit 0.9, the building's own credit
0.95, ManualPremium 1,090). Predictions are written before the run; ISO decides.
Reference figures from RC-2: 1090 x .85 = 926.5 -> 927; building credit -> 1,013;
contents / policy credit -> 959; no credit -> 1,066; one rounding -> 1,065.

C15-11  ZERO CASES (Cannabis on the building unless noted)
  Z1  ManualPremium absent -> $0. The operand is FirstValue with FromConstant 0.0,
      so it reads 0, not null; the null-skip rule (OI-109) would give $1.
  Z2  ManualPremium 0 -> $0.
  Z3  ManualPremium -1,090 -> -$1,013 (half-up rounds away from zero: -926.5 -> -927,
      -880.65 -> -881, -1013.15 -> -1013). Rival, half toward +infinity: -$1,012.
  Z4  policy PackageModFactor absent -> SetPackageModFactor writes 1.0:
      1090 x .95 = 1035.5 -> 1036 x 1.15 = 1191.4 -> $1,191.
  Z5  policy PackageModFactor 0 -> kept (0 is not null) -> $0, or ISO refuses (OI-103).
  Z6  policy IRPMFactor absent (IRPM not applied) -> 1.0: 927 x .95 = 881 -> $881.
  Z7  policy credit absent -> policy 1.0, copied to the Contents row -> Cannabis on
      contents 927 x 1.0 x 1.15 = 1066.05 -> $1,066.
  Z8  the building's own credit 0 -> kept -> Cannabis on the building $0, or ISO refuses.
  Z9  Interruption of Computer Operations, switch "No", ManualPremium 1,090 -> $0.
  Z10 Valuable Papers ManualPremium on the ordinary Contents row (CovType Personal
      Property) -> $0 (its switch is the row's CovType).
  Z11 Newly Acquired Location, switch "No", CoverageOnPolicyIndicator 1 SUBMITTED ->
      $0: the switch rule writes the indicator unconditionally (no IsNull guard).
  Z12 Cannabis with Premium 5 SUBMITTED -> $1,013: SetPremium writes unconditionally.
C15-12  THE EXCLUSION
  X1a control: the policy with no chunk 15 record.
  X1b Cannabis (without hemp) on all five coverages: 1,013 / 959 / 1,066 / 959 / 1,066,
      and every other premium on the policy equal to X1a's (an exclusion here only
      carries its own manual premium; no parent coverage reads it).
  X2  both Cannabis forms on one building: both $1,013, "Only one Exclusion Form for
      Cannabis can apply to the risk".
  X3  Cannabis Coverage (CP 99 06, a record with no premium) and the Cannabis exclusion
      on one Contents row: exclusion $959, plus "CP 99 06 Cannabis Coverage is not valid
      with Cannabis Exclusion CP 99 03 or CP 99 04" (Contents) and the policy's "Cannabis
      Exclusion CP 99 03 or CP 99 04 is not valid with Cannabis Coverage CP 99 06" (a
      ForEach inside an Or: "any").
C15-13  MESSAGES
  M1  Interruption of Computer Operations limit 2,499 -> $1,065 and the $2,500 message.
  M2  limit 2,500 -> $1,065, silent.  M3 limit absent (reads 0) -> $1,065 and the message.
  M4  Limited International x2 under an OCCUPANCY with CovForm "Building and Personal
      Property Coverage Form" -> $959 each, CP 04 32 / 04 33 silent. (The Contents row's
      CovForm is copied from its occupancy unconditionally, SetCovForm ../../CovForm:
      a value on the row itself is overwritten -- the first run set it there.)
  M5  Standard Property Policy with Limited International x2 and Electronic Commerce ->
      "CP 04 32 / CP 04 33 not valid with the Standard Property Policy", "CP 04 30 is
      not valid with the Standard Property Policy"; the manual premiums still price.
  M6  Newly Acquired Property on a building with CovType "No Coverage" -> "CP 04 25 not
      valid with selected Coverage"; the endorsement still prices.
C15-14  SHARED NAMES (static, below): who writes ManualPremium, Premium and
      CoverageOnPolicyIndicator on the 29 records, anywhere in CW and the 46 states.

    python scripts/cf/170_chunk15_rc3.py [--live]

For every case: engine against the prediction; --live: ISO against the prediction,
every premium field for field, and the full message set. Exits 1 on any disagreement.
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
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
rep = import_module("157_chunk14_c14-02_total_replay")
cmp = import_module("154_chunk13_rc5_fields_messages")
c11 = import_module("106_chunk11_census")
rc1 = import_module("168_chunk15_rc1")
rc2 = import_module("169_chunk15_rc2")
r11 = gc.r11
P = "CommercialProperty"
CB, CBH, CPP = "CannabisExclusionBuilding", "CannabisExclusionWithHempExceptionBuilding", "CannabisExclusionPersonalProperty"
CAN5 = [CB, CPP, "CannabisExclusionBusinessIncome", "CannabisExclusionSpecialClass",
        "CannabisExclusionSpecialClassBusinessIncome"]
ICO, VP, NAL, NAP = rc2.ICO, rc2.VP, "LocationNewlyAcquiredLocationTimeElement", rc2.NAP
LIM = ["BusnPrsnlPropLimitedInternationalCov", "PropInProcessOfMfrByOthersLimitedInternationalCov"]
ECOM = ["ElectronicCommerceLossOfBusinessIncomeCov", "ElectronicCommerceLossOfDataCov"]
BPP = "Building and Personal Property Coverage Form"
MSG_ICO = "Increase in Interruption of Computer Operations Limit must not be less than $2,500"
MSG_ONE = "Only one Exclusion Form for Cannabis can apply to the risk"
MSG_9906_PP = "CP 99 06 Cannabis Coverage is not valid with Cannabis Exclusion CP 99 03 or CP 99 04"
MSG_9906_POL = "Cannabis Exclusion CP 99 03 or CP 99 04 is not valid with Cannabis Coverage CP 99 06"
MSG_0432_FORM, MSG_0433_FORM = "CP 04 32 is not valid with selected Coverage Form", "CP 04 33 is not valid with selected Coverage Form"
MSG_0432_SPP, MSG_0433_SPP = "CP 04 32 not valid with the Standard Property Policy", "CP 04 33 not valid with the Standard Property Policy"
MSG_0430_SPP = "CP 04 30 is not valid with the Standard Property Policy"
MSG_0425 = "CP 04 25 not valid with selected Coverage"


def at(sub):
    return rc1.node_dicts(sub)


def row(sub, parent, rec):
    """the (first) placed row of rec under its parent dict."""
    d = at(sub)[P + parent]
    v = d.get(P + rec) or d[P + rec + "Table"][P + rec][0]
    return v


def mut(fn):
    def apply(sub):
        fn(sub)
        return sub
    return apply


def pol(**kw):
    def f(sub):
        cp = at(sub)[P]
        for k, v in kw.items():
            if v is None:
                cp.pop(k, None)
            else:
                cp[k] = v
    return f


def rowset(parent, rec, **kw):
    def f(sub):
        r = row(sub, parent, rec)
        for k, v in kw.items():
            if v is None:
                r.pop(k, None)
            else:
                r[k] = v
    return f


def chain(*fns):
    def f(sub):
        for fn in fns:
            fn(sub)
    return f


def vp_on_ordinary_row(sub):
    pp = at(sub)[P + "PersonalProperty"]
    pp[P + VP] = {"ManualPremium": rc2.MANUAL}


def cannabis_coverage_pp(sub):
    at(sub)[P + "PersonalProperty"][P + "CannabisCoveragePersonalPropertyTable"] = {
        P + "CannabisCoveragePersonalProperty": [{}]}


#: id -> (task, label, records placed, mutation, {record: premium | "refuse-or-0"}, messages expected NEW vs base, messages expected ABSENT)
CASES = {
    "Z1": ("C15-11", "ManualPremium absent", [CB], rowset("Structure", CB, ManualPremium=None), {CB: 0}, [], []),
    "Z2": ("C15-11", "ManualPremium 0", [CB], rowset("Structure", CB, ManualPremium="0"), {CB: 0}, [], []),
    "Z3": ("C15-11", "ManualPremium -1,090", [CB], rowset("Structure", CB, ManualPremium="-1090"), {CB: -1013}, [], []),
    "Z4": ("C15-11", "policy package discount absent", [CB], pol(PackageModFactor=None), {CB: 1191}, [], []),
    "Z5": ("C15-11", "policy package discount 0", [CB], pol(PackageModFactor="0"), {CB: 0}, [], []),
    "Z6": ("C15-11", "policy IRPM absent", [CB], pol(IRPMFactor=None), {CB: 881}, [], []),
    "Z7": ("C15-11", "policy credit absent (Contents copies 1.0)", [CPP],
           pol(MultiPremiumAndDispersionCreditFactorUser=None), {CPP: 1066}, [], []),
    "Z8": ("C15-11", "building's own credit 0", [CB],
           lambda s: at(s)[P + "Structure"].__setitem__("MultiPremiumAndDispersionCreditFactor", "0"), {CB: 0}, [], []),
    "Z9": ("C15-11", "Interruption of Computer Operations switch No", [ICO],
           rowset("BusinessIncome", ICO, InterruptionCompuOpsIndicator="No"), {ICO: 0}, [], [MSG_ICO]),
    "Z10": ("C15-11", "Valuable Papers on the ordinary Contents row", [], vp_on_ordinary_row, {VP: 0}, [], []),
    "Z11": ("C15-11", "Newly Acquired Location switch No, CoverageOnPolicyIndicator 1 submitted", [NAL],
            rowset("Location", NAL, Indicator="No", CoverageOnPolicyIndicator="1"), {NAL: 0}, [], []),
    "Z12": ("C15-11", "Cannabis with Premium 5 submitted", [CB], rowset("Structure", CB, Premium="5"), {CB: 1013}, [], []),
    "X1a": ("C15-12", "control: no chunk 15 record", [], None, {}, [], []),
    "X1b": ("C15-12", "Cannabis (no hemp) on all five coverages", CAN5, None,
            dict(zip(CAN5, (1013, 959, 1066, 959, 1066))), [], [MSG_ONE, MSG_9906_PP, MSG_9906_POL]),
    "X2": ("C15-12", "both Cannabis forms on one building", [CB, CBH], None, {CB: 1013, CBH: 1013}, [MSG_ONE], []),
    "X3": ("C15-12", "Cannabis Coverage CP 99 06 + exclusion on one Contents row", [CPP], cannabis_coverage_pp,
           {CPP: 959}, [MSG_9906_PP, MSG_9906_POL], []),
    "M1": ("C15-13", "computer operations limit 2,499", [ICO], rowset("BusinessIncome", ICO, Limit="2499"), {ICO: 1065}, [MSG_ICO], []),
    "M2": ("C15-13", "computer operations limit 2,500", [ICO], rowset("BusinessIncome", ICO, Limit="2500"), {ICO: 1065}, [], [MSG_ICO]),
    "M3": ("C15-13", "computer operations limit absent", [ICO], rowset("BusinessIncome", ICO, Limit=None), {ICO: 1065}, [MSG_ICO], []),
    "M4": ("C15-13", "Limited International on a BPP-form Contents row", LIM,
           lambda s: at(s)[P + "OccupClass"].__setitem__("CovForm", BPP), dict.fromkeys(LIM, 959),
           [], [MSG_0432_FORM, MSG_0433_FORM]),
    "M5": ("C15-13", "Standard Property Policy with Limited International and Electronic Commerce", LIM + ECOM,
           chain(pol(PolicyType="Standard Property Policy"),
                 lambda s: at(s)[P + "OccupClass"].__setitem__("CovForm", BPP)),
           dict.fromkeys(LIM + ECOM, 959), [MSG_0432_SPP, MSG_0433_SPP, MSG_0430_SPP], []),
    "M6": ("C15-13", "Newly Acquired Property on a 'No Coverage' building", [NAP],
           lambda s: at(s)[P + "Structure"].__setitem__("CovType", "No Coverage"), {NAP: 1013}, [MSG_0425], []),
}


def build(cid):
    task, label, recs, fn, want, new, absent = CASES[cid]
    sub = rc2.build(recs)
    if fn:
        fn(sub)
    return sub


def prem_all(data, rec):
    return [x.first("Premium").text if x.first("Premium") is not None else None for x in rc1.find(data, P + rec)]


def iso_all(resp, rec):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + rec:
                out.append(o.get("Premium"))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return out


def ok_prem(vals, want):
    vals = [v for v in vals]
    if not vals:
        return False
    return all(Decimal(str(v if v not in (None, "") else 0)) == Decimal(want) for v in vals)


def shared_names(fails):
    """C15-14: who writes the three shared fields on the 29 records (CW + 46 states)."""
    print("\n" + "=" * 78 + "\nC15-14  SHARED NAMES\n" + "-" * 78)
    recs = {P + r for r in rc1.CW_RECORDS + rc1.VA_RECORDS}
    pkgs = {"CW": book_for("OR", gc.ASOF).parent.package.content}
    for j in c11.JURIS:
        if j == "PR":
            continue
        try:
            pkgs[j] = book_for(j, gc.ASOF).state.package.content
        except Exception:
            pass
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
                for fld in ("ManualPremium", "Premium", "CoverageOnPolicyIndicator"):
                    for w in re.findall(rf'ToDataDef="([^"]*\b{fld})"', body):
                        target = grp if "/" not in w else w
                        hit = grp in recs if "/" not in w else any(r in w for r in recs)
                        if not hit:
                            continue
                        writers[(fld, grp.replace(P, "") if "/" not in w else w)].add(f"{j}:{name}")
                        if re.search(rf'IsNull>\s*<rul:Value[^>]*FromDataDef="{fld}"', body):
                            guarded[(fld, grp.replace(P, ""))].add(name)
    by_field = collections.defaultdict(collections.Counter)
    for (fld, grp), ws in writers.items():
        for w in ws:
            by_field[fld][w.split(":", 1)[1]] += 1
    mp = [k for k in writers if k[0] == "ManualPremium"]
    print(f"  ManualPremium: written by {len(mp)} rules on these records -> a pure input" if not mp
          else f"  ManualPremium: WRITTEN by {sorted(writers[k] for k in mp)}")
    if mp:
        fails.append("C15-14 ManualPremium written")
    print(f"  Premium: writers by rule name: {dict(by_field['Premium'])}")
    print(f"  CoverageOnPolicyIndicator: writers by rule name: {dict(by_field['CoverageOnPolicyIndicator'])}")
    print(f"  IsNull-guarded writes (a submitted value would survive): {dict(guarded) or 'none'}")
    ext = [k for k in writers if "/" in k[1]]
    print(f"  written from OUTSIDE the record (a path into it): {ext or 'none'}")
    if guarded:
        fails.append("C15-14 guarded write")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []
    base_data, base_ip = gc.run(rc2.build([]))
    base_msgs = set(base_ip.messages)
    engine = {}
    for cid, (task, label, recs, fn, want, new, absent) in CASES.items():
        try:
            data, ip = gc.run(build(cid))
        except InterpretError as exc:
            print(f"{cid:4s} {task} {label}: RAISED {exc}")
            fails.append(cid)
            continue
        engine[cid] = (data, ip)
        bad = [(r, prem_all(data, r), v) for r, v in want.items() if not ok_prem(prem_all(data, r), v)]
        msgs = set(ip.messages)
        mbad = [m for m in new if m not in msgs] + [f"not {m}" for m in absent if m in msgs]
        print(f"{cid:4s} {task} {label}: engine {'as derived' if not bad and not mbad else 'DIFFERS'}"
              + (f"; new messages {sorted(msgs - base_msgs)}" if msgs - base_msgs else "")
              + "".join(f"\n        {r}: got {g}, derived {v}" for r, g, v in bad)
              + "".join(f"\n        message: {m}" for m in mbad))
        if bad or mbad:
            fails.append(cid)
    d1, d2 = engine.get("X1a"), engine.get("X1b")
    if d1 and d2:
        p1, p2 = rep.our_prem(d1[0]), rep.our_prem(d2[0])
        diff = [k for k in p1 if "Cannabis" not in k and "ErcCalculatedTotalPremium" not in k and k != "CommercialProperty[0]/Premium"
                and not rep.cmp.same(p1[k], p2.get(k))]
        print(f"X1   engine: every non-Cannabis premium equal with and without the exclusion: "
              f"{'yes' if not diff else diff[:4]} ({len(p1)} compared)")
        if diff:
            fails.append("X1 engine")
    shared_names(fails)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17:")
        iso = {}
        for cid, (task, label, recs, fn, want, new, absent) in CASES.items():
            req = r11.payload(build(cid))
            (gc.OUT / f"chunk15_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid:4s} ISO REFUSES: {m.group(0) if m else str(exc.body)[:160]}")
                if cid not in ("Z5", "Z8"):
                    fails.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk15_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            iso[cid] = resp
            pbad = [(r, iso_all(resp, r), v) for r, v in want.items() if not ok_prem(iso_all(resp, r), v)]
            data, ip = rep.cmp.rate(req)
            ip_, op_ = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, op_.get(k)) for k, v in ip_.items() if not rep.cmp.same(v, op_.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            print(f"  {cid:4s} predicted {'yes' if not pbad else 'NO'}; {'AGREE' if not d else 'DIFFER'} on all {len(ip_)} premiums;"
                  f" messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r}: ISO {x}, derived {v}" for r, x, v in pbad)
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)}; ours only {sorted(mo - mi)}" if mi != mo else ""))
            if pbad or d or mi != mo:
                fails.append(f"{cid} live")
        if "X1a" in iso and "X1b" in iso:
            p1, p2 = rep.iso_prem(iso["X1a"]), rep.iso_prem(iso["X1b"])
            diff = [k for k in p1 if "Cannabis" not in k and "ErcCalculatedTotalPremium" not in k and k != "CommercialProperty[0]/Premium"
                    and not rep.cmp.same(p1[k], p2.get(k))]
            print(f"  X1   ISO: every non-Cannabis premium equal with and without the exclusion: "
                  f"{'yes' if not diff else diff[:4]} ({len(p1)} compared)")
            if diff:
                fails.append("X1 live")
    print(f"\nRC-3: {'ALL AGREE' if not fails else 'FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
