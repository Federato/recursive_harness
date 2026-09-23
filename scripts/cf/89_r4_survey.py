"""R-4, part 1 -- survey the policy-level factor cells before changing any.

Reads FORMULA text (which pyxlsb cannot give -- it stores cached values only),
so we know whether each of the 74 cells is a literal we can safely repoint or a
formula that means something. Read-only, own instance, quits itself.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
OUT = REPO / "CF_Algorithm" / "CF_R4_Factor_Survey.csv"

SHEETS = ["CALC - Bldg Rating", "CALC - Contents Rating",
          "CALC - BI Rating", "CALC - Special Class"]
LABELS = {"LCM", "IRPM", "MultiPremiumDispersion", "PackageMod"}
PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
ITEM_COLS = range(3, 13)          # C..L


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
    rows = []
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135

        print("--- premiums before any change ---")
        for p in PREMIUMS:
            print(f"  {p:<22} {wb.Names(p).RefersToRange.Value}")

        for sheet in SHEETS:
            ws = wb.Worksheets(sheet)
            last = ws.UsedRange.Rows.Count + ws.UsedRange.Row
            for r in range(1, last + 1):
                lab = ws.Cells(r, 2).Value
                if not isinstance(lab, str):
                    continue
                if lab not in LABELS and not lab.startswith("CyberExcl"):
                    continue
                for c in ITEM_COLS:
                    cell = ws.Cells(r, c)
                    f = cell.Formula
                    if f in (None, ""):
                        continue
                    rows.append({
                        "Sheet": sheet, "Row": r, "Col": c,
                        "Label": lab,
                        "IsFormula": "YES" if str(f).startswith("=") else "no",
                        "Formula": str(f),
                        "Value": cell.Value,
                    })
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

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    formulas = [r for r in rows if r["IsFormula"] == "YES"]
    print(f"\n  cells found            : {len(rows)}")
    print(f"  of those, FORMULAS     : {len(formulas)}")
    print(f"  of those, literals     : {len(rows) - len(formulas)}")
    if formulas:
        print("\n  !! formulas must be understood before repointing:")
        for r in formulas[:12]:
            print(f"     {r['Sheet'][:22]:<22} R{r['Row']}C{r['Col']} {r['Label']:<30} {r['Formula'][:60]}")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
