#!/usr/bin/env python3
"""The test console's data layer, RC-1 (docs/TC-PLAN.md TC-06..TC-13). No ISO calls.

  A  status vocabulary (TC-08)            E  mismatch tolerances and classification (TC-11)
  B  path configuration (TC-09)           F  call ledger: lanes, cap, override, Eastern day (TC-12)
  C  reference store and staleness (TC-06, TC-07)
  D  path signatures on real ratings (TC-10)
  G  roll-up: one test per §3 rule, n/a, sign-off, still-to-test order (TC-13)

    python tests/verify_console_rc1.py [--no-store]     # --no-store skips the 1-2 minute store rebuild
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(encoding="utf-8")

from console import ledger, mismatch, paths, rollup, signature, status, store
from console.rollup import Evidence

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. status vocabulary")
    check("A1 the five spec states plus n/a, fixed keys", [s.key for s in status.ALL] ==
          ["verified", "internal", "mismatch", "stale", "untested", "na"])
    check("A2 glyphs and colours unique", len({s.glyph for s in status.ALL}) == 6 and len({s.colour for s in status.ALL}) == 6)
    check("A3 Passed is the matrix label of verified", status.get("verified").matrix == "Passed")


def part_b():
    print("B. path configuration")
    check("B1 both lines", sorted(paths.lines()) == ["CP", "GL"])
    check("B2 CP: 6 coverages, 17 paths", len(paths.coverages("CP")) == 6 and len(paths.paths("CP")) == 17)
    check("B3 GL: 5 coverages; size of risk replaces ILF interpolated (D8)",
          len(paths.coverages("GL")) == 5 and "gl.po.sor" in paths.paths("GL")
          and not any("interp" in p for p in paths.paths("GL")))
    check("B4 GL Prod/CO area and units left out (D13)",
          "gl.pco.basis.area" not in paths.paths("GL") and "gl.pco.basis.units" not in paths.paths("GL"))
    check("B5 n/a where the state files none: NY BCEG, GA size of risk (D5)",
          not paths.applies("CP", "NY", "cp.bldg.bceg")[0] and not paths.applies("GL", "GA", "gl.po.sor")[0])
    check("B6 applies where filed: OH BCEG, NJ size of risk",
          paths.applies("CP", "OH", "cp.bldg.bceg")[0] and paths.applies("GL", "NJ", "gl.po.sor")[0])
    check("B7 a path may count toward two coverages (Cov C increased -> Cov C and Prem/Ops)",
          set(paths.paths("GL")["gl.covc.increased"]["coverages"]) == {"Cov C · Med pay", "Prem/Ops"})


def part_c(rebuild: bool):
    print("C. reference store and staleness")
    idx = store.build() if rebuild else store.load()
    refs = idx["references"]
    fx = [e for e in refs if "fixture" in e.get("note", "")]
    check("C1 the 293 ISO fixtures are in: 207 distinct requests (fixtures repeat policies)", len(fx) == 207, len(fx))
    check("C2 one entry per request hash", len({e["hash"] for e in refs}) == len(refs))
    rated = [e for e in refs if e["outcome"] == "rated"]
    check("C3 thousands of rated CP answers indexed", len(rated) > 2000, len(rated))
    check("C4 GL premium-level rows from the run store", len(idx["gl_premium_rows"]) > 500, len(idx["gl_premium_rows"]))
    il = [e for e in refs if e["state"] == "IL" and e["date"] == "2026-11-01" and e["outcome"] == "rated"]
    check("C5 IL 2026-11-01 answers are fresh on the October package", il and all(e["freshness"] == "fresh" for e in il),
          [(e["iso_package"], e["freshness"]) for e in il[:2]])
    fake = dict(il[0]) if il else {"line": "CP", "state": "IL", "date": "2026-11-01"}
    fake["iso_package"] = "CF_IL_20260701_V02"
    check("C6 an answer on a package no longer in force is stale", store.staleness(fake)[0] == "stale",
          store.staleness(fake))
    p = json.loads((ROOT / "results" / "cf-raas" / "chunk28_c28-03_V-VT_request.json").read_text(encoding="utf-8"))
    hit = store.lookup(p, idx)
    check("C7 dedupe lookup finds a stored answer by request", hit is not None and hit["outcome"] == "rated")


def part_d():
    print("D. path signatures on real ratings")
    import property_rating as pr
    from gl_engine.rating import Kernel
    cmp = import_module("154_chunk13_rc5_fields_messages")
    data, _ = cmp.rate(pr.sample("OH"))
    s = signature.cp_signature(data)
    check("D1 CP OH sample walks Group I, II, Special, coinsurance and BCEG on all three records",
          {"cp.bldg.g1", "cp.bldg.g2", "cp.bpp.g1", "cp.bi.g1", "cp.col.special", "cp.bldg.coins", "cp.bldg.bceg"} <= s, s)
    data, _ = cmp.rate(pr.sample("NY"))
    check("D2 CP NY walks no BCEG (NY reads none)", "cp.bldg.bceg" not in signature.cp_signature(data))
    k = Kernel(mode="strict-erc")
    bad, n = [], 0
    for st in paths.states("GL"):
        f = ROOT / "Engine_Payloads" / st / "submission.json"
        if not f.exists():
            continue
        n += 1
        for pid in signature.gl_signature(k.rate(str(f))):
            if not paths.applies("GL", st, pid)[0]:
                bad.append((st, pid))
    check(f"D3 GL: across {n} state samples, no path walked where the census says n/a", n > 40 and not bad, bad[:5])
    s = signature.gl_signature(k.rate(str(ROOT / "Engine_Payloads" / "NJ" / "submission.json")))
    check("D4 GL NJ sample walks gross sales, increased limits, filed LCM, state exceptions",
          {"gl.po.basis.sales", "gl.po.ilf.direct", "gl.po.lcm.filed", "gl.po.stateexc"} <= s, s)


def part_e():
    print("E. mismatch categories")
    check("E1 seven categories incl. refusal vs narrowing (D15)", len(mismatch.CATEGORIES) == 7
          and "refusal_vs_narrowing" in mismatch.BY_KEY)
    check("E2 rounding within $1", mismatch.within("rounding", Decimal(101), Decimal(100))
          and not mismatch.within("rounding", Decimal(102), Decimal(100)))
    check("E3 interpolation within 0.5%", mismatch.within("interpolation", Decimal("1004"), Decimal("1000"))
          and not mismatch.within("interpolation", Decimal("1006"), Decimal("1000")))
    check("E4 a true engine defect is never within tolerance", not mismatch.within("true_engine_defect", Decimal(101), Decimal(100)))
    check("E5 unclassified differences are open; equal premiums never are",
          mismatch.is_open("x", 101, 100, latest={}) and not mismatch.is_open("x", 100, 100, latest={}))
    check("E6 a classified in-tolerance difference is not open",
          not mismatch.is_open("x", 101, 100, latest={"x": {"category": "rounding"}}))


def part_f():
    print("F. call ledger")
    with tempfile.TemporaryDirectory() as d:
        os.environ["RAAS_LEDGER_DIR"] = d
        os.environ.pop("RAAS_OVERRIDE", None)
        try:
            check("F1 cap 250 in lanes 150 / 50 / 50 (D2)", ledger.CAP == 250 and ledger.LANES == {"active": 150, "refresh": 50, "adhoc": 50})
            for _ in range(50):
                ledger.record(lane="adhoc", origin="test", outcome="rated")
            check("F2 the 51st ad hoc call is stopped", _raises(lambda: ledger.admit("adhoc")))
            check("F3 another lane still admits", ledger.admit("active") is None)
            check("F4 an override with a reason admits, and is returned for the log", ledger.admit("adhoc", "probe for OI-133") == "probe for OI-133")
            ledger.record(lane="adhoc", origin="test", outcome="refused", status=400, override="probe")
            u = ledger.used()
            check("F5 refusals count (TC-03)", u["adhoc"] == 51 and u["total"] == 51, u)
        finally:
            os.environ.pop("RAAS_LEDGER_DIR", None)
    summer = datetime(2026, 7, 1, 3, 30, tzinfo=timezone.utc)     # 23:30 EDT on June 30
    winter = datetime(2026, 12, 1, 4, 30, tzinfo=timezone.utc)    # 23:30 EST on Nov 30
    check("F6 the day resets at 00:00 Eastern (daylight and standard)",
          ledger.day(summer) == "2026-06-30" and ledger.day(winter) == "2026-11-30")
    src = (ROOT / "scripts" / "raas.py").read_text(encoding="utf-8")
    check("F7 the RaaS client admits and records every call (D21)", "ledger.admit(" in src and "ledger.record(" in src
          and "store.save_answer(" in src)


def _raises(fn) -> bool:
    try:
        fn()
    except ledger.CapReached:
        return True
    return False


def part_g():
    print("G. roll-up")
    E = Evidence
    check("G1 path: nothing walked -> untested", rollup.path_status([]) == "untested")
    check("G2 path: an open mismatch wins", rollup.path_status([E("a", set(), "agree"), E("b", set(), "open-mismatch")]) == "mismatch")
    check("G3 path: a stale reference -> stale", rollup.path_status([E("a", set(), "agree", fresh=False)]) == "stale")
    check("G4 path: a fresh agreeing answer -> verified", rollup.path_status([E("a", set(), "agree")]) == "verified")
    check("G5 path: engine only -> internal", rollup.path_status([E("a", set(), "none")]) == "internal")
    check("G6 path: an INERT scenario counts toward nothing", rollup.path_status([E("a", set(), "agree", inert=True)]) == "untested")
    line, st, cov = "CP", "OH", "Building"
    scope = paths.in_scope(line, st, cov)
    allv = {p: "verified" for p in scope}
    check("G7 cell: every in-scope path verified -> Passed", rollup.cell(line, st, cov, allv).status == "verified")
    check("G8 cell: one mismatch -> mismatch (rule 1)", rollup.cell(line, st, cov, {**allv, scope[0]: "mismatch", scope[1]: "stale"}).status == "mismatch")
    check("G9 cell: one stale, no mismatch -> stale (rule 2)", rollup.cell(line, st, cov, {**allv, scope[0]: "stale"}).status == "stale")
    check("G10 cell: nothing walked -> untested (rule 3)", rollup.cell(line, st, cov, {}).status == "untested")
    check("G11 cell: some verified, some internal -> internal (rule 5)", rollup.cell(line, st, cov, {**allv, scope[0]: "internal"}).status == "internal")
    check("G12 cell: no in-scope path -> n/a (D5; ID has no Property package)", rollup.cell("CP", "ID", "Building", {}).status == "na")
    so = {"by": "Dan", "at": "2026-10-06"}
    check("G13 sign-off kept while Passed (D4)", rollup.cell(line, st, cov, allv, signoff=so).signed_off_by == "Dan")
    check("G14 sign-off cleared when the cell leaves Passed", rollup.cell(line, st, cov, {**allv, scope[0]: "stale"}, signoff=so).signed_off_by is None)
    check("G15 descoped paths leave the denominator and are listed", (lambda c: c.status == "verified" and c.descoped)(
        rollup.cell(line, st, cov, {**allv, scope[0]: "untested"}, descoped={scope[0]: "deferred"})))
    cells = [rollup.cell(line, st, cov, {**allv, scope[0]: "stale"}), rollup.cell(line, "OH", "BPP", {}),
             rollup.cell(line, st, "Extra expense", {p: "mismatch" for p in paths.in_scope(line, st, "Extra expense")}),
             rollup.cell(line, st, cov, allv)]
    order = [c.status for c in rollup.still_to_test(cells)]
    check("G16 still to test: mismatch, stale, then untested; Passed left out (§6, no waves)", order == ["mismatch", "stale", "untested"], order)


def main() -> int:
    rebuild = "--no-store" not in sys.argv
    part_a(); part_b(); part_c(rebuild); part_d(); part_e(); part_f(); part_g()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
