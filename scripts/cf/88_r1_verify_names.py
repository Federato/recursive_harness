"""R-1, part 3 -- verify the names resolve to the cells they claim to.

A name that exists but points somewhere wrong is worse than no name at all, so
this does not just count them: it reads a value *through* each name and checks
it against the value ``pyxlsb`` reads from the raw cell the plan named. Two
independent paths to the same number.

Opens the copy READ-ONLY and quits its own instance.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = REPO / "CF_Algorithm" / "CF_R1_Name_Plan.csv"
TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")


def raw_values() -> dict[tuple[str, int, int], object]:
    """(sheet, row, col) -> value, straight from the file, no Excel involved."""
    from pyxlsb import open_workbook
    out: dict[tuple[str, int, int], object] = {}
    with open_workbook(str(TARGET)) as wb:
        for sheet in ("IN - Policy", "IN - Location", "IN - Special Class"):
            with wb.get_sheet(sheet) as sh:
                for row in sh.rows():
                    for c in row:
                        if c.v is not None:
                            out[(sheet, c.r + 1, c.c + 1)] = c.v
    return out


def main() -> int:
    import subprocess
    n = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")

    plan = list(csv.DictReader(PLAN.open(encoding="utf-8")))
    raw = raw_values()

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    ok = mismatch = missing = 0
    problems: list[str] = []
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        names = {nm.Name: nm for nm in wb.Names}
        print(f"opened read-only -- {len(names)} names present\n")

        for row in plan:
            name = row["Name"]
            if name not in names:
                missing += 1
                problems.append(f"MISSING  {name}")
                continue
            # Read the first cell of whatever the name points at.
            try:
                rng = wb.Names(name).RefersToRange
                via_name = rng.Cells(1, 1).Value
                sheet, r, c = rng.Worksheet.Name, rng.Row, rng.Column
            except Exception as exc:                        # noqa: BLE001
                missing += 1
                problems.append(f"UNRESOLVABLE {name}: {exc}")
                continue

            via_file = raw.get((sheet, r, c))
            a = "" if via_name is None else str(via_name).strip()
            b = "" if via_file is None else str(via_file).strip()
            # Excel hands back floats where the file stores ints, and vice versa.
            try:
                same = abs(float(a) - float(b)) < 1e-9
            except (ValueError, TypeError):
                same = a == b
            if same:
                ok += 1
            else:
                mismatch += 1
                problems.append(
                    f"MISMATCH {name} @ {sheet}!R{r}C{c}: name={a!r} file={b!r}")

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

    print(f"  resolve and match : {ok:>4}")
    print(f"  mismatched        : {mismatch:>4}")
    print(f"  missing/unresolved: {missing:>4}")
    for p in problems[:15]:
        print(f"    ! {p}")
    print("\nInstance closed.")
    return 1 if (mismatch or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
