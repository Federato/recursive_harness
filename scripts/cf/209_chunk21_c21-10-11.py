#!/usr/bin/env python3
"""Chunk 21, C21-10 zero cases and C21-11 messages, live ISO.

Builds on 208_ (its builders, hand models and payload). Each case predicts, from the rules as read
(2026-09-30), every premium of its records, the messages that must FIRE and those that must stay SILENT,
or an ISO refusal. The engine must match; --live ISO must match the predicted premiums, every premium on
the policy must equal ours, and ISO's whole message set must equal ours.

C21-10 zero cases (predict both readings; the engine's reading first):
  Z1  sewer PD, limit BLANK: Divide(blank, 100) is blank and Product skips it -> Rate x factor x modifiers,
      each rounded to 0 places = $1 / blank read as 0 = $0            (the C21-02 probe)
  Z2  sewer BI, limit blank: 0.07 rounds to 0 either way = $0
  Z3  sewer PD limit 0: $0                Z4  sewer PD at the building's own limit 100,000: priced, no cap message
  Z5  loss assessment "0", no misc. real property: both $0; "requires either" and "only valid" fire
  Z6  sub-limit 5,000 with loss assessment "0": $0; "sub limit cannot be greater" fires (limit to use 0)
  Z7  the options record with NEITHER limit (loss assessment blank): ISO refuses at LossAssessmentRate,
      ours $0 (OI-103, as 208_ MRZ)
  Z8  FL building record, CovType not Condominium Association: $0, CP 01 54 CovType message
  Z9  FL occupancy record on an SPP policy: $0, CP 01 54 PolicyType message
  Z10 FL occupancy record, manual premium blank: FirstValue -> 0 = $0 (both readings)
  Z11 FL special class record, manual premium blank: the rule CONVERTS the text; ours reads blank and
      Product skips it -> IRPM x package mod 0.9775 -> $1 / $0 or a refusal. ISO REFUSES (it cannot convert
      a blank string to a decimal): OI-117, pinned as a predicted refusal

C21-11 messages, each triggered and silent (24 of the census's 26; the other two are Green Upgrades
CP 04 02 wording matches owned by another chunk):
  M1/M2   the five sewer caps (limit > the parent's LimitToUse): all at 100,001 fire; all at 100,000 silent
  M3/M4   sub-limit greater than the loss assessment limit: 6,000 over 5,000 fires; 5,000 silent
  M5/M6   sub-limit multiple of 1,000: 11,500 fires; 3,000 and 3,500 BOTH silent (checked only above 10,000)
  M7/M8   Over 10,000 multiple of 5,000: 17,500 fires; 15,000 silent (12,000 silent: 208_ LA6)
  M9/M10  CW CP 04 18 only valid with unit owners (reads the CONTENTS' CovForm, which SetCovForm copies
          from the occupancy unconditionally: a contents CovForm sent alone is overwritten) / requires a limit
  RI, FL, UT: the state form's "only valid" and "requires either" pairs; GA's two valuation messages;
  FL's six CP 01 54 attach messages (CovForm / CovType, PolicyType; occupancy, special class, building)

    python scripts/cf/209_chunk21_c21-10-11.py [--live] [--cases Z1,M1]

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
import _iso_refusals as _iso                                    # noqa: E402

m8 = import_module("208_chunk21_rc2")
h21, r2, g19, rc1, r16, gc, rep, cmp = m8.h21, m8.r2, m8.g19, m8.rc1, m8.r16, m8.gc, m8.rep, m8.cmp
P, SEWER, LA, MRP, OPT, UO = m8.P, m8.SEWER, m8.LA, m8.MRP, m8.OPT, m8.UO
BLDG, PP, SC, BI, SCBI = SEWER
FLR, FLSPP = m8.FLR, m8.FLSPP
same = r2.same
FAIL = []
D = Decimal
SPP = "Standard Property Policy"

# message texts (substrings)
CAP = "Limit on CP 10 38 must not be greater than the "
CAPS = [CAP + w + " limit" for w in ("Building", "Personal Property", "Special Class", "Business Income",
                                      "Special Class Business Income")]
SUBGT = "Loss Assessment Sub Limit cannot be greater"
M1000 = "SubLimit needs to be multiple of 1000"
M5000 = "Over $10,000 needs to be multiple of 5000"
ONLY = "{f} is only valid"
REQ = "{f} requires either a Loss Assessment Limit or a Miscellaneous Real Property Limit"
CP0154_FORM = "CP 01 54 Cannot Be Attached If CovForm"
CP0154_POL = "CP 01 54 Cannot Be Attached If PolicyType"
UT_WITH = "Form CP 04 22 can only be used with either form CP 00 18 or form CP 17 98"
GA_VAL = "Valuation Type selection must be Replacement Cost when CP 17 01"


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


# ---------------------------------------------------------------- builders

def portable(j, cause="Special"):
    sub = g19.with_cause(g19.portable(j), cause)
    if j != "OR":
        m8.no_eq(sub)
        if j == "FL":
            rc1.node_dicts(sub)[P + "SpecialClass"]["ClassDescription"] = m8.FL_SC
    return sub


def with_(build, *edits):
    def b():
        sub = build()
        for e in edits:
            e(sub)
        return sub
    return b


def at(sub, k=""):
    return rc1.node_dicts(sub)[P + k]


def opts(j, cont, recs=(LA, MRP)):
    def b():
        sub = portable(j)
        at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [dict(cont, **{P + r: {} for r in recs})]}
        return sub
    return b


def sew(limits):
    def b():
        sub = portable("OR")
        for rec, lim in limits.items():
            r2.put(sub, rec, {} if lim is None else {SEWER[rec]: str(lim)})
        return sub
    return b


def fl_rec(rec, fields, policy="Commercial Property Policy", covform=None, covtype=None):
    def b():
        sub = portable("FL")
        at(sub)["PolicyType"] = policy
        if covform:
            at(sub, "OccupClass" if rec.endswith("OccupClass") else "SpecialClass")["CovForm"] = covform
        if covtype:
            at(sub, "Structure")["CovType"] = covtype
        r2.put(sub, rec, fields, state="FL")
        return sub
    return b


def cases():
    c = {}

    def add(cid, task, j, label, build, recs, expect=None, fire=(), silent=(), refuse=None, oi="OI-103"):
        c[cid] = dict(task=task, j=j, label=label, build=build, recs=recs, expect=expect or {},
                      fire=list(fire), silent=list(silent), refuse=refuse, oi=oi)

    # ---- C21-10 zero cases
    add("Z1", "C21-10", "OR", "sewer PD, limit blank (engine $1: Product skips the blank limit)", sew({BLDG: None}), [BLDG],
        {BLDG: [D(1)]}, silent=CAPS)
    add("Z2", "C21-10", "OR", "sewer BI, limit blank ($0 either way)", sew({BI: None}), [BI], {BI: [D(0)]})
    add("Z3", "C21-10", "OR", "sewer PD, limit 0", sew({BLDG: 0}), [BLDG], {BLDG: [D(0)]}, silent=CAPS)
    add("Z4", "C21-10", "OR", "sewer PD at the building's own limit 100,000 (no cap message)", sew({BLDG: 100000}), [BLDG],
        silent=CAPS)
    add("Z5", "C21-10", "OR", "loss assessment \"0\", no misc. real property", opts("OR", {"LossAssessmentLimit": "0"}),
        [LA, MRP], {LA: [D(0)], MRP: [D(0)]}, fire=[REQ.format(f="CP 04 18"), ONLY.format(f="CP 04 18")])
    add("Z6", "C21-10", "OR", "sub-limit 5,000 with loss assessment \"0\"",
        opts("OR", {"LossAssessmentLimit": "0", "LossAssessmentSubLimit": "5000"}), [LA], {LA: [D(0)]},
        fire=[SUBGT, REQ.format(f="CP 04 18")])
    add("Z7", "C21-10", "OR", "OI-103: the options record with neither limit (loss assessment blank)", opts("OR", {}), [LA],
        {LA: [D(0)]}, refuse="LossAssessmentRate")
    add("Z8", "C21-10", "FL", "FL building record, CovType not Condominium Association",
        fl_rec(FLR, {"ManualPremium": "250"}), [FLR], {FLR: [D(0)]}, fire=[CP0154_FORM])
    add("Z9", "C21-10", "FL", "FL occupancy record on an SPP policy",
        fl_rec(FLR + "OccupClass", {"ManualPremium": "100"}, policy=SPP, covform=UO), [FLR + "OccupClass"],
        {FLR + "OccupClass": [D(0)]}, fire=[CP0154_POL], silent=[CP0154_FORM])
    add("Z10", "C21-10", "FL", "FL occupancy record, manual premium blank",
        fl_rec(FLR + "OccupClass", {}, covform=UO), [FLR + "OccupClass"], {FLR + "OccupClass": [D(0)]},
        silent=[CP0154_FORM, CP0154_POL])
    # first sent 2026-09-30: ISO REFUSES ("Unable to convert value  from type System.String to type
    # System.Decimal"); ours reads the blank and prices $1 -> OI-117, pinned
    add("Z11", "C21-10", "FL", "OI-117: FL special class record, manual premium blank (ISO refuses the Convert; ours $1)",
        fl_rec(FLR + "SpecClass", {}, covform=UO), [FLR + "SpecClass"], {FLR + "SpecClass": [D(1)]},
        silent=[CP0154_FORM, CP0154_POL], refuse="Unable to convert value", oi="OI-117")

    # ---- C21-11 messages, triggered / silent
    add("M1", "C21-11", "OR", "sewer caps: all five at 100,001 (fire)", sew({r: 100001 for r in SEWER}), list(SEWER), fire=CAPS)
    add("M2", "C21-11", "OR", "sewer caps: all five at 100,000 (silent)", sew({r: 100000 for r in SEWER}), list(SEWER),
        silent=CAPS)
    la8 = {"LossAssessmentDeductible": "250"}
    add("M3", "C21-11", "OR", "sub-limit 6,000 over a 5,000 limit (fires)",
        opts("OR", dict(la8, LossAssessmentLimit="5,000", LossAssessmentSubLimit="6000"), [LA]), [LA], fire=[SUBGT])
    add("M4", "C21-11", "OR", "sub-limit 5,000 at a 5,000 limit (silent)",
        opts("OR", dict(la8, LossAssessmentLimit="5,000", LossAssessmentSubLimit="5000"), [LA]), [LA], silent=[SUBGT])
    add("M5", "C21-11", "OR", "sub-limit 11,500 (fires: not a multiple above 10,000)",
        opts("OR", dict(la8, LossAssessmentLimit="Over 10,000", LossAssessmentLimitOver10000="20000",
                        LossAssessmentSubLimit="11500"), [LA]), [LA], fire=[M1000])
    for cid, s in (("M6a", "3000"), ("M6b", "3500")):
        add(cid, "C21-11", "OR", f"sub-limit {s} (silent: the check runs only above 10,000)",
            opts("OR", dict(la8, LossAssessmentLimit="5,000", LossAssessmentSubLimit=s), [LA]), [LA], silent=[M1000])
    add("M7", "C21-11", "OR", "Over 10,000 = 17,500 (fires)",
        opts("OR", dict(la8, LossAssessmentLimit="Over 10,000", LossAssessmentLimitOver10000="17500"), [LA]), [LA], fire=[M5000])
    add("M8", "C21-11", "OR", "Over 10,000 = 15,000 (silent)",
        opts("OR", dict(la8, LossAssessmentLimit="Over 10,000", LossAssessmentLimitOver10000="15000"), [LA]), [LA], silent=[M5000])
    good = {"LossAssessmentLimit": "0", "MiscRealPropLimit": "20000"}
    none = {"LossAssessmentLimit": "0"}
    for j, form in (("OR", "CP 04 18"), ("RI", "CP 04 20"), ("FL", "CP 04 21"), ("UT", "CP 04 22")):
        k = {"OR": "CW", "RI": "RI", "FL": "FL", "UT": "UT"}[j]
        add(f"R-{k}1", "C21-11", j, f"{form} requires either: neither limit (fires)", opts(j, none, [MRP]), [MRP],
            {MRP: [D(0)]}, fire=[REQ.format(f=form)])
        add(f"R-{k}2", "C21-11", j, f"{form} requires either: misc. real property 20,000 (silent)", opts(j, good, [MRP]), [MRP],
            silent=[REQ.format(f=form)])
    # "only valid with unit owners": CW reads the CONTENTS' CovForm, RI the occupancy's; FL / UT test for the
    # unit-owners coverage-form record (CP 00 18) that the occupancy's CovForm attaches
    add("V-CW1", "C21-11", "OR", "CP 04 18 only valid: contents on the policy's form (fires)", opts("OR", good, [MRP]), [MRP],
        fire=[ONLY.format(f="CP 04 18")])
    # PersonalProperty.SetCovForm COPIES the occupancy's CovForm over the contents' unconditionally
    # (found 2026-09-30: first predicted silent), so a contents CovForm sent alone does not stand
    add("V-CW2", "C21-11", "OR", "CP 04 18 only valid: contents CovForm unit owners SENT, occupancy not (fires: overwritten)",
        with_(opts("OR", good, [MRP]), lambda s: at(s, "PersonalProperty").__setitem__("CovForm", UO)), [MRP],
        fire=[ONLY.format(f="CP 04 18")])
    add("V-CW3", "C21-11", "OR", "CP 04 18 only valid: occupancy CovForm unit owners (silent)",
        with_(opts("OR", good, [MRP]), lambda s: at(s, "OccupClass").__setitem__("CovForm", UO)), [MRP],
        silent=[ONLY.format(f="CP 04 18")])
    for j, msg in (("RI", ONLY.format(f="CP 04 20")), ("FL", "CP 04 21 is only valid"), ("UT", UT_WITH)):
        add(f"V-{j}1", "C21-11", j, f"{msg[:26]}: occupancy on the policy's form (fires)", opts(j, good, [MRP]), [MRP], fire=[msg])
        add(f"V-{j}2", "C21-11", j, f"{msg[:26]}: occupancy CovForm unit owners (silent)",
            with_(opts(j, good, [MRP]), lambda s: at(s, "OccupClass").__setitem__("CovForm", UO)), [MRP], silent=[msg])
    # FL CP 01 54: CovForm / CovType, and PolicyType, on each of the three CPP records
    for rec, kind, where in ((FLR + "OccupClass", "covform", "occupancy"), (FLR + "SpecClass", "covform", "special class"),
                             (FLR, "covtype", "building")):
        right = {"covform": UO} if kind == "covform" else {"covtype": "Condominium Association"}
        add(f"F-{where[:4]}1", "C21-11", "FL", f"CP 01 54 on the {where}: wrong form (fires)",
            fl_rec(rec, {"ManualPremium": "100"}), [rec], {rec: [D(0)]}, fire=[CP0154_FORM])
        add(f"F-{where[:4]}2", "C21-11", "FL", f"CP 01 54 on the {where}: right form, CPP (silent)",
            fl_rec(rec, {"ManualPremium": "100"}, **right), [rec], silent=[CP0154_FORM, CP0154_POL])
        add(f"F-{where[:4]}3", "C21-11", "FL", f"CP 01 54 on the {where}: right form, SPP (PolicyType fires)",
            fl_rec(rec, {"ManualPremium": "100"}, policy=SPP, **right), [rec], {rec: [D(0)]}, fire=[CP0154_POL])
    # GA CP 17 01: the unit owners SPP changes record attaches on an SPP policy with the unit owners form;
    # the valuation message then tests the contents' / special class's ValuationType
    def ga(where, val):
        def e(s):
            at(s)["PolicyType"] = SPP
            at(s, "OccupClass" if where == "PersonalProperty" else "SpecialClass")["CovForm"] = UO
            at(s, where)["ValuationType"] = val
        return with_(lambda: portable("GA"), e)
    for where in ("PersonalProperty", "SpecialClass"):
        add(f"G-{where[:2]}1", "C21-11", "GA", f"GA CP 17 01 on the {where}: valuation Actual Cash Value (fires)",
            ga(where, "Actual Cash Value"), [], fire=[GA_VAL])
        add(f"G-{where[:2]}2", "C21-11", "GA", f"GA CP 17 01 on the {where}: valuation Replacement Cost (silent)",
            ga(where, "Replacement Cost"), [], silent=[GA_VAL])
    return c


# ---------------------------------------------------------------- run

def engine_premiums(data, rec, expect):
    """(predicted, engine) per node; the prediction is the explicit one, else 208_'s hand models."""
    res = []
    if rec in expect:
        got = [None if n.first("Premium") is None else n.first("Premium").text for n in rc1.find(data, P + rec)]
        return list(zip(expect[rec], got + [None] * (len(expect[rec]) - len(got))))
    for hand, _ev, e in m8.predict(data, rec):
        res.append((hand, e))
    return res


def msg_check(msgs, fire, silent):
    bad = [f"missing: {f[:70]}" for f in fire if not any(f in m for m in msgs)]
    bad += [f"unexpected: {s[:70]}" for s in silent if any(s in m for m in msgs)]
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, c) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(c["build"](), c["j"])
        except InterpretError as exc:
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                continue
            print(f"{cid} {c['task']} {c['j']} {c['label']}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        msgs = [str(x) for x in ip.messages]
        lines, bad = [], []
        preds[cid] = {}
        for rec in c["recs"]:
            res = engine_premiums(data, rec, c["expect"])
            ok = bool(res) and all(p is not None and e is not None and same(p, e) for p, e in res)
            preds[cid][rec] = [p for p, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[-44:]:44s} predicted {[str(p) for p, _ in res]} "
                         f"engine {[e for _, e in res]}")
            if not ok:
                bad.append(rec)
        mb = msg_check(msgs, c["fire"], c["silent"])
        print(f"{cid} {c['task']} {c['j']} {c['label']}: engine {'as predicted' if not bad and not mb else 'DIFFERS'}"
              + (f"  {mb}" if mb else ""))
        if lines:
            print("\n".join(lines))
        if bad or mb:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, the whole message set):")
        for i, (cid, c) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = m8.payload(c["build"](), c["j"])
            (gc.OUT / f"chunk21_c21-10-11_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                what = mm.group(0)[:220] if mm else str(exc.body)[:220]
                if c["refuse"] and c["refuse"] in what:
                    print(f"  {cid} REFUSES AS PREDICTED ({c['oi']}; ours rates): {what}")
                    continue
                print(f"  {cid} ISO REFUSES {what}")
                FAIL.append(f"{cid} live")
                continue
            if c["refuse"]:
                print(f"  {cid} ISO RATED where a refusal was predicted")
                FAIL.append(f"{cid} live")
            (gc.OUT / f"chunk21_c21-10-11_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in c["recs"]:
                want = [w for w in preds.get(cid, {}).get(rec, []) if w is not None and not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(D(str(x)) for x in iso) != sorted(D(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            mb = msg_check([str(x) for x in mi], c["fire"], c["silent"])
            ok = not pbad and not d and mi == mo and not mb
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted {len(c['recs']) - len(pbad)} of {len(c['recs'])} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + (f"; fire/silent on ISO: {mb}" if mb else "")
                  + "".join(f"\n        predicted {r16.short(r)[-50:]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(str(x)[:100] for x in mi - mo)[:3]}\n        ours only {sorted(str(x)[:100] for x in mo - mi)[:3]}"
                     if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC21-10 / C21-11: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
