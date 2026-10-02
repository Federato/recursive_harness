#!/usr/bin/env python3
"""Chunk 27 RC-3 (C27-06..C27-09): chunk 8's point 8 and the per-state gaps chunk 2 logged. Live ISO.

Re-run on 2026-10-02's engine before anything was predicted: chunk 8's sweep (62_) still gives CA no Legal Liability
premium but now gives FL $59 (FL resolves CF_FL_20241201_V02 over CW 2023 V04; on 2026-09-18 it resolved an older
package); chunk 2's sweep (11_) now rates MT ($72 as predicted) and skips DC, IL and NY for "no BCEGFactor row".
Every skip traced to the state's own rule:

  C27-06  CA's base rate is a District I / District II table (`SetBasicGroupIBaseRate`, keyed by `../../District`); the
          sweep sent no District, so the base rate (and Legal Liability) was 0. Legal Liability itself is the countrywide
          fork: r0(r3(r3(COLadj x 0.25) x 1.0) x Limit / 100), the deductible never applied.
          L-CA1 District I   predicted $57 (0.227 x 0.25); competing: the class premium $243, and $0
          L-CA2 District II  predicted $68 (0.273 x 0.25); competing: District ignored, $57
          L-FL  FL           predicted $59 (0.234 x 0.25); competing: the class premium $250, and $0 (chunk 8)
  C27-07  TX: `SetBasicGroupIICauseOfLossAdjustment` = r3(r3(BasicGroupIIRate x WindstormOrHailExclFactor) x StdPropPol);
          the factor is 1.0 without the exclusion record and a flat 0.1 with it (`WindstormOrHailExclFactorTX`, one row,
          no symbol). The countrywide shape instead REBUILDS from LowestBasicGroupIIRate x a symbol factor (B: 0.315).
          W-TX0 no exclusion, W-TX1 the exclusion scheduled: each predicted below; competing: the countrywide rebuild
  C27-08  DC and NY override `SetBCEGFactor` with an EMPTY rule and file a header-only `BCEGFactor`; neither state's Group
          II rate reads BCEG at all. IL maps territory "Cook County" to the table's "Cook" rows and keys any other
          territory ("Balance of State") directly. The sweep matched the table's territory literally: its skip, not a gap.
          B-DC4 / B-DC9, B-NY4 / B-NY9: grade 4 and grade 9 predicted EQUAL (no BCEG in the formula); competing: $0
          B-ILc / B-ILb: Cook County and Balance of State, each with its own row's factor; competing: factor 1.0, or $0
  C27-09  MT's Group II symbol now resolves (the sweep rates it); M-MT sends it to ISO. NY empties `SetBasicGroupIISymbol`
          and copies a SUBMITTED `BasicGroupIISymbol` (`SetBGIISymbolToUse`): the NY cases send "B"; B-NY0 sends none
          (ours: base rate 0, Group II $0; ISO may refuse instead)

    python scripts/cf/240_chunk27_rc3.py [--live] [--cases L-CA1,W-TX1]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

r2 = import_module("239_chunk27_rc2")                    # TAGGED, iso_tagged, rate_retry
c23, t2, rep, gc, P, TAGGED, lvl = r2.c23, r2.t2, r2.rep, r2.gc, r2.P, r2.TAGGED, r2.lvl
g2, g8 = r2.g2, r2.g8
s11 = import_module("11_chunk2_enumerate_states")
from cf_engine.resolve import book_for

D = Decimal
FAIL = []
ASOF = "20260917"
LIMIT = 100000


def r3(x):
    return D(x).quantize(D("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return D(x).quantize(D("1"), rounding=ROUND_HALF_UP)


def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)


def struct_fields(data):
    st = next(n for n in walk(data) if n.tag == P + "Structure")
    return {c.tag: c.text for c in st.children if not c.children}


def bldg_prem(data, form):
    n = next((n for n in walk(data) if n.tag == "Premium" and n.parent.tag == f"{P}StructureBuilding{form}Coverage"), None)
    return None if n is None or n.text is None else D(str(n.text))


def loc_of(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]


# ---------------------------------------------------------------- C27-06 Legal Liability

def ll(j, district=None, legal=True):
    def b():
        sub = g8.building("Basic")
        loc = loc_of(sub)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"           # 62_'s pin: the one input that cannot cross state lines
        if district:
            loc["District"] = district
        if j == "FL":                                        # FL converts its own Group II territories; "Entire State" is refused
            loc["BasicGroupIIRatingTerr"] = "Inland"
        if not legal:
            st = g8.zeros2.structure(sub)
            st["CovType"] = "Building"
            st.pop(f"{g8.LL_FORM}Table", None)
        return sub
    return b


def district_rate(district):
    pk = book_for("CA", ASOF).state.package.content
    tab = "BasicGroupIDistrictIRate" if district == "District I" else "BasicGroupIDistrictIIRate"
    import csv
    with open(Path(pk) / "Rate Tables" / f"{tab}.RateTable.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["ClassCode"] == "0951" and row["ConstructionCode"] == "1" and row["CovType"] == "Building":
                return D(row["Rate"])


def expect_ll(district=None):
    def f(data, j):
        s = struct_fields(data)
        bad = []
        if district and not r2.c23.m.same(s.get("BasicGroupIBaseRate"), district_rate(district)):
            bad.append(f"CA {district} base rate {s.get('BasicGroupIBaseRate')} vs table {district_rate(district)}")
        col = D(str(s["BasicGroupICauseOfLossAdjustment"]))
        want = r0(r3(r3(col * D("0.25")) * 1) * LIMIT / 100)
        return {"BasicGroupI": want}, bad, f"COLadj {col} x 0.25 -> {r3(col * D('0.25'))}"
    return f


def expect_class(data, j):
    s = struct_fields(data)
    return {"BasicGroupI": r0(D(str(s["FinalBasicGroupIRate"])) * LIMIT / 100)}, [], f"final {s['FinalBasicGroupIRate']}"


# ---------------------------------------------------------------- C27-07..09 Group II

def bgii_tree(j, terr, grade, excl=False, symbol=None):
    def b():
        sub = g2.submission()
        loc = loc_of(sub)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc["BasicGroupIIRatingTerr"] = terr
        st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
        st.update({"BCEG": grade, "RatingTypeBasicGroupII": "Class", "Deductible": s11.DEDUCTIBLE, "Coinsurance": s11.COINS})
        if symbol:
            st["BasicGroupIISymbol"] = symbol
            # NY looks up CompletedBasicGroupIISymbol on every building unless it is "Not Applicable": blank is refused at
            # ISO (chunk 24 C24-18, OI-103)
            st["CompletedBasicGroupIISymbol"] = "Not Applicable"
        if excl:
            st["CommercialPropertyWindstormOrHailExclusionTable"] = {"CommercialPropertyWindstormOrHailExclusion": [{}]}
        return sub
    return b


def gii_base(j, terr):
    book = book_for(j, ASOF)
    sym = s11.chunk0._exact(book.table("BasicGroupIIConstructionSymbol"), [j, s11.CONSTRUCTION, s11.STORIES], "Symbol") \
        or s11.chunk0._exact(book.table("BasicGroupIIConstructionSymbol"), ["CW", s11.CONSTRUCTION, s11.STORIES], "Symbol")
    t = book.table("BasicGroupIIRate")
    row = next(r for r in t.rows if str(r[t.col("BasicGroupIISymbol")]) == str(sym) and str(r[t.col("CovType")]) == "Bldg"
               and str(r[t.col("BasicGroupIIRatingTerr")]) == terr)
    return book, sym, D(str(row[t.col("Rate")]))


def bceg_row(j, key, grade):
    t = book_for(j, ASOF).table("BCEGFactor")
    return next((D(str(r[t.col("Factor")])) for r in t.rows
                 if str(r[t.col("BasicGroupIIRatingTerr")]) == key and str(r[t.col("BldgCodeEffectivenessGrade2")]) == grade), None)


def expect_gii(j, terr, grade, bceg_key=None, excl_factor=None):
    """11_'s fold (base x LCM x numeric x roof x roof x BCEG, 3dp each step), then coinsurance, LOI, deductible; the BCEG
    factor is the row at bceg_key (None: the state reads no BCEG); TX's cause-of-loss step multiplies excl_factor."""
    def f(data, j_):
        book, sym, base = gii_base(j, terr)
        bceg = D(1) if bceg_key is None else bceg_row(j, bceg_key, grade)
        rate = base
        for x in (1, 1, 1, 1, bceg):
            rate = r3(rate * D(x))
        col = r3(r3(rate * excl_factor) * 1) if excl_factor is not None else r3(rate * 1)
        inp = {"symbol": sym, "terr": terr, "base": base, "grade": grade, "bceg": bceg}
        _, parts = s11.predict(book, j, inp)
        adjusted = r3(r3(col * D(str(parts["coins"]))) * D(str(parts["loi"])))
        final = r3(r3(adjusted * 1) * D(str(parts["ded"])))
        return ({"BasicGroupII": r0(final * LIMIT / 100)}, [],
                f"symbol {sym} base {base} BCEG {bceg} -> COLadj {col}, coins {parts['coins']} LOI {parts['loi']} "
                f"ded {parts['ded']} -> final {final}")
    return f


def cw_rebuild(j, terr):
    """the competing reading for TX: the countrywide shape (LowestBasicGroupIIRate x the symbol's factor)."""
    book, sym, _ = gii_base(j, terr)
    lo = s11.chunk0._exact(book.table("LowestBasicGroupIIRate"), ["CW", str(sym)], "Rate") if not book.table("LowestBasicGroupIIRate").is_empty else None
    t = book.table("WindstormOrHailExclFactor")
    fac = next((r[t.col("Factor")] for r in t.rows if str(r[t.col("BasicGroupIISymbol")]) == str(sym)), None)
    return f"lowest rate {lo} x symbol factor {fac}"


CASES = {
    "L-CA1": ("C27-06", "CA", "Legal Liability, District I", ll("CA", "District I"), expect_ll("District I")),
    "L-CA2": ("C27-06", "CA", "Legal Liability, District II", ll("CA", "District II"), expect_ll("District II")),
    "L-CA0": ("C27-06", "CA", "the same building, not Legal Liability (control), District I", ll("CA", "District I", False), expect_class),
    "L-FL": ("C27-06", "FL", "Legal Liability", ll("FL"), expect_ll()),
    "L-FL0": ("C27-06", "FL", "the same building, not Legal Liability (control)", ll("FL", legal=False), expect_class),
    "W-TX0": ("C27-07", "TX", "Group II, Seacoast 1, no wind / hail exclusion", bgii_tree("TX", "Seacoast 1", "4"),
              expect_gii("TX", "Seacoast 1", "4", "Seacoast 1", D(1))),
    "W-TX1": ("C27-07", "TX", "Group II, Seacoast 1, wind / hail EXCLUDED (TX: x 0.1)", bgii_tree("TX", "Seacoast 1", "4", True),
              expect_gii("TX", "Seacoast 1", "4", "Seacoast 1", D("0.1"))),
    "B-DC4": ("C27-08", "DC", "Group II, BCEG 4 (DC reads no BCEG)", bgii_tree("DC", None, "4"), None),
    "B-DC9": ("C27-08", "DC", "Group II, BCEG 9 (predicted equal to grade 4)", bgii_tree("DC", None, "9"), None),
    "B-NY4": ("C27-08", "NY", "Group II, BCEG 4 (NY reads no BCEG)", bgii_tree("NY", None, "4"), None),
    "B-NY9": ("C27-08", "NY", "Group II, BCEG 9 (predicted equal to grade 4)", bgii_tree("NY", None, "9"), None),
    "B-ILc": ("C27-08", "IL", "Group II, Cook County, BCEG 9 (the 'Cook' row)", bgii_tree("IL", "Cook County", "9"),
              expect_gii("IL", "Cook County", "9", "Cook")),
    "B-ILb": ("C27-08", "IL", "Group II, Balance of State, BCEG 9", bgii_tree("IL", "Balance of State", "9"),
              expect_gii("IL", "Balance of State", "9", "Balance of State")),
    "M-MT": ("C27-09", "MT", "Group II, Division A (the symbol table resolves)", bgii_tree("MT", "Division A", "4"), None),
}


def first_terr(j):
    """the state's first Group II territory filing a Frame 1-3 Bldg rate: the sweep's own choice."""
    book = book_for(j, ASOF)
    inp, why = s11.inputs_for(book, j)
    if inp:
        return str(inp["terr"])
    book_, sym, _ = None, None, None
    t = book.table("BasicGroupIIRate")
    sym = s11.chunk0._exact(book.table("BasicGroupIIConstructionSymbol"), [j, s11.CONSTRUCTION, s11.STORIES], "Symbol") \
        or s11.chunk0._exact(book.table("BasicGroupIIConstructionSymbol"), ["CW", s11.CONSTRUCTION, s11.STORIES], "Symbol")
    return str(next(r[t.col("BasicGroupIIRatingTerr")] for r in t.rows
                    if str(r[t.col("BasicGroupIISymbol")]) == str(sym) and str(r[t.col("CovType")]) == "Bldg"))


for cid in ("B-DC4", "B-DC9", "B-NY4", "B-NY9"):
    task, j, label, _, _ = CASES[cid]
    terr = first_terr(j)
    sym = "B" if j == "NY" else None                    # NY: the symbol is SUBMITTED (SetBasicGroupIISymbol is empty)
    CASES[cid] = (task, j, f"{label}, {terr}" + (", BasicGroupIISymbol B submitted" if sym else ""),
                  bgii_tree(j, terr, cid[-1], symbol=sym), expect_gii(j, terr, cid[-1]))


def expect_zero(form):
    return lambda data, j: ({form: D(0)}, [], "no symbol submitted: base rate 0")


CASES["B-NY0"] = ("C27-09", "NY", f"Group II, {first_terr('NY')}, NO BasicGroupIISymbol (ours: base rate 0, $0)",
                  bgii_tree("NY", first_terr("NY"), "4"), expect_zero("BasicGroupII"))
CASES["M-MT"] = CASES["M-MT"][:4] + (expect_gii("MT", "Division A", "4", "Division A"),)


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = {k: v for k, v in CASES.items() if not a.cases or k in a.cases.split(",")}
    reqs, preds = {}, {}
    for i, (cid, (task, j, label, build, expect)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"{cid} {task} {j} {label}")
        req = t2.state_req(t2.m20.payload(build()), j)
        TAGGED.clear()
        data, ip = rep.cmp.rate(req)
        want, bad, how = expect(data, j)
        got = {f: bldg_prem(data, f) for f in want}
        miss = [(f, w, got[f]) for f, w in want.items() if got[f] is None or got[f] != w]
        print(f"  {cid}: predicted {', '.join(f'{f} ${w}' for f, w in want.items())} ({how}); engine "
              f"{', '.join(f'{f} ${g}' for f, g in got.items())}  {'ok' if not miss and not bad else 'DIFFERS ' + str(miss + bad)}")
        if miss or bad:
            FAIL.append(cid)
        reqs[cid], preds[cid] = req, want
    for x, y in (("B-DC4", "B-DC9"), ("B-NY4", "B-NY9")):
        if x in preds and y in preds and preds[x] != preds[y]:
            print(f"  {x} / {y}: the hand fold differs by grade: the BCEG claim is wrong")
            FAIL.append(f"{x}/{y}")
    if "W-TX1" in cs:
        print(f"  W-TX1 competing (countrywide rebuild): {cw_rebuild('TX', 'Seacoast 1')}")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17: the predicted premium, every premium, the (level, message) multiset")
        for i, cid in enumerate(cs, 1):
            progress(i, len(cs), f"ISO {cid}")
            req = reqs[cid]
            (gc.OUT / f"chunk27_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = r2.rate_retry(client, req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:400]}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk27_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            TAGGED.clear()
            data, ip = rep.cmp.rate(req)
            mine = collections.Counter((lvl(t), x) for t, x in TAGGED)
            isos = collections.Counter(c23.iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            iso_pred = {f: next((v for k, v in ipr.items() if k.endswith(f"StructureBuilding{f}Coverage[0]/Premium")), None)
                        for f in preds[cid]}
            pbad = [(f, w, iso_pred[f]) for f, w in preds[cid].items() if iso_pred[f] is None or D(str(iso_pred[f])) != w]
            ok = not dd and mine == isos and not pbad
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: ISO {', '.join(f'{f} {v}' for f, v in iso_pred.items())} "
                  f"(predicted {', '.join(f'${w}' for w in preds[cid].values())}); {len(ipr) - len(dd)} of {len(ipr)} premiums; "
                  f"(level, message) {'equal' if mine == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (isos - mine).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (mine - isos).items()))
            if not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-3 (C27-06..09): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
