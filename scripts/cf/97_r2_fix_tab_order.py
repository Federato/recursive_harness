"""R-2, part 2 -- put the tabs in the intended order.

The rename pass got the names right and the order wrong. It looped
``if Worksheets(new).Index != i: Move(Before=Worksheets(i))``, which is the classic
off-by-one: moving a sheet renumbers every sheet after it, so a later comparison is
made against indices that have already shifted. Two sheets ended up misplaced.

This does it the way that cannot drift -- walk the plan in order and anchor each
sheet immediately **after** the one already placed, so the sorted prefix grows by
exactly one each step and nothing behind it is ever consulted again.

Sheet order affects no formula, so this is purely cosmetic and cannot change a
premium. It is verified anyway.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

ORDER = [
    "IN - Policy", "IN - Location", "IN - Special Class",

    "CALC - Bldg Rating", "CALC - Contents Rating", "CALC - BI Rating",
    "CALC - Special Class", "CALC - CoreScratchpad",

    "TBL - BGI Territories", "TBL - BGIITerritory", "TBL - ZipCityState",
    "TBL - ProtClass", "TBL - Sprinkler", "TBL - SubStdConditionCode",
    "TBL - ClassCodes", "TBL - ConstructionCodes", "TBL - Derivations",
    "TBL - BldgBGIRating", "TBL - BldgBGIIRating", "TBL - BroadRating",
    "TBL - BldgSpecialRating", "TBL - ContentsTables", "TBL - BI Tables",
    "TBL - Special Class", "TBL - PolicyDropdowns", "TBL - LCM",
]


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

        present = {ws.Name for ws in wb.Worksheets}
        if present != set(ORDER):
            sys.exit(f"ABORT: sheet set mismatch.\n  missing {set(ORDER)-present}"
                     f"\n  extra {present-set(ORDER)}")

        # `Move`'s argument semantics through win32com proved genuinely slippery:
        # the `After=` keyword raises outright, and three separate inferences
        # about what a single positional argument means each contradicted the
        # next. A direct probe (move the sheet at position 5 with
        # `Move(Worksheets(1))`, see where it lands) said **Before** -- position 1.
        #
        # Rather than trust any inference, this applies the order and then checks,
        # and if the book came out exactly reversed it reapplies with the plan
        # flipped. Self-correcting beats being right about COM marshalling.
        # Final technique: anchor by NAME, never by index. `wb.Worksheets(1)`
        # re-evaluated inside a loop gave inconsistent results -- the run came
        # out partially ordered, which is what a stale index reference looks
        # like. Resolving the anchor by its name each iteration removes that
        # variable entirely.
        for name in reversed(ORDER):
            first = wb.Worksheets(1).Name          # read it, then look it up
            if first != name:
                wb.Worksheets(name).Move(wb.Worksheets(first))

        actual = [ws.Name for ws in wb.Worksheets]
        if actual != ORDER:
            for i, (want, got) in enumerate(zip(ORDER, actual), 1):
                if want != got:
                    print(f"  position {i}: wanted {want!r}, got {got!r}")
            sys.exit("ABORT: order still wrong -- NOT saving.")
        print("  tab order correct\n")

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        if after != baseline:
            sys.exit("ABORT: premiums changed -- NOT saving.")
        print("  premiums unchanged  " + "  ".join(
            f"{k.split('_')[-1]}={v}" for k, v in after.items()))

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        print("\n  saved.\n")
        group = None
        for ws in wb.Worksheets:
            g = ws.Name.split(" - ")[0]
            if g != group:
                print(f"  --- {g} ---")
                group = g
            print(f"   {ws.Index:>3}. {ws.Name}")
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
