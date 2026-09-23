"""R-8 Phase 2, part 1 -- who consumes the five CoreScratchpad exclusion helpers?

R-5 split the exclusion inputs per coverage group but left six consumers on the
shared master: five `CALC - CoreScratchpad` helper rows plus one cross-sheet
reference. The helpers were left alone because each may feed more than one
coverage, and assigning them to a group on a guess is how you get a silent
mispricing.

This traces every formula that reads those five rows, so each can be assigned on
evidence. It doubles as the agreed rehearsal for R-8's hardest piece -- re-keying
CoreScratchpad away from "one column = one fused item".

Read-only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")

HELPERS = {
    64:  "Numeric Value (fed by 60)",
    68:  "Final Factor (fed by 60)",
    143: "WindstormHailExclusion (fed by 60)",
    26:  "Vandalism lookup key",
    60:  "Windstorm copy",
    175: "Theft lookup key",
    182: "Final deductible factor",
    205: "Wstormexclusion key",
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

        # A reference is either cross-sheet ('CALC - CoreScratchpad'!C26) or,
        # within CoreScratchpad itself, a bare C26. Both are matched inline below.
        found: dict[int, list] = {r: [] for r in HELPERS}
        for sname in SCAN:
            ws = wb.Worksheets(sname)
            used = ws.UsedRange
            last = used.Row + used.Rows.Count - 1
            same_sheet = sname == "CALC - CoreScratchpad"
            for r in range(1, last + 1):
                f = str(ws.Cells(r, 3).Formula)
                if not f.startswith("="):
                    continue
                for hrow in HELPERS:
                    cross = re.search(
                        rf"'CALC - CoreScratchpad'!\$?[A-L]\$?{hrow}\b", f)
                    local = same_sheet and re.search(
                        rf"(?<!['!$A-Z0-9]){'C'}\$?{hrow}\b", f)
                    if cross or local:
                        found[hrow].append(
                            (sname, r, str(ws.Cells(r, 2).Value), f[:74]))

        for hrow, label in HELPERS.items():
            hits = found[hrow]
            print(f"\n=== CoreScratchpad row {hrow} -- {label} : {len(hits)} consumer(s) ===")
            for sname, r, lab, f in hits:
                print(f"   {sname:<24} row {r:>4} {str(lab)[:30]:<30} {f}")
            sheets = {s for s, _, _, _ in hits}
            if len(sheets) == 1:
                print(f"   -> single sheet ({sheets.pop()}): SAFE to assign to that coverage")
            elif len(sheets) > 1:
                print(f"   -> spans {len(sheets)} sheets: must stay shared, or be split into one per coverage")
            else:
                print("   -> no consumers found: candidate dead helper")

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
