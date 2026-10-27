#!/usr/bin/env python3
"""Chunk 6, tasks C6-24 to C6-29 -- the cross-form claims.

  24  **No limit-of-insurance factor anywhere** -- enumerated across the
      ruleset, the four premium files and all 47 jurisdictions.
  25  **No `MultiResidentialPropSpecialCreditFactor` anywhere** -- same
      treatment, against a Building that applies it in every form.
  26  **Basic Group I and II are not gated on the cause of loss.**
  27  **The rounding convention is the OPPOSITE of what the algorithms page
      says** -- and the page has to be corrected.
  28  **The blanket branch, run for the first time in the project.**
  29  **Four coverages on one submission, none of them moving.**

Two negative claims are enumerated rather than asserted, the way C4-22 and
C5-24/25 were: a negative claim has to state what was searched.

Derived by hand before the run:

    28  BlktLimit 1,000,000 / FullSpecialClassValue 100,000 /
        BlktTotalFullValueAmount 500,000 / BlktBasicGroupIAvgRate 0.05
            10,000 x 0.2 x 0.05 = 100                          $100
        BlktBasicGroupIIAvgRate 0.02  ->  10,000 x 0.2 x 0.02   $40
        BlktTotalFullValueAmount 0    ->  the guarded zero      $0

    29  Building 263 / 32, Contents 223 / 24, Business Income 112 / 13,
        Special Class 66 / 209 -- all on one submission, each unchanged
        from its own chunk.

    python scripts/cf/48_chunk6_crossform.py

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
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chain = import_module("45_chunk6_description_chain")
g = import_module("41_chunk6_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")

SC, ASOF = g.SC, g.ASOF
P = {f: g._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
GROUP = "CommercialPropertySpecialClass"
MAIN = "CommercialPropertySpecialClassRules.Rule.xml"
PREMIUM_FILES = [f"CommercialPropertySpecialClass{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
BUILDING_FILES = ["CommercialPropertyStructureRules.Rule.xml"] + [
    f"CommercialPropertyStructureBuilding{f}CoverageRules.Rule.xml"
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]

ABSENCES = [
    ("a limit-of-insurance factor", r"LOIFactor",
     "Building applies one in every form's rate chain AND names it in every "
     "premium file. Special Class multiplies the final rate by Limit/100 with "
     "nothing standing in between"),
    ("MultiResidentialPropSpecialCreditFactor",
     r"MultiResidentialPropSpecialCreditFactor",
     "Building multiplies it into every form's FINAL rate. It is a "
     "Building/Contents credit and scheduled Special Class property does not "
     "get it"),
]


def blanket(over=None):
    """The golden-case item, folded into a blanket."""
    base = {
        "IncludedInBlkt": "Yes",
        "BlktCauseOfLossValue": "Basic",
        "BlktLimit": "1000000",
        "FullSpecialClassValue": "100000",
        "BlktTotalFullValueAmount": "500000",
        "BlktBasicGroupIAvgRate": "0.05",
        "BlktBasicGroupIIAvgRate": "0.02",
    }
    base.update(over or {})
    return chain.run("OR", base)


def main() -> int:
    ok = True
    book = book_for("OR", ASOF)
    d = book.parent.package.content / "Rules"
    res = CFEditionResolver()

    # ---- C6-24 and C6-25, enumerated
    print("=== 24 / 25  Two absences, enumerated rather than asserted\n")
    for label, pattern, note in ABSENCES:
        hits, bldg = [], 0
        for f in PREMIUM_FILES + [MAIN]:
            t = (d / f).read_text(encoding="utf-8-sig")
            if re.search(pattern, t):
                hits.append(f"CW:{f}")
        for f in BUILDING_FILES:
            p = d / f
            if p.exists() and re.search(pattern,
                                        p.read_text(encoding="utf-8-sig")):
                bldg += 1
        states = []
        for j in sorted(res.jurisdictions):
            b = book_for(j, ASOF, resolver=res)
            for f in PREMIUM_FILES + [MAIN]:
                p = b.state.package.content / "Rules" / f
                if p.exists() and re.search(pattern,
                                            p.read_text(encoding="utf-8-sig")):
                    states.append(f"{j}:{f}")
        good = not hits and not states
        ok &= good
        n = len(res.jurisdictions)
        print(f"  {label}")
        print(f"      countrywide Special Class files naming it : {len(hits)} "
              f"of {len(PREMIUM_FILES) + 1}  (expected 0)")
        print(f"      state Special Class files naming it       : "
              f"{len(states)} across {n} jurisdictions  (expected 0)  "
              f"{'OK' if good else 'MISMATCH ' + str(states[:4])}")
        print(f"      ...and BUILDING files naming it           : {bldg} of "
              f"{len(BUILDING_FILES)}  <- the contrast")
        print(f"      {note}\n")

    # ---- C6-26
    print("=== 26  Basic Group I and II are not gated on the cause of loss")
    for f, want_test in ((PREMIUM_FILES[0], False), (PREMIUM_FILES[1], False),
                         (PREMIUM_FILES[2], True), (PREMIUM_FILES[3], True)):
        t = (d / f).read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetCoverageOnPolicyIndicator"')
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        has = "<rul:Test>" in seg
        good = has == want_test
        ok &= good
        form = f.split("SpecialClass")[1].split("Coverage")[0]
        print(f"    {form:14s} gate has a Test : {str(has):5s} "
              f"(expected {want_test}) {'OK' if good else 'MISMATCH'}")
    for col, want in (("Basic", ("66", "209")), ("Broad", ("66", "209")),
                      ("Special", ("66", "209"))):
        data = chain.run("OR", {"CauseOfLoss": col})
        got = (str(read(P["BasicGroupI"], data)),
               str(read(P["BasicGroupII"], data)))
        good = got == want
        ok &= good
        print(f"    CauseOfLoss={col:8s} Basic Group I/II = {got[0]}/{got[1]}"
              f"   (expected {want[0]}/{want[1]}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **Three chunks established that each form gates on the cause of")
    print("    loss. Here half of it is false.** ISO confirmed it independently")
    print("    in C6-08: the Broad call's total was the Basic pair PLUS $14.")

    # ---- C6-27
    print("\n=== 27  The rounding convention -- and the algorithms page is wrong")
    rows = []
    for f in PREMIUM_FILES + [b for b in BUILDING_FILES[1:]]:
        p = d / f
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetPremium"')
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        rows.append((f, seg.count("<rul:Round"),
                     seg.count('DecimalPlaces="0"')))
    for f, nr, np_ in rows:
        who = "SpecialClass" if "SpecialClass" in f else "Building    "
        form = f.split("Coverage")[0].split("Building")[-1].split(
            "SpecialClass")[-1]
        print(f"    {who} {form:14s} rul:Round={nr:>2d}  "
              f"Product DecimalPlaces=0={np_:>3d}")
    sc = [r for r in rows if "SpecialClass" in r[0]]
    bl = [r for r in rows if "SpecialClass" not in r[0]]
    good = (all(r[1] == 0 for r in sc)
            and any(r[1] > 0 for r in bl)
            and [r for r in bl if "Special" in r[0]][0][1] == 0)
    ok &= good
    print(f"    Special Class files using rul:Round : "
          f"{sum(1 for r in sc if r[1])} of {len(sc)}  (expected 0) "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **The algorithms page says Special Class uses the standard")
    print("    nested `Round` and does NOT carry Building's Special-form")
    print("    quirk. It is the other way round.** All four Special Class")
    print("    premium files are `Product DecimalPlaces=\"0\"` with zero")
    print("    `rul:Round` wrappers -- Building's Special-form convention,")
    print("    applied to every form. Building's own Basic and Broad files")
    print("    carry six `rul:Round` wrappers each.")
    print("    **And the premium rounds to 0 dp at SIX NESTED LEVELS**, so")
    print("    PackageMod, the multi-premium credit, IRPM and both cyber")
    print("    factors each multiply an ALREADY-ROUNDED dollar figure --")
    print("    read from the POLICY, five levels up, through")
    print("    `FromConstant=\"0.0\"`. Corrected on the algorithms page.")

    # ---- C6-28
    print("\n=== 28  The blanket branch, run for the first time in the project")
    # **Predicted $100 and got $0 -- and the reason is the finding.**
    # Two of the four blanket inputs are DERIVED and discard what the
    # submission sends: `BlktTotalFullValueAmount` comes back 0 and
    # `BlktCauseOfLossValue` comes back blank, both written by
    # `SetNonEQBlanketValues` from blanket records at the policy level that
    # chunk 6 does not have. The other two survive. So the branch runs, takes
    # its guarded-zero arm, and **cannot be priced from the item alone.**
    sched = chain.run("OR", {})
    blk = blanket()
    pairs = [
        ("IncludedInBlkt = No  (scheduled)",
         (str(read(P["BasicGroupI"], sched)),
          str(read(P["BasicGroupII"], sched))), ("66", "209")),
        ("IncludedInBlkt = Yes (blanket)",
         (str(read(P["BasicGroupI"], blk)),
          str(read(P["BasicGroupII"], blk))), ("0", "0")),
    ]
    for name, got, want in pairs:
        good = got == want
        ok &= good
        print(f"    {name:38s} {got[0]:>4s} / {got[1]:>4s}  "
              f"(expected {want[0]}/{want[1]}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **The branch IS taken** -- the same item, the same rate chain,")
    print("    and a different premium formula. Proof that it is the blanket")
    print("    arm and not a gate: `FinalBasicGroupIRate` is still "
          f"{read(f'{SC}/FinalBasicGroupIRate', blk)} on the")
    print("    blanketed item, computed in full and **never read**.")
    print("\n    Which blanket inputs survive the submission:")
    for f, want_kept in (("BlktLimit", True),
                         ("BlktBasicGroupIAvgRate", True),
                         ("BlktTotalFullValueAmount", False),
                         ("BlktCauseOfLossValue", False)):
        got_v = str(read(f"{SC}/{f}", blk))
        kept = got_v not in ("0", "", "None")
        good = kept == want_kept
        ok &= good
        print(f"      {f:28s} = {got_v!r:12s} "
              f"{'kept' if kept else 'OVERWRITTEN':12s} "
              f"{'OK' if good else 'MISMATCH'}")
    print("    `SetNonEQBlanketValues` writes the denominator and the cause of")
    print("    loss from blanket records at the POLICY level. **The two fields")
    print("    it overwrites are exactly the two the formula cannot do")
    print("    without** -- so a caller who supplies all four blanket values on")
    print("    the item gets a silent $0, with two of its four inputs")
    print("    discarded and no message. The sixth derived-field trap in the")
    print("    chunk, and the first that discards HALF a submitted formula.")
    print("    **Chunks 1-5 only ever ran scheduled items**, so this is the")
    print("    first execution of a branch every premium file in the project")
    print("    carries. Pricing it is chunk 9's job, and chunk 9 now has a")
    print("    named starting point: `SetNonEQBlanketValues`.")

    # ---- C6-29
    print("\n=== 29  Four coverages on one submission, none of them moving")
    sub = chunk4.submission("Basic")
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    st = zeros2.structure(sub)
    st["CommercialPropertyBusinessIncomeTable"] = (
        zeros2.structure(chunk5.submission("Basic"))
        ["CommercialPropertyBusinessIncomeTable"])
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc["CommercialPropertySpecialClassTable"] = (
        g.location(g.submission("Basic"))
        ["CommercialPropertySpecialClassTable"])
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict("MasterCFOR", sub)
    ip.run(data)
    pp = chunk4.PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
    for label, path, want in (
            ("BUILDING Group I     ", chunk2.BGI, "263"),
            ("BUILDING Group II    ", chunk2.BGII, "32"),
            ("CONTENTS Group I     ", pp % "BasicGroupI", "223"),
            ("CONTENTS Group II    ", pp % "BasicGroupII", "24"),
            ("BUSN INCOME Group I  ", chunk5._P % "BasicGroupI", "112"),
            ("BUSN INCOME Group II ", chunk5._P % "BasicGroupII", "13"),
            ("SPECIAL CLASS Group I", P["BasicGroupI"], "66"),
            ("SPECIAL CLASS Gp II  ", P["BasicGroupII"], "209")):
        got = str(read(path, data))
        good = got == want
        ok &= good
        print(f"    {label} = {got:>4s}   (expected {want:>4s}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **Special Class is a sibling of the Structure, not a child**,")
    print("    so its 100,000 limit never reaches Building's TotAmtInsurance")
    print("    and the location total that drives three other coverages'")
    print("    deductible band is unchanged. Four coverages, one submission,")
    print("    and the only new number is Special Class's own.")

    print()
    if ok:
        print("Every cross-form claim holds.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
