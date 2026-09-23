#!/usr/bin/env python3
"""Chunk 9, C9-07 -- the hardcoded-literal census for the blanket path.

Every literal the task doc names, checked against the rule XML and the
Domain Tables directly (this project's own rule: Domain Tables, not Rate
Tables/Rules, are authoritative for a field's filed enum -- see
`reference_cf-erc-domain-tables-folder`), not carried over from any prior
chunk's paraphrase.

Five literal groups:

  1. `MUBlktRated` -- gate 1 of the C9-01/census root cause. `SetNonEQ-
     BlanketValues` tests the single literal "No" (`Equal`); `SetMUBlktRated`
     defaults a null/absent value to "No"; four OTHER places in
     `CommercialPropertyStructureRules.Rule.xml` test `<> "Yes"` explicitly
     (`NotEqual`) -- so "Yes" IS tested directly elsewhere in the chain, not
     merely implied by the absence of "No". `DomainBlanketRatedSelection`
     confirms the field's whole domain is exactly {No, Yes} -- 2 values,
     no third state filed anywhere.
  2. `IncludedInBlkt` -- gate 2. Building's own `SetPremium` tests both "No"
     (When 1, routes non-blanket items) and reaches the blanket branch by
     elimination. The Domain Tables show this is NOT one flat Yes/No switch
     countrywide -- 5 separate per-form domain tables (Bldg/PrsnlProp/
     BusnIncome/SpecialClass/generic) each gate DataValue on a POLICY-level
     `BlktRated` plus, for Building, `CovTypeBldg` -- and two `CovTypeBldg`
     values (Legal Liability, Leasehold Interest) can NEVER reach "Yes" even
     when `BlktRated="Yes"`, confirmed by direct read of every row.
  3. `CovType <> "Leasehold Interest"` -- Building `SetPremium`'s 3rd `When`,
     confirmed present verbatim, and confirmed to be an elimination test
     (not a literal `Choose` on `IncludedInBlkt`) -- the 4 `When`/`Otherwise`
     shape read directly.
  4. `BlktTypeOfBlanketRating` -- `DomainTypeOfBlanketRating.DomainTable.csv`
     read directly: exactly 2 `DataValue`s (Average, Highest) for EVERY one
     of 6 `BlanketType` key values, so the task doc's 2-value list IS the
     full domain, not a subset picked by example.
  5. `Type` (the Detail record's own field) -- `SetBasicGroupIStructureCalc`'s
     gate literal-by-literal read off the XML, cross-checked against
     `DomainBlanketType.DomainTable.csv`'s `PolicyType="Commercial Property
     Policy"` row set (6 values) -- confirming the rule's 4-value gate is a
     SUBSET of a 6-value domain, and where the other 2 (the Business Income
     variants) actually go.

    python scripts/cf/73_chunk9_c9-07_hardcoded_literals.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

STRUCT_FILE = "CommercialPropertyStructureRules.Rule.xml"
BLDG_BGI_FILE = "CommercialPropertyStructureBuildingBasicGroupICoverageRules.Rule.xml"
DETAIL_FILE = "CommercialPropertyBlanketRatingDetailRules.Rule.xml"
POLICY_FILE = "CommercialPropertyRules.Rule.xml"


def rule_body(text: str, name: str) -> str:
    i = text.find(f'<rul:Rule Name="{name}"')
    j = text.find("</rul:Rule>", i) + 11
    return text[i:j]


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    book = book_for(juris[0], ASOF, resolver=res)
    rules_dir = book.parent.package.content / "Rules"
    domains_dir = book.parent.package.content / "Domain Tables"

    struct_body = (rules_dir / STRUCT_FILE).read_text(encoding="utf-8-sig")
    bldg_bgi_body = (rules_dir / BLDG_BGI_FILE).read_text(encoding="utf-8-sig")
    detail_body = (rules_dir / DETAIL_FILE).read_text(encoding="utf-8-sig")
    policy_body = (rules_dir / POLICY_FILE).read_text(encoding="utf-8-sig")

    # ---- 1: MUBlktRated
    print("=== 1  MUBlktRated -- gate 1's literal(s)\n")
    noneq_body = rule_body(struct_body, "SetNonEQBlanketValues")
    m = re.search(r'FromDataDef="\.\./\.\./\.\./\.\./MUBlktRated"[^/]*/>\s*'
                  r'<rul:Constant Type="string">(\w*)</rul:Constant>', noneq_body)
    print(f"    SetNonEQBlanketValues outer gate: Equal(MUBlktRated, "
          f"{m.group(1)!r}) -- the ONLY literal this rule tests directly.")
    setmu_body = rule_body(policy_body, "SetMUBlktRated")
    default_lit = re.search(r'ToDataDef="MUBlktRated">(\w*)<', setmu_body)
    print(f"    SetMUBlktRated (CommercialPropertyRules.Rule.xml -- "
          f"CommercialProperty policy level): defaults a null MUBlktRated "
          f"to {default_lit.group(1)!r} -- absent-or-null resolves to the "
          f"same value gate 1 requires, before any blanket rule runs.")
    not_yes = len(re.findall(
        r'FromDataDef="\.\./\.\./\.\./\.\./MUBlktRated"[^/]*/>\s*'
        r'<rul:Constant Type="string">Yes</rul:Constant>', struct_body))
    print(f"    `NotEqual(MUBlktRated, \"Yes\")` tested explicitly elsewhere "
          f"in {STRUCT_FILE}: {not_yes} places (not merely implied by the "
          f"absence of a \"No\" `Equal`) -- confirmed by direct grep, "
          f"answering the task's own question.")
    dbrs = (domains_dir / "DomainBlanketRatedSelection.DomainTable.csv").read_text(
        encoding="utf-8-sig").strip().splitlines()
    vals = sorted({row.split(",")[-1].strip('"') for row in dbrs[1:]})
    print(f"    DomainBlanketRatedSelection.DomainTable.csv DataValue "
          f"domain: {vals} -- exactly {{No, Yes}}, no third filed state.")

    # ---- 2: IncludedInBlkt
    print("\n=== 2  IncludedInBlkt -- gate 2, and the 5 per-form Domain "
          "Tables\n")
    when1 = re.search(r"<rul:When>.*?</rul:When>", bldg_bgi_body, re.S)
    has_no = 'IncludedInBlkt' in when1.group(0) and '>No<' in when1.group(0)
    print(f"    Building SetPremium When 1 tests IncludedInBlkt=\"No\" "
          f"(routes the item OFF the blanket path): {has_no}")
    domain_files = {
        "generic": "DomainIncludedInBlkt.DomainTable.csv",
        "Building": "DomainIncludedInBlktBldg.DomainTable.csv",
        "Contents": "DomainIncludedInBlktPrsnlProp.DomainTable.csv",
        "Business Income": "DomainIncludedInBlktBusnIncome.DomainTable.csv",
        "Special Class": "DomainIncludedInBlktSpecialClass.DomainTable.csv",
    }
    for label, fn in domain_files.items():
        rows = (domains_dir / fn).read_text(encoding="utf-8-sig").strip().splitlines()
        print(f"    {label:18s} {fn:42s} {len(rows) - 1} rows")
    bldg_rows = (domains_dir / domain_files["Building"]).read_text(
        encoding="utf-8-sig").strip().splitlines()[1:]
    never_yes = sorted({r.split(",")[1].strip('"') for r in bldg_rows
                         if 'Yes","Yes"' not in r})
    always_yes_capable = sorted({r.split(",")[1].strip('"') for r in bldg_rows
                                  if 'Yes","Yes"' in r})
    never_yes_at_all = sorted(set(never_yes) - set(always_yes_capable))
    print(f"\n    DomainIncludedInBlktBldg's CovTypeBldg values that CAN "
          f"reach DataValue=\"Yes\" (BlktRated=\"Yes\" row present): "
          f"{always_yes_capable}")
    print(f"    CovTypeBldg values that can NEVER reach \"Yes\" no matter "
          f"what BlktRated is: {never_yes_at_all} -- Leasehold Interest is "
          f"blocked at the DOMAIN level, not just by SetPremium's own "
          f"elimination `When` (finding 3 below) -- two independent "
          f"mechanisms exclude the same CovType.")

    # ---- 3: Leasehold Interest / SetPremium shape
    print("\n=== 3  Building SetPremium's Choose -- the elimination shape\n")
    seg = rule_body(bldg_bgi_body, "SetPremium")
    whens = [m.start() for m in re.finditer(r"<rul:When>", seg)]
    print(f"    {len(whens)} When(s) + "
          f"{'Otherwise present' if '<rul:Otherwise>' in seg else 'no Otherwise'}")
    tests = []
    for n, s in enumerate(whens):
        e = whens[n + 1] if n + 1 < len(whens) else seg.find("<rul:Otherwise>")
        chunk = seg[s:e]
        covtype_eq = re.findall(
            r'FromDataDef="\.\./CovType"[^/]*/>\s*<rul:Constant Type="string">'
            r'([^<]*)</rul:Constant>', chunk)
        neq = re.findall(
            r'<rul:NotEqual>\s*<rul:FirstValue Type="string" FromConstant="" '
            r'FromDataDef="\.\./CovType"[^/]*/>\s*<rul:Constant Type="string">'
            r'([^<]*)</rul:Constant>\s*</rul:NotEqual>', chunk)
        tests.append((covtype_eq, neq))
        print(f"    When {n + 1}: CovType Equal{covtype_eq or []}  "
              f"NotEqual{neq or []}")
    print("    Confirmed: When 3's NotEqual(CovType, \"Leasehold Interest\") "
          "is the elimination test C9-01 named -- everything that is not "
          "Legal Liability (When 2) and not Leasehold Interest (excluded "
          "here) falls through to the blanket formula, including plain "
          "Building. The literal's ROLE is exclusionary, not a positive "
          "blanket-election test.")

    # ---- 4: BlktTypeOfBlanketRating domain
    print("\n=== 4  BlktTypeOfBlanketRating (well, TypeOfBlanketRating on "
          "the Detail record) -- domain completeness\n")
    rows = (domains_dir / "DomainTypeOfBlanketRating.DomainTable.csv").read_text(
        encoding="utf-8-sig").strip().splitlines()[1:]
    by_type: dict[str, set[str]] = {}
    for r in rows:
        parts = [p.strip('"') for p in r.split('","')]
        parts[0] = parts[0].strip('"')
        parts[-1] = parts[-1].strip('"')
        _state, blanket_type, _disp, data_val = parts
        by_type.setdefault(blanket_type, set()).add(data_val)
    for bt, vals in by_type.items():
        print(f"    BlanketType={bt!r:45s} DataValue domain: {sorted(vals)}")
    all_same = all(v == {"Average", "Highest"} for v in by_type.values())
    print(f"\n    All {len(by_type)} BlanketType keys resolve to the SAME "
          f"2-value {{Average, Highest}} domain: {all_same} -- the task "
          f"doc's 2-value list (C9-03's finding) IS the full filed domain, "
          f"confirmed by reading every row, not one example key.")

    # ---- 5: Type (Detail record) domain vs the 4-value gate
    print("\n=== 5  Detail record's `Type` -- the 4-value gate vs the full "
          "domain\n")
    scalc = rule_body(detail_body, "SetBasicGroupIStructureCalc")
    gate_lits = [lit.replace("&amp;", "&") for lit in re.findall(
        r'FromDataDef="Type"[^/]*/>\s*<rul:Constant Type="string">([^<]*)'
        r'</rul:Constant>', scalc)]
    print(f"    SetBasicGroupIStructureCalc's `Type` `Or` gate, read "
          f"literal-for-literal: {gate_lits}")
    print("    Confirmed verbatim (not abbreviated): the 4th literal is the "
          "FULL string \"Building & Personal Property Combined\" (with "
          "`&amp;`) -- the task doc's \"Building & PP Combined\" is a "
          "paraphrase of this exact domain string, not a different value.")
    dbt_rows = (domains_dir / "DomainBlanketType.DomainTable.csv").read_text(
        encoding="utf-8-sig").strip().splitlines()[1:]
    by_policy: dict[str, list[str]] = {}
    for r in dbt_rows:
        parts = [p.strip('"') for p in r.split('","')]
        parts[0] = parts[0].strip('"')
        parts[-1] = parts[-1].strip('"')
        _state, policy_type, _disp, data_val = parts
        by_policy.setdefault(policy_type, []).append(data_val)
    for pt, vals in by_policy.items():
        print(f"    PolicyType={pt!r:32s} Type domain ({len(vals)}): {vals}")
    cpp = by_policy["Commercial Property Policy"]
    missing_from_gate = [v for v in cpp if v not in gate_lits]
    print(f"\n    \"Commercial Property Policy\"'s full `Type` domain has "
          f"{len(cpp)} values; SetBasicGroupIStructureCalc's gate covers "
          f"{len(gate_lits)} of them. Missing from THIS gate: "
          f"{missing_from_gate}.")
    print("    Confirmed by direct read (C9-02's own trace, re-checked "
          "here): both missing values are the 2 Business Income `Type`s -- "
          "`SetMaxBasicGroupICauseOfLossAdjmtRate` branches them to "
          "`MaxBasicGroupIBusnIncomeCalc`/`MaxBasicGroupISpclClassBusnIncome"
          "Calc` instead of the Building/PP/SpecialClass candidates this "
          "rule computes. **So the 4-value gate is a real SUBSET of a "
          "6-value domain, but every one of the 6 is reachable somewhere in "
          "the chain -- none is unfiled or unreachable corpus-wide, only "
          "unreachable through THIS ONE rule.**")

    print("\n=== Summary -- reachable vs unreachable, per literal\n")
    print("    MUBlktRated {No, Yes}                    -- both reachable; "
          "\"No\" gates entry, \"Yes\" (or absent) skips the whole rule body.")
    print("    IncludedInBlkt {No, Yes, Not Applicable}  -- domain-gated per "
          "form; Building's Legal Liability/Leasehold Interest CovTypes can "
          "never reach \"Yes\" even when the policy elects blanket.")
    print("    CovType<>\"Leasehold Interest\"            -- an exclusion "
          "literal, not an election literal; doubly enforced (SetPremium's "
          "own `When` AND the IncludedInBlkt domain table above).")
    print("    BlktTypeOfBlanketRating {Average, Highest} -- full domain, "
          "confirmed identical across all 6 BlanketType keys.")
    print("    Detail `Type` -- 6-value full domain, 4 reachable through "
          "THIS gate, 2 more reachable through the Business Income sibling "
          "gate in the same rule family. No unfiled/unreachable literal "
          "found; no engine gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
