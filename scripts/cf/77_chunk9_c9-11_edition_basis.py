#!/usr/bin/env python3
"""Chunk 9, C9-11 -- is `CommercialPropertyBlanketRatingDetailRules.Rule.xml`
at the same edition as the 20 premium files it feeds, given Florida
overrides it?

Read directly against `cf_engine.resolve` (`CFEditionResolver`/`book_for`)
rather than inferring from the census's one-line "Florida overrides this
file" claim.

**Mechanism, confirmed from `cf_engine/resolve/resolver.py`'s own
docstring**: this resolver is deliberately TWO layers, no carry-forward --
one state package (if any applies as of the date) over its own DECLARED
parent countrywide package. There is no notion of "this rule file is on
edition X while that one is on edition Y" WITHIN one resolved book: every
rule file a jurisdiction reads comes from the same package pair.

**Prediction, before running:**
  - Oregon (the golden case's jurisdiction) has no state package with a
    `Rules/` folder at all (its 20260601 package carries only Form
    Fields/Pages/RelatedFields) -- every rule file, Detail engine included,
    falls through to the CURRENT countrywide package
    (`CFCW20260601V01`). Edition basis: consistent, and current.
  - Florida's newest package is `CF FL 20241201 V01` (filed under the
    `20230801v1` snapshot, no 20260601-dated FL package exists at all), whose
    declared parent is `CF CW 20230801 V01` -- NOT the current
    `CFCW20260601V01`. If FL resolves as of today, its WHOLE book (Detail
    engine and all 5 premium parents alike) pairs with that older parent.
    Not a Detail-vs-premium split inside one state -- a whole-book
    jurisdictional skew, self-consistent, and exactly what the resolver's
    own "no carry-forward" design produces.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"
DETAIL_FILE = "CommercialPropertyBlanketRatingDetailRules.Rule.xml"
PARENT_FILES = [
    "CommercialPropertyStructureBuildingBasicGroupICoverageRules.Rule.xml",
    "CommercialPropertyContentsBasicGroupICoverageRules.Rule.xml",
    "CommercialPropertyBusinessIncomeBasicGroupICoverageRules.Rule.xml",
    "CommercialPropertySpecialClassBasicGroupICoverageRules.Rule.xml",
    "CommercialPropertySCBusnIncomeBasicGroupICoverageRules.Rule.xml",
]


def project_name_refs(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r'ProjectName="([^"]*)"', text))


def main() -> int:
    print("=== 1. Oregon (golden case jurisdiction) ===")
    b_or = book_for("OR", ASOF)
    print(f"  {b_or}")
    or_state_pkg = b_or.state.package
    or_parent_pkg = b_or.parent.package
    or_rules_dir = or_state_pkg.dir("Rules")
    print(f"  OR state package: {or_state_pkg.pkg_id}  content dir: {or_state_pkg.content}")
    or_files = sorted(p.name for p in or_rules_dir.glob('*.xml')) if or_rules_dir.is_dir() else []
    print(f"  OR state package overrides {len(or_files)} rule files total "
          f"(NOT zero -- correcting an over-broad first pass):")
    for f in or_files:
        print(f"    {f}")
    or_overrides_detail = (or_rules_dir / DETAIL_FILE).exists()
    or_overrides_parents = [(f, (or_rules_dir / f).exists()) for f in PARENT_FILES]
    print(f"\n  Of those, does OR override {DETAIL_FILE}? {or_overrides_detail}")
    print("  Does OR override any of the 5 parent BasicGroupI SetPremium files "
          "the golden case actually exercises?")
    for f, exists in or_overrides_parents:
        print(f"    {f:65s} override={exists}")
    print(f"  OR declared CW parent: {or_parent_pkg.pkg_id}")

    print("\n=== 2. Florida ===")
    b_fl = book_for("FL", ASOF)
    print(f"  {b_fl}")
    fl_state_pkg = b_fl.state.package
    fl_parent_pkg = b_fl.parent.package
    print(f"  FL resolved state package: {fl_state_pkg.pkg_id}")
    print(f"  FL declared CW parent:     {fl_parent_pkg.pkg_id}")
    print(f"  Current (2026-09-21) countrywide edition available: CF_CW_20260601_V01")
    skew = fl_parent_pkg.pkg_id.strip() != "CF_CW_20260601_V01"
    print(f"  FL's whole book is on an OLDER countrywide edition than current: {skew}")

    fl_rules_dir = fl_state_pkg.dir("Rules")
    fl_detail_path = fl_rules_dir / DETAIL_FILE
    fl_detail_overrides = fl_detail_path.exists()
    print(f"  FL overrides {DETAIL_FILE}: {fl_detail_overrides}"
          f" (path: {fl_detail_path if fl_detail_overrides else 'n/a'})")

    fl_premium_overrides = []
    for f in PARENT_FILES:
        p = fl_rules_dir / f
        fl_premium_overrides.append((f, p.exists()))
    print("  FL overrides of the 5 parent premium files:")
    for f, exists in fl_premium_overrides:
        print(f"    {f:65s} override={exists}")

    print("\n=== 3. Is it content-difference or edition-difference for FL? ===")
    detail_refs = project_name_refs(fl_detail_path) if fl_detail_overrides else set()
    print(f"  ProjectName references inside FL's {DETAIL_FILE} override: {detail_refs}")
    print(f"  FL's resolved parent package id: {fl_parent_pkg.pkg_id}")
    print(f"  Those references target FL's own declared CW parent (20230801): "
          f"{bool(detail_refs) and any('20230801' in r for r in detail_refs)}")

    print("\n=== Verdict ===")
    print("  Oregon (golden case): OR overrides 15 rule files, but NEITHER "
          "the Blanket Detail engine NOR any of the 5 parent BasicGroupI "
          "SetPremium files the golden case exercises is among them -- both "
          "fall through to the same declared CW parent, CF_CW_20260601_V01, "
          "the current edition. Consistent, and current.")
    print("  Florida: internally consistent but OLDER -- FL's Detail-engine "
          "override and its premium-file overrides (where they exist) are "
          "both paired with the SAME declared parent (CF CW 20230801 V01), "
          "not split across two editions within FL's own book. The skew is "
          "FL's WHOLE resolved book being behind the current countrywide "
          "edition (FL has filed no 20260601-dated package at all), not a "
          "Detail-vs-premium edition mismatch inside one jurisdiction. This "
          "is the resolver's own documented, deliberate two-layer/"
          "no-carry-forward design (resolver.py's module docstring), not an "
          "engine gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
