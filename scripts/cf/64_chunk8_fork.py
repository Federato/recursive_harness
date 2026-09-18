#!/usr/bin/env python3
"""Chunk 8, tasks C8-10 to C8-14 -- the fork.

  10  **The rate chain is shared, rule for rule**, through the cause-of-loss
      adjustment -- and diverges only after it.
  11  **Two concepts computed and discarded, and a third never reached.**
      Coinsurance and the deductible move the class-rated premium and leave
      the Legal Liability premium **exactly** unchanged. The LOI factor is
      different: it comes back at **1** on this path, because its own setter is
      gated on the class-rated CovType. The map calls all three "computed and
      ignored"; **two-thirds of that is right.**
  12  **Contents is double**, and each row of the two-row table is unreachable
      from the other side.
  13  **The additional-insurable-interest option** -- four options, two values
      -- and a line of the traced map that is stale.
  14  **Blanket: the map's conclusion is right and its reason is not the
      operative one.**

Derived by hand before the run. Baseline: Building **$60**, Contents **$132**.

    10  class 0074   COLadj 0.069 -> r3(0.01725)=0.017 -> $17
                     and the class-rated premium moves to $75

    11  coinsurance 80%   class-rated moves, Legal Liability stays $60
        deductible 250    class-rated moves, Legal Liability stays $60
        the LOI factor    class-rated 1.172, Legal Liability **1**

    13  Option1 / Option2  1.25 -> r3(0.075) -> $75
        Option3 / Option4  1.0  ->             $60

    python scripts/cf/64_chunk8_fork.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp.tree import read

g8 = import_module("59_chunk8_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")

S, PP = chunk2.STRUCT, chunk4.PP
B_BGI = S + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
C_BGI = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium"
COV = S + "/CommercialPropertyStructureBuildingBasicGroupICoverage"


def rate(mut=None, covtype="Legal Liability"):
    sub = g8.building("Basic") if covtype == "Legal Liability" \
        else _class_rated()
    if mut:
        mut(zeros2.structure(sub))
    return g8.run(sub)[0]


def _class_rated():
    sub = chunk2.submission()
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = (
        "Commercial Property Policy")
    return sub


#: C8-11: id, mutation, class-rated premium must MOVE, LL premium must be 60
DISCARDED = [
    ("coinsurance 80%", lambda st: st.__setitem__("Coinsurance", "80%")),
    ("deductible 250", lambda st: st.__setitem__("Deductible", "250")),
    ("deductible 5,000", lambda st: st.__setitem__("Deductible", "5,000")),
]

#: C8-13: plain-language answer -> option -> factor -> premium
OPTIONS = [
    ("General Lessees, Mgrs or Operators of Prem, in Policies Covering "
     "Tenants or Lessees of Such Prem", "Option1", "1.25", "75"),
    ("Employees Other than Executive Officers or Partners in Policies "
     "Covering Their Employers", "Option2", "1.25", "75"),
    ("Other", "Option3", "1", "60"),
    ("None", "Option4", "1", "60"),
]


def main() -> int:
    ok = True

    # ---- C8-10
    print("=== 10  The rate chain is shared, and diverges only after the "
          "adjustment\n")
    for name, mut, want_col, want_ll, want_cr in (
            ("baseline  class 0951", None, "0.239", "60", "261"),
            ("class 0074", lambda st: st.__setitem__("ClassCode", "0074"),
             "0.069", "17", "75")):
        ll = rate(mut)
        cr = rate(mut, covtype="Building")
        got = (str(read(f"{S}/BasicGroupICauseOfLossAdjustment", ll)),
               str(read(B_BGI, ll)),
               str(read(f"{S}/BasicGroupICauseOfLossAdjustment", cr)),
               str(read(B_BGI, cr)))
        good = got == (want_col, want_ll, want_col, want_cr)
        ok &= good
        print(f"  {name:22s} COLadj LL={got[0]:>6s} classRated={got[2]:>6s}"
              f"   premium LL={got[1]:>4s} classRated={got[3]:>4s}"
              + ("" if good else f"   <-- expected {want_col}/{want_ll}/"
                                 f"{want_col}/{want_cr}"))
    print("  **The two paths agree on the cause-of-loss adjustment to the")
    print("  digit and disagree on every number after it.** Moving the class")
    print("  code moves both; nothing between the adjustment and the premium")
    print("  is shared at all.")

    # ---- C8-11
    print("\n=== 11  Three concepts computed and discarded")
    base_cr = str(read(B_BGI, rate(covtype="Building")))
    for name, mut in DISCARDED:
        ll = str(read(B_BGI, rate(mut)))
        cr = str(read(B_BGI, rate(mut, covtype="Building")))
        good = ll == "60" and cr != base_cr
        ok &= good
        print(f"  {name:20s} class-rated {base_cr:>4s} -> {cr:<4s}   "
              f"Legal Liability stays {ll:>4s}  "
              f"{'OK' if good else 'MISMATCH'}")
    loi_ll = str(read(f"{S}/BasicGroupILOIFactor", rate()))
    loi_cr = str(read(f"{S}/BasicGroupILOIFactor", rate(covtype="Building")))
    good = loi_cr == "1.172" and loi_ll == "1"
    ok &= good
    print(f"  the LOI factor: class-rated {loi_cr}, Legal Liability {loi_ll}  "
          f"{'OK' if good else 'MISMATCH'}")
    print("  **The third concept is not merely discarded -- it is never even")
    print("  computed.** Coinsurance and the deductible ARE computed on this")
    print("  path and thrown away; the LOI factor comes back at 1 because its")
    print("  own setter is gated on the class-rated CovType. So `three")
    print("  concepts computed and discarded` is two-thirds right: **two are")
    print("  computed and discarded, one is never reached.** A distinction")
    print("  invisible in the premium and visible in one field.")
    print("  **This is the claim that cannot be proven by reading**: a value")
    print("  present in the record and absent from the answer looks exactly")
    print("  like one that is simply 1.0.")

    # ---- C8-12
    print("\n=== 12  Contents is double, and each row is unreachable from the "
          "other side")
    b = str(read(B_BGI, rate()))
    c_data = g8.run(g8.contents("Basic"))[0]
    c = str(read(C_BGI, c_data))
    fb = str(read(f"{S}/LegalLiabilityFactor", rate()))
    fc = str(read(f"{PP}/LegalLiabFactor", c_data))
    good = (b, c, fb, fc) == ("60", "132", "0.25", "0.5")
    ok &= good
    print(f"    Building  factor {fb}  premium {b}")
    print(f"    Contents  factor {fc}  premium {c}   "
          f"{'OK' if good else 'MISMATCH'}")
    tbl = book_for(g8.JURIS, g8.ASOF).table("LegalLiabilityFactor")
    print(f"    the table: {len(tbl.rows)} countrywide rows, "
          f"{ {r[1]: str(r[2]) for r in tbl.rows} }")
    print("    **Each lookup pins `CovType` to its own literal**, so Building")
    print("    can never read the PersProp row and Contents can never read")
    print("    the Bldg one. One table, two coverages, no overlap.")

    # ---- C8-13
    print("\n=== 13  The insurable-interest option -- four options, two values")
    for answer, option, factor, want in OPTIONS:
        sub = g8.building("Basic", option=answer)
        data = g8.run(sub)[0]
        got = (str(read(f"{S}/LegalLiabAddlInsurableIntFactor", data)),
               str(read(B_BGI, data)))
        good = got == (factor, want)
        ok &= good
        print(f"    {answer[:44]:46s} {option:8s} x{got[0]:>5s} -> "
              f"${got[1]:>3s}"
              + ("" if good else f"   <-- expected {factor}/{want}"))
    mapping = book_for(g8.JURIS, g8.ASOF).table("AdditionalInsurableIntOption")
    good = len(mapping.rows) == 4
    ok &= good
    print(f"    the plain-language -> Option mapping: {len(mapping.rows)} "
          f"countrywide rows  (expected 4) {'OK' if good else 'MISMATCH'}")
    print("    **The traced map says this table ships EMPTY in the current")
    print("    package and tells the builder to pull it from the 20191201")
    print("    edition. It is filed with four rows in the 2026 edition.**")
    print("    Four options collapse to two values, so half the distinction")
    print("    the submitter is asked to make costs nothing either way.")

    # ---- C8-14
    print("\n=== 14  Blanket -- the map's conclusion is right, its reason is "
          "not the operative one")
    blk = rate(lambda st: st.__setitem__("IncludedInBlkt", "Yes"))
    vals = {f: str(read(f"{S}/{f}", blk)) for f in
            ("CovType", "CauseOfLossToUse", "BlktCauseOfLossValue")}
    ind = str(read(f"{COV}/CoverageOnPolicyIndicator", blk))
    prem = str(read(B_BGI, blk))
    good = (vals["CovType"] == "Legal Liability"
            and vals["CauseOfLossToUse"] == ""
            and ind == "0" and prem == "0")
    ok &= good
    print(f"    CovType is still {vals['CovType']!r} -- branch 2 DOES match")
    print(f"    BlktCauseOfLossValue = {vals['BlktCauseOfLossValue']!r}   "
          f"CauseOfLossToUse = {vals['CauseOfLossToUse']!r}")
    print(f"    CoverageOnPolicyIndicator = {ind}   premium = {prem}   "
          f"{'OK' if good else 'MISMATCH'}")
    print("    **The premium never reaches the `Choose`.** The map reasons")
    print("    about branch ordering inside `SetPremium`; the coverage gate")
    print("    one level up has already written 0, because `CauseOfLossToUse`")
    print("    is copied from an EMPTY `BlktCauseOfLossValue`.")
    print("    **That is the same overwrite C6-28 and C7-25 found** -- three")
    print("    chunks, three coverages, one mechanism: a blanket field the")
    print("    submission cannot populate because a rule rewrites it from")
    print("    policy-level records that are not there.")
    print("    The map's instruction -- do not build a blanket path for Legal")
    print("    Liability -- is correct. **Its reason is not why.**")

    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
