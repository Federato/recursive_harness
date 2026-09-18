#!/usr/bin/env python3
"""Chunk 6, tasks C6-20 to C6-23 -- four claims about three forms.

  20  **The fire-only gate is narrower than Building's** -- two strings, not
      four -- and the two Building tests that are missing here are the two
      that name sprinkler leakage, which Special Class has no concept of.
  21  **Group II's coinsurance surcharge comes from a DIFFERENT table**, and
      Florida proves it: 1.42 where Group I takes 1.50.
  22  **Broad is construction-blind** -- six construction types, one rate --
      while Building's Broad moves on the identical change.
  23  **Special reads Building's unfilled `SpecialBuildingRate`**, and there is
      no Builders Risk branch at all.

All figures derived by hand from the filed rows before the run.

    20  OR, Basic Group II, baseline $209, Group I $66 THROUGHOUT
          "Fire"                                    -> 0       $0
          "Fire and Vandalism"                      -> 0       $0
          "Fire and Sprinkler Leakage"              -> 0.224   $209   <- NOT gated
          "Fire, Vandalism and Sprinkler Leakage"   -> 0.224   $209   <- NOT gated
        and on a BUILDING the last two DO zero Group II, from $32.

    21  OR 50%   Group I 1.5 (LessThan80Pct)   Group II 1.5 (Flat)   same number
        FL 50%   Group I 1.5                  Group II **1.42**     different
        OR Group II at 50%: r3(0.224x1.5)=0.336 x .98 -> 0.329       $329

    22  Frame / Joisted Masonry / Non-Combustible / Masonry Non-Combustible /
        Modified Fire Resistive / Fire Resistive  ->  $14 every time.
        Building's Broad reads the same table on the item's real construction
        and moves 0.015 -> 0.010.

    23  ClassCode 1150 -> SpecialBaseRate still 0.047 -> $44.
        `SpecialBuildersRiskRate` is named 6 times in the Structure ruleset
        and **0 times** in this one.

    python scripts/cf/47_chunk6_forms.py

Exit 0 when every case matches its derivation.
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

chain = import_module("45_chunk6_description_chain")
g = import_module("41_chunk6_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")

SC, ASOF = g.SC, g.ASOF
P = {f: g._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
RULES = "CommercialPropertySpecialClassRules.Rule.xml"

#: C6-20. Building's gate tests four strings; Special Class's tests two.
FIRE = [
    ("Basic (baseline)", "209", "the reference"),
    ("Fire", "0", "gated -- the first of the two strings this rule tests"),
    ("Fire and Vandalism", "0", "gated -- the second"),
    ("Fire and Sprinkler Leakage", "209",
     "**not gated here, and gated on a Building.** Special Class's Basic "
     "Group I has no sprinkler-leakage term anywhere, so there is nothing for "
     "this cause of loss to switch off"),
    ("Fire, Vandalism and Sprinkler Leakage", "209",
     "**the same, and the starker of the two** -- vandalism IS a Special "
     "Class concept and sprinkler leakage is not, so the combined string "
     "falls outside a gate that catches plain \"Fire and Vandalism\""),
]

#: C6-22. **Two constructions known to be LEGAL**, not six strings copied out
#: of the rate table's key column. The first draft of this test sent all six of
#: `BroadFormBaseRate`'s `Bldg` values and watched Special Class hold at $14 --
#: which proves nothing, because four of those six are not values
#: `ConstructionTypeToUse` ever resolves to. On a Building, `"Fire Resistive"`
#: resolves to NOTHING (construction code 0, base rate 0); the legal value is
#: the long form below. **A test that sends an unrecognised string and reports
#: "unchanged" cannot tell construction-blindness from a bad input** -- so both
#: strings here are pinned by Building moving on the identical change.
FR = "Fire Resistive - Reinforced Masonry - Light Steel"
CONSTRUCTIONS = ["Frame", FR]


def building(col):
    """Chunk 2's building alone, at a chosen cause of loss."""
    sub = chunk2.submission()
    zeros2.structure(sub)["CauseOfLoss"] = col
    ip = Interpreter(book_for(chunk2.JURIS, chunk2.ASOF), rounding=ROUNDING,
                     trace=False, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    return data


def main() -> int:
    ok = True

    # ---- C6-20
    print("=== 20  The fire-only gate -- two strings here, four on a Building\n")
    for col, want, _ in FIRE:
        data = chain.run("OR", {"CauseOfLoss": col})
        gii = str(read(P["BasicGroupII"], data))
        gi = str(read(P["BasicGroupI"], data))
        good = gii == want and gi == "66"
        ok &= good
        print(f"  {col:38s} Group II={gii:>4s}  Group I={gi:>3s} "
              f"(expected {want} / 66) {'OK' if good else 'MISMATCH'}")
    print("\n  ...and the same two strings ON A BUILDING:")
    for col, want in (("Basic", "32"), ("Fire and Sprinkler Leakage", "0"),
                      ("Fire, Vandalism and Sprinkler Leakage", "0")):
        data = building(col)
        got = str(read(chunk2.BGII, data))
        good = got == want
        ok &= good
        print(f"  {col:38s} Building Group II={got:>3s} (expected {want}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("  **The same cause of loss zeroes a Building's Group II and leaves")
    print("  a Special Class item's alone.** Two coverages, one submission")
    print("  field, opposite answers -- and the reason is that Special Class")
    print("  never introduced sprinkler leakage, so it has nothing to exclude.")

    # ---- C6-21
    print("\n=== 21  Group II's coinsurance comes from a DIFFERENT table")
    rows = []
    for state, coins in (("OR", "90%"), ("OR", "50%"), ("FL", "50%")):
        data = chain.run(state, {"Coinsurance": coins})
        rows.append((state, coins,
                     str(read(f"{SC}/CoinsuranceFactor", data)),
                     str(read(f"{SC}/BasicGroupIICoinsuranceFactor", data)),
                     str(read(P["BasicGroupII"], data))))
    expect = [("OR", "90%", "0.95", "0.95", "209"),
              ("OR", "50%", "1.5", "1.5", "329"),
              ("FL", "50%", "1.5", "1.42", None)]
    for got, want in zip(rows, expect):
        good = all(w is None or gv == w for gv, w in zip(got, want))
        ok &= good
        print(f"  {got[0]} {got[1]:>4s}   Group I factor={got[2]:>5s}   "
              f"Group II factor={got[3]:>5s}   Group II premium={got[4]:>4s}"
              + ("" if good else f"   <-- expected {want}"))
    print("  **Countrywide the two tables file the same 1.5, so nothing in an")
    print("  Oregon premium could tell them apart.** Florida files its own")
    print("  `BasicGroupIIFlatCoinsuranceFactor` at 1.42 and leaves")
    print("  `LessThan80PctMultiplicativeFactor` countrywide -- so in Florida")
    print("  the two Basic forms take DIFFERENT coinsurance surcharges from")
    print("  one apparent concept. And note the direction: Group II at 50%")
    print("  costs $329 against 90%'s $209. A lower coinsurance is a higher")
    print("  premium in both forms.")
    pr = book_for("PR", ASOF)
    n_flat = len(pr.table("BasicGroupIIFlatCoinsuranceFactor").rows)
    n_lt80 = len(pr.table("LessThan80PctMultiplicativeFactor").rows)
    good = n_flat == 0 and n_lt80 == 0
    ok &= good
    print(f"  PR declares BOTH tables header-only ({n_flat} and {n_lt80} rows) "
          f"{'OK' if good else 'MISMATCH'}")
    print("  -- a state with no coinsurance surcharge of any kind, by filing")
    print("  two empty tables rather than by changing a rule.")

    # ---- C6-22
    print("\n=== 22  Broad is construction-blind")
    for ct in CONSTRUCTIONS:
        data = chain.run("OR", {"CauseOfLoss": "Broad", "ConstructionType": ct})
        base = str(read(f"{SC}/BroadBaseRate", data))
        got = str(read(P["Broad"], data))
        good = (base, got) == ("0.015", "14")
        ok &= good
        print(f"  {ct:50s} base={base:>6s}  premium={got:>3s}"
              + ("" if good else "   <-- expected 0.015 / 14"))
    print("  `LookupBroadFormBaseRate` keys on the hardcoded literal")
    print("  `\"Frame\"`, so the table's two Fire Resistive rows at 0.010 are")
    print("  filed, published and unreachable on this path -- along with")
    print("  Joisted Masonry, Non-Combustible and Masonry Non-Combustible,")
    print("  which file 0.015 and would have made no difference anyway.")
    print("  **ISO confirmed this independently** in C6-08: the same item")
    print("  re-sent as Fire Resistive came back at $14 again.")
    # **$12, and $11 was predicted.** Scaling Frame's $16 by the base-rate
    # ratio 0.010/0.015 gives 10.7 -> $11. The chain rounds to 3 decimals at
    # EVERY step, and at rates this small the rounding dominates the ratio:
    # Frame's final rate is 0.016 and Fire Resistive's is 0.012, a ratio of
    # 0.75 where the base rates are 0.667 apart. **A two-thirds rate does not
    # produce a two-thirds premium**, and that is worth recording next to the
    # project's open per-step-vs-once rounding question.
    for ct, want in (("Frame", "16"), (FR, "12")):
        sub = chunk2.submission()
        st = zeros2.structure(sub)
        st["CauseOfLoss"], st["ConstructionType"] = "Broad", ct
        ip = Interpreter(book_for(chunk2.JURIS, chunk2.ASOF), rounding=ROUNDING,
                         trace=False, null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        ip.run(data)
        path = (chunk2.STRUCT
                + "/CommercialPropertyStructureBuildingBroadCoverage/Premium")
        got = str(read(path, data))
        good = got == want
        ok &= good
        print(f"  BUILDING's Broad, {ct[:22]:24s} premium={got:>3s} "
              f"(expected {want}) {'OK' if good else 'MISMATCH'}")
    print("  **Building moves and Special Class does not, on the same two")
    print("  strings** -- which is what makes the Special Class result mean")
    print("  something. Both values are legal; only one coverage reads them.")

    # ---- C6-23
    print("\n=== 23  Special reads Building's table, and has no Builders Risk")
    book = book_for("OR", ASOF)
    d = book.parent.package.content / "Rules"
    mine = (d / RULES).read_text(encoding="utf-8-sig")
    theirs = (d / "CommercialPropertyStructureRules.Rule.xml").read_text(
        encoding="utf-8-sig")
    a, b = mine.count("SpecialBuildersRiskRate"), theirs.count(
        "SpecialBuildersRiskRate")
    good = a == 0 and b > 0
    ok &= good
    print(f"  `SpecialBuildersRiskRate` named in the SpecialClass ruleset : {a}"
          f"   (expected 0)")
    print(f"  ...in the Structure ruleset                                 : {b}"
          f"   (expected > 0)  {'OK' if good else 'MISMATCH'}")
    for cc, want in (("1150", "44"), ("0951", "44")):
        data = chain.run("OR", {"CauseOfLoss": "Special", "ClassCode": cc})
        base = str(read(f"{SC}/SpecialBaseRate", data))
        got = str(read(P["Special"], data))
        good = (base, got) == ("0.047", want)
        ok &= good
        print(f"  ClassCode {cc}: base={base:>6s} premium={got:>3s} "
              f"(expected 0.047 / {want}) {'OK' if good else 'MISMATCH'}")
    print("  **Class 1150 is Building's Builders Risk trigger and it does")
    print("  nothing here.** Building branches to its own table on that code;")
    print("  Special Class always resolves through `LookupSpecialBuildingRate`.")
    for j in ("FL", "PR"):
        bk = book_for(j, ASOF)
        n = len(bk.table("SpecialBuildingRate").rows)
        where = bk.declares("SpecialBuildingRate")
        good = n == 0 and where == "countrywide"
        ok &= good
        print(f"  {j}: reads the {where} `SpecialBuildingRate` -- {n} rows "
              f"{'OK' if good else 'MISMATCH'}")
    print("  **The countrywide table is header-only**, so the two states that")
    print("  file no rows of their own cannot price the Special form at all --")
    print("  the same gap chunk 3 found on Building, now with a second")
    print("  consumer and the same two states.")

    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
