#!/usr/bin/env python3
"""Chunk 3, gate point 4 -- every Broad and Special `0` against its branch.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK3-ZERO-CASES.md`.

Four filed zeros, and they do not all behave the same way:

  * `SetBroadBaseRate` gates on `ConstructionTypeToUse` -- the only non-Basic
    form with a construction dependency -- and yields `0.0` when it is blank;
  * `SetSpecialBaseRate` gates only on the cause of loss, so it survives a
    missing construction type that kills Broad, Group I and Group II;
  * both LOI rules yield `0.0` when `Limit` is absent, from the same shared
    matrix `BroadSpecialLOIFactorBldg`;
  * both deductible rules end in an `Otherwise` worth `0.0`.

**Two predictions were wrong, and both corrections are the value here.**

`SetDeductibleFactorSpecial` was predicted to have NO `Otherwise`, so that a
blank `Deductible` would leave the factor null and the premium refused. The
filed XML has one, identical in shape to Broad's, and the engine was right.
`CauseOfLoss_Building_RatingAlgorithms.md` had documented four branches and
stated the fall-through "behaves differently" from Broad's; it does not. The
doc has been corrected (two errors -- the missing `Otherwise`, and branch 2's
`Or` written as an `And`).

`Limit` removed was predicted to price at zero through the LOI branch. It does
not: the **null-premium guard raises**, on both forms. An absent limit is the
one input in this family that is LOUD.

Each case moves ONE input and reports all four Building coverages, because
several produce the same premium by different mechanisms and because a chain
moving when it should not is the more valuable finding.

    python scripts/cf/16_chunk3_zero_cases.py

Exit 0 when every case matches its prediction.
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
chunk3 = import_module("15_chunk3_golden_case")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII
BROAD, SPECIAL = chunk3.BROAD, chunk3.SPECIAL

#: The chain values worth seeing alongside the premium, per form. These
#: distinguish cases that price identically by different mechanisms -- a base
#: rate of 0.015 above a premium of 0 is a very different failure from a base
#: rate of 0.
WATCH = {
    "Broad": ["BroadBaseRate", "BroadRate", "BroadLOIFactor",
              "AdjustedBroadRate", "DeductibleFactorBroad", "FinalBroadRate"],
    "Special": ["SpecialBaseRate", "SpecialRate", "SpecialLOIFactor",
                "AdjustedSpecialRate", "DeductibleFactorSpecial",
                "FinalSpecialRate"],
}

#: Sentinel: this case must REFUSE to rate. The null-premium guard raising is
#: the expected outcome, and a quiet premium would be the failure.
RAISES = "<raises>"

#: id, mutation, {form: expected premium}, {Basic coverage: expected}, what it
#: proves. `None` in the Basic dict means "do not assert" -- used where the run
#: is expected to raise before the Basic premiums are written.
CASES = [
    ("baseline", lambda s: None,
     {"Broad": "16", "Special": "54"}, {"BGI": "261", "BGII": "32"},
     "the reference the others are read against"),

    ("Z1  ConstructionType removed",
     lambda s: zeros2.structure(s).pop("ConstructionType"),
     {"Broad": "0", "Special": "54"}, {"BGI": "0", "BGII": "0"},
     "`SetBroadBaseRate` names `ConstructionTypeToUse` in its gate, so Broad "
     "zeroes; Group I looks its base rate up BY construction and Group II "
     "derives its symbol from construction plus stories, so both zero too. "
     "**Special is predicted to survive at 54** -- its base rate is a flat "
     "statewide constant with no class, construction, territory or symbol. "
     "One mutation, three chains down and one standing, which is the "
     "strongest single statement available that Special's rate really is flat"),

    ("Z2  Deductible removed",
     lambda s: zeros2.structure(s).pop("Deductible"),
     {"Broad": "0", "Special": "0"}, {"BGI": "0", "BGII": "0"},
     "**a prediction that was wrong, and the correction is the finding.** Both "
     "forms were expected to diverge: Broad's `Otherwise` worth `0.0` against "
     "a Special rule documented as having only four conditions and no "
     "fall-through, which would have left the factor null and the premium "
     "refused. The filed XML has an `Otherwise` on BOTH rules, identical in "
     "shape, so both price at zero.\n"
     "    The engine was right and the algorithms doc was wrong -- it also "
     "wrote branch 2's `Or` as an `And`. Corrected there rather than here.\n"
     "    What survives is the shape that matters: both forms price at zero "
     "underneath a perfectly healthy base rate (0.015 / 0.047) and adjusted "
     "rate (0.017 / 0.056). The chunk-2 BCEG shape again -- absent means "
     "zero, and nothing raises"),

    ("Z3  Limit removed",
     lambda s: zeros2.structure(s).pop("Limit"),
     {"Broad": RAISES, "Special": RAISES}, {"BGI": None, "BGII": None},
     "**predicted to price at zero; it RAISES instead, on both forms.** The "
     "prediction read branch 3 of the LOI rules -- `0.0` when `Limit` is "
     "absent -- and stopped there. What actually happens is that the premium's "
     "own exposure base is `Limit / 100 x final rate`, so an absent limit "
     "makes the premium itself null, and the null-premium guard refuses it:\n"
     "      Product wrote a NULL to 'Premium'. A premium is money: absent is "
     "not zero.\n"
     "    **This is the one input in the family that is LOUD.** Every other "
     "missing input found in chunks 1-3 -- Arizona's reduction credit, an "
     "unrecognised construction type, an absent BCEG, a missing Group II "
     "rating type, a missing Group II territory, and now a blank deductible on "
     "both chunk 3 forms -- prices at zero in silence. A missing limit is "
     "refused, because it is the only one that reaches the premium as a null "
     "rather than as a factor of zero. That is the distinction, and it is an "
     "argument for the input-validation layer rather than against it: the "
     "guard catches nulls, and the whole problem is that ISO's rules turn "
     "missing inputs into zeros before they ever become nulls"),

    ("Z4  CauseOfLoss = Basic",
     lambda s: zeros2.structure(s).__setitem__("CauseOfLoss", "Basic"),
     {"Broad": "0", "Special": "0"}, {"BGI": "261", "BGII": "32"},
     "the control. Both base-rate gates test the cause of loss, so selecting "
     "`Basic` must leave Broad and Special at zero while Basic Group I and II "
     "price normally. ISO confirmed this shape in task 23; it is asserted here "
     "so a regression in the gate fails this script rather than the sweep"),
]


def run(book, form, mutate):
    """One submission for `form`, mutated, run to completion."""
    sub = chunk3.submission(chunk3.FORMS[form]["col"])
    mutate(sub)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    return data


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, prem_want, basic_want, why in CASES:
        print(f"=== {name}")
        for form in ("Broad", "Special"):
            want = prem_want[form]
            try:
                data = run(book, form, mutate)
            except Exception as exc:
                good = want is RAISES
                ok &= good
                first = str(exc).split(".")[0]
                print(f"    {form:8s} RAISED {type(exc).__name__}: {first}."
                      f"  {'OK -- refusing to rate is the expectation' if good else 'MISMATCH -- expected a premium of ' + str(want)}")
                continue
            if want is RAISES:
                ok = False
                print(f"    {form:8s} rated, and it must NOT have -- expected "
                      f"the null-premium guard to refuse this submission")
            chain = " ".join(
                f"{dd.replace(form, '').replace('Adjusted', 'adj')}="
                f"{read(f'{STRUCT}/{dd}', data)}" for dd in WATCH[form])
            path = BROAD if form == "Broad" else SPECIAL
            got = read(path, data)
            good = got == want
            ok &= good
            print(f"    {form:8s} premium = {str(got):>5s}  "
                  f"(expected {str(want):>5s}) {'OK' if good else 'MISMATCH'}")
            print(f"             {chain}")
            # Basic must be asserted in every case: Broad and Special are
            # additive layers on top of it, so Basic moving in a case that
            # touches only a Broad/Special input would mean the layers are
            # coupled somewhere no document says they are.
            gi, gii = read(BGI, data), read(BGII, data)
            bgood = ((basic_want["BGI"] is None or gi == basic_want["BGI"])
                     and (basic_want["BGII"] is None
                          or gii == basic_want["BGII"]))
            ok &= bgood
            print(f"             Basic GI={gi} GII={gii}  "
                  f"(expected GI={basic_want['BGI']} "
                  f"GII={basic_want['BGII']}) "
                  f"{'OK' if bgood else 'MISMATCH'}")
        print()

    print("What each case proves")
    for name, _, _, _, why in CASES:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match, both forms.")
        return 0
    print("MISMATCHES above -- the disagreement is the finding.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
