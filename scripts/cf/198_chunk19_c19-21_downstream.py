#!/usr/bin/env python3
"""Chunk 19, RC-5 (C19-21): what the chunk 19 families feed downstream.

Predicted from the rules before running (2026-09-29), carrying chunk 18's lesson (190_: a switch or a row that
sits on a PARENT can move the parent, so T0 carries every parent input and T0's own chunk 19 premiums, if any,
are predicted too):
  T0  191_'s Oregon policy (175_'s: chunk 7 + 15's modifiers + chunk 10's earthquake election) on the Special
      cause, WITH the parent inputs the families read -- the contents' own earthquake election (EQGrade, the
      contents EQ endorsement record, sprinkler-leakage-only), contents type Stock -- and terrorism; no chunk 19
      container
  T1  + every chunk 19 record (191_'s family_tree: 63 records, each container given its inputs)
  T2  the clean test: T1 with every chunk 19 limit x 10 (194_'s times10); its total rise predicted by hand and
      printed before ISO is asked
  TOTAL      T1 - T0 = hand(T1) - hand(T0) + the change in the CONTENTS' own premiums, every other premium
             identical. FOUND (first engine pass, 2026-09-29): Household Personal Property's limit is added to the
             occupancy's total amount of insurance (OccupTotalLOIToUse / OccupSpecialTotAmtInsurance), on which the
             contents' limit-of-insurance factors are looked up (chunk 4): with Household on, the contents' own
             Group I factor falls 0.898 -> 0.879 and its premium $197 -> $192. That parent move cannot sit in T0
             (it exists only with Household), so the contents' premiums are hand-evaluated on each tree and their
             change is part of the prediction; the occupancy total = contents limit + Household limits is checked
  TERRORISM  no terrorism rule reads a chunk 19 record: every terrorism field identical T0 / T1, none on a chunk 19
             record
  STAT CODES every stat value ISO returns on a chunk 19 record (the antennas' and signs' class, coverage and
             construction / no-construction codes, exposure amounts), strictly as text, on every stored chunk 19
             response and on T0-T2

    python scripts/cf/198_chunk19_c19-21_downstream.py [--live] [--no-stored]

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

rc1m = import_module("191_chunk19_rc1")
x1516 = import_module("194_chunk19_c19-15-16")
d15 = import_module("172_chunk15_c15-19_downstream")
tot = import_module("159_chunk14_rc2_total")
g = rc1m                                                   # noqa
r2, rc1, gc, r16 = rc1m.r2, rc1m.rc1, rc1m.gc, rc1m.r16
rep, cmp, r11 = x1516.rep, x1516.cmp, x1516.r11
P = "CommercialProperty"
OUT = gc.OUT
FAIL = []
POP = rc1m.population()
PREMIUM_RECS = {r for rs in POP.values() for r in rs}
assert PREMIUM_RECS and all(r.startswith(P) and not r.startswith(P + P) for r in PREMIUM_RECS)


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def family_records():
    """every chunk 19 record name (premium records and containers): the DataDefGroups of the family files."""
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    recs = set()
    for _, pat in rc1m.cen.FAMILIES:
        for f in cw.glob("*.xml"):
            if re.search(pat, f.name) and not rc1m.cen.EXCLUDE.search(f.name):
                recs |= set(re.findall(r'DataDefGroup="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    return recs


RECS = family_records()
#: the contents' own coverage records: Household moves them (the occupancy LOI total), so they are predicted too
CONTENTS = {P + f"PersonalPropertyPrsnlProp{f}Coverage": (book_for("OR", r2.ASOF).parent.package.content / "Rules" /
                                                          f"{P}PersonalPropertyPrsnlProp{f}CoverageRules.Rule.xml").read_text(encoding="utf-8-sig")
            for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
XSD = rc1.xsd_for(book_for("OR", r2.ASOF))


def t0():
    sub, _ = rc1m.family_tree({}, XSD, "Special")          # the base with every parent input, no chunk 19 record
    return tot.terror(sub)


def t1():
    sub, _ = rc1m.family_tree(POP, XSD, "Special")
    return tot.terror(sub)


def t2():
    sub, _ = rc1m.family_tree(POP, XSD, "Special")
    x1516.times10(sub)
    return tot.terror(sub)


def hand_sum(sub, label):
    """(sum of every chunk 19 premium, predicted by hand; n nodes; n hand = engine; the contents' own premiums
    by hand)."""
    data, _ = gc.run(sub, "OR")
    gv = lambda n, f: n.first(f).text if n.first(f) is not None else None
    pp = r16.find(data, P + "PersonalProperty")[0]
    hh = sum(Decimal(gv(d, "Limit") or 0) for d in r16.find(data, P + "HouseholdPersonalPropertyCoverageDetail"))
    want = Decimal(gv(pp, "Limit")) + hh
    for fld in ("OccupTotalLOIToUse", "OccupSpecialTotAmtInsurance"):
        ok = Decimal(gv(pp, fld) or 0) == want
        print(f"  {label}: contents {fld} {gv(pp, fld)} = contents limit + Household limits {want}  {'ok' if ok else 'DIFFERS'}")
        if not ok:
            FAIL.append(f"{label} {fld}")
    contents = Decimal(0)
    for rec, text in CONTENTS.items():
        for node in r16.find(data, rec):
            eng = Decimal(gv(node, "Premium") or 0)
            h = Decimal(str(r16.hand(rc1m.cen.set_premium(text), node)))
            if h != eng:
                FAIL.append(f"{label} contents {r16.short(rec)}")
                print(f"  {label}: contents hand {h} engine {eng}: {r16.short(rec)}")
            contents += h
    total, n, ok = Decimal(0), 0, 0
    for rs in POP.values():
        for rec, text in rs.items():
            body = rc1m.cen.set_premium(text)
            for node in r16.find(data, rec):
                prem = node.first("Premium")
                eng = Decimal(prem.text) if prem is not None and prem.text not in (None, "") else Decimal(0)
                cov = node.first("CoverageOnPolicyIndicator")
                if cov is not None and cov.text == "0":
                    h = Decimal(0)
                else:
                    try:
                        h = Decimal(str(r16.hand(body, node)))
                    except ArithmeticError:
                        h = None
                n += 1
                if h is not None and h == eng:
                    ok += 1
                    total += h
                else:
                    FAIL.append(f"{label} {r16.short(rec)}")
                    print(f"  {label}: hand {h} engine {eng}: {r16.short(rec)}")
    return total, n, ok, contents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--no-stored", action="store_true")
    a = ap.parse_args()
    progress(1, 2, "hand sums T0, T1, T2")
    h0, n0, ok0, c0 = hand_sum(t0(), "T0")
    h1, n1, ok1, c1 = hand_sum(t1(), "T1")
    h2, n2, ok2, c2 = hand_sum(t2(), "T2")
    t1_pred, t2_pred = (h1 - h0) + (c1 - c0), (h2 - h0) + (c2 - c0)
    print(f"T0: {n0} chunk 19 nodes (hand = engine on {ok0}); their sum {h0}; the contents' own premiums {c0}")
    print(f"T1: {n1} chunk 19 nodes, hand = engine on {ok1}; sum {h1}; contents {c1} ({c1 - c0:+}); "
          f"predicted total rise {h1 - h0} {c1 - c0:+} = {t1_pred}")
    print(f"T2 (clean test, predicted BEFORE its ISO call): {n2} nodes, hand = engine on {ok2}; sum {h2}; contents {c2} "
          f"({c2 - c0:+}); predicted total rise {t2_pred}")
    total = lambda sub: Decimal(str(rep.our_prem(gc.run(sub, "OR")[0])[d15.TOTAL]))
    e0 = total(t0())
    for label, build, pred in (("T1", t1, t1_pred), ("T2", t2, t2_pred)):
        d = total(build()) - e0
        print(f"  engine total {label} - T0: {d}; hand {pred}  {'ok' if d == pred else 'DIFFERS'}")
        if d != pred:
            FAIL.append(f"{label} engine total")

    want = lambda r: r in RECS
    if not a.no_stored:
        stored = sorted(p for p in OUT.glob("chunk19_*_response.json") if "c19-21" not in p.name)
        print(f"\nSTAT CODES on chunk 19 records ({len(stored)} stored responses, strict text)")
        n = values = 0
        fields = collections.Counter()
        for i, rpath in enumerate(stored, 1):
            tag = rpath.name[len("chunk19_"):-len("_response.json")]
            reqp = OUT / f"chunk19_{tag}_request.json"
            if not reqp.exists():
                continue
            progress(i, len(stored), f"stat codes {tag}")
            req = json.loads(reqp.read_text(encoding="utf-8"))
            resp = json.loads(rpath.read_text(encoding="utf-8"))
            data, ip = cmp.rate(req)
            iso, ours = d15.iso_fields(resp, want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
            n += 1
            values += len(iso)
            fields.update(k.rsplit("/", 1)[-1] for k in iso)
            bad = [(k, v, ours.get(k)) for k, v in iso.items() if not d15.same(v, ours.get(k))]
            if bad:
                FAIL.append(f"stat {tag}")
                print(f"  {tag}: {len(bad)} differ" + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4]))
        print(f"  {n} stored chunk 19 responses re-rated; {values} stat values on chunk 19 records, "
              f"{len(fields)} field names ({', '.join(sorted(fields))}); "
              f"{'all equal' if not any(f.startswith('stat') for f in FAIL) else 'DIFFERENCES above'}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL, TERRORISM, STAT CODES (ISO live): T0 without, T1 with the chunk 19 families, T2 the clean test")
        resp = {}
        for i, (cid, build) in enumerate((("T0", t0), ("T1", t1), ("T2", t2)), 1):
            progress(i, 3, f"ISO {cid}")
            req = r11.payload(build())
            (OUT / f"chunk19_c19-21_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:180]}")
                FAIL.append(f"{cid} live")
                continue
            (OUT / f"chunk19_c19-21_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp[cid]), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ist, ost = d15.iso_fields(resp[cid], want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
            ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not dd and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 19 stat values, "
                  f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[cid]):,.0f}"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
            if not ok:
                FAIL.append(f"{cid} live")
        if len(resp) == 3:
            not19 = lambda r: r not in RECS
            a0 = d15.iso_fields(resp["T0"], not19, d15.TERR.search)
            a1 = d15.iso_fields(resp["T1"], not19, d15.TERR.search)
            moved = [(k, v, a1.get(k)) for k, v in a0.items() if not d15.same(v, a1.get(k))]
            on19 = [k for k, v in d15.iso_fields(resp["T1"], want, d15.TERR.search).items() if not d15.blank(v)]
            p0, p1 = rep.iso_prem(resp["T0"]), rep.iso_prem(resp["T1"])
            other = [k for k, v in p0.items()
                     if "Total" not in k and k != "CommercialProperty[0]/Premium"
                     and k.rsplit("/", 2)[-2].split("[")[0] not in RECS | set(CONTENTS)
                     and not rep.cmp.same(v, p1.get(k))]
            rise = lambda x, y: Decimal(str(d15.total_of(resp[y]))) - Decimal(str(d15.total_of(resp[x])))
            dtot, dt2 = rise("T0", "T1"), rise("T0", "T2")
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  {'ok' if dt2 == t2_pred else 'DIFFERS'}")
            print(f"  terrorism fields T0 vs T1: {len(a0) - len(moved)} of {len(a0)} identical; on chunk 19 records: {len(on19)}"
                  + "".join(f"\n      {k[-80:]} T0 {v!r} T1 {w!r}" for k, v, w in moved[:4]))
            print(f"  every other premium (not chunk 19, not the contents' coverages) identical T0 -> T1: {'yes' if not other else other[:4]}")
            print(f"  total T1 - T0 at ISO: {dtot}; predicted {t1_pred}  {'ok' if dtot == t1_pred else 'DIFFERS'}")
            if moved or on19 or other or dtot != t1_pred or dt2 != t2_pred:
                FAIL.append("downstream")
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC19-21: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
