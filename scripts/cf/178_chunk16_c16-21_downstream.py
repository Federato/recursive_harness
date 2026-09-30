#!/usr/bin/env python3
"""Chunk 16, RC-5 (C16-21): what the chunk 16 families feed downstream.

Predicted from the rules before running (2026-09-25):
  TOTAL      each record's Premium enters the policy total like any other (chunk 14), so adding
             the families on the Basic cause -- which changes no parent coverage's own inputs --
             moves the total by EXACTLY the sum of their premiums, each predicted by hand (175_'s
             method: the family factor from its own table, the rule evaluated by hand).
               T0  RC-2's Oregon policy + terrorism in effect, no chunk 16 record
               T1  the same + EPI (BI 270 / SCBI 180), no waiting period (BI "Eliminated", SCBI
                   "24 hours"), Civil Authority (BI 180 / SCBI 90, each with Radius 1,090), Pollutant
                   Clean Up (60,000 / 2,500), Molten Material x5, Spoilage (Florists, 25,000)
  CORRECTION (first run): the prediction must cover every chunk 16 record that prices, not only
             the ones placed -- the base carries chunk 10's earthquake election, so the EQ forms price
             too ($2,821 predicted, $2,832 at ISO; the $11 was EQ forms). "Every other premium" now
             leaves the families' own records out (one EPI form sits at $0 in T0 and prices in T1).
  T2         the clean test: T1 with Spoilage 40,000 and Pollutant Clean Up 80,000, its total rise
             the hand sum, printed before ISO is asked.
  TERRORISM  no terrorism rule in the countrywide edition reads a chunk 16 record: every terrorism
             field on the policy is identical in T0 and T1, and no chunk 16 record carries one.
  STAT CODES unlike chunk 15, these families carry stat-code rules (no waiting period and Civil
             Authority containers, Pollutant Clean Up, Molten Material x5, Spoilage). Every stat
             value ISO returns on a chunk 16 record or container is compared with ours strictly as
             text (161_'s rule), on every stored chunk 16 response (RC-2, RC-3, RC-4) and T1.

    python scripts/cf/178_chunk16_c16-21_downstream.py [--live]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

r2 = import_module("175_chunk16_rc2")
d15 = import_module("172_chunk15_c15-19_downstream")
tot = import_module("159_chunk14_rc2_total")
r16, rc1, gc, rep, cmp, r11 = r2.r16, r2.rc1, r2.gc, r2.rep, r2.cmp, r2.r11
P = "CommercialProperty"
OUT = gc.OUT
NW, NW_SC, CA, PC = r2.NW, r2.NW_SC, r2.CA, r2.PC
FAIL = []

POP = r16.population()
RECS = {r for rs in POP.values() for r in rs} | {
    P + NW, P + NW + "SpclClassBusnIncome", P + CA, P + CA + "SpclClassBusnIncome", P + PC,
    P + "BusinessIncomeExtendedPeriodOfIndemnityCoverage", P + "SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage"}

E = lambda f: f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"
ES = lambda f: f"SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"
MOLT = ["MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome", "MoltenMaterialSpecialClass",
        "MoltenMaterialSpclClassBusnIncome"]
SPOIL = dict(r2.SPOIL, Limit="25000")


import _regress  # noqa: E402  regression-mode sampling: 104_ sets CF_REGRESSION_SAMPLE; gates run in full

def t0():
    return tot.terror(r2.base())


def t1():
    sub = t0()
    at = rc1.node_dicts(sub)
    at[P + "BusinessIncome"]["ExtendedPeriod"] = "270"
    at[P + "SpecialClassBusnIncome"]["ExtendedPeriod"] = "180"
    for f in ("BasicGroupI", "BasicGroupII"):
        for rec in (E(f), ES(f), f"{NW}{f}Coverage", f"{NW_SC}{f}Coverage", f"{CA}{f}Coverage",
                    f"{CA}SpclClassBusnIncome{f}Coverage", f"{PC}{f}Coverage"):
            r2.put(sub, rec)
    r2.put(sub, f"{CA}RadiusCoverage", {"ManualPremium": r2.rc2.MANUAL})
    r2.put(sub, f"{CA}SpclClassBusnIncomeRadiusCoverage", {"ManualPremium": r2.rc2.MANUAL})
    r2.container(sub, "BusinessIncome", NW)["TimePeriod"] = "Eliminated"
    r2.container(sub, "SpecialClassBusnIncome", NW + "SpclClassBusnIncome")["TimePeriod"] = "Replaced By 24 Hours"
    r2.container(sub, "BusinessIncome", CA)["IncreasedCoveragePeriod"] = "180"
    r2.container(sub, "SpecialClassBusnIncome", CA + "SpclClassBusnIncome")["IncreasedCoveragePeriod"] = "90"
    r2.container(sub, "Location", PC).update({"Limit": "60000", "Deductible": "2,500"})
    for rec in MOLT:
        r2.put(sub, rec)
    r2.put(sub, "SpoilageCoverage", dict(SPOIL))
    return sub


def overrides():
    ov = {}
    for f in ("BasicGroupI", "BasicGroupII"):
        ov[E(f)] = {"Factor": r2.EPI_F["270"]}
        ov[ES(f)] = {"Factor": r2.EPI_F["180"]}
        ov[f"{NW}{f}Coverage"] = {"../Factor": r2.TIME_F["Eliminated"]}
        ov[f"{NW_SC}{f}Coverage"] = {"../Factor": r2.TIME_F["Replaced By 24 Hours"]}
        ov[f"{CA}{f}Coverage"] = {"../Factor": r2.CIVIL_F["180"]}
        ov[f"{CA}SpclClassBusnIncome{f}Coverage"] = {"../Factor": r2.CIVIL_F["90"]}
    ov[f"{CA}RadiusCoverage"] = {}
    ov[f"{CA}SpclClassBusnIncomeRadiusCoverage"] = {}
    ov[f"{PC}BasicGroupICoverage"] = {"BasicGroupIFactor": r2.POLL_RATE["GroupI"], "DeductibleFactor": r2.POLL_DED["2,500"],
                                      "HighestPollutantBGIRate": "LAST_BGI"}
    ov[f"{PC}BasicGroupIICoverage"] = {"BasicGroupIIFactor": r2.POLL_RATE["GroupII"], "DeductibleFactor": r2.POLL_DED["2,500"]}
    for rec in MOLT:
        ov[rec] = {"Factor": r2.MOLTEN_F}
    cls, rate, spf = r2.spoilage_factors(SPOIL["Description"], SPOIL["SpoilageCauseOfLoss"],
                                         SPOIL["RefrigerationMaintenanceAgreement"], SPOIL["SellingPrice"])
    ov["SpoilageCoverage"] = {"Class": cls, "Rate": rate, "SellingPriceFactor": spf}
    return ov


def family_override(rec):
    """the family factor for any chunk 16 record (the EQ forms the placed list did not name)."""
    if "ExtendedPeriodOfIndemnity" in rec:
        return {"Factor": r2.EPI_F["180" if rec.startswith("SpecialClass") else "270"]}
    if rec.startswith(NW_SC):
        return {"../Factor": r2.TIME_F["Replaced By 24 Hours"]}
    if rec.startswith(NW):
        return {"../Factor": r2.TIME_F["Eliminated"]}
    if rec.startswith(CA) and "Radius" not in rec:
        return {"../Factor": r2.CIVIL_F["90" if "SpclClassBusnIncome" in rec else "180"]}
    if rec.startswith(PC):
        form = rec[len(PC):-len("Coverage")]
        key = {"BasicGroupI": ("BasicGroupIFactor", "GroupI"), "BasicGroupII": ("BasicGroupIIFactor", "GroupII"),
               "Broad": ("BroadRate", "Broad"), "Special": ("SpecialRate", "Special"),
               "Earthquake": ("EQFactor", "Earthquake")}[form]
        return {key[0]: r2.POLL_RATE[key[1]], "DeductibleFactor": r2.POLL_DED["2,500"]}
    return {}


def t2():
    """T1 with other limits (Spoilage 40,000, Pollutant Clean Up 80,000): the clean test, its total
    predicted by hand and printed before ISO is asked."""
    sub = t1()
    pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
    for rec in pp[P + "SpoilageCoverageTable"][P + "SpoilageCoverage"]:
        rec["Limit"] = "40000"
    r2.container(sub, "Location", PC)["Limit"] = "80000"
    return sub


def hand_sum(sub):
    """every chunk 16 premium on the rated tree, predicted by hand: (sum, rows)."""
    d1, _ = gc.run(sub, "OR")
    total_pred, rows = Decimal(0), []
    # every chunk 16 record ON THE TREE, not only the ones placed: the base policy carries chunk 10's
    # earthquake election, so the families' EQ forms price too (the first run left them out and
    # predicted $2,821 against ISO's $2,832 -- $11 of EQ forms)
    ov_all = overrides()
    for rec in sorted({r.replace(P, "", 1) for r in RECS if r.startswith(P) and r in {x for rs in POP.values() for x in rs}}):
        if rec in ov_all or not rc1.find(d1, P + rec):
            continue
        ov_all[rec] = family_override(rec)
    for rec, ov in ov_all.items():
        nodes_ = rc1.find(d1, P + rec)
        if nodes_ and all(n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0"
                          for n in nodes_):
            # a form whose own switch is off (EPI Broad / Special on the Basic cause): $0, nothing to evaluate
            rows.append((rec, Decimal(0), nodes_[0].first("Premium").text if nodes_[0].first("Premium") is not None else None,
                         all(r2.same(n.first("Premium").text if n.first("Premium") is not None else 0, 0) for n in nodes_)))
            continue
        res, checks = r2.predict(d1, rec, ov, "OR")
        for h, e in res:
            ok = not str(h).startswith("hand") and r2.same(h, e)
            rows.append((rec, h, e, ok))
            if not ok:
                FAIL.append(f"engine {rec}")
                print(f"  engine differs from hand: {r16.short(rec)} hand {h} engine {e}")
                continue
            total_pred += Decimal(str(h))
    return total_pred, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    total_pred, rows = hand_sum(t1())
    t2_pred, rows2 = hand_sum(t2())
    print(f"T1: {len(rows)} chunk 16 premiums, engine = hand on {sum(r[3] for r in rows)} of {len(rows)}; "
          f"their sum, predicted by hand: {total_pred}")
    print(f"T2 (clean test, predicted BEFORE its ISO call): {len(rows2)} premiums, engine = hand on "
          f"{sum(r[3] for r in rows2)} of {len(rows2)}; predicted total rise {t2_pred}")

    print("\nSTAT CODES on chunk 16 records and containers (stored responses, strict)")
    n = values = 0
    fields = collections.Counter()
    for rpath in _regress.sample(sorted(OUT.glob("chunk16_rc[234]_*_response.json"))):
        tag = rpath.name[len("chunk16_"):-len("_response.json")]
        req = json.loads((OUT / f"chunk16_{tag}_request.json").read_text(encoding="utf-8"))
        resp = json.loads(rpath.read_text(encoding="utf-8"))
        data, ip = cmp.rate(req)
        want = lambda r: r in RECS
        iso, ours = d15.iso_fields(resp, want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
        n += 1
        values += len(iso)
        fields.update(k.rsplit("/", 1)[-1] for k in iso)
        bad = [(k, v, ours.get(k)) for k, v in iso.items() if not d15.same(v, ours.get(k))]
        if bad:
            FAIL.append(f"stat {tag}")
            print(f"  {tag}: {len(bad)} differ" + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4]))
    print(f"  {n} stored chunk 16 responses re-rated; {values} stat values on chunk 16 records, "
          f"{len(fields)} field names ({', '.join(sorted(fields)[:8])}{'...' if len(fields) > 8 else ''}); "
          f"{'all equal' if not any(f.startswith('stat') for f in FAIL) else 'DIFFERENCES above'}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTOTAL AND TERRORISM (ISO live): T0 without, T1 with the chunk 16 families")
        resp = {}
        for cid, build in (("T0", t0), ("T1", t1), ("T2", t2)):
            req = r11.payload(build())
            (OUT / f"chunk16_c16-21_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:160]}")
                FAIL.append(f"{cid} live")
                continue
            (OUT / f"chunk16_c16-21_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ipr, opr = rep.iso_prem(resp[cid]), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            want = lambda r: r in RECS
            ist, ost = d15.iso_fields(resp[cid], want, d15.STAT.search), d15.our_fields(data, want, d15.STAT.search)
            ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not dd and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 16 stat values, "
                  f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {d15.total_of(resp[cid]):,.0f}"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
            if not ok:
                FAIL.append(f"{cid} live")
        if len(resp) == 3:
            not16 = lambda r: r not in RECS
            a0 = d15.iso_fields(resp["T0"], not16, d15.TERR.search)
            a1 = d15.iso_fields(resp["T1"], not16, d15.TERR.search)
            moved = [(k, v, a1.get(k)) for k, v in a0.items() if not d15.same(v, a1.get(k))]
            on16 = [k for k, v in d15.iso_fields(resp["T1"], lambda r: r in RECS, d15.TERR.search).items() if not d15.blank(v)]
            other = [k for k, v in rep.iso_prem(resp["T0"]).items()
                     if "Total" not in k and k != "CommercialProperty[0]/Premium"
                     and k.rsplit("/", 2)[-2].split("[")[0] not in RECS
                     and not rep.cmp.same(v, rep.iso_prem(resp["T1"]).get(k))]
            dtot = Decimal(str(d15.total_of(resp["T1"]))) - Decimal(str(d15.total_of(resp["T0"])))
            dt2 = Decimal(str(d15.total_of(resp["T2"]))) - Decimal(str(d15.total_of(resp["T0"])))
            print(f"  T2 (clean test) total - T0 at ISO: {dt2}; predicted before the call {t2_pred}  "
                  f"{'ok' if dt2 == t2_pred else 'DIFFERS'}")
            ok = not moved and not on16 and not other and dtot == total_pred and dt2 == t2_pred
            print(f"  terrorism fields T0 vs T1: {len(a0) - len(moved)} of {len(a0)} identical; on chunk 16 records: {len(on16)}")
            print(f"  every other premium identical: {'yes' if not other else other[:3]}")
            print(f"  total T1 - T0 at ISO: {dtot}; predicted (the families' hand-predicted premiums) {total_pred}  "
                  f"{'ok' if dtot == total_pred else 'DIFFERS'}")
            if not ok:
                FAIL.append("downstream")
    print(f"\nC16-21: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
