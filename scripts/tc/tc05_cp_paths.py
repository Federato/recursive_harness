#!/usr/bin/env python3
"""TC-05 (Property half): the rating-path catalog per state, the Readiness Matrix's denominator. No ISO calls.

Each path is a way a Commercial Property policy can be priced, named by a stable id, grouped into the design spec's six
coverages (`readiness-matrix-integration.md` §4; a path may belong to more than one). For every state with a Property
package in force at 2026-09-17, a path **applies** when the tables it prices on resolve with rows for that state (the
**The form paths are decided by rating, not by table names**: the app's sample (`scripts/property_rating.py`) is rated
in each state three times, on the Special, Broad and Basic cause-of-loss forms, and a path applies when the engine
prices it there (table names mislead: CA rates Group I on district tables, AK and FL on their own). The paths that are
not a form (BCEG, extra expense, wind/hail %) apply when their table resolves with rows for the state (the state's own,
or countrywide's where the engine fills an empty state table), and are **n/a** (D5) otherwise, or where the state's
own rules never read them (NY and DC read no BCEG, chunk 27).

    python scripts/tc/tc05_cp_paths.py          # writes results/tc/tc05_cp_paths.json and prints the census

The path list is the first version of TC-09's coverage -> path configuration.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import EngineError

DATE = "20260917"
OUT = ROOT / "results" / "tc" / "tc05_cp_paths.json"

#: id -> (label, coverages, tables it prices on (all must resolve with rows), note)
PATHS = {
    "cp.bldg.g1":        ("Building · Basic Group I (class rated)", ["Building"], ["BasicGroupIRate"], ""),
    "cp.bldg.g2":        ("Building · Basic Group II", ["Building"], ["BasicGroupIIRate"], "symbol + territory (chunk 2)"),
    "cp.bldg.specific":  ("Building · Specific / Tentative rate", ["Building"], [], "a submitted rate (chunk 26): every state"),
    "cp.bldg.bceg":      ("Building · BCEG", ["Building"], ["BCEGFactor"], "NY and DC read no BCEG (chunk 27)"),
    "cp.bldg.coins":     ("Building · coinsurance", ["Building"], ["CoinsuranceFactor"], ""),
    "cp.bpp.g1":         ("BPP · Basic Group I", ["BPP"], ["BasicGroupIRate"], "contents ride the building's rate (chunk 4)"),
    "cp.bpp.g2":         ("BPP · Basic Group II", ["BPP"], ["BasicGroupIIRate"], ""),
    "cp.bpp.specific":   ("BPP · Specific rate", ["BPP"], [], "every state"),
    "cp.bpp.coins":      ("BPP · coinsurance", ["BPP"], ["CoinsuranceFactor"], ""),
    "cp.bi.g1":          ("Business income · Basic Group I", ["Business income"], ["BasicGroupIRate"], ""),
    "cp.bi.g2":          ("Business income · Basic Group II", ["Business income"], ["BasicGroupIIRate"], ""),
    "cp.bi.coins":       ("Business income · coinsurance (incl. other than 80%)", ["Business income"], ["CoinsuranceFactor"], ""),
    "cp.ee":             ("Extra expense", ["Extra expense"], ["ExtraExpenseFactor"], ""),
    "cp.col.basic":      ("Causes of loss · Basic (Group I + II)", ["Causes of loss"], ["BasicGroupIRate", "BasicGroupIIRate"], ""),
    "cp.col.broad":      ("Causes of loss · Broad", ["Causes of loss"], ["BroadFormBaseRate"], ""),
    "cp.col.special":    ("Causes of loss · Special", ["Causes of loss"], ["SpecialBuildingRate"], "FL / PR read their own (chunk 3)"),
    "cp.whded.pct":      ("Wind/hail % deductible", ["Wind/hail ded."], ["WindstormOrHailDeductibleFactor"], "state-applicable only"),
}
#: paths a state's own rules never take, whatever its tables (evidence from the chunks)
NOT_READ = {("NY", "cp.bldg.bceg"): "NY reads no BCEG (chunk 27)", ("DC", "cp.bldg.bceg"): "DC reads no BCEG (chunk 27)"}


def has_rows(book, table: str) -> bool:
    try:
        return bool(book.table(table).rows)
    except EngineError:
        return False


def pct_wind(book) -> bool:
    """A wind/hail percentage deductible is filed: the factor table has a row keyed on a % value."""
    try:
        t = book.table("WindstormOrHailDeductibleFactor")
    except EngineError:
        return False
    return any(isinstance(c, str) and c.strip().endswith("%") for r in t.rows for c in r)


#: form paths -> (record path fragment, coverage record fragment, the cause-of-loss run that shows it)
FORM_PATHS = {
    "cp.bldg.g1": ("StructureBuilding", "BasicGroupICoverage", "Special"),
    "cp.bldg.g2": ("StructureBuilding", "BasicGroupIICoverage", "Special"),
    "cp.bpp.g1": ("PersonalPropertyPrsnlProp", "BasicGroupICoverage", "Special"),
    "cp.bpp.g2": ("PersonalPropertyPrsnlProp", "BasicGroupIICoverage", "Special"),
    "cp.bi.g1": ("BusinessIncome", "BasicGroupICoverage", "Special"),
    "cp.bi.g2": ("BusinessIncome", "BasicGroupIICoverage", "Special"),
    "cp.col.special": ("", "SpecialCoverage", "Special"),
    "cp.col.broad": ("", "BroadCoverage", "Broad"),
    "cp.col.basic": ("", "BasicGroupICoverage", "Basic"),
}


def priced(st: str) -> dict:
    """cause of loss -> (premium path -> value) for the app's sample in `st`, or the refusal text."""
    import copy
    from importlib import import_module
    import property_rating as pr
    sys.path.insert(0, str(ROOT / "scripts" / "cf"))
    cmp = import_module("154_chunk13_rc5_fields_messages")
    rep = import_module("157_chunk14_c14-02_total_replay")
    out = {}
    for col in ("Special", "Broad", "Basic"):
        q = pr.sample(st)
        def walk(o):
            if isinstance(o, dict):
                if "CauseOfLoss" in o:
                    o["CauseOfLoss"] = col
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(q["body"])
        try:
            data, _ = cmp.rate(q)
            out[col] = rep.our_prem(data)
        except Exception as exc:                          # noqa: BLE001 -- a refusal is the answer
            out[col] = "refused: " + str(exc)[:100]
    return out


def main() -> int:
    states = sorted(j for j in CFEditionResolver().jurisdictions if j != "CW")
    out = {"date": DATE, "paths": {k: {"label": v[0], "coverages": v[1], "tables": v[2], "note": v[3]}
                                   for k, v in PATHS.items()}, "states": {}}
    for st in states:
        try:
            book = book_for(st, DATE)
        except EngineError as exc:
            out["states"][st] = {"error": str(exc)[:120]}
            continue
        row = {}
        runs = priced(st) if st != "PR" else {}
        for pid, (_, _, tables, _) in PATHS.items():
            if pid in FORM_PATHS:
                rec, cov, col = FORM_PATHS[pid]
                got = runs.get(col)
                if got is None:
                    row[pid] = "n/a: the app's sample does not rate in PR"
                elif isinstance(got, str):
                    row[pid] = f"n/a: the {col} run is refused ({got[9:80]})"
                else:
                    vals = [v for k, v in got.items() if k.endswith("/Premium") and cov + "[" in k
                            and (not rec or rec in k) and v not in (None, "")]
                    row[pid] = "applies" if any(float(v) > 0 for v in vals) else f"n/a: priced $0 on the {col} form"
                continue
            if (st, pid) in NOT_READ:
                row[pid] = "n/a: " + NOT_READ[(st, pid)]
            elif pid == "cp.whded.pct":
                row[pid] = "applies" if pct_wind(book) else "n/a: no % wind/hail deductible filed"
            else:
                missing = [t for t in tables if not has_rows(book, t)]
                row[pid] = "applies" if not missing else "n/a: " + ", ".join(missing) + " not filed"
        out["states"][st] = {"package": book.resolution.state.pkg_id, "paths": row}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    ok = {s: v for s, v in out["states"].items() if "paths" in v}
    print(f"{len(ok)} states with a Property package at {DATE}; {len(PATHS)} paths in 6 coverages")
    for pid in PATHS:
        na = [s for s, v in ok.items() if v["paths"][pid] != "applies"]
        print(f"  {pid:18s} applies in {len(ok) - len(na):2d}" + (f"; n/a: {', '.join(na)}" if na else ""))
    for s, v in out["states"].items():
        if "error" in v:
            print(f"  {s}: {v['error']}")
    cov = Counter(c for v in PATHS.values() for c in v[1])
    print("paths per coverage:", dict(cov))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
