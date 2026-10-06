#!/usr/bin/env python3
"""Chunk 23, RC-2 (C23-07..C23-11): the state-only families' golden cases, every one a new ISO probe.

Each record is predicted three ways BEFORE the call (219_'s hand models, 174_'s evaluator, the engine), on the
family's own state's policy, then sent to ISO at 2026-09-17 and compared: the predicted records, every premium on the
policy field for field, and the messages. Each case is aimed where the competing readings give different dollars.

C23-07 MA heating oil   H1 3 tanks + 2 extra buildings, credit ON at the CAP (Pollutant Clean Up 60,000: deduction
                        30 > max 20); H2 the credit UNDER the cap (Pollutant 20,000: deduction 10); H3 1 tank, no extras
C23-08 MA relocation    R1 per-unit calc under the cap, 6 units; R2 a submitted building Group I rate of 2.0 pushes the
                        per-unit calc (7.5 x r3(2.0 x LOI)) over the cap of 10: 3 units -> 3 x 10 (the cap is per unit)
C23-09 AK fees          K1 Legal Liability building fee 10 x its limit, contents 4 x, policy fee 500,000 on
                        Mortgageholders 25,000 x 1,000; K2 policy fee 74,999 (trunc(2.99996) = 2, a rounded ratio gives 3)
C23-10 CA earthquake    C1 Limited EQ 1,000,000 / 400,000 / 300,000 + Additional EQ manual 1,234.5 (half-up 1,235;
                        half-even would give 1,234); C2 Limited EQ on the BLANKETED building (two buildings in an EQ
                        blanket of unequal values: the average rate x EQLimitToUse, not the record's limit x its own rate)
C23-11 VA O&L forms     V1 broad + tenants, A and B & C Separate, Special, EQ, pollutant 150, beside the countrywide
                        Ordinance or Law form; V2 Combined, Broad, post-loss "Yes"; V3 Coverage C Only, Basic
                        (closes chunk 12's open "VA priced case")

    python scripts/cf/220_chunk23_rc2.py [--live] [--cases H1,K2]
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

m = import_module("219_chunk23_rc1")
r2, rc1, gc, rep, cmp, r11 = m.r2, m.rc1, m.gc, m.rep, m.cmp, m.r11
P, D = m.P, m.D
FAIL = []
MA_RECS, AK_RECS = [m.HO, m.HOC, m.TR], [m.AKS, m.AKP, m.AKF]
CA_RECS = [m.LEQ + "Building", m.LEQ + "PrsnlProp", m.LEQ + "BusnIncome", m.ADDEQ]
VA_RECS = m.PREMIUM_RECS["VA"]
OL_CW = "OrdinanceOrLawCoverage"
#: 200_'s payload: the Mortgageholders E&O record declares Limit as TEXT ("25,000"), every other Limit is xs:int
m20 = import_module("200_chunk20_rc2")
r11.NUMERIC |= {"BasicGroupIRate", "EQCauseOfLossCovBlktIDNum", "TotalLimit", "NumberMortgages"}


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def state_req(req, j, localize=True):
    for c in req["body"]["CommercialProperty"]:
        c["State"] = j
    req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
    if not localize:                           # a case whose missing input is the subject
        return req
    import _state_inputs                       # C28-17: the state's own Group II territory, as gc.run gives
    return _state_inputs.localize_request(req, j)


# ------------------------------------------------------------------ trees

def ma(limit_pc="60000", tanks="3", extra="2", units="4", bgi=None):
    def b():
        sub = m.ma_tree(tanks=tanks, extra=extra, units=units)
        m.at(sub)[P + "Location"][P + m.PC + "Table"][P + m.PC][0]["Limit"] = limit_pc
        if bgi:
            m.at(sub)[P + "Structure"]["BasicGroupIRate"] = bgi
        return sub
    return b


def ak(struct_x=10, pp_x=4, fee="500000", mortgages="1000"):
    def b():
        sub = m.portable("AK")
        a = m.at(sub)
        st, pp = a[P + "Structure"], a[P + "PersonalProperty"]
        sub0 = m.ak_tree(struct_lim=str(int(st["Limit"]) * struct_x), pp_lim=str(int(pp["Limit"]) * pp_x), fee=fee)
        cp = sub0[P + "Table"][P][0]
        cp[P + m.MORT + "Table"][P + m.MORT][0]["NumberMortgages"] = mortgages
        return sub0
    return b


def ca(manual="1234.5", lim=("1000000", "400000", "300000")):
    return lambda: m.ca_tree(manual=manual, lim=lim)


def ca_blanket():
    """two buildings of unequal value in one EQ blanket (chunk 10's 100_ recipe: the building elected 'Yes, Included in
    Blanket' with the blanket's ID, the detail's EQCauseOfLossIncludedInBlkt 'Yes'); Limited EQ on the first only."""
    def b():
        sub = m.ca_tree(manual=None, lim=("150000", "0", "0"))
        cp = sub[P + "Table"][P][0]
        cp["BlktRated"], cp["MUBlktRated"] = "Yes", "No"
        loc = m.at(sub)[P + "Location"]
        sts = loc[P + "StructureTable"][P + "Structure"]
        b2 = copy.deepcopy(sts[0])
        for k in [k for k in b2 if k.endswith("Table")]:
            b2.pop(k)
        b2.update({"Limit": "600000", "FullBldgValue": "600000", "ClassCode": "0311"})
        sts.append(b2)
        total = sum(int(s["Limit"]) for s in sts)
        cp[P + "BlanketRatingTable"] = {P + "BlanketRating": [{P + "BlanketRatingDetailTable": {P + "BlanketRatingDetail": [{
            "UnitNumber": "100", "TypeOfBlanketRating": "Average", "Type": "Building Only", "Coinsurance": "90%",
            "CauseOfLoss": sts[0].get("CauseOfLoss", "Special"), "TotalLimit": str(total), "EQCauseOfLossIncludedInBlkt": "Yes"}]}}]}
        for s_ in sts:
            s_.update({"EQCovIndicator": "Yes, Included in Blanket", "EQCauseOfLossCovBlktIDNum": "100", "IncludedInBlkt": "No"})
        return sub
    return b


def va(covtype="Coverages A and B & C Separate", cause="Special", post="No", pollutant="150", cw=False):
    def b():
        sub = m.va_tree(covtype, cause, post, pollutant=pollutant)
        st = m.at(sub)[P + "Structure"]
        for c in (st[P + m.VABF + "Table"][P + m.VABF][0], st[P + m.VAT + "Table"][P + m.VAT][0]):
            c.update({"CovBDemolitionLimit": "200000", "CovCIncreasedConstructionLimit": "300000",
                      "CombinedBAndCDemolitionAndIncrdConstrctnLimit": "500000"})
        if cw:
            st[P + OL_CW + "Table"] = {P + OL_CW: [{"CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000",
                                                     "CovCIncreasedConstructionLimit": "30000", "PostLossOrdinanceOrLawOption": "No"}]}
        return sub
    return b


def cases():
    return {
        "H1": ("C23-07", "MA", "remediation 3 tanks + 2 buildings; credit AT the cap (Pollutant 60,000)", ma(), MA_RECS),
        "H2": ("C23-07", "MA", "credit UNDER the cap (Pollutant 20,000)", ma(limit_pc="20000"), MA_RECS),
        "H3": ("C23-07", "MA", "1 tank, no extra buildings", ma(tanks="1", extra=None), MA_RECS),
        "R1": ("C23-08", "MA", "tenant relocation, per-unit calc under the cap, 6 units", ma(units="6"), [m.TR]),
        "R2": ("C23-08", "MA", "building Group I rate 2.0 submitted: per-unit calc over the cap, 3 units", ma(units="3", bgi="2.0"), [m.TR]),
        "K1": ("C23-09", "AK", "Legal Liability: building fee 10 x, contents 4 x, policy 500,000 on 25,000 x 1,000", ak(), AK_RECS),
        "K2": ("C23-09", "AK", "policy fee 74,999 (truncated ratio 2)", ak(fee="74999"), AK_RECS),
        "C1": ("C23-10", "CA", "Limited EQ 1,000,000 / 400,000 / 300,000 + Additional EQ 1,234.5", ca(), CA_RECS),
        "C2": ("C23-10", "CA", "Limited EQ on a blanketed building: predicted UNREACHABLE ($0 + no-EQ-blanket message: blanket EQ values need an EQ endorsement record, which Limited EQ excludes)", ca_blanket(), CA_RECS[:1]),
        "V1": ("C23-11", "VA", "broad + tenants, A and B & C Separate, Special, EQ, pollutant, beside the CW form", va(cw=True), VA_RECS),
        "V2": ("C23-11", "VA", "A and B & C Combined, Broad, post-loss Yes", va("Coverages A and B & C Combined", "Broad", "Yes"), VA_RECS),
        "V3": ("C23-11", "VA", "Coverage C Only, Basic, no pollutant", va("Coverage C Only", "Basic", pollutant=None), VA_RECS),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, recs)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        data, ip, err = m.rated(build(), j)
        if err:
            print(f"{cid} {task} {j} {label}: engine RAISED {err}")
            FAIL.append(cid)
            continue
        preds[cid], lines, bad = {}, [], False
        for rec in recs:
            res = m.predict(j, data, rec)
            ok = bool(res) and all(m.same(hv, e) and m.same(ev, e) for hv, ev, e in res)
            bad |= not ok
            preds[cid][rec] = [hv for hv, _, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[-58:]:58s} hand {[str(x) for x, _, _ in res]} evaluator {[str(x) for _, x, _ in res]} engine {[e for _, _, e in res]}")
        nz = sum(1 for rec in recs for x in preds[cid][rec] if not m.same(x, 0))
        print(f"{cid} {task} {j} {label}: engine {'as predicted' if not bad else 'DIFFERS'} ({nz} non-zero premiums predicted)")
        if not cid.startswith("V") or bad:
            print("\n".join(lines))
        else:
            print("\n".join(x for x in lines if "engine ['0']" not in x and "engine []" not in x))
        if bad:
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, j, label, build, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = state_req(m20.payload(build()), j)
            (gc.OUT / f"chunk23_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,260})', str(exc.body))
                print(f"  {cid} ISO REFUSES {mm_.group(0)[:280] if mm_ else str(exc.body)[:280]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk23_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not m.same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not m.same(x, 0)]
                if sorted(D(str(x)) for x in iso) != sorted(D(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not dd and mi == mo
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(dd)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {rr[-55:]}: ISO {x}, derived {w}" for rr, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C23-07..C23-11): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
