#!/usr/bin/env python3
"""Chunk 6 opening census -- Special Class, before any task is written.

Same opening move as chunks 4 and 5: enumerate the tables and the rule
overrides across all 47 jurisdictions FIRST, so the task list is written
against what is filed rather than against what the algorithms page says.

Three questions:

  1  **The table census.** Which Special Class tables carry countrywide rows,
     and how many of the 47 file their own?
  2  **The class-description census.** `SpecialClassDescriptionConvertedOption`
     maps free-text `ClassDescription` to an OptionNN code. If a state files
     description strings that do not exist countrywide, a CW-derived list of
     descriptions silently misses in that state.
  3  **The override census.** Which of the Special Class chain rules does any
     state replace, and which does a state DELETE (empty `<rul:Sequence />`)?

    python scripts/cf/40_chunk6_census.py

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
RULES = "CommercialPropertySpecialClassRules.Rule.xml"

TABLES = [
    "BasicGroupIRateSpecialClass",
    "SpecialClassDescriptionConvertedOption",
    "SpecialClassBasicGroupIINumber",
    "BasicGroupIIRate",
    "LowestBasicGroupIIRate",
    "BroadFormBaseRate",
    "SpecialBuildingRate",
    "SpecialBldgTheftExclusionFactor",
    "BasicGroupIIFlatCoinsuranceFactor",
    "CoinsuranceFactor",
    "DeductibleFactor",
    "Deductible250Factor",
    "ProtectionClassFactor",
]

CHAIN_RULES = [
    "SetSpecialClassDescConvertedOption",
    "SetBasicGroupIISymbolNum",
    "SetCoinsuranceFactor",
    "SetBasicGroupIBaseRate",
    "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment",
    "SetAdjustedBasicGroupIRate",
    "SetDeductibleFactorBasicGroupI",
    "SetFinalBasicGroupIRate",
    "SetBasicGroupIINumericValue",
    "SetBasicGroupIIBaseRate",
    "SetBasicGroupIIRate",
    "SetBasicGroupIICauseOfLossAdjustment",
    "SetBasicGroupIICoinsuranceFactor",
    "SetFinalBasicGroupIIRate",
    "SetBroadBaseRate",
    "SetBroadRate",
    "SetAdjustedBroadRate",
    "SetDeductibleFactorBroad",
    "SetFinalBroadRate",
    "SetSpecialTheftExclusionIndicator",
    "SetSpecialTheftExclusionFactor",
    "SetSpecialBaseRate",
    "SetSpecialRate",
    "SetSpecialCauseOfLossAdjustment",
    "SetDeductibleFactorSpecial",
    "SetFinalSpecialRate",
    "SetProtectionClassFactor",
]


def rows_of(book, name):
    try:
        return len(book.table(name).rows)
    except Exception:
        return None


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    cw = book_for(juris[0], ASOF, resolver=res)
    books = {}
    for j in juris:
        try:
            books[j] = book_for(j, ASOF, resolver=res)
        except Exception as exc:
            print(f"    {j}: book failed -- {exc}")

    print(f"=== 1  Table census   ({len(juris)} jurisdictions, as of {ASOF})\n")
    print(f"    {'table':44s} {'CW':>5s}  states declaring")
    for t in TABLES:
        n_cw = None
        try:
            n_cw = len(cw.parent_table(t).rows)
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
        print(f"    {t:44s} {cwtxt:>5s}  {len(declaring)} of {len(juris)}"
              + ("" if len(declaring) in (0, len(juris))
                 else "   " + ",".join(declaring)))

    # ---- 2  class descriptions
    #
    # **Compare each state against ITS OWN resolved parent, not against some
    # other state's.** The first cut of this census read ONE countrywide table
    # -- whichever jurisdiction sorted first -- and diffed all 47 against it.
    # Florida resolves over `CF_CW_20230801_V01` while almost everyone else
    # resolves over `CF_CW_20260601_V01`, so that cut reported 11
    # "Florida-only" descriptions where the true within-edition figure is 3.
    # **A cross-edition diff manufactures differences**, and it manufactured
    # them in exactly the place this chunk was about to draw a headline.
    NAME = "SpecialClassDescriptionConvertedOption"
    print(f"\n=== 2  Class-description census  ({NAME})\n")
    ref_desc = ref_pkg = None
    for j, b in books.items():
        try:
            parent = b.parent_table(NAME)
        except Exception:
            continue
        own_parent = {r[1] for r in parent.rows}
        if ref_desc is None:
            ref_desc, ref_pkg = own_parent, b.parent.pkg_id
        if b.declares(NAME) != "state":
            continue
        st = b.table(NAME)
        own = {r[1] for r in st.rows}
        cwm = {r[1]: r[2] for r in parent.rows}
        stm = {r[1]: r[2] for r in st.rows}
        remap = [d for d in own & set(cwm) if cwm[d] != stm[d]]
        print(f"    {j} [{b.state.pkg_id} over {b.parent.pkg_id}]")
        print(f"        {len(own):>4d} rows against its own parent's "
              f"{len(parent.rows)}")
        print(f"        {len(own - own_parent):>4d} description(s) its parent "
              f"does not file")
        for d in sorted(own - own_parent):
            print(f"             + {d}")
        print(f"        {len(own_parent - own):>4d} description(s) it DROPS "
              f"from its parent")
        for d in sorted(own_parent - own):
            print(f"             - {d}")
        print(f"        option codes outside its parent's set : "
              f"{len({r[2] for r in st.rows} - {r[2] for r in parent.rows})}")
        print(f"        shared descriptions mapped to a DIFFERENT code : "
              f"{len(remap)}")
        if own_parent != ref_desc:
            cross = len(own - ref_desc)
            art = cross - len(own - own_parent)
            print(f"        **its parent is a DIFFERENT EDITION from "
                  f"{ref_pkg}.** Diffed against that")
            print(f"        instead, this table would read {cross} "
                  f"state-only description(s) -- {art} of")
            print(f"        them an artefact of comparing across editions, "
                  f"not a Florida filing choice.")

    # ---- 3  overrides
    print("\n=== 3  Rule-override census\n")
    hits, deleted = {}, {}
    for j, b in books.items():
        f = b.state.package.content / "Rules" / RULES
        if not f.exists():
            continue
        body = f.read_text(encoding="utf-8-sig")
        for name in CHAIN_RULES:
            i = body.find(f'<rul:Rule Name="{name}"')
            if i < 0:
                continue
            rule = body[i:i + body[i:].find("</rul:Rule>") + 11]
            hits.setdefault(name, []).append(j)
            if "<rul:Sequence />" in rule or "<rul:Sequence/>" in rule:
                deleted.setdefault(name, []).append(j)
    for name in CHAIN_RULES:
        h = hits.get(name, [])
        d = deleted.get(name, [])
        if not h:
            print(f"    {name:40s}  0")
            continue
        print(f"    {name:40s} {len(h):>2d}   {','.join(h)}"
              + (f"   DELETED by {','.join(d)}" if d else ""))
    print("\n    (a state's own Rules file may also exist but not override "
          "these names)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
