"""R-4, follow-up -- Business Income's three factors are `=1`, not references.

The main R-4 pass repointed 120 literal cells on `CALC - Bldg Rating`, and
Contents picked the change up because it chain-references Bldg. **Business Income
did not** -- setting IRPM to 0.9 moved Building and Contents and left BI at 2699.

Cause: BI's head cells hold the *formula* ``=1``. A literal dressed as a formula.
The survey's "does it start with `=`" test read them as wired, which is exactly
how they survived the first pass -- and, presumably, how they were never noticed.

30 cells: rows 19 (IRPM), 20 (MultiPremiumDispersion), 21 (PackageMod), columns
C..L. Every later BI block chains off these three rows, so repointing them
propagates through the sheet.

Same two-sided verification as the main pass: unchanged at 1.0, moves at 0.9.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: CALC - BI Rating row -> the name it should point at.
REPOINT = {
    19: "IN_Pol_IRPMFactor",
    20: "IN_Pol_MultiPremiumDispersionFactor",
    21: "IN_Pol_PackageModFactor",
}
ITEM_COLS = range(3, 13)


def show(tag, prem):
    print(f"  {tag:<26} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in prem.items()))


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
        bi = wb.Worksheets("CALC - BI Rating")
        pol = wb.Worksheets("IN - Policy")

        app.CalculateFull()
        baseline = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("baseline", baseline)

        changed = 0
        for row, name in REPOINT.items():
            label = bi.Cells(row, 2).Value
            for c in ITEM_COLS:
                cur = str(bi.Cells(row, c).Formula).strip()
                if cur not in ("=1", "1", "=1.0"):
                    sys.exit(f"ABORT: BI R{row}C{c} is {cur!r}, not the expected "
                             f"'=1' -- refusing to overwrite something else.")
                bi.Cells(row, c).Formula = f"={name}"
                changed += 1
            print(f"  row {row} ({label}) -> ={name}")
        print(f"  repointed {changed} cells")

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after (all 1.0)", after)
        if after != baseline:
            sys.exit("ABORT: premiums changed at 1.0 -- NOT saving.")
        print("  -> unchanged, as required")

        pol.Cells(22, 3).Value = 0.9
        app.CalculateFull()
        moved = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("IRPM = 0.9", moved)
        if moved["OUT_Prem_BI"] == baseline["OUT_Prem_BI"]:
            sys.exit("ABORT: BI premium still inert -- NOT saving.")
        print("  -> BI now responds to IRPM")

        pol.Cells(22, 3).Value = 1.0
        app.CalculateFull()
        restored = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("restored", restored)
        if restored != baseline:
            sys.exit("ABORT: did not restore -- NOT saving.")

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
