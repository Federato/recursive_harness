#!/usr/bin/env python3
"""Chunk 10, C10-12 -- prove EQClass/EQTerr are LIVE submission inputs, not
just structurally present.

The census and C10-01's golden case already established (by direct
`ToDataDef` search) that neither field is ever ASSIGNED by a rule anywhere
in the corpus -- they are pure submission inputs, the same shape as chunk
2's own `BasicGroupIISymbol`. This task is the dynamic half of that claim:
take the golden case's Building submission, change ONLY `EQTerr` to a
different value that has a different filed rate row (confirmed against
`EQLossCostBldg` directly first), and confirm `EQBaseRate`'s `Lookup`
result -- and the final premium -- actually change. Then repeat for
`EQClass`.

Filed rows read directly, before running (`book.table("EQLossCostBldg")`):

    EQClass="A1", EQTerr="1"  ->  0.009   (the golden case's own row)
    EQClass="A1", EQTerr="2"  ->  0.032   (same class, different territory)
    EQClass="C1", EQTerr="1"  ->  0.012   (different class, same territory)

Changing `EQClass` also moves `EQClassToUse` (`A1`->`A1`, `C1`->`B1 and
C1`, from `EQClassToUse[CW]`) and therefore the deductible-factor row
(`EQPercentageDeductibleFactor[OR](1,"A1","10%")=0.68` vs.
`[OR](1,"B1 and C1","10%")=0.69`) -- so the EQClass case also proves the
downstream `EQClassToUse` lookup is live, not just the base-rate lookup.

    python scripts/cf/96_chunk10_c10-12_eqclass_eqterr_live.py

Exit 0 when both fields move EQBaseRate (and the final premium) off the
golden case's own baseline.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

golden = import_module("85_chunk10_golden_case")

JURIS, ASOF = golden.JURIS, golden.ASOF
STRUCT = golden.STRUCT
ENDT = golden.ENDT


def struct_of(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])


def loc_of(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])


def table_value(book, name, col, **keys):
    t = book.table(name)
    idx = {k: t.col(k) for k in keys}
    for r in t.rows:
        if all(str(r[i]) == str(keys[k]) for k, i in idx.items()):
            return r[t.col(col)]
    raise LookupError(f"{name}: no row matching {keys}")


def run_and_read(sub, book):
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)
    return {
        "EQBaseRate": read(STRUCT + "/EQBaseRate", data),
        "EQClassToUse": read(STRUCT + "/EQClassToUse", data),
        "EQDeductibleFactor": read(STRUCT + "/EQDeductibleFactor", data),
        "FinalEQRate": read(STRUCT + "/FinalEQRate", data),
        "Premium": read(ENDT + "/Premium", data),
    }


def main() -> int:
    book = book_for(JURIS, ASOF)
    print(f"{book}\n")

    base_row = table_value(book, "EQLossCostBldg", "LossCost",
                            StateCode="OR", EQClass="A1", EQTerr="1")
    terr2_row = table_value(book, "EQLossCostBldg", "LossCost",
                             StateCode="OR", EQClass="A1", EQTerr="2")
    class_c1_row = table_value(book, "EQLossCostBldg", "LossCost",
                                StateCode="OR", EQClass="C1", EQTerr="1")
    print("Filed rows, read directly before running:")
    print(f"  EQLossCostBldg[OR](\"A1\",\"1\") = {base_row}   (golden case's own row)")
    print(f"  EQLossCostBldg[OR](\"A1\",\"2\") = {terr2_row}   (EQTerr changed)")
    print(f"  EQLossCostBldg[OR](\"C1\",\"1\") = {class_c1_row}   (EQClass changed)")
    assert base_row != terr2_row, "EQTerr=2 must file a DIFFERENT row -- confirmed before running"
    assert base_row != class_c1_row, "EQClass=C1 must file a DIFFERENT row -- confirmed before running"
    print()

    ok = True

    baseline = run_and_read(golden.submission(), book)
    print("Baseline (golden case, EQClass='A1', EQTerr='1'):")
    for k, v in baseline.items():
        print(f"    {k:20s} = {v}")
    ok &= Decimal(baseline["EQBaseRate"]) == base_row

    sub_terr = golden.submission()
    loc_of(sub_terr)["EQTerr"] = "2"
    r_terr = run_and_read(sub_terr, book)
    print("\nEQTerr changed to '2' (EQClass unchanged, 'A1'):")
    for k, v in r_terr.items():
        print(f"    {k:20s} = {v}")
    moved = Decimal(r_terr["EQBaseRate"]) != Decimal(baseline["EQBaseRate"])
    matches_table = Decimal(r_terr["EQBaseRate"]) == terr2_row
    print(f"    EQBaseRate moved off baseline: {moved}   "
          f"matches the filed EQTerr=2 row: {matches_table}")
    print(f"    Premium moved off baseline ({baseline['Premium']} -> {r_terr['Premium']}): "
          f"{r_terr['Premium'] != baseline['Premium']}")
    ok &= moved and matches_table and r_terr["Premium"] != baseline["Premium"]

    sub_class = golden.submission()
    struct_of(sub_class)["EQClass"] = "C1"
    r_class = run_and_read(sub_class, book)
    print("\nEQClass changed to 'C1' (EQTerr unchanged, '1'):")
    for k, v in r_class.items():
        print(f"    {k:20s} = {v}")
    moved_c = Decimal(r_class["EQBaseRate"]) != Decimal(baseline["EQBaseRate"])
    matches_table_c = Decimal(r_class["EQBaseRate"]) == class_c1_row
    class_to_use_moved = r_class["EQClassToUse"] != baseline["EQClassToUse"]
    ded_moved = Decimal(r_class["EQDeductibleFactor"]) != Decimal(baseline["EQDeductibleFactor"])
    print(f"    EQBaseRate moved off baseline: {moved_c}   "
          f"matches the filed EQClass=C1 row: {matches_table_c}")
    print(f"    EQClassToUse moved ({baseline['EQClassToUse']} -> {r_class['EQClassToUse']}): "
          f"{class_to_use_moved}")
    print(f"    EQDeductibleFactor moved ({baseline['EQDeductibleFactor']} -> "
          f"{r_class['EQDeductibleFactor']}): {ded_moved}")
    print(f"    Premium moved off baseline ({baseline['Premium']} -> {r_class['Premium']}): "
          f"{r_class['Premium'] != baseline['Premium']}")
    ok &= moved_c and matches_table_c and class_to_use_moved and ded_moved and \
        r_class["Premium"] != baseline["Premium"]

    print()
    if ok:
        print("Both EQTerr and EQClass are confirmed LIVE: changing either one "
              "alone moves EQBaseRate to a DIFFERENT filed row and moves the "
              "final premium -- not just structurally present, but actually "
              "read by the Lookup at runtime. EQClass also confirmed to move "
              "the downstream EQClassToUse/EQDeductibleFactor chain. No engine "
              "gap.")
        return 0
    print("MISMATCH above -- see printed values.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
