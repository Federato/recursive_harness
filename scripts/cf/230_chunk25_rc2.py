#!/usr/bin/env python3
"""Chunk 25, RC-2 (C25-08..C25-13): Flood golden cases. Live ISO.

Every flood premium is predicted by 229_'s hand models (loss cost, the deductible's rate-modification table interpolated
on ITV, CRS factor, annual aggregate, excess factor, BI factors, the blanket average rate) BEFORE the ISO call, and
checked against the engine first; the parent values a hand model reads (LCM, the contents' full value to use, the BI
parent's MaxPeriod / Extra Expense factors, the policy modifiers) are built and ISO-confirmed in earlier chunks.
Every case is then sent to ISO at 2026-09-17: the flood records as predicted, every premium field for field, messages.

Cases (Oregon; the trees are 229_'s, by id):
  C25-08 Building       B1 = T1 (deductible 10,000 table 3, zone A, CRS 5), B2 = T2 (no CRS grade), B3 = T3 (500,
                        table 1, zone X), B4 = T4 (2,500, table 2, X500), B5 = T5 (50,000, table 4, zone D), B6 = T6
                        (100,000, table 5), B7 = T7 (500,000, table 6), B8 = T8 (1,000,000, table 7)
  C25-09 Contents       the same trees' contents, plus C1: deductible 25,000 (table 3's other deductible, same ITV / TPV)
  C25-10 BI / SCBI      I1 = T14 (combined manufacturing / mercantile; SCBI rental, without EE), I2 = T15 (maximum period;
                        SCBI extra expense only), OI-122 probes O1 = T16 (operational unit, CRS 5: as written $0,
                        intended 0.637) and O2 = T16b (no CRS grade: as written the last building's 0.472, intended 0.637)
  C25-11 Special Class  S1 = T17 (SC Frame on a Joisted Masonry building, SCBI Masonry Non-Combustible)
  C25-12 Blanket        K1 two risks, K2 three risks at aggregate, K3 with BI, K4 excess blanket
  C25-13 Excess / ITV   E1 = T11 (excess, 750,000, three value bands), E2 = T12 (1,000,000; contents under the NFIP max),
                        E3 = T9 (ITV 50% / 100% / above 100%), E4 = T10 (aggregate = limit, 0.999)

    python scripts/cf/230_chunk25_rc2.py [--live] [--cases B1,O1]
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

x = import_module("229_chunk25_rc1")
t2 = import_module("220_chunk23_rc2")
m, rc1, rep, cmp, gc = x.m, x.rc1, x.rep, x.cmp, x.m.gc
r11 = m.r11
P, D, val, d = x.P, Decimal, x.val, x.d
FAIL = []
B, PP, SC, BI, SCBI, BRD = x.B, x.PP, x.SC, x.BI, x.SCBI, x.BRD


def numeric():
    xs = next((x.CW / "DataDefs").glob("*.xsd")).read_text(encoding="utf-8-sig")
    out = set()
    for rec in x.FAMILY:
        mm = re.search(rf'<xs:complexType name="{P}{rec}">(.*?)</xs:complexType>', xs, re.S)
        if mm:
            out |= {e for e, _ in re.findall(r'<xs:element name="(\w+)"[^>]*type="xs:(int|decimal|integer|long)"', mm.group(1))}
    return out | {"FullBldgValue", "FullPrsnlPropValue", "FullSpecialClassValue", "CombinedTypeOfRiskManufacturingPct",
                  "CombinedTypeOfRiskMercantilePct", "UnitNumber"}


r11.NUMERIC |= numeric()

T, K = x.trees(), x.blanket_trees()
CASES = {
    "B1": ("C25-08/09", "T1"), "B2": ("C25-08/09", "T2"), "B3": ("C25-08/09", "T3"), "B4": ("C25-08/09", "T4"),
    "B5": ("C25-08/09", "T5"), "B6": ("C25-08/09", "T6"), "B7": ("C25-08/09", "T7"), "B8": ("C25-08/09", "T8"),
    "C1": ("C25-09", "C1"),
    "I1": ("C25-10", "T14"), "I2": ("C25-10", "T15"), "O1": ("C25-10 OI-122", "T16"), "O2": ("C25-10 OI-122", "T16b"),
    "S1": ("C25-11", "T17"),
    "K1": ("C25-12", "K1"), "K2": ("C25-12", "K2"), "K3": ("C25-12", "K3"), "K4": ("C25-12", "K4"),
    "E1": ("C25-13", "T11"), "E2": ("C25-13", "T12"), "E3": ("C25-13", "T9"), "E4": ("C25-13", "T10"),
}
EXTRA = {"C1": ("deductible 25,000 (table 3's other row set), otherwise B1", lambda: x.flood_tree(ded="25,000"))}
OI122 = {"O1", "O2"}


def tree(tid):
    if tid in EXTRA:
        return EXTRA[tid]
    return T.get(tid) or K[tid]


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def request(cid):
    return t2.state_req(t2.m20.payload(tree(CASES[cid][1])[1]()), "OR")


def predict(cid):
    req = request(cid)
    data, ip = cmp.rate(req)
    lines, bad, preds, alt = [], [], {}, {}
    for rec in x.PREMIUM_RECS:
        preds[rec] = []
        for node, hv, ev, e in x.predict(data, rec):
            pr = {}
            x.hand("OR", node, rec, pr)
            diff = x.parts_agree(rec, node, pr)
            ok = m.same(hv, e) and (ev is None or m.same(ev, e)) and not diff
            preds[rec].append(hv)
            if cid in OI122 and rec == BI:
                # the intended reading: the operational unit's highest building base rate
                loc = x.anc(node, "Location")
                base = x.highest_opunit_rate("OR", loc, intended=True)
                rate = x.r(x.r(base * d(x.cov(node), "LossCostMultiplier"), 3) * pr["agg"], 3)
                alt.setdefault(rec, []).append(x.tail(x.r(rate * pr["bif"], 3) * d(node, "Limit") / 100, m.root(node)))
            name = rec[len(x.FL):] or "Building"
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {name[:30]:30s} predicted {hv}   engine {e}   {x.show(pr)}")
            if not ok:
                bad.append(f"{name} hand {hv} evaluator {ev} engine {e} {diff}")
    label = tree(CASES[cid][1])[0]
    print(f"{cid} {CASES[cid][0]} {label}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:4])}")
    print("\n".join(lines))
    if alt:
        print(f"      OI-122 intended reading (highest building base rate): BI {[str(v) for v in alt[BI]]}")
    if bad:
        FAIL.append(cid)
    return req, data, ip, preds, alt


def live(client, raas_mod, cid, req, data, ip, preds, alt):
    (gc.OUT / f"chunk25_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:3s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return None
    (gc.OUT / f"chunk25_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad, iso_by = [], {}
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if v is not None)
        iso_by[rec] = iso
        w = sorted(D(str(v)) for v in want if not isinstance(v, str))
        if [v for v in iso if v] != [v for v in w if v]:
            pbad.append((rec, iso, w))
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not dd and not pbad and mi == mo
    print(f"  {cid:3s} {'AGREE' if ok else 'DIFFER'}: flood records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums equal; messages {'equal' if mi == mo else 'DIFFER'}"
          + "".join(f"\n      predicted {rr[-45:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:6])
          + "".join(f"\n      {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + (f"\n      ISO only {sorted(mi - mo)[:3]}\n      ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
    if alt:
        intended = sorted(D(str(v)) for v in alt[BI])
        written = sorted(D(str(v)) for v in preds[BI])
        verdict = ("ISO = AS WRITTEN (our engine agrees; OI-122 is an ISO defect)" if iso_by[BI] == written
                   else "ISO = INTENDED (engine change needed, the user's go)" if iso_by[BI] == intended else "ISO = NEITHER reading")
        print(f"      OI-122: BI flood ISO {[str(v) for v in iso_by[BI]]}, as written {[str(v) for v in written]}, intended "
              f"{[str(v) for v in intended]} -> {verdict}")
    if not ok:
        FAIL.append(f"{cid} live")
    return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    only = set(a.cases.split(",")) if a.cases else None
    cs = [c for c in CASES if not only or c in only]
    got = {}
    for i, cid in enumerate(cs, 1):
        progress(i, len(cs), f"predict {cid}")
        try:
            got[cid] = predict(cid)
        except Exception as exc:
            print(f"{cid}: engine RAISED {type(exc).__name__}: {str(exc)[:200]}")
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (flood records as predicted, every premium field for field, messages):")
        for i, cid in enumerate(cs, 1):
            if cid in got:
                progress(i, len(cs), f"ISO {cid}")
                live(client, raas_mod, cid, *got[cid])
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C25-08..C25-13): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
