#!/usr/bin/env python
"""Stage 1 acceptance: load and resolve.

Every case here checks a property of ISO's content that was measured BEFORE the
code existed -- the bar `BUILD-LOG.md` Entry 1 set on 2026-08-12, plus the three
things stage 1 found while meeting it. A failure means the corpus changed or the
engine did; it never means the test is stale.

    python tests/verify_stage1.py
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gl_engine import (Disposition, Cell, Citation, EditionResolver,
                       ReferToCompany, ResolutionError, ResolvedBook,
                       TableError)
from gl_engine.assertions import KNOWN_NONMONOTONIC, ZERO_FACTOR_TABLES, run_all
from gl_engine.config import CLASS_BASIS_CLIFF, MIN_ASOF
from gl_engine.erc.tables import Shape, split_families

TODAY = "20260811"
CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


R = EditionResolver()


# ------------------------------------------------- the bar set before the code

@case("all 51 jurisdictions resolve at a date, plus countrywide")
def _():
    assert len(R.jurisdictions) == 51, len(R.jurisdictions)
    assert "CW" not in R.jurisdictions
    res = R.resolve_all(TODAY)
    assert len(res) == 51, len(res)
    for j, r in res.items():
        assert r.state.identity.juris == j, (j, r.state.pkg_id)
        assert r.state.identity.edition <= TODAY, r


@case("identity comes from the XSD namespace, never the directory (N6)")
def _():
    # 568 packages, each identified by its own targetNamespace. The directory
    # names use spaces where the namespace uses underscores, so a path-derived
    # id would not even be the same string.
    #
    # Was 567 until 2026-08-13, when `GL_OK_20261001_V01` was supplied and
    # unpacked (OI-79). The count is pinned deliberately: a package appearing
    # or vanishing should be a decision, not a surprise.
    pkgs = R.packages
    assert len(pkgs) == 568, len(pkgs)
    for p in pkgs:
        assert len(p.namespaces) == 1, (p.pkg_id, p.namespaces)
        assert p.identity.raw in p.namespaces
        assert "_" in p.identity.raw and " " not in p.identity.raw


@case("each state resolves to ITS OWN declared parent, not the newest (N5)")
def _():
    parents = R.declared_parents(TODAY)
    assert len(parents) == 3, parents
    # California alone declares GL_CW_20231201_V02. If this ever collapses to
    # one parent, the resolver has started taking the newest and five states are
    # being rated against rules they never adopted.
    assert parents["GL_CW_20231201_V02"] == ["CA"], parents
    assert parents["GL_CW_20231201_V03"] == ["NJ", "OK", "TX", "VT"], parents
    assert len(parents["GL_CW_20260101_V01"]) == 46, parents
    cw = [p for p in R.by_juris["CW"] if p.identity.edition <= TODAY]
    assert cw[-1].pkg_id == "GL_CW_20260101_V01"


@case("three parents are live at the 2027 cliff too, and 43 states move")
def _():
    parents = R.declared_parents(CLASS_BASIS_CLIFF)
    assert len(parents) == 3, parents
    assert len(parents["GL_CW_20270401_V01"]) == 43, parents
    assert parents["GL_CW_20231201_V02"] == ["CA"], parents
    # There is no date at which one countrywide edition suffices.
    for d in (TODAY, CLASS_BASIS_CLIFF):
        assert len(R.declared_parents(d)) > 1, d


@case("a date before the floor fails loudly, never falls back (OI-41)")
def _():
    for bad in ("20220831", "20210401", "19990101"):
        try:
            R.resolve("NJ", bad)
        except ResolutionError as e:
            assert MIN_ASOF in str(e), str(e)
        else:
            raise AssertionError(f"{bad} resolved; it must not")
    # and the floor itself is fine
    assert R.resolve("NJ", MIN_ASOF)


@case("a malformed or unknown request fails rather than guessing")
def _():
    for juris, date, exc in (("NJ", "2026-08-11", ResolutionError),
                             ("NJ", "abc", ResolutionError),
                             ("ZZ", TODAY, ResolutionError),
                             ("HI", TODAY, ResolutionError)):   # OI-54: no HI package
        try:
            R.resolve(juris, date)
        except exc:
            pass
        else:
            raise AssertionError(f"{juris}@{date} resolved; it must not")


@case("every load-time assertion passes, and they FAIL rather than warn")
def _():
    rep = run_all(R, TODAY, deep=False)
    assert rep.ok, [str(c) for c in rep.failures]
    assert len(rep.checks) == 6, len(rep.checks)
    rep.raise_if_failed()            # must not raise
    bad = run_all(R, TODAY, deep=False)
    bad.checks[0].passed = False
    try:
        bad.raise_if_failed()
    except Exception as e:
        assert "A1" in str(e), str(e)
    else:
        raise AssertionError("a failed assertion did not raise")


# ------------------------------------------------------------ table loading

@case("tables are typed from ISO's definition, in Decimal, never float")
def _():
    b = ResolvedBook(R.resolve("TX", TODAY))
    t = b.rating_table("ILFPremOps")
    assert t.package == "GL_TX_20250801_V01", t.package
    fi = t.col("Factor")
    assert t.definition.type_of("Factor") == "decimal"
    vals = [r[fi] for r in t.rows if r[fi] is not None]
    assert vals and all(isinstance(v, Decimal) for v in vals)
    assert not any(isinstance(v, float) for v in vals)
    # the limit columns are STRINGS carrying a basis: '1,000,000 CSL'
    assert t.definition.type_of("EachOccurrenceLimit") == "string"


@case("banded and interpolated tables keep their bounds and their mode")
def _():
    b = ResolvedBook(R.resolve("GA", TODAY))
    t = b.table("PremOpsSizeOfRiskRelativity")
    assert t.shape is Shape.INTERPOLATED, t.shape
    kr = t.definition.key_ranges[0]
    assert kr.range_type == "FromInclusiveToExclusive", kr
    assert (kr.lo_col, kr.hi_col) == ("PremOpsExposureTimesThousand_From",
                                      "PremOpsExposureTimesThousand_ToLessThan")
    assert kr.lo_inclusive and not kr.hi_inclusive
    vr = t.definition.value_ranges[0]
    # Size-of-risk relativity INTERPOLATES. Reading it as a step function is
    # wrong by up to the width of a band.
    assert vr.interpolate == "Linear", vr
    assert vr.range_key_col == "PremOpsExposureTimesThousand", vr


@case("a state override wins by NAME and may be deliberately empty (N3)")
def _():
    b = ResolvedBook(R.resolve("NY", TODAY))
    assert b.declares("PremOpsLossCost") == "state"
    # New York declares the name and files no rows in it -- the rows live in 21
    # per-territory slices. Empty is a statement, not an invitation to look up.
    assert b.table("PremOpsLossCost").is_empty
    assert b.parent_table("PremOpsLossCost").package.startswith("GL_CW_")


@case("a rating table that is empty everywhere raises rather than returning zero")
def _():
    b = ResolvedBook(R.resolve("AK", TODAY))
    empties = [n for n in b.parent.names("Rate")
               if b.parent.table("Rate", n).is_empty
               and not b.state.has("Rate", n)
               and not b.siblings(n)]
    assert empties, "expected header-only countrywide tables to exist (N7)"
    n = empties[0]
    assert b.table(n).is_empty              # plain read is allowed
    try:
        b.rating_table(n)                   # rating read is not
    except TableError as e:
        assert "NOT OFFERED HERE" in str(e), str(e)
    else:
        raise AssertionError(f"{n} returned an empty rating table")


@case("per-territory loss-cost slices are found even with NO base table (OI-20)")
def _():
    # The defect this guards: in CA, NJ and OH the state files only the slices,
    # so `PremOpsLossCost` resolves UPWARD to a header-only countrywide table.
    # An engine that reads the base name gets zero rows and no error at all.
    expect = {"CA": 11, "NJ": 15, "NY": 21, "OH": 10}
    for j, n_slices in expect.items():
        b = ResolvedBook(R.resolve(j, TODAY))
        sibs = b.sibling_tables("PremOpsLossCost")
        assert len(sibs) == n_slices, (j, len(sibs))
        assert sum(len(t) for t in sibs) > 10_000, (j, sum(len(t) for t in sibs))
        assert b.rating_table("PremOpsLossCost") is not None
    # CA, NJ and OH have no state base at all; NY declares one and empties it
    for j in ("CA", "NJ", "OH"):
        assert ResolvedBook(R.resolve(j, TODAY)).declares(
            "PremOpsLossCost") == "countrywide", j
    # Texas is the control: it files a populated base and no slices
    tx = ResolvedBook(R.resolve("TX", TODAY))
    assert not tx.siblings("PremOpsLossCost")
    assert len(tx.rating_table("PremOpsLossCost")) == 9504


@case("a bare state-code suffix is not a split family")
def _():
    # `ProdsCompldLossCostNY` is one header-only New York table whose name ends
    # in a state code. Reading it as a broken split family was a false positive
    # that A9 reported before the predicate required a territory marker.
    fams = split_families(["ProdsCompldLossCostNY"])
    assert fams == {}, fams
    assert split_families(["PremOpsLossCostNYTerr001"]) == {
        "PremOpsLossCost": ("PremOpsLossCostNYTerr001",)}
    # `OverOneHundred` / `OverOneMillion` are SEPARATE tables, not slices
    assert split_families(["OwnersContractorsLossCost",
                           "OwnersContractorsLossCostOverOneMillion"]) == {}


# ------------------------------------------------- what stage 1 found on its own

@case("a zero increased-limit factor is a sentinel, and the set is fixed (N13)")
def _():
    b = ResolvedBook(R.resolve("MN", TODAY))
    t = b.rating_table("ILFLiquorWithSubLimit")
    fi = t.col("Factor")
    zeros = [r for r in t.rows if r[fi] == 0]
    assert zeros, "expected zero factors in this table"
    assert "ILFLiquorWithSubLimit" in ZERO_FACTOR_TABLES
    # A zero factor would price the highest limits at nil premium. It is a
    # marker the interpreter must dispose of, never arithmetic.
    assert len(ZERO_FACTOR_TABLES) == 3, ZERO_FACTOR_TABLES


@case("the assertion suite is green at the 2027 cliff too, not just today")
def _():
    # The cliff is where a date-blind engine breaks: 43 jurisdictions change
    # classification basis on one morning and size-of-risk is withdrawn with it.
    rep = run_all(R, CLASS_BASIS_CLIFF, deep=False)
    assert rep.ok, [str(c) for c in rep.failures]


@case("size-of-risk is withdrawn at the cliff, and the withdrawal tracks the parent")
def _():
    # OI-53 asked whether the 2027 countrywide edition WITHDRAWS size-of-risk or
    # merely files it incompletely. The answer is visible once the states that
    # adopt it are counted: at 2026-08-11 35 of 51 jurisdictions carry premises/
    # operations size-of-risk loss costs; at 2027-04-01 only 2 do, and BOTH are
    # among the eight still on an older parent. Every one of the 43 adopting
    # GL_CW_20270401_V01 empties them. 49 states doing the same thing in step is
    # a coordinated withdrawal, not an incomplete filing.
    def populated(asof):
        out = []
        for j in R.jurisdictions:
            b = ResolvedBook(R.resolve(j, asof))
            sibs = b.sibling_tables("PremOpsSizeOfRiskLossCost")
            if sibs:
                n = sum(len(t) for t in sibs)
            elif b.declares("PremOpsSizeOfRiskLossCost"):
                n = len(b.table("PremOpsSizeOfRiskLossCost"))
            else:
                n = 0
            if n:
                out.append(j)
        return out
    assert len(populated(TODAY)) == 35, len(populated(TODAY))
    cliff = populated(CLASS_BASIS_CLIFF)
    assert cliff == ["NJ", "WA"], cliff
    for j in cliff:
        p = R.resolve(j, CLASS_BASIS_CLIFF).parent.pkg_id
        assert p != "GL_CW_20270401_V01", (j, p)
    # and the countrywide apparatus goes with it
    b = ResolvedBook(R.resolve("OH", CLASS_BASIS_CLIFF))
    assert b.parent.pkg_id == "GL_CW_20270401_V01"
    assert len(b.table("PremOpsSizeOfRiskRelativity")) == 8330
    for t in ("PremOpsSizeOfRiskRelativityTableAssignment",
              "PremOpsSizeOfRiskMinimumRelativity",
              "PremOpsSizeOfRiskMaximumRelativity"):
        assert b.table(t).is_empty, t
    # nothing silently returns zero: a rating read of any of it fails loudly
    for t in ("PremOpsSizeOfRiskLossCost",
              "PremOpsSizeOfRiskRelativityTableAssignment"):
        try:
            b.rating_table(t)
        except TableError:
            pass
        else:
            raise AssertionError(f"{t} rated as available while withdrawn")


@case("ONE is also used as a sentinel, and that one case is escalated (E20)")
def _():
    b = ResolvedBook(R.resolve("TX", TODAY))
    t = b.rating_table("ILFElevatorContractor")
    fi, ai = t.col("Factor"), t.col("GeneralAggregateLimit")
    ones = [r for r in t.rows if r[fi] == 1]
    real = [r for r in t.rows if r[fi] > 1]
    # 26 of 30 rows are exactly 1.00, and four carry a genuine 1.69-1.72. A
    # 20,000,000 aggregate priced identically to a 50,000 one is not a filed
    # rate structure -- but ERC cannot say which reading is right, so it
    # escalates rather than being decided here.
    assert len(ones) == 26 and len(real) == 4, (len(ones), len(real))
    assert ("GL_TX_20250801_V01", "ILFElevatorContractor") in KNOWN_NONMONOTONIC
    assert KNOWN_NONMONOTONIC[("GL_TX_20250801_V01",
                               "ILFElevatorContractor")] == "E20"
    # It is not a one-off. All SEVEN Texas editions carry it -- 26 of 30 rows at
    # 1.00 from 2021 through 2025, and 11 of 15 in the 2027 edition, which halves
    # the table and keeps all four genuine factors. Six years of consecutive
    # filings is not a typo, so "no load applies here" is the stronger reading
    # and "placeholder" the weaker one. It refers either way.
    eds = [k for k in KNOWN_NONMONOTONIC if k[1] == "ILFElevatorContractor"]
    assert len(eds) == 7, eds
    later = ResolvedBook(R.resolve("TX", CLASS_BASIS_CLIFF)).rating_table(
        "ILFElevatorContractor")
    assert later.package == "GL_TX_20270401_V01", later.package
    fi2 = later.col("Factor")
    assert sum(1 for r in later.rows if r[fi2] == 1) == 11
    assert sum(1 for r in later.rows if r[fi2] > 1) == 4


@case("the same selector is an integer in one table and a letter in its twin")
def _():
    b = ResolvedBook(R.resolve("AK", TODAY))
    po = b.rating_table("ILFPremOps")
    pr = b.rating_table("ILFProds")
    assert po.definition.type_of("IncreasedLimitsTableAssignmentPremOpsFinal") \
        == "integer"
    assert pr.definition.type_of(
        "IncreasedLimitsTableAssignmentProdsCompldOpsFinal") == "string"
    pv = {r[pr.col("IncreasedLimitsTableAssignmentProdsCompldOpsFinal")]
          for r in pr.rows}
    assert pv == {"A", "B", "C"}, pv
    # Both columns contain the word `Limit` and neither is a limit. This is why
    # the ILF monotonicity check identifies its axes by parsing values, not by
    # reading names.


# ---------------------------------------------------------- the typed cell

@case("a value cannot exist without an ERC source, and REFER never becomes a number")
def _():
    src = Citation("GL_TX_20250801_V01", "Rate Tables", "ILFPremOps", "row 1")
    ok = Cell.published(Decimal("1.25"), src)
    assert ok.require_value() == Decimal("1.25")
    assert ok.is_usable

    ref = Cell.refer(src, escalation="E20", needs="CompanyFiledFactor")
    assert not ref.is_usable
    try:
        ref.require_value()
    except ReferToCompany as e:
        assert e.needs == "CompanyFiledFactor" and e.escalation == "E20"
    else:
        raise AssertionError("a REFER cell yielded a number")

    # a sentinel may not be smuggled in as a value
    try:
        Cell(Disposition.REFER, Decimal("0"), src)
    except ValueError as e:
        assert "not a number" in str(e)
    else:
        raise AssertionError("a REFER cell accepted a value")
    try:
        Cell(Disposition.PUBLISHED, None, src)
    except ValueError:
        pass
    else:
        raise AssertionError("a PUBLISHED cell accepted no value")
    # and there is no way to build one without a source
    try:
        Cell(Disposition.PUBLISHED, Decimal("1"))
    except TypeError:
        pass
    else:
        raise AssertionError("a Cell was built with no ERC source")


@case("the citation names the package that actually won, not the one asked for")
def _():
    b = ResolvedBook(R.resolve("CA", TODAY))
    # CA inherits this from its OWN declared parent, which is not the newest
    c = b.cite("PremOpsLossCost", locator="terr 001")
    assert c.package == "GL_CW_20231201_V02", c.package
    assert str(c).endswith("PremOpsLossCost @ terr 001"), str(c)
    c2 = ResolvedBook(R.resolve("NY", TODAY)).cite("PremOpsLossCost")
    assert c2.package.startswith("GL_NY_"), c2.package


def main():
    fails = []
    for name, fn in CASES:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:
            fails.append((name, e))
            print(f"  FAIL  {name}\n          {type(e).__name__}: {e}")
    print(f"\n{len(CASES) - len(fails)}/{len(CASES)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
