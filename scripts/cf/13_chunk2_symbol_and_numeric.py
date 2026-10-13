#!/usr/bin/env python3
"""Chunk 2, tasks 4 and 5 -- the symbol overrides, and the numeric value.

Two pieces of Group II machinery that chunk 2's golden case reaches but never
exercises, because class 0951 in Frame construction takes the plain path
through both.

**The symbol overrides.** `BasicGroupIISymbolToUse` normally comes from
construction type + storeys, but four branches replace it, tested in this
order:

    1  SuperiorRoofingIndicator = Yes   -> roof-construction table
    2  OpenSides = Yes                  -> the "OpenSides" pseudo-class
    3  ClassCodeToUse in 0580/0585/1300/1650
    4  ClassCodeToUse in 1751/1752      -> oil distributing stations

Symbol drives the base rate, so an override is a different rate table row:
Oregon files AA 0.015, A 0.016, AB 0.024, B 0.028.

**The numeric value.** Group II's analogue of Group I's protection-class
factor, loading occupancy and open-sides hazard. It is 1.0 on the golden case
and can be **4** -- which quadruples the rate -- or **0**, which removes the
premium entirely.

    python scripts/cf/13_chunk2_symbol_and_numeric.py

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
zeros = import_module("10_chunk2_zero_cases")

STRUCT, BGII = chunk2.STRUCT, chunk2.BGII

#: A construction type whose BASE symbol and ROOF-OVERRIDE symbol differ. Most
#: of the eight Superior Roofing variants map to the same symbol either way, so
#: the override is invisible on them; this one is AA normally and A overridden.
SUPERIOR = ("Masonry Non-Combustible - Reinforced - Other Than Light Steel "
            "- Superior Roofing")
#: A detailed type that resolves for BOTH groups: construction code 4 and
#: Group II symbol A.
MNC_DETAILED = "Masonry Non-Combustible - Reinforced - Other Than Light Steel"


def set_fields(**kw):
    def mut(sub):
        zeros.structure(sub).update(kw)
    return mut


#: id, mutation, (symbol, numeric, base, rate, BGII premium), what it proves
#: Group I is reported alongside, because several of these move it too.
CASES = [
    ("S0  baseline -- plain path", lambda s: None,
     ("B", "1", "0.028", "0.027", "32"),
     "class 0951 in Frame takes neither an override nor a numeric value"),

    ("S1  OpenSides = Yes", set_fields(OpenSides="Yes"),
     ("B", "4", "0.028", "0.108", "127"),
     "**two things at once, and only one is visible in the symbol.** The "
     "symbol override fires -- but `OpenSides`/construction 1 resolves to B, "
     "the same symbol the base table gives, so the rate row does not move. "
     "What moves the premium is the NUMERIC VALUE going to 4: the premium "
     "very nearly quadruples, 32 to 127"),

    ("S2  class 0580 (Frame)",
     set_fields(ClassCode="0580"),
     ("B", "4", "0.028", "0.108", "127"),
     "the class-code branch. Same arithmetic as S1 by a different route -- "
     "symbol still B, numeric value 4 from the class/construction table"),

    ("S3  bare 'Masonry Non-Combustible'",
     set_fields(ConstructionType="Masonry Non-Combustible"),
     ("", "1", "0", "0", "0"),
     "**not a valid construction type, and nothing says so.** The six bare "
     "names -- Frame, Joisted Masonry, Non-Combustible, Masonry "
     "Non-Combustible, Modified Fire Resistive, Fire Resistive -- are what "
     "`ConstructionTypeToUse` RESOLVES TO, not what may be submitted. Submit "
     "one and the construction code is 0, the Group II symbol is absent, and "
     "**both** Group I and Group II price at zero. Only `Frame` happens to be "
     "spelled identically in both vocabularies, which is the one reason chunk "
     "2's golden case rates two coverages from one building.\n"
     "    **ISO does NOT return zero here -- it rejects the submission**, and "
     "the difference is a contract question rather than a data one:\n"
     "        400  Matrix: ConstructionTypeToUse, Keys: CW, Masonry\n"
     "             Non-Combustible. No results have been returned.\n"
     "    That lookup's countrywide pass is `ResultMode=\"SingleResult\"`. ISO "
     "treats a SingleResult matching ZERO rows as an error; this engine treats "
     "it as null and lets it flow, raising only when it matches MORE than one. "
     "Open item -- changing it touches shared code and General Liability, so "
     "it needs its own measured pass, exactly as the null-arithmetic question "
     "did"),

    ("S4  oil distributing station (1751)",
     set_fields(ClassCode="1751"),
     ("AB", "1", "0.024", "0.023", "27"),
     "the fourth override branch: class 1751/1752 get symbol AB outright, "
     "from a one-row table keyed on a constant. The symbol moves B->AB so the "
     "base rate moves 0.028->0.024. Worth noting these are the same two class "
     "codes chunk 1's literal census found bypassing Group I's "
     "protection-class factor"),

    ("S5  detailed construction type", set_fields(ConstructionType=MNC_DETAILED),
     ("A", "1", "0.016", "0.015", "18"),
     "the detailed names ARE the submittable vocabulary: 25 of them, and this "
     "one resolves to construction code 4 for Group I and symbol A for Group "
     "II. Both coverages rate"),

    ("S6  superior roofing variant", set_fields(ConstructionType=SUPERIOR),
     ("AA", "1", "0.015", "0.014", "16"),
     "**the roof-construction override does NOT fire here, and the reason is "
     "structural.** `SuperiorRoofingIndicator` is correctly derived to Yes, "
     "and the roof table maps this type to symbol A -- but the roof branch is "
     "nested INSIDE an outer `Choose` whose `When` requires OpenSides = Yes "
     "or one of five specific class codes. Class 0951 satisfies neither, so "
     "the branch is unreachable and the base symbol AA stands.\n"
     "    The algorithms doc lists the roof override as a peer of the "
     "class-specific overrides. It is not -- it is a child of them, and that "
     "distinction decides whether it is reachable at all"),
]


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    print(f"{'case':42s} {'sym':>4s} {'num':>4s} {'base':>6s} {'rate':>6s} "
          f"{'BGII':>5s} {'BGI':>5s}")
    ok = True
    for name, mutate, expect, why in CASES:
        sub = chunk2.submission()
        mutate(sub)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
        try:
            ip.run(data)
        except Exception as exc:
            print(f"{name:42s} RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = (read(f"{STRUCT}/BasicGroupIISymbolToUse", data) or "",
               read(f"{STRUCT}/BasicGroupIINumericValue", data),
               read(f"{STRUCT}/BasicGroupIIBaseRate", data),
               read(f"{STRUCT}/BasicGroupIIRate", data),
               read(BGII, data))
        gi = read(chunk2.BGI, data)
        good = got == expect
        ok &= good
        print(f"{name:42s} {got[0]:>4s} {got[1]:>4s} {got[2]:>6s} {got[3]:>6s} "
              f"{got[4]:>5s} {str(gi):>5s}"
              + ("" if good else f"   MISMATCH expected {expect}"))

    print("\nWhat each case proves")
    for name, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
