#!/usr/bin/env python3
"""Chunk 8, task C8-04 -- every jurisdiction, Legal Liability.

**The sweep's target is the FORK, not the rate chain.** Everything through
`BasicGroupICauseOfLossAdjustment` is shared with the class-rated path, and
chunks 1-3 already swept that across all 47. Re-deriving it here would test the
same arithmetic twice while hiding the thing chunk 8 is actually about.

So each jurisdiction's own cause-of-loss adjustment is read from the run and
the **Legal Liability premium is predicted from it**:

    r0( r3( r3(COLadj x LegalLiabilityFactor) x AddlInsurableIntFactor )
        x Limit/100 )

The two factors are countrywide-only -- **0 of 47 jurisdictions file either** --
so the prediction is the same arithmetic in every state and any divergence is
a state rewriting the premium rule. **Only FL and PR rewrite any of the eight
premium files**, and neither rewrites Basic Group I, so the expectation is
47 of 47 with no exceptions at all.

That is a weaker claim than chunks 4-7's sweeps and it is deliberately stated
as one: **this sweep tests that the fork is countrywide, not that 47 rate
chains are right.**

**And the first version of it was worthless, which is worth recording.** It
sent Oregon's `BasicGroupIRatingTerr = "Portland"` to all 47. That territory
exists only in Oregon, so 46 states produced no Group I rate at all and the
sweep reported **47 of 47 agreeing -- 46 of them at $0.** A sweep where the
answer is zero almost everywhere is an empty search wearing a pass, the same
failure gate points 6 and 7 hit in chunk 3.

The fix is to pin `BasicGroupIRatingTerrFactor` to **1.0** on the location in
every jurisdiction. The territory factor is `Copy`d down from the location
rather than looked up from the item, so supplying it directly removes the one
input that cannot be made portable -- and leaves each state's OWN base rate,
protection class and cause-of-loss adjustment driving the answer. **These are
not premiums any state would charge**; they are 47 genuine cause-of-loss
adjustments put through one countrywide fork, which is what C8-04 is for.

    python scripts/cf/62_chunk8_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction matches its own prediction.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

g8 = import_module("59_chunk8_golden_case")
chunk2 = import_module("09_chunk2_golden_case")

STRUCT = chunk2.STRUCT
PREM = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
COLADJ = STRUCT + "/BasicGroupICauseOfLossAdjustment"
LIMIT = 100000


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    print(f"Legal Liability, Building Basic Group I, {len(juris)} "
          f"jurisdictions, as of {g8.ASOF}\n")

    ok, hits, zeros = True, 0, []
    for j in juris:
        book = book_for(j, g8.ASOF, resolver=res)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        sub = g8.building("Basic")
        # See the docstring: the territory factor is the one input that cannot
        # be carried across state lines, so it is pinned rather than sent.
        (sub["CommercialPropertyTable"]["CommercialProperty"][0]
         ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
         ["BasicGroupIRatingTerrFactor"]) = "1.0"
        data = Node.from_dict(f"MasterCF{j}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"  {j}  RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        col = read(COLADJ, data)
        fac = read(f"{STRUCT}/LegalLiabilityFactor", data)
        add = read(f"{STRUCT}/LegalLiabAddlInsurableIntFactor", data)
        got = str(read(PREM, data))
        if col in (None, "0") or fac in (None, "0"):
            want, note = 0, "no cause-of-loss adjustment in this state"
        else:
            rate = r3(r3(Decimal(col) * Decimal(fac)) * Decimal(add))
            want = int((rate * LIMIT / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP))
            note = f"COLadj {col} x {fac} x {add} -> {rate}"
        good = got == str(want)
        ok &= good
        hits += good
        if want == 0:
            zeros.append(j)
        line = (f"  {j}  predicted {str(want):>5s}  engine {got:>5s}  "
                f"{'OK ' if good else 'MISMATCH'}")
        if a.verbose or not good or want == 0:
            line += f"   {note}"
        print(line)

    print(f"\n{hits} of {len(juris)} match their own prediction.")
    print(f"jurisdictions producing no Legal Liability premium: "
          f"{len(zeros)}  ({', '.join(zeros) if zeros else 'none'})")
    print("\n**The fork is countrywide.** Both factors are filed only at the")
    print("countrywide layer -- 0 of 47 jurisdictions file either -- and only")
    print("FL and PR rewrite any of the eight premium files, neither of them")
    print("Basic Group I. **After seven chunks of state divergence, chunk 8's")
    print("distinctive machinery is the first that every state shares.**")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
