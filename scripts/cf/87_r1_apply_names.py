"""R-1, part 2 -- apply the defined-name plan to a COPY of the rater.

**Safety protocol, and why each rule exists.**

* Refuses to run if *any* Excel process is alive. A prior session lost unsaved
  work by driving an instance the user had open; never again.
* Refuses to run against ``CFRater1.01.xlsb``. The live rater is not a target,
  ever -- this script only accepts a path it has been told is a copy.
* Uses ``DispatchEx``, not ``Dispatch``. ``Dispatch`` *attaches* to a running
  instance; ``DispatchEx`` always creates a fresh one. That distinction is the
  whole difference between safe and destructive here.
* Quits only the instance it created, and only in a ``finally`` block, so a
  crash mid-run does not leave an orphan process holding the file.

Adds nothing but names. No cell value, formula, sheet or format is touched.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = REPO / "CF_Algorithm" / "CF_R1_Name_Plan.csv"
TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"


def preflight() -> None:
    import subprocess
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True).stdout.strip()
    if out and out not in {"0", ""}:
        sys.exit(f"ABORT: {out} Excel process(es) running. Close Excel first.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    if not TARGET.exists():
        sys.exit(f"ABORT: {TARGET} does not exist -- make the copy first.")
    print(f"preflight OK -- no Excel running, target is {TARGET.name}")


def main() -> int:
    preflight()
    plan = list(csv.DictReader(PLAN.open(encoding="utf-8")))
    print(f"plan: {len(plan)} names\n")

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")   # NEW instance
    app.Visible = False
    app.DisplayAlerts = False
    app.AskToUpdateLinks = False
    app.EnableEvents = False
    print("Excel instance created -- opening workbook (5.4 MB, may take a minute)...")
    wb = None
    added = replaced = failed = 0
    errors: list[str] = []
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        # Only settable once a workbook exists -- Excel raises otherwise.
        # Manual calc keeps 133 Names.Add calls from triggering 133 recalcs
        # of a 5.4 MB formula tree.
        app.Calculation = -4135                             # xlCalculationManual
        existing = {n.Name for n in wb.Names}
        print(f"workbook opened -- {len(existing)} pre-existing names\n")

        for row in plan:
            name, refers = row["Name"], row["RefersTo"]
            try:
                if name in existing:
                    wb.Names(name).RefersTo = refers
                    replaced += 1
                else:
                    wb.Names.Add(Name=name, RefersTo=refers)
                    added += 1
            except Exception as exc:                      # noqa: BLE001
                failed += 1
                errors.append(f"{name}: {exc}")

        wb.Save()
        final = wb.Names.Count
        wb.Close(SaveChanges=False)
        wb = None
        print(f"  added    {added}")
        print(f"  replaced {replaced}")
        print(f"  failed   {failed}")
        for e in errors[:10]:
            print(f"    ! {e}")
        print(f"\n  names in workbook after save: {final}")
    finally:
        # Always tear down the instance this script created -- and only it.
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                 # noqa: BLE001
            pass
        app.Quit()
        del app
    print("\nExcel instance closed. Original CFRater1.01.xlsb untouched.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
