#!/usr/bin/env python3
"""Chunk 22, RC-4 (C22-17..C22-20): the state layer, the editions, all 46 states, scale and rounding.

Built on 216_ (its state-aware tree, its (level, message) capture and ISO comparison) and 215_'s hand model.
The five chunk tables are identical in all 46 states (checked here), so the hand model's constants hold
everywhere; what changes by state is the rule text, and every case below is predicted from it first.

C22-17  THE STATE LAYER
  T-AL1 / T-AL2  AL sets the VR wind / hail indicator from ITS OWN record (WindstormOrHailExclusionDirectDamagePrsnlProp):
                 'Yes' with AL's record, 'No' with the countrywide one.
  T-AR T-DC T-NY T-RI  the indicator is hard-set 'No' even with the exclusion record; AR / DC look the peril stat code
                 up in their own tables (rows for 'No' only).
  T-CA1 / T-CA2  CA's CP 10 43 (Limited Earthquake, lessors' risk) at a sub-limit, with CP 13 10 / CP 13 20.
  T-CAB          CA rewrites Blanket Rating Detail: VR rows 1-2 blanketed, row 3 own rate (215_'s B1 in CA).
C22-18  THE EDITIONS (every-rule diff, 2026-10-01: MO 2023 V02 29 family rules + 16 parent rules; CA / NC V03 4 + 13;
        V04 0 + 3 in the main ruleset's roll-up)
  E1  MO, VR "Not Used" + incidental + acquired 60,000 (V02's Not Used formulas equal 2026's)
  E2  MO, VR "Used": V02 still calls the self-referencing maxLimit rule -> refused at ISO and ours (OI-119)
  E3  MO, VR rows 1-2 in a Monthly Reporting blanket with the CONTENTS at 90%: V02's attach rule reads BlktCoinsuranceValue,
      2026's BlktCoinsurance
  E4  MO, VR + wind exclusion: V02's indicator rule (GetList / Break) -> 'Yes'
  E5  MO, VR, terrorism sub-limit over the contents limit: V02 says "Sub Limit cannot exceed the coverage's limit"
  E6  MO, AL, terrorism sub-limit over the Provisions full value: the same V02 text from its AL rule
  E5b OR, the same as E5: 2026 says "Terrorism Sub Limit cannot exceed the coverage's limit"
  E7  NC (V03), VR + wind exclusion + terrorism sub-limit
  E8 / E9  IL (V04), VR / AL
C22-19  ALL 46 STATES: each state's own package, both forms on one policy (contents on Monthly Reporting; the mutual
        exclusion and coinsurance messages fire and are compared), VR incidental + acquired 60,000. Run in batches.
C22-20  SCALE AND ROUNDING: SC1 AL on 8 locations of mixed limits, full values chosen by a search so that rounding each
        full value x rate (the rule) and rounding only the average give DIFFERENT Group I MLARs; SC2 VR "Not Used" on the
        same 8 locations.

    python scripts/cf/217_chunk22_rc4.py [--live] [--cases T-AL1,E1] [--states AL,AK,...]
"""
from __future__ import annotations

import argparse
import collections
import itertools
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

t3 = import_module("216_chunk22_rc3")
m, h, r2, rc1, gc, rep, r11 = t3.m, t3.h, t3.r2, t3.rc1, t3.gc, t3.rep, t3.r11
r4 = m.r4
s18 = import_module("164_chunk14_c14-18_all_states")
P, VR, AL, r, same = m.P, m.VR, m.AL, m.r, m.same
tree, each, with_, put0 = t3.tree, t3.each, t3.with_, t3.put0
r11.NUMERIC |= {"TerrorismSubLimit"}
FAIL = []
CA_LEQ = "CauseOfLossLimitedEarthquakeEndorsementCaliforniaResidentialPropertyLessorsRiskPrsnlProp"
WIND_CW = "WindstormOrHailExclusionPrsnlProp"
WIND_AL = "WindstormOrHailExclusionDirectDamagePrsnlProp"
SUBLIMIT = "Sub Limit cannot exceed the coverage's limit"
TERR = "Terrorism Sub Limit cannot exceed the coverage's limit"
EXPECT_REFUSAL = {"E2": "maxLimit"}
#: VR Form rows predicted to survive: MO V02 removes the form (its attach test reads BlktCoinsuranceValue before V02's
#: InitializeValueReportingForm has set it: 2026 runs SetBlanketValues first, V02 dropped that call); 2026 keeps the 2 blanketed rows
EXPECT_ROWS = {"E3": 0, "E3b": 2}     # E3b row 3 is unblanketed at 90%: removed in 2026 too
L8 = ("100000", "150000", "200000", "250000", "300000", "350000", "400000", "450000")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def lvl(t):
    """our TableName vs ISO's node name: the V02 / 2026 sub-limit messages pass a bare 'PersonalProperty'."""
    return t if t.startswith(P) or t in ("?",) else P + t


# ---------------------------------------------------------------- trees

def no_eq(o):
    """208_'s Florida recipe: drop every earthquake input (the portable policy's EQ class "A1" is not one FL files;
    ISO refuses at BldgHeightFactor, ours rates: OI-103). The chunk 22 records read no earthquake here."""
    if isinstance(o, dict):
        for k in [k for k in o if k.startswith("EQ")]:
            del o[k]
        for v in o.values():
            no_eq(v)
    elif isinstance(o, list):
        for v in o:
            no_eq(v)
    return o


def both_forms(j):
    def b():
        sub = tree(j=j, vr="Not Used", al=True, full=("200000", "100000"), gi={"StockOnlyAcqrd": "60000"})
        sub = each(sub, "PersonalProperty", Coinsurance="Monthly Reporting")
        if j == "FL":
            no_eq(sub)
            for loc in h.locations(sub):
                loc[P + "SpecialClassTable"][P + "SpecialClass"][0]["ClassDescription"] = r4.FL_SC
        return sub
    return b


def ca_leq(form):
    def pre(sub):
        rc1.node_dicts(sub)[P + "Location"]["EQCauseOfLossForm"] = "Limited Earthquake Endorsement (CP 10 43)"
        r2.put(sub, CA_LEQ, {"Limit": "50000"}, state="CA")
    return pre


def blanket_contents_90(sub):
    t3.blanket("Monthly Reporting")(sub)
    each(sub, "PersonalProperty", Coinsurance="90%")


def put_s(j, rec, fields=None):
    """place a record with the STATE's schema (AL's own wind record is not in the CW XSD)."""
    return lambda sub: r2.put(sub, rec, dict(fields or {}), state=j)


def terr(level, value):
    return lambda sub: each(sub, level, TerrorismSubLimit=value)


# ---------------------------------------------------------------- C22-20: the full values, found by search

def rounding_search():
    """8 locations at L8; full values >= each limit chosen so that Group I's AL MLAR differs between rounding each
    full value x rate (the rule) and rounding the average only. Returns (full values, rule MLAR, alt MLAR)."""
    data = h.rated(tree(al=True, limits=L8, full=L8))[0]
    pps = rc1.find(data, P + "PersonalProperty")
    rates = [m.d(pp, "FinalBasicGroupIRate") for pp in pps]
    cp = rc1.find(data, P)[0]
    inc = Decimal(10000)
    inc_part = r(r(m.INC_RATE["Basic"] * m.d(cp, "LossCostMultiplier"), 3) * inc / 100, 0)
    picks = []
    for lim, rate in zip(L8[:7], rates[:7]):                # 7 rows whose full value x rate rounds DOWN by ~0.45
        picks.append(next(fv for fv in range(int(lim), int(lim) + 4000) if Decimal("0.40") <= (fv * rate) % 1 < Decimal("0.5")))
    for fv8 in range(int(L8[7]), int(L8[7]) + 200000):      # scan the 8th: every step moves the average a little
        combo = picks + [fv8]
        den = inc + sum(combo)
        rule = r((sum(r(fv * rt, 0) for fv, rt in zip(combo, rates)) + inc_part) / den, 3)
        alt = r((sum(fv * rt for fv, rt in zip(combo, rates)) + inc_part) / den, 3)
        if rule != alt:
            return tuple(str(fv) for fv in combo), rule, alt, rates
    return None, None, None, rates


SEARCH = {}


def sc1():
    full = SEARCH["full"]
    return tree(al=True, limits=L8, full=full, gi={"OverallLimit": str(sum(int(x) for x in full))})


# ---------------------------------------------------------------- cases

def cases(states=None):
    vr = dict(vr="Not Used")
    al = dict(al=True, full=("200000", "100000"))
    no_ = []
    cs = {
        "T-AL1": ("C22-17", "AL", "VR + AL's own wind / hail exclusion record", T(j="AL", pre=put_s("AL", WIND_AL), **vr), m.VR_RECS, no_, no_, "Yes"),
        "T-AL2": ("C22-17", "AL", "VR + the countrywide wind / hail record (AL reads its own)", T(j="AL", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "No"),
        "T-AR": ("C22-17", "AR", "VR + wind / hail exclusion (indicator hard-set 'No')", T(j="AR", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "No"),
        "T-DC": ("C22-17", "DC", "VR + wind / hail exclusion (indicator hard-set 'No')", T(j="DC", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "No"),
        "T-NY": ("C22-17", "NY", "VR + wind / hail exclusion (indicator hard-set 'No')", T(j="NY", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "No"),
        "T-RI": ("C22-17", "RI", "VR + wind / hail exclusion (indicator hard-set 'No')", T(j="RI", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "No"),
        "T-CA1": ("C22-17", "CA", "CA CP 10 43 at a 50,000 sub-limit with CP 13 10", T(j="CA", eq=True, pre=ca_leq("vr"), **vr), [],
                  [("PP", "CP 10 43 not valid with CP 13 10 when sub-limit is used")] * 2, no_, None),
        "T-CA2": ("C22-17", "CA", "CA CP 10 43 at a 50,000 sub-limit with CP 13 20", T(j="CA", eq=True, pre=ca_leq("al"), **al), [],
                  [("PP", "CP 10 43 not valid with CP 13 20 when sub-limit is used")] * 2, no_, None),
        "T-CAB": ("C22-17", "CA", "CA: VR rows 1-2 blanketed, row 3 own rate", with_(T(j="CA", limits=("100000", "500000", "200000"), **vr),
                                                                                    t3.blanket("Monthly Reporting")), m.VR_RECS, no_, no_, None),
        "E1": ("C22-18", "MO", "MO V02: VR Not Used + incidental + acquired 60,000", T(j="MO", gi={"StockOnlyAcqrd": "60000"}, **vr),
               t3.VR_ALL, no_, no_, None),
        "E2": ("C22-18", "MO", "MO V02: VR Used (OI-119 in V02 too)", T(j="MO", vr="Used"), [], no_, no_, None),
        "E3": ("C22-18", "MO", "MO V02: VR rows 1-2 in a Monthly Reporting blanket, contents at 90%",
               with_(T(j="MO", limits=("100000", "500000", "200000"), **vr), blanket_contents_90), [], no_, no_, None),
        "E3b": ("C22-18", "OR", "2026: the same as E3", with_(T(limits=("100000", "500000", "200000"), **vr), blanket_contents_90),
                m.VR_RECS, no_, no_, None),
        "E4": ("C22-18", "MO", "MO V02: VR + wind / hail exclusion (Break variant)", T(j="MO", pre=put0(WIND_CW), **vr), m.VR_RECS, no_, no_, "Yes"),
        "E5": ("C22-18", "MO", "MO V02: VR, terrorism sub-limit 150,000 over the contents limit",
               with_(T(j="MO", limits=("100000", "100000"), **vr), terr("PersonalProperty", "150000")), [],
               [("PPb", SUBLIMIT)] * 2, [("PPb", TERR)], None),
        "E5b": ("C22-18", "OR", "2026: the same as E5", with_(T(limits=("100000", "100000"), **vr), terr("PersonalProperty", "150000")), [],
                [("PPb", TERR)] * 2, no_, None),     # SUBLIMIT is a substring of TERR: no forbid
        "E6": ("C22-18", "MO", "MO V02: AL, terrorism sub-limit 250,000 over the Provisions full value",
               with_(T(j="MO", **al), terr("PersonalProperty", "250000")), [], [("PPb", SUBLIMIT)] * 2, [("PPb", TERR)], None),
        "E7": ("C22-18", "NC", "NC V03: VR + wind exclusion + terrorism sub-limit 150,000",
               with_(T(j="NC", limits=("100000", "100000"), pre=put0(WIND_CW), **vr), terr("PersonalProperty", "150000")), m.VR_RECS,
               [("PPb", SUBLIMIT)] * 2, [("PPb", TERR)], "Yes"),
        "E8": ("C22-18", "IL", "IL V04: VR Not Used + acquired 60,000", T(j="IL", gi={"StockOnlyAcqrd": "60000"}, **vr), t3.VR_ALL, no_, no_, None),
        "E9": ("C22-18", "IL", "IL V04: AL", T(j="IL", **al), t3.AL_ALL, no_, no_, None),
        "SC1": ("C22-20", "OR", "AL on 8 locations, full values from the rounding search", sc1, t3.AL_ALL, no_, no_, None),
        "SC2": ("C22-20", "OR", "VR Not Used on the same 8 locations", T(limits=L8, **vr), t3.VR_ALL, no_, no_, None),
    }
    for j in (states or s18.STATES):
        cs[f"S-{j}"] = ("C22-19", j, f"{j}: both forms, two locations", both_forms(j), t3.VR_ALL + t3.AL_ALL,
                        [("PP", "CP 13 10 and CP 13 20 are not valid together")] * 2, no_, None)
    return cs


def T(**kw):
    return lambda: tree(**kw)


t3.L["PPb"] = P + "PersonalProperty"


# ---------------------------------------------------------------- stat code (C22-17 / 18)

def stat_check(data, j, want_wind):
    """the VR GI's wind indicator as predicted, and its peril stat code looked up by hand in the state's own table."""
    g = rc1.find(data, P + VR + "GeneralInformation")[0]
    ind = {k: m.val(g, k) for k in ("VandalismExcludedIndicator", "SprinklerLeakageExcludedIndicator",
                                    "WindstormOrHailExcludedIndicator", "TheftExcludedIndicator")}
    special = m.val(g, "CauseOfLoss") == "Special"
    tab = "PerilExclusionIndicatorBasicAndSpecialStatCode" if special else "PerilExclusionIndicatorBasicAndBroadStatCode"
    rows = r4.rows(j, tab)
    want = [ind["VandalismExcludedIndicator"], ind["SprinklerLeakageExcludedIndicator"], want_wind] + \
           ([ind["TheftExcludedIndicator"]] if special else [])
    code = next((row["Code"] for row in rows if [row["VandalismExcluded"], row["SprinklerLeakageExcluded"], row["WindHailExcluded"]]
                 + ([row["TheftExcluded"]] if special else []) == want), None)
    got = {"WindstormOrHailExcludedIndicator": ind["WindstormOrHailExcludedIndicator"], "PerilExclusionIndicatorStatCode": m.val(g, "PerilExclusionIndicatorStatCode")}
    pred = {"WindstormOrHailExcludedIndicator": want_wind, "PerilExclusionIndicatorStatCode": code}
    return pred, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    ap.add_argument("--states", help="C22-19 states for this process (batches); default all 46")
    a = ap.parse_args()
    for t_ in ("ValRptgIncLocsRate", "ValRptgAcqrdLocsRate", "NewBusnFactor", "SeasonalRiskFactor", "AddlLocSpclCoinsFactor"):
        vals = {str([tuple(x.values())[1:] for x in r4.rows(j, t_)]) for j in s18.STATES}
        if len(vals) != 1:
            print(f"  [FAIL] {t_} differs by state: the hand model's OR constants do not hold everywhere")
            FAIL.append(t_)
    states = a.states.split(",") if a.states else None
    cs = cases(states)
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    elif a.states:
        cs = {k: v for k, v in cs.items() if k.startswith("S-")}
    if "SC1" in cs:
        full, rule, alt, rates = rounding_search()
        if full is None:
            print("  [FAIL] no rounding-discriminating set of full values found")
            FAIL.append("SC1 search")
            cs.pop("SC1")
        else:
            SEARCH["full"] = full
            print(f"C22-20 search: Group I rates {[str(x) for x in rates]}; full values {full}: Group I MLAR {rule} rounding each "
                  f"term (the rule) vs {alt} rounding the average only")
    preds, stats = {}, {}
    for i, (cid, (task, j, label, build, recs, must, mustnt, wind)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        t3.TAGGED.clear()
        try:
            data, ip = gc.run(build(), j)
        except Exception as exc:
            ok = cid in EXPECT_REFUSAL and EXPECT_REFUSAL[cid] in str(exc)
            print(f"{cid:6s} {task} {j} {label}: engine REFUSES{' as predicted' if ok else ''}: {str(exc)[:140]}")
            if not ok:
                FAIL.append(cid)
            continue
        if cid in EXPECT_REFUSAL:
            print(f"{cid:6s} {task} {j} {label}: engine RATES, refusal predicted")
            FAIL.append(cid)
            continue
        tagged = [(lvl(t), x) for t, x in t3.TAGGED]
        preds[cid], lines, bad = t3.predictions(data, {rec: None for rec in recs})
        mbad = t3.check_msgs(tagged, must, mustnt)
        if wind is not None:
            pred, got = stat_check(data, j, wind)
            stats[cid] = (pred, got)
            if pred != got:
                bad.append("stat")
            lines.append(f"      {'ok  ' if pred == got else 'FAIL'} VR GI wind indicator / peril stat code predicted {pred} engine {got}")
        if cid in EXPECT_ROWS:
            n_rows = len(rc1.find(data, P + VR))
            okr = n_rows == EXPECT_ROWS[cid]
            lines.append(f"      {'ok  ' if okr else 'FAIL'} VR Form rows {n_rows} (predicted {EXPECT_ROWS[cid]})")
            if not okr:
                bad.append("rows")
        if cid == "SC1":
            g = rc1.find(data, P + AL + "GeneralInformation")[0]
            lines.append(f"      AL GI Group I MLAR engine {m.val(g, 'BasicGroupIMLAR')} (rule {m.al_mlars(g, rc1.find(data, P)[0])[0]['BasicGroupI']})")
        print(f"{cid:6s} {task} {j} {label}: {'as predicted' if not bad and not mbad else 'DIFFERS'} "
              f"({len(recs)} records; messages {len(must)} required, {len(mustnt)} forbidden{': ' + '; '.join(mbad) if mbad else ', ok'})")
        if lines and (bad or mbad or not cid.startswith("S-")):
            print("\n".join(lines))
        if bad or mbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium, the (level, message) multiset):")
        for i, (cid, (task, j, label, build, recs, must, mustnt, wind)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = t3.state_req(r11.payload(build()), j)
            (gc.OUT / f"chunk22_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm_ = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,240})', str(exc.body))
                what = mm_.group(0)[:260] if mm_ else str(exc.body)[:260]
                if cid in EXPECT_REFUSAL and EXPECT_REFUSAL[cid] in what:
                    print(f"  {cid:6s} REFUSES AS PREDICTED (OI-119; ours refuses too): {what[:150]}")
                    continue
                print(f"  {cid:6s} ISO REFUSES {what}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk22_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            if cid in EXPECT_REFUSAL:
                print(f"  {cid:6s} ISO PRICES where a refusal was predicted")
                FAIL.append(f"{cid} live")
                continue
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            t3.TAGGED.clear()
            data, ip = rep.cmp.rate(req)
            ours = collections.Counter((lvl(t), x) for t, x in t3.TAGGED)
            isos = collections.Counter((lvl(t), x) for t, x in t3.iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mreq = t3.check_msgs(list(isos.elements()), must, mustnt)
            extra = ""
            if cid in stats:
                pred = stats[cid][0]
                iso_s = {f: (m.iso_field(resp, VR + "GeneralInformation", f) or [None])[0] for f in pred}
                extra = f"; stat ISO {iso_s}"
                if any(iso_s[f] is not None and str(iso_s[f]) != str(pred[f]) for f in pred):
                    pbad.append(("stat", iso_s, pred))
            ok = not pbad and not d and ours == isos and not mreq
            print(f"  {cid:6s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} "
                  f"({sum(isos.values())} ISO){extra}"
                  + (f"; against the prediction: {mreq}" if mreq else "")
                  + "".join(f"\n        predicted {m.short(str(rr))[:60]}: ISO {x}, derived {w}" for rr, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (isos - ours).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:100]} x{n}" for (t, x), n in (ours - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C22-17..C22-20): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
