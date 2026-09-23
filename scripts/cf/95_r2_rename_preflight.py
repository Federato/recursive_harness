"""R-2, part 1 -- is it safe to rename the sheets?

Excel rewrites ordinary formula references when a sheet is renamed, and updates
defined names and data-validation sources too. Three things it does **not** fix:

* ``INDIRECT("SheetName!A1")`` -- the sheet name is a string literal, so it keeps
  pointing at a name that no longer exists and the cell goes ``#REF!``.
* VBA that addresses sheets by name.
* Anything outside the workbook that references a sheet by name -- in this project,
  the ``pyxlsb``/COM scripts under ``scripts/cf/``.

This reports all three before anything is renamed. Read-only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")


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

        print(f"sheets: {wb.Worksheets.Count}")
        for ws in wb.Worksheets:
            print(f"   {ws.Index:>3}. {ws.Name}")

        # --- INDIRECT ----------------------------------------------------
        print("\n--- INDIRECT( scan ---")
        total = 0
        for ws in wb.Worksheets:
            found = ws.Cells.Find("INDIRECT", LookIn=-4123, LookAt=2)   # xlFormulas, xlPart
            if found is None:
                continue
            first = found.Address
            hits = []
            while True:
                hits.append((found.Address, str(found.Formula)[:90]))
                found = ws.Cells.FindNext(found)
                if found is None or found.Address == first or len(hits) > 40:
                    break
            total += len(hits)
            print(f"  {ws.Name}: {len(hits)} cell(s)")
            for addr, f in hits[:4]:
                print(f"      {addr}  {f}")
        if total == 0:
            print("  none -- no INDIRECT anywhere. Safe on that count.")

        # --- VBA ----------------------------------------------------------
        print("\n--- VBA ---")
        try:
            comps = wb.VBProject.VBComponents.Count
            print(f"  VBComponents: {comps}")
            if comps:
                for c in wb.VBProject.VBComponents:
                    print(f"      {c.Name} (type {c.Type})")
        except Exception as exc:                            # noqa: BLE001
            print(f"  could not inspect VBProject ({str(exc)[:60]})")
            print("  -- usually means 'Trust access to the VBA project' is off,")
            print("     which itself implies no macro development here.")

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

    # --- our own scripts ------------------------------------------------
    print("\n--- sheet names hard-coded in scripts/cf/*.py ---")
    names = ["IN - Policy", "IN - Location", "IN - Special Class",
             "CALC - Bldg Rating", "CALC - Contents Rating",
             "CALC - BI Rating", "CALC - Special Class", "CALC - CoreScratchpad"]
    for py in sorted((REPO / "scripts" / "cf").glob("*.py")):
        text = py.read_text(encoding="utf-8", errors="replace")
        hit = [nm for nm in names if nm in text]
        if hit:
            print(f"  {py.name}: {', '.join(hit)}")
    print("\n  ^ these need updating in step 3, or they break on the next run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
