#!/usr/bin/env python3
"""OI-134 / OI-130: which answers change the premium silently when missing or not on ISO's list?
-> gl_engine/schema/rating_inputs.json

Population, at each date below: every state's console request (`console.workbench.build`) and ISO's own sample
policies for the coverages the console request does not carry (OCP, Liquor, Railroad, drones, Stop Gap, NY
terrorism, Cyber). For each request, every answer it carries is tried two ways, one at a time:

    missing   an ISO-required answer left out               -> `fields`: the engine refuses it missing (or blank)
    invalid   a list-based answer given a value not on ISO's list for the edition
                                                              -> `list_fields`: the engine refuses an invalid value

`list_fields` is written as measured. `fields` is NOT: it is the decided list (the file's own, B-27's 14, plus
`ADD_FIELDS`), and every other silent missing field goes to `missing_candidates` for review one at a time (the
user's decision 2026-10-13). The wider population found 39 more, and some are opt-in answers whose absence
prices exactly like "No" or $0 -- Cyber in CA/GA, Stop Gap in PR, every ManualPremium -- so adding them
wholesale refuses clean requests.

and each try is classified:

    silent  rated, the premium moved, nothing refused, no new ISO message   -> must refuse
    stops   the engine refused                                              -> already safe
    same    rated, premium unchanged                                        -> informational

    python scripts/erc/57_rating_inputs.py            # measure and print
    python scripts/erc/57_rating_inputs.py --write    # also write gl_engine/schema/rating_inputs.json

The checks are switched off while measuring (`ERC_RATING_INPUTS=off`), or every input would already stop.
First run 2026-10-13 (missing only, console requests): 4,385 drops, 964 silent across 14 fields. No ISO calls.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import glob
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
OUT = ROOT / "gl_engine" / "schema" / "rating_inputs.json"
DATES = ("20260801", "20270501")       # the editions in force now, and past the 2027-04-01 cliff
NOT_ON_LIST = "ZZ-NOT-ON-ISO-LIST"

#: Added to `fields` beyond B-27's 14, each decided in the B-07 plan (OI-130): part 3d, a company-rated class
#: (54444 / 94444) with its ELP override but not its limit-table override prices Prem/Ops $8 for $4,633 and
#: Products $0 (Company-TX); part 3a, NY terrorism in territory 001 / 010 without the Manhattan answer prices
#: terrorism $0 (Terrorism-NY 12602 -> 12141).
ADD_FIELDS = ("GeneralLiabilityClassification.PremOpsIncrdLimitTableAssignmentOverride",
              "GeneralLiabilityClassification.ProdsCompldOpsIncrdLimitTableAssignmentOverride",
              "GeneralLiabilityLocation.CertifiedActsOfTerrorismManhattan")

#: ISO's own sample policies (`<state>/**/STC/<file>`), one classification kept where noted. Chosen
#: 2026-10-13 by the OI-130 reproduction: each carries a coverage the console request does not.
SAMPLES = {
    "OCP-WY": ("WY", "STC_GL000140110.json", None),
    "Liquor-AL": ("AL", "STC_GL000092157.json", 3),
    "Railroad-RI": ("RI", "STC_GL000077673.json", 2),
    "Railroad-NH": ("NH", "STC_GL000080459.json", 0),
    "Cyber-IL": ("IL", "STC_GL000110216.json", None),
}


def _gl(p):
    return p["body"]["GeneralLiability"][0]


def _sample(name, date):
    from gl_engine.config import CORPUS_ROOT as ERC_ROOT
    st, fname, keep = SAMPLES[name]
    f = glob.glob(os.path.join(str(ERC_ROOT), st, "**", fname), recursive=True)[0]
    p = {"header": {"quoteback": "", "authorization": {}}, "body": json.load(open(f, encoding="utf-8-sig"))}
    p["body"]["SchemeKeys"]["EffectiveDateTime"] = f"{date[:4]}-{date[4:6]}-{date[6:]}T00:00:00"
    g = _gl(p)
    if keep is not None:
        loc = g["GeneralLiabilityLocation"][0]
        loc["GeneralLiabilityClassification"] = [loc["GeneralLiabilityClassification"][keep]]
    if date >= "20270401":
        if name == "Liquor-AL":                 # 58161 is retired in 2027: a live class and basis instead
            c = g["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]
            c["LiquorClassCode"] = "50952"
            c["LiquorPremiumBasis"] = "Gross Sales of Alcoholic Beverages"

        def strip(n):                          # 2027 limits carry no " CSL" suffix (OI-96)
            if isinstance(n, dict):
                for k, v in n.items():
                    if isinstance(v, str) and v.endswith(" CSL"):
                        n[k] = v[:-4]
                    else:
                        strip(v)
            elif isinstance(n, list):
                for x in n:
                    strip(x)
        strip(p)
        g.setdefault("ProdsCompldOpsExclusion", "No")
    return p


def _built(name, date):
    from console import workbench as WB
    if name.startswith("console-"):
        return WB.build("GL", name[8:], {"effective_date": date})
    if name == "Drone-TX":
        p = WB.build("GL", "TX", {"effective_date": date})
        g = _gl(p)
        if date >= "20270401":
            g["UnmannedAircraftCoverageOptions"] = "Limited Coverage For Designated Unmanned Aircraft"
        else:
            g["LimitedCovForDesignatedUnmannedAircraft"] = "Yes"
        g["GeneralLiabilityLimitedCovForDesignatedUnmannedAircraft"] = [
            {"GeneralLiabilityLimitedCovForDesignatedUnmannedAircraftDetail": [{}]}]
        g["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]["GeneralLiabilityUnmannedAircraft"] = [{
            "PrimaryPlaceOfOperation": "Rural",
            "OwnershipAndOperation": "Unmanned aircraft owned and operated by the insured",
            "BIPDDeductible": "No Deductible",
            "Usage": "Aerial photography, surveillance, inspection, survey, data collection, media services",
            "CovAApplies": "Yes", "CovBApplies": "Yes", "MaximumTakeoffWeight": 10, "AggregateLimit": "1,000,000"}]
        return p
    if name.startswith("StopGap-"):
        p = WB.build("GL", name[8:], {"effective_date": date})
        g = _gl(p)
        g["StopGap"] = "Yes"
        lim = "100,000" if date >= "20270401" else "100,000 BI"
        g["GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl"] = [{
            "LimitBodilyInjuryByAccident": lim, "LimitBodilyInjuryByDiseaseEachEmployee": lim,
            "LimitBodilyInjuryByDiseaseAggregate": "500,000" if date >= "20270401" else "500,000 BI"}]
        return p
    if name == "Company-TX":                  # a 'refer to company' class: both overrides ISO's form requires
        p = WB.build("GL", "TX", {"effective_date": date})
        c = _gl(p)["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]
        c.update(ClassCode="54444", PremOpsELPOverride=0.5, ProdsCompldOpsELPOverride=0.5,
                 PremOpsIncrdLimitTableAssignmentOverride="2", ProdsCompldOpsIncrdLimitTableAssignmentOverride="B")
        return p
    if name.startswith("StopGapManual-"):     # limits off ISO's combinations: ISO's form requires a manual premium
        p = _built("StopGap-" + name[14:], date)
        r = _gl(p)["GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl"][0]
        r["LimitBodilyInjuryByDiseaseEachEmployee"] = "500,000" if date >= "20270401" else "500,000 BI"
        r["ManualPremium"] = 250.0
        return p
    if name == "Terrorism-NY":
        p = WB.build("GL", "NY", {"effective_date": date, "terrorism": "Yes"})
        for loc in _gl(p)["GeneralLiabilityLocation"]:
            loc.setdefault("TerrorismTerritory", "001")
            loc.setdefault("CertifiedActsOfTerrorismManhattan", "No")
        return p
    return _sample(name, date)


def one(job):
    name, date = job
    os.environ["ERC_RATING_INPUTS"] = "off"
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
    from gl_engine.rating import Kernel
    from gl_engine.resolve import ResolvedBook
    from gl_engine.schema import Schema
    try:
        req = _built(name, date)
    except Exception as exc:                         # noqa: BLE001
        return [(name, date, "-", "-", f"build failed: {type(exc).__name__}", None, None)]
    k = Kernel(mode="strict-erc")
    base = k.rate(copy.deepcopy(req))
    if not base.complete:
        return [(name, date, "-", "-", f"base stopped: {str(base.stopped)[:80]}", None, None)]
    base_msgs = {str(m) for m in base.messages}
    sch = Schema.for_book(ResolvedBook(k.resolver.resolve(base.juris, base.asof)))

    def visit(obj, table, path):
        for key, val in list(obj.items()):
            if isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        yield from visit(item, key, path + [key, i])
            elif isinstance(val, dict):
                yield from visit(val, f"{table}.{key}", path + [key])
            else:
                f = sch.get(table, key)
                if f is not None and f.is_input:
                    yield path, key, f

    out = []
    for path, col, f in list(visit(_gl(req), "GeneralLiability", [])):
        tries = []
        if f.policy_required:
            tries.append("missing")
        if f.domain and sch.legal_values(f.table, f.column):
            tries.append("invalid")
        for how in tries:
            r2 = copy.deepcopy(req)
            d = _gl(r2)
            for p in path:
                d = d[p]
            if how == "missing":
                d.pop(col, None)
            else:
                d[col] = NOT_ON_LIST
            try:
                r = k.rate(r2)
                if not r.complete:
                    cls = "stops"
                elif r.premium == base.premium:
                    cls = "same"
                elif {str(m) for m in r.messages} - base_msgs:
                    cls = "messaged"
                else:
                    cls = "silent"
                prem = str(r.premium) if r.complete else None
            except Exception as exc:                 # noqa: BLE001 - a refusal by another name
                cls, prem = "stops", type(exc).__name__
            out.append((name, date, how, f"{f.table}.{f.column}", cls, str(base.premium), prem))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    states = sorted(Path(p).parent.name for p in glob.glob(str(ROOT / "Engine_Payloads" / "*" / "submission.json")))
    names = [f"console-{s}" for s in states] + list(SAMPLES) + ["Drone-TX", "StopGap-ND", "StopGap-WA",
                                                                    "StopGapManual-ND", "Company-TX", "Terrorism-NY"]
    rows = []
    # a fresh worker per request: each loads one state's book and exits, so memory stays at one book per worker
    # (a long-lived worker keeps every book it has loaded; at 6 workers that exhausted a 16 GB machine)
    with ProcessPoolExecutor(a.jobs, max_tasks_per_child=1) as ex:
        for res in ex.map(one, [(n, d) for d in DATES for n in names]):
            rows.extend(res)
    for r in rows:
        if r[3] == "-":
            print(f"  skipped {r[0]} {r[1]}: {r[4]}")
    tally = collections.Counter((r[2], r[4]) for r in rows if r[3] != "-")
    found = {}
    for how in ("missing", "invalid"):
        by = collections.defaultdict(lambda: {"silent": set(), "stops": 0, "same": 0, "messaged": 0, "example": ""})
        for name, date, h, field, cls, b, p in rows:
            if h != how or field == "-":
                continue
            e = by[field]
            if cls == "silent":
                e["silent"].add(f"{name}@{date}")
                e["example"] = e["example"] or f"{name} {date}: {b} -> {p}"
            else:
                e[cls] += 1
        found[how] = {n: e for n, e in by.items() if e["silent"]}
        print(f"\n{how.upper()}: {sum(v for (h, _), v in tally.items() if h == how)} tries, "
              f"{ {c: v for (h, c), v in tally.items() if h == how} }")
        for n, e in sorted(found[how].items(), key=lambda x: -len(x[1]["silent"])):
            print(f"  {len(e['silent']):3} silent  {n:78} (stops {e['stops']}, same {e['same']}, "
                  f"messaged {e['messaged']})  e.g. {e['example']}")
    if a.write:
        decided = sorted(set(json.loads(OUT.read_text(encoding="utf-8")).get("fields", ())) | set(ADD_FIELDS))
        unseen = [f for f in decided if f not in found["missing"]]
        if unseen:
            print(f"  note: decided fields not silent in this run (kept): {unseen}")
        OUT.write_text(json.dumps({
            "what": "Answers whose absence (fields) or off-list value (list_fields) changes the premium with no "
                    "refusal and no ISO message (OI-134, OI-130). The engine refuses a rating that leaves a field "
                    "out or blank where ISO's conditions require it, or gives a list field a value not on ISO's list.",
            "measured": str(dt.date.today()), "by": "scripts/erc/57_rating_inputs.py", "dates": list(DATES),
            "population": names,
            "tries": {f"{h} {c}": v for (h, c), v in sorted(tally.items())},
            "fields": decided,
            "list_fields": sorted(found["invalid"]),
            "evidence": {h: {n: {"silent_in": len(e["silent"]), "example": e["example"]}
                             for n, e in sorted(found[h].items()) if h == "invalid" or n in decided}
                         for h in found},
            "missing_candidates": {n: {"silent_in": len(e["silent"]), "same": e["same"], "example": e["example"]}
                                   for n, e in sorted(found["missing"].items()) if n not in decided},
        }, indent=1) + "\n", encoding="utf-8")
        cands = len(set(found["missing"]) - set(decided))
        print(f"\nwrote {OUT.relative_to(ROOT)}: {len(decided)} fields (decided), {len(found['invalid'])} list "
              f"fields, {cands} missing candidates for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
