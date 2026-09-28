#!/usr/bin/env python3
"""Chunk 17, RC-5 (C17-20): what the chunk 17 families feed downstream.

Predicted from the rules before running (2026-09-28):
  TOTAL      each record's Premium enters the policy total like any other (chunk 14), so adding the
             families moves the total by EXACTLY the sum of their premiums, each predicted by hand
             (175_'s method). Two families need PARENT inputs, which would move Business Income's own
             premium if they changed between T0 and T1, so T0 already carries them:
               * Mining: Business Income deletes Mining rows unless TypeOfRisk is Mining (RC-1), so
                 both BI and SCBI are Mining risks in T0 too (BI auto-attaches an empty Mining
                 container there: no coverage record, nothing priced);
               * cause Special on BI and SCBI and the Special theft type (Landlord Special).
             Watercraft: Business Income auto-creates the buyback record on EVERY policy (why 82
             fixtures carried it), so T0 has it with waterfront "No" ($0) and T1 turns waterfront on.
               T0  RC-2's Oregon policy + terrorism, Mining risk, Special, waterfront No
               T1  + Ordinary Payroll (BI 90 / SCBI 0 days), Power-heat, Mining (BI Limited / SCBI
                   Broad), Landlord (BI own cause Special / SCBI own cause Broad), Watercraft
                   (waterfront Yes, Option2 / Option6), Off-Premises (Collision + OTC, BI and SCBI);
                   every EQ rider the base's earthquake election switches on is predicted too
  T2         the clean test: T1 with Landlord limits 90,000 / 70,000 and Off-Premises 55,000 /
             20,000, its total rise the hand sum, printed before ISO is asked.
  TERRORISM  no terrorism rule reads a chunk 17 record: every terrorism field identical in T0 / T1,
             none on a chunk 17 record.
  STAT CODES the payroll, power-heat and Mining containers write ExposureStatAmount, Off-Premises its
             coverage / Option A / insurance-to-exposure / exposure codes: every stat value ISO returns
             on a chunk 17 record is compared with ours strictly as text, on every stored chunk 17
             response (RC-2, RC-3, RC-4) and T0-T2.

    python scripts/cf/184_chunk17_c17-20_downstream.py [--live] [--no-stored]

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

g = import_module("181_chunk17_rc2")
cen = import_module("179_chunk17_census")
d15 = import_module("172_chunk15_c15-19_downstream")
tot = import_module("159_chunk14_rc2_total")
r2, rc1, gc, rep, cmp, r11, r16 = g.r2, g.rc1, g.gc, g.rep, g.cmp, g.r11, g.r16
P = "CommercialProperty"
OUT = gc.OUT
FAIL = []
LL, LL_SC, PAY, PAY_SC, PHR, PHR_SC = g.LL, g.LL_SC, g.PAY, g.PAY_SC, g.PHR, g.PHR_SC
MIN, MIN_SC, WC, WC_SC, OP, OP_SC = g.MIN, g.MIN_SC, g.WC, g.WC_SC, g.OP, g.OP_SC
L = lambda n, f: f"{n}{f}Coverage"
WE = "Business Income With Extra Expense"


def family_records():
    """every chunk 17 record name (premium records and containers): the DataDefGroups of the family files."""
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    recs = set()
    for _, pat in cen.FAMILIES:
        for f in cw.glob("*.xml"):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                recs |= set(re.findall(r'DataDefGroup="([^"]+)"', f.read_text(encoding="utf-8-sig")))
    return recs


RECS = family_records()


# ---------------------------------------------------------------- policies

def t0():
    sub = tot.terror(r2.base())
    a = g.at(sub)
    for k in ("BusinessIncome", "SpecialClassBusnIncome"):
        a[P + k].update({"CauseOfLoss": "Special", "TypeOfRisk": "Mining", "SpecialIncludingTheftTypeRisk": g.OTHER})
    a[P + "BusinessIncome"]["WaterfrontProperty"] = "No"
    a[P + "SpecialClassBusnIncome"]["WaterFrontProperty"] = "No"
    return sub


def t1(ll=("60000", "45000"), op=("37500", "12345")):
    sub = t0()
    a = g.at(sub)
    a[P + "BusinessIncome"].update({"WaterfrontProperty": "Yes", "WatercraftExclBuybackConstrctnOption": g.OPT["Option2"]})
    a[P + "SpecialClassBusnIncome"].update({"WaterFrontProperty": "Yes", "WatercraftExclBuybackConstrctnOption": g.OPT["Option6"]})
    put = lambda rec: r2.put(sub, rec)
    con = lambda parent, name: r2.container(sub, parent, name)
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        for n in (PAY, PAY_SC, PHR, PHR_SC, LL, LL_SC):
            put(L(n, f))
    for f in ("BasicGroupI", "BasicGroupII"):
        put(L(MIN, f))
        put(L(MIN_SC, f))
    put(L(LL, "Special"))
    put(L(LL_SC, "Broad"))
    put(WC)
    put(WC_SC)
    for f in ("Collision", "OTC"):
        put(f"{OP}Detail{f}")
        put(f"{OP_SC}Detail{f}")
    con("BusinessIncome", PAY)["NumOfDays"] = "90"
    con("SpecialClassBusnIncome", PAY_SC)["NumOfDays"] = "0"
    con("BusinessIncome", MIN).update({"MiningCoverageOption": "Limited", "Limit": "40000"})
    con("SpecialClassBusnIncome", MIN_SC).update({"MiningCoverageOption": "Broad", "Limit": "40000"})
    con("BusinessIncome", LL).update({"Limit": ll[0], "Coinsurance": "80%", "CauseOfLoss": "Special"})
    con("SpecialClassBusnIncome", LL_SC).update({"Limit": ll[1], "Coinsurance": "50%", "CauseOfLoss": "Broad"})
    con("BusinessIncome", OP).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "150"})
    con("SpecialClassBusnIncome", OP_SC).update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "730"})
    con("BusinessIncome", OP)[P + OP + "DetailTable"][P + OP + "Detail"][0].update(
        {"Limit": op[0], "Option": "Option B", "PercentInsToExposure": "Under 25%"})
    con("SpecialClassBusnIncome", OP_SC)[P + OP_SC + "DetailTable"][P + OP_SC + "Detail"][0].update(
        {"Limit": op[1], "Option": "Option A"})
    return sub


def t2():
    return t1(ll=("90000", "70000"), op=("55000", "20000"))


def overrides():
    """record -> the family factor, looked up independently from the countrywide tables."""
    ov = {}
    for f in ("BasicGroupI", "BasicGroupII", "Earthquake"):
        ov[L(PAY, f)] = {"../Factor": g.payroll(90)}
        ov[L(PAY_SC, f)] = {"../Factor": g.payroll(0)}
        ov[L(PHR, f)] = {"../Factor": g.PHR_F}
        ov[L(PHR_SC, f)] = {"../Factor": g.PHR_F}
        ov[L(LL, f)] = {"../TypeOfRiskFactor": g.trf("80%")}
        ov[L(LL_SC, f)] = {"../TypeOfRiskFactor": g.trf("50%")}
    ov[L(MIN, "BasicGroupI")] = {"../BasicGroupIRate": g.mining("Limited", "Basic Group I")}
    ov[L(MIN, "BasicGroupII")] = {"../BasicGroupIIRate": g.mining("Limited", "Basic Group II")}
    ov[L(MIN_SC, "BasicGroupI")] = {"../BasicGroupIRate": g.mining("Broad", "Basic Group I")}
    ov[L(MIN_SC, "BasicGroupII")] = {"../BasicGroupIIRate": g.mining("Broad", "Basic Group II")}
    ov[L(LL, "Special")] = {"../SpecialBaseRate": g.special_rate("Frame")}
    ov[L(LL_SC, "Broad")] = {"../BroadBaseRate": g.broad_rate("Frame")}
    ov[WC] = {"Factor": g.watercraft("Option2")}
    ov[WC_SC] = {"Factor": g.watercraft("Option6")}
    ext, wait = g.op_f("OffPremExtendedBusnIncCovFactor", "ExtendedPeriodBusnInc", "150"), \
        g.op_f("OffPremBusnIncCovWaitPeriodFactor", "TimePeriod", "72 Hours")
    ins = g.op_f("OffPremInsToExposureFactor", "PercentInsToExposure", "Under 25%")
    eq = g.op_f("OffPremEndtsModifyingCovdCOLFactor", "Endorsement", "Earthquake And Volcanic Eruption Coverage")
    ext_sc = g.op_f("OffPremExtendedBusnIncCovFactor", "ExtendedPeriodBusnInc", "730")
    ov[f"{OP}DetailCollision"] = {"../../../LossCostCollision": g.op_lc(WE, "Collision"), "../../../ExtendedBICovFactor": ext,
                                  "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": ins}
    ov[f"{OP}DetailOTC"] = {"../../../LossCostOTC": g.op_lc(WE, "Other Than Collision"), "../../../ExtendedBICovFactor": ext,
                            "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": ins,
                            "../../../EQCovFactor": eq, "../../../FloodCovFactor": Decimal("1.0"),
                            "../../../WindHailExclFactor": Decimal("1.0")}
    ov[f"{OP_SC}DetailCollision"] = {"../../../LossCostCollision": g.op_lc(WE, "Collision"), "../../../ExtendedBICovFactor": ext_sc,
                                     "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": Decimal("1.0")}
    ov[f"{OP_SC}DetailOTC"] = {"../../../LossCostOTC": g.op_lc(WE, "Other Than Collision"), "../../../ExtendedBICovFactor": ext_sc,
                               "../../../BusnIncCovWaitingPeriodFactor": wait, "../InsToExposureFactor": Decimal("1.0"),
                               "../../../EQCovFactor": eq, "../../../FloodCovFactor": Decimal("1.0"),
                               "../../../WindHailExclFactor": Decimal("1.0")}
    return ov


def hand_sum(sub, label):
    """every chunk 17 premium record on the rated tree, predicted by hand: (sum, rows)."""
    data, _ = gc.run(sub, "OR")
    ov = overrides()
    premium_recs = {r for rs in import_module("180_chunk17_rc1").population().values() for r in rs}
    # a record ON the tree but switched off carries $0 (the Landlord container creates all its forms):
    # only a record with a non-zero premium and no prediction is a gap
    priced = lambda r: any(n.first("Premium") is not None and not r2.same(n.first("Premium").text or 0, 0)
                           for n in rc1.find(data, r))
    missing = sorted(r[len(P):] for r in premium_recs if priced(r) and r[len(P):] not in ov)
    if missing:
        print(f"  {label}: priced records with no prediction: {missing}")
        FAIL.append(f"{label} unpredicted")
    total, rows = Decimal(0), []
    for rec, o in ov.items():
        res, checks = r2.predict(data, rec, o, "OR")
        fac_bad = [(f, e, v) for f, e, v in checks if not r2.same(e, v)]
        for h, e in res:
            ok = not str(h).startswith("hand") and r2.same(h, e) and not fac_bad
            rows.append((rec, h, e, ok))
            if not ok:
                FAIL.append(f"{label} engine {rec}")
                print(f"  {label}: engine differs from hand: {r16.short(rec)} hand {h} engine {e} {fac_bad[:1]}")
            else:
                total += Decimal(str(h))
    return total, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--no-stored", action="store_true", help="skip re-rating the stored RC-2..RC-4 responses")
    a = ap.parse_args()
    progress(1, 2, "hand sums T1, T2")
    total_pred, rows = hand_sum(t1(), "T1")
    t2_pred, rows2 = hand_sum(t2(), "T2")
    print(f"T1: {len(rows)} chunk 17 premiums, engine = hand on {sum(r[3] for r in rows)} of {len(rows)}; "
          f"their sum, predicted by hand: {total_pred}")
    print(f"T2 (clean test, predicted BEFORE its ISO call): {len(rows2)} premiums, engine = hand on "
          f"{sum(r[3] for r in rows2)} of {len(rows2)}; predicted total rise {t2_pred}")
    zero = [r16.short(r)[:50] for r, h, e, ok in rows if ok and r2.same(h, 0)]
    if zero:
        print(f"  $0 in T1 as predicted: {', '.join(zero)}")

    want = lambda r: r in RECS
    if not a.no_stored:
        stored = sorted(OUT.glob("chunk17_rc[234]_*_response.json"))
        print(f"\nSTAT CODES on chunk 17 records ({len(stored)} stored responses, strict text)")
        n = values = 0
        fields = collections.Counter()
        for i, rpath in enumerate(stored, 1):
            tag = rpath.name[len("chunk17_"):-len("_response.json")]
            progress(i, len(stored), f"stat codes {tag}")
            req = json.loads((OUT / f"chunk17_{tag}_request.json").read_text(encoding="utf-8"))
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
        print(f"  {n} stored chunk 17 responses re-rated; {values} stat values on chunk 17 records, "
              f"{len(fields)} field names ({', '.join(sorted(fields))}); "
              f"{'all equal' if not any(f.startswith('stat') for f in FAIL) else 'DIFFERENCES above'}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL, TERRORISM, STAT CODES (ISO live): T0 without, T1 with the chunk 17 families, T2 the clean test")
        resp = {}
        for i, (cid, build) in enumerate((("T0", t0), ("T1", t1), ("T2", t2)), 1):
            progress(i, 3, f"ISO {cid}")
            req = r11.payload(build())
            (OUT / f"chunk17_c17-20_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:160]}")
                FAIL.append(f"{cid} live")
                continue
            (OUT / f"chunk17_c17-20_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp[cid]), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ist, ost = d15.iso_fields(resp[cid], want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
            ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not dd and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 17 stat values, "
                  f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[cid]):,.0f}"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
            if not ok:
                FAIL.append(f"{cid} live")
        if len(resp) == 3:
            not17 = lambda r: r not in RECS
            a0 = d15.iso_fields(resp["T0"], not17, d15.TERR.search)
            a1 = d15.iso_fields(resp["T1"], not17, d15.TERR.search)
            moved = [(k, v, a1.get(k)) for k, v in a0.items() if not d15.same(v, a1.get(k))]
            on17 = [k for k, v in d15.iso_fields(resp["T1"], want, d15.TERR.search).items() if not d15.blank(v)]
            p0, p1 = rep.iso_prem(resp["T0"]), rep.iso_prem(resp["T1"])
            other = [k for k, v in p0.items()
                     if "Total" not in k and k != "CommercialProperty[0]/Premium"
                     and k.rsplit("/", 2)[-2].split("[")[0] not in RECS
                     and not rep.cmp.same(v, p1.get(k))]
            dtot = Decimal(str(d15.total_of(resp["T1"]))) - Decimal(str(d15.total_of(resp["T0"])))
            dt2 = Decimal(str(d15.total_of(resp["T2"]))) - Decimal(str(d15.total_of(resp["T0"])))
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  "
                  f"{'ok' if dt2 == t2_pred else 'DIFFERS'}")
            ok = not moved and not on17 and not other and dtot == total_pred and dt2 == t2_pred
            print(f"  terrorism fields T0 vs T1: {len(a0) - len(moved)} of {len(a0)} identical; on chunk 17 records: {len(on17)}")
            print(f"  every other premium identical: {'yes' if not other else other[:3]}")
            print(f"  total T1 - T0 at ISO: {dtot}; predicted (the families' hand-predicted premiums) {total_pred}  "
                  f"{'ok' if dtot == total_pred else 'DIFFERS'}")
            if not ok:
                FAIL.append("downstream")
    m, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC17-20: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
