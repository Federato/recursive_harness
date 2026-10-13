#!/usr/bin/env python3
"""Chunk 12 -- live ISO comparison for one endorsement family (C12-16, C12-22).

Generalises `129_chunk12_c12-10_raas.py`: every node whose tag carries the
family's key and holds a `Premium` is compared, ours against ISO's, in document
order, so a family with many cells (Ordinance or Law: A/B/C/B+C x 5 forms,
plus Increased Period of Restoration) needs no hand-written cell list.

    python scripts/cf/132_chunk12_family_raas.py ordinance [--only C0,K5]
    python scripts/cf/132_chunk12_family_raas.py utility   [--only ...]

Sent at EffectiveDateTime 2026-09-17 (OI-105). Requests and responses go to
results/cf-raas/chunk12_<family>_<case>_*.json.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

import raas as raas_mod                                        # noqa: E402
from cf_engine.config import NULL_ARITHMETIC, ROUNDING         # noqa: E402
from cf_engine.resolve import book_for                         # noqa: E402
from gl_engine.interp.interpreter import Interpreter           # noqa: E402
from gl_engine.interp.tree import Node                         # noqa: E402
from gl_engine.interp.values import InterpretError             # noqa: E402

dr = import_module("129_chunk12_c12-10_raas")
r11, ops = dr.r11, dr.ops
# ISO types these as JSON numbers and rejects a string ("Error reading view element").
r11.NUMERIC |= {"CovBDemolitionLimit", "CovCIncreasedConstructionLimit",
                "CombinedBAndCDemolitionAndIncrdConstrctnLimit", "Factor",
                "LimitOfInsurance", "BlanketLimitOfInsurance", "RelatedExpenses", "ManualPremium", "ContributingLocationsLimit", "BasicGroupIRate", "BasicGroupIIRate", "UtilityServicesLimit", "DirectDamageLimit", "TimeElementLimit"}
EFFECTIVE, OUT = dr.EFFECTIVE, dr.OUT


def ours_premiums(data, key):
    out, seen = {}, collections.Counter()
    stack = [data]
    while stack:
        n = stack.pop(0)
        for c in n.children:
            if key in c.tag and not c.tag.endswith("Table"):
                p = next((x.text for x in c.children if x.tag == "Premium"), None)
                if p is not None:
                    seen[c.tag] += 1
                    out[f"{short(c.tag, key)}#{seen[c.tag]}"] = p
            stack.append(c)
    return out


def iso_premiums(resp, key):
    out, seen = {}, collections.Counter()
    queue = [resp]
    while queue:
        n = queue.pop(0)
        if isinstance(n, dict):
            for k, v in n.items():
                recs = v if isinstance(v, list) else [v]
                for r in recs:
                    if isinstance(r, dict):
                        if key in k and "Premium" in r:
                            seen[k] += 1
                            out[f"{short(k, key)}#{seen[k]}"] = r["Premium"]
                        queue.append(r)
        elif isinstance(n, list):
            queue.extend(n)
    return out


def short(tag, key):
    return tag.replace("CommercialProperty", "").replace(key, "~")


def iso_messages(resp):
    return sorted({e.get("Description") for m in r11.find(resp, "RatingMessages")
                   for kind in (m.values() if isinstance(m, dict) else [])
                   for e in (kind if isinstance(kind, list) else [])
                   if isinstance(e, dict) and e.get("Description")})


def rate_ours(esub, juris, key):
    try:
        ip = Interpreter(book_for(juris, "20260917"), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{juris}", esub)
        ip.run(data)
        return ours_premiums(data, key), sorted(set(ip.messages))
    except InterpretError as exc:
        return f"REFUSED {str(exc)[:120]}", []


def filed_eqterrs(st):
    """EQTerr values the state's EarthquakeDeductibleTier files at 2026-09-17."""
    import csv
    bk = book_for(st, "20260917")
    for layer in (bk.state.package.content, bk.parent.package.content):
        p = layer / "Rate Tables" / "EarthquakeDeductibleTier.RateTable.csv"
        if p.exists():
            with open(p, encoding="utf-8-sig") as h:
                rows = [r for r in csv.reader(h) if r][1:]
            if rows:
                return [r[1] for r in rows]
    return []


def fixture_cases(key):
    """Each fixture as filed, plus -- when its EQTerr has no EarthquakeDeductibleTier
    row at 2026 (a 2023 fixture; ISO refuses, OI-103) -- a variant re-sent at the
    state's first filed territory, so the family's own cells can still be compared."""
    import re
    out = []
    for p in sorted(ops.ISO_CF.rglob("STC/*.json")):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        if key not in t:
            continue
        d = json.loads(t)
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        out.append((f"F-{p.stem[-5:]}", f"ISO fixture {p.name} ({st})", ("fixture", d)))
        terrs = set(re.findall(r'"EQTerr"\s*:\s*"([^"]*)"', t)) - {""}
        filed = filed_eqterrs(st)
        if terrs and filed and not terrs <= set(filed):
            t2 = re.sub(r'("EQTerr"\s*:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{filed[0]}"', t)
            out.append((f"F-{p.stem[-5:]}t", f"same, EQTerr {sorted(terrs)} -> {filed[0]} ({st})",
                        ("fixture", json.loads(t2))))
    return out


def prepare(case, key):
    cid, label, sub = case
    if isinstance(sub, tuple) and sub[0] == "fixture":
        d = sub[1]
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        esub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
        esub.update(ops.to_engine({"CommercialProperty": d["CommercialProperty"]}))
        req = {"header": {"quoteback": "", "authorization": {}},
               "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                       "EffectiveDateTime": EFFECTIVE},
                        "CommercialProperty": d["CommercialProperty"]}}
    else:
        st = "OR"
        esub = r11.at_date(sub)
        req = r11.payload(esub)
    ours, msgs = rate_ours(esub, st, key)
    return ours, msgs, req


def nz(d):
    return {k: v for k, v in d.items() if dr.num(v) != 0} if isinstance(d, dict) else d


def compare(name, key, cases, only=()):
    todo = [c for c in cases if not only or c[0] in only]
    client = raas_mod.RaaS()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Chunk 12 {name} -- live ISO at {EFFECTIVE}\n")
    agree = 0
    for case in todo:
        cid, label = case[0], case[1]
        ours, msgs, req = prepare(case, key)
        stem = f"chunk12_{name}_{cid}"
        (OUT / f"{stem}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
            (OUT / f"{stem}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            iso, imsgs = iso_premiums(resp, key), iso_messages(resp)
            same = isinstance(ours, dict) and all(
                dr.num(iso.get(k)) == dr.num(ours.get(k)) for k in set(iso) | set(ours))
            iso_s = nz(iso) or "all $0"
        except raas_mod.RaaSError as exc:
            (OUT / f"{stem}_refusal.json").write_text(str(exc.body), encoding="utf-8")
            iso_s, imsgs, same = f"ISO REFUSED {exc.status}: {str(exc.body)[:260]}", [], isinstance(ours, str)
        agree += same
        print(f"  {cid:9s} {label}")
        print(f"       ours : {nz(ours) or 'all $0'}")
        print(f"       ISO  : {iso_s}")
        print(f"       {'AGREE' if same else 'DIVERGE'}   messages "
              f"{'identical' if msgs == imsgs else f'DIFFER ours={msgs} iso={imsgs}'}")
    print(f"\n{agree} of {len(todo)} agree")


def ordinance_cases():
    o = import_module("130_chunk12_ordinance_golden_case")
    gates = import_module("128_chunk12_debris_removal_gates")
    chunk5 = import_module("32_chunk5_golden_case")
    base = dict(o.RECORD)
    combined = dict(base, CovType="Coverages A and B & C Combined", CovBDemolitionLimit="0",
                    CovCIncreasedConstructionLimit="0",
                    CombinedBAndCDemolitionAndIncrdConstrctnLimit="50000")

    def vandal():
        s = o.submission()
        s["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = "Commercial Property Policy"
        gates.structure(s)["CommercialPropertyVandalismExclusionTable"] = {
            "CommercialPropertyVandalismExclusion": [{}]}
        return s

    def ipr():
        s = chunk5.submission()
        bi = gates.structure(s)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
        k = "CommercialPropertyOrdinanceOrLawIncreasedPeriodOfRestoration"
        bi[k + "Table"] = {k: [{"PostLossOrdinanceOrLawOption": "No"}]}
        return s

    return [
        ("C0", "golden: A and B & C Separate (ours $198)", o.submission()),
        ("K2", "Coverage C Only (ours $82 + $10)", o.submission(record=dict(base, CovType="Coverage C Only"))),
        ("K4", "A and B & C Combined 50,000 (ours $198)", o.submission(record=combined)),
        ("K5", "CovType blank (ours: Cov A still $39 + $5)", o.submission(record=dict(base, CovType=""))),
        ("K6", "post-loss option Yes (ours $208)", o.submission(record=dict(base, PostLossOrdinanceOrLawOption="Yes"))),
        ("K7", "B and C limits absent (ours: REFUSES, null premium)",
         o.submission(record={k: v for k, v in base.items() if "Limit" not in k})),
        ("V1", "vandalism exclusion (ours: $37/$52/$78 on BGI)", vandal()),
        ("I1", "Increased Period of Restoration on chunk 5's BI (ours BGI $22)", ipr()),
    ]


def utility_cases():
    u = import_module("133_chunk12_utility_golden_case")
    return u.RAAS_CASES()


def drone_cases():
    d = import_module("137_chunk12_drone_golden_case")
    gt = import_module("138_chunk12_drone_gates")
    D = d.DETAIL

    def wind():
        s = d.submission()
        gt._pp(s)["CommercialPropertyWindstormOrHailExclusionPrsnlPropTable"] = {
            "CommercialPropertyWindstormOrHailExclusionPrsnlProp": [{}]}
        return s
    return [
        ("U0", "golden: one drone, All Other, 10,000, no deductible (ours $187)", d.submission()),
        ("U1", "Contents on the Basic form (ours $0)", d.submission(col="Basic")),
        ("U2", "TypeOfOperations blank (ours $0)", d.submission(dict(D, TypeOfOperations=""))),
        ("U3", "Search & Rescue, high risk (ours $290)", d.submission(dict(D, TypeOfOperations="Search & Rescue"))),
        ("U4", "LimitOfInsurance absent (ours $2, null skipped)", d.submission({k: v for k, v in D.items() if k != "LimitOfInsurance"})),
        ("U5", "deductible 1,000 (ours $156)", d.submission(dict(D, Deductible="1,000"))),
        ("U6", "newly-acquired extension (ours $196)", d.submission(dict(D, CoverageExtensionForNewlyAcquiredPropertyIncludingTemporarySubstitutePropertyAppliesToScheduledCoverageonly="Yes"))),
        ("U7", "blanket drone 10,000 (ours $187)", d.submission(dict(D, BlanketCoverageUnmannedAircraftAppliesToUnmannedAircraftNotIndividuallyDescribed="Yes", BlanketLimitOfInsurance="10000"))),
        ("U8", "two drones (ours $187 + $93)", d.submission(details=[dict(D), dict(D, LimitOfInsurance="5000")])),
        ("U9", "Contents windstorm exclusion (ours $59)", wind()),
    ]


def green_cases():
    return import_module("139_chunk12_green_golden_case").RAAS_CASES()


def dependent_cases():
    return import_module("141_chunk12_dependent_golden_case").RAAS_CASES()


FAMILIES = {
    "dependent": ("DependentProp", dependent_cases),
    "green": ("GreenUpgrades", green_cases),
    "drone": ("UnmannedAircraft", drone_cases),
    "ordinance": ("OrdinanceOrLaw", ordinance_cases),
    "utility": ("UtilityServices", utility_cases),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("family", choices=sorted(FAMILIES))
    ap.add_argument("--only", default="")
    ap.add_argument("--no-fixtures", action="store_true")
    a = ap.parse_args()
    key, cases = FAMILIES[a.family]
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    todo = cases() + ([] if a.no_fixtures else fixture_cases(key))
    compare(a.family, key, todo, only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
