#!/usr/bin/env python3
"""Chunk 28 C28-06 (set A): the refusals C28-05 introduced that ISO had never been asked about, sent live.

After C28-05 (a `SingleResult` lookup with no row refuses, Property only), the full gate's 23 newly failing scripts
refused on 22 tables; 15 of them are on record as ISO refusals (C28-02's table, OI-99's chunk 6 / 26 calls). The rest
were inputs no one had sent. Each probe is the exact policy the failing script built, sent as a request, ours first
(predicted: refuses at the named table), then ISO at 2026-09-17. Predicted before the run (2026-10-05): ISO refuses
every one at the same table; a probe ISO RATES is a rule that refuses too much, and stops set A.

  P1  207_ FL portable policy (EQ on the special class)          BldgHeightFactor
  P2  207_ OR condo options, loss assessment limit "10000"       LossAssessmentLimitConverted
  P3  207_ OR condo options, LA 10,000, deductible "All Other"   DeductibleFactor
  P4  207_ OR sewer special class, parent deductible N/A        DeductibleFactor
  P5  88_  OR EQ class "Z9"                                      EQClassToUse
  P6  35_  OR Business Income, all three options elected         MaxPeriodOfIndemnityFactor
  P7  120_ the chunk 11 golden policy (territory "Portland") in FL   RatingTerritoryGroupIFactor
  P8  168_ the chunk 13 five-record policy ("Portland") in VA        RatingTerritoryGroupIFactor
  P9  54_  OR Group II territory moved to "Portland" (OR files Entire State only)   BCEGFactor
  P10 42_  OR special class described with FL's own string "(Radio and TV)"     SpecialClassDescriptionConvertedOption
  P11 152_ CO terrorism, in effect, lowest tier (no wind hazard input)             GeographicWindHazardLevel
  P12 152_ SC terrorism, in effect, lowest tier                                    BCEGEQFactor
  P13-P17  45_ C6-14's other near-miss spellings of the tower description in OR  SpecialClassDescriptionConvertedOption

Run 2026-10-05: P1-P8 refused live at the same table and keys (P4 after sending DischargeLimitPD as a number).

Not probed: 46_'s Puerto Rico case (`ProtectionClassStatCode`, CW 3): no RaaS entitlement for PR.

    python scripts/cf/248_chunk28_c28-06_probes.py [--live] [--cases P1,P2]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

cmp = import_module("154_chunk13_rc5_fields_messages")
m207 = import_module("207_chunk21_rc1")
m88 = import_module("88_chunk10_c10-04_zero_cases")
m35 = import_module("35_chunk5_factor")
m114 = import_module("114_chunk11_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")
OUT = ROOT / "results" / "cf-raas"
P = m207.P


def portable(j):
    return m207.g19.with_cause(m207.g19.portable(j), "Special")


def condo(cont):
    def b():
        sub = portable("OR")
        pp = m207.rc1.node_dicts(sub)[P + "PersonalProperty"]
        pp[P + m207.OPT + "Table"] = {P + m207.OPT: [dict(cont, **{P + m207.LA: {}, P + m207.MRP: {}})]}
        return sub
    return b


def sewer_na():
    rec = "DischargeFromSewerDrainOrSumpNotFloodReltdSpclClass"
    sub = portable("OR")
    m207.rc1.node_dicts(sub)[P + "SpecialClass"]["Deductible"] = "Not Applicable"
    m207.r2.put(sub, rec, {m207.SEWER[rec]: "25000"})
    return sub


def g2_portland():
    sub = g7.submission("Basic")
    (sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
     ["CommercialPropertyLocation"][0])["BasicGroupIIRatingTerr"] = "Portland"
    return sub


def fl_description(desc="Towers - Broadcasting Antennas (Radio and TV)"):
    def b():
        sub = g6.submission("Basic")
        g6.item(sub)["ClassDescription"] = desc
        return sub
    return b


NEAR = [("P13", "case", "towers - broadcasting antennas (cell, radio and tv)"),
        ("P14", "one trailing space", g6.DESC + " "),
        ("P15", "'&' for 'and'", "Towers - Broadcasting Antennas (Cell, Radio & TV)"),
        ("P16", "one doubled space", "Towers  - Broadcasting Antennas (Cell, Radio and TV)"),
        ("P17", "an en dash", "Towers – Broadcasting Antennas (Cell, Radio and TV)")]


def terror(j):
    def b():
        m152 = import_module("152_chunk13_rc4_states")
        plan, _, _ = m152.territory_plan(m152.book_for(j, m152.ASOF), j)
        return m152.state_sub(j, plan[0]["territory"])
    return b


def bi_all_three():
    sub = m35.chunk5.submission("Basic")
    over = next(o for n, o, *_ in m35.CASES if n == "all three elected at once")
    m35.zeros5._bi(sub).update(over)
    return sub


CASES = {
    "P1": ("FL", "207_ FL portable policy (EQ on the special class)", lambda: portable("FL"), "BldgHeightFactor"),
    "P2": ("OR", "207_ condo options, loss assessment limit '10000'",
           condo({"LossAssessmentLimit": "10000", "LossAssessmentDeductible": "250"}), "LossAssessmentLimitConverted"),
    "P3": ("OR", "207_ condo options, LA 10,000, deductible 'All Other'",
           condo({"LossAssessmentLimit": "10,000", "LossAssessmentDeductible": "All Other"}), "DeductibleFactor"),
    "P4": ("OR", "207_ sewer special class, parent deductible 'Not Applicable'", sewer_na, "DeductibleFactor"),
    "P5": ("OR", "88_ EQ class 'Z9'", lambda: m88.submission({"EQClass": "Z9"}), "EQClassToUse"),
    "P6": ("OR", "35_ Business Income, all three options elected", bi_all_three, "MaxPeriodOfIndemnityFactor"),
    "P7": ("FL", "120_ the chunk 11 golden policy ('Portland') in FL", m114.submission, "RatingTerritoryGroupIFactor"),
    "P8": ("VA", "168_ the chunk 13 five-record policy ('Portland') in VA", grp.five, "RatingTerritoryGroupIFactor"),
    "P9": ("OR", "54_ Group II territory moved to 'Portland'", g2_portland, "BCEGFactor"),
    "P11": ("CO", "152_ CO terrorism in effect, lowest tier", terror("CO"), "GeographicWindHazardLevel"),
    "P12": ("SC", "152_ SC terrorism in effect, lowest tier", terror("SC"), "BCEGEQFactor"),
    "P10": ("OR", "42_ FL's own special class description in OR", fl_description(), "SpecialClassDescriptionConvertedOption"),
    **{k: ("OR", f"45_ near-miss description: {why}", fl_description(d), "SpecialClassDescriptionConvertedOption")
       for k, why, d in NEAR},
}


#: fields ISO's request schema types as integers that the tree builders carry as text (P4: ISO 400s on "25000")
INT_FIELDS = {"DischargeLimitPD"}


def ints(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in INT_FIELDS and isinstance(v, str) and v.isdigit():
                o[k] = int(v)
            else:
                ints(v)
    elif isinstance(o, list):
        for x in o:
            ints(x)
    return o


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = {k: v for k, v in CASES.items() if not a.cases or k in a.cases.split(",")}
    fail, reqs = [], {}
    for i, (cid, (j, label, build, table)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"ours {cid}")
        req = ints(cmp.state_req(j, build()))
        reqs[cid] = req
        try:
            cmp.rate(req)
            ours = "PRICES"
        except Exception as exc:
            mm = re.search(r"NO row in '(\w+)' for keys (\[[^]]*\])", str(exc))
            ours = f"REFUSES {mm.group(1)} {mm.group(2)}" if mm else f"raises {type(exc).__name__}: {str(exc)[:120]}"
        hit = ours.startswith(f"REFUSES {table} ")
        print(f"  {cid} {j} {label}: ours {ours}{'' if hit else '   <-- predicted REFUSES ' + table}")
        if not hit:
            fail.append(cid)
    if a.live:
        import raas as raas_mod
        os.environ.setdefault("RAAS_ENV_FILE", r"F:\Will_Dan_Collab_dev\.env")
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17:")
        for i, (cid, (j, label, build, table)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = reqs[cid]
            (OUT / f"chunk28_c28-06_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                body = str(exc.body)
                (OUT / f"chunk28_c28-06_{cid}_refusal.json").write_text(body, encoding="utf-8")
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", body)
                same = bool(mm) and mm.group(1) == table
                print(f"  {cid} ISO REFUSES {mm.group(0)[:200] if mm else body[:200]}"
                      f"   {'= ours' if same else '<-- not the table ours refuses on'}")
                if not same:
                    fail.append(f"{cid} live")
                continue
            (OUT / f"chunk28_c28-06_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            print(f"  {cid} ISO RATES -- ours refuses: the rule refuses too much here")
            fail.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC28-06 probes: {'ALL AS PREDICTED' if not fail else 'DIFFER: ' + ', '.join(fail)}  ({mm}m{s:02d}s)")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
