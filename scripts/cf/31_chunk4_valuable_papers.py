#!/usr/bin/env python3
"""Chunk 4, task C4-29 -- the Valuable Papers carve-out, enumerated and priced.

`CovType = "Valuable Papers and Records - Other Than Electronic Data"` zeroes
the Contents rate, so that a separately rated coverage type does not rate twice.
Building has no such `CovType` and no equivalent gate anywhere.

**The task list said "three of the four forms". It is all four -- what differs
is WHERE the carve-out sits**, and that is the thing worth proving:

    Basic Group I    SetBasicGroupICauseOfLossAdjustment   -> the ADJUSTMENT
    Basic Group II   SetBasicGroupIICauseOfLossAdjustment  -> the ADJUSTMENT
    Special          SetSpecialCauseOfLossAdjustment       -> the ADJUSTMENT
    Broad            SetBroadRate                          -> the RATE ITSELF

Broad has no cause-of-loss adjustment step to put it in -- C4-22 and chunk 3
both established that -- so the carve-out moves one step earlier into the rate.
The premium is zero either way; the difference is what a trace shows, and
whether the rate above it still looks healthy.

Enumerated across the whole Personal Property ruleset, the literal appears in
**seven** rules: the four above, plus `SetEQCauseOfLossAdjustment` (Earthquake,
chunk 10) and the two theft-limitation adjusted-rate rules (chunk 12). A
`SetSpecialCauseOfLossAdjustment` in the Household Personal Property ruleset
carries it too.

Derived by hand before the run, on chunk 4's golden case:

    Basic    rate 0.263 INTACT, adjustment 0.0 -> $0   (and Group II likewise)
    Broad    rate 0.0 outright                 -> $0
    Special  rate 0.186 INTACT, adjustment 0.0 -> $0

    python scripts/cf/31_chunk4_valuable_papers.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import re
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
chunk4 = import_module("22_chunk4_golden_case")
zeros4 = import_module("25_chunk4_zero_cases")

PP = chunk4.PP
VP = "Valuable Papers and Records - Other Than Electronic Data"
_P = PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"

#: cause of loss, rate datadef, adjustment datadef, (rate, adjustment,
#: premium) with the carve-out ON, and the baseline premium, why
CASES = [
    ("Basic", "BasicGroupIRate", "BasicGroupICauseOfLossAdjustment",
     _P % "BasicGroupI", ("0.263", "0", "0"), "223",
     "**the rate survives and the adjustment is zeroed.** 0.263 is exactly the "
     "figure the golden case produced, so everything upstream of the "
     "cause-of-loss step is untouched -- a trace shows a healthy rate above a "
     "zero premium"),

    ("Basic", "BasicGroupIIRate", "BasicGroupIICauseOfLossAdjustment",
     _P % "BasicGroupII", ("0.03", "0", "0"), "24",
     "Group II the same way, in its own adjustment rule"),

    ("Broad", "BroadRate", None, _P % "Broad", ("0", None, "0"), "16",
     "**Broad zeroes the RATE, not an adjustment** -- it has no cause-of-loss "
     "step to put the carve-out in, so it moves one rule earlier. Same zero "
     "premium, a different thing visible in the trace"),

    ("Special", "SpecialRate", "SpecialCauseOfLossAdjustment",
     _P % "Special", ("0.186", "0", "0"), "137",
     "Special keeps its rate at 0.186 and zeroes the adjustment, like the two "
     "Basic groups -- so Broad is the odd one out among the four"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True

    # The census first: a negative claim has to state what was enumerated.
    d = book.parent.package.content / "Rules"
    rules = set()
    for f in sorted(d.glob("*PersonalProperty*.Rule.xml")):
        t = f.read_text(encoding="utf-8-sig")
        if VP not in t:
            continue
        for m in re.finditer(r'<rul:Rule Name="([A-Za-z]+)"', t):
            i = m.start()
            end = t[i:].find("\n\t</rul:Rule>")
            if VP in t[i:i + end]:
                rules.add(m.group(1))
    print(f"Rules carrying the literal, Personal Property side: {len(rules)}")
    for r in sorted(rules):
        print(f"    {r}")
    good = len(rules) == 7
    ok &= good
    print(f"    (expected 7) {'OK' if good else 'MISMATCH'}\n")

    for col, rate_dd, adj_dd, prem_path, expect, baseline, why in CASES:
        sub = chunk4.submission(col)
        zeros4.item_of(sub)["CovType"] = VP
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{col:8s} {rate_dd:28s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{PP}/{rate_dd}", data),
               read(f"{PP}/{adj_dd}", data) if adj_dd else None,
               read(prem_path, data))
        good = got == expect
        ok &= good
        print(f"{col:8s} {rate_dd:28s} rate={str(got[0]):>6s} "
              f"adj={str(got[1]):>5s} premium={str(got[2]):>2s}  "
              f"(baseline was ${baseline})"
              + ("" if good else f"   <-- expected {expect}"))

    print("\nWhat each case proves")
    for col, rate_dd, _, _, _, _, why in CASES:
        print(f"\n  {col} / {rate_dd}\n    " + why.replace("**", ""))
    print()
    if ok:
        print("All four forms carve out Valuable Papers, and Broad does it one")
        print("rule earlier than the other three.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
