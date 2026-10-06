#!/usr/bin/env python3
"""Chunk 18, RC-5 (C18-20): what the chunk 18 families feed downstream.

Predicted from the rules before running (2026-09-29):
  TOTAL      each record's Premium enters the policy total like any other (chunk 14), so adding the
             families moves the total by EXACTLY the sum of their premiums, each predicted by hand
             (189_'s expectations and 177_'s evaluator). The families read PARENT inputs (limits
             1,000,000, cause Special, the policy dates) that would move the parents' own premiums if
             they changed between T0 and T1, so T0 already carries them (ValuationType "Functional
             Valuation" on the building and contents too: it moves their own rates, found live):
               T0  189_'s Oregon policy (Special, building and special class at 1,000,000, dated
                   09/17/2026 - 09/17/2027) + terrorism, every family switch off, no family record
               T1  + all six families as 189_ puts them (48 records): Agreed Value (80,000) on the five
                   coverages and Leased Property (200,000), Inflation Guard 6 / 20 / 12%, Functional
                   Valuation (post-loss option), Rebuilding 25%, Vacancy Permit (90 / 181 days), Peak
                   Season (+30,000, 60 days)
             Every other premium must be identical T0 -> T1 (a family switch that moved a parent would
             show here: AgreedValueOption, InflationGuard, ValuationType sit on the parents).
  T2         the clean test: T1 with the agreed limit 120,000 and Peak Season +45,000 (the leased item's
             limit stays: it moves the leased item's own premium); its total rise the hand sum, printed
             before ISO is asked.
  FOUND LIVE (2026-09-29, first run): ValuationType "Functional Valuation" is a parent input AND the
             family's switch (it moves the parents' rates and attaches the records, which price without
             the post-loss option); the Leased Property row prices the leased item itself. Both now sit in
             T0, T0's Functional premiums are predicted by hand, and the total must move by hand(T1) -
             hand(T0).
  BLANKET    chunk 9's two-building blanket (A3's): B0 with the detail's AgreedVal "No", B1 "Yes". The
             total moves by exactly the Agreed Value premiums; every blanket roll-up field (the
             BlanketRating records: average rates, LimitToUse, totals) identical except the family's own
             AgreedVal fields.
  TERRORISM  no terrorism rule reads a chunk 18 record: every terrorism field identical T0 / T1, none on
             a chunk 18 record.
  STAT CODES every stat value ISO returns on a chunk 18 record, compared with ours strictly as text, on
             every stored chunk 18 response (RC-1..RC-4) and T0-T2, B0-B1.

    python scripts/cf/190_chunk18_c18-20_downstream.py [--live] [--no-stored]

Progress streams as [i/n elapsed] lines (run it into results/cf-raas/logs/). Exits 1 on any disagreement.
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


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


from cf_engine.resolve import book_for                     # noqa: E402

x4 = import_module("189_chunk18_rc4")
g = x4.g
cen = import_module("185_chunk18_census")
d15 = import_module("172_chunk15_c15-19_downstream")
tot = import_module("159_chunk14_rc2_total")
r2, rc1, gc, rep, cmp, r11, r16, r4 = x4.r2, x4.rc1, x4.gc, x4.rep, x4.cmp, x4.r11, x4.r16, x4.r4
P = "CommercialProperty"
OUT = gc.OUT
FAIL = []


def family_records():
    """every chunk 18 record name (premium records and containers): the DataDefGroups of the family files."""
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    recs = set()
    for _, pat in cen.FAMILIES:
        for f in cw.glob("*.xml"):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                recs |= set(re.findall(r'DataDefGroup="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    return recs


RECS = family_records()
FAMILY_FIELD = re.compile(r"AgreedVal|AgreeValue|InflationGuard|Functional|Rebuilding|VacancyPermit|PeakSeason")


# ---------------------------------------------------------------- policies

def t0():
    """189_'s policy with only the PARENT inputs the families need (no family switch, no family record)."""
    sub = r2.grp.five()
    at = rc1.node_dicts(sub)
    at[P].update(r2.rc2.POLICY)
    sub["EffDate"], sub["ExpDate"] = x4.EFF, x4.EXP
    at[P].update({"EffectiveDt": x4.EFF, "ExpirationDt": x4.EXP})
    st = at[P + "Structure"]
    st["MultiPremiumAndDispersionCreditFactor"] = r2.rc2.BUILDING_CREDIT
    st.setdefault("WindstormOrHailDeductible", "1,000")
    for k in g.PARENTS:
        at[P + k]["CauseOfLoss"] = "Special"
    st.update({"Limit": "1000000", "FullBldgValue": "1000000"})
    at[P + "SpecialClass"]["Limit"] = "1000000"
    # ValuationType "Functional Valuation" is a PARENT input: it moves the building's and contents' own
    # premiums (building BGI $1,923 -> $2,032; first live run 2026-09-29, T1 - T0 was $866 over the hand
    # sum), so T0 carries it, as chunk 17's T0 carried the Mining risk
    # It is also Functional Valuation's own switch: the records attach and PRICE on it alone (no post-loss
    # option here: T0's Functional premiums are predicted by hand too, and T1 - T0 moves by the difference)
    for k in ("Structure", "PersonalProperty"):
        at[P + k]["ValuationType"] = "Functional Valuation"
    # the Leased Property row is chunk 11 / 19's own record: it prices the leased item ($713 at 200,000)
    # whether or not its Agreed Value is on, so T0 has it with the contents' Agreed Value off
    at[P + "PersonalProperty"][P + "LeasedPropertyTable"] = {P + "LeasedProperty": [{P + "LeasedPropertyDetailTable": {
        P + "LeasedPropertyDetail": [{"Limit": "200000"}]}}]}
    return tot.terror(sub)


def t1():
    return tot.terror(x4.build("OR"))


def _t2(sub):
    at = rc1.node_dicts(sub)
    for k in g.PARENTS:
        at[P + k]["AgreedValueLimit"] = "120000"
    pp = at[P + "PersonalProperty"]
    pp[P + "PeakSeasonLimitOfInsuranceTable"][P + "PeakSeasonLimitOfInsurance"][0][
        P + "PeakSeasonLimitOfInsuranceDetailTable"][P + "PeakSeasonLimitOfInsuranceDetail"][0].update(
        {"Limit": "45000", "FullValue": "45000"})


def t2():
    return tot.terror(x4.build("OR", _t2))


def b(agreed):
    sub = g.a3()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp["CommercialPropertyBlanketRatingTable"]["CommercialPropertyBlanketRating"][0][
        "CommercialPropertyBlanketRatingDetailTable"]["CommercialPropertyBlanketRatingDetail"][0]["AgreedVal"] = \
        "Yes" if agreed else "No"
    if not agreed:
        for st in cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0][
                "CommercialPropertyStructureTable"]["CommercialPropertyStructure"]:
            st.pop(P + "StructureAgreedValBasicGroupICoverage", None)
            st.pop(P + "StructureAgreedValBasicGroupIICoverage", None)
    return sub


#: C28-17: the buildings now carry Oregon's Group II territory, so Group II prices and Agreed Value adds its Group II
#: piece too (ISO live 2026-10-05: $13 + $25 Group I, $1 + $2 Group II = $41, was $38 with Group II at $0)
B_EXP = {"StructureAgreedValBasicGroupICoverage": {"Factor": g.AV},
         "StructureAgreedValBasicGroupIICoverage": {"Factor": g.AV}}


# ------------------------------------------------------------ hand sums

def premium_records():
    # population()'s keys are the file stems, already "CommercialProperty..." (a first draft prefixed P again,
    # which silently emptied the T0 / B0 and unpredicted-record checks)
    recs = {r for rs in import_module("186_chunk18_rc1").population().values() for r in rs}
    assert recs and all(r.startswith(P) and not r.startswith(P + P) for r in recs)
    return recs


PREMIUM_RECS = premium_records()


def engine_total(sub):
    data, _ = gc.run(sub, "OR")
    return Decimal(str(rep.our_prem(data)[d15.TOTAL]))


def hand_sum(sub, label, exp):
    """every chunk 18 premium record on the rated tree, predicted by hand: (sum, n, n ok)."""
    data, _ = gc.run(sub, "OR")
    # a record ON the tree but switched off carries $0; only a non-zero premium with no prediction is a gap
    priced = lambda r: any(n.first("Premium") is not None and not r2.same(n.first("Premium").text or 0, 0)
                           for n in rc1.find(data, r))
    missing = sorted(r[len(P):] for r in PREMIUM_RECS if priced(r) and r[len(P):] not in exp)
    if missing:
        print(f"  {label}: priced records with no prediction: {missing}")
        FAIL.append(f"{label} unpredicted")
    bad, detail, n, preds = r4.evaluate("OR", data, exp)
    for d in detail[:6]:
        print(d)
    if bad:
        FAIL.append(f"{label} engine")
    total = sum((Decimal(str(h)) for v in preds.values() if v != "NONE" for h in v), Decimal(0))
    return total, n, n - len(bad)


# ------------------------------------------------------------- comparisons

def live_one(client, raas_mod, cid, sub, want):
    req = r11.payload(sub)
    (OUT / f"chunk18_c18-20_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        print(f"  {cid} ISO REFUSES {str(exc.body)[:160]}")
        FAIL.append(f"{cid} live")
        return None
    (OUT / f"chunk18_c18-20_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    data, ip = cmp.rate(req)
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    ist, ost = d15.iso_fields(resp, want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
    ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
    mi, mo = cmp.iso_messages(resp), set(ip.messages)
    ok = not dd and not ds and mi == mo
    print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 18 stat values, "
          f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp):,.0f}"
          + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5])
          + (f"\n      ISO only {sorted(mi - mo)[:3]}\n      ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
    if not ok:
        FAIL.append(f"{cid} live")
    return resp


def other_premiums_moved(r0, r1):
    p0, p1 = rep.iso_prem(r0), rep.iso_prem(r1)
    return [k for k, v in p0.items()
            if "Total" not in k and k != "CommercialProperty[0]/Premium"
            and k.rsplit("/", 2)[-2].split("[")[0] not in RECS
            and not rep.cmp.same(v, p1.get(k))]


def rise(r0, r1):
    return Decimal(str(d15.total_of(r1))) - Decimal(str(d15.total_of(r0)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--no-stored", action="store_true", help="skip re-rating the stored RC-1..RC-4 responses")
    a = ap.parse_args()
    exp = x4.expectations("OR")
    # T0: only Functional Valuation prices (its switch is the parent's ValuationType); no post-loss option,
    # so the building's post-loss factor is the tree's own, not 1.02
    exp0 = {r: ({k: v for k, v in o.items() if k != "../PostLossFactor"} if isinstance(o, dict) else o)
            for r, o in exp.items() if r.startswith("Functional")}
    progress(1, 3, "hand sums T0, T1, T2, B1")
    h0, n0, ok0 = hand_sum(t0(), "T0", exp0)
    h1, n1, ok1 = hand_sum(t1(), "T1", exp)
    h2, n2, ok2 = hand_sum(t2(), "T2", exp)
    b_pred, nb, okb = hand_sum(b(True), "B1", B_EXP)
    t1_pred, t2_pred = h1 - h0, h2 - h0
    progress(2, 3, "B0 carries no chunk 18 premium")
    data, _ = gc.run(b(False), "OR")
    on = [r16.short(r) for r in PREMIUM_RECS for n in rc1.find(data, r)
          if n.first("Premium") is not None and not r2.same(n.first("Premium").text or 0, 0)]
    print(f"  B0: {len(on)} chunk 18 premiums priced" + (f" {on[:4]}" if on else " (none, as predicted)"))
    if on:
        FAIL.append("B0 not clean")
    print(f"T0: {n0} Functional Valuation records (switched on by ValuationType), engine = hand on {ok0} of {n0}; sum {h0}")
    print(f"T1: {n1} chunk 18 records, engine = hand on {ok1} of {n1}; sum {h1}; predicted total rise {h1} - {h0} = {t1_pred}")
    print(f"T2 (clean test, predicted BEFORE its ISO call): engine = hand on {ok2} of {n2}; sum {h2}; "
          f"predicted total rise {t2_pred}")
    print(f"B1 (blanket Agreed Value): engine = hand on {okb} of {nb}; predicted total rise {b_pred}")
    # the same totals on our engine, offline (ISO agrees with it policy by policy in --live)
    e0, eb0 = engine_total(t0()), engine_total(b(False))
    for label, sub, base_, pred in (("T1", t1(), e0, t1_pred), ("T2", t2(), e0, t2_pred), ("B1", b(True), eb0, b_pred)):
        d = engine_total(sub) - base_
        print(f"  engine total {label} - {'B0' if label == 'B1' else 'T0'}: {d}; hand sum {pred}  {'ok' if d == pred else 'DIFFERS'}")
        if d != pred:
            FAIL.append(f"{label} engine total")

    want = lambda r: r in RECS
    if not a.no_stored:
        stored = sorted(OUT.glob("chunk18_rc[1234]_*_response.json"))
        print(f"\nSTAT CODES on chunk 18 records ({len(stored)} stored responses, strict text)")
        n = values = 0
        fields = collections.Counter()
        for i, rpath in enumerate(stored, 1):
            tag = rpath.name[len("chunk18_"):-len("_response.json")]
            progress(i, len(stored), f"stat codes {tag}")
            reqp = OUT / f"chunk18_{tag}_request.json"
            if not reqp.exists():
                continue
            req = json.loads(reqp.read_text(encoding="utf-8"))
            resp = json.loads(rpath.read_text(encoding="utf-8"))
            try:
                data, ip = cmp.rate(req)
            except Exception as exc:                          # noqa: BLE001
                if "is missing, and" in str(exc):           # C28-17: a stored silent-zero request, refused by decision
                    print(f"  {tag}: ours refuses by decision (C28-17), kept as sent: {str(exc)[:70]}")
                    continue
                raise
            iso, ours = d15.iso_fields(resp, want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
            n += 1
            values += len(iso)
            fields.update(k.rsplit("/", 1)[-1] for k in iso)
            bad = [(k, v, ours.get(k)) for k, v in iso.items() if not d15.same(v, ours.get(k))]
            if bad:
                FAIL.append(f"stat {tag}")
                print(f"  {tag}: {len(bad)} differ" + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4]))
        print(f"  {n} stored chunk 18 responses re-rated; {values} stat values on chunk 18 records, "
              f"{len(fields)} field names ({', '.join(sorted(fields))}); "
              f"{'all equal' if not any(f.startswith('stat') for f in FAIL) else 'DIFFERENCES above'}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL, TERRORISM, STAT CODES, BLANKET (ISO live): T0 / T1 / T2, B0 / B1")
        resp = {}
        runs = (("T0", t0), ("T1", t1), ("T2", t2), ("B0", lambda: b(False)), ("B1", lambda: b(True)))
        for i, (cid, build) in enumerate(runs, 1):
            progress(i, len(runs), f"ISO {cid}")
            r = live_one(client, raas_mod, cid, build(), want)
            if r is not None:
                resp[cid] = r
        if all(k in resp for k in ("T0", "T1", "T2")):
            not18 = lambda r: r not in RECS
            a0 = d15.iso_fields(resp["T0"], not18, d15.TERR.search)
            a1 = d15.iso_fields(resp["T1"], not18, d15.TERR.search)
            moved = [(k, v, a1.get(k)) for k, v in a0.items() if not d15.same(v, a1.get(k))]
            on18 = [k for k, v in d15.iso_fields(resp["T1"], want, d15.TERR.search).items() if not d15.blank(v)]
            other = other_premiums_moved(resp["T0"], resp["T1"])
            dtot, dt2 = rise(resp["T0"], resp["T1"]), rise(resp["T0"], resp["T2"])
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  "
                  f"{'ok' if dt2 == t2_pred else 'DIFFERS'}")
            print(f"  terrorism fields T0 vs T1: {len(a0) - len(moved)} of {len(a0)} identical; on chunk 18 records: {len(on18)}"
                  + "".join(f"\n      {k[-80:]} T0 {v!r} T1 {w!r}" for k, v, w in moved[:4]))
            print(f"  every other premium identical T0 -> T1: {'yes' if not other else other[:4]}")
            print(f"  total T1 - T0 at ISO: {dtot}; predicted (the families' hand-predicted premiums) {t1_pred}  "
                  f"{'ok' if dtot == t1_pred else 'DIFFERS'}")
            if moved or on18 or other or dtot != t1_pred or dt2 != t2_pred:
                FAIL.append("downstream")
        if all(k in resp for k in ("B0", "B1")):
            blk = lambda r: "BlanketRating" in r
            f0 = d15.iso_fields(resp["B0"], blk, lambda k: True)
            f1 = d15.iso_fields(resp["B1"], blk, lambda k: True)
            moved = [(k, v, f1.get(k)) for k, v in f0.items() if not d15.same(v, f1.get(k))]
            fam = [m for m in moved if FAMILY_FIELD.search(m[0].rsplit("/", 1)[-1])]
            roll = [m for m in moved if m not in fam]
            other = other_premiums_moved(resp["B0"], resp["B1"])
            db = rise(resp["B0"], resp["B1"])
            print(f"  blanket roll-up B0 vs B1: {len(f0) - len(moved)} of {len(f0)} fields identical; "
                  f"moved: {len(fam)} Agreed Value field(s) {[m[0].rsplit('/', 1)[-1] for m in fam]}, "
                  f"{len(roll)} other" + "".join(f"\n      {k[-80:]} B0 {v!r} B1 {w!r}" for k, v, w in roll[:5]))
            print(f"  every other premium identical B0 -> B1: {'yes' if not other else other[:4]}")
            print(f"  total B1 - B0 at ISO: {db}; predicted {b_pred}  {'ok' if db == b_pred else 'DIFFERS'}")
            if roll or other or db != b_pred:
                FAIL.append("blanket")
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC18-20: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
