"""R-8 Phase 2b-i -- widen `CALC - Contents Rating` to 40 record columns.

**Split deliberately from the repointing.** The full migration is two changes at
once: widen the sheet to 40 columns, and change what each column *means* (from
"location+building+contents fused" to "one contents record", resolving
building-level values via its parent). Doing both in one pass leaves no way to tell
which half broke anything.

This is the safe half. Columns M..AP are filled with the existing formula pattern,
which resolves against input columns that do not exist yet and therefore produce
zero -- so the roll-ups, widened from `SUM(C30:L30)` to `SUM(C30:AP30)`, must give
exactly the same premium. If they do not, the widening itself is wrong and the
repointing never starts.

The survey (`107_...`) established the design this enables:

* `CALC - Contents Rating` reads only 14 input rows directly, but **21
  CoreScratchpad rows** -- that is where building-level values (protection class,
  territory, construction, deductible) come from.
* CoreScratchpad is keyed one column per item and shared with Building.
* So CoreScratchpad is **not** re-shaped. Instead each contents column will carry
  its parent building's column index, and read building-level values with
  `INDEX('CALC - CoreScratchpad'!$C{row}:$L{row}, 1, ParentCol)`.

That keeps R-3's annotations, R-7's roll-up and the whole shared chain intact.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
SHEET = "CALC - Contents Rating"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

OLD_LAST = 12          # column L
NEW_LAST = 42          # column AP -- 40 record columns, C..AP
ROLLUPS = {31: 30, 59: 58, 82: 81, 110: 109}     # total row -> detail row


def colname(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


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
        app.CalculateFull()
        baseline = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("baseline", baseline)

        ws = wb.Worksheets(SHEET)
        used = ws.UsedRange
        last_row = used.Row + used.Rows.Count - 1

        if str(ws.Cells(31, 3).Formula).replace(" ", "") != "=SUM(C30:L30)":
            sys.exit(f"ABORT: roll-up at row 31 is "
                     f"{ws.Cells(31,3).Formula!r}, not the expected SUM(C30:L30).")

        # 1. The new columns are left EMPTY on purpose.
        #
        # Filling them by copying column L was tried and rejected: those formulas
        # reference 'CALC - CoreScratchpad'!M..AP and 'CALC - Bldg Rating'!M..AP,
        # which do not exist -- those sheets are still ten columns wide. Some of
        # the chain (a CONCATENATE feeding a lookup) returns #VALUE! rather than 0
        # on empty input, and the Contents premium went to #VALUE!.
        #
        # An empty column contributes 0 to a SUM, which is exactly what an
        # unpopulated record slot should contribute. The repointing step fills
        # them with formulas that resolve their parent building explicitly, and
        # that is the right place for it.
        print(f"  columns {colname(OLD_LAST+1)}..{colname(NEW_LAST)} left empty "
              f"(populated by the repointing step)")

        # 2. widen the four roll-ups
        for total_row, detail_row in ROLLUPS.items():
            for c in range(3, NEW_LAST + 1):
                cur = str(ws.Cells(total_row, c).Formula)
                if not cur.startswith("="):
                    continue
                new = re.sub(rf"SUM\(([A-Z]+){detail_row}:[A-Z]+{detail_row}\)",
                             rf"SUM(\g<1>{detail_row}:{colname(NEW_LAST)}{detail_row})",
                             cur)
                if new != cur:
                    ws.Cells(total_row, c).Formula = new
            print(f"  roll-up row {total_row}: {ws.Cells(total_row,3).Formula}")

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after widening", after)
        if after != baseline:
            sys.exit("ABORT: premiums moved on a pure widening -- NOT saving. "
                     "The new columns are contributing something they should not.")
        print("  -> unchanged: the 30 new columns contribute exactly zero")

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        wb.Close(SaveChanges=False)
        wb = None
        print("\n  saved and closed.")
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app

    print("  reopening to verify the persisted state")
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        app.CalculateFull()
        final = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after reopen", final)
        ok = final == baseline
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
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
