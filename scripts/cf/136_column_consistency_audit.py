"""Standing check (W-7): every per-record column on the calc sheets must hold column C's formula.

The calc sheets price record k in column C+k-1 (40 records, C..AP). A formula filled across
correctly is IDENTICAL in R1C1 notation in every column, so any column whose `FormulaR1C1`
differs from column C's has drifted: a missing state prefix, a table shifted one column, a
hand edit. Rows 9-12 of CoreScratchpad had exactly this and were standardised in R-8 Phase 4a;
rows 57 / 126 / 216 were still drifted (backlog W-7).

Read-only (opens the workbook ReadOnly, never saves). Excel must be closed.

    python scripts/cf/136_column_consistency_audit.py            # report
    python scripts/cf/136_column_consistency_audit.py --strict   # exit 1 on any drift

A row may be listed in `ALLOWED` with the reason it legitimately differs by column. A drifted row that no
formula reads is reported DEAD (not a pricing defect) and does not fail --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r8_contents_translate import colname                          # noqa: E402

p4a = import_module("112_r8_phase4a_building")

SHEETS = ("CALC - CoreScratchpad", "CALC - Bldg Rating", "CALC - Contents Rating",
          "CALC - BI Rating", "CALC - Special Class")
FIRST, LAST = 3, 42                                                 # C .. AP
#: (sheet, row) -> why its columns legitimately differ
ALLOWED: dict[tuple[str, int], str] = {
    ("CALC - CoreScratchpad", 61): "DEAD: read only by row 62, which nothing reads (checked 2026-09-23)",
}


_SCH_CELL = re.compile(r"('IN - Schedule'!)R(\d+)C(\d+)(?![:\d])(?<!:)")


def stepped(base: str, i: int) -> str:
    """Column C's formula as record k = C+i should hold it: every single-cell absolute
    reference into `IN - Schedule` steps down i rows (record k reads Schedule row r0+k-1).
    Ranges ($C$5:$C$44) and every other reference stay as they are."""
    def sub(m):
        start = m.start()
        if start > 0 and base[start - 1] == ":":
            return m.group(0)
        return f"{m.group(1)}R{int(m.group(2)) + i}C{m.group(3)}"
    return _SCH_CELL.sub(sub, base)


_REF = re.compile(r"(?:'([^']+)'!|([A-Za-z0-9_]+)!)?\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")


def read_rows(wb):
    """{sheet: set(rows)} that some formula (outside that row itself) references.
    A drifted row nobody reads is DEAD, not a pricing defect; the scan keeps that verdict
    honest if a dead row is wired up later."""
    read = {n: set() for n in SHEETS}
    for ws in wb.Worksheets:
        if ws.Name.startswith("TBL"):
            continue
        ur = ws.UsedRange
        vals, top, wname = ur.Formula, ur.Row, ws.Name          # one COM call each, not per cell
        if not isinstance(vals, tuple):
            vals = ((vals,),)
        for i, row in enumerate(vals):
            for f in row:
                if not (isinstance(f, str) and f.startswith("=")):
                    continue
                for m in _REF.finditer(f):
                    sheet = m.group(1) or m.group(2) or wname
                    if sheet in read:
                        a, b = int(m.group(4)), int(m.group(6) or m.group(4))
                        own = top + i if sheet == wname else None
                        read[sheet].update(x for x in range(a, min(b, a + 400) + 1) if x != own)
    return read


def audit(wb):
    drift = []
    readers = read_rows(wb)
    for name in SHEETS:
        ws = wb.Worksheets(name)
        rows = ws.UsedRange.Row + ws.UsedRange.Rows.Count - 1
        block = ws.Range(ws.Cells(1, FIRST), ws.Cells(rows, LAST)).FormulaR1C1
        labels = ws.Range(ws.Cells(1, 2), ws.Cells(rows, 2)).Value
        for r, cells in enumerate(block, start=1):
            base = cells[0]
            if not (isinstance(base, str) and base.startswith("=")):
                continue                                           # constants / headers
            if str(labels[r - 1][0] or "").strip().upper().startswith("TOTAL"):
                continue                                           # SUM across records in column C only
            bad = [colname(FIRST + i) for i, f in enumerate(cells[1:], start=1)
                   if f != base and f != stepped(base, i)]
            if bad:
                why = ALLOWED.get((name, r)) or (None if r in readers[name] else "DEAD: no formula reads this row")
                drift.append((name, r, labels[r - 1][0], bad, why))
    return drift


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible, app.DisplayAlerts, app.EnableEvents = False, False, False
    wb = None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        drift = audit(wb)
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    real = [d for d in drift if not d[4]]
    for name, r, label, bad, why in drift:
        cols = f"{bad[0]}..{bad[-1]} ({len(bad)})" if len(bad) > 3 else ", ".join(bad)
        print(f"  {('DEAD    ' if why and why.startswith('DEAD') else 'ALLOWED ') if why else 'DRIFT   '}{name}!{r:<4} {str(label)[:40]:40} {cols}"
              + (f"   -- {why}" if why else ""))
    print(f"\n{len(real)} drifted row(s) that something reads; {len(drift) - len(real)} dead or allowed; "
          f"{len(SHEETS)} sheets checked")
    return 1 if (a.strict and real) else 0


if __name__ == "__main__":
    raise SystemExit(main())
