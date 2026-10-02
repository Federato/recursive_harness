#!/usr/bin/env python3
"""Chunk 26, C26-20: what Specific rating feeds downstream. Live ISO.

Each pair rates the same policy CLASS-rated (base) and SPECIFIC-rated (with). Predicted before running (2026-10-02):

  TOTAL       with - base = the sum, over the core building / contents / BI coverage records, of (with - base), each side
              priced by 174_'s evaluator on the state's own SetPremium with the rates by hand (234_; the base's class rates
              are chunks 1-8's, ISO-confirmed)
  NOTHING ELSE MOVES  the Specific branch writes only BasicGroupIRate / BasicGroupIIRate (and the identification code); every
              other premium, terrorism included, is identical base -> with; only the totals move
  STAT CODES  every stat value and RatingIdentificationCode ISO returns on the building, contents and BI equals ours, as text
              (Class 2, Specific 1 on the building and BI)

  pairs: D1 OR (G1's policy), D2 the clean test: Specific rates doubled (0.600 / 0.400), its rise printed BEFORE the call,
         D3 FL (its single-rounding shape, no roof factor), D4 SC Group II Class -> Specific (0.060 / 0.050, Inland),
         D5 MO (CW 2023 V02: BI on the building's final rate)

    python scripts/cf/238_chunk26_c26-20_downstream.py [--live] [--cases D1,D4]
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

c4 = import_module("237_chunk26_rc4")
c3, c2, h, t2, m, rc1, rep, cmp, gc = c4.c3, c4.c2, c4.h, c4.t2, c4.m, c4.rc1, c4.rep, c4.cmp, c4.gc
d15 = import_module("172_chunk15_c15-19_downstream")
P, D = c4.P, Decimal
FAIL = []
TOTALISH = re.compile(r"Total|ErcCalculated|TotPremium")
CORE = re.compile(r"/" + P + r"(StructureBuilding|PersonalPropertyPrsnlProp|BusinessIncome)(BasicGroupI|BasicGroupII|Broad|Special)Coverage\[")
WANT_REC = lambda rr: bool(re.fullmatch(P + r"(Structure|PersonalProperty|BusinessIncome)", "".join(rr.split("/")[-1:]) if False else rr) or CORE.search("/" + rr + "["))
WANT_FIELD = lambda f: bool(d15.STAT.search(f)) or f == "RatingIdentificationCode"


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def sc_pair(gii):
    def b():
        sub = c3.SC_G("Charleston", 20000)()
        if not gii:
            m.at(sub)[P + "Structure"]["RatingTypeBasicGroupII"] = "Class"
        return sub
    return b


def with_rt(build, rt):
    def b():
        sub = build()
        m.at(sub)[P + "Structure"]["RatingType"] = rt
        return sub
    return b


PAIRS = {
    "D1": ("OR", "Oregon: G1's policy, Class -> Specific (0.300 / 0.200)", with_rt(h.tree, "Class"), h.tree),
    "D2": ("OR", "the clean test: Specific rates doubled (0.600 / 0.400)", with_rt(h.tree, "Class"), lambda: h.tree(s1="0.600", pp_s1="0.400")),
    "D3": ("FL", "Florida (single rounding, no roof factor)", with_rt(c4.state_policy("FL"), "Class"), c4.state_policy("FL")),
    "D4": ("SC", "South Carolina Group II Class -> Specific (Inland, Severe, 20,000 sq ft)", sc_pair(False), sc_pair(True)),
    "D5": ("MO", "Missouri (CW 2023 V02)", with_rt(c4.state_policy("MO"), "Class"), c4.state_policy("MO")),
}


def core_sum(data, j):
    rates, prem, bad = c2.derive(data, j)
    tot = D(0)
    for key, vs in prem.items():
        for ev, e in vs:
            if isinstance(ev, str):
                bad.append(f"{key} not derived ({ev})")
                continue
            tot += D(str(ev))
    return tot, prem, rates, bad


def predict_pair(cid):
    j, label, base_b, with_b = PAIRS[cid]
    b_req = t2.state_req(t2.m20.payload(base_b()), j)
    w_req = t2.state_req(t2.m20.payload(with_b()), j)
    b, _ = cmp.rate(b_req)
    w, _ = cmp.rate(w_req)
    sb, pb_core, _, bad_b = core_sum(b, j)
    sw, pw_core, rates_w, bad_w = core_sum(w, j)
    # the base's CLASS Group I / II rates are chunks 1-8's (engine-read, ISO-confirmed): only the with-side rates are hand-derived
    bad = [x for x in bad_b if "hand" not in x] + bad_w
    rise = sw - sb
    pb, pw = rep.our_prem(b), rep.our_prem(w)
    other = [(k, pb.get(k), pw.get(k)) for k in set(pb) | set(pw) if not CORE.search(k) and not TOTALISH.search(k)
             and k != f"{P}[0]/Premium" and not m.same(pb.get(k), pw.get(k))]
    terr = [(k, pb.get(k), pw.get(k)) for k in set(pb) | set(pw) if d15.TERR.search(k) and not m.same(pb.get(k), pw.get(k))]
    eng = D(str(pw[d15.TOTAL])) - D(str(pb[d15.TOTAL]))
    moved = {k.split("/")[-1][:-len("Coverage")]: ([str(v[0]) for v in pb_core.get(k, [])], [str(v[0]) for v in vs])
             for k, vs in pw_core.items() if [str(v[0]) for v in vs] != [str(v[0]) for v in pb_core.get(k, [])]}
    print(f"{cid} {j} {label}:\n    with-side rates by hand = engine: {'yes' if not [x for x in bad_w if 'hand' in x] else bad_w[:2]}"
          f"\n    core records that move (base -> with): {moved}"
          f"\n    every other premium identical base -> with: {'yes' if not other else other[:4]}"
          f"\n    terrorism / TRIA fields moved: {'none' if not terr else terr[:4]}"
          f"\n    predicted rise {rise}; engine {eng}  {'ok' if eng == rise else 'DIFFERS'}")
    if bad or other or terr or eng != rise:
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
        print("\nISO live at 2026-09-17: each pair's base and with, every premium, stat values and identification codes, messages, the rise")
        for i, cid in enumerate(ps, 1):
            j, b_req, w_req, rise = preds[cid]
            progress(i, len(ps), f"ISO {cid} (predicted rise {rise})")
            resp = {}
            for tag, req in (("base", b_req), ("with", w_req)):
                (gc.OUT / f"chunk26_c26-20_{cid}_{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                try:
                    resp[tag] = client.rate(req)
                except raas_mod.RaaSError as exc:
                    print(f"  {cid} {tag} ISO REFUSES {str(exc.body)[:240]}")
                    FAIL.append(f"{cid} {tag} live")
                    continue
                (gc.OUT / f"chunk26_c26-20_{cid}_{tag}_response.json").write_text(json.dumps(resp[tag], indent=2), encoding="utf-8")
                data, ip = cmp.rate(req)
                ipr, opr = rep.iso_prem(resp[tag]), rep.our_prem(data)
                dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
                want = lambda rr: rr in (P + "Structure", P + "PersonalProperty", P + "BusinessIncome") or bool(CORE.search("/" + rr + "["))
                ist, ost = d15.iso_fields(resp[tag], want, WANT_FIELD), d15.our_fields(data, want, WANT_FIELD)
                ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
                ids = sorted({str(v) for k, v in ist.items() if k.endswith("RatingIdentificationCode")})
                mi, mo = cmp.iso_messages(resp[tag]), set(ip.messages)
                ok = not dd and not ds and mi == mo
                print(f"  {cid} {tag}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} stat / identification values "
                      f"(identification codes {ids}), messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[tag]):,.0f}"
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
    print(f"\nC26-20: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
