#!/usr/bin/env python3
"""Chunk 10, C10-03 -- state enumeration, BOTH layers, all 47, re-confirmed
directly rather than cited from the opening census, same discipline as
C9-05.

  (a) The 97 `*Earthquake*` wrapper files' state PACKAGE census (census
      Sec.9 already printed a version of this -- re-confirmed here, not
      assumed still accurate).
  (b) The 5 parent files' EQ-engine-RULE override census -- does any of the
      47 jurisdictions override any of the ~9 EQ engine rule names, in any
      of the 5 groups (census Sec.9's per-group tally, re-confirmed with the
      full per-state list, not just the count).

    python scripts/cf/87_chunk10_c10-03_state_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

GROUPS = {
    "Building": "CommercialPropertyStructureRules.Rule.xml",
    "Contents": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "Business Income": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "Special Class": "CommercialPropertySpecialClassRules.Rule.xml",
    "SC Business Income": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}
EQ_ENGINE_RULES = [
    "SetEQBaseRate", "SetEQRate", "SetFinalEQRate", "SetEQCauseOfLossAdjustment",
    "SetEQClassToUse", "LookupEQClassToUse", "SetEQDeductibleFactor",
    "SetEQDeductibleByLocationFactor", "SetAdjustedEQRate",
]


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    rules_dir = any_book.parent.package.content / "Rules"

    eq_files = sorted(p.name for p in rules_dir.glob("*.xml") if "Earthquake" in p.name)
    assert len(eq_files) == 97, len(eq_files)

    print(f"=== (a)  The 97 wrapper files' state PACKAGE census, re-confirmed "
          f"directly, all {len(juris)} jurisdictions\n")
    wrapper_counts = {}
    for f in eq_files:
        own = sorted(j for j in juris
                      if (books[j].state.package.content / "Rules" / f).exists())
        wrapper_counts[f] = own
    total_any = sum(1 for f in eq_files if wrapper_counts[f])
    print(f"    of 97 wrapper files, {total_any} have at least one state "
          f"PACKAGE copy (file-existing, not rule-overriding -- per this "
          f"project's overlay rule); census Sec.9 said 56 -- "
          f"{'MATCH' if total_any == 56 else 'DOES NOT MATCH, now ' + str(total_any)}")
    top = sorted(wrapper_counts.items(), key=lambda kv: -len(kv[1]))[:8]
    print("\n    Top 8 by state-file count, full state lists (census Sec.9 "
          "only printed the top 5 with no state names):")
    for f, states in top:
        print(f"        {len(states):2d}  {f}")
        print(f"             {states}")
    zero = [f for f, s in wrapper_counts.items() if not s]
    print(f"\n    Wrapper files with ZERO state package copies anywhere: "
          f"{len(zero)} of 97")

    print(f"\n=== (b)  The 5 parent files' EQ-engine-RULE override census, "
          f"all 47, full per-state lists (census Sec.9 printed only counts)\n")
    engine_override_by_group = {}
    for group, fn in GROUPS.items():
        overriding = []
        for j in juris:
            p = books[j].state.package.content / "Rules" / fn
            if not p.exists():
                continue
            body = p.read_text(encoding="utf-8-sig", errors="ignore")
            if any(re.search(rf'<rul:Rule Name="{r}"', body) for r in EQ_ENGINE_RULES):
                overriding.append(j)
        engine_override_by_group[group] = sorted(overriding)
        print(f"    {group:20s} {fn:56s} states overriding an EQ engine "
              f"rule: {len(overriding):2d} of {len(juris)}  {sorted(overriding)}")

    expected = {"Building": 10, "Contents": 9, "Special Class": 7,
                "Business Income": 5, "SC Business Income": 0}
    print("\n    Re-confirmed against the opening census's own claim "
          "(finding 6 / the state-layer section):")
    for group, n in expected.items():
        got = len(engine_override_by_group[group])
        print(f"        {group:20s} census claimed {n:2d}, direct re-count "
              f"gives {got:2d}  -- {'MATCH' if got == n else 'DOES NOT MATCH'}")

    print("\n=== (c)  Which rule, per group, per overriding state -- not just "
          "'an EQ engine rule', the specific one(s)\n")
    for group, fn in GROUPS.items():
        for j in engine_override_by_group[group]:
            p = books[j].state.package.content / "Rules" / fn
            body = p.read_text(encoding="utf-8-sig", errors="ignore")
            found = [r for r in EQ_ENGINE_RULES if re.search(rf'<rul:Rule Name="{r}"', body)]
            print(f"    {group:20s} {j:3s}  overrides: {found}")

    print("\n=== (d)  FL and PR appear in every group with any override at "
          "all -- re-confirmed, not just cited\n")
    fl_pr_universal = all(
        {"FL", "PR"} <= set(engine_override_by_group[g])
        for g in engine_override_by_group if engine_override_by_group[g]
    )
    print(f"    Groups with >=1 override, and whether FL+PR are both in "
          f"every one of them: {fl_pr_universal}")
    for g, states in engine_override_by_group.items():
        if states:
            print(f"        {g:20s} FL in override set: {'FL' in states}   "
                  f"PR in override set: {'PR' in states}")

    print("\n=== (e)  Two layers, confirmed genuinely different questions\n")
    package_only = set()
    for f, states in wrapper_counts.items():
        package_only |= set(states)
    engine_states = set()
    for states in engine_override_by_group.values():
        engine_states |= set(states)
    print(f"    States with >=1 wrapper-file PACKAGE copy: {len(package_only)} "
          f"of {len(juris)}")
    print(f"    States with >=1 EQ-engine-RULE override in any of the 5 "
          f"groups: {len(engine_states)} of {len(juris)}  {sorted(engine_states)}")
    print(f"    Package-copy states NOT among the engine-rule-override "
          f"states (file exists, but carries no EQ engine rule at all -- "
          f"unrelated state-specific rules in the same file, per this "
          f"project's overlay rule): {len(package_only - engine_states)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
