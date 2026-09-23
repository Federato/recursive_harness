"""T-1 -- Total Premium omits Special Class and Special Class Business Income.

``'IN - Policy'!I9`` reads ``=I3+I4+I5`` -- Building + Contents + Business
Income -- while displaying **I6** (Special Class) and **I7** (SCBI) directly above
itself. On the current sample it shows $17,904 against $19,744 actual: understated
by $1,840, about 9.3%.

Not a question about ISO's rules. A cell labelled *Total Premium* that omits two of
the five premiums listed above it is wrong on its own terms. Almost certainly the
Special Class rows were added later (BUILD-LOG Entry 33) and the total was never
extended.

Verified three ways: the arithmetic is right, the components are untouched, and the
total still tracks the components when a factor moves -- the last because a total
that is right once may still be a hard-coded number.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

COMPONENTS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
              "OUT_Prem_SCBuilding", "OUT_Prem_SCBI"]
TOTAL = "OUT_Prem_Total"
OLD = "=I3+I4+I5"
NEW = "=I3+I4+I5+I6+I7"


def read(wb):
    comp = {p: wb.Names(p).RefersToRange.Value for p in COMPONENTS}
    return comp, wb.Names(TOTAL).RefersToRange.Value


def show(tag, comp, total):
    parts = "  ".join(f"{k.split('_')[-1]}={v}" for k, v in comp.items())
    print(f"  {tag:<22} {parts}")
    print(f"  {'':<22} sum={sum(comp.values()):<10} TOTAL={total}")


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
        pol = wb.Worksheets("IN - Policy")

        app.CalculateFull()
        comp0, tot0 = read(wb)
        show("before", comp0, tot0)

        current = str(pol.Cells(9, 9).Formula).replace(" ", "")
        if current != OLD:
            sys.exit(f"ABORT: I9 is {current!r}, expected {OLD!r} -- "
                     "not overwriting something unexpected.")

        pol.Cells(9, 9).Formula = NEW
        app.CalculateFull()
        comp1, tot1 = read(wb)
        show("after", comp1, tot1)

        if comp1 != comp0:
            sys.exit("ABORT: component premiums changed -- NOT saving.")
        if tot1 != sum(comp1.values()):
            sys.exit(f"ABORT: total {tot1} != sum {sum(comp1.values())} -- NOT saving.")
        print(f"  -> components untouched; total now equals their sum "
              f"({tot0} -> {tot1}, +{tot1 - tot0})")

        # A total that is right once may still be a constant. Move a factor and
        # confirm it tracks.
        pol.Cells(22, 3).Value = 0.9                        # IRPM
        app.CalculateFull()
        comp2, tot2 = read(wb)
        show("IRPM = 0.9", comp2, tot2)
        if tot2 != sum(comp2.values()):
            sys.exit("ABORT: total stopped tracking components -- NOT saving.")
        print("  -> total still tracks the components when they move")

        pol.Cells(22, 3).Value = 1.0
        app.CalculateFull()
        comp3, tot3 = read(wb)
        if comp3 != comp0 or tot3 != tot1:
            sys.exit("ABORT: did not restore -- NOT saving.")
        show("restored", comp3, tot3)

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
