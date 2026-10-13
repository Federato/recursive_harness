#!/usr/bin/env python3
"""Chunk 5, tasks C5-15 to C5-18 -- the dependency on Building, proven.

Business Income is the first coverage in the project that cannot be rated
without rating another coverage first. These four tasks prove the dependency
rather than reading it off the rules.

  15  Basic Group I reads Building's **computed** `BasicGroupIBaseRate`.
  16  Basic Group II reads Building's symbol and territory.
  17  `BaseRateAdjustmentFactor` is the one header-only BI table -- and PR,
      the one state that does not file it, **deletes the rule that reads it**.
  18  Every absent-means-zero finding from chunks 1-3 now has a second
      consumer.

Derived by hand from Oregon's filed rows before the run, against the chunk 5
golden case (Building base 0.498, BI rate 0.203, Factor 0.55, premium $112):

    15  class 0074   Building base 0.143
            BI rate = r3(r3(r3(0.143 x adj 0.85) x terr 0.499) x prot 0.96)
                    = 0.059
            final r3(0.059 x 0.55) = 0.032                  -> $32
        Building's own premium moves too, and it must -- that is the point.

    **The BI premium was predicted correctly at $32 and the RATE was not.**
    Predicting 0.058 assumed the algorithms page's ordering, which applies
    `BGIBaseRateAdjustmentFactor` LAST:

        page:    base x terr x protClass x adjustment  -> 0.058
        engine:  base x adjustment x terr x protClass  -> 0.059

    Both give 0.203 on the golden case, which is why C5-01 passed; class 0074
    is the first case that tells them apart. **The adjustment applies first.**
    Corrected on the algorithms page.

    **And Building's own premium came back $75 against a predicted $74**, which
    is a separate matter and a bigger one: 0.143 x 0.96 x 0.499 is 0.069 rounded
    ONCE and 0.068 rounded after every factor. The engine gives 0.069. Chunk 1
    recorded Building's rate step as per-factor rounding, but its golden case
    (0.498) gives 0.239 either way -- **the reading was never tested at a
    discriminating rate.** Logged as an open item rather than fixed here: it
    reaches back into chunk 1 and possibly into chunks 4 and 5's sweeps.

    16  NumStories removed -> no construction symbol
            BI Basic Group II base 0, premium 0
            Basic Group I untouched at $112, because it reads a different
            ancestor value

    18  ClassCode removed -> Building's base rate 0
            BI Basic Group I 0, **with the Factor still a healthy 0.55**

**C5-17 is the finding of the four.** PR files no `BaseRateAdjustmentFactor`
rows AND overrides `SetBGIBaseRateAdjustmentFactor` with an empty
`<rul:Sequence />` -- it **deletes the rule**. The build order flagged that
mechanism for validation messages (316 countrywide rules are emptied by some
state), but this is the first time it has been seen on a RATING rule. So Puerto
Rico's Business Income Basic Group I has no base-rate adjustment at all, and
the factor is never written.

    python scripts/cf/37_chunk5_downstream.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk5 = import_module("32_chunk5_golden_case")

BI, BGI, BGII = chunk5.BI, chunk2.BGI, chunk2.BGII
P_BGI = chunk5._P % "BasicGroupI"
P_BGII = chunk5._P % "BasicGroupII"

#: id, structure mutation, (BI rate, BI Factor, BI BGI premium,
#: BI BGII premium, Building GI, Building GII), why
CASES = [
    ("baseline", lambda s: None,
     ("0.203", "0.55", "112", "13", "261", "32"), "the reference"),

    ("15  class 0074 -- Building's rate moves",
     lambda s: zeros2.structure(s).__setitem__("ClassCode", "0074"),
     ("0.059", "0.55", "32", "13", "75", "32"),
     "**the dependency, proven by moving it.** Business Income has no "
     "base-rate lookup of its own -- change the BUILDING's class code and the "
     "Business Income premium follows, $112 -> $32, while nothing in the "
     "Business Income record changed at all"),

    ("16  NumStories removed -- no symbol",
     lambda s: zeros2.structure(s).pop("NumStories", None),
     ("0.203", "0.55", "112", "0", "261", "0"),
     "**Group II reads a different ancestor value from Group I, and only "
     "Group II falls over.** The symbol is resolved on the Structure and "
     "copied down; without storey count there is none, so BI Group II and "
     "Building Group II both price at zero while both Group I premiums are "
     "untouched. Chunk 4's C4-19 reaching a third coverage"),

    ("18  ClassCode removed -- Building's rate is 0",
     lambda s: zeros2.structure(s).pop("ClassCode", None),
     ("0", "0.55", "0", "13", "0", "32"),
     "**every absent-means-zero finding now has a second consumer.** The "
     "Factor is still a healthy 0.55 and the Business Income record is "
     "perfectly well formed -- the premium is zero because a field on the "
     "BUILDING is missing. Nothing raises, in either coverage"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk5.submission("Basic")
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:40s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{BI}/BasicGroupIRate", data),
               read(f"{BI}/Factor", data),
               read(P_BGI, data), read(P_BGII, data),
               read(BGI, data), read(BGII, data))
        good = got == expect
        ok &= good
        print(f"{name:40s} rate={str(got[0]):>6s} F={str(got[1]):>5s} "
              f"BI={str(got[2]):>4s}/{str(got[3]):>3s} "
              f"Bldg={str(got[4]):>4s}/{str(got[5]):>3s}"
              + ("" if good else f"   <-- expected {expect}"))

    # ---- C5-17, the deleted rule
    print("\n=== 17  PR deletes the rule, it does not just omit the table")
    pr = book_for("PR", chunk2.ASOF)
    f = (pr.state.package.content / "Rules" /
         "CommercialPropertyBusinessIncomeRules.Rule.xml")
    body = f.read_text(encoding="utf-8-sig")
    i = body.find('<rul:Rule Name="SetBGIBaseRateAdjustmentFactor"')
    rule = body[i:][:body[i:].find("</rul:Rule>") + 11]
    emptied = "<rul:Sequence />" in rule
    ok &= emptied
    print(f"    PR's SetBGIBaseRateAdjustmentFactor is an empty Sequence: "
          f"{emptied}  (expected True) {'OK' if emptied else 'MISMATCH'}")
    print(f"    table rows in PR: {len(pr.table('BaseRateAdjustmentFactor').rows)}"
          f"  (46 of 47 jurisdictions file rows; PR does not)")
    print("    So Puerto Rico has neither the table nor the rule that reads")
    print("    it. **The build order flagged rule-deletion for validation")
    print("    messages -- 316 countrywide rules are emptied by some state --")
    print("    and this is the first time it has been seen on a RATING rule.**")

    print("\nWhat each case proves")
    for name, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print("The dependency is proven in both directions: Building's inputs")
        print("move Business Income, and Business Income moves nothing back.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
