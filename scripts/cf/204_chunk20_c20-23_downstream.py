#!/usr/bin/env python3
"""Chunk 20, RC-5 (C20-23): what the chunk 20 families feed downstream.

Predicted from the rules before running (2026-09-29), with chunk 18's lesson (T0 carries every PARENT input the
families read, so a parent move cannot hide in the difference) and chunk 19's (a family can move a parent's own
premium; checked by comparing every non-chunk-20 premium T0 -> T1):
  T0  203_'s Oregon policy with the parent inputs: occupancy on the Tobacco form, BI's no-waiting-period record
      ("Eliminated") and fungus indicator, the policy's fungus cover "Policy Limit"; terrorism on; no chunk 20 record
  T1  + every chunk 20 record (203_'s family tree: RC-1's inputs)
  T2  the clean test: T1 with every chunk 20 amount x 10 (limits, food / advertising, sub-limit, ammonia, the
      hazardous manual premium, the mortgage COUNT; Mortgageholders' per-mortgage Limit is a table key and stays);
      its total rise predicted by hand and printed before ISO is asked
  TOTAL      T1 - T0 = the chunk 20 premiums by hand (no parent move predicted: no family file writes a parent
             field); every other premium identical T0 -> T1
  TERRORISM  no SetTerrorismPremium (Structure, contents, special class, BI, SCBI) reads a chunk 20 record: every
             terrorism field identical T0 / T1, none on a chunk 20 record. Mortgageholders with terrorism on fires
             "CP 00 70 is not valid with Terrorism Risk Insurance Program" (the TRIA rule, C20-16 MM2): ISO too
  BLANKET    B0 / B1: 201_'s five-level blanket (detail radioactive "Yes") without / with every chunk 20 record:
             every BlanketRating field identical except the radioactive roll-up (RadioactiveContamination*)
  STAT CODES every stat value ISO returns on a chunk 20 record, strictly as text, on the stored chunk 20
             responses (--stored GLOB, run in batches) and on T0-T2 / B0-B1

    python scripts/cf/204_chunk20_c20-23_downstream.py [--live] [--stored "chunk20_rc2_*"]

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

from cf_engine.resolve import book_for                     # noqa: E402

s4 = import_module("203_chunk20_rc4")
r3 = import_module("201_chunk20_rc3")
d15 = import_module("172_chunk15_c15-19_downstream")
tot = import_module("159_chunk14_rc2_total")
m = s4.m
gc, rc1, r16, rep, cmp, r11, r2 = m.gc, m.rc1, m.r16, m.rep, m.cmp, m.r11, m.r2
P = m.P
OUT = gc.OUT
FAIL = []
POP = s4.pop()
PREMIUM_RECS = {r for rs in POP.values() for r in rs}
assert len(PREMIUM_RECS) == 28 and all(r.startswith(P) and not r.startswith(P + P) for r in PREMIUM_RECS)


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def family_records():
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    recs = set()
    for _, pat in m.cen20.FAMILIES:
        for f in cw.glob("*.xml"):
            if re.search(pat, f.name) and not m.cen20.EXCLUDE.search(f.name):
                recs |= set(re.findall(r'DataDefGroup="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    return recs


RECS = family_records()
#: chunk 20's own statistical fields beyond chunk 15's pattern: its sublines and coverage codes
STAT = re.compile(d15.STAT.pattern + r"|^Subline|^EquipmentBreakdownCode$|^FoodContaminationCode$")


def parents(sub):
    at = rc1.node_dicts(sub)
    at[P + "OccupClass"]["CovForm"] = "Tobacco Sales Warehouse Coverage Form"
    at[P + "BusinessIncome"]["FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator"] = "Yes"
    at[P + "BusinessIncome"][P + m.NOWAIT + "Table"] = {P + m.NOWAIT: [{"TimePeriod": "Eliminated"}]}
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["FungusWetRotDryRotBacteriaCov"] = "Policy Limit"
    return sub


def t0():
    return tot.terror(parents(s4.state_base("OR")))


def t1():
    return tot.terror(s4.family("OR"))


TIMES10 = {"Limit", "FoodLimit", "AdvertisingLimit", "SubLimit", "AmmoniaContamination",
           "HazardousSubstanceOtherThanAmmoniaManualPremium", "NumberMortgages", "VolunteerLimit"}


def times10(d, inside=False, key=None):
    if isinstance(d, dict):
        for k, v in list(d.items()):
            fam = inside or (not k.endswith("Table") and k in RECS)
            if isinstance(v, (dict, list)):
                times10(v, fam, k)
            elif inside and k in TIMES10 and v not in (None, "") and not (key == P + m.MORT and k == "Limit"):
                d[k] = str(int(Decimal(str(v).replace(",", "")) * 10))
    elif isinstance(d, list):
        for x in d:
            times10(x, inside, key)


def t2():
    sub = t1()
    times10(sub)
    return sub


def place_all(sub):
    """every chunk 20 record with RC-1's inputs on an existing tree (203_'s family placement)."""
    cf = s4.rc1m.container_fields()
    cf["ChangesFungusWetRotDryRotBacteria"] = {"SubLimit": "50000", "IncreasedPeriodOfRestoration": "90"}
    for r in s4.records("OR") + m.BIF:
        top, steps = r16.chain_down(s4.xsd("OR"), r)
        d = rc1.node_dicts(sub)[top]
        for t, table in steps:
            if table:
                lst = d.setdefault(t + "Table", {t: []})[t]
                if not lst:
                    lst.append({})
                d = lst[-1]
            else:
                d = d.setdefault(t, {})
            for k, v in cf.get(r16.short(t), {}).items():
                d.setdefault(k, v)
    return sub


def b0():
    return parents(r3.blanket_all("Yes"))


def b1():
    return place_all(parents(r3.blanket_all("Yes")))


def hand_sum(sub, label):
    data, _ = gc.run(sub, "OR")
    total, n, ok = Decimal(0), 0, 0
    for rec in sorted(PREMIUM_RECS):
        for h, e in m.predict(data, rec[len(P):], "OR"):
            n += 1
            try:
                hv = Decimal(str(h))
            except ArithmeticError:
                hv = None
            ev = Decimal(str(e)) if e not in (None, "") else Decimal(0)
            if hv is None and ev == 0:
                hv = Decimal(0)
            if hv == ev:
                ok += 1
                total += hv
            else:
                FAIL.append(f"{label} {r16.short(rec)}")
                print(f"  {label}: hand {h} engine {e}: {r16.short(rec)}")
    return total, n, ok, data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--stored", help="glob of stored chunk 20 responses to re-rate for stat codes (run in batches)")
    a = ap.parse_args()
    if not a.stored:
        progress(1, 3, "hand sums T0, T1, T2")
        h0, n0, ok0, _ = hand_sum(t0(), "T0")
        h1, n1, ok1, _ = hand_sum(t1(), "T1")
        h2, n2, ok2, _ = hand_sum(t2(), "T2")
        t1_pred, t2_pred = h1 - h0, h2 - h0
        print(f"T0: {n0} chunk 20 nodes (hand = engine on {ok0}); sum {h0}")
        print(f"T1: {n1} chunk 20 nodes, hand = engine on {ok1}; sum {h1}; predicted total rise {t1_pred}")
        print(f"T2 (clean test, predicted BEFORE its ISO call): {n2} nodes, hand = engine on {ok2}; sum {h2}; predicted total rise {t2_pred}")
        total = lambda sub: Decimal(str(rep.our_prem(gc.run(sub, "OR")[0])[d15.TOTAL]))
        e0 = total(t0())
        for label, build, pred in (("T1", t1, t1_pred), ("T2", t2, t2_pred)):
            d = total(build()) - e0
            print(f"  engine total {label} - T0: {d}; hand {pred}  {'ok' if d == pred else 'DIFFERS'}")
            if d != pred:
                FAIL.append(f"{label} engine total")
        progress(2, 3, "blanket roll-up B0 / B1")
        d0, _ = gc.run(b0(), "OR")
        d1, _ = gc.run(b1(), "OR")
        f0 = d15.our_fields(d0, lambda r: r.endswith("BlanketRatingDetail"), lambda k: True)
        f1 = d15.our_fields(d1, lambda r: r.endswith("BlanketRatingDetail"), lambda k: True)
        moved = sorted({k.rsplit("/", 1)[-1] for k in set(f0) | set(f1) if not d15.same(f0.get(k), f1.get(k))})
        other = [k for k in moved if "Radioactive" not in k]
        print(f"  blanket detail fields B0 vs B1: {len(f0)} / {len(f1)}; moved: {moved}; non-radioactive moved: {other or 'none'}")
        if other:
            FAIL.append("blanket roll-up")

    want = lambda r: r in RECS
    if a.stored:
        stored = sorted(p for p in OUT.glob(a.stored + "_response.json"))
        print(f"\nSTAT CODES on chunk 20 records ({len(stored)} stored responses matching {a.stored}, strict text)")
        n = values = 0
        fields = collections.Counter()
        for i, rpath in enumerate(stored, 1):
            reqp = Path(str(rpath).replace("_response.json", "_request.json"))
            if not reqp.exists():
                continue
            progress(i, len(stored), f"stat codes {rpath.name[:-14]}")
            req = json.loads(reqp.read_text(encoding="utf-8"))
            resp = json.loads(rpath.read_text(encoding="utf-8"))
            data, ip = cmp.rate(req)
            iso, ours = d15.iso_fields(resp, want, STAT.search), d15.our_fields(data, want, STAT.search)
            n += 1
            values += len(iso)
            fields.update(k.rsplit("/", 1)[-1] for k in iso)
            bad = [(k, v, ours.get(k)) for k, v in iso.items() if not d15.same(v, ours.get(k))]
            if bad:
                FAIL.append(f"stat {rpath.name}")
                print(f"  {rpath.name}: {len(bad)} differ" + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4]))
        print(f"  {n} stored responses re-rated; {values} stat values on chunk 20 records, {len(fields)} field names "
              f"({', '.join(sorted(fields))}); {'all equal' if not FAIL else 'DIFFERENCES above'}")

    if a.live and not a.stored:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL, TERRORISM, STAT CODES, BLANKET (ISO live): T0 / T1 / T2, B0 / B1")
        resp = {}
        builds = (("T0", t0), ("T1", t1), ("T2", t2), ("B0", b0), ("B1", b1))
        for i, (cid, build) in enumerate(builds, 1):
            progress(i, len(builds), f"ISO {cid}")
            req = m.payload(build())
            (OUT / f"chunk20_c20-23_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:200]}")
                FAIL.append(f"{cid} live")
                continue
            (OUT / f"chunk20_c20-23_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp[cid]), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ist, ost = d15.iso_fields(resp[cid], want, STAT.search), d15.our_fields(data, want, STAT.search)
            ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not dd and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 20 stat values, "
                  f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[cid]):,.0f}"
                  + (f"; TRIA message {'present' if any('Terrorism Risk Insurance Program' in x for x in mi) else 'absent'}" if cid != "T0" and cid[0] == "T" else "")
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
            if not ok:
                FAIL.append(f"{cid} live")
        if all(k in resp for k in ("T0", "T1", "T2")):
            not20 = lambda r: r not in RECS
            a0 = d15.iso_fields(resp["T0"], not20, d15.TERR.search)
            a1 = d15.iso_fields(resp["T1"], not20, d15.TERR.search)
            tmoved = [(k, v, a1.get(k)) for k, v in a0.items() if not d15.same(v, a1.get(k))]
            on20 = [k for k, v in d15.iso_fields(resp["T1"], want, d15.TERR.search).items() if not d15.blank(v)]
            p0, p1 = rep.iso_prem(resp["T0"]), rep.iso_prem(resp["T1"])
            other = [k for k, v in p0.items() if "Total" not in k and k != "CommercialProperty[0]/Premium"
                     and k.rsplit("/", 2)[-2].split("[")[0] not in RECS and not rep.cmp.same(v, p1.get(k))]
            rise = lambda x, y: Decimal(str(d15.total_of(resp[y]))) - Decimal(str(d15.total_of(resp[x])))
            dtot, dt2 = rise("T0", "T1"), rise("T0", "T2")
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  {'ok' if dt2 == t2_pred else 'DIFFERS'}")
            print(f"  terrorism fields T0 vs T1: {len(a0) - len(tmoved)} of {len(a0)} identical; on chunk 20 records: {len(on20)}"
                  + "".join(f"\n      {k[-80:]} T0 {v!r} T1 {w!r}" for k, v, w in tmoved[:4]))
            print(f"  every other premium (not chunk 20) identical T0 -> T1: {'yes' if not other else other[:4]}")
            print(f"  total T1 - T0 at ISO: {dtot}; predicted {t1_pred}  {'ok' if dtot == t1_pred else 'DIFFERS'}")
            if tmoved or on20 or other or dtot != t1_pred or dt2 != t2_pred:
                FAIL.append("downstream")
        if "B0" in resp and "B1" in resp:
            g0 = d15.iso_fields(resp["B0"], lambda r: r.endswith("BlanketRatingDetail"), lambda k: True)
            g1 = d15.iso_fields(resp["B1"], lambda r: r.endswith("BlanketRatingDetail"), lambda k: True)
            moved = sorted({k.rsplit("/", 1)[-1] for k in set(g0) | set(g1) if not d15.same(g0.get(k), g1.get(k))})
            other = [k for k in moved if "Radioactive" not in k]
            print(f"  ISO blanket detail B0 vs B1: moved {moved}; non-radioactive moved: {other or 'none'}")
            if other:
                FAIL.append("ISO blanket roll-up")
    mm, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC20-23: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
