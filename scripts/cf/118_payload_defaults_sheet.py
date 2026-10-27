"""Payload generator Step 4 -- the `Defaults` sheet.

After R-8 the payload reader reads `IN - Schedule` directly (user decision,
2026-09-22), so Step 4 is only this: the twelve values the workbook does not hold,
from `CF_Payload_Sheet_Spec_Step3.html`. The reader fails loudly if one it needs is
missing -- it never invents a rating input (decision 8).

EffectiveDate was "your call" in the spec (no input exists anywhere). It is set to the
build date and is meant to be edited per run; the edition a state rates on follows it.

Premium-neutral by construction: nothing in the workbook reads this sheet. Verified.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
p4a = import_module("112_r8_phase4a_building")

SHEET = "Defaults"
ROWS = [
    ("Field", "Value", "Why"),
    ("LossCostMultiplier", 1.0, "BUILD-LOG Entry 35: 1.0 passes ISO's filed loss cost through unchanged"),
    ("PackageModFactor", 1.0, "overridden per run by IN - Policy C23 when set"),
    ("MultiPremiumAndDispersionCreditFactor", 1.0, "overridden per run by IN - Policy C24 when set"),
    ("IRPMFactor", 1.0, "overridden per run by IN - Policy C22 when set"),
    ("BlktRated", "No", "blanket is unbuilt in the rater"),
    ("MUBlktRated", "No", "blanket is unbuilt in the rater"),
    ("IncludedInBlkt", "No", "blanket is unbuilt in the rater"),
    ("BlktIDNum", "omit", "not sent"),
    ("TerrorismOverride", "No", "terrorism/TRIA untraced on both sides (harness chunk 13)"),
    ("RatingTypeBasicGroupII", "= RatingType", "same rater input; split if Group II ever rates on another basis"),
    ("EQCovIndicator", "No Coverage", "earthquake unbuilt on both sides (harness chunk 10)"),
    ("EffectiveDate", "2026-09-22", "no input exists; set per run -- the ISO edition follows it"),
]


def main() -> int:
    if p4a.TARGET.name.lower() == p4a.FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb, ok = None, False
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0)
        app.Calculation = -4135
        app.CalculateFull()
        base = p4a.prem(wb)
        if SHEET in [w.Name for w in wb.Worksheets]:
            sys.exit(f"ABORT: '{SHEET}' already exists -- not overwriting it.")
        ws = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
        ws.Name = SHEET
        for r, row in enumerate(ROWS, start=1):
            for c, v in enumerate(row, start=1):
                ws.Cells(r, c).Value = p4a.as_input(v) if isinstance(v, str) else v
        app.CalculateFull()
        after = p4a.prem(wb)
        p4a.show("premiums before", base)
        p4a.show("premiums after", after)
        if after != base:
            print("  GATE FAILED: a premium moved -- NOT saving.")
        else:
            app.Calculation = -4105
            app.CalculateFull()
            wb.Save()
            ok = True
            print(f"  '{SHEET}' added ({len(ROWS) - 1} rows) and saved.")
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
        p4a.reap_orphans(set(pre))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
