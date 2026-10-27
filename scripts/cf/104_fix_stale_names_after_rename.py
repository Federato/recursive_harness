"""Repair the 133 defined names left pointing at pre-R-2 sheet names.

**What went wrong.** R-2 renamed all 26 sheets. Excel normally rewrites defined
names on rename, and R-2's verification said it had: it compared the set of
unresolvable names before and after and found no growth. That check passed and was
**wrong**, because it ran *in the same session as the rename*. Excel kept resolving
the names from in-memory sheet identity while persisting the stale sheet-name
string. The breakage only surfaced on a later open.

So all 133 names created by R-1 still refer to ``'Policy Inputs'``,
``'Location Inputs'`` and ``'Special Class Inputs'`` -- sheets that no longer exist.

**The lesson, and why this script ends the way it does.** A verification that runs
before a save/close/reopen cycle is testing the in-memory state, not the artefact.
This one saves, closes, reopens, and only then checks -- because the persisted form
is the only form that matters.

Repairs the RefersTo strings; touches no cell.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

RENAMED = {
    "Policy Inputs": "IN - Policy",
    "Location Inputs": "IN - Location",
    "Special Class Inputs": "IN - Special Class",
}

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]


def excel():
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    return app


def audit(wb) -> tuple[int, int, dict]:
    """Return (resolvable, stale, {sheet: count}) for non-shim names."""
    live = {w.Name for w in wb.Worksheets}
    ok = stale = 0
    by_sheet: dict[str, int] = {}
    for nm in wb.Names:
        if nm.Name.startswith("_xl"):
            continue
        m = re.search(r"'([^']+)'!", str(nm.RefersTo))
        sheet = m.group(1) if m else None
        if sheet and sheet not in live:
            stale += 1
            by_sheet[sheet] = by_sheet.get(sheet, 0) + 1
        else:
            ok += 1
    return ok, stale, by_sheet


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")

    # ---------- pass 1: repair ----------
    app = excel()
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135
        ok, stale, by_sheet = audit(wb)
        print(f"  before: {ok} resolvable, {stale} stale")
        for s, c in by_sheet.items():
            print(f"      {c:>4} -> {s!r}")

        fixed = 0
        for nm in wb.Names:
            if nm.Name.startswith("_xl"):
                continue
            rt = str(nm.RefersTo)
            new = rt
            for old, cur in RENAMED.items():
                new = new.replace(f"'{old}'!", f"'{cur}'!")
            if new != rt:
                nm.RefersTo = new
                fixed += 1
        print(f"\n  rewrote {fixed} names")

        ok2, stale2, _ = audit(wb)
        print(f"  in-session: {ok2} resolvable, {stale2} stale")

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        wb.Close(SaveChanges=False)
        wb = None
        print("  saved and closed.")
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app

    # ---------- pass 2: reopen and verify the PERSISTED state ----------
    print("\n  reopening -- this is the check that matters")
    app = excel()
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        app.CalculateFull()
        ok3, stale3, by3 = audit(wb)
        print(f"  after reopen: {ok3} resolvable, {stale3} stale")
        for s, c in by3.items():
            print(f"      {c:>4} -> {s!r}")

        print("\n  premiums read through the names:")
        bad = 0
        for p in PREMIUMS:
            try:
                v = wb.Names(p).RefersToRange.Value
                print(f"      {p:<22} {v}")
            except Exception as exc:                        # noqa: BLE001
                bad += 1
                print(f"      {p:<22} FAILS: {str(exc)[:50]}")
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

    if stale3 or bad:
        print("\n  STILL BROKEN after reopen.")
        return 1
    print("\n  clean after a full save/close/reopen cycle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
