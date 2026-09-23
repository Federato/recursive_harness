#!/usr/bin/env python3
"""Chunk 9's golden case -- the first populated blanket submission in this
project. Building, Basic Group I, two structures sharing one `BlktIDNum`.

The derivation, written BEFORE this ran, is in `docs/CF-CHUNK9-GOLDEN-CASE.md`.

Built differentially: **chunk 1's own risk** (Oregon, class code 0951,
Frame, Portland territory, protection class 3, Basic Group I, Coinsurance
90%, Deductible 1,000), duplicated into two structures at one location, with
`IncludedInBlkt` switched to "Yes" on both and one shared `BlktIDNum`. Every
rate row through `BasicGroupICauseOfLossAdjustment` (0.239) and
`DeductibleFactorBasicGroupI` (0.98 / 0.99) is the SAME row chunk 1 already
proved -- the only new variable is the blanket election and the averaging
engine it feeds.

    Structure A   FullBldgValue 100,000   DeductibleFactor 0.98 [OR, chunk 1 case A]
    Structure B   FullBldgValue 200,000   DeductibleFactor 0.99 [OR, chunk 1 case B]
    BlktLimit (Detail.TotalLimit, an INPUT, not a sum)      300,000

Two structural facts, both confirmed against the rule XML rather than
inferred from the census doc, decide the shape of this submission:

  1. **`BlktRated="Yes"` on the POLICY is a THIRD gate, distinct from
     `IncludedInBlkt` and `MUBlktRated`, and it is destructive.**
     `AttachFormBlanketRating` (`CommercialPropertyRules.Rule.xml`) runs at
     `ErcProcess` step "ErcDoConditionalMandatoryLogic", and its `Else`
     branch is `<rul:Remove AtDataDef="CommercialPropertyBlanketRatingTable/
     CommercialPropertyBlanketRating" RemoveMultiple="true" />`. Submit a
     `CommercialPropertyBlanketRating` record without `BlktRated="Yes"` on
     the policy and ISO's own rule deletes it -- **C6-01's trap
     (`PolicyType`) and C8's trap (also `PolicyType`) for a third time, one
     chunk later.** Neither the census nor the task's structural findings
     named this field; it surfaced only from reading `AttachFormBlanketRating`
     directly, per this project's "read the actual XML" rule.
  2. **The Detail record's `TotalFullValueAmount` is DERIVED, not supplied.**
     `SetTotalFullValueAmount` (`CommercialPropertyBlanketRatingDetailRules`)
     sums `FullBldgValue` across every structure with `IncludedInBlkt="Yes"`
     and `BlktIDNum` equal to the Detail record's own `UnitNumber`. Supplying
     it directly would be silently overwritten -- this project's
     `ClassCode`/`ClassCodeToUse` trap, generalized to blanket. `TotalLimit`
     (-> `BlktLimit`), by contrast, is never set by any rule in the 13,458-line
     Detail file: it IS a genuine input, the company's chosen blanket limit
     of insurance.

    python scripts/cf/68_chunk9_golden_case.py [--trace]

**Result: MISMATCH, and it is an engine gap, not a bad derivation.** The
Detail record's own aggregate fields compute exactly right --
`TotalFullValueAmount = 300000`, matching the hand sum -- but
`BasicGroupIAvgRate` comes back `0.236`, not the hand-derived `0.255`, and
both structures' `Premium` come back `$0`, not `$255` / `$510`. Both
symptoms trace to ONE root cause, named precisely below; nothing here is
fixed, per the chunk's standing rule.

**The gap: `ForEach` does not distinguish `@AtDataDef` from
`@AtInputDataDef`.** `gl_engine/interp/nodes.py::_for_each` reads
`el.attrib.get("AtDataDef") or el.attrib.get("AtInputDataDef")` and, either
way, repoints the WHOLE frame -- reads AND writes -- at the iterated item
(`inner = fr.at(item)`). `SetNonEQBlanketValues` and
`SetNonEQBlanketRatesAndFactors` (`CommercialPropertyStructureRules.Rule.xml`)
both walk `../../../../CommercialPropertyBlanketRatingTable/.../
CommercialPropertyBlanketRatingDetail` with `ForEach AtInputDataDef=...`,
and their bodies write bare, unprefixed `ToDataDef`s --
`BlktCauseOfLossValueTemp`, `BlktTotalFullValueAmountTemp`,
`BlktBasicGroupIAvgRateTemp` -- meaning "the structure I'm already
inside", the rule's own bound `CommercialPropertyStructure` row. Under this
engine's `_for_each`, those writes land on the ITERATED Detail record
instead. Proof, read straight off the tree after a run: the Detail record
ends up carrying stray, undeclared children named
`BlktCauseOfLossValueTemp` (`= "Basic Group I"`, a self-referential
no-op copy since `Detail.CauseOfLoss` is also `"Basic Group I"`) and
`BlktBasicGroupIAvgRateTemp` (`= 0.236`) -- fields that belong on
`CommercialPropertyStructure`, never on `CommercialPropertyBlanketRatingDetail`
in the DataDef -- while the STRUCTURE's own `BlktTotalFullValueAmount` and
`BlktLimit` stay at their pre-walk default of `0`.

That single miswrite cascades twice:

1. `SetBlktBasicGroupILOIFactor` gates its table lookup on
   `BlktTotalLOIToUse > 0`, which itself needs `BlktTotalFullValueAmount > 0`
   (`SetBlktTotalLOIToUse`). Stuck at `0`, both gates fail and
   `BlktBasicGroupILOIFactor` falls to its literal `1.0` default instead of
   the filed `1.172` / `1.039` this case was built to exercise. Recomputing
   `BasicGroupIStructureCalc` with `LOI=1.0` for both structures reproduces
   the engine's `70744` / `0.236` EXACTLY (`23422 + 47322 = 70744`,
   `70744/300000 = 0.236` rounded) -- so the averaging engine's own
   arithmetic is right; it is just being fed a `1.0` it should not have.
2. `SetPremium`'s blanket branch gates on
   `Convert(BlktTotalFullValueAmount) > 0.0` before computing anything, and
   its `Else` is a bare `Premium := 0.0`. Since the structure's own
   `BlktTotalFullValueAmount` never left `0` (the copy from `Detail.
   TotalFullValueAmount`, which DID compute correctly, never reached the
   structure), that gate fails on both structures and `SetPremium` takes the
   zero branch -- explaining `$0` / `$0` with no error anywhere.

This is not a new arithmetic node and not a new rating concept -- it is a
missing distinction in one existing evaluator between a ForEach that should
reparent writes (`@AtDataDef`) and one that should only reparent reads
(`@AtInputDataDef`). Fixing it is squarely engine code, and this chunk's
standing rule is analysis and gates only: **not fixed here.**

Exit 0 would mean both structures' premiums matched the hand derivation.
They do not, by design of this report: the script exits 1 and prints the
diagnosis above so the mismatch is never mistaken for success.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, dump, read, select_one

JURIS, ASOF = "OR", "20260917"

CP = "CommercialPropertyTable/CommercialProperty"
LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
STRUCT_TBL = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure"
S1 = STRUCT_TBL + "[1]"
S2 = STRUCT_TBL + "[2]"
DETAIL = (CP + "/CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]"
          "/CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]")

BLKT_ID = 100
BLKT_LIMIT = 300_000
VALUE_A = 100_000
VALUE_B = 200_000

#: hand-derived, filed rows cited in the doc
COL_ADJ = Decimal("0.239")                 # chunk 1's own OR/CW row
DEDUCTIBLE_A = Decimal("0.98")             # chunk 1 case A, TotAmtInsurance 100,000
DEDUCTIBLE_B = Decimal("0.99")             # chunk 1 case B, TotAmtInsurance 200,000
LOI_A = Decimal("1.172")                   # BasicGroupILOIFactorBldg[CW] band [100000,125000) at its From edge
LOI_B = Decimal("1.039")                   # same table, band [200000,225000) at its From edge

STRUCT_CALC_A = (VALUE_A * COL_ADJ * DEDUCTIBLE_A * LOI_A).quantize(Decimal("1"))
STRUCT_CALC_B = (VALUE_B * COL_ADJ * DEDUCTIBLE_B * LOI_B).quantize(Decimal("1"))
AVG_RATE = ((STRUCT_CALC_A + STRUCT_CALC_B) / BLKT_LIMIT).quantize(Decimal("0.001"))
PREMIUM_A = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_A) / BLKT_LIMIT) * AVG_RATE
             ).quantize(Decimal("1"))
PREMIUM_B = (Decimal(BLKT_LIMIT) / 100 * (Decimal(VALUE_B) / BLKT_LIMIT) * AVG_RATE
             ).quantize(Decimal("1"))


def _structure(full_value: int) -> dict:
    """Chunk 1's own building, switched to blanket, differing only in value."""
    return {
        "RatingType": "Class",
        "ClassCode": "0951",
        "ConstructionType": "Frame",
        "CovType": "Building",
        "CauseOfLoss": "Basic Group I",
        "Coinsurance": "90%",
        "Limit": str(full_value),
        "FullBldgValue": str(full_value),
        "Deductible": "1,000",
        "LossCostMultiplier": "1.0",
        "IncludedInBlkt": "Yes",
        "BlktIDNum": str(BLKT_ID),
        "PackageModFactor": "1.0",
        "MultiPremiumAndDispersionCreditFactor": "1.0",
    }


def submission() -> dict:
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                # Gate 1 of 3 (structural finding 1 above): without this the
                # form-attachment rule REMOVES the record below, per
                # `AttachFormBlanketRating`'s Else branch.
                "BlktRated": "Yes",
                # Auto-defaults to "No" if omitted (`SetMUBlktRated`), set
                # explicitly per the task spec and the census's gate 1.
                "MUBlktRated": "No",
                "CommercialPropertyBlanketRatingTable": {
                    "CommercialPropertyBlanketRating": [{
                        "CommercialPropertyBlanketRatingDetailTable": {
                            "CommercialPropertyBlanketRatingDetail": [{
                                # The join key both structures' BlktIDNum
                                # must match -- census's own point 5.
                                "UnitNumber": str(BLKT_ID),
                                "Type": "Building Only",
                                "TypeOfBlanketRating": "Average",
                                "CauseOfLoss": "Basic Group I",
                                # "90%" is the ONE value that leaves
                                # `CoinsuranceFactor` at its 1.0 default on
                                # the Detail record (`SetCoinsuranceFactor`'s
                                # own Else branch) -- chosen to keep the
                                # averaging formula's other factor neutral.
                                "Coinsurance": "90%",
                                # Structural finding 2 above: an INPUT, never
                                # set by any rule in the Detail file.
                                "TotalLimit": str(BLKT_LIMIT),
                            }],
                        },
                    }],
                },
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland",
                        "ProtectClass": "3",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [
                                _structure(VALUE_A),
                                _structure(VALUE_B),
                            ],
                        },
                    }],
                },
            }],
        },
    }


def run(trace=False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    ip.run(data)
    return data, ip


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    print("Hand-derivation, computed before this ran:")
    print(f"  StructureCalc A  = round({VALUE_A} x {COL_ADJ} x {DEDUCTIBLE_A} x {LOI_A}, 0)"
          f" = {STRUCT_CALC_A}")
    print(f"  StructureCalc B  = round({VALUE_B} x {COL_ADJ} x {DEDUCTIBLE_B} x {LOI_B}, 0)"
          f" = {STRUCT_CALC_B}")
    print(f"  BasicGroupIAvgRate = round(({STRUCT_CALC_A}+{STRUCT_CALC_B})"
          f"/{BLKT_LIMIT}, 3) = {AVG_RATE}")
    print(f"  Premium A = round({BLKT_LIMIT}/100 x {VALUE_A}/{BLKT_LIMIT} x {AVG_RATE}, 0)"
          f" = {PREMIUM_A}")
    print(f"  Premium B = round({BLKT_LIMIT}/100 x {VALUE_B}/{BLKT_LIMIT} x {AVG_RATE}, 0)"
          f" = {PREMIUM_B}\n")

    data, ip = run(a.trace)

    ok = True
    checks = [
        ("Detail.BasicGroupIAvgRate", DETAIL + "/BasicGroupIAvgRate", str(AVG_RATE)),
        ("Detail.TotalFullValueAmount", DETAIL + "/TotalFullValueAmount",
         str(VALUE_A + VALUE_B)),
        ("Structure A.BlktBasicGroupIAvgRate", S1 + "/BlktBasicGroupIAvgRate",
         str(AVG_RATE)),
        ("Structure B.BlktBasicGroupIAvgRate", S2 + "/BlktBasicGroupIAvgRate",
         str(AVG_RATE)),
        ("Structure A.BlktTotalFullValueAmount", S1 + "/BlktTotalFullValueAmount",
         str(VALUE_A + VALUE_B)),
        ("Structure A Premium", S1 + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium",
         str(PREMIUM_A)),
        ("Structure B Premium", S2 + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium",
         str(PREMIUM_B)),
    ]
    for label, path, want in checks:
        got = read(path, data)
        good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:38s} = {str(got):>10s}{flag}")

    if not ok:
        detail_node = select_one(DETAIL, data)
        stray = [c.tag for c in detail_node.children
                 if c.tag in ("BlktCauseOfLossValueTemp", "BlktTotalFullValueAmountTemp",
                              "BlktBasicGroupIAvgRateTemp", "BlktLimitTemp")]
        print("\n  Root-cause proof -- fields that belong on CommercialPropertyStructure,")
        print("  found instead as stray children of the Detail record ForEach's own item:")
        for tag in stray:
            print(f"    Detail.{tag} = {read(DETAIL + '/' + tag, data)!r}")
        print("  (see the module docstring: ForEach does not distinguish @AtDataDef")
        print("   from @AtInputDataDef, so writes meant for the enclosing structure")
        print("   land on the iterated Detail record instead.)")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}):")
        for m in ip.messages[:20]:
            print(f"    - {m}")

    if a.trace:
        print(ip.trace_text())
    if a.dump:
        print(dump(data))

    print()
    if ok:
        print("Blanket golden case matches: the averaging engine and the "
              "starved SetPremium formula both fired through the ordinary "
              "Interpreter.run entry point.")
        return 0
    print("MISMATCH, and it is the interpreter gap described in the module "
          "docstring -- @AtInputDataDef reparents writes exactly like "
          "@AtDataDef, so the averaging engine's output never reaches the "
          "structure. Not fixed here, per this chunk's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
