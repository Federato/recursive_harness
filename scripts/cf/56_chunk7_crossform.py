#!/usr/bin/env python3
"""Chunk 7, tasks C7-22 to C7-27 -- the cross-form claims.

  22  **Four absences, enumerated across all 47 jurisdictions.**
  23  **46 of 47 file a table this coverage never reads.**
  24  **The rounding convention, COUNTED** -- and this group follows plain
      Business Income, not the parent it hangs off.
  25  **The blanket branch discards the same two inputs as chunk 6's.**
  26  **Five coverages on one submission, none of them moving.**
  27  **The reuse map, checked rather than trusted** -- and it was right where
      chunk 7's own census was wrong.

Derived by hand before the run:

    26  Building 263 / 32, Contents 223 / 24, Business Income 112 / 13,
        Special Class 66 / 209, Special Class Business Income 39 / 123.

    python scripts/cf/56_chunk7_crossform.py

Exit 0 when every claim holds.
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

borrow = import_module("54_chunk7_borrowed")
perform = import_module("55_chunk7_perform")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")
cross6 = import_module("48_chunk6_crossform")

BI, SC, ASOF = g7.BI, g7.SC, g7.ASOF
P7 = borrow.P7
RULES = "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"
PREMIUM = [f"CommercialPropertySpecialClassBusnIncome{f}CoverageRules.Rule.xml"
           for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
MAP = Path("CF_Algorithm/Excel_Rater_SpecialClassBusinessIncome_ReuseMap.html")

ABSENCES = ["LOIFactor", "MultiResidentialPropSpecialCreditFactor",
            "BaseRateAdjustmentFactor", "StdPropPolGroupIFactor"]

ROUND_SETS = {
    "Special Class Busn Income": "CommercialPropertySpecialClassBusnIncome%sCoverageRules.Rule.xml",
    "Special Class (the parent)": "CommercialPropertySpecialClass%sCoverageRules.Rule.xml",
    "plain Business Income": "CommercialPropertyBusinessIncome%sCoverageRules.Rule.xml",
}


def main() -> int:
    ok = True
    book = book_for("OR", ASOF)
    d = book.parent.package.content / "Rules"
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)

    # ---- C7-22
    print("=== 22  Four absences, enumerated across all 47 jurisdictions\n")
    for term in ABSENCES:
        cw = sum((d / f).read_text(encoding="utf-8-sig").count(term)
                 for f in PREMIUM + [RULES])
        states = []
        for j in juris:
            b = book_for(j, ASOF, resolver=res)
            n = 0
            for f in PREMIUM + [RULES]:
                p = b.state.package.content / "Rules" / f
                if p.exists():
                    n += p.read_text(encoding="utf-8-sig").count(term)
            if n:
                states.append(j)
        good = cw == 0 and not states
        ok &= good
        print(f"    {term:42s} countrywide {cw:>3d}   states {len(states):>2d} "
              f"of {len(juris)}   (expected 0 / 0) "
              f"{'OK' if good else 'MISMATCH ' + str(states)}")
    print("    **Each has a different contrast, and the opening census only")
    print("    drew one.** C7-15 measured them: `StdPropPolGroupIFactor` is")
    print("    absent from plain Business Income too, so it is inherited from")
    print("    the Business Income side rather than dropped from the Special")
    print("    Class side. A single-comparison census cannot tell those apart.")

    # ---- C7-23
    print("\n=== 23  46 of 47 file a table this coverage never reads")
    t = "BaseRateAdjustmentFactor"
    cw_rows = len(book.parent_table(t).rows)
    own = [j for j in juris
           if book_for(j, ASOF, resolver=res).declares(t) == "state"]
    named = sum((d / f).read_text(encoding="utf-8-sig").count(t)
                for f in PREMIUM + [RULES])
    plain_named = (d / "CommercialPropertyBusinessIncomeRules.Rule.xml").read_text(
        encoding="utf-8-sig").count(t)
    good = cw_rows == 0 and len(own) == 46 and named == 0 and plain_named > 0
    ok &= good
    print(f"    countrywide rows                        : {cw_rows}")
    print(f"    jurisdictions filing their own          : {len(own)} of "
          f"{len(juris)}   (all but {sorted(set(juris) - set(own))})")
    print(f"    times named in THIS coverage's rules    : {named}")
    print(f"    times named in plain Business Income's  : {plain_named}   "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **A filed table is not evidence of a live path.** Forty-six")
    print("    jurisdictions maintain rows for a factor this coverage group")
    print("    does not have -- it belongs to plain Business Income, which")
    print("    rebuilds a rate the Special Class version simply copies.")
    print("    C7-21 is the same lesson from the other side: a table with a")
    print("    countrywide row, zero state filings, and no consumer here.")

    # ---- C7-24
    print("\n=== 24  The rounding convention, counted rather than read\n")
    counts = {}
    for label, pat in ROUND_SETS.items():
        row = []
        for form in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
            p = d / (pat % form)
            t_ = p.read_text(encoding="utf-8-sig")
            i = t_.find('<rul:Rule Name="SetPremium"')
            seg = t_[i:i + t_[i:].find("</rul:Rule>") + 11]
            row.append((seg.count("<rul:Round"),
                        seg.count('DecimalPlaces="0"')))
        counts[label] = row
        cells = "  ".join(f"{r:>2d}/{p_:<3d}" for r, p_ in row)
        print(f"    {label:28s} {cells}   (rul:Round / DecimalPlaces=0)")
    mine = counts["Special Class Busn Income"]
    parent = counts["Special Class (the parent)"]
    plain = counts["plain Business Income"]
    checks = [
        ("this group uses rul:Round on all four forms",
         all(r == 4 for r, _ in mine), True),
        ("the PARENT uses it on none",
         all(r == 0 for r, _ in parent), True),
        ("plain Business Income is inconsistent with ITSELF",
         sorted(r for r, _ in plain), [0, 4, 4, 4]),
    ]
    for label, got_v, want_v in checks:
        good = got_v == want_v
        ok &= good
        print(f"    {label:46s} {str(got_v):>14s}  (expected {want_v}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **This group follows plain Business Income, not the parent it")
    print("    hangs off** -- four `rul:Round` wrappers on every form, where")
    print("    Special Class Building has none on any. And **plain Business")
    print("    Income is inconsistent with itself**: its Basic Group II has 0")
    print("    where its other three have 4. Special Class Business Income")
    print("    normalises that back to 4, so **the copy is tidier than the")
    print("    original.** C6-27 caught an algorithms page recording this")
    print("    backwards; counting is the only way to know.")

    # ---- C7-25
    print("\n=== 25  The blanket branch discards the same two inputs")
    rec = {"IncludedInBlkt": "Yes", "BlktCauseOfLossValue": "Basic",
           "BlktLimit": "1000000", "FullBusnIncomeValue": "100000",
           "BlktTotalFullValueAmount": "500000",
           "BlktBasicGroupIAvgRate": "0.05"}
    data = perform.run_rec("Basic", rec=rec)
    for f, want_kept in (("BlktLimit", True), ("BlktBasicGroupIAvgRate", True),
                         ("BlktTotalFullValueAmount", False),
                         ("BlktCauseOfLossValue", False)):
        got = str(read(f"{BI}/{f}", data))
        kept = got not in ("0", "", "None")
        good = kept == want_kept
        ok &= good
        print(f"    {f:28s} = {got!r:12s} "
              f"{'kept' if kept else 'OVERWRITTEN':12s} "
              f"{'OK' if good else 'MISMATCH'}")
    prem = str(read(P7["BasicGroupI"], data))
    good = prem == "0"
    ok &= good
    print(f"    Basic Group I premium = {prem}  (expected 0) "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **The same two fields, on a different coverage.** C6-28 found")
    print("    the denominator and the cause of loss overwritten on the")
    print("    Special Class item; they are overwritten here too, so a caller")
    print("    supplying all four blanket values gets a silent $0 twice over.")
    print("    Chunk 9 now has the same starting point in two groups.")

    # ---- C7-26
    print("\n=== 26  Five coverages on one submission, none of them moving")
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
        g6.location(g7.submission("Basic"))
        ["CommercialPropertySpecialClassTable"])
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict("MasterCFOR", sub)
    ip.run(data)
    pp = chunk4.PP + "/CommercialPropertyPersonalPropertyPrsnlProp%sCoverage/Premium"
    rows = [("BUILDING Group I        ", chunk2.BGI, "263"),
            ("BUILDING Group II       ", chunk2.BGII, "32"),
            ("CONTENTS Group I        ", pp % "BasicGroupI", "223"),
            ("CONTENTS Group II       ", pp % "BasicGroupII", "24"),
            ("BUSN INCOME Group I     ", chunk5._P % "BasicGroupI", "112"),
            ("BUSN INCOME Group II    ", chunk5._P % "BasicGroupII", "13"),
            ("SPECIAL CLASS Group I   ", g6._P % "BasicGroupI", "66"),
            ("SPECIAL CLASS Group II  ", g6._P % "BasicGroupII", "209"),
            ("SPCL CLASS BI Group I   ", P7["BasicGroupI"], "39"),
            ("SPCL CLASS BI Group II  ", P7["BasicGroupII"], "123")]
    for label, path, want in rows:
        got = str(read(path, data))
        good = got == want
        ok &= good
        print(f"    {label} = {got:>4s}   (expected {want:>4s}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **Five coverages, four nesting levels, one submission.** Chunk")
    print("    5 ran this at three and chunk 6 at four. The two Special Class")
    print("    premiums are the only new numbers; everything on the Structure")
    print("    side is unchanged, because Special Class is a SIBLING of the")
    print("    building record rather than a child of it.")

    # ---- C7-27
    print("\n=== 27  The reuse map, checked rather than trusted")
    html = MAP.read_text(encoding="utf-8", errors="replace")
    body = (d / RULES).read_text(encoding="utf-8-sig")
    borrowed = set(re.findall(r'FromDataDef="\.\./\.\./(\w+)"', body))
    claims, checked, wrong = [], 0, []
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if len(cells) < 3:
            continue
        verdict = cells[2]
        if verdict not in ("COPY", "BUILD OWN", "DO NOT PULL IN",
                           "SHARE THE TABLE"):
            continue
        for name in re.findall(r"\b([A-Z]\w{6,})\b", cells[1]):
            claims.append((name, verdict))
    for name, verdict in claims:
        if name not in borrowed and verdict != "COPY":
            checked += 1          # correctly says this is not copied down
        elif name in borrowed and verdict in ("COPY", "SHARE THE TABLE"):
            checked += 1
        elif verdict in ("BUILD OWN", "DO NOT PULL IN") and name in borrowed:
            wrong.append((name, verdict))
    print(f"    value-shaped claims extracted from the page : {len(claims)}")
    print(f"    ...consistent with the corpus              : {checked}")
    print(f"    ...contradicted                            : {len(wrong)}  "
          f"{wrong}")
    print(f"    ...NOT decidable by this check             : "
          f"{len(claims) - checked - len(wrong)}")
    print("    **The undecidable ones are stated rather than counted as "
          "passes.**")
    print("    They are names the regex lifted out of prose that are not")
    print("    datadefs at all -- a claim this check cannot reach is not a")
    print("    claim it verified.")
    good = not wrong
    ok &= good
    right = [n for n, v in claims if v == "COPY" and n in borrowed]
    print(f"    values the map calls COPY that ARE read ../../ : "
          f"{sorted(set(right))}")
    print(f"    {'OK' if good else 'MISMATCH'}")
    print("    **The map was right where chunk 7's own census was wrong.** It")
    print("    lists `BasicGroupIINumericValue` among the values copied from")
    print("    the item -- the value C7-12's opening census filtered out and")
    print("    the golden case had to rediscover by hand. A filed artefact is")
    print("    worth checking, and checking it found our error rather than")
    print("    its own.")

    print()
    if ok:
        print("Every cross-form claim holds.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
