"""R-8 Gate 2 -- does the rater price two contents records the way ISO does?

**Read-only. The workbook is opened ReadOnly and never saved.** The test risk is
loaded into item 5 (column G, an inactive slot) in memory and thrown away.

The case is chunk 4's Oregon two-item case, because ISO has already priced it and
every intermediate is on file (`results/cf-raas/OR_chunk4_Basic_*`):

    class 0951 Offices, Frame (1), PC 3, Portland, Basic, 90% coins, 1,000 ded
    building 100,000; contents 100,000 (+ 50,000 for the two-item case)

ISO is called fresh on both stored requests so the comparison isn't only against a
file from 2026-09-18.

**Prediction, written before the run.** All four PP LOI factors in ISO's rules are
looked up on `OccupTotalLOIToUse` (the sum of PP limits under the occupancy), and
ISO's stored response shows both records at BGI 0.842 / BGII 0.763 / Broad 0.688.
The Phase 2b-ii build copies the LOI chain per record on the record's OWN limit, so:

    1 record   rater == ISO (own limit == occupancy total)       -- control
    2 records  rater != ISO: record 1 takes the 100k factor (0.898), record 2
               the 50k factor, instead of both taking the 150k one (0.842)

    python scripts/cf/110_r8_gate2_multi_record.py [--no-iso]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import raas as raas_mod                                             # noqa: E402

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
IL, SC, CR, POL = "IN - Location", "IN - Schedule", "CALC - Contents Rating", "IN - Policy"
G = 7                               # item 5 / contents record 5
REC2_ROW, REC2_COL = 144, 13        # schedule row of record 11, its Contents column (M)

#: IN - Location row -> value for column G. Mirrors the ISO request field by field.
RISK = {
    13: 97201, 17: "Portland", 20: "Multnomah (including entire city of Portland)",
    22: "3", 23: "4", 24: "Not Applicable", 26: "0951", 27: "0951", 28: "Class",
    30: "Not Applicable", 32: "Offices", 8: "Building", 9: "All Personal Property",
    10: "Building and Personal Property Coverage Form", 43: 100000, 44: 0,
    45: 100000, 46: 0, 47: 0, 50: "Basic", 52: "1,000", 53: "Not Applicable", 54: "1,000",
    55: "No", 57: "No", 60: 1, 62: "Frame", 63: "1-3", 65: "No", 67: "Actual Cash Value",
    68: 0.9, 69: 0.9, 72: "Select", 73: "No", 75: "No", 76: "No", 77: "No",
    79: "No", 80: "No", 81: "No", 82: "No", 83: "No", 85: "No",
    87: "Not Applicable", 90: 1, 92: "Not Applicable",
}
POLICY = {"F3": "No", "F4": "No"}   # no cyber exclusion -- ISO's request carries none

#: Contents rows to report: (label, row)
ROWS = [("BGI LOI", 16), ("BGI final rate", 20), ("BGI premium", 30),
        ("BGII LOI", 44), ("BGII final rate", 48), ("BGII premium", 58)]

#: ISO's per-record values, from the stored responses (re-confirmed live below)
ISO = {
    1: [{"BGI LOI": 0.898, "BGI premium": None}],
    2: [{"BGI LOI": 0.842, "BGII LOI": 0.763, "BGI final rate": 0.209},
        {"BGI LOI": 0.842, "BGII LOI": 0.763, "BGI final rate": 0.209}],
}


def iso_records(resp: dict) -> list[dict]:
    occ = (resp["Body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]
           ["CommercialPropertyStructure"][0]["CommercialPropertyOccupClass"][0])
    out = []
    for rec in occ["CommercialPropertyPersonalProperty"]:
        out.append({
            "BGI LOI": rec.get("BasicGroupILOIFactor"),
            "BGI final rate": rec.get("FinalBasicGroupIRate"),
            "BGII LOI": rec.get("BasicGroupIILOIFactor"),
            "BGII final rate": rec.get("FinalBasicGroupIIRate"),
            "record premium": rec.get("TotalPersonalPropertyCoveragePremium"),
            "OccupTotalLOIToUse": rec.get("OccupTotalLOIToUse"),
        })
    return out


def call_iso(skip: bool) -> dict[int, list[dict]]:
    res = {}
    client = None
    if not skip:
        raas_mod.load_env()
        try:
            client = raas_mod.RaaS()
        except raas_mod.RaaSError as exc:
            print(f"  ISO unavailable ({exc}); using stored responses")
    for n, tag in ((1, "1item"), (2, "2item")):
        req = json.loads((REPO / f"results/cf-raas/OR_chunk4_Basic_{tag}_request.json").read_text())
        stored = json.loads((REPO / f"results/cf-raas/OR_chunk4_Basic_{tag}_response.json").read_text())
        resp, src = stored, "stored 2026-09-18"
        if client is not None:
            try:
                resp, src = client.rate(req), "LIVE"
            except raas_mod.RaaSError as exc:
                print(f"  ISO call failed for {tag}: {exc}; using stored")
        recs = iso_records(resp)
        if src == "LIVE" and recs != iso_records(stored):
            print(f"  NOTE: live ISO answer for {tag} differs from the stored one")
        res[n] = recs
        print(f"  ISO {tag} ({src}): " + " | ".join(
            f"LOI {r['BGI LOI']}/{r['BGII LOI']} rate {r['BGI final rate']} "
            f"prem {r['record premium']}" for r in recs))
    return res


#: CoreScratchpad rows whose per-record copies form the three LOI chains (BGI 131-137,
#: BGII 144-154, Broad/Special 156-166). ISO keys all of them on OccupTotalLOIToUse.
LOI_CHAIN = set(range(131, 138)) | set(range(144, 155)) | set(range(156, 167))


def occupancy_total_fix(cr, sched_row: int, col: int) -> int:
    """In memory only: feed the LOI chains the occupancy's total PP limit instead of
    the record's own. Returns the number of cells rewritten."""
    own = f"'IN - Schedule'!$E${sched_row}"
    occ = (f"SUMIFS('IN - Schedule'!$E$134:$E$173,'IN - Schedule'!$B$134:$B$173,"
           f"'IN - Schedule'!$B${sched_row},'IN - Schedule'!$C$134:$C$173,\"Yes\")")
    n = 0
    for r in range(119, 169):
        lab = str(cr.Cells(r, 1).Value or "")
        if lab.startswith("CS") and int(lab[2:]) in LOI_CHAIN:
            f = str(cr.Cells(r, col).Formula)
            if own in f:
                cr.Cells(r, col).Formula = f.replace(own, occ)
                n += 1
    return n


def rounding_fix(cr, col: int) -> None:
    """In memory only: ISO's order for the BGI adjusted rate -- round rate x
    coinsurance first, then apply LOI (ISO: r3(r3(0.263 x 0.95) x 0.898) = 0.225;
    the rater's single ROUND gives 0.224)."""
    L = cr.Cells(1, col).Address.split("$")[1]
    cr.Cells(17, col).Formula = f"=ROUND(ROUND({L}14*{L}15,3)*{L}16,3)"


def rater(two: bool, fix: bool = False, rnd: bool = False) -> list[dict]:
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing the live rater.")
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n not in {"", "0"}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        il, sc, cr, pol = (wb.Worksheets(s) for s in (IL, SC, CR, POL))
        # Write text AS text. COM lets Excel coerce: "0951" became 951, "1,000"
        # became 1000 (deductible factor 0), and ParentOcc "5 - 1 - 1" was parsed
        # as a DATE -- so the first run's failures were the harness, not the rater.
        for row, v in RISK.items():
            orig = il.Cells(row, 3).Value
            il.Cells(row, G).Value = f"'{v}" if isinstance(orig, str) else v
        for a, v in POLICY.items():
            pol.Range(a).Value = v
        if two:
            occ = sc.Cells(95, 1)            # occupancy of item 5
            app.CalculateFull()
            vals = {1: f"{occ.Value} - 2", 2: occ.Value, 3: "Yes",
                    4: "All Personal Property", 5: 50000, 6: 0, 7: 0.9,
                    8: "Actual Cash Value", 9: "No", 10: "No", 11: "No"}
            for c, v in vals.items():
                sc.Cells(REC2_ROW, c).Value = f"'{v}" if isinstance(v, str) else v
        if fix:
            n = occupancy_total_fix(cr, 138, G) + (occupancy_total_fix(cr, REC2_ROW, REC2_COL) if two else 0)
            print(f"  [with-fix] {n} LOI-chain cells now read the occupancy total")
        if rnd:
            for c in [G] + ([REC2_COL] if two else []):
                rounding_fix(cr, c)
            print("  [round-fix] Contents row 17 uses ISO's rounding order")
        app.CalculateFull()
        cols = [G] + ([REC2_COL] if two else [])
        out = []
        for c in cols:
            d = {lab: (float(v) if v is not None and not isinstance(v, str) else v)
                 for lab, r in ROWS for v in [cr.Cells(r, c).Value]}
            d["BGII chain"] = [cr.Cells(r, c).Value for r in (42, 45, 46, 47, 48, 51, 58)] +                 [wb.Worksheets("CALC - CoreScratchpad").Cells(r, 7).Value for r in (87, 88, 89, 90, 91, 92, 93)] +                 [wb.Worksheets(IL).Cells(r, G).Value for r in (19, 64, 97)]
            d["ParentCol"] = cr.Cells(116, c).Value
            if isinstance(d["ParentCol"], float) and two and c == REC2_COL and d["ParentCol"] != 5:
                print(f"  WARNING: record 2 ParentCol = {d['ParentCol']}, expected 5")
            d["TOTAL LIMIT"] = wb.Worksheets("CALC - CoreScratchpad").Cells(138, 7).Value
            out.append(d)
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        reap_orphans()
    return out


def reap_orphans() -> None:
    """Quit often leaves the process behind. Kill only title-less EXCEL, by PID."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process EXCEL -ErrorAction SilentlyContinue | "
         "ForEach-Object { \"$($_.Id)`t$($_.MainWindowTitle)\" }"],
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        pid, _, title = line.partition("	")
        if pid.strip() and not title.strip():
            subprocess.run(["taskkill", "/PID", pid.strip(), "/F"], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-iso", action="store_true")
    ap.add_argument("--with-fix", action="store_true",
                    help="in memory only: LOI chains read the occupancy total")
    ap.add_argument("--round-fix", action="store_true",
                    help="in memory only: BGI adjusted rate rounded in ISO's order")
    a = ap.parse_args()
    iso = call_iso(a.no_iso)
    ok = True
    for n in (1, 2):
        print(f"\n== {n} record(s)")
        rt = rater(n == 2, a.with_fix, a.round_fix)
        for i, (r, s) in enumerate(zip(rt, iso[n]), 1):
            prem = (r["BGI premium"] or 0) + (r["BGII premium"] or 0)
            print(f"  record {i}  rater: ParentCol {r['ParentCol']}  TOTAL LIMIT "
                  f"{r['TOTAL LIMIT']}  LOI {r['BGI LOI']}/{r['BGII LOI']}  rate "
                  f"{r['BGI final rate']}  BGI {r['BGI premium']} + BGII "
                  f"{r['BGII premium']} = {prem}")
            print(f"            BGII chain (34,35,36,37,38,39,42,45 | CS59,55,19 | IL19,64,97): {r['BGII chain']}")
            print(f"            ISO:   LOI {s['BGI LOI']}/{s['BGII LOI']}  rate "
                  f"{s['BGI final rate']}  record premium {s['record premium']}")
            loi_ok = r["BGI LOI"] == s["BGI LOI"] and r["BGII LOI"] == s["BGII LOI"]
            diff = prem - s["record premium"]
            premium_note = "match" if diff == 0 else f"off by {diff:+}"
            match = loi_ok and prem == s["record premium"]
            print(f"            LOI {'match' if loi_ok else 'MISMATCH'}; premium "
                  f"{premium_note}")
            ok &= match
    print("\nGATE 2:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
