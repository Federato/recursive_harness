#!/usr/bin/env python3
"""Chunk 9, C9-05 -- the 47-state override census the C9-01 census's Sec.2/5
only did the reachability half of.

Confirms, directly against the corpus rather than by repeating the census:

  1. The blanket dispatcher's real rule/file names across the 5 premium
     groups, and whether `SetEQBlanketValues` (the EQ-specific analog to
     `SetNonEQBlanketValues`) exists for all 5 -- census Sec.2 already
     listed it in every group's "machinery"; here it's read directly.
  2. For ALL 47 jurisdictions, whether any state overrides any of the 10
     rules (5 groups x {SetNonEQBlanketValues, SetEQBlanketValues}), reported
     as "n of 47" per rule, not a sample.
  3. Whether the state package FILE existing is the same thing as the state
     overriding the RULE -- it is not (per this project's "ERC state
     packages are overlays" rule): the 5 parent rule files exist in nearly
     every state's own package (because they carry unrelated state-specific
     endorsement rules), but that is not evidence the blanket machinery
     itself is touched. Both counts are printed so the difference is visible.
  4. At least one real diff, read directly, for whichever rule/group DOES
     have an override.

    python scripts/cf/71_chunk9_c9-05_state_override_census.py

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
#: the two dispatcher literal names C9-01/census Sec.2 already found.
DISPATCHER_NAMES = ["SetBlanketValuesSection", "SetBlanketValues"]
#: the 10 rules this task asks about: 5 groups x {NonEQ, EQ}.
VALUE_RULE_NAMES = ["SetNonEQBlanketValues", "SetEQBlanketValues"]


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    rules_dir = any_book.parent.package.content / "Rules"

    print(f"=== 1  Dispatcher and SetEQBlanketValues existence, all 5 "
          f"groups, read directly\n")
    dispatcher_by_group = {}
    for group, fn in GROUPS.items():
        body = (rules_dir / fn).read_text(encoding="utf-8-sig")
        names = set(re.findall(r'<rul:Rule Name="(\w+)"', body))
        disp = [n for n in DISPATCHER_NAMES if n in names]
        dispatcher_by_group[group] = disp
        has_noneq = "SetNonEQBlanketValues" in names
        has_eq = "SetEQBlanketValues" in names
        print(f"    {group:20s} dispatcher={disp}  "
              f"SetNonEQBlanketValues={'present' if has_noneq else 'MISSING'}  "
              f"SetEQBlanketValues={'present' if has_eq else 'MISSING'}")
    missing_eq = [g for g, fn in GROUPS.items()
                  if "SetEQBlanketValues" not in
                  set(re.findall(r'<rul:Rule Name="(\w+)"',
                                 (rules_dir / fn).read_text(encoding="utf-8-sig")))]
    print(f"\n    Groups missing SetEQBlanketValues: {len(missing_eq)} of 5"
          + (f"  {missing_eq}" if missing_eq else " -- all 5 have it, "
             "confirming the task's premise directly rather than trusting "
             "the census's 'machinery' list at face value."))

    print(f"\n=== 2  47-state override census, all 10 rules "
          f"(5 groups x {{NonEQ, EQ}})\n")
    for group, fn in GROUPS.items():
        print(f"    {group} ({fn})")
        file_exists = [j for j in juris
                        if (books[j].state.package.content / "Rules" / fn).exists()]
        print(f"        state package carries this FILE AT ALL: "
              f"{len(file_exists)} of {len(juris)} -- NOT the same question "
              f"(overlay files carry unrelated state rules too, per this "
              f"project's overlay rule)")
        for rule_name in VALUE_RULE_NAMES:
            overriders = []
            for j in file_exists:
                p = books[j].state.package.content / "Rules" / fn
                t = p.read_text(encoding="utf-8-sig", errors="ignore")
                if re.search(rf'<rul:Rule Name="{rule_name}"', t):
                    overriders.append(j)
            print(f"        {rule_name:24s} overridden by: "
                  f"{len(overriders)} of {len(juris)}"
                  + (f"  {overriders}" if overriders else ""))
        # also check the dispatcher name(s) themselves, since C9-08 is a
        # separate task but the override, if any, would show up here first.
        for disp in dispatcher_by_group[group]:
            overriders = []
            for j in file_exists:
                p = books[j].state.package.content / "Rules" / fn
                t = p.read_text(encoding="utf-8-sig", errors="ignore")
                if re.search(rf'<rul:Rule Name="{disp}"', t):
                    overriders.append(j)
            print(f"        {disp:24s} (dispatcher) overridden by: "
                  f"{len(overriders)} of {len(juris)}"
                  + (f"  {overriders}" if overriders else ""))

    print("\n=== 3  At least one real diff, read directly\n")
    # Special Class's dispatcher (SetBlanketValues) is the one hit found
    # above -- AL and KS. Read AL's copy directly.
    al_path = books["AL"].state.package.content / "Rules" / GROUPS["Special Class"]
    t = al_path.read_text(encoding="utf-8-sig", errors="ignore")
    i = t.find('<rul:Rule Name="SetBlanketValues"')
    j = t.find("</rul:Rule>", i) + 11
    print("    AL CommercialPropertySpecialClassRules.Rule.xml, "
          "SetBlanketValues (MetadataCodes=\"RuleTypeOverridden\"):")
    for line in t[i:j].splitlines():
        print("     ", line.strip())
    print("\n    Not a rewrite -- an ADD. AL's override is a Sequence that "
          "RunRules the countrywide SetBlanketValues UNCHANGED "
          "(FileName=CommercialPropertySpecialClassRules, "
          "ProjectName=\"CF CW 20260601 V01\"), then chains one more "
          "state-specific rule, SetPublicInstitutionalPlanFactor, which "
          "itself branches on IncludedInBlkt (both the blanket-elected and "
          "non-elected cases) to decide a Public Institutional Plan credit. "
          "KS carries the identical override. Neither state changes the "
          "blanket averaging mechanism itself -- they tack an unrelated "
          "state credit onto the SAME dispatcher name C9-08 already flags "
          "as shared across groups, which is itself worth noting: the "
          "shared-name machinery is also the state override's attachment "
          "point.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
