#!/usr/bin/env python3
"""Chunk 22, RC-2: golden cases, every one a new multi-location ISO probe (no stored policy has two locations).

Every record is predicted three ways BEFORE the call: a hand model written from the rule text (inputs from the
submission; the contents' own final rates, EQ limit and chunk 9's blanket average rate are read off the
engine, all ISO-confirmed in earlier chunks), 174_'s independent SetPremium evaluator, and the engine. Then
ISO at 2026-09-17: the predicted records, every premium on the policy field for field, and the messages.

C22-07  V1 Value Reporting "Not Used", Special, contents 100,000 / 500,000: each row at its own rates.
        V2 the same at Broad, with contents earthquake on both rows.
C22-08  U1 Value Reporting "Used": OI-119, ISO and ours both refuse (pinned as the expected result).
C22-09  B1 three locations, rows 1 and 2 in a "Personal Property Only" blanket at Monthly Reporting, row 3 not:
        blanket average rate (rows 1, 2) and own rate (row 3) on one policy, each a different value.
C22-10  G1 Broad, incidental 25,000, acquired 60,000 (> 50,000: priced). G2 Special + EQ incidental, acquired
        exactly 50,000 (not > 50,000: $0). G3 seasonal risk on row 2 only (0.3 x limit vs 0.75 x limit).
C22-11  A1 Additional Locations, two locations, 90% (factor 1.05), Special. A2 three locations, 100% (1.0),
        Broad, contents earthquake on every row.
C22-12  the roll-up, on A1 / A2: Personal Property's ordinary premium $0, the GI's PrsnlPropPremium 0 (nothing
        writes the Provisions record's own Premium, RC-1 finding 6).

    python scripts/cf/215_chunk22_rc2.py [--live] [--cases V1,A1]
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

h = import_module("213_chunk22_rc1")           # also adds the chunk 22 numeric fields to r11.NUMERIC
r2, rc1, g19, r4 = h.r2, h.rc1, h.g19, h.r4
gc, rep, cmp, r11 = r2.gc, r2.rep, r2.cmp, r2.r11
r16 = import_module("174_chunk16_rc1")
cen20 = import_module("901_chunk20_census")
P, VR, AL, r = h.P, h.VR, h.AL, h.r
same = r2.same
r11.NUMERIC |= {"FullPrsnlPropValue"}           # xs:int on the contents; ISO refuses it as a string
FAIL = []
EXPECT_REFUSAL = {"U1": "maxLimit"}
EQ_YES = ("Yes, Not Included in Blanket", "Yes, Included in Blanket")
GRP = {"BasicGroupI": "BGI", "BasicGroupII": "BGII", "Broad": "Broad", "Special": "Special", "Earthquake": "EQ"}
VR_RECS = [VR + g + "Coverage" for g in GRP]
AL_GI_RECS = [AL + "GeneralInformation" + g + "Coverage" for g in GRP]
AL_PR_RECS = [AL + "Provisions" + g + "Coverage" for g in GRP]
SEASONAL = Decimal(r4.rows("OR", "SeasonalRiskFactor")[0]["Factor"])
NEWBUSN = Decimal(r4.rows("OR", "NewBusnFactor")[0]["Factor"])
INC_RATE = {row["CauseOfLoss"]: Decimal(row["Rate"]) for row in r4.rows("OR", "ValRptgIncLocsRate")}
ACQ_RATE = Decimal(r4.rows("OR", "ValRptgAcqrdLocsRate")[0]["Rate"])
ALSC_90 = Decimal(r4.rows("OR", "AddlLocSpclCoinsFactor")[0]["Factor"])


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


# ------------------------------------------------------------------ trees

def eq_contents(sub):
    """the contents' OWN earthquake election (chunk 19's 191_ recipe): indicator, grade, the endorsement record."""
    at = rc1.node_dicts(sub)
    st = at[P + "Structure"]
    at[P + "PersonalProperty"].update({k: st[k] for k in ("EQCovIndicator", "EQCoinsurance", "EQDeductible") if k in st})
    at[P + "PersonalProperty"].update({"EQGrade": "2", "EQSprinklerLeakageOnly": "Not Applicable"})
    r2.put(sub, "EarthquakeAndVolcanicEruptionEndorsementPrsnlProp")


def tree(vr=None, al=False, cause="Special", limits=("100000", "500000"), gi=None, vrf=None, eq=False, full=None,
         coins="Monthly Reporting", al_coins="90%"):
    """the Oregon policy at `cause`, the forms placed on location 1, then location 1 copied once per extra limit."""
    sub = g19.with_cause(g19.portable("OR"), cause)
    if eq:
        eq_contents(sub)
    pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
    if vr is not None:
        pp["Coinsurance"] = coins
        r2.put(sub, VR + "GeneralInformation", dict(h.VR_GI, MultiLocAvgRates=vr, CauseOfLoss=cause,
                                                     EQCauseOfLoss="Yes" if eq else "No", **(gi or {})))
        r2.put(sub, VR, dict({"AvgVal": "40000", "SpecificIns": "0", "SeasonalRisk": "No"}, **(vrf or {})))
    if al:
        r2.put(sub, AL + "GeneralInformation", dict(h.AL_GI, CauseOfLoss=cause, Coinsurance=al_coins))
        r2.put(sub, AL + "Provisions", {"FullValue": "0"})
    ls = h.locations(sub)
    for k in range(1, len(limits)):
        ls.append(copy.deepcopy(ls[0]))
        ls[k]["LocationNumber"] = str(k + 1)
    for k, lim in enumerate(limits):
        c = h.contents(ls[k])
        c["Limit"] = lim
        if al:
            fv = (full or limits)[k]
            c[P + AL + "ProvisionsTable"][P + AL + "Provisions"][0]["FullValue"] = fv
            c["FullPrsnlPropValue"] = fv
    return sub


def seasonal_row2(sub):
    h.contents(h.locations(sub)[1])[P + VR + "Table"][P + VR][0]["SeasonalRisk"] = "Yes"
    return sub


def blanket(sub, members=(0, 1), total="600000"):
    """rows `members` in one "Personal Property Only" blanket at Monthly Reporting (201_'s blanket shape)."""
    cp = sub[P + "Table"][P][0]
    cp["BlktRated"], cp["MUBlktRated"] = "Yes", "No"
    cause = h.contents(h.locations(sub)[0])["CauseOfLoss"]
    cp[P + "BlanketRatingTable"] = {P + "BlanketRating": [{P + "BlanketRatingDetailTable": {P + "BlanketRatingDetail": [
        {"UnitNumber": "100", "Type": "Personal Property Only", "TypeOfBlanketRating": "Average", "CauseOfLoss": cause,
         "Coinsurance": "Monthly Reporting", "TotalLimit": total, "RadioactiveContamination": "No"}]}}]}
    for k in members:
        c = h.contents(h.locations(sub)[k])
        c.update({"IncludedInBlkt": "Yes", "BlktIDNum": "100", "FullPrsnlPropValue": c["Limit"]})
    return sub


def cases():
    return {
        "V1": ("C22-07", "VR Not Used, Special, 100,000 / 500,000", lambda: tree(vr="Not Used"), VR_RECS + [VR + "GeneralInformation"]),
        "V2": ("C22-07", "VR Not Used, Broad, contents EQ on both rows", lambda: tree(vr="Not Used", cause="Broad", eq=True),
               VR_RECS + [VR + "GeneralInformation"]),
        "U1": ("C22-08", "VR Used (OI-119: ISO and ours refuse)", lambda: tree(vr="Used"), []),
        "B1": ("C22-09", "VR Not Used, rows 1-2 blanketed (Monthly Reporting), row 3 own rate",
               lambda: blanket(tree(vr="Not Used", limits=("100000", "500000", "200000"))), VR_RECS),
        "G1": ("C22-10", "GI Broad, incidental 25,000, acquired 60,000",
               lambda: tree(vr="Not Used", cause="Broad", gi={"YourBusnPrsnlPropInc": "25000", "StockOnlyAcqrd": "60000"}),
               [VR + "GeneralInformation"]),
        "G2": ("C22-10", "GI Special + EQ, incidental 7,500 + 2,500, acquired 50,000 (not over)",
               lambda: tree(vr="Not Used", eq=True, gi={"YourBusnPrsnlPropInc": "7500", "PrsnlPropOthersInc": "2500",
                                                         "StockOnlyAcqrd": "50000"}),
               [VR + "GeneralInformation"]),
        "G3": ("C22-10", "seasonal risk on row 2 only", lambda: seasonal_row2(tree(vr="Not Used")), VR_RECS),
        "A1": ("C22-11", "AL two locations, 90%, Special", lambda: tree(al=True, full=("200000", "100000")),
               AL_GI_RECS + AL_PR_RECS),
        "A2": ("C22-11", "AL three locations, 100%, Broad, contents EQ",
               lambda: tree(al=True, cause="Broad", eq=True, al_coins="100%", limits=("100000", "150000", "50000")),
               AL_GI_RECS + AL_PR_RECS),
    }


# ------------------------------------------------------------------ hand models

def val(n, f):
    c = n.first(f)
    return None if c is None or c.text in (None, "") else c.text


def d(n, f, default="0"):
    return Decimal(val(n, f) or default)


def up(n, k):
    for _ in range(k):
        n = n.parent
    return n


def root(n):
    while n.tag != P:
        n = n.parent
    return n


def mods(x, cp, mpdc_node, grp, eq=False, broad_twice=False):
    """the modifier chain each record applies, each step rounded to the dollar."""
    if not eq:
        for f in (d(cp, "PackageModFactor"), d(mpdc_node, "MultiPremiumAndDispersionCreditFactor"), d(cp, "IRPMFactor")):
            x = r(x * f, 0)
    c1 = f"CyberIncidentExclusionFactor{grp}"
    c2 = c1 if broad_twice else f"CyberIncidentExclusionCOLExcptnsFactor{grp}"   # the VR Form's Broad reads c1 twice
    return r(r(x * d(cp, c1), 0) * d(cp, c2), 0)


def vr_hand(node, rec):
    g = rec[len(VR):-len("Coverage")]
    vrf, pp, cp = node.parent, up(node, 3), root(node)
    cause = val(pp, "CauseOfLoss")
    if (g == "Broad" and cause != "Broad") or (g == "Special" and cause != "Special") or \
            (g == "Earthquake" and val(pp, "EQCovIndicator") not in EQ_YES):
        return Decimal(0)
    seasonal = val(vrf, "SeasonalRisk") == "Yes"
    sf, nb = (SEASONAL, Decimal(1)) if seasonal else (Decimal(1), NEWBUSN)
    if g == "Earthquake":
        return mods(r(d(pp, "FinalEQRate") * d(pp, "EQLimitToUse") / 100, 0), cp, pp, "EQ", eq=True)
    if val(pp, "IncludedInBlkt") == "Yes":
        det = rc1.find(cp, P + "BlanketRatingDetail")[0]
        members = [x for x in rc1.find(cp, P + "PersonalProperty") if val(x, "IncludedInBlkt") == "Yes"]
        tot = sum(d(x, "FullPrsnlPropValue") for x in members)
        lim = r(r(sf * nb * d(det, "TotalLimit"), 0) * d(pp, "FullPrsnlPropValue") / tot, 0)
        rate = d(pp, f"Blkt{g}AvgRate")
    else:
        lim = r(nb * sf * d(pp, "Limit"), 0)
        rate = d(pp, f"Final{g}Rate")
    return mods(r(rate * lim / 100, 0), cp, pp, GRP[g], broad_twice=g == "Broad")


def vr_gi_hand(node):
    cp = root(node)
    lcm = d(cp, "LossCostMultiplier")
    inc = sum(d(node, k) for k in ("YourBusnPrsnlPropInc", "StockOnlyInc", "PrsnlPropOthersInc"))
    acq = sum(d(node, k) for k in ("YourBusnPrsnlPropAcqrd", "StockOnlyAcqrd", "PrsnlPropOthersAcqrd"))
    cause = val(node, "CauseOfLoss")
    base = {k: r(r(rate * lcm, 3) * inc / 100, 0) for k, rate in INC_RATE.items()}
    tot = mods(base["Basic"], cp, cp, "BGI")
    tot += mods(base["Broad"], cp, cp, "Broad") if cause == "Broad" else 0
    tot += mods(base["Special"], cp, cp, "Special") if cause == "Special" else 0
    tot += mods(base["Earthquake"], cp, cp, "EQ", eq=True) if val(node, "EQCauseOfLoss") == "Yes" else 0
    if val(node, "MultiLocAvgRates") == "Not Used" and acq > 50000:
        x = r(r(ACQ_RATE * lcm, 3) * acq / 100, 0)
        for f in (d(cp, "PackageModFactor"), d(cp, "MultiPremiumAndDispersionCreditFactor"), d(cp, "IRPMFactor")):
            x = r(x * f, 0)
        tot += x
    return tot


def al_mlars(gi, cp):
    """the five AL MLARs by hand from the submission and the contents' own final rates."""
    lcm = d(cp, "LossCostMultiplier")
    inc = sum(d(gi, k) for k in ("YourBusnPrsnlPropInc", "StockOnlyInc", "PrsnlPropOthersInc"))
    rows = [(d(prov, "FullValue"), pp) for pp in rc1.find(cp, P + "PersonalProperty")
            for prov in rc1.find(pp, P + AL + "Provisions")[:1]]
    tfv = sum(fv for fv, _ in rows)
    den = inc + tfv
    cause = val(gi, "CauseOfLoss")
    inc_rate = {"BasicGroupI": INC_RATE["Basic"], "Broad": INC_RATE["Broad"] if cause == "Broad" else Decimal(0),
                "Special": INC_RATE["Special"] if cause == "Special" else Decimal(0), "EQ": INC_RATE["Earthquake"]}
    out = {}
    for g, fr in (("BasicGroupI", "FinalBasicGroupIRate"), ("BasicGroupII", "FinalBasicGroupIIRate"), ("Broad", "FinalBroadRate"),
                  ("Special", "FinalSpecialRate"), ("EQ", "FinalEQRate")):
        times = sum(r(fv * d(pp, fr), 0) for fv, pp in rows)          # full value x rate: NOT divided by 100
        if g != "BasicGroupII":                                       # Group II's numerator omits the incidental part
            times += r(r(inc_rate[g] * lcm, 3) * inc / 100, 0)
        out[g] = Decimal(0) if den == 0 else r(times / den, 3)
    cf = ALSC_90 if val(gi, "Coinsurance") == "90%" else Decimal(1)
    return out, cf, inc, tfv


def al_hand(node, rec):
    cp = root(node)
    gi = rc1.find(cp, P + AL + "GeneralInformation")[0]
    mlar, cf, inc, tfv = al_mlars(gi, cp)
    g = rec.split("Provisions" if "Provisions" in rec else "GeneralInformation")[1][:-len("Coverage")]
    key = "EQ" if g == "Earthquake" else g
    if "Provisions" in rec:
        pp = up(node, 3)
        cause = val(pp, "CauseOfLoss")
        if (g == "Broad" and cause != "Broad") or (g == "Special" and cause != "Special") or \
                (g == "Earthquake" and val(pp, "EQCovIndicator") in ("No Coverage", "Yes, Included in Blanket")):
            return Decimal(0)
        lim = r(d(node.parent, "FullValue") / tfv * d(gi, "OverallLimit"), 0)
        return mods(r(lim / 100 * mlar[key] * cf, 0), cp, pp, GRP[g], eq=g == "Earthquake")
    cause = val(gi, "CauseOfLoss")
    any_eq = any(val(pp, "EQCovIndicator") in EQ_YES for pp in rc1.find(cp, P + "PersonalProperty"))
    if (g == "Broad" and cause != "Broad") or (g == "Special" and cause != "Special") or (g == "Earthquake" and not any_eq):
        return Decimal(0)
    return mods(r(inc / 100 * mlar[key] * cf, 0), cp, cp, GRP[g], eq=g == "Earthquake")


def hand(node, rec):
    if rec == VR + "GeneralInformation":
        return vr_gi_hand(node)
    if rec.startswith(VR):
        return vr_hand(node, rec)
    return al_hand(node, rec)


def predict(data, rec):
    body = cen20.set_premium((r2.CW / "Rules" / f"{P}{rec}Rules.Rule.xml").read_text(encoding="utf-8-sig"))
    out = []
    for node in rc1.find(data, P + rec):
        prem = node.first("Premium")
        # a switched-off record never reaches SetPremium: ErcProcess writes 0 (the evaluator would run it anyway)
        ev = Decimal(0) if val(node, "CoverageOnPolicyIndicator") == "0" else r16.hand(body, node)
        out.append((hand(node, rec), ev, None if prem is None else prem.text))
    return out


def iso_field(resp, rec, field):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + rec:
                out.append(o.get(field))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return out


def short(rec):
    return rec.replace(AL, "AL").replace(VR, "VR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, label, build, recs)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        data, ip, err = h.rated(build())
        if err:
            ok = cid in EXPECT_REFUSAL and EXPECT_REFUSAL[cid] in err
            print(f"{cid} {task} {label}: engine REFUSES{' as predicted' if ok else ''}: {err[:120]}")
            if not ok:
                FAIL.append(cid)
            continue
        if cid in EXPECT_REFUSAL:
            print(f"{cid} {task} {label}: engine RATES, refusal predicted")
            FAIL.append(cid)
            continue
        preds[cid] = {}
        lines, bad = [], False
        for rec in recs:
            res = predict(data, rec)
            ok = bool(res) and all(same(hh, e) and same(ev, e) for hh, ev, e in res)
            bad |= not ok
            preds[cid][rec] = [hh for hh, _, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {short(rec):40s} hand {[str(x) for x, _, _ in res]}"
                         f"  evaluator {[str(ev) for _, ev, _ in res]}  engine {[e for _, _, e in res]}")
        contents = [val(n, "Premium") for n in rc1.find(data, P + "PersonalPropertyPrsnlPropBasicGroupICoverage")]
        print(f"{cid} {task} {label}: engine {'as predicted' if not bad else 'DIFFERS'}; ordinary contents Group I {contents}")
        print("\n".join(lines))
        if any(c not in ("0", "0.0", None) for c in contents):
            print("      FAIL the ordinary contents premium should be switched off on every row")
            bad = True
        if cid.startswith("A"):
            gi = rc1.find(data, P + AL + "GeneralInformation")[0]
            okr = val(gi, "PrsnlPropPremium") in ("0", "0.0")
            print(f"      {'ok  ' if okr else 'FAIL'} C22-12 roll-up: GI PrsnlPropPremium {val(gi, 'PrsnlPropPremium')} (predicted 0)")
            bad |= not okr
        if bad:
            FAIL.append(cid)
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, label, build, recs)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            (gc.OUT / f"chunk22_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                body = str(exc.body)
                m = re.search(r'"Message":"([^"]{0,260})', body)
                what = m.group(1) if m else body[:260]
                if cid in EXPECT_REFUSAL and EXPECT_REFUSAL[cid] in what:
                    print(f"  {cid} REFUSES AS PREDICTED (OI-119; ours refuses too): {what[:160]}")
                    continue
                print(f"  {cid} ISO REFUSES {what}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk22_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            if cid in EXPECT_REFUSAL:
                print(f"  {cid} ISO PRICES where a refusal was predicted")
                FAIL.append(f"{cid} live")
                continue
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            extra = ""
            if cid.startswith("A"):
                ppp = iso_field(resp, AL + "GeneralInformation", "PrsnlPropPremium")
                extra = f"; ISO GI PrsnlPropPremium {ppp}"
                if any(x not in (None, 0, "0", 0.0) for x in ppp):
                    pbad.append(("PrsnlPropPremium", ppp, ["0"]))
            ok = not pbad and not dd and mi == mo
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(dd)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}{extra}"
                  + "".join(f"\n        predicted {short(str(rr))[-50:]}: ISO {x}, derived {w}" for rr, x, w in pbad[:8])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + (f"\n        ISO only {sorted(mi - mo)[:4]}\n        ours only {sorted(mo - mi)[:4]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C22-07..C22-12): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
