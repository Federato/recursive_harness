#!/usr/bin/env python3
"""Chunk 19, RC-3 (C19-15, C19-16): shared names and exclusion records.

C19-15  SHARED NAMES. First a static diff over every chunk 19 countrywide rule file: each Set rule that
        writes one of the shared field names (rates, Factor / BaseFactor, LimitToUse, the Group II symbol,
        CoinsuranceFactor, CoverageOnPolicyIndicator), which record writes it, and whether the write is
        IsNull-GUARDED (a submitted value survives) or unconditional (a submitted value is overwritten).
        Then probes, each predicted before its ISO call from that classification:
  S1  an antenna's BasicGroupIRate 0.100 SUBMITTED (guarded)                  -> used (the filed rate is 0.07)
  S2  Temporarily Away Group I Factor 0.5 SUBMITTED (guarded)                  -> used (filed 0.1)
  S3  Brands Factor 0.5 SUBMITTED (guarded)                                    -> used: every rate is then
                                                                                 min(0.053, 0.5 x the contents rate)
  S4  tenants' unscheduled CoinsuranceFactor 0.9 SUBMITTED (guarded)           -> used (filed 1.0 at 80%)
  S5  a sign's BasicGroupIISymbolNum 2 SUBMITTED (unconditional RunRule)       -> OVERWRITTEN (metal: 4)
  S6  CoverageOnPolicyIndicator 1 SUBMITTED on a tenants' other-than-glass record under a glass-only
      container (unconditional switch rule)                                    -> OVERWRITTEN: 0, $0
C19-16  EXCLUSION RECORDS, each against its control, predicted by hand from the filed rule:
  X0 / X1  every chunk 19 record (191_'s Special tree, limits x 10 so 0.995 can move a dollar) without / with
           the cyber-incident exclusion: every premium = hand with the independent cyber factors
           (CyberIncidentExclusionFactors: 0.995 per peril group, EQ 1.00); the records whose dollar moves listed
  X2       antennas, trees and signs with the building's VANDALISM exclusion: trees multiply their Group I rate
           by their own VandalismExclFactor; antennas / signs read the building's
  X3       the same three with the building's WINDSTORM OR HAIL exclusion: Group II switches to the LOWEST Group
           II rate, symbol number 1, and the windstorm factor (AB / B 0.315)
  X4       T1's tenants' container with the building's EQSprinklerLeakageOnly "Yes": the EQ forms read the
           building's EQSprinklerLeakageOnlyBldgFactor
  (Trees' vehicle exclusion is an input on the trees record, not a record: proven in C19-08, TR2 / TR3.)

    python scripts/cf/194_chunk19_c19-15-16.py [--live] [--cases S1,X3]

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
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

g = import_module("192_chunk19_rc2")
rc1m = import_module("191_chunk19_rc1")
r3 = import_module("176_chunk16_rc3")
r2, rc1, gc, rep, cmp, r11, r16 = g.r2, g.rc1, g.gc, g.rep, g.cmp, g.r11, g.r16
P, same, row = g.P, g.same, g.row
r11.NUMERIC |= {"Factor", "BasicGroupIRate", "CoinsuranceFactor", "BasicGroupIISymbolNum", "CoverageOnPolicyIndicator",
                "EachTreeLimit"}          # ISO types it as a number (193_ found it first)
FAIL = []
UNS, ANT, TREE, SIGN, BRAND, TA = g.UNS, g.ANT, g.TREE, g.SIGN, g.BRAND, g.TA
CYBER = {f"CyberIncidentExclusionFactor{k}": row("CyberIncidentExclusionFactors", "Factor", StateCode="CW",
                                                 CausesOfLossOrPerilGroupPremium=n)
         for k, n in (("BGI", "Basic Group I"), ("BGII", "Basic Group II"), ("Broad", "Broad"),
                      ("Special", "Special"), ("EQ", "Earthquake"))}
SHARED = re.compile(r"^(BasicGroupIRate|BasicGroupIIRate|BasicGroupIIBaseRate|BroadRate|BroadBaseRate|SpecialRate|SpecialBaseRate|"
                    r"EQRate|EQBaseRate|Rate|Factor|BaseFactor|LimitToUse|Limit|BasicGroupIISymbol|BasicGroupIISymbolNum|"
                    r"CoinsuranceFactor|CoverageOnPolicyIndicator)$")


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def at(sub):
    return rc1.node_dicts(sub)


def change(build, fn):
    def b():
        sub = build()
        fn(sub)
        return sub
    return b


# ------------------------------------------------------------ the static diff

def writers():
    """(field, record) -> 'guarded' | 'unconditional', from every Set rule in the chunk 19 CW files."""
    cw = book_for("OR", r2.ASOF).parent.package.content / "Rules"
    out = {}
    for fam, pat in rc1m.cen.FAMILIES:
        for f in sorted(cw.glob("*.xml")):
            if not re.search(pat, f.name) or rc1m.cen.EXCLUDE.search(f.name):
                continue
            t = f.read_text(encoding="utf-8-sig")
            rec = f.name[len(P):-len("Rules.Rule.xml")]
            for m in re.finditer(r'<rul:Rule Name="(Set\w+)"[^>]*>(.*?)</rul:Rule>', t, re.S):
                body = m.group(2)
                for fld in set(re.findall(r'ToDataDef="(\w+)"', body)):
                    if not SHARED.match(fld):
                        continue
                    guarded = re.search(rf'<rul:IsNull>\s*<rul:Value[^>]*FromDataDef="{fld}"', body) is not None
                    prev = out.get((fld, rec))
                    out[(fld, rec)] = "guarded" if guarded and prev != "unconditional" else "unconditional"
    return out


def static_diff():
    w = writers()
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for (fld, rec), kind in w.items():
        by[fld][kind].append(rec)
    print("C19-15  who writes each shared name in the chunk 19 files (guarded: a submitted value survives)")
    for fld in sorted(by):
        for kind in ("guarded", "unconditional"):
            recs = sorted(by[fld][kind])
            if recs:
                short = sorted({re.sub(r"(BasicGroupI+|Broad|Special|Earthquake|EQ)(Coverage|Cov)$", "*", r) for r in recs})
                print(f"    {fld:26s} {kind:13s} {len(recs):3d} records: {', '.join(short)[:150]}")
    return w


# ------------------------------------------------------------ cases

def s1(sub):
    at(sub)[P + "Structure"][P + ANT + "Table"][P + ANT][0][P + ANT + "DetailTable"][P + ANT + "Detail"][0]["BasicGroupIRate"] = "0.100"


def s2(sub):
    at(sub)[P + "PersonalProperty"][P + TA + "Table"][P + TA][0][P + TA + "DetailTable"][P + TA + "Detail"][0][
        P + TA + "DetailBasicGroupICov"]["Factor"] = "0.5"


def s3(sub):
    at(sub)[P + "PersonalProperty"][P + BRAND + "Table"][P + BRAND][0]["Factor"] = "0.5"


def s4(sub):
    r2.container(sub, "Structure", UNS)["CoinsuranceFactor"] = "0.9"


def s5(sub):
    at(sub)[P + "Structure"][P + SIGN + "Table"][P + SIGN][0][P + SIGN + "DetailTable"][P + SIGN + "Detail"][0][
        "BasicGroupIISymbolNum"] = "2"


def s6():
    sub = g.t2()
    c = r2.container(sub, "Structure", g.SCH)
    c["CovType"] = "Building Glass"
    for d in c[P + g.SCH + "DetailTable"][P + g.SCH + "Detail"]:
        d[P + g.SCH + "DetailBuildingPropertyOtherThanGlassBasicGroupICov"] = {"CoverageOnPolicyIndicator": "1"}
    return sub


LIMIT_FIELDS = {"Limit", "AllItemLimit", "LimitOnBuildingGlass", "LimitOnBuildingPropertyOtherThanGlass"}


def times10(d, inside=False):
    """limits x 10 inside the chunk 19 containers (so 0.995 moves a dollar)."""
    if isinstance(d, dict):
        for k, v in list(d.items()):
            fam = inside or any(x in k for x in ("TenantsPolicy", ANT, TREE, SIGN, BRAND, "Household", "LeasedProperty",
                                                  TA, "ManufacturersConsequential"))
            if isinstance(v, (dict, list)):
                times10(v, fam)
            elif inside and k in LIMIT_FIELDS and v not in (None, ""):
                d[k] = str(int(Decimal(str(v)) * 10))
    elif isinstance(d, list):
        for x in d:
            times10(x, inside)


def all_families(cyber):
    def b():
        pop = rc1m.population()
        xsd = rc1.xsd_for(book_for("OR", r2.ASOF))
        sub, _ = rc1m.family_tree(pop, xsd, "Special")
        times10(sub)
        if cyber:
            r3.cyber(sub)
        return sub
    return b


def three(extra=None):
    """antennas (A1), trees and signs on one Oregon policy, Special."""
    def b():
        sub = g.a1()
        st = at(sub)[P + "Structure"]
        st[P + TREE + "Table"] = {P + TREE: [{"AllItemLimit": "250000", "CauseOfLoss": "Special", "VehExcl": "No", "EachTreeLimit": "1000"}]}
        st[P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [
            g.sign_det("Special", "Detached", "Entirely Metal", "300000")]}}]}
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
            r2.put(sub, f"{TREE}{f}Coverage")
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Earthquake", "Special"):
            r2.put(sub, f"{SIGN}Detail{f}Coverage")
        if extra:
            r2.put(sub, extra)
        return sub
    return b


def x4():
    sub = g.t1()
    at(sub)[P + "Structure"]["EQSprinklerLeakageOnly"] = "Yes"
    return sub


THREE_RECS = g.A1_RECS + g.TREE_RECS + g.SIGN_RECS


def cases():
    """id -> (task, state, label, build, records predicted, {rec: overrides}, {rec path-field: expected tree value},
    control id or None)."""
    ALL = [r[len(P):] for rs in rc1m.population().values() for r in rs]
    ant0 = (ANT + "Detail", 0)
    return {
        "S1": ("C19-15", "OR", "antenna BasicGroupIRate 0.100 submitted (guarded -> used)", change(g.a1, s1), g.A1_RECS, {},
               {ant0: {"BasicGroupIRate": Decimal("0.100")}}, None),
        "S2": ("C19-15", "OR", "Temporarily Away Group I Factor 0.5 submitted (guarded -> used)", change(g.ta(False), s2), g.TA_RECS, {},
               {(TA + "DetailBasicGroupICov", 0): {"Factor": Decimal("0.5")}}, None),
        "S3": ("C19-15", "OR", "Brands Factor 0.5 submitted (guarded -> used)", change(g.brands("Special"), s3), g.BRAND_RECS, {},
               {(BRAND, 0): {"Factor": Decimal("0.5")}}, None),
        "S4": ("C19-15", "OR", "tenants' CoinsuranceFactor 0.9 submitted (guarded -> used)", change(g.t1, s4), g.T1_RECS, {},
               {(UNS, 0): {"CoinsuranceFactor": Decimal("0.9")}}, None),
        "S5": ("C19-15", "OR", "sign BasicGroupIISymbolNum 2 submitted (unconditional -> overwritten: 4)", change(g.s1, s5), g.SIGN_RECS, {},
               {(SIGN + "Detail", 0): {"BasicGroupIISymbolNum": g.val("OR", "OutsideSignsBasicGroupIISymbol", "Factor", Constant="Y")}}, None),
        "S6": ("C19-15", "OR", "CoverageOnPolicyIndicator 1 submitted under a glass-only container (overwritten: 0)", s6, g.T2_RECS, {},
               {(g.SCH + "DetailBuildingPropertyOtherThanGlassBasicGroupICov", 0): {"CoverageOnPolicyIndicator": "0", "Premium": "0"}}, None),
        "X0": ("C19-16", "OR", "all 63 records, limits x 10, no cyber exclusion (control)", all_families(False), ALL, {}, {}, None),
        "X1": ("C19-16", "OR", "all 63 records, limits x 10, cyber-incident exclusion", all_families(True), ALL,
               {r: dict(CYBER) for r in ALL}, {}, "X0"),
        "X2c": ("C19-16", "OR", "antennas + trees + signs (control for X2 / X3)", three(), THREE_RECS, {}, {}, None),
        "X2": ("C19-16", "OR", "antennas + trees + signs, the building's vandalism exclusion", three("VandalismExclusion"),
               THREE_RECS, {}, {}, "X2c"),
        "X3": ("C19-16", "OR", "antennas + trees + signs, the building's windstorm or hail exclusion", three("WindstormOrHailExclusion"),
               THREE_RECS, {}, {(ANT + "Detail", 0): {"BasicGroupIISymbolNum": Decimal("1")},
                                (TREE, 0): {"BasicGroupIISymbolNum": Decimal("1")}}, "X2c"),
        "X4": ("C19-16", "OR", "T1 with the building's EQSprinklerLeakageOnly Yes", x4, g.T1_RECS, {}, {}, "T1"),
    }


# ------------------------------------------------------------ run

def field_checks(data, expect):
    out = []
    for (rec, idx), fields in expect.items():
        nodes_ = r16.find(data, P + rec)
        node = nodes_[idx] if len(nodes_) > idx else None
        for f, want in fields.items():
            got = None if node is None or node.first(f) is None else node.first(f).text
            out.append((f"{rec}[{idx}]", f, got, want))
    return out


def engine(cid, j, build, recs, ovs):
    data, ip = gc.run(build(), j)
    preds, bad = {}, []
    for rec in recs:
        res, checks = r2.predict(data, rec, ovs.get(rec, {}), j)
        nodes_ = rc1.find(data, P + rec)
        off = [n.first("CoverageOnPolicyIndicator") is not None and n.first("CoverageOnPolicyIndicator").text == "0" for n in nodes_]
        res = [(Decimal(0) if o else h, e) for (h, e), o in zip(res, off)] if len(off) == len(res) else res
        fac_bad = [(f, e, v) for f, e, v in checks if not same(e, v)]
        ok = all(not str(h).startswith("hand") and same(h, e) for h, e in res) and not fac_bad
        preds[rec] = [h for h, _ in res]
        if not ok:
            bad.append((rec, res, fac_bad))
    return data, ip, preds, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    progress(0, 1, "static diff")
    static_diff()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, j, label, build, recs, ovs, expect, ctrl)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip, pr, bad = engine(cid, j, build, recs, ovs)
        except InterpretError as exc:
            print(f"{cid:4s} RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        preds[cid] = pr
        fc = field_checks(data, expect)
        fbad = [c for c in fc if not same(c[2], c[3])]
        priced = sum(1 for v in pr.values() if any(not same(x, 0) for x in v))
        print(f"{cid:4s} {task} {label}: engine {'as derived' if not bad and not fbad else 'DIFFERS'} "
              f"({len(recs) - len(bad)} of {len(recs)} records hand = engine, {priced} priced)")
        for w, f, got, want in fc:
            print(f"      {'ok  ' if same(got, want) else 'FAIL'} {w[:60]:60s} {f:28s} tree {got}  predicted {want}")
        for rec, res, fb in bad[:6]:
            print(f"      FAIL {r16.short(rec)[:64]:64s} {[(str(h), e) for h, e in res]} {fb[:2]}")
        if ctrl:
            base = preds.get(ctrl)
            if base is None and ctrl == "T1":
                _, _, base, _ = engine("T1", "OR", g.t1, g.T1_RECS, {})
            if base:
                moved = [(r16.short(r), [str(x) for x in base.get(r, [])], [str(x) for x in pr[r]])
                         for r in recs if [Decimal(str(x)) for x in base.get(r, [])] != [Decimal(str(x)) for x in pr[r]]]
                print(f"      moved vs {ctrl}: {len(moved)} records" + "".join(f"\n        {r[:62]:62s} {b} -> {c}" for r, b, c in moved[:40]))
                if not moved:
                    FAIL.append(f"{cid} moved nothing")
        if bad or fbad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, j, label, build, recs, ovs, expect, ctrl)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build())
            (gc.OUT / f"chunk19_c19-15-16_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {cid:4s} ISO REFUSES {m.group(0)[:220] if m else str(exc.body)[:220]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk19_c19-15-16_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid:4s} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC19-15 / C19-16: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
