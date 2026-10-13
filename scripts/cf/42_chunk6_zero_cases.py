#!/usr/bin/env python3
"""Chunk 6, task C6-03 -- every zero tested against its consuming branch.

Six cases, each derived by hand from the filed rows before the run. The golden
case is Basic Group I **$66** / Basic Group II **$209** / Broad **$14** /
Special **$44**, with Building unmoved at 261 / 32.

  1  **No `ClassDescription`.** The converted option is blank, Group I's base
     rate gates shut at 0.0, and the Group II numeric lookup misses. Broad and
     Special do not key on the description and are **untouched** -- so one
     missing field takes half the premium and leaves the other half looking
     perfectly healthy.

  2  **A description ISO itself files -- in another state.** "Towers -
     Broadcasting Antennas (Radio and TV)" is a real filed string in FLORIDA's
     package; countrywide files "...(Cell, Radio and TV)". Spelled from the
     wrong state's list it prices at zero in Oregon with no message.

  3  **No `Deductible`.** All four deductible rules end in an `Otherwise` worth
     **0.0**, not 1.0 -- so one absent field takes ALL FOUR forms to zero at
     once. The widest single-field blast radius found in six chunks.

  4  **No `Limit`.** `SetTotAmtInsurance` copies `Limit`, so the deductible
     band has nothing to key on either. Predicted to RAISE, as chunk 3's
     Building did.

  5  **No `BasicGroupIISymbol`.** Group II's base rate gates on it and prices
     at zero; Group I is untouched at $66. The symbol has no setter anywhere in
     this ruleset (C6-18), so nothing recomputes it.

  6  **No `PolicyType` on the POLICY.** Broad and Special both gate on it, four
     levels above the item. Basic Group I and II do not, and hold at 66 / 209.
     The derived-field trap from C6-01, as a zero case.

    python scripts/cf/42_chunk6_zero_cases.py

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
from gl_engine.interp.values import InterpretError                # noqa: E402
import _iso_refusals as _iso                                    # noqa: E402
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
g = import_module("41_chunk6_golden_case")

SC, BGI, BGII = g.SC, chunk2.BGI, chunk2.BGII
RAISES = object()

#: A real filed string -- in Florida's package, not countrywide. Florida files
#: 11 descriptions countrywide does not and drops 6 countrywide does; this is
#: one of the six, at its older spelling.
FL_ONLY = "Towers - Broadcasting Antennas (Radio and TV)"


def policy(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


#: id, mutation, {form: expected premium}, (Building GI, Building GII), why
CASES = [
    ("0  baseline", lambda s: None,
     {"Basic": ("66", "209"), "Broad": ("14",), "Special": ("44",)},
     ("261", "32"), "the reference"),

    ("1  no ClassDescription",
     lambda s: g.item(s).pop("ClassDescription", None),
     {"Basic": ("0", "0"), "Broad": ("14",), "Special": ("44",)},
     ("261", "32"),
     "**one missing field takes half the premium and leaves the other half "
     "looking healthy.** Broad keys on a hardcoded \"Frame\" and Special on a "
     "flat statewide constant, so neither notices. A reader checking that the "
     "item rates at all would see $58 of premium and move on"),

    ("2  a description ISO files -- in FLORIDA",
     lambda s: g.item(s).__setitem__("ClassDescription", FL_ONLY),
     {"Basic": ("0", "0"), "Broad": ("14",), "Special": ("44",)},
     ("261", "32"),
     "**not a typo -- a real ISO string from the wrong state's list.** "
     "Countrywide files \"...(Cell, Radio and TV)\"; Florida files the older "
     "\"...(Radio and TV)\" and drops the countrywide one. Either spelling is "
     "correct somewhere and worth zero everywhere else, silently"),

    ("3  no Deductible",
     lambda s: g.item(s).pop("Deductible", None),
     {"Basic": ("0", "0"), "Broad": ("0",), "Special": ("0",)},
     ("261", "32"),
     "**all four forms at once.** Every deductible rule ends in an "
     "`Otherwise` worth 0.0, not 1.0 -- absent means no coverage charged, not "
     "no discount. The widest single-field blast radius in six chunks, and "
     "Building is untouched because it carries its own deductible"),

    ("4  no Limit", lambda s: g.item(s).pop("Limit", None),
     {"Basic": ("0", "0"), "Broad": ("0",), "Special": ("0",)}, ("261", "32"),
     "**2026-09-23 (OI-109): now $0, not a refusal.** ISO writes $0 where a missing limit empties a "
     "premium (confirmed live 5 of 5, chunk 12 `136_chunk12_oi109_probes.py`); the engine now does "
     "the same with the user's authorization, and records each one in `null_premiums`. Before: "
     "predicted to raise, as chunk 3's Building did -- the premium formula "
     "divides the limit by 100 and `SetTotAmtInsurance` copies it for the "
     "deductible band, so there is nothing to rate"),

    ("5  no BasicGroupIISymbol",
     lambda s: g.item(s).pop("BasicGroupIISymbol", None),
     {"Basic": ("66", "0"), "Broad": ("14",), "Special": ("44",)},
     ("261", "32"),
     "**Group II alone falls over.** The symbol has no setter anywhere in the "
     "Special Class ruleset (C6-18), so nothing recomputes it from "
     "construction the way Building's does -- and Building's own Group II, "
     "which derives its symbol, is unmoved at $32"),

    ("6  no PolicyType on the POLICY",
     lambda s: policy(s).pop("PolicyType", None),
     {"Basic": ("66", "209"), "Broad": ("0",), "Special": ("0",)},
     ("261", "32"),
     "**the C6-01 trap as a zero case.** Broad and Special gate on a field "
     "four levels above the item; Basic Group I and II do not gate on it at "
     "all and hold at 66 / 209. Setting it ON the item does not help -- "
     "`SetPolicyType` is unguarded and overwrites it with blank"),
]

PATHS = {"Basic": [("Basic Group I", g._P % "BasicGroupI"),
                   ("Basic Group II", g._P % "BasicGroupII")],
         "Broad": [("Broad", g._P % "Broad")],
         "Special": [("Special", g._P % "Special")]}


def main() -> int:
    book = book_for(g.JURIS, g.ASOF)
    print(f"{book}\n")
    ok = True
    for name, mutate, expect, bldg, why in CASES:
        print(f"=== {name}")
        raised = None
        got = {}
        for col in PATHS:
            sub = g.submission(col)
            mutate(sub)
            ip = Interpreter(book, rounding=ROUNDING, trace=False,
                             null_arithmetic=NULL_ARITHMETIC)
            data = Node.from_dict(f"MasterCF{g.JURIS}", sub)
            try:
                ip.run(data)
            except Exception as exc:
                raised = f"{type(exc).__name__}: {exc}"
                break
            got[col] = tuple(str(read(p, data)) for _, p in PATHS[col])
            if col == "Basic":
                got["_bldg"] = (str(read(BGI, data)), str(read(BGII, data)))

        if expect is RAISES:
            good = raised is not None
            ok &= good
            print(f"    RAISED: {raised}   (expected a refusal) "
                  f"{'OK' if good else 'MISMATCH -- it rated'}")
        elif raised is not None and _iso.refused_as_iso(__file__, name.split("  ")[0], raised, indent="    "):
            pass                                            # C28-05: ours refuses where ISO does (C28-06 P10)
        elif raised is not None:
            ok = False
            print(f"    RAISED unexpectedly: {raised}")
        else:
            for col in PATHS:
                good = got[col] == expect[col]
                ok &= good
                labels = [l for l, _ in PATHS[col]]
                pairs = ", ".join(f"{l} {v}" for l, v in zip(labels, got[col]))
                print(f"    {pairs:44s} (expected {expect[col]}) "
                      f"{'OK' if good else 'MISMATCH'}")
            good = got["_bldg"] == bldg
            ok &= good
            print(f"    BUILDING {got['_bldg'][0]} / {got['_bldg'][1]:<4s}"
                  f"{'':>18s} (expected {bldg}) "
                  f"{'OK' if good else 'MISMATCH'}")
        print()

    print("What each case proves")
    for name, _, _, _, why in CASES[1:]:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print()
    if ok:
        print(f"All {len(CASES)} cases match their derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
