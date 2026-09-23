"""R-8 Phase 2a -- assign the unambiguous exclusion helpers, and fix SC row 26.

**Two independent jobs, both evidence-backed, both cheap.**

*Job 1 -- three CoreScratchpad helpers.* R-5 left five on the shared master because
each might feed more than one coverage. The trace
(`105_r8_phase2_trace_helpers.py`) resolved them:

    row 26  Vandalism lookup key    -> CALC - Bldg Rating only
    row 175 Theft lookup key        -> CALC - Contents Rating only
    row 182 Final deductible factor -> CALC - Contents Rating only
    row 60  Windstorm copy          -> Bldg (via 68) AND Contents (via 143)
    row 205 Wstormexclusion key     -> Bldg AND Contents

The first three serve one coverage each and are assigned here. **60 and 205 fan out
to two**, and the chain behind them (rows 63/64/65/67) is shared as well, so
splitting them means duplicating a chain rather than repointing a cell. That belongs
inside the Contents migration, which re-keys the same chain anyway -- doing it now
would be work thrown away.

*Job 2 -- `CALC - Special Class` row 26 is a confirmed defect.* It reads
`'IN - Location'!C75`, the Structure-level wind/hail election, for the Special Class
BGII base rate, while rows 27/29/31 in the same block read the Special Class one.
ISO settles it: `CommercialPropertySpecialClassRules.Rule.xml` line 3202 gates that
exact branch on

    <rul:NotExist AtInputDataDef="CommercialPropertyWindstormOrHailExclusion
                                 SpecialClassTable/...SpecialClass" />

-- the **Special Class** record, and there is no Structure-level reference anywhere
in that file. Row 26 is repointed to the Special Class input.

Both masters currently read "No", so premiums must not move. That is the gate, plus
a responsiveness check proving the new wiring is live rather than merely harmless.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
ITEM_COLS = range(3, 13)

#: (sheet, row) -> (old input row, new per-group input row) on 'IN - Location'
HELPERS = {
    ("CALC - CoreScratchpad", 26):  (76, 99),    # vandalism  -> Vandalism-Building
    ("CALC - CoreScratchpad", 175): (77, 103),   # theft key  -> Theft-Contents
    ("CALC - CoreScratchpad", 182): (77, 103),   # ded factor -> Theft-Contents
}

#: CALC - Special Class row 26: from the LOCATION wind/hail to the SPECIAL CLASS one
SC26 = ("CALC - Special Class", 26, "'IN - Location'", 75,
        "'IN - Special Class'", 51)


def show(tag, prem):
    print(f"  {tag:<32} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in prem.items()))


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

        changed = 0
        for (sheet, row), (old, new) in HELPERS.items():
            ws = wb.Worksheets(sheet)
            for c in ITEM_COLS:
                col = chr(ord("A") + c - 1)
                f = str(ws.Cells(row, c).Formula)
                nf = f.replace(f"'IN - Location'!{col}{old}",
                               f"'IN - Location'!{col}{new}")
                if nf != f:
                    ws.Cells(row, c).Formula = nf
                    changed += 1
            print(f"  {sheet} row {row}: input row {old} -> {new}")
        print(f"  {changed} helper cells repointed")

        sheet, row, oldsh, oldrow, newsh, newrow = SC26
        ws = wb.Worksheets(sheet)
        sc_changed = 0
        for c in ITEM_COLS:
            col = chr(ord("A") + c - 1)
            f = str(ws.Cells(row, c).Formula)
            nf = f.replace(f"{oldsh}!{col}{oldrow}", f"{newsh}!{col}{newrow}")
            if nf != f:
                ws.Cells(row, c).Formula = nf
                sc_changed += 1
        if sc_changed == 0:
            sys.exit("ABORT: SC row 26 did not match the expected reference.")
        print(f"  {sheet} row {row}: {oldsh}!{oldrow} -> {newsh}!{newrow} "
              f"({sc_changed} cells)")

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after", after)
        if after != baseline:
            sys.exit("ABORT: premiums moved while both masters still read 'No' "
                     "-- NOT saving.")
        print("  -> unchanged, as required")

        # Responsiveness: the SC wind/hail election must now reach SC row 26.
        sc = wb.Worksheets("IN - Special Class")
        before = [str(sc.Cells(51, c).Formula) for c in ITEM_COLS]
        for c in ITEM_COLS:
            sc.Cells(51, c).Value = "Yes"
        app.CalculateFull()
        moved = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("SC WindHail-SpecialClass = Yes", moved)
        if moved["OUT_Prem_SCBuilding"] == baseline["OUT_Prem_SCBuilding"]:
            sys.exit("ABORT: Special Class did not respond -- wiring inert. NOT saving.")
        print("  -> Special Class responds to its OWN wind/hail election")
        for c, f in zip(ITEM_COLS, before):
            sc.Cells(51, c).Formula = f

        app.CalculateFull()
        restored = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("restored", restored)
        if restored != baseline:
            sys.exit("ABORT: did not restore -- NOT saving.")

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

    # Structural edits get verified after a reopen, not in-session.
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
