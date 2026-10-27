"""M-1, part 1 -- what is actually on `CALC - Special Class`.

**Correcting my own R-4 finding.** R-4's survey reported that this sheet "carries
no IRPM / PackageMod / MultiPremiumDispersion cells at all". That was wrong, and
it was wrong for a specific, repeatable reason: the survey matched labels against
the *abbreviated* names the Building/Contents/BI sheets use (`IRPM`, `PackageMod`,
`MultiPremiumDispersion`) -- but this sheet uses ISO's *full* names
(`IRPMFactor`, `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor`).

A clean result that was really an empty search. Same class of defect the harness
kept finding in its own instruments -- which is why this one reads the sheet and
reports what is there, rather than asking whether a guessed label exists.

Read-only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
SHEET = "CALC - Special Class"
WANTED = ("IRPMFactor", "PackageModFactor",
          "MultiPremiumAndDispersionCreditFactor")


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        ws = wb.Worksheets(SHEET)
        used = ws.UsedRange
        last_row = used.Row + used.Rows.Count - 1
        last_col = used.Column + used.Columns.Count - 1
        print(f"{SHEET}: used range to row {last_row}, col {last_col}\n")

        # How many item columns actually carry data?
        widths = []
        for c in range(3, min(last_col, 14) + 1):
            if ws.Cells(22, c).Formula not in (None, ""):
                widths.append(c)
        print(f"item columns carrying a PREMIUM formula: {widths}\n")

        print("--- the three factors, and how each cell is populated ---")
        for r in range(1, last_row + 1):
            lab = ws.Cells(r, 2).Value
            if not isinstance(lab, str) or lab not in WANTED:
                continue
            cells = []
            for c in widths or range(3, 6):
                f = str(ws.Cells(r, c).Formula)
                cells.append(f)
            kind = "LITERAL" if not cells[0].startswith("=") else "formula"
            print(f"  row {r:>4} {lab:<40} {kind:<8} {cells[0][:34]}")

        print("\n--- PREMIUM formulas: do they consume the factors? ---")
        for r in range(1, last_row + 1):
            lab = ws.Cells(r, 2).Value
            if lab == "PREMIUM":
                print(f"  row {r:>4}  {str(ws.Cells(r, 3).Formula)[:150]}")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
