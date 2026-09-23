"""R-8 Phase 1 -- build `IN - Schedule` alongside the existing inputs.

Seven stacked blocks in ISO's own hierarchy:

    LOCATION -> BUILDING -> OCCUPANCY CLASS -> CONTENTS
                         -> BUSINESS INCOME
    LOCATION -> SPECIAL CLASS -> SC BUSINESS INCOME

**Populated by formula, not by value.** Every cell reads the corresponding cell on
`IN - Location` / `IN - Special Class`, so the two models describe the same policy
and stay in lockstep while the migration runs. That equivalence is what makes
Phase 2's "premium unchanged" gate mean anything -- if the new sheet held a typed
copy it could drift and the gate would be measuring nothing.

**Nothing reads this sheet yet.** No calc sheet is repointed, so premiums cannot
move. Verified anyway, because "it should be impossible" is how the other bugs got
in.

Capacity is 40 rows per block (the agreed figure). Only the first 10 carry formulas
-- that is all the old column-per-item model can express. Rows 11-40 are empty
capacity for Phase 5, when data is entered here directly instead of being mirrored.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
SHEET = "IN - Schedule"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

CAPACITY = 40
MIRRORED = 10                      # what the old model can express
LOC = "'IN - Location'"
SC = "'IN - Special Class'"


def src(sheet: str, row: int, i: int) -> str:
    """Pull item `i` out of a column-per-item row on an old input sheet."""
    return f"INDEX({sheet}!$C${row}:$L${row},1,{i})"


#: Each block: (name, id template, parent template, active template, fields)
#: field = (column header, source sheet, source row)  -- or (header, None, None)
BLOCKS = [
    ("LOCATION",
     # Read the SAME cell BUILDING.ParentLoc reads, rather than emitting a literal.
     # A literal made LOCATION.ID the text "1" while ParentLoc resolved to the
     # number 1.0 -- and a SUMIFS across a text/number pair matches nothing and
     # reports zero, not an error. Phase 2's roll-up depends on this join.
     lambda i: f'={src(LOC, 4, i)}',
     None,
     lambda i: f'=IF({src(LOC, 15, i)}="State","No","Yes")',
     [("State", LOC, 15), ("ZipCode", LOC, 13), ("City", LOC, 14),
      ("ProtClass", LOC, 22), ("BGITerr", LOC, 17), ("District", LOC, 18),
      ("BGIITerr", LOC, 19), ("SpecialTerr", LOC, 20),
      ("WindHailDed", LOC, 53), ("MultiResCredit", LOC, 57),
      ("HeatingPlantLoc", LOC, 58), ("PerLocationDed", LOC, 55)]),

    ("BUILDING",
     lambda i: f'={src(LOC, 6, i)}',
     lambda i: f'={src(LOC, 4, i)}',
     lambda i: f'=IF({src(LOC, 15, i)}="State","No","Yes")',
     [("CovType", LOC, 8), ("ClassCode", LOC, 26), ("ClassDesc", LOC, 29),
      ("RatingType", LOC, 28), ("ConstrCode", LOC, 60), ("ConstrType", LOC, 62),
      ("ConstrSymbol", LOC, 64), ("NumStories", LOC, 63), ("BCEG", LOC, 23),
      ("OpenSides", LOC, 65), ("Limit", LOC, 43), ("SpecificRate", LOC, 44),
      ("CauseOfLoss", LOC, 50), ("Deductible", LOC, 52),
      ("TheftDed", LOC, 54), ("WindHailDed", LOC, 53),
      ("Valuation", LOC, 67), ("Coinsurance", LOC, 68),
      ("SprinklerSystem", LOC, 72), ("SprinklerLeakageExcl", LOC, 73),
      ("Vacancy", LOC, 85), ("RoofSurfacing", LOC, 24),
      ("SubStdA", LOC, 79), ("SubStdB", LOC, 80), ("SubStdC", LOC, 81),
      ("SubStdD", LOC, 82), ("SubStdE", LOC, 83),
      ("WindHailExcl", LOC, 96), ("VandalismExcl", LOC, 99),
      ("TheftExcl", LOC, 102), ("AddlInsurableIntOption", LOC, 92)]),

    ("OCCUPANCY CLASS",
     lambda i: f'=CONCATENATE({src(LOC, 6, i)}," - 1")',
     lambda i: f'={src(LOC, 6, i)}',
     lambda i: f'=IF({src(LOC, 15, i)}="State","No","Yes")',
     [("ClassCode", LOC, 27), ("OccupCategory", LOC, 32),
      ("OccupSeverity", LOC, 33), ("ContentsGroup", LOC, 34),
      ("CovForm", LOC, 10), ("YardProperty", LOC, 30)]),

    ("CONTENTS",
     lambda i: f'=CONCATENATE({src(LOC, 6, i)}," - 1 - 1")',
     lambda i: f'=CONCATENATE({src(LOC, 6, i)}," - 1")',
     lambda i: f'=IF({src(LOC, 15, i)}="State","No","Yes")',
     [("CovType", LOC, 9), ("Limit", LOC, 45), ("SpecificRate", LOC, 46),
      ("Coinsurance", LOC, 69), ("Valuation", LOC, 67),
      ("WindHailExcl", LOC, 97), ("VandalismExcl", LOC, 100),
      ("TheftExcl", LOC, 103)]),

    ("BUSINESS INCOME",
     lambda i: f'=CONCATENATE({src(LOC, 6, i)}," - BI1")',
     lambda i: f'={src(LOC, 6, i)}',
     lambda i: f'=IF({src(LOC, 15, i)}="State","No","Yes")',
     [("CovType", LOC, 11), ("TypeOfRisk", LOC, 36), ("PctType1", LOC, 37),
      ("PctType2", LOC, 38), ("Limit", LOC, 47), ("SpecificRate", LOC, 48),
      ("Coinsurance", LOC, 70), ("MaxPeriodIndemnity", LOC, 39),
      ("MonthlyLimitIndemnity", LOC, 40), ("ExtraExpenseSchedule", LOC, 41),
      ("WindHailExcl", LOC, 98), ("VandalismExcl", LOC, 101),
      ("TheftExcl", LOC, 104)]),

    ("SPECIAL CLASS",
     lambda i: f'={src(SC, 6, i)}',
     lambda i: f'={src(SC, 4, i)}',
     lambda i: f'=IF({src(SC, 19, i)}+{src(SC, 42, i)}>0,"Yes","No")',
     [("ItemDesc", SC, 10), ("CauseOfLoss", SC, 12), ("InclInBlanket", SC, 13),
      ("ValuationType", SC, 14), ("AgreedValue", SC, 15),
      ("BuildingCoins", SC, 16), ("ContentsCoins", SC, 17),
      ("BuildingLimit", SC, 19), ("LimitInclInBuilding", SC, 21),
      ("LinkedBuildingItemID", SC, 22), ("Deductible", SC, 24),
      ("DedByLocation", SC, 25), ("ProtClass", SC, 27),
      ("BGIITerr", SC, 30), ("ConstrSymbol", SC, 31),
      ("WindHailDed", SC, 33), ("TheftDed", SC, 36),
      ("VandalismExcl", SC, 49), ("WindHailExcl", SC, 51),
      ("TheftExcl", SC, 53)]),

    ("SC BUSINESS INCOME",
     lambda i: f'=CONCATENATE({src(SC, 6, i)}," - BI1")',
     lambda i: f'={src(SC, 6, i)}',
     lambda i: f'=IF({src(SC, 42, i)}>0,"Yes","No")',
     [("CovType", SC, 38), ("TypeOfRisk", SC, 39), ("PctType1", SC, 40),
      ("PctType2", SC, 41), ("Limit", SC, 42), ("Coinsurance", SC, 18),
      ("MaxPeriodIndemnity", SC, 44), ("MonthlyLimitIndemnity", SC, 45),
      ("ExtraExpenseSchedule", SC, 46),
      ("VandalismExcl", SC, 50), ("WindHailExcl", SC, 52),
      ("TheftExcl", SC, 54)]),
]


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135
        app.CalculateFull()
        baseline = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        print("  baseline  " + "  ".join(f"{k.split('_')[-1]}={v}"
                                         for k, v in baseline.items()))

        if SHEET in [w.Name for w in wb.Worksheets]:
            wb.Worksheets(SHEET).Delete()
            print(f"  removed existing '{SHEET}' to rebuild")
        ws = wb.Worksheets.Add(wb.Worksheets(4))       # single positional = Before
        ws.Name = SHEET

        ws.Cells(1, 1).Value = "SCHEDULE"
        ws.Cells(1, 2).Value = (
            "ISO's hierarchy, one row per record. Populated by formula from "
            "IN - Location / IN - Special Class -- nothing reads this sheet yet "
            "(R-8 Phase 1). Rows beyond the first 10 are capacity.")

        r = 3
        summary = []
        for name, id_t, par_t, act_t, fields in BLOCKS:
            ws.Cells(r, 1).Value = name
            r += 1
            hdr = r
            cols = ["ID"] + (["ParentID"] if par_t else []) + ["Active"] + \
                   [f[0] for f in fields]
            for c, h in enumerate(cols, start=1):
                ws.Cells(hdr, c).Value = h
            r += 1
            first = r
            for i in range(1, MIRRORED + 1):
                c = 1
                ws.Cells(r, c).Formula = id_t(i)
                c += 1
                if par_t:
                    ws.Cells(r, c).Formula = par_t(i)
                    c += 1
                ws.Cells(r, c).Formula = act_t(i)
                c += 1
                for _, sheet_ref, row_no in fields:
                    ws.Cells(r, c).Formula = f"={src(sheet_ref, row_no, i)}"
                    c += 1
                r += 1
            r = first + CAPACITY + 1          # leave the rest as capacity
            summary.append((name, len(cols), hdr, first, first + CAPACITY - 1))

        ws.Columns(1).ColumnWidth = 16
        ws.Columns(2).ColumnWidth = 14
        ws.Columns(3).ColumnWidth = 8

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        print("  after     " + "  ".join(f"{k.split('_')[-1]}={v}"
                                         for k, v in after.items()))
        if after != baseline:
            sys.exit("ABORT: premiums moved -- impossible for an unwired sheet. "
                     "NOT saving.")
        print("  -> premiums unchanged (nothing reads the new sheet)")

        print("\n  block            cols  header  rows")
        for nm, nc, hdr, lo, hi in summary:
            print(f"  {nm:<18} {nc:>4}  {hdr:>6}  {lo}-{hi}")

        print("\n--- what it resolved to (active records only) ---")
        for nm, nc, hdr, lo, hi in summary:
            live = []
            for rr in range(lo, lo + MIRRORED):
                act_c = 3 if ws.Cells(hdr, 2).Value == "ParentID" else 2
                if ws.Cells(rr, act_c).Value == "Yes":
                    live.append((ws.Cells(rr, 1).Value,
                                 ws.Cells(rr, 2).Value if act_c == 3 else "",
                                 ws.Cells(rr, act_c + 1).Value))
            print(f"  {nm:<18} {len(live)} active")
            for a, b, c in live[:5]:
                print(f"      {str(a):<12} parent={str(b):<10} {str(c)[:40]}")

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        print("\n  saved.")
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app
    print("Instance closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
