#!/usr/bin/env python3
"""Chunk 3, tasks 10-14 -- the five things Broad does differently.

Broad is the shortest chain in the coverage and the odd one out in four ways.
Each is a claim the task list made from reading the rules; each is asserted
here, with the numbers derived by hand from the filed rows before the run.

  10  **No cause-of-loss adjustment step at all** -- the only one of the four
      forms without one. Verify nothing silently substitutes for it.
  11  **Roof-surfacing ACV is folded into `SetAdjustedBroadRate`**, not into
      the rate or a cause-of-loss step. Different position from every other
      form -- and the position turns out to matter less than the magnitude.
  12  **No Broad deductible-by-location rule.** It reuses the shared
      `DeductibleByLocationFactor` where Group II and Special each have their
      own. Confirm the three do not interfere.
  13  **The two-tier base rate** -- 0.015 for the four combustible/light
      constructions, 0.010 for the two fire-resistive. A case on each tier.
  14  **Class 1150 routes to the `BldrRisk` rows** rather than `Bldg`, and
      those are flat 0.012 across all six construction types.

    python scripts/cf/20_chunk3_broad_structure.py

Exit 0 when every case matches.
"""
from __future__ import annotations

import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk2 = import_module("09_chunk2_golden_case")
chunk3 = import_module("15_chunk3_golden_case")
zeros2 = import_module("10_chunk2_zero_cases")

STRUCT = chunk2.STRUCT
BROAD, SPECIAL = chunk3.BROAD, chunk3.SPECIAL

ROOF = "CommercialPropertyLimitationsOnCovForRoofSurfacing"
BYLOC = "CommercialPropertyDeductiblesByLocationBldg"


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def run(form="Broad", **mut):
    """One Oregon submission, mutated, run to completion."""
    sub = chunk3.submission(form)
    st = zeros2.structure(sub)
    for k, v in mut.items():
        if v is None:
            st.pop(k, None)
        else:
            st[k] = v
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(data)
    return data


def v(data, dd):
    return read(f"{STRUCT}/{dd}", data)


book = book_for(chunk2.JURIS, chunk2.ASOF)
ok = True


def check(label, got, want):
    global ok
    good = str(got) == str(want)
    ok &= good
    print(f"    {label:52s} {str(got):>8s}  "
          f"(expected {str(want):>8s}) {'OK' if good else 'MISMATCH'}")


print(f"{book}\n")

# ---------------------------------------------------------------- task 10
print("=== 10  No cause-of-loss adjustment step, anywhere")
res = CFEditionResolver()
defined = []
for j in ["CW"] + list(res.jurisdictions):
    b = book_for(j, chunk2.ASOF, resolver=res) if j != "CW" else book
    f = b.state.package.content / "Rules" / \
        "CommercialPropertyStructureRules.Rule.xml"
    if f.exists() and '<rul:Rule Name="SetBroadCauseOfLossAdjustment"' \
            in f.read_text(encoding="utf-8-sig"):
        defined.append(j)
# "n of N", with N from the corpus -- a negative claim has to state what was
# enumerated, not just assert a silence.
check(f"jurisdictions defining SetBroadCauseOfLossAdjustment "
      f"(of {len(res.jurisdictions)} + CW)", len(defined), 0)

data = run()
# Nothing substitutes for it either: the datadef is never written, and the
# adjusted rate equals the four-term product with no cause-of-loss term in it.
check("BroadCauseOfLossAdjustment written?", v(data, "BroadCauseOfLossAdjustment"), None)
rate, loi = Decimal(v(data, "BroadRate")), Decimal(v(data, "BroadLOIFactor"))
coins = Decimal(v(data, "CoinsuranceFactor"))
roof = Decimal(v(data, "LimitationsOnCovForRoofSurfacingACVFactor"))
check("AdjustedBroadRate = r3(r3(r3(rate x roof) x coins) x LOI)",
      v(data, "AdjustedBroadRate"), r3(r3(r3(rate * roof) * coins) * loi))
print("    Special, for contrast, HAS the step:")
sp = run("Special")
check("SpecialCauseOfLossAdjustment", sp and v(sp, "SpecialCauseOfLossAdjustment"),
      v(sp, "SpecialRate"))

# ---------------------------------------------------------------- task 13
print("\n=== 13  The two-tier base rate, a case on each tier")
# **`ConstructionType` is NOT the six-name rating list.** It is a 25-value
# submission domain that MAPS onto the six, and `"Frame"` is the only one of
# the six that is also a valid input. Submitting `"Joisted Masonry"` -- the
# name the rate table itself is keyed on -- is off-domain, the lookup misses,
# `ConstructionTypeToUse` is null, and the whole Broad chain prices at ZERO
# with nothing raised. The first draft of this test did exactly that and read
# the five zeros as a bug in the engine.
TIERS = [("Frame", "Frame", "0.015", "16"),
         ("Joisted Masonry - Reinforced", "Joisted Masonry", "0.015", "16"),
         ("Non-Combustible - Light Steel", "Non-Combustible", "0.015", "16"),
         ("Masonry Non-Combustible - Reinforced - Light Steel",
          "Masonry Non-Combustible", "0.015", "16"),
         ("Modified Fire Resistive - Reinforced Masonry - Light Steel",
          "Modified Fire Resistive", "0.01", "12"),
         ("Fire Resistive - Reinforced Masonry - Light Steel",
          "Fire Resistive", "0.01", "12")]
for ct, rating_type, base, prem in TIERS:
    d = run(ConstructionType=ct)
    check(f"{rating_type:24s} resolved from the submitted value",
          v(d, "ConstructionTypeToUse"), rating_type)
    check(f"{rating_type:24s} base", v(d, "BroadBaseRate"), base)
    check(f"{rating_type:24s} premium", read(BROAD, d), prem)

print("\n    **The rating-type names are not valid submission values.**")
for off in ("Joisted Masonry", "Fire Resistive"):
    d = run(ConstructionType=off)
    check(f"submitted {off!r:26s} -> ConstructionTypeToUse",
          v(d, "ConstructionTypeToUse"), None)
    check(f"submitted {off!r:26s} -> premium", read(BROAD, d), "0")
print("    `ConstructionType` is a 25-value domain that MAPS onto the six")
print("    rating types, and `Frame` is the only one of the six that is also")
print("    a valid input. Submitting the name the RATE TABLE is keyed on --")
print("    `Joisted Masonry`, `Fire Resistive` -- misses the domain lookup and")
print("    prices at zero in silence. Eighth member of the absent-means-zero")
print("    family, and the most plausible-looking one yet: the value is")
print("    exactly what the rate table calls the row.")
print("    The fire-resistive tier is a ROUNDING case as well as a rate one:")
print("      r3(0.010 x 0.95) = 0.010 under half-up, 0.009 under truncation,")
print("      which would carry through to $11 instead of $12. Half-up was")
print("      already proven against ISO in chunk 1; this is a second site.")

# ---------------------------------------------------------------- task 14
print("\n=== 14  Class 1150 routes to the BldrRisk rows -- flat across "
      "construction")
for ct in ("Frame", "Fire Resistive - Reinforced Masonry - Light Steel"):
    d = run(ConstructionType=ct, ClassCode="1150")
    check(f"class 1150, {ct[:24]:24s} base", v(d, "BroadBaseRate"), "0.012")
    check(f"class 1150, {ct[:24]:24s} coinsurance", v(d, "CoinsuranceFactor"), "1")
    check(f"class 1150, {ct[:24]:24s} premium", read(BROAD, d), "15")
print("    The point of the pair: on the Bldg rows construction moves the rate")
print("    (0.015 vs 0.010); on the BldrRisk rows it does not (0.012 either")
print("    way). Same rule, same submission field, two different behaviours.")
print()
print("    **And class 1150 removes coinsurance, from a different rule.**")
print("    The premium is $15, not the $14 the base rate alone predicts,")
print("    because `SetCoinsuranceFactor` ALSO tests the literal `1150` and")
print("    returns 1.0 instead of the 90% factor 0.95. Two rules, filed in")
print("    different places, both hardcoding the same class code -- so")
print("    `ClassCode = 1150` is a Builders Risk switch with at least two")
print("    independent consequences, and finding one does not find the other.")

# ---------------------------------------------------------------- task 11
print("\n=== 11  Roof-surfacing ACV -- position confirmed, effect NIL")
# Paragraph B is filed at 0.99 and is UNREACHABLE: the rule tests
# `Applicability != "Paragraph B"` before looking anything up, and its Else
# branch assigns a flat 1.0. Only `Paragraph A` and `Paragraph A and B` reach
# the table. Predicted 0.99 here and the engine said 1.0 -- the engine is
# right, and the filed row is dead.
for para, factor in (("Paragraph A", "0.98"), ("Paragraph A and B", "0.98"),
                     ("Paragraph B", "1")):
    sub = chunk3.submission("Broad")
    st = zeros2.structure(sub)
    st["PolicyType"] = "Commercial Property Policy"
    st[f"{ROOF}Table"] = {ROOF: [{"Applicability": para}]}
    sub["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = \
        "Commercial Property Policy"
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    d = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
    ip.run(d)
    check(f"{para} factor", v(d, "LimitationsOnCovForRoofSurfacingACVFactor"),
          factor)
    # The POSITION claim: the factor is applied inside SetAdjustedBroadRate,
    # so the RATE step must be untouched by it.
    check(f"{para} BroadRate unchanged (position claim)",
          v(d, "BroadRate"), "0.015")
    check(f"{para} premium", read(BROAD, d), "16")

print("\n    **A filed endorsement that cannot change a Broad building "
      "premium.**")
print("    Every Broad base rate filed anywhere in the corpus absorbs both")
print("    factors at three decimals:")
rates = set()
for j in res.jurisdictions:
    t = book_for(j, chunk2.ASOF, resolver=res).table("BroadFormBaseRate")
    rates |= {(str(r[2]), Decimal(str(r[3]))) for r in t.rows
              if str(r[2]) in ("Bldg", "BldrRisk")}
moved = [(c, b, f) for c, b in sorted(rates)
         for f in (Decimal("0.98"), Decimal("0.99")) if r3(b * f) != b]
for cov, base in sorted(rates):
    print(f"      {cov:9s} {base}  x0.98 -> {r3(base * Decimal('0.98'))}"
          f"   x0.99 -> {r3(base * Decimal('0.99'))}")
check(f"filed Broad base rates the roof factor can move "
      f"(of {len(rates)})", len(moved), 0)
print("    This is NOT the rule boundary doing it -- it is magnitude. Special")
print("    applies the same factor to a rate of 0.047 and moves $54 -> $52.")
print("    Broad's rates are simply too small for a 1-2% credit to survive")
print("    rounding to three decimals. Worth logging as a real divergence")
print("    between what ISO filed and what any submission can produce.")

sp = chunk3.submission("Special")
st = zeros2.structure(sp)
st["PolicyType"] = "Commercial Property Policy"
st[f"{ROOF}Table"] = {ROOF: [{"Applicability": "Paragraph A"}]}
sp["CommercialPropertyTable"]["CommercialProperty"][0]["PolicyType"] = \
    "Commercial Property Policy"
ip = Interpreter(book, rounding=ROUNDING, trace=False,
                 null_arithmetic=NULL_ARITHMETIC)
d = Node.from_dict(f"MasterCF{chunk2.JURIS}", sp)
ip.run(d)
check("Special, same endorsement: COL adjustment 0.047 -> ",
      v(d, "SpecialCauseOfLossAdjustment"), "0.046")
check("Special, same endorsement: premium 54 -> ", read(SPECIAL, d), "52")

# ---------------------------------------------------------------- task 12
print("\n=== 12  The three deductible-by-location rules do not interfere")
sub = chunk3.submission("Broad")
zeros2.structure(sub)[f"{BYLOC}Table"] = {BYLOC: [{"Deductible": "2,500"}]}
ip = Interpreter(book, rounding=ROUNDING, trace=False,
                 null_arithmetic=NULL_ARITHMETIC)
d = Node.from_dict(f"MasterCF{chunk2.JURIS}", sub)
ip.run(d)
check("shared DeductibleByLocationFactor (Broad reads this)",
      v(d, "DeductibleByLocationFactor"), "0.995")
check("Group II's own factor -- gated on a WIND/HAIL by-location deductible",
      v(d, "BGIIDeductibleByLocationFactor"), "1")
check("Special's own factor -- gated on a THEFT by-location deductible",
      v(d, "SpecialDeductibleByLocationFactor"), "1")
check("Broad premium", read(BROAD, d), "16")
print("    Three rules, one record, three different gates. Broad has no rule")
print("    of its own and takes the shared one; the other two stay at 1.0")
print("    because this record carries a plain Deductible and neither a")
print("    windstorm/hail nor a theft one. The premium does not move -- 0.995")
print("    is absorbed at three decimals, the same way the roof factor is.")

print()
if ok:
    print("Tasks 10-14 all match.")
    raise SystemExit(0)
print("MISMATCHES above.")
raise SystemExit(1)
