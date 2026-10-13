#!/usr/bin/env python3
"""Chunk 3, tasks 17, 19 and 20 -- the three things Special does differently.

  17  **`SpecialBuildersRiskRate` carries a countrywide row (0.015) and
      `SpecialBuildingRate` does not.** So the two base-rate paths behave
      differently when a state is silent, and that asymmetry is the reason FL
      and PR needed a rule override for one path and nothing at all for the
      other.
  19  **Two amount-of-insurance sums used only as deductible keys** --
      `SpecialTotAmtInsurance` and `SpecialIncludingTheftTotAmtInsurance`, the
      second only when a SEPARATE theft deductible applies. Chunk 1's
      location-total trap in a new form, with a gate in front of it.
  20  **`SetSpecialCauseOfLossAdjustment` has no `IsNull` guard and always
      recomputes** -- unique among the four forms. Verify re-entry cannot
      double-apply, and find out what the missing guard DOES change.

Every figure below was derived by hand from Oregon's filed rows before the run.

    python scripts/cf/21_chunk3_special_structure.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import EngineError
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
chunk3 = import_module("15_chunk3_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
sweep = import_module("17_chunk3_enumerate_states")

STRUCT, SPECIAL = chunk2.STRUCT, chunk3.SPECIAL
THEFT = "CommercialPropertyTheftExclusion"

book = book_for(chunk2.JURIS, chunk2.ASOF)
ok = True


def check(label, got, want):
    global ok
    good = str(got) == str(want)
    ok &= good
    print(f"    {label:56s} {str(got):>9s}  "
          f"(expected {str(want):>9s}) {'OK' if good else 'MISMATCH'}")


def run(theft_record=False, runs=1, **mut):
    sub = chunk3.submission("Special")
    st = zeros2.structure(sub)
    for k, v in mut.items():
        if v is None:
            st.pop(k, None)
        else:
            st[k] = v
    if theft_record:
        st[f"{THEFT}Table"] = {THEFT: [{}]}
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    for _ in range(runs):
        Interpreter(book, rounding=ROUNDING, trace=False,
                    null_arithmetic=NULL_ARITHMETIC).run(data)
    return data


def v(data, dd):
    return read(f"{STRUCT}/{dd}", data)


print(f"{book}\n")

# ---------------------------------------------------------------- task 17
print("=== 17  The two base-rate paths behave differently when a state is "
      "silent")
d = run(ClassCode="1150")
check("class 1150 base -- SpecialBuildersRiskRate, countrywide",
      v(d, "SpecialBaseRate"), "0.015")
check("class 1150 coinsurance (the 1150 literal again)",
      v(d, "CoinsuranceFactor"), "1")
check("class 1150 premium", read(SPECIAL, d), "18")
d = run()
check("class 0951 base -- SpecialBuildingRate, Oregon's own row",
      v(d, "SpecialBaseRate"), "0.047")
check("class 0951 premium", read(SPECIAL, d), "54")

print("\n    The asymmetry, enumerated across every jurisdiction:")
res = CFEditionResolver()
bldg_rows, brisk_rows = [], []
for j in res.jurisdictions:
    b = book_for(j, chunk2.ASOF, resolver=res)
    bldg_rows.append(j) if not b.table("SpecialBuildingRate").is_empty else None
    brisk_rows.append(j) if not b.table("SpecialBuildersRiskRate").is_empty \
        else None
n = len(res.jurisdictions)
check(f"jurisdictions resolving SpecialBuildingRate rows (of {n})",
      len(bldg_rows), 45)
check(f"jurisdictions resolving SpecialBuildersRiskRate rows (of {n})",
      len(brisk_rows), n)
print("    45 of 47 for the building path, 47 of 47 for Builders Risk -- and")
print("    the two missing are FL and PR, the same two that had to override")
print("    `SetSpecialBaseRate` to rate Special at all. The Builders Risk path")
print("    needed no override anywhere, because the countrywide 0.015 is")
print("    there to fall back on. **One header-only table is the entire")
print("    reason two states file a rule the other 45 do not.**")

# ---------------------------------------------------------------- task 19
print("\n=== 19  Two amount-of-insurance sums, used only as deductible keys")
CASES19 = [
    ("baseline -- no theft deductible", {}, False, "0.97", "54",
     "branch 4: keyed on `SpecialTotAmtInsurance`, using `Deductible` 1,000"),
    ("TheftDeductible 2,500 -- a SEPARATE theft deductible",
     {"TheftDeductible": "2,500"}, False, "0.89", "50",
     "branch 1: keyed on `SpecialIncludingTheftTotAmtInsurance`, and using "
     "the THEFT deductible (2,500 -> 0.89) rather than the building one"),
    ("TheftDeductible 1,000 -- EQUAL to Deductible",
     {"TheftDeductible": "1,000"}, False, "0.97", "54",
     "branch 1 requires TheftDeductible != Deductible, so an identical theft "
     "deductible is not a separate one and the branch is skipped"),
    ("TheftDeductible 2,500 AND theft excluded (CP 10 33)",
     {"TheftDeductible": "2,500"}, True, "0.97", "47",
     "branch 1 also requires the theft exclusion indicator to be 0. Excluding "
     "theft makes a separate theft deductible irrelevant -- the 0.88 credit "
     "applies instead and the deductible reverts to the building one"),
]
for label, mut, theft, ded, prem, why in CASES19:
    d = run(theft_record=theft, **mut)
    check(f"{label[:52]:52s} ded", v(d, "DeductibleFactorSpecial"), ded)
    check(f"{'':52s} prem", read(SPECIAL, d), prem)
print()
for label, _, _, _, _, why in CASES19:
    print(f"    {label}\n        {why}")

d = run()
both = (v(d, "SpecialTotAmtInsurance"),
        v(d, "SpecialIncludingTheftTotAmtInsurance"))
check("both sums are written", "yes" if all(both) else "no", "yes")
check("and both equal the building limit here", both[0] == both[1], True)
print("    **They are equal in this case and that is a limitation, not a")
print("    result.** Both sums are `StructureLimitToUse` plus occupancy and")
print("    special-class rollups, and this submission has neither -- so the")
print("    two can only be told apart once Contents exists. Logged for chunk")
print("    4 rather than faked here: what IS proven is which sum each branch")
print("    READS, which is the part that decides the band.")

# ---------------------------------------------------------------- task 20
print("\n=== 20  The missing IsNull guard -- what it does and does not do")
one, two = run(), run(runs=2)
check("single pass  SpecialCauseOfLossAdjustment",
      v(one, "SpecialCauseOfLossAdjustment"), "0.047")
check("SECOND pass  SpecialCauseOfLossAdjustment (re-entry)",
      v(two, "SpecialCauseOfLossAdjustment"), "0.047")
check("SECOND pass  premium", read(SPECIAL, two), "54")
print("    **Re-entry cannot double-apply.** The rule recomputes from")
print("    `SpecialRate x theft x roofACV` -- none of which is its own output")
print("    -- so running the whole chain twice over one data tree lands on the")
print("    same number. An unguarded rule is only dangerous if it reads what")
print("    it writes, and this one does not.")

print("\n    What the missing guard DOES change -- a supplied value:")
d = run(SpecialCauseOfLossAdjustment="9.999")
check("submitted SpecialCauseOfLossAdjustment=9.999 -> OVERWRITTEN",
      v(d, "SpecialCauseOfLossAdjustment"), "0.047")
check("  premium unaffected", read(SPECIAL, d), "54")
d = run(SpecialBaseRate="9.999")
check("submitted SpecialBaseRate=9.999 -> HONOURED (IsNull-guarded)",
      v(d, "SpecialBaseRate"), "9.999")
check("  premium", read(SPECIAL, d), "11398")
print("    Same submission shape, opposite outcomes. Every other rule in the")
print("    Special chain is `IsNull`-guarded, so a value supplied in the")
print("    payload WINS and the filed rate is never looked up -- `9.999`")
print("    rides all the way to an $11,398 premium with nothing raised.")
print("    `SetSpecialCauseOfLossAdjustment` is the one step that cannot be")
print("    overridden that way. **The unguarded rule is the safe one**, which")
print("    is the opposite of what the task list expected to find.")

print()
if ok:
    print("Tasks 17, 19 and 20 all match.")
    raise SystemExit(0)
print("MISMATCHES above.")
raise SystemExit(1)
