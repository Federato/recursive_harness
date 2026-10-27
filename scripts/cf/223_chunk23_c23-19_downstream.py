#!/usr/bin/env python3
"""Chunk 23, C23-19: what the state-only families feed downstream. Live ISO.

Each pair rates a state's policy WITHOUT its chunk 23 family (every record of the family's files removed) and WITH it.
Predicted before running (2026-10-01), from the rule text read in RC-1..RC-4:

  TOTAL      with - base = the sum of the family's premiums by hand (219_'s hand models), leaves only: a family record that
             holds another family record (a container) is not added twice; MA's Pollutant Clean Up credit is its own
             negative record (HOC), so it is in that sum
  NOTHING ELSE MOVES  no family file reads or writes terrorism (none names Terror / TRIA), and none writes a field another
             record prices on, so every premium outside the family is identical base -> with, terrorism and the TRIA
             disclosure total included; only the policy / location / building totals move
  STAT CODES every stat value ISO returns on a family record equals ours, strictly as text

  pairs: the four fuller policies of RC-4 (F-MA two locations, F-AK Legal Liability + an ordinary building, F-CA two
  buildings, F-VA three forms on three buildings) and the four RC-2 golden policies (H1, the AK 10 x / 4 x limits, CA's
  1,000,000 building, VA's 200,000 / 300,000 broad form): 8 pairs, 16 ISO calls.

    python scripts/cf/223_chunk23_c23-19_downstream.py [--live] [--cases F-MA,G-VA]
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

t4 = import_module("222_chunk23_rc4")
d15 = import_module("172_chunk15_c15-19_downstream")
t2, m = t4.t2, t4.m
rc1, gc, rep, cmp = m.rc1, m.gc, m.rep, m.cmp
P, D = m.P, m.D
FAIL = []
TOTALISH = re.compile(r"Total|ErcCalculated|TotPremium|^CommercialProperty\[0\]/Premium$")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def fam_re(j):
    """a premium path belongs to the family when one of its segments is a family record (longest names first)."""
    names = sorted(m.FILES[j], key=len, reverse=True)
    return re.compile(r"/" + P + "(?:" + "|".join(map(re.escape, names)) + r")\[")


def strip(sub, j):
    """remove every record of the state's family files, wherever it sits."""
    tables = {P + n + "Table" for n in m.FILES[j]}

    def walk(o):
        if isinstance(o, dict):
            for k in [k for k in o if k in tables]:
                o.pop(k)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    sub = copy.deepcopy(sub)
    walk(sub)
    return sub


def pairs():
    return {
        "F-MA": ("MA", t4.f_ma), "F-AK": ("AK", t4.f_ak), "F-CA": ("CA", t4.f_ca), "F-VA": ("VA", t4.f_va),
        "G-MA": ("MA", t2.ma()), "G-AK": ("AK", t2.ak()), "G-CA": ("CA", t2.ca()), "G-VA": ("VA", t2.va()),
    }


def descendants(node):
    stack = list(node.children)
    while stack:
        x = stack.pop()
        yield x
        stack.extend(x.children)


def hand_family(j, data):
    """sum of the family's leaf premiums by hand; any hand / evaluator / engine disagreement reported."""
    recs = m.PREMIUM_RECS[j]
    tags = {P + r_ for r_ in recs}
    total, bad, n = D(0), [], 0
    for rec in recs:
        for node, (hv, ev, e) in zip(m.find(data, rec), m.predict(j, data, rec)):
            if not (m.same(hv, e) and m.same(ev, e)):
                bad.append((rec, hv, ev, e))
            if any(x.tag in tags for x in descendants(node)):
                continue                       # a container: its leaves are counted
            total += D(str(hv or 0))
            n += 1
    return total, bad, n


def predict_pair(cid):
    j, build = pairs()[cid]
    w_sub = build()
    b_sub = strip(w_sub, j)
    b, _, eb = m.rated(b_sub, j)
    w, _, ew = m.rated(w_sub, j)
    if eb or ew:
        print(f"{cid} {j}: engine RAISED {eb or ew}")
        FAIL.append(cid)
        return None
    fam = fam_re(j)
    pb, pw = rep.our_prem(b), rep.our_prem(w)
    # the rules attach some family records themselves (AK fees, MA credit, CA Limited EQ via the location EQ form): in the base
    # they must exist only at $0
    auto = [k for k in pb if fam.search(k)]
    left = [k for k in auto if not m.same(pb[k], 0)]
    hand, bad, n = hand_family(j, w)
    other = [(k, pb[k], pw.get(k)) for k in pb if not fam.search(k) and not TOTALISH.search(k.split("/")[-1])
             and not TOTALISH.search(k) and not m.same(pb[k], pw.get(k))]
    new = [k for k in pw if k not in pb and not fam.search(k) and not m.same(pw[k], 0)]
    terr = [(k, pb.get(k), pw.get(k)) for k in set(pb) | set(pw) if d15.TERR.search(k) and not m.same(pb.get(k), pw.get(k))]
    eng = D(str(pw[d15.TOTAL])) - D(str(pb[d15.TOTAL]))
    print(f"{cid} {j}:\n    family premiums by hand {hand} over {n} leaf records (hand = evaluator = engine: {'yes' if not bad else bad[:3]})"
          f"\n    family records in the base: {len(auto)} attached by the rules themselves, priced: {left[:3] or 'none ($0)'}"
          f"\n    every other premium identical base -> with: {'yes' if not other and not new else (other + new)[:4]}"
          f"\n    terrorism / TRIA fields moved: {'none' if not terr else terr[:4]}"
          f"\n    predicted rise {hand}; engine {eng}  {'ok' if eng == hand else 'DIFFERS'}")
    if bad or left or other or new or terr or eng != hand:
        FAIL.append(cid)
    return j, b_sub, w_sub, hand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    ps = pairs()
    if a.cases:
        ps = {k: v for k, v in ps.items() if k in a.cases.split(",")}
    preds = {}
    for i, cid in enumerate(ps, 1):
        progress(i, len(ps), f"predict {cid}")
        preds[cid] = predict_pair(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17: each pair's base and with, every premium, family stat values, messages, the total rise")
        for i, cid in enumerate(ps, 1):
            if not preds.get(cid):
                continue
            j, b_sub, w_sub, hand = preds[cid]
            want = lambda rr, _f=fam_re(j): bool(_f.search("/" + rr + "["))
            progress(i, len(ps), f"ISO {cid} (predicted rise {hand})")
            resp = {}
            for tag, sub in (("base", b_sub), ("with", w_sub)):
                req = t2.state_req(t2.m20.payload(copy.deepcopy(sub)), j)
                (gc.OUT / f"chunk23_c23-19_{cid}_{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                try:
                    resp[tag] = client.rate(req)
                except raas_mod.RaaSError as exc:
                    print(f"  {cid} {tag} ISO REFUSES {str(exc.body)[:200]}")
                    FAIL.append(f"{cid} {tag} live")
                    continue
                (gc.OUT / f"chunk23_c23-19_{cid}_{tag}_response.json").write_text(json.dumps(resp[tag], indent=2), encoding="utf-8")
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
                rise = D(str(d15.total_of(resp["with"]))) - D(str(d15.total_of(resp["base"])))
                print(f"  {cid} total rise at ISO {rise}; predicted before the call {hand}  {'ok' if rise == hand else 'DIFFERS'}")
                if rise != hand:
                    FAIL.append(f"{cid} rise")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC23-19: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
