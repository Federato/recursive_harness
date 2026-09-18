#!/usr/bin/env python3
"""Chunk 8, task C8-03 -- every zero tested against its consuming branch.

Baseline: Building Legal Liability Basic Group I **$60**, Contents **$132**.

**Chunk 8 has more correct-zero paths than any chunk before it**, and they are
correct for four unrelated reasons. Naming them is the whole point: a future
reader who meets one of these in the wild needs to know it is the filing
working, not the engine failing.

  1  **No coverage-form record.** `AttachForm...` appends an empty one, but
     nothing carries `AddlInsurableInt`, so the option is blank and the factor
     falls to its **0.0** default. ISO returns $0 here too -- already
     confirmed by `60_chunk8_raas_probe.py`.
  2  **No `PolicyType` on the policy.** The same rule takes its `Else` and
     **deletes the record the submitter sent** (`<rul:Remove
     RemoveMultiple="true" />`). Same $0, completely different cause -- and
     this is the one that nearly cost an engine change.
  3  **`CovType = "Leasehold Interest"` -- predicted $0 and it REFUSES.** The
     map is right about the wrong scope: it says 0.0 *in this file*, and it
     is, but a submission is not a file. The CovType also activates the
     Leasehold rate chain -- the only `rul:Power` in the package -- and with
     no leasehold data it reaches `Power(0, 0)`. **The engine declines to
     invent an answer.** This zero belongs to chunk 11.
  4  **Builders Risk with a Reporting Form record -- predicted $0 and it
     REFUSES, and here the map is simply wrong.** The outer `If` has no
     `Else`, so when it fails nothing is written and `Premium` is **null**,
     not 0.0. **Unwritten and zero are different things**, which is why this
     project has a guard. C8-08 asks ISO which it returns.
  5  **No `Limit`.** Predicted to RAISE, as every coverage before it has.
  6  **`CovForm` set on the ITEM instead of the occupancy class.** Not a zero
     at all -- it returns chunk 4's class-rated **$223**. **The most dangerous
     case on this page**: four of the five above are loud zeros, and this one
     is a plausible wrong answer.

    python scripts/cf/61_chunk8_zero_cases.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from gl_engine.interp.tree import read

g8 = import_module("59_chunk8_golden_case")
chunk2 = import_module("09_chunk2_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")
chunk4 = import_module("22_chunk4_golden_case")

STRUCT, PP = chunk2.STRUCT, chunk4.PP
B_BGI = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
C_BGI = PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium"
BR_FORM = "CommercialPropertyBuildersRiskReportingForm"
RAISES = object()


def policy(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


#: id, side, mutation, expected premium, (factor, addl factor), why
CASES = [
    ("0  baseline", "B", lambda s: None, "60", ("0.25", "1"),
     "the reference"),

    ("1  no coverage-form record", "B",
     lambda s: zeros2.structure(s).pop(f"{g8.LL_FORM}Table", None),
     "0", ("0.25", "0"),
     "**the rule appends an empty record and the factor still falls to 0.0.** "
     "`AttachForm...` creates one when none exists, so the record is THERE -- "
     "it simply carries no `AddlInsurableInt`, the option is blank, and the "
     "setter's `Else` writes 0.0. **ISO returns $0 here too**"),

    ("2  no PolicyType on the policy", "B",
     lambda s: policy(s).pop("PolicyType", None), "0", ("0.25", "0"),
     "**the same $0 from the opposite cause.** Here the record the submitter "
     "SENT is deleted by ISO's own `<rul:Remove RemoveMultiple=\"true\" />`. "
     "Two zeros, indistinguishable in the answer, and one of them nearly cost "
     "an engine change"),

    ("3  CovType = Leasehold Interest", "B",
     lambda s: zeros2.structure(s).__setitem__("CovType",
                                               "Leasehold Interest"),
     RAISES, None,
     "**predicted $0 and it REFUSES -- and the map is right about the wrong "
     "scope.** The map says Leasehold Interest returns 0.0 *in this file*, "
     "and it does. But a submission is not a file: setting the CovType also "
     "activates the Leasehold Interest rate chain, which carries the only "
     "`rul:Power` in the package, and with no leasehold data it reaches "
     "`Power(0, 0)` and the engine refuses. **The engine declines to invent an "
     "answer**, which is right, and it means this zero cannot be exercised "
     "from chunk 8 at all -- it belongs to chunk 11"),

    ("4  Builders Risk + a reporting form", "B",
     lambda s: zeros2.structure(s).update({
         "CovType": "Builders Risk",
         f"{BR_FORM}Table": {BR_FORM: [{}]}}),
     RAISES, None,
     "**predicted $0 and it REFUSES, and here the map is simply wrong.** The "
     "outer `If` has NO `Else`: when the test fails nothing is written at "
     "all, so `Premium` is **null**, not 0.0. The null-premium guard then "
     "refuses (contract 12.3). The map records this as `Premium = 0.0`; "
     "**unwritten and zero are different things**, and this project has a "
     "guard specifically because they are. Whether ISO returns 0 or refuses "
     "is OI-99's question, and C8-08 will ask it"),

    ("5  no Limit", "B",
     lambda s: zeros2.structure(s).pop("Limit", None), RAISES, None,
     "predicted to raise -- the null-premium guard, contract 12.3"),

    ("6  CovForm on the ITEM, not the occupancy", "C",
     None, "223", None,
     "**not a zero -- a plausible wrong answer.** `SetCovForm` is an "
     "unguarded `Copy` from `../../CovForm`, so the item's value is "
     "overwritten and the class-rated branch runs. $223 is a real Contents "
     "premium; nothing about it looks wrong. **The four loud zeros above are "
     "safer than this one number**"),
]


def contents_wrong_level():
    """Chunk 4's contents with `CovForm` on the ITEM -- the silent one."""
    sub = chunk4.submission("Basic")
    policy(sub)["PolicyType"] = "Commercial Property Policy"
    occ = (zeros2.structure(sub)["CommercialPropertyOccupClassTable"]
           ["CommercialPropertyOccupClass"][0])
    occ["CommercialPropertyPersonalPropertyTable"][
        "CommercialPropertyPersonalProperty"][0]["CovForm"] = (
        "Legal Liability Coverage Form")
    occ[f"{g8.LL_OCC}Table"] = {g8.LL_OCC: [{"AddlInsurableInt": g8.NONE}]}
    return sub


def main() -> int:
    ok = True
    for name, side, mutate, want, factors, _ in CASES:
        if side == "C" and mutate is None:
            sub = contents_wrong_level()
            path, fac_dd = C_BGI, None
        else:
            sub = g8.building("Basic")
            mutate(sub)
            path, fac_dd = B_BGI, "LegalLiabilityFactor"
        raised = None
        try:
            data, ip = g8.run(sub)
        except Exception as exc:
            raised = f"{type(exc).__name__}: {exc}"

        if want is RAISES:
            good = raised is not None
            ok &= good
            print(f"  {name:42s} RAISED: {str(raised)[:64]}  "
                  f"{'OK' if good else 'MISMATCH -- it rated'}")
            continue
        if raised:
            ok = False
            print(f"  {name:42s} RAISED unexpectedly: {raised}")
            continue
        got = str(read(path, data))
        good = got == want
        extra = ""
        if factors:
            f1 = str(read(f"{STRUCT}/{fac_dd}", data))
            f2 = str(read(f"{STRUCT}/LegalLiabAddlInsurableIntFactor", data))
            good &= (f1, f2) == factors
            extra = f"  factors {f1}/{f2}"
        ok &= good
        print(f"  {name:42s} premium={got:>4s}{extra}"
              + ("" if good else f"   <-- expected {want} {factors or ''}"))

    print("\nWhat each case proves")
    for name, _, _, _, _, why in CASES[1:]:
        print(f"\n  {name}\n    " + why.replace("**", ""))
    print("\n  **Four zeros, four unrelated causes, one answer.** An empty")
    print("  record, a deleted record, an unmatched branch and an outer gate")
    print("  all produce $0, and nothing in the premium says which. The fifth")
    print("  path does not produce a zero at all -- it produces a different")
    print("  coverage's premium, and that is the one to be afraid of.")
    print()
    if ok:
        print(f"All {len(CASES)} cases match their derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
