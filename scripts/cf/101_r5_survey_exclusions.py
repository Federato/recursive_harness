"""R-5, part 1 -- who reads the exclusion inputs today?

ISO files FIVE exclusion records per peril, one per coverage group:
``…Exclusion`` (Structure) · ``…ExclusionPrsnlProp`` · ``…ExclusionBusnIncome``
· ``…ExclusionSpecialClass`` · ``…ExclusionSpclClassBusnIncome``.

Backlog S-1/S-2/S-3 described only two of them. It is 15 records driven by 6 inputs.

Before splitting anything, find every formula that reads the current single input,
so the rewire is a known list rather than a search-and-hope. Read-only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")

#: (sheet, row) -> what the input means today
MASTERS = {
    ("IN - Location", 75): "Windstorm or Hail Exclusion",
    ("IN - Location", 76): "Vandalism Exclusion",
    ("IN - Location", 77): "Theft Exclusion",
    ("IN - Special Class", 28): "SC Vandalism Exclusion",
    ("IN - Special Class", 32): "SC Windstorm/Hail Exclusion",
    ("IN - Special Class", 35): "SC Theft Exclusion",
}

SCAN = ["CALC - Bldg Rating", "CALC - Contents Rating", "CALC - BI Rating",
        "CALC - Special Class", "CALC - CoreScratchpad"]


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

        pats = {}
        for (sheet, row), label in MASTERS.items():
            pats[(sheet, row)] = re.compile(
                rf"'{re.escape(sheet)}'!\$?[A-L]\$?{row}\b")

        found: dict[tuple, list] = {k: [] for k in MASTERS}
        for sname in SCAN:
            ws = wb.Worksheets(sname)
            used = ws.UsedRange
            last_r = used.Row + used.Rows.Count - 1
            for r in range(1, last_r + 1):
                f3 = str(ws.Cells(r, 3).Formula)
                if "!" not in f3:
                    continue
                for key, pat in pats.items():
                    if pat.search(f3):
                        found[key].append(
                            (sname, r, str(ws.Cells(r, 2).Value), f3[:70]))

        for (sheet, row), label in MASTERS.items():
            hits = found[(sheet, row)]
            print(f"\n=== {sheet}!row {row} -- {label} : {len(hits)} consumer(s) ===")
            for sname, r, lab, f in hits:
                print(f"   {sname:<24} row {r:>4} {str(lab)[:32]:<32} {f}")

        total = sum(len(v) for v in found.values())
        print(f"\ntotal consumer rows found: {total}")
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
