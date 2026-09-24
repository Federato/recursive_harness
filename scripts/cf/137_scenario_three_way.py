"""Scenario runner (RC-4): the three-way comparison on a WHAT-IF version of the rater.

Opens `CFRater1.02.xlsb` READ-ONLY in a hidden Excel, applies a scenario's cell edits in
memory, recalculates, and hands the recalculated values to `119_payload_three_way.py` in
place of its pyxlsb reader. Everything else -- payload builder, live ISO, cf_engine, the
comparison -- is 119's own code, unchanged. The workbook is never saved.

A scenario is a JSON file:

    {"name": "oh_building",
     "edits": [{"sheet": "IN - Schedule", "cell": "C5", "value": "OH"}, ...]}

    python scripts/cf/137_scenario_three_way.py scenarios/oh_building.json [--state OH]
    python scripts/cf/137_scenario_three_way.py --none            # no edits: must equal 119

Any extra arguments are passed to 119 (e.g. --state, --no-engine). Excel must be closed.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
p4a = import_module("112_r8_phase4a_building")
tw = import_module("119_payload_three_way")

WANT = [tw.SCH, "IN - Policy", "Defaults", "TBL - Cyber", "TBL - BGIISpecific"] + sorted({s for s, _ in tw.RATER.values()})


def _plain(v):
    """COM values the way pyxlsb reports them: dates as ISO text, everything else as is."""
    if hasattr(v, "year") and hasattr(v, "month"):
        return dt.date(v.year, v.month, v.day).isoformat()
    return v


def load(edits: list[dict]) -> dict:
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre} -- close it first")
    if str(p4a.TARGET).lower().endswith("cfrater1.01.xlsb"):
        sys.exit("ABORT: refusing the live rater.")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible, app.DisplayAlerts, app.EnableEvents = False, False, False
    wb = None
    sheets: dict = {}
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        for e in edits:
            rng = wb.Worksheets(e["sheet"]).Range(e["cell"])
            if "r1c1" in e:                                   # a formula written relative to its cell
                rng.FormulaR1C1 = e["r1c1"]
                continue
            v = e["value"]
            if isinstance(v, str) and v.startswith("="):
                rng.Formula = v
            else:
                rng.Value = ("'" + v) if isinstance(v, str) and e.get("text") else v
        app.CalculateFull()
        for name in WANT:
            ur = wb.Worksheets(name).UsedRange
            vals, r0, c0 = ur.Value, ur.Row, ur.Column
            if not isinstance(vals, tuple):
                vals = ((vals,),)
            sheets[name] = {(r0 + i, c0 + j): _plain(v) for i, row in enumerate(vals)
                            for j, v in enumerate(row) if v is not None}
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    return sheets


def main() -> int:
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--none":
        scen, rest = {"name": "baseline", "edits": []}, args[1:]
    else:
        scen, rest = json.loads(Path(args[0]).read_text(encoding="utf-8")), args[1:]
    print(f"Scenario '{scen['name']}': {len(scen['edits'])} in-memory edit(s), workbook never saved")
    sheets = load(scen["edits"])
    tw.read_workbook = lambda: sheets                     # 119 reads the what-if, not the file
    tw.OUT_ROOT = tw.OUT_ROOT.parent / "cf-scenarios" / scen["name"]
    sys.argv = [sys.argv[0]] + rest
    return tw.main()


if __name__ == "__main__":
    raise SystemExit(main())
