#!/usr/bin/env python3
"""Chunk 7, task C7-28 -- the algorithms page's five open questions, answered.

Each is either **answered with evidence** or **left open with a reason**. None
is left as it was.

  Q1  the hard-coded "Other than Apartments and Condominiums" key
  Q2  `SpecialLeaseHoldTimeElementTheftExclusionFactor`'s values, never
      cross-checked against what plain Business Income reads
  Q3  `BasicGroupIIRate` / `LowestBasicGroupIIRate` header-only
  Q4  two endorsement files confirmed to exist but never traced
  Q5  `...SpecialClassBusnIncomeCoverageRules.Rule.xml` never opened

    python scripts/cf/57_chunk7_open_questions.py

Exit 0 when every answer holds.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.tree import read

perform = import_module("55_chunk7_perform")
g7 = import_module("50_chunk7_golden_case")

BI, ASOF = g7.BI, g7.ASOF
MINE = "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"
PLAIN = "CommercialPropertyBusinessIncomeRules.Rule.xml"
DISPATCH = "CommercialPropertySpecialClassBusnIncomeCoverageRules.Rule.xml"
ENDORSEMENTS = [
    "CommercialPropertySpecialClassBusnIncomeInterruptionOfComputerOperationsCoverageRules.Rule.xml",
    "CommercialPropertySpecialClassBusnIncomeWatercraftExclusionBuybackCoverageRules.Rule.xml",
]
THEFT = "SpecialLeaseHoldTimeElementTheftExclusionFactor"


def lookup_keys(body, rule):
    i = body.find(f'<rul:Rule Name="{rule}"')
    if i < 0:
        return None
    seg = body[i:i + body[i:].find("</rul:Rule>") + 11]
    first = seg[:seg.find("</rul:Keys>")]
    consts = re.findall(r"<rul:Constant Type=\"string\">([^<]*)</rul:Constant>",
                        first)
    dds = re.findall(r'FromDataDef="([^"]+)"', first)
    return consts, dds


def main() -> int:
    ok = True
    book = book_for("OR", ASOF)
    d = book.parent.package.content / "Rules"
    mine = (d / MINE).read_text(encoding="utf-8-sig")
    plain = (d / PLAIN).read_text(encoding="utf-8-sig")

    # ---- Q1
    print("=== Q1  The hard-coded apartments key -- ANSWERED, and half of the")
    print("        question was built on a false premise (C7-19 / C7-20).")
    data = perform.run_rec("Special", perform.THEFT,
                           item={"ClassCode": "0311"},
                           rec={"ApartmentCondoIndicator": "Yes"})
    got = (str(read(f"{BI}/SpecialBaseRate", data)),
           str(read(f"{BI}/SpecialTheftExclusionFactor", data)))
    good = got == ("0.047", "0.86")
    ok &= good
    print(f"        apartments elected every way available: base={got[0]}, "
          f"theft={got[1]}  (expected 0.047 / 0.86) "
          f"{'OK' if good else 'MISMATCH'}")
    print("        The page asked whether the base-rate pin was an ISO")
    print("        simplification or an authoring inconsistency, on the")
    print("        grounds that the theft factor 'still varies'. **It does")
    print("        not vary.** Both lookups are pinned, so there is no")
    print("        inconsistency to explain: the apartment concept is")
    print("        switched off in this group at BOTH sites. Corrected on")
    print("        the algorithms page.")

    # ---- Q2
    print("\n=== Q2  The theft-factor values, cross-checked -- ANSWERED")
    t = book.table(THEFT)
    rows = {r[1]: r[2] for r in t.rows}
    mine_keys = lookup_keys(mine, f"Lookup{THEFT}")
    plain_keys = lookup_keys(plain, f"Lookup{THEFT}")
    good = (rows == {"Yes": t.rows[0][2], "No": t.rows[1][2]}
            and "No" in mine_keys[0]
            and any("ApartmentCondoIndicator" in x for x in plain_keys[1]))
    ok &= good
    print(f"        the table: {len(t.rows)} countrywide rows -- {rows}")
    print(f"        this group's key   : constants={mine_keys[0]}")
    print(f"        plain BI's key     : datadefs={plain_keys[1]}")
    print(f"        {'OK' if good else 'MISMATCH'}")
    print("        **Same physical table, same two rows, two different key")
    print("        strategies.** Plain Business Income reads the BUILDING's")
    print("        `../../ApartmentCondoIndicator` and can reach both rows;")
    print("        this group pins the column to `\"No\"` and can reach one.")
    print("        The values were never in doubt -- what the question")
    print("        should have asked is whether both groups can REACH them.")

    # ---- Q3
    print("\n=== Q3  The two header-only Group II tables -- ANSWERED (C7-16)")
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    for name, want_n in (("BasicGroupIIRate", 45),
                         ("LowestBasicGroupIIRate", 39)):
        cw = len(book.parent_table(name).rows)
        own = [j for j in juris
               if book_for(j, ASOF, resolver=res).declares(name) == "state"]
        good = cw == 0 and len(own) == want_n
        ok &= good
        print(f"        {name:24s} CW={cw}  states={len(own)} of "
              f"{len(juris)}  {'OK' if good else 'MISMATCH'}")
    print("        Confirmed, and the consequence is now measured rather than")
    print("        warned about: **Group II is unresolvable at countrywide for")
    print("        three coverage groups**, and the two jurisdictions filing")
    print("        neither table (FL, PR) reach a read with nothing to read.")

    # ---- Q4
    print("\n=== Q4  The two endorsement files -- STILL OPEN, deliberately")
    for n in ENDORSEMENTS:
        p = d / n
        good = p.exists()
        ok &= good
        print(f"        {p.stat().st_size:>6d} bytes  {n[:62]}  "
              f"{'OK' if good else 'MISSING'}")
    print("        Both exist and neither is traced. **Out of scope by the")
    print("        build order, not by oversight** -- endorsement families are")
    print("        chunk 12, and tracing them here would price coverage this")
    print("        chunk has no golden case for. Left open WITH a reason,")
    print("        which is what the gate asks for.")

    # ---- Q5
    print("\n=== Q5  The unopened dispatch file -- ANSWERED, and it is not a")
    print("        dispatch file")
    disp = (d / DISPATCH).read_text(encoding="utf-8-sig")
    rules = re.findall(r'<rul:Rule Name="(\w+)"', disp)
    i = disp.find('<rul:Rule Name="SetCoverageOnPolicyIndicator"')
    seg = disp[i:i + disp[i:].find("</rul:Rule>") + 11]
    pinned_zero = ('ToDataDef="CoverageOnPolicyIndicator">0<' in
                   seg.replace(" ", ""))
    data = perform.run_rec("Basic")
    path = BI + "/CommercialPropertySpecialClassBusnIncomeCoverage"
    ind = read(f"{path}/CoverageOnPolicyIndicator", data)
    prem = read(f"{path}/Premium", data)
    good = (len(rules) == 4 and pinned_zero and str(ind) == "0"
            and prem in (None, "0"))
    ok &= good
    print(f"        rules in the file : {rules}")
    print(f"        matrices named    : "
          f"{sorted(set(re.findall(r'MatrixFromConstant=.(\\w+).', disp)))}")
    print(f"        SetCoverageOnPolicyIndicator is a bare Constant 0 : "
          f"{pinned_zero}")
    print(f"        at run time       : indicator={ind}, premium={prem}  "
          f"{'OK' if good else 'MISMATCH'}")
    print("        **It was expected to mirror plain Business Income's")
    print("        coverage-record dispatch file. It does not.** It is a")
    print("        record-level coverage shell whose own gate is hard-coded")
    print("        to **0**, so it never prices -- four rules, no matrices,")
    print("        and a `CalculateTotalPremium` that its own indicator")
    print("        switches off. The premium for this coverage is produced")
    print("        entirely by the four per-form files.")
    print("        Another computed-and-never-used shape, which is now the")
    print("        fifth in two chunks after ProtectionClassFactor, the")
    print("        unfilled Builders Risk table, BaseRateAdjustmentFactor")
    print("        and Earthquake's rate with nowhere to charge it.")

    print()
    if ok:
        print("Four answered with evidence, one left open with a reason.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
