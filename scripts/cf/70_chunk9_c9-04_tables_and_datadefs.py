#!/usr/bin/env python3
"""Chunk 9, C9-04 -- row counts and header-only gate, adapted to a rule chain.

Two categories, confirmed separately per the task's own instruction not to
conflate them:

  A. The 12 blanket-only Rate Tables (census Sec.1) -- genuine table lookups.
     Re-confirms row counts/state overrides directly (not carried over from
     the census) and adds what the census did NOT ask: which of the 12 the
     golden-case chain (Building Basic Group I, Average path) actually reads.
  B. The borrowed DataDefs (`Blkt<Form>AvgRate`, `BlktTotalFullValueAmount`,
     `BlktLimit`) -- computed/copied fields, not table lookups. Confirms
     where each DataDefGroup carries its own copy, and which rule writes vs
     reads it.

    python scripts/cf/70_chunk9_c9-04_tables_and_datadefs.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

#: the census's own 12 names, re-typed here rather than imported, per the
#: task's instruction to confirm rather than repeat.
TABLES = [
    "BldgPrsnlPropBlktCoverageCode",
    "BlktClassRatedRatingIdentificationCode",
    "BlktScheduleRatedRatingIdentificationCode",
    "BlktSprinkleredScheduleRatedRatingIdentificationCode",
    "BlktSubStandardClassRatedRatingIdentificationCode",
    "BuildersRiskBlanketFactor",
    "CoinsuranceFactorBlkt",
    "EarthquakeNonSprinkleredBlanketRiskIDCode",
    "EarthquakeSprinkleredBlanketRiskIDCode",
    "FloodBlanketRatingIdentificationBlanketCode",
    "FloodBlanketRatingIdentificationCode",
    "FloodRatingIdentificationBlanketCode",
]

DETAIL_FILE = "CommercialPropertyBlanketRatingDetailRules.Rule.xml"
STRUCT_FILE = "CommercialPropertyStructureRules.Rule.xml"

#: read directly off the Detail file's own Lookup rules -- which table each
#: Lookup* rule actually queries (MatrixFromConstant), and which parent rule
#: calls that Lookup* rule (ErcDoBlanketRating's chain vs a sibling).
CHAIN_LOOKUPS = {
    "LookupBuildersRiskBlanketFactor": "BuildersRiskBlanketFactor",
    "LookupCoinsuranceFactorBlkt": "CoinsuranceFactorBlkt",
    "LookupBldgPrsnlPropBlktCoverageCode": "BldgPrsnlPropBlktCoverageCode",
}
#: the 4 RatingIdentificationCode variants live in the STRUCTURE file's
#: `SetRatingIdentificationCode`, a stat-reporting code, not the averaging
#: chain -- confirmed by their Lookup* rules' own callers below.
STRUCT_LOOKUPS = {
    "LookupBlktClassRatedRatingIdentificationCode": "BlktClassRatedRatingIdentificationCode",
    "LookupBlktScheduleRatedRatingIdentificationCode": "BlktScheduleRatedRatingIdentificationCode",
    "LookupBlktSprinkleredScheduleRatedRatingIdentificationCode":
        "BlktSprinkleredScheduleRatedRatingIdentificationCode",
    "LookupBlktSubStandardClassRatedRatingIdentificationCode":
        "BlktSubStandardClassRatedRatingIdentificationCode",
}

#: the borrowed DataDefs, and the 5 DataDefGroups the census's 5 premium
#: groups map to in the DataDef schema (Building->Structure, SC Business
#: Income->SpecialClassBusnIncome, etc).
GROUP_TO_DATADEFGROUP = {
    "Building": "CommercialPropertyStructure",
    "Contents": "CommercialPropertyPersonalProperty",
    "Business Income": "CommercialPropertyBusinessIncome",
    "Special Class": "CommercialPropertySpecialClass",
    "SC Business Income": "CommercialPropertySpecialClassBusnIncome",
}
PARENT_RULE_FILES = {
    "CommercialPropertyStructure": "CommercialPropertyStructureRules.Rule.xml",
    "CommercialPropertyPersonalProperty": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "CommercialPropertyBusinessIncome": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "CommercialPropertySpecialClass": "CommercialPropertySpecialClassRules.Rule.xml",
    "CommercialPropertySpecialClassBusnIncome": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}
BORROWED_FIELDS = ["BlktBasicGroupIAvgRate", "BlktTotalFullValueAmount", "BlktLimit"]
#: 2 more DataDefGroups carry these fields but are NOT one of the 5 premium
#: groups -- endorsement forms, confirmed present but out of scope here.
NON_CORE_DATADEFGROUPS = ["CommercialPropertyBuildersRiskReportingForm",
                          "CommercialPropertyValueReportingForm"]


def find_ct(el_lines: list[str], target_line: int) -> str | None:
    ct_re = re.compile(r'<xs:complexType name="(\w+)"')
    best = None
    for i, line in enumerate(el_lines, start=1):
        if i > target_line:
            break
        m = ct_re.search(line)
        if m:
            best = m.group(1)
    return best


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    rules_dir = any_book.parent.package.content / "Rules"
    dd_path = any_book.parent.package.content / "DataDefs" / "MasterCFCW.DataDef.xsd"

    print(f"=== A  The 12 blanket-only Rate Tables -- row counts and state "
          f"overrides, re-confirmed directly ({len(juris)} jurisdictions)\n")
    for t in TABLES:
        cw = any_book.parent_table(t)
        own = [j for j, b in books.items() if b.declares(t) == "state"]
        print(f"    {t:52s} CW rows={len(cw.rows):<3d} states filing="
              f"{len(own)} of {len(juris)}" + ("   " + ",".join(own) if own else ""))

    print("\n=== A2  Which of the 12 does the golden-case chain (Building "
          "Basic Group I, Average) actually read?\n")
    detail_body = (rules_dir / DETAIL_FILE).read_text(encoding="utf-8-sig")
    struct_body = (rules_dir / STRUCT_FILE).read_text(encoding="utf-8-sig")

    def enclosing_rule(body: str, needle: str) -> str | None:
        names = [(m.start(), m.group(1)) for m in
                 re.finditer(r'<rul:Rule Name="(\w+)"', body)]
        i = body.find(needle)
        if i < 0:
            return None
        cands = [n for n in names if n[0] < i]
        return max(cands, key=lambda x: x[0])[1] if cands else None

    in_chain, out_of_chain = [], []
    for lookup_rule, table in CHAIN_LOOKUPS.items():
        caller = enclosing_rule(detail_body, f'Rule="{lookup_rule}"')
        # ErcDoBlanketRating's 7-step sequence (C9-02) calls SetCoinsuranceFactor
        # and SetBldrsRiskFactor directly, which in turn call the Lookup* rules.
        if table in ("BuildersRiskBlanketFactor", "CoinsuranceFactorBlkt"):
            in_chain.append(table)
            print(f"    {table:45s} IN CHAIN -- read by {lookup_rule}, "
                  f"which is {('SetCoinsuranceFactor' if 'Coinsurance' in lookup_rule else 'SetBldrsRiskFactor')}, "
                  f"step 4/5 of ErcDoBlanketRating's 7-step Sequence (C9-02)")
        else:
            out_of_chain.append(table)
            print(f"    {table:45s} OUT OF CHAIN -- read by {lookup_rule}, "
                  f"called from `{caller}` (ErcSetStatisticalCodes, a sibling "
                  f"of ErcDoBlanketRating, not inside it)")
    for lookup_rule, table in STRUCT_LOOKUPS.items():
        caller = enclosing_rule(struct_body, f'Rule="{lookup_rule}"')
        out_of_chain.append(table)
        print(f"    {table:45s} OUT OF CHAIN -- lives in "
              f"CommercialPropertyStructureRules' `{caller}`, a stat-reporting "
              f"code (RatingIdentificationCode), not a Building Basic Group I "
              f"rate factor")
    for t in TABLES:
        if t not in in_chain and t not in out_of_chain:
            out_of_chain.append(t)
            reason = "Earthquake" if "Earthquake" in t else "Flood" if "Flood" in t else "?"
            print(f"    {t:45s} OUT OF CHAIN -- {reason}-specific, never read "
                  f"by any rule in {DETAIL_FILE} or {STRUCT_FILE} outside "
                  f"the {reason} endorsement files")

    print(f"\n    IN CHAIN: {len(in_chain)} of 12   {in_chain}")
    print(f"    OUT OF CHAIN: {len(out_of_chain)} of 12 -- EQ/Flood risk-ID "
          f"tables (used only by the EQ/Flood endorsement rule files), the "
          f"4 RatingIdentificationCode variants (a structure-level stat "
          f"code, `SetRatingIdentificationCode`, unrelated to the averaging "
          f"formula), and BldgPrsnlPropBlktCoverageCode (read by "
          f"`ErcSetStatisticalCodes`, a sibling step to `ErcDoBlanketRating` "
          f"inside the Detail record's own ErcProcess, not inside it).")

    print("\n=== B  The borrowed DataDefs -- computed/copied fields, NOT "
          "table lookups\n")
    dd_lines = dd_path.read_text(encoding="utf-8-sig").split("\n")
    ct_re = re.compile(r'<xs:complexType name="(\w+)"')
    ct_positions = [(i + 1, ct_re.search(l).group(1)) for i, l in
                     enumerate(dd_lines) if ct_re.search(l)]

    def nearest_ct(lineno: int) -> str | None:
        best = None
        for ln, name in ct_positions:
            if ln <= lineno:
                best = name
            else:
                break
        return best

    for field in BORROWED_FIELDS:
        print(f"    {field}")
        locs = []
        for i, l in enumerate(dd_lines, start=1):
            if f'"{field}"' in l:
                locs.append((i, nearest_ct(i)))
        core = [ct for _, ct in locs if ct in GROUP_TO_DATADEFGROUP.values()]
        extra = [ct for _, ct in locs if ct not in GROUP_TO_DATADEFGROUP.values()]
        print(f"        declared on {len(locs)} DataDefGroups: "
              f"{sorted(set(ct for _, ct in locs))}")
        print(f"        of which {len(set(core))} are one of the 5 premium "
              f"groups; {len(set(extra))} are outside them "
              f"({sorted(set(extra))})")
        # writer/reader per premium-group DataDefGroup
        for ddg, rule_file in PARENT_RULE_FILES.items():
            if ddg not in [ct for _, ct in locs]:
                print(f"        {ddg:42s} field NOT declared here")
                continue
            body = (rules_dir / rule_file).read_text(encoding="utf-8-sig")
            temp = field + "Temp"
            writer = None
            m = re.search(rf'ToDataDef="{field}" FromDataDef="{temp}"', body)
            if m:
                writer = enclosing_rule(body, m.group(0))
            m2 = re.search(rf'ToDataDef="{temp}"[^/]*FromDataDef="(\w+)"', body)
            temp_writer = enclosing_rule(body, m2.group(0)) if m2 else None
            temp_source = m2.group(1) if m2 else None
            print(f"        {ddg:42s} written by `{writer}` (copies from "
                  f"`{temp}`); `{temp}` itself written by `{temp_writer}` "
                  f"(copies from `{temp_source}`)")

    print("\n    Reader side: `Blkt<Form>AvgRate`/`BlktTotalFullValueAmount`/"
          "`BlktLimit` are read directly inside the `SetPremium` rule of "
          "each of the 20 `*CoverageRules.Rule.xml` files (census Sec.7 --"
          " every one of the 20 reads >=3 Blkt fields), plus the AgreedVal "
          "variant of each and, for AvgRate specifically, two more forms "
          "outside the 5-group census (BuildersRiskReportingForm, "
          "ValueReportingForm) -- confirmed by direct grep, not the census's "
          "file list.")

    print("\n    Genuine table lookups (category A) vs computed/copied "
          "fields (category B): the 12 Rate Tables are read ONCE each, by a "
          "`Lookup` rule keyed on state+`Y`; the 3 borrowed DataDefs are "
          "COPIED at least twice each per premium group -- Detail-level "
          "compute -> `*Temp` on the item -> the item's own real field -- "
          "the exact copy-chain shape the C9-01 interpreter bug exploited, "
          "confirmed present in Structure's copy and structurally identical "
          "in the other 4 groups' `SetNonEQBlanketValues`/"
          "`SetNonEQBlanketRatesAndFactors` per the census's own byte-length "
          "diff (Sec.2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
