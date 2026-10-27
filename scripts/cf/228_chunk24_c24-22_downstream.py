#!/usr/bin/env python3
"""Chunk 24, C24-22: what Builders Risk feeds downstream. Live ISO.

Each pair rates a policy WITHOUT any Builders Risk family record (every record of the 31 family files removed, the
building itself unchanged) and WITH them. Predicted before running (2026-10-01), from the rule text read in RC-1..RC-4:

  TOTAL       with - base = the sum of the family's premiums as derived in RC-4 (224_'s hand models where the state uses the
              countrywide SetPremium, the independent evaluator on the state's own rule text where it rewrites it)
  NOTHING ELSE MOVES  no family file names Terror / TRIA, and the main ruleset reads Builders Risk only in two blanket
              messages; so every premium outside the family is identical base -> with, terrorism and the TRIA disclosure
              total included; only the building / location / policy totals move. Records the rules attach themselves
              (CP 00 20, CP 11 06) carry no premium
  STAT CODES  every stat value ISO returns on a family record equals ours, strictly as text

  pairs: D1 Oregon's fuller policy (227_), D2 its clean test at 10 x every amount (each rise printed BEFORE its ISO call),
         D3 Florida (its own rules), D4 New York (its own rules and symbols): 8 policies, 8 ISO calls.

    python scripts/cf/228_chunk24_c24-22_downstream.py [--live] [--cases D1,D3]
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

c4 = import_module("227_chunk24_rc4")
d15 = import_module("172_chunk15_c15-19_downstream")
x, t2 = c4.x, c4.t2
m, rc1, rep, cmp, gc = x.m, x.rc1, x.rep, x.cmp, x.gc
P, D, val = x.P, Decimal, x.val
FAIL = []
TOTALISH = re.compile(r"Total|ErcCalculated|TotPremium")
NAMES = sorted(x.RULES, key=len, reverse=True)
FAM = re.compile(r"/" + P + "(?:" + "|".join(map(re.escape, NAMES)) + r")\[")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def strip(sub):
    """remove every Builders Risk family record, tables and singletons, wherever it sits."""
    keys = {P + n + "Table" for n in x.RULES} | {P + n for n in x.RULES}

    def walk(o):
        if isinstance(o, dict):
            for k in [k for k in o if k in keys]:
                o.pop(k)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    sub = copy.deepcopy(sub)
    walk(sub)
    return sub


def x10(sub):
    """the clean test: every Builders Risk amount x 10."""
    amounts = {"Limit", "NewValue", "ManualPremium"}

    def walk(o, fam=False):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, fam or any(k in (P + n + "Table", P + n) for n in x.RULES))
                elif fam and k in amounts and v not in (None, ""):
                    o[k] = str(int(D(str(v)) * 10))
        elif isinstance(o, list):
            for v in o:
                walk(v, fam)
    sub = copy.deepcopy(sub)
    walk(sub)
    return sub


PAIRS = {
    "D1": ("OR", "Oregon's fuller Builders Risk policy", lambda: c4.full_policy("OR")()),
    "D2": ("OR", "the clean test: every Builders Risk amount x 10", lambda: x10(c4.full_policy("OR")())),
    "D3": ("FL", "Florida's fuller policy (its own rules)", lambda: c4.full_policy("FL")()),
    "D4": ("NY", "New York's fuller policy (its own rules and symbols)", lambda: c4.full_policy("NY")()),
}


def family_sum(j, data):
    total, n, kinds = D(0), 0, {"hand": 0, "state evaluator": 0}
    bad = []
    for rec in x.PREMIUM_RECS:
        state_rule = c4.own_setpremium(j, rec)
        for hv, ev, e in x.predict(data, rec):
            deriv = ev if state_rule else hv
            kind = "state evaluator" if state_rule else "hand"
            if isinstance(deriv, str) and re.fullmatch(r"-?\d+(\.\d+)?", deriv):
                deriv = D(deriv)                   # a constant premium ('0.0') the evaluator returns as text
            if deriv is None or isinstance(deriv, str):
                bad.append(f"{rec[-40:]} not derived ({deriv})")
                continue
            if not m.same(deriv, e):
                bad.append(f"{rec[-40:]} {kind} {deriv} engine {e}")
            kinds[kind] += 1
            total += D(str(deriv))
            n += 1
    return total, n, kinds, bad


def predict_pair(cid):
    j, label, build = PAIRS[cid]
    w_sub = build()
    b_sub = strip(w_sub)
    w_req, b_req = (t2.state_req(t2.m20.payload(copy.deepcopy(s_)), j) for s_ in (w_sub, b_sub))
    w, _ = cmp.rate(w_req)
    b, _ = cmp.rate(b_req)
    pb, pw = rep.our_prem(b), rep.our_prem(w)
    left = [k for k in pb if FAM.search(k) and not m.same(pb[k], 0)]
    rise, n, kinds, bad = family_sum(j, w)
    other = [(k, pb[k], pw.get(k)) for k in pb if not FAM.search(k) and not TOTALISH.search(k) and k != f"{P}[0]/Premium"
             and not m.same(pb[k], pw.get(k))]
    new = [k for k in pw if k not in pb and not FAM.search(k) and not m.same(pw[k], 0)]
    terr = [(k, pb.get(k), pw.get(k)) for k in set(pb) | set(pw) if d15.TERR.search(k) and not m.same(pb.get(k), pw.get(k))]
    eng = D(str(pw[d15.TOTAL])) - D(str(pb[d15.TOTAL]))
    print(f"{cid} {j} {label}:\n    family premiums derived {rise} over {n} records ({kinds['hand']} by hand, {kinds['state evaluator']} by the "
          f"state's own rule; = engine: {'yes' if not bad else bad[:3]})"
          f"\n    family records priced in the base: {left[:3] or 'none'}"
          f"\n    every other premium identical base -> with: {'yes' if not other and not new else (other + new)[:4]}"
          f"\n    terrorism / TRIA fields moved: {'none' if not terr else terr[:4]}"
          f"\n    predicted rise {rise}; engine {eng}  {'ok' if eng == rise else 'DIFFERS'}")
    if bad or left or other or new or terr or eng != rise:
        FAIL.append(cid)
    return j, b_req, w_req, rise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    ps = {k: v for k, v in PAIRS.items() if not a.cases or k in a.cases.split(",")}
    preds = {}
    for i, cid in enumerate(ps, 1):
        progress(i, len(ps), f"predict {cid}")
        preds[cid] = predict_pair(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        want = lambda rr: bool(FAM.search("/" + rr + "["))
        print("\nISO live at 2026-09-17: each pair's base and with, every premium, family stat values, messages, the total rise")
        for i, cid in enumerate(ps, 1):
            j, b_req, w_req, rise = preds[cid]
            progress(i, len(ps), f"ISO {cid} (predicted rise {rise})")
            resp = {}
            for tag, req in (("base", b_req), ("with", w_req)):
                (gc.OUT / f"chunk24_c24-22_{cid}_{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                try:
                    resp[tag] = client.rate(req)
                except raas_mod.RaaSError as exc:
                    print(f"  {cid} {tag} ISO REFUSES {str(exc.body)[:240]}")
                    FAIL.append(f"{cid} {tag} live")
                    continue
                (gc.OUT / f"chunk24_c24-22_{cid}_{tag}_response.json").write_text(json.dumps(resp[tag], indent=2), encoding="utf-8")
                data, ip = cmp.rate(req)
                ipr, opr = rep.iso_prem(resp[tag]), rep.our_prem(data)
                dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
                ist, ost = d15.iso_fields(resp[tag], want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
                ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
                mi, mo = cmp.iso_messages(resp[tag]), set(ip.messages)
                ok = not dd and not ds and mi == mo
                print(f"  {cid} {tag}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} family stat values, "
                      f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[tag]):,.0f}"
                      + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5])
                      + (f"\n      ISO only {sorted(mi - mo)[:3]}\n      ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
                if not ok:
                    FAIL.append(f"{cid} {tag} live")
            if len(resp) == 2:
                got = D(str(d15.total_of(resp["with"]))) - D(str(d15.total_of(resp["base"])))
                print(f"  {cid} total rise at ISO {got}; predicted before the call {rise}  {'ok' if got == rise else 'DIFFERS'}")
                if got != rise:
                    FAIL.append(f"{cid} rise")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC24-22: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
