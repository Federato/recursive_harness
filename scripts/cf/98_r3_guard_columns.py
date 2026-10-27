"""R-3 -- make every calc row explain itself.

Adds two columns to the right of the item columns on each rating worksheet:

``M  Source``  where this row's value comes from, derived by parsing the actual
               formula -- a lookup table, a named input, a chained cell, or
               **CONSTANT**, which is the flag that a hard-coded number is sitting
               where a lookup belongs.
``N  Check``   a live formula that counts zeros among the **active** items only.

**Why "active" matters.** The item columns are C..L but only the first few are
populated; the rest are placeholder slots. A naive zero count would report six
zeros on every row forever and be ignored within a day. These formulas test each
column's State cell (via the R-1 named ranges ``IN_Loc_State`` / ``IN_SC_State``)
and count only items that are really there.

**This pass cannot change a premium.** It only writes to two previously empty
columns that no formula reads. That is the one structural difference from every
other change in this series -- the others rewired live formulas and needed
before/after proof; this one is additive by construction. Verified anyway.

Two severities, since none was specified: CONSTANT (a hard-coded value where a
lookup is expected) and ZERO (an active item zeroed). Anything else reads "ok".
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: sheet -> the named range whose non-placeholder entries mark a live item.
SHEETS = {
    "CALC - Bldg Rating":     ("IN_Loc_State", "State"),
    "CALC - Contents Rating": ("IN_Loc_State", "State"),
    "CALC - BI Rating":       ("IN_Loc_State", "State"),
    "CALC - Special Class":   ("IN_SC_State", "State"),
}

SRC_COL, CHK_COL = 13, 14          # M, N
FIRST_ITEM, LAST_ITEM = "C", "L"

#: Only MULTIPLICATIVE terms are zero-checked.
#:
#: The first pass checked anything rate-ish and produced mostly noise, because a
#: zero is perfectly normal in three common cases:
#:   * additive rates -- `VacantBuildingRate`, `SubStdConditionRate` are 0 unless
#:     the condition applies, and they are *added*, so 0 is the neutral value;
#:   * an unelected form -- Broad's `BaseRate` is 0 on a risk that elects Special;
#:   * branch-only values -- `LowestBaseRate` is 0 outside the wind/hail-excluded
#:     rebuild.
#: A zero in a *factor* has none of those excuses: it is multiplied in, so it
#: takes the whole chain to zero. That is the case worth an alarm, and it is the
#: shape of the documented Joisted-Masonry defect.
FACTORISH = re.compile(r"factor|multiplier|coins", re.IGNORECASE)
SKIP = re.compile(r"premium|limit|^total", re.IGNORECASE)

#: Block titles carry a typed 1 and are not factors -- flagging them as CONSTANT
#: was the other half of the first pass's noise.
HEADER = re.compile(
    r"^(basic group|building|business income|contents|broad|special"
    r"|special class|personal property)\b.*$", re.IGNORECASE)


def classify(formula: str) -> str:
    """Formula text -> a short, human statement of where the value came from."""
    f = (formula or "").strip()
    if not f:
        return ""
    if not f.startswith("="):
        return "CONSTANT (typed value)"
    body = f[1:]
    if re.fullmatch(r"-?[\d.]+", body):
        return "CONSTANT (hard-coded)"
    m = re.search(r"\b(IN_[A-Za-z_]+|OUT_[A-Za-z_]+)\b", body)
    if m:
        return f"input: {m.group(1)}"
    m = re.search(r"'([^']+)'!", body)
    if m:
        return f"sheet: {m.group(1)}"
    m = re.search(r"\b([A-Za-z][A-Za-z0-9_ ]*)!", body)
    if m:
        return f"table: {m.group(1).strip()}"
    if re.fullmatch(r"\$?[A-L]\$?\d+", body):
        return f"chained: {body}"
    return "computed"


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
        print("  baseline  " + "  ".join(f"{k.split('_')[-1]}={v}"
                                         for k, v in baseline.items()))

        totals = {"rows": 0, "const": 0, "checks": 0}
        for sheet, (active_name, placeholder) in SHEETS.items():
            ws = wb.Worksheets(sheet)
            used = ws.UsedRange
            last = used.Row + used.Rows.Count - 1

            # M/N are this script's own columns -- clear them so the pass is
            # idempotent and the thresholds can be retuned without stale rows
            # surviving underneath.
            ws.Range(ws.Cells(1, SRC_COL), ws.Cells(last, CHK_COL)).ClearContents()

            ws.Cells(1, SRC_COL).Value = "Source"
            ws.Cells(1, CHK_COL).Value = "Check"
            n_rows = n_const = n_chk = 0

            for r in range(2, last + 1):
                lab = ws.Cells(r, 2).Value
                if not isinstance(lab, str) or not lab.strip():
                    continue
                first = str(ws.Cells(r, 3).Formula)
                if first.strip() in ("", "None"):
                    continue

                src = classify(first)
                if not src:
                    continue
                if HEADER.match(lab.strip()) and src.startswith("CONSTANT"):
                    src = "block header"          # a title, not a factor
                ws.Cells(r, SRC_COL).Value = src
                n_rows += 1
                if src.startswith("CONSTANT"):
                    n_const += 1

                if FACTORISH.search(lab) and not SKIP.search(lab):
                    rng = f"{FIRST_ITEM}{r}:{LAST_ITEM}{r}"
                    cnt = (f'SUMPRODUCT(({active_name}<>"{placeholder}")'
                           f'*({rng}=0))')
                    ws.Cells(r, CHK_COL).Formula = (
                        f'=IF({cnt}=0,"ok","ZERO in "&{cnt}&" active item(s)")')
                    n_chk += 1

            print(f"  {sheet:<24} {n_rows:>4} rows annotated, "
                  f"{n_const:>3} CONSTANT, {n_chk:>3} zero-checks")
            totals["rows"] += n_rows
            totals["const"] += n_const
            totals["checks"] += n_chk

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        print("\n  after     " + "  ".join(f"{k.split('_')[-1]}={v}"
                                           for k, v in after.items()))
        if after != baseline:
            sys.exit("ABORT: premiums changed -- NOT saving. "
                     "(R-3 is additive; this should be impossible.)")
        print("  -> premiums unchanged, as they must be")

        # What did the new checks actually find?
        print("\n--- what the Check column flags right now ---")
        for sheet in SHEETS:
            ws = wb.Worksheets(sheet)
            used = ws.UsedRange
            last = used.Row + used.Rows.Count - 1
            hits = []
            for r in range(2, last + 1):
                v = ws.Cells(r, CHK_COL).Value
                s = ws.Cells(r, SRC_COL).Value
                if isinstance(v, str) and v.startswith("ZERO"):
                    hits.append((r, ws.Cells(r, 2).Value, v))
                elif isinstance(s, str) and s.startswith("CONSTANT"):
                    hits.append((r, ws.Cells(r, 2).Value, s))
            print(f"  {sheet}: {len(hits)}")
            for r, lab, v in hits[:8]:
                print(f"      row {r:>4} {str(lab)[:38]:<38} {v}")

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        print(f"\n  saved. {totals['rows']} rows annotated, "
              f"{totals['const']} constants flagged, "
              f"{totals['checks']} live zero-checks.")
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
