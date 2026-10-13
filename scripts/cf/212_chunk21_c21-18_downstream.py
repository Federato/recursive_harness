#!/usr/bin/env python3
"""Chunk 21, C21-18: what the chunk 21 families feed downstream. Live ISO.

Predicted before running (2026-09-30), with chunk 18's lesson (T0 already carries every parent input the
families read, so a parent move cannot hide in the difference) and chunk 19's (a family can move a parent's
own premium: every non-chunk-21 premium is compared T0 -> T1):
  T0  Oregon's portable policy (211_'s), cause Special; no chunk 21 record
  T1  + the five sewer records at 25,000 + the unit-owners options container (loss assessment 10,000,
      deductible 250, sub-limit 7,000; misc. real property 20,000)
  T2  the clean test: every chunk 21 amount x 10 (sewer 250,000 over parents of 100,000, so the five cap
      messages fire; loss assessment "Over 10,000" = 100,000, sub-limit 70,000; misc. real property 200,000);
      its total rise predicted by hand (211_'s state-aware models) and printed BEFORE the ISO call
  TOTAL      T1 - T0 = the chunk 21 premiums by hand; every other premium identical T0 -> T1 (no chunk 21
             file writes a parent field: C21-12)
  TERRORISM  no terrorism rule reads a chunk 21 record: every terrorism field identical T0 / T1 / T2, none
             on a chunk 21 record
  STAT CODES every stat value ISO returns on a chunk 21 record (the sewer sublines and codes, the options
             container's exclusion indicators and peril-exclusion code, the exposure amount), strictly as text,
             on T0-T2 and on every stored chunk 21 response (--stored GLOB)

    python scripts/cf/212_chunk21_c21-18_downstream.py [--live] [--stored "chunk21_*"]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
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
T0_CLOCK = time.monotonic()

m11 = import_module("211_chunk21_c21-14-17")
d15 = import_module("172_chunk15_c15-19_downstream")
m8, m9 = m11.m8, m11.m9
gc, rc1, r16, rep, cmp, r2 = m8.gc, m8.rc1, m8.r16, m8.rep, m8.cmp, m8.r2
P, SEWER, LA, MRP, OPT = m8.P, m8.SEWER, m8.LA, m8.MRP, m8.OPT
OUT = gc.OUT
FAIL = []
D = Decimal
PREMIUM_RECS = list(SEWER) + [LA, MRP]
RECS = {P + r for r in PREMIUM_RECS} | {P + OPT} | {P + r for r in (m8.FLR + "OccupClass", m8.FLR, m8.FLR + "SpecClass",
                                                                     m8.FLSPP + "OccupClass", m8.FLSPP + "SpecClass")}
STAT = re.compile(d15.STAT.pattern + r"|^Subline|Code$|ExcludedIndicator$")


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def t0():
    return m11.policy("OR", sewer=False, mrp=None, ded=None)()


def strip_container(sub):
    m9.at(sub, "PersonalProperty").pop(P + OPT + "Table", None)
    return sub


def t0_clean():
    return strip_container(t0())


def t1():
    return m11.policy("OR", la={"LossAssessmentLimit": "10,000", "LossAssessmentSubLimit": "7000"})()


def t2():
    sub = m11.portable("OR", "Special")
    for rec, lim in SEWER.items():
        r2.put(sub, rec, {lim: "250000"})
    m9.at(sub, "PersonalProperty")[P + OPT + "Table"] = {P + OPT: [{
        "LossAssessmentLimit": "Over 10,000", "LossAssessmentLimitOver10000": "100000", "LossAssessmentSubLimit": "70000",
        "LossAssessmentDeductible": "250", "MiscRealPropLimit": "200000", P + LA: {}, P + MRP: {}}]}
    return sub


def hand_sum(sub, label):
    data, ip = gc.run(sub, "OR")
    total, n, ok = D(0), 0, 0
    for rec in PREMIUM_RECS:
        for h, e in m11.predict("OR", data, rec):
            n += 1
            ev = D(str(e)) if e not in (None, "") else D(0)
            if D(str(h)) == ev:
                ok += 1
                total += ev
            else:
                FAIL.append(f"{label} {r16.short(rec)}")
                print(f"  {label}: hand {h} engine {e}: {r16.short(rec)}")
    return total, n, ok, data, ip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--stored", help="glob of stored chunk 21 responses to re-rate for stat codes")
    a = ap.parse_args()
    want = lambda r: r in RECS
    builds = (("T0", t0_clean), ("T1", t1), ("T2", t2))
    if not a.stored:
        progress(1, 2, "hand sums T0, T1, T2")
        sums = {}
        for cid, b in builds:
            h, n, ok, data, ip = hand_sum(b(), cid)
            sums[cid] = h
            caps = sum(1 for x in ip.messages if m9.CAP in str(x))
            print(f"{cid}: {n} chunk 21 premium nodes, hand = engine on {ok}; sum {h}; sewer cap messages {caps}")
        t1_pred, t2_pred = sums["T1"] - sums["T0"], sums["T2"] - sums["T0"]
        print(f"predicted total rise: T1 {t1_pred}; T2 (clean test, printed BEFORE its ISO call) {t2_pred}")
        total = lambda sub: D(str(rep.our_prem(gc.run(sub, "OR")[0])[d15.TOTAL]))
        e0 = total(t0_clean())
        for cid, b, pred in (("T1", t1, t1_pred), ("T2", t2, t2_pred)):
            d = total(b()) - e0
            print(f"  engine total {cid} - T0: {d}; hand {pred}  {'ok' if d == pred else 'DIFFERS'}")
            if d != pred:
                FAIL.append(f"{cid} engine total")

    if a.stored:
        stored = sorted(OUT.glob(a.stored + "_response.json"))
        print(f"\nSTAT CODES on chunk 21 records ({len(stored)} stored responses matching {a.stored}, strict text)")
        n = values = 0
        fields = collections.Counter()
        for i, rpath in enumerate(stored, 1):
            reqp = Path(str(rpath).replace("_response.json", "_request.json"))
            if not reqp.exists():
                continue
            if i % 10 == 1 or i == len(stored):
                progress(i, len(stored), f"stat codes {rpath.name[:-14]}")
            req = json.loads(reqp.read_text(encoding="utf-8"))
            resp = json.loads(rpath.read_text(encoding="utf-8"))
            try:
                data, ip = cmp.rate(req)
            except Exception as exc:                      # a pinned refusal case has no stored response anyway
                print(f"  {rpath.name}: ours raised {str(exc)[:100]}")
                continue
            iso, ours = d15.iso_fields(resp, want, STAT.search), d15.our_fields(data, want, STAT.search)
            n += 1
            values += len(iso)
            fields.update(k.rsplit("/", 1)[-1] for k in iso)
            bad = [(k, v, ours.get(k)) for k, v in iso.items() if not d15.same(v, ours.get(k))]
            if bad:
                FAIL.append(f"stat {rpath.name}")
                print(f"  {rpath.name}: {len(bad)} differ" + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4]))
        print(f"  {n} stored responses re-rated; {values} stat values on chunk 21 records, {len(fields)} field names:")
        for f, c in sorted(fields.items()):
            print(f"      {f}: {c}")
        print(f"  {'all equal' if not FAIL else 'DIFFERENCES above'}")

    if a.live and not a.stored:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL, TERRORISM, STAT CODES (ISO live): T0 / T1 / T2")
        resp = {}
        for i, (cid, build) in enumerate(builds, 1):
            progress(i, len(builds), f"ISO {cid}")
            req = m8.payload(build(), "OR")
            (OUT / f"chunk21_c21-18_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:200]}")
                FAIL.append(f"{cid} live")
                continue
            (OUT / f"chunk21_c21-18_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp[cid]), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ist, ost = d15.iso_fields(resp[cid], want, STAT.search), d15.our_fields(data, want, STAT.search)
            ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not dd and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 21 stat values, "
                  f"messages {'equal' if mi == mo else 'DIFFER'} ({sum(1 for x in mi if m9.CAP in str(x))} sewer caps); "
                  f"ISO total {d15.total_of(resp[cid]):,.0f}"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
            if not ok:
                FAIL.append(f"{cid} live")
        if all(k in resp for k in ("T0", "T1", "T2")):
            not21 = lambda r: r not in RECS
            tf = {c: d15.iso_fields(resp[c], not21, d15.TERR.search) for c in ("T0", "T1", "T2")}
            tmoved = [(c, k) for c in ("T1", "T2") for k, v in tf["T0"].items() if not d15.same(v, tf[c].get(k))]
            on21 = [k for c in ("T1", "T2") for k, v in d15.iso_fields(resp[c], want, d15.TERR.search).items() if not d15.blank(v)]
            p0, p1 = rep.iso_prem(resp["T0"]), rep.iso_prem(resp["T1"])
            other = [k for k, v in p0.items() if "Total" not in k and k != "CommercialProperty[0]/Premium"
                     and "ErcCalculatedTotalPremium" not in k and not rep.cmp.same(v, p1.get(k))]
            rise = lambda x, y: D(str(d15.total_of(resp[y]))) - D(str(d15.total_of(resp[x])))
            dt1, dt2 = rise("T0", "T1"), rise("T0", "T2")
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  {'ok' if dt2 == t2_pred else 'DIFFERS'}")
            print(f"  terrorism fields: {len(tf['T0'])} on T0; moved in T1 / T2: {len(tmoved)}; on chunk 21 records: {len(on21)}")
            print(f"  every other premium (not chunk 21) identical T0 -> T1: {'yes' if not other else other[:4]}")
            print(f"  total T1 - T0 at ISO: {dt1}; predicted {t1_pred}  {'ok' if dt1 == t1_pred else 'DIFFERS'}")
            if tmoved or on21 or other or dt1 != t1_pred or dt2 != t2_pred:
                FAIL.append("downstream")
    mm, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC21-18: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
