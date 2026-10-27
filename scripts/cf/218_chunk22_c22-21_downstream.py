#!/usr/bin/env python3
"""Chunk 22, C22-21: what the multi-location forms feed downstream. Live ISO.

Unlike chunks 15-21, attaching either form REMOVES premium as well as adding it: the contents' ordinary premium
records switch off (CoverageOnPolicyIndicator 0 when a VR Form or Provisions row exists, RC-1). And the
contents' terrorism charge is built on TerrorismLimitToUse = the contents' LimitToUse (no sub-limit form), which the
VR Form sets to NewBusnFactor x SeasonalRiskFactor x Limit (0.75 x Limit): so terrorism MOVES under Value
Reporting and stays put under Additional Locations (LimitToUse = Limit). Predicted before running (2026-10-01):

  pairs (base -> with), Oregon, terrorism in effect (159_'s terror()), two locations 100,000 / 500,000:
    P1  -> VR "Not Used", incidental 10,000, acquired 60,000            P2  -> AL, full values 200,000 / 100,000
    P3 / P4  the clean tests: the same at 10 x every amount (1,000,000 / 5,000,000; incidental 100,000; acquired
             600,000; full values 2,000,000 / 1,000,000), each rise printed BEFORE its ISO call
  TOTAL      with - base = the chunk 22 premiums (215_'s hand model) - the contents' ordinary premiums switched off
             (the base's own, built and ISO-confirmed) + the contents' terrorism change (PP SetTerrorismPremium
             evaluated on the predicted TerrorismLimitToUse); every other premium identical base -> with
  TERRORISM  the contents' TerrorismLimitToUse = 0.75 x Limit under VR, = Limit under AL; no terrorism field on a
             chunk 22 record
  STAT CODES every stat value ISO returns on a chunk 22 record, strictly as text, on P1-P4 and on every stored
             chunk 22 response (--stored "chunk22_rc*")

    python scripts/cf/218_chunk22_c22-21_downstream.py [--live] [--stored "chunk22_rc*"]
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0_CLOCK = time.monotonic()

t3 = import_module("216_chunk22_rc3")
d15 = import_module("172_chunk15_c15-19_downstream")
t14 = import_module("159_chunk14_rc2_total")
m = t3.m
h, rc1, gc, rep, cmp, r11 = m.h, m.rc1, m.gc, m.rep, m.cmp, m.r11
r16 = m.r16
P, VR, AL, r = m.P, m.VR, m.AL, m.r
D = Decimal
OUT = gc.OUT
FAIL = []
CH22 = re.compile(rf"{VR}|{AL}")
ORDINARY = re.compile(r"PersonalPropertyPrsnlProp\w*Coverage")
STAT = re.compile(d15.STAT.pattern + r"|^Subline|Code$|ExcludedIndicator$")
PP_RULES = (m.r2.CW / "Rules" / f"{P}PersonalPropertyRules.Rule.xml").read_text(encoding="utf-8-sig")
TERR_BODY = re.search(r'<rul:Rule Name="SetTerrorismPremium".*?</rul:Rule>', PP_RULES, re.S).group(0)


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def T(**kw):
    return lambda: t14.terror(t3.tree(**kw))


X10 = dict(limits=("1000000", "5000000"))
PAIRS = {
    "P1": ("VR Not Used, incidental 10,000, acquired 60,000", T(), T(vr="Not Used", gi={"StockOnlyAcqrd": "60000"}), "VR"),
    "P2": ("AL, full values 200,000 / 100,000", T(), T(al=True, full=("200000", "100000")), "AL"),
    "P3": ("clean test: VR at 10 x", T(**X10), T(vr="Not Used", gi={"YourBusnPrsnlPropInc": "100000", "StockOnlyAcqrd": "600000"}, **X10), "VR"),
    "P4": ("clean test: AL at 10 x", T(**X10), T(al=True, full=("2000000", "1000000"), gi={"YourBusnPrsnlPropInc": "100000",
                                                                                         "OverallLimit": "3000000"}, **X10), "AL"),
}
RECS = t3.VR_ALL + t3.AL_ALL


def hand_ch22(data):
    total, bad = D(0), []
    for rec in RECS:
        if not rc1.find(data, P + rec):
            continue
        for hv, ev, e in m.predict(data, rec):
            if not (m.same(hv, e) and m.same(ev, e)):
                bad.append((rec, hv, ev, e))
            total += D(str(hv))
    return total, bad


CF100 = D(next(row["Factor"] for row in m.r4.rows("OR", "CoinsuranceFactor") if row["CoinsuranceValue"] == "100%"))


def terrorism(base, data, form):
    """each contents row's terrorism premium BY HAND (PP SetTerrorismPremium, the TRIA-disclosure branch):
    r0(r4(r4(r4(TerrorismLimitToUse / 100 x TRIAExclusionRate) x ProtectionClassFactor) x CoinsuranceFactor) x
    DeductibleFactorBasicGroupI), with two predicted inputs: TerrorismLimitToUse = the contents' LimitToUse (0.75 x Limit
    under VR, Limit under AL), and CoinsuranceFactor = the 100% row (PP SetCoinsuranceFactor: either form present ->
    LookupCoinsuranceFactor('100%'), whatever coinsurance is entered). The rest from the base, unchanged."""
    out, bad = D(0), []
    for pb, pp in zip(rc1.find(base, P + "PersonalProperty"), rc1.find(data, P + "PersonalProperty")):
        lim = D(m.val(pp, "Limit"))
        tl = r(m.NEWBUSN * lim, 0) if form == "VR" else lim
        for f, want in (("TerrorismLimitToUse", tl), ("CoinsuranceFactor", CF100)):
            got = m.val(pp, f)
            if got is None or D(got) != want:
                bad.append((f, want, got))
        x = r(tl / 100 * m.d(pb, "TRIAExclusionRate"), 4)
        x = r(x * m.d(pb, "ProtectionClassFactor"), 4)
        x = r(x * CF100, 4)
        hv = r(x * m.d(pb, "DeductibleFactorBasicGroupI"), 0)
        e = m.val(pp, "TerrorismPremium")
        if not m.same(hv, e):
            bad.append(("TerrorismPremium", hv, e))
        out += hv
    return out, bad


def prem(data):
    return rep.our_prem(data)


def predict_pair(cid):
    label, base_b, with_b, form = PAIRS[cid]
    b, _ = gc.run(base_b(), "OR")
    w, _ = gc.run(with_b(), "OR")
    pb, pw = prem(b), prem(w)
    ch22, bad1 = hand_ch22(w)
    switched = sum(D(str(v)) for k, v in pb.items() if ORDINARY.search(k) and not CH22.search(k))
    tb = sum(D(m.val(pp, "TerrorismPremium") or 0) for pp in rc1.find(b, P + "PersonalProperty"))
    tw, bad2 = terrorism(b, w, form)
    rise = ch22 - switched + (tw - tb)
    ordinary_on = [k for k, v in pw.items() if ORDINARY.search(k) and not m.same(v, 0)]
    # the policy's TRIA disclosure record carries the policy terrorism total: it must move by exactly the contents' change
    zz = [k for k in pb if "ZzDisclosure" in k and k.endswith("/Premium")]
    dzz = sum(D(str(pw.get(k) or 0)) - D(str(pb[k] or 0)) for k in zz)
    if dzz != tw - tb:
        bad2.append(("TRIA disclosure total moved", dzz, tw - tb))
    other = [k for k in pb if not CH22.search(k) and not ORDINARY.search(k) and "Total" not in k and k != f"{P}[0]/Premium"
             and "ErcCalculatedTotalPremium" not in k and not k.endswith("TerrorismPremium") and "TRIAPremium" not in k
             and "PostTRIACoverage" not in k and "TotPremiumCoverage" not in k and k not in zz and not m.same(pb[k], pw.get(k))]
    eng = D(str(pw[d15.TOTAL])) - D(str(pb[d15.TOTAL]))
    print(f"{cid} {label}:\n    chunk 22 premiums by hand {ch22} (hand = evaluator = engine on every record: {'yes' if not bad1 else bad1[:3]})"
          f"\n    ordinary contents premiums switched off {switched} (on in 'with': {ordinary_on[:3] or 'none'})"
          f"\n    contents terrorism {tb} -> {tw} by the PP rule on TerrorismLimitToUse {'= 0.75 x Limit' if form == 'VR' else '= Limit'}"
          f" ({'ok' if not bad2 else bad2[:3]})"
          f"\n    every other premium identical base -> with: {'yes' if not other else other[:4]}"
          f"\n    predicted rise {rise}; engine {eng}  {'ok' if eng == rise else 'DIFFERS'}")
    if bad1 or bad2 or ordinary_on or other or eng != rise:
        FAIL.append(cid)
    return rise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--stored", help="glob of stored chunk 22 responses to re-rate for stat codes")
    a = ap.parse_args()
    want = lambda rr: bool(CH22.search(rr))
    if not a.stored:
        preds = {}
        for i, cid in enumerate(PAIRS, 1):
            progress(i, len(PAIRS), f"predict {cid}")
            preds[cid] = predict_pair(cid)
        if a.live:
            import raas as raas_mod
            client = raas_mod.RaaS()
            print("\nISO live at 2026-09-17: each pair's base and with, every premium, chunk 22 stat values, messages, the total rise")
            for i, (cid, (label, base_b, with_b, form)) in enumerate(PAIRS.items(), 1):
                progress(i, len(PAIRS), f"ISO {cid} (predicted rise {preds[cid]})")
                resp = {}
                for tag, bld in (("base", base_b), ("with", with_b)):
                    req = r11.payload(bld())
                    (OUT / f"chunk22_c22-21_{cid}_{tag}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
                    try:
                        resp[tag] = client.rate(req)
                    except raas_mod.RaaSError as exc:
                        print(f"  {cid} {tag} ISO REFUSES {str(exc.body)[:200]}")
                        FAIL.append(f"{cid} {tag} live")
                        continue
                    (OUT / f"chunk22_c22-21_{cid}_{tag}_response.json").write_text(json.dumps(resp[tag], indent=2), encoding="utf-8")
                    data, ip = cmp.rate(req)
                    ipr, opr = rep.iso_prem(resp[tag]), rep.our_prem(data)
                    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
                    ist, ost = d15.iso_fields(resp[tag], want, STAT.search), d15.our_fields(data, want, STAT.search)
                    ds = [(k, v, ost.get(k)) for k, v in ist.items() if not d15.same(v, ost.get(k))]
                    on22 = [k for k, v in d15.iso_fields(resp[tag], want, d15.TERR.search).items() if not d15.blank(v)]
                    mi, mo = cmp.iso_messages(resp[tag]), set(ip.messages)
                    ok = not dd and not ds and not on22 and mi == mo
                    print(f"  {cid} {tag}: {'AGREE' if ok else 'DIFFER'} on {len(ipr)} premiums, {len(ist)} chunk 22 stat values, "
                          f"terrorism fields on chunk 22 records {len(on22)}, messages {'equal' if mi == mo else 'DIFFER'}; "
                          f"ISO total {d15.total_of(resp[tag]):,.0f}"
                          + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (dd + ds)[:5]))
                    if not ok:
                        FAIL.append(f"{cid} {tag} live")
                if len(resp) == 2:
                    rise = D(str(d15.total_of(resp["with"]))) - D(str(d15.total_of(resp["base"])))
                    print(f"  {cid} total rise at ISO {rise}; predicted before the call {preds[cid]}  {'ok' if rise == preds[cid] else 'DIFFERS'}")
                    if rise != preds[cid]:
                        FAIL.append(f"{cid} rise")
    if a.stored:
        stored = sorted(OUT.glob(a.stored + "_response.json"))
        print(f"\nSTAT CODES on chunk 22 records ({len(stored)} stored responses matching {a.stored}, strict text)")
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
            except Exception as exc:
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
        print(f"  {n} stored responses re-rated; {values} stat values on chunk 22 records, {len(fields)} field names:")
        for f, c in sorted(fields.items()):
            print(f"      {f}: {c}")
        print(f"  {'all equal' if not FAIL else 'DIFFERENCES above'}")
    mm, s = divmod(int(time.monotonic() - T0_CLOCK), 60)
    print(f"\nC22-21: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
