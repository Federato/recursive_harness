"""M-1 -- wire IRPM / PackageMod / MultiPremium into Special Class and SCBI.

**What the survey corrected.** R-4 reported this sheet had no such cells. Wrong:
it has 24 of them, and the premium formulas already consume them --
``=ROUND((C15/100)*C16*C17*C18*C19*C20*C21,0)`` where C17/C18/C19 are the three
factors. R-4's survey matched the *abbreviated* labels the other sheets use and
missed ISO's full names used here. So this is not new rating behaviour after all;
it is the same disconnected-constant defect, in a third place.

**Two defects fixed:**

1. Rows 17/18/19 hold the formula ``=1`` -- a literal disguised as a formula, the
   same shape found on the BI sheet. Every later block chains off them, so all
   eight blocks are pinned to 1.0 with no input.
2. **Row 82 is a genuine chaining bug**: ``MultiPremiumAndDispersionCreditFactor``
   reads ``=C60``, which is *PackageModFactor*, instead of ``=C61``. Special Class's
   Special form therefore counts PackageMod twice and ignores MultiPremium. Invisible
   today because both are 1.0; wrong the moment they differ.

**The fix removes the chain rather than repairing it.** All 24 rows point directly
at the named inputs. A chain that is already wrong in one place will be wrong again
after the next copy-paste; direct reference makes every block independently correct
and retires the whole class of bug. That is what "single source of truth" is for.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
SHEET = "CALC - Special Class"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: label -> the name every row with that label should read.
NAME_FOR = {
    "PackageModFactor": "IN_Pol_PackageModFactor",
    "MultiPremiumAndDispersionCreditFactor": "IN_Pol_MultiPremiumDispersionFactor",
    "IRPMFactor": "IN_Pol_IRPMFactor",
}
ITEM_COLS = range(3, 13)          # C..L -- all ten carry a PREMIUM formula


def show(tag, prem):
    print(f"  {tag:<28} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in prem.items()))


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
        ws = wb.Worksheets(SHEET)
        pol = wb.Worksheets("IN - Policy")

        app.CalculateFull()
        baseline = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("baseline", baseline)

        used = ws.UsedRange
        last_row = used.Row + used.Rows.Count - 1
        targets = []
        for r in range(1, last_row + 1):
            lab = ws.Cells(r, 2).Value
            if isinstance(lab, str) and lab in NAME_FOR:
                targets.append((r, lab))
        print(f"\n  found {len(targets)} factor rows on '{SHEET}'")

        changed = 0
        for r, lab in targets:
            name = NAME_FOR[lab]
            for c in ITEM_COLS:
                ws.Cells(r, c).Formula = f"={name}"
                changed += 1
        print(f"  repointed {changed} cells directly at the named inputs "
              f"(chain removed, row-82 bug retired with it)")

        # --- unchanged at 1.0 ------------------------------------------
        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after (all 1.0)", after)
        if after != baseline:
            sys.exit("ABORT: premiums changed at 1.0 -- NOT saving.")
        print("  -> unchanged, as required")

        # --- IRPM must now reach Special Class and SCBI ----------------
        pol.Cells(22, 3).Value = 0.9
        app.CalculateFull()
        m = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("IRPM = 0.9", m)
        for p in ("OUT_Prem_SCBuilding", "OUT_Prem_SCBI"):
            if m[p] == baseline[p]:
                sys.exit(f"ABORT: {p} still inert -- NOT saving.")
        print("  -> Special Class AND SCBI now respond")
        pol.Cells(22, 3).Value = 1.0

        # --- the row-82 bug: MultiPremium must move Special Class ------
        pol.Cells(24, 3).Value = 0.5
        app.CalculateFull()
        mp = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("MultiPremium = 0.5", mp)
        if mp["OUT_Prem_SCBuilding"] == baseline["OUT_Prem_SCBuilding"]:
            sys.exit("ABORT: MultiPremium does not reach Special Class -- NOT saving.")
        print("  -> MultiPremium reaches Special Class (row-82 bug gone)")
        pol.Cells(24, 3).Value = 1.0

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
