#!/usr/bin/env python3
"""Chunk 3, gate point 7 -- the theft exclusion record, elected and priced.

The census (`05_exclusion_records.py`) says which endorsement record each
datadef group tests. **This proves the one it names for our group is the one
the Special chain actually reads**, which a census alone cannot show.

Theft is chunk 3's exclusion, and it is filed per coverage: five distinct
records across seven datadef groups. Ours is `CommercialPropertyTheftExclusion`
-- form **CP 10 33** -- and the countrywide credit is **0.88**, a 12% discount
for excluding theft.

Derivation, written before the run, from the Oregon golden case:

    without the record   SpecialTheftExclusionIndicator = 0
                         SpecialTheftExclusionFactor    = 1.0
                         premium                        = $54   (golden case)

    with the record      indicator = 1, factor = 0.88
                         coladj   = r3(r3(0.047 x 0.88) x roofACV 1.0) = 0.041
                         adjusted = r3(r3(0.041 x 0.95) x 1.237)       = 0.048
                         final    = r3(r3(0.048 x 1) x 0.97)           = 0.047
                         premium  = 0.047 x 100,000 / 100              = $47

**Broad must not move.** It has no theft dimension at all -- its deductible
rule is the four-way `Choose` without one -- so a theft election that changed
the Broad premium would mean the two forms share machinery neither document
says they share.

    python scripts/cf/18_chunk3_theft_exclusion.py

Exit 0 when both forms match.
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
chunk3 = import_module("15_chunk3_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII
BROAD, SPECIAL = chunk3.BROAD, chunk3.SPECIAL

#: The record the census names for `CommercialPropertyStructure`. Written as
#: the table ISO files it under, so that electing the WRONG one -- any of the
#: other four in the family -- fails rather than quietly doing nothing.
RECORD = "CommercialPropertyTheftExclusion"

CASES = [
    ("no theft exclusion elected", False,
     {"ind": "0", "factor": "1", "special": "54", "broad": "16"}),
    (f"{RECORD} attached (CP 10 33)", True,
     {"ind": "1", "factor": "0.88", "special": "47", "broad": "16"}),
]


def submission(form, elect):
    sub = chunk3.submission(form)
    if elect:
        # The record is a CHILD OF THE STRUCTURE, not of the policy -- which is
        # the whole point of gate point 7. Attaching it at the wrong level is
        # the failure mode a single policy-wide "theft excluded?" control
        # produces, and it would price at 54 with nothing raised.
        zeros2.structure(sub)[f"{RECORD}Table"] = {RECORD: [{}]}
    return sub


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for label, elect, want in CASES:
        print(f"=== {label}")
        for form in ("Special", "Broad"):
            ip = Interpreter(book, rounding=ROUNDING, trace=False,
                             null_arithmetic=NULL_ARITHMETIC)
            data = Node.from_dict(f"MasterCF{chunk2.JURIS}",
                                  submission(chunk3.FORMS[form]["col"], elect))
            try:
                ip.run(data)
            except Exception as exc:
                print(f"    {form:8s} RAISED {type(exc).__name__}: {exc}")
                ok = False
                continue
            got = read(BROAD if form == "Broad" else SPECIAL, data)
            good = got == want[form.lower()]
            ok &= good
            line = f"    {form:8s} premium = {str(got):>4s}  " \
                   f"(expected {want[form.lower()]:>4s}) " \
                   f"{'OK' if good else 'MISMATCH'}"
            if form == "Special":
                ind = read(f"{STRUCT}/SpecialTheftExclusionIndicator", data)
                fac = read(f"{STRUCT}/SpecialTheftExclusionFactor", data)
                igood = ind == want["ind"] and fac == want["factor"]
                ok &= igood
                line += f"   indicator={ind} factor={fac}" \
                        f"{'' if igood else '  <-- expected ' + want['ind'] + '/' + want['factor']}"
            print(line)
        print()

    print("What this proves, beyond the census")
    print("  * The record the census names for `CommercialPropertyStructure`")
    print("    is the one the Special chain reads. A census can only say which")
    print("    record a rule TESTS; this says the election reaches the premium.")
    print("  * The record hangs off the STRUCTURE, not the policy. A single")
    print("    policy-wide 'theft excluded?' control would attach it in the")
    print("    wrong place, price at 54, and raise nothing at all.")
    print("  * Broad does not move. It has no theft dimension -- its deductible")
    print("    rule is the four-way Choose without one -- and the two forms")
    print("    share an LOI table but not this.")
    if ok:
        print("\nBoth cases match.")
        return 0
    print("\nMISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
