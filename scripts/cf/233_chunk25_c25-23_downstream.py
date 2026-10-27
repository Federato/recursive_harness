#!/usr/bin/env python3
"""Chunk 25, C25-23: what Flood feeds downstream. Live ISO.

Each pair rates a policy WITHOUT flood (every record of the 8 family files removed, FloodCovIndicator and
FloodCovEndtBlktIndicator "No", the buildings / contents / special class / BI themselves unchanged) and WITH it. Predicted
before running (2026-10-02), from the rule text read in RC-1..RC-4:

  TOTAL       with - base = the sum of the family's premiums as derived in RC-4 (232_: 229_'s hand models with the state's
              tables and edition, the state's own rule where it rewrites SetPremium, the manual premium in AK / FL)
  NOTHING ELSE MOVES  no rule outside the family reads a flood premium (searched: no FromDataDef ending in a flood record's
              Premium / ManualPremium / PremiumIndicator, and no terrorism rule names flood); the flood cyber factors and
              FloodTotalPropertyValue are read only by flood records; so every premium outside the family is identical
              base -> with, terrorism included; only the location / policy totals move
  STAT CODES  every stat value ISO returns on a family record equals ours, strictly as text

  pairs: D1 Oregon's two-location flood policy with a blanket (232_'s S-OR), D2 the same with every flood limit halved
         (a clean test: ITV and the rate-modification factors move; each rise printed BEFORE its ISO call), D3 New York
         (county table, its own premium rules), D4 Alaska (company-entered premiums), D5 Missouri (its V02 rules)

    python scripts/cf/233_chunk25_c25-23_downstream.py [--live] [--cases D1,D3]
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

c4 = import_module("232_chunk25_rc4")
d15 = import_module("172_chunk15_c15-19_downstream")
x, t2 = c4.x, c4.t2
m, rc1, rep, cmp, gc = x.m, x.rc1, x.rep, x.cmp, c4.gc
P, D = x.P, Decimal
FAIL = []
TOTALISH = re.compile(r"Total|ErcCalculated|TotPremium")
NAMES = sorted(x.FAMILY, key=len, reverse=True)
FAM = re.compile(r"/" + P + "(?:" + "|".join(map(re.escape, NAMES)) + r")\[")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def strip(sub):
    """remove every flood family record and switch flood off at the locations and the policy."""
    keys = {P + n + "Table" for n in x.FAMILY} | {P + n for n in x.FAMILY}

    def walk(o):
        if isinstance(o, dict):
            for k in [k for k in o if k in keys]:
                o.pop(k)
            if "FloodCovIndicator" in o:
                o["FloodCovIndicator"] = "No"
            if "FloodCovEndtBlktIndicator" in o:
                o["FloodCovEndtBlktIndicator"] = "No"
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    sub = copy.deepcopy(sub)
    walk(sub)
    return sub


def halve(sub):
    """the clean test: every flood record's Limit halved (the blanket detail's too)."""
    def walk(o, fam=False):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, fam or any(k in (P + n + "Table", P + n) for n in x.FAMILY))
                elif fam and k == "Limit" and v not in (None, ""):
                    o[k] = str(int(D(str(v)) / 2))
        elif isinstance(o, list):
            for v in o:
                walk(v, fam)
    sub = copy.deepcopy(sub)
    walk(sub)
    return sub


PAIRS = {
    "D1": ("OR", "Oregon's two-location flood policy with a blanket", lambda: c4.state_policy("OR")()),
    "D2": ("OR", "the clean test: every flood limit halved", lambda: halve(c4.state_policy("OR")())),
    "D3": ("NY", "New York (county table, its own premium rules)", lambda: c4.state_policy("NY")()),
    "D4": ("AK", "Alaska (company-entered premiums)", lambda: c4.state_policy("AK")()),
    "D5": ("MO", "Missouri (its CW 2023 V02 rules)", lambda: c4.state_policy("MO")()),
}


def predict_pair(cid):
    j, label, build = PAIRS[cid]
    w_sub = build()
    b_sub = strip(w_sub)
    w_req, data_w, ip_w, preds = c4.predict(cid, ("C25-23", j, label, lambda: copy.deepcopy(w_sub)))
    b_req = t2.state_req(t2.m20.payload(copy.deepcopy(b_sub)), j)
    b, _ = cmp.rate(b_req)
    pb, pw = rep.our_prem(b), rep.our_prem(data_w)
    rise = sum((D(str(v)) for vs in preds.values() for v in vs if not isinstance(v, str)), D(0))
    left = [k for k in pb if FAM.search(k) and not m.same(pb[k], 0)]
    other = [(k, pb[k], pw.get(k)) for k in pb if not FAM.search(k) and not TOTALISH.search(k) and k != f"{P}[0]/Premium"
             and not m.same(pb[k], pw.get(k))]
    new = [k for k in pw if k not in pb and not FAM.search(k) and not m.same(pw[k], 0)]
    terr = [(k, pb.get(k), pw.get(k)) for k in set(pb) | set(pw) if d15.TERR.search(k) and not m.same(pb.get(k), pw.get(k))]
    eng = D(str(pw[d15.TOTAL])) - D(str(pb[d15.TOTAL]))
    print(f"    family records priced in the base: {left[:3] or 'none'}"
          f"\n    every other premium identical base -> with: {'yes' if not other and not new else (other + new)[:4]}"
          f"\n    terrorism / TRIA fields moved: {'none' if not terr else terr[:4]}"
          f"\n    predicted rise {rise}; engine {eng}  {'ok' if eng == rise else 'DIFFERS'}")
    if left or other or new or terr or eng != rise:
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
    FAIL.extend(f for f in c4.FAIL if f not in FAIL)
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
                (gc.OUT / f"chunk25_c25-23_{cid}_{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                try:
                    resp[tag] = client.rate(req)
                except raas_mod.RaaSError as exc:
                    print(f"  {cid} {tag} ISO REFUSES {str(exc.body)[:240]}")
                    FAIL.append(f"{cid} {tag} live")
                    continue
                (gc.OUT / f"chunk25_c25-23_{cid}_{tag}_response.json").write_text(json.dumps(resp[tag], indent=2), encoding="utf-8")
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
                if not ok and not (j == "MO" and not dd and not ds):
                    FAIL.append(f"{cid} {tag} live")
                elif not ok:
                    print(f"      (MO: messages only, OI-123)")
            if len(resp) == 2:
                got = D(str(d15.total_of(resp["with"]))) - D(str(d15.total_of(resp["base"])))
                print(f"  {cid} total rise at ISO {got}; predicted before the call {rise}  {'ok' if got == rise else 'DIFFERS'}")
                if got != rise:
                    FAIL.append(f"{cid} rise")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC25-23: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
