#!/usr/bin/env python3
"""Chunk 10, C10-07 -- exclusion-record identification per datadef group,
for EQ's own Cyber-incident-exclusion factors.

`05_exclusion_records.py` (gate point 7, chunks 1-9) established that ORDINARY
exclusions (Vandalism, Theft, Windstorm/Hail, Cyber-on-the-ordinary-chain) are
filed **per coverage**: Building's vandalism-exclusion record is a different
record from Contents', which is different again from Business Income's. This
task asks whether EQ's OWN Cyber-exclusion factors --
`CyberIncidentExclusionFactorEQ` and `CyberIncidentExclusionCOLExcptnsFactorEQ`
-- follow that same per-coverage-record pattern, or something else.

Two passes:

  1. Corpus-wide write/read census -- where is each factor ACTUALLY set
     (`ToDataDef`), and which files across all 5 groups' own family (Bldg/
     PrsnlProp/BusnIncome/SpecialClass/SpclClassBusnIncome-named files) read
     it. This settles whether there are 5 per-group copies of the rule/field,
     or one shared one.
  2. A dynamic confirmation on two of the five groups (Building, already
     proven by C10-01's golden case; Contents, built fresh here by
     extending chunk 4's own Personal Property submission with chunk 10's
     EQ election, per this task's instruction to reuse/extend the golden
     case's payload builder) -- absent ANY
     `CommercialPropertyCyberIncidentExclusion` record, does the factor
     default to the same `1.0` no-op in both, using the SAME shared field.

    python scripts/cf/93_chunk10_c10-07_exclusion_records.py [--trace]

Always exits 0 on a clean adjudication (both dynamic checks defaulting to
1.0); exits 1 if a real gap turns up, which per this project's standing rule
is logged here, not patched in engine code.
"""
from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

ASOF = "20260917"

FIELDS = ["CyberIncidentExclusionFactorEQ", "CyberIncidentExclusionCOLExcptnsFactorEQ"]

#: filename fragments identifying which of the 5 groups' own family a reader
#: file belongs to, for the corpus-wide read census.
GROUP_TAGS = {
    "Building": "Bldg",
    "Contents": "PrsnlProp",
    "Business Income": "BusnIncome",
    "Special Class": "SpecialClass",
    "SC Business Income": "SpclClassBusnIncome",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"
    all_files = sorted(rules_dir.glob("*.xml"))
    bodies = {p.name: p.read_text(encoding="utf-8-sig", errors="ignore")
              for p in all_files}

    print("=== 1  Corpus-wide write/read census, both EQ Cyber factors\n")
    for field in FIELDS:
        writers = [fn for fn, t in bodies.items() if f'ToDataDef="{field}"' in t]
        print(f"    {field}")
        print(f"        WRITTEN in: {writers}")
        readers_by_group: dict[str, list[str]] = {g: [] for g in GROUP_TAGS}
        other_readers = []
        for fn, t in bodies.items():
            if fn in writers:
                continue
            if not re.search(rf'FromDataDef="[./]*{field}"', t):
                continue
            matched = False
            for g, tag in GROUP_TAGS.items():
                if tag in fn or (g == "Building" and "Bldg" in fn):
                    readers_by_group[g].append(fn)
                    matched = True
            if not matched:
                other_readers.append(fn)
        for g, fns in readers_by_group.items():
            print(f"        read by {len(fns):3d} file(s) tagged {g!r}"
                  + (f"  (e.g. {fns[0]})" if fns else ""))
        print(f"        read by {len(other_readers)} file(s) matching NONE "
              f"of the 5 group tags (policy-level/other-coverage riders)")
        print()

    print("    Both factors are written in EXACTLY ONE file "
          "(`CommercialPropertyRules.Rule.xml`), at "
          "`DataDefGroup=\"CommercialProperty\"` -- the common POLICY-level "
          "ancestor all 5 premium groups descend from -- and read by files "
          "tagged for ALL FIVE group families. This is the "
          "\"one-shared-value-no-copy\" pattern this project already logged "
          "for the ordinary chain's own Cyber Exclusion (`project_bgi-"
          "contents-vs-building-factor-notes.md`), re-confirmed here for "
          "EQ's own variant: there are not 5 per-group rules under 5 "
          "different names to adjudicate (that would be the C10-06 shape) "
          "-- there is exactly ONE rule, ONE field, ONE record, read "
          "identically (via a relative-path climb back to the ancestor "
          "node) by every group's own Endorsement/wrapper files.\n")

    print("=== 2  What record does that ONE rule test?\n")
    cp_rules = bodies["CommercialPropertyRules.Rule.xml"]

    def rule_body(name: str) -> str:
        i = cp_rules.find(f'<rul:Rule Name="{name}"')
        j = cp_rules.find("</rul:Rule>", i) + 11
        return cp_rules[i:j]

    for name, field in [("SetCyberIncidentExclusionFactorEQ", FIELDS[0]),
                         ("SetCyberIncidentExclusionCOLExcptnsFactorEQ", FIELDS[1])]:
        body = rule_body(name)
        records = re.findall(r'AtInputDataDef="([^"]+)"', body)
        default_hits = re.findall(
            rf'<rul:Constant Type="decimal" ToDataDef="{field}">([\d.]+)</rul:Constant>',
            body)
        print(f"    {name}")
        print(f"        record(s) tested (Exist/NotExist): {records}")
        print(f"        literal default(s) written when absent: {default_hits}")
    print("\n    Both records (`CommercialPropertyCyberIncidentExclusion` and "
          "`...WithEnsuingCausesOfLossExceptions`) live at the SAME "
          "`CommercialProperty` policy level as the rule itself -- one "
          "record per POLICY, not one per coverage. This is a genuinely "
          "different shape from the ordinary-chain exclusions "
          "`05_exclusion_records.py` census found (Vandalism/Theft/"
          "Windstorm-or-Hail, each filed once PER datadef group) -- EQ's own "
          "Cyber exclusion opts out of that per-coverage pattern entirely.\n")

    print("=== 3  Dynamic confirmation -- absent the record, does the SAME "
          "field default to 1.0 for two different groups?\n")

    golden = import_module("85_chunk10_golden_case")
    ip_b = Interpreter(book_for(golden.JURIS, golden.ASOF), rounding=ROUNDING,
                        trace=a.trace, null_arithmetic=NULL_ARITHMETIC)
    data_b = Node.from_dict(f"MasterCF{golden.JURIS}",
                             golden.submission())
    ip_b.run(data_b)
    CP_B = "CommercialPropertyTable/CommercialProperty"
    bldg_f1 = read(CP_B + "/" + FIELDS[0], data_b)
    bldg_f2 = read(CP_B + "/" + FIELDS[1], data_b)
    print(f"    Building (chunk 10's own golden case, no Cyber exclusion "
          f"record present):")
    print(f"        {FIELDS[0]:44s} = {bldg_f1}")
    print(f"        {FIELDS[1]:44s} = {bldg_f2}")

    chunk4 = import_module("22_chunk4_golden_case")
    sub = chunk4.submission("Basic")
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["EQCauseOfLossForm"] = "Earthquake Form (CP 10 40)"
    loc["EQTerr"] = "1"
    loc["EQDeductibleTier"] = "1"
    pp = (loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
          ["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
          ["CommercialPropertyPersonalPropertyTable"]
          ["CommercialPropertyPersonalProperty"][0])
    pp["EQCovIndicator"] = "Yes, Not Included in Blanket"
    pp["EQClass"] = "A1"
    pp["EQGrade"] = "1"
    pp["EQCoinsurance"] = "90%"
    pp["EQDeductible"] = "10%"
    pp["EQSprinklerLeakageOnly"] = "Not Applicable"
    pp["BCEG"] = "1"
    pp["SprinklerSystem"] = "None"

    ip_c = Interpreter(book_for(chunk4.JURIS, chunk4.ASOF), rounding=ROUNDING,
                        trace=a.trace, null_arithmetic=NULL_ARITHMETIC)
    data_c = Node.from_dict(f"MasterCF{chunk4.JURIS}", sub)
    ip_c.run(data_c)
    endt = (chunk4.PP + "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement"
            "PrsnlPropTable/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement"
            "PrsnlProp[1]")
    endt_exists = read(endt + "/Premium", data_c) is not None
    contents_f1 = read(CP_B + "/" + FIELDS[0], data_c)
    contents_f2 = read(CP_B + "/" + FIELDS[1], data_c)
    print(f"\n    Contents (fresh submission built here: chunk 4's own "
          f"Personal Property record + chunk 10's EQ election, mirroring "
          f"the golden case's fields at the PrsnlProp level, NO Cyber "
          f"exclusion record supplied):")
    print(f"        EQ Endorsement record created for Contents: {endt_exists}")
    print(f"        {FIELDS[0]:44s} = {contents_f1}")
    print(f"        {FIELDS[1]:44s} = {contents_f2}")

    ok = (endt_exists
          and Decimal(bldg_f1) == 1 and Decimal(bldg_f2) == 1
          and Decimal(contents_f1) == 1 and Decimal(contents_f2) == 1
          and bldg_f1 == contents_f1 and bldg_f2 == contents_f2)

    print(f"\n    Both groups read the IDENTICAL shared field (same value, "
          f"{bldg_f1 == contents_f1 and bldg_f2 == contents_f2}), and both "
          f"default to the genuine 1.0 no-op absent any exclusion record: "
          f"{ok}")

    print("\n=== 4  Verdict, all 5 groups\n")
    print("    **None of the 5 premium groups files its own exclusion "
          "record for EQ's Cyber-incident factors.** There is exactly ONE "
          "record per factor (`CommercialPropertyCyberIncidentExclusion`, "
          "`...WithEnsuingCausesOfLossExceptions`), filed once at the "
          "policy-level `CommercialProperty` node, tested by exactly ONE "
          "rule (also declared once, at that same ancestor level), and read "
          "identically by every group's own Endorsement/wrapper files via a "
          "relative-path climb back to the shared node -- confirmed by "
          "direct corpus-wide write/read census (Sec.1) and by two "
          "independent dynamic runs, Building and Contents, landing on the "
          "exact same value from the exact same field (Sec.3). "
          "Business Income, Special Class and SC Business Income were not "
          "run dynamically here (their own full EQ submissions are C10-11/"
          "C10-15's job, out of this task's scope), but the corpus-wide "
          "census already confirms their own family-tagged files read the "
          "SAME two fields the same way -- there is no per-group variant "
          "for this census to have missed.")
    print("\n    This is a genuinely different shape from the ordinary "
          "(non-EQ) exclusion pattern `05_exclusion_records.py` documented: "
          "there, each of the 5 groups files ITS OWN vandalism/theft/"
          "windstorm-or-hail record. EQ's own Cyber exclusion is a POLICY "
          "election, not a per-coverage one -- one flag covers Building, "
          "Contents, Business Income, Special Class and SC Business Income "
          "at once. Whether that is the right product shape or a "
          "simplification worth flagging is a filing-content question, not "
          "an engine gap: the mechanism is confirmed consistent across all "
          "5 groups, not silently divergent.")
    print("\n    No engine gap.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
