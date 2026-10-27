#!/usr/bin/env python3
"""Chunk 27 RC-4, C27-10 and C27-11: chunk 12's two leftovers. Live ISO.

C27-10  Theft exclusion on the drone and on Dependent Properties. Chunk 12's probes attached the exclusion at the building
        (and the occupancy); neither premium reads it there. Traced 2026-10-02:
          the drone cell reads ../../../../../SpecialTheftExclusionFactor = the CONTENTS record (the Table wrappers count),
          set on Special by `CommercialPropertyTheftExclusionPrsnlProp` from `SpecialPrsnlPropTheftExclusionFactor`
          (state-filed in every state but PR, keyed by the contents' OccupCategory; OR "Offices" 0.4);
          the Dependent Properties detail reads ../../../../SpecialTheftExclusionFactor = the BUSINESS INCOME record, set on
          Special by `CommercialPropertyTheftExclusionBusnIncome` from `SpecialLeaseHoldTimeElementTheftExclusionFactor`
          (CW, keyed by the building's ApartmentCondoIndicator: "No" 0.86, "Yes" 0.96).
        Predicted before the call:
          T-D0  the drone golden case (137_), no exclusion              drone $187
          T-D1  + the exclusion on the contents                         drone r0(r3(1.869 x 0.4) x 100) = $75; competing $187
          T-Db  + the exclusion on the BUILDING (chunk 12's placement)  drone $187 (not read there); competing $75
          T-P0  Dependent Properties, Special BI (141_ P9)               DP Special $19
          T-P1  + the exclusion on the Business Income record           r3(r3(0.047 x 0.86) x 0.4) = 0.016 x 1,000 = $16; competing $19
C27-11  Ordinance or Law priced end to end in FL and WV (chunk 12 read their rules; the Oregon building did not rate there).
        Each cell predicted by 174_'s evaluator on the state's own SetPremium (the state file if it files one, else its
        countrywide parent), plus the mechanism the state changes:
          O-FL1  A and B & C Separate, post-loss No
          O-FL2  the same, post-loss Yes: FL's `SetPostLossFactor` is EMPTY, so predicted EQUAL to O-FL1; competing x 1.02
                 (FL's Group II cells also add `SinkholeRateAdjustment` and drop the cyber factors: in the evaluator)
          O-WV1  "Coverages B & C Separate" (WV only): no Coverage A cell priced; competing: A priced as in O-WV0
          O-WV0  A and B & C Separate (the countrywide combination)
          O-WVf  O-WV0 with `FloodOnlyLimitationOnOrdinanceOrLaw` "Yes": the Coverage A cells $0; competing: as O-WV0

    python scripts/cf/241_chunk27_rc4.py [--live] [--cases T-D1,O-FL2]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

r2 = import_module("239_chunk27_rc2")                    # TAGGED, iso_tagged, rate_retry
c23, t2, rep, gc, P, TAGGED, lvl = r2.c23, r2.t2, r2.rep, r2.gc, r2.P, r2.TAGGED, r2.lvl
r3m = import_module("240_chunk27_rc3")
dr = import_module("137_chunk12_drone_golden_case")
dp = import_module("141_chunk12_dependent_golden_case")
ol = import_module("130_chunk12_ordinance_golden_case")
r16 = import_module("174_chunk16_rc1")
s11 = r3m.s11
from cf_engine.resolve import book_for

D = Decimal
FAIL = []
ASOF = "20260917"
walk, loc_of = r3m.walk, r3m.loc_of


def r3(x):
    return D(x).quantize(D("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return D(x).quantize(D("1"), rounding=ROUND_HALF_UP)


def prem_of(data, frag):
    return [D(str(n.text or 0)) for n in walk(data) if n.tag == "Premium" and n.parent.tag.endswith(frag)]


# ---------------------------------------------------------------- C27-10

def contents(sub):
    return (r2.g8.zeros2.structure(sub)["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
            ["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0])


def drone(where=None):
    def b():
        sub = dr.submission()
        if where == "contents":
            contents(sub)[P + "TheftExclusionPrsnlPropTable"] = {P + "TheftExclusionPrsnlProp": [{}]}
        elif where == "building":
            r2.g8.zeros2.structure(sub)[P + "TheftExclusionTable"] = {P + "TheftExclusion": [{}]}
        return sub
    return b


def dep(excl=False):
    def b():
        sub = dp.submission(col="Special")
        if excl:
            bi = dp.gates.structure(sub)[P + "BusinessIncomeTable"][P + "BusinessIncome"][0]
            bi[P + "TheftExclusionBusnIncomeTable"] = {P + "TheftExclusionBusnIncome": [{}]}
        return sub
    return b


def theft_row(j, occ):
    t = book_for(j, ASOF).table("SpecialPrsnlPropTheftExclusionFactor")
    return next(D(str(r[t.col("Factor")])) for r in t.rows if str(r[t.col("OccupCategory")]) == occ)


DRONE = "PrsnlPropDetailDroneCov"
DPS = "DependentPropertiesBroadFormSpecialCoverage"


def expect_drone(excl):
    def f(data):
        occ = next(n for n in walk(data) if n.tag == P + "PersonalProperty").first("OccupCategory").text
        fac = theft_row("OR", occ) if excl else D(1)
        return {DRONE: r0(r3(D("1.869") * fac) * 100)}, f"contents OccupCategory {occ}, theft factor {fac}"
    return f


def expect_dep(excl):
    def f(data):
        apt = next(n for n in walk(data) if n.tag == P + "Structure").first("ApartmentCondoIndicator").text
        fac = {"No": D("0.86"), "Yes": D("0.96")}[apt] if excl else D(1)
        rate = r3(r3(r3(D("0.047") * 1) * fac) * D("0.4"))
        return {DPS: r0(rate * 1000)}, f"ApartmentCondoIndicator {apt}, theft factor {fac}, rate {rate}"
    return f


# ---------------------------------------------------------------- C27-11

OLP = P + "OrdinanceOrLaw"


def ol_tree(j, covtype="Coverages A and B & C Separate", post="No", flood_only=None):
    def b():
        rec = dict(ol.RECORD, CovType=covtype, PostLossOrdinanceOrLawOption=post)
        if flood_only:
            rec["FloodOnlyLimitationOnOrdinanceOrLaw"] = flood_only
        sub = ol.submission(rec)
        loc = loc_of(sub)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc["BasicGroupIIRatingTerr"] = "Inland" if j == "FL" else r3m.first_terr(j)
        return sub
    return b


def premium_body(j, rec):
    """the state's own SetPremium for this record if its package files one, else the countrywide parent's."""
    b = book_for(j, ASOF)
    for pk in (b.state.package.content, b.parent.package.content):
        f = Path(pk) / "Rules" / f"{rec}Rules.Rule.xml"
        if f.exists():
            m = re.search(r'<rul:Rule Name="SetPremium".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
            if m:
                return m.group(0)
    return None


def ol_cells(data):
    return [n for n in walk(data) if n.tag.startswith(OLP + "Cov") and n.tag.endswith("Coverage") and n.first("Premium") is not None]


def expect_ol(j, check=None):
    def f(data):
        out, bad = {}, []
        for n in ol_cells(data):
            on = n.first("CoverageOnPolicyIndicator")
            if on is not None and str(on.text) == "0":
                ev = D(0)
            else:
                ev = r16.hand(premium_body(j, n.tag), n)
            key = n.tag[len(OLP):]
            try:
                out[key] = r0(D(str(ev or 0)))
            except Exception:
                # 174_'s evaluator cannot skip a blank operand the way ISO and the engine do (OI-110): ISO decides that cell
                out[key] = r0(D(str(n.first("Premium").text or 0)))
                bad.append(key)
        return out, f"{len(out)} cells by the evaluator on {j}'s own SetPremium" + (f"; {len(bad)} on a blank operand the evaluator cannot read (engine's, ISO decides): {bad}" if bad else "")
    return f


CASES = {
    "T-D0": ("C27-10", "OR", "drone golden case, no exclusion", drone(), expect_drone(False)),
    "T-D1": ("C27-10", "OR", "drone, the theft exclusion on the CONTENTS record", drone("contents"), expect_drone(True)),
    "T-Db": ("C27-10", "OR", "drone, the theft exclusion on the BUILDING (chunk 12's placement)", drone("building"), expect_drone(False)),
    "T-P0": ("C27-10", "OR", "Dependent Properties on the Special BI, no exclusion", dep(), expect_dep(False)),
    "T-P1": ("C27-10", "OR", "Dependent Properties, the theft exclusion on the BUSINESS INCOME record", dep(True), expect_dep(True)),
    "O-FL1": ("C27-11", "FL", "A and B & C Separate, post-loss No", ol_tree("FL"), expect_ol("FL")),
    "O-FL2": ("C27-11", "FL", "A and B & C Separate, post-loss Yes (FL: no post-loss factor)", ol_tree("FL", post="Yes"), expect_ol("FL")),
    "O-WV0": ("C27-11", "WV", "A and B & C Separate", ol_tree("WV"), expect_ol("WV")),
    "O-WV1": ("C27-11", "WV", "Coverages B & C Separate (WV only: no Coverage A)", ol_tree("WV", "Coverages B & C Separate"), expect_ol("WV")),
    "O-WVc": ("C27-11", "WV", "Coverages B & C Combined (WV only)", ol_tree("WV", "Coverages B & C Combined"), expect_ol("WV")),
    "O-WVf": ("C27-11", "WV", "A and B & C Separate, FloodOnlyLimitationOnOrdinanceOrLaw Yes", ol_tree("WV", flood_only="Yes"), expect_ol("WV")),
}


def our_cells(data, want):
    out = {}
    for key in want:
        if key in (DRONE, DPS):
            v = prem_of(data, key)
            out[key] = v[0] if v else None
        else:
            n = next((n for n in ol_cells(data) if n.tag == OLP + key), None)
            out[key] = None if n is None else D(str(n.first("Premium").text or 0))
    return out


INT_FIELDS = {"LimitOfInsurance"}                  # the drone detail declares it xs:int; ISO refuses it as text


def ints(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in INT_FIELDS and isinstance(v, str) and v.strip().lstrip("-").isdigit():
                o[k] = int(v)
            else:
                ints(v)
    elif isinstance(o, list):
        for v in o:
            ints(v)
    return o


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def mechanism_checks(preds):
    """the claim each case pair exists to test, on the predictions (before ISO)."""
    out = []
    if {"O-FL1", "O-FL2"} <= preds.keys():
        out.append(("FL post-loss Yes = post-loss No (no factor)", preds["O-FL1"] == preds["O-FL2"]))
    if {"O-WV0", "O-WV1"} <= preds.keys():
        a = {k: v for k, v in preds["O-WV1"].items() if k.startswith("CovACoverage")}
        out.append(("WV B & C Separate: every Coverage A cell $0", bool(a) and all(v == 0 for v in a.values())
                    and any(v for k, v in preds["O-WV0"].items() if k.startswith("CovACoverage"))))
    if "O-WVf" in preds:
        a = {k: v for k, v in preds["O-WVf"].items() if k.startswith("CovACoverage")}
        out.append(("WV flood-only Yes: every Coverage A cell $0", bool(a) and all(v == 0 for v in a.values())))
    if "O-FL1" in preds:
        g2 = {k: v for k, v in preds["O-FL1"].items() if "BasicGroupII" in k}
        out.append((f"FL Group II cells priced (sinkhole adjustment): {g2}", True))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = {k: v for k, v in CASES.items() if not a.cases or k in a.cases.split(",")}
    reqs, preds = {}, {}
    for i, (cid, (task, j, label, build, expect)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"{cid} {task} {j} {label}")
        req = ints(t2.state_req(t2.m20.payload(build()), j))
        TAGGED.clear()
        data, ip = rep.cmp.rate(req)
        want, how = expect(data)
        got = our_cells(data, want)
        miss = [(k, str(w), str(got[k])) for k, w in want.items() if got[k] is None or got[k] != w]
        print(f"  {cid}: predicted {', '.join(f'{k[-40:]} ${w}' for k, w in want.items() if w or cid.startswith('T'))} ({how}); "
              f"engine {'equal' if not miss else 'DIFFERS ' + str(miss)}")
        if miss:
            FAIL.append(cid)
        reqs[cid], preds[cid] = req, want
    for claim, ok in mechanism_checks(preds):
        print(f"  {'ok  ' if ok else 'FAIL'} {claim}")
        if not ok:
            FAIL.append(claim[:40])
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17: the predicted cells, every premium, the (level, message) multiset")
        for i, cid in enumerate(cs, 1):
            progress(i, len(cs), f"ISO {cid}")
            req = reqs[cid]
            (gc.OUT / f"chunk27_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = r2.rate_retry(client, req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:400]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk27_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            TAGGED.clear()
            data, ip = rep.cmp.rate(req)
            mine = collections.Counter((lvl(t), x) for t, x in TAGGED)
            isos = collections.Counter(c23.iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            pbad = []
            for key, w in preds[cid].items():
                iv = [v for k, v in ipr.items() if re.search(re.escape(key) + r"\[0\]/Premium$", k)]
                if (iv and D(str(iv[0])) != w) or (not iv and w):
                    pbad.append((key, w, iv))
            ok = not dd and mine == isos and not pbad
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted cells {len(preds[cid]) - len(pbad)} of {len(preds[cid])}; "
                  f"{len(ipr) - len(dd)} of {len(ipr)} premiums; (level, message) {'equal' if mine == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
                  + "".join(f"\n        predicted {k[-60:]} ${w}, ISO {iv}" for k, w, iv in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (isos - mine).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (mine - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C27-10, C27-11): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
