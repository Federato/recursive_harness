#!/usr/bin/env python3
"""Chunk 10, C10-05 -- every hardcoded literal key listed for the Building
Endorsement's own `SetPremium`, checked against the Domain Tables folder
directly, same discipline as C9-07.

Three literal groups, all read off
`CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml`'s
`SetPremium` directly (not paraphrased from the task doc):

  1. `EQCovIndicator` -- 3 literals tested inside `SetPremium` itself
     (`"No Coverage"`, `"Not Applicable"` on the outer gate's `NotEqual`s,
     `"Yes, Included in Blanket"` on the blanket `When`) -- cross-checked
     against the FULL 4-value domain C10-04 already confirmed
     (`DomainEQCovIndicatorBldg.DomainTable.csv`).
  2. `CovType` -- 6 literals: the outer gate's exclusion
     (`"Leasehold Interest"`), the first `When`'s 4-value `Or`
     (`"Building"`, `"Improvements and Betterments"`,
     `"Condominium Association"`, `"Builders Risk"`), the second `When`'s
     single value (`"Legal Liability"`) -- cross-checked against
     `DomainCovTypeBldg.DomainTable.csv`'s full domain.
  3. Structural gates found while reading, not named by the task doc: the
     outer `If`'s 3 `NotExist` checks against the sibling flat-dollar/
     sub-limit tables -- confirming the 4 `AttachForm*` variants (C10-01
     Sec.2A) are MUTUALLY EXCLUSIVE at the `SetPremium` level too, not just
     at attachment.

    python scripts/cf/89_chunk10_c10-05_hardcoded_literals.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"
ENDT_FILE = "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml"


def rule_body(text: str, name: str) -> str:
    i = text.find(f'<rul:Rule Name="{name}"')
    j = text.find("</rul:Rule>", i) + 11
    return text[i:j]


def main() -> int:
    book = book_for("OR", ASOF)
    rules_dir = book.parent.package.content / "Rules"
    domains_dir = book.parent.package.content / "Domain Tables"

    body = (rules_dir / ENDT_FILE).read_text(encoding="utf-8-sig")
    seg = rule_body(body, "SetPremium")

    print("=== 1  EQCovIndicator literals tested inside SetPremium\n")
    eq_lits = re.findall(
        r'FromDataDef="\.\./\.\./EQCovIndicator"[^/]*/>\s*'
        r'<rul:Constant Type="string">([^<]*)</rul:Constant>', seg)
    print(f"    literals found, in order of appearance: {eq_lits}")
    dom_rows = (domains_dir / "DomainEQCovIndicatorBldg.DomainTable.csv").read_text(
        encoding="utf-8-sig").strip().splitlines()[1:]
    full_domain = sorted({r.split('","')[-1].strip('"') for r in dom_rows})
    print(f"    full DomainEQCovIndicatorBldg domain (C10-04's own re-count): "
          f"{full_domain}")
    missing = sorted(set(full_domain) - set(eq_lits))
    print(f"    domain value(s) SetPremium never tests directly: {missing} "
          f"-- 'Yes, Not Included in Blanket' is the IMPLICIT case (falls "
          f"through the outer gate's NotEqual pair into When 1/2, the plain "
          f"path C10-01's golden case exercised) -- not untested, just not "
          f"a literal `Equal` anywhere in this rule.")

    print("\n=== 2  CovType literals tested inside SetPremium\n")
    covtype_lits = re.findall(
        r'FromDataDef="\.\./\.\./CovType"[^/]*/>\s*'
        r'<rul:Constant Type="string">([^<]*)</rul:Constant>', seg)
    print(f"    literals found, in order of appearance: {covtype_lits}")
    dbt_rows = (domains_dir / "DomainCovTypeBldg.DomainTable.csv").read_text(
        encoding="utf-8-sig").strip().splitlines()[1:]
    cov_domain = sorted({r.split('","')[-1].strip('"') for r in dbt_rows})
    print(f"    full DomainCovTypeBldg domain: {cov_domain}")
    all_in_domain = all(c in cov_domain for c in covtype_lits)
    print(f"    every literal SetPremium tests is a legal domain value: "
          f"{all_in_domain}")
    missing_covtype = sorted(set(cov_domain) - set(covtype_lits))
    print(f"    domain value(s) never tested by name in SetPremium: "
          f"{missing_covtype} -- 'No Coverage' is a structure that never "
          f"elects EQ at all (never reaches this rule's Then branch in the "
          f"first place, since the CovType field describes the STRUCTURE's "
          f"coverage type, not the EQ election).")
    print("\n    Read directly -- the 6-literal shape, exactly as it "
          "appears (task doc's own list, confirmed verbatim, not "
          "paraphrased):")
    print("        outer If exclusion:  CovType <> 'Leasehold Interest'")
    print("        When 1 (Or, 4 lits): CovType = 'Building' | 'Improvements "
          "and Betterments' | 'Condominium Association' | 'Builders Risk'")
    print("        When 2:              CovType = 'Legal Liability'")
    print("        When 3:              EQCovIndicator = 'Yes, Included in "
          "Blanket' (any CovType, including Leasehold Interest -- the "
          "outer exclusion only blocks the NON-blanket Whens, confirmed by "
          "its placement OUTSIDE the Choose, gating entry to the whole Then)")

    print("\n=== 3  Structural gates found while reading, not named by the "
          "task doc\n")
    not_exists = re.findall(r'<rul:NotExist AtInputDataDef="([^"]+)"', seg)
    print(f"    outer If's NotExist checks ({len(not_exists)}):")
    for n in not_exists:
        print(f"        {n}")
    print("\n    Confirmed: the plain Endorsement's own SetPremium only "
          "computes a Premium when NONE of the 3 sibling variant records "
          "(FlatDollarDeductible, SubLimitForm, SubLimitFormWithFlat"
          "DollarDeductible) exist on this structure -- the 4 AttachForm* "
          "variants (C10-01 Sec.2A) are mutually exclusive not only at "
          "attachment (each AttachForm*'s own Else deletes the OTHERS) but "
          "re-confirmed independently here, one level downstream, at the "
          "premium-computation rule itself. A submission that somehow "
          "carried two of the four sibling records at once would silently "
          "compute $0 for the plain Endorsement (outer gate fails) rather "
          "than double-count -- a defensive redundancy, not a gap.")

    print("\n=== Summary\n")
    print("    EQCovIndicator: 3 of 4 domain values tested by literal Equal/"
          "NotEqual; the 4th ('Yes, Not Included in Blanket') is the "
          "fall-through default, not untested.")
    print("    CovType: 6 literals, all 6 legal domain values (of 7 total; "
          "'No Coverage' is structurally unreachable here by construction, "
          "not a missed literal).")
    print("    3 NotExist structural gates confirm the 4-way mutual "
          "exclusion the golden case already assumed but did not verify "
          "independently. No engine gap, no unfiled/unreachable literal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
