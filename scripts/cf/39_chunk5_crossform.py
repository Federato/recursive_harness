#!/usr/bin/env python3
"""Chunk 5, tasks C5-24 to C5-28 -- the cross-form claims.

  24  **No deductible factor anywhere** in the Business Income chain.
  25  **No limit-of-insurance factor anywhere** either.
  26  **The multi-premium credit is populated and not applied.**
  27  **Add-ons charge `(Factor - 1) x Rate x Limit/100`** -- a surcharge
      shape nothing else in the corpus uses.
  28  **Building and Contents must not move** when Business Income rates.

24 and 25 are enumerated across the whole ruleset and every jurisdiction
rather than asserted, the way C4-22 enumerated Contents' missing roof factor:
a negative claim has to state what was searched.

Derived by hand from Oregon's filed rows before the run, on the chunk 5 golden
case (Basic Group I final rate 0.112, premium $112):

    26  MultiPremiumAndDispersionCreditFactor 0.5
            Building Group I  $261 -> $131   (the credit IS applied)
            Business Income   $112 -> $112   (it is NOT)

    27  Agreed Value, AgreedValueFactorBusnIncome [CW] = 1.1
            premium = 0.112 x r3(1.1 - 1) x 100,000/100 = 11.2 -> $11
            **The full rate would charge $112.** Ten times the difference,
            and the shape is the whole point: an add-on charges only the load
            it adds, never the base again.

    28  Building 263 / 32, Contents 223 / 24, Business Income 112 / 13
            all on one submission, each unchanged from its own chunk.

    python scripts/cf/39_chunk5_crossform.py

Exit 0 when every case matches and both absences are enumerated.
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

chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")

BI, BGI, BGII = chunk5.BI, chunk2.BGI, chunk2.BGII
P_BGI = chunk5._P % "BasicGroupI"
AV = BI + "/CommercialPropertyBusinessIncomeAgreedValBasicGroupICoverage/Premium"


def run(book, sub):
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    return data


def main() -> int:
    book = book_for(chunk2.JURIS, chunk2.ASOF)
    print(f"{book}\n")
    ok = True

    # ---- C5-24 and C5-25, enumerated
    print("=== 24 / 25  Two absences, enumerated rather than asserted")
    res = CFEditionResolver()
    ded, loi = [], []
    for j in ["CW"] + list(res.jurisdictions):
        b = book if j == "CW" else book_for(j, chunk2.ASOF, resolver=res)
        pkg = b.parent.package if j == "CW" else b.state.package
        f = pkg.content / "Rules" / "CommercialPropertyBusinessIncomeRules.Rule.xml"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8-sig")
        names = set(re.findall(r'<rul:Rule Name="(Set[A-Za-z]+)"', t))
        if any(re.match(r"Set.*Deductible.*Factor", n) for n in names):
            ded.append(j)
        if any(re.match(r"Set.*LOIFactor", n) for n in names):
            loi.append(j)
    n = len(res.jurisdictions)
    for label, hits, note in (
            ("a deductible-FACTOR rule", ded,
             'the "deductible" in Business Income is a waiting period built '
             'into the rate, not a scheduled dollar amount'),
            ("a limit-of-insurance factor rule", loi,
             "the premium multiplies the final rate by Limit/100 with nothing "
             "standing in between")):
        good = not hits
        ok &= good
        print(f"    jurisdictions whose BI ruleset defines {label:34s}"
              f" {len(hits)} of {n} + CW  (expected 0) "
              f"{'OK' if good else 'MISMATCH ' + str(hits)}")
        print(f"        {note}")
    print("    Building applies BOTH on every form, and Contents applies a")
    print("    limit factor whose curves run below 1.0. Business Income has")
    print("    neither concept at all -- so nothing about limit banding or")
    print("    deductible credits carries over from chunks 1 to 4.")

    # ---- C5-26
    print("\n=== 26  The multi-premium credit is populated and NOT applied")
    sub = chunk5.submission("Basic")
    zeros2.structure(sub)["MultiPremiumAndDispersionCreditFactor"] = "0.5"
    data = run(book, sub)
    got = (read(BGI, data), read(P_BGI, data))
    good = got == ("131", "112")
    ok &= good
    print(f"    Building Group I = {got[0]}  (expected 131 -- the credit "
          f"applies)")
    print(f"    Business Income  = {got[1]}  (expected 112 -- unchanged)  "
          f"{'OK' if good else 'MISMATCH'}")
    print("    The datadef is populated during shared prep and Building's")
    print("    scheduled branch multiplies it in. Business Income's premium")
    print("    files do not, for any of the five forms -- **a populated but")
    print("    unused value is exactly the shape that makes a reader assume")
    print("    it is in the formula.**")

    # ---- C5-27
    print("\n=== 27  Add-ons charge the LOAD, not the rate")
    sub = chunk5.submission("Basic")
    bi = zeros2.structure(sub)["CommercialPropertyBusinessIncomeTable"][
        "CommercialPropertyBusinessIncome"][0]
    bi["AgreedValueOption"] = "Yes"
    bi["AgreedValueLimit"] = "100000"
    data = run(book, sub)
    av, base = read(AV, data), read(P_BGI, data)
    good = av == "11" and base == "112"
    ok &= good
    print(f"    Agreed Value premium = {av}   (expected 11)")
    print(f"    Basic Group I        = {base}   (expected 112, still charged "
          f"in full)  {'OK' if good else 'MISMATCH'}")
    print("    0.112 x (1.1 - 1) x 1,000 = 11.2 -> $11. **The full rate would")
    print("    charge $112** -- ten times as much. Nothing in Building or")
    print("    Contents uses this shape; their endorsement factors are always")
    print("    full multipliers on the whole rate.")

    # ---- C5-28
    print("\n=== 28  Three coverages on one submission, none of them moving")
    sub = chunk4.submission("Basic")
    st = zeros2.structure(sub)
    st["CommercialPropertyBusinessIncomeTable"] = (
        zeros2.structure(chunk5.submission("Basic"))
        ["CommercialPropertyBusinessIncomeTable"])
    data = run(book, sub)
    pp = chunk4.PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
    rows = [("BUILDING Group I ", BGI, "263"),
            ("BUILDING Group II", BGII, "32"),
            ("CONTENTS Group I ", pp % "BasicGroupI", "223"),
            ("CONTENTS Group II", pp % "BasicGroupII", "24"),
            ("BUSN INCOME Gp I ", P_BGI, "112"),
            ("BUSN INCOME Gp II", chunk5._P % "BasicGroupII", "13")]
    for label, path, want in rows:
        g = read(path, data)
        g_ok = g == want
        ok &= g_ok
        print(f"    {label} = {str(g):>4s}   (expected {want:>4s}) "
              f"{'OK' if g_ok else 'MISMATCH'}")
    print("    **Business Income is immune to the Contents record**, and that")
    print("    follows from 24 and 25: it has no deductible key and no limit")
    print("    factor, so the location total that moves Building from $261 to")
    print("    $263 cannot reach it.")

    print()
    if ok:
        print("All five cross-form claims hold.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
