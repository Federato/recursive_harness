#!/usr/bin/env python3
"""Chunk 3, gate point 3 -- every jurisdiction enumerated for Broad and Special.

Same discipline as chunks 1 and 2: each jurisdiction gets its own case, built
from its own filed rows, and **both premiums are predicted before the engine
runs**. Rating 47 states and reporting that 94 numbers came out proves nothing.

What makes chunk 3's sweep different from chunk 2's is that the two forms are
expected to behave in OPPOSITE ways across the states, and the sweep is the
thing that tests it:

  * **Broad's base-rate table is countrywide** -- `BroadFormBaseRate` carries
    30 CW rows, two-tiered by construction (0.015 combustible / 0.010 fire
    resistive) with Builders Risk flat at 0.012. So Broad is predicted to rate
    almost everywhere off the same rows, and any state that differs is a
    genuine state filing rather than a gap.

  * **Special's is not.** `SpecialBuildingRate` is header-only countrywide --
    45 of 47 jurisdictions file it. Chunk 2's shape exactly, and the second
    time the state layer has been load-bearing.

**The first pass of this sweep skipped FL and PR as "no rate filed", and that
was wrong.** Both rate Special; both do it through their own overriding rule
reading their own differently-named table, which a table-name search cannot
see. The corrected readings are in `special_inputs` below and they are the most
valuable thing the sweep produced:

  * **FL splits the building rate residential / non-residential**, choosing
    between `SpecialBuildingRateNonResidential` and `...Residential` on a
    hardcoded list of 21 class codes written into the rule itself. No other
    jurisdiction has that dimension.
  * **PR does not use the cause-of-loss value `"Special"` at all.** Its rule
    gates on `"Special Including Theft"` / `"Special Excluding Theft"` -- two
    values that do not exist countrywide -- and reads `SpecialBldgRate`, which
    is keyed on **construction type**, a dimension countrywide Special does not
    have. A submission saying `Special` is off-domain in Puerto Rico, which is
    why the first pass saw a zero and read it as an absent filing.

Both forms share one LOI table (`BroadSpecialLOIFactorBldg`), which is the
sweep's incidental test of a shared table: if a state files its own, it must
move both forms together or the sharing is not what it looks like.

Basic Group I and II are deliberately NOT asserted here -- their per-state
inputs are chunks 1 and 2's job, and this sweep supplies Oregon's. They are
reported so a state where they raise is visible, not silent.

    python scripts/cf/17_chunk3_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction either matches both predictions or is skipped
for a stated, enumerated reason.
"""
from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import EngineError
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk0 = import_module("00_chunk0_checks")
chunk2 = import_module("09_chunk2_golden_case")
chunk3 = import_module("15_chunk3_golden_case")

STRUCT, BGI, BGII = chunk2.STRUCT, chunk2.BGI, chunk2.BGII
BROAD, SPECIAL = chunk3.BROAD, chunk3.SPECIAL

LIMIT, DEDUCTIBLE, COINS = 100000, "1,000", "90%"
CONSTRUCTION, CLASS_CODE = "Frame", "0951"
DED_COL = "Other Cause Of Loss"      # both forms, not the Basic Group labels


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def r0(x):
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def key(book, name, juris):
    """The state's own row if it files this table, else the countrywide one."""
    return juris if book.declares(name) == "state" else "CW"


def shared(book, juris):
    """Coinsurance, LOI and deductible -- the three factors both forms share."""
    coins = chunk0._exact(book.table("CoinsuranceFactor"),
                          [key(book, "CoinsuranceFactor", juris), COINS],
                          "Factor")
    if coins is None:
        return None, f"no CoinsuranceFactor row for {COINS}"
    loi = chunk0._banded(book.table("BroadSpecialLOIFactorBldg"),
                         [key(book, "BroadSpecialLOIFactorBldg", juris)],
                         None, LIMIT, "Factor")
    if loi is None:
        return None, "no BroadSpecialLOIFactorBldg band for the limit"
    ded = chunk0._banded(book.table("DeductibleFactor"),
                         [key(book, "DeductibleFactor", juris), DEDUCTIBLE],
                         DED_COL, LIMIT, "Factor")
    if ded is None:
        return None, f"no DeductibleFactor band for {DEDUCTIBLE}/{DED_COL}"
    return {"coins": Decimal(coins), "loi": Decimal(loi),
            "ded": Decimal(ded)}, None


def predict_broad(book, juris, f):
    """6 steps. Roof-surfacing ACV is folded into the adjusted-rate step."""
    t = book.table("BroadFormBaseRate")
    if t.is_empty:
        return None, "BroadFormBaseRate is header-only in both layers"
    base = chunk0._exact(t, [key(book, "BroadFormBaseRate", juris),
                             CONSTRUCTION, "Bldg"], "Rate")
    if base is None:
        return None, f"no BroadFormBaseRate row for {CONSTRUCTION}/Bldg"
    rate = r3(Decimal(base) * 1)                       # x LossCostMultiplier
    adjusted = r3(r3(r3(rate * 1) * f["coins"]) * f["loi"])   # x roofACV = 1.0
    final = r3(r3(adjusted * 1) * f["ded"])            # x dedByLoc, x multiRes
    return {"base": base, "final": final, "col": None, "note": None,
            "premium": r0(final * LIMIT / 100)}, None


def fl_residential_classes(book):
    """The 21 class codes Florida's own rule routes to the RESIDENTIAL table.

    Parsed out of the filed rule rather than typed from the manual, so the
    script cannot drift from the corpus. Gate point 5 wants every hardcoded
    literal key listed: these are Florida's, and they exist in no other
    jurisdiction's copy of this rule.
    """
    f = book.state.package.content / "Rules" / \
        "CommercialPropertyStructureRules.Rule.xml"
    t = f.read_text(encoding="utf-8-sig")
    i = t.find('<rul:Rule Name="SetSpecialBaseRate"')
    body = t[i:][:t[i:].find("\n\t</rul:Rule>")]
    codes = re.findall(r'<rul:Constant Type="string">(\d{4})</rul:Constant>',
                       body)
    return sorted({c for c in codes if c != "1150"})


def special_inputs(book, juris):
    """This jurisdiction's own Special base rate, by ITS OWN rule.

    Three shapes, not one -- and the sweep is the thing that found that.
    """
    if juris == "FL":
        res = fl_residential_classes(book)
        table = ("SpecialBuildingRateResidential" if CLASS_CODE in res
                 else "SpecialBuildingRateNonResidential")
        base = chunk0._exact(book.table(table), [juris, "Y"], "Rate")
        note = (f"FL: {table.replace('SpecialBuildingRate', '')} "
                f"(class {CLASS_CODE} is "
                f"{'in' if CLASS_CODE in res else 'not in'} FL's list of "
                f"{len(res)} residential class codes)")
        return base, None, note
    if juris == "PR":
        # PR's rule never tests `"Special"`. Its own cause-of-loss domain
        # splits theft into the selection instead of applying a factor, and
        # its table is keyed on construction type -- which countrywide
        # Special is not.
        col = "Special Including Theft"
        base = chunk0._exact(book.table("SpecialBldgRate"),
                             [juris, col, CONSTRUCTION], "Rate")
        return base, col, (f"PR: SpecialBldgRate, cause of loss {col!r}, "
                           f"keyed on construction")
    t = book.table("SpecialBuildingRate")
    if t.is_empty:
        return None, None, "SpecialBuildingRate resolves to no rows"
    return chunk0._exact(t, [key(book, "SpecialBuildingRate", juris), "Y"],
                         "Rate"), None, None


def predict_special(book, juris, f):
    """9 steps, but the rate build-up is a flat constant and nothing else."""
    base, col, note = special_inputs(book, juris)
    if base is None:
        return None, note or "no Special base rate for this jurisdiction"
    rate = r3(Decimal(base) * 1)
    coladj = r3(r3(rate * 1) * 1)                  # x theft 1.0, x roofACV 1.0
    adjusted = r3(r3(coladj * f["coins"]) * f["loi"])
    final = r3(r3(adjusted * 1) * f["ded"])
    return {"base": base, "final": final, "col": col, "note": note,
            "premium": r0(final * LIMIT / 100)}, None


def rate_state(juris, form, resolver, col=None):
    """`col` overrides the submitted cause of loss -- PR needs its own."""
    sub = chunk3.submission(col or form)
    book = book_for(juris, chunk2.ASOF, resolver=resolver)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    path = BROAD if form == "Broad" else SPECIAL
    return read(path, data), read(BGI, data), read(BGII, data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    resolver = CFEditionResolver()
    js = resolver.jurisdictions
    print("Chunk 3, gate point 3 -- Broad and Special across every "
          "jurisdiction")
    print(f"as-of {chunk2.ASOF};  N = {len(js)} in the corpus\n")
    print(f"{'':4s} {'Bbase':>6s} {'Bfinal':>7s} {'pred':>5s} {'eng':>5s}  "
          f"{'Sbase':>6s} {'Sfinal':>7s} {'pred':>5s} {'eng':>5s}   notes")

    rows, broad_bad, special_bad, skipped = [], [], [], []
    for j in js:
        try:
            book = book_for(j, chunk2.ASOF, resolver=resolver)
        except EngineError as exc:
            skipped.append((j, "both", f"does not resolve: {exc}"))
            continue
        f, why = shared(book, j)
        if f is None:
            skipped.append((j, "both", why))
            print(f"{j:4s} SKIP  {why}")
            continue

        line, notes = f"{j:4s} ", []
        for form, predictor, bad in (("Broad", predict_broad, broad_bad),
                                     ("Special", predict_special, special_bad)):
            p, why = predictor(book, j, f)
            if p is None:
                skipped.append((j, form, why))
                line += f"{'--':>6s} {'--':>7s} {'--':>5s} {'--':>5s}  "
                notes.append(f"{form}: {why}")
                continue
            if p.get("note"):
                notes.append(p["note"])
            try:
                got, gi, gii = rate_state(j, form, resolver, p.get("col"))
            except EngineError as exc:
                bad.append((j, f"RAISED {type(exc).__name__}: {exc}"))
                line += f"{str(p['base']):>6s} {str(p['final']):>7s} " \
                        f"{str(p['premium']):>5s} {'RAIS':>5s}  "
                continue
            ok = got is not None and Decimal(got) == p["premium"]
            if not ok:
                bad.append((j, f"engine {got}, predicted {p['premium']}"))
            line += f"{str(p['base']):>6s} {str(p['final']):>7s} " \
                    f"{str(p['premium']):>5s} {str(got):>5s}{'' if ok else '*'} "
            if a.verbose:
                notes.append(f"{form}: coins={f['coins']} loi={f['loi']} "
                             f"ded={f['ded']} GI={gi} GII={gii}")
        print(line + ("   " + " | ".join(notes) if notes else ""))
        rows.append(j)

    n = len(js)
    print(f"\n{'':4s} Broad   {n - len(broad_bad) - sum(1 for _, fm, _ in skipped if fm in ('Broad', 'both'))}"
          f" of {n} exact")
    print(f"{'':4s} Special {n - len(special_bad) - sum(1 for _, fm, _ in skipped if fm in ('Special', 'both'))}"
          f" of {n} exact")
    if skipped:
        print(f"\nSkipped, each for a stated reason ({len(skipped)}):")
        for j, form, why in skipped:
            print(f"   {j} {form}: {why}")
    for label, bad in (("Broad", broad_bad), ("Special", special_bad)):
        if bad:
            print(f"\n{label}: {len(bad)} FAILED -- a defect until explained:")
            for j, why in bad:
                print(f"   {j}: {why}")
    return 0 if not (broad_bad or special_bad) else 1


if __name__ == "__main__":
    raise SystemExit(main())
