#!/usr/bin/env python3
"""Chunk 7 opening census -- Special Class Business Income, before any task.

Same opening move as chunks 4, 5 and 6: enumerate the tables and the rule
overrides across all 47 jurisdictions FIRST, so the task list is written
against what is filed rather than against what the algorithms page says.

**And it carries chunk 6's correction in from the start.** Each state is
diffed against **its own resolved parent**, and the parent package id is
printed on every line. Chunk 6's census read one countrywide table for all 47
jurisdictions and published a finding that was 8/11 artefact (OI-100).

Three questions:

  1  **The table census.** Which tables does this group reach, how many rows do
     they carry countrywide, and how many states file their own?
  2  **The borrowed-rate census.** Basic Group I and Earthquake are said to copy
     the Special Class item's FULLY RATED rate rather than its base rate. Count
     the rules in this group that write a base rate at all.
  3  **The override census.** Which chain rules does any state replace, and
     which does a state DELETE (empty `<rul:Sequence />`)?

    python scripts/cf/49_chunk7_census.py

Always exits 0 -- this is a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"
GROUP = "CommercialPropertySpecialClassBusnIncome"
RULES = f"{GROUP}Rules.Rule.xml"
PARENT_RULES = "CommercialPropertySpecialClassRules.Rule.xml"

TABLES = [
    "BasicGroupIIRate",
    "LowestBasicGroupIIRate",
    "BroadFormBaseRate",
    "SpecialFormIncldgTheftTimeElementBaseRate",
    "SpecialLeaseHoldTimeElementTheftExclusionFactor",
    "BusnIncomeFactor",
    "MaxPeriodOfIndemnityFactor",
    "MonthlyLimitOfIndemnityFactor",
    "ExtraExpenseFactor",
    "AgreedValueFactor",
    "BaseRateAdjustmentFactor",
    "SpecialFormBldrsRiskTimeElementBaseRate",
]

CHAIN_RULES = [
    "SetBGIRatesAndFactors", "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment", "SetFinalBasicGroupIRate",
    "SetBGIIRatesAndFactors", "SetBasicGroupIIBaseRate",
    "SetLowestBasicGroupIIBaseRate", "SetBasicGroupIIRate",
    "SetBasicGroupIICauseOfLossAdjustment", "SetFinalBasicGroupIIRate",
    "SetBroadRatesAndFactors", "SetBroadBaseRate", "SetBroadRate",
    "SetFinalBroadRate", "SetSpecialRatesAndFactors",
    "SetSpecialTheftExclusionIndicator", "SetSpecialTheftExclusionFactor",
    "SetSpecialBaseRate", "SetSpecialRate",
    "SetSpecialCauseOfLossAdjustment", "SetFinalSpecialRate",
    "SetFactor", "SetTypeOfRiskFactor", "SetCoinsuranceToUse",
    "SetEQRatesAndFactors", "SetEQRate", "SetPolicyType",
]

#: Claims the algorithms page makes that a census can check cheaply.
ABSENT = ["BaseRateAdjustmentFactor", "SpecialIncludingTheftTypeRisk",
          "StdPropPolGroupIFactor", "BuildersRiskFactor", "LOIFactor",
          "MultiResidentialPropSpecialCreditFactor"]


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {}
    for j in juris:
        try:
            books[j] = book_for(j, ASOF, resolver=res)
        except Exception as exc:
            print(f"    {j}: book failed -- {exc}")
    any_book = next(iter(books.values()))

    print(f"=== 1  Table census   ({len(juris)} jurisdictions, as of {ASOF})")
    print(f"    each state diffed against ITS OWN parent (chunk 6 / OI-100)\n")
    print(f"    {'table':46s} {'CW':>5s}  states declaring")
    for t in TABLES:
        try:
            n_cw = len(any_book.parent_table(t).rows)
        except Exception:
            n_cw = None
        declaring = []
        for j, b in books.items():
            try:
                if b.declares(t) == "state":
                    declaring.append(j)
            except Exception:
                pass
        cwtxt = "none" if n_cw is None else str(n_cw)
        line = f"    {t:46s} {cwtxt:>5s}  {len(declaring)} of {len(juris)}"
        if 0 < len(declaring) <= 6:
            line += "   " + ",".join(declaring)
        elif len(declaring) and len(declaring) < len(juris):
            missing = sorted(set(books) - set(declaring))
            line += f"   (all but {','.join(missing)})"
        print(line)

    # ---- 2  what this group looks up for itself
    print(f"\n=== 2  What this group computes for itself\n")
    body = (any_book.parent.package.content / "Rules" / RULES).read_text(
        encoding="utf-8-sig")
    parent = (any_book.parent.package.content / "Rules"
              / PARENT_RULES).read_text(encoding="utf-8-sig")
    borrows = sorted(set(re.findall(
        r'FromDataDef="\.\./\.\./(\w*(?:Rate|Symbol|Terr|Factor)\w*)"', body)))
    print(f"    values read from the Special Class item (../../) : "
          f"{len(borrows)}")
    for b_ in borrows:
        print(f"        {b_}")
    lookups = sorted(set(re.findall(r'MatrixFromConstant="(\w+)"', body)))
    print(f"\n    matrices this ruleset names : {len(lookups)}")
    for m in lookups:
        print(f"        {m}")
    print()
    for name in ABSENT:
        a, b_ = body.count(name), parent.count(name)
        print(f"    {name:44s} here {a:>3d}   in Special Class Building {b_:>3d}")

    # ---- 3  overrides
    print(f"\n=== 3  Rule-override census   ({RULES})\n")
    hits, deleted = {}, {}
    for j, b in books.items():
        f = b.state.package.content / "Rules" / RULES
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8-sig")
        for name in CHAIN_RULES:
            i = t.find(f'<rul:Rule Name="{name}"')
            if i < 0:
                continue
            rule = t[i:i + t[i:].find("</rul:Rule>") + 11]
            hits.setdefault(name, []).append(j)
            if "<rul:Sequence />" in rule or "<rul:Sequence/>" in rule:
                deleted.setdefault(name, []).append(j)
    for name in CHAIN_RULES:
        h, d = hits.get(name, []), deleted.get(name, [])
        if not h:
            print(f"    {name:40s}  0")
            continue
        print(f"    {name:40s} {len(h):>2d}   {','.join(h)}"
              + (f"   DELETED by {','.join(d)}" if d else ""))
    states_with_file = [j for j, b in books.items()
                        if (b.state.package.content / "Rules" / RULES).exists()]
    print(f"\n    jurisdictions filing their own {RULES}: "
          f"{len(states_with_file)} of {len(juris)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
