#!/usr/bin/env python3
"""Chunk 4, tasks C4-02, C4-10 and C4-11 -- the first repeating group.

Building rates one Structure. Personal Property rates **N records per Occupancy
Class**, driven by a `ForEach`, each running the full four-chain build-up. Every
case in chunks 1-3 was a single record, so nothing yet proves the engine rates a
collection and sums it.

Three things, all derived by hand from Oregon's filed rows before the run.

**C4-10 -- two records must both rate, and must sum.**
Two items at 100,000 and 50,000 under one occupancy class:

    OccupTotalLOIToUse = 150,000    -> LOI 0.842 (NOT each item's own limit)
    location total     = 250,000    -> deductible 0.99
    each record  rate 0.263 -> adjusted r3(0.250 x 0.842) = 0.211
                 final r3(0.211 x 0.99)                   = 0.209
    premiums     0.209 x 1,000 = $209  and  0.209 x 500 = $105
    total                                                 = $314

**The LOI factor is the OCCUPANCY's, not the item's** -- both records take
0.842 off a 150,000 occupancy total, and neither takes the 0.898 or 1.000 its
own limit would give. That is the substantive claim in this case, and it is
what makes two small items priced differently from one large one.

**C4-11 -- the ForEach must not leak values between records.**
Two items of 50,000 each, differing only in `CovType`, which drives the
Personal-Property-only fire-safe vault factor:

    Personal Property                 vault 1.0 -> rate 0.263 -> final 0.223 -> $112
    ...in a Vault with an Approved
       Fire Rating                    vault 0.5 -> rate 0.131 -> final 0.110 -> $55
    total                                                                     = $167

If a datadef were written once and not cleared per iteration, record 2 would
reuse record 1's rate and the total would be $224 -- a plausible number with no
error anywhere. **The rates are asserted per record**, not just the total,
because the total alone cannot tell the two apart.

**The first draft varied the class code instead, and that was the wrong
instrument.** `SetBldgClassCode` is a `Copy` from `../../BldgClassCode` -- the
OCCUPANCY CLASS's field -- so a per-item class code in the submission is
overwritten and both records legitimately rate at the same base rate. That is
not a leak; it is the same shape as `CovForm`. **Class code is an occupancy
attribute, not an item attribute**, and contents items within one class cannot
differ by it. Asserted below in its own right.

**C4-02 -- and no new interpreter node.** Chunks 1, 2 and 3 all ran on chunk 0's
foundation unchanged. If a repeating group needed one, that would be the finding.

    python scripts/cf/23_chunk4_foreach.py

Exit 0 when every record, and every total, matches.
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
chunk4 = import_module("22_chunk4_golden_case")

BGI, BGII = chunk2.BGI, chunk2.BGII
OCCUP, PP = chunk4.OCCUP, chunk4.PP
PREM = "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium"

VAULT_NO = "Personal Property"
VAULT_YES = "Personal Property in a Vault with an Approved Fire Rating"

#: id, [(limit, CovType)], [(watched value, final rate, premium)], total, why
CASES = [
    ("C4-10  two items, 100,000 and 50,000",
     [(100000, VAULT_NO), (50000, VAULT_NO)],
     [("1", "0.209", "209"), ("1", "0.209", "105")], "314",
     "both take LOI 0.842 off the 150,000 OCCUPANCY total -- neither uses the "
     "0.898 or 1.000 its own limit would give. Two small items are not priced "
     "as one large one"),

    ("C4-11  two items, 50,000 each, different CovType",
     [(50000, VAULT_NO), (50000, VAULT_YES)],
     [("1", "0.223", "112"), ("0.5", "0.11", "55")], "167",
     "a leaking ForEach would give record 2 record 1's rate and a total of "
     "$224 -- plausible, with no error anywhere. `FireSafeVaultFactor` is "
     "asserted PER RECORD because the total alone cannot tell them apart"),

    ("control  one item, 100,000 (chunk 4's golden case)",
     [(100000, VAULT_NO)],
     [("1", "0.223", "223")], "223",
     "the single-record figure the other two are read against"),
]


def submission(items):
    """Chunk 4's golden case with N Personal Property records, not one."""
    sub = chunk4.submission("Basic")
    st = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
          ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
          ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    occ = st["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
    proto = occ["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][0]
    occ["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"] = [
        # `CovType` is a genuine per-item field. A per-item `BldgClassCode`
        # would be overwritten by the occupancy class's -- see the docstring.
        dict(proto, Limit=str(limit), CovType=cov)
        for limit, cov in items]
    return sub


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, items, expect, total, why in CASES:
        print(f"=== {name}")
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", submission(items))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"    RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue

        # Each record is addressed by index -- which is also how a leak would
        # become visible. A sum alone cannot tell two records apart.
        running = 0
        for i, ((limit, cov), (base, final, prem)) in enumerate(
                zip(items, expect)):
            got = tuple(read(f"{PP}[{i + 1}]/{dd}", data)
                        for dd in ("FireSafeVaultFactor",
                                   "FinalBasicGroupIRate"))
            gp = read(f"{PP}[{i + 1}]{PREM}", data)
            good = got == (base, final) and gp == prem
            ok &= good
            running += int(gp) if gp and gp.lstrip("-").isdigit() else 0
            print(f"    record {i + 1}  limit {limit:>7,d}  "
                  f"{'vault' if cov is VAULT_YES else 'plain'}  "
                  f"vaultFactor={str(got[0]):>4s} final={str(got[1]):>6s} "
                  f"premium={str(gp):>4s}   "
                  f"(expected {base}/{final}/{prem}) "
                  f"{'OK' if good else 'MISMATCH'}")
        tgood = str(running) == total
        ok &= tgood
        print(f"    {'sum of the records':>34s} = {running:>4d}   "
              f"(expected {total:>4s}) {'OK' if tgood else 'MISMATCH'}")

        for label, path, want in (("BUILDING Group I ", BGI, "263"),
                                  ("BUILDING Group II", BGII, "32")):
            g = read(path, data)
            bgood = g == want
            ok &= bgood
            print(f"    {label} = {str(g):>5s}   (expected {want})"
                  f" {'OK' if bgood else 'MISMATCH'}  -- must not move")
        print(f"    -> {why}\n")

    # The class-code finding, asserted rather than left in prose.
    print("=== C4-11b  a per-item class code is OVERWRITTEN by the occupancy's")
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    sub = submission([(50000, VAULT_NO), (50000, VAULT_NO)])
    occ = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
           ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
           ["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0])
    occ["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][1]["BldgClassCode"] = "0074"
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    for i in (1, 2):
        g = read(f"{PP}[{i}]/BasicGroupIBaseRate", data)
        good = g == "0.548"
        ok &= good
        print(f"    record {i} base rate = {g}   (expected 0.548, the "
              f"OCCUPANCY's class 0951) {'OK' if good else 'MISMATCH'}")
    print("    Record 2 asked for class 0074 and got 0951's rate.")
    print("    `SetBldgClassCode` is a Copy from `../../BldgClassCode`, so the")
    print("    class code is an OCCUPANCY attribute -- items within one class")
    print("    cannot differ by it, and a submission that tries is silently")
    print("    overruled.\n")

    print("C4-02: all four chains ran, over a repeating group, with NO new")
    print("interpreter node -- the fourth coverage on chunk 0's foundation.")
    if ok:
        print("\nEvery record and every total matches.")
        return 0
    print("\nMISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
