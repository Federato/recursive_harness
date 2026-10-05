"""Chunk 13, RC-3 (C13-10 to C13-15): how the terrorism premium behaves, derived by hand first.

All cases use chunk 2's Oregon building (limit 100,000; PC 0.96, coinsurance
0.95, deductible 0.98) at EffDate 2026-09-17. Premium arithmetic, per the rules:
  round0( round4( round4( round4( Limit/100 x rate [x proration] ) x .96 ) x .95 ) x .98 ), half-up.

C13-10  THE TRIA TIMELINE (Multnomah, tier 1: program year 3 = 0.009, full = 0.01;
        certified acts covered; conditional exclusion "No Exclusion" -> post rate 0.01)
  T2 expires on the effective date      days 0   yr3 0 full 1   Pre 0, Post 10->9.6->9.12->8.94 $9
  T3 expires the next day               days 1   1/365 rounds to 0.00, and 0.00 means
                                        "expired": full 1.0 -> same as T2           $9
  T4 expires in 364 days                364/365 rounds to 1.00 -> full 0 -> Pre 9->8.64->8.208->8.04 $8
  T5 expires in 365 days                ">= 365" branch -> 1.0 / 0                  $8
  T6 "will expire", no expiry date      the days rule needs the date: 0 -> as T2    $9
  T7 "expired, use conditional forms"   days 0 -> Pre 0, Post at the full rate      $9
  T9 expiry date already past (2025)    negative days -> 0 -> as T2                 $9

C13-11  THE FIVE FORM FAMILIES (Remainder of State, tier 3, policy LCM 100: loss cost
        0.1 both years; Oregon fire exception 0.4, nuclear/biological/chemical 0.5)
  in effect:     IL 09 52 cap 1.0 -> 0.1: 100->96->91.2->89.376 $89
                 IL 09 53 fire 0.4 -> 0.04: 40->38.4->36.48->35.75 $36   (CW rule: $0)
                 IL 09 86 NBC 0.5 -> 0.05: 50->48->45.6->44.69 $45
                 IL 09 87 sub-limit 30,000: pct 30 -> factor 3.05+(5/25)(1.63-3.05) = 2.766
                          -> rate 0.2766 on 30,000: 82.98->79.6608->75.6778->74.16 $74
  conditional (expiring 2027-06-01, 0.70/0.30; pre rate 0.1 x cap 1.0):
                 Pre 1000x.1x.7 = 70->67.2->63.84->62.56 $63 (IL 09 95/96, "none")
                 IL 09 95 fire  post 1000x.04x.3 = 12->11.52->10.944->10.73 $11   total $74
                 IL 09 96 NBC   post 1000x.05x.3 = 15->14.4->13.68->13.41 $13     total $76
                 IL 09 97 sub-limit 30,000 applies to BOTH halves:
                          pre 300x.1x.7 = 21->20.16->19.152->18.77 $19
                          post 300x.2766x.3 = 24.894->23.8982->22.7033->22.25 $22 total $41
                 no exclusion post 1000x.1x.3 = 30->28.8->27.36->26.81 $27      total $90
  post-TRIA:     IL 00 30 fire .04 $36 ; IL 00 31 NBC .05 $45 ; IL 00 32 sub-limit $74 ;
                 "No Exclusion" .1 $89  (the PostTRIA roll-up carries the same figure)

C13-12  THE SUB-LIMIT (in effect, IL 09 87, tier 3, LCM 100)
  S5    5,000 = 5%   -> factor 12.6 (band start) -> rate 1.26 on 5,000: 63->60.48->57.456->56.31 $56
  S4    4,000 = 4%   -> below 5: factor 0 -> $0
  S100  100,000 = 100% -> factor 1.0 -> $89 (same as the cap)
  S120  120,000 = 120% -> SetTerrorismSublimitFactor applies the table only for 5 <= pct <= 100,
        so above 100 the factor is 0 and terrorism prices at $0. (First prediction said $107 from
        the table's [100, max) band; that band is reachable only at exactly 100. The engine was right.)
  S33   33,333: pct = 33333x100/100000 = 33.333 rounds to 33 -> factor 3.05-(8/25)(1.42) = 2.5956
        -> 2.596 -> rate 0.2596 on 333.33: 86.5325->83.0712->78.9176->77.34 $77
  S0    no sub-limit entered -> pct 0 -> factor 0 -> $0

C13-13  ZERO CASES (Multnomah, LCM 1, as the golden case unless stated)
  Z1 TRIAType blank                -> no form attaches -> $0, no disclosure record
  Z2 in effect, certified-acts answer blank -> disclosure attaches, no IL 09 form -> rate 0 -> $0
  Z3 no terrorism territory        -> tier 0 -> loss cost 0 -> $0
  Z4 a territory Oregon doesn't file ("Lane County") -> no tier -> $0 here (ISO may refuse: OI-103)
  Z5 TerrorismIndicator "No", TRIA in effect -> still $8 (the indicator switches nothing off)
  Z7 post-TRIA, exclusion answer blank -> no IL 00 form, PostTRIA off -> $0
  Z8 (engine only) no EffDate, TRIA expiring -> our engine refuses, first at DateAdd (ExpDate =
     EffDate + 1 year), before the days rule is reached. ISO always has EffectiveDateTime.

C13-14  THE OVERRIDE (on the building)
  O1 override Yes, premium 500, in effect  -> TerrorismPremium 500, disclosure 500
  O2 override Yes, 500, expiring           -> Pre 500x.7 = 350, Post 500x.3 = 150, total 500
  O3 override Yes, no premium entered      -> nothing copied -> $0 on the disclosure
  O4 override "No" with 500 entered        -> ignored -> $8

C13-15  LITERALS: every constant a terrorism rule compares against, checked against the
        Domain Tables (static; see literals()).

    python scripts/cf/151_chunk13_rc3_mechanisms.py            # engine
    python scripts/cf/151_chunk13_rc3_mechanisms.py --live     # + ISO live
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import book_for
from gl_engine.interp.values import InterpretError
import _iso_refusals as _iso                                    # noqa: E402

gc = import_module("149_chunk13_golden_case")
r11, rp = gc.r11, gc.rp
# ISO types these as JSON numbers and refuses a string ("Error reading view element"),
# found by the first live run; chunk 12 met the same for its own limits (132_).
r11.NUMERIC |= {"TerrorismSubLimit", "TerrorOverridePremium"}
POL, LOC, STRUCT = gc.POL, gc.LOC, gc.STRUCT
IN_EFFECT, WILL_EXPIRE = gc.IN_EFFECT, gc.WILL_EXPIRE
POST = "Has Already Expired, Use Post-TRIA Forms"
COND = "Has Expired but Use Conditional Forms"
P = "CommercialProperty"
DT = f"{POL}/{gc.DISC_TRIA}Table/{gc.DISC_TRIA}/Premium"
DE = f"{POL}/{gc.DISC_EST}Table/{gc.DISC_EST}/Premium"
PT = f"{POL}/{P}PostTRIACoverage/Premium"
T, PRE, POSTP = f"{STRUCT}/TerrorismPremium", f"{STRUCT}/PreTRIAPremium", f"{STRUCT}/PostTRIAPremium"
TIER3 = "Remainder of State"


def sub(tria=IN_EFFECT, cert="Yes", cond=None, post=None, exp=None, lcm=None, territory="Multnomah County",
        sublimit=None, indicator="Yes", override=None, override_prem=None, drop=(), effdate=True):
    s = r11.at_date(gc.g2.submission())
    cp = s["CommercialPropertyTable"]["CommercialProperty"][0]
    for k, v in {"TerrorismIndicator": indicator, "TRIAType": tria, "CoverageForCertifiedActs": cert,
                 "TRIAConditionalExclusion": cond, "PostTRIAExclusion": post, "TRIAExpirationDate": exp,
                 "LossCostMultiplier": None if lcm is None else str(lcm)}.items():
        if v is not None and v != "":
            cp[k] = v
    if tria in (WILL_EXPIRE, COND):
        cp["ConditionalExclusionRatingOption"] = gc.ENTIRE
        cp.setdefault("TRIAConditionalExclusion", "No Exclusion")
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    if territory:
        loc["TerrorismTerritory"] = territory
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    if sublimit is not None:
        st["TerrorismSubLimit"] = str(sublimit)
    if override is not None:
        st["TerrorismOverride"] = override
    if override_prem is not None:
        st["TerrorOverridePremium"] = str(override_prem)
    for k in drop:
        cp.pop(k, None)
    if not effdate:
        s.pop("EffDate", None)
        s.pop("ExpDate", None)
    return s


# id -> (task, label, kwargs, expected {path: value or None for 'absent/null/0'}, live?)
CASES = [
    # C13-10
    ("T2", "C13-10", "expires on the effective date", dict(tria=WILL_EXPIRE, exp="09/17/2026"),
     {f"{POL}/DaysUntilTRIAExpiration": 0, PRE: 0, POSTP: 9, T: 9, DE: 9}, True),
    ("T3", "C13-10", "expires the next day: 1/365 -> 0.00 -> treated as expired", dict(tria=WILL_EXPIRE, exp="09/18/2026"),
     {f"{POL}/DaysUntilTRIAExpiration": 1, f"{POL}/TerrorismProratingProgYr3Factor": 0,
      f"{POL}/TerrorismProratingFullFactor": 1, PRE: 0, POSTP: 9, T: 9}, True),
    ("T4", "C13-10", "expires in 364 days: 364/365 -> 1.00", dict(tria=WILL_EXPIRE, exp="09/16/2027"),
     {f"{POL}/DaysUntilTRIAExpiration": 364, f"{POL}/TerrorismProratingProgYr3Factor": 1,
      f"{POL}/TerrorismProratingFullFactor": 0, PRE: 8, POSTP: 0, T: 8}, True),
    ("T5", "C13-10", "expires in 365 days", dict(tria=WILL_EXPIRE, exp="09/17/2027"),
     {f"{POL}/DaysUntilTRIAExpiration": 365, PRE: 8, POSTP: 0, T: 8}, True),
    ("T6", "C13-10", "'will expire' with no expiry date", dict(tria=WILL_EXPIRE),
     {f"{POL}/DaysUntilTRIAExpiration": 0, PRE: 0, POSTP: 9, T: 9}, True),
    ("T7", "C13-10", "expired, use conditional forms", dict(tria=COND),
     {f"{POL}/DaysUntilTRIAExpiration": 0, PRE: 0, POSTP: 9, T: 9, DE: 9}, True),
    ("T9", "C13-10", "expiry date already past (2025-01-01)", dict(tria=WILL_EXPIRE, exp="01/01/2025"),
     {PRE: 0, POSTP: 9, T: 9}, True),
    # C13-11
    ("F52", "C13-11", "in effect, IL 09 52 cap", dict(territory=TIER3, lcm=100), {T: 89, DT: 89}, True),
    ("F53", "C13-11", "in effect, IL 09 53 fire exception 0.4 (CW: $0)", dict(territory=TIER3, lcm=100, cert="No"),
     {f"{STRUCT}/TRIAExclFactor": "0.4", T: 36}, True),
    ("F86", "C13-11", "in effect, IL 09 86 NBC 0.5",
     dict(territory=TIER3, lcm=100, cert="Yes, but Excludes Nuclear, Biological and Chemical Acts"),
     {f"{STRUCT}/TRIAExclFactor": "0.5", T: 45}, True),
    ("F87", "C13-11", "in effect, IL 09 87 sub-limit 30,000",
     dict(territory=TIER3, lcm=100, cert="Yes, Subject to Sub-Limit", sublimit=30000),
     {f"{STRUCT}/TerrorismSubLimitPct": 30, f"{STRUCT}/TerrorismSubLimitFactor": "2.766",
      f"{STRUCT}/TerrorismLimitToUse": 30000, T: 74}, True),
    ("C95", "C13-11", "conditional IL 09 95 fire", dict(territory=TIER3, lcm=100, tria=WILL_EXPIRE, exp="06/01/2027",
                                                          cond="Exclude"),
     {PRE: 63, POSTP: 11, T: 74}, True),
    ("C96", "C13-11", "conditional IL 09 96 NBC", dict(territory=TIER3, lcm=100, tria=WILL_EXPIRE, exp="06/01/2027",
                                                        cond="Exclude Nuclear, Biological and Chemical Acts"),
     {PRE: 63, POSTP: 13, T: 76}, True),
    ("C97", "C13-11", "conditional IL 09 97 sub-limit 30,000 (both halves)",
     dict(territory=TIER3, lcm=100, tria=WILL_EXPIRE, exp="06/01/2027", cond="Cover Subject to Sub-Limit",
          sublimit=30000),
     {PRE: 19, POSTP: 22, T: 41}, True),
    ("CNo", "C13-11", "conditional, no exclusion", dict(territory=TIER3, lcm=100, tria=WILL_EXPIRE, exp="06/01/2027"),
     {PRE: 63, POSTP: 27, T: 90}, True),
    ("P30", "C13-11", "post-TRIA IL 00 30 fire", dict(territory=TIER3, lcm=100, tria=POST, post="Exclude"),
     {T: 36, PT: 36}, True),
    ("P31", "C13-11", "post-TRIA IL 00 31 NBC",
     dict(territory=TIER3, lcm=100, tria=POST, post="Exclude Nuclear, Biological and Chemical Acts"),
     {T: 45, PT: 45}, True),
    ("P32", "C13-11", "post-TRIA IL 00 32 sub-limit 30,000",
     dict(territory=TIER3, lcm=100, tria=POST, post="Cover Subject to Sub-Limit", sublimit=30000),
     {T: 74, PT: 74}, True),
    ("PNo", "C13-11", "post-TRIA, no exclusion", dict(territory=TIER3, lcm=100, tria=POST, post="No Exclusion"),
     {T: 89, PT: 89}, True),
    # C13-12
    ("S5", "C13-12", "sub-limit 5,000 (5%)", dict(territory=TIER3, lcm=100, cert="Yes, Subject to Sub-Limit", sublimit=5000),
     {f"{STRUCT}/TerrorismSubLimitFactor": "12.6", T: 56}, True),
    ("S4", "C13-12", "sub-limit 4,000 (4%, below 5)", dict(territory=TIER3, lcm=100, cert="Yes, Subject to Sub-Limit",
                                                            sublimit=4000),
     {f"{STRUCT}/TerrorismSubLimitFactor": 0, T: 0}, True),
    ("S100", "C13-12", "sub-limit 100,000 (100%)", dict(territory=TIER3, lcm=100, cert="Yes, Subject to Sub-Limit",
                                                        sublimit=100000),
     {f"{STRUCT}/TerrorismSubLimitFactor": 1, T: 89}, True),
    ("S120", "C13-12", "sub-limit 120,000 (above the limit)", dict(territory=TIER3, lcm=100,
                                                                   cert="Yes, Subject to Sub-Limit", sublimit=120000),
     {f"{STRUCT}/TerrorismSubLimitFactor": 0, T: 0}, True),
    ("S33", "C13-12", "sub-limit 33,333 (33.3% -> 33)", dict(territory=TIER3, lcm=100,
                                                            cert="Yes, Subject to Sub-Limit", sublimit=33333),
     {f"{STRUCT}/TerrorismSubLimitPct": 33, f"{STRUCT}/TerrorismSubLimitFactor": "2.596", T: 77}, True),
    ("S0", "C13-12", "sub-limit form, no sub-limit entered", dict(territory=TIER3, lcm=100,
                                                                  cert="Yes, Subject to Sub-Limit"),
     {f"{STRUCT}/TerrorismSubLimitFactor": 0, T: 0}, True),
    # C13-13
    ("Z1", "C13-13", "TRIAType blank", dict(tria=""), {T: 0, DT: None}, True),
    ("Z2", "C13-13", "in effect, certified-acts answer blank", dict(cert=""), {f"{STRUCT}/TRIAExclusionRate": 0, T: 0, DT: 0},
     True),
    ("Z3", "C13-13", "no terrorism territory", dict(territory=""), {f"{LOC}/TerrorismTerritoryTier": 0, T: 0}, True),
    ("Z4", "C13-13", "territory Oregon doesn't file", dict(territory="Lane County"), {T: 0}, True),
    ("Z5", "C13-13", "TerrorismIndicator 'No', TRIA in effect", dict(indicator="No"), {T: 8, DT: 8}, True),
    ("Z7", "C13-13", "post-TRIA, exclusion answer blank", dict(tria=POST), {T: 0}, True),
    ("Z8", "C13-13", "no EffDate, TRIA expiring (engine only)", dict(tria=WILL_EXPIRE, exp="06/01/2027", effdate=False),
     "REFUSES", False),
    # C13-14
    ("O1", "C13-14", "override Yes, 500, in effect", dict(override="Yes", override_prem=500), {T: 500, DT: 500}, True),
    ("O2", "C13-14", "override Yes, 500, expiring", dict(override="Yes", override_prem=500, tria=WILL_EXPIRE,
                                                          exp="06/01/2027"),
     {PRE: 350, POSTP: 150, T: 500, DE: 500}, True),
    ("O3", "C13-14", "override Yes, no premium entered", dict(override="Yes"), {DT: 0}, True),
    ("O4", "C13-14", "override No, 500 entered", dict(override="No", override_prem=500), {T: 8, DT: 8}, True),
]


def check(data, want):
    bad = []
    for k, v in want.items():
        got = gc.read(k, data)
        if v is None:
            ok = got is None
        elif v == 0:
            ok = got is None or gc.num_eq(got, 0)
        else:
            ok = gc.num_eq(got, v)
        if not ok:
            bad.append((k, got, v))
    return bad


def engine():
    fails = []
    by_task = collections.Counter()
    for cid, task, label, kw, want, _ in CASES:
        try:
            data, ip = gc.run(sub(**kw))
            if want == "REFUSES":
                print(f"{cid:5s} {task} {label}: ran, expected a refusal   << expected")
                fails.append(cid)
                continue
        except InterpretError as exc:
            if want == "REFUSES":
                print(f"{cid:5s} {task} {label}: refuses as predicted ({str(exc)[:70]})")
                by_task[task] += 1
                continue
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                by_task[task] += 1
                continue
            print(f"{cid:5s} {task} {label}: RAISED {exc}")
            fails.append(cid)
            continue
        bad = check(data, want)
        print(f"{cid:5s} {task} {label}: {len(want) - len(bad)} of {len(want)}"
              + ("" if not bad else "   << expected"))
        for k, got, v in bad:
            print(f"        {k[-80:]}  got {got}  want {v}")
        if bad:
            fails.append(cid)
        else:
            by_task[task] += 1
    return fails, by_task


def live():
    import raas as raas_mod
    client = raas_mod.RaaS()
    rows = []
    for cid, task, label, kw, want, go in CASES:
        if not go:
            continue
        req = r11.payload(sub(**kw))
        (gc.OUT / f"chunk13_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            (gc.OUT / f"chunk13_rc3_{cid}_refusal.json").write_text(str(exc.body), encoding="utf-8")
            msg = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
            rows.append((cid, "ISO REFUSES", msg.group(0)[:140] if msg else str(exc.body)[:140]))
            continue
        (gc.OUT / f"chunk13_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        st, eff, ours = rp.replay(req, None)
        iso = rp.iso_fields(resp)
        diffs = [(k, v, ours.get(k)) for k, v in iso.items()
                 if rp.num(v) != rp.num(ours.get(k)) and not (rp.num(v) in (None, 0.0) and rp.num(ours.get(k)) in (None, 0.0))]
        tp = [v for k, v in iso.items() if k.endswith("CommercialPropertyStructure[0]/TerrorismPremium")]
        rows.append((cid, "AGREE" if not diffs else "DIFFER", f"ISO building terrorism {tp[0] if tp else None}"
                     + "".join(f"; {k[-60:]} ISO {v} ours {o}" for k, v, o in diffs)))
    for r in rows:
        print(f"  {r[0]:5s} {r[1]:12s} {r[2]}")
    agree = sum(r[1] == "AGREE" for r in rows)
    print(f"\n  live: {agree} of {len(rows)} agree field for field; "
          f"{sum(r[1] == 'ISO REFUSES' for r in rows)} ISO refusals")
    return rows


def literals():
    """C13-15: every constant a terrorism rule compares a policy answer against, vs the Domain Tables."""
    b = book_for("OR", gc.ASOF)
    dom = {}
    for content in (b.parent.package.content, b.state.package.content):
        d = content / "Domain Tables"
        if not d.exists():
            continue
        for f in d.glob("*.DomainTable.csv"):
            with open(f, encoding="utf-8-sig") as h:
                rows = list(csv.DictReader(h))
            if rows and "DataValue" in rows[0]:
                dom.setdefault(f.name.split(".")[0], set()).update(r["DataValue"] for r in rows)
    fields = {"TRIAType": "DomainTerrorismTRIAType", "CoverageForCertifiedActs": "DomainTerrorismCoverageForCertifiedActs",
              "PostTRIAExclusion": "DomainTerrorismPostTRIAExclusion",
              "TRIAConditionalExclusion": "DomainTerrorismConditionalExlusion",
              "ConditionalExclusionRatingOption": "DomainTerrorismConditionalRatingOption",
              "TerrorismTerritory": None, "TerrorismOverride": None, "TerrorismIndicator": None}
    seen = collections.defaultdict(set)
    rx = re.compile(r'<rul:(?:Equal|NotEqual)[^>]*>\s*<rul:FirstValue[^>]*FromDataDef="(?:\.\./)*([A-Za-z]+)"[^>]*/>'
                    r'\s*<rul:Constant[^>]*>([^<]*)</rul:Constant>')
    for content in (b.parent.package.content, b.state.package.content):
        for f in (content / "Rules").glob("*.xml"):
            s = f.read_text(encoding="utf-8-sig")
            for fld, lit in rx.findall(s):
                if fld in fields:
                    seen[fld].add(lit)
    print("\nC13-15  literals compared against, vs the Domain Tables (CW 20260601 + OR):")
    bad = 0
    for fld, lits in sorted(seen.items()):
        dname = fields[fld]
        domain = dom.get(dname, set()) if dname else None
        if fld == "TerrorismTerritory":
            with open(b.state.package.content / "Rate Tables" / "TerrorismTerritoryTier.RateTable.csv",
                      encoding="utf-8-sig") as h:
                domain = {r["TerrorismTerritory"] for r in csv.DictReader(h)}
        if domain is None:
            print(f"  {fld:34s} {sorted(lits)}  (Yes/No flag; no domain table)")
            continue
        off = sorted(l for l in lits if l and l not in domain)
        bad += len(off)
        print(f"  {fld:34s} {len(lits)} literals, all in the domain" if not off
              else f"  {fld:34s} NOT IN DOMAIN: {off}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails, by_task = engine()
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} cases as derived; by task {dict(by_task)}")
    bad_lits = literals()
    if a.live:
        print("\nISO live at 2026-09-17:")
        live()
    sys.exit(1 if fails or bad_lits else 0)


if __name__ == "__main__":
    main()
