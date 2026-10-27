#!/usr/bin/env python3
"""Chunk 0's four proofs, run against the corpus.

Chunk 0 has no gate of its own -- it is proved by chunk 1's golden case. What
it owes before chunk 1 starts is narrower, and this script is that list:

  1. Every `rul:` element name in the Property corpus either evaluates or
     raises a NAMED error. No silent unknowns.
  2. The header-only detector fires on a known header-only table, and names it.
  3. The resolver resolves a state over its DECLARED parent, and every table
     the chunk 1 chain touches is reachable in one of those two layers.
  4. Every table value the chunk 1 golden case depends on is confirmed against
     the corpus, through the engine's own book rather than by reading files.

Check 4 is not in the chunk 0 spec. It was added because checks 1-3 prove the
machinery loads and refuses correctly while saying nothing about whether the
numbers chunk 1 expects are actually there -- and those numbers were resolved
by hand, which is exactly the kind of evidence worth re-deriving by machine.

    python scripts/cf/00_chunk0_checks.py [--asof YYYYMMDD] [--juris OR]

Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import CORPUS_ROOT
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import TableError
from gl_engine.interp import nodes

#: Container elements, not operators: they hold the program rather than being
#: evaluated in it. `Rules`/`Rule` are the file and rule wrappers, `MetaData`/
#: `MetaDataCode` ISO's own annotations. The same four are unregistered for GL.
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode"}

#: Deliberate refusals -- registered, and raising a named error by design.
REFUSALS = {"Custom", "FromList"}

_EL = re.compile(rb"<rul:([A-Za-z]+)")

PASS, FAIL = "PASS", "FAIL"


def _say(ok: bool, label: str, detail: str = "") -> bool:
    print(f"  [{PASS if ok else FAIL}] {label}")
    if detail:
        for line in detail.splitlines():
            print(f"         {line}")
    return ok


# ---------------------------------------------------------------- check 1

def check_elements(root: Path) -> bool:
    """Enumerate every element name in the corpus; classify every one.

    The population is the corpus, not a search: every `*.xml` under the root,
    every edition, read as bytes so a 7.6 MB master XSD costs nothing to skip.
    """
    print("\n1. Every corpus element name is handled")
    seen: dict[str, int] = {}
    for f in root.rglob("*.xml"):
        for m in _EL.finditer(f.read_bytes()):
            n = m.group(1).decode()
            seen[n] = seen.get(n, 0) + 1

    registered = set(nodes.EVAL)
    unknown = sorted(n for n in seen if n not in registered and n not in STRUCTURAL)
    ok = _say(not unknown,
              f"{len(seen)} distinct element names; "
              f"{len(seen) - len(STRUCTURAL & set(seen))} operators, "
              f"{len(STRUCTURAL & set(seen))} structural",
              "" if not unknown else
              "unhandled, and they would raise 'unknown node':\n  "
              + ", ".join(unknown))
    refused = sorted(REFUSALS & set(seen))
    _say(True, f"refused by name, not silently: {', '.join(refused) or '(none)'}",
         "\n".join(f"{n}: {seen[n]} occurrences" for n in refused))
    return ok


# ---------------------------------------------------------------- check 2

def check_header_only(juris: str, asof: str) -> bool:
    """A header-only table must refuse, and say which package it came from."""
    print("\n2. The header-only detector")
    book = book_for(juris, asof)
    ok = True

    # Countrywide's own book: BasicGroupIRate is header-only there.
    cw = book_for("CW", asof)
    t = cw.table("BasicGroupIRate")
    ok &= _say(len(t.rows) == 0,
               f"CW BasicGroupIRate loads with {len(t.rows)} rows "
               f"(header-only, as filed)")
    try:
        cw.rating_table("BasicGroupIRate")
        ok &= _say(False, "rating_table() returned an empty table")
    except TableError as exc:
        ok &= _say("0 rows" in str(exc) and "BasicGroupIRate" in str(exc),
                   "rating_table() refuses it, naming the table and the package",
                   str(exc))

    # The state layer is what makes it rateable, and it must win by name.
    st = book.rating_table("BasicGroupIRate")
    ok &= _say(st.package == book.state.pkg_id and len(st.rows) > 0,
               f"{juris} BasicGroupIRate resolves to {st.package} "
               f"with {len(st.rows)} rows")
    ok &= _say(book.declares("BasicGroupIRate") == "state",
               "and the book reports the STATE layer as its owner")
    return ok


# ---------------------------------------------------------------- check 3

#: Every table the chunk 1 chain reads, with the layer it is expected from,
#: for the golden case's jurisdiction. Expectations are asserted, not
#: discovered, so a corpus change that moves a table between layers fails here
#: rather than quietly re-pricing.
#:
#: Three of the five state-owned entries were wrong on the first pass, and each
#: was wrong in a way worth keeping visible:
#:
#: * `SubStdConditionRate` -- Oregon files all 30 rows with its own values
#:   (0.313 against countrywide's 0.321). A real deviation, not a copy.
#: * `VacantBldgPreviousOrIntendedOccup` -- countrywide is HEADER-ONLY and
#:   Oregon files 106 rows. This was not on any known list of zero-row tables.
#: * `DeductibleFactor` -- known, and the case A/B discriminator.
CHAIN = [
    ("BasicGroupIRate", "state"),
    ("RatingTerritoryGroupIFactor", "state"),
    ("ProtectionClassFactor", "countrywide"),
    ("CoinsuranceFactor", "countrywide"),
    ("BasicGroupILOIFactorBldg", "countrywide"),
    ("DeductibleFactor", "state"),
    ("Deductible250Factor", "countrywide"),
    ("DeductibleByLocationFactor", "countrywide"),
    ("CyberIncidentExclusionFactors", "countrywide"),
    ("LessThan80PctMultiplicativeFactor", "countrywide"),
    ("SubStdConditionRate", "state"),
    ("VacantBldgPreviousOrIntendedOccup", "state"),
    ("VandalismExclFactor", "countrywide"),
    ("StdPropPolGroupIFactor", "countrywide"),
    ("LimitationsOnCovForRoofSurfacingFactor", "countrywide"),
    ("MultiResidentialPropSpecialCreditHeatFactor", "countrywide"),
    ("MultiResidentialPropSpecialCreditControlFactor", "countrywide"),
]


def check_layers(juris: str, asof: str) -> bool:
    """Two layers, and every chain table reachable inside them.

    This is also the test of the build order's edition-carry-forward premise.
    If every table the chain needs is present in the state package or its
    DECLARED parent, no third layer is needed for chunk 1 -- and the claim that
    one is needed stays unproven rather than being built on.
    """
    print("\n3. Layers, and whether a third one is needed")
    resolver = CFEditionResolver()
    res = resolver.resolve(juris, asof)
    ok = _say(res.parent is not None,
              f"{juris}@{asof} -> {res.state.pkg_id} over {res.parent.pkg_id}")
    ok &= _say(res.state.declared_parent == res.parent.pkg_id,
               "the parent is the one the package DECLARES (N5), not the newest")

    book = book_for(juris, asof, resolver=resolver)
    missing, wrong = [], []
    for name, expect in CHAIN:
        owner = book.declares(name)
        if owner is None:
            missing.append(name)
        elif owner != expect:
            wrong.append(f"{name}: expected {expect}, resolved {owner}")
    ok &= _say(not missing,
               f"all {len(CHAIN)} chain tables resolve within the two layers",
               "not in either layer:\n  " + "\n  ".join(missing) if missing else "")
    ok &= _say(not wrong, "each resolves to the layer chunk 1 expects",
               "\n".join(wrong))
    if not missing:
        print("         -> no edition carry-forward is required for this chain.")
        print("            The build order's third-layer premise stays unproven,")
        print("            and is not built on.")

    # Which chain tables are header-only at countrywide. `Table.__len__` makes
    # an empty table falsy, so "absent" and "zero rows" are asked separately --
    # conflating them is what a first pass of this report did, and it is the
    # same conflation the header-only detector exists to prevent.
    zero_cw = []
    for name, _ in CHAIN:
        if book.parent and book.parent.has("Rate", name):
            if len(book.parent.table("Rate", name).rows) == 0:
                zero_cw.append(name)
    _say(True,
         f"{len(zero_cw)} of {len(CHAIN)} chain tables are header-only at "
         f"countrywide",
         "\n".join(f"{n} -- rateable only from a state filing" for n in zero_cw)
         + ("\nChunk 1 therefore proves state-only table resolution three times "
            "over.\nThe build order put that proof in chunk 2; it happens here."
            if len(zero_cw) > 1 else ""))
    return ok


# ---------------------------------------------------------------- check 4

#: (table, keys, expected value). Keys are in the table's own filed key order.
#: Every one of these was resolved by hand for the golden case; this re-derives
#: them through the engine's book so the two have to agree.
GOLDEN = [
    ("BasicGroupIRate", ["OR", "0951", 1, "Not Applicable", "Building"],
     "Rate", Decimal("0.498")),
    ("RatingTerritoryGroupIFactor", ["OR", "Portland"],
     "Factor", Decimal("0.499")),
    ("ProtectionClassFactor", ["CW", "3", 1], "Factor", Decimal("0.96")),
    ("CoinsuranceFactor", ["CW", "90%"], "Factor", Decimal("0.95")),
    ("CyberIncidentExclusionFactors", ["CW", "Basic Group I"],
     "Factor", Decimal("0.995")),
]

#: Banded lookups: (table, equality keys, band value, column, expected).
GOLDEN_BANDED = [
    ("BasicGroupILOIFactorBldg", ["CW"], 1, 100000, "Factor",
     Decimal("1.172"), "case A -- at the band's lower edge, no interpolation"),
    ("BasicGroupILOIFactorBldg", ["CW"], 1, 112500, "Factor",
     Decimal("1.150"), "case C -- midpoint, linear interpolation"),
    ("DeductibleFactor", ["OR", "1,000"], None, 100000, "Factor",
     Decimal("0.98"), "case A -- TotAmtInsurance 100,000"),
    ("DeductibleFactor", ["OR", "1,000"], None, 200000, "Factor",
     Decimal("0.99"), "case B -- TotAmtInsurance 200,000, Limit unchanged"),
    ("DeductibleFactor", ["CW", "1,000"], None, 100000, "Factor",
     Decimal("0.96"), "the countrywide row the state must beat"),
]


def _exact(table, keys, col):
    d = table.definition
    idx = [table.col(c.name) for c in d.key_cols]
    out = table.col(col)
    for row in table.rows:
        if all(str(row[i]) == str(k) for i, k in zip(idx, keys)):
            return row[out]
    return None


def _banded(table, eq_keys, tail_key, x, col):
    """Match the equality keys, then the band, honouring the declared bounds.

    Interpolates when the VALUE is a range carrying `InterpolateMode`, which is
    where `BasicGroupILOIFactorBldg` lives -- and stepping it instead would be
    wrong by up to the width of a band.
    """
    d = table.definition
    rng = d.key_ranges[0]
    eq = [c.name for c in d.key_cols]
    want = list(eq_keys) + ([tail_key] if tail_key is not None else [])
    idx = [table.col(c) for c in eq]
    lo_i, hi_i = table.col(rng.lo_col), table.col(rng.hi_col)
    x = Decimal(x)
    for row in table.rows:
        if any(str(row[i]) != str(k) for i, k in zip(idx, want)):
            continue
        lo, hi = Decimal(row[lo_i]), Decimal(row[hi_i])
        below = lo <= x if rng.lo_inclusive else lo < x
        above = x <= hi if rng.hi_inclusive else x < hi
        if not (below and above):
            continue
        for vr in d.value_ranges:
            if vr.name == col:
                v_lo = Decimal(row[table.col(vr.lo_col)])
                v_hi = Decimal(row[table.col(vr.hi_col)])
                span = hi - lo
                pos = (x - lo) / span if span else Decimal(0)
                return v_lo + (v_hi - v_lo) * pos
        return row[table.col(col)]
    return None


def check_golden(juris: str, asof: str) -> bool:
    print("\n4. Every value the chunk 1 golden case depends on")
    book = book_for(juris, asof)
    ok = True
    for name, keys, col, expect in GOLDEN:
        t = book.rating_table(name)
        got = _exact(t, keys, col)
        ok &= _say(got is not None and Decimal(str(got)) == expect,
                   f"{name}{keys} -> {got}  (expected {expect}) [{t.package}]")
    for name, eq, tail, x, col, expect, why in GOLDEN_BANDED:
        # A `CW` first key means the countrywide copy is the one being asked
        # about -- which for `DeductibleFactor` is the row the state override
        # has to beat, and is reachable only by naming the parent layer
        # explicitly. Everywhere else the resolved table is the answer.
        wants_parent = eq and eq[0] == "CW" and book.declares(name) == "state"
        t = book.parent_table(name) if wants_parent else book.rating_table(name)
        got = _banded(t, eq, tail, x, col)
        ok &= _say(got is not None and Decimal(str(got)) == expect,
                   f"{name}{eq} @{x} -> {got}  (expected {expect})",
                   why)
    return ok


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default="20260917")
    ap.add_argument("--juris", default="OR")
    ap.add_argument("--skip-scan", action="store_true",
                    help="skip check 1's full-corpus element scan")
    a = ap.parse_args()

    print(f"Property chunk 0 checks -- corpus {CORPUS_ROOT}")
    print(f"jurisdiction {a.juris}, as-of {a.asof}")
    results = []
    if not a.skip_scan:
        results.append(check_elements(CORPUS_ROOT))
    results.append(check_header_only(a.juris, a.asof))
    results.append(check_layers(a.juris, a.asof))
    results.append(check_golden(a.juris, a.asof))

    print()
    if all(results):
        print(f"All {len(results)} checks PASS.")
        return 0
    print(f"{sum(1 for r in results if not r)} of {len(results)} checks FAIL.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
